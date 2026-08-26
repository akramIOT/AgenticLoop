"""Load research spine status for the Evidence Console."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "docs" / "research" / "CURRENT").exists():
            return parent
    return here.parents[2]


def load_research_spine(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    research = root / "docs" / "research"
    current = (research / "CURRENT").read_text(encoding="utf-8").strip()
    status_path = research / current / "STATUS.yaml"
    closeout_path = research / current / "closeout.md"
    binding_path = research / current / "PAPER_BINDING_DECISION.md"

    status: dict[str, Any] = {}
    if status_path.exists():
        status = yaml.safe_load(status_path.read_text(encoding="utf-8")) or {}

    pipeline = [
        {"id": "direction", "label": "Research Direction", "state": "frozen"},
        {"id": "epoch", "label": f"Epoch {current}", "state": status.get("status", "unknown")},
        {"id": "rq_spine", "label": "RQ Spine", "state": "completed" if status.get("completed_rqs") else "active"},
        {"id": "baseline_lock", "label": "Baseline Lock", "state": "locked"},
        {"id": "evidence_gate", "label": "Evidence Gate", "state": "null_effect_observed"},
        {"id": "audit_gate", "label": "Audit Gate", "state": "passed_with_caveat"},
        {"id": "closeout", "label": "Closeout", "state": "closed_negative" if status.get("status") == "closed_negative" else status.get("status", "unknown")},
        {"id": "paper_binding", "label": "Paper Binding", "state": "ready" if (status.get("paper_binding") or {}).get("allowed") else "blocked"},
    ]

    return {
        "current_epoch": current,
        "status": status,
        "pipeline": pipeline,
        "artifacts": {
            "status": str(status_path.relative_to(root)) if status_path.exists() else None,
            "closeout": str(closeout_path.relative_to(root)) if closeout_path.exists() else None,
            "paper_binding": str(binding_path.relative_to(root)) if binding_path.exists() else None,
            "t05_metrics": "runs/V6_RQ01_T05_metrics.json",
            "t06_summary": "runs/V6_RQ01_T06_comparison_summary.json",
            "ablation": "runs/V6_RQ02_T03_ablation_delta.json",
        },
        "falsification": {
            "hypothesis": "Evidence gate reduces unsupported claim rate vs baselines",
            "status": "not_supported_in_v6",
            "evidence": [
                "T05: B02≈Full (−0.01pp claim-weighted)",
                "T06: Friedman p=0.79 (n.s.)",
                "Ablation: Nogate delta −0.1pp",
            ],
        },
    }
