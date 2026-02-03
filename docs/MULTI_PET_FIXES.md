# 多宠物合成问题修复记录

## 发现的问题

### 问题1：粘贴位置计算错误
**症状**：粘贴位置出现负坐标，导致图像超出画布或被裁剪

**原因**：
- 使用了缩放前的视觉中心 `cx, cy` 乘以缩放比例
- 应该先缩放图像，再计算缩放后的视觉中心

**修复**：
```python
# 修复前（错误）
cx, cy = compute_visual_center(pet_image)
paste_x = int(layout.anchor[0] * template_width - cx * layout.scale)

# 修复后（正确）
scaled_pet = pet_image.resize((scaled_width, scaled_height), ...)
cx_scaled, cy_scaled = compute_visual_center(scaled_pet)
paste_x = int(anchor_x_px - cx_scaled)
```

### 问题2：抠图结果格式问题
**症状**：抠图结果是RGB模式，没有透明背景

**原因**：
- 某些抠图工具可能返回RGB格式
- 合成时需要RGBA格式才能正确处理透明背景

**修复**：
- 在 `load_extracted_images` 中强制转换为RGBA
- 如果原图是RGB，添加完全不透明的alpha通道

### 问题3：图像尺寸过大
**症状**：缩放后的图像仍然超出模板尺寸

**原因**：
- 固定缩放比例（0.9）不考虑实际图像尺寸
- 864x1184的图像即使缩放0.9倍后（777x1065）仍然远大于800x800的模板

**修复**：
- 添加 `calculate_auto_scale` 方法
- 根据模板尺寸和图像尺寸自动计算合适的缩放比例
- 确保缩放后的图像能够适应模板

### 问题4：视觉中心计算改进
**症状**：对于RGB图像，视觉中心计算可能不准确

**修复**：
- 改进 `compute_visual_center` 函数
- 如果alpha通道完全透明，使用边界框中心作为备选

## 修改的文件

1. **scripts/run_multi_pet_composition.py**
   - 修复粘贴位置计算逻辑
   - 改进图像格式处理
   - 添加位置边界检查

2. **utils/multi_pet_layout.py**
   - 添加 `calculate_auto_scale` 方法
   - 在布局生成时自动调整缩放比例

3. **utils/visual_center.py**
   - 改进视觉中心计算，支持RGB图像

## 测试建议

运行以下命令测试修复效果：
```bash
python scripts/run_multi_pet_task.py
```

检查输出：
- 两只宠物是否都正确显示在模板上
- 宠物位置是否合理（左右布局）
- 图像是否完整显示（不被裁剪）
- 圆形文字是否正确添加
