"""Baseline: plain retrieval -- every message embedded, the top k by cosine similarity handed to the reader."""
from __future__ import annotations

import datetime as dt
import math

from .base import Adapter, render_message


class Rag(Adapter):
    name = "rag"

    def ingest(self, life):
        self.user = life["user"]
        self.k = int(self.opts.get("k", 15))
        self.items = []
        for s in life["sessions"]:
            for m in s["messages"]:
                if m["role"] == "assistant" and m.get("tool_calls"):
                    continue
                text = render_message(m, self.user)
                day = dt.datetime.fromisoformat(m["timestamp"]).strftime("%Y-%m-%d")
                self.items.append((day, text))
        vecs = self.llm.embed(["search_document: " + t for _, t in self.items])
        self.vecs = [self._norm(v) for v in vecs]

    @staticmethod
    def _norm(v):
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / n for x in v]

    def ask(self, question, now):
        q = self._norm(self.llm.embed(["search_query: " + question])[0])
        scored = sorted(range(len(self.items)), key=lambda i: -sum(a * b for a, b in zip(q, self.vecs[i])))[:self.k]
        memory = "Relevant memories:\n" + "\n".join(f"- [{self.items[i][0]}] {self.items[i][1]}" for i in sorted(scored))
        return {"answer": self.read(self.user, memory, question, now), "context_chars": len(memory),
                "injected_chars": len(memory)}
