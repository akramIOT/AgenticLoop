"""Claim parsing helpers for V5 audit.

Deterministic plan stripping and claim surface extraction.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


# Exact plan/execution/meta section headers (lowercase, without leading #)
_PLAN_HEADERS_EXACT = {
    "plan", "execution", "evidence trace manifest", "report",
    "final output", "final output generation", "reasoning reference",
    "draft update", "explicit plan", "refined mapping",
    "alternative interpretation", "final plan",
}

# Plan keywords that must appear as standalone headers or with specific prefixes
_PLAN_KEYWORDS = [
    "plan", "execution", "evidence trace manifest", "report", "final output",
    "final output generation", "reasoning reference", "draft update",
    "explicit plan", "refined mapping", "alternative interpretation",
    "final plan", "step ", "analyze inputs", "verify outcome",
    "draft report", "finalize", "scope evidence", "exclude contaminated data",
    "generate summary", "filter verified sources", "map claims to verified sources",
    "analyze source audit log",
]

# Report headings that are NOT plan headers
_REPORT_HEADINGS = {
    "outcome report", "baseline recommendation report", "findings",
    "evidence summary", "draft paragraph", "report draft",
}


def _is_plan_header(line: str) -> bool:
    """Check if a line is a plan/execution/meta section header."""
    stripped = line.strip().lower()
    if not stripped:
        return False
    # Numbered plan steps with bold headers like "1. **Analyze Inputs**:"
    if re.match(r"^\d+\.\s+\*\*[a-z ]+\*\*\s*:", stripped):
        return True
    # Colon-style headers
    for kw in _PLAN_KEYWORDS:
        if stripped.startswith(kw + ":"):
            return True
    # Markdown headers
    if stripped.startswith("# ") or stripped.startswith("## "):
        heading_text = re.sub(r"^#+\s+", "", stripped).strip()
        # If it's a known report heading, it's not a plan header
        if heading_text in _REPORT_HEADINGS:
            return False
        for kw in _PLAN_KEYWORDS:
            if kw in heading_text:
                return True
    return False


def _is_plan_content_line(line: str) -> bool:
    """Check if a line looks like plan content (bullet, numbered item, short instruction)."""
    stripped = line.strip()
    if not stripped:
        return False
    # Numbered items
    if re.match(r"^\d+\.\s+", stripped):
        return True
    # Bullet items
    if re.match(r"^[*\-]\s+", stripped):
        return True
    # Short indented lines without sentence terminator
    if len(stripped) < 40 and not re.search(r"[.!?]$", stripped):
        return True
    return False


def strip_plan_sections(text: str) -> str:
    """Remove plan, execution, and meta sections from report text.

    Strategy:
    1. If the text contains no plan markers, return as-is (B01 reports).
    2. Otherwise, find the boundary where the actual report starts:
       - Look for `---` followed by a markdown heading
       - Look for ```markdown
       - Look for a top-level heading that isn't a plan keyword
    3. If no clear boundary, use line-by-line heuristic stripping.
    """
    lines = text.splitlines()
    has_plan = any(_is_plan_header(l) for l in lines)
    if not has_plan:
        return text

    # Strategy A: Find the last clear boundary marker
    # Boundary markers: horizontal rule `---` or `***` followed by report heading
    # Or ```markdown code fence
    best_start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "---" or stripped == "***" or stripped == "--- FILE:":
            # Check if next non-empty line is a report heading
            for j in range(i + 1, min(i + 5, len(lines))):
                nxt = lines[j].strip()
                if not nxt:
                    continue
                if re.match(r"^#\s+", nxt) and not _is_plan_header(nxt):
                    best_start = j
                    break
                if re.match(r"^```markdown\s*$", nxt):
                    best_start = j + 1
                    break
        if stripped == "```markdown":
            best_start = i + 1
        if stripped == "# Report" or stripped == "## Report" or stripped == "# Draft Paragraph":
            # These are meta headers; actual content usually follows
            for j in range(i + 1, min(i + 5, len(lines))):
                nxt = lines[j].strip()
                if nxt and not nxt.startswith("#"):
                    best_start = j
                    break

    if best_start > 0:
        result = "\n".join(lines[best_start:])
        # Strip trailing code fence
        result = re.sub(r"\n```\s*$", "", result)
        return result

    # Strategy B: Line-by-line heuristic stripping
    result_lines: list[str] = []
    in_plan = False
    for line in lines:
        if _is_plan_header(line):
            in_plan = True
            continue
        if in_plan:
            stripped = line.strip()
            if not stripped:
                continue
            if _is_plan_content_line(line):
                continue
            # Exit plan mode if we see a markdown heading that isn't a plan header
            if re.match(r"^#\s+", stripped) and not _is_plan_header(stripped):
                in_plan = False
            # Exit plan mode if we see a substantial paragraph line (not bullet/numbered)
            # that ends with a sentence terminator (allowing trailing quotes/parens) and
            # doesn't look like a plan instruction
            trimmed_end = re.sub(r'["\'\)\]]+$', '', stripped)
            if len(stripped) > 40 and re.search(r"[.!?]$", trimmed_end) and not re.match(r"^\d+\.\s+|^[*\-]\s+", stripped):
                in_plan = False
            else:
                continue
        result_lines.append(line)

    result = "\n".join(result_lines)
    # Strip trailing code fence
    result = re.sub(r"\n```\s*$", "", result)
    return result


