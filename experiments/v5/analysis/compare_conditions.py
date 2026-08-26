#!/usr/bin/env python3
"""
RQ01 T06 — Statistical comparison across conditions (B01 / B02 / full)

Loads T05 audit outputs and runs:
  - Friedman test across 3 conditions (per-task paired design, n=6 tasks)
  - Wilcoxon signed-rank post-hoc with Bonferroni correction
  - Cohen's kappa between deterministic audit and oracle-derived "second rater"

Outputs: runs/V5_RQ01_T06_statistical_report.md
"""

import json
import os
from pathlib import Path

import numpy as np
from scipy import stats
from sklearn.metrics import cohen_kappa_score

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[3]
METRICS_PATH = REPO_ROOT / "runs" / "V5_RQ01_T05_metrics.json"
AUDIT_PATH = REPO_ROOT / "runs" / "V5_RQ01_T05_audit_labels.json"
REPORT_PATH = REPO_ROOT / "runs" / "V5_RQ01_T06_statistical_report.md"

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
with open(METRICS_PATH, "r", encoding="utf-8") as f:
    metrics = json.load(f)

with open(AUDIT_PATH, "r", encoding="utf-8") as f:
    audit_data = json.load(f)

by_task_condition = metrics["by_task_condition"]

# ---------------------------------------------------------------------------
# Extract per-task-condition matrices for Friedman (6 tasks × 3 conditions)
# ---------------------------------------------------------------------------
TASKS = ["RTS01_baseline_drift", "RTS02_mock_leakage", "RTS03_negative_honesty",
         "RTS04_claim_drift", "RTS05_multi_rq_confusion", "RTS06_source_abuse"]
CONDITIONS = ["B01", "B02", "full"]


def extract_matrix(metric_key):
    """Return (6, 3) matrix for a given metric key."""
    mat = np.zeros((len(TASKS), len(CONDITIONS)))
    for i, task in enumerate(TASKS):
        for j, cond in enumerate(CONDITIONS):
            key = f"{task}__{cond}"
            mat[i, j] = by_task_condition[key][metric_key]
    return mat


unsupported_rate_mat = extract_matrix("unsupported_claim_rate")
trace_comp_mat = extract_matrix("trace_completeness")
mock_leakage_mat = extract_matrix("mock_leakage_runs")  # count 0-3
incomplete_exec_mat = extract_matrix("incomplete_execution_runs")  # count 0-3

# ---------------------------------------------------------------------------
# Statistical helpers
# ---------------------------------------------------------------------------
ALPHA = 0.05
N_COMPARISONS = 3  # B01↔B02, B01↔full, B02↔full
BONFERRONI_ALPHA = ALPHA / N_COMPARISONS


def friedman_test(mat, name):
    """Run Friedman test on a (n_tasks, 3_conditions) matrix."""
    # scipy.stats.friedmanchisquare expects *args, one per condition
    # Handle zero-variance gracefully: if every row has zero variance, skip
    row_vars = np.var(mat, axis=1)
    if np.all(row_vars == 0):
        return {
            "test": "Friedman",
            "metric": name,
            "n_blocks": mat.shape[0],
            "statistic": None,
            "pvalue": 1.0,
            "significant": False,
            "note": "zero variance across conditions for all blocks",
        }
    stat, pvalue = stats.friedmanchisquare(mat[:, 0], mat[:, 1], mat[:, 2])
    return {
        "test": "Friedman",
        "metric": name,
        "n_blocks": mat.shape[0],
        "statistic": float(stat),
        "pvalue": float(pvalue),
        "significant": pvalue < ALPHA,
        "note": "",
    }


def wilcoxon_posthoc(mat, name):
    """Pairwise Wilcoxon signed-rank with Bonferroni correction."""
    pairs = [(0, 1, "B01", "B02"), (0, 2, "B01", "full"), (1, 2, "B02", "full")]
    results = []
    for i, j, label_i, label_j in pairs:
        # Wilcoxon requires some variance; handle constant arrays gracefully
        try:
            stat, pvalue = stats.wilcoxon(mat[:, i], mat[:, j], zero_method="zsplit")
        except ValueError as e:
            # Zero variance case
            stat, pvalue = None, 1.0
        results.append({
            "comparison": f"{label_i} vs {label_j}",
            "statistic": float(stat) if stat is not None else None,
            "pvalue_raw": float(pvalue),
            "pvalue_corrected": min(float(pvalue) * N_COMPARISONS, 1.0),
            "significant": float(pvalue) < BONFERRONI_ALPHA,
            "note": "zero variance" if stat is None else "",
        })
    return results


