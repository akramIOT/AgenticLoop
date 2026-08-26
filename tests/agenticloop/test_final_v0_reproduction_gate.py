from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
V0 = ROOT / "docs/research/V0"


def parse_git_log(path: Path) -> list[str]:
    commits: list[str] = []
    current_hash = None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("commit_hash:"):
            current_hash = stripped.split("commit_hash:", 1)[1].strip()
            if current_hash and current_hash != "none":
                commits.append(current_hash)
    return commits


def test_status_does_not_enter_controlled_runs():
    status = yaml.safe_load((V0 / "STATUS.yaml").read_text(encoding="utf-8"))
    assert status["current_gate"] in {"G0_SEARCH_LOCK", "G1_TASK_SUITE_LOCK", "G2_REPRODUCTION_LOCK"}
    assert status["status"] == "closed_stable"
    assert status["paper_binding"]["allowed"] is False


def test_v0_closes_only_after_all_contract_lock_tasks_complete():
    queue = yaml.safe_load((V0 / "TASK_QUEUE.yaml").read_text(encoding="utf-8"))
    tasks = {item["id"]: item for item in queue["tasks"]}
    required = {"T01", "T02", "T03", "T04", "T05", "RQ01_T001", "RQ02_T001", "RQ03_T001", "RQ04_T001", "RQ05_T001", "RQ06_T001"}
    assert required <= set(tasks)
    for task_id in required:
        assert tasks[task_id]["status"] == "completed", task_id
    gates = {item["gate_id"]: item for item in queue["gates"]}
    assert gates["G0_SEARCH_LOCK"]["status"] == "passed"
    assert gates["G1_REPRODUCTION_LOCK"]["status"] == "passed"


def test_git_log_records_v0_reproduction_commits():
    text = (V0 / "git_log.md").read_text(encoding="utf-8")
    commits = parse_git_log(V0 / "git_log.md")
    assert len(commits) >= 7
    assert "41efc5e" in commits
    assert "98bc1ef" in commits
    assert "0c29726" in commits
    assert len(commits) == len(set(commits))
    for token in ["TASK_1", "TASK_7", "docs(plan): record task 7 completion"]:
        assert token in text
