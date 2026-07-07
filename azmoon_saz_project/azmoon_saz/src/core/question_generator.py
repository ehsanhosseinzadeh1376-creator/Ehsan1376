"""
تولید سوال با هوش مصنوعی
AI-powered question generator with multiple backends:
  1. g4f (free, no API key) - PRIMARY, built-in
  2. Ollama (local model, no key) - OPTIONAL local fallback
  3. OpenAI-compatible API (user key) - OPTIONAL
  4. Template-based Persian cloze questions - ULTIMATE FALLBACK
"""
import json
import random
import re
from typing import List, Dict, Optional

# --- Optional backends ---
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from g4f.client import Client as G4FClient
    HAS_G4F = True
except ImportError:
    HAS_G4F = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


SYSTEM_PROMPT = """
شما یک معلم و طراح سوال حرفه‌ای فارسی‌زبان هستید.
وظیفه شما تولید سوالات تألیفی جدید (نه کپی) بر اساس متن درسی داده‌شده است.

قوانین:
- سوالات باید کاملاً به فارسی روان و علمی باشند.
- برای هر سوال چهار گزینه بنویس (به‌جز نوع صحیح/غلط و تشریحی).
- گزینه‌های نادرست باید منطقی و نزدیک به پاسخ درست باشند (Distractors خوب).
- برای هر سوال «توضیح پاسخ» کوتاه بنویس تا دانش‌آموز یاد بگیرد.
- «مبحث» هر سوال را از متن استخراج کن (مثلاً «قانون اهم»، «مشتق»، «انقلاب مشروطه»).
- خروجی فقط JSON خالص باشد، بدون هیچ متن اضافه.
"""


def _build_user_prompt(lesson_text: str, count: int, difficulty: str,
                      qtype: str, existing_questions: List[str]) -> str:
    exist_str = ''
    if existing_questions:
        sample = existing_questions[:5]
        exist_str = '\n\nسوالاتی که قبلاً تولید شده‌اند (نباید تکرار شوند):\n' + '\n'.join(f'- {q}' for q in sample)

    qtype_desc = {
        'multiple_choice': 'چهار گزینه‌ای',
        'true_false': 'صحیح/غلط (دو گزینه: صحیح / غلط)',
        'short_answer': 'پاسخ کوتاه (بدون گزینه)',
        'descriptive': 'تشریحی (بدون گزینه)',
        'mixed': 'ترکیبی از چهارگزینه‌ای، صحیح/غلط و کوتاه‌پاسخ',
    }.get(qtype, 'چهار گزینه‌ای')

    schema_hint = '''
قالب دقیق JSON خروجی:
{
  "questions": [
    {
      "text": "متن سوال",
      "qtype": "multiple_choice | true_false | short_answer | descriptive",
      "options": ["گزینه 1", "گزینه 2", "گزینه 3", "گزینه 4"],
      "correct_index": 0,
      "correct_text": "برای سوالات تشریحی/کوتاه، پاسخ صحیح در این فیلد",
      "explanation": "توضیح چرا این پاسخ صحیح است",
      "topic": "عنوان مبحث",
      "difficulty": "آسان | متوسط | سخت"
    }
  ]
}
'''

    return f'''
متن درسنامه:
"""
{lesson_text[:6000]}
"""

لطفاً {count} سوال {qtype_desc} با سطح دشواری «{difficulty}» بساز.
حتماً از تنوع مبحثی استفاده کن و از تکرار خودداری کن.
{exist_str}

{schema_hint}
'''


