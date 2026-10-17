import json
from pathlib import Path

import pytest

from word_skills.models import CaseManifest, Fact, Source, to_dict, validate_draft_v1
from word_skills.registry import load_registry
from word_skills.router import list_skills, route


ROOT = Path(__file__).resolve().parents[1]


def test_packaged_registry_snapshot_matches_source_of_truth():
    assert (ROOT / "word_skills/data/skills.yaml").read_text(encoding="utf-8") == (
        ROOT / "registry/skills.yaml"
    ).read_text(encoding="utf-8")


def test_registry_has_six_implemented_skills():
    rows = load_registry(ROOT)
    assert {row["name"] for row in rows} == {
        "word-skills", "oh-my-technology", "oh-my-patent", "word-document",
        "oh-my-proposal", "oh-my-copyright",
    }
    assert {row["status"] for row in rows} == {"implemented"}
    assert all(row["path"] for row in rows)


def test_technology_modes_have_explicit_focus_scope():
    technology = next(row for row in load_registry(ROOT) if row["name"] == "oh-my-technology")
    assert technology["mode_scope"] == {
        "technical-report": "focused",
        "design-spec": "focused",
        "requirements-spec": "baseline",
        "interface-spec": "baseline",
        "test-report": "baseline",
        "user-manual": "baseline",
        "operations-manual": "baseline",
    }


@pytest.mark.parametrize(
    ("user_request", "skill", "mode"),
    [
        ("请写一份技术报告", "oh-my-technology", "technical-report"),
        ("请制作系统设计说明", "oh-my-technology", "design-spec"),
        ("只调整 Word 页眉和页码", "word-document", "docx-layout"),
        ("检查发明专利权利要求", "oh-my-patent", None),
    ],
)
def test_route_selects_implemented_skill(user_request, skill, mode):
    result = route(user_request, ROOT)
    assert result["selected"] == skill
    assert result["matches"][0]["status"] == "implemented"
    assert result["matches"][0]["mode"] == mode
    assert not result["needs_clarification"]


def test_route_selects_proposal_preparation():
    result = route("请准备项目申报书和预算说明", ROOT)
    assert result["selected"] == "oh-my-proposal"
    assert not result["needs_clarification"]
    assert result["matches"][0]["status"] == "implemented"


def test_route_keeps_ambiguous_composition_explicit():
    result = route("把专利技术内容整理成技术报告并排版成 Word", ROOT)
    assert result["selected"] == "word-skills"
    assert not result["needs_clarification"]
    assert {item["skill"] for item in result["matches"]} == {"oh-my-patent", "word-document", "oh-my-technology"}


def test_route_selects_interface_mode():
    result = route("请写一份接口说明", ROOT)
    assert result["selected"] == "oh-my-technology"
    assert result["matches"][0]["mode"] == "interface-spec"
    assert result["matches"][0]["mode_scope"] == "baseline"
    assert result["matches"][0]["status"] == "implemented"
    assert not result["needs_clarification"]


def test_contract_dataclasses_are_versioned_and_json_ready():
    values = [
        CaseManifest("case-1", "technical-document", "technical-report"),
        Source("S1", "sources/S1.txt", "a" * 64),
        Fact("F1", "已核对的事实", ["S1"], ["L1"], "verified"),
    ]
    for value in values:
        result = to_dict(value)
        assert result["schema_version"] == 1
        json.dumps(result, ensure_ascii=False)


def test_v1_contract_rejects_malformed_nested_values():
    with pytest.raises(ValueError, match="schema_version=1"):
        validate_draft_v1({"schema_version": 2, "mode": "technical-report", "title": "x", "sections": []})
    with pytest.raises(ValueError, match="claim_ids"):
        validate_draft_v1({
            "schema_version": 1,
            "mode": "technical-report",
            "title": "x",
            "sections": [{"id": "s", "title": "S", "blocks": [{"claim_ids": [1]}]}],
        })


def test_list_skills_is_registry_backed():
    names = {row["name"] for row in list_skills(ROOT)}
    assert "word-skills" in names
    assert "oh-my-proposal" in names
    technology = next(row for row in list_skills(ROOT) if row["name"] == "oh-my-technology")
    assert technology["mode_scope"]["technical-report"] == "focused"
