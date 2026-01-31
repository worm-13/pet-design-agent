# -*- coding: utf-8 -*-
"""
宠物抠图（本地 rembg）：无需 Replicate API，输出透明 PNG。
当 nano-banana API 报 E005 时可用此脚本作为替代。
用法: python run_pet_image_matting_rembg.py <图片路径> [--pet-type head|half_body|full_body] [--out 输出路径]
"""
import argparse
import os

from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve(path: str) -> str:
    if not path or os.path.isabs(path):
        return path
    return os.path.join(PROJECT_ROOT, path)


def _crop_by_pet_type(img: Image.Image, pet_type: str) -> Image.Image:
    """按 pet_type 裁切：head 取上部分，half_body 取上 2/3，full_body 不裁切。"""
    if pet_type == "full_body":
        return img
    arr = img.split()[3] if len(img.split()) >= 4 else img.convert("RGBA").split()[3]
    bbox = arr.getbbox()
    if not bbox:
        return img
    x0, y0, x1, y1 = bbox
    w, h = x1 - x0, y1 - y0
    if pet_type == "head":
        crop_h = int(h * 0.55)
        return img.crop((x0, y0, x1, y0 + crop_h))
    if pet_type == "half_body":
        crop_h = int(h * 0.75)
        return img.crop((x0, y0, x1, y0 + crop_h))
    return img


def run_matting_rembg(
    image_path: str,
    pet_type: str = "head",
    out_path: str = None,
) -> str:
    from rembg import remove

    image_path = _resolve(image_path)
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"输入图不存在: {image_path}")

    if pet_type not in ("head", "half_body", "full_body"):
        raise ValueError(f"pet_type 须为 head/half_body/full_body，当前: {pet_type}")

    if out_path is None:
        out_path = os.path.join(PROJECT_ROOT, "output", f"extracted_{pet_type}_rembg.png")
    out_path = _resolve(out_path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    inp = Image.open(image_path).convert("RGBA")
    out = remove(inp)
    out = _crop_by_pet_type(out, pet_type)
    out.save(out_path)
    print(f"已抠图 (rembg, {pet_type}): {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="宠物抠图（rembg 本地，无 API）")
    parser.add_argument("image", help="图片路径（原图或去背景图）")
    parser.add_argument("--pet-type", "-t", choices=["head", "half_body", "full_body"], default="head")
    parser.add_argument("--out", "-o", default=None)
    args = parser.parse_args()
    run_matting_rembg(args.image, args.pet_type, args.out)


if __name__ == "__main__":
    main()
