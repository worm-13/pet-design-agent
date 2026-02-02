# -*- coding: utf-8 -*-
"""
圆形文字排版：Pillow 绘制单字 + OpenCV 旋转与叠加。
算法在 utils/circular_text_algorithm.py，渲染以 Pillow/OpenCV 为核心。
用法:
  python run_circular_text.py <底图路径> <文字> [--radius 200] [--font 字体1] [--out 输出路径]
  python run_circular_text.py <底图> <文字> --use-default-font --out out.png
"""
import argparse
import math
import os
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
from utils.font_manager import load_font
from utils.circular_text_algorithm import generate_circular_text_path


def hex_to_bgra(hex_color: str, a: int = 255) -> tuple:
    s = hex_color.lstrip("#")
    if len(s) == 6:
        r, g, b = int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16)
        return (b, g, r, a)
    return (0, 0, 0, 255)


def draw_char_pillow(char: str, font: ImageFont.FreeTypeFont, color_rgba: tuple) -> np.ndarray:
    """
    Pillow 专门负责高质量文字渲染，返回 RGBA numpy 数组。
    使用最佳的文字渲染设置确保清晰度。
    """
    # 获取精确的文字边界
    bbox = font.getbbox(char)
    if bbox is None:
        return np.zeros((1, 1, 4), dtype=np.uint8)

    # 计算文字尺寸
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # 添加适当的边距，确保旋转后不裁剪
    margin = max(text_width, text_height) // 3 + 2
    canvas_width = text_width + 2 * margin
    canvas_height = text_height + 2 * margin

    # 创建高质量的透明画布
    pil = Image.new("RGBA", (canvas_width, canvas_height), (0, 0, 0, 0))

    # 使用高质量的绘图设置
    draw = ImageDraw.Draw(pil, mode="RGBA")

    # 计算文字在画布上的位置（居中）
    text_x = margin - bbox[0]  # 补偿bbox的左边距
    text_y = margin - bbox[1]  # 补偿bbox的上边距

    # 绘制文字，使用完整的RGBA颜色
    draw.text((text_x, text_y), char, font=font, fill=color_rgba)

    # 返回numpy数组给OpenCV处理
    return np.array(pil)


def rotate_layer_cv2(layer_rgba: np.ndarray, angle_deg: float, center_xy: tuple) -> np.ndarray:
    """
    OpenCV 专门负责高质量几何变换。
    使用最佳插值方法确保旋转后文字清晰度。
    """
    h, w = layer_rgba.shape[:2]

    # 计算旋转矩阵
    M = cv2.getRotationMatrix2D(center_xy, angle_deg, 1.0)

    # 计算旋转后的边界框，确保不裁剪
    cos_angle = abs(M[0, 0])
    sin_angle = abs(M[0, 1])
    new_w = int((h * sin_angle) + (w * cos_angle))
    new_h = int((h * cos_angle) + (w * sin_angle))

    # 调整旋转矩阵以适应新的画布尺寸
    M[0, 2] += (new_w - w) / 2
    M[1, 2] += (new_h - h) / 2

    # 使用高质量的插值方法进行旋转
    rotated = cv2.warpAffine(
        layer_rgba,
        M,
        (new_w, new_h),
        flags=cv2.INTER_CUBIC,  # 使用立方插值获得更好的质量
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0)  # 透明边界
    )

    return rotated


def alpha_blend_roi(base_bgr: np.ndarray, layer_rgba: np.ndarray, x0: int, y0: int) -> None:
    """
    OpenCV 专门负责高效的图像合成。
    使用优化的alpha blending算法，确保高质量的图像合成。
    """
    h, w = layer_rgba.shape[:2]
    H, W = base_bgr.shape[:2]

    # 计算重叠区域
    x1 = min(W, x0 + w)
    y1 = min(H, y0 + h)
    sx0 = max(0, -x0)
    sy0 = max(0, -y0)

    # 如果没有重叠区域，直接返回
    if x1 <= x0 or y1 <= y0 or sx0 >= w or sy0 >= h:
        return

    # 获取重叠区域
    roi = base_bgr[y0:y1, x0:x1]
    frag = layer_rgba[sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0)]

    # 确保尺寸匹配
    if frag.shape[0] != roi.shape[0] or frag.shape[1] != roi.shape[1]:
        return

    # 分离颜色通道和alpha通道
    layer_bgr = frag[:, :, :3][:, :, ::-1]  # RGB to BGR
    alpha = frag[:, :, 3:4].astype(np.float32) / 255.0

    # 优化alpha blending：使用OpenCV风格的计算
    roi_float = roi.astype(np.float32)
    layer_float = layer_bgr.astype(np.float32)

    # 前景 + 背景 * (1 - alpha)
    blended = layer_float * alpha + roi_float * (1 - alpha)

    # 写回结果
    roi[:] = blended.astype(np.uint8)


