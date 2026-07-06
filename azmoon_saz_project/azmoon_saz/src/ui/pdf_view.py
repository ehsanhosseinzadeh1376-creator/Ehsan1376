"""
صفحه بارگذاری PDF و تولید سوال
PDF upload + question generation screen.
"""
import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox

from utils.persian_utils import fa, fa_textbox
from utils.font_loader import PERSIAN_FONT as FONT
from core.pdf_processor import extract_text_from_pdf
from core.content_separator import separate_content
from core.question_generator import QuestionGenerator
from data import database as db
from utils.pdf_exporter import export_lesson_to_pdf


class PdfView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color='#12141f')
        self.app = app
        self.selected_pdf = None
        self.extracted = None
        self.separated = None
        self.document_id = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_body()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color='#181b2b', corner_radius=16)
        header.grid(row=0, column=0, sticky='ew', padx=24, pady=(24, 12))
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header, text=fa('بارگذاری PDF و تولید سوال'),
            font=(FONT, 22, 'bold'), text_color='#e6e8ef', anchor='e', justify='right'
        )
        title.grid(row=0, column=0, sticky='ew', padx=24, pady=(18, 4))

        subtitle = ctk.CTkLabel(
            header,
            text=fa('یک PDF درسی انتخاب کن، درسنامه و سوالات خودکار جدا می‌شن، بعد با هوش مصنوعی سوال تألیفی تولید کن.'),
            font=(FONT, 13), text_color='#a1a6bd', wraplength=1000, anchor='e', justify='right'
        )
        subtitle.grid(row=1, column=0, sticky='ew', padx=24, pady=(0, 18))

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color='#12141f')
        body.grid(row=1, column=0, sticky='nsew', padx=24, pady=(0, 24))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(1, weight=1)

        # Upload card
        upload_card = ctk.CTkFrame(body, fg_color='#181b2b', corner_radius=16)
        upload_card.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 12))
        upload_card.grid_columnconfigure(0, weight=1)

        self.file_label = ctk.CTkLabel(
            upload_card, text=fa('هنوز فایلی انتخاب نشده'),
            font=(FONT, 14), text_color='#a1a6bd', anchor='e', justify='right'
        )
        self.file_label.grid(row=0, column=0, sticky='ew', padx=24, pady=(20, 10))

        btn_row = ctk.CTkFrame(upload_card, fg_color='transparent')
        btn_row.grid(row=1, column=0, sticky='e', padx=18, pady=(0, 18))

        self.btn_choose = ctk.CTkButton(
            btn_row, text=fa('📂 انتخاب فایل PDF'),
            font=(FONT, 14, 'bold'), height=44, corner_radius=12, width=180,
            fg_color='#4d68f2', hover_color='#3a54d9',
            command=self.choose_file
        )
        self.btn_choose.pack(side='right', padx=6)

        self.btn_extract = ctk.CTkButton(
            btn_row, text=fa('✂️ استخراج و تفکیک متن'),
            font=(FONT, 14, 'bold'), height=44, corner_radius=12, width=220,
            fg_color='#22c58b', hover_color='#1ba374',
            state='disabled', command=self.extract_pdf
        )
        self.btn_extract.pack(side='right', padx=6)

        self.btn_export_lesson = ctk.CTkButton(
            btn_row, text=fa('📄 خروجی PDF درسنامه'),
            font=(FONT, 14, 'bold'), height=44, corner_radius=12, width=200,
            fg_color='#f2a44d', hover_color='#d68a37',
            state='disabled', command=self.export_lesson
        )
        self.btn_export_lesson.pack(side='right', padx=6)

        self.progress = ctk.CTkProgressBar(upload_card, height=8, corner_radius=4)
        self.progress.grid(row=2, column=0, sticky='ew', padx=24, pady=(0, 16))
        self.progress.set(0)

        # Lesson panel (right - drasname)
        self.lesson_panel = ctk.CTkFrame(body, fg_color='#181b2b', corner_radius=16)
        self.lesson_panel.grid(row=1, column=1, sticky='nsew', padx=(6, 0))
        self.lesson_panel.grid_rowconfigure(1, weight=1)
        self.lesson_panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.lesson_panel, text=fa('📖 درسنامه استخراج‌شده'),
                     font=(FONT, 16, 'bold'), text_color='#7c93ff', anchor='e', justify='right'
                     ).grid(row=0, column=0, sticky='ew', padx=18, pady=(16, 8))
        # NOTE: For textboxes with Persian, DO NOT reshape - use raw text with proper font
        self.lesson_text = ctk.CTkTextbox(self.lesson_panel, font=(FONT, 13),
                                          fg_color='#0f1120', text_color='#dfe2ec',
                                          wrap='word', corner_radius=10)
        self.lesson_text.grid(row=1, column=0, sticky='nsew', padx=16, pady=(0, 16))

        # Questions panel (left - detected questions)
        self.source_panel = ctk.CTkFrame(body, fg_color='#181b2b', corner_radius=16)
        self.source_panel.grid(row=1, column=0, sticky='nsew', padx=(0, 6))
        self.source_panel.grid_rowconfigure(1, weight=1)
        self.source_panel.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.source_panel, text=fa('❓ سوالات موجود در PDF'),
                     font=(FONT, 16, 'bold'), text_color='#f2a44d', anchor='e', justify='right'
                     ).grid(row=0, column=0, sticky='ew', padx=18, pady=(16, 8))
        self.source_list = ctk.CTkScrollableFrame(self.source_panel, fg_color='#0f1120', corner_radius=10)
        self.source_list.grid(row=1, column=0, sticky='nsew', padx=16, pady=(0, 8))
        self.question_vars = []

        self.btn_create_quiz = ctk.CTkButton(
            self.source_panel, text=fa('📝 ساخت آزمون از سوالات انتخابی'),
            font=(FONT, 13, 'bold'), height=36, corner_radius=10,
            fg_color='#4d68f2', hover_color='#3a54d9',
            state='disabled', command=self.create_quiz_from_selection
        )
        self.btn_create_quiz.grid(row=2, column=0, sticky='ew', padx=16, pady=(0, 16))

        # Generation controls
        gen_card = ctk.CTkFrame(body, fg_color='#181b2b', corner_radius=16)
        gen_card.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(12, 0))
        gen_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(gen_card, text=fa('🤖 تولید سوال تألیفی با هوش مصنوعی'),
                     font=(FONT, 16, 'bold'), text_color='#7c93ff', anchor='e', justify='right'
                     ).grid(row=0, column=0, sticky='ew', padx=24, pady=(18, 10))

        controls = ctk.CTkFrame(gen_card, fg_color='transparent')
        controls.grid(row=1, column=0, sticky='ew', padx=18, pady=(0, 10))
        for i in range(5):
            controls.grid_columnconfigure(i, weight=1)

        # count (col 4 = rightmost)
        ctk.CTkLabel(controls, text=fa('تعداد سوالات'), font=(FONT, 12, 'bold'),
                     text_color='#dfe2ec', anchor='e').grid(row=0, column=4, sticky='ew', padx=8, pady=(4, 4))
        self.count_var = ctk.StringVar(value='10')
        self.count_entry = ctk.CTkEntry(controls, textvariable=self.count_var,
                                        height=38, justify='center', font=(FONT, 14, 'bold'))
        self.count_entry.grid(row=1, column=4, padx=8, pady=6, sticky='ew')

        # difficulty
        ctk.CTkLabel(controls, text=fa('سطح دشواری'), font=(FONT, 12, 'bold'),
                     text_color='#dfe2ec', anchor='e').grid(row=0, column=3, sticky='ew', padx=8, pady=(4, 4))
        self.difficulty = ctk.CTkOptionMenu(
            controls, values=[fa('آسان'), fa('متوسط'), fa('سخت')],
            height=38, font=(FONT, 13),
            fg_color='#2a2f4a', button_color='#4d68f2', button_hover_color='#3a54d9'
        )
        self.difficulty.set(fa('متوسط'))
        self.difficulty.grid(row=1, column=3, padx=8, pady=6, sticky='ew')

        # type
        ctk.CTkLabel(controls, text=fa('نوع سوال'), font=(FONT, 12, 'bold'),
                     text_color='#dfe2ec', anchor='e').grid(row=0, column=2, sticky='ew', padx=8, pady=(4, 4))
        self.qtype = ctk.CTkOptionMenu(
            controls,
            values=[fa('چهار گزینه‌ای'), fa('صحیح/غلط'), fa('پاسخ کوتاه'), fa('تشریحی'), fa('ترکیبی')],
            height=38, font=(FONT, 13),
            fg_color='#2a2f4a', button_color='#4d68f2', button_hover_color='#3a54d9'
        )
        self.qtype.set(fa('چهار گزینه‌ای'))
        self.qtype.grid(row=1, column=2, padx=8, pady=6, sticky='ew')

        # creativity
        ctk.CTkLabel(controls, text=fa('خلاقیت'), font=(FONT, 12, 'bold'),
                     text_color='#dfe2ec', anchor='e').grid(row=0, column=1, sticky='ew', padx=8, pady=(4, 4))
        creativity_wrap = ctk.CTkFrame(controls, fg_color='transparent')
        creativity_wrap.grid(row=1, column=1, padx=8, pady=6, sticky='ew')
        creativity_wrap.grid_columnconfigure(0, weight=1)
        self.creativity_var = ctk.DoubleVar(value=0.7)
        self.creativity_slider = ctk.CTkSlider(creativity_wrap, from_=0.0, to=1.2,
                                                variable=self.creativity_var,
                                                number_of_steps=24,
                                                progress_color='#4d68f2',
                                                button_color='#7c93ff',
                                                button_hover_color='#a5b7ff')
        self.creativity_slider.grid(row=0, column=0, sticky='ew')
        self.creativity_label = ctk.CTkLabel(creativity_wrap, text='0.70', font=(FONT, 11, 'bold'),
                                              text_color='#7c93ff')
        self.creativity_label.grid(row=1, column=0, sticky='ew', pady=(2, 0))
        self.creativity_var.trace_add('write', lambda *_: self.creativity_label.configure(
            text=f'{self.creativity_var.get():.2f}'))

        # generate button (col 0 = leftmost, biggest)
        self.btn_generate = ctk.CTkButton(
            controls, text=fa('✨ تولید سوال'),
            font=(FONT, 15, 'bold'), height=52, corner_radius=12,
            fg_color='#e0568e', hover_color='#c73c74',
            state='disabled', command=self.generate_questions
        )
        self.btn_generate.grid(row=0, column=0, rowspan=2, padx=10, pady=6, sticky='ew')

        # status
        self.status_label = ctk.CTkLabel(
            gen_card, text='', font=(FONT, 13), text_color='#a1a6bd',
            anchor='e', wraplength=1200, justify='right'
        )
        self.status_label.grid(row=2, column=0, sticky='ew', padx=24, pady=(4, 16))

    # ------------- Actions -------------
    def choose_file(self):
        path = filedialog.askopenfilename(
            title='Select PDF File',
            filetypes=[('PDF Files', '*.pdf')]
        )
        if not path:
            return
        self.selected_pdf = path
        self.file_label.configure(text=fa('فایل انتخاب‌شده: ' + os.path.basename(path)))
        self.btn_extract.configure(state='normal')
        self.btn_generate.configure(state='disabled')
        self.btn_export_lesson.configure(state='disabled')
        self.btn_create_quiz.configure(state='disabled')
        self.lesson_text.delete('1.0', 'end')
        for w in self.source_list.winfo_children():
            w.destroy()
        self.status_label.configure(text='')

    def extract_pdf(self):
        if not self.selected_pdf:
            return
        self.btn_extract.configure(state='disabled', text=fa('در حال پردازش...'))
        self.progress.set(0)
        self.status_label.configure(text=fa('استخراج متن از PDF...'))

        def worker():
            try:
                def cb(cur, tot, phase):
                    self.after(0, lambda: self.progress.set(cur / max(tot, 1)))

                self.extracted = extract_text_from_pdf(self.selected_pdf, progress_callback=cb)
                if not self.extracted.get('text'):
                    self.after(0, lambda: self.status_label.configure(
                        text=fa('⚠️ متنی از PDF استخراج نشد. اگر PDF اسکن‌شده است، Tesseract OCR را نصب کنید.'),
                        text_color='#ff8080'
                    ))
                    return
                self.separated = separate_content(self.extracted['text'])
                self.after(0, self._render_extracted)
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda m=err_msg: self.status_label.configure(
                    text=fa(f'خطا: {m}'), text_color='#ff8080'))
            finally:
                self.after(0, lambda: self.btn_extract.configure(
                    state='normal', text=fa('✂️ استخراج و تفکیک متن')))

        threading.Thread(target=worker, daemon=True).start()

    def _render_extracted(self):
        self.progress.set(1.0)

        lesson = self.separated.get('lesson', '') or ''
        questions = self.separated.get('questions', [])

        # Textbox content: ALWAYS reshape (Text widget doesn't do RTL natively on any platform)
        self.lesson_text.delete('1.0', 'end')
        if lesson.strip():
            self.lesson_text.insert('1.0', fa_textbox(lesson))
            self.btn_export_lesson.configure(state='normal')
        else:
            self.lesson_text.insert('1.0', fa_textbox('درسنامه مشخصی تشخیص داده نشد.'))
            self.btn_export_lesson.configure(state='disabled')

        for w in self.source_list.winfo_children():
            w.destroy()
        self.question_vars = []
        if questions:
            for i, q in enumerate(questions):
                var = ctk.BooleanVar(value=True)
                self.question_vars.append(var)

                q_frame = ctk.CTkFrame(self.source_list, fg_color='transparent')
                q_frame.pack(fill='x', pady=2)

                cb = ctk.CTkCheckBox(q_frame, text=fa(f'{i+1}) {q["text"][:60]}...'),
                                     variable=var, font=(FONT, 12), anchor='e', justify='right')
                cb.pack(side='right', padx=5, fill='x', expand=True)
            self.btn_create_quiz.configure(state='normal')
        else:
            ctk.CTkLabel(self.source_list, text=fa('سوالی شناسایی نشد.'), font=(FONT, 12)).pack(pady=20)
            self.btn_create_quiz.configure(state='disabled')

        # Save document
        title = os.path.basename(self.selected_pdf)
        self.document_id = db.save_document(title, self.selected_pdf, lesson, questions)
        self.app.set_current_document(db.get_document(self.document_id))

        method = self.extracted.get('method', 'text')
        warns = self.extracted.get('warnings', [])
        info = fa(f'✅ {len(questions)} سوال شناسایی شد. روش استخراج: {method}. سند در کتابخانه ذخیره شد.')
        if warns:
            info += '  ' + fa(' | '.join(warns))
        self.status_label.configure(text=info, text_color='#22c58b')

        self.btn_generate.configure(state='normal')

    def export_lesson(self):
        if not self.separated or not self.separated.get('lesson'):
            return
        path = filedialog.asksaveasfilename(
            defaultextension='.pdf',
            filetypes=[('PDF Files', '*.pdf')],
            initialfile=f"Lesson_{os.path.basename(self.selected_pdf)}.pdf"
        )
        if not path:
            return
        try:
            export_lesson_to_pdf(f"درسنامه: {os.path.basename(self.selected_pdf)}",
                                 self.separated['lesson'], path)
            messagebox.showinfo('موفق', 'درسنامه با موفقیت صادر شد.')
        except Exception as e:
            messagebox.showerror('خطا', f'خطا در صدور PDF: {e}')

    def create_quiz_from_selection(self):
        if not self.separated or not self.separated.get('questions'):
            return

        selected_questions = []
        for i, var in enumerate(self.question_vars):
            if var.get():
                selected_questions.append(self.separated['questions'][i])

        if not selected_questions:
            messagebox.showwarning('توجه', 'لطفاً حداقل یک سوال را انتخاب کنید.')
            return

        title = f'آزمون انتخابی از {os.path.basename(self.selected_pdf)}'
        quiz_id = db.save_quiz(self.document_id, title, selected_questions, 'انتخابی', 0.0)
        quiz = db.get_quiz(quiz_id)
        self.app.set_current_quiz(quiz)
        if messagebox.askyesno('آماده', f'آزمون با {len(selected_questions)} سوال ساخته شد. شروع می‌کنی؟'):
            self.app.open_quiz_view(quiz)

    def generate_questions(self):
        if not self.separated:
            return
        lesson = self.separated.get('lesson', '')
        if not lesson.strip():
            messagebox.showwarning('توجه', 'درسنامه‌ای برای تولید سوال وجود ندارد.')
            return

        try:
            count = int(self.count_var.get())
            if count < 1 or count > 50:
                raise ValueError
        except ValueError:
            messagebox.showwarning('توجه', 'تعداد سوالات باید عددی بین ۱ تا ۵۰ باشد.')
            return

        diff_display = self.difficulty.get()
        difficulty_map = {fa('آسان'): 'آسان', fa('متوسط'): 'متوسط', fa('سخت'): 'سخت'}
        difficulty = difficulty_map.get(diff_display, 'متوسط')

        qtype_display = self.qtype.get()
        qtype_map = {
            fa('چهار گزینه‌ای'): 'multiple_choice',
            fa('صحیح/غلط'): 'true_false',
            fa('پاسخ کوتاه'): 'short_answer',
            fa('تشریحی'): 'descriptive',
            fa('ترکیبی'): 'mixed',
        }
        qtype = qtype_map.get(qtype_display, 'multiple_choice')

        creativity = float(self.creativity_var.get())

        self.btn_generate.configure(state='disabled', text=fa('در حال تولید...'))
        self.status_label.configure(text=fa('در حال ارسال به مدل هوش مصنوعی...'),
                                    text_color='#a1a6bd')

        def worker():
            cfg = db.load_config()
            gen = QuestionGenerator(
                api_key=cfg.get('api_key', ''),
                base_url=cfg.get('base_url', 'https://api.openai.com/v1'),
                model=cfg.get('model', 'gpt-4o-mini'),
                use_g4f=cfg.get('use_g4f', True),
                use_ollama=cfg.get('use_ollama', False),
                ollama_url=cfg.get('ollama_url', 'http://localhost:11434'),
                ollama_model=cfg.get('ollama_model', 'qwen2.5:3b'),
            )
            existing = [q.get('text', '') for q in self.separated.get('questions', [])]

            def cb(phase, msg):
                self.after(0, lambda: self.status_label.configure(text=fa(msg)))

            result = gen.generate(
                lesson_text=lesson, count=count, difficulty=difficulty,
                qtype=qtype, creativity=creativity,
                existing_questions=existing, progress_callback=cb,
            )

            questions = result.get('questions', [])
            method = result.get('method', 'template')
            warnings = result.get('warnings', [])

            if not questions:
                warn_msg = ' | '.join(warnings)
                self.after(0, lambda w=warn_msg: self.status_label.configure(
                    text=fa(f'❌ هیچ سوالی تولید نشد. {w}'), text_color='#ff8080'))
                self.after(0, lambda: self.btn_generate.configure(
                    state='normal', text=fa('✨ تولید سوال')))
                return

            title = f'آزمون از {os.path.basename(self.selected_pdf)}'
            quiz_id = db.save_quiz(self.document_id, title, questions, difficulty, creativity)
            quiz = db.get_quiz(quiz_id)
            self.app.set_current_quiz(quiz)

            def ui_done():
                icon = '🤖'
                if 'g4f' in method: icon = '🎁'
                elif 'ollama' in method: icon = '💻'
                elif 'API' in method: icon = '🔑'
                elif 'قالبی' in method: icon = '🧩'
                msg = fa(f'{icon} {len(questions)} سوال تولید شد (روش: {method}). آزمون در کتابخانه ذخیره شد.')
                if warnings:
                    msg += ' ' + fa(' | '.join(warnings))
                self.status_label.configure(text=msg, text_color='#22c58b')
                self.btn_generate.configure(state='normal', text=fa('✨ تولید سوال'))
                if messagebox.askyesno('آماده', 'سوالات تولید شدند. الان آزمون رو شروع می‌کنی؟'):
                    self.app.open_quiz_view(quiz)

            self.after(0, ui_done)

        threading.Thread(target=worker, daemon=True).start()

    def on_show(self):
        pass
