---
description: Write simple release notes for what was just deployed to STG or PROD, for non-technical teams, as an English and a Japanese Google Doc in Drive under release/<project>/<versions>. Finds the deployed and previously deployed versions (tx-manifests, git tags, GitHub releases, deploy runs, VERSION files), collects the PRs in between, and lists only what users see or do differently, each with a title, one sentence and a screenshot from the PR. Use whenever the user asks for release notes, a changelog for a deploy, "what's in this STG/PROD release", or mentions リリースノート.
argument-hint: <stg|prod> [FE=<version> BE=<version> | <version>] [previous FE=<version> ...]
---

# Release notes

The reader is **non-technical**: store and operations staff. They want to know what
looks or behaves differently, not how it was built. Keep the doc short: a title, one
plain sentence and a screenshot per change, plus a link to the PR for anyone who wants
more. The PR already holds the detail.

Output: two Google Docs, `<label> (EN)` and `<label> (JA)`, in
`My Drive/release/<project>/<label>/`. `<label>` is the deployed versions:
`FE:0.4.28-prod|BE:0.4.20`, or `v2026.10.22.3-96bd677-stg` for a one-component project.

`<skill>` is this skill's base directory. Scratch files go in
`.claude/tmp/release-notes/<env>/` in the repo.

## 1. Project config

Read the `## Release notes` section of `.claude/tx-shared/project.md`, a ```json block:

```json
{
  "project": "tx-retail",
  "displayName": "TX Retail (Autail)",
  "repo": "telexistence-inc/tx-retail",
  "components": [
    {"label": "FE", "name": "Web", "manifestApp": "tx-autail-web", "paths": ["frontend/"],
     "workflow": "frontend-web-deploy-manual.yaml", "versionFile": "frontend/apps/web/VERSION",
     "locales": {"en": "frontend/apps/web/app/**/en-US.json", "ja": "frontend/apps/web/app/**/ja-JP.json"}},
    {"label": "BE", "name": "API", "manifestApp": "tx-autail-api", "paths": ["backend/"],
     "workflow": "backend-deploy-manual.yaml", "versionFile": "backend/VERSION"}
  ]
}
```

Only `project`, `repo` and `components[].label` are required. Every other key switches on
a fallback in step 2. `tagGlob` (`{"prod": "v[0-9]*", "stg": "v[0-9]*-stg"}`) is for
projects that tag each deploy. `label` is `""` for a one-component project.

**No section yet?** Discover it from the deploy workflows (`.github/workflows/`),
`overlays/<env>/` in tx-manifests, `git tag`, `gh release list`, `VERSION` files and the
locale files. Show the block, and on a yes append it to `project.md`.

## 2. Find what was deployed

```sh
python3 -I <skill>/scripts/release_range.py --project-md .claude/tx-shared/project.md --env prod \
  > .claude/tmp/release-notes/prod/range.json
```

Versions the user gave go in as `--current FE=0.4.28-prod`, `--previous BE=0.4.16`, or a
bare `--current v2026...` for one component. The script tries, in order:

| Question | Sources |
| --- | --- |
| Deployed version and the one before | user → tx-manifests history → env tag line → GitHub Releases (prod) |
| Commit of a version | git tag → sha inside the version → the deploy run that built it → the commit that bumped the version file |

Every side `high` or `medium` → carry on. A `WARNING` (version missing, `low`
confidence, empty range) → ask the user about that component only. A first release has
no previous version: offer "everything up to now" or a start version they name.

## 3. Collect the PRs

```sh
python3 -I <skill>/scripts/collect_prs.py --repo <repo> \
  --range FE=<prev>..<cur> --range BE=<prev>..<cur> \
  --component FE=frontend/ --component BE=backend/ \
  --out .claude/tmp/release-notes/prod/prs.json --download .claude/tmp/release-notes/prod/img
```

Each component has its own range, since they deploy separately. `prs.json` holds each
PR's title, body, images (`asset` id, `local` copy) and components. `commitsWithoutPr`
lists direct pushes.

## 4. Pick what to tell

Read each PR body. Keep a change only if a user **sees or does something differently**:
a new button or message, a screen that looks different, a step that behaves
differently, an error that no longer happens. Leave out refactors, dependency updates,
CI, tests and developer tooling. They don't appear in the doc at all.

**The merge commit is what shipped.** A PR body can promise something a later push
removed. If a body's claim matters, check the strings at the deployed sha
(`git show <cur sha>:<path>`), and drop screenshots of a version that didn't ship.

For each kept change:

- **Label**: `New` (新機能), `Changed` (変更) or `Fixed` (修正).
- **Title**: what the user notices, in plain words, about 8 words.
  "Log out works", not "Wire logout to the SSO endpoints".
- **One sentence**: what they see or must do now. No technical terms: no API, server,
  backend, frontend, cache, endpoint, component or field names.
- **One screenshot** from the PR, if one shows the change.
- **PR link**: `Details: PR #N` (`詳細: PR #N`). Merge PRs that make one change into one
  entry and link the main one.

Quote on-screen text exactly. With `locales` set, grep those files at the deployed sha:
the English text for EN, the Japanese text for JA, in 「」. Never translate a label
yourself, because the app's Japanese often differs (Redo → 「やり直す」, Not Started →
「実行前」).

Order: what users will notice most first.

**Screenshots.** Look before choosing. A contact sheet shows them all at once:
`magick montage <dir>/'*[0]' -label '%t' -geometry 400x250+6+6 -tile 4x sheet.png`, then
Read it (in zsh, quote the `[0]`). Keep UI screenshots, and drop code, terminals, logs
and database views. Prefer a PNG over a big GIF. Images over 6 MB are left out
automatically, because Google rejects them. No good screenshot → no image.

## 5. Draft both documents

Fill `<skill>/template.html` into `draft-en.html` and `draft-ja.html`: title, one line
with the date and versions (`Released 2026-10-23 · Web 0.4.28 · API 0.4.20`, env suffix
dropped), then the entries. Nothing else.

Japanese: write it the way a Japanese colleague would. Titles are short noun phrases or
「〜になりました」, sentences use です・ます, and on-screen text comes from the ja locale.

## 6. Put it in Drive

1. **Folder**: find `release` in `root` (`title = 'release' and mimeType =
   'application/vnd.google-apps.folder' and parentId = 'root'`), then `<project>`, then
   `<label>`, creating any that are missing.
2. **Already there?** If `<label>` already holds docs, ask before adding more. Never trash
   a doc you didn't create in this run.
3. **Upload right after signing.** GitHub's image links expire after five minutes, and
   Google fetches them during the upload:

   ```sh
   python3 -I <skill>/scripts/sign_images.py --repo <repo> --prs <prs.json> \
     draft-en.html upload-en.html && cat upload-en.html
   ```

   Pass the output unchanged as `textContent` to Drive `create_file`
   (`contentMimeType: text/html`, `parentId` = the `<label>` folder, title
   `<label> (EN)`), with no other call in between. Then sign and upload JA.
4. **Check the images arrived**: `download_file_content` with
   `exportMimeType: application/pdf`, then
   `python3 -I <skill>/scripts/check_doc.py <saved file> --expect <n>`. Don't trust
   `[image]` in `read_file_content`, which also shows images that failed. If any are
   missing, sign and upload again, and trash the broken copy you just made.

## 7. Report

Links to the two docs and the folder, the versions found and where they came from, and
anything you left out that someone might expect to see. Don't paste the doc into chat.
