#!/usr/bin/env python3
"""Fail if active context docs present old GTOS assumptions as current truth."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "research/operations/vnext_repo_context_cleanup_deletion_2026_05_29/REPO_CONTEXT_STALENESS_VERIFICATION.json"

ACTIVE_DOCS = [
    "README.md",
    "CLAUDE.md",
    "AGENTS.md",
    ".context/00_READING_ORDER.md",
    ".context/00_core/quick_reference_card.md",
    ".context/00_core/current_vnext_system_map.md",
    ".context/00_core/current_repo_reading_order.md",
    ".context/00_core/repo_cleanup_and_staleness_policy.md",
    ".context/00_core/research_current_state.md",
    ".context/00_core/research_operating_doctrine.md",
]

FORBIDDEN_PATTERNS = [
    ("old_7_symbol_current", re.compile(r"\b7[- ]symbol\b|\b7 instruments\b|7 orchestrators", re.IGNORECASE)),
    ("old_primary_l2_current", re.compile(r"PrimaryAnalyzer\s*/\s*L2|PrimaryAnalyzer\s*->\s*L2|old PrimaryAnalyzer/L2", re.IGNORECASE)),
    ("static_15r_current", re.compile(r"fixed `?1\.5R`?|static fixed `?1\.5R`?|static `?1\.5R`?", re.IGNORECASE)),
    ("j46_j49_current", re.compile(r"\bJ46\b|\bJ49\b", re.IGNORECASE)),
    ("be_only_current", re.compile(r"\bBE-only\b|BE described as current active production policy", re.IGNORECASE)),
    ("april_live_current", re.compile(r"\bApril-live\b|\bApril live\b|2026-04 live", re.IGNORECASE)),
]

ALLOW_CONTEXT = re.compile(
    r"historical|archive|archived|old|older|legacy|baseline|prior|comparator|comparator-only|fail-closed|not current|do not use|unless a current|stale|superseded|research-only|owner review|separate production|proxy|discovery",
    re.IGNORECASE,
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def scan_doc(path: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    rel_path = path.relative_to(ROOT).as_posix()
    boundary_line = 0
    if rel_path == ".context/00_core/research_current_state.md":
        boundary_heading = "## Current vNext Production Truth Boundary"
        for idx, raw_line in enumerate(text.splitlines(), 1):
            if raw_line.strip() == boundary_heading:
                boundary_line = idx
                break
    elif rel_path == ".context/00_core/research_operating_doctrine.md":
        boundary_heading = "## Current System Truth Boundary"
        for idx, raw_line in enumerate(text.splitlines(), 1):
            if raw_line.strip() == boundary_heading:
                boundary_line = idx
                break

    for line_no, line in enumerate(text.splitlines(), 1):
        for pattern_id, regex in FORBIDDEN_PATTERNS:
            if not regex.search(line):
                continue
            allowed = bool(ALLOW_CONTEXT.search(line)) or (boundary_line > 0 and line_no > boundary_line)
            findings.append(
                {
                    "relative_path": rel_path,
                    "line_number": line_no,
                    "pattern_id": pattern_id,
                    "status": "allowed_historical_or_comparator_context" if allowed else "fail_stale_current_claim",
                    "line_excerpt": line[:500],
                }
            )
    return findings


def build_result() -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    missing: list[str] = []
    for rel_path in ACTIVE_DOCS:
        path = ROOT / rel_path
        if not path.exists():
            missing.append(rel_path)
            continue
        findings.extend(scan_doc(path))
    failures = [row for row in findings if row["status"] == "fail_stale_current_claim"]
    return {
        "schema_version": "repo_context_staleness_verification_v1",
        "generated_at_utc": utc_now(),
        "active_docs_scanned": ACTIVE_DOCS,
        "missing_docs": missing,
        "finding_count": len(findings),
        "allowed_historical_or_comparator_count": sum(1 for row in findings if row["status"] == "allowed_historical_or_comparator_context"),
        "failure_count": len(failures) + len(missing),
        "failures": failures,
        "status": "passed" if not failures and not missing else "failed",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    result = build_result()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "failure_count": result["failure_count"], "output": str(output.relative_to(ROOT))}, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
