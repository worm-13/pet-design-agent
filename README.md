# 宠物图像定制项目

这是一个基于 Cursor Skills 的宠物图像定制工作流项目，通过编排多个技能实现从原始宠物照片到最终定制设计图的完整流程。

## 项目结构

```
test pet/
├── input/                     # 原图目录：放宠物原始照片
│   └── README.md
├── templates/                 # 模板资源目录：背景图等
│   ├── backgrounds/          # 背景图（模板合成时 --bg 使用）
│   └── README.md
├── output/                    # 输出目录：抠图、设计图等生成结果
├── skills/                    # 所有技能目录
│   ├── image-clarity-enhancement/
│   ├── image-quality-enhancement/
│   ├── pet-design-orchestrator/
│   ├── pet-image-completion/
│   ├── pet-image-matting/
│   ├── pet-image-position-adjustment/
│   ├── template-application/
│   └── text-style-adjustment/
├── scripts/                   # 可执行脚本
│   ├── state_manager.py              # 状态管理（读写 state.json）
│   ├── run_orchestrator.py          # 编排器（协调完整工作流）
│   ├── replicate_utils.py
│   ├── run_pet_image_matting.py      # 抠图（AI，输出透明 PNG）
│   ├── run_compose_pet_on_template.py # 图层合成：宠物 PNG + 背景（无 AI）
│   ├── run_template_application.py   # 模板应用（调用 compose）
│   ├── run_design_synthesis_ai.py   # [可选] AI 融合合成（nano-banana）
│   ├── run_image_quality_enhancement.py
│   ├── run_pet_image_completion.py
│   ├── run_pet_image_position_adjustment.py
│   └── run_text_style_adjustment.py
├── sessions/                 # 会话状态目录（自动创建）
│   └── {session_id}/        # 每个会话一个目录
│       ├── state.json        # 状态元数据（步骤、时间、参数等）
│       ├── original.jpg      # 原始输入
│       ├── enhanced.jpg      # 增强后（可选）
│       ├── extracted.png     # 抠图结果
│       ├── completed.png     # 补齐结果（可选）
│       ├── design.png        # 设计图
│       └── final.png         # 最终图
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

### 文件夹说明

| 文件夹 | 用途 |
|--------|------|
| **input/** | 放**原图**（宠物原始照片），抠图/增强等步骤的输入 |
| **templates/backgrounds/** | 放**模板背景图**，合成设计图时通过 `--bg` 指定 |
| **output/** | 脚本生成的抠图、设计图等输出文件 |

## 技能说明

### 核心编排器
- **pet-design-orchestrator**: 主编排器，协调所有子技能按顺序执行完整工作流

### 图像处理技能
- **image-clarity-enhancement**: 检查图像清晰度，低于标准时调用 Real-ESRGAN 提升
- **image-quality-enhancement**: 图像质量增强，使用 Real-ESRGAN 提升图像质量

### 宠物处理技能
- **pet-image-matting**: 使用 nano-banana 模型提取宠物头部、半身或全身
- **pet-image-completion**: 检查并补齐缺失的耳朵或身体部分

### 设计合成技能
- **template-application**: 图层合成（宠物透明 PNG + 背景图），无 AI，可控制 position/scale
- **pet-image-position-adjustment**: 只改 layout（position、scale）后重新跑合成脚本，不重抠、不用 AI
- **text-style-adjustment**: 调整设计图中的文字样式（添加/编辑/删除，字体、大小、颜色、位置）

## 工作流程

1. **去除背景** → 851-labs/background-remover
2. **抠出主体** → google/nano-banana（全身/半身/头部）
3. **再次去除背景** → 确保边缘干净
4. **模板合成** → 与背景模板合成
5. **文字样式** → 按需添加

详见 [docs/WORKFLOW.md](docs/WORKFLOW.md)

## 使用方法

### 环境配置

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 设置 API Token（二选一）：
   - **推荐**：在项目根目录创建 `.env` 文件，写入一行：`REPLICATE_API_TOKEN=你的token`（可复制 `.env.example` 为 `.env` 再修改）。`.env` 已加入 `.gitignore`，不会提交到 Git。
   - 或设置环境变量：`export REPLICATE_API_TOKEN=your_token_here`（Windows: `set REPLICATE_API_TOKEN=your_token_here`）。

### 使用编排器

**方式1：命令行脚本（推荐）**

使用 `run_orchestrator.py` 执行完整工作流，自动管理状态：

```bash
# 初次生成（默认工作流）
python scripts/run_orchestrator.py session_001 input/宠物图.jpg

