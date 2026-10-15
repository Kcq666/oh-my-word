"""Each new document mode must fail on its own material contract."""
from pathlib import Path

import pytest

from word_skills.common import write_json
from word_skills.evidence import contract, validate
from word_skills.ingest import ingest
from word_skills.technology import RECORDS


@pytest.fixture
def case(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("功能、请求、响应和执行记录均由项目材料核对。\n", encoding="utf-8")
    directory = tmp_path / "case"
    ingest([source], directory)
    write_json(directory / "evidence.json", {"schema_version": 1, "claims": [{
        "id": "C1", "statement": "功能、请求、响应和执行记录均由项目材料核对。",
        "source_id": "S001", "locators": ["L1"], "quote": "功能、请求、响应和执行记录均由项目材料核对。",
        "status": "verified", "verified_by": "fixture", "verified_at": "2026-10-16"}]})
    return directory


def draft_for(mode):
    key, fields = RECORDS[mode]
    record = {"id": "item", "block_ids": ["content"], "claim_ids": ["C1"]}
    record.update({field: "真实记录" for field in fields})
    text = "功能、请求、响应和执行记录均由项目材料核对。真实记录"
    if mode == "test-report":
        record.update(status="passed", actual="实际结果")
        text += " passed 实际结果"
    if mode in ("user-manual", "operations-manual"):
        record["status"] = "verified"
    draft = {"schema_version": 1, "mode": mode, "title": "项目文档", "sections": [
        {"id": sid, "title": title, "blocks": [{"id": "content" if i == 0 else f"body-{i}",
                                                "type": "paragraph", "intent": "fact", "text": text, "claim_ids": ["C1"]}]}
        for i, (sid, title) in enumerate(contract(mode)["required_sections"].items())]}
    if mode == "test-report":
        draft["conclusion"] = "passed"
        next(s for s in draft["sections"] if s["id"] == "conclusion")["blocks"][0]["text"] += " passed"
    draft[key] = [record]
    return draft


def codes(result):
    return {issue["code"] for issue in result["issues"]}


@pytest.mark.parametrize("mode", list(RECORDS))
def test_independent_mode_record_and_missing_field(case, mode):
    draft = draft_for(mode)
    assert validate(draft, case)["passed"]
    del draft[RECORDS[mode][0]][0][RECORDS[mode][1][0]]
    assert "MODE_FIELD" in codes(validate(draft, case))


@pytest.mark.parametrize("mode", list(RECORDS))
def test_mode_record_must_point_to_rendered_text_and_verified_claim(case, mode):
    draft = draft_for(mode)
    row = draft[RECORDS[mode][0]][0]
    row["block_ids"] = ["missing"]
    row["claim_ids"] = ["missing"]
    result = codes(validate(draft, case))
    assert {"MODE_TRACE", "MODE_EVIDENCE"} <= result


def test_test_report_cannot_pass_with_unexecuted_case(case):
    draft = draft_for("test-report")
    record = draft["test_cases"][0]
    record.update(status="not-run", actual="")
    assert "TEST_CONCLUSION" in codes(validate(draft, case))


@pytest.mark.parametrize("mode,key", [("user-manual", "steps"), ("operations-manual", "procedures")])
def test_unverified_procedure_is_not_deliverable(case, mode, key):
    draft = draft_for(mode)
    draft[key][0]["status"] = "unverified"
    assert "PROCEDURE_UNVERIFIED" in codes(validate(draft, case))
