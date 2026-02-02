# -*- coding: utf-8 -*-
"""
文字样式调整：在设计图上按指定字体、大小、颜色、位置绘制文字。
支持清除旧文字、文字删除、文字编辑（替换而不是叠加）。
用法: 
  python run_text_style_adjustment.py <设计图路径> <文字内容> [--font-size 30] [--color #000000] [--position center] [--out 输出路径]
  python run_text_style_adjustment.py <设计图路径> "" [--remove]  # 删除所有文字
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

MARGIN = 20
POSITIONS = (
    "top-left", "top-center", "top-right",
    "center",
    "bottom-left", "bottom-center", "bottom-right",
)


def hex_to_rgb(s: str):
    s = s.lstrip("#")
    if len(s) == 6:
        return tuple(int(s[i : i + 2], 16) for i in (0, 2, 4))
    raise ValueError(f"无效颜色: {s}")


def get_text_anchor(cw: int, ch: int, position: str, bbox: tuple):
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if position == "center":
        return cw // 2 - tw // 2, ch // 2 - th // 2
    if position == "top-left":
        return MARGIN, MARGIN
    if position == "top-center":
        return cw // 2 - tw // 2, MARGIN
    if position == "top-right":
        return cw - tw - MARGIN, MARGIN
    if position == "bottom-left":
        return MARGIN, ch - th - MARGIN
    if position == "bottom-center":
        return cw // 2 - tw // 2, ch - th - MARGIN
    if position == "bottom-right":
        return cw - tw - MARGIN, ch - th - MARGIN
    return cw // 2 - tw // 2, ch // 2 - th // 2


def clear_text_at_position(img: Image.Image, draw: ImageDraw.Draw, x: int, y: int, text_bbox: tuple, padding: int = 3):
    """
    清除指定位置的文字区域（精确清除，不填充大块背景）。
    从文字区域周围采样背景色，只清除文字本身的位置。
    """
    w, h = img.size
    tw, th = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
    
    # 从文字区域周围采样背景色（多个点取平均，更准确）
    sample_points = []
    for dx in [-20, 0, 20]:
        for dy in [-20, 0, 20]:
            sx = max(0, min(x + dx, w - 1))
            sy = max(0, min(y + dy, h - 1))
            if (sx < x - padding or sx > x + tw + padding or 
                sy < y - padding or sy > y + th + padding):
                sample_points.append((sx, sy))
    
    if sample_points:
        # 使用第一个采样点的颜色（简化，也可以取平均）
        bg_color = img.getpixel(sample_points[0])
        # 只清除文字区域（精确清除）
        draw.rectangle(
            [x - padding, y - padding, x + tw + padding, y + th + padding],
            fill=bg_color
        )


def run_text_adjustment(
    final_design_image: str,
    text: str = None,
    font_style: str = "Arial",
    font_size: int = 30,
    font_color: str = "#000000",
    position: str = "center",
    out_path: str = None,
    clear_old: bool = True,
    remove: bool = False,
):
    """
    文字样式调整：支持添加、编辑、删除文字。
    
    Args:
        final_design_image: 设计图路径
        text: 文字内容（None 或空字符串表示删除）
        font_style: 字体样式
        font_size: 字体大小
        font_color: 字体颜色
        position: 文字位置
        out_path: 输出路径
        clear_old: 是否清除旧文字（默认 True，替换而不是叠加）
        remove: 是否删除所有文字（如果为 True，忽略 text）
    """
    if not os.path.isfile(final_design_image):
        raise FileNotFoundError(f"设计图不存在: {final_design_image}")

    im = Image.open(final_design_image).convert("RGB")
    cw, ch = im.size
    draw = ImageDraw.Draw(im)
    
    # 如果删除文字或 text 为空，清除文字区域（顶部和底部）
    if remove or not text or text.strip() == "":
        w, h = im.size
        # 获取边缘背景色
        bg_color_top = im.getpixel((w // 2, 10))
        bg_color_bottom = im.getpixel((w // 2, h - 10))
        # 只清除顶部和底部的小区域
        draw.rectangle([0, 0, w, 60], fill=bg_color_top)
        draw.rectangle([0, h - 60, w, h], fill=bg_color_bottom)
        if out_path is None:
            out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
            out_path = os.path.join(out_dir, "final_with_text.png")
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        im.save(out_path)
        print(f"已删除所有文字: {out_path}")
        return out_path
    
    # 准备字体和文字信息
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
    color = (*hex_to_rgb(font_color), 255)
    bbox = draw.textbbox((0, 0), text, font=font)
    x, y = get_text_anchor(cw, ch, position, bbox)
    
    # 清除旧文字（如果启用）：精确清除文字区域
    if clear_old:
        clear_text_at_position(im, draw, x, y, bbox)
    
    # 添加新文字（只绘制文字本身，PIL 的 draw.text() 默认无背景）
    draw.text((x, y), text, fill=color, font=font)

    if out_path is None:
        out_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
        out_path = os.path.join(out_dir, "final_with_text.png")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    im.save(out_path)
    print(f"已保存: {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="文字样式调整：支持添加、编辑、删除文字")
    parser.add_argument("final_design_image", help="最终设计图路径")
    parser.add_argument("text", nargs="?", default="", help="要绘制的文字（空字符串表示删除）")
    parser.add_argument("--font-style", default="Arial", help="字体样式")
    parser.add_argument("--font-size", type=int, default=30, help="字体大小")
    parser.add_argument("--color", default="#000000", help="十六进制颜色，如 #000000")
    parser.add_argument("--position", choices=POSITIONS, default="center", help="文字位置")
    parser.add_argument("--out", default=None, help="输出路径")
    parser.add_argument("--clear-old", action="store_true", default=True, help="清除旧文字（默认启用，替换而不是叠加）")
    parser.add_argument("--no-clear-old", dest="clear_old", action="store_false", help="不清除旧文字（叠加模式）")
    parser.add_argument("--remove", action="store_true", help="删除所有文字（忽略 text 参数）")
    args = parser.parse_args()
    
    run_text_adjustment(
        args.final_design_image,
        args.text if args.text else None,
        args.font_style,
        args.font_size,
        args.color,
        args.position,
        args.out,
        args.clear_old,
        args.remove,
    )


if __name__ == "__main__":
    main()
