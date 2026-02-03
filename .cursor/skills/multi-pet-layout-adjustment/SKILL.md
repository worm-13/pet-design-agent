---
name: multi-pet-layout-adjustment
description: 多宠物场景下调整某只宠物的位置与大小，更新 state 后按 state 布局重合成（不重抠、不重新自动布局）
---

**实现与脚本**：本技能逻辑在 `scripts/run_pet_layout_adjustment.py`、`scripts/state_manager.py` 与 `scripts/run_multi_pet_composition.py`；此处为 Cursor 约定入口，便于 Agent 发现。

# 多宠物布局调整技能（Multi-Pet Layout Adjustment）

在**多宠物**会话中，单独调整某只宠物的**位置（anchor）**或**缩放（scale）**，写回 state 后按 state 中的布局参数重新合成，得到新设计图。不重抠图、不重新自动布局。

## 定位

- **不做**：重新抠图、重新自动布局、视觉面积归一化、组合中心对齐。
- **只做**：更新 state 中该宠物的 `anchor` / `scale`，然后以 `use_state_layout=True` 调用多宠物合成；合成时仅做边缘处理、anchor 硬约束与（若为圆形模板）整体缩放。
- **最终产品图**：只移动用户指定的宠物图层，其他宠物、背景、文字等不变。若 state 中保存了文字配置（`text_content` / `text_style`），会在新 `design.png` 上重绘圆形文字并输出 `design_final.png`，保证「最终产品图」只变动被移动的那一层。

## 与单宠物位置调整的区别

| 能力 | pet-image-position-adjustment | multi-pet-layout-adjustment |
|------|------------------------------|-----------------------------|
| 场景 | 单宠物 + 直接传参合成 | 多宠物 + session state |
| 输入 | pet_png, template_path, position, scale | session_id, pet_id, position, scale |
| 合成 | 单宠合成脚本 | run_multi_pet_composition(use_state_layout=True) |

## 输入与输出

| 类型 | 参数 | 必填 | 说明 |
|------|------|------|------|
| 输入 | `session_id` | 是 | 会话 ID（如 two_pets_love_2） |
| 输入 | `pet_id` | 是 | 要调整的宠物 ID（如 pet_a, pet_b） |
| 输入 | `position` | 否* | 新位置 (x,y)，相对坐标 0~1，如 0.35,0.55 |
| 输入 | `scale` | 否* | 新缩放比例，如 0.85 |
| 输出 | `design_path` | — | 重新合成后的设计图路径；若有文字配置则输出 `design_final.png`，否则为 `design.png` |

\* 至少指定 `position` 或 `scale` 之一。

## 脚本调用

```bash
# 仅改位置
python scripts/run_pet_layout_adjustment.py <session_id> <pet_id> --position x,y

# 仅改缩放
python scripts/run_pet_layout_adjustment.py <session_id> <pet_id> --scale 0.85

# 同时改位置与缩放
python scripts/run_pet_layout_adjustment.py <session_id> pet_a --position 0.32,0.58 --scale 0.88
```

位置格式为 `x,y`（相对坐标 0~1），例如 `0.5,0.6` 表示水平居中、略偏下。

## 工作流程

1. **加载 state**：`StateManager().load_state(session_id)`。
2. **校验宠物**：确认 `pet_id` 存在于 `state.pets`。
3. **更新布局**：`state_manager.update_pet_layout(session_id, pet_id, anchor=..., scale=...)`，只写回指定宠物的 anchor/scale。
4. **重合成**：调用 `run_multi_pet_composition(session_id, use_state_layout=True)`，使合成使用 state 中所有宠物的 anchor/scale，不做自动布局、归一化与组合对齐，仅做边缘处理、anchor 硬约束与圆形整体缩放。
5. **输出**：合成结果保存到 `sessions/<session_id>/design.png`。若 state 中有 `text_content`（及 `text_style` 中的圆形文字参数），则在新 design 上重绘圆形文字并保存为 `sessions/<session_id>/design_final.png`，返回最终图路径，从而保证「只移动指定图层、保留文字等其他元素」。

## 与 state 的配合

- 用户说「把左边那只往左一点」「右边那只缩小一点」时：只改 state 中对应 `pet_id` 的 `anchor` 或 `scale`，然后执行上述流程。
- 抠图与初次合成只做一次；布局调整阶段全是「改 state → 按 state 重合成」。
- **最终图与文字**：添加圆形文字时若通过 `run_multi_pet_with_circle_text` 等流程写入 state（`set_text`），布局调整后会自动重绘 `design_final.png`；否则仅更新 `design.png`。

## 参考

- 状态管理：`scripts/state_manager.py`（`update_pet_layout`）
- 多宠物合成：`scripts/run_multi_pet_composition.py`（参数 `use_state_layout`）
- 多宠物合成增强：`skills/multi_pet_composition_enhancement/`（`use_state_layout` 时跳过归一化与组合对齐）
