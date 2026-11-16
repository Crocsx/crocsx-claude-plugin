---
description: List what an upcoming STG or PROD release contains. Give an environment and a commit; finds what is live on that environment now (tx-manifests, git tags, GitHub releases, deploy runs, VERSION files), collects the PRs between it and the commit, and lists only what users see or do differently, plus what the team must know. Can also write the list up as EN + JA Google Docs and draft a Slack announcement. Project skills (tx-release-retail) build on it. Use whenever the user asks what is in a release, for release notes, a changelog for a deploy, or mentions リリースノート.
argument-hint: <stg|prod> [<commit>, default origin/main] [live FE=<version> BE=<version>]
---

# Release

Two inputs: the **environment** and the **commit** about to be released there (default:
the tip of `origin/main`). The base is what is live on that environment now. The output
is a short list of changes for **non-technical** readers, store and operations staff:
what looks or behaves differently, not how it was built.

`<skill>` is this skill's base directory. Scratch files go in
`.claude/tmp/release/<env>/` in the repo. Run every script from the repo root:
`prs.json` stores image paths relative to it.

Steps 1–4 always run. Steps 5–7 run when the user asks for them, or when a project skill
says to.

## 1. Project config

Read the `## Release notes` section of `.claude/tx-shared/project.md`, a ```json block
(a project skill may pass its own config file instead):

```json
{
  "project": "tx-retail",
  "displayName": "TX Retail (Autail)",
  "repo": "telexistence-inc/tx-retail",
  "components": [
    {"label": "FE", "name": "Web", "manifestApp": "tx-autail-web", "paths": ["frontend/"],
     "workflow": "cicd-frontend-web-deploy-manual.yaml", "versionFile": "frontend/apps/web/VERSION",
     "locales": {"en": "frontend/apps/web/app/**/en-US.json", "ja": "frontend/apps/web/app/**/ja-JP.json"}},
    {"label": "BE", "name": "API", "manifestApp": "tx-autail-api", "paths": ["backend/"],
     "workflow": "cd-backend.yaml", "versionFile": "backend/VERSION"}
  ]
}
```

Only `project`, `repo` and `components[].label` are required. Every other key switches on
a fallback in step 2. `tagGlob` (`{"prod": "v[0-9]*", "stg": "v[0-9]*-stg"}`) is for
projects that tag each deploy. `label` is `""` for a one-component project.

**No section yet?** Discover it from the deploy workflows (`.github/workflows/`),
`overlays/<env>/` in tx-manifests, `git tag`, `gh release list`, `VERSION` files and the
locale files. Show the block, and on a yes append it to `project.md`.

## 2. Find the range

The **base** is what is live on the environment; the **target** is the commit given.

```sh
git fetch origin -q
python3 -I <skill>/scripts/release_range.py --project-md .claude/tx-shared/project.md --env <env> \
  > .claude/tmp/release/<env>/range.json
```

In the output, each component's `current` is what is live, so its `sha` is the base. The
script's `previous` is the release before that, and is not used here. If the user named
the live versions, pass them as `--current FE=0.4.28-prod --current BE=0.4.20`. The
script tries, in order:

| Question | Sources |
| --- | --- |
| Live version | user → tx-manifests history → env tag line → GitHub Releases (prod) |
| Commit of a version | git tag → sha inside the version → the deploy run that built it → the commit that bumped the version file |

Confidence `high` or `medium` → carry on. `low` → confirm it against the deploy runs
(`gh run list --workflow <workflow>`: the run that built the live version names its
head sha) before trusting it, and ask the user only if that doesn't settle it. Nothing
live yet → offer "everything up to the commit" or a start commit they name.

Resolve the target to a full sha (`git rev-parse <commit>`). If base and target are the
same, there is nothing to release: say so and stop.

## 3. Collect the PRs

```sh
python3 -I <skill>/scripts/collect_prs.py --repo <repo> \
  --range FE=<base sha>..<target sha> --range BE=<base sha>..<target sha> \
  --component FE=frontend/ --component BE=backend/ \
  --out .claude/tmp/release/<env>/prs.json --download .claude/tmp/release/<env>/img
