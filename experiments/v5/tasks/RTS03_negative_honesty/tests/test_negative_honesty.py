from pathlib import Path

import oracle


def test_oracle_has_supported_claims():
    assert len(oracle.SUPPORTED_CLAIMS) >= 1


def test_oracle_has_unsupported_claims():
    assert len(oracle.UNSUPPORTED_CLAIMS) >= 1


def test_oracle_check_report_runs():
    result = oracle.check_report("The target was not achieved.")
    assert result["states_failure"] is True


def test_workspace_seed_files_exist():
    ws = Path(__file__).resolve().parents[1] / "workspace"
    assert (ws / "target_spec.yaml").exists()
    assert (ws / "experiment_log.json").exists()
    assert (ws / "negative_result_summary.md").exists()