# 按指令增量更新
python scripts/run_orchestrator.py session_001 input/宠物图.jpg --instruction "把宠物移到左上角"
python scripts/run_orchestrator.py session_001 input/宠物图.jpg --instruction "文字改成小白"

# 重置所有步骤（从头开始）
python scripts/run_orchestrator.py session_001 input/宠物图.jpg --reset
```

**方式2：通过 Cursor Agent 技能**

通过 `pet-design-orchestrator` 技能使用完整工作流：

- 输入：`session_id`（必填）、`instruction`（可选）
- 输出：`latest_image`（最新生成的图像路径）

会话状态存储在 `sessions/{session_id}/` 目录下，包含：
- `state.json`：记录每个步骤的完成时间、输入/输出路径、参数等元数据
- 各步骤的中间结果文件（original.jpg, extracted.png, design.png 等）

### 命令行可执行脚本

在项目根目录下执行（需先 `pip install -r requirements.txt` 并设置 `REPLICATE_API_TOKEN`）：

| 脚本 | 说明 | 示例 |
|------|------|------|
| `run_pet_image_matting.py` | 宠物抠图（nano-banana，输出透明 PNG） | `python scripts/run_pet_image_matting.py 图片.png --pet-type head --out output/head.png` |
| `run_pet_image_matting_rembg.py` | 宠物抠图（rembg 本地，无 API，输出透明 PNG） | `python scripts/run_pet_image_matting_rembg.py 图片.png --out output/head_rembg.png`（首次会下载模型，约 1～3 分钟） |
| `run_compose_pet_on_template.py` | **图层合成**：宠物 PNG + 背景（无 AI） | `python scripts/run_compose_pet_on_template.py output/head.png templates/backgrounds/xxx.png --position 0.5,0.5 --scale 0.6 --out output/design.png` |
| `run_template_application.py` | 模板应用（调用 compose，支持 template_A/B） | `python scripts/run_template_application.py output/head.png template_A --out output/design.png` |
| `run_pet_image_position_adjustment.py` | 位置/大小调整（改 layout 后重跑合成） | `python scripts/run_pet_image_position_adjustment.py output/head.png templates/backgrounds/xxx.png --position 0.5,0.62 --scale 0.55 --out output/design.png` |
| `run_design_synthesis_ai.py` | [可选] AI 融合合成（nano-banana） | `python scripts/run_design_synthesis_ai.py output/head.png templates/backgrounds/xxx.png --out output/design.png` |
| `run_image_quality_enhancement.py` | 图像清晰度/质量增强（调用 AI） | `python scripts/run_image_quality_enhancement.py 图片.png --min-quality 70 --out output/enhanced.png` |
| `run_pet_image_completion.py` | 宠物图像补齐（调用 AI） | `python scripts/run_pet_image_completion.py 图片.png --parts all --out output/filled.png` |
| `run_text_style_adjustment.py` | 文字样式调整（添加/编辑/删除） | `python scripts/run_text_style_adjustment.py output/design.png "宠物名" --out output/design.png` |
| `run_orchestrator.py` | **编排器（完整工作流）** | `python scripts/run_orchestrator.py session_001 input/图.jpg [--instruction 指令]` |

- 调用 Replicate 的脚本会先上传本地图片（若传入路径），再下载结果到 `output/` 或 `--out` 指定路径。
- 本地脚本（模板、位置、文字）仅依赖 Pillow，无需 API token。

## rembg 抠图 → 合成流程（本地无 API）

1. 抠图：`python scripts/run_pet_image_matting_rembg.py input/图.jpg --out output/head_rembg.png`（首次运行会下载 u2net 模型，稍等片刻）
2. 合成：`python scripts/run_compose_pet_on_template.py output/head_rembg.png templates/backgrounds/清新粉蓝-1.png --out output/design.png`

路径含中文时建议在项目根目录用 Python 构建路径再调用，避免终端编码问题。

## 依赖

- replicate >= 0.25.0
- opencv-python >= 4.8.0（清晰度检测与补齐掩码）
- Pillow >= 10.0.0（模板、位置、文字合成）
- rembg[cpu] >= 2.0.0（可选，本地抠图无 API）

## 注意事项

- 所有技能路径使用正斜杠（`/`），避免反斜杠
- 需要设置 `REPLICATE_API_TOKEN` 环境变量才能调用 Replicate API
- 编排器会管理会话状态，避免重复处理已完成步骤
