---
name: pet-design-orchestrator
description: 编排完整宠物定制图像工作流，协调项目内技能按图像状态与用户指令执行，实现增量更新而非整图重生成。用户进行宠物产品图定制、初次生成或基于指令微调时使用。
---

**实现与脚本**：本技能逻辑与脚本未改动，位于项目 `skills/pet-design-orchestrator/` 与 `scripts/`；此处为 Cursor 约定入口，便于 Agent 发现。

# 宠物设计编排器（pet-design-orchestrator）

编排完整宠物定制图像工作流，协调现有项目技能，根据**图像数量**、**图像状态**与**用户指令**决定执行哪些步骤；始终做**增量更新**，避免不必要的重跑。**每次订单（原图 + 客户文字需求）对应一个会话**，单宠与多宠均输出到 `sessions/<session_id>/`。

## 核心路由机制

编排器首先**检测输入的宠物图片数量**，自动选择对应的工程路线；**单宠与多宠均走 session**：

| 图片数量 | 工程路线 | 使用的脚本 | 输出目录 |
|---------|---------|-----------|----------|
| **1张** | **单宠物流程** | `run_multi_pet_with_circle_text`（1 张图） | `sessions/<session_id>/` |
| **2张或以上** | **多宠物流程** | `run_multi_pet_with_circle_text`（多张图） | `sessions/<session_id>/` |

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

统一使用 **run_multi_pet_with_circle_text**（1 张图），输出到 `sessions/{session_id}/`：

1. **初始化会话**：`state_manager.add_pet(session_id, image_path)`，1 只宠物记为 `pet_a`
2. **批量抠图**：`run_multi_pet_matting` → `sessions/{session_id}/extracted/pet_a_extracted.png`
3. **合成**：`run_multi_pet_composition` → `sessions/{session_id}/design.png`
4. **圆形文字（可选）**：`add_circle_text_to_image` → `sessions/{session_id}/design_final.png`
5. **state.json** 记录：pets、template、text_content、text_style

### 多宠物流程（2张或以上图片）

统一使用 **run_multi_pet_with_circle_text**（多张图），输出到 `sessions/{session_id}/`：

1. **初始化会话**：`state_manager.add_pet` 为每张图添加宠物（pet_a, pet_b, ...）
2. **批量抠图**：`run_multi_pet_matting` → `sessions/{session_id}/extracted/{pet_id}_extracted.png`
3. **自动布局与合成**：`run_multi_pet_composition` → `sessions/{session_id}/design.png`
4. **圆形文字（可选）**：`add_circle_text_to_image` → `sessions/{session_id}/design_final.png`
5. **state.json** 记录：pets、template、text_content、text_style

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

### 会话目录结构（单宠与多宠统一）

`sessions/{session_id}/`：
- `extracted/` — 抠图结果
  - 单宠：`pet_a_extracted.png`
  - 多宠：`pet_a_extracted.png`, `pet_b_extracted.png`, ...
- `design.png` — 合成底图（无文字）
- `design_final.png` — 含圆形文字的成品图
- `state.json` — 状态（pets、template、text_content、text_style）

每次订单（原图 + 客户文字需求）对应一个 session_id，便于追踪与增量更新。

编排器根据**文件是否存在**判断某步是否已完成，从而决定是跳过还是执行。详见 [reference.md](../../../skills/pet-design-orchestrator/reference.md)。

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
- 会话文件约定、指令解析与错误处理见 [reference.md](../../../skills/pet-design-orchestrator/reference.md)。
