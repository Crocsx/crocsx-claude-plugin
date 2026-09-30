---
description: Split all uncommitted work into small, logically grouped commits that are easy to review
allowed-tools: Bash, Read, Grep, Glob
---

Split everything uncommitted into a sequence of self-contained commits, each one thing a reviewer can read in isolation.

Status: !`git status --porcelain`
Branch: !`git rev-parse --abbrev-ref HEAD`

## 0. Load project context

Read `.claude/tx-shared/project.md` first — you need `§ Repo shape` for the grouping order and `§ Commit convention` for the message format.

## 1. Read everything first

- `git diff` (unstaged), `git diff --cached` (staged), `git status --porcelain`.
- Read every untracked file in full — they are usually the bulk of a new feature.
- For non-trivial modified files, `Read` the current full file, not just the hunks.

If the index already has staged changes, tell me and ask whether to `git reset` so the grouping starts clean, or keep them as the first commit. Never unstage without asking.

If nothing is uncommitted, say so and stop.

## 2. Group by intent

One commit = one reason to change. Order groups by dependency, using the layering in `project.md § Repo shape` — a layer's own commit comes before anything that consumes it. General order:

1. Tooling, config, deps.
2. Shared primitives — shared UI package, shared utils and types, contract definitions plus their regenerated output.
3. Backend, layer by layer, innermost first, per the layer order in `project.md`.
4. The feature itself, split by unit when it is large: data layer, then components, then the page that wires them.
5. i18n copy for that feature.
6. Unrelated fixes — one commit each, never folded into the feature.
7. Formatter or lint drift on files the feature did not otherwise touch.

Rules:
- Dependencies come before their consumers, so the branch reads top-down and each commit builds on its own.
- A test goes with the code it covers. A story goes with its component.
- i18n copy goes with the feature that uses the keys, unless it is a shared-vocabulary rework — then it stands alone.
- Generated contract output goes in the same commit as the source definition that produced it (see `project.md § Guidelines checklist → Contracts`).
- An unrelated fix or rename never rides along in a feature commit. That is the whole point of this exercise.
- Aim for 3–8 commits. If a group exceeds ~15 files or mixes two ideas, split it.
- If a single file contains changes belonging to two groups, flag it. Prefer putting it in the dominant commit and saying so. Only split it at hunk level if it genuinely matters — write the hunks to a patch file and `git apply --cached <patch>`, since `git add -p` and `git add -i` are not available here.

## 3. Show me the plan and wait

Print a table before touching anything:

| # | Commit message | Files | Why grouped |

Plus a **Notes** line for anything you had to compromise on — mixed files, changes you could not cleanly separate, work that looks unfinished or debug-only and maybe should not be committed at all.

Then stop and wait for my go-ahead. Do not commit until I approve. If I change the grouping, re-print the table.

## 4. Commit

Follow `project.md § Commit convention` exactly, and verify it against `git log --oneline -20` — the log wins if the two disagree, and tell me if they do.

For each commit: `git add -- <exact paths>`, `git diff --cached --stat` to confirm the staged set matches the plan, then commit. Never `git add -A` or `git add .`.

Do not push, do not amend earlier commits, do not rebase.

## 5. Report

Print `git log --oneline <first-new-commit>~1..HEAD` and `git status --porcelain`. Confirm nothing was left behind, or say exactly what you deliberately left uncommitted and why.
