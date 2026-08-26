import json
import subprocess
import sys
from pathlib import Path

import yaml

from experiments.agenticloop.scripts.audit_sources import audit_v0_sources


ROOT = Path(__file__).resolve().parents[2]


def test_audit_v0_sources_passes_current_dossier():
    result = audit_v0_sources(ROOT)
    assert result.errors == ()
    assert result.checked_files


def test_cli_outputs_json_summary():
    completed = subprocess.run(
        [sys.executable, "experiments/agenticloop/scripts/audit_sources.py", "--repo", str(ROOT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert set(payload) == {"checked_files", "errors", "warnings"}


def test_audit_rejects_missing_source_refs(tmp_path):
    card_dir = tmp_path / "docs/research/V0/baselines/BAD"
    card_dir.mkdir(parents=True)
    (tmp_path / "docs/research/V0/baselines").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs/research/V0/baselines/INDEX.yaml").write_text(
        yaml.safe_dump({"baselines": [{"card_ref": "docs/research/V0/baselines/BAD/BASELINE_CARD.yaml"}]}),
        encoding="utf-8",
    )
    (card_dir / "BASELINE_CARD.yaml").write_text(
        yaml.safe_dump({"baseline_id": "BAD", "paper_claim_support_allowed": False, "source_refs": []}),
        encoding="utf-8",
    )
    result = audit_v0_sources(tmp_path)
    assert any("source_refs" in error for error in result.errors)


def test_audit_rejects_claim_supporting_reproduction_ledger(tmp_path):
    ledger_dir = tmp_path / "docs/research/V0/reproduction"
    ledger_dir.mkdir(parents=True)
    (ledger_dir / "REPRODUCTION_LEDGER.yaml").write_text(
        yaml.safe_dump({"assets": [{"target_id": "BAD", "paper_claim_support_allowed": True}]}),
        encoding="utf-8",
    )
    result = audit_v0_sources(tmp_path)
    assert any("paper_claim_support_allowed" in error for error in result.errors)


def test_g2_reproduction_audit_file_records_command():
    audit_path = ROOT / "docs/research/V0/audits/G2_reproduction_audit.yaml"
    payload = yaml.safe_load(audit_path.read_text(encoding="utf-8"))
    assert payload["audit_id"] == "G2_REPRODUCTION_AUDIT"
    assert "audit_sources.py" in payload["command"]
