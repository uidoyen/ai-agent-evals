"""Run every question of questions.json N times and score the answers.

Usage: .venv/bin/python run_evals.py SET [--runs N] [--model NAME] [--mcp FILE] [--questions FILE] [--append-system-prompt TEXT] [--workers K] [--only q01,q02]
Writes runs/SET/<qid>_r<k>.json|.stream.jsonl per run and results/SET.json (every run with verdict, reason, cost, turns), and prints a table.
Pass = see score.py. Cost = Claude Code's total_cost_usd (list-price estimate). Cost per correct answer = set cost / passes.
"""
import json, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from agent import run
from score import score

HERE = Path(__file__).parent
args = sys.argv[1:]
set_name = args[0]
def opt(flag, default=None):
    return args[args.index(flag) + 1] if flag in args else default
n_runs = int(opt("--runs", 1)); model = opt("--model"); mcp = opt("--mcp", "mcp.json"); asp = opt("--append-system-prompt")
workers = int(opt("--workers", 4)); only = opt("--only"); qfile = opt("--questions", "questions.json")
questions = json.loads((HERE / qfile).read_text())
if only:
    questions = [q for q in questions if q["id"] in only.split(",")]
jobs = [(q, r) for r in range(1, n_runs + 1) for q in questions]

def job(qr):
    q, r = qr
    res = run(f"{q['id']}_r{r}", q["question"], set_name=set_name, mcp=mcp, model=model, append_system_prompt=asp)
    verdict, reason = score(q, res["answer"])
    row = {"id": q["id"], "kind": q["kind"], "run": r, "verdict": verdict, "reason": reason, "questions": qfile, "mcp": mcp, "asp": asp, **res}
    print(f"{q['id']} r{r} {verdict:4} {reason:13} turns {res['turns']} calls {res['tool_calls']} ${res['cost_usd']:.3f} | {res['answer'][:90]!r}", flush=True)
    return row

with ThreadPoolExecutor(max_workers=workers) as ex:
    rows = list(ex.map(job, jobs))
(HERE / "results").mkdir(exist_ok=True)
(HERE / "results" / f"{set_name}.json").write_text(json.dumps(rows, indent=1))
passes = sum(r["verdict"] == "pass" for r in rows); cost = sum(r["cost_usd"] for r in rows)
print(f"\n{set_name}: {passes}/{len(rows)} passed ({100*passes/len(rows):.0f}%), cost ${cost:.3f}, "
      f"cost per correct ${cost/passes if passes else float('nan'):.3f}, model {rows[0]['model']}")
