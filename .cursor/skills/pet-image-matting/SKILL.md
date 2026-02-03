---
name: pet-image-matting
description: 抠出无背景的宠物主体（透明 PNG）。用户提供宠物原图并可选 pet_type（head、half_body、full_body）时使用。输出用于图层合成，不做融合。
---

**实现与脚本**：本技能逻辑与脚本未改动，位于项目 `skills/pet-image-matting/` 与 `scripts/`；此处为 Cursor 约定入口，便于 Agent 发现。

# 宠物图像抠图技能

根据用户提供的宠物原图，抠出**无背景主体**，输出**透明背景 PNG（带 alpha）**，供后续图层合成使用。不负责合背景、不融合。

## 输出要求（重要）

- **格式**：PNG
- **背景**：透明（alpha 通道）
- **主体**：仅宠物头部/半身/全身，边缘干净
- **不做**：不合背景、不融合，后续由 Python 合成脚本叠到模板上

## 输入与输出

| 类型  | 参数                | 必填  | 说明                                            |
| --- | ----------------- | --- | --------------------------------------------- |
| 输入  | `image`           | 是   | 宠物原图文件路径                                      |
| 输入  | `pet_type`        | 否   | 提取范围：`head`、`half_body`、`full_body`；若提供 state 则从 `state.crop_mode` 读取 |
| 输入  | `state`           | 否   | state.json 路径或 dict，包含 `crop_mode` 字段 |
| 输出  | `extracted_image` | —   | 提取后的宠物图像本地路径                                  |

### state.crop_mode（Agent 决策层写入）

```json
{
  "crop_mode": "head" | "half" | "full"
}
```

- `head` → `pet_type=head`
- `half` → `pet_type=half_body`
- `full` → `pet_type=full_body`
- 默认值：`"head"`

**Matting Skill 只读取 state，不做决策。** 决策由 Agent / 编排器负责。


## 工作流程

1. **前置**：输入应为**已去除背景**的图片（由 `run_background_removal.py` 使用 851-labs/background-remover 生成）。
2. **解析输入**：读取 `image` 路径，确认文件存在；若未提供 `pet_type` 则使用 `head`。
3. **构造提示**：根据 `pet_type` 选择抠图提示词，见下方「提示词映射」。
4. **调用模型**：通过 Replicate 调用 `google/nano-banana`，传入图像与提示，获取输出。
5. **保存并返回**：将模型输出下载并保存为本地文件，将该路径作为 `extracted_image` 返回。

## 提示词映射（三种抠图模式）

| `pet_type`  | 模式 | 说明 |
| ----------- | ---- | ---- |
| `head`      | Head Only（仅头部） | 仅保留头部，无脖颈/身体/底部阴影，边缘圆滑干净。 |
| `half_body` | Head + Upper Body（半身） | 头部 + 颈、胸、上躯干，下边界自然收于中躯干。 |
| `full_body` | Full Body（全身） | 头至爪、四肢与尾巴完整可见，不裁切。 |

每种模式使用**一段固定、完整提示词**（见 `scripts/run_pet_image_matting.py` 中 `PROMPTS`），不动态拼接。通用规则：不重绘、不风格化、不失真；边缘 crisp and clean；完全去除背景与地面阴影。详见 [reference.md](../../../skills/pet-image-matting/reference.md)。

## 实现要点

### Replicate 调用

- 需设置环境变量 `REPLICATE_API_TOKEN`。
- 模型：`google/nano-banana`。输入通常包含图像（URL 或 data URI）与文本提示（prompt）；具体入参名以 Replicate 该模型当前 schema 为准。
- 输出为图像 URL，需下载并保存到本地，得到 `extracted_image` 路径。

### 图像上传

- 若模型要求 URL：可先将本地 `image` 转为可访问 URL（如 Replicate 的 file upload 或临时图床），再传入。
- 或使用 Replicate 客户端支持的本地路径/文件上传方式（以当前 API 为准）。

### 路径与错误

- 输出路径使用正斜杠（如 `output/extracted.png`），避免反斜杠。
- 若 API 调用失败、未设置 token 或下载失败，应抛出明确错误并说明原因。

## 参考

- nano-banana 的 Replicate 页面与最新输入/输出 schema：[reference.md](../../../skills/pet-image-matting/reference.md)。
