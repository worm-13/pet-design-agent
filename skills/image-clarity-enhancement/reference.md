# 图像清晰度提升技能 - 参考

## Real-ESRGAN（Replicate）

- **模型**：`nightmareai/real-esrgan`
- **文档**：https://replicate.com/nightmareai/real-esrgan/api

### 输入

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `image` | string | 是 | 输入图像，支持 URL 或 data URI |
| `scale` | integer | 否 | 放大倍数，默认 4，最大 10 |
| `face_enhance` | boolean | 否 | 是否启用人脸增强（GFPGAN），默认 false |

### 输出

- 返回增强后图像的 URL，需下载并保存为本地文件后得到 `enhanced_image` 路径。

### 调用前提

- 环境变量 `REPLICATE_API_TOKEN` 已设置。

---

## 清晰度评分与阈值

### Laplacian 方差

- 用 OpenCV 对灰度图做 Laplacian，再计算方差，数值越大越清晰、越小越模糊。
- 典型范围：模糊图约几十，清晰图可达数百以上。

### 映射到 0–100

- 将 Laplacian 方差映射到 0–100，例如：
  - `score = min(100, variance / 3)`，或
  - 设 `v_low=0`、`v_high=300`，则 `score = min(100, max(0, (variance - v_low) / (v_high - v_low) * 100))`
- 用户传入的 `min_quality`（默认 70）即与此 `score` 比较：**若 score < min_quality，则调用 Real-ESRGAN 增强**。

### 实现示例（Python）

```python
import cv2

def clarity_score(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"无法读取图像: {image_path}")
    laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()
    # 映射到 0-100：方差 0->0, 300+->100
    score = min(100, max(0, laplacian_var / 3.0))
    return score
```

可根据实际图片分布调整除数（如 3.0）或 `v_high`，使 70 分左右对应「可接受清晰度」的观感。
