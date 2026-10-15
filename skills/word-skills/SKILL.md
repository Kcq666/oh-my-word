---
name: word-skills
description: 根据用户目标选择已实现的技术文档、专利或 Word 制作能力，并在多份文档任务中组合共享的来源、事实和交付链路；未实现的申报与软著能力必须明确说明规划状态。
---

# word-skills 总入口

这是仓库级路由入口，不替业务 Skill 起草正文。先根据用户请求选择一个或多个已登记能力，再读取对应的 `SKILL.md`。能力状态以 [注册表](../../registry/skills.yaml) 为准；文件存在本身不代表能力已经验证。

## 路由规则

| 用户目标 | 读取能力 | 当前状态 |
| --- | --- | --- |
| 技术报告、设计说明 | `skills/oh-my-technology/SKILL.md` | 已实现：technical-report、design-spec |
| 已组织内容的 Word 排版、模板样式或页图检查 | `skills/word-document/SKILL.md` | 已实现：基本单节样式与受限插槽 |
| 专利交底、申请审阅稿、事实/权项检查和 XML 交接 | `skills/oh-my-patent/SKILL.md` | 已实现；沿用旧入口与六领域模块 |
| 项目申报书、可研和预算 | `oh-my-proposal` | 规划中，不创建空技能冒充可用 |
| 软件著作权材料 | `oh-my-copyright` | 规划中，不创建空技能冒充可用 |

明确的业务请求可以直接进入对应技能。请求同时包含多个交付物时，先分别确定每份文档的来源和状态，再共享经过核对的事实；不要把一个文档的结论、审阅状态或权利要求自动复制到另一个文档。

## 共享边界

- Agent 负责阅读材料、选择章节、组织正文和语义审查。
- Python 工具负责来源快照、哈希、结构/数值门禁、Word 生成和交付状态。
- 用户保留项目事实、权属、申报资格以及最终提交判断。
- `planned` 能力只能返回缺口和下一步，不能生成看似完整的空模板。
- `reviewed` 只表示已记录的内容/版面复核，不表示事实真实性、提交、受理或授权。

## CLI

```text
word-skills skills list
word-skills route "写一份技术报告"
word-skills route "只调整 Word 页眉和页码"
word-skills patent template invention -o outputs/draft.md
```

需要技术文档或 Word 产物时，继续读取被选技能的 references 和工具流程。需要专利时保留旧的 `python tools/patent.py ...` 与 `oh-my-patent ...` 入口；总入口只是兼容调度器，不改变既有专利门禁。
