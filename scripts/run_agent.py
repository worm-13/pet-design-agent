# -*- coding: utf-8 -*-
"""
Agent 交互循环：解析用户自然语言指令 → 调用 pipeline 执行 → 输出结果。
支持多轮对话、增量执行。
用法: python run_agent.py [--image 原图] [--out-dir 输出目录]
"""
import argparse
import os
import sys

# 统一使用 UTF-8，避免中文路径与打印乱码
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from run_full_pipeline import run_pipeline


def _resolve(path: str) -> str:
    if not path or os.path.isabs(path):
        return path
    return os.path.join(PROJECT_ROOT, path)


def main():
    parser = argparse.ArgumentParser(description="Agent 交互循环：自然语言驱动宠物设计")
    parser.add_argument("--image", "-i", default=None, help="原图路径（首次输入或重置后需提供）")
    parser.add_argument("--out-dir", "-o", default=None, help="输出目录，默认 output")
    args = parser.parse_args()

    out_dir = args.out_dir or os.path.join(PROJECT_ROOT, "output")
    out_dir = os.path.abspath(_resolve(out_dir))
    os.makedirs(out_dir, exist_ok=True)

    state_path = os.path.join(out_dir, "state.json")
    image_path = args.image
    if image_path:
        image_path = os.path.abspath(_resolve(image_path))

    print("=" * 50)
    print("宠物设计 Agent（输入指令，输入 q 退出）")
    print("=" * 50)
    if image_path and os.path.isfile(image_path):
        print(f"原图: {image_path}")
    else:
        print("提示: 首次需提供 --image 原图路径，或输入「用这张图 xxx」后附路径")

    while True:
        try:
            line = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见")
            break
        if not line:
            continue
        if line.lower() in ("q", "quit", "exit", "退出"):
            print("再见")
            break

        instruction = line

        # 尝试从指令中提取图片路径（如「用 C:/xxx.jpg 半身」）
        import re
        m = re.search(r'[用以]([^\s]+\.(?:jpg|jpeg|png|webp))\s*(.*)', instruction, re.I)
        if m:
            img = m.group(1).strip()
            rest = m.group(2).strip()
            if os.path.isfile(_resolve(img)):
                image_path = os.path.abspath(_resolve(img))
                instruction = rest if rest else instruction
            elif os.path.isfile(img):
                image_path = os.path.abspath(img)
                instruction = rest if rest else instruction

        if not image_path or not os.path.isfile(image_path):
            print("错误: 请先提供原图路径（--image 或 用 xxx.jpg）")
            continue

        try:
            result = run_pipeline(
                image_path,
                instruction=instruction,
                out_dir=out_dir,
            )
            if result and os.path.isfile(result):
                print(f"结果: {result}")
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
