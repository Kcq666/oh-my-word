# Guide contract

A profile is a frozen input, not a live eligibility decision. It must identify the agency, programme, year, notice/template version, official HTTPS URL, retrieval date, local notice snapshot and SHA-256. A profile marked `expired` can support regression fixtures only when the operator explicitly passes `--allow-expired`.

Each requirement records the exact source identifier and locator, a nonempty target section, and `pending`, `addressed` or `not-applicable`. Required items must be addressed. Section records must have authored blocks and back references to requirement IDs. Do not silently remove profile requirements.

Applicant and personnel data are supplied by the user. At least one personnel record must match the applicant, each record points to a case-relative material, and missing biographies or representative-work evidence remains a lint error. Required attachments must be supplied as real case files.

The lint result is mechanical preparation evidence. It does not establish eligibility, reviewer preference, funding, acceptance or a current open call.
