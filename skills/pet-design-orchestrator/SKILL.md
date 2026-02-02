---
name: pet-design-orchestrator
description: 编排完整宠物定制图像工作流，协调项目内技能按图像状态与用户指令执行，实现增量更新而非整图重生成。用户进行宠物产品图定制、初次生成或基于指令微调时使用。
---

# 宠物设计编排器（pet-design-orchestrator）

编排完整宠物定制图像工作流，协调现有项目技能，根据**图像状态**与**用户指令**决定执行哪些步骤；始终做**增量更新**，避免不必要的重跑。输出为**当前最新生成的产品图**。

## 可用技能

| 技能目录名 | 用途 |
|-----------|------|
| `image-clarity-enhancement` | 清晰度不足时增强图像 |
| `image-quality-enhancement` | 仅做小幅画质优化时使用 |
| `pet-image-matting` | 宠物抠图 |
| `pet-image-completion` | 抠图缺耳朵/身体时补齐 |
| `template-application` | 应用产品模板 |
| `pet-image-position-adjustment` | 宠物位置/大小 |
| `text-style-adjustment` | 文字内容与样式 |
| `circle-text-layout` | 圆形文字排版与渲染 |

## 默认工作流（初次生成）

仅在**尚未完成**对应步骤时执行；已完成步骤**不重跑**，除非用户明确要求重置。

1. **检查图像清晰度**
   - 若清晰度不足：使用 **image-clarity-enhancement**，输出作为后续输入。
   - 若清晰度足够：直接使用原图进入下一步。

2. **宠物抠图**
   - 使用 **pet-image-matting**，得到透明背景宠物图。

3. **缺失部分补齐（条件执行）**
   - 若抠图结果存在缺失（如耳朵、身体）：使用 **pet-image-completion**。
   - 若无缺失：跳过。

4. **应用产品模板**
   - 使用 **template-application**，合成背景、宠物与默认布局。

5. **应用默认宠物位置**
   - 使用 **pet-image-position-adjustment**，应用默认位置/大小。

6. **应用默认文字样式**
   - 使用 **text-style-adjustment**，应用默认文字内容与样式。

7. **应用圆形文字装饰（可选）**
   - 根据产品类型，使用 **circle-text-layout** 添加圆形文字装饰。

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

建议会话目录结构（如 `sessions/{session_id}/`）：

- `original.jpg` — 原始输入
- `enhanced.jpg` — 清晰度增强后（步骤 1 输出，若无增强则可为原图副本或跳过）
- `extracted.png` — 抠图结果
- `completed.png` — 补齐结果（若有）
- `design.png` — 模板合成后的设计图
- `design_with_text.png` — 应用文字样式后的设计图
- `final.png` — 当前最新产品图（包含圆形文字装饰）

编排器根据**文件是否存在**判断某步是否已完成，从而决定是跳过还是执行。详见 [reference.md](reference.md)。

## 执行逻辑摘要

1. 确定是**初次生成**还是**按指令更新**。
2. **初次生成**：按默认工作流顺序检查每步输出是否存在；若不存在则执行对应技能并写回会话目录。
3. **按指令更新**：根据指令类型只调用上表中所列技能，在现有最新产品图上做增量更新。
4. 将更新后的结果写回会话目录（如 `final.png`）。
5. **返回**：当前最新产品图路径（始终返回）。

## 参考

- 各技能用法与 I/O 见各技能目录下 `SKILL.md`。
- 会话文件约定、指令解析与错误处理见 [reference.md](reference.md)。
