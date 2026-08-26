from pathlib import Path

from experiments.agenticloop.scripts.smoke_harness import build_dry_run_report, load_smoke_spec, main


ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = ROOT / "docs/research/V0/reproduction/smoke_specs"


def test_p0_smoke_specs_exist():
    for target_id in ["AGENT_LABORATORY", "AI_SCIENTIST_V2", "PROVENANCE_ONLY"]:
        assert (SPEC_DIR / f"{target_id}.yaml").exists()


def test_smoke_specs_are_dry_run_and_not_claim_supporting():
    for path in SPEC_DIR.glob("*.yaml"):
        spec = load_smoke_spec(path)
        assert spec.dry_run_only is True
        assert spec.claim_support_allowed is False


def test_ai_scientist_v2_requires_sandbox():
    spec = load_smoke_spec(SPEC_DIR / "AI_SCIENTIST_V2.yaml")
    assert spec.sandbox_required is True


def test_provenance_only_declares_claim_admission_gap():
    spec = load_smoke_spec(SPEC_DIR / "PROVENANCE_ONLY.yaml")
    assert "paper claim admission" in spec.blocker_policy


def test_dry_run_report_marks_mock_and_forbids_claim_support():
    spec = load_smoke_spec(SPEC_DIR / "AGENT_LABORATORY.yaml")
    report = build_dry_run_report(spec, ROOT)
    assert report["target_id"] == "AGENT_LABORATORY"
    assert report["is_mock"] is True
    assert report["claim_support_allowed"] is False
    assert report["command"]
    assert report["expected_outputs"]


def test_cli_emits_truthful_dry_run_report(tmp_path, capsys):
    spec_path = SPEC_DIR / "AGENT_LABORATORY.yaml"
    exit_code = main(["--target", "AGENT_LABORATORY", "--dry-run", "--spec", str(spec_path)])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "AGENT_LABORATORY" in out
    assert "SMOKE_DRY_RUN" in out
