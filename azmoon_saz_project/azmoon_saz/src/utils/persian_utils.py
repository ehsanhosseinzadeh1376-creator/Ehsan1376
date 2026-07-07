"""
ابزارهای فارسی
Persian text utilities.

On modern Windows/Mac Tk (8.6.10+), a proper Persian font (Vazirmatn)
natively handles shaping and RTL. `fa()` is a no-op by default.

On older systems where shaping doesn't work, users can enable
compatibility mode which will apply arabic-reshaper + bidi to labels.
"""
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_PERSIAN_RESHAPE = True
except ImportError:
    HAS_PERSIAN_RESHAPE = False

# Global state - can be toggled via config
_RESHAPE_ENABLED = True  # default ON: needed for tk RTL rendering on most platforms


def set_reshape_mode(enabled: bool):
    """
    Enable/disable manual reshaping.
    Default is OFF because modern Tk with Vazirmatn handles Persian natively.
    Turn ON only for compatibility with old systems.
    """
    global _RESHAPE_ENABLED
    _RESHAPE_ENABLED = enabled


def get_reshape_mode() -> bool:
    return _RESHAPE_ENABLED


def fa(text) -> str:
    """
    Prepare Persian text for Label display.
    In modern mode (default): pass-through (font handles rendering).
    In compat mode: apply arabic-reshaper + bidi for old Tk.
    """
    if text is None:
        return ''
    text = str(text)
    if not text:
        return text
    if not _RESHAPE_ENABLED or not HAS_PERSIAN_RESHAPE:
        return text
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


def fa_textbox(text) -> str:
    """
    Prepare Persian text for CTkTextbox (Text widget) display.
    Text widget doesn't do native RTL on any platform, so we ALWAYS
    apply reshape + bidi here regardless of global setting.
    """
    if text is None:
        return ''
    text = str(text)
    if not text:
        return text
    if not HAS_PERSIAN_RESHAPE:
        return text
    try:
        # Reshape+bidi each line separately so multi-line text works
        lines = text.split('\n')
        out = []
        for line in lines:
            if line.strip():
                try:
                    reshaped = arabic_reshaper.reshape(line)
                    out.append(get_display(reshaped))
                except Exception:
                    out.append(line)
            else:
                out.append(line)
        return '\n'.join(out)
    except Exception:
        return text


def fa_number(num) -> str:
    """Convert English digits to Persian digits."""
    en = '0123456789'
    fa_digits = '۰۱۲۳۴۵۶۷۸۹'
    result = str(num)
    for e, f in zip(en, fa_digits):
        result = result.replace(e, f)
    return result


def truncate(text: str, length: int = 60) -> str:
    """Truncate long text with ellipsis."""
    if text is None:
        return ''
    text = str(text)
    if len(text) <= length:
        return text
    return text[:length] + '…'


def fix_persian_text(text: str) -> str:
    """
    Fix Persian text that might be in visual order (reversed) or has other
    common PDF extraction issues.
    """
    if not text:
        return text

    # Heuristic: if a large portion of the text is Persian and looks reversed
    # (e.g., ends with characters that usually start a sentence), we might
    # need to flip it. However, simple reversal often breaks things if
    # there are numbers or English words.

    # A common issue in some PDFs is that characters are stored in visual order.
    # We'll use a simple heuristic: if many lines start with Persian punctuation
    # that usually appears at the end (like ؟ or .), it might be reversed.

    lines = text.split('\n')
    fixed_lines = []

    for line in lines:
        # Check if line seems reversed.
        # This is a very basic heuristic.
        if line.strip().startswith(('؟', '!', '.')) and not line.strip().endswith(('؟', '!', '.')):
            # Likely reversed visual order
            # Note: proper RTL reversal is complex, here we do a simple character reverse
            # as a starting point for "messed up" text.
            fixed_lines.append(line[::-1])
        else:
            fixed_lines.append(line)

    return '\n'.join(fixed_lines)
