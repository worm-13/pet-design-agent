# 宠物设计编排器参考文档

## 路由机制：根据图片数量自动选择工程路线

编排器的核心特性是**根据输入的宠物图片数量自动选择对应的工程路线**。

### 路由决策流程

```
输入图片 → 检测数量 → 路由决策 → 执行对应流程
```

1. **输入检测**：
   - 检查 `image_paths` 参数（列表长度）
   - 检查 `state.pets` 数组长度（如果会话已存在）
   - 检查用户指令中的多宠物关键词

2. **路由规则**：
   ```
   if 图片数量 >= 2 OR 用户指令包含多宠物关键词:
       选择 → 多宠物流程
   elif 图片数量 == 1:
       选择 → 单宠物流程
   else:
       错误：需要至少1张图片
   ```

3. **执行对应流程**：
   - 单宠物流程：使用单宠物相关技能和脚本
   - 多宠物流程：使用多宠物相关技能和脚本

### 技能与编排器对应关系

#### 单宠物流程

| 编排器步骤/指令 | 技能目录/脚本 | 说明 |
|----------------|--------------|------|
| 步骤 1：清晰度不足时增强 | `image-clarity-enhancement` | 检查清晰度，不足则用 Real-ESRGAN 等增强 |
| 小幅画质优化（按指令） | `image-quality-enhancement` | 仅做画质优化时单独调用 |
| 步骤 2：宠物抠图 | `pet-image-matting` | 输出透明背景宠物图 |
| 步骤 3：缺失补齐 | `pet-image-completion` | 抠图缺耳朵/身体时补齐 |
| 步骤 4：模板应用 | `template-application` | 合成背景、宠物与文字 |
| 步骤 5：默认位置 | `pet-image-position-adjustment` | 应用默认宠物位置/大小 |
| 步骤 6：默认文字 | `text-style-adjustment` | 应用默认文字内容与样式 |
| 按指令：位置/大小 | `pet-image-position-adjustment` | 仅做位置或大小调整 |
| 按指令：文字 | `text-style-adjustment` | 仅做文字内容或样式调整 |
| 按指令：抠图不好 | `pet-image-matting` + 依赖步骤 | 重跑抠图→补齐→模板→位置→文字 |
| 按指令：小幅优化 | `image-quality-enhancement` | 仅做画质增强 |

#### 多宠物流程

| 编排器步骤/指令 | 技能目录/脚本 | 说明 |
|----------------|--------------|------|
| 步骤 1：清晰度不足时增强 | `image-clarity-enhancement` | 每只宠物独立检查清晰度 |
| 步骤 2：批量宠物抠图 | `run_multi_pet_matting` | 批量处理多只宠物抠图 |
| 步骤 3：缺失补齐 | `pet-image-completion` | 每只宠物独立检查缺失 |
| 步骤 4：多宠物合成 | `run_multi_pet_composition` | 自动布局并合成多只宠物 |
| 步骤 5：默认文字 | `text-style-adjustment` | 在多宠物合成图上添加文字 |
| 按指令：位置/大小调整 | `state_manager.update_pet_layout` + `run_multi_pet_composition` | 调整单只宠物布局后重新合成 |
| 按指令：文字 | `text-style-adjustment` | 仅做文字内容或样式调整 |
| 按指令：抠图不好 | `run_multi_pet_matting` + 依赖步骤 | 重跑批量抠图→补齐→合成→文字 |
| 按指令：小幅优化 | `image-quality-enhancement` | 仅做画质增强 |

## 会话目录与文件约定

### 单宠物会话目录

| 文件名 | 说明 | 生成步骤 |
|--------|------|----------|
| `original.jpg` | 用户原始输入图像 | 用户上传 |
| `enhanced.jpg` | 清晰度增强后的图像 | 步骤 1（仅当清晰度不足时生成） |
| `extracted.png` | 抠图后的宠物图（透明背景） | 步骤 2 |
| `completed.png` | 补齐后的宠物图 | 步骤 3（仅当有缺失时生成） |
| `design.png` | 应用模板后的设计图 | 步骤 4 |
| `design_with_text.png` | 应用文字后的设计图 | 步骤 6 |
| `final.png` | 当前最新产品图 | 步骤 7 或按指令增量更新 |
| `state.json` | 状态文件（单宠物格式） | 状态管理 |

### 多宠物会话目录

| 文件/目录名 | 说明 | 生成步骤 |
|------------|------|----------|
| `original.jpg` | 第一只宠物原始输入（可选） | 用户上传 |
| `enhanced.jpg` | 清晰度增强后的图像（可选） | 步骤 1（仅当清晰度不足时生成） |
| `extracted/` | 抠图结果目录 | 步骤 2 |
| `extracted/pet_a_no_bg.png` | 第一只宠物去背景结果 | 步骤 2.1 |
| `extracted/pet_a_extracted.png` | 第一只宠物抠图结果 | 步骤 2.2 |
| `extracted/pet_b_extracted.png` | 第二只宠物抠图结果 | 步骤 2.2 |
| `extracted/pet_c_extracted.png` | 第三只宠物抠图结果（如有） | 步骤 2.2 |
| `extracted/pet_d_extracted.png` | 第四只宠物抠图结果（如有） | 步骤 2.2 |
| `completed/` | 补齐结果目录（可选） | 步骤 3 |
| `completed/pet_a_completed.png` | 第一只宠物补齐结果（如有） | 步骤 3 |
| `design.png` | 多宠物合成后的设计图 | 步骤 4 |
| `design_with_text.png` | 应用文字后的设计图 | 步骤 5 |
| `final.png` | 当前最新产品图 | 步骤 6 或按指令增量更新 |
| `state.json` | 状态文件（多宠物格式，包含 `pets` 数组） | 状态管理 |

