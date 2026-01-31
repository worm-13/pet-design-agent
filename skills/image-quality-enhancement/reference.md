# Real-ESRGAN API 参考

## Replicate 模型

- **模型标识**：`nightmareai/real-esrgan`
- **推荐版本**：`f121d640`（以 Replicate 官网当前版本为准）
- **文档**：https://replicate.com/nightmareai/real-esrgan/api

## 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `image` | string | 是 | 输入图像，支持 URL 或 data URI |
| `scale` | integer | 否 | 放大倍数，默认 4，最大 10 |
| `face_enhance` | boolean | 否 | 是否启用人脸增强（GFPGAN），默认 false |

## 输出

- 返回增强后图像的 URL，需自行下载保存为本地文件。

## 清晰度阈值参考

- Laplacian 方差 < 约 100–120 常被视为较模糊，需结合场景调整。
- 用户指定的「最低清晰度标准」（如 70）即与此方差比较；低于则触发增强。
