#!/usr/bin/env python3
"""V4 RQ01 T04 — Statistical comparison of ad-hoc vs AgenticLoop on AIME 2026."""

import json
import sys
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent / "config"))

RUNS_DIR = Path(__file__).parent.parent.parent / "runs"


def load_results():
    with open(RUNS_DIR / "V4_RQ01_T02_adhoc_results.json", "r", encoding="utf-8") as f:
        t02 = json.load(f)
    with open(RUNS_DIR / "V4_RQ01_T03_loop_results.json", "r", encoding="utf-8") as f:
        t03 = json.load(f)
    return t02["results"], t03


def build_table(ad_hoc, loop):
    """Build per-problem comparison table."""
    ad_map = {r["problem_id"]: r for r in ad_hoc}
    loop_map = {r["problem_id"]: r for r in loop}

    rows = []
    for pid in sorted(ad_map.keys()):
        a = ad_map[pid]
        l = loop_map.get(pid)
        if l is None:
            continue

        a_correct = a["correct"]
        l_correct = l["correct"]
        a_pred = a["predicted_answer"]
        l_pred = l["predicted_answer"]

        # Error mode classification
        if a_correct and l_correct:
            mode = "both_correct"
        elif not a_correct and l_correct:
            mode = "loop_fixed"
        elif a_correct and not l_correct:
            mode = "loop_broke"
        else:
            # Both wrong
            a_has_reasoning = a_pred is not None
            l_has_reasoning = l_pred is not None
            if not a_has_reasoning and l_has_reasoning:
                mode = "extraction_failure_only"
            elif a_has_reasoning and not l_has_reasoning:
                mode = "loop_json_failure"
            elif not a_has_reasoning and not l_has_reasoning:
                mode = "both_extraction_failure"
            else:
                mode = "both_wrong_reasoning"

        rows.append({
            "problem_id": pid,
            "gold": a["gold_answer"],
            "ad_hoc_pred": a_pred,
            "ad_hoc_correct": a_correct,
            "loop_pred": l_pred,
            "loop_correct": l_correct,
            "error_mode": mode,
        })
    return rows


def mcnemar_test(rows):
    """Compute McNemar's test for paired binary outcomes."""
    # Contingency table:
    # b = ad-hoc wrong, loop correct
    # c = ad-hoc correct, loop wrong
    b = sum(1 for r in rows if not r["ad_hoc_correct"] and r["loop_correct"])
    c = sum(1 for r in rows if r["ad_hoc_correct"] and not r["loop_correct"])

    # McNemar chi-square statistic (with continuity correction)
    if b + c == 0:
        chi2 = 0.0
        p_value = 1.0
    else:
        chi2 = (abs(b - c) - 1) ** 2 / (b + c)
        # Approximate p-value from chi-square with 1 df
        import math
        p_value = math.erfc(math.sqrt(chi2 / 2))

    return {
        "b_adhoc_wrong_loop_correct": b,
        "c_adhoc_correct_loop_wrong": c,
        "chi2_statistic": round(chi2, 4),
        "p_value": round(p_value, 6),
        "significant_at_0_05": p_value < 0.05,
    }


def error_breakdown(rows):
    """Analyze error mode frequencies."""
    modes = Counter(r["error_mode"] for r in rows)
    total = len(rows)

    ad_hoc_correct = sum(1 for r in rows if r["ad_hoc_correct"])
    loop_correct = sum(1 for r in rows if r["loop_correct"])
    ad_hoc_extract_fail = sum(1 for r in rows if r["ad_hoc_pred"] is None)
    loop_extract_fail = sum(1 for r in rows if r["loop_pred"] is None)

    return {
        "total_problems": total,
        "ad_hoc_accuracy": ad_hoc_correct / total,
        "loop_accuracy": loop_correct / total,
        "ad_hoc_correct_count": ad_hoc_correct,
        "loop_correct_count": loop_correct,
        "ad_hoc_extraction_failures": ad_hoc_extract_fail,
        "loop_extraction_failures": loop_extract_fail,
        "mode_counts": dict(modes),
        "absolute_improvement": (loop_correct - ad_hoc_correct) / total,
        "relative_improvement": (loop_correct / ad_hoc_correct) if ad_hoc_correct > 0 else float('inf'),
    }