- 步骤 1 若清晰度足够，可不生成 `enhanced.jpg`，后续步骤直接使用 `original.jpg`。
- 编排器根据**文件是否存在**判断该步是否已完成，从而决定跳过或执行。
- 多宠物流程中，每只宠物的抠图结果存储在 `extracted/` 目录下，文件名格式为 `{pet_id}_extracted.png`。

## 指令解析与行为

### 位置或大小相关

#### 单宠物流程
- 关键词示例：向上/向下移动、居中、左上/右下角、放大/缩小、位置、大小等。
- 行为：**仅**使用 `pet-image-position-adjustment`，在最新产品图上做增量更新。
- 不重跑：抠图、补齐、清晰度增强、模板应用。

#### 多宠物流程
- 关键词示例：左边那只大一点、右边往中间靠、上面那只缩小等。
- 行为：
  1. 使用 `state_manager.update_pet_layout` 更新指定宠物的布局参数
  2. 调用 `run_multi_pet_composition` 重新合成
- 不重跑：抠图、补齐、清晰度增强（除非用户明确要求）。

### 文字内容或样式相关

- 关键词示例：改文字、改字体、字号、颜色、文案等。
- 行为：**仅**使用 `text-style-adjustment`，在最新产品图上做增量更新。
- 不重跑：抠图、补齐、清晰度增强、模板应用、位置调整。

### 抠图不好 / 重抠

#### 单宠物流程
- 用户明确表示抠图不好、要重新抠图、边缘不好等。
- 行为：重跑 **pet-image-matting**，并重跑依赖步骤：**pet-image-completion**（若仍有缺失）→ **template-application** → **pet-image-position-adjustment** → **text-style-adjustment**。
- 不重跑：清晰度增强（除非用户明确要求重置）。

#### 多宠物流程
- 用户明确表示抠图不好、要重新抠图、边缘不好等。
- 行为：
  1. 重跑 **run_multi_pet_matting**（批量重抠所有宠物）
  2. 重跑依赖步骤：**pet-image-completion**（若仍有缺失）→ **run_multi_pet_composition** → **text-style-adjustment**
- 不重跑：清晰度增强（除非用户明确要求重置）。
- 如果用户指定某只宠物（如"左边那只重抠"），可以只重抠指定宠物，然后重新合成。

### 小幅优化 / 画质优化

- 用户仅要求画质优化、轻微增强、不改变构图等。
- 行为：**仅**使用 `image-quality-enhancement`。
- 不重跑：抠图、补齐、模板、位置、文字。

### 重置 / 从头开始

- 用户明确要求“从头开始”“全部重做”“重置”等。
- 行为：可按用户意图清除会话中部分或全部中间结果，再按默认工作流重新执行；清晰度与补齐仅在此时可被重跑。

## 约束摘要

- **不重跑已完成步骤**：除非用户明确要求重做或重置。
- **不重跑清晰度增强或补齐**：除非用户明确要求重置或重抠。
- **保留已有结果**：在已有产品图上只做增量更新。
- **输出**：始终返回**当前最新生成的产品图**路径（或 URL）。

## 错误与边界情况

| 情况 | 建议处理 |
|------|----------|
| 无原始图 | 提示用户先提供原始宠物图像 |
| 某技能调用失败 | 记录错误，若可能则返回上一步可用结果并提示 |
| 会话目录不存在 | 自动创建会话目录 |
| 用户指令含糊 | 优先解释为最小化更新（如仅位置或仅文字），必要时向用户确认 |

## 路由决策实现示例

### Python 伪代码

```python
def route_by_pet_count(image_paths: List[str], state: MultiPetState, instruction: str) -> str:
    """
    根据图片数量路由到对应的工程路线
    
    Returns:
        "single_pet" 或 "multi_pet"
    """
    # 1. 检查图片数量
    pet_count = len(image_paths) if image_paths else len(state.pets)
    
    # 2. 检查用户指令中的多宠物关键词
    multi_pet_keywords = ["两只", "两个", "多只", "合照", "一起", "并排"]
    has_multi_keyword = any(keyword in instruction for keyword in multi_pet_keywords)
    
    # 3. 路由决策
    if pet_count >= 2 or has_multi_keyword:
        return "multi_pet"
    elif pet_count == 1:
        return "single_pet"
    else:
        raise ValueError("需要至少1张宠物图片")
```

### 实际调用示例

```python
# 单宠物流程
orchestrator.process(
    image_paths=["input/pet1.jpg"],
    instruction="生成宠物项圈设计",
    template="templates/backgrounds/清新粉蓝-1.png"
)
# → 自动选择单宠物流程

# 多宠物流程
orchestrator.process(
    image_paths=["input/pet1.jpg", "input/pet2.jpg"],
    instruction="把两只宠物合照放一起",
    template="templates/backgrounds/清新粉蓝-1.png"
)
# → 自动选择多宠物流程
```

## 扩展说明

- 各技能的具体输入/输出与调用方式见 `skills/<技能目录名>/SKILL.md`。
- 若需新增步骤或新指令类型，应在 SKILL.md 的「默认工作流」「按指令执行」与本文档的「指令解析与行为」中同步更新。
- 路由机制确保单宠物和多宠物流程的平滑切换，无需手动指定流程类型。
