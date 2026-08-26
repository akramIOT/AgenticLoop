"""Tests for core research-direction analyses."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
import sys

sys.path.insert(0, str(ROOT / "src"))

from agenticloop.core_directions import compute_core_directions, write_core_direction_artifacts


def test_three_directions_present():
    analysis = compute_core_directions(ROOT)
    ids = {d["id"] for d in analysis.research_directions}
    assert "RD1_error_propagation_recovery" in ids
    assert "RD2_token_cost_efficiency" in ids
    assert "RD3_semantic_convergence_stopping" in ids
    assert analysis.schema_version == 1


def test_cascade_lift_greater_than_one():
    ep = compute_core_directions(ROOT).error_propagation
    assert ep["cascade_lift"] is not None
    assert ep["cascade_lift"] > 1.5
    assert ep["recovery_rate_any_supported_after_first_bad"] > 0.8


def test_full_less_token_efficient_than_b01():
    cost = compute_core_directions(ROOT).token_cost_efficiency
    b01 = cost["v6_proxy_by_condition"]["B01"]["quality_per_1k_proxy_tokens"]
    full = cost["v6_proxy_by_condition"]["full"]["quality_per_1k_proxy_tokens"]
    assert b01 > full
    assert cost["real_token_calibration"]["n_transcripts"] >= 1


def test_early_stop_saves_claims():
    conv = compute_core_directions(ROOT).semantic_convergence
    sim = conv["early_stop_simulation"]
    assert sim["claims_saved_vs_full"] > 0
    assert abs(sim["ur_delta_early_minus_full_pp"]) < 5.0  # UR roughly preserved


def test_write_artifacts(tmp_path=None):
    paths = write_core_direction_artifacts(ROOT)
    assert paths["json"].exists()
    assert paths["md"].exists()