def extract_claim_units(text: str) -> list[str]:
    """Split stripped report text into claim units (sentences / paragraphs).

    Strategy:
    1. Remove markdown headings and evidence list lines first.
    2. Split remaining text on sentence boundaries.
    3. Filter out empty/short sentences.
    """
    # Normalize whitespace
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"  +", " ", text)

    # Step 1: Remove markdown headings, section titles, plan steps, and pure evidence list lines
    lines = text.splitlines()
    cleaned_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Skip markdown headings
        if re.match(r"^#{1,3}\s+", stripped):
            continue
        # Skip section titles / bold labels without substantive content
        if re.match(r"^\*\*[A-Za-z ]+\*\*\s*:?\s*$", stripped) or re.match(r"^\*\*[A-Za-z ]+:\*\*$", stripped):
            continue
        # Skip plan step lines like "Step 4: Construct the final report content."
        if re.match(r"^Step\s+\d+\s*:", stripped, re.IGNORECASE):
            continue
        # Skip pure evidence list items that don't contain a complete sentence
        if re.match(r"^[-*]\s+", stripped):
            # Keep bullet lines that end with a sentence terminator (complete sentence/claim)
            if not re.search(r"[.!?]$", stripped):
                continue
            # Also skip lines that are just file references
            if re.match(r"^[-*]\s+`?workspace/", stripped):
                continue
            # Skip metadata bullets like "Cross-Contamination Status: None."
            if re.match(r"^[-*]\s+\*\*[A-Za-z ]+\*\*\s*:", stripped):
                continue
        cleaned_lines.append(stripped)

    cleaned_text = " ".join(cleaned_lines)

    # Step 2: Split on sentence boundaries
    raw = re.split(r"(?<=[.!?])\s+", cleaned_text)
    units: list[str] = []
    for fragment in raw:
        fragment = fragment.strip()
        if not fragment:
            continue
        if len(fragment) < 15 and not re.search(r"[.!?]$", fragment):
            # Very short fragment, likely a continuation; merge if possible
            if units:
                units[-1] = units[-1] + " " + fragment
            else:
                units.append(fragment)
            continue
        units.append(fragment)

    # Step 3: Filter
    filtered: list[str] = []
    for u in units:
        if len(u) < 10:
            continue
        filtered.append(u)
    return filtered


def is_plan_only_report(report_text: str) -> bool:
    """True if the report contains only plan/execution text with no actual findings."""
    stripped = strip_plan_sections(report_text)
    cleaned = re.sub(r"\s+", " ", stripped).strip()
    # Check for substantive report indicators
    report_indicators = [
        "conclusion", "finding", "result", "report", "therefore", "based on",
        "evidence", "summary", "recommend", "achieved", "not achieved",
        "significant", "improve", "degrad", "performance", "accuracy",
        "latency", "precision", "recall", "caching", "baseline", "drifted",
        "draft paragraph", "outcome report", "baseline recommendation",
        "findings", "evidence summary",
    ]
    lower = cleaned.lower()
    score = sum(1 for ind in report_indicators if ind in lower)
    # If score is low and text is short, it's plan-only
    if len(cleaned) < 100 and score < 2:
        return True
    # If the only content is plan steps (numbered/bulleted)
    lines = [l for l in cleaned.splitlines() if l.strip()]
    plan_lines = sum(1 for l in lines if re.match(r"^\d+\.\s+|^\*\s+|^-\s+", l.strip()))
    if plan_lines > 0 and plan_lines >= len(lines) * 0.8:
        return True
    return False


def load_report_artifact(manifest: dict, repo_root: Path) -> str:
    """Load and return the report artifact text, or empty string if missing."""
    rel = manifest.get("report_artifact_path", "")
    if not rel:
        return ""
    path = repo_root / rel
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def load_claims(manifest: dict, repo_root: Path) -> list[str]:
    """Load claims.json as list of strings."""
    rel = manifest.get("claims_path", "")
    if not rel:
        return []
    path = repo_root / rel
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [str(c) for c in data if isinstance(c, str)]
    return []


def load_oracle(manifest: dict, repo_root: Path) -> dict:
    """Load oracle_audit.json as dict."""
    rel = manifest.get("oracle_audit_path", "")
    if not rel:
        return {}
    path = repo_root / rel
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
