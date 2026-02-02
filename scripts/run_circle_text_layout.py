# -*- coding: utf-8 -*-
"""
圆形文字布局：在图像上渲染圆形排列的文字。
基于三层架构：短语级均分 + 单词级间距 + 字符级高精度排版

用法:
  python run_circle_text_layout.py --phrases "I LOVE YOU" "I LOVE YOU" "I LOVE YOU" --out output/circle_text.png
  python run_circle_text_layout.py --config config.json --base-image output/final.png --out output/with_circle_text.png
  python run_circle_text_layout.py --preset pet_tag --text "LUCKY" --out output/pet_tag.png
"""
import argparse
import json
import os
import sys
from typing import List, Optional

from PIL import Image

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from skills.circle_text_skill import CircleTextLayoutSkill


def load_config_from_file(config_path: str) -> dict:
    """从JSON文件加载配置"""
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"配置文件不存在: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config


def create_preset_config(preset: str, text: str = None, **kwargs) -> dict:
    """根据预设创建配置"""
    base_config = {
        "canvas": {"width": 800, "height": 800, "center": [400, 400], "radius": 300},
        "layout": {"start_angle_deg": 0, "clockwise": True, "align": "center"},
        "spacing": {"char_tracking_px": 1.5, "word_spacing_px": 24},
        "font": {"path": "assets/fonts/AaHuanLeBao-2.ttf", "size": 48},
        "style": {"fill_rgba": [0, 0, 0, 255]},
        "render": {"supersample": 2}
    }

    if preset == "pet_tag":
        # 宠物标签预设
        base_config.update({
            "canvas": {"width": 600, "height": 600, "center": [300, 300], "radius": 250},
            "layout": {"start_angle_deg": 0, "clockwise": True, "align": "center"},
            "spacing": {"char_tracking_px": 2.0, "word_spacing_px": 20},
            "font": {"path": "assets/fonts/AaHuanLeBao-2.ttf", "size": 36},
            "style": {"fill_rgba": [255, 182, 193, 255]}  # 浅粉色
        })
        if text:
            base_config["phrases"] = [text, text, text]

    elif preset == "brand_badge":
        # 品牌徽章预设
        base_config.update({
            "canvas": {"width": 800, "height": 800, "center": [400, 400], "radius": 320},
            "layout": {"start_angle_deg": 180, "clockwise": True, "align": "center"},
            "spacing": {"char_tracking_px": 1.0, "word_spacing_px": 15},
            "font": {"path": "assets/fonts/AaHuanLeBao-2.ttf", "size": 32},
            "style": {"fill_rgba": [255, 215, 0, 255]},  # 金色
            "render": {"supersample": 3}  # 高质量
        })
        if text:
            words = text.split()
            if len(words) <= 3:
                base_config["phrases"] = words
            else:
                # 多于3个单词时，取前3个
                base_config["phrases"] = words[:3]

    elif preset == "holiday_card":
        # 节日卡片预设
        base_config.update({
            "canvas": {"width": 700, "height": 700, "center": [350, 350], "radius": 280},
            "layout": {"start_angle_deg": 270, "clockwise": True, "align": "center"},
            "spacing": {"char_tracking_px": 2.5, "word_spacing_px": 35},
            "font": {"path": "assets/fonts/AaHuanLeBao-2.ttf", "size": 44},
            "style": {"fill_rgba": [255, 0, 0, 255]},  # 红色
        })
        if text:
            words = text.split()
            if len(words) == 2:
                base_config["phrases"] = words
            else:
                # 其他情况，创建两个短语
                mid = len(words) // 2
                base_config["phrases"] = [" ".join(words[:mid]), " ".join(words[mid:])]

    return base_config


