# 多宠物合成稳定性升级说明

依据《升级方案.md》与《TWO_PETS_LOVE_2_DIAGNOSIS.md》完成的增强，未改动机器学习/抠图模型本身。

---

## 一、新增：抠图结果有效性校验（模块一）

**文件**：`utils/matting_validation.py`

- **规则 1**：alpha 覆盖率  
  - 通用：`0.05 <= alpha_ratio <= 0.6`  
  - 圆形双宠：`0.08 <= alpha_ratio <= 0.45`
- **规则 2**：最大连通域占比 >= 80%（否则判定抠图碎裂/失败）
- **规则 3**：长宽比 sanity  
  - 通用：`0.6 <= width/height <= 1.8`  
  - 圆形双宠：`0.7 <= width/height <= 1.6`

**接入**：`scripts/run_multi_pet_composition.py` 在加载抠图结果后、合成前调用 `validate_all_pet_mattings()`；**任一失败即中断多宠物合成**，抛出 `ValueError` 并说明哪只失败及原因，不继续合成。

---

## 二、视觉面积归一化安全兜底（模块二）

**文件**：`utils/multi_pet_enhancement.py`

- `normalize_visual_areas()` 增加参数：  
  - `factor_clamp`：通用 (0.75, 1.25)，圆形 (0.80, 1.20)  
  - `scale_clamp`：(0.65, 1.0)，禁止单宠 scale > 1.0
- 计算顺序：`factor = sqrt(ref/area)` → clamp factor → `scale *= factor` → clamp scale

---

## 三、多宠物合成硬约束与圆形专用（模块三）

**文件**：`utils/multi_pet_enhancement.py`、`skills/multi_pet_composition_enhancement/skill.py`

- **anchor 硬约束**：  
  - 通用：x ∈ [0.2, 0.8]，y ∈ [0.25, 0.75]  
  - 圆形双宠：x ∈ [0.30, 0.70]，y ∈ [0.42, 0.62]
- **组合中心对齐**：  
  - 通用：目标中心 (0.5, 0.5)  
  - 圆形：目标中心 (0.5, 0.53)，对齐后 anchor 再 clamp 到圆形范围
- **圆形模板检测**：除原有逻辑外，路径中含「清新粉蓝」「qingxin」「fenlan」时视为圆形。
- **圆形整体缩放**：`global_scale_multiplier = 0.85`（scale_reduction=0.15），且每只 scale 上限 1.0。
- **圆形双宠**：内描边默认开启（规范七）。

---

## 四、执行顺序（与规范八一致）

1. 单宠抠图（现有流程）
2. **抠图结果有效性校验（任一失败 → 中断）**
3. 边缘展示级处理（净化 + 羽化 + 圆形时内描边）
4. 计算视觉中心、视觉面积
5. 视觉面积归一化 + factor/scale clamp
6. 组合中心对齐 + anchor clamp（圆形用专用目标与范围）
7. 圆形模板时应用全局缩放 0.85
8. 最终合成

---

## 五、涉及文件一览

| 文件 | 变更 |
|------|------|
| `utils/matting_validation.py` | 新增：校验规则与 `validate_all_pet_mattings` |
| `utils/multi_pet_enhancement.py` | 归一化 clamp、anchor 常量、对齐参数、圆形检测与缩放 |
| `skills/multi_pet_composition_enhancement/skill.py` | 圆形时使用专用参数与内描边 |
| `scripts/run_multi_pet_composition.py` | 合成前调用校验，失败即中断 |

---

**说明**：未实现「降级为单宠物」的自动回退；校验失败时仅中断并报错，由调用方或用户决定是否重抠或改为单宠流程。
