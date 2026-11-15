"""Print a results set as a table and the set's pass rate and cost per correct answer.

Usage: .venv/bin/python summarize.py SET [SET ...]   (reads results/SET.json)
"""
import json, sys
from collections import defaultdict
from pathlib import Path
HERE = Path(__file__).parent
for s in sys.argv[1:]:
    rows = json.loads((HERE / "results" / f"{s}.json").read_text())
    by_q = defaultdict(list)
    for r in rows:
        by_q[r["id"]].append(r)
    print(f"\n## {s}  (model {rows[0]['model']}, {len(rows)} runs)")
    print("| q | kind | pass | reasons | turns | calls | cost | answer (first run, 110 chars) |\n|---|---|---|---|---|---|---|---|")
    for qid, rs in by_q.items():
        p = sum(r["verdict"] == "pass" for r in rs)
        reasons = ",".join(sorted({r["reason"] for r in rs if r["reason"]})) or "-"
        turns = "/".join(str(r["turns"]) for r in rs); calls = "/".join(str(r["tool_calls"]) for r in rs)
        cost = sum(r["cost_usd"] for r in rs) / len(rs)
        print(f"| {qid} | {rs[0]['kind']} | {p}/{len(rs)} | {reasons} | {turns} | {calls} | ${cost:.3f} | {rs[0]['answer'][:110].replace(chr(10),' ')!r} |")
    passes = sum(r["verdict"] == "pass" for r in rows); cost = sum(r["cost_usd"] for r in rows)
    flaky = [q for q, rs in by_q.items() if 0 < sum(r["verdict"] == "pass" for r in rs) < len(rs)]
    print(f"\n{s}: {passes}/{len(rows)} passed ({100*passes/len(rows):.0f}%), cost ${cost:.3f}, cost per correct "
          f"${cost/passes if passes else float('nan'):.3f}, mean turns {sum(r['turns'] or 0 for r in rows)/len(rows):.1f}, flaky: {flaky or 'none'}")
