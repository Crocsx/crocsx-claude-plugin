---
description: Describe every change on this branch and open the pull request on GitHub — title, body from the repo's template, push, create
argument-hint: [<base-commit>] [--draft] (empty = everything since the branch left the default branch)
allowed-tools: Bash, Read, Grep, Glob, Write
---

Open a pull request for the current branch, with a title and body that describe every change in it.

Root: !`git rev-parse --show-toplevel`
Branch: !`git rev-parse --abbrev-ref HEAD`
Upstream: !`git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo none`
Uncommitted: !`git status --porcelain`

## 0. Load project context

Read `.claude/tx-shared/project.md`, relative to the repo root. It holds every project-specific fact this command needs — paths, commands, ticketing, commit and PR-title convention. If a section it needs is missing or still `TODO`, say so rather than guessing.

## 1. Preflight — stop on any of these

- **On the default branch.** The default branch is `git symbolic-ref --short refs/remotes/origin/HEAD` with `origin/` stripped, falling back to `main`. Stop and tell me to branch first, using the branch naming in `project.md § Ticketing`.
- **Uncommitted work.** A PR only carries commits. List what is uncommitted and stop; suggest `tx-split`. Do not commit anything yourself.
- **No commits ahead of the base.** Nothing to open. Stop.
- **`gh` not authenticated.** Run `gh auth status`. If it fails, tell me to run `! gh auth login` and stop.
- **A PR already exists for this branch.** `gh pr view --json number,url,title,state,isDraft`. If one is open, this run *updates* it: same steps, but step 5 uses `gh pr edit` instead of `gh pr create`. Read its current body first and keep anything a human wrote there (screenshots, reviewer notes) that the new body would otherwise drop.

## 2. Build the change set

Base: `$1` if it is a commit, otherwise `$(git merge-base <default-branch> HEAD)`. `--draft` anywhere in the arguments means open as a draft. Range is `<base>..HEAD`.

- `git log --oneline --no-decorate <range>`
- `git diff --stat <range>`
- `git diff <range>` — read all of it. If it is too large for one call, go directory by directory: `git diff <range> -- <path>`.
- For every file with non-trivial changes, `Read` the current full file. Diff hunks hide context.
- Derive the ticket key per `project.md § Ticketing`. Cannot derive one → no key, and say so in the confirmation step.

This command describes the work; it does not audit it. If a review command already ran in this conversation, reuse those findings — unresolved ones become follow-ups or out-of-scope items in **Notes**. Do not re-review from scratch, but do flag anything obviously broken that you notice while reading.

## 3. Write the title and body

**Title** — follow the PR-title rule in `project.md § Commit convention` / `§ Ticketing` exactly, including where the ticket key goes. Verify the shape against `gh pr list --state merged --limit 10 --json title` — merged titles win if they disagree with `project.md`, and tell me if they do. It describes the whole branch, not the last commit. If the branch is one commit, its subject is usually the right title.

**Body** — write it to the scratch directory named in `project.md § Repo shape`, as `pr-<ticket-or-branch>.md`, creating the folder if needed.

Follow the repo's PR template (`project.md § Ticketing`, usually `.github/PULL_REQUEST_TEMPLATE.md`) exactly — same headings, same order. If no template exists, use:

- **Overview** — 2–3 sentences. Scope (feature / refactor / rewrite / fix) and the main behavioral or architectural change.
- **Why** — the problem in the previous implementation: UX, correctness, performance, maintainability, tech debt.
- **Core Changes** — 2–5 numbered groups by area, not one per commit. Name the real files, components, endpoints, and tables.
- **Verification Evidence** — an unchecked-box list of the screenshots and recordings to attach. One line each: route + state + what it proves. Cover the happy path, every new or changed UI state, and the edge cases listed in `project.md § Domain edge cases`. Prefer a recording for anything with a flow or animation.
- **Notes** — real tradeoffs, follow-ups, out-of-scope. Delete the section if there are none.
- **Ticket** — per `project.md § Ticketing`.

End the body with whatever attribution footer the session's instructions require, and none if they say none. Nothing else goes in the file — no working notes, no divider; the whole file is posted.

Never leave the template's instructional placeholder text in the output. Drop a section that has nothing real to say rather than padding it. If the "Why" is not in the commits, the code, or the ticket, stop at the confirmation step and ask me for it rather than posting a guess.

## 4. Writing style — this matters

The PR body is read by teammates in a hurry. Write like an engineer explaining a diff to a colleague.

- Short declarative sentences. One idea per bullet, one line where it fits.
- Say what changed and why, with concrete nouns — real file, component, endpoint, table names.
- No filler adjectives and no LLM tells: comprehensive, robust, seamless, powerful, streamlined, leverage, delve, ensure that, it is worth noting, significantly enhanced, this PR aims to.
- No hype. No repeating the same point across two sections.
- Do not invent motivation.

## 5. Confirm, then push and create

Opening a PR is visible to the whole team, so show me first and wait:

```
Title:  <title>
Base:   <default-branch>  ←  <branch>   (<n> commits, draft: yes/no)
Push:   <what will be pushed — new upstream, or n commits ahead of origin/<branch>>
Body:   <path to the file>
Action: create | update #<number>
```

Plus any open question (missing ticket key, missing "Why", title shape disagreeing with `project.md`). Do not paste the body — I will open the file. Wait for my go-ahead; if I ask for changes, edit the file and re-print this block.

On go-ahead:

1. **Push.** No upstream → `git push -u origin <branch>`. Ahead of upstream → `git push`. Diverged from upstream → stop and tell me; never force-push unless I say so, and then only `--force-with-lease`.
2. **Create or update.**
   - Create: `gh pr create --base <default-branch> --head <branch> --title "<title>" --body-file <path>`, plus `--draft` when asked.
   - Update: `gh pr edit <number> --title "<title>" --body-file <path>`.
3. **Check it landed.** `gh pr view --json url,title,isDraft,baseRefName` and confirm the title, draft state and base match what I approved.

If the repo has a workflow that rewrites PR titles (`project.md § Ticketing` or `.github/workflows/`), say so, since the title may change after creation.

## 6. Report back

In chat: the PR URL, the final title, and a three-line summary of what it covers. Then the **Verification Evidence** items as a short list — those are the screenshots I still have to attach. Do not paste the body.
