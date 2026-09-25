"""Sophia (hermes-sophia) as an Almanac adapter.

Ingestion is live, turn by turn, the way Hermes runs it: before each user message Sophia recalls and injects, after
the reply it captures the turn (so its grounding check sees what was injected). Options:
  recall  passive | active   active also gives the reader Sophia's recall/query/browse tools, as a Hermes agent has
  night   none | end | daily  when Sophia's night runs: never, once before the questions, or after every day
Requires hermes-sophia on the path (pip install -e path/to/hermes-sophia).
"""
from __future__ import annotations

import copy
import datetime as dt
import json
import re
import tempfile
from pathlib import Path

from .base import QUESTION, SYSTEM, Adapter

ACTIVE_TOOLS = ("sophia_recall", "sophia_query", "sophia_browse")


def _ts(s: str) -> float:
    return dt.datetime.fromisoformat(s).timestamp()


class Sophia(Adapter):
    name = "sophia"

    def _engine(self, user: str):
        from hermes_sophia.config import DEFAULTS
        from hermes_sophia.engine import Engine
        cfg = copy.deepcopy(DEFAULTS)
        cfg.update(lmstudio_url=self.llm.url, embed_model=self.opts.get("embed", "nomic-embed"),
                   decider_model=self.opts.get("decider", "qwen35-9b"),
                   sleep_model=self.opts.get("night_model", "qwen35-9b"), user_name=user, agent_name="Assistant",
                   embed_timeout=60.0, decider_timeout=60.0, sleep_call_timeout=600.0,
                   night_parallel=int(self.opts.get("night_parallel", 2)))
        cfg["sleep_guard_models"] = []              # a benchmark run: nobody's chat to yield to
        cfg["lms_cli"] = str(Path(cfg["lms_cli"]).expanduser())
        self.tmp = tempfile.mkdtemp(prefix="almanac-sophia-")
        return Engine(cfg, Path(self.tmp) / "sophia.db")

    def _night(self, now: float):
        from hermes_sophia.sleep import SleepRunner
        SleepRunner(self.e, max_wait_s=3600, log=lambda *_: None, now=now).run()

    def ingest(self, life):
        self.user = life["user"]
        self.e = self._engine(self.user)
        night = self.opts.get("night", "none")
        last_day = None
        for s in life["sessions"]:
            day = s["started"][:10]
            if night == "daily" and last_day and day != last_day:
                self._night(_ts(last_day + "T23:59:00"))
            last_day = day
            msgs, i = s["messages"], 0
            while i < len(msgs):
                j = i + 1                                   # a turn: one user message and everything until the next
                while j < len(msgs) and msgs[j]["role"] != "user":
                    j += 1
                user = msgs[i]["content"] if msgs[i]["role"] == "user" else ""
                self.e.now_override = _ts(msgs[i]["timestamp"])
                if user:
                    self.e.prefetch(user, s["id"])
                reply = next((m["content"] for m in reversed(msgs[i:j]) if m["role"] == "assistant" and m["content"]), "")
                self.e.capture_turn(s["id"], user, reply, messages=msgs[:j])
                i = j
        if night in ("end", "daily"):
            self._night(_ts(life["asked_at"]) - 3600)

    def ask(self, question, now):
        self.e.now_override = now.timestamp()
        text, info = self.e.recall.prefetch(question, "almanac-ask", now=now.timestamp())
        memory = text or "(Nothing was recalled for this message.)"
        if self.opts.get("recall", "passive") == "active":
            answer, calls, tool_chars = self._active(memory, question, now)
        else:
            answer, calls, tool_chars = self.read(self.user, memory, question, now), [], 0
        return {"answer": answer, "context_chars": len(text or "") + tool_chars, "injected_chars": len(text or ""),
                "tool_calls": calls, "gate": info.get("gate")}

    def _active(self, memory: str, question: str, now: dt.datetime):
        from hermes_sophia.tools import SCHEMAS, SYSTEM_NOTE
        import hermes_sophia
        skill = (Path(hermes_sophia.__file__).parent / "skills" / "memory" / "SKILL.md").read_text()
        skill = re.sub(r"^---.*?---\s*", "", skill, flags=re.S)
        tools = [{"type": "function", "function": s} for s in SCHEMAS if s["name"] in ACTIVE_TOOLS]
        messages = [{"role": "system", "content": SYSTEM.format(user=self.user) + "\n\n" + SYSTEM_NOTE + "\n\n" + skill
                     + "\n\n" + memory},
                    {"role": "user", "content": QUESTION.format(now=now.strftime("%A, %B %d, %Y %H:%M"),
                                                                user=self.user, question=question)}]
        calls, chars = [], 0
        for step in range(5):
            msg = self.llm.chat(self.llm.reader, messages, max_tokens=500, tools=tools if step < 4 else None)
            tcs = msg.get("tool_calls") or []
            if not tcs:
                return re.sub(r"<think>.*?</think>\s*", "", msg.get("content") or "", flags=re.S).strip(), calls, chars
            messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": tcs})
            for tc in tcs:
                fn = tc.get("function") or {}
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except ValueError:
                    args = {}
                out = self.e.tools.dispatch(fn.get("name", ""), args) if fn.get("name") in ACTIVE_TOOLS else "{}"
                calls.append({"tool": fn.get("name"), "args": args})
                chars += len(out[:8000])
                messages.append({"role": "tool", "tool_call_id": tc.get("id", ""), "name": fn.get("name", ""),
                                 "content": out[:8000]})
        return "", calls, chars

    def holds(self, text):
        return any(text in line for line in self.e.store.conn.iterdump())   # every table, index and log

    def close(self):
        if getattr(self, "e", None):
            self.e.close()
