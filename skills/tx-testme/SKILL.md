---
name: tx-testme
description: Tests the user's ownership of recently changed code by gathering uncommitted changes or commits, then quizzing them on what changed, why it works, where things live, and what would break. Use this skill whenever the user says "test me", "quiz me on my code", "tx-testme", or wants to verify they actually understand recent changes rather than just having reviewed them passively.
---

# tx-testme

Tests code ownership by gathering recent changes and quizzing the user on them — not syntax, but understanding: where things live, why decisions were made, what would break.

---

## Philosophy

- Passive review of AI-generated code doesn't build understanding.
- The test is: can you explain it, locate it, and predict what breaks if it changes?
- Questions target the gap between "I reviewed this" and "I own this".
- Never test trivia. Always test judgment and structure.

---

## Step 0 — Project context (optional but preferred)

If `.claude/tx-shared/project.md` exists, read it. It tells you the repo's layering, conventions, and docs, which makes **Locate it** and **Design question** answerable against real structure instead of guesswork. If it does not exist, run anyway — infer structure from the diff and say that the questions are diff-local.

---

## Step 1 — Gather changes

### If the user provides changes directly
Use them. Skip to Step 2.

### If no changes provided
Ask:

> "Should I check uncommitted changes, a specific commit, or a range? If you want me to look at git, just paste the output of one of these:"
> ```
> git diff                         # uncommitted unstaged
> git diff --staged                # staged only
> git diff HEAD~1                  # last commit vs current
> git log --oneline -10            # recent commits to pick from
> git show <hash>                  # specific commit
> ```

Wait for the paste. Do not proceed without actual diff content.

### Parse the diff
Extract a structured change list:
- Files modified
- Functions/classes added, changed, or removed
- Key logic changes (not line-by-line — meaningful changes only)
- Architectural decisions visible in the diff (new abstractions, changed data flow, etc.)

Present the list briefly before starting the quiz:
> "I can see N meaningful changes across X files. Starting the quiz."

---

## Step 2 — Run the quiz

Run **5 questions minimum**, up to 8 for large diffs. Mix question types. Never ask more than 2 of the same type in a row.

### Question types

**Locate it** — find something without being told where it is.
> "Where does cleanup for X get triggered? Which file and which method?"
> "If this resource is exhausted, what happens, and where does that happen?"

**Explain it** — why a decision was made, not what it does.
> "Why does `acquire` reset the object before registering it?"
> "Why is this a `Map` and not a `WeakMap` here?"

**Predict the break** — remove or change something mentally and ask what breaks.
> "If you removed the guard in `destroy()`, what goes wrong and when?"
> "If this returned a live iterator instead of a copied array, what could break downstream?"

**Trace the flow** — follow data or an event through multiple files.
> "An event of type X arrives at the boundary. Walk me through exactly what happens, file by file."
> "This value hits its terminal state. Trace what happens from that moment to it being released."

**Design question** — a tradeoff visible in the diff.
> "You put the registries in A instead of B. Why does that split make sense?"
> "Why does this expose two narrow accessors instead of the underlying object?"

When `project.md` was read, prefer questions that test the repo's actual rules — layering direction, where a given kind of logic is supposed to live, what a convention exists to prevent.

---

## Step 3 — Score and respond

**If correct or mostly correct:**
- Confirm briefly, no praise
- Add one sentence of depth they might not have mentioned
- Move to next question

**If partially correct:**
- Say what was right
- Point to exactly what was missing or wrong
- Don't give the full answer yet — ask them to try again on the missing part

**If wrong or "I don't know":**
- Tell them the correct answer directly
- Tell them where in the code to find it
- Flag it as a gap: "This one to revisit."

---

## Step 4 — Final summary

```
Owned:      [concepts answered well]
Gaps:       [things wrong or unknown]
To revisit: [specific files or functions worth re-reading]
Score:      X / Y questions owned
```

Then one honest line:
- Score ≥ 4/5: "You own this change."
- Score 3/5: "Partial ownership. Revisit the gaps before moving on."
- Score < 3/5: "You reviewed this but don't own it yet. Read it again and run tx-testme."

---

## Rules

- Never test syntax ("what does X return") — only structure, flow, and judgment
- Never reveal the answer before the user tries
- Don't soften wrong answers — say it's wrong and say why
- If the diff is too small to generate 5 meaningful questions, say so and ask for more context
- If the code was fully AI-generated and only reviewed, flag that the quiz may expose review gaps rather than authorship gaps — still run it
- Questions must be answerable from the diff plus the surrounding architecture — don't ask about things not in scope
