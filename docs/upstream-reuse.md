# 上游复用决策

本文件记录本轮为 Word Skills monorepo 实际核查并改编的方法。固定提交、许可证和落点以 `upstream.lock.json` 为准；这里只说明为什么复用以及哪些内容明确不带入。

## 软著材料

Fokkyp/SoftwareCopyright-Skill 的固定提交 `947d5963194bfda8ce57b8b454b486f13359dee4` 核查了 `software-copyright-materials/SKILL.md`、`scripts/extract_code_material.py` 和 MIT `LICENSE`。它强调从真实项目入口选择源码、保留文件与行段来源、把手册和页面证据放回同一软件身份。本地 `word_skills/copyright.py` 将这些边界改成源清单哈希、行范围、敏感文件排除和共享 Word 交付审阅；没有引入 OfficeCLI 或其执行器。

suling-fun/software-copyright-materials-skill 的固定提交 `d7b49eea8f6e455ef3547c0d16d1945e204bc8a7` 核查了 `SKILL.md`、`verify_materials.py` 和 MIT `LICENSE`。本地吸收了“机械一致性检查”和“人工语义/权属判断”分离的原则，并增加了声明字段与源文件变化失效；没有复制它的黑名单、验证器或登记流程。

## 项目申报

caolonghao/nsfc-grant-assistant-skill 的固定提交 `a694ab4cfbf8bad64357c6803e5f39c4b0eda47a` 核查了 `ndrc-bid-assistant/` 入口和 MIT `LICENSE`。本地 `word_skills/proposal.py` 采用渠道、指南快照、要求定位、章节映射和条件证据先行，并把预算算术交给确定性校验；没有复制它的评审模型、提示词编排或提交动作。随附 NSFC Profile 是历史回归结构，状态为 expired，不能代表当前开放申报渠道。

## 其他参考

技术写作规则和设计说明方法分别来自 `Fenng/Tech-Doc-Style-Chinese` 与 `riekelt/technical-writer` 的固定提交，采用范围见 `THIRD_PARTY.md`。`official-document-drafting`、doc-coauthoring、Pandoc 模板和未明确许可的标书仓库只作比较；没有把它们的文本、字体、模板或执行代码放进发行包。

复用后的代码仍遵守本仓库的事实边界：工具能核对来源、哈希、章节、预算、代码行段和版面启发式，但不会自动确认权属、法律资格、官方受理或写作语义充分性。
