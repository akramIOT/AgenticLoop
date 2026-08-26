from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
V0 = ROOT / "docs/research/V0"


def test_baseline_landscape_names_p0_targets():
    text = (V0 / "wiki/baseline_landscape.md").read_text(encoding="utf-8")
    for token in ["ad-hoc prompting", "Agent Laboratory", "AI Scientist-v2", "MLflow", "DVC"]:
        assert token in text


def test_evidence_map_distinguishes_source_smoke_and_full_reproduction():
    text = (V0 / "wiki/evidence_map.md").read_text(encoding="utf-8")
    for token in ["source dossier", "dry-run", "smoke", "full reproduction"]:
        assert token in text
    assert "smoke 不支持 paper claim" in text


def test_failed_paths_records_alphaevolve_boundary():
    text = (V0 / "wiki/failed_paths.md").read_text(encoding="utf-8")
    assert "AlphaEvolve" in text
    assert "closed-source" in text or "source-only" in text
    for token in ["Sandbox risk", "Provenance/control mismatch", "STORM/PaperQA2 non-experimental risk"]:
        assert token in text


def test_no_paper_claim_allowed_after_v0_reproduction_lock():
    ledger = yaml.safe_load((V0 / "PAPER_CLAIM_LEDGER.yaml").read_text(encoding="utf-8"))
    assert all(item["paper_allowed"] is False for item in ledger["claims"])
