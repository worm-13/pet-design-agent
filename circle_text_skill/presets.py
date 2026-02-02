# -*- coding: utf-8 -*-
"""
预设配置模块 - 常用参数预设
"""

# 默认配置模板
DEFAULT_CONFIG = {
    "canvas": {
        "width": 800,
        "height": 800,
        "center": [400, 400],
        "radius": 320
    },

    "phrases": [
        "i love you",
        "i love you",
        "i love you"
    ],

    "layout": {
        "start_angle_deg": 210,
        "clockwise": True,
        "align": "center"
    },

    "spacing": {
        "char_tracking_px": 1.5,
        "word_spacing_px": 24
    },

    "font": {
        "path": "assets/fonts/AaHuanLeBao-2.ttf",
        "size": 48
    },

    "style": {
        "fill_rgba": [248, 170, 180, 230]
    },

    "render": {
        "supersample": 2
    }
}

# 宠物定制预设
PET_CUSTOM_CONFIG = {
    **DEFAULT_CONFIG,
    "canvas": {
        "width": 800,
        "height": 800,
        "center": [400, 400],
        "radius": 280  # 稍微内敛
    },
    "font": {
        "path": "assets/fonts/AaHuanLeBao-2.ttf",
        "size": 42
    },
    "style": {
        "fill_rgba": [255, 182, 193, 255]  # 浅粉色
    }
}

# 徽章设计预设
BADGE_CONFIG = {
    **DEFAULT_CONFIG,
    "canvas": {
        "width": 1024,
        "height": 1024,
        "center": [512, 512],
        "radius": 430
    },
    "phrases": [
        "EXCELLENCE",
        "ACHIEVEMENT",
        "COMMITMENT"
    ],
    "font": {
        "path": "assets/fonts/AaHuanLeBao-2.ttf",
        "size": 52
    },
    "style": {
        "fill_rgba": [255, 215, 0, 255]  # 金色
    }
}

# 品牌LOGO预设
LOGO_CONFIG = {
    **DEFAULT_CONFIG,
    "phrases": [
        "BRAND",
        "NAME"
    ],
    "spacing": {
        "char_tracking_px": 2.0,
        "word_spacing_px": 30
    },
    "style": {
        "fill_rgba": [33, 33, 33, 255]  # 深灰色
    }
}

# 快速配置函数
def get_config_for_pet_name(name: str) -> dict:
    """为宠物名字生成配置"""
    config = PET_CUSTOM_CONFIG.copy()
    # 将名字重复三遍
    config["phrases"] = [name, name, name]
    return config

def get_config_for_badges(texts: list) -> dict:
    """为徽章文本生成配置"""
    config = BADGE_CONFIG.copy()
    config["phrases"] = texts
    return config