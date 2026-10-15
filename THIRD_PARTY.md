# 第三方来源与复用记录

更新日期：2026-10-15。本项目使用成熟库处理 Word、模板与材料；本地胶水代码实现证据契约、模式校验及交付状态。没有复制 Anthropic DOCX、字体文件或外部专利实现代码。

## 已改编的写作规则

| 来源与固定提交 | 许可 | 实际落地 | 修改范围 |
|---|---|---|---|
| [Fenng/Tech-Doc-Style-Chinese](https://github.com/Fenng/Tech-Doc-Style-Chinese/tree/b119d01c9bb7cd132b3c62fafdff34227c4410d1) | [MIT](third_party/licenses/fenng-MIT.txt) | shared/references/chinese-writing.md | 精简为事实保真、术语和机器标识符原则，不继承个人标点偏好 |
| [riekelt/technical-writer](https://github.com/riekelt/technical-writer/tree/85e53729dd959a2795d593d6769068e342cf3486) | [MIT](third_party/licenses/technical-writer-MIT.txt) | skills/oh-my-technology/references/design-spec.md | 改编事实/提案区分、设计取舍和残余风险的审阅方法，不复制英文文风限制 |

以上实际改编项及运行依赖版本记录在 [upstream.lock.json](upstream.lock.json)，并保留完整许可证。

## 方法参考，未复制源码或文案

[official-document-drafting](https://github.com/zhaohui-yang/official-document-drafting/tree/6b4166a50b96733684b36da6336ea85a847cf3be) 的 `skills/document-qa/SKILL.md` 用于比较章节检查与人工语义复核的边界，取舍见 [docs/04-reuse-and-poc.md](docs/04-reuse-and-poc.md)。仓库 LICENSE 为 [MIT，资产除外](third_party/licenses/official-document-MIT.txt)；本项目的检查程序独立实现，未导入公文格式、字体或文种模板。仅方法对照不伪称代码集成。

## 运行库

| 库 | 本轮验证版本 | 使用方式与许可 |
|---|---|---|
| python-docx | 1.2.0 | 直接依赖，MIT；DOCX 对象与样式 |
| docxtpl | 0.20.2 | 可选依赖，LGPL-2.1；受限插槽模板 |
| docxcompose | 1.4.1 | docxtpl 子文档辅助，MIT |
| MarkItDown | 0.1.8 | 可选依赖，MIT；本地 DOCX/PDF 摄入 |
| PyYAML | 6.0.3 | 直接依赖，MIT；章节契约 |
| pdfplumber | 0.11.9 | 直接依赖，MIT；PDF 文本位置与版面启发式检查 |
| pypdf | 6.10.0 | 直接依赖，BSD-3-Clause；页数及按页文本 |
| LibreOffice | 具体运行版本记入 manifest | 外部程序，不随代码发行；遵循其原有许可 |
| Poppler | 具体运行环境提供 | 外部程序，不随代码发行；遵循其原有许可 |

第三方库通过包管理器安装，不复制源码或重新许可。发行安装器、捆绑二进制或修改库前，另核对相应版本完整许可及间接依赖声明。`requirements-tested.txt` 记录本轮主要运行版本，不代表全部传递依赖锁定。

## 本轮新增候选但未集成

| 仓库 | 固定 SHA | 实际核查与决策 |
|---|---|---|
| [suling-fun/software-copyright-materials-skill](https://github.com/suling-fun/software-copyright-materials-skill) | d7b49eea8f6e455ef3547c0d16d1945e204bc8a7 | LICENSE 为 MIT，读取 verify_materials.py 前部；机械检查与独立语义复核值得采纳。软著阶段再与 Fokkyp 比较，不在 P0 导入执行器 |
| [caolonghao/nsfc-grant-assistant-skill](https://github.com/caolonghao/nsfc-grant-assistant-skill) | a694ab4cfbf8bad64357c6803e5f39c4b0eda47a | LICENSE 为 MIT，读取 ndrc-bid-assistant 入口前部；条件证据、具体指南与评审模型留待申报阶段，不自动采用其 Agent 编排 |
| [docling-project/docling](https://github.com/docling-project/docling) | 6fadbae317b09c4dd4051c0f1fc1746c6baf04bc | GitHub 识别 MIT，目录已核查；暂不安装模型和复杂输入后端，模型许可尚待具体选型 |

OpenAI skill-creator 使用当前环境提供的初始化/元数据/校验工具，未复制到本仓库。初轮来源继续见 docs/upstream-sources.json；它是候选调查记录，不是实际依赖锁。

## 未复制资源

Anthropic docx 明确列为受限材料；doc-coauthoring 的通用协作方法可比较，原文未复制。未明确授权的技术标书与 Pandoc 模板仓库不导入。字体使用运行环境已有字体，本仓库不分发字体二进制。
