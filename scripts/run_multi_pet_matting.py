# -*- coding: utf-8 -*-
"""
多宠物抠图：支持对多只宠物进行批量抠图
用法: python run_multi_pet_matting.py <session_id>
"""
import argparse
import os
import sys
from typing import List

# 统一使用 UTF-8，避免中文路径与打印乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# 确保脚本目录和项目根目录在 path 中
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)

for path in [_SCRIPT_DIR, _PROJECT_ROOT]:
    if path not in sys.path:
        sys.path.insert(0, path)

from state_manager import StateManager
from run_background_removal import run_background_removal
from run_pet_image_matting import run_matting
from PIL import Image
import numpy as np
from utils.visual_center import compute_visual_center


def make_square_1to1(image_path: str, out_path: str = None) -> str:
    """
    将抠图结果调整为1:1比例（正方形）
    使用视觉中心（而非边界框中心）来对齐，确保宠物头部在正方形中心
    
    Args:
        image_path: 输入图像路径
        out_path: 输出路径（如果为None，则覆盖原文件）
    
    Returns:
        输出文件路径
    """
    img = Image.open(image_path)
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    data = np.array(img)
    
    # 找到非透明像素的边界框
    alpha_channel = data[:, :, 3]
    non_transparent = np.where(alpha_channel > 0)
    
    if len(non_transparent[0]) == 0:
        # 如果没有非透明像素，直接返回原图
        print(f"  警告: 图像完全透明，跳过1:1调整")
        if out_path and out_path != image_path:
            img.save(out_path, "PNG")
            return out_path
        return image_path
    
    min_y, max_y = non_transparent[0].min(), non_transparent[0].max()
    min_x, max_x = non_transparent[1].min(), non_transparent[1].max()
    
    # 计算边界框的宽度和高度
    bbox_width = max_x - min_x + 1
    bbox_height = max_y - min_y + 1
    
    # 使用最大边作为正方形的边长
    square_size = max(bbox_width, bbox_height)
    
    # 计算视觉中心（基于alpha通道加权的质心，更能反映宠物头部的实际中心）
    visual_center_x, visual_center_y = compute_visual_center(img)
    
    # 创建正方形画布（透明背景）
    square_img = Image.new('RGBA', (square_size, square_size), (0, 0, 0, 0))
    
    # 计算在新画布中的粘贴位置（使视觉中心对齐到画布中心）
    # 新画布中心位置
    square_center_x = square_size / 2
    square_center_y = square_size / 2
    
    # 计算粘贴位置：使视觉中心对齐到画布中心
    paste_x = int(square_center_x - visual_center_x)
    paste_y = int(square_center_y - visual_center_y)
    
    # 确保粘贴位置不会超出画布（允许部分超出，但至少有一部分在画布内）
    if paste_x + img.width < 0:
        paste_x = -img.width + 10
    if paste_x > square_size:
        paste_x = int(square_size - 10)
    if paste_y + img.height < 0:
        paste_y = -img.height + 10
    if paste_y > square_size:
        paste_y = int(square_size - 10)
    
    # 将原图粘贴到正方形画布上
    square_img.paste(img, (paste_x, paste_y), img)
    
    # 保存结果
    if out_path is None:
        out_path = image_path
    
    square_img.save(out_path, "PNG")
    print(f"  步骤4完成: 已调整为1:1比例 ({square_size}x{square_size})，视觉中心对齐")
    return out_path