def _extract_json(text: str) -> Optional[Dict]:
    """Extract JSON from LLM response (may have markdown fences)."""
    if not text:
        return None
    # Remove markdown code fences
    text = re.sub(r'^```(?:json)?\s*', '', text.strip(), flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r'\s*```\s*$', '', text.strip(), flags=re.MULTILINE)
    # Find first { ... last }
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1:
        return None
    candidate = text[start:end + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        # Try to fix common issues
        try:
            # remove trailing commas
            fixed = re.sub(r',\s*(}|])', r'\1', candidate)
            return json.loads(fixed)
        except Exception:
            return None


def _normalize_questions(questions: List[Dict], difficulty: str, qtype: str) -> List[Dict]:
    """Ensure all fields are present."""
    for q in questions:
        q.setdefault('options', [])
        q.setdefault('correct_index', 0)
        q.setdefault('correct_text', '')
        q.setdefault('explanation', '')
        q.setdefault('topic', '')
        q.setdefault('difficulty', difficulty)
        q.setdefault('qtype', qtype if qtype != 'mixed' else 'multiple_choice')
        # Clamp correct_index
        if q.get('options'):
            ci = q.get('correct_index', 0)
            if not isinstance(ci, int) or ci < 0 or ci >= len(q['options']):
                q['correct_index'] = 0
    return questions


def _template_fallback(lesson_text: str, count: int, difficulty: str) -> List[Dict]:
    """
    Offline fallback when no AI backend is available.
    Generates simple cloze-style Persian questions from meaningful sentences.
    """
    sents = re.split(r'(?<=[\.\!\?\؟\:])\s+|\n\n+', lesson_text)
    sents = [s.strip() for s in sents if len(s.strip()) > 40]

    if not sents:
        return []

    random.shuffle(sents)
    questions = []

    for sent in sents:
        if len(questions) >= count:
            break

        words = [w for w in re.findall(r'[\u0600-\u06FF]+', sent) if len(w) >= 4]
        if len(words) < 3:
            continue
        key = random.choice(words)
        blanked = sent.replace(key, ' ______ ', 1)

        pool = list({w for w in re.findall(r'[\u0600-\u06FF]+', lesson_text) if len(w) >= 4 and w != key})
        random.shuffle(pool)
        distractors = pool[:3] if len(pool) >= 3 else pool + ['گزینه نادرست ۱', 'گزینه نادرست ۲', 'گزینه نادرست ۳']
        distractors = distractors[:3]

        options = distractors + [key]
        random.shuffle(options)
        correct_idx = options.index(key)

        questions.append({
            'text': f'در جمله زیر جای خالی را کامل کنید:\n«{blanked}»',
            'qtype': 'multiple_choice',
            'options': options,
            'correct_index': correct_idx,
            'correct_text': key,
            'explanation': f'با توجه به متن اصلی، واژه صحیح «{key}» است.',
            'topic': 'درک متن',
            'difficulty': difficulty,
        })

    return questions


# =============================================================
# Backend implementations
# =============================================================

def _try_g4f(system: str, user: str, model: str = 'gpt-4o-mini',
             temperature: float = 0.7, timeout: int = 90) -> Optional[str]:
    """Try to use g4f (free, no key)."""
    if not HAS_G4F:
        return None
    try:
        client = G4FClient()
        # Try a couple of models in order of preference
        models_to_try = [model, 'gpt-4o-mini', 'gpt-4o', 'gemini-pro', 'claude-3-haiku']
        seen = set()
        for m in models_to_try:
            if m in seen:
                continue
            seen.add(m)
            try:
                resp = client.chat.completions.create(
                    model=m,
                    messages=[
                        {'role': 'system', 'content': system},
                        {'role': 'user', 'content': user},
                    ],
                    timeout=timeout,
                )
                content = resp.choices[0].message.content
                if content and len(content.strip()) > 20:
                    return content
            except Exception as e:
                print(f'[g4f {m}] failed: {e}')
                continue
    except Exception as e:
        print(f'[g4f] setup failed: {e}')
    return None


def _try_ollama(system: str, user: str, model: str = 'qwen2.5:3b',
                base_url: str = 'http://localhost:11434',
                temperature: float = 0.7, timeout: int = 120) -> Optional[str]:
    """Try local Ollama (if user has ollama running)."""
    if not HAS_REQUESTS:
        return None
    try:
        resp = requests.post(
            f'{base_url}/api/chat',
            json={
                'model': model,
                'messages': [
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': user},
                ],
                'stream': False,
                'options': {'temperature': temperature},
            },
            timeout=timeout,
        )
        if resp.status_code == 200:
            data = resp.json()
            return data.get('message', {}).get('content')
    except Exception as e:
        print(f'[ollama] failed: {e}')
    return None


def _try_openai(system: str, user: str, api_key: str, base_url: str,
                model: str, temperature: float = 0.7, timeout: int = 90) -> Optional[str]:
    """Try user-configured OpenAI-compatible API."""
    if not HAS_OPENAI or not api_key:
        return None
    try:
        client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user},
            ],
            temperature=temperature,
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f'[openai] failed: {e}')
    return None


# =============================================================
# Main generator
# =============================================================

