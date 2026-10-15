---
name: oh-my-copyright
description: Prepare traceable software copyright source and manual materials from a real project. Use for source selection, provenance, identity consistency, and evidence checks; it never infers ownership or submits a registration.
---

# Software copyright materials

Start with `word-skills copyright scan SOURCE_ROOT`. Review excluded files and select real source ranges only after understanding the application's actual entry points. The scanner excludes dependencies, builds, credentials and binary content; lint revalidates the manifest, source hash, line count, safe path and selection ranges.

Fill a copyright JSON template with user-confirmed rights, software identity, a real manual, UI screenshots when applicable, and selected source files. Run `word-skills copyright lint`; then `copyright extract` writes exact source excerpts and provenance outside the source tree. It does not estimate pages or invent code. Page layout and every page image still require the shared Word build/review pipeline and human review.

Read [source-and-rights.md](references/source-and-rights.md) and [manual-and-visuals.md](references/manual-and-visuals.md). Treat official filing rules as current only when supported by a current authoritative source.
