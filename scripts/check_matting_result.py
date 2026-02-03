# -*- coding: utf-8 -*-
"""
检查抠图结果：诊断为什么pet_a_extracted.png只有纯背景
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

import sys
if len(sys.argv) > 1:
    session_id = sys.argv[1]
else:
    session_id = "multi_pet_love_v3"
extracted_dir = os.path.join(_PROJECT_ROOT, "sessions", session_id, "extracted")

print("=== 检查抠图结果 ===\n")

# 检查各个步骤的输出
files_to_check = [
    "pet_a_no_bg.png",      # 步骤1：去背景
    "pet_a_extracted.png",  # 步骤2：抠图（或步骤3后）
]

for filename in files_to_check:
    filepath = os.path.join(extracted_dir, filename)
    if os.path.exists(filepath):
        img = Image.open(filepath)
        print(f"{filename}:")
        print(f"  尺寸: {img.size}")
        print(f"  模式: {img.mode}")
        
        if img.mode == 'RGBA':
            # 检查alpha通道
            alpha = np.array(img.split()[3])
            non_transparent = np.sum(alpha > 0)
            total = alpha.size
            print(f"  非透明像素: {non_transparent}/{total} ({non_transparent*100/total:.1f}%)")
            
            # 检查是否有内容（非完全透明）
            if non_transparent == 0:
                print(f"  警告：图像完全透明！")
            elif non_transparent < total * 0.01:
                print(f"  警告：图像几乎完全透明（只有{non_transparent}个像素有内容）")
            else:
                # 检查RGB通道是否有内容
                rgb = np.array(img.convert('RGB'))
                non_black = np.sum(np.any(rgb > 10, axis=2))
                print(f"  非黑色像素: {non_black}/{total} ({non_black*100/total:.1f}%)")
                
                if non_black == 0:
                    print(f"  警告：RGB通道完全黑色，可能只有背景！")
        else:
            print(f"  警告：不是RGBA模式，无法检查透明度")
        
        print()
    else:
        print(f"{filename}: 文件不存在\n")

# 检查步骤3的问题
print("=== 问题分析 ===")
print("步骤3再次调用run_background_removal可能导致问题：")
print("如果步骤2的输出已经是透明背景PNG，")
print("background-remover可能会把整个图像都处理成透明背景。")
print("\n建议：")
print("1. 检查步骤2的输出（抠图结果）是否已经有透明背景")
print("2. 如果步骤2输出正常，应该跳过步骤3")
print("3. 或者步骤3应该使用不同的逻辑（只清理边缘，而不是重新去背景）")
