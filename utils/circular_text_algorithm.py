# -*- coding: utf-8 -*-
"""圆形文字排版算法：基于真实字体度量的精确布局，字符底部指向圆心。"""
import math
from typing import Any, List, Dict, Tuple
from PIL import ImageFont


def get_char_pixel_width(char: str, font: ImageFont.FreeTypeFont) -> float:
    """获取字符的实际像素宽度（包括字间距）。"""
    if not char or not hasattr(font, "getbbox"):
        return 0.0
    try:
        bbox = font.getbbox(char)
        if bbox:
            return float(bbox[2] - bbox[0])
        return 0.0
    except Exception:
        return 0.0


def get_char_arc_angle(char: str, font: ImageFont.FreeTypeFont, radius: float, letter_spacing_px: float = 0.0) -> float:
    """
    计算字符在圆周上占用的角度（度）。
    角度 = (弧长 / 圆周长) * 360°，弧长 = 字符像素宽度 + 额外间距。
    """
    width_px = get_char_pixel_width(char, font)
    arc_length = width_px + letter_spacing_px
    circumference = 2.0 * math.pi * radius
    if circumference <= 0:
        return 0.0
    return (arc_length / circumference) * 360.0


def get_group_arc_angle(text: str, font: ImageFont.FreeTypeFont, radius: float,
                        letter_spacing_px: float = 0.0, group_spacing_deg: float = 10.0) -> float:
    """计算一组文字占用的总角度（度）。"""
    if not text:
        return group_spacing_deg
    total_char_angle = sum(get_char_arc_angle(c, font, radius, letter_spacing_px) for c in text)
    return total_char_angle + group_spacing_deg


def optimize_circular_layout(text: str, font: ImageFont.FreeTypeFont, radius: float,
                           letter_spacing_px: float = 2.0, group_spacing_deg: float = 10.0) -> Dict[str, Any]:
    """
    优化布局参数，确保文字均匀分布在圆周上。
    返回最佳的组数和参数。
    """
    if not text or radius <= 0:
        return {"group_count": 1, "letter_spacing_px": letter_spacing_px, "group_spacing_deg": group_spacing_deg}

    # 计算单组角度
    group_angle = get_group_arc_angle(text, font, radius, letter_spacing_px, group_spacing_deg)

    # 尝试不同组数，找到最合适的
    best_group_count = 1
    best_score = float('inf')

    for group_count in range(1, 13):  # 最多12组
        total_angle = group_count * group_angle
        if total_angle > 360:
            break

        # 计算剩余角度和均匀度评分
        remaining = 360.0 - total_angle
        if remaining < 0:
            continue

        # 均匀度评分：剩余角度越小越好，但也要考虑组间分布
        score = abs(remaining) + abs(group_count - 1) * 5  # 偏好单组

        if score < best_score:
            best_score = score
            best_group_count = group_count

    return {
        "group_count": best_group_count,
        "letter_spacing_px": letter_spacing_px,
        "group_spacing_deg": group_spacing_deg
    }


def generate_circular_text_layout(text: str, center_x: float, center_y: float, radius: float,
                                 font: ImageFont.FreeTypeFont, *,
                                 group_count: int = 1,
                                 letter_spacing_px: float = 2.0,
                                 group_spacing_deg: float = 10.0,
                                 start_angle_deg: float = 0.0) -> List[Dict[str, Any]]:
    """
    生成圆形文字布局：基于真实字体度量，每个字符底部指向圆心。
    返回字符布局列表，每个包含位置和旋转角度。
    """
    layout: List[Dict[str, Any]] = []
    if not text or radius <= 0:
        return layout

    # 获取优化参数
    optimized = optimize_circular_layout(text, font, radius, letter_spacing_px, group_spacing_deg)
    group_count = optimized["group_count"]
    letter_spacing_px = optimized["letter_spacing_px"]
    group_spacing_deg = optimized["group_spacing_deg"]

    # 计算每组的起始角度，确保均匀分布
    group_angle = get_group_arc_angle(text, font, radius, letter_spacing_px, group_spacing_deg)
    total_groups_angle = group_count * group_angle

    # 如果总角度小于360度，将其居中
    offset_angle = (360.0 - total_groups_angle) / 2.0

    for group_idx in range(group_count):
        # 组起始角度
        group_start = start_angle_deg + offset_angle + group_idx * group_angle
        current_angle = group_start

        for char_idx, char in enumerate(text):
            # 字符角度跨度
            char_angle = get_char_arc_angle(char, font, radius, letter_spacing_px)
            if char_angle <= 0:
                continue

            # 字符中心角度
            char_center_angle = current_angle + char_angle / 2.0

            # 计算字符位置（在圆周上）
            rad = math.radians(char_center_angle - 90.0)  # 0° = 圆顶
            x = center_x + radius * math.cos(rad)
            y = center_y + radius * math.sin(rad)

            layout.append({
                "char": char,
                "x": round(x, 3),
                "y": round(y, 3),
                "angle": round(char_center_angle, 3),
                "groupIndex": group_idx,
                "charIndex": char_idx
            })

            # 更新到下一个字符起始角度
            current_angle += char_angle

    return layout


def generate_circular_text_path(text: str, center_x: float, center_y: float, radius: float,
                               font: ImageFont.FreeTypeFont, *,
                               group_count: int = 1,
                               letter_spacing_px: float = 2.0,
                               group_spacing_deg: float = 10.0,
                               start_angle_deg: float = 0.0,
                               auto_adjust: bool = True) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    一站式圆形文字布局生成。
    auto_adjust=True 时会自动优化参数。
    """
    if auto_adjust:
        optimized = optimize_circular_layout(text, font, radius, letter_spacing_px, group_spacing_deg)
        group_count = optimized["group_count"]
        letter_spacing_px = optimized["letter_spacing_px"]
        group_spacing_deg = optimized["group_spacing_deg"]

    layout = generate_circular_text_layout(
        text, center_x, center_y, radius, font,
        group_count=group_count,
        letter_spacing_px=letter_spacing_px,
        group_spacing_deg=group_spacing_deg,
        start_angle_deg=start_angle_deg
    )

    params = {
        "group_count": group_count,
        "letter_spacing_px": letter_spacing_px,
        "group_spacing_deg": group_spacing_deg,
        "auto_adjust": auto_adjust
    }

    return layout, params
