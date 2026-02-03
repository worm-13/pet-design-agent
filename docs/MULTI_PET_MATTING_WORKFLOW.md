# 多宠物抠图工作流程

## 完整工作流程

多宠物抠图采用三步处理流程，确保最终结果适合本地图层合并：

### 步骤1: 去除背景
- **技能**: `background-removal`
- **脚本**: `scripts/run_background_removal.py`
- **API**: `851-labs/background-remover`
- **输入**: 原始宠物图片
- **输出**: `{pet_id}_no_bg.png` (透明背景PNG)
- **目的**: 去除原图背景，为后续抠图做准备

### 步骤2: 抠出主体
- **技能**: `pet-image-matting`
- **脚本**: `scripts/run_pet_image_matting.py`
- **API**: `google/nano-banana`
- **输入**: `{pet_id}_no_bg.png` (步骤1的输出)
- **输出**: `{pet_id}_matting_temp.png` (临时文件)
- **目的**: 根据 `pet_type` (head/half_body/full_body) 精确抠出宠物主体

### 步骤3: 再次去除背景（确保边缘干净）
- **技能**: `background-removal`
- **脚本**: `scripts/run_background_removal.py`
- **API**: `851-labs/background-remover`
- **输入**: `{pet_id}_matting_temp.png` (步骤2的输出)
- **输出**: `{pet_id}_extracted.png` (最终输出)
- **目的**: 
  - 清理抠图边缘的残留背景
  - 确保最终结果是纯透明背景
  - 方便后续本地图层合并

## 保护机制

为了防止第三次去背景导致图像完全透明，系统添加了保护机制：

1. **非透明像素检查**: 检查第三次去背景后的结果
2. **阈值判断**: 如果非透明像素少于1%，认为图像几乎完全透明
3. **自动兜底**: 如果检测到问题，自动使用步骤2的结果作为最终输出

```python
# 检查结果是否还有内容（防止完全透明）
result_img = Image.open(final_path)
data = np.array(result_img)
non_transparent_ratio = np.sum(data[:, :, 3] > 0) / total_pixels

if non_transparent_ratio < 0.01:  # 如果非透明像素少于1%
    # 使用步骤2的结果作为兜底
    shutil.copy2(matting_result_path, output_path)
```

## 文件命名约定

```
sessions/{session_id}/extracted/
├── pet_a_no_bg.png          # 步骤1输出
├── pet_a_matting_temp.png   # 步骤2输出（临时文件）
├── pet_a_extracted.png      # 步骤3输出（最终结果）
├── pet_b_no_bg.png
├── pet_b_matting_temp.png
└── pet_b_extracted.png
```

## 为什么需要三次处理？

1. **步骤1（去背景）**: 去除原图复杂背景，简化后续处理
2. **步骤2（抠图）**: 精确提取宠物主体，根据需求选择头部/半身/全身
3. **步骤3（再次去背景）**: 
   - 清理步骤2可能残留的边缘背景
   - 确保最终结果是纯透明背景
   - 优化边缘质量，方便本地图层合并

## 错误处理

- **步骤1失败**: 抛出异常，停止处理
- **步骤2失败**: 抛出异常，停止处理
- **步骤3失败或结果异常**: 
  - 记录警告信息
  - 自动使用步骤2的结果作为兜底
  - 继续处理下一只宠物

## 使用示例

```bash
# 执行多宠物抠图
python scripts/run_multi_pet_matting.py multi_pet_session_001

# 输出示例
开始为 2 只宠物进行抠图...
处理宠物 pet_a: input/pet1.jpg
  步骤1: 去除背景 -> sessions/multi_pet_session_001/extracted/pet_a_no_bg.png
  步骤1完成: 背景已去除
  步骤2: 抠出主体 -> sessions/multi_pet_session_001/extracted/pet_a_matting_temp.png
  步骤2完成: 主体已抠出
  步骤3: 再次去除背景（确保边缘干净） -> sessions/multi_pet_session_001/extracted/pet_a_extracted.png
  步骤3完成: 背景已再次去除，边缘已清理（非透明像素: 45.23%）
宠物 pet_a 处理完成
...
所有宠物抠图完成，共 2 张结果
```

## 注意事项

1. **临时文件**: `{pet_id}_matting_temp.png` 是中间文件，可以保留用于调试
2. **最终输出**: `{pet_id}_extracted.png` 是最终用于图层合成的文件
3. **API调用**: 每只宠物需要调用3次Replicate API（步骤1、2、3各一次）
4. **处理时间**: 三步流程会增加处理时间，但能确保更好的边缘质量
