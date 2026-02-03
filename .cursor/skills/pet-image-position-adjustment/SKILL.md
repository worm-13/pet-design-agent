---
name: pet-image-position-adjustment
description: 调整宠物在最终设计中的位置与大小。仅修改 layout（scale、position）后重新执行图层合成，不重抠、不用 AI。用户提供 pet_png、template 与 position/scale 时使用。
---

**实现与脚本**：本技能逻辑与脚本未改动，位于项目 `skills/pet-image-position-adjustment/` 与 `scripts/`；此处为 Cursor 约定入口，便于 Agent 发现。

# 位置/大小调整技能

在已有抠图与背景的前提下，**只修改 layout（scale、position）**，然后**重新执行图层合成**。不重抠、不增强、不调用 AI。

## 定位

- **不做**：重新抠图、画质增强、AI 融合。
- **只做**：用新的 position/scale 再跑一次合成脚本，得到新设计图。

## 输入与输出

| 类型 | 参数 | 必填 | 说明 |
|------|------|------|------|
| 输入 | `pet_png` | 是 | 抠图后的宠物图路径（透明 PNG） |
| 输入 | `template_path` | 是 | 背景/模板图路径 |
| 输入 | `position` | 否 | 宠物中心相对位置 (x, y)，0~1，如 (0.5, 0.62) 表示居中偏下；默认 (0.5, 0.5) |
| 输入 | `scale` | 否 | 宠物宽度相对背景宽度的比例，如 0.55 表示小一点；默认 0.6 |
| 输入 | `out_path` | 否 | 输出路径 |
| 输出 | `adjusted_image` | — | 按新 layout 合成后的设计图路径 |

## 脚本调用

与图层合成共用同一实现，调用合成脚本并传入新的 position/scale：

```bash
python scripts/run_compose_pet_on_template.py <宠物PNG> <背景图路径> --out output/design.png --position 0.5,0.62 --scale 0.55
```

或使用封装脚本：

```bash
python scripts/run_pet_image_position_adjustment.py <宠物PNG> <背景图路径> --position 0.5,0.62 --scale 0.55 --out output/design.png
```

## 工作流程

1. **解析输入**：确认 `pet_png`、`template_path` 存在；未提供的 position/scale 使用 state 或默认值。
2. **调用合成**：调用 `compose_pet_on_template(pet_png, template_path, out_path, position=..., scale=...)`。
3. **更新 state（可选）**：若由编排器使用，可更新 state 的 `layout.position`、`layout.scale` 与 `output`。

## 与 state 的配合

- 用户说「往下一点、小一点」时：只改 state 的 `layout.position`（如 [0.5, 0.62]）、`layout.scale`（如 0.55），然后重新跑合成脚本。
- 抠图只做一次，后续全是「重摆图层」。

## 参考

- 图层合成实现：[template-application](skills/template-application/SKILL.md)。
