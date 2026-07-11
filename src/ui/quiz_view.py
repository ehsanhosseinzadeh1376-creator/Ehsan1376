"""
صفحه آزمون
Quiz taking screen.
"""
import json
import time
import customtkinter as ctk
from tkinter import messagebox

from utils.persian_utils import fa, fa_textbox
from utils.font_loader import PERSIAN_FONT as FONT
from data import database as db


class QuizView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color='#12141f')
        self.app = app
        self.quiz = None
        self.questions = []
        self.current_index = 0
        self.user_answers = []
        self.start_time = 0
        self.review_mode = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()
        self._build_footer()

    def on_show(self):
        quiz = self.app.current_quiz
        if not quiz:
            self._show_empty()
            return
        if self.quiz and self.quiz.get('id') == quiz.get('id') and not self.review_mode and self.user_answers:
            return
        self._load_quiz(quiz)

    def _build_header(self):
        self.header = ctk.CTkFrame(self, fg_color='#181b2b', corner_radius=16)
        self.header.grid(row=0, column=0, sticky='ew', padx=24, pady=(24, 12))
        self.header.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            self.header, text=fa('آزمون'),
            font=(FONT, 20, 'bold'), text_color='#e6e8ef', anchor='e', justify='right'
        )
        self.title_label.grid(row=0, column=0, sticky='ew', padx=24, pady=(18, 4))

        self.meta_label = ctk.CTkLabel(
            self.header, text='',
            font=(FONT, 13), text_color='#a1a6bd', anchor='e', justify='right'
        )
        self.meta_label.grid(row=1, column=0, sticky='ew', padx=24, pady=(0, 8))

        self.progress = ctk.CTkProgressBar(self.header, height=8, progress_color='#e0568e',
                                            corner_radius=4)
        self.progress.grid(row=2, column=0, sticky='ew', padx=24, pady=(0, 18))
        self.progress.set(0)

    def _build_body(self):
        self.body = ctk.CTkScrollableFrame(self, fg_color='#12141f')
        self.body.grid(row=1, column=0, sticky='nsew', padx=24)
        self.body.grid_columnconfigure(0, weight=1)

    def _build_footer(self):
        self.footer = ctk.CTkFrame(self, fg_color='#181b2b', corner_radius=16)
        self.footer.grid(row=2, column=0, sticky='ew', padx=24, pady=(12, 24))
        self.footer.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(self.footer, fg_color='transparent')
        left.grid(row=0, column=0, sticky='ew', padx=20, pady=14)
        left.grid_columnconfigure(0, weight=1)

        self.btn_prev = ctk.CTkButton(left, text=fa('◀ قبلی'), width=110, height=42,
                                      font=(FONT, 13, 'bold'), corner_radius=10,
                                      fg_color='#2a2f4a', hover_color='#3a4267',
                                      command=self._prev)
        self.btn_prev.pack(side='right', padx=6)

        self.btn_next = ctk.CTkButton(left, text=fa('بعدی ▶'), width=110, height=42,
                                      font=(FONT, 13, 'bold'), corner_radius=10,
                                      fg_color='#4d68f2', hover_color='#3a54d9',
                                      command=self._next)
        self.btn_next.pack(side='right', padx=6)

        self.btn_submit = ctk.CTkButton(left, text=fa('✅ پایان و ثبت آزمون'), width=200, height=42,
                                        font=(FONT, 13, 'bold'), corner_radius=10,
                                        fg_color='#22c58b', hover_color='#1ba374',
                                        command=self._submit)
        self.btn_submit.pack(side='right', padx=6)

        self.btn_go_dashboard = ctk.CTkButton(left, text=fa('📊 مشاهده تحلیل'), width=170, height=42,
                                              font=(FONT, 13, 'bold'), corner_radius=10,
                                              fg_color='#e0568e', hover_color='#c73c74',
                                              command=lambda: self.app.show_view('dashboard'))
        self.btn_go_dashboard.pack(side='right', padx=6)
        self.btn_go_dashboard.pack_forget()

    def _show_empty(self):
        for w in self.body.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.body, text=fa('هنوز آزمونی انتخاب نشده. از بخش کتابخانه یک آزمون انتخاب کن یا یک PDF جدید بارگذاری کن.'),
                     text_color='#a1a6bd', font=(FONT, 15), wraplength=900,
                     anchor='e', justify='right'
                     ).pack(pady=80, padx=24)
        self.title_label.configure(text=fa('آزمون'))
        self.meta_label.configure(text='')

    def _load_quiz(self, quiz):
        self.quiz = quiz
        try:
            self.questions = json.loads(quiz.get('questions') or '[]')
        except Exception:
            self.questions = []
        self.current_index = 0
        self.user_answers = [self._empty_answer() for _ in self.questions]
        self.start_time = time.time()
        self.review_mode = False
        self.btn_go_dashboard.pack_forget()
        self.btn_submit.configure(state='normal')

        self.title_label.configure(text=fa(quiz.get('title', 'آزمون')))
        self.meta_label.configure(text=fa(
            f'{len(self.questions)} سوال   •   دشواری: {quiz.get("difficulty", "-")}   •   خلاقیت: {float(quiz.get("creativity") or 0):.2f}'
        ))
        self._render_question()

    def _empty_answer(self):
        return {'selected_index': -1, 'selected_text': '', 'correct': False}

    def _render_question(self):
        for w in self.body.winfo_children():
            w.destroy()

        if not self.questions:
            self._show_empty()
            return

        idx = self.current_index
        q = self.questions[idx]
        self.progress.set((idx + 1) / len(self.questions))

        # Question header
        qhead = ctk.CTkFrame(self.body, fg_color='#181b2b', corner_radius=16)
        qhead.pack(fill='x', pady=(14, 10))
        qhead.grid_columnconfigure(0, weight=1)

        badge = ctk.CTkLabel(
            qhead,
            text=fa(f'سوال {idx + 1} از {len(self.questions)}   •   مبحث: {q.get("topic", "") or "عمومی"}   •   دشواری: {q.get("difficulty", "-")}'),
            font=(FONT, 12, 'bold'), text_color='#7c93ff', anchor='e', justify='right'
        )
        badge.grid(row=0, column=0, sticky='ew', padx=24, pady=(18, 6))

        qtext = ctk.CTkLabel(
            qhead, text=fa(q.get('text', '')),
            font=(FONT, 16, 'bold'), text_color='#e6e8ef', wraplength=1000,
            justify='right', anchor='e'
        )
        qtext.grid(row=1, column=0, sticky='ew', padx=24, pady=(0, 22))

        qtype = q.get('qtype', 'multiple_choice')
        options = q.get('options', [])

        # Render options
        opts_frame = ctk.CTkFrame(self.body, fg_color='transparent')
        opts_frame.pack(fill='x', pady=6)

        if qtype in ('multiple_choice', 'true_false') and options:
            self.answer_var = ctk.IntVar(value=self.user_answers[idx]['selected_index'])
            for i, opt in enumerate(options):
                is_correct = (i == q.get('correct_index', 0))
                sel = self.user_answers[idx]['selected_index']

                if self.review_mode:
                    if is_correct:
                        color = '#22c58b'; txt_color = '#0a0d1a'; prefix = '✅  '
                    elif sel == i:
                        color = '#e0568e'; txt_color = '#ffffff'; prefix = '❌  '
                    else:
                        color = '#2a2f4a'; txt_color = '#dfe2ec'; prefix = '        '
                    ctk.CTkLabel(
                        opts_frame, text=fa(prefix + opt),
                        font=(FONT, 14, 'bold' if is_correct else 'normal'),
                        text_color=txt_color, fg_color=color,
                        corner_radius=12, anchor='e', padx=22, pady=16, wraplength=920,
                        justify='right',
                    ).pack(fill='x', padx=8, pady=5)
                else:
                    row = ctk.CTkFrame(opts_frame, fg_color='#181b2b', corner_radius=12)
                    row.pack(fill='x', padx=8, pady=5)
                    rb = ctk.CTkRadioButton(
                        row, text=fa(opt),
                        variable=self.answer_var, value=i,
                        font=(FONT, 14), text_color='#dfe2ec',
                        fg_color='#4d68f2', hover_color='#3a54d9',
                        border_color='#4d68f2', border_width_checked=6,
                        command=lambda i=i, opt=opt, q=q: self._record_answer(i, opt, q)
                    )
                    rb.pack(anchor='e', padx=22, pady=14, fill='x')

        elif qtype in ('short_answer', 'descriptive'):
            self.answer_entry = ctk.CTkTextbox(opts_frame, height=140 if qtype == 'descriptive' else 70,
                                                font=(FONT, 14), fg_color='#181b2b',
                                                text_color='#dfe2ec', wrap='word',
                                                corner_radius=12)
            self.answer_entry.pack(fill='x', padx=8, pady=10)
            existing = self.user_answers[idx].get('selected_text', '')
            if existing:
                self.answer_entry.insert('1.0', existing)
            if self.review_mode:
                self.answer_entry.configure(state='disabled')
                correct_lbl = ctk.CTkLabel(
                    opts_frame,
                    text=fa('✅ پاسخ نمونه: ' + (q.get('correct_text') or '')),
                    font=(FONT, 14, 'bold'), text_color='#22c58b',
                    wraplength=900, justify='right', anchor='e', fg_color='#0f2018',
                    corner_radius=10, padx=18, pady=12
                )
                correct_lbl.pack(fill='x', padx=8, pady=6)
            else:
                def _save_text(event=None, q=q):
                    txt = self.answer_entry.get('1.0', 'end').strip()
                    correct = False
                    ct = (q.get('correct_text') or '').strip()
                    if ct and txt and (ct in txt or txt in ct):
                        correct = True
                    self.user_answers[idx] = {
                        'selected_index': -1,
                        'selected_text': txt,
                        'correct': correct,
                    }
                self.answer_entry.bind('<FocusOut>', _save_text)
                self.answer_entry.bind('<KeyRelease>', _save_text)

        # explanation in review mode
        if self.review_mode and q.get('explanation'):
            exp = ctk.CTkFrame(self.body, fg_color='#1a2440', corner_radius=12)
            exp.pack(fill='x', pady=(14, 4), padx=8)
            ctk.CTkLabel(exp, text=fa('💡 توضیح: ' + q.get('explanation', '')),
                         font=(FONT, 13), text_color='#a5b7ff',
                         wraplength=950, justify='right', anchor='e'
                         ).pack(fill='x', padx=20, pady=14)

        self.btn_prev.configure(state='normal' if idx > 0 else 'disabled')
        self.btn_next.configure(state='normal' if idx < len(self.questions) - 1 else 'disabled')

    def _record_answer(self, i, opt, q):
        idx = self.current_index
        correct = (i == q.get('correct_index', 0))
        self.user_answers[idx] = {
            'selected_index': i,
            'selected_text': opt,
            'correct': correct,
        }

    def _prev(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._render_question()

    def _next(self):
        if self.current_index < len(self.questions) - 1:
            self.current_index += 1
            self._render_question()

    def _submit(self):
        if not self.questions:
            return
        if self.review_mode:
            self.app.show_view('dashboard')
            return

        unanswered = sum(1 for a in self.user_answers if a['selected_index'] == -1 and not a['selected_text'])
        if unanswered > 0:
            if not messagebox.askyesno('توجه', f'{unanswered} سوال بی‌پاسخ مانده. آیا ادامه می‌دی؟'):
                return

        correct = sum(1 for a in self.user_answers if a['correct'])
        total = len(self.questions)
        score = (correct / total) * 100 if total else 0
        duration = int(time.time() - self.start_time)

        db.save_attempt(self.quiz['id'], self.user_answers, score, correct, total, duration)

        for i, a in enumerate(self.user_answers):
            q = self.questions[i] if i < len(self.questions) else {}
            db.update_question_stats(self.quiz['id'], i, q.get('topic', ''), not a['correct'])

        self.review_mode = True
        self.btn_submit.configure(state='disabled')
        self.btn_go_dashboard.pack(side='right', padx=6)

        messagebox.showinfo(
            'نتیجه',
            f'نمره شما: {score:.1f}%\nپاسخ صحیح: {correct} از {total}\nزمان: {duration} ثانیه'
        )
        self.current_index = 0
        self._render_question()
