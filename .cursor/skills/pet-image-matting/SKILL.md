---
name: pet-image-matting
description: 抠出无背景的宠物主体（透明 PNG）。用户提供宠物原图并可选 pet_type（head、half_body、full_body）时使用。输出用于图层合成，不做融合。
---

**实现与脚本**：本技能逻辑与脚本未改动，位于项目 `skills/pet-image-matting/` 与 `scripts/`；此处为 Cursor 约定入口，便于 Agent 发现。

# 宠物图像抠图技能

根据用户提供的宠物原图，抠出**无背景主体**，输出**透明背景 PNG（带 alpha）**，供后续图层合成使用。不负责合背景、不融合。

## 输出要求（重要）

- **格式**：PNG；**背景**：透明（alpha 通道）；**主体**：仅宠物头部/半身/全身，边缘干净。
- **不做**：不合背景、不融合，后续由 Python 合成脚本叠到模板上。

## 输入与输出

| 类型  | 参数                | 必填  | 说明                                            |
| --- | ----------------- | --- | --------------------------------------------- |
| 输入  | `image`           | 是   | 宠物原图文件路径                                      |
| 输入  | `pet_type`        | 否   | 提取范围：`head`、`half_body`、`full_body`；若提供 state 则从 `state.crop_mode` 读取 |
| 输入  | `state`           | 否   | state.json 路径或 dict，包含 `crop_mode` 字段 |
| 输出  | `extracted_image` | —   | 提取后的宠物图像本地路径                                  |

state.crop_mode 与 pet_type 映射见 **skills/pet-image-matting/reference.md**「state.crop_mode」。

## 工作流程

1. **前置**：输入应为**已去除背景**的图片（由 `run_background_removal.py` 使用 851-labs/background-remover 生成）。
2. **解析输入**：读取 `image` 路径，确认文件存在；若未提供 `pet_type` 则使用 `head`。
3. **构造提示**：根据 `pet_type` 选择抠图提示词。
4. **调用模型**：通过 Replicate 调用 `google/nano-banana`，传入图像与提示，获取输出。
5. **保存并返回**：将模型输出下载并保存为本地文件，将该路径作为 `extracted_image` 返回。

提示词映射（三种抠图模式）、Replicate 调用与图像上传、路径与错误处理见 **skills/pet-image-matting/reference.md**「提示词映射」「实现要点」「Replicate 模型」。

## 何时读 reference

- 需要 **state.crop_mode 与 pet_type 对应、三种模式说明** 时，读 **skills/pet-image-matting/reference.md**「state.crop_mode」「提示词映射」。
- 需要 **Replicate 调用、上传方式、路径与错误** 时，读「实现要点」「Replicate 模型」「环境」「输出」。
