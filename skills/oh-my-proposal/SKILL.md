---
name: oh-my-proposal
description: Prepare evidence-bound project proposal drafts from a verified, versioned official guide. Use for application structure, requirement traceability, personnel and attachment completeness, and budget checks; it never submits or decides eligibility.
---

# Project proposals

Use a current official notice or a clearly labelled historical profile. Record its snapshot, retrieval and verification metadata before drafting. Treat requirements as a trace map: every required item has a source locator, an authored section and an addressed status. Keep applicant, personnel, attachments and budget facts user-supplied.

Run `word-skills proposal template` only to create a scaffold. Fill the JSON with real facts, section blocks and case-relative material paths, then run `word-skills proposal lint`. An expired profile is useful only for historical tests with `--allow-expired`; it is not a current submission channel.

For Word output, project authored sections into the shared JSON v1 document pipeline and use `word-document` for rendering, review-init, visual page review and finalize. Do not call an external submission system. Human verification and any AI disclosure remain explicit.

Read [guide-contract.md](references/guide-contract.md) for the input contract and [budget-and-trace.md](references/budget-and-trace.md) for failure conditions.
