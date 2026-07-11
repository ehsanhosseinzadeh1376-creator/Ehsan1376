"""
صفحه داشبورد تحلیل
Analytics dashboard.
"""
import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.rcParams['font.family'] = ['Vazirmatn', 'Tahoma', 'DejaVu Sans']

from utils.persian_utils import fa
from utils.font_loader import PERSIAN_FONT as FONT
from core.analyzer import analyze_quiz, analyze_global


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color='#12141f')
        self.app = app
        self.scope = 'quiz'

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color='#181b2b', corner_radius=16)
        header.grid(row=0, column=0, sticky='ew', padx=24, pady=(24, 12))
        header.grid_columnconfigure(0, weight=1)

        top_row = ctk.CTkFrame(header, fg_color='transparent')
        top_row.grid(row=0, column=0, sticky='ew', padx=24, pady=16)
        top_row.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(
            top_row, text=fa('داشبورد تحلیل عملکرد'),
            font=(FONT, 22, 'bold'), text_color='#e6e8ef', anchor='e', justify='right'
        )
        self.title_label.grid(row=0, column=0, sticky='ew')

        scope_row = ctk.CTkFrame(top_row, fg_color='transparent')
        scope_row.grid(row=0, column=1, sticky='e')
        self.btn_scope_quiz = ctk.CTkButton(
            scope_row, text=fa('آزمون فعلی'), width=120, height=36,
            font=(FONT, 12, 'bold'), corner_radius=10,
            fg_color='#4d68f2', hover_color='#3a54d9',
            command=lambda: self._set_scope('quiz')
        )
        self.btn_scope_quiz.pack(side='right', padx=4)

        self.btn_scope_global = ctk.CTkButton(
            scope_row, text=fa('همه آزمون‌ها'), width=120, height=36,
            font=(FONT, 12, 'bold'), corner_radius=10,
            fg_color='#2a2f4a', hover_color='#3a4267',
            command=lambda: self._set_scope('global')
        )
        self.btn_scope_global.pack(side='right', padx=4)

        self.subtitle = ctk.CTkLabel(
            header, text='', font=(FONT, 13), text_color='#a1a6bd',
            anchor='e', justify='right'
        )
        self.subtitle.grid(row=1, column=0, sticky='ew', padx=24, pady=(0, 14))

        self.body = ctk.CTkScrollableFrame(self, fg_color='#12141f')
        self.body.grid(row=1, column=0, sticky='nsew', padx=24, pady=(0, 24))
        self.body.grid_columnconfigure(0, weight=1)

    def _set_scope(self, scope):
        self.scope = scope
        if scope == 'quiz':
            self.btn_scope_quiz.configure(fg_color='#4d68f2')
            self.btn_scope_global.configure(fg_color='#2a2f4a')
        else:
            self.btn_scope_quiz.configure(fg_color='#2a2f4a')
            self.btn_scope_global.configure(fg_color='#4d68f2')
        self._refresh()

    def on_show(self):
        self._refresh()

    def _refresh(self):
        for w in self.body.winfo_children():
            w.destroy()

        if self.scope == 'quiz':
            quiz = self.app.current_quiz
            if not quiz:
                self._empty_state(fa('هیچ آزمونی انتخاب نشده. یک آزمون از کتابخانه انتخاب کن یا آزمون فعلی رو تمام کن.'))
                return
            data = analyze_quiz(quiz['id'])
            self.subtitle.configure(text=fa(f'تحلیل آزمون: {quiz.get("title", "")}'))
        else:
            data = analyze_global()
            self.subtitle.configure(text=fa('تحلیل کلی همه آزمون‌ها و تلاش‌های ثبت‌شده'))

        self._render_dashboard(data)

    def _empty_state(self, msg):
        ctk.CTkLabel(self.body, text=msg, text_color='#a1a6bd',
                     font=(FONT, 15), wraplength=900,
                     anchor='e', justify='right'
                     ).pack(pady=80, padx=20)

    def _render_dashboard(self, data):
        total_attempts = data.get('total_attempts', 0)
        if total_attempts == 0:
            self._empty_state(fa('هنوز داده‌ای برای تحلیل ثبت نشده. یک آزمون بده تا تحلیل انجام بشه.'))
            return

        # KPI cards
        kpi_row = ctk.CTkFrame(self.body, fg_color='transparent')
        kpi_row.pack(fill='x', pady=(6, 14))
        for i in range(4):
            kpi_row.grid_columnconfigure(i, weight=1)

        kpis = [
            ('میانگین نمره', f'{data.get("avg_score", 0):.1f}%', '#22c58b'),
            ('بهترین نمره', f'{data.get("best_score", data.get("avg_score", 0)):.1f}%', '#4d68f2'),
            ('کمترین نمره', f'{data.get("worst_score", data.get("avg_score", 0)):.1f}%', '#e0568e'),
            ('تعداد تلاش', f'{total_attempts}', '#f2a44d'),
        ]
        for i, (label, value, color) in enumerate(kpis):
            card = ctk.CTkFrame(kpi_row, fg_color='#181b2b', corner_radius=14)
            card.grid(row=0, column=i, padx=6, sticky='ew')
            ctk.CTkLabel(card, text=fa(label), font=(FONT, 13),
                         text_color='#a1a6bd').pack(pady=(18, 6))
            ctk.CTkLabel(card, text=value, font=(FONT, 26, 'bold'),
                         text_color=color).pack(pady=(0, 18))

        # Suggestions
        sug_card = ctk.CTkFrame(self.body, fg_color='#181b2b', corner_radius=14)
        sug_card.pack(fill='x', pady=8)
        ctk.CTkLabel(sug_card, text=fa('💡 پیشنهاد مطالعه'),
                     font=(FONT, 16, 'bold'), text_color='#7c93ff',
                     anchor='e', justify='right'
                     ).pack(fill='x', padx=20, pady=(16, 8))
        for s in data.get('suggestions', []):
            ctk.CTkLabel(sug_card, text=fa('• ' + s), font=(FONT, 13),
                         text_color='#dfe2ec', anchor='e', justify='right',
                         wraplength=1050).pack(fill='x', padx=28, pady=4)
        ctk.CTkLabel(sug_card, text='', height=8).pack()

        # Charts row
        charts_row = ctk.CTkFrame(self.body, fg_color='transparent')
        charts_row.pack(fill='x', pady=8)
        charts_row.grid_columnconfigure(0, weight=1)
        charts_row.grid_columnconfigure(1, weight=1)

        topic_stats = data.get('topic_stats', [])
        if topic_stats:
            fig1 = Figure(figsize=(5.5, 3.4), dpi=100, facecolor='#181b2b')
            ax1 = fig1.add_subplot(111)
            ax1.set_facecolor('#181b2b')
            names = [t['topic'][:18] for t in topic_stats[:8]]
            accs = [t['accuracy'] for t in topic_stats[:8]]
            colors = ['#22c58b' if a >= 75 else '#f2a44d' if a >= 50 else '#e0568e' for a in accs]
            ax1.barh(names, accs, color=colors)
            ax1.set_xlim(0, 100)
            ax1.set_xlabel('Accuracy %', color='#a1a6bd', fontsize=9)
            ax1.tick_params(colors='#a1a6bd', labelsize=9)
            for spine in ax1.spines.values():
                spine.set_color('#2a2f4a')
            ax1.set_title('Accuracy by Topic', color='#e6e8ef', fontsize=11, pad=10)
            fig1.tight_layout()

            cbox1 = ctk.CTkFrame(charts_row, fg_color='#181b2b', corner_radius=14)
            cbox1.grid(row=0, column=0, padx=6, sticky='nsew')
            canvas1 = FigureCanvasTkAgg(fig1, master=cbox1)
            canvas1.draw()
            canvas1.get_tk_widget().pack(padx=10, pady=10, fill='both', expand=True)

        trend = data.get('trend', [])
        if trend and len(trend) >= 1:
            fig2 = Figure(figsize=(5.5, 3.4), dpi=100, facecolor='#181b2b')
            ax2 = fig2.add_subplot(111)
            ax2.set_facecolor('#181b2b')
            xs = list(range(1, len(trend) + 1))
            ys = [t['score'] for t in trend]
            ax2.plot(xs, ys, marker='o', color='#4d68f2', linewidth=2.5, markersize=7)
            ax2.fill_between(xs, ys, alpha=0.18, color='#4d68f2')
            ax2.set_ylim(0, 105)
            ax2.set_xlabel('Attempt #', color='#a1a6bd', fontsize=9)
            ax2.set_ylabel('Score %', color='#a1a6bd', fontsize=9)
            ax2.tick_params(colors='#a1a6bd', labelsize=9)
            for spine in ax2.spines.values():
                spine.set_color('#2a2f4a')
            ax2.grid(True, alpha=0.15, color='#a1a6bd')
            ax2.set_title('Score Trend', color='#e6e8ef', fontsize=11, pad=10)
            fig2.tight_layout()

            cbox2 = ctk.CTkFrame(charts_row, fg_color='#181b2b', corner_radius=14)
            cbox2.grid(row=0, column=1, padx=6, sticky='nsew')
            canvas2 = FigureCanvasTkAgg(fig2, master=cbox2)
            canvas2.draw()
            canvas2.get_tk_widget().pack(padx=10, pady=10, fill='both', expand=True)

        # Weakest topics
        weakest = data.get('weakest_topics', [])
        if weakest:
            weak_card = ctk.CTkFrame(self.body, fg_color='#181b2b', corner_radius=14)
            weak_card.pack(fill='x', pady=8)
            ctk.CTkLabel(weak_card, text=fa('⚠️ نقاط ضعف (مباحث با دقت زیر ۷۰٪)'),
                         font=(FONT, 16, 'bold'), text_color='#e0568e',
                         anchor='e', justify='right'
                         ).pack(fill='x', padx=20, pady=(16, 8))
            for t in weakest:
                row = ctk.CTkFrame(weak_card, fg_color='#0f1120', corner_radius=10)
                row.pack(fill='x', padx=20, pady=4)
                ctk.CTkLabel(row, text=fa(f'📌 {t["topic"]}'), font=(FONT, 14, 'bold'),
                             text_color='#e6e8ef', anchor='e', justify='right'
                             ).pack(side='right', padx=16, pady=10)
                ctk.CTkLabel(row, text=fa(f'دقت: {t["accuracy"]}٪   •   اشتباه: {t["wrong"]} از {t["total"]}'),
                             font=(FONT, 12), text_color='#a1a6bd'
                             ).pack(side='right', padx=16, pady=10)
            ctk.CTkLabel(weak_card, text='', height=8).pack()

        # Error prone questions
        error_prone = data.get('error_prone_questions', [])
        if error_prone:
            ep_card = ctk.CTkFrame(self.body, fg_color='#181b2b', corner_radius=14)
            ep_card.pack(fill='x', pady=8)
            ctk.CTkLabel(ep_card, text=fa('❗ سوالات پرخطا (بیشترین پاسخ اشتباه)'),
                         font=(FONT, 16, 'bold'), text_color='#f2a44d',
                         anchor='e', justify='right'
                         ).pack(fill='x', padx=20, pady=(16, 8))
            for eq in error_prone[:6]:
                row = ctk.CTkFrame(ep_card, fg_color='#0f1120', corner_radius=10)
                row.pack(fill='x', padx=20, pady=5)
                ctk.CTkLabel(row, text=fa('❓ ' + eq['text']), font=(FONT, 13, 'bold'),
                             text_color='#e6e8ef', anchor='e', wraplength=900, justify='right'
                             ).pack(fill='x', padx=16, pady=(10, 4))
                ctk.CTkLabel(row, text=fa(f'مبحث: {eq["topic"] or "-"}   •   اشتباه: {eq["wrong_count"]} از {eq["total"]}   •   نرخ خطا: {eq["error_rate"]}٪'),
                             font=(FONT, 11), text_color='#a1a6bd', anchor='e', justify='right'
                             ).pack(fill='x', padx=16, pady=(0, 10))
            ctk.CTkLabel(ep_card, text='', height=8).pack()
