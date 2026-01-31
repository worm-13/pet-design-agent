# -*- coding: utf-8 -*-
"""
文字图层 Skill：base layer + 可选 text layer 合成。
删除文字 = enabled=false，仅不合成文字图层，不执行任何图像擦除。
最终图像始终由 base + 可选 text layer 重新合成生成。
"""
import argparse
import json
import os
import shutil

from PIL import Image, ImageDraw, ImageFont

MARGIN = 20
POSITIONS = (
    "top-left", "top-center", "top-right",
    "center",
    "bottom-left", "bottom-center", "bottom-right",
)

DEFAULT_TEXT_CONFIG = {
    "enabled": True,
    "content": "",
    "font": "arial.ttf",
    "size": 96,
    "color": "#000000",
    "position": "bottom-center",
    "outline": {"enabled": False, "color": "#FFFFFF", "width": 3},
}


def hex_to_rgb(s: str) -> tuple:
    s = s.lstrip("#")
    if len(s) == 6:
        return tuple(int(s[i : i + 2], 16) for i in (0, 2, 4))
    raise ValueError(f"无效颜色: {s}")


def get_text_anchor(cw: int, ch: int, position: str, bbox: tuple, margin: int = None) -> tuple:
    m = margin if margin is not None else MARGIN
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    if position == "center":
        return cw // 2 - tw // 2, ch // 2 - th // 2
    if position == "top-left":
        return m, m
    if position == "top-center":
        return cw // 2 - tw // 2, m
    if position == "top-right":
        return cw - tw - m, m
    if position == "bottom-left":
        return m, ch - th - m
    if position == "bottom-center":
        return cw // 2 - tw // 2, ch - th - m
    if position == "bottom-right":
        return cw - tw - m, ch - th - m
    return cw // 2 - tw // 2, ch // 2 - th // 2


def load_font(font_name: str, size: int) -> ImageFont.FreeTypeFont:
    for path in [font_name, "arial.ttf", "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/msyh.ttc"]:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def create_text_layer(w, h, content, font_name, font_size, color, position, outline, margin=None, offset_x=0, offset_y=0) -> Image.Image:
    """创建透明 RGBA 文字图层。"""
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    font = load_font(font_name, font_size)

    bbox = draw.textbbox((0, 0), content, font=font)
    x, y = get_text_anchor(w, h, position, bbox, margin)
    x, y = x + offset_x, y + offset_y
    main_color = (*hex_to_rgb(color), 255)

    if outline and outline.get("enabled"):
        outline_color = (*hex_to_rgb(outline.get("color", "#FFFFFF")), 255)
        width_val = outline.get("width", 2)
        for dx in range(-width_val, width_val + 1):
            for dy in range(-width_val, width_val + 1):
                if dx != 0 or dy != 0:
                    draw.text((x + dx, y + dy), content, font=font, fill=outline_color)

    draw.text((x, y), content, font=font, fill=main_color)
    return layer


