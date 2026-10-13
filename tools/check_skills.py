"""Read-only checks for this repository's Skill bundle, not model behavior."""
from pathlib import Path
import argparse
import re
import sys
from urllib.parse import unquote

import yaml


def check(root):
    root = Path(root).resolve()
    errors = []
    skills = [root / 'SKILL.md', *sorted((root / 'domains').glob('*/SKILL.md'))]
    names = set()
    for path in skills:
        try:
            body = path.read_text(encoding='utf-8')
            match = re.match(r'\A---\s*\n(.*?)\n---(?:\s*\n|$)', body, re.S)
            data = yaml.safe_load(match[1]) if match else None
            if not isinstance(data, dict):
                raise ValueError('missing frontmatter mapping')
            name = data.get('name')
            if not isinstance(name, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name) or len(name) > 64:
                raise ValueError('invalid name')
            # Root may be unpacked into an arbitrary folder by the user.
            if path != skills[0] and name != path.parent.name:
                raise ValueError('name differs from domain directory')
            if name in names:
                raise ValueError('duplicate name')
            names.add(name)
            if not isinstance(data.get('description'), str) or not data['description'].strip():
                raise ValueError('missing description')
            if path != skills[0] and not (data.get('metadata') or {}).get('version'):
                raise ValueError('missing domain version')
        except (OSError, ValueError, TypeError, AttributeError, yaml.YAMLError) as exc:
            errors.append(f'{path.relative_to(root)}: {exc}')

    docs = skills + [root / 'README.md']
    for directory in ('references', 'prompts'):
        docs.extend(sorted((root / directory).rglob('*.md')))
    links = 0
    for path in docs:
        if not path.exists():
            errors.append(f'missing {path.relative_to(root)}')
            continue
        body = re.sub(r'```.*?```', '', path.read_text(encoding='utf-8'), flags=re.S)
        for target in re.findall(r'\]\(([^\s)]+)\)', body):
            if re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', target) or target.startswith('#'):
                continue
            target = unquote(target.split('#')[0]).strip('<>')
            links += 1
            if not (path.parent / target).exists():
                errors.append(f'{path.relative_to(root)}: broken link {target}')
    catalog = root / 'references/domain-catalog.md'
    catalog_text = catalog.read_text(encoding='utf-8') if catalog.exists() else ''
    for path in skills[1:]:
        if f'../domains/{path.parent.name}/SKILL.md' not in catalog_text:
            errors.append(f'domain absent from catalog: {path.parent.name}')
    count = 0
    try:
        data = yaml.safe_load((root / 'evals/skill-routing-cases.yaml').read_text(encoding='utf-8'))
        cases = data['cases']
        if not isinstance(cases, list) or not cases:
            raise ValueError('cases must be a nonempty list')
        ids = set()
        domains = {path.parent.name for path in skills[1:]}
        for case in cases:
            cid = case['id']
            if not isinstance(cid, str) or not cid or cid in ids:
                raise ValueError('empty or duplicate case id')
            ids.add(cid)
            if not isinstance(case['request'], str) or not case['request'].strip():
                raise ValueError(f'{cid}: missing request')
            expected = case['expected']
            for key in ('required', 'avoid'):
                if not isinstance(expected[key], list) or any(not isinstance(x, str) for x in expected[key]):
                    raise ValueError(f'{cid}: {key} must be a list of names')
            a, b = set(expected['required']), set(expected['avoid'])
            if a & b or not (a | b) <= domains:
                raise ValueError(f'{cid}: conflicting or unknown domains')
            if not isinstance(expected['behavior'], str) or not expected['behavior'].strip():
                raise ValueError(f'{cid}: missing behavior')
        count = len(cases)
    except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as exc:
        errors.append(f'evals: {exc}')
    return errors, {'skills': len(skills), 'local_links': links, 'cases': count}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors, counts = check(args.root)
    for error in errors:
        print(f'ERROR: {error}')
    print(('FAIL' if errors else 'PASS') + ': ' + ', '.join(f'{k}={v}' for k, v in counts.items()))
    return int(bool(errors))


if __name__ == '__main__':
    sys.exit(main())
