# -*- coding: utf-8 -*-
"""
对齐多宠物视觉中心到同一水平线
用法: python align_pets_horizontal.py <session_id>
"""
import argparse
import os
import sys
from PIL import Image

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)

for path in [_SCRIPT_DIR, _PROJECT_ROOT]:
    if path not in sys.path:
        sys.path.insert(0, path)

from state_manager import StateManager
from utils.visual_center import compute_visual_center
from run_pet_layout_adjustment import adjust_pet_layout


def align_pets_to_same_horizontal(session_id: str) -> str:
    """
    调整两只宠物的位置，使它们的视觉中心处于同一水平
    调用现有的skill功能实现
    
    Args:
        session_id: 会话ID
    
    Returns:
        重新合成后的设计图路径
    """
    state_manager = StateManager()
    state = state_manager.load_state(session_id)
    
    if len(state.pets) < 2:
        raise ValueError(f"需要至少2只宠物，当前只有{len(state.pets)}只")
    
    print(f"对齐 {len(state.pets)} 只宠物的视觉中心到同一水平...")
    
    # 加载宠物图像和模板
    extracted_dir = os.path.join("sessions", session_id, "extracted")
    template = Image.open(state.template)
    template_size = template.size
    template.close()
    
    # 先运行一次合成以获取实际的布局参数（包括视觉面积归一化后的scale）
    from run_multi_pet_composition import run_multi_pet_composition
    from utils.multi_pet_layout import create_multi_pet_layout
    
    # 加载宠物图像
    pet_images = []
    pet_ids = [pet.id for pet in state.pets]
    for pet_id in pet_ids:
        pet_image_path = os.path.join(extracted_dir, f"{pet_id}_extracted.png")
        if not os.path.exists(pet_image_path):
            raise FileNotFoundError(f"找不到宠物 {pet_id} 的抠图结果: {pet_image_path}")
        pet_image = Image.open(pet_image_path).convert('RGBA')
        pet_images.append(pet_image)
    
    # 获取实际布局（包括增强功能应用后的）
    pet_sizes = [(img.width, img.height) for img in pet_images]
    layouts = create_multi_pet_layout(template_size, len(state.pets), pet_sizes)
    
    # 应用增强功能获取实际的scale（视觉面积归一化等）
    from skills.multi_pet_composition_enhancement import MultiPetCompositionEnhancementSkill
    enhancement_skill = MultiPetCompositionEnhancementSkill()
    
    # 临时计算以获取归一化后的scale（不实际合成）
    from utils.multi_pet_enhancement import normalize_visual_areas
    base_scales = [layout.scale for layout in layouts]
    normalized_scales = normalize_visual_areas(pet_images, base_scales)
    for layout, new_scale in zip(layouts, normalized_scales):
        layout.scale = new_scale
    
    # 计算每只宠物在当前布局下的视觉中心Y坐标（使用state中的实际anchor位置）
    pet_visual_centers_y = []
    
    for i, (pet_image, layout) in enumerate(zip(pet_images, layouts)):
        pet = state.pets[i]
        # 使用实际的scale缩放图像
        scaled_width = int(pet_image.width * layout.scale)
        scaled_height = int(pet_image.height * layout.scale)
        scaled_pet = pet_image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
        
        # 计算缩放后的视觉中心（相对于缩放后图像）
        cx_local, cy_local = compute_visual_center(scaled_pet)
        
        # 转换为模板坐标系（使用state中的anchor，因为这是当前实际的位置）
        anchor_x_px = pet.anchor[0] * template_size[0]
        anchor_y_px = pet.anchor[1] * template_size[1]
        
        # 视觉中心在模板中的Y坐标
        pet_center_y = anchor_y_px - (scaled_height / 2 - cy_local)
        
        pet_visual_centers_y.append(pet_center_y)
        
        print(f"  宠物 {pet.id}: 当前视觉中心Y = {pet_center_y:.1f}px (scale={layout.scale:.3f})")
    
    # 计算平均Y坐标（目标水平线）
    target_y = sum(pet_visual_centers_y) / len(pet_visual_centers_y)
    target_y_relative = target_y / template_size[1]
    
    print(f"\n目标水平线Y = {target_y:.1f}px (相对坐标: {target_y_relative:.3f})")
    
    # 调整每只宠物的Y坐标，使视觉中心对齐到目标水平线
    adjustments = []
    
    for i, (pet_image, layout) in enumerate(zip(pet_images, layouts)):
        pet = state.pets[i]
        # 使用实际的scale缩放图像
        scaled_width = int(pet_image.width * layout.scale)
        scaled_height = int(pet_image.height * layout.scale)
        scaled_pet = pet_image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)
        
        # 计算缩放后的视觉中心
        cx_local, cy_local = compute_visual_center(scaled_pet)
        
        # 计算需要的anchor Y坐标，使视觉中心对齐到目标水平线
        # target_y = anchor_y_px - (scaled_height / 2 - cy_local)
        # 所以: anchor_y_px = target_y + (scaled_height / 2 - cy_local)
        needed_anchor_y_px = target_y + (scaled_height / 2 - cy_local)
        needed_anchor_y = needed_anchor_y_px / template_size[1]
        
        # 限制在合理范围内
        needed_anchor_y = max(0.1, min(0.9, needed_anchor_y))
        
        # 保持X坐标不变，只调整Y坐标
        new_anchor = (pet.anchor[0], needed_anchor_y)
        
        print(f"调整宠物 {pet.id}: Y坐标从 {pet.anchor[1]:.3f} 到 {needed_anchor_y:.3f}")
        
        adjustments.append((pet.id, new_anchor))
    
    # 一次性更新所有宠物的位置（调用现有的skill功能）
    for pet_id, new_anchor in adjustments:
        state_manager.update_pet_layout(session_id, pet_id, anchor=new_anchor)
    
    # 重新合成（调用现有的合成功能）
    design_path = run_multi_pet_composition(session_id)
    
    print(f"\n对齐完成！结果: {design_path}")
    return design_path


def main():
    parser = argparse.ArgumentParser(description="对齐多宠物视觉中心到同一水平")
    parser.add_argument("session_id", help="会话ID")
    
    args = parser.parse_args()
    
    try:
        result_path = align_pets_to_same_horizontal(args.session_id)
        print(f"\n完成！结果已保存到: {result_path}")
    except Exception as e:
        print(f"对齐失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
