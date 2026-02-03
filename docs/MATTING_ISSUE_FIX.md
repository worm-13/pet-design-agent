# 抠图问题修复：步骤3导致图像完全透明

## 问题描述

用户报告：`pet_a_extracted.png` 没有抠图，只是纯背景（完全透明）。

## 问题诊断

通过检查脚本发现：
- `pet_a_no_bg.png`（步骤1输出）：44.4% 非透明像素，正常
- `pet_a_extracted.png`（步骤3后）：只有 0.6% 非透明像素，几乎完全透明

## 根本原因

**步骤3再次调用 `run_background_removal` 导致的问题**：

1. 步骤2（nano-banana）已经输出了透明背景的PNG
2. 步骤3再次调用 `background-remover` 处理这个透明背景PNG
3. `background-remover` 把整个图像都处理成了透明背景，导致宠物主体也被去掉了

## 解决方案

**跳过步骤3**，因为：
- nano-banana 已经输出了透明背景PNG
- 不需要再次去背景
- 再次去背景反而会破坏抠图结果

## 修复内容

修改 `scripts/run_multi_pet_matting.py`：

**修复前**：
```python
# 步骤3: 再次去除背景（确保边缘干净）
final_path = run_background_removal(result_path, final_path)
```

**修复后**：
```python
# 步骤3: 检查是否需要再次去除背景
# nano-banana已经输出了透明背景PNG，通常不需要再次去背景
# 如果再次调用background-remover可能会把整个图像都变成透明
# 因此跳过步骤3，直接使用步骤2的结果
final_path = result_path  # 直接使用步骤2的结果
```

## 正确的工作流程

1. **去除背景** → `851-labs/background-remover` ✅
2. **抠出主体** → `google/nano-banana`（输出透明背景PNG）✅
3. **跳过再次去背景** → nano-banana已输出透明背景，无需再次处理 ✅
4. **模板合成** → 本地合成 ✅
5. **添加文字** → 完成设计 ✅

## 注意事项

如果将来需要"确保边缘干净"的功能，应该：
- 使用边缘清理算法（如形态学操作）
- 而不是再次调用 `background-remover`
- 或者只在检测到边缘不干净时才执行
