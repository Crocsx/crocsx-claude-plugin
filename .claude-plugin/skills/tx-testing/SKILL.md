---
description: Turn the changes in a branch, a commit or a range into a hands-on test checklist — what to read, how to set up, and one Setup/Action/Expected table per changed behaviour
argument-hint: [<base-commit> | <commit>^! | <A>..<B> | <branch>] (empty = this branch since it left the default branch)
allowed-tools: Bash, Read, Grep, Glob
---

Write the checklist a reviewer works through to see every change in `$1` actually working. Report only — do not run the app, do not fix anything, do not commit.

Root: !`git rev-parse --show-toplevel`
Branch: !`git rev-parse --abbrev-ref HEAD`
Uncommitted: !`git status --porcelain`
Shell: !`basename "$SHELL"`

## 0. Load project context

Read `.claude/tx-shared/project.md`, relative to the repo root. You need:

- `§ Commands` — the dev, harness and gate commands you will quote.
- `§ Docs map` — find the doc for the local test harness (a simulator, a fake backend, fixtures, seed data). Read it in full.
- `§ Domain edge cases` — each one the diff can reach becomes a row.
- `§ Stack` — the default UI language, if the product has one.

Then read the root `AGENTS.md` and the nearest `AGENTS.md` for each touched area. If `project.md` is missing, say so and fall back to `AGENTS.md` and the README; if a section you need is `TODO`, say which and work without it rather than inventing it.

## 1. Build the change set

Resolve `$1` to a range:

| `$1` | Range |
| --- | --- |
| empty | `$(git merge-base <default-branch> HEAD)..HEAD`, plus uncommitted work |
| contains `..` or ends in `^!` | as given (`<sha>^!` is one commit) |
| a branch name | `$(git merge-base <default-branch> <branch>)..<branch>` |
| any other commit | `<commit>..HEAD`, plus uncommitted work — same meaning as `tx-review` |

The default branch is `git symbolic-ref --short refs/remotes/origin/HEAD` with the `origin/` stripped, falling back to `main`. Say which range you resolved to in the first line of the output.

Then:

- `git log --oneline --no-decorate <range>`
- `git diff --stat <range>`
- `git diff <range>` — read all of it. Too large for one call → directory by directory.
- When the range reaches `HEAD`: `git diff HEAD` and untracked files, read in full. Mark rows that test uncommitted work.
- `Read` the current full file for every non-trivial change. You are predicting runtime behaviour; a hunk alone will mislead you.

If `tx-review` already ran in this conversation, reuse its findings: every **Blocking** and **Should fix** item gets a row that proves it is fixed or still broken, tagged with the finding's label (`S1`, `Should fix 2`). Do not re-review.

## 2. Map changes to behaviours

List the behaviours the diff changes, not the files. A behaviour is something an operator or a caller can trigger and observe: an action, an error path, a retry, a navigation, a dialog, a message, a sound, a state that survives or resets. For each, note:

- **Trigger** — the UI action or call that reaches it.
- **Branches** — every outcome the new code distinguishes: success, each error kind, each retry/stop condition, each answer to a prompt.
- **Observable** — what the tester sees or can query: the exact text, the code shown, where navigation lands, what the harness state reports.
- **Adjacent behaviour** — unchanged code the diff sits next to that could regress, and any guard that must still hold (a case that must *not* retry, a key that must *not* confirm).

Group behaviours by user-facing flow (start X, end X, scanning, save Y). Those groups become sections C onward.

## 3. Derive every value — this is the part that matters

A checklist with a wrong expected value sends the tester chasing a bug that does not exist. Nothing in a table may be guessed.

**Setup must exist.** For every harness call you write, find the handler in the harness source and confirm the endpoint, every parameter name and every value. When a parameter is an enum number, confirm which member it maps to on the side that reads it — the number that means "shelf disconnected" in one enum means something else in the next. A state the harness cannot produce goes in **Could not set up here**, never in a table.

**Expected text comes from the bundle.** Follow the code path to the translation key it uses and quote the string from the bundle in the language the tester will use. Quote enough to recognise it and elide the rest with `…`. Interpolated values are filled in with what this setup produces.

