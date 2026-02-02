# -*- coding: utf-8 -*-
"""
字体度量模块 - 字符advance/kerning计算
"""
from PIL import ImageFont


def get_char_advance(
    char: str,
    font: ImageFont.FreeTypeFont,
    prev_char: str = None
) -> float:
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
        # 优先使用font.getlength获取真实advance
        if hasattr(font, 'getlength'):
            advance = font.getlength(char)

            # 如果有前一个字符，计算kerning修正
            if prev_char:
                try:
                    pair_advance = font.getlength(prev_char + char)
                    kerning_adjust = pair_advance - (font.getlength(prev_char) + advance)
                    advance += kerning_adjust
                except:
                    pass  # kerning计算失败，使用基础advance

            return max(0.0, advance)
        else:
            # 降级到bbox方式（不推荐）
            bbox = font.getbbox(char)
            return float(bbox[2] - bbox[0]) if bbox else 0.0

    except Exception:
        return 0.0


def measure_phrase_arc(
    phrase: str,
    font: ImageFont.FreeTypeFont,
    char_tracking_px: float,
    word_spacing_px: float
) -> float:
    """
    计算一个短语在圆上的总弧长（像素）

    Args:
        phrase: 短语文本
        font: 字体对象
        char_tracking_px: 字符间距
        word_spacing_px: 单词间距

    Returns:
        短语总弧长（像素）
    """
    if not phrase:
        return 0.0

    # 按空格分割单词
    words = [word.strip() for word in phrase.split() if word.strip()]

    if not words:
        return 0.0

    total_arc = 0.0
    prev_char = None

    for word in words:
        # 计算单词内字符的总长度
        for char in word:
            advance = get_char_advance(char, font, prev_char)
            total_arc += advance + char_tracking_px
            prev_char = char

        # 单词间距（除了最后一个单词）
        if word != words[-1]:
            total_arc += word_spacing_px

    # 减去最后一个字符的tracking，因为单词结束后不需要额外的字符间距
    if words:
        total_arc -= char_tracking_px

    return max(0.0, total_arc)