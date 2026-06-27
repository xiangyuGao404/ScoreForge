"""AI service for weakness analysis, question generation, and mastery assessment."""

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


def _extract_list_from_response(result: any, keys: list[str] = None) -> list:
    """Extract a list from AI response, handling various JSON formats.

    L-8 fix: Robust parsing that handles:
    - Direct list: [...]
    - Wrapped list: {"weaknesses": [...]} or {"questions": [...]} or {"data": [...]}
    - Nested: {"data": {"weaknesses": [...]}}
    """
    if keys is None:
        keys = ["weaknesses", "questions", "data", "items", "results"]

    if isinstance(result, list):
        return result

    if isinstance(result, dict):
        # Try each key
        for key in keys:
            val = result.get(key)
            if isinstance(val, list):
                return val
            # Handle nested dict
            if isinstance(val, dict):
                for subkey in keys:
                    subval = val.get(subkey)
                    if isinstance(subval, list):
                        return subval

        # Try to find any list value in the dict
        for val in result.values():
            if isinstance(val, list):
                return val

    logger.warning(f"Could not extract list from AI response: {type(result)}")
    return []


class AIService:
    """Service for AI-powered analysis and generation."""

    def __init__(self):
        self._client = None

    def _get_client(self, api_key: Optional[str] = None):
        """Get OpenAI client with the given or default API key."""
        from openai import AsyncOpenAI

        key = api_key or settings.OPENAI_API_KEY
        if not key:
            logger.warning("No API key configured, using mock AI responses")
            return None

        return AsyncOpenAI(
            api_key=key,
            base_url=settings.OPENAI_API_BASE,
        )

    async def _log_usage(self, db: AsyncSession, user_id: str, action: str, input_tokens: int, output_tokens: int, cost: float):
        """Log API usage for billing and monitoring."""
        log = APIUsageLog(
            user_id=uuid.UUID(user_id),
            action=action,
            token_input=input_tokens,
            token_output=output_tokens,
            cost=cost,
        )
        db.add(log)
        await db.flush()

    async def _get_user_api_key(self, db: AsyncSession, user_id: str) -> Optional[str]:
        """Get user's custom API key if available."""
        from app.core.security import decrypt_api_key

        result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        user = result.scalar_one_or_none()
        if user and user.api_key_encrypted:
            try:
                return decrypt_api_key(user.api_key_encrypted)
            except Exception:
                return None
        return None

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

        # Get student info
        from app.models.user import Student
        student_result = await db.execute(select(Student).where(Student.id == uuid.UUID(student_id)))
        student = student_result.scalar_one_or_none()

        if not student:
            raise ValueError("Student not found")

        # Get historical weaknesses
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

        # Build prompt
        system_prompt = """你是一位资深的中学教研专家，拥有20年教学经验，擅长分析学生试卷并制定高效的提分策略。

## 输出要求
你必须返回一个合法的JSON数组，格式如下：
[
  {
    "knowledge_point": "知识点名称",
    "star_rating": 5,
    "reason": "2-3句话说明为什么排在这里",
    "error_type": "conceptual|careless|incomplete",
    "related_score": 15,
    "difficulty_to_improve": "easy|medium|hard"
  }
]

## 星级评定标准
- 5星：分值大 + 错误类型为基础概念 + 提分难度低 = 最应该优先
- 4星：分值中等 + 有明确改进空间
- 3星：分值中等 + 提分需要较长时间
- 2星：分值小 或 提分难度大
- 1星：难题/压轴题，短期无法提分

## 严格约束
- 只输出JSON数组，不要输出任何其他文字
- star_rating 必须是 1-5 的整数
- reason 不超过100字"""

        subject_labels = {"math": "数学", "politics": "道法", "history": "历史"}
        subject_label = subject_labels.get(subject, subject)

        wrong_questions_text = "\n".join([
            f"第{q['question_no']}题：{q.get('question_content', '未知')}，得分：{q['score_got']}/{q['score_total']}"
            for q in wrong_questions
        ])

        user_prompt = f"""## 学生信息
- 姓名：{student.name}
- 年级：{student.grade.value}
- 本次考试：{subject_label}，满分 {total_score}，得分 {actual_score}

## 本次试卷错题
{wrong_questions_text}

## 该学生历史薄弱点数据
{json.dumps(historical_weaknesses, ensure_ascii=False, indent=2)}

请分析并输出薄弱点列表（JSON数组）。"""

        # Call AI
        client = self._get_client()
        if not client:
            return self._mock_weakness_analysis(wrong_questions)

        try:
            response = await client.chat.completions.create(
                model=settings.DEFAULT_AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            # L-8 fix: robust list extraction
            result = _extract_list_from_response(result, ["weaknesses", "data", "items"])

            # Log usage
            await self._log_usage(
                db=db,
                user_id=str(student.user_id),
                action="analyze",
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                cost=0,  # Calculate based on model pricing
            )

            return result

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._mock_weakness_analysis(wrong_questions)

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
4. 数学题：计算过程必须完整
5. 道法/历史题：必须标注涉及的课本章节

## 输出要求
返回合法的JSON数组：
[
  {{
    "question_no": 1,
    "difficulty": "basic",
    "question_type": "choice|fill_blank|solve",
    "question_content": "题目内容",
    "reference_answer": "参考答案",
    "solution_detail": "详细解析"
  }}
]

## 严格约束
- 只输出JSON数组
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

        client = self._get_client()
        if not client:
            return self._mock_question_generation(question_count)

        try:
            response = await client.chat.completions.create(
                model=settings.DEFAULT_AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            # L-8 fix: robust list extraction
            result = _extract_list_from_response(result, ["questions", "data", "items"])

            await self._log_usage(
                db=db,
                user_id=user_id,
                action="generate_questions",
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                cost=0,
            )

            return result

        except Exception as e:
            logger.error(f"AI question generation failed: {e}")
            return self._mock_question_generation(question_count)

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

## 掌握标准
- 连续2轮正确率 ≥ 80%，且无概念性错误 → 建议"已掌握"
- 正确率 60%-80% → 建议"继续练习"
- 正确率 < 60% → 建议"加强练习"

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

        client = self._get_client()
        if not client:
            return self._mock_mastery_assessment(correct_count, total_count)

        try:
            response = await client.chat.completions.create(
                model=settings.DEFAULT_AI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            result = json.loads(content)

            await self._log_usage(
                db=db,
                user_id=user_id,
                action="assess_mastery",
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                cost=0,
            )

            return result

        except Exception as e:
            logger.error(f"AI mastery assessment failed: {e}")
            return self._mock_mastery_assessment(correct_count, total_count)

    def _mock_weakness_analysis(self, wrong_questions: list[dict]) -> list[dict]:
        """Return mock weakness analysis for development."""
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
        """Return mock questions for development."""
        questions = []
        difficulties = ["basic", "basic", "medium", "medium", "advanced"]
        types = ["fill_blank", "choice", "fill_blank", "solve", "choice"]

        for i in range(1, count + 1):
            diff_idx = min(i - 1, len(difficulties) - 1)
            questions.append({
                "question_no": i,
                "difficulty": difficulties[diff_idx],
                "question_type": types[diff_idx],
                "question_content": f"这是第{i}道练习题的内容（AI生成）",
                "reference_answer": f"参考答案{i}",
                "solution_detail": f"详细解析：这道题的解题思路是...（第{i}题解析）",
            })
        return questions

    def _mock_mastery_assessment(self, correct: int, total: int) -> dict:
        """Return mock mastery assessment for development."""
        rate = correct / total if total > 0 else 0
        return {
            "mastery_score": int(rate * 100),
            "trend": "rising" if rate >= 0.6 else "stable",
            "error_pattern": "概念不清" if rate < 0.6 else "计算失误",
            "recommendation": "continue" if rate < 0.8 else "mastered",
            "suggested_days": 2 if rate < 0.8 else 0,
            "suggestion_detail": "建议继续练习，巩固基础知识" if rate < 0.8 else "已达到掌握标准，可以进入下一阶段",
        }


ai_service = AIService()
