#!/usr/bin/env python3
"""Resume T03 from problem 18 to 30, appending to existing results."""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "config"))
from model_client import ModelClient

DATA_DIR = Path(__file__).parent.parent.parent / "datasets" / "aime_2026"
RUNS_DIR = Path(__file__).parent.parent.parent / "runs"

PHASES = [
    ("strategy", "Analyze this AIME problem. State your solution strategy in one sentence.\n\nProblem: {problem_text}"),
    ("execution", "Execute your strategy step by step. Show all reasoning and intermediate calculations.\n\nProblem: {problem_text}\n\nStrategy: {strategy}"),
    ("verification", "Verify your intermediate results. Are there any calculation errors or logical gaps? If so, correct them.\n\nProblem: {problem_text}\n\nReasoning: {reasoning_chain}"),
    ("audit", "Audit your final answer: (a) Does it satisfy all problem conditions? (b) Is it in range 000-999? (c) Re-read the problem to ensure you didn't misinterpret any condition.\n\nProblem: {problem_text}\n\nReasoning: {reasoning_chain}"),
    ("structured_output", "Output ONLY the following JSON format. No extra text outside the JSON.\n```json\n{{\n  \"final_answer\": <integer 000-999>,\n  \"confidence\": <1-10>,\n  \"audit_passed\": <true/false>\n}}\n```\n\nProblem: {problem_text}\n\nReasoning: {reasoning_chain}"),
]


def load_data():
    with open(DATA_DIR / "problems.json", "r", encoding="utf-8") as f:
        problems = json.load(f)
    with open(DATA_DIR / "answer_key.json", "r", encoding="utf-8") as f:
        answer_key = {item["id"]: item["answer"] for item in json.load(f)}
    return problems, answer_key


def parse_json_output(text):
    text = text.strip()
    if "```json" in text:
        start = text.find("```json") + len("```json")
        end = text.find("```", start)
        if end == -1:
            end = len(text)
        text = text[start:end].strip()
    elif "```" in text:
        start = text.find("```") + len("```")
        end = text.find("```", start)
        if end == -1:
            end = len(text)
        text = text[start:end].strip()
    try:
        data = json.loads(text)
        final_answer = data.get("final_answer")
        confidence = data.get("confidence")
        audit_passed = data.get("audit_passed")
        if final_answer is not None and not isinstance(final_answer, int):
            try:
                final_answer = int(final_answer)
            except (ValueError, TypeError):
                final_answer = None
        if confidence is not None and not isinstance(confidence, int):
            try:
                confidence = int(confidence)
            except (ValueError, TypeError):
                confidence = None
        if audit_passed is not None and not isinstance(audit_passed, bool):
            audit_passed = bool(audit_passed)
        return final_answer, confidence, audit_passed
    except json.JSONDecodeError:
        return None, None, None


def run_problem(client, problem, gold_answer):
    problem_text = problem["problem_text"]
    problem_id = problem["id"]

    results = {
        "problem_id": problem_id,
        "strategy": None,
        "reasoning_chain": None,
        "verification": None,
        "audit": None,
        "predicted_answer": None,
        "correct": False,
        "gold_answer": gold_answer,
        "confidence": None,
        "audit_passed": None,
        "usage": {},
        "cost_usd": 0.0,
        "phases": [],
    }

    total_tokens = 0
    total_cost = 0.0
    strategy = ""
    reasoning_chain = ""

    for phase_name, prompt_template in PHASES:
        if phase_name == "strategy":
            prompt = prompt_template.format(problem_text=problem_text)
        elif phase_name == "execution":
            prompt = prompt_template.format(problem_text=problem_text, strategy=strategy)
        else:
            prompt = prompt_template.format(problem_text=problem_text, reasoning_chain=reasoning_chain)

        messages = [{"role": "user", "content": prompt}]
        try:
            response = client.chat(messages, temperature=0, max_tokens=4096)
        except Exception as e:
            print(f"  [ERROR] Problem {problem_id} phase {phase_name}: {e}", flush=True)
            response = {"content": f"ERROR: {e}", "usage": {}, "finish_reason": "error"}

        content = response.get("content", "")
        usage = response.get("usage", {})
        finish_reason = response.get("finish_reason", "")

        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens += prompt_tokens + completion_tokens
        total_cost += (prompt_tokens + completion_tokens) * 2.0 / 1e6

        results["phases"].append({
            "phase_name": phase_name,
            "prompt": prompt,
            "response": content,
            "usage": usage,
            "finish_reason": finish_reason,
        })

        if phase_name == "strategy":
            strategy = content.strip()
            results["strategy"] = strategy
        elif phase_name == "execution":
            reasoning_chain = content.strip()
            results["reasoning_chain"] = reasoning_chain
        elif phase_name == "verification":
            results["verification"] = content.strip()
        elif phase_name == "audit":
            results["audit"] = content.strip()
        elif phase_name == "structured_output":
            final_answer, confidence, audit_passed = parse_json_output(content)
            results["predicted_answer"] = final_answer
            results["confidence"] = confidence
            results["audit_passed"] = audit_passed
            results["correct"] = (final_answer == gold_answer)

    results["usage"] = {
        "total_tokens": total_tokens,
        "prompt_tokens": sum(p["usage"].get("prompt_tokens", 0) for p in results["phases"]),
        "completion_tokens": sum(p["usage"].get("completion_tokens", 0) for p in results["phases"]),
    }
    results["cost_usd"] = total_cost
    return results


