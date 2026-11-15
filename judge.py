"""LLM-as-judge: a second Claude Code call per logged answer (not an agent run; no tools, one turn).

Usage: python judge.py SET... --model M [--workers K]
Reads results/SET.json (the logged answers), asks the judge model PASS or FAIL given the question, the key facts and the answer,
and writes results/judge_<model-short>_<SET>.json with the judge's verdict, reason, cost and the scorer v3 verdict for comparison.
"""
import json, re, subprocess, sys, argparse
from concurrent.futures import ThreadPoolExecutor
from score import score

PROMPT = """You are grading an AI agent's answer to a question about a small shop database.

Question: {q}
Correct answer (key facts; an empty list means the correct answer is that there is none): {keys}
Agent's answer:
\"\"\"{answer}\"\"\"

Does the agent's answer give the correct answer? Extra explanation, tables or caveats are fine as long as the core answer is right.
Reply with exactly one line: PASS or FAIL, a colon, and one short sentence why."""

def judge_one(model, q, row):
    keys = json.dumps(q["keys"])
    p = subprocess.run(["claude", "-p", PROMPT.format(q=q["question"], keys=keys, answer=row["answer"] or ""),
                        "--tools", "", "--max-turns", "1", "--model", model, "--output-format", "json"],
                       capture_output=True, text=True)
    try:
        res = json.loads(p.stdout)
        text = res.get("result", ""); cost = res.get("total_cost_usd", 0.0); used = list((res.get("modelUsage") or {}).keys())
    except Exception:
        text = p.stdout.strip() or p.stderr.strip(); cost = 0.0; used = []
    m = re.match(r"\s*\**(PASS|FAIL)\**\s*:?\s*(.*)", text, re.S)
    verdict = m.group(1).lower() if m else "unparsed"
    sv, sr = score(q, row["answer"] or "")
    return {"id": row["id"], "name": row.get("name"), "judge": verdict, "judge_reason": (m.group(2) if m else text)[:300],
            "judge_cost": cost, "judge_model": used, "scorer_v3": sv, "scorer_reason": sr, "answer": row["answer"]}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("sets", nargs="+"); ap.add_argument("--model", required=True)
    ap.add_argument("--workers", type=int, default=5); ap.add_argument("--questions", default="questions.json")
    a = ap.parse_args()
    qs = {q["id"]: q for q in json.load(open(a.questions))}
    short = a.model.split("-")[1] if "-" in a.model else a.model
    for s in a.sets:
        rows = json.load(open(f"results/{s}.json"))
        with ThreadPoolExecutor(a.workers) as ex:
            out = list(ex.map(lambda r: judge_one(a.model, qs[r["id"]], r), rows))
        json.dump(out, open(f"results/judge_{short}_{s}.json", "w"), indent=1)
        agree = sum(1 for o in out if o["judge"] == o["scorer_v3"]); cost = sum(o["judge_cost"] for o in out)
        jp = sum(1 for o in out if o["judge"] == "pass"); unp = sum(1 for o in out if o["judge"] == "unparsed")
        print(f"judge {short} on {s}: {len(out)} answers, judge pass {jp}, agrees with scorer v3 on {agree}, unparsed {unp}, cost ${cost:.3f}")

if __name__ == "__main__":
    main()
