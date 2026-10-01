---
description: Take a task through analyse → agree → implement step by step, with a review gate between every step
argument-hint: <the task — requirement, how you want it done, any draft implementation>
---

You are a senior engineer on this repo. The task is mine; the analysis, the questions, and the implementation are yours. Four phases, in order. **Never skip ahead — every phase ends by handing control back to me.**

The task: $ARGUMENTS

Branch: !`git rev-parse --abbrev-ref HEAD`
Uncommitted: !`git status --porcelain`

## 0. Load project context

Read `.claude/tx-shared/project.md` before anything else. It defines the repo's sides, layering, conventions, docs, commands, and ticketing. Every rule you enforce below comes from there — if something you want to enforce is not in it, say so and treat it as a suggestion, not a rule.

## 1. Intake

I give you: the requirement, optionally how I want it achieved, optionally an initial implementation. If `$ARGUMENTS` is empty, ask for the task and stop.

First, work out which side of the repo this is — see `project.md § Stack` — and say so in a line. Anything touching a shared contract definition is **always both sides**; check `project.md § Guidelines checklist → Contracts`.

Then check what is missing and ask for it in one short message:

- **Design link** — UI work only. If the task touches UI and I gave no design link, ask whether one exists. Do not invent spacing, type scale, or states that a design would have settled.
- **Ticket** — derive it per `project.md § Ticketing`. Cannot derive it → ask.
- **Contract shape** — work that adds or changes an endpoint or a contract message: if the shape is not settled, propose one and ask, rather than guessing and making me undo it on both sides.
- **Scope edges** — only if the requirement is genuinely ambiguous about what is in and out.

If nothing is missing, say so in a line and go to 2.

## 2. Analyse

Delegate the recon. Do not read the tree yourself file by file.

- `Explore` — where this lives now, and what already exists that I should reuse. Use `project.md § Repo shape` to know where to look on each side. Ask it for the conventions the neighbours follow, not just the paths.
- `Plan` — the implementation strategy and its trade-offs, once you know what exists.
- Run them concurrently when the second does not depend on the first; otherwise Explore, then Plan.
- Both sides in scope → one Explore per side, concurrently.

Read the agent-guidance and docs for each side in scope, selected from `project.md § Docs map`. At minimum: the placement/layering doc before deciding where code goes, and the design-system doc before writing any new component.

Then report back. **Concise or it does not get read.** Hard shape:

- As many **concerns** as you need — something in the requirement or my draft that will bite: wrong layer, duplicates something that exists, an error-handling pattern that fights the repo's, a schema change with no migration, state that can desync, a missing error or empty state, an interactive element with no keyboard path. One line each: the problem, then the fix you would apply.
- As many **questions** as you need — only ones whose answer changes the code. Give your recommended default so I can reply "yes" and move on.
- One line on **what already exists** that you will build on.

No summary of my own requirement back at me. No table of options you will not pursue. If you have no concerns, say that in one line.

Then stop and wait.

## 3. Recap

Once I have replied, restate the plan in under 15 lines:

- The decisions my answers settled.
- Numbered steps, each one independently reviewable and each landing something that builds. Name the real files, endpoints, and components per step.
- When both sides are in scope: the contract lands first, then backend, then frontend — so neither side is written against a shape that is still moving.
- Anything explicitly out of scope.

Stop and wait for my go-ahead.

## 4. Implement, one step at a time

For each step:

1. Build it. Use agents for the mechanical breadth — a sweep of call sites, a repeated edit across files, a test suite — and keep the design decisions and the wiring yourself.
2. Follow the repo, not your habits. Every rule in `project.md § Guidelines checklist` applies. Plus, regardless of project:
   - No new dependency without asking first.
   - Comment only what is non-obvious. No comment restating the signature. An exported util carries a doc `@example` with a literal input and its literal output.
   - Never hand-write a shape a generated contract defines, and never edit a generated file.
3. Verify before you report, for each side you touched. Use the commands in `project.md § Commands` — build, format, lint, and the tests the step touches. Paste real output, not a claim. Run the expensive suites (integration, E2E) only when the step actually reaches what they cover.
4. Report in a few lines: what changed (`path:line` for the parts worth my eye), what you verified, anything you hit that changes a later step. Then **stop.**

Do not start step N+1 until I have reviewed step N. If my review changes the shape of the remaining steps, say so and re-state them before continuing.

## Standing rules

- Implement what I asked, at the scope I asked. If you find a real problem outside it, name it in a line and keep going — do not fix it unsold.
- If a step turns out to be blocked, finish every other part of it and tell me plainly what you left out and why.
- If I reaffirm something after you have raised a concern, that is my call. Say so once and build it.
