"""Local maintenance artifacts; independent of the application review schema."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PureWindowsPath


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identifier(value):
    if (not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}', value)
            or value.lower() in {'con', 'prn', 'aux', 'nul', *('com'+str(i) for i in range(10)),
                                *('lpt'+str(i) for i in range(10))}):
        raise ValueError(f'invalid identifier: {value!r}')
    return value


def relative_file(root, value):
    if not isinstance(value, str) or not value.strip() or '\\' in value:
        raise ValueError('paths must be nonempty relative paths with / separators')
    path = Path(value)
    if path.is_absolute() or PureWindowsPath(value).drive or '..' in path.parts:
        raise ValueError(f'path escapes artifact root: {value}')
    base = Path(root).resolve()
    resolved = (base / path).resolve()
    if base not in resolved.parents or not resolved.is_file():
        raise ValueError(f'missing or out-of-root file: {value}')
    return resolved


def write_json(path, data, *, exclusive=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x' if exclusive else 'w', encoding='utf-8', newline='\n') as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))