def run_text_adjustment(
    base_image_path: str,
    text_config: dict | None = None,
    out_path: str | None = None,
    **kwargs,
) -> str:
    """
    合成：base layer + 可选 text layer。
    - enabled=false 或 content 为空：仅复制 base 到输出，不合成文字
    - enabled=true 且 content 非空：base + text_layer alpha 合成
    不修改 base_image_path。
    """
    if not os.path.isfile(base_image_path):
        raise FileNotFoundError(f"底图不存在: {base_image_path}")

    cfg = dict(DEFAULT_TEXT_CONFIG)
    if text_config:
        cfg.update(text_config)
        if "outline" in text_config and isinstance(text_config["outline"], dict):
            cfg["outline"] = {**cfg.get("outline", {}), **text_config["outline"]}
    for k, v in kwargs.items():
        if v is not None and k in ("content", "enabled", "font", "size", "color", "position", "margin", "offset_x", "offset_y"):
            cfg[k] = v
        if k == "font_style" and v is not None:
            cfg["font"] = v
        if k == "font_size" and v is not None:
            cfg["size"] = v
        if k == "font_color" and v is not None:
            cfg["color"] = v

    if out_path is None:
        out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output", "final_with_text.png")
    base_abs = os.path.abspath(base_image_path)
    out_abs = os.path.abspath(out_path)
    if base_abs == out_abs:
        raise ValueError(
            "输出路径不能与底图相同，否则会破坏底图。请使用 --out 指定不同路径，例如 output/final.png"
        )
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    # 是否合成文字层：enabled=true 且 content 非空
    enabled = cfg.get("enabled", True)
    content = (cfg.get("content") or "").strip()
    should_composite_text = enabled and bool(content)

    if not should_composite_text:
        # 不合成文字：直接复制 base 到输出
        shutil.copy2(base_image_path, out_path)
        print(f"已保存（无文字）: {out_path}")
        return out_path

    base = Image.open(base_image_path).convert("RGBA")
    w, h = base.size
    text_layer = create_text_layer(
        w, h,
        content=content,
        font_name=cfg.get("font", "arial.ttf"),
        font_size=int(cfg.get("size", 96)),
        color=cfg.get("color", "#000000"),
        position=cfg.get("position", "bottom-center"),
        outline=cfg.get("outline"),
        margin=cfg.get("margin"),
        offset_x=cfg.get("offset_x", 0),
        offset_y=cfg.get("offset_y", 0),
    )
    result = Image.alpha_composite(base, text_layer)
    result.convert("RGB").save(out_path)
    print(f"已保存: {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="base layer + 可选 text layer 合成")
    parser.add_argument("base_image", help="不含文字的底图（只读，不修改）")
    parser.add_argument("--content", "-c", default=None, help="文字内容")
    parser.add_argument("--enabled", action="store_true", help="显示文字")
    parser.add_argument("--disabled", action="store_true", help="不显示文字（仅复制底图，不合成 text layer）")
    parser.add_argument("--font", default="arial.ttf", help="字体")
    parser.add_argument("--size", type=int, default=96, help="字号")
    parser.add_argument("--color", default="#000000", help="颜色")
    parser.add_argument("--position", "-p", choices=POSITIONS, default="bottom-center", help="位置")
    parser.add_argument("--margin", "-m", type=int, default=None, help="底边距（bottom 时越大文字越靠上），默认 20")
    parser.add_argument("--offset-x", type=int, default=0, help="水平偏移（正数向右）")
    parser.add_argument("--offset-y", type=int, default=0, help="垂直偏移（正数向下）")
    parser.add_argument("--out", "-o", default=None, help="输出路径（必须与 base 不同，以保护底图）")
    parser.add_argument("--state", default=None, help="state.json 路径")
    parser.add_argument("--outline-enabled", action="store_true", help="启用描边")
    parser.add_argument("--outline-color", default="#FFFFFF", help="描边颜色")
    parser.add_argument("--outline-width", type=int, default=3, help="描边宽度")
    args = parser.parse_args()

    text_config = None
    if args.state and os.path.isfile(args.state):
        with open(args.state, "r", encoding="utf-8") as f:
            text_config = json.load(f).get("text", {})

    kwargs = {}
    if args.disabled:
        kwargs["enabled"] = False
    elif args.enabled:
        kwargs["enabled"] = True
    if text_config is None:
        kwargs.update(
            content=args.content or "",
            font=args.font,
            size=args.size,
            color=args.color,
            position=args.position,
            margin=args.margin,
            offset_x=args.offset_x,
            offset_y=args.offset_y,
        )
        if args.outline_enabled:
            kwargs["outline"] = {"enabled": True, "color": args.outline_color, "width": args.outline_width}

    run_text_adjustment(args.base_image, text_config=text_config, out_path=args.out, **kwargs)


if __name__ == "__main__":
    main()
