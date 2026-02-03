# -*- coding: utf-8 -*-
"""
诊断多宠物合成问题
"""
import os
import sys
from PIL import Image

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)

for path in [_SCRIPT_DIR, _PROJECT_ROOT]:
    if path not in sys.path:
        sys.path.insert(0, path)

session_id = "multi_pet_love_v2"
session_dir = os.path.join(_PROJECT_ROOT, "sessions", session_id)

print("=== 诊断多宠物合成问题 ===\n")

# 1. 检查抠图结果
extracted_dir = os.path.join(session_dir, "extracted")
if os.path.exists(extracted_dir):
    extracted_files = [f for f in os.listdir(extracted_dir) if f.endswith('.png')]
    print(f"1. 抠图结果文件数量: {len(extracted_files)}")
    for f in extracted_files:
        img_path = os.path.join(extracted_dir, f)
        img = Image.open(img_path)
        print(f"   - {f}: 尺寸={img.size}, 模式={img.mode}")
else:
    print("1. 抠图目录不存在!")

# 2. 检查设计图
design_path = os.path.join(session_dir, "design.png")
if os.path.exists(design_path):
    design_img = Image.open(design_path)
    print(f"\n2. 设计图: 尺寸={design_img.size}, 模式={design_img.mode}")
    
    # 检查是否有透明区域（可能宠物没合成上去）
    if design_img.mode == 'RGBA':
        alpha = design_img.split()[3]
        # 统计非透明像素
        non_transparent = sum(1 for p in alpha.getdata() if p > 0)
        total = alpha.size[0] * alpha.size[1]
        print(f"   非透明像素: {non_transparent}/{total} ({non_transparent*100/total:.1f}%)")
else:
    print("\n2. 设计图不存在!")

# 3. 检查状态文件
from state_manager import StateManager
state_manager = StateManager()
state = state_manager.load_state(session_id)
print(f"\n3. 状态信息:")
print(f"   宠物数量: {len(state.pets)}")
for pet in state.pets:
    print(f"   - {pet.id}: 图片={os.path.basename(pet.image)}, anchor={pet.anchor}, scale={pet.scale}")
print(f"   模板: {os.path.basename(state.template) if state.template else 'None'}")

# 4. 检查布局计算
if state.template and len(state.pets) > 0:
    template_img = Image.open(state.template)
    template_size = template_img.size
    template_img.close()
    
    print(f"\n4. 布局计算:")
    print(f"   模板尺寸: {template_size}")
    
    from utils.multi_pet_layout import create_multi_pet_layout
    pet_images = []
    for pet in state.pets:
        extracted_path = os.path.join(extracted_dir, f"{pet.id}_extracted.png")
        if os.path.exists(extracted_path):
            pet_img = Image.open(extracted_path)
            pet_images.append(pet_img)
            print(f"   宠物 {pet.id} 抠图尺寸: {pet_img.size}")
    
    if len(pet_images) == len(state.pets):
        pet_sizes = [(img.width, img.height) for img in pet_images]
        layouts = create_multi_pet_layout(template_size, len(state.pets), pet_sizes)
        print(f"   生成的布局:")
        for layout in layouts:
            print(f"     {layout.id}: anchor={layout.anchor}, scale={layout.scale}")
            
        # 5. 检查合成逻辑
        print(f"\n5. 合成位置计算:")
        for i, (pet_img, layout) in enumerate(zip(pet_images, layouts)):
            from utils.visual_center import compute_visual_center
            cx, cy = compute_visual_center(pet_img)
            print(f"   宠物 {layout.id}:")
            print(f"     视觉中心: ({cx:.1f}, {cy:.1f})")
            print(f"     缩放后尺寸: ({int(pet_img.width * layout.scale)}, {int(pet_img.height * layout.scale)})")
            paste_x = int(layout.anchor[0] * template_size[0] - cx * layout.scale)
            paste_y = int(layout.anchor[1] * template_size[1] - cy * layout.scale)
            print(f"     粘贴位置: ({paste_x}, {paste_y})")
            print(f"     是否在画布内: x范围[{paste_x}, {paste_x + int(pet_img.width * layout.scale)}], y范围[{paste_y}, {paste_y + int(pet_img.height * layout.scale)}]")
    
    for img in pet_images:
        img.close()

print("\n=== 诊断完成 ===")
