"""Tests for extended research-point analyses."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from agenticloop.analysis_ext import compute_extended_analysis, verify_paper_numbers


def test_extended_analysis_has_twelve_research_points():
    analysis = compute_extended_analysis(ROOT)
    ids = {rp["id"] for rp in analysis.research_points}
    assert "RP1_claim_volume" in ids
    assert "RP7_temperature_profile" in ids
    assert "RP9_pairwise_wins" in ids
    assert "RP12_ablation_volume" in ids
    assert len(analysis.research_points) >= 12


def test_gate_redundancy_near_one():
    gr = compute_extended_analysis(ROOT).gate_redundancy
    assert gr["gate_redundancy_index"] >= 0.99
    assert abs(gr["gate_extra_over_linear_pp"]) < 0.05


def test_claim_volume_full_exceeds_b01():
    cv = compute_extended_analysis(ROOT).claim_volume
    assert cv["full"]["claims_per_run"] > cv["B01"]["claims_per_run"]
    assert cv["ratios"]["full_over_b01_claims_per_run"] > 2.0


def test_pairwise_wins_do_not_favor_full():
    wins = compute_extended_analysis(ROOT).pairwise_wins
    assert wins["full_worse_than_b01"] >= wins["full_better_than_b01"]


def test_provenance_verify_passes():
    assert verify_paper_numbers(ROOT)["ok"] is True
