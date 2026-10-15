"""Small versioned data contracts shared by document skills.

These models are deliberately transport-oriented.  Business-specific fields
remain in extension dictionaries so the patent package does not become a
dependency of the common Word pipeline.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CaseManifest:
    case_id: str
    document_kind: str
    mode: str
    audience: str = ""
    template: str | None = None
    deliverables: list[str] = field(default_factory=list)
    schema_version: int = 1


@dataclass
class Source:
    id: str
    path: str
    sha256: str
    locator_kind: str = "line"
    retrieved_at: str = ""
    conversion_notices: list[str] = field(default_factory=list)
    schema_version: int = 1


@dataclass
class Fact:
    id: str
    statement: str
    source_ids: list[str] = field(default_factory=list)
    locators: list[str] = field(default_factory=list)
    verification_status: str = "unverified"
    assertion_kind: str = "fact"
    schema_version: int = 1


@dataclass
class Requirement:
    id: str
    text: str
    source_id: str = ""
    locator: str = ""
    applicability: str = "unknown"
    target_sections: list[str] = field(default_factory=list)
    schema_version: int = 1


@dataclass
class DocumentDraft:
    id: str
    document_kind: str
    title: str
    version: str = ""
    section_ids: list[str] = field(default_factory=list)
    assets: list[str] = field(default_factory=list)
    profile_id: str | None = None
    schema_version: int = 1


@dataclass
class TraceMap:
    draft_id: str
    section_or_block_id: str
    fact_ids: list[str] = field(default_factory=list)
    requirement_ids: list[str] = field(default_factory=list)
    schema_version: int = 1


@dataclass
class Review:
    draft_hash: str
    source_hash: str
    asset_hash: str = ""
    template_hash: str = ""
    scope: str = ""
    checks: list[dict[str, Any]] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    reviewed_at: str = ""
    reviewer: str = ""
    schema_version: int = 1


@dataclass
class BuildManifest:
    inputs: dict[str, str] = field(default_factory=dict)
    profile_hash: str = ""
    outputs: dict[str, str] = field(default_factory=dict)
    output_hashes: dict[str, str] = field(default_factory=dict)
    render_backend: str = ""
    schema_version: int = 1


def to_dict(value: Any) -> dict[str, Any]:
    """Serialize a contract without exposing implementation-specific methods."""
    if not hasattr(value, "__dataclass_fields__"):
        raise TypeError("expected a contract dataclass")
    return asdict(value)


def _object(value: Any, location: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{location} must be an object")
    return value


def _array(value: Any, location: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"{location} must be an array")
    return value


def _string(value: Any, location: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{location} must be a string")


def _versioned(value: Any, location: str) -> dict:
    data = _object(value, location)
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError(f"{location} requires schema_version=1")
    return data


def validate_draft_v1(value: Any) -> dict:
    """Check the transport shape of the existing JSON v1 draft, without changing its meaning."""
    draft = _versioned(value, "draft")
    _string(draft.get("mode"), "draft.mode")
    _string(draft.get("title"), "draft.title")
    for i, section in enumerate(_array(draft.get("sections"), "draft.sections")):
        location = f"draft.sections[{i}]"
        section = _object(section, location)
        for key in ("id", "title"):
            if key in section:
                _string(section[key], f"{location}.{key}")
        for j, block in enumerate(_array(section.get("blocks", []), f"{location}.blocks")):
            block_location = f"{location}.blocks[{j}]"
            block = _object(block, block_location)
            for key in ("id", "type", "intent", "text", "source_id"):
                if key in block:
                    _string(block[key], f"{block_location}.{key}")
            for k, claim_id in enumerate(_array(block.get("claim_ids", []), f"{block_location}.claim_ids")):
                _string(claim_id, f"{block_location}.claim_ids[{k}]")
            if block.get("type") == "table":
                for k, heading in enumerate(_array(block.get("headers", []), f"{block_location}.headers")):
                    _string(heading, f"{block_location}.headers[{k}]")
                for k, row in enumerate(_array(block.get("rows", []), f"{block_location}.rows")):
                    for cell in _array(row, f"{block_location}.rows[{k}]"):
                        _string(cell, f"{block_location}.rows[{k}] cell")
                _array(block.get("widths", []), f"{block_location}.widths")
    return draft


def validate_source_index_v1(value: Any) -> dict:
    index = _versioned(value, "source index")
    for i, source in enumerate(_array(index.get("sources"), "source index.sources")):
        source = _object(source, f"source index.sources[{i}]")
        for key in ("id", "original_path", "snapshot", "sha256", "extracted", "extracted_sha256", "segments", "segments_sha256"):
            _string(source.get(key), f"source index.sources[{i}].{key}")
    return index


def validate_evidence_v1(value: Any) -> dict:
    ledger = _versioned(value, "evidence")
    for i, claim in enumerate(_array(ledger.get("claims"), "evidence.claims")):
        claim = _object(claim, f"evidence.claims[{i}]")
        for key in ("id", "statement", "source_id", "quote", "status", "verified_by", "verified_at"):
            if key in claim:
                _string(claim[key], f"evidence.claims[{i}].{key}")
        for j, locator in enumerate(_array(claim.get("locators", []), f"evidence.claims[{i}].locators")):
            _string(locator, f"evidence.claims[{i}].locators[{j}]")
    return ledger


def validate_segments_v1(value: Any) -> list:
    for i, segment in enumerate(_array(value, "segments")):
        segment = _object(segment, f"segments[{i}]")
        for key in ("locator", "text"):
            _string(segment.get(key), f"segments[{i}].{key}")
    return value
