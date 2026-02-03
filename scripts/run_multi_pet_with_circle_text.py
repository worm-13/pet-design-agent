# -*- coding: utf-8 -*-
"""
宠物定制工作流（单宠/多宠）：抠图 -> 合成 -> 圆形文字，输出到 sessions/<session_id>/
用法: python run_multi_pet_with_circle_text.py <session_id> <image1> [image2 ...] --template <template> [--text <text>]
"""
import argparse
import os
import sys

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

from add_circle_text import add_circle_text_to_image
from state_manager import StateManager
from run_multi_pet_matting import run_multi_pet_matting
from run_multi_pet_composition import run_multi_pet_composition
from utils.font_manager import get_font_path


def find_file_in_dir(directory, filename_pattern):
    """在目录中查找文件（支持部分匹配，便于处理中文路径）"""
    if not os.path.exists(directory):
        return None
    full_path = os.path.join(directory, filename_pattern)
    if os.path.exists(full_path):
        return full_path
    pngs = []
    for f in os.listdir(directory):
        if not f.lower().endswith(".png"):
            continue
        pngs.append(f)
        try:
            if filename_pattern in f or (filename_pattern in f.replace(" ", "")):
                return os.path.join(directory, f)
        except Exception:
            pass
    # 若仅有一个 png 或匹配“清新粉蓝”等场景，直接使用该目录下唯一/第一个 png
    if len(pngs) == 1:
        return os.path.join(directory, pngs[0])
    if filename_pattern in ("清新粉蓝", "qingxin") and pngs:
        return os.path.join(directory, pngs[0])
    return None


def run_complete_pet_workflow(
    session_id: str,
    image_paths: list,
    template_path: str,
    circle_text: str = None,
    circle_text_color: tuple = (255, 182, 193, 255),  # 粉色
    font_path: str = None
) -> str:
    """
    宠物定制工作流（支持单宠或多宠）：抠图 -> 合成 -> 添加圆形文字，全部输出到 sessions/<session_id>/
    """
    print(f"开始宠物定制工作流: session={session_id}，{len(image_paths)} 张图")

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
    template_dir = os.path.join(_PROJECT_ROOT, "templates", "backgrounds")
    abs_template_path = None
    if os.path.isabs(template_path) and os.path.exists(template_path):
        abs_template_path = template_path
    if abs_template_path is None and not os.path.isabs(template_path):
        abs_template_path = os.path.join(_PROJECT_ROOT, template_path)
        if not os.path.exists(abs_template_path):
            abs_template_path = None
    if abs_template_path is None:
        # 按名称在 templates/backgrounds 中查找（支持“清新粉蓝”等）
        key = "清新粉蓝" if ("清新粉蓝" in template_path or "qingxin" in (template_path or "").lower()) else (os.path.basename(template_path).split(".")[0] if "." in (template_path or "") else template_path)
        found = find_file_in_dir(template_dir, key)
        if found:
            abs_template_path = found
    if abs_template_path is None or not os.path.exists(abs_template_path):
        raise FileNotFoundError(f"模板不存在: {template_path}（已尝试 {template_dir}）")

    state_manager.set_template(session_id, abs_template_path)

    print(f"已添加 {len(image_paths)} 只宠物，模板: {template_path}")

    # 4. 执行抠图
    print("执行多宠物抠图...")
    extracted_paths = run_multi_pet_matting(session_id)

    # 5. 执行合成
    print("执行多宠物合成...")
    design_path = run_multi_pet_composition(session_id)

    # 6. 添加圆形文字（如果提供）
    final_path = design_path
    if circle_text:
        print(f"添加圆形文字: {circle_text}")
        
        # 确定字体路径
        if font_path is None:
            font_path = os.path.join(_PROJECT_ROOT, "assets", "fonts", "AaHuanLeBao-2.ttf")
        
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"字体文件不存在: {font_path}")

        # 添加圆形文字
        render_result = add_circle_text_to_image(
            base_image_path=design_path,
            text=circle_text,
            font_path=font_path,
            color_rgba=circle_text_color,
            position="bottom-center",
            out_path=design_path.replace(".png", "_final.png")
        )
        final_path = render_result["output_path"]
        color_list = render_result.get("color_rgba") or list(circle_text_color)
        font_path_used = render_result.get("font_path") or font_path or os.path.join(_PROJECT_ROOT, "assets", "fonts", "AaHuanLeBao-2.ttf")
        text_style = {
            "layout_type": render_result.get("layout_type", "circle"),
            "position_label": render_result.get("position_label", "bottom-center"),
            "color_rgba": color_list,
            "font_path": font_path_used,
            "font_size": render_result.get("font_size"),
            "phrases": render_result.get("phrases", [circle_text]),
            "repeat_count": len(render_result.get("phrases", [circle_text])),
            "template_name": render_result.get("template_name"),
            "circle_config": render_result.get("config"),
            # 兼容旧字段
            "circle_text_color": color_list,
            "circle_text_position": render_result.get("position_label", "bottom-center"),
            "circle_text_font_path": font_path_used,
        }
        # 将文字配置写入 state，便于后续布局调整时重绘最终图（只移动宠物图层、保留文字）
        state_manager.set_text(session_id, circle_text, text_style)

    print(f"完整工作流完成！最终结果: {final_path}")
    return final_path


def main():
    parser = argparse.ArgumentParser(description="宠物定制工作流（单宠/多宠）：抠图 -> 合成 -> 圆形文字")
    parser.add_argument("session_id", help="会话ID（每次订单对应一个会话）")
    parser.add_argument("images", nargs="+", help="宠物图片路径（1张=单宠，2张+=多宠）")
    parser.add_argument("--template", "-t", required=True, help="模板路径")
    parser.add_argument("--text", help="圆形文字内容")
    parser.add_argument("--color", help="文字颜色（格式：r,g,b,a，如 255,182,193,255）")
    parser.add_argument("--font", help="字体 ID（如 字体1、字体2）或字体路径")
    parser.add_argument("--out", "-o", help="输出路径")

    args = parser.parse_args()

    # 解析颜色
    color_rgba = (255, 182, 193, 255)  # 默认粉色
    if args.color:
        try:
            parts = [int(x.strip()) for x in args.color.split(",")]
            if len(parts) == 3:
                color_rgba = tuple(parts) + (255,)  # 添加alpha
            elif len(parts) == 4:
                color_rgba = tuple(parts)
            else:
                raise ValueError("颜色格式错误")
        except Exception as e:
            print(f"颜色解析失败，使用默认粉色: {e}")

    # 确定字体路径（支持字体 ID 如「字体2」或路径）
    font_path = args.font
    if font_path:
        font_path = get_font_path(font_path) or font_path
    if font_path is None:
        font_path = os.path.join(_PROJECT_ROOT, "assets", "fonts", "AaHuanLeBao-2.ttf")

    try:
        final_path = run_complete_pet_workflow(
            session_id=args.session_id,
            image_paths=args.images,
            template_path=args.template,
            circle_text=args.text,
            circle_text_color=color_rgba,
            font_path=font_path
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
