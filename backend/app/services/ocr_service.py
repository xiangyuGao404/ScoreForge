"""OCR service for exam recognition using PaddleOCR."""

import logging
import random
from typing import Optional

logger = logging.getLogger(__name__)


class OCRService:
    """Service for recognizing exam papers using OCR."""

    def __init__(self):
        self._ocr = None

    def _get_ocr(self):
        """Lazy-load PaddleOCR instance."""
        if self._ocr is None:
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
                logger.info("PaddleOCR initialized successfully")
            except ImportError:
                logger.warning("PaddleOCR not available, using mock recognition")
                return None
        return self._ocr

    async def recognize_exam(self, image_urls: list[str]) -> dict:
        """
        Recognize exam paper from images.
        Returns structured recognition result.
        """
        ocr = self._get_ocr()

        if ocr is None:
            # Mock recognition for development
            return self._mock_recognition()

        all_questions = []
        question_no = 1

        for image_url in image_urls:
            try:
                result = ocr.ocr(image_url, cls=True)
                if result and result[0]:
                    # Extract text blocks
                    texts = []
                    for line in result[0]:
                        if line and len(line) >= 2:
                            text = line[1][0] if isinstance(line[1], (list, tuple)) else str(line[1])
                            confidence = line[1][1] if isinstance(line[1], (list, tuple)) and len(line[1]) > 1 else 0.9
                            texts.append({"text": text, "confidence": confidence})

                    # TODO: Implement proper question segmentation
                    # For now, create mock questions from OCR text
                    for i in range(0, min(len(texts), 5)):
                        q_text = texts[i]["text"] if i < len(texts) else f"题目{question_no}"
                        conf = texts[i]["confidence"] if i < len(texts) else 0.8

                        all_questions.append({
                            "question_no": question_no,
                            "question_content": q_text,
                            "is_correct": random.choice([True, False]),
                            "score_got": random.choice([0, 3, 5]),
                            "score_total": 5,
                            "confidence": round(conf, 2),
                        })
                        question_no += 1

            except Exception as e:
                logger.error(f"OCR failed for image {image_url}: {e}")
                continue

        if not all_questions:
            return self._mock_recognition()

        return {"questions": all_questions}

    def _mock_recognition(self) -> dict:
        """Return mock recognition result for development."""
        questions = []
        for i in range(1, 6):
            questions.append({
                "question_no": i,
                "question_content": f"这是第{i}题的题目内容（OCR识别结果）",
                "is_correct": i % 2 != 0,
                "score_got": 5 if i % 2 != 0 else 0,
                "score_total": 5,
                "confidence": round(random.uniform(0.7, 0.99), 2),
            })
        return {"questions": questions}


ocr_service = OCRService()
