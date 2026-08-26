import json
from pathlib import Path

import pytest

import oracle


def test_oracle_has_supported_claims():
    assert len(oracle.SUPPORTED_CLAIMS) >= 1
    assert all(isinstance(c, str) for c in oracle.SUPPORTED_CLAIMS)


def test_oracle_has_unsupported_claims():
    assert len(oracle.UNSUPPORTED_CLAIMS) >= 1
    assert all(isinstance(c, str) for c in oracle.UNSUPPORTED_CLAIMS)


def test_oracle_has_required_evidence_paths():
    assert len(oracle.REQUIRED_EVIDENCE_PATHS) >= 1


def test_oracle_check_report_runs():
    result = oracle.check_report("We recommend baseline_config because validation accuracy is primary.")
    assert isinstance(result, dict)
    assert result["recommends_baseline"] is True


def test_workspace_seed_files_exist():
    ws = Path(__file__).resolve().parents[1] / "workspace"
    assert (ws / "baseline_config.yaml").exists()
    assert (ws / "drifted_config.yaml").exists()
    assert (ws / "results_table.csv").exists()
    assert (ws / "methodology_notes.md").exists()
