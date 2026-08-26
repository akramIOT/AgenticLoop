from pathlib import Path

import oracle


def test_oracle_has_supported_claims():
    assert len(oracle.SUPPORTED_CLAIMS) >= 1


def test_oracle_has_unsupported_claims():
    assert len(oracle.UNSUPPORTED_CLAIMS) >= 1


def test_oracle_check_report_runs():
    result = oracle.check_report("Smith2024 and Chen2023 are verified sources.")
    assert result["cites_verified_only"] is True


def test_workspace_seed_files_exist():
    ws = Path(__file__).resolve().parents[1] / "workspace"
    assert (ws / "source_audit_log.yaml").exists()
    assert (ws / "verified_sources.bib").exists()
    assert (ws / "unverified_dossier.md").exists()
    assert (ws / "draft_paragraph.md").exists()
