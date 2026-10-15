from copy import deepcopy

import pytest

from word_skills.common import sha256, write_json
from word_skills.ingest import ingest
from word_skills.proposal import proposal_template, validate_proposal, build


@pytest.fixture
def prepared(tmp_path):
    notice = tmp_path / "notice.txt"
    notice.write_text("国科金发计〔2026〕2号\n历史指南内容，供合约测试。\n", encoding="utf-8")
    facts = tmp_path / "facts.txt"
    facts.write_text("项目资料说明。\n预算金额 10 元。\n", encoding="utf-8")
    cv = tmp_path / "cv.txt"
    cv.write_text("张三：测试申请人资料。", encoding="utf-8")
    commitment = tmp_path / "commitment.txt"
    commitment.write_text("测试单位承诺。", encoding="utf-8")
    case = tmp_path / "case"
    index = ingest([notice, facts, cv, commitment], case)
    sources = index["sources"]
    write_json(case / "evidence.json", {"schema_version": 1, "claims": [
        {"id": "C1", "statement": "项目资料说明。", "source_id": "S002", "locators": ["L1"],
         "quote": "项目资料说明。", "status": "verified", "verified_by": "fixture", "verified_at": "2026-10-16"},
        {"id": "C2", "statement": "预算金额 10 元。", "source_id": "S002", "locators": ["L2"],
         "quote": "预算金额 10 元。", "status": "verified", "verified_by": "fixture", "verified_at": "2026-10-16"}]})
    proposal = proposal_template()
    proposal["profile"].update(notice_path=sources[0]["snapshot"], notice_sha256=sha256(case / sources[0]["snapshot"]))
    proposal["applicant"] = {"name": "张三", "entity_type": "个人", "contact": "内部测试"}
    proposal["personnel"] = [{"name": "张三", "role": "applicant", "document_path": sources[2]["snapshot"]}]
    for row in proposal["requirements"]:
        row.update(source_id="S001", locator="L1", quote="国科金发计〔2026〕2号", status="addressed")
    for section in proposal["sections"]:
        budget = section["id"] == "budget"
        section["blocks"] = [{"id": f"{section['id']}-body", "type": "paragraph", "intent": "fact",
                              "text": "预算金额 10 元。" if budget else "项目资料说明。",
                              "claim_ids": ["C2" if budget else "C1"]}]
    for row, source in zip(proposal["attachments"], sources[2:]):
        row.update(provided=True, path=source["snapshot"])
    proposal["budget"].update(items=[{"id": "b1", "category": "material", "amount": "10"}],
                              declared_total="10", category_totals={"material": "10"},
                              presentation_block_ids=["budget-body"])
    path = tmp_path / "proposal.json"
    write_json(path, proposal)
    return proposal, case, path


def codes(result):
    return {issue["code"] for issue in result["issues"]}


def test_historical_profile_needs_explicit_exception(prepared):
    value, case, _ = prepared
    assert "GUIDE_STALE" in codes(validate_proposal(value, base_dir=case))
    assert validate_proposal(value, base_dir=case, allow_expired=True)["passed"]


@pytest.mark.parametrize("mutation,code", [
    (lambda p: p["profile"].update(status="current"), "PROFILE_FROZEN"),
    (lambda p: p["profile"].update(notice_sha256="x"), "GUIDE_HASH"),
    (lambda p: p["requirements"].pop(), "REQUIREMENT_MISSING"),
    (lambda p: p["requirements"][0].update(status="pending"), "REQUIREMENT_UNRESOLVED"),
    (lambda p: p["personnel"].clear(), "PERSONNEL_MISSING"),
    (lambda p: p["attachments"][0].update(provided=False), "ATTACHMENT_MISSING"),
    (lambda p: p["budget"].update(declared_total="11"), "BUDGET_TOTAL"),
    (lambda p: p["budget"]["items"][0].update(amount="NaN"), "BUDGET_AMOUNT"),
    (lambda p: p["budget"]["items"][0].update(amount="1e999999999"), "BUDGET_AMOUNT"),
    (lambda p: p["requirements"][0].update(quote=None), "REQUIREMENT_QUOTE"),
    (lambda p: p["budget"].update(currency="USD"), "BUDGET_UNIT"),
])
def test_proposal_failure_paths(prepared, mutation, code):
    value, case, _ = prepared
    changed = deepcopy(value)
    mutation(changed)
    assert code in codes(validate_proposal(changed, base_dir=case, allow_expired=True))


def test_proposal_produces_shared_unreviewed_docx(prepared, tmp_path):
    _, case, path = prepared
    result = build(path, case, tmp_path / "delivery", allow_expired=True, no_preview=True)
    assert result["state"] == "draft"
    assert (tmp_path / "delivery/output.docx").is_file()


def test_guide_quote_must_match_selected_segment(prepared, tmp_path):
    value, case, path = prepared
    value["requirements"][0]["quote"] = "a fabricated guide requirement"
    write_json(path, value)
    result = build(path, case, tmp_path / "delivery", allow_expired=True, no_preview=True)
    assert result["state"] == "blocked"
    assert "GUIDE_QUOTE" in codes(result["validation"])


def test_business_input_change_after_validation_fails(prepared, tmp_path, monkeypatch):
    from word_skills import delivery
    from word_skills.common import read_json
    value, case, path = prepared
    original = delivery.build
    def changing_build(*args, **kwargs):
        result = original(*args, **kwargs)
        value["budget"]["declared_total"] = "999"
        write_json(path, value)
        return result
    monkeypatch.setattr(delivery, "build", changing_build)
    result = build(path, case, tmp_path / "delivery", allow_expired=True, no_preview=True)
    assert result["state"] == "failed"
    assert "BUSINESS_INPUT_CHANGED" in codes(read_json(tmp_path / "delivery/audit/validation.json"))


def test_reserved_business_mode_cannot_use_generic_build(prepared, tmp_path):
    from word_skills import delivery
    value, case, _ = prepared
    draft = tmp_path / "draft.json"
    write_json(draft, {"schema_version": 1, "mode": "proposal", "title": value["title"], "sections": value["sections"]})
    with pytest.raises(ValueError, match="dedicated business"):
        delivery.build(draft, case, tmp_path / "delivery", no_preview=True)
