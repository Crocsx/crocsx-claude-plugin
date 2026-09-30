---
description: Bootstrap this repo for the tx-* commands — write an AGENTS.md per project, a CLAUDE.md pointer next to each, and the shared project.md the other commands read
argument-hint: (none) — or `update` to refresh an already-initialised repo
allowed-tools: Bash, Read, Grep, Glob, Write, Edit
---

Set this repo up so the project-agnostic `tx-*` commands have something real to read.

Root: !`git rev-parse --show-toplevel`
Branch: !`git rev-parse --abbrev-ref HEAD`
Uncommitted: !`git status --porcelain`

You produce three things:

1. **`AGENTS.md`** — one at the repo root, one in each project or package. Root explains the whole; each leaf explains itself.
2. **`CLAUDE.md`** — next to each `AGENTS.md`, a pointer file, nothing else.
3. **`.claude/tx-shared/project.md`** — the single project-fact file `tx-task`, `tx-review`, `tx-pr`, `tx-split`, `tx-testme`, and `tx-testing` all read.

**The hard rule for all of it: every statement is evidence-backed.** You are reading this repo, not describing a repo you have seen before. Anything you cannot point at a file for is `TODO:` with a one-line question — never a plausible guess. A confident wrong `AGENTS.md` is worse than no `AGENTS.md`, because five commands will then cite it as law.

---

## 0. Preflight

