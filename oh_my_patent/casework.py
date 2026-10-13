"""Local corpus validation and loss-aware revision comparison. No model calls."""
from __future__ import annotations

import difflib
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

from .lab_common import digest, identifier, read_json, relative_file

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
M = '{http://schemas.openxmlformats.org/officeDocument/2006/math}'


def validate_case(path):
    path = Path(path).resolve()
    data = read_json(path)
    if not isinstance(data, dict) or data.get('schema_version') != 1:
        raise ValueError('case manifest requires schema_version=1')
    for key in ('case_id', 'family_id', 'project_id'):
        identifier(data.get(key))
    if data.get('split') not in ('development', 'test'):
        raise ValueError('split must be development or test')
    if data.get('use_permission') not in ('local_only', 'approved_external', 'public'):
        raise ValueError('use_permission must be local_only, approved_external or public')
    docs = data.get('documents')
    if not isinstance(docs, list) or not docs:
        raise ValueError('documents must be nonempty')
    ids, paths = set(), set()
    for doc in docs:
        if not isinstance(doc, dict):
            raise ValueError('invalid document record')
        identifier(doc.get('id'))
        if doc['id'] in ids:
            raise ValueError('duplicate document id')
        ids.add(doc['id'])
        if doc.get('role') not in ('input', 'reference', 'answer'):
            raise ValueError('document role must be input, reference or answer')
        for key in ('kind', 'version'):
            if not isinstance(doc.get(key), str) or not doc[key].strip():
                raise ValueError(f'document needs {key}')
        source = relative_file(path.parent, doc.get('path'))
        if source in paths:
            raise ValueError('same file registered more than once; choose one role for this task')
        paths.add(source)
        if not isinstance(doc.get('sha256'), str) or not re.fullmatch(r'[0-9a-f]{64}', doc['sha256']) or digest(source) != doc['sha256']:
            raise ValueError(f'{doc["id"]}: document hash changed or missing')
    if not any(d['role'] == 'input' for d in docs):
        raise ValueError('case needs an input document')
    return data


def validate_corpus(paths):
    cases, ids, groups, hashes = [], set(), {}, {}
    for path in paths:
        data = validate_case(path)
        if data['case_id'] in ids:
            raise ValueError('duplicate case_id')
        ids.add(data['case_id'])
        for group in ('family_id', 'project_id'):
            key = (group, data[group])
            if key in groups and groups[key] != data['split']:
                raise ValueError(f'{group} crosses development/test: {data[group]}')
            groups[key] = data['split']
        for doc in data['documents']:
            for split, role in hashes.get(doc['sha256'], []):
                if split != data['split'] and (role != 'reference' or doc['role'] != 'reference'):
                    raise ValueError('duplicate input/answer content crosses development/test, including reference reuse')
            hashes.setdefault(doc['sha256'], []).append((data['split'], doc['role']))
        cases.append(data)
    return cases


def _text(node, mode):
    if mode == 'before' and node.tag in (W+'ins', W+'moveTo'):
        return ''
    if mode == 'after' and node.tag in (W+'del', W+'moveFrom'):
        return ''
    if node.tag in (W+'t', W+'delText'):
        return node.text or ''
    if node.tag == W+'tab':
        return '\t'
    if node.tag in (W+'br', W+'cr'):
        return '\n'
    if node.tag in (M+'oMath', M+'oMathPara'):
        return '⟪公式：请核对原件⟫'
    return ''.join(_text(child, mode) for child in node)


