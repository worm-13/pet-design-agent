# 多宠物合成增强技能参考文档

## 概述

本技能实现了文档《多宠物头部合成自洽性问题 & 工程化解决方案说明》中提出的所有功能，将多宠物合成从"简单叠图"升级为"规则驱动的视觉排版引擎"。

## 核心功能

### 1. 展示级边缘处理

#### Alpha边缘净化
- **函数**: `clean_alpha_edge(image, threshold=10)`
- **功能**: 去除低于阈值的噪点（alpha < 10），防止毛边残留
- **参数**:
  - `image`: RGBA图像
  - `threshold`: Alpha阈值（默认10）

#### 极轻度羽化
- **函数**: `apply_light_feather(image, radius=1.5)`
- **功能**: 只作用于alpha边缘，不模糊主体
- **参数**:
  - `image`: RGBA图像
  - `radius`: 羽化半径（1-2px，默认1.5）

#### 可选内描边
- **函数**: `apply_inner_stroke(image, stroke_width=1, stroke_color=None, opacity=180)`
- **功能**: 半透明内描边，减少浅色背景下的生硬边界
- **参数**:
  - `image`: RGBA图像
  - `stroke_width`: 描边宽度（1px）
  - `stroke_color`: 描边颜色（None则使用图像平均色）
  - `opacity`: 描边透明度（0-255，默认180）

#### 综合处理函数
- **函数**: `process_pet_image_for_display(image, enable_edge_cleaning=True, enable_feather=True, enable_stroke=False)`
- **功能**: 对单只宠物图像进行展示级边缘处理

### 2. 视觉面积归一化

#### 计算视觉面积
- **函数**: `compute_visual_area(image, alpha_threshold=128)`
- **功能**: 计算图像的视觉面积（非透明像素数量）

#### 归一化缩放比例
- **函数**: `normalize_visual_areas(pet_images, base_scales)`
- **功能**: 调整scale使不同宠物的视觉面积接近
- **算法**: `scale_new = scale_base * sqrt(area_max / area_current)`

### 3. 组合视觉中心对齐

#### 计算组合视觉中心
- **函数**: `compute_group_visual_center(pet_images, layouts, template_size)`
- **功能**: 计算所有宠物的组合视觉中心
- **算法**: `C_group = (C1 + C2 + ...) / N`

#### 对齐到模板中心
- **函数**: `align_group_to_template_center(pet_images, layouts, template_size)`
- **功能**: 将组合视觉中心对齐到模板中心
- **效果**: 显著提升"自洽感"和"成组感"

### 4. 圆形模板整体缩放

#### 检测圆形模板
- **函数**: `is_circular_template(template_path)`
- **功能**: 检测模板是否为圆形或强裁切形状
- **检测方法**:
  - 检查alpha通道：中心区域不透明但边缘区域透明
  - 检查文件名：包含"circle"、"circular"、"round"等关键词

#### 应用整体缩放
- **函数**: `apply_circular_template_scaling(layouts, scale_reduction=0.08)`
- **功能**: 对圆形模板应用整体缩放（降低5-10%）
- **参数**:
  - `layouts`: 布局列表
  - `scale_reduction`: 缩放减少比例（默认0.08 = 8%）

## 完整工作流程（10步）

```
1. 单只宠物抠图（已有）
2. 抠图后边缘展示级处理
   ├─ Alpha边缘净化
   ├─ 极轻度羽化（1-2px）
   └─ 可选内描边
3. 计算单只宠物视觉中心
4. 计算单只宠物视觉面积
5. 多宠物视觉面积归一化 scale
6. 计算组合视觉中心
7. 自动布局（左右 / 三角 / 网格）
8. 防遮挡修正
9. 圆形模板整体缩放兜底
10. 合成输出
```

## 使用示例

### 基本使用

```python
from skills.multi_pet_composition_enhancement import MultiPetCompositionEnhancementSkill

skill = MultiPetCompositionEnhancementSkill()
result = skill.enhance_composition(
    pet_images=[pet_a_img, pet_b_img],
    template_path="templates/backgrounds/清新粉蓝-1.png",
    layouts=layouts,
    enable_edge_cleaning=True,
    enable_feather=True,
    enable_stroke=False,
    enable_visual_normalization=True,
    enable_group_alignment=True
)
```

### 在合成脚本中使用

```python
# scripts/run_multi_pet_composition.py
from skills.multi_pet_composition_enhancement import MultiPetCompositionEnhancementSkill

enhancement_skill = MultiPetCompositionEnhancementSkill()
result_image = enhancement_skill.enhance_composition(
    pet_images=pet_images,
    template_path=state.template,
    layouts=layouts,
    enable_edge_cleaning=True,
    enable_feather=True,
    enable_stroke=False,
    enable_visual_normalization=True,
    enable_group_alignment=True
)
```

## 设计原则

1. **不重绘、不风格化、不替换抠图模型**
   - 所有改进发生在抠图之后、合成之前/过程中
   - 禁止使用AI重新生成或美化主体

2. **多宠物 ≠ 多次单宠物**
   - 多宠物合成作为整体设计对象
   - 引入组合视觉中心、视觉尺寸归一化、展示级边缘处理

3. **可复现、可调试**
   - 所有行为必须可复现
   - 不使用随机布局
   - 不使用AI决定位置或比例

## 技术细节

### 视觉面积归一化算法

```python
# 计算每只宠物的视觉面积
visual_areas = [compute_visual_area(img) for img in pet_images]

# 找到最大视觉面积作为参考
max_area = max(visual_areas)

# 归一化scale
for base_scale, area in zip(base_scales, visual_areas):
    area_ratio = sqrt(max_area / area)
    normalized_scale = base_scale * area_ratio
```

### 组合视觉中心计算

```python
# 计算每只宠物在模板坐标系中的视觉中心
visual_centers = []
for pet_image, layout in zip(pet_images, layouts):
    # 缩放图像
    scaled_pet = resize(pet_image, layout.scale)
    
    # 计算视觉中心
    cx_local, cy_local = compute_visual_center(scaled_pet)
    
    # 转换为模板坐标系
    pet_center = anchor_position - (image_center - visual_center)
    visual_centers.append(pet_center)

# 计算组合中心
group_center = mean(visual_centers)
```

## 文件结构

```
skills/multi_pet_composition_enhancement/
├── __init__.py          # 模块导出
├── SKILL.md             # Skill说明文档
├── skill.py             # 主技能类
└── reference.md         # 本文档

utils/
└── multi_pet_enhancement.py  # 工具函数模块
```

## 相关文件

- **工具模块**: `utils/multi_pet_enhancement.py`
- **合成脚本**: `scripts/run_multi_pet_composition.py`
- **布局引擎**: `utils/multi_pet_layout.py`
- **视觉中心**: `utils/visual_center.py`
