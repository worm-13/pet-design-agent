---
name: multi-pet-composition-enhancement
description: 多宠物合成增强技能，实现展示级边缘处理、视觉面积归一化、组合视觉中心对齐等功能，将多宠物合成从"简单叠图"升级为"规则驱动的视觉排版引擎"
---

**实现与脚本**：本技能逻辑与脚本未改动，位于项目 `skills/multi_pet_composition_enhancement/`、`utils/` 与 `scripts/`；此处为 Cursor 约定入口，便于 Agent 发现。

# 多宠物合成增强技能（Multi-Pet Composition Enhancement）

将多宠物合成从"简单叠图"升级为"规则驱动的视觉排版引擎"，解决多宠物头部合成时的视觉自洽性问题。

## 核心问题

在多宠物（2-4只）头部合成时，存在以下视觉问题：
1. 两个头部位置看起来不协调、不成组
2. 两个头部比例观感不一致（即使scale相同）
3. 抠图边缘在纯色/浅色背景下显得生硬、不平滑
4. 圆形模板会放大以上所有问题

## 设计原则

1. **不重绘、不风格化、不替换抠图模型**
   - 所有改进发生在抠图之后、合成之前/过程中
   - 禁止使用AI重新生成或美化主体

2. **多宠物 ≠ 多次单宠物**
   - 多宠物合成作为整体设计对象
   - 引入组合视觉中心、视觉尺寸归一化、展示级边缘处理

## 功能模块

### 1. 展示级边缘处理

#### Alpha边缘净化
- 去除低于阈值的噪点（alpha < 10）
- 防止毛边残留

#### 极轻度羽化（1-2px）
- 只作用于alpha边缘
- 不模糊主体
- 目的：让边缘"呼吸"，不是糊

#### 可选内描边
- 半透明，1px
- 颜色 ≈ 主体毛发平均色
- 用于减少浅色背景下的生硬边界

### 2. 视觉面积归一化

**问题**：几何尺寸 ≠ 视觉尺寸。毛发多、轮廓复杂的主体，在视觉上更"重"。

**解决方案**：
- 统计每只宠物的视觉面积（alpha > 阈值的像素数量）
- 调整scale，使视觉面积接近：
  ```
  scale_b *= sqrt(area_a / area_b)
  ```

### 3. 组合视觉中心对齐

**问题**：两个头部看起来像两个独立贴纸，没有形成整体构图。

**解决方案**：
- 计算每只宠物的视觉中心
- 计算组合中心：`C_group = (C1 + C2) / 2`
- 将组合中心对齐模板中心
- 各宠物在组合坐标系内进行相对偏移

### 4. 圆形模板整体缩放

**约束**：
- 当模板为圆形或强裁切形状时
- 整体组合scale自动降低5-10%
- 即使看起来还能放大，也不要放

## 完整工作流程

```
1. 单只宠物抠图（已有）
2. 抠图后边缘展示级处理
3. 计算单只宠物视觉中心
4. 计算单只宠物视觉面积
5. 多宠物视觉面积归一化 scale
6. 计算组合视觉中心
7. 自动布局（左右 / 三角 / 网格）
8. 防遮挡修正
9. 圆形模板整体缩放兜底
10. 合成输出
```

## 输入输出

| 类型 | 参数 | 说明 |
|------|------|------|
| 输入 | `pet_images` | 宠物抠图结果列表（RGBA） |
| 输入 | `template_path` | 模板路径 |
| 输入 | `layouts` | 布局配置列表 |
| 输入 | `enable_edge_cleaning` | 是否启用边缘净化（默认True） |
| 输入 | `enable_feather` | 是否启用轻度羽化（默认True） |
| 输入 | `enable_stroke` | 是否启用内描边（默认False） |
| 输入 | `enable_visual_normalization` | 是否启用视觉面积归一化（默认True） |
| 输入 | `enable_group_alignment` | 是否启用组合中心对齐（默认True） |
| 输出 | `result_image` | 增强后的合成图像 |

## 实现边界

- ❌ 不引入随机布局
- ❌ 不使用AI决定位置或比例
- ❌ 不在合成阶段重绘主体
- ✅ 所有行为必须可复现、可调试

## 使用示例

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

## 参考

- 工具模块：`utils/multi_pet_enhancement.py`
- 合成脚本：`scripts/run_multi_pet_composition.py`
