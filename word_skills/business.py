"""Bind a business check and its exact input into the shared review manifest."""
from pathlib import Path
import hashlib
import shutil

from .common import digest, finding, read_json, sha256, write_json


def bind_business_audit(output, kind, source, validation, extra_files=(), *, source_bytes=None):
    output = Path(output).resolve()
    source = Path(source).resolve()
    manifest = read_json(output / "manifest.json")
    if manifest["state"] not in ("business-pending", "draft") or manifest.get("business_gate") != kind:
        raise ValueError("business input can bind only to its dedicated build")
    if not validation.get("passed") or source_bytes is None:
        raise ValueError("a successful validation of the exact input bytes is required")
    audit = output / "audit"
    expected = hashlib.sha256(source_bytes).hexdigest()
    if sha256(source) != expected:
        common_validation = read_json(audit / "validation.json")
        common_validation["issues"].append(finding("BUSINESS_INPUT_CHANGED", "Business input changed after validation; rebuild"))
        common_validation["passed"] = False
        write_json(audit / "validation.json", common_validation)
        manifest["outputs"]["audit/validation.json"] = sha256(audit / "validation.json")
        manifest["state"] = "failed"
        write_json(output / "manifest.json", manifest)
        return manifest
    draft_name = f"business-{kind}.json"
    (audit / draft_name).write_bytes(source_bytes)
    write_json(audit / f"business-{kind}-validation.json", validation)
    manifest["inputs"][f"audit/{draft_name}"] = sha256(audit / draft_name)
    manifest["inputs"][f"audit/business-{kind}-validation.json"] = sha256(audit / f"business-{kind}-validation.json")
    for number, source_file in enumerate(extra_files):
        name = f"business-attachment-{number}{Path(source_file).suffix}"
        shutil.copyfile(source_file, audit / name)
        manifest["inputs"][f"audit/{name}"] = sha256(audit / name)
    if sha256(source) != expected:
        common_validation = read_json(audit / "validation.json")
        common_validation["issues"].append(finding("BUSINESS_INPUT_CHANGED", "Business input changed during audit binding; rebuild"))
        common_validation["passed"] = False
        write_json(audit / "validation.json", common_validation)
        manifest["outputs"]["audit/validation.json"] = sha256(audit / "validation.json")
        manifest["state"] = "failed"
        write_json(output / "manifest.json", manifest)
        return manifest
    common_validation = read_json(audit / "validation.json")
    common_validation["issues"].extend(validation["issues"])
    common_validation["passed"] = common_validation["passed"] and validation["passed"]
    write_json(audit / "validation.json", common_validation)
    manifest["outputs"]["audit/validation.json"] = sha256(audit / "validation.json")
    manifest["business"] = {"kind": kind, "input": f"audit/{draft_name}",
                            "checks": f"audit/business-{kind}-validation.json"}
    if manifest["state"] == "business-pending":
        manifest["state"] = "awaiting-review"
    manifest["build_id"] = digest({"inputs": manifest["inputs"], "outputs": manifest["outputs"], "code": manifest["code_identity"]})
    write_json(output / "manifest.json", manifest)
    return manifest
