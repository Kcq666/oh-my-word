"""审阅交付门禁。检查证据契约，不把模型的声明当成法律/技术认证。"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from docx.image.image import Image

from .report import Issue, Severity

CHECKS = (
    "fact_boundary", "claim_support", "parameter_consistency",
    "optional_steps", "quantity_constraints", "dimensions",
    "enabled_states", "experiment_provenance", "sufficiency",
    "prior_art", "patent_type", "ai_disclosure", "ethics",
)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _norm(text):
    return re.sub(r"\s|\*\*", "", text)


def _contains(quote, body):
    return _text(quote) and bool(_norm(quote)) and _norm(quote) in _norm(body)


def _coverage_text(text):
    # 忽略排版及句读，保留数字、小数点、运算符和选择性措辞。
    return re.sub(r"[，,；;。：:、]", "", _norm(text))


def _uncovered(body, quotes):
    """按真实连续片段标记覆盖；不能靠逐字拼凑越过遗漏。"""
    body = _coverage_text(body)
    covered = [False] * len(body)
    for quote in quotes:
        if not _text(quote):
            continue
        fragment = _coverage_text(quote)
        if not fragment:
            continue
        for match in re.finditer(re.escape(fragment), body):
            covered[match.start():match.end()] = [True] * len(fragment)
    gaps = ''.join(char if not covered[i] else '\n' for i, char in enumerate(body))
    return [gap for gap in gaps.splitlines() if gap]


def _claim_scope(claim, title, text=None):
    """排除主题/引用开头和固定引导语，保留前序部分的技术限定。

    这是保守的文字覆盖检查，不是法律上的特征分解或语义证明。
    无法安全剥离的开头仍需在支持记录中覆盖。
    """
    text = (claim.text if text is None else text).strip().rstrip('。.')
    first = re.split(r'[，,]', text, maxsplit=1)
    if len(first) == 2:
        header = first[0]
        subject = re.sub(r'^.*?所述的?', '', header) if not claim.independent else header
        subject = re.sub(r'^一种', '', _norm(subject))
        title = re.sub(r'^一种', '', _norm(title))
        if subject == title and not re.search(r'包括|包含|具有|设置|连接|组成|构成|含有', header):
            text = first[1]
    text = re.sub(r'其特征在于\s*[，,:：]?', '', text)
    return re.sub(r'^\s*包括\s*[:：]', '', text).strip()


def description(draft):
    return draft.description_text()


def evidence_digest(facts_path, draft):
    """绑定账本原始字节、来源当前字节与附图当前字节。"""
    path = Path(facts_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("sources"), list) or not data["sources"]:
        raise ValueError("账本必须有非空 sources 数组")
    entries = [("facts", sha256(path))]
    for source in data["sources"]:
        if not isinstance(source, dict) or not _text(source.get("id")) or not _text(source.get("path")):
            raise ValueError("每个来源需要非空 id 和 path")
        p = (path.parent / source["path"]).resolve()
        entries.append(("source:" + source["id"], sha256(p)))
    for drawing in draft.drawings:
        if drawing.path:
            entries.append(("figure:" + str(drawing.number), sha256(drawing.path)))
    return hashlib.sha256(json.dumps(entries, ensure_ascii=False).encode()).hexdigest()


def review_skeleton(draft_path, facts_path, draft):
    return {
        "schema_version": 1,
        "patent_type": draft.patent_type.value,
        "draft_sha256": sha256(draft_path),
        "evidence_sha256": evidence_digest(facts_path, draft),
        "reviewer": "", "reviewed_at": "",
        "checks": [{"id": x, "status": "pending", "evidence": ""} for x in CHECKS],
        "claim_support": [{"claim": c.number, "features": []} for c in draft.claims],
        "design_support": [],
        "findings": [], "accepted_warnings": [],
    }


def final_issues(draft_path, draft, lint_report, facts_path=None, review_path=None):
    issues = list(lint_report.errors)

    def fail(code, message):
        issues.append(Issue(Severity.ERROR, code, message, "审阅交付门禁"))

    # final 不可由 --force 绕过；图片需实际可解码，而非仅路径存在。
    for drawing in draft.drawings:
        if not drawing.path:
            fail("FINAL-DRAW", f"图{drawing.number}未登记图件。")
        else:
            try:
                Image.from_file(str(drawing.path))
            except Exception as exc:
                fail("FINAL-DRAW", f"图{drawing.number}不可读取：{exc}")
    if draft.patent_type.has_claims and draft.drawings:
        if sum(d.is_abstract for d in draft.drawings) != 1:
            fail("FINAL-ABSTRACT", "有说明书附图时必须明确指定一幅摘要附图。")
    raw = Path(draft_path).read_text(encoding="utf-8")
    if re.search(r"待补充|待填写|待确认|TODO|TBD|⟪公式|\（图\d+缺失", raw, re.I):
        fail("FINAL-PLACEHOLDER", "稿件仍有占位符或未恢复的公式。")
    if re.search(r"\\(?:frac|sum|sqrt|begin|end|left|right|int)\b|\$\$|\\\[", raw):
        fail("FINAL-MATH", "含未渲染 LaTeX；本版本不提供复杂公式排版。先按原式核对并在受支持编辑路径恢复，不能交付原始语法。")
    if not facts_path or not review_path:
        fail("FINAL-EVIDENCE", "--final 需要 --facts 技术事实账本和 --review 内容审查。")
        return issues
    try:
        facts_file = Path(facts_path)
        facts = json.loads(facts_file.read_text(encoding="utf-8"))
        review = json.loads(Path(review_path).read_text(encoding="utf-8"))
        if not isinstance(facts, dict) or not isinstance(review, dict):
            raise ValueError("账本和审查必须是 JSON 对象")
        if facts.get("schema_version") != 1 or review.get("schema_version") != 1:
            raise ValueError("不支持的 schema_version")
        for key in ("sources", "facts"):
            if not isinstance(facts.get(key), list) or not facts[key]:
                raise ValueError(f"事实账本必须有非空 {key} 数组")
        for key in ("checks", "claim_support", "findings", "accepted_warnings", "design_support"):
            if not isinstance(review.get(key), list):
                raise ValueError(f"审查必须有 {key} 数组")
        if review.get("patent_type") != draft.patent_type.value:
            fail("FINAL-STALE", "专利类型与内容审查不一致。")
        if review.get("draft_sha256") != sha256(draft_path):
            fail("FINAL-STALE", "稿件已变更，内容审查失效。")
        if review.get("evidence_sha256") != evidence_digest(facts_file, draft):
            fail("FINAL-STALE", "账本、来源或附图已变更，内容审查失效。")
        if not _text(review.get("reviewer")) or not _text(review.get("reviewed_at")):
            fail("FINAL-REVIEW", "缺少审查人或审查日期。")

        source_text = {}
        for source in facts["sources"]:
            sid = source["id"]
            if not _text(sid) or sid in source_text:
                raise ValueError("来源 ID 为空或重复")
            p = (facts_file.parent / source["path"]).resolve()
            if source.get("sha256") != sha256(p):
                fail("FINAL-SOURCE", f"来源 {sid} 与登记 SHA256 不一致。")
            source_text[sid] = p.read_text(encoding="utf-8")

        verified = {}
        for fact in facts["facts"]:
            fid = fact["id"]
            if not _text(fid) or fid in verified:
                raise ValueError("事实 ID 为空或重复")
            # 未使用的 unresolved 事实允许留在账本中；绝不能进入正文支持关系。
            verified[fid] = fact
            if fact.get("status") not in ("verified", "partial", "unsupported"):
                fail("FINAL-FACT", f"事实 {fid} 状态无效。")
            if not _text(fact.get("text")):
                fail("FINAL-FACT", f"事实 {fid} 缺少描述。")
            if fact.get("status") == "verified":
                if not _text(fact.get("locator")) or not (_text(fact.get("quote")) and bool(_norm(fact["quote"])) and fact["quote"] in source_text.get(fact.get("source_id"), "")):
                    fail("FINAL-FACT", f"事实 {fid} 缺少来源位置或逐字引文支持。")

        def supports(item, body):
            ids = item.get("fact_ids")
            if not isinstance(ids, list) or not ids or any(not isinstance(x, str) for x in ids):
                fail("FINAL-SUPPORT", "支持关系缺少有效 fact_ids。")
                return
            if any(x not in verified or verified[x].get("status") != "verified" for x in ids):
                fail("FINAL-SUPPORT", "支持关系引用未知或未确认事实。")
                return
            if not _contains(item.get("description_quote"), body):
                fail("FINAL-SUPPORT", "支持引文不在说明书中。")

            feature = item.get("text", "")
            quotes = [verified[x].get("quote", "") for x in ids]
            # 直接文字支持保持v1兼容；不同表述或综合概括须有逐事实映射。
            related = all(_contains(feature, q) or _contains(q, feature) for q in quotes)
            source_covered = any(_contains(feature, q) for q in quotes) or not _uncovered(feature, quotes)
            if related and source_covered and _contains(feature, item.get("description_quote", "")):
                return
            links = item.get("fact_links", [])
            linked = set()
            valid = isinstance(links, list) and bool(links) and _text(item.get("support_basis"))
            if isinstance(links, list):
                for link in links:
                    if not isinstance(link, dict):
                        valid = False
                        continue
                    fid = link.get("fact_id")
                    if (not isinstance(fid, str) or fid not in ids or fid in linked
                            or not _text(link.get("basis"))
                            or not _contains(link.get("source_quote"), verified.get(fid, {}).get("quote", ""))):
                        valid = False
                    else:
                        linked.add(fid)
            if not valid or linked != set(ids):
                fail("FINAL-SUPPORT", "特征与说明书/来源缺少直接文字对应；须逐事实填写 fact_links 和 support_basis 并实际复核，不能仅引用 verified ID。")

        by_number = {c.number: c for c in draft.claims}
        seen = set()
        for row in review["claim_support"]:
            number = row["claim"]
            if number not in by_number or number in seen:
                fail("FINAL-CLAIM", "存在重复或未知权项支持关系。")
                continue
            seen.add(number)
            features = row.get("features", [])
            if not isinstance(features, list) or not features:
                fail("FINAL-CLAIM", f"权{number}必须逐特征给出支持关系。")
                continue
            for feature in features:
                if not _contains(feature.get("text"), by_number[number].text):
                    fail("FINAL-CLAIM", f"权{number}的特征引文不在该权项。")
                supports(feature, description(draft))
            gaps = _uncovered(_claim_scope(by_number[number], draft.title),
                              [_claim_scope(by_number[number], draft.title, x.get("text", "")) for x in features])
            if gaps:
                fail("FINAL-COVERAGE", f"权{number}存在未被特征支持记录覆盖的正文：{' / '.join(gaps)[:160]}。")
        if seen != set(by_number):
            fail("FINAL-CLAIM", "权项支持关系不完整。")
        if not draft.patent_type.has_claims:
            if not review["design_support"]:
                fail("FINAL-DESIGN", "外观设计必须给出设计要点与真实视图的支持关系。")
            for row in review["design_support"]:
                if row.get("figure") not in {d.number for d in draft.drawings}:
                    fail("FINAL-DESIGN", "设计支持关系引用未知视图。")
                if not _text(row.get("evidence")) or not row.get("fact_ids") or any(x not in verified or verified[x].get("status") != "verified" for x in row["fact_ids"]):
                    fail("FINAL-DESIGN", "设计支持关系缺少已确认事实或审查说明。")
        checks = {}
        for check in review["checks"]:
            cid = check["id"]
            if cid not in CHECKS or cid in checks:
                raise ValueError("审查检查项未知或重复")
            checks[cid] = check
        for cid in CHECKS:
            check = checks.get(cid, {})
            if check.get("status") not in ("pass", "not_applicable") or not _text(check.get("evidence")):
                fail("FINAL-CHECK", f"检查 {cid} 未完成或未给依据。")
        for finding in review["findings"]:
            if finding.get("severity") not in ("P0", "P1", "P2") or finding.get("status") not in ("open", "resolved", "accepted") or not _text(finding.get("evidence")):
                raise ValueError("finding 缺少有效严重度、状态或依据")
            if finding["severity"] in ("P0", "P1") and finding["status"] != "resolved":
                fail("FINAL-FINDING", "存在未解决的 P0/P1 内容问题。")
            if finding["status"] == "open":
                fail("FINAL-FINDING", "存在未闭合内容问题。")
        acknowledgements = {x["code"]: x for x in review["accepted_warnings"]}
        for warning in lint_report.warnings:
            accepted = acknowledgements.get(warning.code, {})
            if warning.code.startswith("DRAW-") or not _text(accepted.get("reason")):
                fail("FINAL-WARNING", f"警告 {warning.code} 尚未复核。")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        fail("FINAL-SCHEMA", f"证据包不可读取或结构无效：{exc}")
    return issues
