"""
AI Service - ScoreForge

支持多平台（小米/DeepSeek/OpenAI）+ 多模型（通用/视觉）切换。
用户可配置自己的 API Key，优先级：用户配置 > 系统配置 > mock
"""

import json
import logging
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.models.api_usage import APIUsageLog

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
REQUEST_TIMEOUT = 60.0


def _extract_list_from_response(result, keys: list[str] = None) -> list:
    """Extract a list from AI response, handling various JSON formats."""
    if keys is None:
        keys = ["weaknesses", "questions", "data", "items", "results"]

    if isinstance(result, list):
        return result

    if isinstance(result, dict):
        for key in keys:
            val = result.get(key)
            if isinstance(val, list):
                return val
            if isinstance(val, dict):
                for subkey in keys:
                    subval = val.get(subkey)
                    if isinstance(subval, list):
                        return subval
        for val in result.values():
            if isinstance(val, list):
                return val

    logger.warning(f"Could not extract list from AI response: {type(result)}")
    return []


def _parse_json_from_text(text: str):
    """Parse JSON from AI response, handling markdown code blocks."""
    import re

    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n", 1)
        if len(lines) > 1:
            text = lines[1]
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3].rstrip()

    return json.loads(text)


# ──────────────────────────────────────────────────────────────
# Client Factory
# ──────────────────────────────────────────────────────────────

def _get_client(task_type: str = "general", user_config: dict = None):
    """
    获取 AI 客户端。
    优先级：用户配置 > 系统配置 > mock

    Args:
        task_type: "general" (分析/出题/评估) 或 "vision" (图片识别)
        user_config: 用户自配置 {"provider", "api_key", "api_base", "general_model", "vision_model"}

    Returns:
        (client, model, provider) 或 (None, None, "mock")
    """
    from openai import AsyncOpenAI

    # 优先使用用户配置
    if user_config and user_config.get("api_key"):
        provider = user_config.get("provider", "openai")
        api_key = user_config["api_key"]
        api_base = user_config.get("api_base", "https://api.openai.com/v1")
        model_key = f"{task_type}_model"
        model = user_config.get(model_key, "")

        if not model:
            # Fallback to system default
            model = _get_system_model(provider, task_type)

        client = AsyncOpenAI(
            api_key=api_key,
            base_url=api_base,
            timeout=REQUEST_TIMEOUT,
            max_retries=MAX_RETRIES,
        )
        return client, model, provider

    # 使用系统默认配置
    provider = settings.AI_PROVIDER.lower()

    if provider == "xiaomi" and settings.XIAOMI_API_KEY:
        api_key = settings.XIAOMI_API_KEY
        api_base = settings.XIAOMI_API_BASE
        model = settings.XIAOMI_VISION_MODEL if task_type == "vision" else settings.XIAOMI_GENERAL_MODEL
    elif provider == "deepseek" and settings.DEEPSEEK_API_KEY:
        api_key = settings.DEEPSEEK_API_KEY
        api_base = settings.DEEPSEEK_API_BASE
        model = settings.DEEPSEEK_VISION_MODEL if task_type == "vision" else settings.DEEPSEEK_GENERAL_MODEL
    elif settings.OPENAI_API_KEY:
        api_key = settings.OPENAI_API_KEY
        api_base = settings.OPENAI_API_BASE
        model = settings.OPENAI_VISION_MODEL if task_type == "vision" else settings.OPENAI_GENERAL_MODEL
        provider = "openai"
    else:
        logger.warning("No AI API key configured, will use mock responses")
        return None, None, "mock"

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=api_base,
        timeout=REQUEST_TIMEOUT,
        max_retries=MAX_RETRIES,
    )
    return client, model, provider


def _get_system_model(provider: str, task_type: str) -> str:
    """Get default model for a provider and task type."""
    if provider == "xiaomi":
        return settings.XIAOMI_VISION_MODEL if task_type == "vision" else settings.XIAOMI_GENERAL_MODEL
    elif provider == "deepseek":
        return settings.DEEPSEEK_VISION_MODEL if task_type == "vision" else settings.DEEPSEEK_GENERAL_MODEL
    else:
        return settings.OPENAI_VISION_MODEL if task_type == "vision" else settings.OPENAI_GENERAL_MODEL


def get_vision_client(user_config: dict = None):
    """Get vision model client for OCR service."""
    return _get_client(task_type="vision", user_config=user_config)


def get_general_client(user_config: dict = None):
    """Get general model client for analysis/generation."""
    return _get_client(task_type="general", user_config=user_config)


# ──────────────────────────────────────────────────────────────
# AI Service
# ──────────────────────────────────────────────────────────────

