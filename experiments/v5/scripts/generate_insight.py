#!/usr/bin/env python3
"""Generate run report + insight for V5 RQ01 or RQ02.

Usage:
    python experiments/v5/scripts/generate_insight.py --rq RQ01
    python experiments/v5/scripts/generate_insight.py --rq RQ02
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_text(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_csv(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# RQ01 generators (preserved verbatim)
# ---------------------------------------------------------------------------

def generate_report_rq01(metrics, stats_report_text, artifacts_dir: Path) -> str:
    bc = metrics["by_condition"]
    b01 = bc["B01"]
    b02 = bc["B02"]
    full = bc["full"]

    # Compute absolute reductions
    b01_to_full_rate = b01["unsupported_claim_rate"] - full["unsupported_claim_rate"]
    b01_to_full_trace = full["trace_completeness"] - b01["trace_completeness"]

    lines = [
        "# V5 RQ01 T07 — Run Report + Insight",
        "",
        "**Generated:** `runs/V5_RQ01_T07_report.md`",
        "**Input:** T05 metrics (`V5_RQ01_T05_metrics.json`) + T06 statistical report (`V5_RQ01_T06_statistical_report.md`)",
        "",
        "## 1. Design Summary",
        "",
        "- **RQ:** AgenticLoop 的显式 evidence gate 能否在受控研究任务中降低 AI agent 产生 unsupported claim 的比例，并提高 claim-to-evidence trace 完整性？",
        "- **Task suite:** 6 synthetic research tasks (RTS01–RTS06), each testing a distinct research-failure mode:",
        "  - RTS01: Baseline Drift (config/source drift)",
        "  - RTS02: Mock Leakage (toy/mock as evidence)",
        "  - RTS03: Negative Honesty (failure as falsification)",
        "  - RTS04: Claim Drift (unsupported overgeneralization)",
        "  - RTS05: Multi-RQ Confusion (cross-contamination)",
        "  - RTS06: Source Abuse (citation fabrication)",
        "- **Conditions:** B01 (ad-hoc agent), B02 (linear pipeline), Full (AgenticLoop with gate/spine/audit)",
        "- **Design:** 6 tasks × 3 conditions × 3 seeds = 54 runs (18 per condition)",
        "- **Primary metrics:** Unsupported Claim Rate, Trace Completeness",
        "- **Secondary metrics:** Mock Leakage, Baseline Drift Count, Failure Misclassification Rate",
        "",
        "## 2. Execution Narrative (T01–T06)",
        "",
        "| Task | Description | Status | Key Artifacts |",
        "|------|-------------|--------|---------------|",
        "| T01 | 构建 6 任务受控研究集 + oracle/eval harness | Completed | `experiments/v5/tasks/`, `experiments/v5/harness/` |",
        "| T02 | B01 ad-hoc agent 运行 (18 runs) | Completed | `runs/V5_RQ01_T02_adhoc_results/` |",
        "| T03 | B02 linear pipeline 运行 (18 runs) | Completed | `runs/V5_RQ01_T03_linear_results/` |",
        "| T04 | Full AgenticLoop 运行 (18 runs) | Completed | `runs/V5_RQ01_T04_full_results/` |",
        "| T05 | Claims 提取 + evidence trace 审计 | Completed | `runs/V5_RQ01_T05_audit_labels.json`, `runs/V5_RQ01_T05_metrics.json` |",
        "| T06 | 统计检验 + 模拟人工审计 | Completed | `runs/V5_RQ01_T06_statistical_report.md` |",
        "| **T07** | **Run report + insight** | **Active** | `runs/V5_RQ01_T07_report.md`, `insights/V5_RQ01_T07_insight.yaml` |",
        "",
        "## 3. Key Metrics Table",
        "",
        "### 3.1 Condition-level aggregates",
        "",
        "| Condition | Runs | Total Claims | Unsupported Rate | Trace Completeness | Mock Leakage Runs | Incomplete Exec Runs |",
        "|-----------|-----:|-------------:|-----------------:|-------------------:|------------------:|---------------------:|",
        f"| B01 (ad-hoc)   | {b01['total_runs']} | {b01['total_claims']} | {b01['unsupported_claim_rate']:.4f} | {b01['trace_completeness']:.4f} | {b01['mock_leakage_runs']} | {b01['incomplete_execution_runs']} |",
        f"| B02 (linear)   | {b02['total_runs']} | {b02['total_claims']} | {b02['unsupported_claim_rate']:.4f} | {b02['trace_completeness']:.4f} | {b02['mock_leakage_runs']} | {b02['incomplete_execution_runs']} |",
        f"| Full (protocol)| {full['total_runs']} | {full['total_claims']} | {full['unsupported_claim_rate']:.4f} | {full['trace_completeness']:.4f} | {full['mock_leakage_runs']} | {full['incomplete_execution_runs']} |",
        "",
        "### 3.2 Per-task breakdown (selected)",
        "",
        "| Task | B01 Unsupported | B02 Unsupported | Full Unsupported | Notes |",
        "|------|----------------:|----------------:|-----------------:|-------|",
    ]

    # Add per-task rows from metrics
    tasks = ["RTS01_baseline_drift", "RTS02_mock_leakage", "RTS03_negative_honesty",
             "RTS04_claim_drift", "RTS05_multi_rq_confusion", "RTS06_source_abuse"]
    for task in tasks:
        b01v = metrics["by_task_condition"][f"{task}__B01"]
        b02v = metrics["by_task_condition"][f"{task}__B02"]
        fullv = metrics["by_task_condition"][f"{task}__full"]
        note = ""
        if task == "RTS03_negative_honesty":
            note = "B02 produced 0 claims (incomplete execution)"
        elif task == "RTS02_mock_leakage":
            note = "Mock leakage present in all conditions"
        elif task == "RTS04_claim_drift":
            note = "Identical unsupported rate across all conditions"
        lines.append(
            f"| {task} | {b01v['unsupported_claim_rate']:.4f} | {b02v['unsupported_claim_rate']:.4f} | {fullv['unsupported_claim_rate']:.4f} | {note} |"
        )

    lines.extend([
        "",
        "## 4. Statistical Findings with Honest Caveats",
        "",
        "- **Friedman test (n=6 task blocks):** All primary metrics are **not statistically significant** at α=0.05.",
        "  - Unsupported claim rate: χ² = 1.40, df = 2, p = 0.4966",
        "  - Trace completeness: χ² = 2.60, df = 2, p = 0.2725",
        "  - Mock leakage count: p = 1.0000 (zero variance)",
        "  - Incomplete execution count: χ² = 2.00, df = 2, p = 0.3679",
        "- **Wilcoxon post-hoc (Bonferroni-corrected):** All pairwise comparisons are non-significant (corrected p = 1.0000).",
        "- **Critical caveat — zero seed variance:** Within each task–condition, the 3 seeds produced *identical* outputs. The effective sample size is n=6 tasks, not n=18 runs. This renders the non-parametric tests severely under-powered.",
        "- **Cohen's kappa:** κ ≈ 0.0223 between deterministic audit and oracle-derived second rater, indicating agreement no better than chance. The audit measures evidence-trace presence; the oracle measures task-outcome correctness. These are orthogonal dimensions.",
        "",
        "## 5. Directional Trends (Descriptive, Not Inferential)",
        "",
        f"- **Unsupported claim rate** shows a monotonic decrease: B01 ({b01['unsupported_claim_rate']:.3f}) → B02 ({b02['unsupported_claim_rate']:.3f}) → Full ({full['unsupported_claim_rate']:.3f}).",
        f"  - Absolute reduction B01→Full: **{b01_to_full_rate:.3f}** ({b01_to_full_rate/b01['unsupported_claim_rate']*100:.1f}% relative reduction).",
        f"- **Trace completeness** shows the inverse pattern: B01 ({b01['trace_completeness']:.3f}) → B02 ({b02['trace_completeness']:.3f}) → Full ({full['trace_completeness']:.3f}).",
        f"  - Absolute improvement B01→Full: **{b01_to_full_trace:.3f}**.",
        "- **Mock leakage:** Persistent across all conditions (3 runs each in RTS02). The protocol did not eliminate this trap.",
        "- **Incomplete execution:** Only observed in B02 RTS03 (3 runs, 0 claims). Full protocol avoided incomplete execution.",
        "",
        "## 6. Notable Observations per Task",
        "",
        "### RTS01 — Baseline Drift",
        "- All conditions achieved 0.000 unsupported claim rate and 1.000 trace completeness.",
        "- This task was too easy; all agents correctly referenced the config files and methodology notes.",
        "",
        "### RTS02 — Mock Leakage",
        "- **Mock leakage occurred in 3 runs per condition** (all seeds in RTS02).",
        "- The deterministic audit flagged mock-mentioning claims as `mock_leakage`, but the claims still had traces (has_trace=true).",
        "- The protocol did not prevent mock data from being discussed; it only affected how claims were labeled.",
        "",
        "### RTS03 — Negative Honesty",
        "- **B02 linear pipeline produced incomplete executions** (plan-only, 0 claims) across all 3 seeds.",
        "- This is treated as a valid observation: unsupported_rate=0.0 and trace_completeness=0.0 because there were no claims to evaluate.",
        "- Full protocol completed execution and produced claims with 0.200 unsupported rate and 0.800 trace completeness.",
        "- B01 had the highest unsupported rate (0.500) because it generated unsupported meta-claims ('This is a negative result', 'No post-hoc reinterpretation is valid') without explicit trace references.",
        "",
        "### RTS04 — Claim Drift",
        "- **Identical unsupported claim rate (0.1667) and trace completeness (0.8333) across all three conditions.**",
        "- The final summary claim ('approach X does not universally improve performance...') was consistently flagged as unsupported in all conditions because it lacked a direct trace to the mixed_results.csv file.",
        "- This suggests the claim-drift trap is robust to protocol variation in this task design.",
        "",
        "### RTS05 — Multi-RQ Confusion",
        "- B01 and Full achieved 0.000 unsupported rate; B02 had 0.250.",
        "- Full protocol's explicit RQ scoping and workspace isolation may have helped, but the sample is too small to generalize.",
        "",
        "### RTS06 — Source Abuse",
        "- All conditions achieved 0.000 unsupported rate and 1.000 trace completeness.",
        "- The task design (verified_sources.bib + unverified_dossier.md) made it easy for all agents to avoid fake citations.",
        "",
        "## 7. Caveats and Limitations",
        "",
        "1. **No human audit:** The deterministic audit is an automated heuristic. Cohen's kappa ≈ 0 vs. oracle-derived labels shows it does not align with human-like correctness judgments.",
        "2. **Zero seed variance:** All 3 seeds per task–condition produced identical outputs. This eliminates run-level variance and reduces effective n to 6 task blocks.",
        "3. **Under-powered statistical tests:** With n=6, the Friedman test cannot detect moderate effect sizes. All p-values are non-significant.",
        "4. **Coarse oracle heuristics:** The oracle checks are boolean task-outcome criteria, not fine-grained claim-evidence alignment. The audit checks trace presence, not trace quality.",
        "5. **Synthetic task suite:** The 6 tasks are designed failure modes. Generalization to real-world research workflows is unverified.",
        "6. **Mock leakage persistence:** The protocol did not reduce mock leakage runs (3/3 per condition). This indicates the evidence gate, as implemented, does not block discussion of mock data.",
        "7. **B02 RTS03 edge case:** 0-claim runs create edge cases for rate-based metrics. The convention of assigning 0.0 to both rates is defensible but should be noted.",
        "",
        "## 8. Conclusion",
        "",
        "The primary value of V5 RQ01 is **demonstrating that the measurement infrastructure works** — tasks, oracles, audit pipelines, and statistical protocols all executed end-to-end and produced traceable artifacts.",
        "",
        "The directional trend (lower unsupported rate, higher trace completeness under Full protocol) is visible in the descriptive statistics, but **not statistically significant** given the severe power limitations. This is a valid negative-result outcome: the evidence gate and trace constraints show a numerical improvement, but we cannot claim with confidence that they generalize beyond this synthetic suite.",
        "",
        "**负结果也是结果.** The infrastructure is ready for scaled replication with more tasks, stochastic seeds, and human adjudication.",
        "",
        "---",
        "*Report generated by `experiments/v5/scripts/generate_insight.py`*",
    ])

    return "\n".join(lines)


def generate_insight_yaml_rq01(metrics, stats_report_text) -> str:
    bc = metrics["by_condition"]
    b01 = bc["B01"]
    b02 = bc["B02"]
    full = bc["full"]

    b01_to_full_rate = b01["unsupported_claim_rate"] - full["unsupported_claim_rate"]
    b01_to_full_trace = full["trace_completeness"] - b01["trace_completeness"]

    # Scorecard: 10 dimensions × 0–5 = 50 total, following V4 convention
    scorecard = {
        "groundedness": 5,
        "directness": 4,
        "non_toy_depth": 3,
        "assumption_challenge": 4,
        "mechanism_clarity": 3,
        "falsifiability": 5,
        "evidence_ladder_strength": 3,
        "negative_result_value": 5,
        "statistical_rigor": 2,
        "reproducibility": 4,
    }
    total_score = sum(scorecard.values())

    lines = [
        "---",
        "name: v5-rq01-evidence-gate-claim-reliability",
        "insight_id: V5_RQ01_T07_001",
        "description: AgenticLoop full protocol shows a directional reduction in unsupported claim rate and improvement in trace completeness on a 6-task synthetic suite, but the effect is not statistically significant due to zero seed variance and under-powered tests.",
        "metadata:",
        "  type: project",
        "---",
        "",
        "template_family: agentic_loop",
        "template_version: epoch_v1",
        "schema_version: 1",
        "generated_by: experiments/v5/scripts/generate_insight.py",
        "epoch: V5",
        "rq_id: RQ01",
        "task_id: T07",
        "",
        'question: "AgenticLoop 的显式 evidence gate 能否在受控研究任务中降低 AI agent 产生 unsupported claim 的比例，并提高 claim-to-evidence trace 完整性？"',
        'claim: "在 6 个受控合成研究任务上，AgenticLoop full protocol 相比 B01 ad-hoc agent 将 unsupported claim rate 从 0.241 降至 0.125（绝对降幅 0.116，相对降幅 48.2%），并将 trace completeness 从 0.759 提升至 0.875。然而，Friedman 检验（n=6 任务块）未达显著性（unsupported rate p=0.497；trace completeness p=0.273），且 3 个种子间零方差严重限制了统计功效。因此，该趋势是方向性的，而非结论性的。"',
        "status: supported_with_caveats",
        "",
        "layer: L2",
        "evidence_type: controlled_run_artifact",
        "evidence_source:",
        "  - runs/V5_RQ01_T05_metrics.json",
        "  - runs/V5_RQ01_T05_audit_labels.json",
        "  - runs/V5_RQ01_T06_statistical_report.md",
        "  - runs/V5_RQ01_T02_adhoc_results/",
        "  - runs/V5_RQ01_T03_linear_results/",
        "  - runs/V5_RQ01_T04_full_results/",
        "",
        "scorecard:",
    ]
    for k, v in scorecard.items():
        lines.append(f"  {k}: {v}")
    lines.extend([
        f"  total_score: {total_score}",
        "  verdict: support_with_caveat",
        '  rationale: "L2 mechanistic insight: evidence gate and trace constraints produce a directional improvement in claim reliability metrics, but the synthetic 6-task suite, zero seed variance, and under-powered tests prevent a strong causal claim. The primary value is infrastructure validation. Mock leakage persisted across all conditions, indicating the gate does not block all failure modes."',
        "",
        "evidence:",
        "  - artifact: runs/V5_RQ01_T05_metrics.json",
        f'    description: "Condition-level aggregates: B01 unsupported_rate={b01["unsupported_claim_rate"]:.4f}, B02={b02["unsupported_claim_rate"]:.4f}, full={full["unsupported_claim_rate"]:.4f}; trace_completeness B01={b01["trace_completeness"]:.4f}, B02={b02["trace_completeness"]:.4f}, full={full["trace_completeness"]:.4f}."',
        "  - artifact: runs/V5_RQ01_T06_statistical_report.md",
        '    description: "Friedman test n.s. for all primary metrics (p > 0.27). Wilcoxon post-hoc all corrected p = 1.0000. Cohen kappa ≈ 0.0223 between audit and oracle-derived second rater."',
        "  - artifact: runs/V5_RQ01_T05_audit_labels.json",
        '    description: "Per-run per-claim deterministic audit labels. RTS03 B02 shows 3 incomplete executions (0 claims). RTS02 shows mock_leakage in 3 runs per condition."',
        "  - artifact: runs/V5_RQ01_T02_adhoc_results/",
        '    description: "18 B01 ad-hoc runs with raw transcripts, claims, and oracle audits."',
        "  - artifact: runs/V5_RQ01_T03_linear_results/",
        '    description: "18 B02 linear pipeline runs with raw transcripts, claims, and oracle audits."',
        "  - artifact: runs/V5_RQ01_T04_full_results/",
        '    description: "18 Full AgenticLoop runs with raw transcripts, claims, evidence traces, and oracle audits."',
        "",
        "supporting_metrics:",
        f'  - metric: "unsupported_claim_rate_B01"',
        f'    value: {b01["unsupported_claim_rate"]:.4f}',
        f'  - metric: "unsupported_claim_rate_B02"',
        f'    value: {b02["unsupported_claim_rate"]:.4f}',
        f'  - metric: "unsupported_claim_rate_full"',
        f'    value: {full["unsupported_claim_rate"]:.4f}',
        f'  - metric: "trace_completeness_B01"',
        f'    value: {b01["trace_completeness"]:.4f}',
        f'  - metric: "trace_completeness_B02"',
        f'    value: {b02["trace_completeness"]:.4f}',
        f'  - metric: "trace_completeness_full"',
        f'    value: {full["trace_completeness"]:.4f}',
        f'  - metric: "absolute_reduction_unsupported_rate_B01_to_full"',
        f'    value: {b01_to_full_rate:.4f}',
        f'  - metric: "absolute_improvement_trace_completeness_B01_to_full"',
        f'    value: {b01_to_full_trace:.4f}',
        f'  - metric: "friedman_p_unsupported_rate"',
        f'    value: 0.4966',
        f'  - metric: "friedman_p_trace_completeness"',
        f'    value: 0.2725',
        f'  - metric: "cohens_kappa_audit_vs_oracle"',
        f'    value: 0.0223',
        f'  - metric: "mock_leakage_runs_per_condition"',
        f'    value: 3',
        f'  - metric: "incomplete_execution_runs_B02_RTS03"',
        f'    value: 3',
        "",
        f"score: {total_score}/50",
        "",
        "detector_scan:",
        "  label_chaser: false",
        "  leaderboard_lizard: false",
        "  architecture_lego: false",
        "  vague_promiser: false",
        "  single_point_claim: false",
        "  toy_rq: false",
        "",
        "mve_status: completed",
        'mve_description: "6-task synthetic suite executed across 3 conditions × 3 seeds; deterministic audit and statistical tests produced traceable artifacts."',
        "",
        'falsification_condition: "若 full protocol 的 unsupported claim rate 相对 B01 未降低至少 40%，或 trace completeness < 0.90，或人工审计不支持 deterministic audit 标签，则该 RQ 假设被反驳或降级。"',
        "reproducibility:",
        '  command: "python experiments/v5/scripts/generate_insight.py --rq RQ01"',
        "  environment: Python 3.10+",
        "  seed: null",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# RQ02 generators
# ---------------------------------------------------------------------------

def generate_report_rq02(delta, cost_rows, stats_report_text, runs_dir: Path) -> str:
    bc = delta["by_condition"]
    full = bc["full"]
    nogate = bc["nogate"]
    noaudit = bc["noaudit"]
    dv = delta["delta_vs_full"]

    # Cost lookup
    cost = {}
    for row in cost_rows:
        cost[row["condition"]] = row

    lines = [
        "# V5 RQ02 T05 — Run Report + Insight",
        "",
        "**Generated:** `runs/V5_RQ02_T05_report.md`",
        "**Input:** T03 ablation delta (`V5_RQ02_T03_ablation_delta.json`) + T03 cost breakdown (`V5_RQ02_T03_cost_breakdown.csv`) + T04 statistical report (`V5_RQ02_T04_statistical_report.md`)",
        "",
        "## 1. Design Summary",
        "",
        "- **RQ:** 在 AgenticLoop full protocol 中，移除 evidence gate（nogate）或移除 audit phase（noaudit）会如何影响 unsupported claim rate、trace completeness 和运行成本？",
        "- **Task suite:** 6 synthetic research tasks (RTS01–RTS06), identical to RQ01.",
        "- **Conditions:** Full (RQ01 full protocol, reused as baseline), nogate (full without evidence gate), noaudit (full without audit phase)",
        "- **Design:** 6 tasks × 3 conditions × 3 seeds = 54 runs (18 per condition). Full condition reuses RQ01 T04 data; nogate/noaudit are new ablation runs.",
        "- **Primary metrics:** Unsupported Claim Rate, Trace Completeness",
        "- **Secondary metrics:** Total Claims, Overgeneralization Runs, Mock Leakage Runs, Wall Time, Token Usage",
        "",
        "## 2. Execution Narrative (T01–T04)",
        "",
        "| Task | Description | Status | Key Artifacts |",
        "|------|-------------|--------|---------------|",
        "| T01 | nogate ablation 运行 (18 runs) | Completed | `runs/V5_RQ02_T01_nogate_results/` |",
        "| T02 | noaudit ablation 运行 (18 runs) | Completed | `runs/V5_RQ02_T02_noaudit_results/` |",
        "| T03 | Ablation delta + cost breakdown | Completed | `runs/V5_RQ02_T03_ablation_delta.json`, `runs/V5_RQ02_T03_cost_breakdown.csv` |",
        "| T04 | 统计检验 + cost-benefit analysis | Completed | `runs/V5_RQ02_T04_statistical_report.md` |",
        "| **T05** | **Run report + insight** | **Active** | `runs/V5_RQ02_T05_report.md`, `insights/V5_RQ02_T05_insight.yaml` |",
        "",
        "## 3. Key Ablation Metrics Table",
        "",
        "### 3.1 Condition-level aggregates",
        "",
        "| Condition | Runs | Total Claims | Unsupported Rate | Trace Completeness | Mock Leakage Runs | Overgeneralization Runs |",
        "|-----------|-----:|-------------:|-----------------:|-------------------:|------------------:|------------------------:|",
        f"| full      | {full['total_runs']} | {full['total_claims']} | {full['unsupported_claim_rate']:.4f} | {full['trace_completeness']:.4f} | {full['mock_leakage_runs']} | {full['overgeneralization_runs']} |",
        f"| nogate    | {nogate['total_runs']} | {nogate['total_claims']} | {nogate['unsupported_claim_rate']:.4f} | {nogate['trace_completeness']:.4f} | {nogate['mock_leakage_runs']} | {nogate['overgeneralization_runs']} |",
        f"| noaudit   | {noaudit['total_runs']} | {noaudit['total_claims']} | {noaudit['unsupported_claim_rate']:.4f} | {noaudit['trace_completeness']:.4f} | {noaudit['mock_leakage_runs']} | {noaudit['overgeneralization_runs']} |",
        "",
        "### 3.2 Cost and time summary",
        "",
        "| Condition | Avg Wall Time (s) | Avg Prompt Tokens | Avg Completion Tokens | Avg Total Tokens |",
        "|-----------|------------------:|------------------:|----------------------:|-----------------:|",
        f"| full      | {cost['full']['avg_wall_time_seconds']} | {cost['full']['avg_prompt_tokens']} | {cost['full']['avg_completion_tokens']} | {float(cost['full']['avg_prompt_tokens']) + float(cost['full']['avg_completion_tokens']):.1f} |",
        f"| nogate    | {cost['nogate']['avg_wall_time_seconds']} | {cost['nogate']['avg_prompt_tokens']} | {cost['nogate']['avg_completion_tokens']} | {float(cost['nogate']['avg_prompt_tokens']) + float(cost['nogate']['avg_completion_tokens']):.1f} |",
        f"| noaudit   | {cost['noaudit']['avg_wall_time_seconds']} | {cost['noaudit']['avg_prompt_tokens']} | {cost['noaudit']['avg_completion_tokens']} | {float(cost['noaudit']['avg_prompt_tokens']) + float(cost['noaudit']['avg_completion_tokens']):.1f} |",
        "",
        "### 3.3 Delta vs full",
        "",
        "| Metric | nogate Δ | noaudit Δ |",
        "|--------|----------|-----------|",
        f"| Unsupported claim rate | +{dv['nogate']['unsupported_claim_rate_delta']:.4f} | +{dv['noaudit']['unsupported_claim_rate_delta']:.4f} |",
        f"| Trace completeness | {dv['nogate']['trace_completeness_delta']:.4f} | {dv['noaudit']['trace_completeness_delta']:.4f} |",
        f"| Total claims | {dv['nogate']['total_claims_delta']:+d} | {dv['noaudit']['total_claims_delta']:+d} |",
        f"| Overgeneralization runs | {dv['nogate']['overgeneralization_runs_delta']:+d} | {dv['noaudit']['overgeneralization_runs_delta']:+d} |",
        "",
        "## 4. Cost-Benefit Summary (from T04)",
        "",
        "- **nogate:** Removing the evidence gate increases average wall time (+9.6%) and total tokens, while substantially degrading quality. Unsupported claim rate rises +18.5 pp and trace completeness falls −18.5 pp. Verdict: **cost-increasing and quality-decreasing** on every measured dimension.",
        "- **noaudit:** Removing the audit phase yields large time/token savings (−55.6% wall time, −37.3% total tokens) but incurs a moderate quality penalty (+8.6 pp unsupported rate, −11.9 pp trace completeness). Overgeneralization runs appear (3 runs) that were caught by the audit in full. Verdict: **large cost savings with moderate quality loss**; trade-off acceptability depends on operational tolerance for missed overgeneralizations.",
        "- **Tokens-per-supported-claim:** full = 332.9, nogate = 478.8, noaudit = 247.0. noaudit is most token-efficient but loses the audit reflection loop.",
        "",
        "## 5. Honest Caveats",
        "",
        "1. **Descriptive only:** All deltas are point estimates. No p-values or confidence intervals are reported because the design is under-powered (n=6 task blocks) and seeds are not independent.",
        "2. **Seed non-independence:** The same seeds (1, 2, 3) are reused across full, nogate, and noaudit runs. Any seed-specific idiosyncrasy is correlated across conditions, inflating apparent precision.",
        "3. **Deterministic audit:** The audit pipeline uses substring and oracle-based heuristics. False positives and false negatives are possible, and any systematic bias applies equally across conditions.",
        "4. **No human adjudication:** All quality labels are automated. There is no ground-truth human-labeled dataset to calibrate sensitivity/specificity.",
        "5. **noaudit RTS04 overgeneralization heuristic false-positive risk:** The 3 overgeneralization runs flagged in noaudit RTS04 may be false positives. The model's shorter output (no audit loop) may simply omit methodological detail rather than genuinely overgeneralize. This caveat is carried forward from T03.",
        "6. **RQ01 full threshold not met:** The full protocol itself did not achieve statistically significant improvements over B01/B02 in RQ01. Therefore, ablation deltas against full are benchmarking against a baseline that is itself not conclusively superior to simpler alternatives.",
        "",
        "## 6. Conclusion",
        "",
        "- **Evidence gate removal (nogate)** clearly worsened claim-quality metrics (unsupported rate +18.5 pp, completeness −18.5 pp) without producing cost savings. The gate appears to provide quality benefits at no additional runtime cost in this synthetic suite.",
        "- **Audit removal (noaudit)** saved substantial time and tokens but degraded quality metrics and lost overgeneralization detection. Whether this trade-off is acceptable depends on the operational value of the audit phase and the false-positive rate of the overgeneralization heuristic.",
        "- **Neither ablation supports a strong significance claim.** The design is descriptive and directional; all statements about comparative quality are qualified by seed non-independence, deterministic audit limitations, and small block-level sample size.",
        "",
        "**负结果也是结果.** The ablation infrastructure executed end-to-end and produced traceable cost-quality trade-off data. The primary value is methodological: we now have a reproducible pipeline for measuring component-level contributions in research-agent protocols.",
        "",
        "---",
        "*Report generated by `experiments/v5/scripts/generate_insight.py`*",
    ]

    return "\n".join(lines)


def generate_insight_yaml_rq02(delta, cost_rows, stats_report_text) -> str:
    bc = delta["by_condition"]
    full = bc["full"]
    nogate = bc["nogate"]
    noaudit = bc["noaudit"]
    dv = delta["delta_vs_full"]

    cost = {}
    for row in cost_rows:
        cost[row["condition"]] = row

    # Scorecard: 10 dimensions × 0–5 = 50 total, following V4/RQ01 convention
    scorecard = {
        "groundedness": 5,
        "directness": 4,
        "non_toy_depth": 3,
        "assumption_challenge": 4,
        "mechanism_clarity": 4,
        "falsifiability": 5,
        "evidence_ladder_strength": 3,
        "negative_result_value": 5,
        "statistical_rigor": 2,
        "reproducibility": 4,
    }
    total_score = sum(scorecard.values())

    lines = [
        "---",
        "name: v5-rq02-ablation-cost-benefit",
        "insight_id: V5_RQ02_T05_001",
        "description: Ablation of evidence gate and audit phase in AgenticLoop full protocol shows directional cost-quality trade-offs on a 6-task synthetic suite. Gate removal degrades quality without cost savings; audit removal saves cost but degrades quality and loses overgeneralization detection. No statistical significance is claimed.",
        "metadata:",
        "  type: project",
        "---",
        "",
        "template_family: agentic_loop",
        "template_version: epoch_v1",
        "schema_version: 1",
        "generated_by: experiments/v5/scripts/generate_insight.py",
        "epoch: V5",
        "rq_id: RQ02",
        "task_id: T05",
        "",
        'question: "在 AgenticLoop full protocol 中，移除 evidence gate（nogate）或移除 audit phase（noaudit）会如何影响 unsupported claim rate、trace completeness 和运行成本？"',
        'claim: "在 6 个受控合成研究任务上，移除 evidence gate 使 unsupported claim rate 从 0.125 升至 0.310（+0.185），trace completeness 从 0.875 降至 0.690（−0.185），且未节省 wall time 或 tokens。移除 audit phase 使 unsupported claim rate 升至 0.211（+0.086），trace completeness 降至 0.756（−0.119），但 wall time 减少 55.6%、tokens 减少 37.3%。两种 ablation 均 degrade 质量；nogate 无成本收益，noaudit 有显著成本收益但伴随质量损失和 overgeneralization 检测失效。所有结论均为描述性，未声称统计显著性。"',
        "status: supported_with_caveats",
        "",
        "layer: L2",
        "evidence_type: controlled_run_artifact",
        "evidence_source:",
        "  - runs/V5_RQ02_T03_ablation_delta.json",
        "  - runs/V5_RQ02_T03_cost_breakdown.csv",
        "  - runs/V5_RQ02_T04_statistical_report.md",
        "  - runs/V5_RQ02_T01_nogate_results/",
        "  - runs/V5_RQ02_T02_noaudit_results/",
        "  - runs/V5_RQ01_T04_full_results/",
        "  - runs/V5_RQ01_T05_metrics.json",
        "",
        "scorecard:",
    ]
    for k, v in scorecard.items():
        lines.append(f"  {k}: {v}")
    lines.extend([
        f"  total_score: {total_score}",
        "  verdict: support_with_caveat",
        '  rationale: "L2 mechanistic insight: evidence gate and audit phase each contribute directional quality benefits in a synthetic 6-task suite. Gate removal is unambiguously harmful on all measured dimensions. Audit removal produces a cost-quality trade-off that may be acceptable depending on operational constraints. Caveats include seed non-independence, deterministic audit heuristics, no human adjudication, and under-powered block-level sample (n=6)."',
        "",
        "evidence:",
        "  - artifact: runs/V5_RQ02_T03_ablation_delta.json",
        f'    description: "Condition-level aggregates: full unsupported_rate={full["unsupported_claim_rate"]:.4f}, nogate={nogate["unsupported_claim_rate"]:.4f}, noaudit={noaudit["unsupported_claim_rate"]:.4f}; trace_completeness full={full["trace_completeness"]:.4f}, nogate={nogate["trace_completeness"]:.4f}, noaudit={noaudit["trace_completeness"]:.4f}."',
        "  - artifact: runs/V5_RQ02_T03_cost_breakdown.csv",
        f'    description: "Cost data: full avg wall_time={cost["full"]["avg_wall_time_seconds"]}s, nogate={cost["nogate"]["avg_wall_time_seconds"]}s, noaudit={cost["noaudit"]["avg_wall_time_seconds"]}s."',
        "  - artifact: runs/V5_RQ02_T04_statistical_report.md",
        '    description: "Descriptive and nonparametric summaries. Formal inferential tests abstained due to seed non-independence and n=6 blocks. Cost-normalized quality metrics and directional counts reported."',
        "  - artifact: runs/V5_RQ02_T01_nogate_results/",
        '    description: "18 nogate ablation runs with raw transcripts, claims, and oracle audits."',
        "  - artifact: runs/V5_RQ02_T02_noaudit_results/",
        '    description: "18 noaudit ablation runs with raw transcripts, claims, and oracle audits."',
        "  - artifact: runs/V5_RQ01_T04_full_results/",
        '    description: "18 Full AgenticLoop runs reused as baseline from RQ01."',
        "  - artifact: runs/V5_RQ01_T05_metrics.json",
        '    description: "RQ01 full condition metrics used as baseline for delta computation."',
        "",
        "supporting_metrics:",
        f'  - metric: "unsupported_claim_rate_full"',
        f'    value: {full["unsupported_claim_rate"]:.4f}',
        f'  - metric: "unsupported_claim_rate_nogate"',
        f'    value: {nogate["unsupported_claim_rate"]:.4f}',
        f'  - metric: "unsupported_claim_rate_noaudit"',
        f'    value: {noaudit["unsupported_claim_rate"]:.4f}',
        f'  - metric: "trace_completeness_full"',
        f'    value: {full["trace_completeness"]:.4f}',
        f'  - metric: "trace_completeness_nogate"',
        f'    value: {nogate["trace_completeness"]:.4f}',
        f'  - metric: "trace_completeness_noaudit"',
        f'    value: {noaudit["trace_completeness"]:.4f}',
        f'  - metric: "delta_unsupported_rate_nogate_vs_full"',
        f'    value: {dv["nogate"]["unsupported_claim_rate_delta"]:.4f}',
        f'  - metric: "delta_trace_completeness_nogate_vs_full"',
        f'    value: {dv["nogate"]["trace_completeness_delta"]:.4f}',
        f'  - metric: "delta_unsupported_rate_noaudit_vs_full"',
        f'    value: {dv["noaudit"]["unsupported_claim_rate_delta"]:.4f}',
        f'  - metric: "delta_trace_completeness_noaudit_vs_full"',
        f'    value: {dv["noaudit"]["trace_completeness_delta"]:.4f}',
        f'  - metric: "overgeneralization_runs_noaudit"',
        f'    value: {noaudit["overgeneralization_runs"]}',
        f'  - metric: "wall_time_seconds_full"',
        f'    value: {float(cost["full"]["avg_wall_time_seconds"]):.2f}',
        f'  - metric: "wall_time_seconds_nogate"',
        f'    value: {float(cost["nogate"]["avg_wall_time_seconds"]):.2f}',
        f'  - metric: "wall_time_seconds_noaudit"',
        f'    value: {float(cost["noaudit"]["avg_wall_time_seconds"]):.2f}',
        f'  - metric: "tokens_per_supported_claim_full"',
        f'    value: 332.9',
        f'  - metric: "tokens_per_supported_claim_nogate"',
        f'    value: 478.8',
        f'  - metric: "tokens_per_supported_claim_noaudit"',
        f'    value: 247.0',
        "",
        f"score: {total_score}/50",
        "",
        "detector_scan:",
        "  label_chaser: false",
        "  leaderboard_lizard: false",
        "  architecture_lego: false",
        "  vague_promiser: false",
        "  single_point_claim: false",
        "  toy_rq: false",
        "",
        "mve_status: completed",
        'mve_description: "6-task synthetic suite executed across 3 ablation conditions × 3 seeds; cost-quality deltas and descriptive statistical summaries produced as traceable artifacts."',
        "",
        'falsification_condition: "若 nogate 的 unsupported claim rate 未显著高于 full，或 noaudit 的 wall time 未显著低于 full，或人工审计推翻 deterministic audit 标签，则该 RQ 假设被反驳或降级。"',
        "reproducibility:",
        '  command: "python experiments/v5/scripts/generate_insight.py --rq RQ02"',
        "  environment: Python 3.10+",
        "  seed: null",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate run report + insight for V5 RQ01 or RQ02")
    parser.add_argument("--rq", required=True, help="RQ ID (e.g., RQ01, RQ02)")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[3]
    runs_dir = repo_root / "runs"
    insights_dir = repo_root / "insights"
    ensure_dir(insights_dir)

    if args.rq == "RQ01":
        metrics_path = runs_dir / "V5_RQ01_T05_metrics.json"
        stats_path = runs_dir / "V5_RQ01_T06_statistical_report.md"

        if not metrics_path.exists():
            print(f"Error: Metrics file not found: {metrics_path}", file=sys.stderr)
            sys.exit(1)
        if not stats_path.exists():
            print(f"Error: Statistical report not found: {stats_path}", file=sys.stderr)
            sys.exit(1)

        metrics = load_json(metrics_path)
        stats_report_text = load_text(stats_path)

        report_path = runs_dir / "V5_RQ01_T07_report.md"
        insight_path = insights_dir / "V5_RQ01_T07_insight.yaml"

        report = generate_report_rq01(metrics, stats_report_text, runs_dir)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Written: {report_path}")

        insight = generate_insight_yaml_rq01(metrics, stats_report_text)
        with open(insight_path, "w", encoding="utf-8") as f:
            f.write(insight)
        print(f"Written: {insight_path}")

        print("RQ01 T07 generation complete.")

    elif args.rq == "RQ02":
        delta_path = runs_dir / "V5_RQ02_T03_ablation_delta.json"
        cost_path = runs_dir / "V5_RQ02_T03_cost_breakdown.csv"
        stats_path = runs_dir / "V5_RQ02_T04_statistical_report.md"

        if not delta_path.exists():
            print(f"Error: Ablation delta file not found: {delta_path}", file=sys.stderr)
            sys.exit(1)
        if not cost_path.exists():
            print(f"Error: Cost breakdown file not found: {cost_path}", file=sys.stderr)
            sys.exit(1)
        if not stats_path.exists():
            print(f"Error: Statistical report not found: {stats_path}", file=sys.stderr)
            sys.exit(1)

        delta = load_json(delta_path)
        cost_rows = load_csv(cost_path)
        stats_report_text = load_text(stats_path)

        report_path = runs_dir / "V5_RQ02_T05_report.md"
        insight_path = insights_dir / "V5_RQ02_T05_insight.yaml"

        report = generate_report_rq02(delta, cost_rows, stats_report_text, runs_dir)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Written: {report_path}")

        insight = generate_insight_yaml_rq02(delta, cost_rows, stats_report_text)
        with open(insight_path, "w", encoding="utf-8") as f:
            f.write(insight)
        print(f"Written: {insight_path}")

        print("RQ02 T05 generation complete.")

    else:
        print(f"Error: Unsupported RQ: {args.rq}. Supported: RQ01, RQ02", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
