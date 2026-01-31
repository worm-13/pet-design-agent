# 位置调整技能 - 参考

## 画布与边距

- **默认画布尺寸**：与模板应用一致为 1:1（1080×1080）；若仅做位置调整无模板，可按宠物图像尺寸加边距（如左右各 10%）生成。
- **默认边距**：`margin` 建议 10～20 像素，可根据设计需求调整。

## 位置扩展

除 `center`、`top-left`、`top-right`、`bottom-left`、`bottom-right` 外，可扩展：

- `top-center`：顶部居中
- `bottom-center`：底部居中
- `left-center`：左侧垂直居中
- `right-center`：右侧垂直居中

坐标对应：`top-center` → `( (canvas_w - pet_w) // 2, margin )`，其余类推。

## 与模板应用的关系

本技能输出 `adjusted_image` 为「已按位置放置的宠物图层」；若后续要合成到模板，可将 `adjusted_image` 作为 `extracted_image` 传入模板应用技能，或由模板应用技能内部按 `position` 自行计算。根据项目流程二选一即可。