class AIService:
    """Service for AI-powered analysis and generation."""

    async def _log_usage(self, db: AsyncSession, user_id: str, action: str,
                         input_tokens: int = 0, output_tokens: int = 0, cost: float = 0):
        """Log API usage for billing and monitoring."""
        try:
            log = APIUsageLog(
                user_id=uuid.UUID(user_id),
                action=action,
                token_input=input_tokens,
                token_output=output_tokens,
                cost=cost,
            )
            db.add(log)
            await db.flush()
        except Exception as e:
            logger.warning(f"Failed to log API usage: {e}")

    async def _get_user_config(self, db: AsyncSession, user_id: str) -> Optional[dict]:
        """Get user's API config if available."""
        try:
            from app.core.security import decrypt_api_key
            result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
            user = result.scalar_one_or_none()
            if user and user.api_config_encrypted:
                decrypted = decrypt_api_key(user.api_config_encrypted)
                return json.loads(decrypted)
        except Exception as e:
            logger.warning(f"Failed to get user config: {e}")
        return None

    # ──────────────────────────────────────────────────────────
    # 1. 薄弱点分析
    # ──────────────────────────────────────────────────────────

    async def analyze_weaknesses(
        self,
        student_id: str,
        subject: str,
        total_score: int,
        actual_score: int,
        wrong_questions: list[dict],
        db: AsyncSession,
    ) -> list[dict]:
        """Analyze exam results and identify weaknesses with star ratings."""

        from app.models.user import Student
        student_result = await db.execute(select(Student).where(Student.id == uuid.UUID(student_id)))
        student = student_result.scalar_one_or_none()
        if not student:
            raise ValueError("Student not found")

        from app.models.weakness import Weakness
        from app.models.knowledge import KnowledgePoint
        history_result = await db.execute(
            select(Weakness, KnowledgePoint)
            .join(KnowledgePoint, Weakness.knowledge_point_id == KnowledgePoint.id)
            .where(Weakness.student_id == uuid.UUID(student_id))
        )
        historical_weaknesses = [
            {"knowledge_point": kp.name, "status": w.status.value, "mastery_score": w.mastery_score}
            for w, kp in history_result.all()
        ]

        system_prompt = """你是一位资深的中学教研专家，拥有20年教学经验，擅长分析学生试卷并制定高效的提分策略。

## 输出要求
你必须返回一个合法的JSON对象，格式如下：
{
  "weaknesses": [
    {
      "knowledge_point": "知识点名称",
      "star_rating": 5,
      "reason": "2-3句话说明为什么排在这里",
      "error_type": "conceptual|careless|incomplete",
      "related_score": 15,
      "difficulty_to_improve": "easy|medium|hard"
    }
  ]
}

## 星级评定标准
- 5星：分值大 + 错误类型为基础概念 + 提分难度低 = 最应该优先
- 4星：分值中等 + 有明确改进空间
- 3星：分值中等 + 提分需要较长时间
- 2星：分值小 或 提分难度大
- 1星：难题/压轴题，短期无法提分

## 严格约束
- 只输出JSON对象，不要输出任何其他文字
- star_rating 必须是 1-5 的整数
- reason 不超过100字"""

        subject_labels = {"math": "数学", "politics": "道法", "history": "历史"}
        subject_label = subject_labels.get(subject, subject)

        wrong_questions_text = "\n".join([
            f"第{q['question_no']}题：{q.get('question_content', '未知')}，得分：{q['score_got']}/{q['score_total']}"
            for q in wrong_questions
        ]) if wrong_questions else "无错题数据"

        user_prompt = f"""## 学生信息
- 姓名：{student.name}
- 年级：{student.grade.value}
- 本次考试：{subject_label}，满分 {total_score}，得分 {actual_score}

## 本次试卷错题
{wrong_questions_text}

## 该学生历史薄弱点数据
{json.dumps(historical_weaknesses, ensure_ascii=False, indent=2)}

请分析并输出薄弱点列表（JSON对象，包含weaknesses数组）。"""

        # Get client (try user config first)
        user_config = await self._get_user_config(db, str(student.user_id))
        client, model, provider = get_general_client(user_config)

        if not client:
            logger.warning("No AI client available, returning mock weakness analysis")
            return self._mock_weakness_analysis(wrong_questions)

        try:
            logger.info(f"Calling {provider}/{model} for weakness analysis (student={student_id})")

            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=4096,
            )

            text = response.choices[0].message.content
            result = _parse_json_from_text(text)
            result = _extract_list_from_response(result, ["weaknesses", "data", "items"])

            usage = response.usage
            await self._log_usage(
                db, str(student.user_id), "analyze",
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
            )

            logger.info(f"Weakness analysis completed: {len(result)} weaknesses found")
            return result

        except Exception as e:
            logger.error(f"AI weakness analysis failed ({provider}/{model}): {e}", exc_info=True)
            return self._mock_weakness_analysis(wrong_questions)

    # ──────────────────────────────────────────────────────────
    # 2. 智能出题
    # ──────────────────────────────────────────────────────────

    async def generate_questions(
        self,
        knowledge_point: str,
        subject: str,
        grade: str,
        question_count: int,
        historical_questions: list[str],
        db: AsyncSession,
        user_id: str,
    ) -> list[dict]:
        """Generate practice questions for a specific knowledge point."""

        subject_labels = {"math": "数学", "politics": "道法", "history": "历史"}
        subject_label = subject_labels.get(subject, subject)

        system_prompt = f"""你是一位中学{subject_label}命题专家，擅长针对特定知识点设计精准的练习题。

## 命题原则
1. 题目必须紧扣指定知识点，不超纲
2. 难度梯度严格按要求：前2题基础 → 中间2题中等 → 最后1题进阶
3. 题型要多样（选择题、填空题、解答题混合）
4. 数学题：计算过程必须完整，每一步都要写清楚
5. 道法/历史题：必须标注涉及的课本章节，答案要引用教材原文
6. 所有题目必须是原创的，不能照搬教材原题

## 输出要求
返回合法的JSON对象：
{{
  "questions": [
    {{
      "question_no": 1,
      "difficulty": "basic",
      "question_type": "choice|fill_blank|solve",
      "question_content": "题目内容（支持换行用\\\\n）",
      "reference_answer": "参考答案",
      "solution_detail": "详细解析，包含解题思路和关键步骤"
    }}
  ]
}}

## 严格约束
- 只输出JSON对象
- 每道题的 solution_detail 必须详细到学生能看懂
- 选择题的选项必须用 A/B/C/D 标注
- 不要生成与历史题目重复的内容"""

        historical_text = "\n".join([f"- {q}" for q in historical_questions[:20]]) if historical_questions else "无"

        user_prompt = f"""## 知识点
{knowledge_point}

## 年级
{grade}

## 难度要求
前2题基础，中间2题中等，最后1题进阶

## 该学生已做过的同类题目（请避免重复）
{historical_text}

请生成{question_count}道练习题。"""

        user_config = await self._get_user_config(db, user_id)
        client, model, provider = get_general_client(user_config)

        if not client:
            logger.warning("No AI client available, returning mock questions")
            return self._mock_question_generation(question_count)

        try:
            logger.info(f"Calling {provider}/{model} for question generation (knowledge_point={knowledge_point})")

            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=4096,
            )

            text = response.choices[0].message.content
            result = _parse_json_from_text(text)
            result = _extract_list_from_response(result, ["questions", "data", "items"])

            usage = response.usage
            await self._log_usage(
                db, user_id, "generate_questions",
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
            )

            logger.info(f"Question generation completed: {len(result)} questions generated")
            return result

        except Exception as e:
            logger.error(f"AI question generation failed ({provider}/{model}): {e}", exc_info=True)
            return self._mock_question_generation(question_count)

    # ──────────────────────────────────────────────────────────
    # 3. 掌握度评估
    # ──────────────────────────────────────────────────────────

    async def assess_mastery(
        self,
        student_name: str,
        grade: str,
        knowledge_point: str,
        practice_history: list[dict],
        correct_count: int,
        total_count: int,
        wrong_details: list[dict],
        db: AsyncSession,
        user_id: str,
    ) -> dict:
        """Assess mastery level based on practice results."""

        system_prompt = """你是一位教育心理学专家，擅长评估学生对特定知识点的掌握程度。

## 评估维度
1. 正确率：本轮做题的正确比例
2. 错误模式：分析错误的深层原因
3. 掌握趋势：结合历史数据判断进步/退步
4. 综合判断：给出0-100的掌握度评分

## 掌握标准
- 连续2轮正确率 ≥ 80%，且无概念性错误 → 建议"已掌握"
- 正确率 60%-80%，或有概念性错误 → 建议"继续练习"
- 正确率 < 60% → 建议"加强练习，可能需要换种方式讲解"

## 输出要求
返回合法的JSON对象：
{
  "mastery_score": 75,
  "trend": "rising|stable|falling",
  "error_pattern": "概念不清|计算失误|审题不仔细|知识遗忘|其他",
  "recommendation": "continue|mastered|intensify",
  "suggested_days": 2,
  "suggestion_detail": "具体的建议，50字以内"
}

## 严格约束
- 只输出JSON对象
- mastery_score 必须是 0-100 的整数
- suggested_days 必须是 1-14 的整数"""

        wrong_text = "\n".join([
            f"第{d['question_no']}题：{d.get('question_content', '')}，学生答案：{d.get('student_answer', '')}"
            for d in wrong_details
        ]) if wrong_details else "无错题"

        history_text = "\n".join([
            f"{h['date']}：正确率 {h['correct_rate']*100:.0f}%"
            for h in practice_history[-5:]
        ]) if practice_history else "首次练习"

        user_prompt = f"""## 学生信息
- 姓名：{student_name}
- 年级：{grade}

## 知识点
{knowledge_point}

## 练习历史
{history_text}

## 本次练习结果
- 做了 {total_count} 题，对了 {correct_count} 题
- 正确率：{correct_count/total_count*100:.0f}%

## 错题详情
{wrong_text}

请评估掌握程度。"""

        user_config = await self._get_user_config(db, user_id)
        client, model, provider = get_general_client(user_config)

        if not client:
            logger.warning("No AI client available, returning mock assessment")
            return self._mock_mastery_assessment(correct_count, total_count)

        try:
            logger.info(f"Calling {provider}/{model} for mastery assessment (knowledge_point={knowledge_point})")

            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=4096,
            )

            text = response.choices[0].message.content
            result = _parse_json_from_text(text)

            usage = response.usage
            await self._log_usage(
                db, user_id, "assess_mastery",
                input_tokens=usage.prompt_tokens if usage else 0,
                output_tokens=usage.completion_tokens if usage else 0,
            )

            logger.info(f"Mastery assessment completed: score={result.get('mastery_score')}")
            return result

        except Exception as e:
            logger.error(f"AI mastery assessment failed ({provider}/{model}): {e}", exc_info=True)
            return self._mock_mastery_assessment(correct_count, total_count)

    # ──────────────────────────────────────────────────────────
    # Mock 数据（降级用）
    # ──────────────────────────────────────────────────────────

    def _mock_weakness_analysis(self, wrong_questions: list[dict]) -> list[dict]:
        logger.info("Returning mock weakness analysis data")
        return [
            {
                "knowledge_point": "函数基础概念",
                "star_rating": 5,
                "reason": "函数是中考必考重点，本次函数题全错，但属于基础概念题，掌握后提分空间大。",
                "error_type": "conceptual",
                "related_score": 15,
                "difficulty_to_improve": "easy",
            },
            {
                "knowledge_point": "一元二次方程计算",
                "star_rating": 4,
                "reason": "方程计算错误集中在求根公式应用，属于计算粗心而非概念不清，短期练习可改善。",
                "error_type": "careless",
                "related_score": 10,
                "difficulty_to_improve": "easy",
            },
            {
                "knowledge_point": "几何证明",
                "star_rating": 3,
                "reason": "几何证明需要较强的逻辑推理能力，短期提分难度较大，建议后期攻克。",
                "error_type": "incomplete",
                "related_score": 12,
                "difficulty_to_improve": "hard",
            },
        ]

    def _mock_question_generation(self, count: int) -> list[dict]:
        logger.info(f"Returning {count} mock questions")
        questions = []
        difficulties = ["basic", "basic", "medium", "medium", "advanced"]
        types = ["fill_blank", "choice", "fill_blank", "solve", "choice"]
        for i in range(1, count + 1):
            diff_idx = min(i - 1, len(difficulties) - 1)
            questions.append({
                "question_no": i,
                "difficulty": difficulties[diff_idx],
                "question_type": types[diff_idx],
                "question_content": f"这是第{i}道练习题的内容（AI服务降级，返回Mock数据）",
                "reference_answer": f"参考答案{i}",
                "solution_detail": f"详细解析：这道题的解题思路是...（第{i}题解析）",
            })
        return questions

    def _mock_mastery_assessment(self, correct: int, total: int) -> dict:
        rate = correct / total if total > 0 else 0
        logger.info(f"Returning mock mastery assessment (rate={rate:.2f})")
        return {
            "mastery_score": int(rate * 100),
            "trend": "rising" if rate >= 0.6 else "stable",
            "error_pattern": "概念不清" if rate < 0.6 else "计算失误",
            "recommendation": "continue" if rate < 0.8 else "mastered",
            "suggested_days": 2 if rate < 0.8 else 0,
            "suggestion_detail": "建议继续练习，巩固基础知识" if rate < 0.8 else "已达到掌握标准，可以进入下一阶段",
        }


ai_service = AIService()