class QuestionGenerator:
    """
    Multi-backend AI question generator with automatic fallback:
      1. g4f (built-in, free) — tried first
      2. Ollama (local, if user has it running) — second
      3. OpenAI-compatible API (if user provided key) — third
      4. Template (offline heuristic) — always available
    """

    def __init__(self, api_key: str = '', base_url: str = 'https://api.openai.com/v1',
                 model: str = 'gpt-4o-mini', use_g4f: bool = True,
                 use_ollama: bool = False, ollama_url: str = 'http://localhost:11434',
                 ollama_model: str = 'qwen2.5:3b'):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.use_g4f = use_g4f
        self.use_ollama = use_ollama
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model

    def has_any_ai(self) -> bool:
        return HAS_G4F or bool(self.api_key) or self.use_ollama

    def generate(self, lesson_text: str, count: int = 10, difficulty: str = 'متوسط',
                 qtype: str = 'multiple_choice', creativity: float = 0.7,
                 existing_questions: Optional[List[str]] = None,
                 progress_callback=None) -> Dict:
        """
        Generate questions with automatic backend fallback.
        Returns: { 'questions': [...], 'method': str, 'warnings': [] }
        """
        existing_questions = existing_questions or []
        warnings = []

        if not lesson_text or not lesson_text.strip():
            return {'questions': [], 'method': 'none', 'warnings': ['متن درسنامه خالی است.']}

        user_prompt = _build_user_prompt(lesson_text, count, difficulty, qtype, existing_questions)
        temperature = max(0.0, min(1.5, float(creativity)))

        # ---- 1. Try g4f (free, built-in) ----
        if self.use_g4f and HAS_G4F:
            if progress_callback:
                progress_callback('g4f', 'اتصال به هوش مصنوعی رایگان (g4f)...')
            content = _try_g4f(SYSTEM_PROMPT, user_prompt, self.model, temperature)
            if content:
                data = _extract_json(content)
                if data and data.get('questions'):
                    qs = _normalize_questions(data['questions'], difficulty, qtype)
                    return {'questions': qs, 'method': 'g4f (رایگان)', 'warnings': warnings}
                else:
                    warnings.append('پاسخ g4f قابل تجزیه نبود.')
            else:
                warnings.append('اتصال به هوش مصنوعی رایگان (g4f) موفق نبود.')

        # ---- 2. Try Ollama (local) ----
        if self.use_ollama:
            if progress_callback:
                progress_callback('ollama', f'اتصال به Ollama محلی ({self.ollama_model})...')
            content = _try_ollama(SYSTEM_PROMPT, user_prompt, self.ollama_model,
                                   self.ollama_url, temperature)
            if content:
                data = _extract_json(content)
                if data and data.get('questions'):
                    qs = _normalize_questions(data['questions'], difficulty, qtype)
                    return {'questions': qs, 'method': f'ollama ({self.ollama_model})', 'warnings': warnings}
                else:
                    warnings.append('پاسخ Ollama قابل تجزیه نبود.')
            else:
                warnings.append('Ollama در دسترس نیست (روی localhost:11434 در حال اجرا نیست؟).')

        # ---- 3. Try user-configured API ----
        if self.api_key:
            if progress_callback:
                progress_callback('openai', f'اتصال به API شخصی ({self.model})...')
            content = _try_openai(SYSTEM_PROMPT, user_prompt, self.api_key,
                                    self.base_url, self.model, temperature)
            if content:
                data = _extract_json(content)
                if data and data.get('questions'):
                    qs = _normalize_questions(data['questions'], difficulty, qtype)
                    return {'questions': qs, 'method': f'API شخصی ({self.model})', 'warnings': warnings}
                else:
                    warnings.append('پاسخ API قابل تجزیه نبود.')
            else:
                warnings.append('اتصال به API شخصی موفق نبود.')

        # ---- 4. Template fallback ----
        if progress_callback:
            progress_callback('template', 'استفاده از تولید قالبی (بدون AI)...')
        qs = _template_fallback(lesson_text, count, difficulty)
        if not qs:
            warnings.append('متن کافی برای تولید سوال قالبی وجود ندارد.')
        warnings.append('هوش مصنوعی در دسترس نبود؛ سوالات با روش قالبی ساخته شدند.')
        return {'questions': qs, 'method': 'قالبی (آفلاین)', 'warnings': warnings}
