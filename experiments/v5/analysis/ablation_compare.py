#!/usr/bin/env python3
"""Ablation claims audit + comparison with RQ01 full for V5 RQ02 T03.

Reads:
  - RQ01 full metrics: runs/V5_RQ01_T05_metrics.json
  - RQ01 full labels:  runs/V5_RQ01_T05_audit_labels.json
  - RQ02 nogate runs:  runs/V5_RQ02_T01_nogate_results/
  - RQ02 noaudit runs: runs/V5_RQ02_T02_noaudit_results/

Emits:
  - runs/V5_RQ02_T03_ablation_delta.json
  - runs/V5_RQ02_T03_cost_breakdown.csv

Caveats encoded:
  1. Seeds are not independent across conditions (same seed values reused).
  2. Deterministic audit uses substring/oracle heuristics; false positives/negatives possible.
  3. Deltas are descriptive only; statistical significance is handled in T04.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.v5.audit.audit_all import (
    _aggregate_metrics,
    _audit_run,
)

# Inputs
RQ01_METRICS_PATH = REPO_ROOT / "runs" / "V5_RQ01_T05_metrics.json"
RQ01_LABELS_PATH = REPO_ROOT / "runs" / "V5_RQ01_T05_audit_labels.json"

NOGATE_DIR = REPO_ROOT / "runs" / "V5_RQ02_T01_nogate_results"
NOAUDIT_DIR = REPO_ROOT / "runs" / "V5_RQ02_T02_noaudit_results"
FULL_DIR = REPO_ROOT / "runs" / "V5_RQ01_T04_full_results"

# Outputs
OUTPUT_DELTA = REPO_ROOT / "runs" / "V5_RQ02_T03_ablation_delta.json"
OUTPUT_COST = REPO_ROOT / "runs" / "V5_RQ02_T03_cost_breakdown.csv"


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


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _audit_directory(root_dir: Path, condition_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Audit all manifests in a directory and return (audits, metrics)."""
    manifests = _find_manifests(root_dir)
    print(f"[{condition_id}] Found {len(manifests)} manifests in {root_dir}")
    audits: list[dict[str, Any]] = []
    for mf in manifests:
        audit = _audit_run(mf)
        audits.append(audit)
        print(f"  Audited {audit['run_id']}: {audit['total_claims']} claims, "
              f"unsupported={audit['unsupported_count']}, supported={audit['supported_count']}, "
              f"incomplete={audit['incomplete_execution']}")
    metrics = _aggregate_metrics(audits, conditions=[condition_id])
    return audits, metrics


def _compute_delta(full: dict[str, Any], ablation: dict[str, Any]) -> dict[str, Any]:
    """Compute numeric deltas of ablation vs full."""
    delta: dict[str, Any] = {}

    # Primary deltas
    delta["unsupported_claim_rate_delta"] = round(
        ablation.get("unsupported_claim_rate", 0.0) - full.get("unsupported_claim_rate", 0.0), 4
    )
    delta["trace_completeness_delta"] = round(
        ablation.get("trace_completeness", 0.0) - full.get("trace_completeness", 0.0), 4
    )
    delta["mock_leakage_runs_delta"] = (
        ablation.get("mock_leakage_runs", 0) - full.get("mock_leakage_runs", 0)
    )
    delta["total_claims_delta"] = (
        ablation.get("total_claims", 0) - full.get("total_claims", 0)
    )
    delta["baseline_drift_count_delta"] = (
        ablation.get("baseline_drift_count", 0) - full.get("baseline_drift_count", 0)
    )
    delta["failure_misclassification_runs_delta"] = (
        ablation.get("failure_misclassification_runs", 0) - full.get("failure_misclassification_runs", 0)
    )
    delta["incomplete_execution_runs_delta"] = (
        ablation.get("incomplete_execution_runs", 0) - full.get("incomplete_execution_runs", 0)
    )
    delta["overgeneralization_runs_delta"] = (
        ablation.get("overgeneralization_runs", 0) - full.get("overgeneralization_runs", 0)
    )
    delta["cherry_picking_runs_delta"] = (
        ablation.get("cherry_picking_runs", 0) - full.get("cherry_picking_runs", 0)
    )
    delta["cross_contamination_runs_delta"] = (
        ablation.get("cross_contamination_runs", 0) - full.get("cross_contamination_runs", 0)
    )
    delta["source_abuse_runs_delta"] = (
        ablation.get("source_abuse_runs", 0) - full.get("source_abuse_runs", 0)
    )
    return delta


def _build_cost_row(condition: str, manifests: list[Path]) -> dict[str, Any]:
    total_runs = len(manifests)
    total_model_calls = 0
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_wall_time = 0.0
    for mf in manifests:
        data = _load_json(mf)
        overhead = data.get("overhead", {})
        total_model_calls += overhead.get("model_calls", 0)
        total_prompt_tokens += overhead.get("prompt_tokens", 0)
        total_completion_tokens += overhead.get("completion_tokens", 0)
        total_wall_time += overhead.get("wall_time_seconds", 0.0)

    avg_prompt = total_prompt_tokens / total_runs if total_runs > 0 else 0.0
    avg_completion = total_completion_tokens / total_runs if total_runs > 0 else 0.0
    avg_wall = total_wall_time / total_runs if total_runs > 0 else 0.0

    return {
        "condition": condition,
        "total_runs": total_runs,
        "total_model_calls": total_model_calls,
        "total_prompt_tokens": total_prompt_tokens,
        "total_completion_tokens": total_completion_tokens,
        "total_wall_time_seconds": round(total_wall_time, 2),
        "avg_prompt_tokens": round(avg_prompt, 1),
        "avg_completion_tokens": round(avg_completion, 1),
        "avg_wall_time_seconds": round(avg_wall, 2),
    }


