---
name: pet-design-orchestrator
description: 编排完整宠物定制图像工作流，协调项目内技能按图像状态与用户指令执行，实现增量更新而非整图重生成。用户进行宠物产品图定制、初次生成或基于指令微调时使用。
---

# 宠物设计编排器（pet-design-orchestrator）

编排完整宠物定制图像工作流，协调现有项目技能，根据**图像数量**、**图像状态**与**用户指令**决定执行哪些步骤；始终做**增量更新**，避免不必要的重跑。输出为**当前最新生成的产品图**。

## 核心路由机制

编排器首先**检测输入的宠物图片数量**，自动选择对应的工程路线：

| 图片数量 | 工程路线 | 使用的脚本/技能 |
|---------|---------|----------------|
| **1张** | **单宠物流程** | `pet-image-matting` → `template-application` → `pet-image-position-adjustment` → `text-style-adjustment` → `circle-text-layout` |
| **2张或以上** | **多宠物流程** | `run_multi_pet_matting` → `run_multi_pet_composition` → `text-style-adjustment` → `circle-text-layout` |

### 路由决策逻辑

1. **输入检测阶段**：
   - 检查用户提供的图片数量（通过 `image_paths` 参数或 `state.pets` 数量）
   - 如果图片数量 ≥ 2，自动切换到多宠物流程
   - 如果图片数量 = 1，使用单宠物流程

2. **状态检查**：
   - 如果会话已存在，检查 `state.json` 中的 `pets` 数组长度
   - 如果 `len(pets) > 1`，使用多宠物流程
   - 如果 `len(pets) == 1`，使用单宠物流程

3. **用户指令优先级**：
   - 如果用户明确提到"两只宠物"、"多只"、"合照"等关键词，强制使用多宠物流程
   - 如果用户明确提到"单只"、"一只"，使用单宠物流程
   - 否则，按图片数量自动决定

## 可用技能

| 技能目录名 | 用途 | 适用场景 |
|-----------|------|---------|
| `image-clarity-enhancement` | 清晰度不足时增强图像 | 单/多宠物通用 |
| `image-quality-enhancement` | 仅做小幅画质优化时使用 | 单/多宠物通用 |
| `pet-image-matting` | 宠物抠图（单只） | 单宠物流程 |
| `run_multi_pet_matting` | 多宠物批量抠图 | 多宠物流程 |
| `pet-image-completion` | 抠图缺耳朵/身体时补齐 | 单/多宠物通用 |
| `template-application` | 应用产品模板（单只） | 单宠物流程 |
| `run_multi_pet_composition` | 多宠物合成 | 多宠物流程 |
| `pet-image-position-adjustment` | 宠物位置/大小（单只） | 单宠物流程 |
| `pet-image-position-adjustment` (多宠物) | 多宠物布局调整 | 多宠物流程（通过 state_manager） |
| `text-style-adjustment` | 文字内容与样式 | 单/多宠物通用 |
| `circle-text-layout` | 圆形文字排版与渲染 | 单/多宠物通用 |

## 默认工作流（初次生成）

编排器首先**检测图片数量**，然后选择对应的工程路线。仅在**尚未完成**对应步骤时执行；已完成步骤**不重跑**，除非用户明确要求重置。

### 单宠物流程（1张图片）

1. **检查图像清晰度**
   - 若清晰度不足：使用 **image-clarity-enhancement**，输出作为后续输入。
   - 若清晰度足够：直接使用原图进入下一步。

2. **宠物抠图**
   - 使用 **pet-image-matting**，得到透明背景宠物图。
   - 输出：`sessions/{session_id}/extracted.png`

3. **缺失部分补齐（条件执行）**
   - 若抠图结果存在缺失（如耳朵、身体）：使用 **pet-image-completion**。
   - 若无缺失：跳过。

4. **应用产品模板**
   - 使用 **template-application**，合成背景、宠物与默认布局。
   - 输出：`sessions/{session_id}/design.png`

5. **应用默认宠物位置**
   - 使用 **pet-image-position-adjustment**，应用默认位置/大小。

6. **应用默认文字样式**
   - 使用 **text-style-adjustment**，应用默认文字内容与样式。
   - 输出：`sessions/{session_id}/design_with_text.png`

7. **应用圆形文字装饰（可选）**
   - 根据产品类型，使用 **circle-text-layout** 添加圆形文字装饰。
   - 输出：`sessions/{session_id}/final.png`

### 多宠物流程（2张或以上图片）

1. **检查图像清晰度**（每只宠物独立检查）
   - 若清晰度不足：使用 **image-clarity-enhancement**，输出作为后续输入。
   - 若清晰度足够：直接使用原图进入下一步。

2. **批量宠物抠图**
   - 使用 **run_multi_pet_matting**，对每只宠物执行：
     - 背景去除 → `sessions/{session_id}/extracted/{pet_id}_no_bg.png`
     - 主体抠图 → `sessions/{session_id}/extracted/{pet_id}_extracted.png`
   - 输出：多张抠图结果

3. **缺失部分补齐（条件执行，每只宠物独立）**
   - 若某只宠物的抠图结果存在缺失：使用 **pet-image-completion**。
   - 若无缺失：跳过。

