"""Core research-direction analyses for long-horizon agentic loops.

Directions (operationalized on durable V5/V6 artifacts; no new model runs):
  RD1 Error propagation & recovery dynamics
  RD2 Token / cost efficiency benchmarks
  RD3 Semantic convergence & stopping criteria

V6 T05 audits are single-response claim sequences (ordered claim lists), not
multi-turn tool loops. Metrics below treat claim ordinal position as a proxy
for within-report iteration order. V5 transcripts supply real token usage for
cost calibration.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Any


def _repo_root(start: Path | None = None) -> Path:
    if start is None:
        start = Path(__file__).resolve()
    for parent in [start, *start.parents]:
        if (parent / "docs" / "research" / "CURRENT").exists():
            return parent
    return Path(__file__).resolve().parents[2]


def _is_bad(label: str) -> bool:
    return label != "supported"


@dataclass(frozen=True)
class CoreDirectionsAnalysis:
    schema_version: int
    error_propagation: dict[str, Any]
    token_cost_efficiency: dict[str, Any]
    semantic_convergence: dict[str, Any]
    research_directions: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _error_propagation(audits: list[dict[str, Any]]) -> dict[str, Any]:
    trans_bad_given_bad = 0
    trans_tot_bad = 0
    trans_bad_given_good = 0
    trans_tot_good = 0
    recover_any = 0
    recover_den = 0
    later_supported_frac: list[float] = []
    stuck_runs = 0  # ≥2 consecutive bad with no later recovery
    by_cond: dict[str, dict[str, Any]] = {}

    cond_stats: dict[str, dict[str, list]] = defaultdict(
        lambda: {"cascade_p": [], "recover": [], "later_frac": []}
    )

    for a in audits:
        labs = [c["label"] for c in a.get("claim_labels", [])]
        cond = a.get("condition_id", "?")
        if len(labs) < 2:
            continue
        local_bad_trans = 0
        local_bad_tot = 0
        for i in range(len(labs) - 1):
            if _is_bad(labs[i]):
                trans_tot_bad += 1
                local_bad_tot += 1
                if _is_bad(labs[i + 1]):
                    trans_bad_given_bad += 1
                    local_bad_trans += 1
            else:
                trans_tot_good += 1
                if _is_bad(labs[i + 1]):
                    trans_bad_given_good += 1
        if local_bad_tot:
            cond_stats[cond]["cascade_p"].append(local_bad_trans / local_bad_tot)

        try:
            first = next(i for i, lab in enumerate(labs) if _is_bad(lab))
        except StopIteration:
            continue
        later = labs[first + 1 :]
        if not later:
            continue
        recover_den += 1
        recovered = any(not _is_bad(lab) for lab in later)
        if recovered:
            recover_any += 1
            cond_stats[cond]["recover"].append(1.0)
        else:
            stuck_runs += 1
            cond_stats[cond]["recover"].append(0.0)
        frac = sum(1 for lab in later if not _is_bad(lab)) / len(later)
        later_supported_frac.append(frac)
        cond_stats[cond]["later_frac"].append(frac)

    for cond, st in cond_stats.items():
        by_cond[cond] = {
            "mean_cascade_p_given_bad_prefix": round(mean(st["cascade_p"]), 4) if st["cascade_p"] else None,
            "recovery_rate": round(mean(st["recover"]), 4) if st["recover"] else None,
            "mean_later_supported_frac": round(mean(st["later_frac"]), 4) if st["later_frac"] else None,
            "n_cascade_runs": len(st["cascade_p"]),
            "n_recovery_runs": len(st["recover"]),
        }

    p_cascade = (trans_bad_given_bad / trans_tot_bad) if trans_tot_bad else None
    p_from_good = (trans_bad_given_good / trans_tot_good) if trans_tot_good else None
    lift = (p_cascade / p_from_good) if (p_cascade is not None and p_from_good and p_from_good > 0) else None

    return {
        "unit": "ordered_claim_sequence_within_report",
        "n_audits": len(audits),
        "p_unsupported_given_prev_unsupported": round(p_cascade, 4) if p_cascade is not None else None,
        "p_unsupported_given_prev_supported": round(p_from_good, 4) if p_from_good is not None else None,
        "cascade_lift": round(lift, 4) if lift is not None else None,
        "n_transitions_after_unsupported": trans_tot_bad,
        "n_transitions_after_supported": trans_tot_good,
        "recovery_rate_any_supported_after_first_bad": round(recover_any / recover_den, 4)
        if recover_den
        else None,
        "mean_later_supported_fraction": round(mean(later_supported_frac), 4)
        if later_supported_frac
        else None,
        "stuck_no_recovery_runs": stuck_runs,
        "n_runs_with_unsupported": recover_den,
        "by_condition": by_cond,
        "interpretation": (
            "Cascade lift >1 means unsupported claims raise the odds the next claim is also "
            "unsupported; recovery_rate measures self-correction after the first failure."
        ),
    }


def _token_cost_efficiency(audits: list[dict[str, Any]], root: Path) -> dict[str, Any]:
    # Real tokens from V5 transcripts (available manifests)
    real_tokens: list[dict[str, Any]] = []
    for path in sorted((root / "runs").rglob("transcript.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        usage = data.get("usage") or {}
        pt = usage.get("prompt_tokens")
        ct = usage.get("completion_tokens")
        if pt is None and ct is None:
            continue
        real_tokens.append(
            {
                "path": str(path.relative_to(root)),
                "condition_id": data.get("condition_id"),
                "prompt_tokens": pt,
                "completion_tokens": ct,
                "total_tokens": usage.get("total_tokens") or ((pt or 0) + (ct or 0)),
            }
        )

    real_summary: dict[str, Any] = {"n_transcripts": len(real_tokens)}
    if real_tokens:
        totals = [r["total_tokens"] for r in real_tokens]
        prompts = [r["prompt_tokens"] for r in real_tokens if r["prompt_tokens"] is not None]
        comps = [r["completion_tokens"] for r in real_tokens if r["completion_tokens"] is not None]
        real_summary.update(
            {
                "mean_total_tokens": round(mean(totals), 2),
                "median_total_tokens": round(median(totals), 2),
                "sd_total_tokens": round(pstdev(totals), 2) if len(totals) > 1 else 0.0,
                "mean_prompt_tokens": round(mean(prompts), 2) if prompts else None,
                "mean_completion_tokens": round(mean(comps), 2) if comps else None,
                "source": "V5_RQ02 noaudit transcripts (usage field)",
            }
        )

    # V6 claim-text proxy (chars/4 ≈ tokens) + quality = 1 - UR
    by_cond: dict[str, Any] = {}
    for cond in ("B01", "B02", "full"):
        runs = [a for a in audits if a.get("condition_id") == cond]
        chars = sum(len(c.get("claim_text", "")) for a in runs for c in a.get("claim_labels", []))
        claims = sum(int(a.get("total_claims", 0)) for a in runs)
        uns = sum(int(a.get("unsupported_count", 0)) for a in runs)
        tok_est = chars / 4.0
        quality = (1.0 - uns / claims) if claims else 0.0
        by_cond[cond] = {
            "n_runs": len(runs),
            "total_claims": claims,
            "claim_chars": chars,
            "proxy_tokens_chars_over_4": round(tok_est, 1),
            "supported_rate_quality": round(quality, 4),
            "unsupported_claim_rate": round(uns / claims, 4) if claims else None,
            "quality_per_1k_proxy_tokens": round(1000.0 * quality / tok_est, 4) if tok_est else None,
            "claims_per_run": round(claims / len(runs), 4) if runs else None,
        }

    # Incremental gain: quality of Full vs B02 relative to extra proxy tokens
    b02 = by_cond["B02"]
    full = by_cond["full"]
    d_q = full["supported_rate_quality"] - b02["supported_rate_quality"]
    d_tok = full["proxy_tokens_chars_over_4"] - b02["proxy_tokens_chars_over_4"]
    incremental = {
        "delta_quality_full_minus_b02": round(d_q, 6),
        "delta_proxy_tokens_full_minus_b02": round(d_tok, 1),
        "quality_gain_per_1k_extra_tokens": round(1000.0 * d_q / d_tok, 6) if d_tok else None,
        "note": "Near-zero quality gain for large token/claim inflation under Full vs B02.",
    }

    return {
        "real_token_calibration": real_summary,
        "v6_proxy_by_condition": by_cond,
        "incremental_full_vs_b02": incremental,
        "proxy_definition": "sum(len(claim_text))/4 over T05 audit claim labels",
    }


def _semantic_convergence(audits: list[dict[str, Any]]) -> dict[str, Any]:
    # UR by claim ordinal (pooled)
    by_pos: dict[int, dict[str, int]] = defaultdict(lambda: {"bad": 0, "n": 0})
    for a in audits:
        for i, c in enumerate(a.get("claim_labels", [])):
            by_pos[i]["n"] += 1
            if _is_bad(c.get("label", "")):
                by_pos[i]["bad"] += 1
    ur_by_index = []
    for i in sorted(by_pos):
        d = by_pos[i]
        if d["n"] < 20:
            continue
        ur_by_index.append(
            {
                "claim_index": i,
                "n": d["n"],
                "unsupported_rate": round(d["bad"] / d["n"], 4),
            }
        )

    # Early-stop simulation: truncate each Full run to first K claims (K = B02 mean claims/run)
    b02_runs = [a for a in audits if a.get("condition_id") == "B02"]
    full_runs = [a for a in audits if a.get("condition_id") == "full"]
    k = int(round(mean(a["total_claims"] for a in b02_runs))) if b02_runs else 11

    def _ur_truncated(runs: list[dict], budget: int | None) -> dict[str, Any]:
        claims = 0
        uns = 0
        for a in runs:
            labs = a.get("claim_labels", [])
            slice_ = labs if budget is None else labs[:budget]
            claims += len(slice_)
            uns += sum(1 for c in slice_ if _is_bad(c.get("label", "")))
        return {
            "budget_claims": budget,
            "total_claims": claims,
            "unsupported_claim_rate": round(uns / claims, 4) if claims else None,
            "claims_per_run": round(claims / len(runs), 4) if runs else None,
        }

    full_all = _ur_truncated(full_runs, None)
    full_early = _ur_truncated(full_runs, k)
    b02_all = _ur_truncated(b02_runs, None)

    # Plateau stop: cumulative UR change < eps after min_claims
    eps = 0.005
    min_claims = 5
    plateau_pairs: list[tuple[int, int]] = []  # (stop_at, total_claims)
    for a in full_runs:
        labs = [c.get("label", "") for c in a.get("claim_labels", [])]
        if len(labs) < min_claims:
            continue
        stop_at = len(labs)
        bad = 0
        for i, lab in enumerate(labs, start=1):
            if _is_bad(lab):
                bad += 1
            if i < min_claims:
                continue
            prev_ur = (bad - (1 if _is_bad(lab) else 0)) / (i - 1) if i > 1 else 0.0
            cur_ur = bad / i
            if abs(cur_ur - prev_ur) < eps and i >= min_claims:
                stop_at = i
                break
        plateau_pairs.append((stop_at, len(labs)))

    plateau_stops = [p[0] for p in plateau_pairs]
    plateau = {
        "eps_ur_delta": eps,
        "min_claims": min_claims,
        "mean_stop_index": round(mean(plateau_stops), 2) if plateau_stops else None,
        "median_stop_index": round(median(plateau_stops), 2) if plateau_stops else None,
        "mean_full_claims": round(mean(a["total_claims"] for a in full_runs), 2) if full_runs else None,
        "fraction_stopped_before_end": round(
            sum(1 for s, n in plateau_pairs if s < n) / len(plateau_pairs), 4
        )
        if plateau_pairs
        else None,
    }

    # Goal-sufficiency: runs with zero unsupported (semantic goal met)
    goal = {}
    for cond in ("B01", "B02", "full"):
        runs = [a for a in audits if a.get("condition_id") == cond]
        ok = sum(1 for a in runs if int(a.get("unsupported_count", 0)) == 0)
        goal[cond] = {
            "n_runs": len(runs),
            "zero_unsupported_runs": ok,
            "zero_unsupported_rate": round(ok / len(runs), 4) if runs else None,
        }

    return {
        "ur_by_claim_index": ur_by_index,
        "early_stop_simulation": {
            "k_equals_b02_mean_claims": k,
            "full_all_claims": full_all,
            "full_truncated_to_k": full_early,
            "b02_all_claims": b02_all,
            "ur_delta_early_minus_full_pp": round(
                100
                * (
                    (full_early["unsupported_claim_rate"] or 0)
                    - (full_all["unsupported_claim_rate"] or 0)
                ),
                4,
            ),
            "claims_saved_vs_full": full_all["total_claims"] - full_early["total_claims"],
        },
        "plateau_stopping_rule": plateau,
        "goal_sufficiency_zero_unsupported": goal,
        "interpretation": (
            "If truncating Full to B02's claim budget preserves not-supported rate, extra claims "
            "are over-optimization. Rates here use label!='supported', not T05 unsupported_count UR. "
            "Plateau stop detects when cumulative not-supported rate stabilizes."
        ),
    }


def compute_core_directions(repo_root: Path | None = None) -> CoreDirectionsAnalysis:
    root = repo_root or _repo_root()
    labels = json.loads((root / "runs" / "V6_RQ01_T05_audit_labels.json").read_text(encoding="utf-8"))
    audits = labels.get("audits", [])

    error = _error_propagation(audits)
    cost = _token_cost_efficiency(audits, root)
    conv = _semantic_convergence(audits)

    directions = [
        {
            "id": "RD1_error_propagation_recovery",
            "title": "Error propagation and recovery dynamics",
            "statement": (
                f"P(not-supported|prev not-supported)="
                f"{error['p_unsupported_given_prev_unsupported']:.2%} "
                f"vs P(not-supported|prev supported)="
                f"{error['p_unsupported_given_prev_supported']:.2%} "
                f"(cascade lift {error['cascade_lift']:.2f}×; not-supported = any label≠supported). "
                f"Recovery after first bad claim: {error['recovery_rate_any_supported_after_first_bad']:.1%} "
                f"({error['stuck_no_recovery_runs']} stuck / {error['n_runs_with_unsupported']})."
            ),
            "evidence": "runs/V6_RQ01_T05_audit_labels.json ordered claim_labels",
        },
        {
            "id": "RD2_token_cost_efficiency",
            "title": "Token and cost efficiency benchmarks",
            "statement": (
                f"V5 calibration: mean {cost['real_token_calibration'].get('mean_total_tokens')} "
                f"total tokens/run (n={cost['real_token_calibration']['n_transcripts']}). "
                f"V6 proxy quality-per-1k-tokens: B01 "
                f"{cost['v6_proxy_by_condition']['B01']['quality_per_1k_proxy_tokens']}, "
                f"B02 {cost['v6_proxy_by_condition']['B02']['quality_per_1k_proxy_tokens']}, "
                f"Full {cost['v6_proxy_by_condition']['full']['quality_per_1k_proxy_tokens']}; "
                f"Full−B02 quality gain per 1k extra tokens ≈ "
                f"{cost['incremental_full_vs_b02']['quality_gain_per_1k_extra_tokens']}."
            ),
            "evidence": "V5 transcripts usage + V6 claim_text proxy tokens",
        },
        {
            "id": "RD3_semantic_convergence_stopping",
            "title": "Semantic convergence and stopping criteria",
            "statement": (
                f"Truncating Full to K={conv['early_stop_simulation']['k_equals_b02_mean_claims']} "
                f"claims (B02 mean) changes not-supported rate by "
                f"{conv['early_stop_simulation']['ur_delta_early_minus_full_pp']}pp "
                f"(not T05 claim-weighted UR) while saving "
                f"{conv['early_stop_simulation']['claims_saved_vs_full']} claims. "
                f"Plateau rule (Δ not-supported rate<"
                f"{conv['plateau_stopping_rule']['eps_ur_delta']}) stops at mean index "
                f"{conv['plateau_stopping_rule']['mean_stop_index']} vs mean Full length "
                f"{conv['plateau_stopping_rule']['mean_full_claims']}. "
                f"Zero-unsupported_count run rates: B01 "
                f"{conv['goal_sufficiency_zero_unsupported']['B01']['zero_unsupported_rate']:.1%}, "
                f"B02 {conv['goal_sufficiency_zero_unsupported']['B02']['zero_unsupported_rate']:.1%}, "
                f"Full {conv['goal_sufficiency_zero_unsupported']['full']['zero_unsupported_rate']:.1%}."
            ),
            "evidence": "early-stop + plateau simulations on T05 claim sequences",
        },
    ]

    return CoreDirectionsAnalysis(
        schema_version=1,
        error_propagation=error,
        token_cost_efficiency=cost,
        semantic_convergence=conv,
        research_directions=directions,
    )


def write_core_direction_artifacts(repo_root: Path | None = None) -> dict[str, Path]:
    root = repo_root or _repo_root()
    analysis = compute_core_directions(root)
    out_json = root / "runs" / "V6_RQ01_T10_core_directions.json"
    out_md = root / "runs" / "V6_RQ01_T10_core_directions.md"
    out_json.write_text(json.dumps(analysis.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# V6 RQ01 T10 — Core Research Directions",
        "",
        "Derived from durable V5/V6 artifacts (no new model runs).",
        "Claim ordinal position is a within-report proxy for loop iteration.",
        "",
    ]
    for rd in analysis.research_directions:
        lines.append(f"## {rd['id']}: {rd['title']}")
        lines.append("")
        lines.append(rd["statement"])
        lines.append("")
        lines.append(f"Evidence: `{rd['evidence']}`")
        lines.append("")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": out_json, "md": out_md}
