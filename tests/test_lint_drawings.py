# -*- coding: utf-8 -*-
"""附图登记与实际图件的对应关系（DRAW-001 / DRAW-002）。

这两条检查盯的是**交付物缺图**：稿件形式上全部合规、自检也就全绿，
打开生成的 .docx 才发现图位是一行「（图N缺失）」占位句。

原先只有外观设计查过这件事（DES-005），发明与实用新型完全没人看，
于是"附图说明写了几幅图、一幅图件都没产出"的稿件可以一路走到交付——
本项目的两份 OKS 稿件就真的这么交出去过一次。
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from oh_my_patent.lint import lint
from oh_my_patent.parser import load, parse_markdown
from oh_my_patent.report import Severity

#: 一份结构完整、可以独立通过自检的发明稿件。``{front}`` 用来插附图声明。
BASE = (
    "---\ntitle: 一种装置\ntype: invention\n{front}---\n\n"
    "# 说明书\n\n## 技术领域\n本发明涉及装置技术领域。\n\n"
    "## 附图说明\n图1为本发明的结构示意图。\n\n"
    "## 具体实施方式\n如图1所示，装置包括壳体1与电路板2。\n\n"
    "# 摘要\n本发明公开一种装置。\n"
)

#: 一个字节最小的合法 PNG 头，仅用于让 ``Path.exists()`` 为真。
PNG_HEADER = b"\x89PNG\r\n\x1a\n"


def codes(draft) -> set[str]:
    return {i.code for i in lint(draft).issues}


def issue_of(draft, code: str):
    for item in lint(draft).issues:
        if item.code == code:
            return item
    return None


class DrawingRegistrationTest(unittest.TestCase):
    def test_caption_without_file_warns(self):
        """附图说明写了图、却没登记图件：这是警告，不是形式错误。"""
        draft = parse_markdown(BASE.format(front=""))
        self.assertIn("DRAW-001", codes(draft))
        self.assertIs(issue_of(draft, "DRAW-001").severity, Severity.WARNING)

    def test_warning_comes_with_a_fix(self):
        draft = parse_markdown(BASE.format(front=""))
        self.assertTrue(issue_of(draft, "DRAW-001").hint.strip())

    def test_design_keeps_its_own_code(self):
        """外观设计仍由 DES-005 报出，同一个问题不出现两条码。"""
        draft = parse_markdown(
            "---\ntitle: 水杯\ntype: design\n---\n\n"
            "# 外观设计简要说明\n\n## 用途\n本产品用于盛装饮用水。\n\n"
            "## 设计要点\n设计要点在于杯身的弧面造型。\n\n"
            "## 最能表明设计要点的图片\n立体图。\n\n"
            "# 附图说明\n图1为立体图。\n"
        )
        self.assertIn("DES-005", codes(draft))
        self.assertNotIn("DRAW-001", codes(draft))

    def test_registered_but_absent_file_is_error(self):
        """登记了路径、文件却不在：这是错误——生成时图位只剩占位句。"""
        draft = parse_markdown(
            BASE.format(front="drawings:\n  - {number: 1, path: 不存在的目录/图1.png}\n")
        )
        self.assertIs(issue_of(draft, "DRAW-002").severity, Severity.ERROR)

    def test_absent_file_does_not_also_raise_the_warning(self):
        """有路径时只报缺文件，不再叠一条"没登记"。"""
        draft = parse_markdown(
            BASE.format(front="drawings:\n  - {number: 1, path: 不存在的目录/图1.png}\n")
        )
        self.assertNotIn("DRAW-001", codes(draft))


class RelativePathTest(unittest.TestCase):
    """稿件的相对路径以稿件文件所在目录为基准。

    早先按运行目录解析，于是示例里写的 ``images/图1.png`` 只在恰好站在
    examples/ 下时才找得到；换个目录构建，图件静默变成缺失占位。
    """

    def test_relative_path_resolves_against_draft_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "images").mkdir()
            (root / "images" / "图1.png").write_bytes(PNG_HEADER)
            draft_file = root / "稿件.md"
            draft_file.write_text(
                BASE.format(front="drawings:\n  - {number: 1, path: images/图1.png}\n"),
                encoding="utf-8",
            )

            draft = load(draft_file)

            self.assertNotIn("DRAW-002", codes(draft))
            self.assertTrue(
                Path(draft.drawings[0].path).is_absolute(),
                "相对路径应当解析成绝对路径，构建才不依赖运行目录",
            )

    def test_unresolvable_path_is_left_alone(self):
        """解析不出来就保持原样：这一层不猜，交给自检报缺。"""
        draft = parse_markdown(
            BASE.format(front="drawings:\n  - {number: 1, path: images/没有这个.png}\n"),
            source=str(Path(tempfile.gettempdir()) / "稿件.md"),
        )
        self.assertEqual(draft.drawings[0].path, "images/没有这个.png")
        self.assertIn("DRAW-002", codes(draft))

    def test_string_source_does_not_break(self):
        """``source`` 缺省是空串，不能因此去解析路径。"""
        draft = parse_markdown(
            BASE.format(front="drawings:\n  - {number: 1, path: images/图1.png}\n")
        )
        self.assertEqual(draft.drawings[0].path, "images/图1.png")


if __name__ == "__main__":
    unittest.main()
