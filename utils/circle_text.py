# -*- coding: utf-8 -*-
"""
高精度圆形文字排版算法
基于真实glyph advance和kerning，支持超采样渲染和居中对齐
"""
import math
from typing import Tuple, List, Dict, Any
from PIL import Image, ImageDraw, ImageFont


def get_char_advance(char: str, font: ImageFont.FreeTypeFont, prev_char: str = None) -> float:
    """
    获取字符的真实前进量（advance），优先使用font.getlength，支持kerning修正

    Args:
        char: 当前字符
        font: 字体对象
        prev_char: 前一个字符，用于kerning计算

    Returns:
        字符前进量（像素）
    """
    if not char:
        return 0.0

    try:
        # 使用font.getlength获取基础advance
        if hasattr(font, 'getlength'):
            advance = font.getlength(char)
        else:
            # 降级到bbox方式（不推荐）
            bbox = font.getbbox(char)
            advance = float(bbox[2] - bbox[0]) if bbox else 0.0

        # 如果有前一个字符，计算kerning修正
        if prev_char:
            try:
                pair_advance = font.getlength(prev_char + char)
                kerning_adjust = pair_advance - (font.getlength(prev_char) + advance)
                advance += kerning_adjust
            except:
                pass  # kerning计算失败，使用基础advance

        return max(0.0, advance)
    except Exception:
        return 0.0


def calculate_text_arc_length(text: str, font: ImageFont.FreeTypeFont, tracking_px: float = 0.0) -> float:
    """
    计算文本的总弧长

    Args:
        text: 文本内容
        font: 字体对象
        tracking_px: 字符间距

    Returns:
        总弧长（像素）
    """
    if not text:
        return 0.0

    total_length = 0.0
    prev_char = None

    for char in text:
        advance = get_char_advance(char, font, prev_char)
        total_length += advance + tracking_px
        prev_char = char

    return total_length


def calculate_position_and_rotation(center: Tuple[int, int], radius: float, angle_rad: float,
                                   clockwise: bool = True) -> Tuple[float, float, float]:
    """
    计算字符位置和旋转角度

    Args:
        center: 圆心坐标 (x, y)
        radius: 圆半径
        angle_rad: 角度（弧度）
        clockwise: 是否顺时针

    Returns:
        (x, y, rotation_deg) 位置坐标和旋转角度
    """
    cx, cy = center

    # 计算位置
    x = cx + radius * math.cos(angle_rad)
    y = cy + radius * math.sin(angle_rad)

    # 计算旋转角度（字符沿切线方向）
    if clockwise:
        rotation_deg = math.degrees(angle_rad) + 90
    else:
        rotation_deg = math.degrees(angle_rad) - 90

    return x, y, rotation_deg


