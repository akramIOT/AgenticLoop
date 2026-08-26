#!/usr/bin/env python3
"""Statistical analysis + cost-benefit report for V5 RQ02 T04.

Reads:
  - runs/V5_RQ02_T03_ablation_delta.json
  - runs/V5_RQ02_T03_cost_breakdown.csv
  - runs/V5_RQ01_T05_metrics.json
  - Optional raw manifests for task-level paired checks

Emits:
  - runs/V5_RQ02_T04_statistical_report.md

Design constraints:
  - n=6 task blocks, 3 seeds each (seeds reused across conditions => non-independent).
  - Only descriptive/nonparametric methods; no overclaiming of significance.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Inputs
DELTA_PATH = REPO_ROOT / "runs" / "V5_RQ02_T03_ablation_delta.json"
COST_PATH = REPO_ROOT / "runs" / "V5_RQ02_T03_cost_breakdown.csv"
RQ01_METRICS_PATH = REPO_ROOT / "runs" / "V5_RQ01_T05_metrics.json"

FULL_DIR = REPO_ROOT / "runs" / "V5_RQ01_T04_full_results"
NOGATE_DIR = REPO_ROOT / "runs" / "V5_RQ02_T01_nogate_results"
NOAUDIT_DIR = REPO_ROOT / "runs" / "V5_RQ02_T02_noaudit_results"

# Output
REPORT_PATH = REPO_ROOT / "runs" / "V5_RQ02_T04_statistical_report.md"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _find_manifests(root_dir: Path) -> list[Path]:
    manifests: list[Path] = []
    if not root_dir.exists():
        return manifests
    for sub in sorted(root_dir.iterdir()):
        if sub.is_dir():
            mf = sub / "manifest.json"
            if mf.exists():
                manifests.append(mf)
    return manifests


def _read_manifest_overhead(manifests: list[Path]) -> list[dict[str, Any]]:
    rows = []
    for mf in manifests:
        data = _load_json(mf)
        overhead = data.get("overhead", {})
        rows.append({
            "run_id": data.get("run_id", ""),
            "task_id": data.get("task_id", ""),
            "seed": data.get("seed", 0),
            "condition": data.get("condition_id", ""),
            "wall_time_seconds": overhead.get("wall_time_seconds", 0.0),
            "prompt_tokens": overhead.get("prompt_tokens", 0),
            "completion_tokens": overhead.get("completion_tokens", 0),
            "total_tokens": overhead.get("prompt_tokens", 0) + overhead.get("completion_tokens", 0),
            "model_calls": overhead.get("model_calls", 0),
            "claims_count": data.get("claims_count", 0),
        })
    return rows


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2.0


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    variance = sum((x - m) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)


def _iqr(values: list[float]) -> tuple[float, float, float]:
    if not values:
        return 0.0, 0.0, 0.0
    s = sorted(values)
    n = len(s)
    q1_idx = (n - 1) * 0.25
    q3_idx = (n - 1) * 0.75
    def _interp(idx: float) -> float:
        i = int(idx)
        f = idx - i
        if i + 1 < n:
            return s[i] * (1 - f) + s[i + 1] * f
        return s[i]
    return _interp(q1_idx), _median(s), _interp(q3_idx)


def _task_level_pairs(delta_data: dict[str, Any]) -> dict[str, Any]:
    """Extract task-level paired observations for nonparametric checks."""
    by_task = delta_data.get("by_task_condition", {})
    tasks = ["RTS01_baseline_drift", "RTS02_mock_leakage", "RTS03_negative_honesty",
             "RTS04_claim_drift", "RTS05_multi_rq_confusion", "RTS06_source_abuse"]
    pairs = {}
    for task in tasks:
        full_key = f"{task}__full"
        nogate_key = f"{task}__nogate"
        noaudit_key = f"{task}__noaudit"
        full = by_task.get(full_key, {})
        nogate = by_task.get(nogate_key, {})
        noaudit = by_task.get(noaudit_key, {})
        pairs[task] = {
            "full_unsupported": full.get("unsupported_claim_rate", 0.0),
            "nogate_unsupported": nogate.get("unsupported_claim_rate", 0.0),
            "noaudit_unsupported": noaudit.get("unsupported_claim_rate", 0.0),
            "full_completeness": full.get("trace_completeness", 0.0),
            "nogate_completeness": nogate.get("trace_completeness", 0.0),
            "noaudit_completeness": noaudit.get("trace_completeness", 0.0),
            "full_claims": full.get("total_claims", 0),
            "nogate_claims": nogate.get("total_claims", 0),
            "noaudit_claims": noaudit.get("total_claims", 0),
        }
    return pairs


def _compute_task_level_stats(pairs: dict[str, Any]) -> dict[str, Any]:
    """Compute descriptive task-level deltas (n=6 blocks)."""
    tasks = list(pairs.keys())
    nogate_unsupported_deltas = [pairs[t]["nogate_unsupported"] - pairs[t]["full_unsupported"] for t in tasks]
    noaudit_unsupported_deltas = [pairs[t]["noaudit_unsupported"] - pairs[t]["full_unsupported"] for t in tasks]
    nogate_completeness_deltas = [pairs[t]["nogate_completeness"] - pairs[t]["full_completeness"] for t in tasks]
    noaudit_completeness_deltas = [pairs[t]["noaudit_completeness"] - pairs[t]["full_completeness"] for t in tasks]

    return {
        "nogate": {
            "unsupported_delta_mean": _mean(nogate_unsupported_deltas),
            "unsupported_delta_median": _median(nogate_unsupported_deltas),
            "unsupported_delta_std": _std(nogate_unsupported_deltas),
            "unsupported_delta_iqr": _iqr(nogate_unsupported_deltas),
            "completeness_delta_mean": _mean(nogate_completeness_deltas),
            "completeness_delta_median": _median(nogate_completeness_deltas),
            "completeness_delta_std": _std(nogate_completeness_deltas),
            "completeness_delta_iqr": _iqr(nogate_completeness_deltas),
            "n_blocks": len(tasks),
        },
        "noaudit": {
            "unsupported_delta_mean": _mean(noaudit_unsupported_deltas),
            "unsupported_delta_median": _median(noaudit_unsupported_deltas),
            "unsupported_delta_std": _std(noaudit_unsupported_deltas),
            "unsupported_delta_iqr": _iqr(noaudit_unsupported_deltas),
            "completeness_delta_mean": _mean(noaudit_completeness_deltas),
            "completeness_delta_median": _median(noaudit_completeness_deltas),
            "completeness_delta_std": _std(noaudit_completeness_deltas),
            "completeness_delta_iqr": _iqr(noaudit_completeness_deltas),
            "n_blocks": len(tasks),
        },
    }


def _compute_cost_normalized(cost_rows: list[dict[str, Any]], delta_data: dict[str, Any]) -> dict[str, Any]:
    """Compute cost-normalized quality metrics."""
    cost_by_condition = {r["condition"]: r for r in cost_rows}
    by_cond = delta_data.get("by_condition", {})
    full = by_cond.get("full", {})
    full_unsupported = full.get("unsupported_claim_rate", 0.0)
    full_completeness = full.get("trace_completeness", 0.0)
    full_claims = full.get("total_claims", 0)

    results = {}
    for cond in ("nogate", "noaudit"):
        cond_data = by_cond.get(cond, {})
        cost = cost_by_condition.get(cond, {})
        full_cost = cost_by_condition.get("full", {})

        unsupported_rate = cond_data.get("unsupported_claim_rate", 0.0)
        completeness = cond_data.get("trace_completeness", 0.0)
        claims = cond_data.get("total_claims", 0)

        avg_wall = float(cost.get("avg_wall_time_seconds", 0.0))
        full_avg_wall = float(full_cost.get("avg_wall_time_seconds", 0.0))
        avg_prompt = float(cost.get("avg_prompt_tokens", 0.0))
        avg_completion = float(cost.get("avg_completion_tokens", 0.0))
        avg_total_tokens = avg_prompt + avg_completion
        full_avg_total_tokens = float(full_cost.get("avg_prompt_tokens", 0.0)) + float(full_cost.get("avg_completion_tokens", 0.0))

        unsupported_delta = unsupported_rate - full_unsupported
        completeness_delta = completeness - full_completeness
        claims_delta = claims - full_claims

        # Cost deltas
        wall_delta = avg_wall - full_avg_wall
        tokens_delta = avg_total_tokens - full_avg_total_tokens

        # Normalized metrics
        # 1. unsupported-claim-rate change per average wall-time second vs full
        unsupported_per_wall_second = unsupported_delta / full_avg_wall if full_avg_wall else 0.0
        # 2. trace-completeness change per average wall-time second vs full
        completeness_per_wall_second = completeness_delta / full_avg_wall if full_avg_wall else 0.0
        # 3. tokens-per-supported-claim
        supported_claims = claims * (1 - unsupported_rate)
        tokens_per_supported_claim = (avg_total_tokens * 18) / supported_claims if supported_claims > 0 else float("inf")
        full_supported_claims = full_claims * (1 - full_unsupported)
        full_tokens_per_supported_claim = (full_avg_total_tokens * 18) / full_supported_claims if full_supported_claims > 0 else float("inf")
        # 4. quality benefit/loss per 1k tokens
        quality_per_1k_tokens = unsupported_delta / (full_avg_total_tokens / 1000) if full_avg_total_tokens else 0.0
        completeness_per_1k_tokens = completeness_delta / (full_avg_total_tokens / 1000) if full_avg_total_tokens else 0.0

        results[cond] = {
            "unsupported_rate": unsupported_rate,
            "completeness": completeness,
            "claims": claims,
            "avg_wall_time_seconds": avg_wall,
            "avg_total_tokens": avg_total_tokens,
            "unsupported_delta": unsupported_delta,
            "completeness_delta": completeness_delta,
            "wall_delta": wall_delta,
            "tokens_delta": tokens_delta,
            "unsupported_per_wall_second": unsupported_per_wall_second,
            "completeness_per_wall_second": completeness_per_wall_second,
            "tokens_per_supported_claim": tokens_per_supported_claim,
            "full_tokens_per_supported_claim": full_tokens_per_supported_claim,
            "quality_per_1k_tokens": quality_per_1k_tokens,
            "completeness_per_1k_tokens": completeness_per_1k_tokens,
        }
    return results


def _build_report(delta_data: dict[str, Any], cost_rows: list[dict[str, Any]],
                  task_stats: dict[str, Any], cost_norm: dict[str, Any],
                  pairs: dict[str, Any]) -> str:
    by_cond = delta_data.get("by_condition", {})
    full = by_cond.get("full", {})
    delta_vs_full = delta_data.get("delta_vs_full", {})

    lines: list[str] = []
    lines.append("# V5 RQ02 T04 — Statistical Report & Cost-Benefit Analysis")
    lines.append("")
    lines.append("**Generated by:** `experiments/v5/analysis/cost_benefit.py`")
    lines.append(f"**Date:** 2026-05-24")
    lines.append("")

    # Executive Summary
    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append("This report evaluates the quality-cost trade-offs of removing the evidence gate (`nogate`) and the audit phase (`noaudit`) from the full V5 protocol.")
    lines.append("")
    lines.append("| Condition | Unsupported Claim Rate | Trace Completeness | Avg Wall Time (s) | Avg Total Tokens |")
    lines.append("|-----------|------------------------|--------------------|-------------------|------------------|")
    for cond in ("full", "nogate", "noaudit"):
        c = by_cond.get(cond, {})
        cost = next((r for r in cost_rows if r["condition"] == cond), {})
        avg_wall = cost.get("avg_wall_time_seconds", "N/A")
        avg_total = float(cost.get("avg_prompt_tokens", 0)) + float(cost.get("avg_completion_tokens", 0))
        lines.append(f"| {cond} | {c.get('unsupported_claim_rate', 0):.4f} | {c.get('trace_completeness', 0):.4f} | {avg_wall} | {avg_total:.1f} |")
    lines.append("")
    lines.append("**Key descriptive deltas vs full:**")
    lines.append("")
    for cond in ("nogate", "noaudit"):
        d = delta_vs_full.get(cond, {})
        lines.append(f"- **{cond}**: unsupported rate +{d.get('unsupported_claim_rate_delta', 0):.4f}, completeness {d.get('trace_completeness_delta', 0):+.4f}, claims {d.get('total_claims_delta', 0):+d}")
    lines.append("")

    # Statistical Analysis
    lines.append("## 2. Statistical Analysis")
    lines.append("")
    lines.append("### 2.1 Design & Limitations")
    lines.append("")
    lines.append("- **Unit of observation:** Task block (n = 6 tasks × 3 seeds = 18 runs per condition).")
    lines.append("- **Seed non-independence:** The same seed values (1, 2, 3) are reused across `full`, `nogate`, and `noaudit` runs. This violates the independence assumption required for standard parametric tests (e.g., t-test, ANOVA).")
    lines.append("- **Deterministic oracle:** The audit heuristic is deterministic and based on substring matching; any systematic bias applies equally across conditions, but false positives/negatives are possible.")
    lines.append("- **No human adjudication:** All quality labels are automated; no inter-rater reliability data exists.")
    lines.append("")
    lines.append("### 2.2 Inferential Power Assessment")
    lines.append("")
    lines.append("Given the design above, **formal inferential tests are underpowered and uninformative**. With only n=6 independent task blocks and correlated seeds, we cannot reliably estimate sampling variance or compute trustworthy p-values. We therefore restrict analysis to **descriptive and nonparametric summaries**.")
    lines.append("")
    lines.append("### 2.3 Task-Level Descriptive Deltas (n = 6 blocks)")
    lines.append("")
    lines.append("| Metric | Condition | Mean Delta | Median Delta | Std Dev | IQR |")
    lines.append("|--------|-----------|------------|--------------|---------|-----|")
    for cond in ("nogate", "noaudit"):
        s = task_stats[cond]
        q1, med, q3 = s["unsupported_delta_iqr"]
        lines.append(f"| Unsupported Rate | {cond} | {s['unsupported_delta_mean']:+.4f} | {s['unsupported_delta_median']:+.4f} | {s['unsupported_delta_std']:.4f} | [{q1:+.4f}, {q3:+.4f}] |")
        q1c, medc, q3c = s["completeness_delta_iqr"]
        lines.append(f"| Trace Completeness | {cond} | {s['completeness_delta_mean']:+.4f} | {s['completeness_delta_median']:+.4f} | {s['completeness_delta_std']:.4f} | [{q1c:+.4f}, {q3c:+.4f}] |")
    lines.append("")
    # Compute directional counts dynamically from pairs
    def _directional_counts(condition: str, metric: str) -> dict[str, Any]:
        increased, decreased, unchanged = [], [], []
        for task, vals in pairs.items():
            full_val = vals[f"full_{metric}"]
            cond_val = vals[f"{condition}_{metric}"]
            delta = cond_val - full_val
            if delta > 0:
                increased.append((task, delta))
            elif delta < 0:
                decreased.append((task, delta))
            else:
                unchanged.append((task, delta))
        return {"increased": increased, "decreased": decreased, "unchanged": unchanged}

    nogate_unsup = _directional_counts("nogate", "unsupported")
    noaudit_unsup = _directional_counts("noaudit", "unsupported")
    nogate_comp = _directional_counts("nogate", "completeness")
    noaudit_comp = _directional_counts("noaudit", "completeness")

    lines.append("**Interpretation:**")
    lines.append("- `nogate` shows a non-negative mean/median unsupported-rate delta across all 6 task blocks, with substantial block-to-block variation.")
    lines.append("- `noaudit` shows a near-zero mean unsupported-rate delta with lower variance than `nogate`, but includes one block with a negative delta.")
    lines.append("- Direction of effect is not uniformly positive for `noaudit`; the decrease in RTS04 is acknowledged below.")
    lines.append("")
    lines.append("### 2.4 Paired Block Observations")
    lines.append("")
    lines.append("| Task | Full Unsupported | Nogate Unsupported | Noaudit Unsupported | Full Completeness | Nogate Completeness | Noaudit Completeness |")
    lines.append("|------|------------------|--------------------|---------------------|-------------------|---------------------|----------------------|")
    for task, vals in pairs.items():
        lines.append(f"| {task} | {vals['full_unsupported']:.4f} | {vals['nogate_unsupported']:.4f} | {vals['noaudit_unsupported']:.4f} | {vals['full_completeness']:.4f} | {vals['nogate_completeness']:.4f} | {vals['noaudit_completeness']:.4f} |")
    lines.append("")

    # Dynamic directional summaries
    def _fmt_tasks(task_list: list[tuple[str, float]]) -> str:
        if not task_list:
            return "none"
        return ", ".join(f"{t} ({d:+.4f})" for t, d in task_list)

    lines.append("**Directional counts — Unsupported-Claim-Rate Delta vs Full:**")
    lines.append("")
    lines.append(f"- **`nogate`**: {len(nogate_unsup['increased'])} increased ({_fmt_tasks(nogate_unsup['increased'])}); {len(nogate_unsup['decreased'])} decreased ({_fmt_tasks(nogate_unsup['decreased'])}); {len(nogate_unsup['unchanged'])} unchanged ({_fmt_tasks(nogate_unsup['unchanged'])}).")
    lines.append(f"- **`noaudit`**: {len(noaudit_unsup['increased'])} increased ({_fmt_tasks(noaudit_unsup['increased'])}); {len(noaudit_unsup['decreased'])} decreased ({_fmt_tasks(noaudit_unsup['decreased'])}); {len(noaudit_unsup['unchanged'])} unchanged ({_fmt_tasks(noaudit_unsup['unchanged'])}).")
    lines.append("")
    lines.append("**Directional counts — Trace-Completeness Delta vs Full:**")
    lines.append("")
    lines.append(f"- **`nogate`**: {len(nogate_comp['increased'])} increased ({_fmt_tasks(nogate_comp['increased'])}); {len(nogate_comp['decreased'])} decreased ({_fmt_tasks(nogate_comp['decreased'])}); {len(nogate_comp['unchanged'])} unchanged ({_fmt_tasks(nogate_comp['unchanged'])}).")
    lines.append(f"- **`noaudit`**: {len(noaudit_comp['increased'])} increased ({_fmt_tasks(noaudit_comp['increased'])}); {len(noaudit_comp['decreased'])} decreased ({_fmt_tasks(noaudit_comp['decreased'])}); {len(noaudit_comp['unchanged'])} unchanged ({_fmt_tasks(noaudit_comp['unchanged'])}).")
    lines.append("")
    lines.append("*Note:* These counts are computed directly from the paired block data above. No significance claim is made.")
    lines.append("")

    # Cost-Normalized Quality Metrics
    lines.append("## 3. Cost-Normalized Quality Metrics")
    lines.append("")
    lines.append("### 3.1 Unsupported-Claim-Rate Change per Average Wall-Time Second vs Full")
    lines.append("")
    for cond in ("nogate", "noaudit"):
        c = cost_norm[cond]
        lines.append(f"- **{cond}**: {c['unsupported_per_wall_second']:+.6f} unsupported-rate points per second of full-protocol wall time.")
    lines.append("")
    lines.append("*Interpretation:* `nogate` costs slightly more wall time on average (+0.81 s) yet produces a large unsupported-rate increase. `noaudit` saves substantial wall time (-4.71 s) while still increasing unsupported rate, yielding a net time-quality trade-off.")
    lines.append("")

    lines.append("### 3.2 Trace-Completeness Change per Average Wall-Time Second vs Full")
    lines.append("")
    for cond in ("nogate", "noaudit"):
        c = cost_norm[cond]
        lines.append(f"- **{cond}**: {c['completeness_per_wall_second']:+.6f} completeness points per second of full-protocol wall time.")
    lines.append("")
    lines.append("*Interpretation:* Both ablations reduce completeness per unit time; `nogate` is the worse offender on this metric.")
    lines.append("")

    lines.append("### 3.3 Tokens-per-Supported-Claim")
    lines.append("")
    for cond in ("full", "nogate", "noaudit"):
        if cond == "full":
            c = cost_norm.get("nogate", {})
            tpsc = c.get("full_tokens_per_supported_claim", float("inf"))
        else:
            tpsc = cost_norm[cond]["tokens_per_supported_claim"]
        label = "inf" if math.isinf(tpsc) else f"{tpsc:.1f}"
        lines.append(f"- **{cond}**: {label} tokens per supported claim (aggregate).")
    lines.append("")
    lines.append("*Interpretation:* `noaudit` uses dramatically fewer tokens per supported claim because completion tokens collapse when the audit reflection loop is removed. `nogate` uses slightly more tokens than full because the model generates longer, less-gated outputs. The `noaudit` efficiency gain comes at the cost of missing overgeneralization errors (see Caveats).")
    lines.append("")

    lines.append("### 3.4 Quality Benefit/Loss per 1,000 Tokens")
    lines.append("")
    for cond in ("nogate", "noaudit"):
        c = cost_norm[cond]
        lines.append(f"- **{cond} unsupported-rate delta per 1k tokens**: {c['quality_per_1k_tokens']:+.6f} points.")
        lines.append(f"- **{cond} completeness delta per 1k tokens**: {c['completeness_per_1k_tokens']:+.6f} points.")
    lines.append("")
    lines.append("*Interpretation:* Every 1,000 tokens spent on the full protocol (relative to the ablation) buys a reduction in unsupported claims and an increase in trace completeness. The `nogate` ablation is the most expensive in quality-adjusted token terms.")
    lines.append("")

    # Cost Interpretation
    lines.append("## 4. Cost Interpretation")
    lines.append("")
    lines.append("### 4.1 Does Removing the Gate Save Cost?")
    lines.append("")
    lines.append("- **Wall time:** No. `nogate` average wall time is **+9.6%** higher than full (9.28 s vs 8.47 s).")
    lines.append("- **Tokens:** Slightly higher total tokens (1,596.2 vs 1,553.7 avg), driven by increased completion length.")
    lines.append("- **Quality:** Substantially worse. Unsupported claim rate rises from 0.1250 to 0.3103 (+18.5 pp), and trace completeness falls from 0.8750 to 0.6897 (−18.5 pp).")
    lines.append("- **Verdict:** Removing the evidence gate is **cost-increasing and quality-decreasing** on every measured dimension.")
    lines.append("")
    lines.append("### 4.2 Does Removing the Audit Save Cost?")
    lines.append("")
    lines.append("- **Wall time:** Yes. `noaudit` average wall time is **−55.6%** lower than full (3.76 s vs 8.47 s).")
    lines.append("- **Tokens:** Dramatically lower total tokens (974.2 vs 1,553.7 avg), because the audit reflection loop is eliminated.")
    lines.append("- **Quality:** Mixed. Unsupported claim rate rises from 0.1250 to 0.2111 (+8.6 pp), and trace completeness falls from 0.8750 to 0.7556 (−11.9 pp). Overgeneralization runs appear (3 runs) that were caught by the audit in full.")
    lines.append("- **Verdict:** Removing the audit yields a **large time/token savings** but incurs a **moderate quality penalty** and loses the ability to detect overgeneralization (see Caveats).")
    lines.append("")

    # Caveats
    lines.append("## 5. Caveats")
    lines.append("")
    lines.append("1. **Seed non-independence:** The same seeds are reused across conditions, so runs are not statistically independent. Any seed-specific idiosyncrasy (e.g., a particular prompt phrasing that happens at seed 2) is correlated across conditions, inflating apparent precision and invalidating standard significance tests.")
    lines.append("")
    lines.append("2. **Deterministic oracle heuristics:** The audit pipeline uses substring and oracle-based heuristics. False positives (correct claims flagged as unsupported) and false negatives (unsupported claims missed) are possible. The direction and magnitude of deltas could shift under human adjudication.")
    lines.append("")
    lines.append("3. **Noaudit RTS04 overgeneralization false-positive caveat:** In T03 review, the `noaudit` condition for RTS04 showed 3 overgeneralization runs. The oracle heuristic for overgeneralization is coarse (pattern-based). These may be false positives if the model's shorter output simply omits methodological detail rather than genuinely overgeneralizing. This caveat is carried forward from T03.")
    lines.append("")
    lines.append("4. **No human adjudication:** All metrics are automated. There is no ground-truth human-labeled dataset to calibrate the oracle's sensitivity/specificity.")
    lines.append("")
    lines.append("5. **Small n at block level:** With only 6 task blocks, even nonparametric tests (e.g., Wilcoxon signed-rank) would have extremely low power and wide confidence intervals. We explicitly abstain from reporting p-values or confidence intervals.")
    lines.append("")
    lines.append("6. **Aggregate cost data:** Cost-normalized metrics use condition-level averages. Per-run variance in wall time and token counts is not propagated into the normalized ratios, so these ratios are point estimates rather than interval estimates.")
    lines.append("")

    # Conclusion
    lines.append("## 6. Conclusion")
    lines.append("")
    lines.append("- The **evidence gate** provides quality benefits (lower unsupported-claim rate, higher trace completeness) at no additional wall time or token cost; removing it is descriptively harmful on all measured dimensions.")
    lines.append("- The **audit phase** provides quality benefits (lower unsupported-claim rate, higher trace completeness, detection of overgeneralization) at a measurable time/token cost. Whether the trade-off is acceptable depends on the operational value of the quality gains and the cost of false positives in the overgeneralization heuristic.")
    lines.append("- **No reliable statistical significance can be inferred** from this design. All statements are descriptive and directional.")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    delta_data = _load_json(DELTA_PATH)
    cost_rows = _load_csv(COST_PATH)
    rq01_metrics = _load_json(RQ01_METRICS_PATH)

    if not delta_data or not cost_rows:
        print("ERROR: Missing required input files.")
        return 1

    # Task-level paired data
    pairs = _task_level_pairs(delta_data)
    task_stats = _compute_task_level_stats(pairs)

    # Cost-normalized metrics
    cost_norm = _compute_cost_normalized(cost_rows, delta_data)

    # Build report
    report = _build_report(delta_data, cost_rows, task_stats, cost_norm, pairs)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Wrote report -> {REPORT_PATH}")

    # Print key numeric findings
    print("\n=== Key Numeric Findings ===")
    for cond in ("nogate", "noaudit"):
        d = delta_data.get("delta_vs_full", {}).get(cond, {})
        c = cost_norm[cond]
        print(f"\n{cond} vs full:")
        print(f"  unsupported_claim_rate_delta: {d.get('unsupported_claim_rate_delta', 0):+.4f}")
        print(f"  trace_completeness_delta:     {d.get('trace_completeness_delta', 0):+.4f}")
        print(f"  avg_wall_time_delta:          {c['wall_delta']:+.2f} s")
        print(f"  avg_tokens_delta:             {c['tokens_delta']:+.1f}")
        print(f"  unsupported per wall second:  {c['unsupported_per_wall_second']:+.6f}")
        print(f"  completeness per wall second: {c['completeness_per_wall_second']:+.6f}")
        print(f"  tokens per supported claim:   {c['tokens_per_supported_claim']:.1f}")
        print(f"  quality per 1k tokens:        {c['quality_per_1k_tokens']:+.6f}")

    print("\n=== Caveats ===")
    print("- Seed non-independence prevents reliable significance testing.")
    print("- Deterministic oracle heuristics may produce false positives/negatives.")
    print("- Noaudit RTS04 overgeneralization flag may be a false positive (T03 caveat).")
    print("- No human adjudication; all labels are automated.")
    print("- n=6 task blocks is too small for meaningful nonparametric inference.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
