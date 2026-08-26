#!/usr/bin/env python3
"""V4 RQ02 T04 — Proof quality comparison: ad-hoc vs AgenticLoop on BRUMO 2025.

Uses local model as automated grader on 4-dimension rubric (1-7 scale):
1. Assumption clarity (假设明确性)
2. Logical coherence (逻辑连贯性)
3. Conclusion completeness (结论完整性)
4. No unsupported leaps (无逻辑跳跃)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "config"))
from model_client import ModelClient

RUNS_DIR = Path(__file__).parent.parent.parent / "runs"
DATA_DIR = Path(__file__).parent.parent.parent / "datasets" / "brumo_2025"

RUBRIC_PROMPT = """You are an expert math competition grader. Evaluate the following TWO proof sketches for the same problem against the official solution.

Rate each proof sketch on a 1-7 scale for each dimension. Output ONLY JSON.

## Problem
{problem_text}

## Official Solution
{gold_solution}

## Proof Sketch A (Ad-hoc)
{adhoc_proof}

## Proof Sketch B (AgenticLoop)
{loop_proof}

## Rubric (1-7 scale)
1. assumption_clarity: Are all given conditions correctly stated and used? (1=missing key assumptions, 7=all assumptions explicitly noted)
2. logical_coherence: Does each step follow from previous steps with justification? (1=disconnected steps, 7=rigorous logical chain)
3. conclusion_completeness: Does the answer directly and fully address the problem? (1=missing or wrong conclusion, 7=complete correct answer)
4. no_unsupported_leaps: Are there no gaps requiring unstated assumptions? (1=major leaps, 7=every step justified)

## Instructions
Compare both sketches against the official solution. Be critical but fair. Proof Sketch B may have more explicit structure (hypotheses, lemmas) — reward this if it improves clarity, but do not inflate scores for structure alone if reasoning is wrong.

