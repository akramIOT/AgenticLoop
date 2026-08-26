"""V4 RQ01 T02: ad-hoc baseline run (30 AIME problems)."""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.v4.config.model_client import ModelClient


def load_data():
    repo = Path(__file__).resolve().parents[2]
    problems_path = repo / "datasets" / "aime_2026" / "problems.json"
    answers_path = repo / "datasets" / "aime_2026" / "answer_key.json"
    with open(problems_path, "r", encoding="utf-8") as f:
        problems = json.load(f)
    with open(answers_path, "r", encoding="utf-8") as f:
        answers = {a["id"]: a["answer"] for a in json.load(f)}
    return problems, answers


def extract_integer_answer(text):
    if not text:
        return None
    # Look for the last sequence of digits that looks like an answer
    # First try to find explicit answer patterns
    patterns = [
        r"answer is\s+(\d+)",
        r"answer:\s*(\d+)",
        r"\\boxed\{(\d+)\}",
        r"\*\*(\d+)\*\*",
        r"\b(\d{1,3})\b",
    ]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            val = int(match.group(1))
            if 0 <= val <= 999:
                return val
    # Fallback: find all 1-3 digit numbers and return the last one
    nums = re.findall(r"\b(\d{1,3})\b", text)
    if nums:
        return int(nums[-1])
    # Last resort: any digit sequence
    nums = re.findall(r"\d+", text)
    if nums:
        val = int(nums[-1])
        if 0 <= val <= 999:
            return val
        # If more than 3 digits, maybe it's a concatenation? Try last 3 digits
        return val % 1000
    return None


def run():
    problems, answers = load_data()
    client = ModelClient()

    results = []
    total_tokens = 0
    total_cost_usd = 0.0

    for p in problems:
        pid = p["id"]
        problem_text = p["problem_text"]
        gold = answers.get(pid)

        prompt = (
            "Solve the following AIME problem. Give only the integer answer (000-999).\n\n"
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

        pred = extract_integer_answer(content)
        correct = pred == gold if pred is not None else False

        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens += prompt_tokens + completion_tokens

        # Cost estimate: assume ~$0.001 per 1K tokens (local self-hosting, negligible)
        # But we record 0 since local hosting has no per-token API cost
        cost_usd = 0.0
        total_cost_usd += cost_usd

        results.append({
            "problem_id": pid,
            "predicted_answer": pred,
            "correct": correct,
            "gold_answer": gold,
            "model_response": content,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            "cost_usd": cost_usd,
        })

    correct_count = sum(1 for r in results if r["correct"])
    accuracy = correct_count / len(results)

    summary = {
        "accuracy": accuracy,
        "correct_count": correct_count,
        "total_problems": len(results),
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost_usd,
        "model": client.get_env_info(),
    }

    output = {
        "results": results,
        "summary": summary,
    }

    repo = Path(__file__).resolve().parents[2]
    runs_dir = repo / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    results_path = runs_dir / "V4_RQ01_T02_adhoc_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    accuracy_path = runs_dir / "V4_RQ01_T02_adhoc_accuracy.txt"
    with open(accuracy_path, "w", encoding="utf-8") as f:
        f.write(f"Accuracy: {correct_count}/30 ({accuracy*100:.1f}%)\n")

    print(f"Completed {len(results)} problems.")
    print(f"Accuracy: {correct_count}/30 ({accuracy*100:.1f}%)")
    print(f"Total tokens: {total_tokens}")
    print(f"Results written to {results_path}")
    print(f"Accuracy summary written to {accuracy_path}")


if __name__ == "__main__":
    run()
