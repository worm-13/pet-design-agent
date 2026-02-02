# -*- coding: utf-8 -*-
"""
渲染器模块 - 单字符渲染与旋转
"""
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont
from .geometry import angle_to_position, compute_rotation_angle


def render_char_supersample(
    char: str,
    font,
    fill_rgba: Tuple[int, int, int, int],
    supersample: int = 2
) -> Image.Image:
    """
    超采样渲染单个字符，防止旋转裁切

    Args:
        char: 要渲染的字符
        font: 字体对象
        fill_rgba: RGBA填充色
        supersample: 超采样倍数

    Returns:
        RGBA图像
    """
    # 获取字体度量
    try:
        ascent, descent = font.getmetrics()
        bbox = font.getbbox(char)
        if bbox is None:
            return Image.new("RGBA", (1, 1), (0, 0, 0, 0))

        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
    except:
        ascent = descent = 10
        width = height = 10

    # 计算画布尺寸（超采样 + 防裁切边距）
    pad = int(max(width, height) * 0.8) + 4
    canvas_width = (width + 2 * pad) * supersample
    canvas_height = (height + 2 * pad) * supersample

    # 创建超采样画布
    canvas = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))

    # 放大字体
    try:
        scaled_font = ImageFont.truetype(font.path, font.size * supersample) if hasattr(font, 'path') else font
    except:
        scaled_font = font

    # 绘制文字（居中）
    draw = ImageDraw.Draw(canvas)
    text_x = pad * supersample - bbox[0] * supersample
    text_y = pad * supersample - bbox[1] * supersample

    draw.text((text_x, text_y), char, font=scaled_font, fill=fill_rgba)

    # 缩放回目标尺寸
    final_size = (width + 2 * pad, height + 2 * pad)
    canvas = canvas.resize(final_size, Image.Resampling.LANCZOS)

    return canvas


def draw_single_char(
    image: Image.Image,
    char: str,
    center: Tuple[int, int],
    radius: float,
    angle_rad: float,
    font,
    fill_rgba: Tuple[int, int, int, int],
    clockwise: bool = True,
    supersample: int = 2
):
    """
    在指定角度绘制一个字符（旋转+alpha合成）

    Args:
        image: 目标图像
        char: 要绘制的字符
        center: 圆心坐标
        radius: 圆半径
        angle_rad: 角度（弧度）
        font: 字体对象
        fill_rgba: RGBA填充色
        clockwise: 是否顺时针
        supersample: 超采样倍数
    """
    # 渲染字符
    char_image = render_char_supersample(char, font, fill_rgba, supersample)

    if char_image.width == 0 or char_image.height == 0:
        return

    # 计算位置
    x, y = angle_to_position(center, radius, angle_rad)

    # 计算旋转角度
    rotation_deg = compute_rotation_angle(angle_rad, clockwise)

    # 旋转字符
    char_image = char_image.rotate(
        -rotation_deg,  # PIL旋转方向与数学相反
        resample=Image.Resampling.BICUBIC,
        expand=True
    )

    # 计算粘贴位置
    paste_x = int(x - char_image.width / 2)
    paste_y = int(y - char_image.height / 2)

    # alpha合成
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    image.paste(char_image, (paste_x, paste_y), char_image)


def render_word_on_circle(
    image: Image.Image,
    word: str,
    center: Tuple[int, int],
    radius: float,
    start_angle_rad: float,
    font,
    char_tracking_px: float,
    clockwise: bool = True,
    supersample: int = 2
) -> float:
    """
    从 start_angle 开始渲染一个单词
    返回渲染结束后的角度

    Args:
        image: 目标图像
        word: 要渲染的单词
        center: 圆心坐标
        radius: 圆半径
        start_angle_rad: 起始角度（弧度）
        font: 字体对象
        char_tracking_px: 字符间距
        clockwise: 是否顺时针
        supersample: 超采样倍数

    Returns:
        渲染结束后的角度（弧度）
    """
    current_angle = start_angle_rad
    prev_char = None

    for char in word:
        if not char.strip():
            prev_char = char
            continue

        # 获取字符前进量
        from .font_metrics import get_char_advance
        advance = get_char_advance(char, font, prev_char)

        # 计算字符中心角度
        char_center_angle = current_angle
        if clockwise:
            char_center_angle += (advance / 2) / radius
        else:
            char_center_angle -= (advance / 2) / radius

        # 绘制字符
        fill_rgba = (0, 0, 0, 255)  # 默认黑色，实际应该从参数传入
        draw_single_char(
            image, char, center, radius, char_center_angle,
            font, fill_rgba, clockwise, supersample
        )

        # 更新角度
        angle_increment = (advance + char_tracking_px) / radius
        if clockwise:
            current_angle += angle_increment
        else:
            current_angle -= angle_increment

        prev_char = char

    return current_angle