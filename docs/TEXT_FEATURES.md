# 文字功能

设计图上的文字由 **文字图层 Skill（text-style-adjustment）** 实现。所有最终图像由 **base layer + 可选 text layer** 合成。删除文字时**不执行任何图像擦除**，仅通过 `state.text.enabled=false` 控制是否合成文字图层。

- **技能位置**：[skills/text-style-adjustment/SKILL.md](../skills/text-style-adjustment/SKILL.md)
- **实现脚本**：`scripts/run_text_style_adjustment.py`
- **状态配置**：`state.json` 中的 `text` 字段（enabled、content、font、size、color、position、outline）

使用说明见上述 SKILL.md。
