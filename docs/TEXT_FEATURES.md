# 文字功能

项目支持两种文字功能：**普通文字**和**圆形文字排版**。

## 普通文字功能

设计图上的文字由 **文字图层 Skill（text-style-adjustment）** 实现。文字作为独立透明图层生成，通过 alpha 合成叠加到底图，支持多轮安全修改，无像素擦除。

- **技能位置**：[skills/text-style-adjustment/SKILL.md](../skills/text-style-adjustment/SKILL.md)
- **实现脚本**：`scripts/run_text_style_adjustment.py`
- **状态配置**：`state.json` 中的 `text` 字段（content、font、size、color、position、outline）

## 圆形文字排版

圆形文字排版由 **圆形文字布局 Skill（circle-text-layout）** 实现，支持短语级均分、单词级间距、字符级高精度排版的高质量圆形文字渲染。

- **技能位置**：[skills/circle-text-layout/SKILL.md](../skills/circle-text-layout/SKILL.md)
- **实现脚本**：`scripts/run_circle_text_layout.py`
- **预设配置**：支持宠物标签、品牌徽章、节日问候等场景

### 快速使用

```bash
# 宠物标签预设
python scripts/run_circle_text_layout.py --preset pet_tag --text "LUCKY"

# 自定义配置
python scripts/run_circle_text_layout.py --phrases "I LOVE YOU" "I LOVE YOU" "I LOVE YOU"
```

## 集成使用

文字功能已集成到宠物设计编排器中，可通过 [pet-design-orchestrator](../skills/pet-design-orchestrator/SKILL.md) 统一调用。

详细的使用说明、参数配置、脚本示例请参考各Skill文档。
