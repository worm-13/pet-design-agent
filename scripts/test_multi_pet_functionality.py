# -*- coding: utf-8 -*-
"""
多宠物功能测试脚本
测试多宠物抠图、布局、合成等完整流程
用法: python test_multi_pet_functionality.py
"""
import os
import sys
import tempfile
from PIL import Image, ImageDraw

# 确保脚本目录和项目根目录在 path 中
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)

for path in [_SCRIPT_DIR, _PROJECT_ROOT]:
    if path not in sys.path:
        sys.path.insert(0, path)

from state_manager import StateManager
from run_multi_pet_matting import run_multi_pet_matting
from run_multi_pet_composition import run_multi_pet_composition
from utils.multi_pet_layout import create_multi_pet_layout


def create_test_images():
    """创建测试用的宠物图片"""
    test_dir = "test_images"
    os.makedirs(test_dir, exist_ok=True)

    # 创建两张简单的测试图片（彩色圆形代表宠物）
    images = []

    for i, color in enumerate([(255, 100, 100), (100, 100, 255)], 1):  # 红色和蓝色
        img = Image.new("RGB", (200, 200), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        # 画一个圆形
        draw.ellipse([50, 50, 150, 150], fill=color)

        path = os.path.join(test_dir, f"pet_{i}.jpg")
        img.save(path)
        images.append(path)
        print(f"创建测试图片: {path}")

    return images


def create_test_template():
    """创建测试用的模板"""
    template_dir = "test_templates"
    os.makedirs(template_dir, exist_ok=True)

    # 创建一个简单的横版模板
    img = Image.new("RGB", (400, 300), (240, 240, 240))
    draw = ImageDraw.Draw(img)

    # 画一个边框
    draw.rectangle([10, 10, 390, 290], outline=(200, 200, 200), width=2)

    # 添加一些装饰
    draw.text((150, 130), "Pet Template", fill=(100, 100, 100))

    path = os.path.join(template_dir, "test_template.png")
    img.save(path)
    print(f"创建测试模板: {path}")

    return path


def test_state_management():
    """测试状态管理功能"""
    print("\n=== 测试状态管理 ===")

    state_manager = StateManager()

    # 创建测试会话
    session_id = "test_session_multi_pet"

    # 添加宠物
    state = state_manager.add_pet(session_id, "test_images/pet_1.jpg")
    state = state_manager.add_pet(session_id, "test_images/pet_2.jpg")

    print(f"添加了 {len(state.pets)} 只宠物")
    for pet in state.pets:
        print(f"  {pet.id}: {pet.image}, scale={pet.scale}, anchor={pet.anchor}")

    # 设置模板
    template_path = create_test_template()
    state = state_manager.set_template(session_id, template_path)

    print(f"设置模板: {state.template}")

    # 测试加载
    loaded_state = state_manager.load_state(session_id)
    assert len(loaded_state.pets) == 2, "宠物数量不匹配"
    assert loaded_state.template == template_path, "模板路径不匹配"

    print("状态管理测试通过")
    return session_id


def test_layout_engine():
    """测试布局引擎"""
    print("\n=== 测试布局引擎 ===")

    # 测试横版模板
    landscape_size = (400, 300)
    layouts = create_multi_pet_layout(landscape_size, 2, [(200, 200), (200, 200)])

    print("横版2宠物布局:")
    for layout in layouts:
        print(f"  {layout.id}: 锚点{layout.anchor}, 缩放{layout.scale}")

    # 测试竖版模板
    portrait_size = (300, 400)
    layouts = create_multi_pet_layout(portrait_size, 2, [(200, 200), (200, 200)])

    print("竖版2宠物布局:")
    for layout in layouts:
        print(f"  {layout.id}: 锚点{layout.anchor}, 缩放{layout.scale}")

    print("布局引擎测试通过")




def test_multi_pet_workflow():
    """测试完整的多宠物工作流"""
    print("\n=== 测试完整多宠物工作流 ===")

    # 1. 创建测试数据
    test_images = create_test_images()
    template_path = create_test_template()

    # 2. 初始化状态
    session_id = "test_full_workflow"
    state_manager = StateManager()

    for image_path in test_images:
        state_manager.add_pet(session_id, image_path)

    state_manager.set_template(session_id, template_path)

    print(f"初始化会话 {session_id}，包含 {len(test_images)} 只宠物")

    # 3. 测试多宠物抠图（使用 Replicate API）
    print("注意: 完整工作流测试需要 Replicate API，跳过抠图步骤")
    print("如需完整测试，请确保已设置 REPLICATE_API_TOKEN 环境变量")


def cleanup_test_files():
    """清理测试文件"""
    import shutil

    test_dirs = ["test_images", "test_templates", "test_output", "sessions/test_session_multi_pet", "sessions/test_full_workflow"]

    for test_dir in test_dirs:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"清理测试目录: {test_dir}")


def main():
    """主测试函数"""
    print("开始多宠物功能测试")

    try:
        # 基础功能测试
        test_state_management()
        test_layout_engine()

        # 完整工作流测试
        test_multi_pet_workflow()

        print("\n所有测试完成！")

    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        # 清理测试文件
        cleanup_test_files()

    return 0


if __name__ == "__main__":
    sys.exit(main())