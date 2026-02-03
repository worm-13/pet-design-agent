# -*- coding: utf-8 -*-
"""
多宠物合成：将多只宠物抠图结果合成到模板中
支持自动布局和防遮挡
用法: python run_multi_pet_composition.py <session_id>
"""
import argparse
import os
import sys
from PIL import Image
from typing import List, Tuple

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
from utils.multi_pet_layout import create_multi_pet_layout, PetLayout
from utils.visual_center import compute_visual_center
from utils.matting_validation import validate_all_pet_mattings
from utils.multi_pet_enhancement import is_circular_template
from skills.multi_pet_composition_enhancement import MultiPetCompositionEnhancementSkill


def load_extracted_images(session_id: str, pet_ids: List[str]) -> List[Image.Image]:
    """加载所有宠物的抠图结果"""
    extracted_dir = os.path.join("sessions", session_id, "extracted")
    images = []

    for pet_id in pet_ids:
        image_path = os.path.join(extracted_dir, f"{pet_id}_extracted.png")
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"找不到宠物 {pet_id} 的抠图结果: {image_path}")

        image = Image.open(image_path)
        # 确保转换为RGBA模式（如果原图是RGB，添加完全不透明的alpha通道）
        if image.mode == 'RGB':
            # RGB转RGBA：添加完全不透明的alpha通道
            image = image.convert('RGBA')
        elif image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        images.append(image)
        print(f"加载宠物 {pet_id} 抠图结果: {image.size}, 模式: {image.mode}")

    return images


def composite_multi_pets(template_path: str,
                        pet_images: List[Image.Image],
                        layouts: List[PetLayout]) -> Image.Image:
    """
    将多只宠物合成到模板中
    """
    # 打开模板
    template = Image.open(template_path).convert("RGBA")
    template_width, template_height = template.size

    print(f"模板尺寸: {template.size}")

    # 创建结果图像
    result = Image.new("RGBA", (template_width, template_height), (0, 0, 0, 0))
    result.paste(template, (0, 0))

    # 为每只宠物合成
    for i, (pet_image, layout) in enumerate(zip(pet_images, layouts)):
        print(f"合成宠物 {layout.id}: 锚点{layout.anchor}, 缩放{layout.scale}")

        # 确保图像是RGBA模式
        if pet_image.mode != 'RGBA':
            pet_image = pet_image.convert('RGBA')

        # 缩放宠物图像
        scaled_width = int(pet_image.width * layout.scale)
        scaled_height = int(pet_image.height * layout.scale)

        if scaled_width > 0 and scaled_height > 0:
            scaled_pet = pet_image.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

            # 计算缩放后的视觉中心（必须先缩放再计算）
            cx_scaled, cy_scaled = compute_visual_center(scaled_pet)

            # 计算粘贴位置（以视觉中心对齐到锚点）
            # 锚点坐标是相对坐标(0-1)，需要转换为像素坐标
            anchor_x_px = layout.anchor[0] * template_width
            anchor_y_px = layout.anchor[1] * template_height
            
            # 粘贴位置 = 锚点位置 - 缩放后的视觉中心
            paste_x = int(anchor_x_px - cx_scaled)
            paste_y = int(anchor_y_px - cy_scaled)

            # 确保粘贴位置在合理范围内（允许部分超出，但至少有一部分在画布内）
            # 如果完全超出画布，调整到画布边缘
            if paste_x + scaled_width < 0:
                paste_x = -scaled_width + 10  # 至少露出10像素
            if paste_x > template_width:
                paste_x = template_width - 10
            if paste_y + scaled_height < 0:
                paste_y = -scaled_height + 10
            if paste_y > template_height:
                paste_y = template_height - 10

            # 粘贴到结果图（使用alpha通道进行合成）
            result.paste(scaled_pet, (paste_x, paste_y), scaled_pet)

            print(f"  原始尺寸: {pet_image.size}, 缩放后尺寸: {scaled_pet.size}")
            print(f"  视觉中心(缩放后): ({cx_scaled:.1f}, {cy_scaled:.1f})")
            print(f"  锚点像素位置: ({anchor_x_px:.1f}, {anchor_y_px:.1f})")
            print(f"  粘贴位置: ({paste_x}, {paste_y})")

    return result


