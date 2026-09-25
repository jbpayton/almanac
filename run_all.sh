#!/usr/bin/env bash
# Baselines and Sophia on the eight test lives; the 27B reads and judges.
set -u
cd "$(dirname "$0")"
export PYTHONPATH="${SOPHIA_PATH:-$HOME/sophia-hermes-research/hermes-sophia}:$PWD"
python3 -m almanac.run --adapter full-context --out results/full-context.jsonl || echo failed
python3 -m almanac.run --adapter rag --out results/rag.jsonl || echo failed
python3 -m almanac.run --adapter sophia --out results/sophia_passive_day.jsonl || echo failed
python3 -m almanac.run --adapter sophia --opt night=end --out results/sophia_passive_night.jsonl || echo failed
python3 -m almanac.run --adapter sophia --opt night=end --opt recall=active --out results/sophia_active_night.jsonl || echo failed
echo ALL DONE
