---
description: Write NEDO UPP effort-report entries (委託業務従事日誌 / labor-cost claim log) for a date range, by reconstructing the work from git, GitHub PRs, JIRA and Slack, then wording each entry so it reads as claimable R&D. Each week is a block of goal-numbered lines covering the activities performed that week. Use whenever the user mentions the NEDO report, effort report, 従事日誌, weekly/monthly effort entries, or asks "what did I do from <date> to <date>" in a reporting context.
argument-hint: <date range, e.g. 2026-09-01..2026-09-30>
---

# NEDO UPP effort report

The effort report is the basis for labor-cost claims. Hours are only claimable when the
text reads as development work on this project. The same real work can be claimable or not
depending purely on wording, so the job is twofold: reconstruct the period accurately, then
word it so a reviewer who knows nothing about the codebase sees project R&D.

**Rules in force (Kawamata / GR, September 2026 — the July format, restored):**

The two additions announced for the August log were dropped after Hirokawa-san coordinated
with NEDO, so from September onward neither is required: **no Business Development Item
line**, and **no Key Learnings / Observations summary**. Enter only the relevant Departmental
Goal and the activities performed during the week. An August log already submitted is not
revised — only reports from September 2026 on use this format.

- **A weekly block is Departmental Goal lines and nothing else.** No Items header, no
  closing summary. Only the goal and what was done that week.
- Every entry line **starts with the full UPP goal number** (e.g. `Goal 2.a.vi`) — that
  number *is* the Departmental Goal.
- **Enter the activities by day, or summarised over the week.** Either is accepted; keep one
  style through the month.
- **No date prefix on a line.** The sheet row already carries the week. Keep the lines in
  chronological order within the block, so the day-level structure survives without being
  written out. When a piece of work must be pinned to particular days, put them in the
  closing parenthetical — `(Sep 4, 5)`.
- **No PR numbers, no JIRA ticket IDs, no implementation detail.** The reviewer is not on
  the team and does not need to know how it was built. One line is one sentence: the
  activity, what it was applied to, and the purpose or result it served.
- **A line may carry several goals** when the work serves more than one — `Goal 2.a.iv;
  2.b.iii:` — and a day's work may be joined onto one line, separated by `;`.
- Keep the whole block short enough to fit an Excel cell. If it overflows, cut detail — not
  entries.
- Do **not** write the usual work location (Office / WFH). Only a business trip is noted,
  as `[Business Trip]` at the start of the description.

## Reference

Business Development Items — **not required from September 2026 onward**; kept only for
reading or reproducing an August or earlier log:

| Item | Scope |
|---|---|
| Item 1 | Nationwide rollout of robot introduction to FamilyMart franchise stores |
| Item 2 | Nationwide rollout of robot introduction to 7-Eleven Japan franchise stores |
| Item 3 | Nationwide rollout of robot introduction to Lawson franchise stores |

UPP goals — this is the "Departmental Goal" the log asks for. Use the full number,
`Goal <n>.<letter>.<roman>`:

```
1     HW / Procurement / Production
  1.a   Establish mass-production quality of the hardware
  1.b   Stabilize parts supply through multi-supplier sourcing
  1.c   Reduce mass-production costs
  1.d   Hardware with high deployment versatility (any store layout)
  1.e   Hardware that reduces the repair store-visit rate (durability)
2     Software
  2.a   SysApp
    2.a.i    UI/UX that eliminates store inquiries (zero store inquiries)
    2.a.ii   Develop and achieve security requirements
    2.a.iii  Improve auto-recovery availability (zero internal escalations)
    2.a.iv   Restocking logic to prevent out-of-stock (OOS)
    2.a.v    Teleoperation system platform that minimizes downtime
    2.a.vi   Systems for reliable initial deployment and operation (deployment automation tools)
    2.a.vii  Scalable, observable, cost-efficient platform foundation
    2.a.viii Operations-facing tooling that reduces operational handling / unblocking time
  2.b   Automation & DevOps
    2.b.i    Reliable software, 99% automation rate
    2.b.ii   Scalable software
    2.b.iii  Features that reduce operational handling time
    2.b.iv   Improve PnP and scan speeds
    2.b.v    Robot foundation model
3     Partner Development
  3.a   Define key customer requirements, establish the commercial specification
  3.b   Deployment/operation requirements for paid franchise-store PoCs and impact measurement (store ROI)
```

Sheet: https://docs.google.com/spreadsheets/d/1QMNtsqV9Py2fAW9IPdZ5c4ZT3lgpLwuPlFpNmKzeOKM/edit?gid=314679503#gid=314679503
Deadline: by the 5th business day of the following month. Questions go to GR (Kawamata).

## Workflow

### 1. Establish the weeks

