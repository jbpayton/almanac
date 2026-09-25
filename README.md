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

*v0.1 baselines are running; this table is filled in as they finish.*

## Limitations

- **Templated conversations.** Lives are generated from templates with seeded variety. They are cleaner than real chat, and a model trained or tuned on them would learn their phrasings. Treat `data/lives/` as a test set: tune on `data/dev/` or on your own lives (`--seed`).
- **Small.** Eight lives is a first version; scores carry wide intervals, so compare systems per area, not by a point or two overall.
- **Honest about its origin.** Almanac was written alongside Sophia, to measure things Sophia was designed for. Those are also things any agent memory should do. The baselines run on exactly the same data and code, and the adapter interface is open so other systems can be measured the same way.

## License

MIT
