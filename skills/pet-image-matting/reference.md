# 宠物图像抠图技能 - 参考

## state.crop_mode（Agent 决策层写入）

```json
{
  "crop_mode": "head" | "half" | "full"
}
```

- `head` → `pet_type=head`
- `half` → `pet_type=half_body`
- `full` → `pet_type=full_body`
- 默认值：`"head"`

Matting Skill 只读取 state，不做决策。决策由 Agent / 编排器负责。

## 提示词映射（三种抠图模式）

| `pet_type`  | 模式 | 说明 |
| ----------- | ---- | ---- |
| `head`      | Head Only（仅头部） | 仅保留头部，无脖颈/身体/底部阴影，边缘圆滑干净。 |
| `half_body` | Head + Upper Body（半身） | 头部 + 颈、胸、上躯干，下边界自然收于中躯干。 |
| `full_body` | Full Body（全身） | 头至爪、四肢与尾巴完整可见，不裁切。 |

每种模式使用**一段固定、完整提示词**（见 `scripts/run_pet_image_matting.py` 中 `PROMPTS`），不动态拼接。通用规则：不重绘、不风格化、不失真；边缘 crisp and clean；完全去除背景与地面阴影。

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

## Replicate 模型

- **模型**：`google/nano-banana-pro`
- **API 文档**：<https://replicate.com/google/nano-banana-pro/api>
- **Schema**：<https://replicate.com/google/nano-banana-pro/api/schema>

调用前请查阅当前 schema，确认输入参数名（如 `image` / `image_input`、`prompt` 等）及是否支持本地文件或需先上传为 URL。

## 环境

- 需设置环境变量 `REPLICATE_API_TOKEN`。
- Python 示例依赖：`replicate>=0.25.0`。

## 提示词与 pet_type

| pet_type   | 用途     | 建议提示（可微调） |
|-----------|----------|--------------------|
| head      | 仅头部   | Extract only the pet's head, remove background, keep subject clear. |
| half_body | 头部+半身| Extract the pet from head to half body (upper half), remove background, keep subject clear. |
| full_body | 全身     | Extract the full body of the pet, remove background, keep subject clear. |

若模型对“抠图/去背景”理解不佳，可改为强调 “isolate the subject” 或 “crop to show only…”。

## 输出

- 模型通常返回图像 URL；需用 HTTP 请求下载为字节流，再写入本地文件。
- 建议输出文件名包含 `pet_type` 或时间戳，避免覆盖（如 `extracted_head.png`、`extracted_20250129.png`）。
