from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "docs/research"
V1 = RESEARCH / "V1"


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_v1_is_closed_research_os_arxiv_version():
    current = (RESEARCH / "CURRENT").read_text(encoding="utf-8").strip()
    assert (RESEARCH / current).is_dir()

    status = load_yaml(V1 / "STATUS.yaml")
    assert status["version"] == "V1"
    assert status["status"] == "closed_success"
    assert status["paper_type"] == "arxiv_method_preprint"


def test_v1_names_paper_research_os_not_agenticloop():
    scope = (V1 / "PAPER_SCOPE.md").read_text(encoding="utf-8")
    assert "# Research OS" in scope
    assert "AgenticLoop is the runtime/protocol name" in scope
    assert "paper title is Research OS" in scope
    assert "ResearchLoop" not in scope


def test_v1_declares_three_core_pillars():
    spine = load_yaml(V1 / "RESEARCH_SPINE.yaml")
    pillars = spine["method_pillars"]
    assert [item["id"] for item in pillars] == [
        "RQ_DRIVEN_EXECUTION",
        "EVIDENCE_GATED_CLAIM_ADMISSION",
        "INSIGHT_COMPOUNDING",
    ]


def test_v1_claim_ledger_allows_method_claims_but_blocks_effectiveness_claims():
    ledger = load_yaml(V1 / "PAPER_CLAIM_LEDGER.yaml")
    allowed = {item["claim_id"] for item in ledger["claims"] if item["paper_allowed"] is True}
    blocked = {item["claim_id"] for item in ledger["claims"] if item["paper_allowed"] is False}
    assert {"C_V1_METHOD", "C_V1_RQ_DRIVEN", "C_V1_GATED", "C_V1_INSIGHT", "C_V1_SELF_HOSTING"} <= allowed
    assert {"B_V1_EFFECTIVENESS", "B_V1_GENERALITY", "B_V1_STAT_SIG"} <= blocked


def test_v1_task_queue_starts_with_arxiv_scope_and_skeleton():
    queue = load_yaml(V1 / "TASK_QUEUE.yaml")
    task_ids = [item["id"] for item in queue["tasks"]]
    assert task_ids == [
        "V1_T01",
        "V1_T02",
        "V1_T03",
        "V1_T04",
        "V1_T05",
        "V1_T06",
        "V1_T07",
    ]
    assert queue["queue_status"] == "closed_success"
    assert queue["current_gate"] == "G5_ARXIV_PACKAGE"
    assert queue["current_task"] is None
    completed = [item["id"] for item in queue["tasks"] if item.get("status") == "completed"]
    active = [item["id"] for item in queue["tasks"] if item.get("status") == "active"]
    assert completed == ["V1_T01", "V1_T02", "V1_T03", "V1_T04", "V1_T05", "V1_T06", "V1_T07"]
    assert active == []


def test_v1_paper_has_core_figures_and_bindings():
    figure_dir = V1 / "paper/figures/final"
    assert (figure_dir / "research-os-control-plane.png").exists()
    assert (figure_dir / "rq-to-paper-binding-pipeline.png").exists()
    assert (figure_dir / "claim-admission-state-machine.png").exists()

    design = (V1 / "paper/sections/design.tex").read_text(encoding="utf-8")
    gates = (V1 / "paper/sections/evidence_gates.tex").read_text(encoding="utf-8")
    assert "fig:research-os-control-plane" in design
    assert "fig:rq-to-paper-pipeline" in design
    assert "fig:claim-admission-state-machine" in gates