def draw_circular_text_cv2(
    base_bgr: np.ndarray,
    center_x: float,
    center_y: float,
    layout: list,
    font,
    color_hex: str = "#000000",
) -> None:
    """
    协同工作：Pillow渲染高质量文字，OpenCV进行精确几何变换和合成。
    确保每个字符底部指向圆心，视觉效果自然。
    """
    color_rgba = (*hex_to_bgra(color_hex)[:3][::-1], 255)

    for item in layout:
        ch, x, y = item["char"], item["x"], item["y"]

        # [Pillow] 步骤1：高质量文字渲染
        layer = draw_char_pillow(ch, font, color_rgba)
        orig_h, orig_w = layer.shape[:2]

        # [OpenCV] 步骤2：计算精确的旋转角度（底部指向圆心）
        dx, dy = center_x - x, center_y - y
        rotation_angle = math.degrees(math.atan2(dy, dx))  # 指向圆心的角度

        # [OpenCV] 步骤3：高质量几何旋转
        center_point = (orig_w / 2.0, orig_h / 2.0)
        rotated = rotate_layer_cv2(layer, rotation_angle, center_point)
        rot_h, rot_w = rotated.shape[:2]

        # [OpenCV] 步骤4：计算粘贴位置，确保底部落在圆周上
        # 旋转后的图像底部中点对准圆周上的 (x, y) 点
        paste_x = int(round(x - rot_w / 2.0))
        paste_y = int(round(y - rot_h))  # 底部对齐

        # [OpenCV] 步骤5：高效alpha合成
        alpha_blend_roi(base_bgr, rotated, paste_x, paste_y)


def main():
    parser = argparse.ArgumentParser(description="圆形文字排版（Pillow + OpenCV）")
    parser.add_argument("base_image", help="底图路径")
    parser.add_argument("text", help="要排布的文字")
    parser.add_argument("--center-x", type=float, default=None)
    parser.add_argument("--center-y", type=float, default=None)
    parser.add_argument("--radius", type=float, default=200)
    parser.add_argument("--font", default="default")
    parser.add_argument("--font-size", type=int, default=96)
    parser.add_argument("--color", default="#000000")
    parser.add_argument("--group-count", type=int, default=1)
    parser.add_argument("--group-spacing", type=float, default=12.0)
    parser.add_argument("--char-spacing", type=float, default=15.0)
    parser.add_argument("--start-angle", type=float, default=0.0)
    parser.add_argument("--no-auto-adjust", action="store_true")
    parser.add_argument("--use-default-font", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    base_path = os.path.abspath(args.base_image)
    if not os.path.isfile(base_path):
        print(f"错误: 底图不存在 {base_path}")
        sys.exit(1)

    img = cv2.imread(base_path)
    if img is None:
        print("错误: OpenCV 无法读取底图")
        sys.exit(1)
    h, w = img.shape[:2]
    cx = args.center_x if args.center_x is not None else w / 2
    cy = args.center_y if args.center_y is not None else h / 2

    out_path = args.out
    if out_path:
        out_path = os.path.abspath(out_path)
        if os.path.normpath(out_path) == os.path.normpath(base_path):
            print("错误: 输出路径不能与底图相同")
            sys.exit(1)

    text = (args.text or "").strip()
    if not text:
        if out_path:
            cv2.imwrite(out_path, img)
        print("未输入文字，已复制底图" if out_path else "")
        sys.exit(0)

    if args.use_default_font:
        font = ImageFont.load_default()
    else:
        font = load_font(args.font, args.font_size)
    if not hasattr(font, "getbbox"):
        font = ImageFont.load_default()

    layout, _ = generate_circular_text_path(
        text, cx, cy, args.radius, font,
        group_count=args.group_count,
        letter_spacing_px=args.char_spacing,  # 用字符间距作为像素间距的基础
        group_spacing_deg=args.group_spacing,
        start_angle_deg=args.start_angle,
        auto_adjust=not args.no_auto_adjust,
    )
    if not layout:
        if out_path:
            cv2.imwrite(out_path, img)
        sys.exit(0)

    draw_circular_text_cv2(img, cx, cy, layout, font, color_hex=args.color)
    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        cv2.imwrite(out_path, img)
        print(f"已保存: {out_path}")


if __name__ == "__main__":
    main()