def generate_report(rows, mcnemar, breakdown):
    lines = [
        "# V4 RQ01 T04 — Statistical Comparison: Ad-hoc vs AgenticLoop",
        "",
        "## Summary",
        "",
        f"- **Ad-hoc baseline**: {breakdown['ad_hoc_correct_count']}/{breakdown['total_problems']} correct ({breakdown['ad_hoc_accuracy']*100:.1f}%)",
        f"- **AgenticLoop protocol**: {breakdown['loop_correct_count']}/{breakdown['total_problems']} correct ({breakdown['loop_accuracy']*100:.1f}%)",
        f"- **Absolute improvement**: +{breakdown['absolute_improvement']*100:.1f} percentage points",
        "",
        "## McNemar Test (Paired Binary Classification)",
        "",
        f"- Ad-hoc wrong / Loop correct (b): {mcnemar['b_adhoc_wrong_loop_correct']}",
        f"- Ad-hoc correct / Loop wrong (c): {mcnemar['c_adhoc_correct_loop_wrong']}",
        f"- Chi-square statistic: {mcnemar['chi2_statistic']}",
        f"- p-value: {mcnemar['p_value']:.6f}",
        f"- Significant at alpha=0.05: **{'YES' if mcnemar['significant_at_0_05'] else 'NO'}**",
        "",
        "## Error Mode Breakdown",
        "",
        "| Mode | Count | Description |",
        "|------|-------|-------------|",
    ]

    mode_descriptions = {
        "both_correct": "Both methods solved correctly",
        "loop_fixed": "AgenticLoop fixed ad-hoc error",
        "loop_broke": "AgenticLoop broke a correct ad-hoc answer",
        "extraction_failure_only": "Ad-hoc extraction failed; Loop succeeded",
        "loop_json_failure": "Loop JSON parse failed; ad-hoc extracted something",
        "both_extraction_failure": "Both failed to produce extractable answer",
        "both_wrong_reasoning": "Both produced answers, both were wrong",
    }

    for mode, count in sorted(breakdown["mode_counts"].items(), key=lambda x: -x[1]):
        desc = mode_descriptions.get(mode, mode)
        lines.append(f"| {mode} | {count} | {desc} |")

    lines.extend([
        "",
        f"- **Ad-hoc extraction failures**: {breakdown['ad_hoc_extraction_failures']} (predicted_answer=None)",
        f"- **Loop extraction failures**: {breakdown['loop_extraction_failures']} (predicted_answer=None, i.e., JSON parse failed)",
        "",
        "## Per-Problem Table",
        "",
        "| PID | Gold | Ad-hoc | AH Correct | Loop | Loop Correct | Error Mode |",
        "|-----|------|--------|------------|------|--------------|------------|",
    ])

    for r in rows:
        ah = r["ad_hoc_pred"] if r["ad_hoc_pred"] is not None else "FAIL"
        lp = r["loop_pred"] if r["loop_pred"] is not None else "FAIL"
        lines.append(
            f"| {r['problem_id']} | {r['gold']} | {ah} | {r['ad_hoc_correct']} | {lp} | {r['loop_correct']} | {r['error_mode']} |"
        )

    lines.append("")
    return "\n".join(lines)


def main():
    ad_hoc, loop = load_results()
    rows = build_table(ad_hoc, loop)
    mcnemar = mcnemar_test(rows)
    breakdown = error_breakdown(rows)

    # Write CSV
    import csv
    csv_path = RUNS_DIR / "V4_RQ01_T04_comparison_table.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    # Write statistical test report
    stat_path = RUNS_DIR / "V4_RQ01_T04_statistical_test.txt"
    with open(stat_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"mcnemar": mcnemar, "breakdown": breakdown}, indent=2, ensure_ascii=False))

    # Write full report
    report = generate_report(rows, mcnemar, breakdown)
    report_path = RUNS_DIR / "V4_RQ01_T04_error_mode_analysis.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Artifacts written:")
    print(f"  CSV: {csv_path}")
    print(f"  Stats: {stat_path}")
    print(f"  Report: {report_path}")
    print()
    print(f"Ad-hoc accuracy: {breakdown['ad_hoc_accuracy']*100:.1f}%")
    print(f"Loop accuracy: {breakdown['loop_accuracy']*100:.1f}%")
    print(f"McNemar p-value: {mcnemar['p_value']:.6f}")
    print(f"Significant: {'YES' if mcnemar['significant_at_0_05'] else 'NO'}")


if __name__ == "__main__":
    main()
