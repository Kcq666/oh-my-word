# oh-my-word / word-skills

`word-skills` 是一个可安装的 Word Skills monorepo：它把中文技术文档制作、可追溯的 Word 交付和既有中国专利审阅稿工具放在同一套可验证的来源、渲染与交付边界中。

当前实现包括：

- `word-skills`：总入口、技能注册表和确定性路由；
- `oh-my-technology`：`technical-report` 与 `design-spec` 两种 JSON 中间稿模式；
- `word-document`：基本单节样式与受限 `docxtpl` 插槽模板；
- `oh-my-patent`：原有发明、实用新型、外观设计 CLI、六个领域模块和 final/handoff 门禁。

项目申报、软件著作权，以及需求、接口、测试、用户和运维五种技术文档模式已经登记为 `planned`，不会用空目录伪装成已实现能力。目标架构、依赖方向与阶段验收见 [docs/02-architecture.md](docs/02-architecture.md)、[docs/03-roadmap.md](docs/03-roadmap.md) 和 [registry/skills.yaml](registry/skills.yaml)。

## 安装

需要 Python 3.10+。基础安装包含专利和技术文档的结构检查、Word 生成与来源校验；读取 DOCX/PDF 材料和插槽模板使用可选依赖。

```powershell
python -m pip install -e ".[dev,ingest,templates]"
python -m word_skills skills list --json
python tools/check_word_skills.py
```

安装包不包含真实案卷、`outputs/`、本机证据、LibreOffice、Poppler 或字体。完整 monorepo 是受支持的 Skill 安装形态，不能只复制一个 `SKILL.md` 就声称共享资源已安装。

## 总入口与路由

```powershell
python -m word_skills route "请写一份技术报告" --json
python -m word_skills route "只调整 Word 页眉和页码" --json
python -m word_skills route "请准备项目申报书" --json
```

路由结果只声明登记状态。若命中 `planned`，需要补充材料或等待对应阶段实现；路由器不会自动写正文。

## 技术文档与 Word 交付

将 `skills/oh-my-technology/SKILL.md` 和 `skills/word-document/SKILL.md` 交给 Agent，阅读来源后填写 JSON 中间稿和证据账本，再运行：

```powershell
python -m word_skills ingest "项目材料路径" --case "case"
python -m word_skills template --mode technical-report --out "draft.json"
python -m word_skills lint draft.json --case case
python -m word_skills build draft.json --case case --out delivery --soffice "SOFFICE_EXE" --pdftoppm "PDFTOPPM_EXE"
python -m word_skills review-init delivery
# 实际核对正文和全部页图后，填写 delivery/audit/review.json
python -m word_skills finalize delivery
```

`reviewed` 只表示已记录的内容和版面复核，不表示事实真实性、正式提交、受理或授权。模板支持范围、证据契约和交付状态见 `skills/word-document/references/`。

## 专利兼容入口

规范入口位于 [skills/oh-my-patent/SKILL.md](skills/oh-my-patent/SKILL.md)。旧调用继续有效：

```powershell
python tools/patent.py template invention -o outputs/draft.md
python tools/patent.py lint outputs/draft.md
python tools/patent.py build outputs/draft.md -o outputs/review.docx --strict
python -m word_skills patent template invention -o outputs/draft.md
```

专利 Skill、prompts、references 和六个领域模块的规范路径是 `skills/oh-my-patent/`；旧的 Python 包、`tools/patent.py` 和 `oh-my-patent` 命令继续可用。专利门禁和原 Python 包没有被通用技术文档渲染器反向依赖。

## 验证

```powershell
python tools/check_word_skills.py
python tools/check_skills.py
python -m pytest tests -q
python tools/check_full_dependencies.py
```

`check_word_skills.py` 和 `check_skills.py` 只证明结构、路径和声明一致；测试证明确定性代码行为。真实写作质量、事实语义、全部 Word/WPS 版本和用户页面体验仍需按对应材料和环境独立复核。

`check_full_dependencies.py` 使用同一解释器执行 pytest 全部测试并记录依赖版本、测试数和跳过项；缺依赖、失败、skip、xfail 或 xpass 均使验收失败。报告保存在本地 `outputs/acceptance/`。

## 许可与来源

代码使用 MIT 许可。共享写作规则、依赖、固定来源和改编范围见 [THIRD_PARTY.md](THIRD_PARTY.md)。官方 Word 转 XML 工具只是专利交接路径的外部依赖，不随仓库发布，也不由本项目自动提交文件。
