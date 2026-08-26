"""Tests for strengthened research claims."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from agenticloop.strengthened_claims import compute_strengthened_claims, write_strengthened_claim_artifacts


def test_eight_strengthened_claims():
    analysis = compute_strengthened_claims(ROOT)
    ids = {c["id"] for c in analysis.claims}
    assert len(analysis.claims) >= 8
    assert "SC1_cosmetic_traces" in ids
    assert "SC4_near_equivalence" in ids
    assert "SC8_gate_negative_tasks" in ids


def test_near_zero_difference_not_tost():
    ne = compute_strengthened_claims(ROOT).near_equivalence
    assert ne["within_descriptive_0_5pp_band"] is True
    assert ne["formal_equivalence_tested"] is False
    assert ne["abs_full_minus_b02_claim_weighted_pp"] <= 0.05


def test_cosmetic_traces_exist():
    ct = compute_strengthened_claims(ROOT).cosmetics_traces
    assert ct["traced_but_not_supported_rate"] > 0.05
    assert ct["supported_all_have_trace"] is True
    assert ct["n_traced_with_label_unsupported"] == 0


def test_full_seed_range_exceeds_b02():
    si = compute_strengthened_claims(ROOT).seed_instability
    assert si["full"]["range_pp"] > si["B02"]["range_pp"]


def test_bootstrap_ci_includes_zero():
    harm = compute_strengthened_claims(ROOT).task_harm_asymmetry
    lo, hi = harm["bootstrap_95ci_pp"]
    assert lo < 0 < hi
    assert abs(harm["bootstrap_mean_full_minus_b02_pp"]) < 1.0
