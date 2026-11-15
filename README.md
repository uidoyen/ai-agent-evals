# ai-agent-evals

The code and run logs behind the video **AI Agent Evals From Scratch: I Ran One Agent 465 Times**: [VIDEO LINK]

What is here: one tiny shop database (`shop.db`, made-up data: 5 customers, 8 orders), one MCP server
(`db_server.py`, three read-only tools), Claude Code run headless as the agent, and an eval: 20 questions with a reviewed true
answer each, a scorer, and a runner that repeats. Every number in the video comes from a logged run in `runs/`.

## Run it
Needs Python 3.11+, [uv](https://docs.astral.sh/uv/) and Claude Code (the agent under test; a run uses your Claude plan or API credit).
The four `mcp*.json` files hold absolute paths to this folder: replace `/ABSOLUTE/PATH/TO/ai-agent-evals` with the folder's real path first.
```bash
uv sync
.venv/bin/python check_truth.py                      # prints each question's SQL rows next to its stored keys
.venv/bin/python run_evals.py pilot --runs 1 --model claude-opus-5-5   # 20 questions, once each
.venv/bin/python run_evals.py main --runs 5 --model claude-opus-5-5    # the main set (always pin the model: the default drifted in the pilot)
.venv/bin/python run_evals.py haiku --runs 3 --model claude-haiku-5-5
.venv/bin/python run_evals.py verify --runs 3 --append-system-prompt "Check your SQL result against the question before answering."
```
`run_evals.py SET [--runs N] [--model NAME] [--mcp FILE] [--append-system-prompt TEXT] [--workers K] [--only q01,q02]` writes
`runs/SET/<qid>_r<k>.json` (Claude Code's result) and `.stream.jsonl` (every message), plus `results/SET.json` with every run's
verdict, reason, turns, tool calls and cost. Each run gets an empty working folder and only the shop tools.

| File | What it does |
|---|---|
| `questions.json` | 20 questions: 15 with a fact as the answer, 5 whose true answer is "none"; each with the SQL that gives the truth and the keys the scorer looks for |
| `check_truth.py` | runs every question's SQL so the truth is reviewed by hand once (SQL can be wrong too) |
| `score.py` | pass or fail for one answer (definitions below) |
| `agent.py` | one Claude Code headless run with the MCP tools, logged |
| `run_evals.py` | every question, N runs, scored, summarised |
| `judge.py` | LLM-as-judge: one no-tool Claude Code call per logged answer (PASS/FAIL + one sentence), compared with scorer v3; `python judge.py SET... --model M` |
| `compare.py`, `rescore.py`, `summarize.py` | re-score saved answers with the current scorer and print the per-set and per-question tables |
| `db_server.py`, `mcp.json`, `shop.db`, `make_db.py` | the three read-only tools, from https://github.com/uidoyen/mcp-database-server |

## Metrics
- **Pass** (fact questions): the final answer contains every key after normalisation: string keys case-insensitive (surnames, so
  "Ben" alone fails, "Ben Okafor" passes); number keys equal to any number in the answer to 2 decimals, after stripping currency
  marks and thousands separators. **Pass** (none-questions): a negative phrase and no customer or item name from the database.
- **Fail reasons**: `wrong` (a different fact), `invented` (a fact where there is none), `names_present` (a negative phrase, but
  database names listed; reviewed by hand), `no_answer` (empty result or cut off).
- **Pass rate** = passes / (questions x runs). **Per-question pass** = passes / runs ("4 of 5"); **flaky** when neither 0 nor 1.
- **Cost** = Claude Code's `total_cost_usd` per run, a list-price estimate. **Cost per correct answer** = set cost / passes.
  **Turns** = `num_turns` as Claude Code reports it. Comparisons change one factor at a time and state N.

Results hold for this agent, these models and these questions only: run your own. MIT licence (see `LICENSE`).
Replace this working name before publishing.

## About the logs
`runs/` holds one result file and one message log per run (465 runs across the sets, plus the batch that hit a usage limit in
`results/invalid_ratelimit/`). The logs are trimmed for publishing: only the start event (tools, model, version), the assistant and
tool messages and the final result are kept, and local paths are replaced. Cost figures are Claude Code's own list-price estimates.
`shop.db` and `shop_messy.db` are made-up data; `make_db.py` and `make_messy_db.py` rebuild them.

MIT licence.
