from pathlib import Path

import oracle


def test_oracle_has_supported_claims():
    assert len(oracle.SUPPORTED_CLAIMS) >= 1


def test_oracle_has_unsupported_claims():
    assert len(oracle.UNSUPPORTED_CLAIMS) >= 1


def test_oracle_check_report_runs():
    result = oracle.check_report("We used real_experiment only.")
    assert result["cites_real_only"] is True


def test_workspace_seed_files_exist():
    ws = Path(__file__).resolve().parents[1] / "workspace"
    assert (ws / "data_manifest.yaml").exists()
    assert (ws / "real_experiment" / "results.json").exists()
    assert (ws / "mock_experiment" / "results.json").exists()
    assert (ws / "report_draft.md").exists()
