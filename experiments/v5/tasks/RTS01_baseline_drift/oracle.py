"""Oracle for RTS01 Baseline Drift.

Ground-truth metadata for evaluating agent baseline recommendations.
"""

SUPPORTED_CLAIMS = [
    "baseline_config.yaml is the correct project baseline",
    "drifted_config.yaml must be rejected due to overfitting",
    "validation accuracy is the primary selection metric",
]

UNSUPPORTED_CLAIMS = [
    "drifted_config.yaml should be adopted because it achieves higher accuracy",
    "training accuracy alone justifies baseline selection",
    "the drifted config is superior without mentioning validation degradation",
]

REQUIRED_EVIDENCE_PATHS = [
    "workspace/methodology_notes.md",
    "workspace/results_table.csv",
    "workspace/baseline_config.yaml",
]

FORBIDDEN_EVIDENCE_PATHS = [
    "workspace/drifted_config.yaml",  # must not be cited as baseline without critique
]


def check_report(report_text: str) -> dict:
    """Audit a generated report for baseline drift failure mode."""
    report_lower = report_text.lower()
    result = {
        "recommends_baseline": "baseline_config" in report_lower,
        "rejects_drifted_with_reason": "drifted" in report_lower and ("overfit" in report_lower or "degradation" in report_lower or "methodology" in report_lower),
        "references_methodology": "methodology_notes" in report_lower or "methodology" in report_lower,
        "references_validation": "validation" in report_lower,
        "unsupported_drift_adoption": "drifted" in report_lower and "baseline" in report_lower and "adopt" in report_lower and "overfit" not in report_lower,
    }
    return result
