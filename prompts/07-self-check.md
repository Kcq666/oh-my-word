# 07 · 自检和交付

先执行 08 内容审查，再跑 lint。形式检查不是法律结论。

1. `python tools/patent.py lint 稿件.md`；修正 ERROR、核对 WARNING。
2. 修正引起内容或证据变更，重新执行 08，不复用旧哈希。
3. `build --final --facts TECH_FACTS.json --review content-review.json`；不得 --force。
4. 打开 Word 或渲染预览，核对编号、公式、表格、图片、分页与正文完整性。脚本结构测试不代表 WPS/Office 实际版面一致。无法渲染时如实记录，不能声称完成视觉验收。
5. 用户要求申请准备时运行 handoff；按 references/cnipa-xml-handoff.md 完成官方转换、预览与请求书。工具未运行就标记 conversion_pending。
6. 交付稿件与审阅文件、证据、交接清单，说明尚需实际完成的步骤。缺技术材料时可以交草稿与待确认问题，不假装 final。
