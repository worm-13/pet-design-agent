# -*- coding: utf-8 -*-
"""
模板应用：将宠物图与背景图做图层合成（纯 Pillow，无 AI）。
支持视觉中心对齐：自动计算宠物 alpha 加权重心，对齐到模板锚点。
用法: python run_compose_pet_on_template.py <宠物PNG> <背景图> [--out 输出] [--position 0.5,0.55] [--scale 0.6]
"""
import argparse
import os
import sys

from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from utils.visual_center import compute_visual_center_from_alpha


def _resolve(path: str) -> str:
    if not path or os.path.isabs(path):
        return path
    return os.path.join(PROJECT_ROOT, path)


def _clamp_position(
    x: int,
    y: int,
    bg_w: int,
    bg_h: int,
    pet_w: int,
    pet_h: int,
    min_visible: int = 50,
) -> tuple[int, int]:
    """确保宠物至少有 min_visible 像素在画布内可见。"""
    x = max(min(x, bg_w - min_visible), -pet_w + min_visible)
    y = max(min(y, bg_h - min_visible), -pet_h + min_visible)
    return x, y


def compose_pet_on_template(
    pet_png: str,
    template_path: str,
    out_path: str = None,
    position: tuple = (0.5, 0.55),
    scale: float = 0.6,
) -> str:
    pet_png = _resolve(pet_png)
    template_path = _resolve(template_path)
    if not os.path.isfile(pet_png):
        raise FileNotFoundError(f"宠物图不存在: {pet_png}")
    if not os.path.isfile(template_path):
        raise FileNotFoundError(f"背景图不存在: {template_path}")

    if out_path is None:
        out_path = os.path.join(PROJECT_ROOT, "output", "design.png")
    out_path = _resolve(out_path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    bg = Image.open(template_path).convert("RGBA")
    pet = Image.open(pet_png).convert("RGBA")

    bw, bh = bg.size
    pw, ph = pet.size

    # 按 scale 相对背景宽度缩放
    new_pw = int(bw * scale)
    ratio = new_pw / pw
    new_ph = int(ph * ratio)
    pet = pet.resize((new_pw, new_ph), Image.Resampling.LANCZOS)

    pw, ph = pet.size

    # (B) 计算视觉中心（alpha 加权重心，头部权重更高）
    cx, cy = compute_visual_center_from_alpha(
        pet,
        alpha_threshold=20,
        top_weight=1.5,
        bottom_weight=0.8,
    )

    # (C) anchor -> 背景中的目标像素
    ax, ay = position
    tx = bw * ax
    ty = bh * ay

    # (D) 计算 paste 左上角：使视觉中心对齐到目标点
    x = round(tx - cx)
    y = round(ty - cy)

    # (E) 边界 clamp：确保至少 min_visible 像素可见
    x, y = _clamp_position(x, y, bw, bh, pw, ph, min_visible=50)

    # Debug 日志
    print(f"[合成] pet {pw}x{ph} | bg {bw}x{bh} | 视觉中心 ({cx:.1f},{cy:.1f}) | anchor ({ax},{ay}) -> 目标 ({tx:.0f},{ty:.0f}) | paste ({x},{y})")

    bg.paste(pet, (x, y), pet)
    bg.convert("RGB").save(out_path)
    print(f"已合成: {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="宠物图与背景图层合成")
    parser.add_argument("pet_png", help="宠物图路径")
    parser.add_argument("template", help="背景图路径")
    parser.add_argument("--out", "-o", default=None, help="输出路径")
    parser.add_argument("--position", "-p", default="0.5,0.55", help="宠物中心相对位置 x,y，如 0.5,0.55")
    parser.add_argument("--scale", "-s", type=float, default=0.6, help="宠物宽度相对背景宽度的比例")
    args = parser.parse_args()

    pos = tuple(float(x) for x in args.position.split(","))
    compose_pet_on_template(
        args.pet_png,
        args.template,
        args.out,
        position=pos,
        scale=args.scale,
    )


if __name__ == "__main__":
    main()
