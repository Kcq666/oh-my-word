"""Checks integrity and numeric coverage, never pretends to prove prose entailment."""
from __future__ import annotations

import re
import math
from importlib.resources import files
from pathlib import Path

import yaml

from .common import finding, inside, read_json, sha256
from .models import (
    validate_draft_v1,
    validate_evidence_v1,
    validate_segments_v1,
    validate_source_index_v1,
)


def contract(mode):
    if mode not in {"technical-report", "design-spec"}:
        raise ValueError(f"Unsupported mode: {mode}")
    return yaml.safe_load(files("word_skills").joinpath(f"schemas/{mode}.yaml").read_text(encoding="utf-8"))


def numbers(text):
    # Numbers in identifiers are deliberately included: version/config claims need evidence too.
    return set(re.findall(r"\d+(?:[.,]\d+)*(?:%|％)?", text))


def block_text(block):
    if block.get("type") == "table":
        return "\n".join(" | ".join(str(c) for c in row) for row in [block.get("headers", [])] + block.get("rows", []))
    return block.get("text", "")


def validate(draft, case):
    case = Path(case)
    issues = []
    validate_draft_v1(draft)
    schema = contract(draft.get("mode"))
    if draft.get("schema_version") != 1 or not isinstance(draft.get("title"), str) or not draft["title"].strip():
        issues.append(finding("DRAFT", "schema_version=1 and a nonempty title are required"))
    source_index = validate_source_index_v1(read_json(case / "source-index.json"))
    ledger = validate_evidence_v1(read_json(case / "evidence.json"))
    sources = {}
    for source in source_index["sources"]:
        if source["id"] in sources:
            issues.append(finding("SOURCE_DUPLICATE", source["id"]))
        sources[source["id"]] = source
        for key, hash_key in [("snapshot", "sha256"), ("extracted", "extracted_sha256"), ("segments", "segments_sha256")]:
            path = inside(case, source[key])
            if not path.is_file() or sha256(path) != source[hash_key]:
                issues.append(finding("SOURCE_CHANGED", f"{source['id']} {key} no longer matches indexed content"))
        original = Path(source["original_path"])
        if original.is_file() and sha256(original) != source["sha256"]:
            issues.append(finding("LIVE_SOURCE_CHANGED", f"{source['id']} original changed; re-ingest and review"))
    claims = {}
    for claim in ledger.get("claims", []):
        cid = claim.get("id")
        if not cid or cid in claims:
            issues.append(finding("CLAIM_ID", "Missing or duplicate claim ID"))
            continue
        claims[cid] = claim
        if claim.get("status") != "verified":
            continue
        source = sources.get(claim.get("source_id"))
        if not source:
            issues.append(finding("CLAIM_SOURCE", f"{cid}: source not found"))
            continue
        segments = validate_segments_v1(read_json(inside(case, source["segments"])))
        selected = [s["text"] for s in segments if s["locator"] in claim.get("locators", [])]
        quote = claim.get("quote", "")
        if not quote.strip() or not selected or quote not in "\n".join(selected):
            issues.append(finding("QUOTE", f"{cid}: exact quote not found at specified locations"))
        if not claim.get("statement", "").strip() or not claim.get("verified_by") or not claim.get("verified_at"):
            issues.append(finding("CLAIM_REVIEW", f"{cid}: statement and verifier/time required"))
        if numbers(claim.get("statement", "")) - numbers(quote):
            issues.append(finding("CLAIM_NUMBER", f"{cid}: statement adds numeric values absent from quotation"))
    section_ids, block_ids = set(), set()
    prior_level = 0
    for section in draft.get("sections", []):
        sid = section.get("id")
        if not sid or sid in section_ids:
            issues.append(finding("SECTION_ID", "Missing or duplicate section ID"))
        section_ids.add(sid)
        level = section.get("level", 1)
        if type(level) is not int or level not in (1, 2, 3) or level > prior_level + 1:
            issues.append(finding("HEADING_LEVEL", f"{sid}: invalid/jumping level"))
        prior_level = level if type(level) is int else 1
        if not section.get("title", "").strip() or not section.get("blocks"):
            issues.append(finding("EMPTY_SECTION", f"{sid}: heading or content empty"))
        # Numeric factual headings require the same evidence coverage as body text.
        if numbers(section.get("title", "")):
            issues.append(finding("NUMERIC_HEADING", f"{sid}: put numeric claims in evidence-bound body blocks"))
        for block in section.get("blocks", []):
            bid = block.get("id")
            if not bid or bid in block_ids:
                issues.append(finding("BLOCK_ID", "Missing or duplicate block ID", location=sid))
            block_ids.add(bid)
            if block.get("type") not in {"paragraph", "table"}:
                issues.append(finding("BLOCK_TYPE", "Supported types: paragraph/table", location=bid))
                continue
            text = block_text(block)
            if not text.strip():
                issues.append(finding("EMPTY_BLOCK", "Empty body block", location=bid))
            if re.search(r"TODO|XXX|待补充|\{\{|\{%", text, re.I):
                issues.append(finding("PLACEHOLDER", "Visible placeholder remains", location=bid))
            intent = block.get("intent")
            if intent not in {"fact", "analysis", "gap"}:
                issues.append(finding("INTENT", "Block needs fact/analysis/gap intent", location=bid))
            refs = block.get("claim_ids", [])
            if intent == "fact" and not refs:
                issues.append(finding("UNSOURCED", "Factual block needs claim IDs", location=bid))
            supported = set()
            for cid in refs:
                claim = claims.get(cid)
                if not claim or claim.get("status") != "verified":
                    issues.append(finding("UNVERIFIED", f"{cid}: referenced claim is not verified", location=bid))
                else:
                    supported |= numbers(claim.get("statement", ""))
            extra = numbers(text) - supported
            if extra:
                issues.append(finding("UNSUPPORTED_NUMBER", f"Numeric tokens without verified claim: {sorted(extra)}", location=bid))
            if intent == "gap":
                issues.append(finding("DECLARED_GAP", text, "warning", bid))
            if block.get("type") == "table":
                columns = len(block.get("headers", []))
                if columns == 0 or not block.get("rows") or any(len(r) != columns for r in block.get("rows", [])):
                    issues.append(finding("TABLE_SHAPE", "Nonempty rectangular table required", location=bid))
                weights = block.get("widths", [1] * columns)
                if len(weights) != columns or any(type(w) not in (int, float) or not math.isfinite(w) or w <= 0 for w in weights):
                    issues.append(finding("TABLE_WIDTH", "Positive width weight required for every column", location=bid))
    for sid in schema["required_sections"]:
        if sid not in section_ids:
            issues.append(finding("MISSING_SECTION", f"Required section: {sid}"))
    # Titles are metadata, not a bypass for factual numeric claims.
    if numbers(draft.get("title", "")):
        issues.append(finding("NUMERIC_TITLE", "Place numeric claims in evidence-bound body text"))
    if not sources:
        issues.append(finding("NO_SOURCES", "No readable sources indexed"))
    return {"schema_version": 1, "passed": not any(i["severity"] == "error" for i in issues),
            "checks": "structure, source integrity, exact quotation, numeric coverage; semantic support requires review",
            "issues": issues}
