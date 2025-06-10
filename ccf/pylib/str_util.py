import re

import ftfy


def clean(text):
    text = ftfy.fix_text(text)  # Handle common mojibake
    text = re.sub(r"[–—\-]+", "-", text)
    text = text.replace("±", "+/-")
    text = text.replace("×", "x")
    text = text.replace("\xa0", " ")  # Non-breaking space
    text = text.replace("\xad", "")  # Soft hyphen
    return text
