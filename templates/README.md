# 模板资源目录

放**模板相关图片**，如背景图。

- **backgrounds/**：背景图，模板合成时通过 `--bg templates/backgrounds/某背景.jpg` 使用。
- 未指定背景时，程序使用默认浅色背景。

使用示例：
```bash
python scripts/run_template_application.py output/extracted_head.png template_A --bg templates/backgrounds/bg1.jpg --text 宠物名 --out output/design.png
```
