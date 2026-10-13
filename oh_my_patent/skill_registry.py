"""Validate domain ownership and lifecycle without asserting model quality."""
from __future__ import annotations

from datetime import date
from pathlib import Path
import re

import yaml

from .lab_common import relative_file


def load_registry(root):
    root = Path(root).resolve()
    data = yaml.safe_load((root / 'domains/registry.yaml').read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError('domain registry requires schema_version=1')
    entries = data.get('modules')
    if not isinstance(entries, list) or not entries:
        raise ValueError('registry modules must be nonempty')
    names = set()
    for row in entries:
        if not isinstance(row, dict):
            raise ValueError('invalid registry module')
        name = row.get('name')
        if not isinstance(name, str) or not re.fullmatch(r'patent-[a-z0-9]+(?:-[a-z0-9]+)*', name) or name in names:
            raise ValueError('invalid or duplicate module name')
        names.add(name)
        if row.get('path') != f'domains/{name}/SKILL.md':
            raise ValueError(f'{name}: registry path/name mismatch')
        path = relative_file(root, row['path'])
        body = path.read_text(encoding='utf-8')
        match = re.match(r'\A---\s*\n(.*?)\n---', body, re.S)
        meta = yaml.safe_load(match[1]) if match else {}
        if not isinstance(meta, dict) or meta.get('name') != name or (meta.get('metadata') or {}).get('version') != row.get('version'):
            raise ValueError(f'{name}: registry/frontmatter mismatch')
        for field in ('owner', 'scope', 'exclusions', 'version', 'reviewed_on'):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f'{name}: missing {field}')
        date.fromisoformat(row['reviewed_on'])
        if row.get('status') not in ('experimental', 'validated', 'deprecated'):
            raise ValueError(f'{name}: invalid lifecycle status')
        evidence = row.get('quality_evidence')
        if not isinstance(evidence, list) or (row['status'] == 'validated' and not evidence):
            raise ValueError(f'{name}: validated requires quality_evidence')
        for item in evidence:
            relative_file(root, item)
    discovered = {p.parent.name for p in (root / 'domains').glob('*/SKILL.md')}
    if discovered != names:
        raise ValueError(f'registry coverage mismatch: {sorted(discovered ^ names)}')
    return entries
