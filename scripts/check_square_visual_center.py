# -*- coding: utf-8 -*-
"""验证正方形图像的视觉中心对齐"""
import sys
import os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _PROJECT_ROOT)

from PIL import Image
from utils.visual_center import compute_visual_center

def check_image(image_path):
    img = Image.open(image_path)
    vc = compute_visual_center(img)
    canvas_center_x = img.width / 2
    canvas_center_y = img.height / 2
    
    offset_x = abs(vc[0] - canvas_center_x)
    offset_y = abs(vc[1] - canvas_center_y)
    
    print(f"Image: {os.path.basename(image_path)}")
    print(f"  Size: {img.size}, Ratio: {img.size[0]/img.size[1]:.2f}")
    print(f"  Visual Center: ({vc[0]:.1f}, {vc[1]:.1f})")
    print(f"  Canvas Center: ({canvas_center_x:.1f}, {canvas_center_y:.1f})")
    print(f"  Offset: ({offset_x:.1f}, {offset_y:.1f})")
    print()

if __name__ == "__main__":
    session_id = sys.argv[1] if len(sys.argv) > 1 else "session_004"
    
    pet_a_path = os.path.join("sessions", session_id, "extracted", "pet_a_extracted.png")
    pet_b_path = os.path.join("sessions", session_id, "extracted", "pet_b_extracted.png")
    
    if os.path.exists(pet_a_path):
        check_image(pet_a_path)
    if os.path.exists(pet_b_path):
        check_image(pet_b_path)