def read_revision(path):
    path = Path(path)
    if path.suffix.lower() in ('.txt', '.md'):
        text = path.read_text(encoding='utf-8-sig')
        return {'before': text, 'after': text, 'revisions': [], 'comments': [], 'warnings': []}
    if path.suffix.lower() != '.docx':
        raise ValueError('revision comparison supports UTF-8 TXT/MD and DOCX; PDF/OCR requires a verified external reader')
    try:
        with zipfile.ZipFile(path) as archive:
            root = ET.fromstring(archive.read('word/document.xml'))
            comments = ET.fromstring(archive.read('word/comments.xml')) if 'word/comments.xml' in archive.namelist() else None
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        raise ValueError(f'invalid DOCX: {path.name}') from exc
    before, after, revisions, anchors = [], [], [], {}
    paragraphs = list(root.iter(W+'p'))
    for index, para in enumerate(paragraphs, 1):
        locator = f'word/document.xml:p{index}'
        before.append(_text(para, 'before'))
        after.append(_text(para, 'after'))
        for node in para.iter():
            kind = node.tag.removeprefix(W) if node.tag.startswith(W) else ''
            if kind in ('ins', 'del', 'moveFrom', 'moveTo'):
                revisions.append({'kind': kind, 'locator': locator, 'id': node.get(W+'id'),
                                  'author': node.get(W+'author'), 'date': node.get(W+'date'),
                                  'text': _text(node, 'before' if kind in ('del', 'moveFrom') else 'after')})
            if kind in ('commentRangeStart', 'commentRangeEnd', 'commentReference'):
                anchors.setdefault(node.get(W+'id'), set()).add(locator)
    comment_rows = []
    if comments is not None:
        for node in comments.iter(W+'comment'):
            comment_rows.append({'id': node.get(W+'id'), 'author': node.get(W+'author'),
                                 'date': node.get(W+'date'), 'text': _text(node, 'after'),
                                 'locators': sorted(anchors.get(node.get(W+'id'), set()))})
    warnings = ['TEXT_ONLY: 仅解析常见行内修订；段落索引不是页码。复杂嵌套/段落/表格结构修订、图件、版面与字段须核对原件。']
    if any(node.tag in (M+'oMath', M+'oMathPara') for node in root.iter()):
        warnings.append('FORMULA_UNREAD: 公式已留占位，不能据此比较数学意义。')
    if any(node.tag.startswith(W) and node.tag.endswith('Change') for node in root.iter()):
        warnings.append('FORMAT_CHANGE: 存在属性修订，文本比较不解释格式变化。')
    return {'before': '\n'.join(before), 'after': '\n'.join(after),
            'revisions': revisions, 'comments': comment_rows, 'warnings': warnings}


def compare_revisions(before, after):
    a, b = read_revision(before), read_revision(after)
    return {'schema_version': 1, 'kind': 'text_comparison_not_semantic_review',
            'before_sha256': digest(before), 'after_sha256': digest(after),
            'diff': '\n'.join(difflib.unified_diff(a['after'].splitlines(), b['after'].splitlines(),
                                               fromfile=Path(before).name, tofile=Path(after).name, lineterm='')),
            'documents': {'before': a, 'after': b}, 'modification_reasons': [],
            'review_status': 'pending'}


def validate_needs(path):
    data = read_json(path)
    if not isinstance(data, dict) or data.get('schema_version') != 1 or not isinstance(data.get('needs'), list):
        raise ValueError('needs manifest requires schema_version=1 and needs list')
    ids = set()
    for row in data['needs']:
        if not isinstance(row, dict):
            raise ValueError('invalid knowledge need')
        identifier(row.get('id'))
        if row['id'] in ids:
            raise ValueError('duplicate need id')
        ids.add(row['id'])
        for key in ('question', 'query', 'version_or_date_scope', 'delivery'):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f'need requires {key}')
        if row.get('role') not in ('law', 'standard', 'prior_art', 'writing_case') or row.get('status') not in ('pending', 'found', 'unavailable'):
            raise ValueError('invalid need role/status')
        evidence = row.get('evidence', [])
        if not isinstance(evidence, list) or (row['status'] == 'found' and not evidence):
            raise ValueError('found need requires evidence')
        for item in evidence:
            if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item[k].strip() for k in ('source', 'locator', 'supports', 'limitations')):
                raise ValueError('evidence requires source, locator, supports and limitations')
    return data
