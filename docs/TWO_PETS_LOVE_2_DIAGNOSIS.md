# 两只宠物商业图（two_pets_love_2）问题排查报告

**仅排查、未做任何代码或流程修改。**

---

## 一、现象概述

- 其中一只宠物的**抠图处理明显失败**。
- 与模板合成时**抠头过大、比例与位置完全不正确**。

---

## 二、抠图阶段：其中一只明显失败

### 2.1 运行日志中的关键信息

- **pet_a（柯基）**  
  - 步骤3「再次去除背景」后：**非透明像素仅 0.79%**（低于 1% 阈值）。  
  - 日志：`警告: 第三次去背景后图像几乎完全透明 (0.79%)，使用步骤2的结果作为兜底`  
  - 因此 **pet_a_extracted.png 实际使用的是步骤2的 matting_temp**，没有经过步骤3的边缘清理。

- **pet_b（猫咪）**  
  - 步骤3 正常完成：`步骤3完成: 背景已再次去除，边缘已清理（非透明像素: 24.41%）`  
  - 无兜底，流程正常。

### 2.2 抠图流程回顾

1. **步骤1**：对原图做背景去除 → `*_no_bg.png`
2. **步骤2**：对去背景图做主体抠图（head）→ `*_matting_temp.png`
3. **步骤3**：对 matting_temp **再次**做背景去除（意图是边缘更干净）→ 写入 `*_extracted.png`
4. **步骤4**：对 extracted 做 1:1 正方形（视觉中心对齐）→ 覆盖写回 `*_extracted.png`

### 2.3 问题定位（抠图）

- **直接原因**：对 **pet_a（柯基）** 的步骤2结果再做一次背景去除时，**主体被几乎全部去掉**（只剩 0.79% 非透明），触发「完全透明」兜底，用步骤2结果覆盖了 `pet_a_extracted.png`。
- **含义**：  
  - 要么「步骤3」用的 background-removal 模型对**已抠好的透明底图**过于激进，把主体当背景去掉了；  
  - 要么步骤2对柯基的抠图结果（alpha/边缘）与步骤3的预期输入不匹配，导致误删主体。  
- **结果**：  
  - 柯基这条线**没有经历步骤3的边缘清理**，且若步骤2本身对柯基就抠得不好（含颈/身、或 mask 不脏），这些问题会原样进入后续合成，表现为「**其中一只抠图明显失败**」。

---

## 三、合成阶段：抠头过大、比例与位置完全不正确

### 3.1 抠图输出尺寸差异巨大

- **pet_a_extracted.png**：**1184×1184**（1:1）
- **pet_b_extracted.png**：**599×599**（1:1）

两图边长相差约一倍，说明两路抠图+1:1 裁切后的**画布像素尺寸**差异很大。

### 3.2 布局与 scale 是如何算的

- **create_multi_pet_layout(template_size, pet_count, pet_sizes)** 用的是 **pet_sizes = [(1184,1184), (599,599)]**，即**画布像素尺寸**，不是「头」的实际占比。
- **calculate_auto_scale** 逻辑概要：  
  - 横版模板：`max_width = template_width * 0.4`，`max_height = template_height * 0.6`  
  - `auto_scale = min(max_width/pet_width, max_height/pet_height, layout.scale)`，再 clamp 到 [0.3, 1.0]  
- 因此：  
  - pet_a (1184) → scale 被压到约 **0.3**  
  - pet_b (599) → scale 约 **0.53**  
  即**先按「整张图」的像素尺寸算 scale**，与「头在图中占多大」无关。

### 3.3 视觉面积归一化对比例的影响

- **normalize_visual_areas** 以**第一只（pet_a）的视觉面积**为参考，`factor = sqrt(reference_area / area)`，再乘到各自 base_scale 上。
- 若 pet_a 的**视觉面积很小**（例如画布 1184×1184 但主体只占中间一小块、或透明很多），则：  
  - reference_area 小；  
  - pet_b 的 area 相对大 → factor > 1 → pet_b 的 scale 被**放大**；  
  - 合成时就会显得「**另一只过大**」或两只比例失调。
- 若 pet_a 因兜底保留了大量无效/半透明区域，视觉面积统计也会失真，进一步导致**比例与「头」的观感不对**。

### 3.4 组合中心对齐对位置的影响

- **align_group_to_template_center** 会算组合视觉中心，再把所有 anchor 整体平移，使组合中心对准模板中心。
- 若：  
  - 一侧抠图失败（头小或含颈/身）、一侧正常；  
  - 或两侧 scale 差异大、视觉面积归一化后仍不协调；  
  组合中心会偏向某一侧，对齐后再 clamp 到 [0.1, 0.9]，**位置会显得「完全不正确」**。

### 3.5 「抠头过大」的可能来源

- **抠图失败**：若失败的那只保留了颈/身或多余背景，视觉上会像「头过大」或头身比例错。
- **scale 过大**：视觉面积归一化或 auto_scale 上限（1.0）、防重叠修正等，可能让某一只在模板上的缩放偏大，看起来「头过大」。
- **1:1 裁切方式**：`make_square_1to1` 以非透明像素的 bbox 最大边为正方形边长，若主体在图中占比小，正方形内会有大量留白；但布局仍按**整张图**的像素尺寸算 scale，可能使该侧在模板上占位偏大，与「头」的实际大小不匹配。

---

## 四、问题链条小结

| 环节 | 现象/原因 | 后果 |
|------|-----------|------|
| 步骤3 再次去背景 | 对 pet_a（柯基）结果过度去除，非透明仅 0.79% | 使用步骤2兜底，无边缘清理；若步骤2本身不理想，抠图质量差 |
| 抠图输出尺寸 | pet_a 1184×1184，pet_b 599×599，差异大 | 布局按像素尺寸算 scale，与「头」占比无关，易比例失调 |
| 视觉面积归一化 | 以 pet_a 为参考；若 pet_a 面积异常小/大 | 另一只 scale 被放大或缩小，比例/「头过大」感明显 |
| 组合中心对齐 | 依赖当前 scale 与视觉中心 | 抠图或比例异常时，组合中心偏移，位置不正确 |

整体链条：**抠图阶段一只失败/兜底** → **两图像素与视觉面积差异大** → **布局与归一化基于异常或差异过大的输入** → **合成时抠头过大、比例与位置完全不正确**。

---

## 五、相关代码位置（便于后续修改）

- 抠图流程与步骤3 兜底：`scripts/run_multi_pet_matting.py`（约 157–209 行）
- 步骤3 调用的去背景：`scripts/run_background_removal.py`
- 步骤2 抠头：`scripts/run_pet_image_matting.py`（PROMPTS["head"] 等）
- 1:1 正方形：`scripts/run_multi_pet_matting.py` 中 `make_square_1to1`
- 布局引擎（scale/anchor）：`utils/multi_pet_layout.py`（`calculate_auto_scale`、`generate_layout`）
- 视觉面积归一化：`utils/multi_pet_enhancement.py` 中 `normalize_visual_areas`
- 组合中心对齐：`utils/multi_pet_enhancement.py` 中 `align_group_to_template_center`
- 多宠物合成入口：`scripts/run_multi_pet_composition.py`；增强：`skills/multi_pet_composition_enhancement/skill.py`

---

**文档仅用于排查结论记录，未对项目做任何修改。**
