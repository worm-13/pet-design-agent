# -*- coding: utf-8 -*-
"""
完整流程：去背景1 → 抠图 → 去背景2 → 模板合成 → 文字(可选)
用法: python run_full_pipeline.py <原图路径> [--template 模板] [--pet-type head|half_body|full_body] [--text 文字] [--out-dir 输出目录]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve(path: str) -> str:
    if not path or os.path.isabs(path):
        return path
    return os.path.join(PROJECT_ROOT, path)


def run_pipeline(
    image_path: str,
    template_path: str = None,
    pet_type: str = "head",
    text: str = None,
    text_color: str = "#000000",
    scale: float = 0.75,
    out_dir: str = None,
    use_rembg: bool = False,
) -> str:
    if out_dir is None:
        out_dir = os.path.join(PROJECT_ROOT, "output")
    os.makedirs(out_dir, exist_ok=True)

    # 1. 去除背景（原图 → no_bg.png）
    from run_background_removal import run_background_removal
    no_bg_path = run_background_removal(image_path, os.path.join(out_dir, "no_bg.png"))
    no_bg_path = os.path.abspath(_resolve(no_bg_path))
    if not os.path.isfile(no_bg_path):
        raise FileNotFoundError(f"步骤1 输出不存在: {no_bg_path}")

    # 2. 抠出主体（传入去背景后的 no_bg.png）
    print(f"抠图输入: {no_bg_path}")
    if use_rembg:
        from run_pet_image_matting_rembg import run_matting_rembg
        extracted = run_matting_rembg(no_bg_path, pet_type, os.path.join(out_dir, "extracted.png"))
    else:
        from run_pet_image_matting import run_matting
        extracted = run_matting(no_bg_path, pet_type, os.path.join(out_dir, "extracted.png"))

    # 3. 再次去除背景
    extracted_clean = run_background_removal(extracted, os.path.join(out_dir, "extracted_clean.png"))

    # 4. 模板合成
    if template_path is None:
        import glob
        templates = glob.glob(os.path.join(PROJECT_ROOT, "templates", "backgrounds", "*.png"))
        template_path = templates[0] if templates else None
    if not template_path or not os.path.isfile(_resolve(template_path)):
        raise FileNotFoundError("未找到模板，请指定 --template")

    from run_compose_pet_on_template import compose_pet_on_template
    design_path = os.path.join(out_dir, "design.png")
    compose_pet_on_template(extracted_clean, _resolve(template_path), out_path=design_path, scale=scale)

    # 5. 文字(可选)
    if text:
        from run_text_style_adjustment import run_text_adjustment
        final_path = os.path.join(out_dir, "final.png")
        run_text_adjustment(design_path, content=text, position="bottom-center", color=text_color, out_path=final_path)
        print(f"\n完成！最终图: {final_path}")
        return final_path

    print(f"\n完成！设计图: {design_path}")
    return design_path


def main():
    parser = argparse.ArgumentParser(description="完整流程：去背景→抠图→去背景→合成→文字")
    parser.add_argument("image", help="原图路径")
    parser.add_argument("--template", "-T", default=None, help="模板背景图路径")
    parser.add_argument("--pet-type", "-t", choices=["head", "half_body", "full_body"], default="head")
    parser.add_argument("--text", "-c", default=None, help="底部文字（可选）")
    parser.add_argument("--text-color", default="#000000", help="文字颜色，如 #8B008B")
    parser.add_argument("--scale", "-s", type=float, default=0.75, help="宠物相对背景的比例，默认 0.75（越大头越大）")
    parser.add_argument("--out-dir", "-o", default=None, help="输出目录")
    parser.add_argument("--use-rembg", action="store_true", help="强制使用本地 rembg 抠图（跳过 Replicate，避免 E005）")
    args = parser.parse_args()

    run_pipeline(
        args.image,
        template_path=args.template,
        pet_type=args.pet_type,
        text=args.text,
        text_color=args.text_color,
        scale=args.scale,
        out_dir=args.out_dir,
        use_rembg=args.use_rembg,
    )


if __name__ == "__main__":
    main()
