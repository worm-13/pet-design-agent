---
name: circle-text-skill
description: 圆形文字排版核心实现Skill，提供完整的文字圆形布局功能
---

**实现与脚本**：本技能逻辑与脚本未改动，位于项目 `skills/circle_text_skill/` 与 `scripts/`；此处为 Cursor 约定入口，便于 Agent 发现。

# Circle Text Skill

圆形文字排版的核心实现Skill，包含完整的渲染引擎和配置系统。

## 核心功能

- ✅ **三层架构**：短语层、单词层、字符层的高精度排版
- ✅ **智能布局**：等角度分布、居中对齐、顺时针/逆时针排列
- ✅ **文字旋转**：支持inward/outward朝向，以及文字图层旋转
- ✅ **高质量渲染**：超采样抗锯齿、透明合成
- ✅ **多语言支持**：支持中文、韩文、日文等多种语言文字

## 使用方式

```python
from skills.circle_text_skill import CircleTextLayoutSkill

skill = CircleTextLayoutSkill()
config = {
    "canvas": {
        "width": 800,
        "height": 800,
        "center": [400, 400],
        "radius": 300,
        "canvas_rotation_deg": 0
    },
    "phrases": ["TEXT", "CONTENT"],
    "layout": {
        "start_angle_deg": 0,
        "clockwise": True,
        "align": "center",
        "orientation": "inward"
    },
    "spacing": {
        "char_tracking_px": 1.5,
        "word_spacing_px": 24
    },
    "font": {
        "path": "assets/fonts/AaHuanLeBao-2.ttf",
        "size": 48
    },
    "style": {
        "fill_rgba": [0, 0, 0, 255]
    },
    "render": {
        "supersample": 2
    }
}

result_image = skill.render(base_image, config)
```

## 技术特性

- **精确排版**：基于glyph advance的真实字符宽度
- **智能旋转**：文字沿圆切线对齐，支持多种朝向
- **性能优化**：字体缓存、角度预计算
- **扩展性**：模块化设计，易于扩展新功能

## 文件结构

```
skills/circle_text_skill/
├── __init__.py          # 包初始化
├── skill.py             # 主Skill类
├── renderer.py          # 渲染引擎
├── geometry.py          # 几何计算
├── font_metrics.py      # 字体度量
├── presets.py           # 预设配置
├── demo.py              # 演示代码
└── README.md            # 详细文档
```

## 相关脚本

- `scripts/run_circle_text_layout.py` - 命令行工具
- 更多用法请参考 `skills/circle_text_skill/README.md`
