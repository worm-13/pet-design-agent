# -*- coding: utf-8 -*-
"""查看圆形文字参数"""
import sys
import os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _PROJECT_ROOT)

from PIL import Image

if __name__ == "__main__":
    image_path = sys.argv[1] if len(sys.argv) > 1 else "sessions/session_002/design.png"
    
    img = Image.open(image_path)
    width, height = img.size
    
    # 计算参数
    radius_ratio = 0.40  # 40%
    font_size_ratio = 0.08  # 8%
    
    radius = min(width, height) * radius_ratio
    font_size = int(min(width, height) * font_size_ratio)
    
    print(f"Image size: {width}x{height}")
    print(f"Circle radius: {radius:.1f} pixels ({radius_ratio*100:.0f}% of min dimension)")
    print(f"Font size: {font_size} pixels ({font_size_ratio*100:.0f}% of min dimension)")
    print(f"\nOther parameters:")
    print(f"  - Start angle: 270 degrees (bottom)")
    print(f"  - Position: center")
    print(f"  - Char tracking: 2.0 pixels")
    print(f"  - Word spacing: 20 pixels")
    print(f"  - Repeat count: 4 (for 'lol')")
