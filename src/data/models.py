"""
مدل‌های داده
Data models (dataclasses) for questions and quizzes
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class Question:
    text: str
    options: List[str] = field(default_factory=list)  # for multiple-choice
    correct_index: int = 0  # index into options
    correct_text: str = ''  # for short-answer / descriptive
    explanation: str = ''
    topic: str = ''
    difficulty: str = 'متوسط'  # آسان / متوسط / سخت
    qtype: str = 'multiple_choice'  # multiple_choice / true_false / short_answer / descriptive

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return Question(
            text=d.get('text', ''),
            options=d.get('options', []),
            correct_index=d.get('correct_index', 0),
            correct_text=d.get('correct_text', ''),
            explanation=d.get('explanation', ''),
            topic=d.get('topic', ''),
            difficulty=d.get('difficulty', 'متوسط'),
            qtype=d.get('qtype', 'multiple_choice'),
        )
