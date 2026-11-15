#!/bin/bash
# The whole experiment plan (script/outline.md, "Experiment plan"): one factor changes per set. Pinned models, 5 runs in parallel.
cd "$(dirname "$0")"
P=.venv/bin/python
OPUS=claude-opus-5-5; HAIKU=claude-haiku-5-5; SONNET=claude-sonnet-5-5
run() { echo "=== $1 $(date +%H:%M:%S)"; $P run_evals.py "$@" --workers 5 2>&1 | tail -1; }
run main        --runs 5 --model $OPUS
run haiku       --runs 3 --model $HAIKU
run sonnet      --runs 3 --model $SONNET
run vague       --runs 3 --model $OPUS --mcp mcp_vague.json
run precise     --runs 3 --model $OPUS --mcp mcp_precise.json
run verify      --runs 3 --model $OPUS --append-system-prompt "Before you answer, check your SQL result against the question: does it answer exactly what was asked?"
run messy_opus  --runs 3 --model $OPUS --mcp mcp_messy.json --questions questions_messy.json
run messy_haiku --runs 3 --model $HAIKU --mcp mcp_messy.json --questions questions_messy.json
echo "=== done $(date +%H:%M:%S)"
