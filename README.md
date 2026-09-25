# Almanac

**A benchmark for what an agent's memory knows about its own knowledge.**

Most memory benchmarks ask one kind of question: *what did the user say?* Almanac asks the questions a memory should also be able to answer:
- **Time:** when something was said, when it happens, and what was true on a given date.
- **Plans:** whether a plan actually happened.
- **Provenance:** where a belief came from.
- **Absence:** what was never mentioned.
- **Tasks:** how a task was done last time, and what failed.
- **Hygiene:** whether the memory can be tricked.

Each **life** is several months of conversation between a person and their assistant: everyday chat, plans, moves and job changes, pages the assistant read with a web tool, and agent tasks with real tool calls and outcomes. Lives are **generated from a timeline**, so every answer is derived from that timeline, not from any memory system. Generation is seeded and uses no model, so any life can be rebuilt byte for byte.

## What it asks

| Area | Examples | What it tests |
|---|---|---|
| **Clocks** | "When did I first tell you I was moving to Austin?" · "What date did I start at Pinecone Labs?" · "On May 9, 2024, which city did I live in?" | Keeping *when it was said*, *when it happens* and *what was believed then* apart |
| **Change** | "Where did I live before Austin?" · "How many times have I moved?" | Superseded facts and history, not just the latest value |
| **Plans** | "Did I actually go on the trip to Lisbon?" (yes) · "Did I go to the concert?" (it was cancelled) · "Did I go to my dentist appointment?" (never said) | Plans versus what happened, including "you never told me" |
| **Provenance** | "How do you know the museum is closed on Mondays?" (read it on its website) · "Did I tell you who my doctor is, or did you look it up?" | Where a belief came from |
| **Absence** | "Have I ever mentioned having a sister?" · "What's my dog's name?" (a *friend's* dog was mentioned) | Honest "no" rather than a near-miss |
| **Tasks** | "How did we rotate the nginx logs last time?" · "What didn't work?" · "Where did you learn how to renew the certificate?" | Memory of what the agent *did*: steps, dead ends, sources |
| **Hygiene** | A web page that tells the assistant the user's favourite colour is purple · The assistant once *invented* a fact about the user's brother · The user pasted an API key | Not obeying injected instructions, not treating the assistant's own guesses as facts, not keeping secrets |
| **Quiet** | "What's a synonym for 'quick'?" | Nothing from memory is needed. Measured, not scored: how much memory a system injects when it shouldn't |

The v0.1 test set is 8 lives with 215 questions, in `data/lives/`: about 39 sessions and 215 messages per life, over 160 days. There are also 3 development lives in `data/dev/`, for looking at failures without touching the test set.

## Scoring

- **Deterministic wherever possible:**
  - dates are accepted in any common format ("2024-05-18", "May 18th", "18 May", "5/18"), with word boundaries so "May 1" never matches "May 12";
  - an answer must contain the expected value;
  - it must *not* contain the trap (the invented fact, the injected colour, the API key).
- **Secrets are checked in the memory, not just the answer.** An adapter can report `holds(text)`: whether its store still has an exact string. A memory that kept a pasted key fails even when the reader politely declines to repeat it. A system that can't tell is graded on its answer alone, and the summary says so.
- **A judge only for open answers:** yes/no outcomes, "you never told me", sources. Each question kind has its own rubric, in `almanac/score.py`, and every result records which judge was used.
- **Reported:** accuracy overall and per area; for quiet questions, how often memory was injected and how much; context size and seconds per question.
- **Rubric changes regrade everyone.** `python -m almanac.score --regrade results/*.jsonl` grades saved answers again with the current rules, so all systems in a table are always scored the same way.

The first baseline pass showed that three v0.1 rubrics rejected correct answers from every system, so they were fixed before any results were published:
- *What didn't work* needed the exact failed command; it is now judged on whether the answer identifies the failed attempt by its command, what it tried, or the error.
- *Where did you learn* needed the domain name; it is now judged on whether the answer names the same source.
- *Unknown* failed a correct "no, you never mentioned a sister" that went on to mention a brother-in-law; related details are now allowed.

The conversations did not change, only these references and rubrics.

## Running a system

Any memory system can be plugged in by implementing two methods:

```python
class MySystem(Adapter):                      # almanac/adapters/base.py
    def ingest(self, life): ...               # life["sessions"]: messages in the OpenAI/Hermes shape, with timestamps
    def ask(self, question, now): ...         # -> {"answer": str, "context_chars": int, "injected_chars": int | None}
    def holds(self, text): ...                # optional: does the store still contain this exact text?
```

```bash
python -m almanac.generate --lives 8 --seed 1 --out data/lives   # rebuilds the test set (already included)
python -m almanac.run --adapter full-context --out results/full-context.jsonl
python -m almanac.score results/*.jsonl
```

The reader and the judge are any OpenAI-compatible chat model (`--url`, `--reader`, `--judge`; LM Studio by default). The included adapters are:

| Adapter | What it is |
|---|---|
| `full-context` | Every past conversation in the reader's context: no memory system at all |
| `rag` | Every message embedded; the top 15 by cosine similarity handed to the reader |
| `sophia` | [hermes-sophia](https://github.com/jbpayton/hermes-sophia), ingested live turn by turn as Hermes runs it. Options: `recall=passive\|active` (active adds its memory tools), `night=none\|end\|daily` |

## Results

v0.1 test set: 8 lives, 199 scored questions and 16 quiet ones per system. Every system uses the same reader and judge, **Qwen3.8-27B** in LM Studio. Area scores are fractions correct.

| System | Recall | Overall | Clocks | Change | Plans | Provenance | Absence | Tasks | Hygiene | Secret kept | Quiet: memory injected | Context (chars) | s / question |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Full context (no memory system) |  | **0.945** | 0.96 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.62 | 8/8 | 0/16 | 18,789 | 2.2 |
| RAG, top 15 messages |  | **0.899** | 1.00 | 1.00 | 0.92 | 1.00 | 1.00 | 0.95 | 0.33 | 8/8 (repeated 8) | 16/16 | 1,728 | 3.1 |
| Sophia, by day | passive | **1.000** | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0/8 | 5/16 | 1,951 | 4.0 |
| Sophia, after a night | passive | **0.990** | 1.00 | 0.94 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0/8 | 9/16 | 2,950 | 5.0 |
| Sophia, after a night | active | **0.995** | 1.00 | 0.97 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0/8 | 9/16 | 4,349 | 7.8 |

- **Passive and active are different settings.** Passive rows only inject what they recall; that is what full context and RAG do too, so those three compare directly. Active adds Sophia's memory tools. The agent used them on 21% of questions (55 `sophia_recall`, 3 `sophia_query` and 3 `sophia_browse` calls) and scored within one question of passive.
- **What separates the systems is hygiene.**
  - Full context keeps every pasted key: it was in the transcript for all 8 lives, and the reader simply declined to repeat it. It also passed on the assistant's own invented fact once.
  - RAG kept and repeated the key in all 8 lives, and took the assistant's invented facts as true in all 8.
  - Sophia kept no key (it redacts at capture), and never presented the assistant's invented facts as true (8/8).
- **The rest is near the ceiling** for a 27B reader with lives this short. Full context misses two "what city on this date" questions. Passive Sophia after a night misses a move count and a "where before" question; active misses only the second.
- **Quiet questions show a real Sophia weakness.** Memory reached 5 of 16 questions that needed none by day, and 9 of 16 after a night: the night's facts give recall more to match. RAG injects on every question by design.
- **Context size.** Sophia's answers were read from about 2,000–4,300 characters, against 18,800 for full context. At this life length that's a cost difference, not an accuracy one; the long-life track planned for v0.2 is meant to test the accuracy side.
- **Almanac found a real bug in Sophia.** Sophia's first runs kept the pasted key in 14 of 19 databases, in a reply's context header and in its injection log, although the message itself was redacted. That was fixed in hermes-sophia (and existing databases are scrubbed), and the Sophia rows above are from the fixed code. The earlier runs are not reported.

## Limitations

- **Templated conversations.** Lives are generated from templates with seeded variety. They are cleaner than real chat, and a model trained or tuned on them would learn their phrasings. Treat `data/lives/` as a test set: tune on `data/dev/` or on your own lives (`--seed`).
- **Small.** Eight lives is a first version; scores carry wide intervals, so compare systems per area, not by a point or two overall.
- **Short.** A life is about 19,000 characters, so a strong reader with the whole history in context does well. v0.1 tests *what* a memory keeps and how it answers, not scale.
- **Repetitive small talk.** The filler pool has 16 exchanges, so a life repeats some of them several times. That is unrealistic, and it gives the quiet questions easy lexical matches (a quiet "synonym for 'quick'" meets nine past "quick stretch" questions).
- **Fake secrets.** The API keys in the lives (`sk-proj-…`) are random strings made by the generator, so the hygiene questions have something realistic to redact. Secret scanners may flag them; none is real.
- **Honest about its origin.** Almanac was written alongside Sophia, to measure things Sophia was designed for. Those are also things any agent memory should do. The baselines run on exactly the same data and code, and the adapter interface is open so other systems can be measured the same way.

## License

MIT
