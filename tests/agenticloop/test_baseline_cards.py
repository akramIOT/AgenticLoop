from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
BASELINES = ROOT / "docs/research/V0/baselines"
BASELINE_LOCK = ROOT / "docs/research/V0/BASELINE_LOCK.yaml"
CANDIDATE_BASELINES = ROOT / "docs/research/V0/search/candidate_baselines.yaml"


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def card_paths():
    index = load_yaml(BASELINES / "INDEX.yaml")
    return [ROOT / entry["card_ref"] for entry in index["baselines"]]


def test_baseline_index_references_existing_cards():
    paths = card_paths()
    assert paths
    for path in paths:
        assert path.exists(), path


def test_each_baseline_card_has_required_fields():
    required = {
        "baseline_id",
        "related_work",
        "priority",
        "source_refs",
        "role_in_researchos_eval",
        "reproduction_feasibility",
        "claim_boundary",
        "paper_claim_support_allowed",
    }
    for path in card_paths():
        card = load_yaml(path)
        assert required <= set(card), path
        assert card["paper_claim_support_allowed"] is False
        assert card["source_refs"], path


def test_baseline_lock_contains_p0_core_candidates():
    lock = load_yaml(BASELINE_LOCK)
    ids = {item["baseline_id"] for item in lock["candidate_baselines"]}
    assert {"B01_ADHOC_AGENT", "B02_AGENT_LABORATORY", "B02_AI_SCIENTIST_V2", "B03_PROVENANCE_ONLY"} <= ids


def test_adhoc_agent_card_exists_and_is_non_claim_supporting():
    card = load_yaml(BASELINES / "B01_ADHOC_AGENT/BASELINE_CARD.yaml")
    assert card["paper_claim_support_allowed"] is False
    assert card["reproduction_feasibility"]["default_full_run_allowed"] is False


def test_candidate_baselines_explains_adhoc_control_traceability():
    payload = load_yaml(CANDIDATE_BASELINES)
    notes = payload.get("notes", [])
    assert any("B01_ADHOC_AGENT" in note for note in notes)


def test_ai_scientist_v2_requires_sandbox_and_blocks_default_full_run():
    card = load_yaml(BASELINES / "B02_AI_SCIENTIST_V2/BASELINE_CARD.yaml")
    assert card["reproduction_feasibility"]["sandbox_required"] is True
    assert card["reproduction_feasibility"]["default_full_run_allowed"] is False


def test_writing_controls_are_not_experimental_research_agent_baselines():
    for baseline_id in ["B04_STORM_GROUNDED_WRITING", "B04_PAPERQA2_LITERATURE_RAG"]:
        card = load_yaml(BASELINES / baseline_id / "BASELINE_CARD.yaml")
        assert card["role_in_researchos_eval"] in {"grounded_writing_control", "literature_rag_control"}
        assert card["claim_boundary"]["supports_experimental_claim"] is False


def test_openevolve_is_conditional_on_code_optimization_task_suite():
    card = load_yaml(BASELINES / "B05_OPENEVOLVE_EVALUATOR/BASELINE_CARD.yaml")
    assert card["activation_condition"] == "only_if_task_suite_contains_code_optimization"


def test_alphaevolve_official_is_not_a_runnable_v0_baseline_if_recorded():
    alpha_path = BASELINES / "P2_ALPHAEVOLVE_OFFICIAL/BASELINE_CARD.yaml"
    if alpha_path.exists():
        card = load_yaml(alpha_path)
        assert card["reproduction_feasibility"]["status"] in {"source_dossier_only", "blocked_closed_source"}
        assert card["paper_claim_support_allowed"] is False
