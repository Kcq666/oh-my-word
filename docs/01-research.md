# 调研与复用清单

调研日期：2026-10-15。范围：本地现有专利项目 + 9 个外部 GitHub 仓库。搜索用于发现候选，结论以实际读取的仓库、文件和许可证为依据。没有执行候选项目，成熟度不以星数推定。

## 1. 现有专利项目

本地基线：原 `oh-my-patent` 工作区，Git HEAD 为 `d6c6b8d603fa96cf67f95ff9a7fcb716d5e3eb48`；工作区存在已修改和未跟踪文件，因此 HEAD 不代表本次阅读内容的完整快照。

实查统计：7 个 SKILL.md（总入口 1 + 领域模块 6），18 个 `oh_my_patent` 包内 Python 文件，10 个测试文件。测试文件数量不等于测试用例数量；本轮未运行专利测试。

| 已有能力 | 当前文件 | 复用方式 |
|---|---|---|
| 范围识别、按需加载、局部修改 | `SKILL.md`、`references/task-scope.md` | 继承流程结构，替换业务规则 |
| 来源、原文位置、事实状态 | `references/evidence-contract.md` | 泛化为共用事实与来源契约；保留专利扩展 |
| Word/PPT 摄入、公式退化告警 | `oh_my_patent/ingest.py` | 先经适配器调用，再迁入共享层；保留原件、位置与告警 |
| 字体、主题字体、页码、OOXML 兼容 | `oh_my_patent/oxml.py` | 抽取通用函数，页面配置参数化 |
| 专利 Word 渲染 | `oh_my_patent/render/docx.py` | 保留原实现作为专利后端；技术报告使用独立渲染模型 |
| 证据哈希、审查过期检测 | `oh_my_patent/gate.py` | 提取变化检测原则；不复用专利专属检查项列表 |
| 专利模型、权项关系和申请规则 | `schema.py`、`lint*.py`、`spec.py`、`handoff.py` | 留在专利模块，不改成所有文档的通用模型 |
| 技能目录、案卷和行为评测 | `skill_registry.py`、`casework.py`、`skill_eval.py` | 扩充 registry 与跨业务评测；不把结构校验当质量评分 |

重要约束：`configure_section()` 固定 A4 和 25/25/15/15 mm 页边距；现有渲染器依赖 `PatentDraft`、`PatentType`、专利章节及固定正文宽度。仅改项目名称不能得到技术文档引擎。共享排版应接受 Profile，并按实际页面和页边距计算可用宽度。

现有项目采用 MIT。迁移或复制代码时保留原版权信息和许可证；原工作区有未提交改动，迁移前需记录文件哈希和差异，不以远端 clone 替换本地版本。

## 2. GitHub 候选与决策

固定提交见 [upstream-sources.json](upstream-sources.json)。以下 URL 用于浏览，上游变化不能自动覆盖已审核版本。

