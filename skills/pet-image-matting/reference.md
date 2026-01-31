# 宠物图像抠图技能 - 参考

## Replicate 模型

- **模型**：`google/nano-banana`
- **API 文档**：<https://replicate.com/google/nano-banana/api>
- **Schema**：<https://replicate.com/google/nano-banana/api/schema>

- **image_input**（数组，必填）：输入图像，支持多图。Replicate 接受 file 对象或 URL。
- **prompt**（字符串，必填）：编辑描述。

## 环境

- 需设置环境变量 `REPLICATE_API_TOKEN`。
- Python 示例依赖：`replicate>=0.25.0`。

## 提示词与 pet_type

### head（仅头部）— 完整英文提示词

抠图步骤中 `pet_type=head` 时使用以下提示词（已用于脚本与编排）：

```
Remove everything except the pet's head—ensure no neck, no body, and no bottom shadow. The pet's head should be completely isolated, with absolutely no part of the neck or body visible in the image. The neck must be fully removed, leaving only the head. If the pet is wearing clothing, remove the parts of the body that are covered by clothing. Preserve all facial features, texture, coloration, and expression exactly; highest priority: do not alter the pet in any way. Ensure the edges of the head are crisp and clear—avoid over-feathering, halos, or soft transitions. If the pet has clearly defined fur layers around the chin and neck, remove any parts of the body or fur that don't follow the natural fur layering. If there are no clear fur layers, the bottom of the pet's head should align with the pet's chin, following the natural shape of the chin area without jagged lines. The fur should be well-defined at the chin area, ensuring a clean separation with no blurring or fading. The pet's head should remain fully within the top portion of the image, with the bottom part dedicated to the background. Completely remove any shadow beneath the head, ensuring a flat, seamless base. Set the background color to a light shade that seamlessly blends with the pet's fur tone, ensuring a natural and smooth transition.
```

### 其他 pet_type

| pet_type   | 用途     | 建议提示（可微调） |
|-----------|----------|--------------------|
| half_body | 头部+半身| Extract the pet from head to half body (upper half), remove background, keep subject clear. |
| full_body | 全身     | Extract the full body of the pet, remove background, keep subject clear. |

若模型对“抠图/去背景”理解不佳，可改为强调 “isolate the subject” 或 “crop to show only…”。

## 输出

- 模型通常返回图像 URL；需用 HTTP 请求下载为字节流，再写入本地文件。
- 建议输出文件名包含 `pet_type` 或时间戳，避免覆盖（如 `extracted_head.png`、`extracted_20250129.png`）。
