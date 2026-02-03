# -*- coding: utf-8 -*-
"""
多宠物任务执行脚本：处理中文文件名
"""
import os
import sys

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
from run_multi_pet_matting import run_multi_pet_matting
from run_multi_pet_composition import run_multi_pet_composition
from skills.circle_text_skill import CircleTextLayoutSkill
from PIL import Image


def find_file_in_dir(directory, filename_pattern):
    """在目录中查找文件（支持部分匹配）"""
    if not os.path.exists(directory):
        return None
    
    # 先尝试精确匹配
    full_path = os.path.join(directory, filename_pattern)
    if os.path.exists(full_path):
        return full_path
    
    # 尝试部分匹配
    for file in os.listdir(directory):
        if filename_pattern in file or file.endswith(filename_pattern.split('.')[-1]):
            return os.path.join(directory, file)
    
    return None


def add_circle_text_to_image(
    base_image_path: str,
    text: str,
    font_path: str,
    color_rgba: tuple,
    position: str = "bottom-center",
    radius: float = None,
    out_path: str = None
) -> str:
    """在图像上添加圆形文字"""
    base_image = Image.open(base_image_path).convert("RGBA")
    width, height = base_image.size

    if position == "bottom-center":
        center_x = width // 2
        center_y = int(height * 0.85)
    else:
        center_x = width // 2
        center_y = int(height * 0.85)

    if radius is None:
        radius = min(width, height) * 0.40  # 图像尺寸的40%（增大半径）

    config = {
        "canvas": {
            "width": width,
            "height": height,
            "center": [center_x, center_y],
            "radius": radius,
            "canvas_rotation_deg": 0
        },
        "phrases": [text],
        "layout": {
            "start_angle_deg": 270,  # 从圆的下方开始（270度 = 6点钟方向）
            "clockwise": True,
            "align": "center",
            "orientation": "outward"
        },
        "spacing": {
            "char_tracking_px": 2.0,
            "word_spacing_px": 20
        },
        "font": {
            "path": font_path,
            "size": int(min(width, height) * 0.08)
        },
        "style": {
            "fill_rgba": list(color_rgba)
        },
        "render": {
            "supersample": 2
        }
    }

    skill = CircleTextLayoutSkill()
    result_image = skill.render(base_image, config)

    if out_path is None:
        out_path = base_image_path.replace(".png", "_final.png").replace(".jpg", "_final.png")

    result_image.save(out_path, "PNG")
    print(f"圆形文字已添加: {out_path}")
    return out_path


def main():
    # 查找文件
    input_dir = os.path.join(_PROJECT_ROOT, "input")
    template_dir = os.path.join(_PROJECT_ROOT, "templates", "backgrounds")
    
    # 查找图片文件
    cat_file = find_file_in_dir(input_dir, "pet_cat.png")
    wechat_file = find_file_in_dir(input_dir, "微信图片")
    
    if not cat_file:
        print("找不到 cat.png")
        return
    
    if not wechat_file:
        print("找不到微信图片文件")
        return
    
    # 查找模板
    template_file = find_file_in_dir(template_dir, "清新粉蓝")
    if not template_file:
        print("找不到清新粉蓝模板")
        return
    
    print(f"找到文件:")
    print(f"  图片1: {cat_file}")
    print(f"  图片2: {wechat_file}")
    print(f"  模板: {template_file}")
    
    session_id = "multi_pet_love_v4"
    
    # 1. 初始化状态（清理旧状态）
    state_manager = StateManager()
    
    # 清理旧会话目录（如果存在）
    session_dir = os.path.join(_PROJECT_ROOT, "sessions", session_id)
    if os.path.exists(session_dir):
        import shutil
        shutil.rmtree(session_dir)
        print(f"已清理旧会话: {session_id}")
    
    # 2. 添加宠物（只添加2只）
    state_manager.add_pet(session_id, cat_file, crop_mode="head")
    state_manager.add_pet(session_id, wechat_file, crop_mode="head")
    
    # 3. 设置模板
    state_manager.set_template(session_id, template_file)
    
    print("开始抠图...")
    # 4. 执行抠图
    extracted_paths = run_multi_pet_matting(session_id)
    
    print("开始合成...")
    # 5. 执行合成
    design_path = run_multi_pet_composition(session_id)
    
    print("添加圆形文字...")
    # 6. 添加圆形文字
    font_path = os.path.join(_PROJECT_ROOT, "assets", "fonts", "AaHuanLeBao-2.ttf")
    final_path = add_circle_text_to_image(
        base_image_path=design_path,
        text="LOVE",
        font_path=font_path,
        color_rgba=(255, 182, 193, 255),  # 粉色
        position="bottom-center"
    )
    
    print(f"\n完成！最终结果: {final_path}")


if __name__ == "__main__":
    main()
