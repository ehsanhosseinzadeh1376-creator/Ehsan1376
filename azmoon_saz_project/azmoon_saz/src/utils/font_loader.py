"""
لود فونت فارسی
Cross-platform font loader with automatic fallback.

Strategy: try to register Vazirmatn (bundled). If that fails, use system
defaults known to render Persian correctly (Tahoma on Windows, etc).
"""
import os
import sys
import platform
import shutil
from pathlib import Path


def _get_fonts_dir() -> Path:
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent.parent / 'assets' / 'fonts',
        here.parent / 'assets' / 'fonts',
        Path.cwd() / 'assets' / 'fonts',
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def _register_windows(font_paths):
    try:
        import ctypes
        from ctypes import wintypes
        gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)
        FR_PRIVATE = 0x10
        add = gdi32.AddFontResourceExW
        add.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.LPVOID]
        add.restype = ctypes.c_int
        loaded = 0
        for fp in font_paths:
            n = add(str(fp), FR_PRIVATE, None)
            if n > 0:
                loaded += 1
        return loaded > 0
    except Exception as e:
        print(f'[font_loader/windows] {e}')
        return False


def _register_linux(font_paths):
    try:
        home_fonts = Path.home() / '.local' / 'share' / 'fonts' / 'AzmoonSaz'
        home_fonts.mkdir(parents=True, exist_ok=True)
        for fp in font_paths:
            dest = home_fonts / Path(fp).name
            if not dest.exists():
                shutil.copy2(str(fp), str(dest))
        try:
            import subprocess
            subprocess.run(['fc-cache', '-f', str(home_fonts)],
                           capture_output=True, timeout=15)
        except Exception:
            pass
        return True
    except Exception as e:
        print(f'[font_loader/linux] {e}')
        return False


def _register_macos(font_paths):
    try:
        home_fonts = Path.home() / 'Library' / 'Fonts'
        home_fonts.mkdir(parents=True, exist_ok=True)
        for fp in font_paths:
            dest = home_fonts / Path(fp).name
            if not dest.exists():
                shutil.copy2(str(fp), str(dest))
        return True
    except Exception as e:
        print(f'[font_loader/macos] {e}')
        return False


def load_persian_fonts() -> bool:
    """Register bundled fonts. Returns True if any font was registered."""
    fonts_dir = _get_fonts_dir()
    if not fonts_dir.exists():
        return False

    font_paths = sorted([str(p) for p in fonts_dir.glob('*.ttf')])
    if not font_paths:
        return False

    system = platform.system()
    ok = False
    try:
        if system == 'Windows':
            ok = _register_windows(font_paths)
        elif system == 'Darwin':
            ok = _register_macos(font_paths)
        elif system == 'Linux':
            ok = _register_linux(font_paths)
    except Exception as e:
        print(f'[font_loader] system={system} error={e}')

    try:
        import matplotlib.font_manager as fm
        for fp in font_paths:
            try:
                fm.fontManager.addfont(fp)
            except Exception:
                pass
    except ImportError:
        pass

    return ok


# System-safe Persian-capable fonts (very likely to be installed)
SYSTEM_FALLBACK_FONTS = {
    'Windows': ['Vazirmatn', 'Segoe UI', 'Tahoma', 'Arial'],
    'Darwin': ['Vazirmatn', 'Geeza Pro', 'Tahoma', 'Arial'],
    'Linux': ['Vazirmatn', 'DejaVu Sans', 'Noto Sans Arabic', 'FreeSans'],
}


def available_font_families():
    """Return list of Persian-capable font families available on this system."""
    system = platform.system()
    return SYSTEM_FALLBACK_FONTS.get(system, ['Vazirmatn', 'Tahoma', 'Arial'])


# Current font (mutable) - can be changed at runtime
PERSIAN_FONT = 'Vazirmatn'


def set_persian_font(name: str):
    global PERSIAN_FONT
    PERSIAN_FONT = name or 'Vazirmatn'


def get_persian_font() -> str:
    return PERSIAN_FONT
