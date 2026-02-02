# Circle Text Layout - 技术实现参考

## 核心算法

### 三层架构设计

Circle Text Layout 采用三层架构实现高精度圆形文字排版：

```
┌─────────────────┐
│   短语层 (Phrase Layer)    │ ← 等角度分布
├─────────────────┤
│   单词层 (Word Layer)     │ ← 单词间距控制
├─────────────────┤
│   字符层 (Character Layer) │ ← 高精度排版
└─────────────────┘
```

#### 1. 短语层：等角度分布

**计算锚点角度**：
```python
def compute_phrase_anchor_angles(phrase_count, start_angle_deg, clockwise):
    step = 2 * math.pi / phrase_count
    anchors = []
    for i in range(phrase_count):
        angle = start_angle_deg + (i * step if clockwise else -i * step)
        anchors.append(angle % (2 * math.pi))
    return anchors
```

**布局策略**：
- 短语按圆周等分分布
- 支持顺时针/逆时针方向
- 起始角度可自定义

#### 2. 单词层：智能间距控制

**单词级间距**：
```python
# 单词内的字符间距
char_spacing = char_tracking_px

# 单词间的独立间距
word_spacing = word_spacing_px
```

**文本解析**：
```python
def parse_phrases(phrases):
    parsed = []
    for phrase in phrases:
        words = [word.strip() for word in phrase.split() if word.strip()]
        parsed.append(words)
    return parsed
```

#### 3. 字符层：高精度排版

**字体度量**：
```python
# 优先使用glyph advance
advance = font.getlength(char)

# 支持kerning修正
if prev_char:
    pair_advance = font.getlength(prev_char + char)
    kerning = pair_advance - (prev_advance + advance)
    advance += kerning
```

**角度推进**：
```python
# 按弧长推进角度
arc_length = advance + tracking_px
angle_increment = arc_length / radius
current_angle += angle_increment
```

## 渲染引擎

### 超采样抗锯齿

**多级渲染流程**：
```python
def render_char_supersample(char, font, fill_rgba, supersample):
    # 1. 创建放大画布
    scaled_size = font.size * supersample
    scaled_font = ImageFont.truetype(font.path, scaled_size)

    # 2. 在放大画布上渲染
    scaled_image = Image.new("RGBA", (width * ss, height * ss))
    draw = ImageDraw.Draw(scaled_image)
    draw.text((0, 0), char, font=scaled_font, fill=fill_rgba)

    # 3. 缩放回原尺寸
    final_image = scaled_image.resize((width, height), Image.LANCZOS)
    return final_image
```

**超采样倍数选择**：
- `1x`：快速渲染，适用于草稿
- `2x`：标准质量，推荐默认
- `3x`：高质量，适合最终输出
- `4x`：极高质量，渲染较慢

### 旋转与防裁切

**切线旋转**：
```python
def rotate_char_along_tangent(char_image, angle):
    # 沿圆切线方向旋转
    tangent_angle = angle + math.pi / 2  # 切线垂直于半径
    rotated = char_image.rotate(math.degrees(tangent_angle), expand=True)
    return rotated
```

**防裁切边距计算**：
```python
def calculate_padding(char_image, angle):
    # 计算旋转后可能超出边界的最小边距
    width, height = char_image.size
    max_dimension = max(width, height)
    diagonal = math.sqrt(2) * max_dimension
    return int(diagonal * 0.6)  # 经验值
```

### Alpha合成

**高质量图层合成**：
```python
def composite_layers(base_image, text_layers):
    result = base_image.convert("RGBA")
    for layer in text_layers:
        # 使用alpha通道进行高质量合成
        result = Image.alpha_composite(result, layer)
    return result
```

## 配置系统

### 标准配置Schema

```json
{
  "canvas": {
    "width": 800,
    "height": 800,
    "center": [400, 400],
    "radius": 300
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
    "path": "fonts/default.ttf",
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

**宠物标签预设**：
```json
{
  "layout": {"start_angle_deg": 0},
  "spacing": {"char_tracking_px": 2.0, "word_spacing_px": 20},
  "font": {"size": 36},
  "style": {"fill_rgba": [255, 182, 193, 255]}
}
```

**品牌徽章预设**：
```json
{
  "layout": {"start_angle_deg": 180},
  "spacing": {"char_tracking_px": 1.0, "word_spacing_px": 15},
  "font": {"size": 32},
  "render": {"supersample": 3}
}
```

## 性能优化

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
```python
# 预计算所有字符的角度位置
angles = []
current_angle = start_angle
for char in text:
    angles.append(current_angle)
    advance = get_char_advance(char, font)
    arc_length = advance + tracking
    current_angle += arc_length / radius
```

### 内存管理
- 及时释放临时图像对象
- 使用生成器处理大量字符
- 分批处理超大画布

## 兼容性与扩展

### 现有代码兼容
- 保留原有 `circular_text_algorithm.py`
- 支持渐进式升级
- 向后兼容现有脚本

### 扩展接口
```python
class CircleTextLayoutSkill:
    def render(self, base_image, config):
        # 主渲染接口
        pass

    def _render_phrase(self, ...):
        # 短语渲染（可重写）
        pass

    def _render_word(self, ...):
        # 单词渲染（可重写）
        pass

    def _render_char(self, ...):
        # 字符渲染（可重写）
        pass
```

## 验收标准

### 功能验收
- [x] 三个短语120°等分分布
- [x] 每个短语内部单词间距清晰
- [x] 字符间距自然，有kerning效果
- [x] 超采样抗锯齿，无明显锯齿
- [x] 字符旋转防裁切，视觉稳定

### 性能验收
- [x] 2x超采样渲染时间 < 2秒 (800x800画布)
- [x] 字体对象正确缓存复用
- [x] 内存使用稳定，无泄漏

### 兼容性验收
- [x] 与现有宠物工作流无缝集成
- [x] 支持PIL.Image输入输出
- [x] 配置格式标准化

## 故障排除

### 常见问题

**文字被裁切**：
- 检查canvas尺寸是否足够
- 调整radius参数
- 验证center坐标计算

**字符间距不均匀**：
- 检查kerning设置
- 验证font.getlength()是否可用
- 使用不同的tracking值

**渲染性能慢**：
- 降低supersample倍数
- 使用更小的font_size
- 优化字符数量

### 调试技巧

**启用调试模式**：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# 查看角度计算和渲染过程
```

**可视化锚点**：
```python
def debug_anchors(image, anchors, center, radius):
    draw = ImageDraw.Draw(image)
    for angle in anchors:
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        draw.circle((x, y), 5, fill='red')
```

## 版本历史

- **v1.0.0**: 初始实现，支持基础圆形文字排版
- **v1.1.0**: 添加超采样抗锯齿
- **v1.2.0**: 实现三层架构，支持单词级间距
- **v1.3.0**: 添加kerning支持和防裁切设计
- **v2.0.0**: 重构为标准Skill格式，支持配置系统