The sheet splits the month into weekly rows. Mirror those rows — do not invent your own
week boundaries. Compute the weekday for every date rather than assuming it:

```bash
for d in $(seq -w 1 31); do echo "2026-08-$d $(date -d 2026-08-$d +%A 2>/dev/null)"; done
```

Weekend and holiday work is simply another line inside the week it falls in. Day types and
hours are handled by the reviewer.

### 2. Pull the raw activity

Run these in parallel; each covers a different trace of the same work.

Commits (richest source — author name from `git config user.name`):

```bash
git log --all --author="<name>" --since=<start> --until=<end+1day> \
  --date=format:'%Y-%m-%d %a %H:%M' --pretty='%ad | %s' | sort -u
```

PRs authored, which give dates and the shape of each change:

```bash
gh pr list --author "@me" --state all --limit 80 \
  --json number,title,createdAt,mergedAt,url
```

PRs reviewed — review is claimable work, and often the only content on a light week:

```bash
gh search prs --repo <owner/repo> --reviewed-by "@me" --updated <start>..<end> \
  --json number,title,updatedAt
```

JIRA, via the Atlassian MCP `searchJiraIssuesUsingJql` (get `cloudId` from
`getAccessibleAtlassianResources` first):

```
assignee = currentUser() AND updated >= "<start>" AND updated <= "<end>" ORDER BY updated ASC
```

Request only `key`, `summary`, `status`, `updated`. The result often exceeds the tool's
token limit and is spilled to a file — parse that file instead of re-running the query.

Ticket and PR numbers are for **your** reconstruction only. They never appear in the output.

Two traps. Git dates carry the author's own offset (`git log --format='%aI'`), while `gh`
JSON is always UTC; prefer the git date when they disagree. And a day that looks empty was
still worked — design, investigation, incident triage and specification work leave no
commits.

If a week is thin, ask the user before searching Slack; do not do it automatically. Slack
search reaches private channels and colleagues' messages, and the user often just remembers
what they did, which is faster. Name the dates you would search. If they agree, load the
Slack search tools with `ToolSearch` (search for `slack_search`; the server id varies) and
summarise only their own contribution.

### 3. Choose what to report

Per day, report the substantive work only — one line, two when the day genuinely split
between two goals. Do not list everything; small incidental items bury the substance and
blow the cell size.

There is no separate summary line any more, so a result or finding worth recording belongs
in the closing clause of the line it came from — what the work established, not just that it
was done.

Consecutive weeks are read side by side. Show what changed from the previous week; never
repeat the previous week's wording. A thread that spans weeks moves along — investigation,
then implementation, then verification and results.

Do not invent work, results or numbers. If you are unsure a thing happened, leave it out or
ask.

### 4. Word it as claimable work

Claimable shapes:

- analysis / evaluation / study of X
- experiments / tests / demonstrations of X
- checks and data collection for X
- specification meetings or interviews about X
- fixes, reviews and adjustments to X

Ambiguous — claimable only once the purpose is stated:

| As written | Why it comes back | Write instead |
|---|---|---|
| Meeting on X | indirect-work meetings are not claimable | specification meeting for X / technical meeting to map X issues |
| Attended a conference or trade show | attendance alone is not work | information gathering / exchange of views on X at the conference |
| Attended a lecture or seminar | reads as "just listened" | exchange of views and information gathering serving the project |
| Preparing / organizing / assembling X | reads as auxiliary support work | building and tuning X as a verification setup |
| Research / literature review | subject and purpose unclear | study of X for the design of Y |
| Inspection / cleaning / retrieval of equipment | reads as maintenance | operation check / function check of X |

Not claimable — omit rather than dress up. A reviewer who spots one disguised as
development starts doubting the whole month:

- training, OJT, seminars, courses, learning to operate a tool
- admin and NEDO paperwork: quotes, orders, contracts, accounting audits, and preparing
  the effort report itself (accounting staff are the exception)
- patent drafting and filing, approval and licensing paperwork
- presentation, exhibit and document preparation — presenting orally or exchanging views is
  fine, the slide deck is not
- commercialization plans and meetings (a productization study applying R&D results is fine)
- ticket grooming and backlog triage
- company events, all-hands, socials

For server, cloud and app work on store operation, the translations that come up most:

| Raw activity | Reads as | Write instead |
|---|---|---|
| Released a hotfix / deployed | operations | correction of X, verified in the store environment |
| Reverted a change | operations | adjustment of X |
| Prepared the release / merged to main | operations | verification of the build for deployment |
| Fixed flaky tests / CI config | maintenance | analysis and correction of unstable verification tests |
| Dev tooling, pre-commit hooks, harness | support | development / tuning of the verification environment |
| Upgraded a library or framework | maintenance | adjustment of the verification environment for X |