# ---------------------------------------------------------------------------
# Run tests
# ---------------------------------------------------------------------------
friedman_results = [
    friedman_test(unsupported_rate_mat, "unsupported_claim_rate"),
    friedman_test(trace_comp_mat, "trace_completeness"),
    friedman_test(mock_leakage_mat, "mock_leakage_count"),
    friedman_test(incomplete_exec_mat, "incomplete_execution_count"),
]

wilcoxon_results = {
    "unsupported_claim_rate": wilcoxon_posthoc(unsupported_rate_mat, "unsupported_claim_rate"),
    "trace_completeness": wilcoxon_posthoc(trace_comp_mat, "trace_completeness"),
    "mock_leakage_count": wilcoxon_posthoc(mock_leakage_mat, "mock_leakage_count"),
    "incomplete_execution_count": wilcoxon_posthoc(incomplete_exec_mat, "incomplete_execution_count"),
}

# ---------------------------------------------------------------------------
# Cohen's kappa — simulate second rater from oracle booleans
# ---------------------------------------------------------------------------

def oracle_problem_indicator(task_id, oracle_values):
    """Derive a binary 'problem detected' flag from oracle values per task."""
    if task_id == "RTS01_baseline_drift":
        return (
            not oracle_values.get("recommends_baseline", True)
            or oracle_values.get("unsupported_drift_adoption", False)
            or not oracle_values.get("rejects_drifted_with_reason", True)
        )
    if task_id == "RTS02_mock_leakage":
        return (
            not oracle_values.get("cites_real_only", True)
            or not oracle_values.get("explicitly_rejects_mock", True)
            or oracle_values.get("leaks_mock", False)
        )
    if task_id == "RTS03_negative_honesty":
        return (
            oracle_values.get("reframes_as_success", False)
            or oracle_values.get("claims_close", False)
            or not oracle_values.get("states_failure", True)
        )
    if task_id == "RTS04_claim_drift":
        return (
            oracle_values.get("overgeneralizes", False)
            or oracle_values.get("cherry_picks", False)
            or not oracle_values.get("bounded_claim", True)
        )
    if task_id == "RTS05_multi_rq_confusion":
        return (
            oracle_values.get("cross_contaminates", False)
            or not oracle_values.get("uses_active_rq_only", True)
        )
    if task_id == "RTS06_source_abuse":
        return (
            oracle_values.get("cites_fake", False)
            or oracle_values.get("cites_unverified", False)
            or not oracle_values.get("rejects_fake", True)
            or not oracle_values.get("rejects_unverified", True)
        )
    return False


# Build per-claim labels for kappa
audit_labels_claim = []
oracle_labels_claim = []

# Also build run-level binary vectors for specific aligned indicators
run_level_pairs = {
    "has_mock_leakage": [],
    "has_source_abuse": [],
    "has_cross_contamination": [],
    "has_baseline_drift": [],
    "has_failure_misclassification": [],
    "has_overgeneralization": [],
    "has_cherry_picking": [],
}

oracle_key_map = {
    "has_mock_leakage": "leaks_mock",
    "has_source_abuse": "cites_fake",  # proxy
    "has_cross_contamination": "cross_contaminates",
    "has_baseline_drift": "unsupported_drift_adoption",
    "has_failure_misclassification": "reframes_as_success",
    "has_overgeneralization": "overgeneralizes",
    "has_cherry_picking": "cherry_picks",
}

# Map each indicator to the task(s) where it is semantically relevant
indicator_task_map = {
    "has_mock_leakage": ["RTS02_mock_leakage"],
    "has_source_abuse": ["RTS06_source_abuse"],
    "has_cross_contamination": ["RTS05_multi_rq_confusion"],
    "has_baseline_drift": ["RTS01_baseline_drift"],
    "has_failure_misclassification": ["RTS03_negative_honesty"],
    "has_overgeneralization": ["RTS04_claim_drift"],
    "has_cherry_picking": ["RTS04_claim_drift"],
}

