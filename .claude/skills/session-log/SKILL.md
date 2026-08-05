---
name: session-log
description: |
  Save the current session as a structured handoff entry in this repo's rolling log
  (logs/consumables-dashboard_log.md). Trigger when the user says "session log",
  "log the handoff", "write the handoff", "handoff note", "log this to the repo",
  or invokes /session-log by name. Also trigger proactively at the end of any
  session where code or data changed, decisions were made, or the project advanced.
  This is a REPO-LOCAL engineering handoff, written for the next Claude session. It
  is NOT the contractual documentation suite and writes nothing to Notion.
---

# session-log

## Purpose

Conversations are ephemeral — and in this project's remote container, so is the
filesystem: it is reclaimed after inactivity. Anything not committed is gone. Every
session therefore ends with a full entry prepended to
`logs/consumables-dashboard_log.md`, committed on the working branch.

**The standard:** a future Claude session with zero memory of this conversation must
be able to continue without asking the user to re-explain anything. Capture not just
what was done, but the reasoning, the exact files, the gotchas, and the precise next
action.

These are **handoff documents first**, reference files second. Err on the side of
more detail.

## Scope — read this before anything else

This skill is **deliberately separate** from ONE LDN's contractual documentation
suite. When it is invoked:

- **Do NOT invoke** `docs-manager`, `progress-update-writer`,
  `stakeholder-update-writer`, `dashboard-doc-pair-updater`, or the user-level
  `save-conversation` skill.
- **Do NOT write to Notion.** No Change Log, no Software Register, no Progress
  Document, no stakeholder email.
- **Do NOT chain into anything.** This skill starts and ends with one file, one
  commit, one push.

The audiences are different and must not be merged: the Notion suite is the
contractual record for stakeholders; this log is an engineering handoff for the next
Claude session. If the user wants both, they will ask for both by name.

Note for future sessions: `docs-manager` chains a skill called `save-conversation`.
This skill is **not** that skill, and was named `session-log` precisely so it never
gets pulled into that chain. Do not rename it to `save-conversation`.

## ⚠ This repository is PUBLIC

`ONE-LDN/consumables-dashboard` is public and serves GitHub Pages. Every log entry
is world-readable and permanent in git history — deleting the file later does not
remove it from earlier commits.

The visibility is a settled decision (confirmed 2026-08-05); do not re-litigate it.
Instead, write accordingly:

- **No personnel narrative.** Describe process, not people. "Purchasing was reactive"
  — not who did it, their job title, or how well.
- **No credential values, ever.** Names only. `SUPABASE_SERVICE_KEY` is a name;
  its value never appears. The `service_role` key must not reach this repo in any
  form — see `apps-script/SETUP.md`.
- Supplier names, prices and stock levels are already public in `migration/`, so
  they are in bounds.
- If an entry genuinely needs a sensitive detail to be a useful handoff, write the
  neutral version and say a detail was omitted, so the next session knows to ask
  rather than assuming it doesn't exist.

## There is one mode

Rolling Log + Git Push. Always. The file is `logs/consumables-dashboard_log.md`,
newest entry at top, committed on the session's working branch. Do not write logs
anywhere else — not `~/Documents`, not the scratchpad, not a new file.

## Process

