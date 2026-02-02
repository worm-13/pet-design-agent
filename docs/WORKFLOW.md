# 工作流程

项目采用**模块化Skill架构**，通过宠物设计编排器统一协调各项功能，支持增量更新和灵活定制。

## 🎯 核心架构

### Skill系统
项目基于标准化的Skill模块构建，每个功能独立封装：

| Skill | 功能描述 | 位置 |
|-------|---------|------|
| `background-removal` | 背景去除 | [skills/background-removal/](../skills/background-removal/SKILL.md) |
| `pet-image-matting` | 宠物抠图 | [skills/pet-image-matting/](../skills/pet-image-matting/SKILL.md) |
| `pet-image-completion` | 缺失部分补齐 | [skills/pet-image-completion/](../skills/pet-image-completion/SKILL.md) |
| `template-application` | 模板合成 | [skills/template-application/](../skills/template-application/SKILL.md) |
| `pet-image-position-adjustment` | 位置大小调整 | [skills/pet-image-position-adjustment/](../skills/pet-image-position-adjustment/SKILL.md) |
| `text-style-adjustment` | 普通文字 | [skills/text-style-adjustment/](../skills/text-style-adjustment/SKILL.md) |
| `circle-text-layout` | 圆形文字排版 | [skills/circle-text-layout/](../skills/circle-text-layout/SKILL.md) |
| `pet-design-orchestrator` | 工作流编排 | [skills/pet-design-orchestrator/](../skills/pet-design-orchestrator/SKILL.md) |

### 编排器优势
- ✅ **增量更新**：只执行必要的步骤，避免重复处理
- ✅ **状态管理**：自动判断步骤完成状态
- ✅ **灵活定制**：支持按需调整任意环节
- ✅ **统一接口**：标准化输入输出格式

## 🚀 使用方式

### 智能编排（推荐）
使用宠物设计编排器，自动处理完整工作流：

```bash
# 基础生成（自动执行完整流程）
python scripts/run_agent.py input/原图.jpg

# 增量更新（只修改指定部分）
python scripts/run_agent.py --adjust-text "新文字" sessions/xxx/
python scripts/run_agent.py --adjust-position 0.5,0.6 sessions/xxx/
```

### 手动编排
通过pet-design-orchestrator手动控制：

```python
from skills.pet_design_orchestrator import PetDesignOrchestrator

orchestrator = PetDesignOrchestrator()
result = orchestrator.process("input/pet.jpg", {
    "template": "templates/backgrounds/clear_blue.png",
    "pet_type": "head",
    "text": {"content": "LUCKY", "position": "bottom-center"},
    "circle_text": {"phrases": ["LUCKY"], "preset": "pet_tag"}
})
```

### 独立Skill调用
直接使用单个Skill进行特定处理：

```bash
# 圆形文字排版
python scripts/run_circle_text_layout.py --preset pet_tag --text "PET NAME"

# 普通文字添加
python scripts/run_text_style_adjustment.py output/design.png -c "文字内容"

# 宠物抠图
python scripts/run_pet_image_matting.py input/pet.jpg --pet-type head
```

## 📋 标准工作流

### 完整流程（初次生成）
1. **图像预处理** → 清晰度增强（可选）
2. **背景去除** → 使用AI模型去除背景
3. **宠物抠图** → 提取头部/半身/全身
4. **缺失补齐** → 修复耳朵/身体缺失（条件执行）
5. **模板合成** → 应用产品背景模板
6. **位置调整** → 优化宠物位置和大小
7. **文字添加** → 添加普通文字（可选）
8. **圆形文字** → 添加圆形装饰文字（可选）

### 增量更新流程
根据用户指令只执行相关步骤，支持：
- 文字内容/样式修改 → 只调用文字Skill
- 位置/大小调整 → 只调用位置调整Skill
- 抠图重做 → 重跑抠图及后续步骤

## ⚙️ 技术栈

### AI模型
- **背景去除**: `851-labs/background-remover:a029dff38972b5fda4ec5d75d7d1cd25aeff621d2cf4946a41055d7db66b80bc`
- **宠物抠图**: `google/nano-banana`（最新版）
- **图像增强**: `nightmareai/real-esrgan` (Real-ESRGAN)
- **图像修复**: `stability-ai/stable-diffusion-inpainting`

### 环境要求
- **Python**: 3.8+
- **依赖**: PIL, requests, replicate
- **API密钥**: `REPLICATE_API_TOKEN` (必需)

## 📚 相关文档

- [文字功能详解](TEXT_FEATURES.md) - 文字相关功能说明
- [Skill开发规范](../README.md) - Skill开发标准
- [API使用指南](../README.md) - 完整API文档

## 🎨 使用场景

- **宠物产品定制**：项圈、衣服、玩具等产品图生成
- **品牌徽章设计**：圆形文字排版的品牌标识
- **节日问候卡片**：个性化的节日祝福设计
- **创意图像处理**：各种圆形文字装饰效果
