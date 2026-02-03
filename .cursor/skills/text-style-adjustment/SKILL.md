---
name: text-style-adjustment
description: 文字图层 Skill。base layer + 可选 text layer 合成。删除文字 = enabled=false，不执行任何图像擦除。
---

**实现与脚本**：本技能逻辑与脚本未改动，位于项目 `skills/text-style-adjustment/` 与 `scripts/`；此处为 Cursor 约定入口，便于 Agent 发现。

# 文字图层 Skill（Text Layer Skill）

所有最终图像由 **base layer + 可选 text layer** 重新合成生成。删除文字时**不执行任何图像擦除**，仅通过 `state.text.enabled=false` 控制是否合成文字图层。

## 核心原则

1. **文字 = 独立透明图层**：文字绘制在透明 RGBA 图层上，仅含文字像素
2. **base 只读**：底图永不修改，输出写入单独路径
3. **删除 = 不合成**：`enabled=false` 或 `content` 为空时，仅复制 base 到输出，不合成 text layer
4. **禁止擦除**：不存在 inpainting、draw.rectangle、背景色采样、固定区域覆盖

## state.json

```json
"text": {
  "enabled": true,
  "content": "Lucky",
  "font": "arial.ttf",
  "size": 96,
  "color": "#000000",
  "position": "bottom-center",
  "outline": {
    "enabled": false,
    "color": "#FFFFFF",
    "width": 3
  }
}
```

- `enabled=false` → 不合成文字，输出 = 纯净 base
- `content=""` → 同上
- `enabled=true` 且 `content` 非空 → 输出 = base + text layer（alpha 合成）

## 输入与输出

| 参数 | 说明 |
|------|------|
| `base_image_path` | 不含文字的底图路径（只读，不修改） |
| `text_config` | state.text 或 CLI 参数 |
| `out_path` | 输出路径（必须与 base 不同） |

## 脚本调用

```bash
# 合成文字（base + text layer）
python scripts/run_text_style_adjustment.py output/design_base.png -c "QAQ" --out output/final.png

# 不显示文字（仅复制 base，不合成 text layer）
python scripts/run_text_style_adjustment.py output/design_base.png --disabled --out output/final.png

# 通过 state.json
python scripts/run_text_style_adjustment.py output/design_base.png --state sessions/xxx/state.json --out output/final.png
```

## 工作流程

1. 加载 base（只读）
2. 若 `enabled=false` 或 `content` 为空：`shutil.copy2(base, out_path)`，返回
3. 否则：创建 text layer → `alpha_composite(base, text_layer)` → 保存到 out_path

## 重要约束

- **输出路径 ≠ 底图路径**，否则抛出错误，防止破坏底图
- 删除文字仅通过 `enabled=false` 或 `content=""`，禁止任何像素擦除
