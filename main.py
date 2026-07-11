"""
آزمون‌ساز هوشمند - نقطه ورود اصلی
Smart Quiz Generator - Main Entry Point
"""
import sys
import os
import platform

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from data.database import init_db, load_config, save_config
from utils.font_loader import (
    load_persian_fonts, set_persian_font, available_font_families
)
from utils.persian_utils import set_reshape_mode


def _platform_defaults():
    """Return good defaults for font+reshape based on the OS."""
    system = platform.system()
    if system == 'Windows':
        # Windows Tk with modern Segoe UI/Tahoma handles Persian natively
        return {'font_family': 'Vazirmatn', 'compat_reshape': False}
    elif system == 'Darwin':
        return {'font_family': 'Vazirmatn', 'compat_reshape': False}
    else:  # Linux
        return {'font_family': 'Vazirmatn', 'compat_reshape': True}


def _show_first_run_picker(cfg):
    """Show font/reshape picker on first launch."""
    import customtkinter as ctk
    from ui.first_run_dialog import show_first_run_dialog

    # Create a temporary root
    root = ctk.CTk()
    root.geometry('1x1+0+0')

    result_holder = {'result': None}

    def _run():
        available = available_font_families()
        # Apply platform defaults first
        defaults = _platform_defaults()
        current_font = cfg.get('font_family') or defaults['font_family']
        current_reshape = cfg.get('compat_reshape', defaults['compat_reshape'])
        r = show_first_run_dialog(root, current_font, current_reshape, available)
        result_holder['result'] = r
        root.destroy()

    root.after(50, _run)
    root.mainloop()

    if result_holder['result']:
        font_name, reshape = result_holder['result']
        cfg['font_family'] = font_name
        cfg['compat_reshape'] = reshape
        cfg['first_run_done'] = True
        save_config(cfg)
    else:
        # User closed dialog without choosing - use platform defaults
        defaults = _platform_defaults()
        cfg.update(defaults)
        cfg['first_run_done'] = True
        save_config(cfg)

    return cfg


def main():
    init_db()

    try:
        loaded = load_persian_fonts()
        print(f'[font] Persian fonts registered: {loaded}')
    except Exception as e:
        print(f'[font] Font loading error: {e}')

    cfg = load_config()

    # First-run: show font picker
    if not cfg.get('first_run_done', False):
        cfg = _show_first_run_picker(cfg)

    # Apply
    set_persian_font(cfg.get('font_family', 'Vazirmatn'))
    set_reshape_mode(bool(cfg.get('compat_reshape', False)))

    # Launch main window
    from ui.main_window import MainWindow
    app = MainWindow()
    app.mainloop()


if __name__ == '__main__':
    main()
