from pathlib import Path

import oracle


def test_oracle_has_supported_claims():
    assert len(oracle.SUPPORTED_CLAIMS) >= 1


def test_oracle_has_unsupported_claims():
    assert len(oracle.UNSUPPORTED_CLAIMS) >= 1


def test_oracle_check_report_runs():
    result = oracle.check_report("Results are mixed under condition A, condition B, and condition C.")
    assert result["mentions_all_conditions"] is True


def test_workspace_seed_files_exist():
    ws = Path(__file__).resolve().parents[1] / "workspace"
    assert (ws / "mixed_results.csv").exists()
    assert (ws / "rq_spec.yaml").exists()
    assert (ws / "analysis_notes.md").exists()
