"""Run one prompt through Claude Code headless with only the shop-db MCP tools, and log the result.

run(name, prompt, ...) writes runs/<set>/<name>.json (Claude Code's result message) and <name>.stream.jsonl (every message), and
returns a dict: answer, turns, tool_calls, cost_usd (Claude Code's total_cost_usd, a list-price estimate), subtype, model.
"""
import json, subprocess, tempfile
from pathlib import Path

HERE = Path(__file__).parent


def run(name, prompt, *, set_name="adhoc", mcp="mcp.json", max_turns=40, budget=1.0, model=None, append_system_prompt=None):
    out = HERE / "runs" / set_name
    out.mkdir(parents=True, exist_ok=True)
    cmd = ["claude", "-p", prompt, "--mcp-config", str(HERE / mcp), "--strict-mcp-config",
           "--tools", "", "--allowedTools", "mcp__shop-db",
           "--max-turns", str(max_turns), "--max-budget-usd", str(budget), "--output-format", "stream-json", "--verbose"]
    if model:
        cmd += ["--model", model]
    if append_system_prompt:
        cmd += ["--append-system-prompt", append_system_prompt]
    with tempfile.TemporaryDirectory() as empty:  # empty cwd: nothing to read but the tools
        p = subprocess.run(cmd, cwd=empty, stdin=subprocess.DEVNULL, capture_output=True, text=True)
    (out / f"{name}.stream.jsonl").write_text(p.stdout)
    msgs = [json.loads(l) for l in p.stdout.splitlines() if l.strip()]
    res = next((m for m in reversed(msgs) if m.get("type") == "result"), {})
    calls = [(b["name"].replace("mcp__shop-db__", ""), b["input"]) for m in msgs if m.get("type") == "assistant"
             for b in m["message"]["content"] if b.get("type") == "tool_use"]
    (out / f"{name}.json").write_text(json.dumps(res, indent=1))
    models = list((res.get("modelUsage") or {}).keys())
    return {"name": name, "answer": res.get("result") or "", "turns": res.get("num_turns"), "tool_calls": len(calls),
            "calls": calls, "cost_usd": res.get("total_cost_usd") or 0.0, "subtype": res.get("subtype"),
            "model": models[0] if models else None, "stderr": p.stderr[:300] if p.returncode and not res else ""}
