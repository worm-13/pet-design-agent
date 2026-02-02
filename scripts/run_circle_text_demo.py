# -*- coding: utf-8 -*-
"""
演示三种填充模式的区别
"""
import os
import sys
from PIL import Image

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from utils.circle_text import draw_circular_text

def demo_fit_modes():
    """演示三种填充模式的区别"""
    # 加载底图
    base_path = "output/final.png"
    if not os.path.exists(base_path):
        print(f"错误: 找不到 {base_path}")
        return

    base_image = Image.open(base_path).convert("RGBA")
    width, height = base_image.size
    center = (width // 2, height // 2)
    radius = min(width, height) * 0.35

    # 配置参数
    text = "love"
    font_path = "assets/fonts/AaHuanLeBao-2.ttf"
    font_size = 48
    fill_rgba = (0, 0, 0, 255)
    start_angle_deg = 0
    clockwise = True
    tracking_px = 15.0
    align = "center"
    supersample = 2

    modes = [
        ("none", "普通模式：单个单词"),
        ("repeat_fill", "重复填满：头接尾分布"),
        ("equal_angle", "等角度分布：等分圆周")
    ]

    print("演示三种填充模式的区别：")
    print(f"文本: '{text}'")
    print(f"半径: {radius:.1f}px")

    for mode, description in modes:
        print(f"\n--- {description} ---")

        try:
            result = draw_circular_text(
                base_image=base_image,
                text=text,
                center=center,
                radius=radius,
                font_path=font_path,
                font_size=font_size,
                fill_rgba=fill_rgba,
                start_angle_deg=start_angle_deg,
                clockwise=clockwise,
                tracking_px=tracking_px,
                align=align,
                fit_mode=mode,
                supersample=supersample,
            )

            output_path = f"output/demo_{mode}.png"
            result.save(output_path, "PNG")
            print(f"[OK] 已保存: {output_path}")

        except Exception as e:
            print(f"[ERROR] 失败: {e}")

if __name__ == "__main__":
    demo_fit_modes()