def render_char_supersample(char: str, font: ImageFont.FreeTypeFont,
                           fill_rgba: Tuple[int, int, int, int],
                           supersample: int = 2) -> Image.Image:
    """
    超采样渲染单个字符，防止旋转裁切

    Args:
        char: 要渲染的字符
        font: 字体对象
        fill_rgba: RGBA颜色
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
    scaled_font = ImageFont.truetype(font.path, font.size * supersample) if hasattr(font, 'path') else font

    # 绘制文字（居中）
    draw = ImageDraw.Draw(canvas)
    text_x = pad * supersample - bbox[0] * supersample
    text_y = pad * supersample - bbox[1] * supersample

    draw.text((text_x, text_y), char, font=scaled_font, fill=fill_rgba)

    # 缩放回目标尺寸
    final_size = (width + 2 * pad, height + 2 * pad)
    canvas = canvas.resize(final_size, Image.Resampling.LANCZOS)

    return canvas


def draw_circular_text(
    base_image: Image.Image,
    text: str,
    center: Tuple[int, int],
    radius: float,
    font_path: str,
    font_size: int,
    fill_rgba: Tuple[int, int, int, int],
    start_angle_deg: float,
    clockwise: bool = True,
    tracking_px: float = 0.0,
    align: str = "center",
    fit_mode: str = "none",
    supersample: int = 2,
) -> Image.Image:
    """
    绘制圆形文字的高精度实现

    Args:
        base_image: 底图（PIL Image）
        text: 要排版的文本
        center: 圆心坐标 (x, y)
        radius: 圆半径
        font_path: 字体文件路径
        font_size: 字体大小
        fill_rgba: RGBA填充色
        start_angle_deg: 起始角度（度）
        clockwise: 是否顺时针
        tracking_px: 字符间距（像素）
        align: 对齐方式 "center" 或 "start"
        fit_mode: 填充模式 "none" | "repeat_fill" | "equal_angle"
        supersample: 超采样倍数

    Returns:
        合成后的图像
    """
    if not text:
        return base_image.copy()

    # 加载字体
    try:
        font = ImageFont.truetype(font_path, font_size)
    except:
        font = ImageFont.load_default()

    # 处理fit_mode：自动重复填满整圈 或 等角度分布
    angle_step_rad = None  # 等角度模式下的角度步长
    if fit_mode == "repeat_fill":
        text, tracking_px = _fit_text_to_circle(text, font, radius, tracking_px)
    elif fit_mode == "equal_angle":
        text, angle_step_rad = _distribute_equal_angle(text, font, tracking_px)

    # 计算起始角度（考虑对齐）
    start_angle_rad = math.radians(start_angle_deg)
    if align == "center":
        total_arc_length = calculate_text_arc_length(text, font, tracking_px)
        center_offset_rad = total_arc_length / (2 * radius)
        if clockwise:
            start_angle_rad -= center_offset_rad
        else:
            start_angle_rad += center_offset_rad

    # 创建结果图像
    result = base_image.copy()

    if fit_mode == "equal_angle" and angle_step_rad is not None:
        # 等角度分布模式：将文本分组，每个组占用相同的角度
        word_groups = text.split(" · ")  # 按分隔符分组
        num_groups = len(word_groups)

        for i, word in enumerate(word_groups):
            if not word.strip():
                continue

            # 计算这个单词的角度位置（等分360度）
            word_angle_rad = start_angle_rad + i * angle_step_rad

            # 在单词内居中对齐
            word_arc_length = calculate_text_arc_length(word, font, tracking_px)
            word_center_offset = word_arc_length / (2 * radius)
            if clockwise:
                word_start_rad = word_angle_rad - word_center_offset
            else:
                word_start_rad = word_angle_rad + word_center_offset

            # 绘制单词内的每个字符
            current_angle_rad = word_start_rad
            prev_char = None

            for char in word:
                if not char.strip():
                    prev_char = char
                    continue

                # 获取字符前进量
                advance = get_char_advance(char, font, prev_char)

                # 计算字符中心角度
                char_center_rad = current_angle_rad
                if clockwise:
                    char_center_rad += (advance / 2) / radius
                else:
                    char_center_rad -= (advance / 2) / radius

                # 计算位置和旋转
                x, y, rotation_deg = calculate_position_and_rotation(
                    center, radius, char_center_rad, clockwise
                )

                # 渲染字符
                char_image = render_char_supersample(char, font, fill_rgba, supersample)

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
                result.paste(char_image, (paste_x, paste_y), char_image)

                # 更新角度
                angle_increment = (advance + tracking_px) / radius
                if clockwise:
                    current_angle_rad += angle_increment
                else:
                    current_angle_rad -= angle_increment

                prev_char = char
    else:
        # 普通模式：按字符长度推进
        current_angle_rad = start_angle_rad
        prev_char = None

        for char in text:
            if not char.strip():  # 跳过空白字符
                prev_char = char
                continue

        # 获取字符前进量
        advance = get_char_advance(char, font, prev_char)

        # 计算字符中心角度
        char_center_rad = current_angle_rad
        if clockwise:
            char_center_rad += (advance / 2) / radius
        else:
            char_center_rad -= (advance / 2) / radius

        # 计算位置和旋转
        x, y, rotation_deg = calculate_position_and_rotation(
            center, radius, char_center_rad, clockwise
        )

        # 渲染字符
        char_image = render_char_supersample(char, font, fill_rgba, supersample)

        # 旋转字符
        char_image = char_image.rotate(
            -rotation_deg,  # PIL旋转方向与数学相反
            resample=Image.Resampling.BICUBIC,
            expand=True
        )

        # 计算粘贴位置（字符中心对准计算位置）
        paste_x = int(x - char_image.width / 2)
        paste_y = int(y - char_image.height / 2)

        # alpha合成
        result.paste(char_image, (paste_x, paste_y), char_image)

        # 更新角度
        angle_increment = (advance + tracking_px) / radius
        if clockwise:
            current_angle_rad += angle_increment
        else:
            current_angle_rad -= angle_increment

        prev_char = char

    return result


def _fit_text_to_circle(text: str, font: ImageFont.FreeTypeFont, radius: float,
                       base_tracking: float) -> Tuple[str, float]:
    """
    自动调整文本和间距，使其填满整圈

    Args:
        text: 原始文本
        font: 字体对象
        radius: 圆半径
        base_tracking: 基础间距

    Returns:
        (调整后的文本, 调整后的间距)
    """
    if not text:
        return text, base_tracking

    circumference = 2 * math.pi * radius
    base_length = calculate_text_arc_length(text, font, base_tracking)

    # 如果文本太长，重复添加分隔符
    if base_length < circumference * 0.8:  # 留20%空间用于调整
        separator = " · "
        repeated_text = text
        while True:
            test_text = repeated_text + separator + text
            test_length = calculate_text_arc_length(test_text, font, base_tracking)
            if test_length > circumference * 0.95:
                break
            repeated_text = test_text

        text = repeated_text
        current_length = calculate_text_arc_length(text, font, base_tracking)
    else:
        current_length = base_length

    # 微调tracking使刚好填满
    if current_length > 0:
        target_length = circumference
        extra_space = target_length - current_length
        char_count = len(text)
        tracking_adjust = extra_space / char_count

        # 限制调整范围
        tracking_adjust = max(-1.5, min(tracking_adjust, 3.0))
        final_tracking = base_tracking + tracking_adjust
    else:
        final_tracking = base_tracking

    return text, final_tracking


def _distribute_equal_angle(text: str, font: ImageFont.FreeTypeFont, tracking_px: float) -> Tuple[str, float]:
    """
    等角度分布：将输入文本按空格分割成单词，每个单词等角度分布在圆周上

    Args:
        text: 输入文本（如"i love you"）
        font: 字体对象
        tracking_px: 基础间距

    Returns:
        (处理后的文本如"i · love · you", 角度步长弧度)
    """
    if not text:
        return text, 2 * math.pi

    # 按空格分割输入文本，过滤空字符串
    words = [word.strip() for word in text.split() if word.strip()]

    if not words:
        return text, 2 * math.pi

    # 如果输入包含多个单词，当作一个整体单位重复
    # 否则（单个单词）按原来的逻辑重复
    if len(words) > 1:
        # 多单词输入：当作一个整体单位重复
        base_phrase = text.strip()  # 保持原格式
        # 计算短语的弧长
        phrase_arc_length = calculate_text_arc_length(base_phrase, font, tracking_px)

        # 分隔符 - 短语间使用更大的间距
        separator = "        ·        "  # 8个空格创造更大的短语间距
        separator_length = calculate_text_arc_length(separator, font, tracking_px)

        # 计算圆周长（使用更大的半径来估算，避免低估）
        circumference = 2 * math.pi * 400  # 使用400作为估算半径，确保有足够空间

        # 优先选择3个重复
        count = 3
        total_length = count * phrase_arc_length + (count - 1) * separator_length

        # 如果太长，减少数量，但优先保持3个
        while total_length > circumference * 1.2 and count > 2:  # 增加容忍度到120%，优先保持3个
            count -= 1
            total_length = count * phrase_arc_length + (count - 1) * separator_length

        # 生成重复文本
        if count == 1:
            repeated_text = base_phrase
        else:
            repeated_text = (base_phrase + separator) * (count - 1) + base_phrase

        # 返回角度步长
        angle_step = 2 * math.pi / count

        return repeated_text, angle_step

    # 如果只有一个单词，当作基础单词重复
    elif len(words) == 1:
        base_word = words[0]
        # 计算单个单词的弧长
        word_arc_length = calculate_text_arc_length(base_word, font, tracking_px)

        # 分隔符
        separator = " · "
        separator_length = calculate_text_arc_length(separator, font, tracking_px)

        # 计算圆周长（使用标准半径100来估算）
        circumference = 2 * math.pi * 100

        # 计算最多可以放多少个单词
        max_count = max(1, int(circumference / (word_arc_length + separator_length)))

        # 选择合适的数量：优先3、4、6、8等视觉上好看的数量
        preferred_counts = [3, 4, 6, 8, 2, 5, 7]
        best_count = 3  # 默认3个

        for count in preferred_counts:
            if count > max_count:
                break
            total_length = count * word_arc_length + (count - 1) * separator_length
            if total_length <= circumference * 0.9:  # 留10%空间
                best_count = count
            else:
                break

        # 生成重复文本
        if best_count == 1:
            repeated_text = base_word
        else:
            repeated_text = (base_word + separator) * (best_count - 1) + base_word

        # 返回角度步长
        angle_step = 2 * math.pi / best_count

    else:
        # 多个单词的情况：直接用" · "连接
        repeated_text = " · ".join(words)
        # 返回角度步长（每个单词的角度间隔）
        angle_step = 2 * math.pi / len(words)

    return repeated_text, angle_step


# 预设参数配置
PRESETS = {
    "english_rounded": {
        "font_path": "assets/fonts/AaHuanLeBao-2.ttf",  # 假设有圆润字体
        "font_size": 48,
        "fill_rgba": (248, 170, 180, 255),  # 淡粉色
        "start_angle_deg": 220,  # 从左上开始
        "clockwise": True,
        "tracking_px": 2.0,
        "align": "center",
        "fit_mode": "repeat_fill",
        "supersample": 2,
    },
    "chinese_calligraphy": {
        "font_path": "assets/fonts/AaHuanLeBao-2.ttf",
        "font_size": 52,
        "fill_rgba": (100, 100, 100, 220),  # 灰色带透明
        "start_angle_deg": 180,
        "clockwise": True,
        "tracking_px": 3.0,
        "align": "center",
        "fit_mode": "none",
        "supersample": 2,
    }
}