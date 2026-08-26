from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import yaml


@dataclass(frozen=True, slots=True)
class SmokeSpec:
    target_id: str
    dry_run_only: bool
    sandbox_required: bool
    command: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    blocker_policy: str
    claim_support_allowed: bool


def load_smoke_spec(path: Path) -> SmokeSpec:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return SmokeSpec(
        target_id=data["target_id"],
        dry_run_only=bool(data["dry_run_only"]),
        sandbox_required=bool(data["sandbox_required"]),
        command=tuple(data.get("command", ())),
        expected_outputs=tuple(data.get("expected_outputs", ())),
        blocker_policy=data["blocker_policy"],
        claim_support_allowed=bool(data["claim_support_allowed"]),
    )


def build_dry_run_report(spec: SmokeSpec, repo_root: Path) -> dict:
    command = spec.command or ("python", "experiments/agenticloop/scripts/smoke_harness.py", "--target", spec.target_id, "--dry-run")
    cwd = str(repo_root)
    return {
        "target_id": spec.target_id,
        "is_mock": True,
        "claim_support_allowed": False,
        "command": command,
        "cwd": cwd,
        "env": {"SMOKE_DRY_RUN": "1", "SMOKE_TARGET_ID": spec.target_id},
        "expected_outputs": spec.expected_outputs,
        "blocker_policy": spec.blocker_policy,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a truthful dry-run smoke report.")
    parser.add_argument("--target", required=True)
    parser.add_argument("--dry-run", action="store_true", help="Emit a dry-run report")
    parser.add_argument("--spec", type=Path, default=None, help="Optional smoke spec path")
    args = parser.parse_args(argv)

    if not args.dry_run:
        parser.error("only --dry-run is supported")

    if args.spec is None:
        spec_path = Path("docs/research/V0/reproduction/smoke_specs") / f"{args.target}.yaml"
    else:
        spec_path = args.spec
    spec = load_smoke_spec(spec_path)
    report = build_dry_run_report(spec, Path.cwd())
    print(yaml.safe_dump(report, sort_keys=False, allow_unicode=True), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
