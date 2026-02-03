---
name: circle-text-layout
description: 三层圆形文字排版Skill。支持短语级均分、单词级间距、字符级高精度排版，在圆形布局上实现高质量文字渲染。用户需要圆形文字排版、品牌徽章、宠物标签等场景时使用。
---

# 圆形文字布局技能（Circle Text Layout）

基于三层架构的高精度圆形文字排版Skill：**短语级均分 + 单词级间距 + 字符级高精度排版**。支持等角度分布、自动居中对齐、高质量超采样渲染。

## 核心特性

### 高精度排版
- ✅ **短语级均分**：多个短语按圆周等角度分布
- ✅ **单词级间距**：单词内字符间距 + 单词间独立间距
- ✅ **字符级高精度**：基于glyph advance的真实字符宽度，支持kerning修正
- ✅ **超采样渲染**：1-4x可调超采样，消除旋转锯齿

### 智能布局
- ✅ **等角度分布**：短语按圆周等分，智能处理单/多单词输入
- ✅ **居中对齐**：每个短语在锚点处自动居中对齐
- ✅ **灵活配置**：支持顺时针/逆时针、自定义起始角度
- ✅ **文字图层旋转**：支持文字圆形绕圆心旋转任意角度，背景图片保持不动

### 视觉优化
- ✅ **切线旋转**：字符沿圆切线方向自然排列
- ✅ **高质量合成**：RGBA alpha合成，无锯齿边缘
- ✅ **防裁切设计**：自动计算边距防止旋转后被裁剪

## 输入与输出

| 类型 | 参数 | 必填 | 说明 |
|------|------|------|------|
| 输入 | `base_image` | 否 | 基础图像（PIL.Image），如果为None则创建空白画布 |
| 输入 | `config` | 是 | 配置字典，包含canvas、phrases、layout等设置 |
| 输出 | `final_image` | — | 渲染完成的圆形文字图像（PIL.Image RGBA） |

### Config Schema

```json
{
  "canvas": {
    "width": 800,
    "height": 800,
    "center": [400, 400],
    "radius": 300,
    "canvas_rotation_deg": 0
  },
  "phrases": ["I LOVE YOU", "I LOVE YOU", "I LOVE YOU"],
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
    "fill_rgba": [255, 182, 193, 255]
  },
  "render": {
    "supersample": 2
  }
}
```

## 脚本调用

```bash
# 基本使用
python scripts/run_circle_text_layout.py --phrases "I LOVE YOU" "I LOVE YOU" "I LOVE YOU" --out output/circle_text.png

# 自定义配置
python scripts/run_circle_text_layout.py --config config.json --out output/custom.png

# 基于现有图像
python scripts/run_circle_text_layout.py --base-image output/final.png --phrases "PET NAME" --out output/with_text.png
```

## 工作流程

1. **解析配置**：读取canvas、phrases、layout等参数
2. **创建画布**：使用base_image或创建空白RGBA画布
3. **计算布局**：
   - 计算短语锚点角度（等角度分布）
   - 测量每个短语的弧长（考虑字符间距和单词间距）
   - 计算居中对齐的起始角度
4. **渲染文字**：
   - 为每个短语创建独立的文字图层
   - 按字符级高精度排版，考虑kerning
   - 使用超采样渲染消除锯齿
   - 沿圆切线方向旋转字符
5. **合成输出**：将所有文字图层alpha合成到底图上

## 应用场景

### 宠物产品定制
```python
config = {
    "canvas": {"width": 600, "height": 600, "center": [300, 300], "radius": 250},
    "phrases": ["LUCKY", "LUCKY", "LUCKY"],
    "layout": {"start_angle_deg": 0, "clockwise": True},
    "font": {"size": 36},
    "style": {"fill_rgba": [255, 182, 193, 255]}
}
```

### 品牌徽章设计
```python
config = {
    "canvas": {"width": 800, "height": 800, "center": [400, 400], "radius": 320},
    "phrases": ["BRAND", "NAME", "LOGO"],
    "layout": {"start_angle_deg": 180, "clockwise": True},
    "spacing": {"char_tracking_px": 1.0, "word_spacing_px": 15}
}
```

### 节日问候卡片
```python
config = {
    "canvas": {"width": 700, "height": 700, "center": [350, 350], "radius": 280},
    "phrases": ["HAPPY", "HOLIDAYS"],
    "layout": {"start_angle_deg": 270},
    "style": {"fill_rgba": [255, 0, 0, 255]}
}
```

## 技术实现

### 三层架构
1. **短语层**：等角度分布的锚点系统
2. **单词层**：单词级间距控制
3. **字符层**：基于glyph advance的高精度排版

### 字体度量
- 优先使用`font.getlength()`获取真实advance
- 自动计算字符对间的kerning修正
- 禁止使用`textbbox`作为推进依据

### 渲染优化
- 超采样抗锯齿（默认2x，可调1-4x）
- 单字符独立RGBA图层
- 旋转防裁切边距计算
- BICUBIC旋转插值

## 约束与限制

- **输入验证**：phrases不能为空列表，至少包含一个非空短语
- **字体要求**：必须提供有效的字体文件路径
- **坐标系统**：所有坐标使用像素单位，角度使用度数
- **性能考虑**：超采样倍数影响渲染质量和速度，建议2x平衡

## 参考

- 技术实现细节见 [reference.md](skills/circle-text-layout/reference.md)
- 预设配置和示例见项目中的 `examples_circle_text_skill.py`
- 现有实现参考 `skills/circle_text_skill/` 目录