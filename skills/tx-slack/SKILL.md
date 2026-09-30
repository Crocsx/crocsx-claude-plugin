---
description: "Recap a Slack thread from a URL — extract what matters, skip the noise"
allowed-tools:
  - mcp__plugin_slack_slack__slack_read_thread
  - mcp__plugin_slack_slack__slack_read_user_profile
---

## Input

The user provided a Slack thread URL in $ARGUMENTS (e.g. `https://<workspace>.slack.com/archives/C1234/p1234567890123456`).

## Task

### Step 1 — Parse the URL

Extract from the URL:
- **channel_id**: the segment starting with `C` (e.g. `C1234567890`)
- **thread_ts**: the `p`-prefixed number, converted to a timestamp by inserting a dot after the 10th digit (e.g. `p1234567890123456` → `1234567890.123456`)

### Step 2 — Fetch the thread

Call `slack_read_thread` with the extracted `channel_id` and `thread_ts`. If user profiles are needed to resolve names, call `slack_read_user_profile`.

### Step 3 — Produce the recap

Read the full thread and produce a structured recap that a teammate who wasn't there can read in 60 seconds.

**Include:**
- The original question or topic that started the thread
- Key decisions made (attribute to person when it matters)
- Important facts, findings, links, or blockers shared
- Action items and who owns them
- Open questions or unresolved points

**Skip:**
- Greetings, thanks, "+1", "sounds good", "got it", "will do", emoji-only replies
- Messages that repeat what was already said
- Side tangents that went nowhere

**Output format:**

```
**Topic:** <one sentence>

**Context:** <1-2 sentences — why it came up, if clear>

**Key points:**
- <fact or finding — attribute to person if it matters>

**Decisions:**
- <what was decided and by whom>

**Action items:**
- [ ] <task> — <owner if named>

**Open questions:**
- <unresolved point still pending>
```

Omit any section with nothing to put in it. One idea per bullet, no padding.

---

**Note:** the only project-coupled thing in this command is the MCP tool name prefix in the frontmatter. If the Slack plugin is installed under a different name in a given repo, fix it there.
