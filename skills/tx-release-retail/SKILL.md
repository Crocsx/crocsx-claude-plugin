---
description: Prepare an Autail (TX Retail) release to STG or PROD. Lists the changes between what is live and the commit to release, writes EN + JA release notes into the shared Autail release folder in Drive, copies the Autail Release Regression Test checklist next to them, and drafts the announcement for the release channel, posted only when the user says to. Use in the tx-retail repo whenever the user wants to release Autail, prepare a release, or asks for Autail release notes.
argument-hint: <stg|prod> [<commit>, default origin/main] [live FE=<version> BE=<version>]
---

**Writing style:** Before you write any output, read `shared/writing-style.md` at the plugin root (two folders above the base directory of this skill). Write all English output in ASD-STE100, as that file describes. Do not assume that the reader knows the topic.

# Autail release

The Autail flavour of the generic `tx-release` skill. Its steps, scripts and template
live in `<release>` = `<skill>/../tx-release` (this skill's sibling folder). Read
`<release>/SKILL.md` first and follow it, with the Autail facts below filling in what
it leaves to a project skill.

Run in the tx-retail repo, from the repo root.

## Autail facts

| What | Value |
| --- | --- |
| Release config | `<skill>/config.json` (pass `--config` instead of `--project-md`) |
| Drive parent folder | `Autail` on the shared drive, id `1Dj1VQyh3Ast6_mrcJ8O6ZwSVWX37-3z1` |
| Regression checklist to copy | "Autail Release Regression Test", doc id `12xFSDylhA_6UGSiUNbrXS58QR5ayGbaSQX37kfpQ2_c` |
| Slack channel | `C09KD3XREPM` |
| Slack mention | `<!subteam^S03J5P0Q3TL>`, nobody else |
| Product name in text | Autail (Settings shows "Autail" and "Autail API") |

## Steps

1. **List the changes**: `<release>` steps 1–4, with `--config <skill>/config.json`.
   Show the list, team notes and deploy notes, then carry on unless the user stops you.
2. **Release notes**: `<release>` step 5, with the folder created in the Drive parent
   folder above (not `My Drive/release/`). Label: `<YYYY-MM-DD> <ENV> · <branch>@<short sha>`,
   for example `2026-11-16 PROD · main@aecbb85`. Don't put the new release version
   anywhere: it isn't known until the deploy runs.
3. **Regression checklist**: copy the checklist doc into the new folder with
   `copy_file` (`parentId` = the new folder), titled
   `Autail Release Regression Test (<label>)`. Copy it, never edit the original.
4. **Slack draft**: `<release>` step 6, in exactly this shape:

   ```
   <!subteam^S03J5P0Q3TL>
   We are releasing on <STG|PROD> an update of Autail:

   • <user change, one line>
   • <next>
   • :warning: <team note, one line with an example>

   Release notes: [English](<EN doc>) · [日本語](<JA doc>)
   Regression test: [checklist](<copied checklist>)

   STATUS: RELEASING
   TEST: TO DO
   ```

   No version number in the message. The last two lines are for the user to update by
   hand later; always post these initial values and never edit the message after
   posting. Post to the channel itself, not a thread, and only after the user says to
   send.
5. **Report**: `<release>` step 7, plus the checklist copy's link.
