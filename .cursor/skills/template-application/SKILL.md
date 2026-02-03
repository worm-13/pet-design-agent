---
name: template-application
description: 将抠图后的透明背景宠物图与背景图做图层合成（无 AI）。用户提供 pet_png 与 template/背景图，并可选 position、scale 时使用。
---

**实现与脚本**：本技能逻辑与脚本未改动，位于项目 `skills/template-application/` 与 `scripts/`；此处为 Cursor 约定入口，便于 Agent 发现。

# 模板应用技能（图层合成）

将抠图后的**透明背景宠物图**与**背景/模板图**做纯图层合成，不调用 AI，不融合。输出为叠好图层后的设计图路径。

## 定位

- **不做**：AI 融合、生成式合成。
- **只做**：把宠物图层按位置、缩放叠到背景图上（Pillow 合成）。

## 输入与输出

| 类型 | 参数 | 必填 | 说明 |
|------|------|------|------|
| 输入 | `pet_png` | 是 | 抠图后的宠物图路径（透明 PNG） |
| 输入 | `template_path` 或 `template_style` | 是 | 背景图路径，或模板样式（如 template_A、template_B） |
| 输入 | `position` | 否 | 宠物中心在画布上的相对位置 (x, y)，0~1，默认 (0.5, 0.5) 居中 |
| 输入 | `scale` | 否 | 宠物宽度相对背景宽度的比例，如 0.6；默认由模板或 0.6 |
| 输入 | `out_path` | 否 | 输出路径；未指定则 output/design.png |
| 输出 | `final_design` | — | 合成后的设计图本地路径 |

## 脚本调用

- **主脚本**：`scripts/run_compose_pet_on_template.py`（纯图层合成）
- **封装**：`scripts/run_template_application.py`（支持 template_A/template_B 默认布局）

### 直接合成（推荐）

```bash
python scripts/run_compose_pet_on_template.py <宠物PNG> <背景图路径> --out output/design.png --position 0.5,0.5 --scale 0.6
```

### 按模板样式

```bash
python scripts/run_template_application.py <宠物PNG> template_A --out output/design.png
python scripts/run_template_application.py <宠物PNG> template_B --bg templates/backgrounds/xxx.png --scale 0.55
```

## 工作流程

1. **解析输入**：确认 `pet_png`、背景路径存在；若为 template_style 则解析为默认背景路径与默认 position/scale。
2. **加载图像**：背景转 RGBA，宠物图转 RGBA（保留透明）。
3. **缩放宠物**：按 `scale` 相对背景宽度等比缩放。
4. **计算坐标**：按 `position`（中心点）计算粘贴左上角坐标。
5. **合成**：`bg.paste(pet, (x, y), pet)` 保留透明。
6. **保存并返回**：输出 PNG 路径。

## 与 state 的配合

- 编排器/Agent 可将 `assets.pet_png`、`assets.template`、`layout.scale`、`layout.position` 写入 state；模板应用或位置调整后，用同一脚本按 state 的 layout 重新合成，实现「只改 layout、不重抠、不碰 AI」。

## 参考

- 位置/大小调整（只改 layout 后重跑合成）：[pet-image-position-adjustment](../../../skills/pet-image-position-adjustment/SKILL.md)。
