"""
صفحه کتابخانه
Library view.
"""
import json
import customtkinter as ctk
from tkinter import messagebox

from utils.persian_utils import fa, truncate, fa_textbox
from utils.font_loader import PERSIAN_FONT as FONT
from data import database as db


class LibraryView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color='#12141f')
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color='#181b2b', corner_radius=16)
        header.grid(row=0, column=0, sticky='ew', padx=24, pady=(24, 12))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=fa('کتابخانه من'),
                     font=(FONT, 22, 'bold'), text_color='#e6e8ef', anchor='e', justify='right'
                     ).grid(row=0, column=0, sticky='ew', padx=24, pady=(18, 4))
        ctk.CTkLabel(header,
                     text=fa('همه اسناد و آزمون‌های ذخیره‌شده'),
                     font=(FONT, 13), text_color='#a1a6bd', anchor='e', justify='right'
                     ).grid(row=1, column=0, sticky='ew', padx=24, pady=(0, 18))

        body = ctk.CTkFrame(self, fg_color='#12141f')
        body.grid(row=1, column=0, sticky='nsew', padx=24, pady=(0, 24))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # Documents card (right)
        doc_card = ctk.CTkFrame(body, fg_color='#181b2b', corner_radius=16)
        doc_card.grid(row=0, column=1, sticky='nsew', padx=(6, 0))
        doc_card.grid_columnconfigure(0, weight=1)
        doc_card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(doc_card, text=fa('📚 اسناد (PDF ها)'),
                     font=(FONT, 16, 'bold'), text_color='#7c93ff',
                     anchor='e', justify='right'
                     ).grid(row=0, column=0, sticky='ew', padx=20, pady=(16, 8))
        self.doc_list = ctk.CTkScrollableFrame(doc_card, fg_color='#0f1120', corner_radius=12)
        self.doc_list.grid(row=1, column=0, sticky='nsew', padx=16, pady=(0, 16))

        # Quizzes card (left)
        quiz_card = ctk.CTkFrame(body, fg_color='#181b2b', corner_radius=16)
        quiz_card.grid(row=0, column=0, sticky='nsew', padx=(0, 6))
        quiz_card.grid_columnconfigure(0, weight=1)
        quiz_card.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(quiz_card, text=fa('📝 آزمون‌ها'),
                     font=(FONT, 16, 'bold'), text_color='#e0568e',
                     anchor='e', justify='right'
                     ).grid(row=0, column=0, sticky='ew', padx=20, pady=(16, 8))
        self.quiz_list = ctk.CTkScrollableFrame(quiz_card, fg_color='#0f1120', corner_radius=12)
        self.quiz_list.grid(row=1, column=0, sticky='nsew', padx=16, pady=(0, 16))

    def on_show(self):
        self._refresh()

    def _refresh(self):
        for w in self.doc_list.winfo_children():
            w.destroy()
        for w in self.quiz_list.winfo_children():
            w.destroy()

        docs = db.list_documents()
        if not docs:
            ctk.CTkLabel(self.doc_list, text=fa('هنوز سندی ذخیره نشده'),
                         text_color='#8b91a5', font=(FONT, 13),
                         anchor='center', justify='center'
                         ).pack(pady=30)
        else:
            for d in docs:
                self._make_doc_row(d)

        quizzes = db.list_quizzes()
        if not quizzes:
            ctk.CTkLabel(self.quiz_list, text=fa('هنوز آزمونی ساخته نشده'),
                         text_color='#8b91a5', font=(FONT, 13),
                         anchor='center', justify='center'
                         ).pack(pady=30)
        else:
            for q in quizzes:
                self._make_quiz_row(q)

    def _make_doc_row(self, doc):
        row = ctk.CTkFrame(self.doc_list, fg_color='#181b2b', corner_radius=12)
        row.pack(fill='x', padx=8, pady=6)
        row.grid_columnconfigure(0, weight=1)

        title = truncate(doc.get('title', ''), 70)
        ctk.CTkLabel(row, text=fa(title), font=(FONT, 14, 'bold'),
                     text_color='#e6e8ef', anchor='e', justify='right'
                     ).grid(row=0, column=0, sticky='ew', padx=14, pady=(12, 4))

        try:
            source_qs = json.loads(doc.get('source_questions') or '[]')
        except Exception:
            source_qs = []
        lesson_len = len(doc.get('lesson_text') or '')
        meta = fa(f'📖 {lesson_len} کاراکتر درسنامه   •   ❓ {len(source_qs)} سوال شناسایی‌شده   •   ⏱ {doc.get("created_at", "")[:16]}')
        ctk.CTkLabel(row, text=meta, font=(FONT, 11), text_color='#8b91a5',
                     anchor='e', justify='right'
                     ).grid(row=1, column=0, sticky='ew', padx=14, pady=(0, 8))

        btns = ctk.CTkFrame(row, fg_color='transparent')
        btns.grid(row=2, column=0, sticky='e', padx=10, pady=(0, 12))

        ctk.CTkButton(btns, text=fa('🗑 حذف'), width=80, height=32, corner_radius=8,
                      font=(FONT, 12), fg_color='#4a2035', hover_color='#7a3055',
                      text_color='#ff9db0',
                      command=lambda d=doc: self._delete_doc(d)
                      ).pack(side='right', padx=4)

        ctk.CTkButton(btns, text=fa('➕ تولید آزمون جدید'), width=180, height=32, corner_radius=8,
                      font=(FONT, 12, 'bold'), fg_color='#4d68f2', hover_color='#3a54d9',
                      command=lambda d=doc: self._select_doc(d)
                      ).pack(side='right', padx=4)

    def _make_quiz_row(self, quiz):
        row = ctk.CTkFrame(self.quiz_list, fg_color='#181b2b', corner_radius=12)
        row.pack(fill='x', padx=8, pady=6)
        row.grid_columnconfigure(0, weight=1)

        title = truncate(quiz.get('title', ''), 70)
        ctk.CTkLabel(row, text=fa(title), font=(FONT, 14, 'bold'),
                     text_color='#e6e8ef', anchor='e', justify='right'
                     ).grid(row=0, column=0, sticky='ew', padx=14, pady=(12, 4))

        try:
            qs = json.loads(quiz.get('questions') or '[]')
        except Exception:
            qs = []
        attempts = db.list_attempts(quiz['id'])
        avg = sum(a['score'] for a in attempts) / len(attempts) if attempts else 0
        meta = fa(
            f'📝 {len(qs)} سوال   •   🎯 {quiz.get("difficulty", "-")}   •   '
            f'🎲 خلاقیت: {float(quiz.get("creativity") or 0):.2f}   •   '
            f'📊 {len(attempts)} تلاش - میانگین {avg:.1f}%'
        )
        ctk.CTkLabel(row, text=meta, font=(FONT, 11), text_color='#8b91a5',
                     anchor='e', justify='right'
                     ).grid(row=1, column=0, sticky='ew', padx=14, pady=(0, 8))

        btns = ctk.CTkFrame(row, fg_color='transparent')
        btns.grid(row=2, column=0, sticky='e', padx=10, pady=(0, 12))

        ctk.CTkButton(btns, text=fa('🗑 حذف'), width=80, height=32, corner_radius=8,
                      font=(FONT, 12), fg_color='#4a2035', hover_color='#7a3055',
                      text_color='#ff9db0',
                      command=lambda q=quiz: self._delete_quiz(q)
                      ).pack(side='right', padx=4)

        ctk.CTkButton(btns, text=fa('📊 تحلیل'), width=100, height=32, corner_radius=8,
                      font=(FONT, 12), fg_color='#22c58b', hover_color='#1ba374',
                      command=lambda q=quiz: self._analyze(q)
                      ).pack(side='right', padx=4)

        ctk.CTkButton(btns, text=fa('▶ شروع آزمون'), width=140, height=32, corner_radius=8,
                      font=(FONT, 12, 'bold'), fg_color='#e0568e', hover_color='#c73c74',
                      command=lambda q=quiz: self.app.open_quiz_view(q)
                      ).pack(side='right', padx=4)

    def _select_doc(self, doc):
        self.app.set_current_document(doc)
        pdf_view = self.app.views.get('pdf')
        if pdf_view:
            try:
                lesson = doc.get('lesson_text') or ''
                source_qs = json.loads(doc.get('source_questions') or '[]')
                pdf_view.separated = {'lesson': lesson, 'questions': source_qs}
                pdf_view.selected_pdf = doc.get('file_path') or doc.get('title')
                pdf_view.document_id = doc['id']
                pdf_view.file_label.configure(text=fa('سند انتخاب‌شده: ' + doc.get('title', '')))
                pdf_view.lesson_text.delete('1.0', 'end')
                pdf_view.lesson_text.insert('1.0', fa_textbox(lesson))
                pdf_view.source_text.delete('1.0', 'end')
                if source_qs:
                    for i, q in enumerate(source_qs, 1):
                        pdf_view.source_text.insert('end', fa_textbox(f'{i}) {q["text"]}') + '\n')
                pdf_view.btn_generate.configure(state='normal')
            except Exception as e:
                messagebox.showerror('خطا', f'خطای بارگذاری سند: {e}')
        self.app.show_view('pdf')

    def _delete_doc(self, doc):
        if messagebox.askyesno('حذف', 'سند حذف بشه؟ (آزمون‌های مرتبط تحت تأثیر قرار نمی‌گیرن.)'):
            db.delete_document(doc['id'])
            self._refresh()

    def _delete_quiz(self, quiz):
        if messagebox.askyesno('حذف', 'این آزمون و تمام نتایج‌ش حذف بشه؟'):
            db.delete_quiz(quiz['id'])
            self._refresh()

    def _analyze(self, quiz):
        self.app.set_current_quiz(quiz)
        self.app.show_view('dashboard')
