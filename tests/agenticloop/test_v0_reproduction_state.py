from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
V0 = ROOT / "docs/research/V0"


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_reproduction_plan_lists_p0_execution_order():
    text = (V0 / "reproduction/REPRODUCTION_PLAN.md").read_text(encoding="utf-8")
    assert "AGENT_LABORATORY" in text
    assert "AI_SCIENTIST_V2" in text
    assert "PROVENANCE_ONLY" in text
    assert text.index("AGENT_LABORATORY") < text.index("AI_SCIENTIST_V2") < text.index("PROVENANCE_ONLY")


def test_reproduction_ledger_forbids_paper_claim_support_for_p0():
    ledger = load_yaml(V0 / "reproduction/REPRODUCTION_LEDGER.yaml")
    assets = {item["target_id"]: item for item in ledger["assets"]}
    for target_id in ["AGENT_LABORATORY", "AI_SCIENTIST_V2", "PROVENANCE_ONLY"]:
        assert assets[target_id]["paper_claim_support_allowed"] is False


def test_task_queue_expands_t05_reproduction_subtasks():
    queue = load_yaml(V0 / "TASK_QUEUE.yaml")
    task = next(item for item in queue["tasks"] if item["id"] == "T05")
    subtask_ids = {item["id"] for item in task["subtasks"]}
    assert {"T05_AGENT_LABORATORY", "T05_AI_SCIENTIST_V2", "T05_PROVENANCE_ONLY"} <= subtask_ids


def test_later_gates_remain_blocked():
    queue = load_yaml(V0 / "TASK_QUEUE.yaml")
    gates = {item["gate_id"]: item["status"] for item in queue["gates"]}
    for gate_id in ["G3_CONTROLLED_RUNS", "G4_EVIDENCE_AUDIT", "G5_REAL_CASE_STUDY", "G6_SELF_HOSTING", "G7_PAPER_BINDING"]:
        assert gates[gate_id] == "blocked"


def test_audit_queue_contains_g2_reproduction_audit():
    audit = load_yaml(V0 / "AUDIT_QUEUE.yaml")
    audit_ids = {item["audit_id"] for item in audit["audits"]}
    assert "G2_REPRODUCTION_AUDIT" in audit_ids


def test_reproduction_index_resolves_target_refs():
    index = load_yaml(V0 / "reproduction/REPRODUCTION_INDEX.yaml")
    for item in index["targets"]:
        for ref_name in ["card_ref", "smoke_spec_ref", "ledger_ref"]:
            assert (V0 / item[ref_name]).exists(), item


def test_research_direction_is_frozen_for_v0_closeout():
    direction = (ROOT / "docs/research/RESEARCH_DIRECTION.md").read_text(encoding="utf-8")
    assert "- status: frozen" in direction or "- status: human_approved" in direction
    assert "- owner_decision_required: false" in direction


def test_rq_local_task_status_matches_main_queue():
    queue = load_yaml(V0 / "TASK_QUEUE.yaml")
    main_status = {item["id"]: item["status"] for item in queue["tasks"]}
    for tasks_path in sorted((V0 / "rqs").glob("RQ*/TASKS.yaml")):
        local = load_yaml(tasks_path)
        for task in local["tasks"]:
            task_id = task.get("task_id", task.get("id"))
            if task_id in main_status:
                assert task["status"] == main_status[task_id], f"{tasks_path}: {task_id}"
