# -*- coding: utf-8 -*-
"""
背景去除：使用 851-labs/background-remover 去除原图背景。
用法: python run_background_removal.py <原图路径> [--out 输出路径]
"""
import argparse
import os

from replicate_utils import BG_REMOVER_VERSION, download_url, ensure_token

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve(path: str) -> str:
    if not path or os.path.isabs(path):
        return path
    return os.path.join(PROJECT_ROOT, path)


def run_background_removal(image_path: str, out_path: str = None) -> str:
    import replicate

    ensure_token()
    image_path = _resolve(image_path)
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"原图不存在: {image_path}")

    if out_path is None:
        out_path = os.path.join(PROJECT_ROOT, "output", "no_bg.png")
    out_path = _resolve(out_path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    with open(image_path, "rb") as f:
        output = replicate.run(
            BG_REMOVER_VERSION,
            input={
                "image": f,
                "background": "rgba",
            },
        )

    if isinstance(output, str):
        url = output
    elif hasattr(output, "url"):
        url = output.url
    else:
        url = str(output)

    download_url(url, out_path)
    print(f"已去除背景: {out_path}")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="去除图像背景（851-labs/background-remover）")
    parser.add_argument("image", help="原图路径")
    parser.add_argument("--out", "-o", default=None, help="输出路径")
    args = parser.parse_args()
    run_background_removal(args.image, args.out)


if __name__ == "__main__":
    main()