def run_multi_pet_composition(session_id: str, use_state_layout: bool = False) -> str:
    """
    执行多宠物合成
    use_state_layout: 为 True 时从 state.pets 的 anchor/scale 构建布局（布局调整后重合成时使用）
    返回合成结果路径
    """
    state_manager = StateManager()
    state = state_manager.load_state(session_id)

    if not state.pets:
        raise ValueError(f"会话 {session_id} 中没有宠物配置")

    if not state.template:
        raise ValueError(f"会话 {session_id} 中没有设置模板")

    print(f"开始多宠物合成: {len(state.pets)} 只宠物")

    # 加载宠物抠图结果
    pet_ids = [pet.id for pet in state.pets]
    pet_images = load_extracted_images(session_id, pet_ids)

    # 抠图结果有效性校验（升级方案 模块一）：任一失败即中断，不继续合成
    for_circle = is_circular_template(state.template)
    all_valid, validation_results = validate_all_pet_mattings(
        pet_images, pet_ids, for_circular_template=for_circle
    )
    if not all_valid:
        failed = [r for r in validation_results if not r.valid]
        msg = "抠图结果校验失败，已中断多宠物合成。\n"
        for r in failed:
            msg += f"  - {r.pet_id}: {r.reason}\n"
        msg += "请重新抠图或降级为单宠物流程。"
        raise ValueError(msg)

    # 获取模板尺寸
    template = Image.open(state.template)
    template_size = template.size
    template.close()

    # 获取宠物图像尺寸
    pet_sizes = [(img.width, img.height) for img in pet_images]

    # 布局：优先使用 state 中用户自定义的 anchor/scale（布局调整场景）
    if use_state_layout and state.pets:
        layouts = [
            PetLayout(id=p.id, anchor=p.anchor, scale=p.scale)
            for p in state.pets
        ]
        print("使用 state 中的布局参数:")
    else:
        layouts = create_multi_pet_layout(template_size, len(state.pets), pet_sizes)
        # 将布局 id 对齐到 state.pets（pet_0->pet_a 等）
        for layout, pet in zip(layouts, state.pets):
            layout.id = pet.id
        print("自动布局结果:")

    for layout in layouts:
        print(f"  {layout.id}: 锚点{layout.anchor}, 缩放{layout.scale}")

    # 使用增强技能进行合成（按照文档要求的10步流程）
    print("\n应用多宠物合成增强...")
    enhancement_skill = MultiPetCompositionEnhancementSkill()
    result_image = enhancement_skill.enhance_composition(
        pet_images=pet_images,
        template_path=state.template,
        layouts=layouts,
        enable_edge_cleaning=True,
        enable_feather=True,
        enable_stroke=False,  # 默认关闭，可根据需要开启
        enable_visual_normalization=not use_state_layout,
        enable_group_alignment=not use_state_layout,
        use_state_layout=use_state_layout
    )
    
    print("增强合成完成")

    # 保存结果
    session_dir = os.path.join("sessions", session_id)
    output_path = os.path.join(session_dir, "design.png")
    result_image.save(output_path, "PNG")

    print(f"多宠物合成完成: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="多宠物合成")
    parser.add_argument("session_id", help="会话ID")
    parser.add_argument("--use-state-layout", action="store_true",
                        help="使用 state 中每只宠物的 anchor/scale 作为布局（布局调整后重合成时使用）")
    args = parser.parse_args()

    try:
        output_path = run_multi_pet_composition(args.session_id, use_state_layout=args.use_state_layout)
        print(f"合成结果: {output_path}")
    except Exception as e:
        print(f"合成失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()