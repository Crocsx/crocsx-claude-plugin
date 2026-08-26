---
description: Turn all changes since a base commit into a ready-to-paste PR description
argument-hint: <base-commit> (the commit BEFORE your first change)
allowed-tools: Bash, Read, Grep, Glob, Write
---

Describe every change from `$1` to `HEAD` as a PR description file.

Branch: !`git rev-parse --abbrev-ref HEAD`
Uncommitted: !`git status --porcelain`

## 0. Load project context

Read `.claude/tx-shared/project.md`, relative to the repo root (!`git rev-parse --show-toplevel`). It holds every project-specific fact this command needs — paths, commands, ticketing, conventions. If a section it needs is missing or still `TODO`, say so rather than guessing.

## 1. Build the change set

If `$1` is empty, stop and ask for it. Range is `$1..HEAD`.

- `git log --oneline --no-decorate $1..HEAD`
- `git diff --stat $1..HEAD`
- `git diff $1..HEAD` — read all of it. If it is too large for one call, go directory by directory: `git diff $1..HEAD -- <path>`.
- `git status --porcelain` and `git diff HEAD` — include uncommitted work, and say in the PR body that it is uncommitted.
- Untracked files are part of the change set: read them in full. They are usually the bulk of a new feature.
- For every file with non-trivial changes, `Read` the current full file. Diff hunks hide context.
- Derive the ticket key per `project.md § Ticketing`. Cannot derive one → `TODO`.

This command describes the work; it does not audit it. If a review command already ran in this conversation, reuse those findings — unresolved ones become follow-ups or out-of-scope items in **Notes**. Do not re-review from scratch, but do flag anything obviously broken that you notice while reading.

## 2. Write the file

Write to the scratch directory named in `project.md § Repo shape`, as `pr-<ticket-or-branch>.md`, creating the folder if needed.

Follow the repo's PR template (`project.md § Ticketing`) exactly — same headings, same order. If no template exists, use:

- **Overview** — 2–3 sentences. Scope (feature / refactor / rewrite / fix) and the main behavioral or architectural change.
- **Why** — the problem in the previous implementation: UX, correctness, performance, maintainability, tech debt.
- **Core Changes** — 2–5 numbered groups by area, not one per commit. Name the real files, components, endpoints, and tables.
- **Verification Evidence** — an unchecked-box list of the screenshots and recordings to attach. One line each: route + state + what it proves. Cover the happy path, every new or changed UI state, and the edge cases listed in `project.md § Domain edge cases`. Prefer a recording for anything with a flow or animation.
- **Notes** — real tradeoffs, follow-ups, out-of-scope. Delete the section if there are none.
- **Ticket** — per `project.md § Ticketing`.

Then a divider and the working notes, which are not pasted into the PR:

```
<!-- ───────── end of PR body ───────── -->

# Not part of the PR body

## Evidence to capture
## Tests to run before opening the PR
## Open questions for the author
```

**Tests to run** — only the commands this diff touches, taken from `project.md § Commands`. Do not invent a command that is not in that table.

Never leave the template's instructional placeholder text in the output. Drop a section that has nothing real to say rather than padding it.

## 3. Writing style — this matters

The PR body is read by teammates in a hurry. Write like an engineer explaining a diff to a colleague.

- Short declarative sentences. One idea per bullet, one line where it fits.
- Say what changed and why, with concrete nouns — real file, component, endpoint, table names.
- No filler adjectives and no LLM tells: comprehensive, robust, seamless, powerful, streamlined, leverage, delve, ensure that, it is worth noting, significantly enhanced, this PR aims to.
- No hype. No repeating the same point across two sections.
- Do not invent motivation. If the "Why" is not in the commits, the code, or the ticket, write a `TODO:` line for me instead of guessing.

## 4. Report back

In chat, print only the file path and a three-line summary of what the PR covers. Do not paste the file contents.
