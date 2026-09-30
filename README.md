# crocsx-claude-plugin

Project-agnostic `tx-*` skills. The skills hold the process; each repo holds its own
facts in `.claude/tx-shared/project.md`, written by `/tx-init`. The same skill works in
any repo that has that file.

| Skill | What it does |
| --- | --- |
| `tx-init` | Write `AGENTS.md`, `CLAUDE.md` and `.claude/tx-shared/project.md` for a repo |
| `tx-task` | Analyse → agree → implement, with a review gate between steps |
| `tx-review` | Review changes since a base commit, then give test steps |
| `tx-testing` | Turn a branch, commit or range into a hands-on test checklist |
| `tx-split` | Split uncommitted work into small, reviewable commits |
| `tx-pr` | Describe the branch and open (or update) its pull request |
| `tx-testme` | Quiz you on recently changed code |
| `tx-slack` | Recap a Slack thread |
| `tx-nedo` | Daily entries for the NEDO effort report |

## Install

```sh
claude plugin marketplace add ~/work/repositories/crocsx-claude-plugin
claude plugin install crocsx-claude-plugin@crocsx --scope user
```

`--scope user` makes the skills available in every repo. Do not copy them into a repo's
`.claude/skills/` — a copy there drifts from this one.

## Update after editing a skill

The installed plugin is a cached copy, so edits here are not live until you refresh it:

```sh
claude plugin marketplace update crocsx
claude plugin update crocsx-claude-plugin@crocsx
```

Bump `version` in `.claude-plugin/plugin.json` when you change a skill. Restart Claude Code to pick it up.

## Layout

```
.claude-plugin/plugin.json       plugin manifest
.claude-plugin/marketplace.json  lets this repo be added as a marketplace
skills/<name>/SKILL.md           one folder per skill
```

Per repo, not here: `.claude/tx-shared/project.md` (facts) and `.claude/tmp/` (scratch).
