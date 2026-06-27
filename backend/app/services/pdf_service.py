"""PDF generation service using WeasyPrint."""

import os
import logging
from datetime import datetime, timezone

from jinja2 import Template

from app.core.config import settings

logger = logging.getLogger(__name__)

# HTML template for PDF generation
PDF_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <style>
    @page {
      size: A4;
      margin: 2cm 2.5cm;
      @bottom-center {
        content: "由 ScoreForge 生成 · scoreforge.app";
        font-size: 9pt;
        color: #94A3B8;
      }
      @top-right {
        content: "第 " counter(page) " 页 / 共 " counter(pages) " 页";
        font-size: 9pt;
        color: #94A3B8;
      }
    }

    body {
      font-family: "PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif;
      font-size: 12pt;
      line-height: 1.8;
      color: #1E293B;
    }

    .header {
      border-bottom: 2px solid #2563EB;
      padding-bottom: 12px;
      margin-bottom: 20px;
    }

    .header h1 {
      font-size: 18pt;
      color: #2563EB;
      margin: 0;
    }

    .header .meta {
      font-size: 10pt;
      color: #64748B;
      margin-top: 4px;
    }

    .weakness-title {
      font-size: 14pt;
      font-weight: bold;
      color: #1E293B;
      margin: 20px 0 16px;
      padding: 8px 12px;
      background: #DBEAFE;
      border-radius: 6px;
    }

    .question {
      margin-bottom: 20px;
      page-break-inside: avoid;
    }

    .question .q-no {
      font-weight: bold;
      color: #2563EB;
    }

    .question .q-difficulty {
      display: inline-block;
      font-size: 9pt;
      padding: 2px 8px;
      border-radius: 4px;
      margin-left: 8px;
    }

    .difficulty-basic { background: #D1FAE5; color: #065F46; }
    .difficulty-medium { background: #FEF3C7; color: #92400E; }
    .difficulty-advanced { background: #FEE2E2; color: #991B1B; }

    .answer-space {
      border-bottom: 1px solid #CBD5E1;
      height: 60px;
      margin: 8px 0;
    }

    .answer-section {
      page-break-before: always;
    }

    .answer-item {
      margin-bottom: 16px;
      padding: 12px;
      background: #F8FAFC;
      border-radius: 8px;
      border-left: 3px solid #10B981;
    }

    .answer-item .answer {
      font-weight: bold;
      color: #10B981;
    }

    .answer-item .solution {
      margin-top: 8px;
      font-size: 11pt;
      color: #475569;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>ScoreForge 练习题</h1>
    <div class="meta">
      学生：{{ student_name }} · 学科：{{ subject }} · 日期：{{ date }}
    </div>
  </div>

  <div class="weakness-title">
    薄弱点：{{ weakness_name }}
  </div>

  <div class="questions-section">
    {% for q in questions %}
    <div class="question">
      <span class="q-no">{{ q.question_no }}.</span>
      <span class="q-difficulty difficulty-{{ q.difficulty }}">
        {{ difficulty_label[q.difficulty] }}
      </span>
      <div class="content">{{ q.question_content }}</div>
      {% if q.question_type == 'solve' %}
      <div class="answer-space"></div>
      <div class="answer-space"></div>
      {% endif %}
    </div>
    {% endfor %}
  </div>

  {% if include_answers %}
  <div class="answer-section">
    <h2>参考答案与解析</h2>
    {% for q in questions %}
    <div class="answer-item">
      <div><strong>{{ q.question_no }}. 答案：</strong><span class="answer">{{ q.reference_answer }}</span></div>
      {% if include_solutions %}
      <div class="solution">{{ q.solution_detail }}</div>
      {% endif %}
    </div>
    {% endfor %}
  </div>
  {% endif %}
</body>
</html>"""


class PDFService:
    """Service for generating PDF practice sheets."""

    def __init__(self):
        os.makedirs(settings.PDF_DIR, exist_ok=True)

    async def generate(
        self,
        student_name: str,
        subject: str,
        weakness_name: str,
        questions: list[dict],
        include_answers: bool = True,
        include_solutions: bool = True,
        pdf_id: str = "",
    ) -> str:
        """Generate a PDF file and return its path."""
        from weasyprint import HTML

        template = Template(PDF_TEMPLATE)
        html_content = template.render(
            student_name=student_name,
            subject=subject,
            weakness_name=weakness_name,
            date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            questions=questions,
            include_answers=include_answers,
            include_solutions=include_solutions,
            difficulty_label={"basic": "基础", "medium": "中等", "advanced": "进阶"},
        )

        filename = f"{pdf_id}.pdf" if pdf_id else f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.pdf"
        filepath = os.path.join(settings.PDF_DIR, filename)

        HTML(string=html_content).write_pdf(filepath)

        logger.info(f"PDF generated: {filepath}")
        return filepath


pdf_service = PDFService()
