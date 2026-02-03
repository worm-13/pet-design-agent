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

# 清新粉蓝模板预设
QINGXIN_FENLAN_CONFIG = {
    "canvas": {
        "width": 800,
        "height": 800,
        "center": [400, 400],  # 图片中心
        "radius": None  # 动态计算：min(width, height) * 0.40
    },
    "phrases": [],  # 动态设置
    "layout": {
        "start_angle_deg": 270,  # 从圆的下方开始（270度 = 6点钟方向）
        "clockwise": True,
        "align": "center",
        "orientation": "outward"
    },
    "spacing": {
        "char_tracking_px": 2.0,
        "word_spacing_px": 20
    },
    "font": {
        "path": "assets/fonts/AaHuanLeBao-2.ttf",
        "size": None  # 动态计算：min(width, height) * 0.08
    },
    "style": {
        "fill_rgba": [255, 182, 193, 255]  # 浅粉色
    },
    "render": {
        "supersample": 2
    }
}

def get_config_for_template(template_name: str, text: str, width: int = 800, height: int = 800) -> dict:
    """
    根据模板名称获取圆形文字配置
    
    Args:
        template_name: 模板名称（如"清新粉蓝"）
        text: 文字内容
        width: 图片宽度
        height: 图片高度
    
    Returns:
        配置字典
    """
    # 检测是否为清新粉蓝模板
    if template_name:
        template_lower = template_name.lower()
        is_qingxin = ("清新粉蓝" in template_name or 
                     "qingxin" in template_lower or 
                     "fenlan" in template_lower)
    else:
        is_qingxin = False
    
    if is_qingxin:
        import copy
        config = copy.deepcopy(QINGXIN_FENLAN_CONFIG)
        
        # 动态计算半径和字体大小
        min_dim = min(width, height)
        config["canvas"]["width"] = width
        config["canvas"]["height"] = height
        config["canvas"]["center"] = [width // 2, height // 2]
        config["canvas"]["radius"] = min_dim * 0.40  # 40%
        config["font"]["size"] = int(min_dim * 0.08)  # 8%
        
        # 设置文字（如果是"lol"则重复4次）
        if text == "lol":
            config["phrases"] = [text] * 4
        else:
            config["phrases"] = [text]
        
        return config
    
    # 默认使用PET_CUSTOM_CONFIG
    import copy
    config = copy.deepcopy(PET_CUSTOM_CONFIG)
    config["canvas"]["width"] = width
    config["canvas"]["height"] = height
    config["canvas"]["center"] = [width // 2, height // 2]
    if text:
        config["phrases"] = [text]
    return config