"""Run a memory system on Almanac lives and grade it.

  python -m almanac.run --adapter full-context --out results/full-context_r27.jsonl
  python -m almanac.run --adapter sophia --opt recall=active --opt night=end --out results/sophia_active_night.jsonl

Results are JSONL (one row per question, resumable); python -m almanac.score prints the tables.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import time
from pathlib import Path

from .llm import LLM
from .score import grade, summarize

ADAPTERS = {"full-context": ("almanac.adapters.full_context", "FullContext"), "rag": ("almanac.adapters.rag", "Rag"),
            "sophia": ("almanac.adapters.sophia", "Sophia")}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--adapter", required=True, choices=sorted(ADAPTERS))
    ap.add_argument("--opt", action="append", default=[], metavar="KEY=VALUE", help="adapter option")
    ap.add_argument("--lives", default="data/lives")
    ap.add_argument("--only", default="", help="comma-separated life ids")
    ap.add_argument("--url", default="http://127.0.0.1:1234")
    ap.add_argument("--reader", default="qwen/qwen3.8-27b")
    ap.add_argument("--judge", default="qwen/qwen3.8-27b")
    ap.add_argument("--embed", default="nomic-embed")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    opts = dict(kv.split("=", 1) for kv in args.opt)
    opts.setdefault("embed", args.embed)
    llm = LLM(args.url, reader=args.reader, judge=args.judge, embed=args.embed)
    import importlib
    mod, cls = ADAPTERS[args.adapter]
    Adapter = getattr(importlib.import_module(mod), cls)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = {json.loads(l)["id"] for l in out.read_text().splitlines()} if out.exists() else set()
    files = sorted(Path(args.lives).glob("life-*.json"))
    if args.only:
        files = [f for f in files if f.stem in set(args.only.split(","))]
    for f in files:
        life = json.loads(f.read_text())
        todo = [q for q in life["questions"] if q["id"] not in done]
        if not todo:
            continue
        adapter = Adapter(llm, **opts)
        t = time.time()
        adapter.ingest(life)
        ingest_s = round(time.time() - t, 1)
        now = dt.datetime.fromisoformat(life["asked_at"])
        for q in todo:
            t = time.time()
            r = adapter.ask(q["question"], now)
            row = {"id": q["id"], "life": life["id"], "category": q["category"], "kind": q["kind"],
                   "question": q["question"], "reference": q["answer"], "response": r["answer"],
                   "context_chars": r.get("context_chars"), "injected_chars": r.get("injected_chars"),
                   "tool_calls": r.get("tool_calls"), "seconds": round(time.time() - t, 2), "ingest_seconds": ingest_s}
            row.update(grade(llm, q, r["answer"]))
            with open(out, "a") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        adapter.close()
        rows = [json.loads(l) for l in out.read_text().splitlines() if json.loads(l)["life"] == life["id"]]
        s = summarize(rows)
        print(f"{life['id']}: accuracy {s['accuracy']} ({s['n']} scored), ingest {ingest_s}s, areas {s['areas']}", flush=True)
    rows = [json.loads(l) for l in out.read_text().splitlines()]
    summary = summarize(rows)
    summary.update(adapter=args.adapter, options=opts, reader=args.reader, judge=args.judge)
    Path(str(out).replace(".jsonl", ".summary.json")).write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
