from pathlib import Path

import pytest
import yaml

from experiments.agenticloop.scripts.reproduction_registry import (
    ReproductionTarget,
    load_reproduction_targets,
    validate_reproduction_targets,
)


def write_registry(tmp_path: Path, targets: list[dict]) -> Path:
    path = tmp_path / "reproduction_targets.yaml"
    path.write_text(yaml.safe_dump({"schema_version": 1, "targets": targets}, allow_unicode=True), encoding="utf-8")
    return path


def valid_target(**overrides):
    payload = {
        "target_id": "AGENT_LABORATORY",
        "priority": "P0",
        "related_work": "Agent Laboratory",
        "baseline_role": "linear research-agent baseline",
        "source_refs": ["https://github.com/SamuelSchmidgall/AgentLaboratory"],
        "reproduction_mode": "official_code_smoke",
        "smoke_command": "python -m pytest tests/agenticloop/test_reproduction_registry.py -v",
        "blocker_policy": "If the official flow cannot run in the sandbox, record blocked_missing_environment.",
        "claim_support_allowed": False,
    }
    payload.update(overrides)
    return payload


def test_load_reproduction_targets_returns_dataclass_instances(tmp_path):
    path = write_registry(
        tmp_path,
        [
            valid_target(),
            valid_target(
                target_id="AI_SCIENTIST_V2",
                related_work="AI Scientist-v2",
                baseline_role="strong adjacent",
                source_refs=["https://github.com/SakanaAI/AI-Scientist-v2", "https://arxiv.org/abs/2504.08066"],
            ),
            valid_target(
                target_id="PROVENANCE_ONLY",
                related_work="MLflow/DVC",
                baseline_role="provenance control",
                source_refs=["https://mlflow.org/docs/latest/", "https://dvc.org/doc"],
                reproduction_mode="conceptual_control",
                smoke_command=None,
            ),
        ],
    )
    targets = load_reproduction_targets(path)
    assert targets == [
        ReproductionTarget(
            target_id="AGENT_LABORATORY",
            priority="P0",
            related_work="Agent Laboratory",
            baseline_role="linear research-agent baseline",
            source_refs=("https://github.com/SamuelSchmidgall/AgentLaboratory",),
            reproduction_mode="official_code_smoke",
            smoke_command="python -m pytest tests/agenticloop/test_reproduction_registry.py -v",
            blocker_policy="If the official flow cannot run in the sandbox, record blocked_missing_environment.",
            claim_support_allowed=False,
        ),
        ReproductionTarget(
            target_id="AI_SCIENTIST_V2",
            priority="P0",
            related_work="AI Scientist-v2",
            baseline_role="strong adjacent",
            source_refs=("https://github.com/SakanaAI/AI-Scientist-v2", "https://arxiv.org/abs/2504.08066"),
            reproduction_mode="official_code_smoke",
            smoke_command="python -m pytest tests/agenticloop/test_reproduction_registry.py -v",
            blocker_policy="If the official flow cannot run in the sandbox, record blocked_missing_environment.",
            claim_support_allowed=False,
        ),
        ReproductionTarget(
            target_id="PROVENANCE_ONLY",
            priority="P0",
            related_work="MLflow/DVC",
            baseline_role="provenance control",
            source_refs=("https://mlflow.org/docs/latest/", "https://dvc.org/doc"),
            reproduction_mode="conceptual_control",
            smoke_command=None,
            blocker_policy="If the official flow cannot run in the sandbox, record blocked_missing_environment.",
            claim_support_allowed=False,
        ),
    ]


@pytest.mark.parametrize("field", ["target_id", "priority", "source_refs", "reproduction_mode", "claim_support_allowed"])
def test_validate_rejects_missing_required_fields(tmp_path, field):
    target = valid_target()
    target.pop(field)
    path = write_registry(tmp_path, [target])
    with pytest.raises(ValueError, match=field):
        load_reproduction_targets(path)


@pytest.mark.parametrize("field", ["target_id", "related_work", "baseline_role", "reproduction_mode", "blocker_policy"])
def test_validate_rejects_blank_string_fields(tmp_path, field):
    path = write_registry(tmp_path, [valid_target(**{field: "   "})])
    with pytest.raises(ValueError, match="non-blank string"):
        load_reproduction_targets(path)


def test_validate_rejects_unknown_priority(tmp_path):
    path = write_registry(tmp_path, [valid_target(priority="P9")])
    with pytest.raises(ValueError, match="priority"):
        load_reproduction_targets(path)


def test_validate_rejects_unknown_reproduction_mode(tmp_path):
    path = write_registry(tmp_path, [valid_target(reproduction_mode="full_experiment")])
    with pytest.raises(ValueError, match="reproduction_mode"):
        load_reproduction_targets(path)


def test_validate_rejects_claim_supporting_v0_targets(tmp_path):
    path = write_registry(tmp_path, [valid_target(claim_support_allowed=True)])
    with pytest.raises(ValueError, match="claim_support_allowed"):
        load_reproduction_targets(path)


@pytest.mark.parametrize("source_refs", [[], ["   "]])
def test_validate_rejects_blank_or_empty_source_refs(tmp_path, source_refs):
    path = write_registry(tmp_path, [valid_target(source_refs=source_refs)])
    with pytest.raises(ValueError, match="source_refs"):
        load_reproduction_targets(path)


def test_validate_requires_p0_core_targets():
    targets = [
        ReproductionTarget("AGENT_LABORATORY", "P0", "Agent Laboratory", "linear", ("https://example.com/a",), "official_code_smoke", None, "record blocker", False),
        ReproductionTarget("AI_SCIENTIST_V2", "P0", "AI Scientist-v2", "strong adjacent", ("https://example.com/b",), "official_code_smoke", None, "requires sandbox", False),
        ReproductionTarget("PROVENANCE_ONLY", "P0", "MLflow/DVC", "provenance control", ("https://example.com/c",), "conceptual_control", None, "provenance only", False),
    ]
    assert validate_reproduction_targets(targets) == []


def test_validate_rejects_missing_core_p0_target():
    targets = [
        ReproductionTarget("AGENT_LABORATORY", "P0", "Agent Laboratory", "linear", ("https://example.com/a",), "official_code_smoke", None, "record blocker", False),
        ReproductionTarget("AI_SCIENTIST_V2", "P0", "AI Scientist-v2", "strong adjacent", ("https://example.com/b",), "official_code_smoke", None, "requires sandbox", False),
    ]
    assert "missing required P0 targets" in validate_reproduction_targets(targets)[0]


def test_loads_actual_repo_reproduction_registry():
    path = Path("docs/research/V0/reproduction/reproduction_targets.yaml")
    targets = load_reproduction_targets(path)
    assert [target.target_id for target in targets] == [
        "AGENT_LABORATORY",
        "AI_SCIENTIST_V2",
        "PROVENANCE_ONLY",
        "STORM_GROUNDED_WRITING",
        "PAPERQA2_LITERATURE_RAG",
        "OPENEVOLVE_EVALUATOR",
        "ALPHAEVOLVE_OFFICIAL",
    ]
