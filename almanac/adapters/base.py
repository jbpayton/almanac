"""The adapter interface: any memory system can be run on Almanac by implementing ingest() and ask()."""
from __future__ import annotations

import datetime as dt
import json
from typing import Any, Dict, List

SYSTEM = ("You are {user}'s personal assistant. You remember your past conversations with {user}; what you remember "
          "is given below. Answer from memory. If your memory doesn't say, say you don't know rather than guessing.")
QUESTION = "Current date and time: {now}\n{user}: {question}\nAnswer concisely."


class Adapter:
    """ingest(life) once, then ask(question, now) for each question. ask() returns
    {"answer": str, "context_chars": int, "injected_chars": int | None, "tool_calls": [...]}"""
    name = "base"

    def __init__(self, llm, **opts):
        self.llm, self.opts = llm, opts

    def ingest(self, life: Dict[str, Any]) -> None:
        raise NotImplementedError

    def ask(self, question: str, now: dt.datetime) -> Dict[str, Any]:
        raise NotImplementedError

    def close(self) -> None:
        pass

    # shared: one reader call over a block of remembered text
    def read(self, user: str, memory: str, question: str, now: dt.datetime) -> str:
        msg = self.llm.chat(self.llm.reader, [
            {"role": "system", "content": SYSTEM.format(user=user) + "\n\n" + memory},
            {"role": "user", "content": QUESTION.format(now=now.strftime("%A, %B %d, %Y %H:%M"), user=user,
                                                        question=question)}], max_tokens=500)
        return (msg.get("content") or "").strip()


def render_message(m: Dict[str, Any], user: str) -> str:
    """A transcript line for systems that read raw conversation."""
    if m["role"] == "tool":
        return f"[tool result from {m.get('name', 'tool')}] {m['content'][:700]}"
    if m.get("tool_calls"):
        calls = "; ".join(f"{c['function']['name']}({c['function']['arguments']})" for c in m["tool_calls"])
        return f"[Assistant called {calls}]"
    who = user if m["role"] == "user" else "Assistant"
    return f"{who}: {m['content']}"
