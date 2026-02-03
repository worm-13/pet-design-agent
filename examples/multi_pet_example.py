# -*- coding: utf-8 -*-
"""
多宠物功能使用示例
演示如何使用新的多宠物合成能力
"""
import os
import sys

# 添加项目路径
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def example_multi_pet_basic():
    """基础多宠物合成示例"""
    print("=== 多宠物基础合成示例 ===")

    from scripts.run_multi_pet_orchestrator import MultiPetOrchestrator

    # 初始化编排器
    orchestrator = MultiPetOrchestrator()

    # 示例：合成两只宠物
    session_id = "example_session"
    pet_images = [
        "input/pet1.jpg",  # 第一只宠物
        "input/pet2.jpg"   # 第二只宠物
    ]
    template_path = "templates/backgrounds/清新粉蓝-1.png"

    try:
        result_path = orchestrator.orchestrate(
            session_id=session_id,
            image_paths=pet_images,
            instruction="把两只宠物合照放一起",
            template_path=template_path
        )

        print(f"合成完成！结果保存至: {result_path}")

    except Exception as e:
        print(f"合成失败: {e}")


def example_pet_adjustment():
    """宠物调整示例"""
    print("\n=== 宠物单独调整示例 ===")

    from scripts.state_manager import StateManager
    from scripts.run_multi_pet_composition import run_multi_pet_composition

    session_id = "example_session"

    # 调整左边宠物的大小
    state_manager = StateManager()
    state_manager.update_pet_layout(
        session_id=session_id,
        pet_id="pet_a",  # 左边宠物
        scale=1.1  # 放大10%
    )

    # 重新合成
    result_path = run_multi_pet_composition(session_id)
    print(f"调整后重新合成完成: {result_path}")


def example_layout_engine():
    """布局引擎使用示例"""
    print("\n=== 布局引擎使用示例 ===")

    from utils.multi_pet_layout import create_multi_pet_layout

    # 横版模板：400x300
    landscape_layouts = create_multi_pet_layout(
        template_size=(400, 300),  # 横版
        pet_count=2,
        pet_sizes=[(200, 200), (180, 180)]  # 两只宠物的大小
    )

    print("横版2宠物自动布局:")
    for layout in landscape_layouts:
        print(f"  {layout.id}: 位置({layout.anchor[0]:.2f}, {layout.anchor[1]:.2f}), 缩放{layout.scale}")

    # 竖版模板：300x400
    portrait_layouts = create_multi_pet_layout(
        template_size=(300, 400),  # 竖版
        pet_count=2,
        pet_sizes=[(200, 200), (180, 180)]
    )

    print("竖版2宠物自动布局:")
    for layout in portrait_layouts:
        print(f"  {layout.id}: 位置({layout.anchor[0]:.2f}, {layout.anchor[1]:.2f}), 缩放{layout.scale}")


def example_intent_detection():
    """意图识别示例"""
    print("\n=== 意图识别示例 ===")

    from scripts.run_multi_pet_orchestrator import MultiPetIntentDetector

    detector = MultiPetIntentDetector()

    test_instructions = [
        "把两只宠物合照放一起",
        "左边那只大一点",
        "右边的往中间靠一点",
        "单只宠物居中显示"
    ]

    for instruction in test_instructions:
        intent = detector.detect_multi_pet_intent(instruction, 1)
        print(f"指令: '{instruction}'")
        print(f"  意图: {intent['intent']}")
        print(f"  宠物数: {intent['pet_count']}")
        if intent['target_pet']:
            print(f"  目标宠物: {intent['target_pet']}")
        print()


def main():
    """运行所有示例"""
    print("多宠物功能使用示例")
    print("=" * 50)

    try:
        # 注意：实际运行需要准备好图片文件
        print("注意：这些示例需要准备好对应的图片文件才能实际运行")
        print("建议先创建测试图片，然后取消注释相关函数调用")
        print()

        # 示例函数（已注释，需要图片文件时取消注释）
        # example_multi_pet_basic()
        # example_pet_adjustment()

        # 这些示例不需要图片文件，可以直接运行
        example_layout_engine()
        example_intent_detection()

    except Exception as e:
        print(f"示例运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()