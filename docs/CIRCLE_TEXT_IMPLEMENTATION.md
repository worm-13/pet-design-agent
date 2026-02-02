# 圆形文字排版功能实现详解

## 📋 功能概述

圆形文字排版功能实现了高质量的圆形文字渲染，支持短语级均分、单词级间距、字符级高精度排版，能够在图像上生成自然、美观的圆形文字效果。

### 🎯 核心特性

- **三层架构**：短语级均分 → 单词级间距 → 字符级高精度排版
- **高质量渲染**：超采样抗锯齿，支持1-4x倍数
- **智能布局**：等角度分布、自动居中对齐
- **预设配置**：宠物标签、品牌徽章、节日问候等场景

## 🏗️ 技术架构

### 1. 核心算法层 (circle_text_skill/)

#### 文件结构
```
circle_text_skill/
├── skill.py              # 主Skill类，统一接口
├── geometry.py           # 几何计算（角度、弧长、分布）
├── font_metrics.py       # 字体度量（字符宽度、kerning）
├── renderer.py           # 渲染引擎（字符渲染、旋转）
├── presets.py            # 预设配置
├── demo.py               # 演示功能
└── __init__.py           # 包初始化
```

#### 核心类：CircleTextLayoutSkill

```python
class CircleTextLayoutSkill:
    def render(self, base_image, config) -> Image.Image:
        """
        统一渲染接口
        - 解析配置参数
        - 计算短语锚点角度
        - 逐个渲染短语
        - 返回合成结果
        """
```

### 2. Skill标准化层 (skills/circle-text-layout/)

#### 接口定义 (SKILL.md)
```markdown
---
name: circle-text-layout
description: 三层圆形文字排版Skill。支持短语级均分、单词级间距、字符级高精度排版
---

# 输入输出Schema
- 输入：base_image（可选）+ config字典
- 输出：PIL.Image (RGBA)
- 配置包含：canvas, phrases, layout, spacing, font, style, render
```

#### 技术文档 (reference.md)
- 三层架构详解
- 字体度量规范
- 渲染优化策略
- 性能优化方案

### 3. 运行脚本层 (scripts/run_circle_text_layout.py)

#### 命令行接口
```bash
# 预设模式
python scripts/run_circle_text_layout.py --preset pet_tag --text "LUCKY"

# 自定义配置
python scripts/run_circle_text_layout.py --phrases "I LOVE YOU" "I LOVE YOU" "I LOVE YOU"

# 基于现有图像
python scripts/run_circle_text_layout.py --base-image output/final.png --phrases "BRAND"
```

#### 功能特性
- 参数解析和验证
- 预设配置管理
- 错误处理和日志
- 输出文件管理

### 4. 集成编排层 (skills/pet-design-orchestrator/)

#### 编排器集成
```markdown
## 可用技能
| 技能目录名 | 用途 |
| circle-text-layout | 圆形文字排版与渲染 |

## 默认工作流
7. **应用圆形文字装饰** → 使用 circle-text-layout（可选）
```

#### 增量更新支持
- 圆形文字相关指令 → 只调用 circle-text-layout
- 避免重复处理其他步骤

## 🔧 核心算法实现

### 三层排版架构

#### 1. 短语层 (Phrase Layer)
```python
def compute_phrase_anchor_angles(phrase_count, start_angle_deg, clockwise):
    """计算短语锚点角度 - 等角度分布"""
    step = 2 * math.pi / phrase_count
    for i in range(phrase_count):
        angle = start_angle_deg + (i * step if clockwise else -i * step)
        anchors.append(angle % (2 * math.pi))
```

#### 2. 单词层 (Word Layer)
```python
def parse_phrases(phrases):
    """单词级解析 - 支持空格分割"""
    parsed = []
    for phrase in phrases:
        words = [word.strip() for word in phrase.split() if word.strip()]
        parsed.append(words)
    return parsed
```

#### 3. 字符层 (Character Layer)
```python
def get_char_advance(char, font, prev_char=None):
    """字符级高精度度量"""
    # 优先使用font.getlength()获取真实advance
    advance = font.getlength(char)

    # 支持kerning修正
    if prev_char:
        pair_advance = font.getlength(prev_char + char)
        kerning = pair_advance - (prev_advance + advance)
        advance += kerning

    return advance
```

### 渲染引擎

#### 超采样抗锯齿
```python
def render_char_supersample(char, font, fill_rgba, supersample):
    """超采样渲染流程"""
    # 1. 创建放大画布
    scaled_font = ImageFont.truetype(font.path, font.size * supersample)
    scaled_image = Image.new("RGBA", (width * ss, height * ss))

    # 2. 放大渲染
    draw = ImageDraw.Draw(scaled_image)
    draw.text((0, 0), char, font=scaled_font, fill=fill_rgba)

    # 3. 缩放回原尺寸
    return scaled_image.resize((width, height), Image.LANCZOS)
```

#### 角度推进计算
```python
def advance_angle(current_angle, char_advance, radius, clockwise):
    """按弧长推进角度"""
    arc_length = char_advance + tracking_px
    angle_increment = arc_length / radius
    return current_angle + (angle_increment if clockwise else -angle_increment)
```

