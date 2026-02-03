# -*- coding: utf-8 -*-
"""
测试多宠物合成核心算法
验证视觉面积归一化和组合视觉中心对齐算法
"""
import os
import sys
from PIL import Image

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)

for path in [_SCRIPT_DIR, _PROJECT_ROOT]:
    if path not in sys.path:
        sys.path.insert(0, path)

from utils.multi_pet_enhancement import (
    compute_visual_area,
    normalize_visual_areas,
    compute_group_visual_center,
    align_group_to_template_center
)
from utils.multi_pet_layout import PetLayout


def test_visual_area_computation():
    """测试视觉面积计算"""
    print("=" * 60)
    print("测试1: 视觉面积计算（基于 alpha mask）")
    print("=" * 60)
    
    # 加载测试图像
    session_id = "session_002"
    extracted_dir = os.path.join("sessions", session_id, "extracted")
    
    pet_a_path = os.path.join(extracted_dir, "pet_a_extracted.png")
    pet_b_path = os.path.join(extracted_dir, "pet_b_extracted.png")
    
    if not os.path.exists(pet_a_path) or not os.path.exists(pet_b_path):
        print("警告: 找不到测试图像，跳过测试")
        return
    
    pet_a = Image.open(pet_a_path).convert('RGBA')
    pet_b = Image.open(pet_b_path).convert('RGBA')
    
    # 计算视觉面积（alpha_threshold=20，忽略半透明毛边）
    area_a = compute_visual_area(pet_a, alpha_threshold=20)
    area_b = compute_visual_area(pet_b, alpha_threshold=20)
    
    print(f"pet_a 视觉面积: {area_a:.0f} 像素")
    print(f"pet_b 视觉面积: {area_b:.0f} 像素")
    print(f"面积比例 (a/b): {area_a/area_b:.3f}")
    
    # 几何尺寸对比
    print(f"\n几何尺寸对比:")
    print(f"pet_a: {pet_a.size} = {pet_a.width * pet_a.height} 像素")
    print(f"pet_b: {pet_b.size} = {pet_b.width * pet_b.height} 像素")
    print(f"几何比例 (a/b): {(pet_a.width * pet_a.height)/(pet_b.width * pet_b.height):.3f}")
    
    print("\n[完成] 视觉面积计算测试完成\n")


def test_visual_area_normalization():
    """测试视觉面积归一化"""
    print("=" * 60)
    print("测试2: 视觉面积归一化（使用 sqrt 修正 scale）")
    print("=" * 60)
    
    session_id = "session_002"
    extracted_dir = os.path.join("sessions", session_id, "extracted")
    
    pet_a_path = os.path.join(extracted_dir, "pet_a_extracted.png")
    pet_b_path = os.path.join(extracted_dir, "pet_b_extracted.png")
    
    if not os.path.exists(pet_a_path) or not os.path.exists(pet_b_path):
        print("警告: 找不到测试图像，跳过测试")
        return
    
    pet_a = Image.open(pet_a_path).convert('RGBA')
    pet_b = Image.open(pet_b_path).convert('RGBA')
    
    pet_images = [pet_a, pet_b]
    base_scales = [1.0, 1.0]  # 初始 scale
    
    print(f"基础 scale: {base_scales}")
    
    # 归一化（使用第一只作为参考）
    normalized_scales = normalize_visual_areas(pet_images, base_scales, reference_index=0)
    
    print(f"归一化后 scale: {normalized_scales}")
    print(f"scale 变化比例: {[n/b for n, b in zip(normalized_scales, base_scales)]}")
    
    # 验证：归一化后的视觉面积应该更接近
    area_a = compute_visual_area(pet_a, alpha_threshold=20)
    area_b = compute_visual_area(pet_b, alpha_threshold=20)
    
    # 归一化后的视觉面积 = 原始面积 * scale^2
    normalized_area_a = area_a * (normalized_scales[0] ** 2)
    normalized_area_b = area_b * (normalized_scales[1] ** 2)
    
    print(f"\n归一化后的视觉面积:")
    print(f"pet_a: {normalized_area_a:.0f} 像素")
    print(f"pet_b: {normalized_area_b:.0f} 像素")
    print(f"面积比例 (a/b): {normalized_area_a/normalized_area_b:.3f}")
    
    print("\n[完成] 视觉面积归一化测试完成\n")


def test_group_visual_center():
    """测试组合视觉中心计算和对齐"""
    print("=" * 60)
    print("测试3: 组合视觉中心计算和对齐")
    print("=" * 60)
    
    session_id = "session_002"
    extracted_dir = os.path.join("sessions", session_id, "extracted")
    
    pet_a_path = os.path.join(extracted_dir, "pet_a_extracted.png")
    pet_b_path = os.path.join(extracted_dir, "pet_b_extracted.png")
    
    if not os.path.exists(pet_a_path) or not os.path.exists(pet_b_path):
        print("警告: 找不到测试图像，跳过测试")
        return
    
    pet_a = Image.open(pet_a_path).convert('RGBA')
    pet_b = Image.open(pet_b_path).convert('RGBA')
    
    pet_images = [pet_a, pet_b]
    
    # 创建测试布局
    template_size = (800, 800)  # 假设模板尺寸
    layouts = [
        PetLayout(id="pet_0", anchor=(0.35, 0.5), scale=0.4),
        PetLayout(id="pet_1", anchor=(0.65, 0.6), scale=0.3)
    ]
    
    print(f"初始布局:")
    for layout in layouts:
        print(f"  {layout.id}: anchor={layout.anchor}, scale={layout.scale}")
    
    # 计算组合视觉中心
    group_center = compute_group_visual_center(pet_images, layouts, template_size)
    print(f"\n组合视觉中心: ({group_center[0]:.1f}, {group_center[1]:.1f}) px")
    print(f"模板中心: ({template_size[0]/2:.1f}, {template_size[1]/2:.1f}) px")
    
    # 对齐到模板中心
    aligned_layouts = align_group_to_template_center(pet_images, layouts, template_size)
    
    print(f"\n对齐后的布局:")
    for layout in aligned_layouts:
        print(f"  {layout.id}: anchor={layout.anchor}, scale={layout.scale}")
    
    # 验证对齐后的组合中心
    new_group_center = compute_group_visual_center(pet_images, aligned_layouts, template_size)
    print(f"\n对齐后的组合视觉中心: ({new_group_center[0]:.1f}, {new_group_center[1]:.1f}) px")
    print(f"模板中心: ({template_size[0]/2:.1f}, {template_size[1]/2:.1f}) px")
    print(f"偏移量: ({abs(new_group_center[0] - template_size[0]/2):.1f}, {abs(new_group_center[1] - template_size[1]/2):.1f}) px")
    
    print("\n[完成] 组合视觉中心测试完成\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("多宠物合成核心算法测试")
    print("=" * 60 + "\n")
    
    try:
        test_visual_area_computation()
        test_visual_area_normalization()
        test_group_visual_center()
        
        print("=" * 60)
        print("所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
