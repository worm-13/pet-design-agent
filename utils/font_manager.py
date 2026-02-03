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


def get_font_path(font_id_or_path: str) -> str:
    """将字体 ID（如「字体2」）或路径解析为完整字体文件路径。"""
    if not font_id_or_path or not isinstance(font_id_or_path, str):
        return None
    s = font_id_or_path.strip()
    if not s:
        return None
    # 已是绝对路径且存在
    if os.path.isabs(s) and os.path.isfile(s):
        return s
    # 按 ID 从 fonts.json 查找
    registry = _load_registry()
    if s in registry:
        p = os.path.join(FONTS_DIR, registry[s])
        return p if os.path.isfile(p) else None
    # 相对路径：项目根、fonts 目录、或仅文件名
    candidates = [
        os.path.join(_PROJECT_ROOT, s),
        os.path.join(FONTS_DIR, s),
        os.path.join(FONTS_DIR, os.path.basename(s)),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


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
