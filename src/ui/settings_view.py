"""
صفحه تنظیمات
Settings view.
"""
import threading
import customtkinter as ctk
from tkinter import messagebox

from utils.persian_utils import fa, set_reshape_mode
from utils.font_loader import PERSIAN_FONT as FONT
from data import database as db
from utils.ocr import is_tesseract_available


class SettingsView(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color='#12141f')
        self.app = app

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color='#181b2b', corner_radius=16)
        header.grid(row=0, column=0, sticky='ew', padx=24, pady=(24, 12))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=fa('تنظیمات'),
                     font=(FONT, 22, 'bold'), text_color='#e6e8ef',
                     anchor='e', justify='right'
                     ).grid(row=0, column=0, sticky='ew', padx=24, pady=(18, 4))
        ctk.CTkLabel(header,
                     text=fa('پیکربندی موتور هوش مصنوعی، زبان و OCR'),
                     font=(FONT, 13), text_color='#a1a6bd',
                     anchor='e', justify='right'
                     ).grid(row=1, column=0, sticky='ew', padx=24, pady=(0, 18))

        body = ctk.CTkScrollableFrame(self, fg_color='#12141f')
        body.grid(row=1, column=0, sticky='nsew', padx=24, pady=(0, 24))
        body.grid_columnconfigure(0, weight=1)

        # ============ g4f card ============
        g4f_card = ctk.CTkFrame(body, fg_color='#181b2b', corner_radius=14)
        g4f_card.pack(fill='x', pady=6)
        g4f_card.grid_columnconfigure(0, weight=1)

        top_row = ctk.CTkFrame(g4f_card, fg_color='transparent')
        top_row.grid(row=0, column=0, sticky='ew', padx=20, pady=(18, 4))
        top_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(top_row, text=fa('🎁 هوش مصنوعی رایگان داخلی (g4f)'),
                     font=(FONT, 16, 'bold'), text_color='#22c58b',
                     anchor='e', justify='right'
                     ).grid(row=0, column=0, sticky='ew')

        self.g4f_var = ctk.BooleanVar(value=True)
        self.g4f_switch = ctk.CTkSwitch(top_row, text='', variable=self.g4f_var,
                                         progress_color='#22c58b')
        self.g4f_switch.grid(row=0, column=1, sticky='e', padx=6)

        ctk.CTkLabel(g4f_card,
                     text=fa('این گزینه به‌طور خودکار به مدل‌های GPT/Claude/Gemini از طریق پروکسی‌های رایگان وصل می‌شه. هیچ کلید API نمی‌خواد. توصیه: همیشه روشن نگه دار.'),
                     font=(FONT, 12), text_color='#a1a6bd',
                     wraplength=1050, anchor='e', justify='right'
                     ).grid(row=1, column=0, sticky='ew', padx=20, pady=(4, 8))

        ctk.CTkButton(g4f_card, text=fa('🧪 تست g4f'),
                      width=150, height=36, corner_radius=10,
                      font=(FONT, 12, 'bold'),
                      fg_color='#22c58b', hover_color='#1ba374',
                      command=self._test_g4f
                      ).grid(row=2, column=0, sticky='e', padx=20, pady=(0, 16))

        # ============ Ollama card ============
        ol_card = ctk.CTkFrame(body, fg_color='#181b2b', corner_radius=14)
        ol_card.pack(fill='x', pady=6)
        ol_card.grid_columnconfigure(0, weight=1)

        ol_top = ctk.CTkFrame(ol_card, fg_color='transparent')
        ol_top.grid(row=0, column=0, sticky='ew', padx=20, pady=(18, 4))
        ol_top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(ol_top, text=fa('💻 Ollama (مدل محلی روی کامپیوتر)'),
                     font=(FONT, 16, 'bold'), text_color='#7c93ff',
                     anchor='e', justify='right'
                     ).grid(row=0, column=0, sticky='ew')

        self.ollama_var = ctk.BooleanVar(value=False)
        self.ollama_switch = ctk.CTkSwitch(ol_top, text='', variable=self.ollama_var,
                                            progress_color='#7c93ff')
        self.ollama_switch.grid(row=0, column=1, sticky='e', padx=6)

        ctk.CTkLabel(ol_card,
                     text=fa('برای اجرای مدل روی کامپیوتر خودت (بدون اینترنت). اول ollama.com رو نصب کن، بعد: ollama pull qwen2.5:3b'),
                     font=(FONT, 12), text_color='#a1a6bd',
                     wraplength=1050, anchor='e', justify='right'
                     ).grid(row=1, column=0, sticky='ew', padx=20, pady=(4, 8))

        ol_grid = ctk.CTkFrame(ol_card, fg_color='transparent')
        ol_grid.grid(row=2, column=0, sticky='ew', padx=20, pady=(0, 8))
        ol_grid.grid_columnconfigure(0, weight=1)
        ol_grid.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(ol_grid, text=fa('آدرس Ollama'),
                     font=(FONT, 12, 'bold'), text_color='#dfe2ec',
                     anchor='e', justify='right'
                     ).grid(row=0, column=1, sticky='ew', padx=6, pady=(0, 4))
        self.ollama_url_entry = ctk.CTkEntry(ol_grid, height=36, font=(FONT, 12),
                                              placeholder_text='http://localhost:11434')
        self.ollama_url_entry.grid(row=1, column=1, sticky='ew', padx=6)

        ctk.CTkLabel(ol_grid, text=fa('نام مدل Ollama'),
                     font=(FONT, 12, 'bold'), text_color='#dfe2ec',
                     anchor='e', justify='right'
                     ).grid(row=0, column=0, sticky='ew', padx=6, pady=(0, 4))
        self.ollama_model_entry = ctk.CTkEntry(ol_grid, height=36, font=(FONT, 12),
                                                placeholder_text='qwen2.5:3b')
        self.ollama_model_entry.grid(row=1, column=0, sticky='ew', padx=6)

        ctk.CTkButton(ol_card, text=fa('🧪 تست Ollama'),
                      width=150, height=36, corner_radius=10,
                      font=(FONT, 12, 'bold'),
                      fg_color='#7c93ff', hover_color='#5a72d6',
                      command=self._test_ollama
                      ).grid(row=3, column=0, sticky='e', padx=20, pady=(0, 16))

        # ============ Custom API ============
        api_card = ctk.CTkFrame(body, fg_color='#181b2b', corner_radius=14)
        api_card.pack(fill='x', pady=6)
        api_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(api_card, text=fa('🔑 API شخصی (اختیاری - OpenAI و سازگارها)'),
                     font=(FONT, 16, 'bold'), text_color='#e0568e',
                     anchor='e', justify='right'
                     ).grid(row=0, column=0, sticky='ew', padx=20, pady=(18, 4))

        ctk.CTkLabel(api_card,
                     text=fa('اگر کلید OpenAI یا هر سرویس سازگار داری، اینجا وارد کن. کیفیت بالاتر و پایدارتر از g4f. خالی گذاشتنش مشکلی نداره.'),
                     font=(FONT, 12), text_color='#a1a6bd',
                     wraplength=1050, anchor='e', justify='right'
                     ).grid(row=1, column=0, sticky='ew', padx=20, pady=(4, 8))

        ctk.CTkLabel(api_card, text=fa('کلید API'),
                     font=(FONT, 13, 'bold'), text_color='#e6e8ef',
                     anchor='e', justify='right'
                     ).grid(row=2, column=0, sticky='ew', padx=20, pady=(6, 4))
        self.api_key_entry = ctk.CTkEntry(api_card, height=40, show='*',
                                          font=(FONT, 13),
                                          placeholder_text='sk-...')
        self.api_key_entry.grid(row=3, column=0, sticky='ew', padx=20, pady=(0, 4))

        show_row = ctk.CTkFrame(api_card, fg_color='transparent')
        show_row.grid(row=4, column=0, sticky='e', padx=20, pady=(0, 4))
        self.show_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(show_row, text=fa('نمایش کلید'), variable=self.show_var,
                        command=self._toggle_show, font=(FONT, 12)
                        ).pack(side='right')

        ctk.CTkLabel(api_card, text=fa('آدرس API (Base URL)'),
                     font=(FONT, 13, 'bold'), text_color='#e6e8ef',
                     anchor='e', justify='right'
                     ).grid(row=5, column=0, sticky='ew', padx=20, pady=(12, 4))
        self.base_url_entry = ctk.CTkEntry(api_card, height=40, font=(FONT, 13),
                                            placeholder_text='https://api.openai.com/v1')
        self.base_url_entry.grid(row=6, column=0, sticky='ew', padx=20, pady=(0, 4))

        ctk.CTkLabel(api_card, text=fa('نام مدل'),
                     font=(FONT, 13, 'bold'), text_color='#e6e8ef',
                     anchor='e', justify='right'
                     ).grid(row=7, column=0, sticky='ew', padx=20, pady=(12, 4))
        self.model_entry = ctk.CTkEntry(api_card, height=40, font=(FONT, 13),
                                        placeholder_text='gpt-4o-mini')
        self.model_entry.grid(row=8, column=0, sticky='ew', padx=20, pady=(0, 12))

        ctk.CTkButton(api_card, text=fa('🧪 تست API'),
                      width=150, height=36, corner_radius=10,
                      font=(FONT, 12, 'bold'),
                      fg_color='#e0568e', hover_color='#c73c74',
                      command=self._test_api
                      ).grid(row=9, column=0, sticky='e', padx=20, pady=(0, 16))

        # ============ Language / Display ============
        lang_card = ctk.CTkFrame(body, fg_color='#181b2b', corner_radius=14)
        lang_card.pack(fill='x', pady=6)
        lang_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(lang_card, text=fa('🔤 زبان و نمایش فارسی'),
                     font=(FONT, 16, 'bold'), text_color='#f2a44d',
                     anchor='e', justify='right'
                     ).grid(row=0, column=0, sticky='ew', padx=20, pady=(18, 4))

        ctk.CTkLabel(lang_card,
                     text=fa('اگه متن فارسی خوانا نیست، اول با دکمه پایین یه تست کن. اگه لازم بود، فونت یا حالت ریشاپ رو عوض کن و بعد برنامه رو یک بار بسته و باز کن.'),
                     font=(FONT, 12), text_color='#a1a6bd',
                     wraplength=1050, anchor='e', justify='right'
                     ).grid(row=1, column=0, sticky='ew', padx=20, pady=(4, 8))

        # Font picker row
        font_row = ctk.CTkFrame(lang_card, fg_color='transparent')
        font_row.grid(row=2, column=0, sticky='ew', padx=20, pady=(4, 8))
        font_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(font_row, text=fa('فونت فارسی'),
                     font=(FONT, 13, 'bold'), text_color='#dfe2ec',
                     anchor='e', justify='right'
                     ).grid(row=0, column=1, sticky='ew', padx=6, pady=(0, 4))
        try:
            from utils.font_loader import available_font_families
            fonts = available_font_families()
        except Exception:
            fonts = ['Vazirmatn', 'Tahoma', 'Arial']
        self.font_var = ctk.StringVar(value='Vazirmatn')
        self.font_menu = ctk.CTkOptionMenu(
            font_row, values=fonts, variable=self.font_var,
            fg_color='#2a2f4a', button_color='#4d68f2',
            font=(FONT, 12), height=36,
        )
        self.font_menu.grid(row=1, column=1, sticky='ew', padx=6)

        # Reshape switch
        compat_row = ctk.CTkFrame(lang_card, fg_color='transparent')
        compat_row.grid(row=3, column=0, sticky='ew', padx=20, pady=(8, 8))
        compat_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(compat_row, text=fa('حالت ریشاپ (اگه حروف جدا نمایش داده می‌شن، این رو روشن کن)'),
                     font=(FONT, 12, 'bold'), text_color='#dfe2ec',
                     anchor='e', justify='right'
                     ).grid(row=0, column=0, sticky='ew')

        self.compat_var = ctk.BooleanVar(value=False)
        self.compat_switch = ctk.CTkSwitch(compat_row, text='', variable=self.compat_var,
                                            progress_color='#f2a44d',
                                            command=self._on_compat_toggle)
        self.compat_switch.grid(row=0, column=1, sticky='e', padx=6)

        # Test button
        test_row = ctk.CTkFrame(lang_card, fg_color='transparent')
        test_row.grid(row=4, column=0, sticky='ew', padx=20, pady=(4, 16))

        ctk.CTkButton(
            test_row, text=fa('🧪 تست نمایش فارسی (پیش‌نمایش با ۴ حالت)'),
            font=(FONT, 13, 'bold'), height=40, corner_radius=10,
            fg_color='#f2a44d', hover_color='#d68a37',
            command=self._open_font_test,
        ).pack(side='right', padx=4)

        # ============ OCR status ============
        ocr_card = ctk.CTkFrame(body, fg_color='#181b2b', corner_radius=14)
        ocr_card.pack(fill='x', pady=6)
        ctk.CTkLabel(ocr_card, text=fa('🔍 وضعیت OCR (برای PDF اسکن‌شده)'),
                     font=(FONT, 16, 'bold'), text_color='#f2a44d',
                     anchor='e', justify='right'
                     ).pack(fill='x', padx=20, pady=(16, 6))
        ocr_ok = is_tesseract_available()
        status_text = fa('✅ Tesseract نصب است. PDF های اسکن‌شده به‌طور خودکار پردازش می‌شن.') if ocr_ok else \
            fa('❌ Tesseract نصب نیست. برای پشتیبانی از PDF اسکن‌شده، Tesseract OCR رو نصب کن.')
        color = '#22c58b' if ocr_ok else '#f2a44d'
        ctk.CTkLabel(ocr_card, text=status_text,
                     font=(FONT, 13), text_color=color,
                     wraplength=1050, anchor='e', justify='right'
                     ).pack(fill='x', padx=20, pady=(0, 16))

        # ============ Save button ============
        btns = ctk.CTkFrame(body, fg_color='transparent')
        btns.pack(fill='x', pady=18)
        ctk.CTkButton(btns, text=fa('💾 ذخیره تنظیمات'),
                      font=(FONT, 14, 'bold'), height=46, corner_radius=12, width=180,
                      fg_color='#22c58b', hover_color='#1ba374',
                      command=self._save
                      ).pack(side='right', padx=6)

        ctk.CTkLabel(body,
                     text=fa('💡 اولویت موتور‌ها: g4f (اگر روشن) ← Ollama (اگر روشن) ← API شخصی (اگر کلید داری) ← قالبی (آفلاین).'),
                     font=(FONT, 11), text_color='#8b91a5',
                     wraplength=1050, anchor='e', justify='right'
                     ).pack(fill='x', padx=6, pady=(0, 12))

        self._load()

    def _toggle_show(self):
        self.api_key_entry.configure(show='' if self.show_var.get() else '*')

    def _on_compat_toggle(self):
        set_reshape_mode(self.compat_var.get())

    def _load(self):
        cfg = db.load_config()
        self.g4f_var.set(cfg.get('use_g4f', True))
        self.ollama_var.set(cfg.get('use_ollama', False))
        self.ollama_url_entry.delete(0, 'end')
        self.ollama_url_entry.insert(0, cfg.get('ollama_url', 'http://localhost:11434'))
        self.ollama_model_entry.delete(0, 'end')
        self.ollama_model_entry.insert(0, cfg.get('ollama_model', 'qwen2.5:3b'))
        self.api_key_entry.delete(0, 'end')
        self.api_key_entry.insert(0, cfg.get('api_key', ''))
        self.base_url_entry.delete(0, 'end')
        self.base_url_entry.insert(0, cfg.get('base_url', 'https://api.openai.com/v1'))
        self.model_entry.delete(0, 'end')
        self.model_entry.insert(0, cfg.get('model', 'gpt-4o-mini'))
        self.compat_var.set(cfg.get('compat_reshape', False))
        self.font_var.set(cfg.get('font_family', 'Vazirmatn'))

    def _save(self):
        cfg = {
            'use_g4f': self.g4f_var.get(),
            'use_ollama': self.ollama_var.get(),
            'ollama_url': self.ollama_url_entry.get().strip() or 'http://localhost:11434',
            'ollama_model': self.ollama_model_entry.get().strip() or 'qwen2.5:3b',
            'api_key': self.api_key_entry.get().strip(),
            'base_url': self.base_url_entry.get().strip() or 'https://api.openai.com/v1',
            'model': self.model_entry.get().strip() or 'gpt-4o-mini',
            'compat_reshape': self.compat_var.get(),
            'font_family': self.font_var.get(),
            'first_run_done': True,
        }
        db.save_config(cfg)
        set_reshape_mode(cfg['compat_reshape'])
        try:
            from utils.font_loader import set_persian_font
            set_persian_font(cfg['font_family'])
        except Exception:
            pass
        messagebox.showinfo(
            'ذخیره شد',
            'تنظیمات ذخیره شد.\n\nاگه فونت یا حالت ریشاپ رو عوض کردی، برای اعمال کامل، برنامه رو یک بار ببند و باز کن.'
        )

    def _open_font_test(self):
        """Open the first-run picker dialog to test 4 combinations live."""
        try:
            from ui.first_run_dialog import show_first_run_dialog
            from utils.font_loader import available_font_families
            fonts = available_font_families()
            result = show_first_run_dialog(
                self.winfo_toplevel(),
                current_font=self.font_var.get(),
                current_reshape=self.compat_var.get(),
                available_fonts=fonts,
            )
            if result:
                font_name, reshape = result
                self.font_var.set(font_name)
                self.compat_var.set(reshape)
                messagebox.showinfo(
                    'تغییر اعمال شد',
                    f'فونت: {font_name}\nریشاپ: {"روشن" if reshape else "خاموش"}\n\nحالا روی «ذخیره تنظیمات» کلیک کن و برنامه رو یک بار ببند و باز کن.'
                )
        except Exception as e:
            messagebox.showerror('خطا', f'خطای باز کردن پیش‌نمایش:\n{e}')

    def _test_g4f(self):
        def worker():
            try:
                from g4f.client import Client
                client = Client()
                resp = client.chat.completions.create(
                    model='gpt-4o-mini',
                    messages=[{'role': 'user', 'content': 'Say "OK" in one word.'}],
                    timeout=30,
                )
                reply = (resp.choices[0].message.content or '').strip()
                self.after(0, lambda: messagebox.showinfo(
                    'موفق', f'✅ g4f کار می‌کنه!\nپاسخ: {reply[:100]}'))
            except ImportError:
                self.after(0, lambda: messagebox.showerror(
                    'خطا', 'کتابخانه g4f نصب نیست. اجرا کن: pip install -U g4f'))
            except Exception as e:
                err = str(e)[:300]
                self.after(0, lambda: messagebox.showerror(
                    'ناموفق', f'❌ اتصال به g4f موفق نشد:\n{err}'))

        threading.Thread(target=worker, daemon=True).start()
        messagebox.showinfo('در حال تست', 'در حال بررسی اتصال به g4f... چند ثانیه صبر کن.')

    def _test_ollama(self):
        try:
            import requests
        except ImportError:
            messagebox.showerror('خطا', 'کتابخانه requests نصب نیست.')
            return
        url = self.ollama_url_entry.get().strip() or 'http://localhost:11434'
        model = self.ollama_model_entry.get().strip() or 'qwen2.5:3b'
        try:
            r = requests.get(f'{url}/api/tags', timeout=5)
            if r.status_code == 200:
                data = r.json()
                models = [m.get('name', '') for m in data.get('models', [])]
                if model in models or any(model in m for m in models):
                    messagebox.showinfo('موفق', f'✅ Ollama در دسترس است.\nمدل «{model}» نصب شده.')
                else:
                    messagebox.showwarning(
                        'توجه',
                        f'⚠️ Ollama در دسترس است اما مدل «{model}» نصب نیست.\nمدل‌های موجود: {", ".join(models) or "هیچ"}\n\nاجرا کن: ollama pull {model}'
                    )
            else:
                messagebox.showerror('ناموفق', f'❌ پاسخ Ollama نامعتبر: {r.status_code}')
        except Exception as e:
            messagebox.showerror(
                'ناموفق',
                f'❌ Ollama در دسترس نیست:\n{e}\n\nمطمئن شو Ollama نصب و اجرا شده.'
            )

    def _test_api(self):
        try:
            from openai import OpenAI
        except ImportError:
            messagebox.showerror('خطا', 'کتابخانه openai نصب نیست.')
            return

        api_key = self.api_key_entry.get().strip()
        base_url = self.base_url_entry.get().strip() or 'https://api.openai.com/v1'
        model = self.model_entry.get().strip() or 'gpt-4o-mini'

        if not api_key:
            messagebox.showwarning('توجه', 'اول کلید API رو وارد کن.')
            return

        try:
            client = OpenAI(api_key=api_key, base_url=base_url, timeout=30)
            resp = client.chat.completions.create(
                model=model,
                messages=[{'role': 'user', 'content': 'Say "OK" in one word.'}],
                max_tokens=5,
            )
            reply = (resp.choices[0].message.content or '').strip()
            messagebox.showinfo('موفق', f'✅ اتصال به مدل {model} برقرار شد.\nپاسخ: {reply}')
        except Exception as e:
            messagebox.showerror('ناموفق', f'❌ اتصال برقرار نشد:\n{e}')

    def on_show(self):
        self._load()
