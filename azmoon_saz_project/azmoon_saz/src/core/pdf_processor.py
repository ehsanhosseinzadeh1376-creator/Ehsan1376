"""
پردازش PDF
PDF processing - text extraction with OCR fallback
"""
import os

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from utils.ocr import ocr_pdf, is_tesseract_available
from utils.persian_utils import fix_persian_text


def extract_text_from_pdf(pdf_path: str, progress_callback=None) -> dict:
    """
    Extract text from a PDF file.
    Returns dict with:
      - text: full extracted text
      - pages: list of per-page text
      - method: 'text' | 'ocr' | 'mixed'
      - warnings: list of warning strings
    """
    result = {
        'text': '',
        'pages': [],
        'method': 'text',
        'warnings': []
    }

    if not os.path.exists(pdf_path):
        result['warnings'].append('فایل PDF پیدا نشد')
        return result

    if pdfplumber is None:
        result['warnings'].append('کتابخانه pdfplumber نصب نیست')
        return result

    pages_text = []
    empty_page_count = 0

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                if progress_callback:
                    progress_callback(i + 1, total, 'extract')
                try:
                    text = page.extract_text() or ''
                    text = fix_persian_text(text)
                except Exception:
                    text = ''
                pages_text.append(text)
                if not text.strip():
                    empty_page_count += 1
    except Exception as e:
        result['warnings'].append(f'خطای خواندن PDF: {e}')
        return result

    total_pages = len(pages_text) if pages_text else 1
    if empty_page_count > total_pages * 0.4:
        # Probably a scanned PDF - try OCR
        if is_tesseract_available():
            if progress_callback:
                progress_callback(0, total_pages, 'ocr')
            ocr_text = ocr_pdf(pdf_path)
            if ocr_text.strip():
                result['text'] = ocr_text
                result['pages'] = [p for p in ocr_text.split('\f') if p] or [ocr_text]
                result['method'] = 'ocr'
                result['warnings'].append('PDF اسکن‌شده تشخیص داده شد؛ متن با OCR استخراج شد.')
                return result
        else:
            result['warnings'].append(
                'به نظر می‌رسد PDF اسکن‌شده است. برای استخراج متن، Tesseract OCR را نصب کنید.'
            )

    result['text'] = '\n\n'.join(pages_text)
    result['pages'] = pages_text
    return result
