"""
پایگاه داده SQLite
SQLite database layer for quiz history and analytics
"""
import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path

APP_DIR = Path.home() / '.azmoon_saz'
APP_DIR.mkdir(exist_ok=True)
DB_PATH = APP_DIR / 'azmoon.db'
CONFIG_PATH = APP_DIR / 'config.json'


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            file_path TEXT,
            lesson_text TEXT,
            source_questions TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            title TEXT,
            questions TEXT,
            difficulty TEXT,
            creativity REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        );

        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            answers TEXT,
            score REAL,
            correct_count INTEGER,
            total INTEGER,
            duration_sec INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes(id)
        );

        CREATE TABLE IF NOT EXISTS question_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id INTEGER,
            question_index INTEGER,
            topic TEXT,
            wrong_count INTEGER DEFAULT 0,
            total_count INTEGER DEFAULT 0
        );
    ''')
    conn.commit()
    conn.close()


# ---------- Documents ----------
def save_document(title, file_path, lesson_text, source_questions):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'INSERT INTO documents (title, file_path, lesson_text, source_questions) VALUES (?, ?, ?, ?)',
        (title, file_path, lesson_text, json.dumps(source_questions, ensure_ascii=False))
    )
    conn.commit()
    doc_id = c.lastrowid
    conn.close()
    return doc_id


def list_documents():
    conn = get_conn()
    rows = conn.execute('SELECT * FROM documents ORDER BY created_at DESC').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_document(doc_id):
    conn = get_conn()
    r = conn.execute('SELECT * FROM documents WHERE id = ?', (doc_id,)).fetchone()
    conn.close()
    return dict(r) if r else None


def delete_document(doc_id):
    conn = get_conn()
    conn.execute('DELETE FROM documents WHERE id = ?', (doc_id,))
    conn.commit()
    conn.close()


# ---------- Quizzes ----------
def save_quiz(document_id, title, questions, difficulty, creativity):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'INSERT INTO quizzes (document_id, title, questions, difficulty, creativity) VALUES (?, ?, ?, ?, ?)',
        (document_id, title, json.dumps(questions, ensure_ascii=False), difficulty, creativity)
    )
    conn.commit()
    quiz_id = c.lastrowid
    conn.close()
    return quiz_id


def list_quizzes(document_id=None):
    conn = get_conn()
    if document_id:
        rows = conn.execute('SELECT * FROM quizzes WHERE document_id = ? ORDER BY created_at DESC', (document_id,)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM quizzes ORDER BY created_at DESC').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_quiz(quiz_id):
    conn = get_conn()
    r = conn.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    conn.close()
    return dict(r) if r else None


def delete_quiz(quiz_id):
    conn = get_conn()
    conn.execute('DELETE FROM quizzes WHERE id = ?', (quiz_id,))
    conn.execute('DELETE FROM attempts WHERE quiz_id = ?', (quiz_id,))
    conn.execute('DELETE FROM question_stats WHERE quiz_id = ?', (quiz_id,))
    conn.commit()
    conn.close()


# ---------- Attempts ----------
def save_attempt(quiz_id, answers, score, correct_count, total, duration_sec):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'INSERT INTO attempts (quiz_id, answers, score, correct_count, total, duration_sec) VALUES (?, ?, ?, ?, ?, ?)',
        (quiz_id, json.dumps(answers, ensure_ascii=False), score, correct_count, total, duration_sec)
    )
    conn.commit()
    attempt_id = c.lastrowid
    conn.close()
    return attempt_id


def list_attempts(quiz_id=None):
    conn = get_conn()
    if quiz_id:
        rows = conn.execute('SELECT * FROM attempts WHERE quiz_id = ? ORDER BY created_at DESC', (quiz_id,)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM attempts ORDER BY created_at DESC').fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_question_stats(quiz_id, question_index, topic, is_wrong):
    conn = get_conn()
    c = conn.cursor()
    row = c.execute(
        'SELECT id, wrong_count, total_count FROM question_stats WHERE quiz_id = ? AND question_index = ?',
        (quiz_id, question_index)
    ).fetchone()
    if row:
        c.execute(
            'UPDATE question_stats SET wrong_count = wrong_count + ?, total_count = total_count + 1 WHERE id = ?',
            (1 if is_wrong else 0, row['id'])
        )
    else:
        c.execute(
            'INSERT INTO question_stats (quiz_id, question_index, topic, wrong_count, total_count) VALUES (?, ?, ?, ?, 1)',
            (quiz_id, question_index, topic or '', 1 if is_wrong else 0)
        )
    conn.commit()
    conn.close()


def get_question_stats(quiz_id=None):
    conn = get_conn()
    if quiz_id:
        rows = conn.execute('SELECT * FROM question_stats WHERE quiz_id = ?', (quiz_id,)).fetchall()
    else:
        rows = conn.execute('SELECT * FROM question_stats').fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- Config ----------
def load_config():
    default = {
        'api_key': '',
        'base_url': 'https://api.openai.com/v1',
        'model': 'gpt-4o-mini',
        'use_g4f': True,
        'use_ollama': False,
        'ollama_url': 'http://localhost:11434',
        'ollama_model': 'qwen2.5:3b',
        'compat_reshape': True,
        'font_family': 'Vazirmatn',
        'ui_scale': 1.0,
        'first_run_done': False,
    }
    if not CONFIG_PATH.exists():
        return default
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        # Fill missing keys with defaults
        for k, v in default.items():
            cfg.setdefault(k, v)
        return cfg
    except Exception:
        return default


def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
