---
name: image-clarity-enhancement
description: 检查图像清晰度，如果图像不符合要求则调用 Real-ESRGAN 模型提升图像清晰度。当处理宠物照片、提升图像清晰度、修复模糊图像或用户提供图像并要求增强清晰度时使用。
---

**实现与脚本**：本技能逻辑与脚本未改动，位于项目 `skills/image-clarity-enhancement/` 与 `scripts/`；此处为 Cursor 约定入口，便于 Agent 发现。

# 图像清晰度提升技能

对上传的宠物原图进行清晰度检查；若低于最小标准则调用 Real-ESRGAN 提升清晰度，并返回增强后图像的路径。

## 输入与输出

| 类型 | 参数 | 必填 | 说明 |
|------|------|------|------|
| 输入 | `image` | 是 | 宠物原图文件路径 |
| 输入 | `min_quality` | 否 | 最小清晰度标准（0–100），默认 70 |
| 输出 | `enhanced_image` | — | 清晰度提升后的图像路径 |

## 工作流程

1. **检查清晰度**：对 `image` 计算清晰度评分（0–100）。评分算法见 [reference.md](../../../skills/image-clarity-enhancement/reference.md)。
2. **判断是否增强**：若评分 **低于** `min_quality`，则调用 Real-ESRGAN 进行增强；否则可直接使用原图路径作为 `enhanced_image`。
3. **调用 Real-ESRGAN**：通过 Replicate 调用 `nightmareai/real-esrgan`，上传/传入图像，获取输出 URL，下载并保存为本地文件。
4. **返回结果**：将保存后的文件路径写入 `enhanced_image` 并返回。

## 实现要点

### 清晰度检查

- 使用 Laplacian 方差衡量模糊程度，再映射到 0–100 分。
- 映射方式与阈值换算见 [reference.md](../../../skills/image-clarity-enhancement/reference.md) 中的「清晰度评分与阈值」。

### Real-ESRGAN 调用

- 需设置环境变量 `REPLICATE_API_TOKEN`。
- 模型：`nightmareai/real-esrgan`；输入为 `image`（URL 或 data URI），可选 `scale`、`face_enhance`。
- 输出为增强图像 URL，需下载并保存到本地，得到最终 `enhanced_image` 路径。

### 路径与错误

- 所有路径使用正斜杠（如 `output/enhanced.png`），避免反斜杠。
- 若 API 调用失败或下载失败，应抛出明确错误并说明原因（如未设置 token、网络错误等）。

## 参考

- Real-ESRGAN 参数与清晰度评分细节见 [reference.md](../../../skills/image-clarity-enhancement/reference.md)。
