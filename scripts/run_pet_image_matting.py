# -*- coding: utf-8 -*-
"""
宠物抠图：使用 google/nano-banana 从去背景图中抠出全身/半身/头部。
API 报 E005 时自动回退到本地 rembg 抠图。
用法: python run_pet_image_matting.py <去背景图路径> [--pet-type head|half_body|full_body] [--out 输出路径]
"""
import argparse
import os
import sys

# 确保脚本目录在 path 中（回退导入用）
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from replicate_utils import download_url, ensure_token

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NANO_BANANA = "google/nano-banana"

PROMPTS = {
    "head": "Remove everything except the pet's head—ensure no neck, no body, and no bottom shadow. The pet's head should be completely isolated, with absolutely no part of the neck or body visible in the image. The neck must be fully removed, leaving only the head. Preserve all facial features, texture, coloration, and expression exactly; highest priority: do not alter the pet in any way. Ensure the edges of the head are crisp and clear—avoid over-feathering, halos, or soft transitions. Completely remove any shadow beneath the head, ensuring a flat, seamless base. Set the background to transparent.",
    "half_body": "Extract the pet from head to half body (upper half), remove background, keep subject clear. Set the background to transparent.",
    "full_body": "Extract the full body of the pet, remove background, keep subject clear. Set the background to transparent.",
}


def _resolve(path: str) -> str:
    if not path or os.path.isabs(path):
        return path
    return os.path.join(PROJECT_ROOT, path)


def run_matting(image_path: str, pet_type: str = "head", out_path: str = None) -> str:
    import replicate
    from replicate.exceptions import ModelError

    ensure_token()
    image_path = _resolve(image_path)
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"输入图不存在: {image_path}")

    if pet_type not in PROMPTS:
        raise ValueError(f"pet_type 须为 head/half_body/full_body，当前: {pet_type}")

    if out_path is None:
        out_path = os.path.join(PROJECT_ROOT, "output", f"extracted_{pet_type}.png")
    out_path = _resolve(out_path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    try:
        prompt = PROMPTS[pet_type]
        image_path_abs = os.path.abspath(image_path)
        if not os.path.isfile(image_path_abs):
            raise FileNotFoundError(f"抠图输入图不存在: {image_path_abs}")

        uploaded = replicate.files.create(image_path_abs)
        image_uri = uploaded.urls.get("get") or str(uploaded.urls)
        output = replicate.run(
            NANO_BANANA,
            input={
                "image_input": [image_uri],
                "prompt": prompt,
            },
        )

        if isinstance(output, str):
            url = output
        elif hasattr(output, "url"):
            url = output.url
        elif isinstance(output, list) and output:
            url = output[0] if isinstance(output[0], str) else getattr(output[0], "url", str(output[0]))
        else:
            url = str(output)

        download_url(url, out_path)
        print(f"已抠图 ({pet_type}): {out_path}")
        return out_path

    except ModelError as e:
        if "E005" in str(e) or "sensitive" in str(e).lower():
            print(f"Replicate API 报错 ({e})，回退到本地 rembg 抠图...")
            from run_pet_image_matting_rembg import run_matting_rembg
            return run_matting_rembg(image_path, pet_type, out_path)
        raise


def main():
    parser = argparse.ArgumentParser(description="宠物抠图（google/nano-banana）")
    parser.add_argument("image", help="去背景后的图片路径")
    parser.add_argument("--pet-type", "-t", choices=["head", "half_body", "full_body"], default="head")
    parser.add_argument("--out", "-o", default=None)
    args = parser.parse_args()
    run_matting(args.image, args.pet_type, args.out)


if __name__ == "__main__":
    main()
