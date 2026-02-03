# -*- coding: utf-8 -*-
"""
宠物布局调整：支持单独调整某只宠物的位置/大小
用法: python run_pet_layout_adjustment.py <session_id> <pet_id> [--position x,y] [--scale factor]
"""
import argparse
import sys
import os

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
from run_multi_pet_composition import run_multi_pet_composition
from utils.font_manager import get_font_path


def _reapply_final_image(session_id: str, design_path: str, state) -> str:
    """
    若 state 中保存了文字配置，在新 design 上重绘圆形文字并输出 design_final.png，
    保证「只移动指定宠物图层，文字等其他元素保留」的最终图与 design 一致。
    """
    session_dir = os.path.join(_PROJECT_ROOT, "sessions", session_id)
    design_final_path = os.path.join(session_dir, "design_final.png")

    if not state.text_content:
        return design_path

    try:
        from add_circle_text import add_circle_text_to_image
    except ImportError:
        print("未找到 add_circle_text，仅更新 design.png，不生成 design_final.png")
        return design_path

    style = state.text_style or {}
    color = style.get("color_rgba") or style.get("circle_text_color")
    if color is not None and len(color) >= 3:
        color_rgba = tuple(color) if len(color) >= 4 else tuple(color) + (255,)
    else:
        color_rgba = (255, 182, 193, 255)
    position = style.get("position_label") or style.get("circle_text_position") or "bottom-center"
    font_path = style.get("font_path") or style.get("circle_text_font_path")
    if font_path:
        font_path_resolved = get_font_path(font_path) or font_path
    else:
        font_path_resolved = os.path.join(_PROJECT_ROOT, "assets", "fonts", "AaHuanLeBao-2.ttf")
    if not os.path.exists(font_path_resolved):
        font_path_resolved = None

    circle_config = style.get("circle_config")

    render_result = add_circle_text_to_image(
        base_image_path=design_path,
        text=state.text_content,
        font_path=font_path_resolved,
        color_rgba=color_rgba,
        position=position,
        out_path=design_final_path,
        existing_config=circle_config,
    )
    final_path = render_result["output_path"]

    # 更新 state 中文字配置（保证最新的 font/path/config 等信息）
    updated_style = dict(style)
    updated_style["layout_type"] = render_result.get("layout_type", updated_style.get("layout_type", "circle"))
    updated_style["position_label"] = render_result.get("position_label", position)
    updated_style["color_rgba"] = render_result.get("color_rgba") or list(color_rgba)
    updated_style["font_path"] = render_result.get("font_path") or font_path_resolved
    updated_style["font_size"] = render_result.get("font_size", updated_style.get("font_size"))
    phrases = render_result.get("phrases") or updated_style.get("phrases")
    updated_style["phrases"] = phrases
    updated_style["repeat_count"] = len(phrases or [])
    updated_style["template_name"] = render_result.get("template_name", updated_style.get("template_name"))
    updated_style["circle_config"] = render_result.get("config")
    updated_style["circle_text_color"] = updated_style["color_rgba"]
    updated_style["circle_text_position"] = updated_style["position_label"]
    updated_style["circle_text_font_path"] = updated_style["font_path"]

    state_manager.set_text(session_id, state.text_content, updated_style)
    print(f"已按 state 重绘最终图（保留文字）: {final_path}")
    return final_path


def adjust_pet_layout(session_id: str, pet_id: str,
                     position: str = None, scale: float = None) -> str:
    """
    调整指定宠物的布局参数；只移动该宠物图层，其他宠物与背景不变。
    若 state 中保存了文字配置，会在新 design 上重绘圆形文字并输出 design_final.png，
    保证最终产品图只变动被移动的图层。
    """
    state_manager = StateManager()
    state = state_manager.load_state(session_id)

    # 验证宠物存在
    pet_exists = any(pet.id == pet_id for pet in state.pets)
    if not pet_exists:
        raise ValueError(f"宠物 {pet_id} 不存在于会话 {session_id}")

    # 解析位置参数
    anchor = None
    if position:
        try:
            x, y = map(float, position.split(','))
            anchor = (x, y)
        except ValueError:
            raise ValueError("位置参数格式错误，应为 x,y（如 0.5,0.6）")

    # 更新布局
    state_manager.update_pet_layout(session_id, pet_id, anchor=anchor, scale=scale)

    print(f"已调整宠物 {pet_id} 布局:")
    if anchor:
        print(f"  新位置: {anchor}")
    if scale:
        print(f"  新缩放: {scale}")

    # 重新合成（仅改该宠物锚点/缩放，其他宠物与背景不变）
    design_path = run_multi_pet_composition(session_id, use_state_layout=True)
    print(f"重新合成完成: {design_path}")

    # 若有文字配置，在新 design 上重绘最终图，使「最终产品图」只变动被移动的图层
    state = state_manager.load_state(session_id)
    result_path = _reapply_final_image(session_id, design_path, state)
    return result_path


def main():
    parser = argparse.ArgumentParser(description="宠物布局调整")
    parser.add_argument("session_id", help="会话ID")
    parser.add_argument("pet_id", help="宠物ID（如 pet_a, pet_b）")
    parser.add_argument("--position", "-p", help="新位置（x,y，相对坐标0-1）")
    parser.add_argument("--scale", "-s", type=float, help="新缩放比例")

    args = parser.parse_args()

    if not args.position and args.scale is None:
        print("错误：必须指定 --position 或 --scale 中的至少一个")
        sys.exit(1)

    try:
        result_path = adjust_pet_layout(
            session_id=args.session_id,
            pet_id=args.pet_id,
            position=args.position,
            scale=args.scale
        )
        print(f"调整完成: {result_path}")

    except Exception as e:
        print(f"调整失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()