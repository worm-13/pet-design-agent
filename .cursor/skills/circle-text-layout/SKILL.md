---
name: circle-text-layout
description: 三层圆形文字排版Skill。支持短语级均分、单词级间距、字符级高精度排版，在圆形布局上实现高质量文字渲染。用户需要圆形文字排版、品牌徽章、宠物标签等场景时使用。
---

**实现与脚本**：本技能逻辑与脚本未改动，位于项目 `skills/circle-text-layout/`、`skills/circle_text_skill/` 与 `scripts/`；此处为 Cursor 约定入口，便于 Agent 发现。

# 圆形文字布局技能（Circle Text Layout）

基于三层架构的高精度圆形文字排版：**短语级均分 + 单词级间距 + 字符级高精度**。支持等角度分布、居中对齐、超采样渲染。调用前可执行 `python scripts/run_circle_text_layout.py --help` 查看完整参数。

## 核心特性（摘要）

- **排版**：短语等角度分布，单词/字符间距可调，基于 glyph advance 与 kerning，超采样抗锯齿（1–4x）。
- **布局**：顺时针/逆时针、起始角度可配；文字圆形可绕圆心旋转（`canvas_rotation_deg`），背景不动。
- **输出**：RGBA 合成，防裁切边距。详见 **skills/circle-text-layout/reference.md**「核心算法」「渲染引擎」「配置系统」。

## 输入与输出

| 类型 | 参数 | 必填 | 说明 |
|------|------|------|------|
| 输入 | `base_image` | 否 | 基础图像（PIL.Image），None 则空白画布 |
| 输入 | `config` | 是 | 含 canvas、phrases、layout、spacing、font、style、render |
| 输出 | `final_image` | — | 渲染完成的圆形文字图像（PIL.Image RGBA） |

完整 Config Schema 与预设见 **skills/circle-text-layout/reference.md**「配置系统」「应用场景示例」。

## 脚本调用

```bash
python scripts/run_circle_text_layout.py --phrases "I LOVE YOU" "I LOVE YOU" "I LOVE YOU" --out output/circle_text.png
python scripts/run_circle_text_layout.py --config config.json --out output/custom.png
python scripts/run_circle_text_layout.py --base-image output/final.png --phrases "PET NAME" --out output/with_text.png
```
完整参数见 `python scripts/run_circle_text_layout.py --help`。

## 工作流程

1. 解析配置（canvas、phrases、layout 等）
2. 创建画布（base_image 或空白 RGBA）
3. 计算布局：短语锚点角度、弧长、居中对齐起始角
4. 渲染文字：字符级排版、超采样、切线旋转、alpha 合成
5. 输出 final_image

## 约束与限制

- phrases 非空；须提供有效字体路径；坐标/角度单位为像素/度数；超采样建议 2x 平衡质量与速度。

## 何时读 reference

- 需要 **Config 完整 Schema、预设、应用场景示例** 时，读 **skills/circle-text-layout/reference.md**「配置系统」「应用场景示例」。
- 需要 **三层架构、字体度量、渲染与防裁切** 时，读「核心算法」「渲染引擎」。
- 需要 **故障排除、调试** 时，读「故障排除」。
