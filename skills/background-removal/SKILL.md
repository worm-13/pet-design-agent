---
name: background-removal
description: 使用 851-labs/background-remover 去除原图背景，输出透明 PNG。为抠图步骤的前置。
---

# 背景去除技能

使用 `851-labs/background-remover` 去除原图背景，输出透明 PNG。去背景后的图片供 `pet-image-matting` 抠出全身/半身/头部。

## 模型版本

`851-labs/background-remover:a029dff38972b5fda4ec5d75d7d1cd25aeff621d2cf4946a41055d7db66b80bc`

## 脚本

`scripts/run_background_removal.py`

```bash
python scripts/run_background_removal.py <原图路径> [--out 输出路径]
```

## 输出

透明背景 PNG（background=rgba）