**Codes, counts and timings are computed.** An error code shown to the user is worked out from the formula in the code. A retry count comes from the policy that applies to *this* error. A duration is the sum of the delays and timeouts the code actually waits (`~17s`), rounded, with `~`. If a value depends on something the tester controls (how fast they act), say what to do within what window.

**Navigation comes from the route table.** Name the URL where an answer lands, from the project's route constants.

**Preconditions are explicit.** If a row only makes sense mid-session, say "Start X first" in the section intro. If the harness keeps state between tests, say how to reset it and when. If the dev command leaves a committed env value in place that changes the behaviour under test, flag it in Setup.

When a value cannot be derived from the code, say so in that cell (`unverified: …`) rather than dropping the row.

## 4. Output

Print in chat. No file. Lead with one line: the range, the commit count, and how many behaviours the checklist covers. Then:

```
Here's a checklist you can work through in order. Section A is for reading the code; sections B–<last> test each change against <harness>.
```

**A. Read the code (about N min, in this order)** — table `# | File | What to look for`.

- Order by the flow of the change, not alphabetically: the definition or table the change is built on first, then the pipeline that uses it, then state, then the UI that shows it, then wiring and transport.
- One row per file, or one row for a group of files that are read together (`a.ts + b.ts`).
- "What to look for" names the specific thing: the function, the branch, the rule, and what to compare it against — including a file in a sibling repo when the change claims parity with it (`compare with <repo> <file>:<lines>`).
- Skip files whose change is copy, formatting or a rename. Estimate ~2 min per row.

**B. Setup** — a fenced block of the commands to run, in `$SHELL`'s syntax (fish functions for fish, shell functions for bash/zsh). Define a one-word helper for the harness call you will repeat, and use it in every table. Then bullets for: signing in, the language to set so the quoted text matches, how to reset between tests, any precondition shared by several sections, env values the tester should know about, and how to force the fault kinds the tables use.

**C onward — one section per flow.** Title: the flow, then the review labels or ticket rules it covers in brackets (`Start restocking (S1, S2, S5)`). One intro line for shared preconditions. Then a table `# | Setup | Action | Expected`:

- One behaviour per row. Setup is the harness call or state, Action is what the tester does in the UI, Expected is what they see.
- Rows in the same section that share a setup write it once and use `...&error=14` for the delta after that.
- Cover, in this order: the happy path when the diff changed it, each changed branch, each prompt answer and where it leads, then the adjacent guards that must still hold.
- Chain rows that depend on each other and say so ("Within ~20s of 4, …").
- A behaviour that is a product decision rather than a clear pass/fail gets a row whose Expected ends with "this is the open question from <source>. Decide if that's acceptable".

**Next-to-last section — General checks.** Bullets, not a table:

- **Language** — switch to the other shipped language (the default one, if the tables used English) and repeat the two rows with the most text. Quote the one string whose translation is most likely to be wrong.
- **Busy / disabled state** during any wait the diff introduces, and when it clears.
- **Domain edge cases** from `project.md` the diff can reach and no table already covers — one line each.
- **Final gate** — the CI gate command from `project.md § Commands`, plus any other command that covers the touched area.

**Last — Could not set up here.** A short paragraph: each case the harness cannot produce, why, and what to expect if the tester can reach it another way. Say "Nothing" if every behaviour is covered.

Style: tables for tests, short bullets for setup. Concrete nouns — real commands, real URLs, real strings. No filler, no restating the diff, no LLM tells (comprehensive, robust, seamless, ensure that, it is worth noting). If a flow the diff touches has no testable surface, drop its section and name it in **Could not set up here** instead of padding.

## 5. Before you print

Check your own tables:

1. Every harness call you wrote matches a handler and its parameter names in the harness source.
2. Every quoted string is in the bundle for the language set in **B**.
3. Every code, count and duration was computed from the code, not recalled.
4. Every changed behaviour from step 2 has a row or is under **Could not set up here**.
5. Every **Blocking** / **Should fix** finding from an earlier `tx-review` in this conversation has a row.

Fix what fails. Anything still unverified is marked `unverified:` in its cell.