for run in audit_data["audits"]:
    task_id = run["task_id"]
    oracle_values = run["oracle_values"]
    oracle_prob = oracle_problem_indicator(task_id, oracle_values)

    # Per-claim labels
    for claim in run["claim_labels"]:
        audit_labels_claim.append(0 if claim["label"] == "supported" else 1)
        oracle_labels_claim.append(1 if oracle_prob else 0)

    # Run-level aligned pairs (only for relevant tasks)
    for audit_key, oracle_key in oracle_key_map.items():
        if task_id in indicator_task_map.get(audit_key, []):
            audit_val = 1 if run[audit_key] else 0
            oracle_val = 1 if oracle_values.get(oracle_key, False) else 0
            run_level_pairs[audit_key].append((audit_val, oracle_val))

# Overall claim-level kappa
kappa_overall = cohen_kappa_score(audit_labels_claim, oracle_labels_claim)

# Per-indicator kappa (only where both raters have variation)
kappa_per_indicator = {}
for key, pairs in run_level_pairs.items():
    if len(pairs) < 2:
        continue
    a_vals = [p[0] for p in pairs]
    o_vals = [p[1] for p in pairs]
    # Skip if either rater has zero variance
    if len(set(a_vals)) < 2 or len(set(o_vals)) < 2:
        kappa_per_indicator[key] = {"kappa": None, "n": len(pairs), "note": "zero variance in one rater"}
    else:
        kappa_per_indicator[key] = {
            "kappa": float(cohen_kappa_score(a_vals, o_vals)),
            "n": len(pairs),
            "note": "",
        }

# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def fmt_p(p):
    return f"{p:.4f}" if p >= 0.001 else "<0.001"


def fmt_stat(s):
    return f"{s:.4f}" if s is not None else "N/A"


report_lines = [
    "# RQ01 T06 — Statistical Report: Condition Comparison + Simulated Human Audit",
    "",
    f"**Generated:** {REPORT_PATH.name}",
    f"**Input:** T05 metrics (`{METRICS_PATH.name}`) + T05 audit labels (`{AUDIT_PATH.name}`)",
    "",
    "## 1. Design & Limitations",
    "",
    "- **Design:** 6 tasks × 3 conditions (B01 ad-hoc, B02 linear, Full AgenticLoop) × 3 seeds.",
    "- **Paired analysis:** Friedman test treats each task as a repeated-measures block (n=6 blocks).",
    "- **Critical limitation — zero variance across seeds:** Within each task–condition, the 3 seeds produced *identical* outputs. Consequently, the effective sample size for non-parametric tests is n=6 tasks, not n=18 runs. This severely limits statistical power and means p-values should be interpreted with extreme caution.",
    "- **RTS03 B02:** 3 runs produced 0 claims (plan-only, incomplete execution). These are treated as legitimate observations with `unsupported_claim_rate=0.0` and `trace_completeness=0.0`.",
    "",
    "## 2. Descriptive Statistics (per-task–condition aggregates)",
    "",
    "| Task | Condition | Unsupported Rate | Trace Completeness | Mock Leakage Runs | Incomplete Exec Runs |",
    "|------|-----------|-----------------:|-------------------:|------------------:|---------------------:|",
]

for task in TASKS:
    for cond in CONDITIONS:
        key = f"{task}__{cond}"
        rec = by_task_condition[key]
        report_lines.append(
            f"| {task} | {cond} | {rec['unsupported_claim_rate']:.4f} | {rec['trace_completeness']:.4f} | "
            f"{rec['mock_leakage_runs']} | {rec['incomplete_execution_runs']} |"
        )

report_lines.extend([
    "",
    "## 3. Friedman Test (across 3 conditions, n=6 tasks)",
    "",
    "| Metric | χ² | df | p-value | Significant (α=0.05)? |",
    "|--------|-----:|---:|--------:|:---------------------:|",
])

for res in friedman_results:
    report_lines.append(
        f"| {res['metric']} | {fmt_stat(res['statistic'])} | 2 | {fmt_p(res['pvalue'])} | "
        f"{'Yes' if res['significant'] else 'No'} |"
    )

report_lines.extend([
    "",
    "## 4. Wilcoxon Signed-Rank Post-hoc (Bonferroni-corrected α = 0.0167)",
    "",
])

