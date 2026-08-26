#!/usr/bin/env python3
"""V4 RQ02 T03 — AgenticLoop protocol proof sketch generation on BRUMO 2025."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "config"))
from model_client import ModelClient

DATA_DIR = Path(__file__).parent.parent.parent / "datasets" / "brumo_2025"
RUNS_DIR = Path(__file__).parent.parent.parent / "runs"

PHASES = [
    ("hypothesis", "Read this math competition problem carefully. State the key assumptions and what you need to prove or compute.\n\nProblem: {problem_text}"),
    ("lemma_development", "Propose any lemmas or intermediate results that will help solve this problem. For each lemma, briefly justify why it is relevant.\n\nProblem: {problem_text}\n\nKey assumptions: {hypothesis}"),
    ("main_proof", "Construct the main proof or solution. Show all key reasoning steps, calculations, and logical connections. Do not skip steps.\n\nProblem: {problem_text}\n\nLemmas: {lemmas}"),
    ("verification", "Verify your proof: (a) Did you use all given conditions? (b) Are there any logical gaps? (c) Does the conclusion directly answer the problem?\n\nProblem: {problem_text}\n\nProof: {proof}"),
    ("structured_output", "Output ONLY the following JSON format. No extra text outside the JSON.\n```json\n{{\n  \"final_answer\": \"<your answer as a string>\",\n  \"key_lemmas\": [\"lemma 1\", \"lemma 2\"],\n  \"proof_summary\": \"<one-sentence summary of proof strategy>\",\n  \"confidence\": <1-10>,\n  \"audit_passed\": <true/false>\n}}\n```\n\nProblem: {problem_text}\n\nProof: {proof}"),
]


def load_data():
    with open(DATA_DIR / "problems.json", "r", encoding="utf-8") as f:
        problems = json.load(f)
    with open(DATA_DIR / "solutions.json", "r", encoding="utf-8") as f:
        solutions = {s["id"]: s for s in json.load(f)}
    return problems, solutions


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
        return {
            "final_answer": data.get("final_answer"),
            "key_lemmas": data.get("key_lemmas", []),
            "proof_summary": data.get("proof_summary"),
            "confidence": data.get("confidence"),
            "audit_passed": data.get("audit_passed"),
        }
    except (json.JSONDecodeError, ValueError):
        return None


def run_problem(client, problem, gold_solution):
    problem_text = problem["problem_text"]
    problem_id = problem["id"]

    result = {
        "problem_id": problem_id,
        "hypothesis": None,
        "lemmas": None,
        "proof": None,
        "verification": None,
        "predicted_answer": None,
        "key_lemmas": [],
        "proof_summary": None,
        "confidence": None,
        "audit_passed": None,
        "usage": {},
        "phases": [],
    }

    total_tokens = 0
    hypothesis = ""
    lemmas = ""
    proof = ""

    for phase_name, prompt_template in PHASES:
        if phase_name == "hypothesis":
            prompt = prompt_template.format(problem_text=problem_text)
        elif phase_name == "lemma_development":
            prompt = prompt_template.format(problem_text=problem_text, hypothesis=hypothesis)
        elif phase_name == "main_proof":
            prompt = prompt_template.format(problem_text=problem_text, lemmas=lemmas)
        else:
            prompt = prompt_template.format(problem_text=problem_text, proof=proof)

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

        result["phases"].append({
            "phase_name": phase_name,
            "prompt": prompt,
            "response": content,
            "usage": usage,
            "finish_reason": finish_reason,
        })

        if phase_name == "hypothesis":
            hypothesis = content.strip()
            result["hypothesis"] = hypothesis
        elif phase_name == "lemma_development":
            lemmas = content.strip()
            result["lemmas"] = lemmas
        elif phase_name == "main_proof":
            proof = content.strip()
            result["proof"] = proof
        elif phase_name == "verification":
            result["verification"] = content.strip()
        elif phase_name == "structured_output":
            parsed = parse_json_output(content)
            if parsed:
                result["predicted_answer"] = parsed["final_answer"]
                result["key_lemmas"] = parsed["key_lemmas"]
                result["proof_summary"] = parsed["proof_summary"]
                result["confidence"] = parsed["confidence"]
                result["audit_passed"] = parsed["audit_passed"]

    result["usage"] = {
        "total_tokens": total_tokens,
        "prompt_tokens": sum(p["usage"].get("prompt_tokens", 0) for p in result["phases"]),
        "completion_tokens": sum(p["usage"].get("completion_tokens", 0) for p in result["phases"]),
    }
    return result


def main():
    problems, solutions = load_data()
    client = ModelClient()
    env = client.get_env_info()
    print(f"Endpoint: {env['endpoint']}", flush=True)
    print(f"Model: {env['model_name']}", flush=True)

    all_results = []
    total_tokens = 0
    json_failures = 0
    endpoint_errors = 0

    for problem in problems:
        pid = problem["id"]
        gold = solutions.get(pid, {})
        print(f"\nProblem {pid}/15 ...", flush=True)
        result = run_problem(client, problem, gold)
        all_results.append(result)

        if result["predicted_answer"] is None:
            json_failures += 1
            print(f"  JSON PARSE FAILURE", flush=True)
        else:
            print(f"  Answer: {result['predicted_answer']}", flush=True)

        for phase in result["phases"]:
            if phase["finish_reason"] == "error":
                endpoint_errors += 1

        total_tokens += result["usage"]["total_tokens"]

        # Save incremental results
        with open(RUNS_DIR / "V4_RQ02_T03_loop_proofs.json", "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)

    summary_text = (
        f"Total problems: {len(all_results)}\n"
        f"Total tokens: {total_tokens}\n"
        f"JSON parse failures: {json_failures}\n"
        f"Endpoint errors: {endpoint_errors}\n"
    )

    with open(RUNS_DIR / "V4_RQ02_T03_loop_accuracy.txt", "w", encoding="utf-8") as f:
        f.write(summary_text)

    claims = {}
    for r in all_results:
        claims[f"problem_{r['problem_id']}"] = {
            "claim": f"Proof sketch for problem {r['problem_id']}",
            "predicted_answer": r["predicted_answer"],
            "gold_answer": solutions.get(r["problem_id"], {}).get("answer"),
            "proof_artifact": f"runs/V4_RQ02_T03_loop_proofs.json#problem_id={r['problem_id']}",
            "key_lemmas": r["key_lemmas"],
            "audit_passed": r["audit_passed"],
            "confidence": r["confidence"],
        }

    import yaml
    with open(RUNS_DIR / "V4_RQ02_T03_loop_claims.yaml", "w", encoding="utf-8") as f:
        yaml.dump(claims, f, allow_unicode=True, sort_keys=False)

    print("\n=== SUMMARY ===", flush=True)
    print(summary_text, flush=True)
    print(f"Artifacts written to {RUNS_DIR}", flush=True)


if __name__ == "__main__":
    main()
