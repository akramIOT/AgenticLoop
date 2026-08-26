from pathlib import Path

import oracle


def test_oracle_has_supported_claims():
    assert len(oracle.SUPPORTED_CLAIMS) >= 1


def test_oracle_has_unsupported_claims():
    assert len(oracle.UNSUPPORTED_CLAIMS) >= 1


def test_oracle_check_report_runs():
    result = oracle.check_report("Only rq_alpha latency evidence was used.")
    assert result["uses_active_rq_only"] is True


def test_workspace_seed_files_exist():
    ws = Path(__file__).resolve().parents[1] / "workspace"
    assert (ws / "current_rq.yaml").exists()
    assert (ws / "rq_alpha" / "evidence.md").exists()
    assert (ws / "rq_beta" / "evidence.md").exists()
    assert (ws / "cross_reference_warning.md").exists()
