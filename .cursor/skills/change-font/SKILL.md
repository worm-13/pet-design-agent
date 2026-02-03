---
name: change-font
description: 仅更换圆形文字字体，大小、排版、颜色、位置、内容全部保持不变
---

**实现与脚本**：本技能逻辑在 `scripts/run_change_font.py`；此处为 Cursor 约定入口，便于 Agent 发现。

# 更换字体技能（Change Font）

在**已有圆形文字**的会话中，**仅更换字体**，其余参数（字体大小、排版方式、颜色、位置、文字内容）全部保持不变。

## 定位

- **不做**：修改文字内容、颜色、位置、大小、排版、重复次数等。
- **只做**：用新字体重新渲染圆形文字，覆盖 `design_final.png`，并更新 `state.text_style.circle_text_font_path`。

## 前置条件

- 会话已通过 `run_multi_pet_with_circle_text` 等流程添加过圆形文字
- `state.text_content` 与 `state.text_style` 已存在
- `sessions/<session_id>/design.png` 存在（无文字的合成底图）

## 输入与输出

| 类型 | 参数 | 必填 | 说明 |
|------|------|------|------|
| 输入 | `session_id` | 是 | 会话 ID |
| 输入 | `font` | 是 | 新字体 ID（如 字体1、字体2）或字体文件路径 |
| 输出 | `design_final_path` | — | 更新后的 `sessions/<session_id>/design_final.png` |

## 脚本调用

```bash
# 使用字体 ID
python scripts/run_change_font.py <session_id> --font 字体2

# 使用字体 ID（简写）
python scripts/run_change_font.py <session_id> -f 字体1

# 使用字体路径
python scripts/run_change_font.py <session_id> --font assets/fonts/zhankukuaile.ttf
```

## 工作流程

1. 加载 state，校验 `text_content` 存在
2. 解析新字体路径（`get_font_path` 支持 ID 或路径）
3. 以 `design.png` 为底图，用 state 中的 color、position、content，**仅字体改为新字体**，调用 `add_circle_text_to_image`
4. 输出到 `design_final.png`
5. 更新 `state.text_style.circle_text_font_path` 为新字体路径

## 参考

- 字体管理：`utils/font_manager.py`（`get_font_path`）
- 圆形文字：`scripts/add_circle_text.py`、`skills/circle_text_skill/`
