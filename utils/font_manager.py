# -*- coding: utf-8 -*-
"""字体管理：唯一来源 assets/fonts/ + fonts.json。"""
import json
import os
from PIL import ImageFont

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_DIR = os.path.join(_PROJECT_ROOT, "assets", "fonts")
FONTS_JSON_PATH = os.path.join(FONTS_DIR, "fonts.json")


def _load_registry():
    if not os.path.isfile(FONTS_JSON_PATH):
        return {}
    try:
        with open(FONTS_JSON_PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def load_font(font_id: str, size: int):
    registry = _load_registry()
    fid = (font_id or "").strip() or "default"
    if fid not in registry:
        fid = next(iter(registry), None) if registry else None
    if not fid:
        return ImageFont.load_default()
    path = os.path.join(FONTS_DIR, registry[fid])
    if not os.path.isfile(path):
        for k, v in registry.items():
            if k != fid and os.path.isfile(os.path.join(FONTS_DIR, v)):
                try:
                    return ImageFont.truetype(os.path.join(FONTS_DIR, v), size)
                except Exception:
                    continue
        return ImageFont.load_default()
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()
