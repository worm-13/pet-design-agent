# -*- coding: utf-8 -*-
"""
仅更换字体：在保持大小、排版、颜色、位置、内容不变的前提下，将圆形文字换为新字体。
用法: python run_change_font.py <session_id> --font <字体ID或路径>
"""
import argparse
import os
import sys

# 统一使用 UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)

for path in [_SCRIPT_DIR, _PROJECT_ROOT]:
    if path not in sys.path:
        sys.path.insert(0, path)

from state_manager import StateManager
from utils.font_manager import get_font_path


def change_font(session_id: str, font: str) -> str:
    """
    仅更换圆形文字字体，其余参数不变。

    Args:
        session_id: 会话 ID
        font: 新字体 ID（如 字体1、字体2）或字体文件路径

    Returns:
        更新后的 design_final.png 路径
    """
    state_manager = StateManager()
    state = state_manager.load_state(session_id)

    if not state.text_content:
        raise ValueError(f"会话 {session_id} 无文字配置，无法更换字体。请先通过工作流添加圆形文字。")

    # 解析新字体路径
    new_font_path = get_font_path(font)
    if not new_font_path or not os.path.isfile(new_font_path):
        raise FileNotFoundError(f"字体不存在或无法解析: {font}")

    session_dir = os.path.join(_PROJECT_ROOT, "sessions", session_id)
    design_path = os.path.join(session_dir, "design.png")
    design_final_path = os.path.join(session_dir, "design_final.png")

    if not os.path.isfile(design_path):
        raise FileNotFoundError(f"合成图不存在: {design_path}，请先完成多宠物合成。")

    # 从 state 读取原有参数（仅换字体）
    style = state.text_style or {}

    # 重新添加圆形文字，仅字体不同
    from add_circle_text import add_circle_text_to_image

    circle_config = style.get("circle_config")
    position_label = style.get("position_label") or style.get("circle_text_position") or "bottom-center"
    color = style.get("color_rgba") or style.get("circle_text_color") or (255, 182, 193, 255)
    if len(color) == 3:
        color = tuple(color) + (255,)
    color_rgba = tuple(color)

    render_result = add_circle_text_to_image(
        base_image_path=design_path,
        text=state.text_content,
        font_path=new_font_path,
        color_rgba=color_rgba,
        position=position_label,
        out_path=design_final_path,
        existing_config=circle_config,
    )
    final_path = render_result["output_path"]

    # 更新 state 中的字体路径，便于后续布局调整等操作使用新字体
    new_style = dict(style) if style else {}
    new_style["layout_type"] = render_result.get("layout_type", new_style.get("layout_type", "circle"))
    new_style["position_label"] = render_result.get("position_label", position_label)
    new_style["color_rgba"] = render_result.get("color_rgba") or list(color_rgba)
    new_style["font_path"] = render_result.get("font_path") or new_font_path
    new_style["font_size"] = render_result.get("font_size", new_style.get("font_size"))
    phrases = render_result.get("phrases") or new_style.get("phrases")
    new_style["phrases"] = phrases
    new_style["repeat_count"] = len(phrases or [])
    new_style["template_name"] = render_result.get("template_name", new_style.get("template_name"))
    new_style["circle_config"] = render_result.get("config")
    new_style["circle_text_font_path"] = new_style["font_path"]
    new_style["circle_text_color"] = new_style.get("color_rgba")
    new_style["circle_text_position"] = new_style.get("position_label")
    state_manager.set_text(session_id, state.text_content, new_style)

    return final_path


def main():
    parser = argparse.ArgumentParser(
        description="仅更换圆形文字字体，大小、排版、颜色、位置、内容保持不变"
    )
    parser.add_argument("session_id", help="会话 ID")
    parser.add_argument("--font", "-f", required=True, help="新字体 ID（如 字体1、字体2）或字体路径")

    args = parser.parse_args()

    try:
        result_path = change_font(args.session_id, args.font)
        print(f"字体已更换，结果: {result_path}")
    except Exception as e:
        print(f"更换字体失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
