# Writing style — ASD-STE100 (Simplified Technical English)

Every `tx-*` skill writes its English output in ASD-STE100. This includes chat replies,
questions, plans, reviews, PR titles and bodies, commit messages, AGENTS.md and other docs,
code comments, test checklists, release notes and effort-report entries.

The reader may not know the topic. Do not assume knowledge. Explain clearly and with
detail: STE limits the length of a sentence, not the quantity of information. When a
topic needs more explanation, write more short sentences.

## Words

- Use simple, common words. Use one word for one meaning, and use the same word for the
  same thing every time. Example: do not write "hub", then "endpoint", then "service" for
  the same thing.
- Technical names (`SignalR`, `OrderService`, `pnpm`) and technical verbs (`deploy`,
  `commit`, `merge`) are permitted. Write code, file names and commands in backticks.
- When a technical term is new to the reader, give its meaning in plain words the first
  time that you use it.
- Do not use phrasal verbs when a simple verb exists: "start", not "kick off"; "find",
  not "figure out"; "prepare", not "set up" (except as a technical name).
- Do not use slang, idioms, marketing words or filler ("seamless", "robust",
  "leverage", "it is worth noting", "basically").
- Do not use contractions: "do not", not "don't"; "it is", not "it's".
- Do not make noun clusters of more than three words. Write "the timeout of the
  connection retry", not "connection retry timeout value setting".

## Sentences

- Instructions (procedures): maximum 20 words for each sentence. Descriptions:
  maximum 25 words.
- Write one instruction in one sentence. Start an instruction with a verb in the
  command form: "Run `pnpm test`." "Open the file."
- Use the active voice: "The server sends the event", not "The event is sent".
- Use simple tenses: present, simple past, simple future.
- Do not use "-ing" forms as verbs. Write "When the client connects", not "On
  connecting".
- Keep "the", "a", "this". Do not delete articles to make text shorter.
- Write conditions first: "If the build fails, read the log."

## Structure

- One paragraph has one topic. A paragraph has a maximum of six sentences.
- Use a vertical list for steps or for three or more items. Number the steps in order.
- Put a warning before the step it applies to. Start it with a command: "Do not push to
  `main`. The CI deploys each push to production."
- Explain why, not only what. Give a concrete example when a rule or a mechanism is
  not clear.

## Exceptions

- Code, commands, identifiers, quoted UI text, quoted log lines and quoted text from
  other people stay exactly as they are.
- Japanese output is not STE. Write it in plain, short, natural Japanese, as a
  Japanese colleague writes it.
- If a skill gives a fixed format (a PR template, a NEDO line shape, a commit
  convention), keep that format. Write the free text inside it in STE.