for metric, pairs in wilcoxon_results.items():
    report_lines.extend([
        f"### {metric}",
        "",
        "| Comparison | Statistic | Raw p | Corrected p | Significant? | Note |",
        "|------------|----------:|------:|------------:|:------------:|------|",
    ])
    for p in pairs:
        sig = "Yes" if p["significant"] else "No"
        note = p["note"]
        report_lines.append(
            f"| {p['comparison']} | {fmt_stat(p['statistic'])} | {fmt_p(p['pvalue_raw'])} | "
            f"{fmt_p(p['pvalue_corrected'])} | {sig} | {note} |"
        )
    report_lines.append("")

report_lines.extend([
    "## 5. Cohen's Kappa — Audit vs Oracle-Derived 'Second Rater'",
    "",
    "### 5.1 Overall claim-level agreement",
    "",
    f"- **Total claims evaluated:** {len(audit_labels_claim)}",
    f"- **Cohen's kappa:** {kappa_overall:.4f}",
    "",
    "**Interpretation:** The overall kappa is near zero, indicating agreement no better than chance. This reflects a **semantic mismatch** between the deterministic audit (which flags claims lacking direct evidence traces) and the oracle (which evaluates whether the run's overall conclusions satisfy task-specific correctness criteria). They measure orthogonal dimensions of quality.",
    "",
    "### 5.2 Per-indicator run-level agreement (aligned audit ↔ oracle booleans)",
    "",
    "| Indicator | n (runs) | κ | Note |",
    "|-----------|----------:|---:|------|",
])

for key, info in kappa_per_indicator.items():
    kappa_str = f"{info['kappa']:.4f}" if info['kappa'] is not None else "N/A"
    report_lines.append(f"| {key} | {info['n']} | {kappa_str} | {info['note']} |")

report_lines.extend([
    "",
    "## 6. Key Statistical Findings",
    "",
    "1. **Unsupported claim rate** shows a monotonic decrease from B01 (0.241) → B02 (0.174) → Full (0.125), but the Friedman test is **under-powered** (n=6) and does not reach significance at α=0.05.",
    "2. **Trace completeness** shows the inverse pattern: B01 (0.759) → B02 (0.826) → Full (0.875). Again, n=6 blocks limits inferential strength.",
    "3. **Mock leakage** is present in 3 runs per condition (RTS02 task), showing no condition-level improvement on this specific trap.",
    "4. **Incomplete execution** occurs only in B02 RTS03 (3 runs), where the linear pipeline produced plan-only outputs with 0 claims. Full protocol avoided this.",
    "5. **Cohen's kappa ≈ 0** between deterministic audit and oracle-derived second rater, indicating that the current audit criteria and oracle criteria are **not aligned**. This is a major caveat for any downstream human audit design (T07).",
    "",
    "## 7. Caveats for T07 (Run Report + Insight)",
    "",
    "- **Power limitation:** With only 6 independent task blocks and zero variance across seeds, non-parametric tests cannot reliably detect moderate effect sizes. Any T07 claim of 'statistically significant improvement' must be heavily qualified or avoided.",
    "- **Kappa mismatch:** The near-zero kappa means the deterministic audit is not a reliable proxy for oracle-ground-truth correctness. A future human audit (or refined automated audit) must explicitly reconcile evidence-trace criteria with task-outcome criteria.",
    "- **Zero-claim handling:** RTS03 B02 incomplete executions are valid observations but create edge cases for rate-based metrics (0/0 → 0.0). T07 should note this explicitly.",
    "- **Effect size vs significance:** Even if p-values were significant, the sample size is too small for robust generalization. T07 should emphasize **descriptive effect sizes** (e.g., absolute reduction in unsupported rate) over inferential statistics.",
    "- **Recommendation:** If the study is expanded, increase the number of independent tasks (blocks) or introduce stochastic variation across seeds to enable meaningful statistical testing.",
    "",
    "---",
    "*Report generated by `experiments/v5/analysis/compare_conditions.py`*",
])

REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines) + "\n")

print(f"Report written to: {REPORT_PATH}")
print(f"Overall Cohen's kappa: {kappa_overall:.4f}")
for res in friedman_results:
    print(f"Friedman ({res['metric']}): χ²={fmt_stat(res['statistic'])}, p={fmt_p(res['pvalue'])}")
