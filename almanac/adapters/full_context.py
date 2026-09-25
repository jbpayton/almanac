"""Baseline: the whole conversation history in the reader's context (no memory system at all)."""
from __future__ import annotations

import datetime as dt

from .base import Adapter, render_message


class FullContext(Adapter):
    name = "full-context"

    def ingest(self, life):
        self.user = life["user"]
        parts = []
        for s in life["sessions"]:
            day = dt.datetime.fromisoformat(s["started"]).strftime("%Y-%m-%d %H:%M")
            parts.append(f"### Conversation on {day}\n" + "\n".join(render_message(m, self.user) for m in s["messages"]))
        self.transcript = "Your past conversations:\n\n" + "\n\n".join(parts)

    def holds(self, text):
        return text in self.transcript

    def ask(self, question, now):
        return {"answer": self.read(self.user, self.transcript, question, now), "context_chars": len(self.transcript),
                "injected_chars": None}