#### 防裁切边距
```python
def calculate_padding(char_image, angle):
    """计算旋转防裁切边距"""
    width, height = char_image.size
    max_dimension = max(width, height)
    diagonal = math.sqrt(2) * max_dimension
    return int(diagonal * 0.6)  # 经验值
```

## 🎨 配置系统

### 标准配置Schema
```json
{
  "canvas": {
    "width": 800, "height": 800,
    "center": [400, 400], "radius": 300
  },
  "phrases": ["TEXT", "PHRASES"],
  "layout": {
    "start_angle_deg": 0,
    "clockwise": true,
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
    "fill_rgba": [0, 0, 0, 255]
  },
  "render": {
    "supersample": 2
  }
}
```

### 预设配置
```python
PRESETS = {
    "pet_tag": {
        "layout": {"start_angle_deg": 0},
        "spacing": {"char_tracking_px": 2.0, "word_spacing_px": 20},
        "font": {"size": 36},
        "style": {"fill_rgba": [255, 182, 193, 255]}  # 粉色
    },
    "brand_badge": {
        "layout": {"start_angle_deg": 180},
        "spacing": {"char_tracking_px": 1.0, "word_spacing_px": 15},
        "font": {"size": 32},
        "style": {"fill_rgba": [255, 215, 0, 255]},  # 金色
        "render": {"supersample": 3}
    }
}
```

## 🚀 使用方式

### 1. 直接Skill调用
```python
from skills.circle_text_skill import CircleTextLayoutSkill

skill = CircleTextLayoutSkill()
config = {
    "canvas": {"width": 600, "height": 600, "center": [300, 300], "radius": 250},
    "phrases": ["LUCKY", "LUCKY", "LUCKY"],
    "layout": {"start_angle_deg": 0, "clockwise": True},
    "font": {"path": "assets/fonts/AaHuanLeBao-2.ttf", "size": 36},
    "style": {"fill_rgba": [255, 182, 193, 255]}
}

result_image = skill.render(base_image=None, config=config)
result_image.save("output/result.png")
```

### 2. 命令行脚本
```bash
# 宠物标签预设
python scripts/run_circle_text_layout.py --preset pet_tag --text "LUCKY"

# 自定义参数
python scripts/run_circle_text_layout.py \
  --phrases "I LOVE YOU" "I LOVE YOU" "I LOVE YOU" \
  --radius 250 --font-size 36 \
  --color-r 255 --color-g 182 --color-b 193

# 基于现有图像
python scripts/run_circle_text_layout.py \
  --base-image output/final.png \
  --phrases "BRAND" "NAME" \
  --out output/with_circle_text.png
```

### 3. 编排器集成
```python
from skills.pet_design_orchestrator import PetDesignOrchestrator

orchestrator = PetDesignOrchestrator()
result = orchestrator.process("input/pet.jpg", {
    "pet_type": "head",
    "text": {"content": "LUCKY"},
    "circle_text": {
        "phrases": ["LUCKY"],
        "preset": "pet_tag"
    }
})
```

## 📊 性能优化

### 字体缓存
```python
class FontCache:
    _cache = {}

    @classmethod
    def get_font(cls, path, size):
        key = (path, size)
        if key not in cls._cache:
            cls._cache[key] = ImageFont.truetype(path, size)
        return cls._cache[key]
```

### 角度预计算
- 预先计算所有字符角度位置
- 批量处理减少重复计算
- 内存友好的图像处理

### 渲染优化
- 超采样分层渲染
- 智能裁剪减少计算量
- Alpha合成优化

## 🧪 测试与验证

### 验收标准
- ✅ 三个短语120°等分分布
- ✅ 每个短语内部单词间距清晰
- ✅ 字符间距自然，有kerning效果
- ✅ 超采样抗锯齿，无明显锯齿
- ✅ 字符旋转防裁切，视觉稳定

### 示例输出
项目包含40+张测试图片：
- `output/test_circle_text.png` - 基础测试
- `output/pet_tag_*.png` - 宠物标签系列
- `output/badge_*.png` - 徽章设计系列
- `output/skill_demo_*.png` - Skill演示系列

## 🔗 集成状态

### 已集成模块
- ✅ **pet-design-orchestrator** - 工作流编排
- ✅ **docs/WORKFLOW.md** - 流程文档
- ✅ **docs/TEXT_FEATURES.md** - 功能概览

### 兼容性
- ✅ **向后兼容** - 不影响现有功能
- ✅ **渐进升级** - 支持现有项目无缝集成
- ✅ **标准化接口** - 统一的所有skill调用方式

## 📈 技术优势

### 质量保证
- **glyph advance**：使用真实字符宽度而非bbox
- **kerning支持**：自动计算字符对间距调整
- **超采样渲染**：最高4x抗锯齿
- **防裁切设计**：智能边距计算

### 架构优势
- **模块化设计**：职责分离，易于维护
- **标准化接口**：统一的skill调用方式
- **配置驱动**：灵活的参数配置系统
- **预设支持**：开箱即用的场景配置

这个圆形文字排版功能现在是项目完整功能的一部分，为宠物设计系统提供了强大的文字装饰能力！🎨✨