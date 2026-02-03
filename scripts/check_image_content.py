# -*- coding: utf-8 -*-
"""
检查图像内容：诊断RGB图像是否有实际内容
"""
import os
import sys
from PIL import Image
import numpy as np

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)

for path in [_SCRIPT_DIR, _PROJECT_ROOT]:
    if path not in sys.path:
        sys.path.insert(0, path)

session_id = sys.argv[1] if len(sys.argv) > 1 else "multi_pet_love_v3"
filepath = os.path.join(_PROJECT_ROOT, "sessions", session_id, "extracted", "pet_a_extracted.png")

print(f"检查文件: {filepath}\n")

if os.path.exists(filepath):
    img = Image.open(filepath)
    print(f"尺寸: {img.size}")
    print(f"模式: {img.mode}")
    
    # 转换为numpy数组
    img_array = np.array(img)
    
    if img.mode == 'RGB':
        # 检查RGB通道
        # 计算非白色/非黑色像素
        white_threshold = 250
        black_threshold = 5
        
        # 非白色像素（可能有内容）
        non_white = np.sum(np.any(img_array < white_threshold, axis=2))
        # 非黑色像素（可能有内容）
        non_black = np.sum(np.any(img_array > black_threshold, axis=2))
        
        total = img_array.shape[0] * img_array.shape[1]
        print(f"总像素数: {total}")
        print(f"非白色像素: {non_white} ({non_white*100/total:.1f}%)")
        print(f"非黑色像素: {non_black} ({non_black*100/total:.1f}%)")
        
        # 检查是否主要是白色或黑色
        if non_white < total * 0.01:
            print("警告：图像几乎完全是白色（可能是纯背景）")
        elif non_black < total * 0.01:
            print("警告：图像几乎完全是黑色")
        else:
            # 检查颜色分布
            unique_colors = len(np.unique(img_array.reshape(-1, 3), axis=0))
            print(f"唯一颜色数: {unique_colors}")
            if unique_colors < 10:
                print("警告：颜色种类很少，可能是纯色背景")
            else:
                print("图像似乎有内容")
    
    elif img.mode == 'RGBA':
        # 检查alpha通道
        alpha = img_array[:, :, 3]
        non_transparent = np.sum(alpha > 0)
        total = alpha.size
        print(f"非透明像素: {non_transparent}/{total} ({non_transparent*100/total:.1f}%)")
        
        if non_transparent == 0:
            print("警告：图像完全透明")
        elif non_transparent < total * 0.01:
            print("警告：图像几乎完全透明")
        else:
            # 检查RGB内容
            rgb = img_array[:, :, :3]
            non_white = np.sum(np.any(rgb < 250, axis=2))
            print(f"非白色像素: {non_white}/{total} ({non_white*100/total:.1f}%)")
            if non_white == 0:
                print("警告：RGB通道完全是白色")
else:
    print("文件不存在")
