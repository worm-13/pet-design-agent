---
name: pet-image-completion
description: 检查宠物图像是否缺失耳朵或身体部分，若缺失则使用 AI inpainting 补齐。用户提供提取后的宠物图像并可选指定 parts_to_fill（ears、body）时使用。
---

**实现与脚本**：本技能逻辑与脚本未改动，位于项目 `skills/pet-image-completion/` 与 `scripts/`；此处为 Cursor 约定入口，便于 Agent 发现。

# 宠物图像补齐技能

根据用户提供的**提取后的宠物图像**，检查是否缺失耳朵或身体部分；若缺失，则使用 AI inpainting 模型补齐缺失区域，并返回补齐后的图像路径。

## 输入与输出

| 类型 | 参数 | 必填 | 说明 |
|------|------|------|------|
| 输入 | `image` | 是 | 提取后的宠物图像文件路径 |
| 输入 | `parts_to_fill` | 否 | 需补齐的部分：`ears`、`body`；为空或未提供则补齐所有检测到的缺失部分 |
| 输出 | `filled_image` | — | 补齐后的图像本地路径 |

## 工作流程

1. **解析输入**：读取 `image` 路径，确认文件存在；若提供 `parts_to_fill` 则仅处理所列部分，否则补齐所有缺失部分。
2. **检测缺失**：判断图像是否缺失耳朵或身体（见下方「缺失检测」）。若用户已指定 `parts_to_fill`，可跳过自动检测，直接针对指定区域补齐。
3. **生成掩码**：根据缺失区域（耳朵多为图像上方/边缘，身体多为下方或裁切边）生成 inpainting 用 mask（缺失区域为白，其余为黑）。
4. **调用 inpainting**：使用 Replicate 上的 inpainting 模型（如 `stability-ai/stable-diffusion-inpainting`），传入原图、mask 与宠物相关提示词，得到补齐结果。
5. **保存并返回**：将输出下载并保存为本地文件，将该路径作为 `filled_image` 返回。

## 缺失检测

- **耳朵**：图像顶部或左右上角被裁切、透明或明显留白，或用户指定 `parts_to_fill` 含 `ears`。
- **身体**：图像底部或下方被裁切、透明或明显留白，或用户指定 `parts_to_fill` 含 `body`。
- 若未提供 `parts_to_fill`：可结合边缘/透明区域检测与简单启发式（如裁剪框位置）判断需补齐区域；不确定时默认同时考虑耳朵与身体区域。

## 提示词与模型

| 补齐部分 | 建议提示词（英文） |
|----------|---------------------|
| `ears` | pet with complete ears, natural ear shape, same fur and style |
| `body` | pet body continuation, same fur and color, natural posture |
| 全部 | complete pet with natural ears and body, consistent fur and style |

- 模型：Replicate 上使用 `stability-ai/stable-diffusion-inpainting`（或当前推荐的 inpainting 模型，见 [reference.md](../../../skills/pet-image-completion/reference.md)）。
- 需设置环境变量 `REPLICATE_API_TOKEN`。
- 输入：`image`（原图 URL 或 data URI）、`mask`（缺失区域为白）、`prompt`（上表或类似描述）；具体入参以该模型当前 schema 为准。
- 输出为图像 URL，需下载并保存到本地，得到 `filled_image` 路径。

## 掩码与图像上传

- **掩码**：与输入图像同尺寸，单通道；需补齐的区域为白色（255），其余为黑色（0）。可根据 `parts_to_fill` 与检测结果绘制矩形或简单多边形区域。
- **上传**：若模型要求 URL，先将本地 `image` 与 mask 转为可公网访问的 URL（如 Replicate file upload 或 data URI），再传入。

## 路径与错误

- 输出路径使用正斜杠（如 `output/filled.png`），避免反斜杠。
- 若 API 调用失败、未设置 token、下载失败或无法检测到可补齐区域，应抛出明确错误并说明原因。

## 参考

- Inpainting 模型列表与 API schema 见 [reference.md](../../../skills/pet-image-completion/reference.md)。
