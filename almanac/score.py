"""Scoring: deterministic checks where possible (dates, values, forbidden strings), a judge only for open answers.

  python -m almanac.score results/*.jsonl
  python -m almanac.score --regrade results/*.jsonl      # after a rubric change: same rules for every system
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional

_ORD = r"(?:st|nd|rd|th)?"

JUDGE_PROMPT = """You are grading an assistant's answer to a question about the user's own life, using a reference answer.

Question: {question}
Reference answer: {answer}
Assistant's answer: {response}

How to grade ({kind}):
{rule}

Reply with exactly one word: CORRECT or WRONG."""

RULES = {
    "value": "CORRECT if the assistant's answer states the same thing as the reference; extra detail is fine.",
    "date": "CORRECT if the assistant gives the same date as the reference (any format); extra detail is fine.",
    "yesno": "CORRECT if the assistant gives the same yes/no outcome as the reference.",
    "source": ("CORRECT if the assistant identifies the same source as the reference (for example, that it read it on "
               "that website, or that the user told it), even if it hedges about the fact itself."),
    "attempt": ("CORRECT if the assistant identifies the attempt that failed, by its command, by what it tried, or by "
                "the error it hit, consistent with the reference. WRONG if it names a different attempt, or only "
                "describes what worked."),
    "unknown": ("CORRECT if the assistant says it does not know, was not told, or has no record of the specific thing "
                "asked about. Mentioning related things it does know (other people, a plan) is fine. WRONG only if it "
                "states the thing asked about as fact."),
}


def date_patterns(iso: str) -> List[str]:
    d = dt.date.fromisoformat(iso)
    month, mon, day = d.strftime("%B"), d.strftime("%b"), d.day
    return [rf"\b{iso}\b", rf"\b{month}\s+{day}{_ORD}\b", rf"\b{day}{_ORD}\s+(?:of\s+)?{month}\b",
            rf"\b{mon}\.?\s+{day}{_ORD}\b", rf"\b{day}{_ORD}\s+{mon}\b", rf"\b{d.month}/{day}(?:/\d{{2,4}})?\b"]


def _has(text: str, s: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(s.lower()) + r"(?![a-z0-9])", text.lower()) is not None


def checks(response: str, chk: Dict[str, Any]) -> Dict[str, bool]:
    return {"any": not chk["any"] or any(_has(response, s) for s in chk["any"]),
            "dates": not chk["dates"] or any(re.search(p, response, re.I) for iso in chk["dates"] for p in date_patterns(iso)),
            "not": not any(s.lower() in response.lower() for s in chk["not"])}


def judge(llm, q: Dict[str, Any], response: str) -> bool:
    msg = llm.chat(llm.judge_model, [{"role": "user", "content": JUDGE_PROMPT.format(
        question=q["question"], answer=q["answer"], response=response, kind=q["kind"],
        rule=RULES.get(q["kind"], RULES["value"]))}], max_tokens=5)
    return "CORRECT" in (msg.get("content") or "").upper()


def grade(llm, q: Dict[str, Any], response: str) -> Dict[str, Any]:
    if q["kind"] == "quiet":
        return {"scored": False}
    c = checks(response, q["check"])
    ok = all(c.values())
    j: Optional[bool] = None
    if ok and q["check"]["judge"]:
        j = judge(llm, q, response)
        ok = j
    return {"scored": True, "checks": c, "judge": j, "correct": int(ok)}


def summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    scored = [r for r in rows if r.get("scored")]
    by = defaultdict(list)
    for r in scored:
        by[r["category"].split(".")[0]].append(r["correct"])
        by[r["category"]].append(r["correct"])
    quiet = [r for r in rows if r["category"] == "quiet"]
    ctx = [r.get("context_chars", 0) for r in scored]
    return {"n": len(scored), "accuracy": round(sum(r["correct"] for r in scored) / len(scored), 3) if scored else None,
            "areas": {k: round(sum(v) / len(v), 3) for k, v in sorted(by.items()) if "." not in k},
            "categories": {k: f"{sum(v)}/{len(v)}" for k, v in sorted(by.items()) if "." in k},
            "quiet": {"n": len(quiet),
                      "memory_injected_on": sum(1 for r in quiet if r.get("injected_chars")),
                      "mean_injected_chars": round(sum(r.get("injected_chars") or 0 for r in quiet) / len(quiet), 1) if quiet else None},
            "mean_context_chars": round(sum(ctx) / len(ctx)) if ctx else None,
            "mean_seconds": round(sum(r.get("seconds", 0) for r in scored) / len(scored), 2) if scored else None}


def regrade(llm, path: str, lives: str) -> None:
    """Grade saved answers again against the current question definitions, so every system is scored by the same
    rules. Rewrites the results file and its summary in place."""
    from pathlib import Path
    qs = {q["id"]: q for f in Path(lives).glob("life-*.json") for q in json.loads(f.read_text())["questions"]}
    rows = [json.loads(l) for l in open(path)]
    for r in rows:
        q = qs[r["id"]]
        for k in ("checks", "judge", "correct"):
            r.pop(k, None)
        r.update(reference=q["answer"], kind=q["kind"], **grade(llm, q, r["response"]))
    Path(path).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    sp = Path(path.replace(".jsonl", ".summary.json"))
    old = json.loads(sp.read_text()) if sp.exists() else {}
    keep = {k: old[k] for k in ("adapter", "options", "reader") if k in old}
    sp.write_text(json.dumps({**summarize(rows), **keep, "judge": llm.judge_model}, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--regrade", action="store_true", help="grade the saved answers again with the current rules")
    ap.add_argument("--lives", default="data/lives")
    ap.add_argument("--url", default="http://127.0.0.1:1234")
    ap.add_argument("--judge", default="qwen/qwen3.8-27b")
    args = ap.parse_args()
    for f in args.files:
        if args.regrade:
            from .llm import LLM
            regrade(LLM(args.url, reader=args.judge, judge=args.judge, embed=""), f, args.lives)
        rows = [json.loads(l) for l in open(f)]
        s = summarize(rows)
        print(f"\n{f}: accuracy {s['accuracy']} over {s['n']}  | areas {s['areas']}")
        print(f"   quiet: {s['quiet']}  | mean context {s['mean_context_chars']} chars, {s['mean_seconds']} s/question")
        print(f"   {s['categories']}")


if __name__ == "__main__":
    main()
