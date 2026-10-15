from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile
from defusedxml import ElementTree


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def now():
    return datetime.now(timezone.utc).isoformat()


def inside(root, relative):
    root = Path(root).resolve()
    result = (root / relative).resolve()
    if not result.is_relative_to(root):
        raise ValueError(f"Path escapes case directory: {relative}")
    return result


def check_docx(path):
    path = Path(path)
    if path.suffix.lower() != ".docx":
        raise ValueError("Only macro-free .docx is supported")
    with ZipFile(path) as archive:
        if sum(i.file_size for i in archive.infolist()) > 100_000_000:
            raise ValueError("DOCX uncompressed size exceeds 100 MB")
        if any("vbaproject" in n.lower() for n in archive.namelist()):
            raise ValueError("Macro payload in DOCX is not supported")
        types = archive.read("[Content_Types].xml")
        if b"macroEnabled" in types:
            raise ValueError("Macro-enabled content type is not supported")
        if "word/document.xml" not in archive.namelist():
            raise ValueError("Missing Word document part")
        if any(n.startswith("word/embeddings/") for n in archive.namelist()):
            raise ValueError("Embedded executable/OLE packages require a separate review path")
        for name in archive.namelist():
            if name.endswith(".rels"):
                for rel in ElementTree.fromstring(archive.read(name)):
                    if rel.get("TargetMode") == "External" and not rel.get("Type", "").endswith("/hyperlink"):
                        raise ValueError("External template/media relationships are not supported for local rendering")


def finding(code, message, severity="error", location=None):
    return {"code": code, "severity": severity, "message": message, "location": location}
