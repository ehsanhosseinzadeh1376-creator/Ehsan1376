"""
تفکیک درسنامه از سوالات
Separate lesson content from existing questions in a PDF.
"""
import re
from typing import List, Dict, Tuple

# Persian-friendly question markers
QUESTION_START_PATTERNS = [
    r'^\s*(?:سوال|سؤال|پرسش|تست|تمرین|مسئله)\s*[:\-\)ـ\s]*\d+',
    r'^\s*\d+\s*[\-\.\)ـ]\s*(?=\S)',            # 1. or 1) or 1-
    r'^\s*[\(\-]?\s*\d+\s*[\)\-]',                # (1) or -1-
    r'^\s*Q\d+',
    r'^\s*Question\s*\d+',
]

OPTION_PATTERN = re.compile(
    r'(?:^|\s)(?:[\(\-]?\s*(?:[۱۲۳۴1234الفبجدab])\s*[\)\-\.ـ]|\bگزینه\s*[۱۲۳۴1234الفبجد])',
    re.MULTILINE
)

ANSWER_KEY_PATTERN = re.compile(
    r'(پاسخنامه|پاسخ\s*نامه|کلید\s*سوال(?:ها|ات)?|کلید\s*پاسخ|answers?\s*key)',
    re.IGNORECASE
)

LESSON_MARKERS = [
    r'(?:درسنامه|درس|فصل|بخش|مبحث|مقدمه|تعریف|نکته|قضیه|قانون|فرمول)',
]


def _looks_like_question_line(line: str) -> bool:
    for pat in QUESTION_START_PATTERNS:
        if re.match(pat, line):
            return True
    return False


def _count_options(block: str) -> int:
    return len(OPTION_PATTERN.findall(block))


def separate_content(full_text: str) -> Dict:
    """
    Split text into 'lesson' (theory) parts and detected 'questions'.
    Returns:
      { 'lesson': str, 'questions': [ {text, options, ...}, ... ] }
    Heuristic-based; robust to noisy Persian PDFs.
    """
    if not full_text or not full_text.strip():
        return {'lesson': '', 'questions': []}

    lines = full_text.split('\n')
    lesson_lines: List[str] = []
    question_blocks: List[str] = []

    current_block: List[str] = []
    in_question = False
    in_answer_key = False

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            if in_question and current_block:
                # continue collecting; empty line is soft separator
                current_block.append('')
            else:
                lesson_lines.append('')
            continue

        if ANSWER_KEY_PATTERN.search(line):
            in_answer_key = True
            if in_question and current_block:
                question_blocks.append('\n'.join(current_block).strip())
                current_block = []
                in_question = False
            continue

        if in_answer_key:
            # keep the answer key out of lesson
            continue

        if _looks_like_question_line(line):
            if in_question and current_block:
                question_blocks.append('\n'.join(current_block).strip())
                current_block = []
            in_question = True
            current_block.append(line)
        else:
            if in_question:
                current_block.append(line)
                # heuristic: if block is quite long without options, might be lesson resuming
                if len(current_block) > 25 and _count_options('\n'.join(current_block)) == 0:
                    lesson_lines.extend(current_block)
                    current_block = []
                    in_question = False
            else:
                lesson_lines.append(line)

    if in_question and current_block:
        question_blocks.append('\n'.join(current_block).strip())

    # Post-process question blocks - parse options
    parsed_questions = []
    for qb in question_blocks:
        parsed = _parse_question_block(qb)
        if parsed and parsed.get('text'):
            parsed_questions.append(parsed)

    lesson_text = '\n'.join(lesson_lines).strip()

    # If we detected very few questions and text has lots of numbers, fall back to lesson-only
    if len(parsed_questions) < 1 and len(full_text) > 200:
        lesson_text = full_text

    return {
        'lesson': lesson_text,
        'questions': parsed_questions,
    }


def _parse_question_block(block: str) -> Dict:
    """Split a question block into question text and options if present."""
    lines = [l.strip() for l in block.split('\n') if l.strip()]
    if not lines:
        return {}

    text_lines = []
    options = []
    option_re = re.compile(r'^\s*[\(\-]?\s*(?:[۱۲۳۴1234]|[الفبجد]|[abcdABCD])\s*[\)\-\.ـ]\s*(.+)')

    for line in lines:
        m = option_re.match(line)
        if m:
            options.append(m.group(1).strip())
        else:
            text_lines.append(line)

    # Clean the question number from the first line
    qtext = ' '.join(text_lines)
    qtext = re.sub(r'^\s*(?:سوال|سؤال|پرسش|تست|تمرین)\s*[:\-\)ـ\s]*\d+\s*[:\-ـ]*\s*', '', qtext)
    qtext = re.sub(r'^\s*\d+\s*[\-\.\)ـ]\s*', '', qtext)

    return {
        'text': qtext.strip(),
        'options': options,
        'source': 'pdf',
    }
