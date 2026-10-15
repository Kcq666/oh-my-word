# 模板支持范围

先运行：`python -m word_skills fingerprint reference.docx --out profile.json`。

两个明确模式：

- `--template reference.docx --template-mode style`：提取并保留单节页面属性、段落样式、页眉页脚等；正文会清空并用中间稿重建。用于样式样板，不能用于“原稿原位改写”或保留封面/固定正文。
- `--template slots.docx --template-mode slots`：参考模板含 `{{ title }}` 与独立段落中的 `{{p body }}`，通过 docxtpl 填充；body 恰好一处，禁止其他 Jinja 表达式。固定模板正文属于模板输入，应与所有输出一起审阅。

当前仅支持单节参考模板。多节、分栏、复杂编号、内容控件、文本框、修订、嵌入对象和特殊域不能承诺保真。fingerprint 只报告可解析的基本属性，对未覆盖元素发出提示；检查器发现差异要先明确原因再交付。

模板原件保持不变。生成后对比页尺寸、边距和基础样式，检查表格与中文长标题；再看所有渲染页。不能仅凭 JSON 相等声称逐像素一致。客户尚未提供模板时，只能说测试模板通过，不能说客户模板已验证。
