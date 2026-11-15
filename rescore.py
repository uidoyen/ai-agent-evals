"""Re-score a saved results set with the current score.py (no new runs, no cost) and write results/SET.rescored.json.

Usage: .venv/bin/python rescore.py SET
"""
import json, sys
from pathlib import Path
from score import score
HERE = Path(__file__).parent
qs = {q["id"]: q for q in json.loads((HERE / "questions.json").read_text())}
s = sys.argv[1]
rows = json.loads((HERE / "results" / f"{s}.json").read_text())
changed = 0
for r in rows:
    v, reason = score(qs[r["id"]], r["answer"])
    if (v, reason) != (r["verdict"], r["reason"]):
        changed += 1; print(f"{r['id']} r{r['run']}: {r['verdict']}/{r['reason'] or '-'} -> {v}/{reason or '-'}")
    r["verdict"], r["reason"] = v, reason
(HERE / "results" / f"{s}.rescored.json").write_text(json.dumps(rows, indent=1))
passes = sum(r["verdict"] == "pass" for r in rows)
print(f"{s} rescored: {passes}/{len(rows)} passed, {changed} verdicts changed")
