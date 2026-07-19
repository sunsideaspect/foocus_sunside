"""Sunside product-mode helpers: slim styles and sizes."""
from __future__ import annotations

import os
import re

import args_manager

PRODUCT_STYLE_FILES = (
    'sdxl_styles_sunside.json',
    'sdxl_styles_fooocus.json',
)

# From Fooocus pack keep only Semi Realistic in product mode
PRODUCT_FOOOCUS_ALLOW = {
    'Fooocus Semi Realistic',
}

SIZE_PRESETS = [
    ('Story 768×1344', 768, 1344),
    ('Square 1024×1024', 1024, 1024),
    ('Landscape 1344×768', 1344, 768),
    ('Landing 1216×832', 1216, 832),
]

SIZE_PRESET_LABELS = [x[0] for x in SIZE_PRESETS]
SIZE_PRESET_MAP = {label: (w, h) for label, w, h in SIZE_PRESETS}

MIN_DIM = 512
MAX_DIM = 1536


def is_product_mode() -> bool:
    if os.environ.get('SUNSIDE_PRODUCT', '').strip() in ('0', 'false', 'False'):
        return False
    return bool(getattr(args_manager.args, 'sunside_product', True))


def clamp_dim(value: int) -> int:
    try:
        v = int(value)
    except (TypeError, ValueError):
        return -1
    if v <= 0:
        return -1
    v = max(MIN_DIM, min(MAX_DIM, v))
    # SDXL-friendly multiple of 8
    return max(MIN_DIM, (v // 8) * 8)


def sanitize_export_slug(text: str) -> str:
    text = (text or '').strip().lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    return text.strip('_')[:48] or 'sunside'


def build_export_prefix(character_name: str | None, styles: list | None) -> str:
    parts = []
    if character_name:
        parts.append(sanitize_export_slug(character_name))
    sunside = None
    for s in styles or []:
        if isinstance(s, str) and s.startswith('Sunside '):
            sunside = sanitize_export_slug(s.replace('Sunside ', ''))
            break
    if sunside:
        parts.append(sunside)
    return '_'.join(parts) if parts else 'sunside'


def filter_product_styles(styles: dict) -> dict:
    """Keep Sunside styles + allowed Fooocus quality styles."""
    out = {}
    for name, value in styles.items():
        if name.startswith('Sunside '):
            out[name] = value
        elif name in PRODUCT_FOOOCUS_ALLOW:
            out[name] = value
    return out