def main():
    problems, answer_key = load_data()
    client = ModelClient()
    env = client.get_env_info()
    print(f"Endpoint: {env['endpoint']}", flush=True)
    print(f"Model: {env['model_name']}", flush=True)

    # Load existing results
    results_path = RUNS_DIR / "V4_RQ01_T03_loop_results.json"
    with open(results_path, "r", encoding="utf-8") as f:
        all_results = json.load(f)

    completed_ids = {r["problem_id"] for r in all_results}
    print(f"Already completed: {len(completed_ids)} problems", flush=True)

    correct_count = sum(1 for r in all_results if r["correct"])
    total_tokens = sum(r["usage"]["total_tokens"] for r in all_results)
    total_cost = sum(r["cost_usd"] for r in all_results)
    json_failures = sum(1 for r in all_results if r["predicted_answer"] is None)
    endpoint_errors = 0
    for r in all_results:
        for phase in r["phases"]:
            if phase["finish_reason"] == "error":
                endpoint_errors += 1

    for problem in problems:
        pid = problem["id"]
        if pid in completed_ids:
            continue
        gold = answer_key.get(pid)
        print(f"\nProblem {pid}/30 (gold={gold}) ...", flush=True)
        result = run_problem(client, problem, gold)
        all_results.append(result)

        if result["correct"]:
            correct_count += 1
            print(f"  CORRECT: predicted={result['predicted_answer']}", flush=True)
        else:
            print(f"  WRONG: predicted={result['predicted_answer']} (gold={gold})", flush=True)

        if result["predicted_answer"] is None:
            json_failures += 1
            print(f"  JSON PARSE FAILURE", flush=True)

        for phase in result["phases"]:
            if phase["finish_reason"] == "error":
                endpoint_errors += 1

        total_tokens += result["usage"]["total_tokens"]
        total_cost += result["cost_usd"]

        # Save incremental results
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

    accuracy = correct_count / len(all_results)
    summary = {
        "accuracy": accuracy,
        "correct_count": correct_count,
        "total_problems": len(all_results),
        "total_tokens": total_tokens,
        "total_cost_usd": total_cost,
        "avg_phases_per_problem": 5.0,
        "json_parse_failures": json_failures,
        "endpoint_errors": endpoint_errors,
    }

    summary_text = (
        f"Accuracy: {accuracy:.4f} ({correct_count}/{len(all_results)})\n"
        f"Total tokens: {total_tokens}\n"
        f"Total cost USD: ${total_cost:.4f}\n"
        f"JSON parse failures: {json_failures}\n"
        f"Endpoint errors: {endpoint_errors}\n"
    )

    with open(RUNS_DIR / "V4_RQ01_T03_loop_accuracy.txt", "w", encoding="utf-8") as f:
        f.write(summary_text)

    claims = {}
    for r in all_results:
        claims[f"problem_{r['problem_id']}"] = {
            "claim": f"Predicted answer {r['predicted_answer']} for problem {r['problem_id']}",
            "correct": r["correct"],
            "gold": r["gold_answer"],
            "reasoning_artifact": f"runs/V4_RQ01_T03_loop_results.json#problem_id={r['problem_id']}",
            "strategy": r["strategy"],
            "audit_passed": r["audit_passed"],
            "confidence": r["confidence"],
        }

    import yaml
    with open(RUNS_DIR / "V4_RQ01_T03_loop_claims.yaml", "w", encoding="utf-8") as f:
        yaml.dump(claims, f, allow_unicode=True, sort_keys=False)

    print("\n=== SUMMARY ===", flush=True)
    print(summary_text, flush=True)
    print(f"Artifacts written to {RUNS_DIR}", flush=True)


if __name__ == "__main__":
    main()
