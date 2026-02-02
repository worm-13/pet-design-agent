# -*- coding: utf-8 -*-
"""
CircleTextLayoutSkill 主模块
三层圆形文字排版Skill
"""
from typing import List, Optional
from PIL import Image, ImageFont
from .geometry import compute_phrase_anchor_angles, normalize_angle
from .font_metrics import measure_phrase_arc
from .renderer import render_word_on_circle


class CircleTextLayoutSkill:
    """
    CircleTextLayoutSkill - 三层圆形文字排版Skill

    短语级均分 + 单词级间距 + 字符级高精度排版
    """

    def render(
        self,
        base_image: Optional[Image.Image],
        config: dict
    ) -> Image.Image:
        """
        根据配置，在圆环上渲染三层结构文字

        Args:
            base_image: 基础图像，如果为None则创建空白画布
            config: 配置字典

        Returns:
            渲染完成的图像
        """
        # 解析配置
        canvas_config = config.get("canvas", {})
        phrases = config.get("phrases", [])
        layout_config = config.get("layout", {})
        spacing_config = config.get("spacing", {})
        font_config = config.get("font", {})
        style_config = config.get("style", {})
        render_config = config.get("render", {})

        # 画布设置
        width = canvas_config.get("width", 800)
        height = canvas_config.get("height", 800)
        center = tuple(canvas_config.get("center", [width//2, height//2]))
        radius = canvas_config.get("radius", min(width, height) * 0.4)

        # 创建或使用基础图像
        if base_image is None:
            result_image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        else:
            result_image = base_image.convert("RGBA")
            if result_image.size != (width, height):
                result_image = result_image.resize((width, height), Image.Resampling.LANCZOS)

        # 布局设置
        start_angle_deg = layout_config.get("start_angle_deg", 0)
        clockwise = layout_config.get("clockwise", True)
        align = layout_config.get("align", "center")

        # 间距设置
        char_tracking_px = spacing_config.get("char_tracking_px", 1.5)
        word_spacing_px = spacing_config.get("word_spacing_px", 24)

        # 字体设置
        font_path = font_config.get("path", "assets/fonts/AaHuanLeBao-2.ttf")
        font_size = font_config.get("size", 48)

        # 加载字体
        try:
            font = ImageFont.truetype(font_path, font_size)
        except:
            font = ImageFont.load_default()

        # 样式设置
        fill_rgba = tuple(style_config.get("fill_rgba", [0, 0, 0, 255]))

        # 渲染设置
        supersample = render_config.get("supersample", 2)

        # 计算短语锚点角度
        phrase_count = len(phrases)
        if phrase_count == 0:
            return result_image

        anchor_angles = compute_phrase_anchor_angles(
            phrase_count, start_angle_deg, clockwise
        )

        # 渲染每个短语
        for i, phrase in enumerate(phrases):
            if not phrase.strip():
                continue

            anchor_angle = anchor_angles[i]

            # 计算短语弧长
            phrase_arc = measure_phrase_arc(
                phrase, font, char_tracking_px, word_spacing_px
            )

            # 计算短语起始角度（居中对齐）
            if align == "center":
                phrase_start_angle = anchor_angle - phrase_arc / (2 * radius)
            else:
                phrase_start_angle = anchor_angle

            # 标准化角度
            phrase_start_angle = normalize_angle(phrase_start_angle)

            # 渲染短语
            self._render_phrase(
                result_image, phrase, center, radius, phrase_start_angle,
                font, char_tracking_px, word_spacing_px, fill_rgba,
                clockwise, supersample
            )

        return result_image

    def _render_phrase(
        self,
        image: Image.Image,
        phrase: str,
        center: tuple,
        radius: float,
        start_angle_rad: float,
        font,
        char_tracking_px: float,
        word_spacing_px: float,
        fill_rgba: tuple,
        clockwise: bool,
        supersample: int
    ):
        """
        渲染单个短语

        Args:
            image: 目标图像
            phrase: 短语文本
            center: 圆心坐标
            radius: 圆半径
            start_angle_rad: 起始角度（弧度）
            font: 字体对象
            char_tracking_px: 字符间距
            word_spacing_px: 单词间距
            fill_rgba: 填充色
            clockwise: 是否顺时针
            supersample: 超采样倍数
        """
        # 按空格分割单词
        words = [word.strip() for word in phrase.split() if word.strip()]

        current_angle = start_angle_rad

        for word in words:
            if not word:
                continue

            # 渲染单词
            end_angle = render_word_on_circle(
                image, word, center, radius, current_angle,
                font, char_tracking_px, clockwise, supersample
            )

            # 添加单词间距（除了最后一个单词）
            if word != words[-1]:
                spacing_angle = word_spacing_px / radius
                if clockwise:
                    current_angle = end_angle + spacing_angle
                else:
                    current_angle = end_angle - spacing_angle
            else:
                current_angle = end_angle