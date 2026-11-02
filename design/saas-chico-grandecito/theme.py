"""Brand theme for the deck generator. Swap this file to reuse build.py for another brand.

Paths are relative to this folder. Every value must come from the brand's design system.
"""
from pathlib import Path

HERE = Path(__file__).parent
SYSTEM = HERE.parent / 'refactoria-design-system'

BRAND = 'RefactorIA'
# Wordmark HTML: plain text with the accented part in <b>. No space between parts.
WORDMARK = 'Refactor<b>IA</b>'
LOGO = HERE / 'assets' / 'refactoria-mark.svg'
# Optional ASCII/braille texture for the cover and watermark. Set to None to skip it.
TEXTURE = HERE / 'assets' / 'refactoria-braille.txt'

SANS = 'Inter'
MONO = 'FiraCode Nerd Font Mono Beard'
# (family, weight, woff2 path). Embedded as base64, so the deck works offline.
FONTS = [
    (SANS, 400, SYSTEM / 'fonts' / 'inter-regular.woff2'),
    (SANS, 500, SYSTEM / 'fonts' / 'inter-medium.woff2'),
    (MONO, 400, SYSTEM / 'fonts' / 'FiraCodeNerdFontMonoBeard-Regular.woff2'),
]

COLORS = dict(
    background='#0b0714', background_2='#17102a', background_3='#2c2144',
    text='#ffffff', text_2='rgba(255,255,255,.6)', border='rgba(255,255,255,.2)',
    brand='#7127ff', brand_glow='113,39,255', spark='#ffb547', paper='#f2effa',
)
