# -*- coding: utf-8 -*-
"""测试清新粉蓝预设"""
import sys
import os

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
sys.path.insert(0, _PROJECT_ROOT)

from skills.circle_text_skill.presets import get_config_for_template

config = get_config_for_template("清新粉蓝", "lol", 800, 800)
print("清新粉蓝模板配置:")
print(f"  半径: {config['canvas']['radius']} (应该是320)")
print(f"  字体大小: {config['font']['size']} (应该是64)")
print(f"  起始角度: {config['layout']['start_angle_deg']} (应该是270)")
print(f"  圆心: {config['canvas']['center']} (应该是[400, 400])")
print(f"  短语: {config['phrases']} (应该是['lol', 'lol', 'lol', 'lol'])")
print(f"  字符间距: {config['spacing']['char_tracking_px']} (应该是2.0)")
print(f"  单词间距: {config['spacing']['word_spacing_px']} (应该是20)")
