# 抠图RGB转RGBA修复

## 问题发现

检查发现 `pet_a_extracted.png` 是RGB模式而不是RGBA模式，导致：
1. 没有透明背景
2. 合成时会有白色背景

## 根本原因

根据Replicate文档和实际测试，`google/nano-banana` 可能返回RGB格式的图像（白色背景），而不是RGBA格式（透明背景）。

## 解决方案

在 `run_pet_image_matting.py` 中添加后处理：
1. 检查下载后的图像格式
2. 如果是RGB，转换为RGBA
3. 将白色背景（接近255,255,255的像素）设为透明

## 修复代码

```python
# 下载后处理
downloaded_img = Image.open(out_path)
if downloaded_img.mode != 'RGBA':
    if downloaded_img.mode == 'RGB':
        downloaded_img = downloaded_img.convert('RGBA')
        # 将白色背景设为透明
        data = np.array(downloaded_img)
        white_threshold = 240
        mask = np.all(data[:, :, :3] > white_threshold, axis=2)
        data[mask, 3] = 0  # 设置alpha为0（透明）
        downloaded_img = Image.fromarray(data)
    else:
        downloaded_img = downloaded_img.convert('RGBA')
    downloaded_img.save(out_path, "PNG")
```

## 注意事项

- 白色阈值设置为240（RGB值>240的像素视为白色背景）
- 这个方法适用于白色背景的情况
- 如果nano-banana返回的是其他颜色的背景，可能需要调整阈值或使用更智能的背景检测算法