Output ONLY JSON:
```json
{{
  "adhoc": {{
    "assumption_clarity": <int>,
    "logical_coherence": <int>,
    "conclusion_completeness": <int>,
    "no_unsupported_leaps": <int>,
    "overall": <int>,
    "comment": "<one sentence critique>"
  }},
  "loop": {{
    "assumption_clarity": <int>,
    "logical_coherence": <int>,
    "conclusion_completeness": <int>,
    "no_unsupported_leaps": <int>,
    "overall": <int>,
    "comment": "<one sentence critique>"
  }},
  "better_method": "<adhoc or loop or tie>",
  "rationale": "<one sentence why one is better>"
}}
```"""


def load_data():
    with open(RUNS_DIR / "V4_RQ02_T02_adhoc_proofs.json", "r", encoding="utf-8") as f:
        adhoc = json.load(f)["results"]
    with open(RUNS_DIR / "V4_RQ02_T03_loop_proofs.json", "r", encoding="utf-8") as f:
        loop = json.load(f)
    with open(DATA_DIR / "problems.json", "r", encoding="utf-8") as f:
        problems = {p["id"]: p for p in json.load(f)}
    with open(DATA_DIR / "solutions.json", "r", encoding="utf-8") as f:
        solutions = {s["id"]: s for s in json.load(f)}
    return adhoc, loop, problems, solutions


def parse_grading_json(text):
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
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def grade_problem(client, problem, solution, adhoc_result, loop_result):
    pid = problem["id"]
    prompt = RUBRIC_PROMPT.format(
        problem_text=problem["problem_text"],
        gold_solution=solution.get("solution_text", solution.get("answer", "")),
        adhoc_proof=adhoc_result["model_response"],
        loop_proof=loop_result.get("proof", loop_result.get("model_response", "")),
    )

    messages = [{"role": "user", "content": prompt}]
    try:
        response = client.chat(messages, temperature=0, max_tokens=2048)
        content = response.get("content", "")
        usage = response.get("usage", {})
    except Exception as e:
        print(f"  [ERROR] Grading problem {pid}: {e}", flush=True)
        return None, {}

    parsed = parse_grading_json(content)
    if parsed is None:
        print(f"  [WARN] JSON parse failed for problem {pid}", flush=True)
        return None, usage

    return parsed, usage


def main():
    adhoc, loop, problems, solutions = load_data()
    client = ModelClient()

    adhoc_map = {r["problem_id"]: r for r in adhoc}
    loop_map = {r["problem_id"]: r for r in loop}

    gradings = []
    total_tokens = 0
    parse_failures = 0

    for pid in sorted(adhoc_map.keys()):
        problem = problems[pid]
        solution = solutions[pid]
        adhoc_result = adhoc_map[pid]
        loop_result = loop_map[pid]

        print(f"\nGrading problem {pid}/15 ...", flush=True)
        grading, usage = grade_problem(client, problem, solution, adhoc_result, loop_result)

        if grading is None:
            parse_failures += 1
            grading = {
                "adhoc": {"assumption_clarity": 1, "logical_coherence": 1, "conclusion_completeness": 1, "no_unsupported_leaps": 1, "overall": 1, "comment": "parse failure"},
                "loop": {"assumption_clarity": 1, "logical_coherence": 1, "conclusion_completeness": 1, "no_unsupported_leaps": 1, "overall": 1, "comment": "parse failure"},
                "better_method": "tie",
                "rationale": "JSON parse failure",
            }

        grading["problem_id"] = pid
        gradings.append(grading)

        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens += prompt_tokens + completion_tokens

        print(f"  Ad-hoc: {grading['adhoc']['overall']}, Loop: {grading['loop']['overall']}, Better: {grading['better_method']}", flush=True)

    # Aggregate scores
    dimensions = ["assumption_clarity", "logical_coherence", "conclusion_completeness", "no_unsupported_leaps", "overall"]
    adhoc_avg = {d: sum(g["adhoc"][d] for g in gradings) / len(gradings) for d in dimensions}
    loop_avg = {d: sum(g["loop"][d] for g in gradings) / len(gradings) for d in dimensions}

    better_counts = {"adhoc": 0, "loop": 0, "tie": 0}
    for g in gradings:
        better_counts[g["better_method"]] += 1

    # Paired t-test approximation
    import math
    diffs = [g["loop"]["overall"] - g["adhoc"]["overall"] for g in gradings]
    mean_diff = sum(diffs) / len(diffs)
    variance = sum((d - mean_diff) ** 2 for d in diffs) / len(diffs)
    std_err = math.sqrt(variance / len(diffs)) if variance > 0 else 0
    t_stat = mean_diff / std_err if std_err > 0 else 0

    report_lines = [
        "# V4 RQ02 T04 — Proof Quality Comparison: Ad-hoc vs AgenticLoop",
        "",
        "## Aggregate Scores (1-7 scale)",
        "",
        "| Dimension | Ad-hoc | AgenticLoop | Delta |",
        "|-----------|--------|--------------|-------|",
    ]
    for d in dimensions:
        report_lines.append(f"| {d} | {adhoc_avg[d]:.2f} | {loop_avg[d]:.2f} | {loop_avg[d] - adhoc_avg[d]:+.2f} |")

    report_lines.extend([
        "",
        "## Winner Counts",
        "",
        f"- Ad-hoc better: {better_counts['adhoc']}",
        f"- AgenticLoop better: {better_counts['loop']}",
        f"- Tie: {better_counts['tie']}",
        "",
        "## Paired Comparison (Overall score)",
        "",
        f"- Mean difference (Loop - Ad-hoc): {mean_diff:+.2f}",
        f"- Standard error: {std_err:.3f}",
        f"- t-statistic: {t_stat:.3f}",
        f"- Problems graded: {len(gradings)}",
        f"- JSON parse failures: {parse_failures}",
        f"- Total grading tokens: {total_tokens}",
        "",
        "## Per-Problem Grading",
        "",
        "| PID | AH Overall | Loop Overall | Winner | Rationale |",
        "|-----|------------|--------------|--------|-----------|",
    ])

    for g in gradings:
        report_lines.append(
            f"| {g['problem_id']} | {g['adhoc']['overall']} | {g['loop']['overall']} | {g['better_method']} | {g['rationale']} |"
        )

    report = "\n".join(report_lines)

    # Write outputs
    csv_path = RUNS_DIR / "V4_RQ02_T04_proof_comparison.csv"
    import csv
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "problem_id", "adhoc_assumption", "adhoc_logic", "adhoc_conclusion", "adhoc_leaps", "adhoc_overall",
            "loop_assumption", "loop_logic", "loop_conclusion", "loop_leaps", "loop_overall",
            "better_method", "rationale"
        ])
        writer.writeheader()
        for g in gradings:
            writer.writerow({
                "problem_id": g["problem_id"],
                "adhoc_assumption": g["adhoc"]["assumption_clarity"],
                "adhoc_logic": g["adhoc"]["logical_coherence"],
                "adhoc_conclusion": g["adhoc"]["conclusion_completeness"],
                "adhoc_leaps": g["adhoc"]["no_unsupported_leaps"],
                "adhoc_overall": g["adhoc"]["overall"],
                "loop_assumption": g["loop"]["assumption_clarity"],
                "loop_logic": g["loop"]["logical_coherence"],
                "loop_conclusion": g["loop"]["conclusion_completeness"],
                "loop_leaps": g["loop"]["no_unsupported_leaps"],
                "loop_overall": g["loop"]["overall"],
                "better_method": g["better_method"],
                "rationale": g["rationale"],
            })

    report_path = RUNS_DIR / "V4_RQ02_T04_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n=== SUMMARY ===")
    print(f"Problems graded: {len(gradings)}")
    print(f"Ad-hoc avg overall: {adhoc_avg['overall']:.2f}")
    print(f"Loop avg overall: {loop_avg['overall']:.2f}")
    print(f"Better counts: {better_counts}")
    print(f"Mean diff: {mean_diff:+.2f}, t={t_stat:.3f}")
    print(f"Total grading tokens: {total_tokens}")
    print(f"Artifacts written to {RUNS_DIR}")


if __name__ == "__main__":
    main()
