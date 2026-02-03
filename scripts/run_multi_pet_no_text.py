# -*- coding: utf-8 -*-
"""
宠物定制工作流（无文字）：抠图 -> 合成，输出到 sessions/<session_id>/
用法: python run_multi_pet_no_text.py <session_id> <image1> [image2 ...] --template <template>
"""
import argparse
import os
import sys

# 确保脚本目录和项目根目录在 path 中
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)

for path in [_SCRIPT_DIR, _PROJECT_ROOT]:
    if path not in sys.path:
        sys.path.insert(0, path)

from state_manager import StateManager
from run_multi_pet_matting import run_multi_pet_matting
from run_multi_pet_composition import run_multi_pet_composition


def run_complete_multi_pet_workflow_no_text(
    session_id: str,
    image_paths: list,
    template_path: str
) -> str:
    """
    完整的多宠物工作流（无文字）：抠图 -> 合成
    """
    print(f"开始宠物定制工作流（无文字）: session={session_id}，{len(image_paths)} 张图")

    # 1. 初始化状态
    state_manager = StateManager()

    # 2. 添加宠物到状态
    for image_path in image_paths:
        # 处理相对路径和绝对路径
        if not os.path.isabs(image_path):
            abs_path = os.path.abspath(os.path.join(_PROJECT_ROOT, image_path))
        else:
            abs_path = image_path
        
        if not os.path.exists(abs_path):
            # 尝试直接使用原始路径
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"图片不存在: {image_path}")
            abs_path = image_path
        
        state_manager.add_pet(session_id, abs_path, crop_mode="head")

    # 3. 设置模板
    # 处理相对路径和绝对路径
    if not os.path.isabs(template_path):
        abs_template_path = os.path.abspath(os.path.join(_PROJECT_ROOT, template_path))
    else:
        abs_template_path = template_path
    
    # 如果路径不存在，尝试通过文件名查找
    if not os.path.exists(abs_template_path):
        # 尝试直接使用原始路径
        if os.path.exists(template_path):
            abs_template_path = template_path
        else:
            # 尝试在templates/backgrounds目录中查找
            template_dir = os.path.join(_PROJECT_ROOT, "templates", "backgrounds")
            if os.path.exists(template_dir):
                files = os.listdir(template_dir)
                # 查找包含"清新粉蓝"的文件
                for f in files:
                    if "清新粉蓝" in f or "清新" in f:
                        abs_template_path = os.path.join(template_dir, f)
                        break
                if not os.path.exists(abs_template_path):
                    raise FileNotFoundError(f"模板不存在: {template_path}，也无法在 {template_dir} 中找到匹配文件")
            else:
                raise FileNotFoundError(f"模板不存在: {template_path}")
    
    state_manager.set_template(session_id, abs_template_path)

    print(f"已添加 {len(image_paths)} 只宠物，模板: {template_path}")

    # 4. 执行抠图
    print("执行多宠物抠图...")
    extracted_paths = run_multi_pet_matting(session_id)

    # 5. 执行合成（不添加文字）
    print("执行多宠物合成（无文字）...")
    design_path = run_multi_pet_composition(session_id)

    # 6. 将最终结果复制为 final.png
    session_dir = os.path.join("sessions", session_id)
    final_path = os.path.join(session_dir, "final.png")
    import shutil
    shutil.copy2(design_path, final_path)

    print(f"完整工作流完成！最终结果: {final_path}")
    return final_path


def main():
    parser = argparse.ArgumentParser(description="宠物定制工作流（无文字）：抠图 -> 合成")
    parser.add_argument("session_id", help="会话ID")
    parser.add_argument("images", nargs="+", help="宠物图片路径（1张=单宠，2张+=多宠）")
    parser.add_argument("--template", "-t", required=True, help="模板路径")
    parser.add_argument("--out", "-o", help="输出路径")

    args = parser.parse_args()

    try:
        final_path = run_complete_multi_pet_workflow_no_text(
            session_id=args.session_id,
            image_paths=args.images,
            template_path=args.template
        )

        # 如果指定了输出路径，复制文件
        if args.out and final_path != args.out:
            import shutil
            shutil.copy2(final_path, args.out)
            print(f"结果已复制到: {args.out}")
            final_path = args.out

        print(f"\n完成！最终结果: {final_path}")

    except Exception as e:
        print(f"执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
