from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .common import read_json, write_json
from . import copyright, proposal
from .delivery import build, finalize, review_init
from .evidence import contract, validate
from .ingest import ingest
from .render import fingerprint
from .router import list_skills, route
from .technology import scaffold


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if argv and argv[0] == "patent":
        from .legacy_patent import main as patent_main

        return patent_main(argv[1:])
    parser = argparse.ArgumentParser(description="Local evidence-bound technical documents; writing is performed by the agent")
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("ingest")
    p.add_argument("inputs", nargs="+")
    p.add_argument("--case", required=True)
    p = commands.add_parser("template")
    p.add_argument("--mode", required=True, help="已安装的技术文档模式名")
    p.add_argument("--out", required=True)
    p = commands.add_parser("fingerprint")
    p.add_argument("docx")
    p.add_argument("--out", required=True)
    p = commands.add_parser("lint")
    p.add_argument("draft")
    p.add_argument("--case", required=True)
    p = commands.add_parser("build")
    p.add_argument("draft")
    p.add_argument("--case", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--template")
    p.add_argument("--template-mode", choices=["style", "slots"], default="style")
    p.add_argument("--soffice")
    p.add_argument("--pdftoppm")
    p.add_argument("--no-preview", action="store_true")
    for name in ("review-init", "finalize"):
        p = commands.add_parser(name)
        p.add_argument("output")
    p = commands.add_parser("skills", help="列出仓库登记的技能及其实现状态")
    p.add_argument("action", choices=["list"], nargs="?", default="list")
    p.add_argument("--json", action="store_true", help="以 JSON 输出")
    p = commands.add_parser("route", help="根据用户请求选择技能；只做确定性路由，不生成正文")
    p.add_argument("request")
    p.add_argument("--json", action="store_true", help="以 JSON 输出")
    p = commands.add_parser("proposal", help="项目申请 Profile、模板与机械校验")
    proposal_commands = p.add_subparsers(dest="proposal_action", required=True)
    p = proposal_commands.add_parser("template")
    p.add_argument("--profile", default="nsfc-2026-general")
    p.add_argument("--out", required=True)
    p = proposal_commands.add_parser("lint")
    p.add_argument("draft")
    p.add_argument("--case", help="ingested source/evidence case directory")
    p.add_argument("--allow-expired", action="store_true", help="仅供历史案例检查，不表示指南仍有效")
    p = proposal_commands.add_parser("build")
    p.add_argument("draft")
    p.add_argument("--case", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--allow-expired", action="store_true", help="仅供历史案例检查，不表示指南仍有效")
    p.add_argument("--soffice")
    p.add_argument("--pdftoppm")
    p.add_argument("--no-preview", action="store_true")
    p = commands.add_parser("copyright", help="软著源码清单、材料草稿与机械校验")
    copyright_commands = p.add_subparsers(dest="copyright_action", required=True)
    p = copyright_commands.add_parser("scan")
    p.add_argument("source_root")
    p.add_argument("--out")
    p = copyright_commands.add_parser("template")
    p.add_argument("--out", required=True)
    p = copyright_commands.add_parser("lint")
    p.add_argument("draft")
    p.add_argument("--source-root")
    p = copyright_commands.add_parser("extract")
    p.add_argument("draft")
    p.add_argument("--source-root")
    p.add_argument("--out", required=True)
    p = copyright_commands.add_parser("build")
    p.add_argument("draft")
    p.add_argument("--source-root")
    p.add_argument("--out", required=True)
    p.add_argument("--soffice")
    p.add_argument("--pdftoppm")
    p.add_argument("--no-preview", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "skills":
            result = {"schema_version": 1, "skills": list_skills()}
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                for row in result["skills"]:
                    path = row["path"] or "(planned; no implementation path)"
                    print(f"{row['name']:<18} {row['status']:<11} {path}")
            return 0
        if args.command == "route":
            result = route(args.request)
            if args.json:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            else:
                print(f"selected: {result['selected']}")
                print(f"status: {'clarification-needed' if result['needs_clarification'] else 'ready'}")
                print(result["reason"])
                for match in result["matches"]:
                    print(f"- {match['skill']} ({match['status']}): {', '.join(match['matched_terms'])}")
            return 0
        if args.command == "proposal":
            if args.proposal_action == "template":
                result = proposal.write_template(args.out, args.profile)
            elif args.proposal_action == "build":
                result = proposal.build(args.draft, args.case, args.out, allow_expired=args.allow_expired,
                                        soffice=args.soffice, pdftoppm=args.pdftoppm, no_preview=args.no_preview)
            else:
                result = proposal.lint(args.draft, allow_expired=args.allow_expired, case=args.case)
        elif args.command == "copyright":
            if args.copyright_action == "scan":
                result = copyright.scan(args.source_root, args.out)
            elif args.copyright_action == "template":
                result = copyright.write_template(args.out)
            elif args.copyright_action == "lint":
                result = copyright.lint(args.draft, source_root=args.source_root)
            elif args.copyright_action == "extract":
                result = copyright.extract_materials(args.draft, args.out, source_root=args.source_root)
            else:
                result = copyright.build(args.draft, args.out, source_root=args.source_root,
                                         soffice=args.soffice, pdftoppm=args.pdftoppm, no_preview=args.no_preview)
        elif args.command == "ingest":
            result = ingest(args.inputs, args.case)
            result = {"sources": len(result["sources"]), "skipped": result["skipped"], "case": args.case}
        elif args.command == "template":
            if Path(args.out).exists():
                raise ValueError("Draft already exists")
            schema = contract(args.mode)
            result = {"schema_version": 1, "mode": args.mode, "title": schema["title"], "sections": [
                {"id": k, "title": v, "blocks": [{"id": k + "-body", "type": "paragraph", "intent": "gap", "text": "待补充", "claim_ids": []}]}
                for k, v in schema["required_sections"].items()], **scaffold(args.mode)}
            write_json(args.out, result)
            result = {"draft": args.out, "state": "scaffold-not-deliverable"}
        elif args.command == "fingerprint":
            if Path(args.out).exists():
                raise ValueError("Fingerprint file already exists")
            result = fingerprint(args.docx)
            write_json(args.out, result)
        elif args.command == "lint":
            result = validate(read_json(args.draft), args.case)
        elif args.command == "build":
            result = build(args.draft, args.case, args.out, args.template, args.template_mode, args.soffice, args.pdftoppm, args.no_preview)
        elif args.command == "review-init":
            result = review_init(args.output)
        else:
            result = finalize(args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result.get("passed") is False or result.get("state") in {"blocked", "failed"} else 0
    except (ValueError, OSError, KeyError, TypeError, AttributeError, ImportError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2
