from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import yaml

Priority = Literal["P0", "P1", "P2"]
ReproductionMode = Literal[
    "official_code_smoke",
    "paper_based_adaptation",
    "conceptual_control",
    "source_dossier_only",
    "blocked_closed_source",
]


@dataclass(frozen=True, slots=True)
class ReproductionTarget:
    target_id: str
    priority: Priority
    related_work: str
    baseline_role: str
    source_refs: tuple[str, ...]
    reproduction_mode: ReproductionMode
    smoke_command: str | None
    blocker_policy: str
    claim_support_allowed: bool


def _validate_required_fields(raw: dict) -> None:
    required = ["target_id", "priority", "related_work", "baseline_role", "source_refs", "reproduction_mode", "blocker_policy", "claim_support_allowed"]
    missing = [field for field in required if field not in raw]
    if missing:
        raise ValueError(f"missing required field(s): {', '.join(missing)}")


def _validate_non_blank_string(field: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-blank string")


def validate_reproduction_targets(targets: list[ReproductionTarget]) -> list[str]:
    errors: list[str] = []
    allowed_priorities = {"P0", "P1", "P2"}
    allowed_modes = {"official_code_smoke", "paper_based_adaptation", "conceptual_control", "source_dossier_only", "blocked_closed_source"}
    p0_required = {"AGENT_LABORATORY", "AI_SCIENTIST_V2", "PROVENANCE_ONLY"}

    seen_p0 = {t.target_id for t in targets if t.priority == "P0"}
    missing_p0 = sorted(p0_required - seen_p0)
    if missing_p0:
        errors.append(f"missing required P0 targets: {', '.join(missing_p0)}")

    for target in targets:
        if target.priority not in allowed_priorities:
            errors.append(f"invalid priority for {target.target_id}: {target.priority}")
        if target.reproduction_mode not in allowed_modes:
            errors.append(f"invalid reproduction_mode for {target.target_id}: {target.reproduction_mode}")
        if target.claim_support_allowed:
            errors.append(f"claim_support_allowed must be false for {target.target_id}")
        for field_name, value in (
            ("target_id", target.target_id),
            ("related_work", target.related_work),
            ("baseline_role", target.baseline_role),
            ("reproduction_mode", target.reproduction_mode),
            ("blocker_policy", target.blocker_policy),
        ):
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{field_name} must be a non-blank string for {target.target_id or '<unknown>'}")
        if not target.source_refs or any(not isinstance(ref, str) or not ref.strip() for ref in target.source_refs):
            errors.append(f"source_refs must contain at least one non-blank URL string for {target.target_id}")
    return errors


def load_reproduction_targets(path: Path) -> list[ReproductionTarget]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    targets_data = data.get("targets", [])
    targets: list[ReproductionTarget] = []
    for raw in targets_data:
        if not isinstance(raw, dict):
            raise ValueError("target must be a mapping")
        _validate_required_fields(raw)
        for field in ["target_id", "priority", "related_work", "baseline_role", "reproduction_mode", "blocker_policy"]:
            _validate_non_blank_string(field, raw[field])
        target = ReproductionTarget(
            target_id=raw["target_id"],
            priority=raw["priority"],
            related_work=raw["related_work"],
            baseline_role=raw["baseline_role"],
            source_refs=tuple(raw["source_refs"]),
            reproduction_mode=raw["reproduction_mode"],
            smoke_command=raw.get("smoke_command"),
            blocker_policy=raw["blocker_policy"],
            claim_support_allowed=raw["claim_support_allowed"],
        )
        targets.append(target)
    errors = validate_reproduction_targets(targets)
    if errors:
        raise ValueError("; ".join(errors))
    return targets