```

Each component has its own base, since they deploy separately. `prs.json` holds each
PR's title, body, images (`asset` id, `local` copy) and components. `commitsWithoutPr`
lists direct pushes.

## 4. Pick what to tell, and list it

Read each PR body. Keep a change only if a user **sees or does something differently**:
a new button or message, a screen that looks different, a step that behaves
differently, an error that no longer happens. Refactors, dependency updates, CI, tests
and developer tooling stay out of the user list.

**Team notes** are the exception: changes the team must know about although users don't
see them, such as a new version format or a new deploy or hotfix flow. Keep them in a
separate short list. A version format change users can see (e.g. on a settings page)
goes in the user list too.

**Deploy notes**: say whether the release needs a database migration (any change under
the migrations folder or to entities) and whether it adds, renames or removes required
config. Check the diff; don't infer it from PR titles.

**The merge commit is what ships.** A PR body can promise something a later push
removed. If a body's claim matters, check it at the target sha
(`git show <target sha>:<path>`), and drop screenshots of a version that didn't ship.

For each kept change:

- **Label**: `New` (新機能), `Changed` (変更) or `Fixed` (修正).
- **Title**: what the user notices, in plain words, about 8 words.
  "Log out works", not "Wire logout to the SSO endpoints".
- **One sentence**: what they see or must do now. No technical terms: no API, server,
  backend, frontend, cache, endpoint, component or field names.
- **One screenshot** from the PR, if one shows the change.
- **PR link**: `Details: PR #N` (`詳細: PR #N`). Merge PRs that make one change into one
  entry and link the main one.

Quote on-screen text exactly. With `locales` set, grep those files at the target sha:
the English text for EN, the Japanese text for JA, in 「」. Never translate a label
yourself, because the app's Japanese often differs (Redo → 「やり直す」, Not Started →
「実行前」).

Order: what users will notice most first.

**Screenshots.** Look before choosing. A contact sheet shows them all at once:
`magick montage <dir>/'*[0]' -label '%t' -geometry 400x250+6+6 -tile 4x sheet.png`, then
Read it (in zsh, quote the `[0]`). For a GIF, coalesce first
(`magick in.gif -coalesce f-%03d.png`) and sample frames. Keep UI screenshots, and drop
code, terminals, logs and database views. Images over 6 MB are left out automatically,
because Google rejects them. No good screenshot → no image.

**Report in chat**: the base per component (version, sha, where it came from) and the
target sha; the user list (label, title, sentence, PR); the team notes; the deploy notes;
and the PRs left out, one line each, so someone can object. Stop here unless the docs or
the announcement were asked for.

## 5. Docs (when asked)

Two Google Docs, `<label> (EN)` and `<label> (JA)`, in a `<label>` folder. The folder's
parent is `My Drive/release/<project>/` unless a project skill names one. `<label>`
names the release, for example `2026-11-16 PROD · main@aecbb85`. The new version is
not known before the deploy, so don't invent one.

**Draft.** Fill `<skill>/template.html` into `draft-en.html` and `draft-ja.html`:
title, one line saying what the range is
(`Prepared 2026-11-16 · Changes since Web 0.4.28 · API 0.4.20, up to main (aecbb85)`),
then the entries. Nothing else. Japanese: write it the way a Japanese colleague would.
Titles are short noun phrases or 「〜になりました」, sentences use です・ます, and
on-screen text comes from the ja locale.

**Folder.** Find or create the parent (for `My Drive/release/<project>/`: `release` in
`root`, then `<project>`), then create `<label>` in it. If `<label>` already holds docs,
ask before adding more. Never trash a doc you didn't create in this run.

**Upload right after signing.** GitHub's image links expire after five minutes, and
Google fetches them during the upload:

```sh
python3 -I <skill>/scripts/sign_images.py --repo <repo> --prs <prs.json> \
  draft-en.html upload-en.html && cat upload-en.html
```

Pass the output unchanged as `textContent` to Drive `create_file`
(`contentMimeType: text/html`, `parentId` = the `<label>` folder, title
`<label> (EN)`), with no other call in between. Then sign and upload JA.

Drive can't replace a doc's content. To change one, edit the draft, upload it again, and
trash the copy you made earlier in this run.

**Check the images arrived**: `download_file_content` with
`exportMimeType: application/pdf`, then
`python3 -I <skill>/scripts/check_doc.py <saved file> --expect <n>`. Don't trust
`[image]` in `read_file_content`, which also shows images that failed. If any are
missing, sign and upload again, and trash the broken copy you just made.

## 6. Slack announcement (when asked; post only on the user's go-ahead)

Draft the message and show it in chat. **Post nothing until the user explicitly says to
send it.** Approval of the docs, or of an earlier draft, is not a send. If they ask for
changes, redraft and wait again.

The channel and mentions come from the project skill or the user. Keep mention tokens
exactly as written (`<@U…>` for a person, `<!subteam^S…>` for a user group) so Slack
notifies them.

```
<mentions>
We are releasing on <STG|PROD> an update of <product name>:

• <user change, one line>
• <next>
• :warning: <team note, one line with an example>

Release notes: [English](<EN doc link>) · [日本語](<JA doc link>)
```

- One line per entry, no sub-bullets unless an entry can't be understood without one.
  The docs hold the detail.
- `slack_send_message` takes Markdown links; mention tokens pass through as-is.
- After sending, read the message back with `slack_read_thread` and give the user its
  link.

## 7. Report

Links to everything created (docs, folder, message), the range and where the base came
from, and anything left out that someone might expect to see. Don't paste the docs into
chat.
