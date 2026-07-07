"""
خروجی PDF
PDF Export utility using reportlab.
"""
import os
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from arabic_reshaper import reshape
from bidi.algorithm import get_display

def _get_assets_dir() -> Path:
    # Try multiple locations to find assets/fonts
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent.parent / 'assets',
        here.parent / 'assets',
        Path.cwd() / 'azmoon_saz_project' / 'azmoon_saz' / 'assets',
        Path.cwd() / 'assets',
    ]
    for c in candidates:
        if (c / 'fonts').exists():
            return c
    return candidates[0]

def register_fonts():
    assets_dir = _get_assets_dir()
    fonts_dir = assets_dir / 'fonts'

    font_regular = fonts_dir / 'Vazirmatn-Regular.ttf'
    font_bold = fonts_dir / 'Vazirmatn-Bold.ttf'

    if font_regular.exists():
        pdfmetrics.registerFont(TTFont('Vazirmatn', str(font_regular)))
    if font_bold.exists():
        pdfmetrics.registerFont(TTFont('Vazirmatn-Bold', str(font_bold)))

def fa_pdf(text):
    """Prepare Persian text for PDF (reshaping + bidi)."""
    if not text:
        return ""
    try:
        reshaped = reshape(str(text))
        return get_display(reshaped)
    except Exception:
        return str(text)

def export_lesson_to_pdf(title, lesson_text, output_path):
    register_fonts()
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    # Header
    c.setFont('Vazirmatn-Bold', 18)
    c.drawCentredString(width/2, height - 2*cm, fa_pdf(title))

    c.setFont('Vazirmatn', 10)
    c.drawRightString(width - 2*cm, height - 3*cm, fa_pdf("سازنده: احسان حسین زاده"))

    c.line(2*cm, height - 3.5*cm, width - 2*cm, height - 3.5*cm)

    # Content
    c.setFont('Vazirmatn', 12)
    y = height - 4.5*cm
    leading = 0.7*cm

    lines = lesson_text.split('\n')
    for line in lines:
        if not line.strip():
            y -= leading
            continue

        if y < 2*cm:
            c.showPage()
            c.setFont('Vazirmatn', 12)
            y = height - 2*cm

        # Simple line wrapping logic
        words = line.split()
        current_line_words = []
        for word in words:
            current_line_words.append(word)
            test_line = ' '.join(current_line_words)
            if c.stringWidth(fa_pdf(test_line), 'Vazirmatn', 12) > (width - 4*cm):
                # Draw previous line
                c.drawRightString(width - 2*cm, y, fa_pdf(' '.join(current_line_words[:-1])))
                y -= leading
                current_line_words = [word]
                if y < 2*cm:
                    c.showPage()
                    c.setFont('Vazirmatn', 12)
                    y = height - 2*cm

        if current_line_words:
            c.drawRightString(width - 2*cm, y, fa_pdf(' '.join(current_line_words)))
            y -= leading

    # Footer
    c.setFont('Vazirmatn', 8)
    c.drawCentredString(width/2, 1*cm, fa_pdf("تولید شده توسط برنامه آزمون‌ساز احسان"))

    c.save()

def export_quiz_to_pdf(title, questions, output_path, include_answers=True):
    register_fonts()
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4

    def draw_header(canvas_obj, page_title):
        canvas_obj.setFont('Vazirmatn-Bold', 18)
        canvas_obj.drawCentredString(width/2, height - 2*cm, fa_pdf(page_title))
        canvas_obj.setFont('Vazirmatn', 10)
        canvas_obj.drawRightString(width - 2*cm, height - 3*cm, fa_pdf("طراح آزمون: احسان حسین زاده"))
        canvas_obj.line(2*cm, height - 3.5*cm, width - 2*cm, height - 3.5*cm)

    draw_header(c, title)

    y = height - 4.5*cm
    c.setFont('Vazirmatn', 12)

    for i, q in enumerate(questions, 1):
        if y < 4*cm:
            c.showPage()
            draw_header(c, title)
            y = height - 4.5*cm
            c.setFont('Vazirmatn', 12)

        q_text = f"{i}- {q.get('text', '')}"
        c.drawRightString(width - 2*cm, y, fa_pdf(q_text))
        y -= 0.7*cm

        for j, opt in enumerate(q.get('options', []), 1):
            opt_text = f"  {j}) {opt}"
            c.drawRightString(width - 3*cm, y, fa_pdf(opt_text))
            y -= 0.6*cm

        y -= 0.5*cm

    if include_answers:
        c.showPage()
        draw_header(c, "پاسخنامه - " + title)
        y = height - 4.5*cm
        c.setFont('Vazirmatn', 11)

        for i, q in enumerate(questions, 1):
            if y < 3*cm:
                c.showPage()
                draw_header(c, "پاسخنامه (ادامه)")
                y = height - 4.5*cm
                c.setFont('Vazirmatn', 11)

            ans_text = f"سوال {i}: "
            if q.get('qtype') in ('multiple_choice', 'true_false'):
                ans_text += f"گزینه {q.get('correct_index', 0) + 1}"
            else:
                ans_text += q.get('correct_text', '')

            c.drawRightString(width - 2*cm, y, fa_pdf(ans_text))
            y -= 0.6*cm

            if q.get('explanation'):
                exp_text = f"توضیح: {q['explanation']}"
                # Simple wrap for explanation
                if len(exp_text) > 90:
                    c.drawRightString(width - 3*cm, y, fa_pdf(exp_text[:90] + "..."))
                else:
                    c.drawRightString(width - 3*cm, y, fa_pdf(exp_text))
                y -= 0.6*cm
            y -= 0.4*cm

    c.save()
