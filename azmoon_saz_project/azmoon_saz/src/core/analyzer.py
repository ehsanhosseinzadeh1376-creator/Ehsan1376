"""
تحلیل عملکرد
Performance analyzer - identify weak topics, error-prone questions, study suggestions.
"""
import json
from collections import defaultdict
from typing import Dict, List

from data import database as db


def analyze_quiz(quiz_id: int) -> Dict:
    """Analyze all attempts for a specific quiz."""
    quiz = db.get_quiz(quiz_id)
    if not quiz:
        return {}

    questions = json.loads(quiz['questions'])
    attempts = db.list_attempts(quiz_id)

    total_attempts = len(attempts)
    if total_attempts == 0:
        return {
            'quiz_id': quiz_id,
            'title': quiz['title'],
            'total_attempts': 0,
            'avg_score': 0.0,
            'best_score': 0.0,
            'worst_score': 0.0,
            'topic_stats': [],
            'weakest_topics': [],
            'error_prone_questions': [],
            'suggestions': ['هنوز آزمونی تکمیل نشده. یک آزمون بده تا تحلیل انجام شود.'],
            'trend': [],
        }

    scores = [a['score'] for a in attempts]
    avg_score = sum(scores) / len(scores)

    # per-question stats across attempts
    q_wrong = defaultdict(int)
    q_total = defaultdict(int)
    topic_wrong = defaultdict(int)
    topic_total = defaultdict(int)

    for a in attempts:
        try:
            answers = json.loads(a['answers'])
        except Exception:
            continue
        for i, ans in enumerate(answers):
            q_total[i] += 1
            if i < len(questions):
                topic = questions[i].get('topic', '') or 'عمومی'
                topic_total[topic] += 1
                is_wrong = not ans.get('correct', False)
                if is_wrong:
                    q_wrong[i] += 1
                    topic_wrong[topic] += 1

    error_prone = []
    for i, q in enumerate(questions):
        total = q_total.get(i, 0)
        wrong = q_wrong.get(i, 0)
        if total > 0:
            err_rate = wrong / total
            error_prone.append({
                'index': i,
                'text': q.get('text', '')[:120],
                'topic': q.get('topic', ''),
                'wrong_count': wrong,
                'total': total,
                'error_rate': round(err_rate * 100, 1),
            })
    error_prone.sort(key=lambda x: -x['error_rate'])

    topic_stats = []
    for topic, tot in topic_total.items():
        wrong = topic_wrong.get(topic, 0)
        acc = (tot - wrong) / tot if tot else 0
        topic_stats.append({
            'topic': topic,
            'accuracy': round(acc * 100, 1),
            'wrong': wrong,
            'total': tot,
        })
    topic_stats.sort(key=lambda x: x['accuracy'])

    weakest = [t for t in topic_stats if t['accuracy'] < 70][:5]

    suggestions = _build_suggestions(avg_score, weakest, error_prone)

    trend = [{'date': a['created_at'], 'score': a['score']} for a in reversed(attempts)]

    return {
        'quiz_id': quiz_id,
        'title': quiz['title'],
        'total_attempts': total_attempts,
        'avg_score': round(avg_score, 1),
        'best_score': round(max(scores), 1),
        'worst_score': round(min(scores), 1),
        'topic_stats': topic_stats,
        'weakest_topics': weakest,
        'error_prone_questions': error_prone[:10],
        'suggestions': suggestions,
        'trend': trend,
    }


def analyze_global() -> Dict:
    """Analyze across all quizzes."""
    quizzes = db.list_quizzes()
    attempts = db.list_attempts()

    total_quizzes = len(quizzes)
    total_attempts = len(attempts)

    if total_attempts == 0:
        return {
            'total_quizzes': total_quizzes,
            'total_attempts': 0,
            'avg_score': 0.0,
            'topic_stats': [],
            'suggestions': ['هنوز داده‌ای برای تحلیل کلی وجود ندارد.'],
        }

    scores = [a['score'] for a in attempts]
    avg = sum(scores) / len(scores)

    # aggregate topic stats
    topic_wrong = defaultdict(int)
    topic_total = defaultdict(int)

    for a in attempts:
        quiz = db.get_quiz(a['quiz_id'])
        if not quiz:
            continue
        try:
            questions = json.loads(quiz['questions'])
            answers = json.loads(a['answers'])
        except Exception:
            continue
        for i, ans in enumerate(answers):
            if i < len(questions):
                topic = questions[i].get('topic', '') or 'عمومی'
                topic_total[topic] += 1
                if not ans.get('correct', False):
                    topic_wrong[topic] += 1

    topic_stats = []
    for topic, tot in topic_total.items():
        wrong = topic_wrong.get(topic, 0)
        acc = (tot - wrong) / tot if tot else 0
        topic_stats.append({
            'topic': topic,
            'accuracy': round(acc * 100, 1),
            'wrong': wrong,
            'total': tot,
        })
    topic_stats.sort(key=lambda x: x['accuracy'])

    weakest = [t for t in topic_stats if t['accuracy'] < 70][:5]
    suggestions = _build_suggestions(avg, weakest, [])

    return {
        'total_quizzes': total_quizzes,
        'total_attempts': total_attempts,
        'avg_score': round(avg, 1),
        'topic_stats': topic_stats,
        'weakest_topics': weakest,
        'suggestions': suggestions,
        'trend': [{'date': a['created_at'], 'score': a['score']} for a in reversed(attempts)],
    }


def _build_suggestions(avg_score: float, weakest_topics: List[Dict],
                      error_prone: List[Dict]) -> List[str]:
    tips = []
    if avg_score < 50:
        tips.append('میانگین نمره پایین است؛ پیشنهاد می‌شود درسنامه را دوباره با دقت مطالعه کن و ابتدا با سطح «آسان» تمرین را شروع کن.')
    elif avg_score < 75:
        tips.append('عملکرد متوسط داری. تمرکز روی مباحث ضعیف می‌تواند نمره را به‌سرعت بالا ببرد.')
    else:
        tips.append('عالی! می‌توانی سطح سختی را روی «سخت» بگذاری و سوالات چالشی‌تر تولید کنی.')

    if weakest_topics:
        names = '، '.join([t['topic'] for t in weakest_topics[:3]])
        tips.append(f'مباحث ضعیف اولویت‌دار برای مطالعه: {names}')

    if error_prone:
        tips.append(f'{len(error_prone[:3])} سوال به‌طور مکرر اشتباه پاسخ داده شده‌اند؛ در بخش تحلیل، توضیح پاسخ آنها را مرور کن.')

    tips.append('برای یادگیری پایدار، هر ۲۴ ساعت یک بار روی همان درسنامه آزمون جدید بگیر (فاصله‌گذاری یا Spaced Repetition).')
    return tips
