# 工作流程

## 当前流程

1. **去除背景** → 使用 `851-labs/background-remover` 去除原图背景
2. **抠出主体** → 使用 `google/nano-banana` 抠出全身/半身/头部
3. **再次去除背景** → 对抠图结果再次去背景，确保边缘干净
4. **模板合成** → 将干净抠图与背景模板合成
5. **文字叠加** → 按需添加文字（可选）

## 一键运行

```bash
python scripts/run_full_pipeline.py input/原图.jpg [--template templates/backgrounds/xxx.png] [--pet-type head] [--text "OVO"] [--out-dir output]
```

## 分步调用

```bash
# 1. 去除背景
python scripts/run_background_removal.py input/原图.jpg --out output/no_bg.png

# 2. 抠图（head / half_body / full_body）
python scripts/run_pet_image_matting.py output/no_bg.png --pet-type head --out output/extracted.png

# 3. 再次去除背景
python scripts/run_background_removal.py output/extracted.png --out output/extracted_clean.png

# 4. 与模板合成
python scripts/run_compose_pet_on_template.py output/extracted_clean.png templates/backgrounds/xxx.png --out output/design.png

# 5. 添加文字（可选）
python scripts/run_text_style_adjustment.py output/design.png -c "文字" --out output/final.png
```

## 模型版本

- **背景去除**: `851-labs/background-remover:a029dff38972b5fda4ec5d75d7d1cd25aeff621d2cf4946a41055d7db66b80bc`
- **抠图**: `google/nano-banana`（最新版）

## 环境

- 需设置 `REPLICATE_API_TOKEN`（.env 或环境变量）
