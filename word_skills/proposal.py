"""Guide-bound proposal contracts and deterministic budget checks.

The module validates the mechanical parts of a proposal case.  It does not
choose an agency, invent applicant facts, or submit anything to an agency.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from datetime import date
from importlib.resources import files
from pathlib import Path
import json
import re
from typing import Any

import yaml

from .common import finding, read_json, write_json


def _decimal(value: Any, location: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{location} must be a non-negative decimal")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{location} must be a non-negative decimal") from exc
    if not result.is_finite() or result < 0:
        raise ValueError(f"{location} must be a non-negative decimal")
    if len(result.as_tuple().digits) > 28 or not -6 <= result.as_tuple().exponent <= 18 or result.adjusted() > 18:
        raise ValueError(f"{location} exceeds supported monetary precision/range")
    return result


def proposal_profile(name: str = "nsfc-2026-general") -> dict[str, Any]:
    """Load a frozen profile; live notices must be rechecked before use."""
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError("profile name must be a safe identifier")
    try:
        path = files("word_skills").joinpath(f"data/proposal-profiles/{name}.yaml")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"unknown proposal profile: {name}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("proposal profile requires schema_version=1")
    if data.get("id") != name:
        raise ValueError("proposal profile id does not match filename")
    return data


def proposal_template(profile: str = "nsfc-2026-general") -> dict[str, Any]:
    config = proposal_profile(profile)
    return {
        "schema_version": 1,
        "case_id": "replace-with-case-id",
        "profile": {
            "id": config["id"],
            "agency": config["agency"],
            "program": config["program"],
            "year": config["year"],
            "notice_id": config["notice_id"],
            "template_version": config["template_version"],
            "source_url": config["source_url"],
            "retrieved_at": config["retrieved_at"],
            "status": config["status"],
            "budget_mode": config["budget_mode"],
            "notice_path": "",
            "notice_sha256": "",
        },
        "applicant": {"name": "", "entity_type": "", "contact": ""},
        "requirements": [
            {"id": item["id"], "text": item["text"], "source_id": "", "locator": "", "quote": "",
             "required": True, "target_sections": [item["section"]], "status": "pending"}
            for item in config["requirements"]
        ],
        "sections": [
            {"id": item["id"], "title": item["title"], "kind": item["kind"], "blocks": [],
             "requirement_ids": [r["id"] for r in config["requirements"] if r["section"] == item["id"]]}
            for item in config["sections"]
        ],
        "budget": {"currency": "CNY", "items": [], "declared_total": "0", "category_totals": {}, "ratio_rules": [], "presentation_block_ids": []},
        "attachments": [
            {"id": item["id"], "name": item["name"], "required": item["required"], "provided": False, "path": ""}
            for item in config.get("attachments", [])
        ],
        "ai_use": {"used": False, "human_verified": False, "disclosure": ""},
        "personnel": [{"name": "", "role": "applicant", "document_path": ""}],
        "title": "项目申请书",
        "status": "draft",
    }


def validate_budget(budget: Any) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    if not isinstance(budget, dict):
        return [finding("BUDGET", "budget must be an object")]
    items = budget.get("items", [])
    if not isinstance(items, list):
        return [finding("BUDGET_ITEMS", "budget.items must be an array")]
    if not items:
        issues.append(finding("BUDGET_ITEMS", "budget.items must contain the planned costs"))
    seen: set[str] = set()
    total = Decimal("0")
    categories: dict[str, Decimal] = {}
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            issues.append(finding("BUDGET_ITEM", f"items[{i}] must be an object"))
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id or item_id in seen:
            issues.append(finding("BUDGET_ID", f"items[{i}] needs a unique id"))
        else:
            seen.add(item_id)
        try:
            amount = _decimal(item.get("amount"), f"items[{i}].amount")
        except ValueError as exc:
            issues.append(finding("BUDGET_AMOUNT", str(exc)))
            continue
        total += amount
        category = item.get("category", "uncategorized")
        if not isinstance(category, str) or not category.strip():
            issues.append(finding("BUDGET_CATEGORY", f"items[{i}].category is required"))
        else:
            categories[category] = categories.get(category, Decimal("0")) + amount
    declared: Decimal | None = None
    try:
        declared = _decimal(budget.get("declared_total"), "declared_total")
        if total != declared:
            issues.append(finding("BUDGET_TOTAL", f"line items total {total} != declared_total {declared}"))
    except ValueError as exc:
        issues.append(finding("BUDGET_TOTAL", str(exc)))
    declared_categories = budget.get("category_totals", {})
    if not isinstance(declared_categories, dict):
        issues.append(finding("BUDGET_CATEGORIES", "category_totals must be an object"))
    else:
        for category, amount in declared_categories.items():
            try:
                if categories.get(category, Decimal("0")) != _decimal(amount, f"category_totals.{category}"):
                    issues.append(finding("BUDGET_CATEGORY_TOTAL", f"category total mismatch: {category}"))
            except ValueError as exc:
                issues.append(finding("BUDGET_CATEGORY_TOTAL", str(exc)))
        if set(declared_categories) != set(categories):
            issues.append(finding("BUDGET_CATEGORIES", "category_totals must cover exactly the item categories"))
    rules = budget.get("ratio_rules", [])
    if not isinstance(rules, list):
        return issues + [finding("BUDGET_RATIO", "ratio_rules must be an array")]
    for rule in rules:
        if not isinstance(rule, dict) or not isinstance(rule.get("category"), str):
            issues.append(finding("BUDGET_RATIO", "ratio rule needs category and max_percent"))
            continue
        try:
            maximum = _decimal(rule.get("max_percent"), f"ratio_rules.{rule['category']}.max_percent")
            if maximum > 100:
                issues.append(finding("BUDGET_RATIO", "max_percent cannot exceed 100"))
            if declared and categories.get(rule["category"], Decimal("0")) * 100 / declared > maximum:
                issues.append(finding("BUDGET_RATIO", f"category exceeds max_percent: {rule['category']}"))
        except (ValueError, InvalidOperation) as exc:
            issues.append(finding("BUDGET_RATIO", str(exc)))
    return issues


def validate_proposal(value: Any, *, allow_expired: bool = False, base_dir: str | Path | None = None) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        return {"schema_version": 1, "passed": False, "issues": [finding("SCHEMA", "proposal requires schema_version=1")]}
    profile = value.get("profile")
    if not isinstance(profile, dict):
        issues.append(finding("PROFILE", "profile is required"))
        profile = {}
    for field in ("agency", "program", "year", "notice_id", "template_version", "source_url", "retrieved_at", "status", "budget_mode"):
        if field not in profile or profile[field] in (None, ""):
            issues.append(finding("PROFILE_FIELD", f"profile.{field} is required"))
    if not str(profile.get("source_url", "")).startswith("https://"):
        issues.append(finding("PROFILE_SOURCE", "profile.source_url must be an HTTPS official notice URL"))
    if profile.get("status") != "current" and not allow_expired:
        issues.append(finding("GUIDE_STALE", "profile is not marked current; recheck the official notice before use"))
    applicant = value.get("applicant")
    if not isinstance(applicant, dict) or not str(applicant.get("name", "")).strip() or not str(applicant.get("entity_type", "")).strip():
        issues.append(finding("APPLICANT", "applicant name and entity_type are required; do not infer ownership"))
    requirements = value.get("requirements")
    sections = value.get("sections")
    if not isinstance(requirements, list) or not isinstance(sections, list):
        issues.append(finding("TRACE", "requirements and sections must be arrays"))
        requirements, sections = [], []
    req_ids = {r["id"] for r in requirements if isinstance(r, dict) and isinstance(r.get("id"), str) and r["id"]}
    section_ids = {s["id"] for s in sections if isinstance(s, dict) and isinstance(s.get("id"), str) and s["id"]}
    if len(req_ids) != len(requirements) or None in req_ids:
        issues.append(finding("REQUIREMENT_ID", "requirements need unique nonempty ids"))
    if len(section_ids) != len(sections) or None in section_ids:
        issues.append(finding("SECTION_ID", "sections need unique nonempty ids"))
    for req in requirements:
        if not isinstance(req, dict):
            issues.append(finding("REQUIREMENT", "requirement must be an object"))
            continue
        if not str(req.get("text", "")).strip() or not str(req.get("source_id", "")).strip() or not str(req.get("locator", "")).strip():
            issues.append(finding("REQUIREMENT_SOURCE", f"{req.get('id', '<unknown>')} needs source_id and locator"))
        if not _text(req.get("quote")):
            issues.append(finding("REQUIREMENT_QUOTE", f"{req.get('id', '<unknown>')} needs the exact source quote"))
        targets = req.get("target_sections", [])
        if not isinstance(targets, list) or not targets or any(not isinstance(target, str) or target not in section_ids for target in targets):
            issues.append(finding("REQUIREMENT_TARGET", f"{req.get('id', '<unknown>')} targets an unknown section"))
        if req.get("status") not in ("pending", "addressed", "not-applicable"):
            issues.append(finding("REQUIREMENT_STATUS", f"{req.get('id')} has an invalid status"))
        elif req.get("required") and req.get("status") != "addressed":
            issues.append(finding("REQUIREMENT_UNRESOLVED", f"required requirement is not addressed: {req.get('id')}"))
        if req.get("status") == "addressed" and isinstance(targets, list):
            linked = any(isinstance(section, dict) and section.get("id") in targets and isinstance(section.get("requirement_ids"), list) and req.get("id") in section["requirement_ids"] for section in sections)
            if not linked:
                issues.append(finding("REQUIREMENT_TRACE", f"{req.get('id')} is not linked back from a target section"))
    for section in sections:
        if not isinstance(section, dict):
            continue
        refs = section.get("requirement_ids", [])
        if not isinstance(refs, list):
            issues.append(finding("TRACE", f"section {section.get('id')} requirement_ids must be an array"))
            continue
        for req_id in refs:
            if not isinstance(req_id, str) or req_id not in req_ids:
                issues.append(finding("TRACE", f"section {section.get('id')} references unknown requirement {req_id}"))
    attachments = value.get("attachments", [])
    if not isinstance(attachments, list):
        issues.append(finding("ATTACHMENTS", "attachments must be an array"))
    else:
        for item in attachments:
            if not isinstance(item, dict) or not item.get("id") or not item.get("name"):
                issues.append(finding("ATTACHMENT", "attachment needs id and name"))
            elif item.get("required") and not item.get("provided"):
                issues.append(finding("ATTACHMENT_MISSING", f"required attachment is missing: {item['name']}"))
            elif item.get("provided") and not str(item.get("path", "")).strip():
                issues.append(finding("ATTACHMENT_PATH", f"provided attachment needs a path: {item['name']}"))
            elif item.get("provided") and base_dir is not None:
                base = Path(base_dir).expanduser().resolve()
                selected = (base / str(item["path"])).resolve()
                if not selected.is_relative_to(base) or not selected.is_file():
                    issues.append(finding("ATTACHMENT_PATH", f"attachment must be an existing file inside the case directory: {item['name']}"))
    issues.extend(validate_budget(value.get("budget", {})))
    ai_use = value.get("ai_use", {})
    if not isinstance(ai_use, dict):
        issues.append(finding("AI_DISCLOSURE", "ai_use must be an object"))
        ai_use = {}
    if ai_use.get("used") and (not ai_use.get("human_verified") or not str(ai_use.get("disclosure", "")).strip()):
        issues.append(finding("AI_DISCLOSURE", "AI-assisted proposal content needs human verification and disclosure"))
    issues.extend(_completeness(value, base_dir, allow_expired))
    return {"schema_version": 1, "passed": not any(i["severity"] == "error" for i in issues),
            "checks": "profile freshness, requirement-to-section trace, attachment completeness, budget arithmetic, AI disclosure",
            "issues": issues}


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _completeness(value, base_dir, allow_expired):
    """The template cannot be made valid by deleting unmet requirements."""
    issues = []
    profile = value.get("profile") if isinstance(value.get("profile"), dict) else {}
    for key in ("agency", "program", "notice_id", "template_version", "source_url", "budget_mode"):
        if not _text(profile.get(key)):
            issues.append(finding("PROFILE_FIELD", f"profile.{key} needs nonempty text"))
    try:
        retrieved = date.fromisoformat(str(profile.get("retrieved_at")))
        if retrieved > date.today():
            raise ValueError("future retrieval date")
    except ValueError:
        issues.append(finding("PROFILE_DATE", "retrieved_at must be an actual retrieval date"))
    config = None
    if profile.get("id") == "nsfc-2026-general":
        config = proposal_profile()
        for key in ("agency", "program", "year", "notice_id", "template_version", "source_url", "status", "budget_mode"):
            if profile.get(key) != config[key]:
                issues.append(finding("PROFILE_FROZEN", f"frozen historical profile field changed: {key}"))
        if allow_expired:
            issues.append(finding("HISTORICAL_ONLY", "Historical profile: not a current submission channel", "warning"))
    else:
        if not _text(profile.get("verified_by")):
            issues.append(finding("GUIDE_REVIEW", "custom guide needs verified_by and valid_until"))
        try:
            until = date.fromisoformat(str(profile.get("valid_until")))
            verified = date.fromisoformat(str(profile.get("verified_at")))
            if verified > date.today() or verified > until or until < date.today():
                raise ValueError("stale verification")
        except ValueError:
            issues.append(finding("GUIDE_STALE", "custom guide needs current verification and validity dates"))
    def material(path, code):
        if not _text(path):
            issues.append(finding(code, "a real case-relative material path is required"))
        elif base_dir is not None:
            from .common import inside
            try:
                candidate = inside(base_dir, path)
                if Path(path).is_absolute() or not candidate.is_file():
                    raise ValueError("missing or absolute material")
                return candidate
            except (ValueError, OSError):
                issues.append(finding(code, "material must exist inside the case directory"))
        return None
    notice = material(profile.get("notice_path"), "GUIDE_MISSING")
    from .common import sha256
    if not _text(profile.get("notice_sha256")) or (notice and sha256(notice) != profile["notice_sha256"]):
        issues.append(finding("GUIDE_HASH", "official notice snapshot hash is missing or changed"))
    if notice:
        try:
            from .ingest import extract
            if str(profile.get("notice_id")) not in extract(notice)[0]:
                issues.append(finding("GUIDE_IDENTITY", "notice snapshot does not contain the stated notice identifier"))
        except (OSError, ValueError) as exc:
            issues.append(finding("GUIDE_IDENTITY", f"notice snapshot could not be read: {exc}"))
    requirements = value.get("requirements") if isinstance(value.get("requirements"), list) else []
    sections = value.get("sections") if isinstance(value.get("sections"), list) else []
    attachments = value.get("attachments") if isinstance(value.get("attachments"), list) else []
    if not requirements or not sections:
        issues.append(finding("TRACE_EMPTY", "requirements and sections cannot be empty"))
    if config:
        for collection, expected, code in ((requirements, config["requirements"], "REQUIREMENT_MISSING"), (sections, config["sections"], "SECTION_MISSING"), (attachments, config["attachments"], "ATTACHMENT_MISSING")):
            present = {r.get("id"): r for r in collection if isinstance(r, dict) and isinstance(r.get("id"), str)}
            for item in expected:
                if item["id"] not in present:
                    issues.append(finding(code, f"profile entry removed: {item['id']}"))
                elif "required" in item and item["required"] and present[item["id"]].get("required") is not True:
                    issues.append(finding(code, f"required entry disabled: {item['id']}"))
            if code == "REQUIREMENT_MISSING":
                for item in expected:
                    row = present.get(item["id"], {})
                    if row.get("required") is not True or row.get("text") != item["text"] or row.get("target_sections") != [item["section"]]:
                        issues.append(finding(code, f"frozen requirement changed: {item['id']}"))
    for section in sections:
        if not isinstance(section, dict) or not _text(section.get("title")) or not isinstance(section.get("blocks"), list) or not section["blocks"]:
            issues.append(finding("SECTION_CONTENT", "every proposal section needs authored blocks"))
    budget = value.get("budget") if isinstance(value.get("budget"), dict) else {}
    shown = budget.get("presentation_block_ids")
    all_blocks = {b.get("id"): b for s in sections if isinstance(s, dict) for b in s.get("blocks", []) if isinstance(b, dict)}
    if not isinstance(shown, list) or not shown or any(not isinstance(bid, str) or bid not in all_blocks for bid in shown):
        issues.append(finding("BUDGET_PRESENTATION", "budget must point to rendered budget blocks"))
    else:
        from .evidence import block_text
        rendered = "\n".join(block_text(all_blocks[bid]) for bid in shown)
        amounts = [item.get("amount") for item in budget.get("items", []) if isinstance(item, dict)] + [budget.get("declared_total")]
        if any(not isinstance(amount, (int, float, str)) or str(amount) not in rendered for amount in amounts):
            issues.append(finding("BUDGET_PRESENTATION", "all budget amounts and declared total must appear in rendered blocks"))
    applicant = value.get("applicant") if isinstance(value.get("applicant"), dict) else {}
    if not _text(applicant.get("name")) or not _text(applicant.get("entity_type")):
        issues.append(finding("APPLICANT", "applicant facts cannot be empty or null"))
    people = value.get("personnel")
    if not isinstance(people, list) or not people:
        issues.append(finding("PERSONNEL_MISSING", "personnel materials must include the applicant"))
    else:
        for person in people:
            if not isinstance(person, dict) or not _text(person.get("name")) or not _text(person.get("role")):
                issues.append(finding("PERSONNEL_MISSING", "each person needs name, role and source material"))
            else:
                material(person.get("document_path"), "PERSONNEL_MISSING")
        if not any(isinstance(p, dict) and p.get("role") == "applicant" and p.get("name") == applicant.get("name") for p in people):
            issues.append(finding("PERSONNEL_MISSING", "applicant must match its personnel record"))
    for item in attachments:
        if isinstance(item, dict):
            if type(item.get("required")) is not bool or type(item.get("provided")) is not bool:
                issues.append(finding("ATTACHMENT", "required/provided must be booleans"))
            if item.get("provided") is True:
                material(item.get("path"), "ATTACHMENT_PATH")
    if budget.get("currency") != "CNY":
        issues.append(finding("BUDGET_UNIT", "budget amounts use CNY yuan; convert other units explicitly"))
    if isinstance(value.get("ai_use"), dict) and any(type(value["ai_use"].get(k)) is not bool for k in ("used", "human_verified")):
        issues.append(finding("AI_DISCLOSURE", "AI flags must be booleans"))
    return issues


def lint(path: str | Path, *, allow_expired: bool = False, case: str | Path | None = None) -> dict[str, Any]:
    case_path = Path(path).expanduser().resolve()
    return validate_proposal(read_json(case_path), allow_expired=allow_expired,
                             base_dir=Path(case).expanduser().resolve() if case else case_path.parent)


def build(path: str | Path, case: str | Path, out: str | Path, *, allow_expired: bool = False,
          soffice: str | None = None, pdftoppm: str | None = None, no_preview: bool = False) -> dict[str, Any]:
    """Validate business inputs, then use the ordinary source-bound production gate."""
    from tempfile import TemporaryDirectory
    from .common import inside
    from .delivery import build as shared_build
    from .business import bind_business_audit
    proposal_path, case_path = Path(path).resolve(), Path(case).resolve()
    source_bytes = proposal_path.read_bytes()
    value = json.loads(source_bytes.decode("utf-8-sig"))
    result = validate_proposal(value, allow_expired=allow_expired, base_dir=case_path)
    if not result["passed"]:
        return {"state": "blocked", "validation": result}
    index = read_json(case_path / "source-index.json")
    sources = {s["id"]: s for s in index["sources"]}
    files = [value["profile"]["notice_path"]]
    files += [p["document_path"] for p in value["personnel"]]
    files += [a["path"] for a in value["attachments"] if a.get("provided")]
    snapshots = {s["snapshot"] for s in sources.values()}
    if any(file not in snapshots for file in files):
        return {"state": "blocked", "validation": {"passed": False, "issues": [finding("MATERIAL_NOT_INGESTED", "all notice, personnel and attachment paths must be indexed source snapshots")]}}
    guide_id = next((sid for sid, item in sources.items() if item["snapshot"] == value["profile"]["notice_path"]), None)
    for req in value["requirements"]:
        source = sources.get(req["source_id"])
        if not source or req["source_id"] != guide_id:
            return {"state": "blocked", "validation": {"passed": False, "issues": [finding("GUIDE_TRACE", "requirement source_id missing from case")]}}
        segments = read_json(inside(case_path, source["segments"]))
        matching = [segment for segment in segments if segment["locator"] == req["locator"]]
        if not matching:
            return {"state": "blocked", "validation": {"passed": False, "issues": [finding("GUIDE_TRACE", "requirement locator missing from indexed source")]}}
        if not any(req["quote"] in segment["text"] for segment in matching):
            return {"state": "blocked", "validation": {"passed": False, "issues": [finding("GUIDE_QUOTE", f"requirement quote is absent at {req['locator']}")]}}
    draft = {"schema_version": 1, "mode": "proposal", "title": value["title"],
             "sections": [{k: s[k] for k in ("id", "title", "blocks")} for s in value["sections"]]}
    with TemporaryDirectory(prefix="word-proposal-") as directory:
        draft_path = Path(directory) / "draft.json"
        write_json(draft_path, draft)
        built = shared_build(draft_path, case_path, out, soffice=soffice, pdftoppm=pdftoppm, no_preview=no_preview, business_gate="proposal")
    if built["state"] in ("business-pending", "draft"):
        return bind_business_audit(out, "proposal", proposal_path, result, source_bytes=source_bytes)
    return built


def write_template(path: str | Path, profile: str = "nsfc-2026-general") -> dict[str, Any]:
    path = Path(path)
    if path.exists():
        raise ValueError("proposal template already exists")
    value = proposal_template(profile)
    write_json(path, value)
    return {"path": str(path), "profile": profile, "state": "scaffold-not-deliverable"}