def run_circle_text_layout(
    phrases: List[str] = None,
    base_image_path: str = None,
    config_path: str = None,
    preset: str = None,
    text: str = None,
    width: int = 800,
    height: int = 800,
    center_x: int = None,
    center_y: int = None,
    radius: int = 300,
    canvas_rotation: float = 0,
    start_angle: float = 0,
    clockwise: bool = True,
    orientation: str = "outward",
    font_path: str = "assets/fonts/AaHuanLeBao-2.ttf",
    font_size: int = 48,
    color_r: int = 0,
    color_g: int = 0,
    color_b: int = 0,
    color_a: int = 255,
    char_tracking: float = 1.5,
    word_spacing: float = 24,
    supersample: int = 2,
    out_path: str = None,
):
    """
    运行圆形文字布局

    Args:
        phrases: 短语列表
        base_image_path: 基础图像路径
        config_path: 配置文件路径
        preset: 预设配置名
        text: 文本内容（用于预设）
        width, height: 画布尺寸
        center_x, center_y: 圆心坐标
        radius: 圆半径
        start_angle: 起始角度
        clockwise: 是否顺时针
        font_path: 字体路径
        font_size: 字体大小
        color_r, color_g, color_b, color_a: RGBA颜色
        char_tracking: 字符间距
        word_spacing: 单词间距
        supersample: 超采样倍数
        out_path: 输出路径
    """
    # 初始化skill
    skill = CircleTextLayoutSkill()

    # 加载基础图像
    base_image = None
    if base_image_path:
        if not os.path.isfile(base_image_path):
            raise FileNotFoundError(f"基础图像不存在: {base_image_path}")
        base_image = Image.open(base_image_path).convert("RGBA")
        print(f"加载基础图像: {base_image_path}")

    # 构建配置
    if config_path:
        # 从文件加载配置
        config = load_config_from_file(config_path)
        print(f"从配置文件加载: {config_path}")
    elif preset:
        # 使用预设配置
        config = create_preset_config(preset, text)
        print(f"使用预设配置: {preset}")
    else:
        # 手动构建配置
        if center_x is None:
            center_x = width // 2
        if center_y is None:
            center_y = height // 2

        if phrases is None:
            phrases = ["CIRCLE", "TEXT", "LAYOUT"]

        config = {
            "canvas": {
                "width": width,
                "height": height,
                "center": [center_x, center_y],
                "radius": radius,
                "canvas_rotation_deg": canvas_rotation
            },
            "phrases": phrases,
            "layout": {
                "start_angle_deg": start_angle,
                "clockwise": clockwise,
                "align": "center",
                "orientation": orientation
            },
            "spacing": {
                "char_tracking_px": char_tracking,
                "word_spacing_px": word_spacing
            },
            "font": {
                "path": font_path,
                "size": font_size
            },
            "style": {
                "fill_rgba": [color_r, color_g, color_b, color_a]
            },
            "render": {
                "supersample": supersample
            }
        }

    print(f"配置信息:")
    print(f"  画布: {config['canvas']['width']}x{config['canvas']['height']}")
    print(f"  圆心: {config['canvas']['center']}, 半径: {config['canvas']['radius']}")
    print(f"  短语: {config['phrases']}")
    print(f"  起始角度: {config['layout']['start_angle_deg']}°, 方向: {'顺时针' if config['layout']['clockwise'] else '逆时针'}")
    print(f"  字体: {config['font']['path']} (大小: {config['font']['size']})")
    print(f"  颜色: RGBA{config['style']['fill_rgba']}")
    print(f"  间距: 字符 {config['spacing']['char_tracking_px']}px, 单词 {config['spacing']['word_spacing_px']}px")
    print(f"  超采样: {config['render']['supersample']}x")

    # 执行渲染
    print("开始渲染圆形文字...")
    result_image = skill.render(base_image, config)

    # 保存结果
    if out_path is None:
        out_dir = os.path.join(os.path.dirname(__file__), "..", "output")
        out_path = os.path.join(out_dir, "circle_text_result.png")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    result_image.save(out_path)
    print(f"渲染完成，已保存: {out_path}")

    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="圆形文字布局：基于三层架构的高精度圆形文字排版",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 基本使用
  python run_circle_text_layout.py --phrases "I LOVE YOU" "I LOVE YOU" "I LOVE YOU"

  # 使用预设配置
  python run_circle_text_layout.py --preset pet_tag --text "LUCKY"

  # 从配置文件加载
  python run_circle_text_layout.py --config circle_config.json

  # 基于现有图像
  python run_circle_text_layout.py --base-image output/final.png --phrases "BRAND" "NAME"

  # 自定义参数
  python run_circle_text_layout.py --phrases "HELLO" "WORLD" --width 1000 --radius 400 --color-r 255 --color-g 0 --color-b 0
        """
    )

    # 输入选项
    input_group = parser.add_argument_group('输入选项')
    input_group.add_argument("--phrases", nargs="+", help="短语列表，如 'I LOVE YOU' 'I LOVE YOU'")
    input_group.add_argument("--base-image", help="基础图像路径")
    input_group.add_argument("--config", dest="config_path", help="配置文件路径 (JSON)")
    input_group.add_argument("--preset", choices=["pet_tag", "brand_badge", "holiday_card"],
                           help="预设配置")
    input_group.add_argument("--text", help="文本内容（用于预设配置）")

    # 画布设置
    canvas_group = parser.add_argument_group('画布设置')
    canvas_group.add_argument("--width", type=int, default=800, help="画布宽度 (默认: 800)")
    canvas_group.add_argument("--height", type=int, default=800, help="画布高度 (默认: 800)")
    canvas_group.add_argument("--center-x", type=int, help="圆心X坐标 (默认: 宽度/2)")
    canvas_group.add_argument("--center-y", type=int, help="圆心Y坐标 (默认: 高度/2)")
    canvas_group.add_argument("--radius", type=int, default=300, help="圆半径 (默认: 300)")
    canvas_group.add_argument("--canvas-rotation", type=float, default=0, help="整个画布旋转角度(度) (默认: 0)")

    # 布局设置
    layout_group = parser.add_argument_group('布局设置')
    layout_group.add_argument("--start-angle", type=float, default=0, help="起始角度(度) (默认: 0)")
    layout_group.add_argument("--counter-clockwise", action="store_false", dest="clockwise",
                             help="逆时针方向 (默认: 顺时针)")
    layout_group.add_argument("--orientation", choices=["outward", "inward"], default="outward",
                             help="文字朝向 (默认: outward)")

    # 字体设置
    font_group = parser.add_argument_group('字体设置')
    font_group.add_argument("--font-path", default="assets/fonts/AaHuanLeBao-2.ttf",
                           help="字体文件路径")
    font_group.add_argument("--font-size", type=int, default=48, help="字体大小 (默认: 48)")

    # 颜色设置
    color_group = parser.add_argument_group('颜色设置')
    color_group.add_argument("--color-r", type=int, default=0, help="红色分量 0-255 (默认: 0)")
    color_group.add_argument("--color-g", type=int, default=0, help="绿色分量 0-255 (默认: 0)")
    color_group.add_argument("--color-b", type=int, default=0, help="蓝色分量 0-255 (默认: 0)")
    color_group.add_argument("--color-a", type=int, default=255, help="透明度 0-255 (默认: 255)")

    # 间距设置
    spacing_group = parser.add_argument_group('间距设置')
    spacing_group.add_argument("--char-tracking", type=float, default=1.5,
                              help="字符间距(像素) (默认: 1.5)")
    spacing_group.add_argument("--word-spacing", type=float, default=24,
                              help="单词间距(像素) (默认: 24)")

    # 渲染设置
    render_group = parser.add_argument_group('渲染设置')
    render_group.add_argument("--supersample", type=int, default=2, choices=[1, 2, 3, 4],
                             help="超采样倍数 (默认: 2)")

    # 输出设置
    parser.add_argument("--out", dest="out_path", help="输出文件路径")

    args = parser.parse_args()

    # 参数验证
    if not any([args.phrases, args.config_path, args.preset]):
        parser.error("必须提供以下之一: --phrases, --config, 或 --preset")

    if args.preset and not args.text:
        parser.error("--preset 模式需要提供 --text 参数")

    try:
        result_path = run_circle_text_layout(
            phrases=args.phrases,
            base_image_path=args.base_image,
            config_path=args.config_path,
            preset=args.preset,
            text=args.text,
            width=args.width,
            height=args.height,
            center_x=args.center_x,
            center_y=args.center_y,
            radius=args.radius,
            canvas_rotation=args.canvas_rotation,
            start_angle=args.start_angle,
            clockwise=args.clockwise,
            orientation=args.orientation,
            font_path=args.font_path,
            font_size=args.font_size,
            color_r=args.color_r,
            color_g=args.color_g,
            color_b=args.color_b,
            color_a=args.color_a,
            char_tracking=args.char_tracking,
            word_spacing=args.word_spacing,
            supersample=args.supersample,
            out_path=args.out_path,
        )
        print(f"\n[SUCCESS] 圆形文字布局完成: {result_path}")

    except Exception as e:
        print(f"[ERROR] 渲染失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()