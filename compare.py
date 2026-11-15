"""Compare result sets: one row per set with pass rate, flaky questions, cost per correct answer, turns; then per-question pass across sets.

Usage: .venv/bin/python compare.py main haiku sonnet vague precise verify messy_opus messy_haiku
Re-scores every saved answer with the current score.py (against the questions file the set was run with), so the table always reflects
the latest scorer; the original verdicts stay in results/SET.json.
"""
import json, sys
from collections import defaultdict
from pathlib import Path
from score import score
HERE = Path(__file__).parent
sets = sys.argv[1:]
rows_by_set, qfiles = {}, {}
for s in sets:
    rows = json.loads((HERE / "results" / f"{s}.json").read_text())
    qf = rows[0].get("questions", "questions.json"); qfiles[s] = qf
    qs = {q["id"]: q for q in json.loads((HERE / qf).read_text())}
    for r in rows:
        r["verdict"], r["reason"] = score(qs[r["id"]], r["answer"])
    rows_by_set[s] = rows
print("| set | model | questions | runs | pass | pass rate | fail reasons | flaky q | errors | mean turns | total cost | cost per correct |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|")
for s, rows in rows_by_set.items():
    n = len(rows); p = sum(r["verdict"] == "pass" for r in rows); cost = sum(r["cost_usd"] for r in rows)
    by_q = defaultdict(list)
    for r in rows: by_q[r["id"]].append(r["verdict"] == "pass")
    flaky = [q for q, v in by_q.items() if 0 < sum(v) < len(v)]
    reasons = defaultdict(int)
    for r in rows:
        if r["reason"]: reasons[r["reason"]] += 1
    errors = sum(1 for r in rows if r["subtype"] != "success" or "hit your 5-hour limit" in (r.get("answer") or ""))
    models = sorted({r["model"] for r in rows if r["model"]})
    print(f"| {s} | {'/'.join(models)} | {qfiles[s]} | {n} | {p} | {100*p/n:.0f}% | {dict(reasons) or '-'} | {len(flaky)} {flaky if flaky else ''} | {errors} | "
          f"{sum(r['turns'] or 0 for r in rows)/n:.1f} | ${cost:.2f} | ${cost/p if p else 0:.4f} |")
print("\nPer question (passes/runs):")
ids = [q["id"] for q in json.loads((HERE / "questions.json").read_text())]
print("| q | " + " | ".join(sets) + " |\n|---|" + "---|" * len(sets))
for qid in ids:
    cells = []
    for s in sets:
        rs = [r for r in rows_by_set[s] if r["id"] == qid]
        p = sum(r["verdict"] == "pass" for r in rs); cells.append(f"{p}/{len(rs)}" if rs else "-")
    print(f"| {qid} | " + " | ".join(cells) + " |")
