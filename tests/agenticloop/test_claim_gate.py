"""Tests for claim admission gate."""

from __future__ import annotations

from agenticloop.claim_gate import admit_claim, classify_claim_support


def test_unsupported_without_trace():
    assert classify_claim_support("The method is clearly better.") == "unsupported"
    out = admit_claim("The method is clearly better.")
    assert out.decision == "held"
    assert out.paper_allowed is False


def test_admitted_with_artifact_reference():
    claim = (
        "Full unsupported claim rate is 6.87% according to "
        "runs/V6_RQ01_T05_metrics.json claim-weighted by_condition."
    )
    out = admit_claim(claim)
    assert out.has_evidence_trace is True
    assert out.decision == "admitted"
    assert out.paper_allowed is True


def test_mock_rejected():
    out = admit_claim("[DRY-RUN] Placeholder accuracy is 99%.")
    assert out.decision == "rejected"
    assert out.mock_risk is True


def test_require_artifact_path_holds_metric_only():
    out = admit_claim("Unsupported rate fell by 1.7%.", require_artifact_path=True)
    assert out.decision == "held"
