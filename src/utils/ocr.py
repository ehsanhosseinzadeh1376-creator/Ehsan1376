"""
ماژول OCR برای PDF های اسکن شده
OCR module for scanned PDFs
"""
import os
import shutil


def is_tesseract_available() -> bool:
    """Check if tesseract binary is installed on system"""
    return shutil.which('tesseract') is not None


def ocr_pdf(pdf_path: str, lang: str = 'fas+eng') -> str:
    """
    Extract text from a scanned PDF using OCR.
    Returns empty string if OCR is not available.
    """
    if not is_tesseract_available():
        return ''

    try:
        from pdf2image import convert_from_path
        import pytesseract
    except ImportError:
        return ''

    try:
        pages = convert_from_path(pdf_path, dpi=200)
    except Exception as e:
        print(f'[OCR] convert_from_path failed: {e}')
        return ''

    all_text = []
    for i, page_img in enumerate(pages):
        try:
            txt = pytesseract.image_to_string(page_img, lang=lang)
            all_text.append(txt)
        except pytesseract.TesseractError:
            # fallback to english if farsi language pack not installed
            try:
                txt = pytesseract.image_to_string(page_img, lang='eng')
                all_text.append(txt)
            except Exception:
                pass
        except Exception:
            pass

    return '\n\n'.join(all_text)