### Line shape

One line is **activity + subject + why it mattered**. In English the house form is a
past-tense verb, what it was applied to, and a closing clause giving the purpose or the
result:

> Goal 1.5: Analyzed finger durability test results to determine root cause of accelerated
> damage in stores.

> Goal 2.a.vi: Analysed and corrected shelf capture and annotation in the store deployment
> tool, eliminating annotations written to the wrong shelf when a capture is repeated.

Japanese entries use a noun phrase instead, with the qualifier in parentheses. Mirror
whichever form the sheet already holds:

> 目標① SEJ 大阪中之島6丁目における検品・受入フロー、発注点・欠品基準等の運用実態ヒアリング・情報収集
> 目標1.1 検知性能向上のための検討用LDH/LDN試験結果の解析およびデータ化

**The closing purpose or result clause is what makes the line claimable.** Cut detail before
you cut that. Roughly fifteen to thirty words.

**Several goals on one line.** Work usually serves more than one goal. List them all, and do
not repeat the word `Goal`:

> Goal 2.a.iv; 2.b.ii; 2.b.iii: Added lane events to the stock shelf and consumed them in the
> store app, enabling faster restocking updates without duplicating shelf-state logic across
> clients.

**Several items in one day's work.** Give each its own line, or join them with `;` on one
line. Keep one style through the month.

**Work spanning days.** Either list the dates on one line — `(Aug 4, 5)` — or split it across
the days and mark the parts `(day 1 of 2)`, `(day 2 of 2, completed as planned)`. A thread
that ran all week can instead be rolled into one line with an `including …` list of what it
covered.

**Naming.** System and product names are expected and help the reviewer place the work: the
store app, the deployment tool, the operator console, the stock shelf. Infrastructure and
platform names are filed by other members too and are fine where they identify the subject.
What never appears: class, method and file names, ticket IDs, PR numbers, and counts of
tests or screens.

Other teams number goals differently — `Goal 1.4`, `目標①`, `目標1.1`. Do not copy their
numbering; software work uses the full `2.a.vi` form.

Too long — explains the implementation:

> Goal 2.a.vii: Development of client-side fault reporting for the verification and
> production environments, so that an application fault in a store is recorded together with
> the screen and the software version instead of depending on a report from the store
> (PR #260). The two differing fault screens were unified into a single translated screen,
> and an unknown address now shows a dedicated page rather than a fault screen.

Too short — no purpose clause, so nothing distinguishes it from any other week:

> Goal 2.a.vii: Development of fault reporting for the store application

Right:

> Goal 2.a.vii: Developed automatic fault reporting for the store application on the
> verification and production environments, so store-side faults are recorded without
> relying on a report from the store.

### 5. Output

One code block per week, so it can be pasted into the sheet. Nothing but goal-numbered
lines, one per piece of work, in chronological order.

```
Goal 2.a.vi: Verified and completed the deployment tool corrections raised in the previous store trial, covering measurement auto-fill and the shelf capture controls.
Goal 2.a.viii; 2.a.iv: Compared three server-application data structures for the store shelf layout editor and prototyped the selected one, which held a screen load to a single request (day 1 of 2).
Goal 2.a.vii: Developed automatic fault reporting for the store application on the verification and production environments, so store-side faults are recorded without relying on a report from the store.
Goal 2.a.vi: Analysed and corrected shelf capture and annotation in the deployment tool, eliminating annotations written to the wrong shelf when a capture is repeated.
```

Write in English by default; produce Japanese only when asked.

Before handing over, reread as the reviewer would:

- Does every line start with a goal number, and does the block contain nothing else — no
  Items header, no closing summary?
- Is the purpose stated, so it cannot read as indirect work?
- Does it read as development, not preparation, support or maintenance?
- Is it different from the previous week?
- Does every line close on a purpose or result clause, rather than just naming the activity?
- Are all the goals a piece of work serves listed, not only the first?
- Is work spanning days marked, by listing its dates or by `(day n of m)`?
- Is it free of ticket IDs, PR numbers, and class, method and file names?
- Did anything non-claimable slip in?

Then flag the judgement calls briefly: what you excluded as non-claimable, and any week
resting on a framing that could be rejected (tooling and test-infrastructure weeks are the
usual candidates). Those are the user's calls to make.

## Conventions

A business trip is marked `[Business Trip]` at the start of the description. The usual work
location is not written. Travel days either side of a trip can be entered when travel-day
hours are claimable under the travel policy; time outside regular working hours is not.

Hours, day types (working day / holiday / leave) and the colon time notation (`7:45`, not
`7.75`) are transferred from the attendance system by the reviewer. Do not invent them.