| 仓库 | 实际检查范围 | 可吸收内容 | 取舍 |
|---|---|---|---|
| [Fenng/Tech-Doc-Style-Chinese](https://github.com/Fenng/Tech-Doc-Style-Chinese) | SKILL.md、LICENSE、目录/元数据 | 中文术语一致性、事实保真、机器标识符保护、按任务选择写作/改写/校对 | MIT，优先改编少量相关规则并保留署名；不原样继承所有个人风格 |
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | research-grants、scientific-writing 的入口前部、LICENSE.md、目录 | 申报指南到章节的要求映射、研究目标与预算组织、证据约束 | MIT，选取这两个模块的适用部分；中国申报类型另做本地化 |
| [Fokkyp/SoftwareCopyright-Skill](https://github.com/Fokkyp/SoftwareCopyright-Skill) | 软著 SKILL.md 前部、源码提取脚本函数与关键行、LICENSE | 真实项目分析、候选源码选择、代码材料清单、申请字段一致性、手册证据 | MIT，作为软著优先基线；源码抽取需完整审读和测试后才导入 |
| [anthropics/skills](https://github.com/anthropics/skills) | doc-coauthoring、README、docx/LICENSE.txt、目录和第三方声明前部 | 协作文档的读者视角和迭代结构有参考价值 | DOCX 明确非开源并有限制，不复制；doc-coauthoring 在所查提交没有独立 LICENSE，先只借鉴方法，明确授权后再复制 |
| [yanhaoluo0/technical-proposal-expert-writing-skill](https://github.com/yanhaoluo0/technical-proposal-expert-writing-skill) | SKILL.md 前部、README 搜索结果、完整路径树 | 中文设计/测试/标书场景划分的比较样本 | 未发现 LICENSE，不搬入文本或代码；其规则不作为本项目指令 |
| [python-openxml/python-docx](https://github.com/python-openxml/python-docx) | 仓库元数据、项目说明、LICENSE；本地已有调用实现 | 原生 DOCX 段落、样式、表格、图片创建 | MIT，继续作为核心库，不重造 OOXML 文档容器 |
| [elapouya/python-docx-template](https://github.com/elapouya/python-docx-template) | 元数据、LICENSE.txt、官方模板语法文档 | 既有 Word 模板的字段、段落与表格行填充 | LGPL-2.1，可选依赖；不复制源码进核心。发布时核对实际依赖版本的许可要求 |
| [microsoft/markitdown](https://github.com/microsoft/markitdown) | 元数据、README 的定位/输入格式/可选依赖 | 扩展 PDF 等输入来源的统一转换适配 | MIT（GitHub 识别），可选摄入后端；先以含公式和表格样本比较保真，不直接替换现有摄入 |
| [jgm/pandoc](https://github.com/jgm/pandoc) | 元数据、README 的格式支持和许可声明 | Markdown/Word 等通用格式转换候选 | README 标示 GPLv2+，作为可选外部命令研究；不把二进制捆绑发布。是否打包需另核对条款 |

数量口径：9 个外部仓库；其中 5 个宽松许可候选（Fenng、K-Dense、Fokkyp、python-docx、MarkItDown），2 个需单列许可证处理的依赖候选（docxtpl、Pandoc），2 个暂不直接复制的仓库（Anthropic 按目录区分、中文技术标书项目无许可）。这不是 9 个全部需要安装的依赖。

### 调查中纠正的信息

- K-Dense 的旧仓库链接 `claude-scientific-skills` 已重定向到 `scientific-agent-skills`，技能现位于 `skills/`，旧 `scientific-skills/` 路径返回 404。
- 搜索结果仍包含旧分支/镜像中“强制 AI 配图”的要求；本次固定提交中的 research-grants 已将配图列为可选。后续以固定提交原件为准。
- Anthropic 根 README 说“许多技能为 Apache 2.0”，不能据此判断所有目录都拥有相同许可。所查 doc-coauthoring 没有独立许可文件，因此保守列为方法参考；DOCX 不纳入代码来源。
- Fokkyp 当前工作流明确绑定 OfficeCLI，且含较多用户确认门禁。直接整包接入会改变现有 Python 工具链和交互方式，所以拟复用经验证的业务选择与追溯机制，而不是照搬整套执行器。

### 明确不继承的设计

- 不把“所有中文文档必须触发”写入技能描述，避免抢占不相关任务。
- 不强制写到固定字数后暂停，也不机械要求每个章节确认。
- 不强制 AI 图片、不把示意图冒充运行截图，不为了页数生成代码或数据。
- 不把 NSF/NIH 等机构模板直接当中国项目申请书；具体受理单位、年度和通知版本决定格式及检查项。
- 不把任意 GitHub 示例中的数字、项目经历、实验数据当作用户项目事实。

## 3. 复用执行清单

| 优先级 | 动作 | 前置证据 |
|---|---|---|
| P0 | 复用本地摄入、字体处理和证据流程 | 保留原测试，确认工作区快照；先适配后抽取 |
| P0 | 采用 python-docx，写技术报告 Profile | 表格、图题、页眉页脚、中文字体和长文分页样本 |
| P0 | 改编 Fenng 中适用的保真与术语规则 | 实际复制片段、来源提交、MIT 许可与修改说明 |
| P1 | 改编 K-Dense 的指南映射与报告证据流程 | 按文件检查依赖引用；去除不适用的机构条款 |
| P1 | 评估 docxtpl 模板后端 | 官方模板样本、字段映射、跨 run 标签与合并单元格测试 |
| P2 | 适配 Fokkyp 代码选择/提取机制 | 完整脚本审读，追踪原始文件行号和内容哈希；分页不能只靠字符估算 |
| P2 | 评估 MarkItDown 和 Pandoc | 保真对比、缺失告警、部署体积和许可证清单 |

docxtpl 官方文档说明普通 Jinja 标签不能跨段落、行或 run；段落/表格结构使用专用标签。这意味着“直接填任何上传的 Word”不是现成能力，需要模板预检和字段适配。[官方文档](https://docxtpl.readthedocs.io/en/latest/index.html)

## 4. 尚缺材料与验证

不影响当前架构决策，但决定后续业务模板质量：

- 技术文档：一份目标技术报告/设计说明模板，以及能支撑它的真实项目材料。
- 项目申请：优先覆盖哪类项目、当年度官方通知、申请模板、评审要点及预算规则；第一版可先实现通用框架。
- 软著：真实代码目录、软件版本、权利人信息、运行环境与截图；登记材料规则实施时核对官方当期说明。
- 验证：至少一套完整材料、一套材料缺失案例、一份已有 Word 模板；记录实际 Office/WPS/LibreOffice 版本，不泛称全版本兼容。

本报告没有验证申请规则的具体页数、行数、期限或法律效果；这些不应从社区技能复制成硬编码。
