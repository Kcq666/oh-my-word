"""Compatibility adapter for the existing patent CLI."""
from __future__ import annotations


def main(argv: list[str] | None = None) -> int:
    from oh_my_patent.cli import main as patent_main

    return patent_main(argv)
