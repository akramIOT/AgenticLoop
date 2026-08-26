#!/usr/bin/env python3
"""V4 RQ02 T02 — Ad-hoc baseline proof sketch generation on BRUMO 2025."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "config"))
from model_client import ModelClient

DATA_DIR = Path(__file__).parent.parent.parent / "datasets" / "brumo_2025"
RUNS_DIR = Path(__file__).parent.parent.parent / "runs"


def load_data():
    with open(DATA_DIR / "problems.json", "r", encoding="utf-8") as f:
        problems = json.load(f)
    with open(DATA_DIR / "solutions.json", "r", encoding="utf-8") as f:
        solutions = {s["id"]: s for s in json.load(f)}
    return problems, solutions


def run():
    problems, solutions = load_data()
    client = ModelClient()

    results = []
    total_tokens = 0

    for p in problems:
        pid = p["id"]
        problem_text = p["problem_text"]
        gold_solution = solutions.get(pid, {})

        prompt = (
            "Solve the following math competition problem. Provide a clear proof sketch "
            "with key steps and reasoning. State your final answer explicitly.\n\n"
            f"{problem_text}"
        )
        messages = [{"role": "user", "content": prompt}]

        try:
            resp = client.chat(messages, temperature=0, max_tokens=4096)
            content = resp.get("content", "")
            usage = resp.get("usage", {})
        except Exception as exc:
            content = f"[ERROR: {exc}]"
            usage = {}

        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens += prompt_tokens + completion_tokens

        results.append({
            "problem_id": pid,
            "problem_text": problem_text,
            "model_response": content,
            "gold_answer": gold_solution.get("answer"),
            "gold_solution": gold_solution.get("solution_text"),
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        })

    output = {
        "results": results,
        "summary": {
            "total_problems": len(results),
            "total_tokens": total_tokens,
            "model": client.get_env_info(),
        },
    }

    out_path = RUNS_DIR / "V4_RQ02_T02_adhoc_proofs.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Completed {len(results)} problems.")
    print(f"Total tokens: {total_tokens}")
    print(f"Results written to {out_path}")


if __name__ == "__main__":
    run()