4. **多宠物自动布局**
   - 使用 **run_multi_pet_composition**，根据模板方向和宠物数量自动计算布局：
     - 2只：横版左右并列 / 竖版上下排列
     - 3只：横版三角构图 / 竖版倒三角构图
     - 4只：2×2网格布局
   - 输出：`sessions/{session_id}/design.png`

5. **应用默认文字样式**
   - 使用 **text-style-adjustment**，在多宠物合成图上添加文字。
   - 输出：`sessions/{session_id}/design_with_text.png`

6. **应用圆形文字装饰（可选）**
   - 使用 **circle-text-layout** 添加圆形文字装饰。
   - 输出：`sessions/{session_id}/final.png`

完成后，**始终返回当前最新生成的产品图路径**。

## 按指令执行（增量更新）

根据用户指令**只执行相关技能**，不重跑无关步骤。

| 指令类型 | 行为 | 使用的技能 |
|---------|------|------------|
| 与**位置或大小**相关 | 仅做位置/大小调整 | **pet-image-position-adjustment** |
| 与**文字内容或样式**相关 | 仅做文字修改 | **text-style-adjustment** |
| 与**圆形文字**相关 | 仅调整圆形文字布局 | **circle-text-layout** |
| 明确表示**抠图不好/重抠** | 重跑抠图及依赖步骤（补齐→模板→位置→文字→圆形文字） | **pet-image-matting**，再按需 **pet-image-completion** → **template-application** → **pet-image-position-adjustment** → **text-style-adjustment** → **circle-text-layout** |
| **小幅优化/画质优化** | 仅做画质增强 | **image-quality-enhancement** |

- 与位置/大小无关的指令：**不**调用 pet-image-position-adjustment。
- 与文字无关的指令：**不**调用 text-style-adjustment。
- 与圆形文字无关的指令：**不**调用 circle-text-layout。
- 未要求重抠或重置时：**不**重跑清晰度增强、补齐或圆形文字步骤。

## 约束

- **不重跑已完成步骤**：除非用户明确要求（如“重新抠图”“从头再来”）。
- **不重跑清晰度增强或补齐**：除非用户明确要求重置或重抠。
- **保留已有结果**：在已有产品图基础上只做增量更新。
- **输出**：始终返回**当前最新生成的产品图**（文件路径或可访问 URL）。

## 会话状态与路径

### 单宠物会话目录结构

`sessions/{session_id}/`：
- `original.jpg` — 原始输入
- `enhanced.jpg` — 清晰度增强后（步骤 1 输出，若无增强则可为原图副本或跳过）
- `extracted.png` — 抠图结果
- `completed.png` — 补齐结果（若有）
- `design.png` — 模板合成后的设计图
- `design_with_text.png` — 应用文字样式后的设计图
- `final.png` — 当前最新产品图（包含圆形文字装饰）
- `state.json` — 状态文件（单宠物格式）

### 多宠物会话目录结构

`sessions/{session_id}/`：
- `original.jpg` — 第一只宠物原始输入（可选，保留参考）
- `enhanced.jpg` — 清晰度增强后（若有）
- `extracted/` — 抠图结果目录
  - `pet_a_no_bg.png` — 第一只宠物去背景结果
  - `pet_a_extracted.png` — 第一只宠物抠图结果
  - `pet_b_no_bg.png` — 第二只宠物去背景结果
  - `pet_b_extracted.png` — 第二只宠物抠图结果
  - `pet_c_extracted.png` — 第三只宠物抠图结果（如有）
  - `pet_d_extracted.png` — 第四只宠物抠图结果（如有）
- `completed/` — 补齐结果目录（可选）
  - `pet_a_completed.png` — 第一只宠物补齐结果（如有）
- `design.png` — 多宠物合成后的设计图
- `design_with_text.png` — 应用文字样式后的设计图
- `final.png` — 当前最新产品图（包含圆形文字装饰）
- `state.json` — 状态文件（多宠物格式，包含 `pets` 数组）

编排器根据**文件是否存在**判断某步是否已完成，从而决定是跳过还是执行。详见 [reference.md](skills/pet-design-orchestrator/reference.md)。

## 执行逻辑摘要

1. **路由决策**：检测输入的宠物图片数量（通过 `image_paths` 参数或 `state.pets` 数量）
   - 如果数量 ≥ 2：选择**多宠物流程**
   - 如果数量 = 1：选择**单宠物流程**
   - 如果用户指令明确提到多宠物关键词：强制使用多宠物流程

2. **确定是初次生成还是按指令更新**：
   - 检查会话目录和状态文件是否存在
   - 如果不存在或为空：初次生成
   - 如果已存在：按指令更新

3. **初次生成**：
   - **单宠物流程**：按单宠物工作流顺序检查每步输出是否存在；若不存在则执行对应技能并写回会话目录。
   - **多宠物流程**：按多宠物工作流顺序执行批量抠图、自动布局、合成等步骤。

4. **按指令更新**：根据指令类型只调用相关技能，在现有最新产品图上做增量更新。
   - 单宠物：使用单宠物相关技能
   - 多宠物：使用多宠物相关技能（如 `run_multi_pet_composition`）

5. 将更新后的结果写回会话目录（如 `final.png`）。

6. **返回**：当前最新产品图路径（始终返回）。

## 参考

- 各技能用法与 I/O 见各技能目录下 `SKILL.md`。
- 会话文件约定、指令解析与错误处理见 [reference.md](skills/pet-design-orchestrator/reference.md)。