def run_multi_pet_matting(session_id: str) -> List[str]:
    """
    对会话中的所有宠物进行抠图
    返回抠图结果路径列表
    """
    state_manager = StateManager()
    state = state_manager.load_state(session_id)

    if not state.pets:
        raise ValueError(f"会话 {session_id} 中没有宠物配置")

    output_paths = []

    # 为每个宠物创建抠图输出目录
    session_dir = os.path.join("sessions", session_id)
    extracted_dir = os.path.join(session_dir, "extracted")
    os.makedirs(extracted_dir, exist_ok=True)

    print(f"开始为 {len(state.pets)} 只宠物进行抠图...")

    for pet in state.pets:
        print(f"处理宠物 {pet.id}: {pet.image}")
        
        # 步骤1: 去除背景
        no_bg_filename = f"{pet.id}_no_bg.png"
        no_bg_path = os.path.join(extracted_dir, no_bg_filename)
        print(f"  步骤1: 去除背景 -> {no_bg_path}")
        try:
            no_bg_path = run_background_removal(pet.image, no_bg_path)
            print(f"  步骤1完成: 背景已去除")
        except Exception as e:
            print(f"  步骤1失败: {e}")
            raise
        
        # 步骤2: 抠出主体（使用去背景后的图）
        matting_output_filename = f"{pet.id}_matting_temp.png"
        matting_output_path = os.path.join(extracted_dir, matting_output_filename)
        print(f"  步骤2: 抠出主体 -> {matting_output_path}")
        try:
            matting_result_path = run_matting(
                image_path=no_bg_path,  # 使用去背景后的图
                pet_type=pet.crop_mode,
                out_path=matting_output_path
            )
            print(f"  步骤2完成: 主体已抠出")
        except Exception as e:
            print(f"  步骤2失败: {e}")
            raise
        
        # 步骤3: 再次去除背景（确保边缘干净，方便最终本地图层合并）
        output_filename = f"{pet.id}_extracted.png"
        output_path = os.path.join(extracted_dir, output_filename)
        print(f"  步骤3: 再次去除背景（确保边缘干净） -> {output_path}")
        try:
            final_path = run_background_removal(matting_result_path, output_path)
            
            # 检查结果是否还有内容（防止完全透明）
            result_img = Image.open(final_path)
            if result_img.mode != 'RGBA':
                result_img = result_img.convert('RGBA')
            data = np.array(result_img)
            non_transparent_pixels = np.sum(data[:, :, 3] > 0)
            total_pixels = data.shape[0] * data.shape[1]
            non_transparent_ratio = non_transparent_pixels / total_pixels
            
            if non_transparent_ratio < 0.01:  # 如果非透明像素少于1%
                print(f"  警告: 第三次去背景后图像几乎完全透明 ({non_transparent_ratio*100:.2f}%)，使用步骤2的结果作为兜底")
                import shutil
                shutil.copy2(matting_result_path, output_path)
                final_path = output_path
            else:
                print(f"  步骤3完成: 背景已再次去除，边缘已清理（非透明像素: {non_transparent_ratio*100:.2f}%）")
            
            # 步骤4: 调整为1:1比例（正方形）
            print(f"  步骤4: 调整为1:1比例 -> {output_path}")
            try:
                final_path = make_square_1to1(final_path, output_path)
                print(f"  步骤4完成: 已调整为1:1比例")
            except Exception as e:
                print(f"  步骤4失败: {e}，使用原图")
                # 如果调整失败，继续使用原图
            
            output_paths.append(final_path)
        except Exception as e:
            print(f"  步骤3失败: {e}")
            # 如果第三次去背景失败，使用步骤2的结果作为兜底
            print(f"  警告: 第三次去背景失败，使用步骤2的结果作为兜底")
            import shutil
            shutil.copy2(matting_result_path, output_path)
            final_path = output_path
            
            # 步骤4: 调整为1:1比例（正方形）
            print(f"  步骤4: 调整为1:1比例 -> {output_path}")
            try:
                final_path = make_square_1to1(final_path, output_path)
                print(f"  步骤4完成: 已调整为1:1比例")
            except Exception as e:
                print(f"  步骤4失败: {e}，使用原图")
                # 如果调整失败，继续使用原图
            
            output_paths.append(final_path)
        
        print(f"宠物 {pet.id} 处理完成")

    print(f"所有宠物抠图完成，共 {len(output_paths)} 张结果")
    return output_paths


def main():
    parser = argparse.ArgumentParser(description="多宠物抠图")
    parser.add_argument("session_id", help="会话ID")
    args = parser.parse_args()

    try:
        output_paths = run_multi_pet_matting(args.session_id)
        print(f"抠图结果: {output_paths}")
    except Exception as e:
        print(f"抠图失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()