def main() -> int:
    # Load RQ01 full metrics
    rq01_metrics = _load_json(RQ01_METRICS_PATH)
    full_by_condition = rq01_metrics.get("by_condition", {}).get("full", {})
    full_by_task_condition = rq01_metrics.get("by_task_condition", {})

    # Audit ablation directories
    nogate_audits, nogate_metrics = _audit_directory(NOGATE_DIR, "nogate")
    noaudit_audits, noaudit_metrics = _audit_directory(NOAUDIT_DIR, "noaudit")

    # Build by_condition for all three
    by_condition: dict[str, Any] = {
        "full": full_by_condition,
        "nogate": nogate_metrics.get("by_condition", {}).get("nogate", {}),
        "noaudit": noaudit_metrics.get("by_condition", {}).get("noaudit", {}),
    }

    # Compute deltas
    delta_vs_full: dict[str, Any] = {}
    for cond in ("nogate", "noaudit"):
        delta_vs_full[cond] = _compute_delta(full_by_condition, by_condition[cond])

    # Build by_task_condition combining full + ablations
    by_task_condition: dict[str, Any] = {}
    # Copy full entries
    for key, val in full_by_task_condition.items():
        if key.endswith("__full"):
            by_task_condition[key] = val
    # Add nogate entries
    for key, val in nogate_metrics.get("by_task_condition", {}).items():
        by_task_condition[key] = val
    # Add noaudit entries
    for key, val in noaudit_metrics.get("by_task_condition", {}).items():
        by_task_condition[key] = val

    # Build delta output
    delta_output = {
        "schema_version": 1,
        "description": "Ablation delta metrics for V5 RQ02 T03: nogate and noaudit vs RQ01 full",
        "by_condition": by_condition,
        "delta_vs_full": delta_vs_full,
        "by_task_condition": by_task_condition,
        "caveats": [
            "Seeds are not independent across conditions (same seed values reused in ablation runs).",
            "Deterministic audit uses substring/oracle heuristics; false positives and negatives are possible.",
            "Deltas are descriptive point estimates only; statistical significance and cost-benefit analysis are handled in T04.",
            "RQ01 full metrics were produced by the same deterministic audit pipeline; any systematic bias applies equally.",
        ],
    }

    OUTPUT_DELTA.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_DELTA.write_text(json.dumps(delta_output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote delta -> {OUTPUT_DELTA}")

    # Cost breakdown
    full_manifests = _find_manifests(FULL_DIR)
    nogate_manifests = _find_manifests(NOGATE_DIR)
    noaudit_manifests = _find_manifests(NOAUDIT_DIR)

    rows = [
        _build_cost_row("full", full_manifests),
        _build_cost_row("nogate", nogate_manifests),
        _build_cost_row("noaudit", noaudit_manifests),
    ]

    fieldnames = [
        "condition",
        "total_runs",
        "total_model_calls",
        "total_prompt_tokens",
        "total_completion_tokens",
        "total_wall_time_seconds",
        "avg_prompt_tokens",
        "avg_completion_tokens",
        "avg_wall_time_seconds",
    ]

    with OUTPUT_COST.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote cost breakdown -> {OUTPUT_COST}")

    # Print summary
    print("\n=== Ablation Delta Summary ===")
    for cond in ("nogate", "noaudit"):
        d = delta_vs_full[cond]
        print(f"\n{cond} vs full:")
        print(f"  unsupported_claim_rate_delta: {d['unsupported_claim_rate_delta']:+.4f}")
        print(f"  trace_completeness_delta:     {d['trace_completeness_delta']:+.4f}")
        print(f"  mock_leakage_runs_delta:      {d['mock_leakage_runs_delta']:+d}")
        print(f"  total_claims_delta:           {d['total_claims_delta']:+d}")
        print(f"  incomplete_execution_delta:   {d['incomplete_execution_runs_delta']:+d}")
        print(f"  baseline_drift_delta:         {d['baseline_drift_count_delta']:+d}")
        print(f"  failure_misclass_delta:       {d['failure_misclassification_runs_delta']:+d}")
        print(f"  overgeneralization_delta:     {d['overgeneralization_runs_delta']:+d}")
        print(f"  cherry_picking_delta:         {d['cherry_picking_runs_delta']:+d}")
        print(f"  cross_contamination_delta:    {d['cross_contamination_runs_delta']:+d}")
        print(f"  source_abuse_delta:           {d['source_abuse_runs_delta']:+d}")

    print("\n=== Cost Breakdown ===")
    for r in rows:
        print(f"  {r['condition']}: runs={r['total_runs']}, calls={r['total_model_calls']}, "
              f"prompt={r['total_prompt_tokens']}, completion={r['total_completion_tokens']}, "
              f"wall={r['total_wall_time_seconds']}s")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