Check what already exists: `AGENTS.md`, `AGENT.md`, `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, `.claude/tx-shared/project.md`, and anything under `docs/`.

- **Nothing exists** → fresh init.
- **Some exist** → update mode, whether or not I passed `update`. Never overwrite a hand-written doc. Read it, keep everything still true, and present changes as a diff in step 3.
- **A `CLAUDE.md` exists with real content** (not just a pointer) → do not reduce it to a pointer silently. Propose moving its content into the sibling `AGENTS.md` and ask.
- **Both `AGENT.md` and `AGENTS.md` exist anywhere** → stop and ask which one this repo uses. Pick one name and use it everywhere; a split naming convention means half the tooling reads the wrong file.

Default to `AGENTS.md` (plural) when there is nothing to inherit.

---

## 1. Discover the topology

Find every **project root** — a directory that is independently built, tested, or published. Detect by manifest, not by intuition:

`package.json` (and whether it declares `workspaces`), `pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`, `*.sln`, `*.csproj`, `Cargo.toml` (and `[workspace]`), `go.mod`, `pyproject.toml` / `setup.py`, `pom.xml`, `build.gradle`, `mise.toml`, `Taskfile.yml`, `Makefile`, `Dockerfile`, `*.tf`.

Then classify:

- **Single project** — one root, one `AGENTS.md`. Do not manufacture a hierarchy that is not there.
- **Monorepo** — root plus one per workspace member or per solution project.
- **Polyglot repo** — a `backend/` and a `frontend/` that are separate toolchains even without a workspace manifest. Each gets one.

Skip: `node_modules`, build output, generated directories, vendored code, anything gitignored, and any package with no source of its own. **Do not** write an `AGENTS.md` for a package that is three files and a barrel export — fold it into its parent and say so.

Report the list before going further if it exceeds ~8 projects; that usually means the detection is too eager.

---

## 2. Gather evidence, per project

Delegate this. One `Explore` agent per project root, run concurrently. Each one answers, with a file path for every answer:

**Commands** — from the manifest and task runner, not from habit. Read `mise.toml` tasks, `package.json` scripts, `Makefile` targets, `Taskfile.yml`, CI workflow files under `.github/workflows/`. CI is the most honest source: what CI runs is what actually has to pass. Capture build, typecheck, unit test, integration test, e2e, lint, format, dev server, migration.

**Layering and dependency direction** — infer from real imports, not from folder names. Which layer imports which. Whether the rule is enforced (an `.eslintrc` boundary rule, an architecture test, a project reference graph) or merely observed.

**Conventions with teeth** — path aliases and their tiers (`tsconfig.json` `paths`, `.csproj` references), error-handling pattern (exceptions vs. a result type — read three call sites, not one), where business logic is allowed to live, i18n setup and locale bundles, design-system package and whether components are actually reused from it, generated code and what generates it.

**Docs that already exist** — every `README.md`, `docs/**`, `plans/**`, ADRs. These become the *Docs map*; they are the files a future review checks for drift.

**Test and fixture conventions** — naming, helper/builder/fake locations, integration test markers, what needs Docker.

**Domain edge cases** — the failure modes this product has that a generic checklist misses. Find them in error handling, retry logic, connection state, feature flags, permission checks, locale lists, device or hardware handling. This section is the one most likely to be empty on a fresh init; leaving it thin is fine, faking it is not.

Separately, yourself:

- **Commit convention** — `git log --oneline -50`. Report the *observed* format: type/scope shape, colon or no colon, casing, imperative or not, max subject length, trailers in use. If the log is inconsistent, say so and show the two most common shapes rather than picking a winner.
- **Ticketing** — `git branch -a --sort=-committerdate | head -30`. Is there a ticket key in branch names? What shape? Is there a PR template at `.github/PULL_REQUEST_TEMPLATE.md`?

---

## 3. Show me the plan and wait

Print, before writing anything:

| Path | Action | Basis |
| --- | --- | --- |

`Action` is `create`, `update`, or `leave alone`. `Basis` is the manifest or doc that justifies it.

Then:

- **Open questions** — every `TODO:` you are about to write, as a numbered list, each with your recommended default so I can answer "1 yes, 2 the second one, 3 skip". This is the part that determines whether the output is useful; do not bury it.
- **Conflicts** — anywhere two sources disagree (a script in `package.json` that CI does not run, a doc that describes a directory that no longer exists, two different aliases for the same path). List them. Do not resolve them yourself.
- **Low confidence** — anything you inferred from a single file.

Stop and wait for my go-ahead. If I answer the questions, fold the answers in and write; do not re-print the whole plan unless the shape changed.

---

## 4. Write the AGENTS.md tree

**Root `AGENTS.md`** — the map, not the detail. Target 60–120 lines:

- One paragraph: what this repo is and what ships from it.
- The project table: path, what it is, its stack, link to its `AGENTS.md`.
- How the pieces talk to each other — contracts, generated code, API boundaries.
- Repo-wide commands only (the ones that work from the root).
- Repo-wide conventions: commit format, branch naming, where docs live.
- What is *not* here — anything a reader would expect and not find.

**Per-project `AGENTS.md`** — target 50–150 lines:

- What this project is and what depends on it.
- Directory layout, with the rule behind it, not just a `tree` dump.
- Layering and dependency direction, and how it is enforced.
- Its conventions: aliases, error handling, naming, where each kind of code goes.
- Its commands, as a table.
- Testing: what to write, where it goes, what needs Docker.
- Gotchas — the things that break a newcomer. This is the highest-value section and the hardest to fake; if you have nothing real, write the heading with a `TODO:` and let me fill it.

Rules for both:

- No duplication between root and leaf. A fact lives in exactly one file; the other links to it.
- Concrete nouns — real paths, real command strings, real type names.
- No filler. No "this project follows best practices". If a section has nothing true to say, cut it.
- Tables for commands and paths, prose for reasoning.
- No LLM tells: comprehensive, robust, seamless, leverage, ensure that, it is worth noting.

**`CLAUDE.md`** next to each `AGENTS.md`, and nothing more than:

```markdown
@AGENTS.md
```

The `@`-import pulls the sibling file in. If a repo convention or a tool in use needs prose instead, write one line — `See AGENTS.md in this directory.` — and no third line. Never let a `CLAUDE.md` accumulate its own rules; that is how the two files drift apart.

---

## 5. Write `.claude/tx-shared/project.md`

This file has a **fixed set of headings** because the other commands reference them by name. Emit all of them, in this order, even when a section is thin — an empty section says "checked, nothing here", a missing section makes the command that needs it guess:

```
## Stack
## Repo shape
## Commands
## Docs map
## Guidelines checklist
## Commit convention
## Ticketing
## Domain edge cases
```

What goes where:

- **Stack** — table of side/tech/root. One line on the task runner and package manager.
- **Repo shape** — the placement and layering rules a command needs to know *without* opening `AGENTS.md`. This is a summary with pointers, not a copy. Include the scratch directory the commands write to (default `.claude/tmp/`, gitignored — add it to `.gitignore` if it is not there).
- **Commands** — the table from step 2. Exact strings. Add the formatters and linters that already own style, so review knows not to comment on it.
- **Docs map** — every doc found in step 2, with one line on what it governs. This is the drift-check list.
- **Guidelines checklist** — the enforceable rules, named, grouped by side. `tx-review` cites these by name and is instructed not to invent any that are not here, so a thin list means a weak review. Each rule: name, one line, and where it is enforced or documented.
- **Commit convention** — the observed format, plus the instruction to verify against `git log --oneline -20`.
- **Ticketing** — tracker, how to derive the key from the branch (including case normalisation, e.g. `feat/roms-4740` → `ROMS-4740`), PR template path.
- **Domain edge cases** — the product-specific failure modes. Used by `tx-review` for UI checks and `tx-pr` for evidence lists.

Head the file with: *"Single source of project-specific truth for the `tx-*` commands. The commands hold process; this file holds facts. `TODO:` means not filled in — a command that needs a `TODO:` section must say so rather than guess."*

Keep it under ~200 lines. Past that the commands reading it will summarise instead of applying it. If it wants to be longer, the excess belongs in an `AGENTS.md` and the entry here becomes a pointer.

---

## 6. Verify before you report

Do not claim it works. Check:

1. **Every command in the table runs.** Where a dry check exists (`mise tasks`, `pnpm run`, `dotnet --list-sdks`, `make -n <target>`), run it and confirm the task exists. Do not execute test suites or builds. Anything unverifiable → mark it `unverified` in the table.
2. **Every path cited exists.** Glob each one from the three files.
3. **Every `@AGENTS.md` import resolves** to a real sibling.
4. **No unanswered `TODO:` I was not shown** in step 3.
5. **`.claude/tmp/` is gitignored, and `.claude/` as a whole is not** — `project.md` and the `AGENTS.md` tree are committed repo truth.

Fix what you can, list what you cannot.

## 7. Report

- The file tree you wrote or changed, as paths.
- The `TODO:`s still open, numbered — the list I need to come back and answer.
- Anything in step 6 that failed verification.
- One line: which of `tx-task`, `tx-review`, `tx-pr`, `tx-split`, `tx-testme`, `tx-testing` are now fully backed, and which are running on a thin section.

Do not paste the file contents. Do not commit — that is `tx-split`'s job.
