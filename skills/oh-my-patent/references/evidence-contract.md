# 证据契约 v1

使用 UTF-8 JSON。来源可来自代码、技术人员补充、摄入后的技术文档与实验记录；不能将模型推测包装成来源。来源路径相对账本，source_id 唯一；quote 是源文件真实逐字文本，locator 是节/行；SHA256 对文件原始字节计算。verified 由实际核验得出，机器不能证明来源本身真实。

```json
{
  "schema_version": 1,
  "sources": [{"id": "S1", "path": "technical.md", "sha256": "源文件SHA256"}],
  "facts": [{"id": "F1", "text": "根据历史近邻统计选择候选值", "status": "verified", "source_id": "S1", "locator": "第3节", "quote": "源文件真实逐字引文"}]
}
```

partial/unsupported 可以留在账本，但不能作为最终正文支持。将已知部分拆为新的 verified 条目。source 文本与引文不支持图片事实时，追加经技术人员核对的视图说明文本，并保留原图。

`review-init` 生成完整审查骨架：patent_type（审查的类型）、draft_sha256（输入稿原始字节）、evidence_sha256（账本+来源+图片）、reviewer、reviewed_at、checks、claim_support、design_support、findings、accepted_warnings。若修改内容，实际重新审查后重建哈希。不要只改哈希复用旧结论。

权项支持：每个实质特征分别填写。说明书引文可忽略空白和 Markdown 加粗，但不能用近义改写冒充逐字引用。

```json
{"claim": 1, "features": [
  {"text": "权1中实际片段", "description_quote": "说明书中实际片段", "fact_ids": ["F1"]}
]}
```

checks 的 id 列表由 CLI 生成，各项 status 为 pass/not_applicable，必须 evidence 说明具体依据（N/A 写原因）。findings：severity P0/P1/P2，status open/resolved/accepted，evidence 描述问题与处理；P0/P1 只能 resolved。warnings 用 `{ "code": "CLAIM-004", "reason": "具体单一性核对依据" }`，缺图不得接受。

外观设计用 design_support：`{"figure":1,"fact_ids":["F1"],"evidence":"真实视图与设计要点的核对说明"}`；claim_support 保持空数组。

程序可检测未知引用、缺项、无法匹配的引文、源文件变更和 stale review。它不能检查所有特征是否穷尽、引文是否语义充分或法律创造性；这些是 08 的实际审查职责。JSON 自报 pass 不构成权威认证。
