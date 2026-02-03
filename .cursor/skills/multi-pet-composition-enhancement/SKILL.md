---
name: multi-pet-composition-enhancement
description: 多宠物合成增强技能，实现展示级边缘处理、视觉面积归一化、组合视觉中心对齐等功能，将多宠物合成从"简单叠图"升级为"规则驱动的视觉排版引擎"
---

**实现与脚本**：本技能逻辑与脚本未改动，位于项目 `skills/multi_pet_composition_enhancement/`、`utils/` 与 `scripts/`；此处为 Cursor 约定入口，便于 Agent 发现。

# 多宠物合成增强技能（Multi-Pet Composition Enhancement）

将多宠物合成从"简单叠图"升级为"规则驱动的视觉排版引擎"，解决多宠物头部合成时的视觉自洽性问题。

## 核心问题（摘要）

在多宠物（2-4只）头部合成时：位置不协调、比例观感不一致、抠图边缘生硬、圆形模板会放大上述问题。本技能在**抠图之后、合成之中**做展示级边缘处理、视觉面积归一化、组合视觉中心对齐，不重绘、不风格化、不替换抠图模型。

## 设计原则

1. **不重绘、不风格化、不替换抠图模型**：所有改进发生在抠图之后、合成之前/过程中；禁止使用 AI 重新生成或美化主体。
2. **多宠物 ≠ 多次单宠物**：多宠物合成作为整体设计对象，引入组合视觉中心、视觉尺寸归一化、展示级边缘处理。

## 功能模块（摘要）

- **展示级边缘处理**：Alpha 边缘净化、极轻度羽化（1-2px）、可选内描边。
- **视觉面积归一化**：按 alpha 像素面积调整 scale，使视觉面积接近。
- **组合视觉中心对齐**：组合中心对齐模板中心，各宠物相对偏移。
- **圆形模板整体缩放**：圆形/强裁切模板时整体 scale 自动降低 5-10%。

完整工作流程、输入输出表、使用示例见 **skills/multi-pet-composition-enhancement/reference.md**。

## 实现边界

- ❌ 不引入随机布局；❌ 不使用 AI 决定位置或比例；❌ 不在合成阶段重绘主体。
- ✅ 所有行为必须可复现、可调试。

## 何时读 reference

- 需要 **功能模块细节、完整工作流程、输入输出参数、Python 调用示例** 时，读 **skills/multi-pet-composition-enhancement/reference.md**。
- 脚本入口：`scripts/run_multi_pet_composition.py`；工具模块：`utils/multi_pet_enhancement.py`。
