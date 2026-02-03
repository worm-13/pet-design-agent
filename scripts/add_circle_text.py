# -*- coding: utf-8 -*-
"""
添加圆形文字到图像
用法: python add_circle_text.py <image_path> <text> [--color r,g,b,a] [--position bottom-center|top-center|center] [--out output_path]
"""
import argparse
import copy
import os
import sys

# 统一使用 UTF-8，避免中文路径与打印乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)

for path in [_SCRIPT_DIR, _PROJECT_ROOT]:
    if path not in sys.path:
        sys.path.insert(0, path)

from PIL import Image
from skills.circle_text_skill import CircleTextLayoutSkill
from skills.circle_text_skill.presets import get_config_for_template
from utils.font_manager import get_font_path


def _json_safe_copy(value):
    """将配置中的 tuple / numpy 类型等转换为 JSON 友好的结构。"""
    if isinstance(value, dict):
        return {k: _json_safe_copy(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe_copy(v) for v in value]
    if isinstance(value, (int, float, str, bool)) or value is None:
        return value
    # 其他类型统一转成字符串描述
    return str(value)


def add_circle_text_to_image(
    base_image_path: str,
    text: str,
    font_path: str = None,
    color_rgba: tuple = (255, 182, 193, 255),  # 默认粉色
    position: str = "center",  # 默认在图片中心
    radius: float = None,
    out_path: str = None,
    repeat_count: int = None,  # 重复次数，如果为 None 则默认 1 次
    template_name: str = None,  # 模板名称，用于自动应用预设
    existing_config: dict = None,  # 若提供则在此配置基础上渲染
) -> dict:
    """
    在图像上添加圆形文字
    
    Args:
        base_image_path: 基础图像路径
        text: 文字内容
        font_path: 字体路径（如果为None则使用默认字体）
        color_rgba: RGBA颜色 (r, g, b, a)
        position: 位置 ("bottom-center", "top-center", "center" 等)
        radius: 圆半径（如果为None则自动计算）
        out_path: 输出路径
        existing_config: 复现渲染时的原始配置（用于只换字体等场景）
    
    Returns:
        dict: 包含输出路径与最终使用的配置（output_path/config/position等）
    """
    # 相对路径相对于项目根目录解析
    if not os.path.isabs(base_image_path):
        base_image_path = os.path.join(_PROJECT_ROOT, base_image_path)
    if not os.path.exists(base_image_path):
        raise FileNotFoundError(f"图像文件不存在: {base_image_path}")
    # 加载基础图像
    base_image = Image.open(base_image_path).convert("RGBA")
    width, height = base_image.size

    detected_template = template_name
    if detected_template is None:
        if "清新粉蓝" in base_image_path or "qingxin" in base_image_path.lower():
            detected_template = "清新粉蓝"
        elif "sessions" in base_image_path:
            try:
                session_dir = os.path.dirname(base_image_path)
                state_path = os.path.join(session_dir, "state.json")
                if os.path.exists(state_path):
                    import json
                    with open(state_path, 'r', encoding='utf-8') as f:
                        state = json.load(f)
                        template_path = state.get("template", "")
                        if template_path and ("清新粉蓝" in template_path or "qingxin" in template_path.lower()):
                            detected_template = "清新粉蓝"
            except Exception:
                pass

    if existing_config:
        config = copy.deepcopy(existing_config)
        meta = config.setdefault("meta", {})
        if detected_template is None:
            detected_template = meta.get("template_name")
        if position is None:
            position = meta.get("position_label", "center")

        config.setdefault("canvas", {})
        config["canvas"]["width"] = width
        config["canvas"]["height"] = height
        config["canvas"].setdefault("center", [width // 2, height // 2])
        config["canvas"].setdefault("radius", min(width, height) * 0.40)
        config["canvas"].setdefault("canvas_rotation_deg", 0)

        resolved_font_path = font_path or config.get("font", {}).get("path")
        if resolved_font_path:
            resolved_font_path = get_font_path(resolved_font_path) or resolved_font_path
        config.setdefault("font", {})
        if resolved_font_path:
            config["font"]["path"] = resolved_font_path
        if not config["font"].get("size"):
            config["font"]["size"] = int(min(width, height) * 0.08)

        if color_rgba is None:
            stored_color = config.get("style", {}).get("fill_rgba")
            color_rgba = tuple(stored_color) if stored_color else (255, 182, 193, 255)
        config.setdefault("style", {})
        if color_rgba:
            config["style"]["fill_rgba"] = list(color_rgba)

        config.setdefault("layout", {})
        config.setdefault("spacing", {"char_tracking_px": 2.0, "word_spacing_px": 20})
        config.setdefault("render", {"supersample": 2})

        existing_phrases = config.get("phrases") or []
        repeat = len(existing_phrases) if existing_phrases else (repeat_count if repeat_count else 1)
        config["phrases"] = [text] * repeat
    else:
        position = position or "center"
        if position == "bottom-center":
            center_x = width // 2
            center_y = int(height * 0.85)
        elif position == "top-center":
            center_x = width // 2
            center_y = int(height * 0.15)
        elif position == "center":
            center_x = width // 2
            center_y = height // 2
        else:
            center_x = width // 2
            center_y = int(height * 0.85)

        if radius is None:
            radius = min(width, height) * 0.40

        resolved_font_path = font_path
        if resolved_font_path:
            resolved_font_path = get_font_path(resolved_font_path) or resolved_font_path
        if resolved_font_path is None:
            resolved_font_path = os.path.join(_PROJECT_ROOT, "assets", "fonts", "AaHuanLeBao-2.ttf")
            if not os.path.exists(resolved_font_path):
                resolved_font_path = None

        if detected_template and ("清新粉蓝" in detected_template or "qingxin" in detected_template.lower()):
            config = get_config_for_template(detected_template, text, width, height)
            if not os.path.isabs(config["font"]["path"]):
                config["font"]["path"] = os.path.join(_PROJECT_ROOT, config["font"]["path"])
            if resolved_font_path:
                config["font"]["path"] = resolved_font_path
            if color_rgba:
                config["style"]["fill_rgba"] = list(color_rgba)
            if repeat_count:
                config["phrases"] = [text] * repeat_count
                config["layout"]["phrase_spacing_deg"] = config["layout"].get("phrase_spacing_deg", 6)
        else:
            config = {
                "canvas": {
                    "width": width,
                    "height": height,
                    "center": [center_x, center_y],
                    "radius": radius,
                    "canvas_rotation_deg": 0
                },
                "phrases": [text] * (repeat_count if repeat_count else 1),
                "layout": {
                    "start_angle_deg": 270,
                    "clockwise": True,
                    "align": "center",
                    "orientation": "outward"
                },
                "spacing": {
                    "char_tracking_px": 2.0,
                    "word_spacing_px": 20
                },
                "font": {
                    "path": resolved_font_path if resolved_font_path else "assets/fonts/AaHuanLeBao-2.ttf",
                    "size": int(min(width, height) * 0.08)
                },
                "style": {
                    "fill_rgba": list(color_rgba)
                },
                "render": {
                    "supersample": 2
                }
            }

    config.setdefault("meta", {})
    config["meta"]["position_label"] = position
    if detected_template:
        config["meta"]["template_name"] = detected_template
    config["meta"]["repeat_count"] = len(config.get("phrases", []))
    config["meta"]["layout_type"] = "circle"

    skill = CircleTextLayoutSkill()
    result_image = skill.render(base_image, config)

    if out_path is not None and not os.path.isabs(out_path):
        out_path = os.path.join(_PROJECT_ROOT, out_path)
    if out_path is None:
        if "sessions" in base_image_path:
            session_dir = os.path.dirname(base_image_path)
            out_path = os.path.join(session_dir, "final.png")
        else:
            out_path = base_image_path.replace(".png", "_with_circle_text.png")
            if out_path == base_image_path:
                out_path = base_image_path.replace(".jpg", "_with_circle_text.png")

    result_image.save(out_path, "PNG")
    print(f"圆形文字已添加: {out_path}")

    json_safe_config = _json_safe_copy(config)
    details = {
        "output_path": out_path,
        "config": json_safe_config,
        "layout_type": "circle",
        "position_label": position,
        "color_rgba": _json_safe_copy(config.get("style", {}).get("fill_rgba")),
        "font_path": config.get("font", {}).get("path"),
        "font_size": config.get("font", {}).get("size"),
        "phrases": _json_safe_copy(config.get("phrases", [])),
        "template_name": detected_template,
    }
    return details


def main():
    parser = argparse.ArgumentParser(description="添加圆形文字到图像")
    parser.add_argument("image_path", help="图像路径")
    parser.add_argument("text", help="文字内容")
    parser.add_argument("--color", help="文字颜色（格式：r,g,b,a，如 255,182,193,255）")
    parser.add_argument("--position", choices=["bottom-center", "top-center", "center"], 
                       default="center", help="文字位置（默认：center，图片中心）")
    parser.add_argument("--radius", type=float, help="圆半径（像素）")
    parser.add_argument("--font", help="字体 ID（如 字体1、字体2）或字体路径")
    parser.add_argument("--repeat", type=int, help="文字重复次数（默认：1次）")
    parser.add_argument("--template", help="模板名称（如：清新粉蓝），用于自动应用预设参数")
    parser.add_argument("--out", "-o", help="输出路径")
    parser.add_argument("--session", "-s", help="会话 ID，指定后自动将文字配置同步到 state.json")

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

    try:
        result = add_circle_text_to_image(
            base_image_path=args.image_path,
            text=args.text,
            font_path=args.font,
            color_rgba=color_rgba,
            position=args.position,
            radius=args.radius,
            out_path=args.out,
            repeat_count=args.repeat,
            template_name=args.template
        )
        print(f"\n完成！结果已保存到: {result['output_path']}")

        if args.session:
            from state_manager import StateManager
            style = {
                "layout_type": result.get("layout_type", "circle"),
                "position_label": result.get("position_label", "center"),
                "color_rgba": result.get("color_rgba"),
                "font_path": result.get("font_path"),
                "font_size": result.get("font_size"),
                "phrases": result.get("phrases"),
                "repeat_count": len(result.get("phrases", [])),
                "template_name": result.get("template_name"),
                "circle_config": result.get("config"),
                "circle_text_color": result.get("color_rgba"),
                "circle_text_position": result.get("position_label"),
                "circle_text_font_path": result.get("font_path"),
            }
            StateManager().set_text(args.session, args.text, style)
            print("已同步到 state.json")
    except Exception as e:
        print(f"执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
