---
description: Review all changes since a base commit against project guidelines, best practice, and the docs, then give test steps
argument-hint: <base-commit> (the commit BEFORE your first change)
allowed-tools: Bash, Read, Grep, Glob
---

Review every change from `$1` to `HEAD`. Report only — do not fix anything unless I ask.

Branch: !`git rev-parse --abbrev-ref HEAD`
Uncommitted: !`git status --porcelain`

## 0. Load project context

Read `.claude/tx-shared/project.md`, relative to the repo root (!`git rev-parse --show-toplevel`). The guidelines you check against, the docs you compare, the commands you list, and the edge cases you cover all come from there. If a section it needs is missing or still `TODO`, say so rather than inventing a rule.

## 1. Build the change set

If `$1` is empty, stop and ask for it. Range is `$1..HEAD`.

- `git log --oneline --no-decorate $1..HEAD`
- `git diff --stat $1..HEAD`
- `git diff $1..HEAD` — read all of it. If it is too large for one call, go directory by directory: `git diff $1..HEAD -- <path>`.
- `git status --porcelain` and `git diff HEAD` — include uncommitted work, and mark findings against it as uncommitted.
- Untracked files are part of the change set: read them in full.
- For every file with non-trivial changes, `Read` the current full file. Diff hunks hide context, and a finding based on a hunk alone is usually wrong.
- Read the nearest `AGENTS.md` for the conventions that apply, plus any doc in `project.md § Docs map` that governs the area the diff touches.
- Search before calling anything new or duplicated. `project.md § Repo shape` says where the shared packages are.

## 2. Review

Work through each of these. Skip a heading only if the diff genuinely does not touch it.

**Correctness**
- Logic bugs, off-by-one, inverted conditions, unhandled null/undefined.
- Async: unawaited promises, races, missing cleanup or abort, stale closures, effects that refire.
- State that can desync — form vs. server, optimistic updates, autosave, cache invalidation.
- Missing loading, empty, and error states on new UI.
- Error paths: what the user sees when a request fails, or when any failure mode in `project.md § Domain edge cases` happens.

**Project guidelines**
Check against `project.md § Guidelines checklist`. Cite the rule you are applying by name. Do not apply a rule that is not in that file, and do not carry one in from another repo — if the code does something you think is wrong but no rule covers it, put it under *Industry standard* as a judgement call instead.

**Docs and agent guidance still in sync**
Docs drift silently. Any change that alters structure, conventions, commands, routes, or contracts has to be reflected in the prose that describes them.

Work out which entries in `project.md § Docs map` the diff touches, then read them and compare against what the code now does.

Report each mismatch as one of:

- **Doc is now wrong** — it describes the old behavior. → update the doc.
- **Doc is silent** — a new pattern, directory, task, route, or convention nothing documents. → add it, or say why it does not need documenting.
- **Code breaks the doc** — the doc rule is still right and the code violates it. → fix the code, not the doc.

For each, give `doc/path.md:line`, what it claims, what is actually true now, and your recommendation with a one-line reason. When the call is genuinely ambiguous — the code is a deliberate new direction — say so and ask me which way to go. Do not edit any doc in this command; it reports only.

**Industry standard / best practice**
- Type safety: `any`, non-null assertions, casts that paper over a real type problem, missing discriminated unions.
- Boundaries: business logic leaking into components or endpoints, a module that knows too much about another.
- Naming that does not match what the thing does.
- Duplicated logic that already exists in the repo — search first, then claim it.
- Accessibility on new interactive UI: label, role, keyboard path, focus management, contrast.
- Performance where it is real, not theoretical: N+1 queries, unmemoized expensive renders, unbounded lists, work in a hot loop.
- Security: authorization on new endpoints, input validation, secrets, injection, data in logs.

**Could be improved**
Concrete simplifications: something that could be deleted, a shared helper that fits, a smaller API, a clearer control flow. Keep these separate from defects.

**Pre-existing issues**
Problems in the touched code that this work did not introduce. Keep them in their own list — a reviewer will raise them and it should be clear they are not from this PR.

**Hygiene**
Leftover debug code and stray logging, commented-out blocks, dead exports and unused files, stray `TODO`s, junk commit messages that need rewording or squashing before merge, new logic with no test.

Rules for findings: verify each one by reading the code. Cite `path/to/file.ts:123`. State the concrete failure — inputs or state → wrong result. Drop anything you cannot back up; a short honest list beats a padded one. No nitpicks that the formatters and linters in `project.md § Commands` already handle.

## 3. Test steps

End with numbered steps, in the order I should run them.

**Commands** — only the ones this diff actually touches, quoted from `project.md § Commands`. Reproduce them as a table with the scope and the exact command.

**UI checks** — a table of `Route | Steps | Expected`. Cover the happy path, every new or changed state, and the edge cases your findings exposed. Work through `project.md § Domain edge cases` and include each one the diff can reach.

Name any test you think is missing and worth writing.

## 4. Output

Report in chat, no file. Order: **Blocking**, **Should fix**, **Docs out of sync**, **Improvements**, **Pre-existing**, **Test steps**. One line per finding plus a short why. Lead with a two-line verdict: is this mergeable, and what is the biggest risk.

Under **Docs out of sync**, mark each line `fix code` or `update doc` so I can hand you the list and say "do the doc ones". If every doc that covers the change is accurate, say `Docs: in sync` in one line rather than omitting the section — I want to know it was checked.
