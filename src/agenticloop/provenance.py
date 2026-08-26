"""Metric provenance resolver — maps headline numbers to durable artifacts.

Prevents mixing T05 claim-weighted rates with ablation-classifier rates.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MetricSource:
    metric_id: str
    label: str
    path: str
    aggregation: str
    paper_use: str
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


METRIC_SOURCES: dict[str, MetricSource] = {
    "t05_claim_weighted": MetricSource(
        metric_id="t05_claim_weighted",
        label="V6 T05 claim-weighted condition rates",
        path="runs/V6_RQ01_T05_metrics.json",
        aggregation="by_condition (claims pooled across tasks/seeds)",
        paper_use="Canonical for B01 / B02 / Full headline tables",
        notes="Do not mix with ablation absolute rates.",
    ),
    "t05_task_mean": MetricSource(
        metric_id="t05_task_mean",
        label="V6 T05 task-mean rates",
        path="runs/V6_RQ01_T06_statistical_report.md",
        aggregation="equal weight per task (Friedman / Wilcoxon blocks)",
        paper_use="Inferential tests only",
        notes="Task-mean and claim-weighted diverge when claim counts differ by task.",
    ),
    "t06_stats": MetricSource(
        metric_id="t06_stats",
        label="V6 T06 corrected statistical summary",
        path="runs/V6_RQ01_T06_comparison_summary.json",
        aggregation="Friedman df=k-1; Wilcoxon with Bonferroni",
        paper_use="Significance claims",
        notes="Replaces pre-correction negative chi-square / wrong-df report.",
    ),
    "ablation_delta": MetricSource(
        metric_id="ablation_delta",
        label="V6 RQ02 ablation deltas",
        path="runs/V6_RQ02_T03_ablation_delta.json",
        aggregation="ablation claim classifier (separate from T05)",
        paper_use="Gate / audit component deltas only",
        notes="Full claim count 699 here vs 742 in T05 — expected classifier drift.",
    ),
}


def _repo_root(start: Path | None = None) -> Path:
    if start is None:
        start = Path(__file__).resolve()
    for parent in [start, *start.parents]:
        if (parent / "docs" / "research" / "CURRENT").exists():
            return parent
    return Path(__file__).resolve().parents[2]


def load_metric_bundle(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    t05_path = root / "runs" / "V6_RQ01_T05_metrics.json"
    summary_path = root / "runs" / "V6_RQ01_T06_comparison_summary.json"
    ablation_path = root / "runs" / "V6_RQ02_T03_ablation_delta.json"

    bundle: dict[str, Any] = {
        "repo_root": str(root),
        "sources": {k: v.to_dict() for k, v in METRIC_SOURCES.items()},
        "available": {},
    }

    if t05_path.exists():
        t05 = json.loads(t05_path.read_text(encoding="utf-8"))
        bundle["available"]["t05_claim_weighted"] = t05.get("by_condition", {})
        bundle["available"]["t05_by_task_condition"] = t05.get("by_task_condition", {})

    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        bundle["available"]["t06_stats"] = {
            "friedman_unsupported_rate": summary.get("friedman_unsupported_rate"),
            "wilcoxon_unsupported_rate": summary.get("wilcoxon_unsupported_rate"),
            "task_mean": summary.get("task_mean"),
            "claim_weighted": summary.get("claim_weighted"),
        }

    if ablation_path.exists():
        ablation = json.loads(ablation_path.read_text(encoding="utf-8"))
        bundle["available"]["ablation_delta"] = {
            "full": {k: v for k, v in ablation.get("full", {}).items() if k != "task_metrics"},
            "nogate": {k: v for k, v in ablation.get("nogate", {}).items() if k != "task_metrics"},
            "noaudit": {k: v for k, v in ablation.get("noaudit", {}).items() if k != "task_metrics"},
            "deltas": ablation.get("deltas", {}),
        }

    return bundle


def resolve_metric(metric_id: str, repo_root: Path | None = None) -> dict[str, Any]:
    if metric_id not in METRIC_SOURCES:
        raise KeyError(f"Unknown metric_id: {metric_id}. Known: {sorted(METRIC_SOURCES)}")
    source = METRIC_SOURCES[metric_id]
    bundle = load_metric_bundle(repo_root)
    return {
        "source": source.to_dict(),
        "data": bundle["available"].get(metric_id),
        "present": metric_id in bundle["available"],
    }
