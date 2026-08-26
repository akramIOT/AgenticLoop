"""Claim admission helpers — evidence-gate style checks for research claims.

These heuristics mirror the V6 audit markers. They are control-plane tooling,
not admitted scientific results by themselves.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


EVIDENCE_MARKERS = (
    "workspace/",
    ".yaml",
    ".csv",
    ".json",
    ".md",
    ".bib",
    "results",
    "experiment_",
    "manifest",
    "methodology",
    "baseline_config",
    "benchmark_",
    "run report",
    "artifact",
    "hash",
    "audit",
)

MOCK_MARKERS = (
    "dry-run",
    "[dry-run]",
    "toy data",
    "synthetic only",
    "placeholder result",
    "mock leakage",
)

UNSUPPORTED_CUES = (
    "all modules",
    "entire project",
    "universally",
    "proves that",
    "definitively shows",
)


@dataclass(frozen=True)
class ClaimAdmission:
    claim: str
    decision: str  # admitted | held | rejected
    has_evidence_trace: bool
    mock_risk: bool
    overclaim_risk: bool
    reasons: tuple[str, ...]
    paper_allowed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def has_evidence_trace(claim: str) -> bool:
    lower = claim.lower()
    if any(m in lower for m in EVIDENCE_MARKERS):
        return True
    if re.search(r"\b\d+\.\d+%?|\b\d+%", lower):
        return True
    if re.search(r"\b(rts\d+|v[0-9]+_rq\d+|runs/)", lower):
        return True
    return False


def classify_claim_support(claim: str) -> str:
    """Return supported | unsupported | mock_risk for a single claim string."""
    lower = claim.strip().lower()
    if not lower:
        return "unsupported"
    if any(m in lower for m in MOCK_MARKERS):
        return "mock_risk"
    if not has_evidence_trace(claim):
        return "unsupported"
    if any(c in lower for c in UNSUPPORTED_CUES) and "scanned" not in lower:
        return "unsupported"
    return "supported"


def admit_claim(
    claim: str,
    *,
    require_artifact_path: bool = False,
    allow_mock: bool = False,
) -> ClaimAdmission:
    """Apply an evidence-gate style admission decision to a draft claim."""
    text = (claim or "").strip()
    reasons: list[str] = []
    if not text:
        return ClaimAdmission(
            claim=text,
            decision="rejected",
            has_evidence_trace=False,
            mock_risk=False,
            overclaim_risk=False,
            reasons=("empty claim",),
            paper_allowed=False,
        )

    support = classify_claim_support(text)
    has_trace = has_evidence_trace(text)
    mock_risk = support == "mock_risk"
    overclaim = any(c in text.lower() for c in UNSUPPORTED_CUES) and "scanned" not in text.lower()

    if mock_risk and not allow_mock:
        reasons.append("mock/dry-run language detected; claim support forbidden")
        decision = "rejected"
    elif not has_trace:
        reasons.append("no evidence-trace markers (path, metric, run id, or artifact)")
        decision = "held"
    elif require_artifact_path and not re.search(r"(workspace/|runs/|\.json|\.yaml|\.csv|\.md)", text, re.I):
        reasons.append("artifact path required by gate policy but missing")
        decision = "held"
    elif overclaim:
        reasons.append("over-generalization cues without bounding language")
        decision = "held"
    elif support == "supported":
        reasons.append("evidence-trace markers present; eligible for audit")
        decision = "admitted"
    else:
        reasons.append(f"classifier label={support}")
        decision = "held"

    return ClaimAdmission(
        claim=text,
        decision=decision,
        has_evidence_trace=has_trace,
        mock_risk=mock_risk,
        overclaim_risk=overclaim,
        reasons=tuple(reasons),
        paper_allowed=decision == "admitted",
    )
