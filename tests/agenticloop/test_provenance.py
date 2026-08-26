"""Tests for metric provenance + spine loading."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from agenticloop.provenance import load_metric_bundle, resolve_metric
from agenticloop.spine import load_research_spine


def test_load_metric_bundle_has_t05_and_ablation():
    bundle = load_metric_bundle(ROOT)
    assert "t05_claim_weighted" in bundle["available"]
    assert "ablation_delta" in bundle["available"]
    full = bundle["available"]["t05_claim_weighted"]["full"]
    assert full["total_claims"] == 742
    assert abs(full["unsupported_claim_rate"] - 0.0687) < 1e-6


def test_resolve_metric_rejects_unknown():
    try:
        resolve_metric("not_a_real_metric", ROOT)
        assert False, "expected KeyError"
    except KeyError:
        pass


def test_spine_current_is_v6():
    spine = load_research_spine(ROOT)
    assert spine["current_epoch"] == "V6"
    assert spine["status"]["status"] == "closed_negative"
    assert spine["falsification"]["status"] == "not_supported_in_v6"