1. **Read the existing log first** — at minimum the top entry. Cross-reference by
   date rather than repeating context (e.g. "see the 2026-08-05 entry for the
   minimum-stock method").
2. **Draft the entry** using the full template below. Every section, every time. If
   a section genuinely doesn't apply, write "N/A" so the reader knows it was
   considered.
3. **Prepend** directly under the file's header block, above the previous newest
   entry. Never append at the bottom; never edit prior entries.
4. **Commit and push** on the current working branch:
   ```
   git add logs/consumables-dashboard_log.md
   git commit -m "session log: YYYY-MM-DD <short-title>"
   git push -u origin <branch>
   ```
   Never push to `master`. If the session has an open PR the log commit rides in it;
   if not, open a draft PR.
5. **Report** the commit hash and a one-line confirmation. If the push fails, say so
   with the error — never fail silently.

## When NOT to write an entry

One carve-out, because this repo generates automated wake-ups:

**A scheduled PR check-in that finds nothing changed is not a session.** Those fire,
re-check PR state and CI, find no change, and re-arm silently. Do not log them — an
entry per no-op wake-up buries the real entries. Log a check-in only if it acted:
pushed a fix, replied to a review, or resolved a conflict.

Everything else gets an entry, including sessions that only discussed things.
Decisions are the artifact.

## Go long / go short

**Go long on:** Decisions & Reasoning (reasoning evaporates fastest), Next Steps
(item 1 must be executable with no warm-up), Notes & Gotchas, exact artifact paths,
and **corrections** — a figure that was wrong and got fixed is the single most
valuable thing to record, because the wrong version is usually the more intuitive
one and will be re-derived otherwise.

**Go short on:** background a prior entry already holds (cross-reference by date),
and process narration that adds nothing ("then I ran the script").

## Template (use in full, every time)

```markdown
# [Short descriptive title]
**Date:** YYYY-MM-DD
**Project:** ONE LDN consumables dashboard — [area]
**Mode:** Rolling Log + Git Push
**Status:** [Complete / In Progress / Blocked]

---

## Project Context
[Broader project this session sits within. If not the first entry, reference the
prior entry by date and add only what is new or changed.]

## Session Goal
[What this session tried to accomplish, 1–3 sentences. Be precise.]

## State Before This Session
[Where the work stood at session start — what was broken, incomplete, or pending.]

## What Was Done
[Full narrative: explored, built, fixed, decided, abandoned. Include what did NOT
work and why, so the next session doesn't re-tread it. Brief a capable colleague
who wasn't in the room.]

## Artifacts Produced / Modified

| File | What it is | Status | Path |
|------|------------|--------|------|

[Every file touched. If modified, what changed. If deleted, why.]

## Decisions & Reasoning
[Every meaningful choice: decision → options considered → choice → reasoning.
Record who decided, where a human overrode the model, and what was rejected.]

## Corrections Made This Session
[Figures, claims or methods that were wrong and are now fixed, with the wrong
version stated explicitly. If the wrong version is the intuitive one, say so.
N/A if none.]

## Skills / Tooling Used
[Which skills, MCP servers or scripts did the work, and what each contributed.
Flag anything that lives outside the repo and will not survive the container.]

## Current State (end of session)
[Exact state right now: working / partially done / known-broken.]

## Next Steps
[Ordered, specific, actionable. Item 1 must be immediately executable.]

## Open Questions / Blockers
[Unresolved items and what unblocks each. Name who has to decide. N/A if none.]

## Environment & Config Notes
[Repo, branch, PR number, commit hashes. Credential/config NAMES only, never
values. Table and project identifiers, versions bumped, non-obvious config.]

## Notes & Gotchas
[Edge cases, assumptions baked in, traps for future editors. Be specific:
"the burn rate overstates because a delivery triggers a dispenser refill round"
is useful; "some unit issues" is not.]
```

## Reference standard

The **2026-08-05 — "Sheet migration, minimum-stock model, first aid and VAT"** entry
is the standard to match. What makes it good:

- Its *Corrections* section states each wrong figure explicitly (£800.53 as a
  mixed-basis total; a par validated against its own source) rather than quietly
  presenting the fixed version.
- It records **who overrode what** — the human-supplied count basis that killed an
  order of 444 tampons, and the explicit requirement that overrode a computed floor.
- It flags a trap for future editors: the model that generates the CSVs lived in an
  ephemeral scratchpad and would have been unrecoverable.
- Its Next Steps name the exact date, file and column the next session must produce.

## Do-nots

- Do NOT write the log anywhere except `logs/consumables-dashboard_log.md`.
- Do NOT append at the bottom or rewrite prior entries — prepend only.
- Do NOT use a condensed template for "small" sessions — full template, always.
- Do NOT repeat context a prior entry holds — cross-reference by date.
- Do NOT include credential VALUES — names only. This repo is public.
- Do NOT push to `master`; the log commit goes on the working branch.
- Do NOT invoke the contractual docs skills or write to Notion from here.
- Do NOT skip the log because the session "only discussed things" — decisions ARE
  the artifact. The one exception is a no-op PR check-in.
