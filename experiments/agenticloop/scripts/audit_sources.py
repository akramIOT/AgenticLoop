from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True, slots=True)
class AuditResult:
    checked_files: tuple[str, ...]
    errors: tuple[str, ...]
    warnings: tuple[str, ...]


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def _as_str_tuple(values: object) -> tuple[str, ...]:
    if not isinstance(values, list):
        return ()
    return tuple(v for v in values if isinstance(v, str))


def audit_v0_sources(repo_root: Path) -> AuditResult:
    checked: list[str] = []
    errors: list[str] = []
    warnings: list[str] = []

    baseline_index = repo_root / "docs/research/V0/baselines/INDEX.yaml"
    checked.append(str(baseline_index.relative_to(repo_root)))
    if baseline_index.exists():
        index_data = _load_yaml(baseline_index)
        for item in index_data.get("baselines", []):
            card_ref = item.get("card_ref") if isinstance(item, dict) else None
            if not card_ref:
                errors.append("baseline index entry missing card_ref")
                continue
            card_path = repo_root / card_ref
            checked.append(str(card_path.relative_to(repo_root)))
            if not card_path.exists():
                errors.append(f"missing baseline card: {card_ref}")
                continue
            card = _load_yaml(card_path)
            source_refs = _as_str_tuple(card.get("source_refs"))
            if not source_refs:
                errors.append(f"baseline card missing source_refs: {card_ref}")
            if card.get("paper_claim_support_allowed") is True:
                errors.append(f"baseline card paper_claim_support_allowed=true: {card_ref}")
    else:
        errors.append(f"missing required file: {baseline_index.relative_to(repo_root)}")

    ledger_path = repo_root / "docs/research/V0/reproduction/REPRODUCTION_LEDGER.yaml"
    checked.append(str(ledger_path.relative_to(repo_root)))
    if ledger_path.exists():
        ledger = _load_yaml(ledger_path)
        for asset in ledger.get("assets", []):
            if not isinstance(asset, dict):
                continue
            if asset.get("paper_claim_support_allowed") is True:
                errors.append(f"reproduction ledger item paper_claim_support_allowed=true: {asset.get('target_id', '<unknown>')}")
    else:
        warnings.append(f"missing optional file: {ledger_path.relative_to(repo_root)}")

    targets_path = repo_root / "docs/research/V0/reproduction/reproduction_targets.yaml"
    checked.append(str(targets_path.relative_to(repo_root)))
    if targets_path.exists():
        targets = _load_yaml(targets_path)
        for target in targets.get("targets", []):
            if not isinstance(target, dict):
                continue
            if not _as_str_tuple(target.get("source_refs")):
                errors.append(f"reproduction target missing source_refs: {target.get('target_id', '<unknown>')}")
            if target.get("claim_support_allowed") is True:
                errors.append(f"reproduction target claim_support_allowed=true: {target.get('target_id', '<unknown>')}")
    else:
        warnings.append(f"missing optional file: {targets_path.relative_to(repo_root)}")

    return AuditResult(checked_files=tuple(checked), errors=tuple(errors), warnings=tuple(warnings))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    args = parser.parse_args(argv)
    result = audit_v0_sources(Path(args.repo))
    print(json.dumps({"checked_files": result.checked_files, "errors": result.errors, "warnings": result.warnings}, ensure_ascii=False))
    return 0 if not result.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
