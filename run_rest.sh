#!/bin/bash
# Resume run_all.sh: runs only the sets that have no results/SET.json yet (a set interrupted mid-way is re-run whole).
# Trimmed 2026-11-14 (user: "cut it"): the variant and messy sets run 2 repeats, not 3; sonnet had already finished at 3.
cd "$(dirname "$0")"
P=.venv/bin/python
OPUS=claude-opus-5-5; HAIKU=claude-haiku-5-5; SONNET=claude-sonnet-5-5
run() { [ -f "results/$1.json" ] && { echo "skip $1"; return; }; echo "=== $1 $(date +%H:%M:%S)"; $P run_evals.py "$@" --workers 5 2>&1 | tail -1; }
run main        --runs 5 --model $OPUS
run haiku       --runs 3 --model $HAIKU
run sonnet      --runs 3 --model $SONNET
run vague       --runs 2 --model $OPUS --mcp mcp_vague.json
run precise     --runs 2 --model $OPUS --mcp mcp_precise.json
run verify      --runs 2 --model $OPUS --append-system-prompt "Before you answer, check your SQL result against the question: does it answer exactly what was asked?"
run messy_opus  --runs 2 --model $OPUS --mcp mcp_messy.json --questions questions_messy.json
run messy_haiku --runs 2 --model $HAIKU --mcp mcp_messy.json --questions questions_messy.json
echo "=== done $(date +%H:%M:%S)"
