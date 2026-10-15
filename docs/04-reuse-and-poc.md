# 二轮复用与 P0 实施

本文件记录早期 P0 选型及后续整合更新。原附件是设计材料；本次远端推送授权来自用户当前请求。P0 试验范围为本地技术文档闭环，后续申报/软著复用取舍另见 [上游复用记录](upstream-reuse.md)。

## 与前三份规划的合并结果

- 保留六主技能及专利领域的生态规划。本轮已提供技术文档、Word 制作、项目申报准备和软著材料准备四个实现技能；真实渠道/项目材料验收仍单独记录。
- P0 曾先验证 technical-report 与 design-spec；本次整合补齐其余五种模式，并继续让七种模式共享同一个 Word 生成器，区别只保留在章节契约、记录检查和写作方法。
- 不把现有专利渲染器泛化；本轮仅读取其实际代码作为试运行材料，专利模块保持独立。
- 新增加模板指纹、结构化章节契约、来源/引文定位、交付护照。文件放 audit，正文保持可读。
- Word 操作直接使用 python-docx/docxtpl；材料解析直接使用 MarkItDown。Docling、项目申请及软著执行器保留后续阶段。

## 新增候选的实际检查

official-document-drafting 的 GitHub API 许可标为 NOASSERTION，但实际 LICENSE 为 MIT，并排除第三方字体/资产。读取 document-qa 后确认其数值清单只是提示，不能当成“没有幻觉”的证明；本实现把机器检查与语义审阅分开。

suling-fun 的 verify_materials.py 明确列出可以机械检查与不能机械检查的内容；Fokkyp 的源码选择和手册结构强调完整文件粒度、真实页面和人工确认。本地软著模块逐项吸收这些边界，未搬入上游脚本或执行器。

caolonghao 的 ndrc 工作流强调先确定申报渠道和证据状态，再起草与评审，适用于后续申报模式。riekelt 的设计技能区分事实与提案，并解释选择、代价及限制，相关规则已精简改编到设计说明参考文件。

固定 SHA、许可副本及具体落点见 [THIRD_PARTY.md](../THIRD_PARTY.md)。没有下载受限 DOCX Skill 或重新分发字体。

## 代码和数据路径

```text
inputs → ingest → source-index.json + source snapshots + segments
Agent source review → evidence.json + draft.json
lint → section/quote/hash/numeric checks
build → python-docx or docxtpl → output.docx
LibreOffice → preview.pdf → Poppler page images
DOCX/PDF checks → audit/validation.json + layout.json
actual content and all-page review → review.json → finalize
```

实现文件：`word_skills/ingest.py`、`evidence.py`、`render.py`、`inspect.py`、`delivery.py`、`cli.py`；两份 YAML 契约随 Python 包安装，避免运行时依赖当前工作目录。

输入和输出不会原地覆盖。源码目录摄入排除常见构建/依赖目录及明显凭据文件，但这不是全面敏感信息识别器。处理保持本地，MarkItDown 插件关闭，用户需对发布的来源材料范围负责。

## 试运行的真实范围

以现有 `oh-my-patent` 的项目配置、摄入、渲染、最终校验及页面配置源文件生成技术报告和设计说明。固定试运行脚本是对已读来源的案例复现，不是通用自动事实核验器。生成说明没有编造吞吐量或实验结果。

没有客户 Word 样板，因此本轮创建一个明确标记的参考模板 fixture，验证页边距、标题样式及显式 title/body 插槽；不能据此声称任意企业复杂模板已通过。Java/Spring Boot 真实案例、客户多节模板属于下一批评测，不在本轮已验证清单中。

## 当前能力边界

- 事实门禁验证文件完整性、准确引文位置和数字覆盖；同一个数字用在错误的指标上仍可能通过机器检查，必须审查语义、单位与条件。
- 模板只支持单节基本样式和受限插槽。style 模式明确替换样板正文，不能用于原稿保真编辑。
- PDF 检查包含页数、空白页、文本越界与孤立标题启发式；重叠、表格视觉截断及字体替换仍需看实际页图。
- review.json 是审阅记录，不是真实性证明。程序可以拒绝缺页或过期记录，不能证明审阅者实际看过页面。
- 本轮不支持插图/复杂公式/任意 Markdown 富文本、跨客户端全版本兼容或外部自动申请。

## 独立复核修复

fresh-context reviewer 在已有测试通过后发现：插槽正文使用默认子文档宽度、正文插槽相邻文本可能被丢弃、缺标题槽位未报错。已增加宿主页面参数传递、独占插槽约束、最终标题/正文检查和对应回归测试。

本地试运行的页图、版本与 manifest 存于未发布的验收目录；公开仓库内的确定性行为以 `tests/test_pipeline.py` 和结构检查为准。本设计说明本身不是运行验收证据。
