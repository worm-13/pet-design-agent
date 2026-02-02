# -*- coding: utf-8 -*-
"""
CircleTextLayoutSkill 示例调用
"""
import os
from PIL import Image
from .skill import CircleTextLayoutSkill
from .presets import DEFAULT_CONFIG, PET_CUSTOM_CONFIG, BADGE_CONFIG


def demo_basic():
    """基础演示 - 三个'i love you'短语"""
    print("=== CircleTextLayoutSkill 基础演示 ===")

    # 使用默认配置
    config = DEFAULT_CONFIG.copy()

    skill = CircleTextLayoutSkill()
    img = skill.render(base_image=None, config=config)

    # 保存结果
    output_path = "output/skill_demo_basic.png"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")

    print(f"[OK] 基础演示完成: {output_path}")
    print("  - 三个短语: i love you, i love you, i love you")
    print("  - 等角度分布: 0°, 120°, 240°")
    print("  - 每个短语居中对齐")


def demo_pet_custom():
    """宠物定制演示"""
    print("\n=== 宠物定制演示 ===")

    config = PET_CUSTOM_CONFIG.copy()
    config["phrases"] = ["max", "max", "max"]  # 宠物名字

    skill = CircleTextLayoutSkill()
    img = skill.render(base_image=None, config=config)

    output_path = "output/skill_demo_pet.png"
    img.save(output_path, "PNG")

    print(f"[OK] 宠物定制演示完成: {output_path}")


def demo_badge():
    """徽章设计演示"""
    print("\n=== 徽章设计演示 ===")

    config = BADGE_CONFIG.copy()

    skill = CircleTextLayoutSkill()
    img = skill.render(base_image=None, config=config)

    output_path = "output/skill_demo_badge.png"
    img.save(output_path, "PNG")

    print(f"[OK] 徽章设计演示完成: {output_path}")


def demo_custom_config():
    """自定义配置演示"""
    print("\n=== 自定义配置演示 ===")

    config = {
        "canvas": {
            "width": 1024,
            "height": 1024,
            "center": [512, 512],
            "radius": 400
        },

        "phrases": [
            "hello world",
            "python skill",
            "circle text"
        ],

        "layout": {
            "start_angle_deg": 180,  # 从顶部开始
            "clockwise": True,
            "align": "center"
        },

        "spacing": {
            "char_tracking_px": 2.0,
            "word_spacing_px": 30
        },

        "font": {
            "path": "assets/fonts/AaHuanLeBao-2.ttf",
            "size": 48
        },

        "style": {
            "fill_rgba": [255, 100, 150, 255]  # 粉红色
        },

        "render": {
            "supersample": 2
        }
    }

    skill = CircleTextLayoutSkill()
    img = skill.render(base_image=None, config=config)

    output_path = "output/skill_demo_custom.png"
    img.save(output_path, "PNG")

    print(f"[OK] 自定义配置演示完成: {output_path}")
    print("  - 三个短语: hello world, python skill, circle text")
    print("  - 从180°开始，粉红色")


def run_all_demos():
    """运行所有演示"""
    print("[TARGET] CircleTextLayoutSkill 完整演示")
    print("=" * 50)

    try:
        demo_basic()
        demo_pet_custom()
        demo_badge()
        demo_custom_config()

        print("\n[SUCCESS] 所有演示完成！")
        print("[FOLDER] 输出文件位于 output/ 目录")

    except Exception as e:
        print(f"[ERROR] 演示失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_demos()