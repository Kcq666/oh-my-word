"""Maintenance CLI: modules, private cases, revisions, and explicit Skill evals."""
from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from oh_my_patent.casework import compare_revisions, read_revision, validate_corpus, validate_needs
from oh_my_patent.lab_common import digest, identifier, relative_file, write_json
from oh_my_patent.skill_registry import load_registry
from oh_my_patent.skill_eval import prepare_suite, run_suite, summarize


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    modules = commands.add_parser('modules', help='validate and list registered modules')
    modules.add_argument('--root', type=Path, default=ROOT)
    hasher = commands.add_parser('hash', help='SHA256 of a source file')
    hasher.add_argument('file', type=Path)
    init = commands.add_parser('case-init', help='register explicitly classified local files without modifying originals')
    init.add_argument('folder', type=Path)
    init.add_argument('--id', required=True)
    init.add_argument('--family', required=True)
    init.add_argument('--project', required=True)
    init.add_argument('--split', choices=('development', 'test'), default='development')
    init.add_argument('--use-permission', choices=('local_only', 'approved_external', 'public'), default='local_only')
    for role in ('input', 'reference', 'answer'):
        init.add_argument('--'+role, action='append', default=[])
    check = commands.add_parser('case-check', help='check file hashes and family/project split leakage')
    check.add_argument('manifests', type=Path, nargs='+')
    revisions = commands.add_parser('revision', help='read tracked DOCX edits/comments, or compare two TXT/MD/DOCX versions')
    revisions.add_argument('before', type=Path)
    revisions.add_argument('after', type=Path, nargs='?')
    revisions.add_argument('-o', '--out', type=Path, required=True)
    needs = commands.add_parser('needs-check', help='validate an issue-driven knowledge request list')
    needs.add_argument('file', type=Path)
    prepare = commands.add_parser('eval-prepare', help='freeze answer-free workspaces; does not call a model')
    prepare.add_argument('--root', type=Path, default=ROOT)
    prepare.add_argument('--cases', type=Path, default=ROOT/'evals/skill-routing-cases.yaml')
    prepare.add_argument('--mode', action='append', choices=('generic', 'domain'))
    prepare.add_argument('--case', action='append', default=[])
    prepare.add_argument('--repeats', type=int, default=1)
    prepare.add_argument('-o', '--out', type=Path, required=True)
    run = commands.add_parser('eval-run', help='explicitly execute prepared tasks with configured Codex CLI')
    run.add_argument('folder', type=Path)
    run.add_argument('--task', action='append', default=[])
    run.add_argument('--model')
    run.add_argument('--timeout', type=int, default=180)
    report = commands.add_parser('eval-report', help='verify evidence and preserve unknown grades')
    report.add_argument('folder', type=Path)
    report.add_argument('-o', '--out', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == 'modules':
            result = load_registry(args.root)
        elif args.command == 'hash':
            result = {'sha256': digest(args.file)}
        elif args.command == 'case-init':
            documents = []
            sources = set()
            for role in ('input', 'reference', 'answer'):
                for file in getattr(args, role):
                    source = relative_file(args.folder, file)
                    if source in sources:
                        raise ValueError('each file must have one role, including path aliases')
                    sources.add(source)
                    documents.append({'id': f'D{len(documents)+1}', 'path': file, 'role': role,
                                      'kind': 'unclassified', 'version': 'unconfirmed', 'sha256': digest(source)})
            result = {'schema_version': 1, 'case_id': identifier(args.id), 'family_id': identifier(args.family),
                      'project_id': identifier(args.project), 'split': args.split,
                      'use_permission': args.use_permission, 'documents': documents}
            # Validate before creating a manifest, including role collisions.
            if not args.input or len({d['path'] for d in documents}) != len(documents):
                raise ValueError('explicit input required; each file must have one role')
            target = args.folder/'case.json'
            write_json(target, result, exclusive=True)
            validate_corpus([target])
        elif args.command == 'case-check':
            result = {'validated_cases': len(validate_corpus(args.manifests)), 'quality_gain': 'not_established'}
        elif args.command == 'revision':
            result = compare_revisions(args.before, args.after) if args.after else read_revision(args.before)
            write_json(args.out, result, exclusive=True)
        elif args.command == 'needs-check':
            result = {'validated_needs': len(validate_needs(args.file)['needs']), 'retrieval_executed': False}
        elif args.command == 'eval-prepare':
            suite = prepare_suite(args.root, args.cases, args.out, modes=tuple(args.mode or ('generic', 'domain')),
                                  selected=args.case, repeats=args.repeats)
            result = {'prepared_tasks': len(suite['tasks']), 'executed': False, 'suite': str(args.out/'suite.json')}
        elif args.command == 'eval-run':
            runs = run_suite(args.folder, selected=args.task, model=args.model, timeout=args.timeout)
            return 0 if all(r['execution_state'] == 'succeeded' for r in runs) else 2
        else:
            result = summarize(args.folder)
            if args.out:
                write_json(args.out, result, exclusive=True)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'维护任务失败：{exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
