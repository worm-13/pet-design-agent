# CircleTextLayoutSkill

三层圆形文字排版Skill：**短语级均分 + 单词级间距 + 字符级高精度排版**

## 🎯 核心特性

### 三层架构设计
- **短语级**：多个短语在圆环上等角度分布，每个短语围绕锚点角居中对齐
- **单词级**：短语内拆分为单词，单词之间有独立的`word_spacing`
- **字符级**：使用字形真实宽度（advance）推进，支持`tracking`/`kerning`

### 高质量渲染
- ✅ 超采样抗锯齿（默认2x）
- ✅ 单字符独立RGBA图层
- ✅ 旋转防裁切边距
- ✅ Alpha合成高质量

## 📦 安装使用

```python
from skills.circle_text_skill import CircleTextLayoutSkill

skill = CircleTextLayoutSkill()
image = skill.render(base_image=None, config=config)
```

## ⚙️ 配置参数

### 完整配置示例

```python
config = {
    "canvas": {
        "width": 1024,
        "height": 1024,
        "center": [512, 512],
        "radius": 430
    },

    "phrases": [
        "i love you",
        "i love you",
        "i love you"
    ],

    "layout": {
        "start_angle_deg": 210,
        "clockwise": True,
        "align": "center"
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
        "fill_rgba": [248, 170, 180, 230]
    },

    "render": {
        "supersample": 2
    }
}
```

### 参数详解

| 参数组 | 参数 | 类型 | 默认值 | 说明 |
|--------|------|------|--------|------|
| **canvas** | width | int | 800 | 画布宽度 |
| | height | int | 800 | 画布高度 |
| | center | [int,int] | [400,400] | 圆心坐标 |
| | radius | float | 320 | 圆半径 |
| **phrases** | - | [str] | [] | 短语列表 |
| **layout** | start_angle_deg | float | 0 | 起始角度 |
| | clockwise | bool | True | 是否顺时针 |
| | align | str | "center" | 对齐方式 |
| **spacing** | char_tracking_px | float | 1.5 | 字符间距 |
| | word_spacing_px | float | 24 | 单词间距 |
| **font** | path | str | - | 字体路径 |
| | size | int | 48 | 字体大小 |
| **style** | fill_rgba | [int×4] | [0,0,0,255] | RGBA填充色 |
| **render** | supersample | int | 2 | 超采样倍数 |

## 🎨 使用场景

### 宠物定制
```python
from skills.circle_text_skill.presets import get_config_for_pet_name

config = get_config_for_pet_name("Max")
skill = CircleTextLayoutSkill()
image = skill.render(None, config)
```

### 徽章设计
```python
from skills.circle_text_skill.presets import BADGE_CONFIG

config = BADGE_CONFIG.copy()
config["phrases"] = ["EXCELLENCE", "ACHIEVEMENT", "COMMITMENT"]
skill = CircleTextLayoutSkill()
image = skill.render(None, config)
```

### 品牌LOGO
```python
from skills.circle_text_skill.presets import LOGO_CONFIG

config = LOGO_CONFIG.copy()
config["phrases"] = ["BRAND", "NAME"]
skill = CircleTextLayoutSkill()
image = skill.render(None, config)
```

## 🚀 运行演示

```bash
# 运行所有演示
python -m circle_text_skill.demo

# 生成的文件：
# - output/skill_demo_basic.png     # 基础演示
# - output/skill_demo_pet.png       # 宠物定制
# - output/skill_demo_badge.png     # 徽章设计
# - output/skill_demo_custom.png    # 自定义配置
```

## 🏗️ 模块结构

```
skills/circle_text_skill/
├── __init__.py              # 包初始化
├── skill.py                 # 主Skill类
├── geometry.py              # 几何计算
├── font_metrics.py          # 字体度量
├── renderer.py              # 渲染引擎
├── presets.py               # 预设配置
├── demo.py                  # 演示脚本
└── README.md               # 文档
```

## 🔬 技术实现

### 短语锚点计算
```python
# 等角度分布
step = 2π / phrase_count
anchor[i] = start_angle + i * step
```

### 短语居中对齐
```python
# 计算短语弧长
phrase_arc = measure_phrase_arc(phrase, font, char_tracking, word_spacing)

# 居中起始角度
phrase_start = anchor_angle - phrase_arc / (2 * radius)
```

### 高精度字符渲染
```python
# 使用真实advance推进
advance = font.getlength(char)

# 支持kerning修正
if prev_char:
    pair_advance = font.getlength(prev_char + char)
    kerning = pair_advance - (prev_advance + advance)
    advance += kerning

# 超采样渲染
char_image = render_supersample(char, font, fill_rgba, 2)
char_image.resize(target_size, Image.LANCZOS)
```

## 📊 验收标准

- ✅ 三个短语120°等分分布
- ✅ 每个短语内部单词间距清晰
- ✅ 字符自然、不挤压、无倾斜错位
- ✅ 整体视觉稳定平衡
- ✅ 支持超采样抗锯齿
- ✅ 单字符旋转防裁切

## 🎯 设计原则

**不要把文本当字符串流，要当作「短语锚点 + 内部排版系统」**

按照这个原则，Skill实现了完整的三层排版架构，确保在各种复杂场景下都能提供专业级的圆形文字排版效果。

## 📄 许可证

本项目遵循规范要求实现，专为圆形文字排版场景优化。