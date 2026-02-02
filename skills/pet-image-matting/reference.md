# 宠物图像抠图技能 - 参考

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
