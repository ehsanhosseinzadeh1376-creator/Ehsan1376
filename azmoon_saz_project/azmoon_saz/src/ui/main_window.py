"""
پنجره اصلی
Main application window with sidebar navigation.
"""
import customtkinter as ctk
from tkinter import messagebox

from utils.persian_utils import fa, set_reshape_mode, get_reshape_mode
from utils.font_loader import PERSIAN_FONT
from data import database as db
from ui.pdf_view import PdfView
from ui.quiz_view import QuizView
from ui.dashboard_view import DashboardView
from ui.settings_view import SettingsView
from ui.library_view import LibraryView


ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('blue')

FONT = PERSIAN_FONT


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('آزمون‌ساز هوشمند - Azmoon Saz')
        self.geometry('1360x860')
        self.minsize(1180, 740)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_area()

        self.current_document = None
        self.current_quiz = None

        self.views = {}
        self.current_view_key = 'pdf'
        self._init_views()
        self.show_view('pdf')

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color='#1a1d2e')
        self.sidebar.grid(row=0, column=1, sticky='nsew')
        self.sidebar.grid_propagate(False)

        logo = ctk.CTkLabel(
            self.sidebar,
            text=fa('آزمون‌ساز هوشمند'),
            font=(FONT, 22, 'bold'),
            text_color='#7c93ff',
        )
        logo.pack(pady=(30, 4))

        sub = ctk.CTkLabel(
            self.sidebar,
            text=fa('نسخه دسکتاپ ۱.۰'),
            font=(FONT, 12),
            text_color='#8b91a5',
        )
        sub.pack(pady=(0, 20))

        # Hot toggle for Persian display
        toggle_btn = ctk.CTkButton(
            self.sidebar,
            text=fa('🔄 چرخش نمایش فارسی'),
            font=(FONT, 12, 'bold'),
            height=38, corner_radius=10,
            fg_color='#f2a44d', hover_color='#d68a37',
            command=self._toggle_persian_display,
        )
        toggle_btn.pack(fill='x', padx=16, pady=(0, 4))

        hint = ctk.CTkLabel(
            self.sidebar,
            text=fa('اگه متن خوانا نیست، اینو بزن'),
            font=(FONT, 10),
            text_color='#8b91a5',
        )
        hint.pack(pady=(0, 20))

        self.nav_buttons = {}
        items = [
            ('pdf', 'بارگذاری PDF', '📄'),
            ('library', 'کتابخانه من', '📚'),
            ('quiz', 'آزمون', '📝'),
            ('dashboard', 'داشبورد تحلیل', '📊'),
            ('settings', 'تنظیمات', '⚙️'),
        ]
        for key, label, icon in items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f'{icon}   ' + fa(label),
                anchor='e',
                height=48,
                corner_radius=12,
                fg_color='transparent',
                hover_color='#2a2f4a',
                text_color='#e6e8ef',
                font=(FONT, 15),
                command=lambda k=key: self.show_view(k),
            )
            btn.pack(fill='x', padx=16, pady=5)
            self.nav_buttons[key] = btn

        footer = ctk.CTkLabel(
            self.sidebar,
            text=fa('ساخته شده توسط احسان حسین زاده'),
            font=(FONT, 11),
            text_color='#5b6079',
        )
        footer.pack(side='bottom', pady=18)

    def _build_content_area(self):
        self.content = ctk.CTkFrame(self, corner_radius=0, fg_color='#12141f')
        self.content.grid(row=0, column=0, sticky='nsew')
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    def _init_views(self):
        self.views['pdf'] = PdfView(self.content, self)
        self.views['library'] = LibraryView(self.content, self)
        self.views['quiz'] = QuizView(self.content, self)
        self.views['dashboard'] = DashboardView(self.content, self)
        self.views['settings'] = SettingsView(self.content, self)

        for v in self.views.values():
            v.grid(row=0, column=0, sticky='nsew')
            v.grid_remove()

    def show_view(self, key: str):
        for k, v in self.views.items():
            v.grid_remove()
            if k in self.nav_buttons:
                self.nav_buttons[k].configure(fg_color='transparent')
        if key in self.views:
            view = self.views[key]
            view.grid()

            # Slide up animation
            view.place(relx=0, rely=0.04, relwidth=1, relheight=0.96)

            def animate(step=1):
                if step <= 8:
                    y = 0.04 - (step * 0.005)
                    view.place(relx=0, rely=max(0, y), relwidth=1, relheight=1-max(0, y))
                    self.after(10, lambda: animate(step + 1))
                else:
                    view.place(relx=0, rely=0, relwidth=1, relheight=1)

            animate()

            self.nav_buttons[key].configure(fg_color='#2a2f4a')
            self.current_view_key = key
            if hasattr(self.views[key], 'on_show'):
                try:
                    self.views[key].on_show()
                except Exception as e:
                    print(f'[on_show error] {e}')

    def set_current_document(self, doc: dict):
        self.current_document = doc

    def set_current_quiz(self, quiz: dict):
        self.current_quiz = quiz

    def open_quiz_view(self, quiz: dict):
        self.set_current_quiz(quiz)
        self.show_view('quiz')

    # ---- Hot toggle for Persian display ----
    def _toggle_persian_display(self):
        """Flip reshape mode and rebuild all views without restart."""
        new_mode = not get_reshape_mode()
        set_reshape_mode(new_mode)

        # Persist to config
        try:
            cfg = db.load_config()
            cfg['compat_reshape'] = new_mode
            cfg['first_run_done'] = True
            db.save_config(cfg)
        except Exception as e:
            print(f'[toggle] save config error: {e}')

        # Rebuild all views
        self._rebuild_views()

    def _rebuild_views(self):
        """Destroy all views and create fresh ones with current settings."""
        saved_doc = self.current_document
        saved_quiz = self.current_quiz
        current_key = self.current_view_key

        for v in list(self.views.values()):
            try:
                v.destroy()
            except Exception:
                pass
        self.views.clear()

        # Re-import so PERSIAN_FONT constant gets latest
        from ui.pdf_view import PdfView as PV
        from ui.quiz_view import QuizView as QV
        from ui.dashboard_view import DashboardView as DV
        from ui.settings_view import SettingsView as SV
        from ui.library_view import LibraryView as LV

        self.views['pdf'] = PV(self.content, self)
        self.views['library'] = LV(self.content, self)
        self.views['quiz'] = QV(self.content, self)
        self.views['dashboard'] = DV(self.content, self)
        self.views['settings'] = SV(self.content, self)
        for v in self.views.values():
            v.grid(row=0, column=0, sticky='nsew')
            v.grid_remove()

        # Rebuild sidebar labels too
        for widget in self.sidebar.winfo_children():
            widget.destroy()
        self._build_sidebar()

        # Restore state
        self.current_document = saved_doc
        self.current_quiz = saved_quiz
        self.show_view(current_key)
