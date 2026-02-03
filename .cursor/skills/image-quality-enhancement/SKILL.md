---
name: image-quality-enhancement
description: Checks image sharpness and enhances image quality using Real-ESRGAN. Use when the user needs to improve image clarity, upscale low-resolution or blurry images, or when image sharpness is below a given threshold.
---

**实现与脚本**：本技能逻辑与脚本未改动，位于项目 `skills/image-quality-enhancement/` 与 `scripts/`；此处为 Cursor 约定入口，便于 Agent 发现。

# Image Quality Enhancement（图像清晰度提升）

检查图像清晰度，若不足则通过 Real-ESRGAN 提升图像质量并输出增强后的图像。

## 输入与输出

| 类型 | 说明 |
|------|------|
| **输入** | 图像文件路径（或 URL）；可选：最低清晰度标准（默认建议 70） |
| **输出** | 清晰度增强后的图像文件（或可访问的 URL） |

## 工作流程

1. **评估清晰度**：用 Laplacian 方差计算图像清晰度分数（越高越清晰）。
2. **判断是否需增强**：若清晰度分数 **低于** 用户给定的最低标准（如 70），则进行增强。
3. **调用 Real-ESRGAN**：通过 Replicate API 调用 `nightmareai/real-esrgan` 对图像做超分/增强。
4. **保存或返回结果**：将增强后的图像保存到本地或返回其 URL。

## 清晰度检测

使用 OpenCV 的 Laplacian 方差作为清晰度指标：

```python
import cv2

def get_sharpness(image_path):
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"无法读取图像: {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()
```

- 分数越高越清晰，越低越模糊。
- 阈值由用户指定（例如 70）；低于该阈值则触发 Real-ESRGAN 增强。

## 调用 Real-ESRGAN（Replicate）

- **模型**：`nightmareai/real-esrgan`（可用版本如 `f121d640` 等，以 Replicate 当前为准）。
- **环境**：需设置环境变量 `REPLICATE_API_TOKEN`。
- **输入**：
  - `image`（必填）：输入图像，可为 URL 或 base64/data URL。
  - `scale`（可选）：放大倍数，默认 4，最大 10。
  - `face_enhance`（可选）：是否启用人脸增强，默认 False。
- **输出**：返回增强后图像的 URL（或文件流），需下载或保存为本地文件。

使用 Replicate Python 客户端示例：

```python
import replicate

output = replicate.run(
    "nightmareai/real-esrgan:f121d640bd286e1fdc67f9799164c1d5be36ff74576ee11c803ae5b665dd46aa",
    input={"image": image_url_or_data, "scale": 4}
)
# output 为结果图像 URL，可用 requests 或 replicate 客户端下载并保存
```

若输入为本地文件，需先上传到可公网访问的 URL，或使用 Replicate 支持的 data URL/base64 等形式（以当前 API 文档为准）。

## 执行清单

执行时按顺序完成：

- [ ] 读取用户提供的图像路径（或 URL）及可选的最低清晰度标准（如 70）。
- [ ] 计算当前图像的清晰度分数（Laplacian 方差）。
- [ ] 若分数 **低于** 最低标准，则调用 Real-ESRGAN 进行增强；否则可告知用户当前已达标并询问是否仍要增强。
- [ ] 将 Real-ESRGAN 的输出保存为本地文件或返回可访问的 URL。
- [ ] 向用户说明：原始清晰度分数、是否进行了增强、输出文件路径或 URL。

## 注意事项

- 清晰度阈值（如 70）需根据实际图像类型和需求调整；Laplacian 方差受分辨率与场景影响。
- 调用 Replicate 前请确认已配置 `REPLICATE_API_TOKEN`。
- 若图像来自本地路径，Replicate 通常需要可公网访问的 URL，需先通过图床或 data URL 等方式提供输入。

## 更多参考

- Real-ESRGAN 参数与 API 详情见 [reference.md](../../../skills/image-quality-enhancement/reference.md)。
