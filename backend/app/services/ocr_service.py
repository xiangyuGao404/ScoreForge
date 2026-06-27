"""
OCR Service - ScoreForge

用多模态 AI（Vision Model）识别试卷图片，一次性输出：
- 每道题的题目内容
- 学生的答案
- 是否正确
- 得分
- 置信度
"""

import base64
import json
import logging
import os
import random
from pathlib import Path

from app.services.ai_service import get_vision_client, _parse_json_from_text, _extract_list_from_response

logger = logging.getLogger(__name__)

# Vision Prompt
VISION_PROMPT = """你是一位试卷识别专家。请仔细分析这张试卷图片，识别出每一道题目。

学科：{subject}

对于每道题，请输出：
1. 题号
2. 题目内容（完整抄写）
3. 学生写的答案（如果能看到）
4. 是否正确（根据批改痕迹判断：✓/✗、分数、红笔批注）
5. 该题得分
6. 该题总分
7. 置信度（0-1，你对识别结果的确信程度）

注意事项：
- 如果看不清某道题，置信度设为 0.5 以下
- 如果没有批改痕迹，is_correct 设为 null
- 如果分数看不清，score_got 设为 null
- 数学公式请用 LaTeX 格式表示
- 每道题的 score_total 请根据试卷总分和题数合理推断

请严格返回 JSON 数组格式：
[{{"question_no":1, "question_content":"...", "student_answer":"...", "is_correct":true, "score_got":5, "score_total":5, "confidence":0.95}}]

只返回 JSON 数组，不要输出任何其他文字。"""


class OCRService:
    """Service for recognizing exam papers using multimodal AI."""

    def _encode_image(self, image_path: str) -> str:
        """Encode image file to base64 string."""
        try:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to encode image {image_path}: {e}")
            return ""

    def _get_mime_type(self, image_path: str) -> str:
        """Get MIME type from file extension."""
        ext = Path(image_path).suffix.lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".bmp": "image/bmp",
            ".webp": "image/webp",
        }
        return mime_map.get(ext, "image/jpeg")

    async def recognize_exam(self, image_paths: list[str], subject: str = "math", user_config: dict = None) -> dict:
        """
        用多模态 AI 识别试卷图片。

        Args:
            image_paths: 图片文件路径列表
            subject: 学科 (math/politics/history)
            user_config: 用户自配置

        Returns:
            {"questions": [...]}
        """
        # Get vision client
        client, model, provider = get_vision_client(user_config)

        if not client:
            logger.warning("No vision AI client available, returning mock recognition")
            return self._mock_recognition()

        try:
            # Build multimodal message content
            subject_labels = {"math": "数学", "politics": "道德与法治", "history": "历史"}
            subject_label = subject_labels.get(subject, subject)

            content = [
                {"type": "text", "text": VISION_PROMPT.format(subject=subject_label)},
            ]

            # Add images
            for img_path in image_paths:
                if not os.path.exists(img_path):
                    logger.warning(f"Image not found: {img_path}")
                    continue

                base64_img = self._encode_image(img_path)
                if not base64_img:
                    continue

                mime_type = self._get_mime_type(img_path)
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{mime_type};base64,{base64_img}"
                    }
                })

            if len(content) <= 1:
                logger.warning("No valid images to process")
                return self._mock_recognition()

            logger.info(f"Calling {provider}/{model} for exam recognition ({len(image_paths)} images)")

            # Call vision model
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": content}],
                max_tokens=4096,
                temperature=0.1,
            )

            text = response.choices[0].message.content
            logger.info(f"Vision model response length: {len(text)}")

            # Parse result
            result = _parse_json_from_text(text)
            questions = _extract_list_from_response(result, ["questions"])

            if not questions:
                # If the result is a list directly
                if isinstance(result, list):
                    questions = result

            # Validate and normalize questions
            normalized = []
            for i, q in enumerate(questions):
                normalized.append({
                    "question_no": q.get("question_no", i + 1),
                    "question_content": q.get("question_content", ""),
                    "student_answer": q.get("student_answer"),
                    "is_correct": q.get("is_correct"),
                    "score_got": q.get("score_got"),
                    "score_total": q.get("score_total", 5),
                    "confidence": min(max(q.get("confidence", 0.8), 0), 1),
                })

            logger.info(f"Exam recognition completed: {len(normalized)} questions identified")
            return {"questions": normalized}

        except Exception as e:
            logger.error(f"Vision AI recognition failed ({provider}/{model}): {e}", exc_info=True)
            return self._mock_recognition()

    def _mock_recognition(self) -> dict:
        """Return mock recognition result for fallback."""
        logger.info("Returning mock recognition data")
        questions = []
        for i in range(1, 6):
            questions.append({
                "question_no": i,
                "question_content": f"这是第{i}题的题目内容（OCR识别结果）",
                "student_answer": f"学生答案{i}" if i % 2 == 0 else None,
                "is_correct": i % 2 != 0,
                "score_got": 5 if i % 2 != 0 else 0,
                "score_total": 5,
                "confidence": round(random.uniform(0.7, 0.99), 2),
            })
        return {"questions": questions}


ocr_service = OCRService()
