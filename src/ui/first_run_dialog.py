"""
دیالوگ اولین اجرا - نسخه واکنش‌گرا
First-run dialog: everything (including UI chrome) re-renders when user
toggles font/reshape, so they can see the difference immediately.
"""
import platform
import customtkinter as ctk

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_RESHAPE = True
except ImportError:
    HAS_RESHAPE = False


def _reshape(text):
    if not HAS_RESHAPE:
        return text
    try:
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def platform_default_reshape() -> bool:
    system = platform.system()
    if system in ('Windows', 'Darwin'):
        return False
    return True


LABELS = {
    'title': '👋 تنظیم نمایش فارسی',
    'sub': 'به این متن نگاه کن. آیا فارسی راحت خوانده می‌شه؟ اگه نه، سوییچ ریشاپ رو عوض کن.',
    'sample': 'این یک متن فارسی نمونه است',
    'q': 'سوال ۱: قانون اهم چیست؟',
    'opts': 'گزینه‌ها: ولت، آمپر، اهم، وات',
    'ans': 'پاسخ صحیح: اهم — واحد استاندارد مقاومت',
    'font': 'فونت فارسی:',
    'reshape': 'حالت ریشاپ:',
    'reshape_hint': '(اگه حروف فارسی جدا نمایش داده می‌شن، سوییچ رو تغییر بده)',
    'accept': '✅ خواناست، ادامه بده',
    'toggle': '🔄 عوض کن (ریشاپ)',
    'status_on': 'ریشاپ: روشن',
    'status_off': 'ریشاپ: خاموش',
}


class FirstRunDialog(ctk.CTkToplevel):
    def __init__(self, parent, current_font='Vazirmatn', current_reshape=None,
                 available_fonts=None):
        super().__init__(parent)
        self.title('تنظیم نمایش فارسی')
        self.geometry('880x720')
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color='#12141f')

        if current_reshape is None:
            current_reshape = platform_default_reshape()

        self.result = None
        self.available_fonts = available_fonts or ['Vazirmatn', 'Tahoma', 'Arial']
        self.current_font = current_font if current_font in self.available_fonts else self.available_fonts[0]
        self.current_reshape = current_reshape

        # Build once
        self.font_var = ctk.StringVar(value=self.current_font)
        self.reshape_var = ctk.BooleanVar(value=self.current_reshape)

        self._build()

        self.after(80, self._center)

    def _center(self):
        try:
            self.update_idletasks()
            w = self.winfo_width(); h = self.winfo_height()
            sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
            self.geometry(f'+{max(0,(sw-w)//2)}+{max(0,(sh-h)//2)}')
        except Exception:
            pass

    def _t(self, key):
        """Translate label with current reshape setting applied."""
        raw = LABELS.get(key, key)
        return _reshape(raw) if self.current_reshape else raw

    def _build(self):
        # Clear
        for w in self.winfo_children():
            w.destroy()

        font_name = self.current_font

        # Header
        header = ctk.CTkFrame(self, fg_color='#181b2b', corner_radius=14)
        header.pack(fill='x', padx=20, pady=(20, 12))

        ctk.CTkLabel(
            header, text=self._t('title'),
            font=(font_name, 20, 'bold'), text_color='#e6e8ef',
            wraplength=800,
        ).pack(padx=20, pady=(18, 4))

        ctk.CTkLabel(
            header, text=self._t('sub'),
            font=(font_name, 13), text_color='#a1a6bd',
            wraplength=800,
        ).pack(padx=20, pady=(0, 16))

        # Preview
        preview = ctk.CTkFrame(self, fg_color='#181b2b', corner_radius=14,
                                border_width=2, border_color='#4d68f2')
        preview.pack(fill='both', expand=True, padx=20, pady=8)

        ctk.CTkLabel(preview, text=self._t('sample'),
                     font=(font_name, 26, 'bold'),
                     text_color='#e6e8ef', wraplength=800).pack(pady=(32, 10))
        ctk.CTkLabel(preview, text=self._t('q'),
                     font=(font_name, 19, 'bold'),
                     text_color='#7c93ff', wraplength=800).pack(pady=6)
        ctk.CTkLabel(preview, text=self._t('opts'),
                     font=(font_name, 15),
                     text_color='#dfe2ec', wraplength=800).pack(pady=6)
        ctk.CTkLabel(preview, text=self._t('ans'),
                     font=(font_name, 14),
                     text_color='#22c58b', wraplength=800).pack(pady=(6, 20))

        status_txt = self._t('status_on') if self.current_reshape else self._t('status_off')
        status_txt = f'{status_txt}   •   font: {font_name}'
        ctk.CTkLabel(preview, text=status_txt,
                     font=(font_name, 11),
                     text_color='#8b91a5').pack(pady=(0, 24))

        # Controls
        ctrl = ctk.CTkFrame(self, fg_color='#181b2b', corner_radius=12)
        ctrl.pack(fill='x', padx=20, pady=(8, 6))

        row1 = ctk.CTkFrame(ctrl, fg_color='transparent')
        row1.pack(fill='x', padx=16, pady=(12, 6))

        ctk.CTkLabel(row1, text=self._t('font'),
                     font=(font_name, 12), text_color='#a1a6bd'
                     ).pack(side='right', padx=(6, 8))
        ctk.CTkOptionMenu(
            row1, values=self.available_fonts, variable=self.font_var,
            command=lambda _: self._on_change(),
            fg_color='#2a2f4a', button_color='#4d68f2',
            font=(font_name, 12), width=200,
        ).pack(side='right', padx=6)

        row2 = ctk.CTkFrame(ctrl, fg_color='transparent')
        row2.pack(fill='x', padx=16, pady=(4, 12))
        ctk.CTkLabel(row2, text=self._t('reshape'),
                     font=(font_name, 12), text_color='#a1a6bd'
                     ).pack(side='right', padx=(6, 8))
        ctk.CTkSwitch(row2, text='', variable=self.reshape_var,
                       command=self._on_change,
                       progress_color='#22c58b').pack(side='right', padx=6)
        ctk.CTkLabel(row2, text=self._t('reshape_hint'),
                     font=(font_name, 11), text_color='#8b91a5'
                     ).pack(side='right', padx=(20, 6))

        # Actions
        actions = ctk.CTkFrame(self, fg_color='transparent')
        actions.pack(fill='x', padx=20, pady=(6, 18))

        ctk.CTkButton(
            actions, text=self._t('accept'),
            font=(font_name, 14, 'bold'), height=48, corner_radius=12,
            fg_color='#22c58b', hover_color='#1ba374',
            command=self._accept,
        ).pack(side='right', padx=6, fill='x', expand=True)

        ctk.CTkButton(
            actions, text=self._t('toggle'),
            font=(font_name, 13, 'bold'), height=48, corner_radius=12,
            fg_color='#f2a44d', hover_color='#d68a37',
            command=self._toggle_reshape, width=180,
        ).pack(side='right', padx=6)

    def _on_change(self):
        self.current_font = self.font_var.get()
        self.current_reshape = self.reshape_var.get()
        self._build()

    def _toggle_reshape(self):
        self.reshape_var.set(not self.reshape_var.get())
        self._on_change()

    def _accept(self):
        self.result = (self.current_font, self.current_reshape)
        self.destroy()


def show_first_run_dialog(parent, current_font, current_reshape, available_fonts):
    dlg = FirstRunDialog(parent, current_font, current_reshape, available_fonts)
    parent.wait_window(dlg)
    return dlg.result
