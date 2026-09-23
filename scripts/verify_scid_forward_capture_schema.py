from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.forward_capture import (
    SCID_CAPTURE_GROUPS,
    SCID_FORWARD_SOURCE_CAPTURE_PATH,
    validate_scid_forward_source_capture_row,
)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            rows.append(
                {
                    "_parse_error": str(exc),
                    "_line": lineno,
                    "field_group": None,
                }
            )
            continue
        if isinstance(row, dict):
            row["_line"] = lineno
            rows.append(row)
    return rows


def verify(path: Path, *, allow_empty: bool = False) -> dict[str, Any]:
    rows = _read_jsonl(path)
    duplicate_registry: dict[str, str] = {}
    failures = []
    counts = Counter()
    for row in rows:
        line = row.pop("_line", None)
        if "_parse_error" in row:
            failures.append({"line": line, "issues": ["json_parse_error"], "error": row["_parse_error"]})
            continue
        validation = validate_scid_forward_source_capture_row(row, duplicate_registry)
        counts[str(row.get("field_group"))] += 1
        if not validation["ok"]:
            failures.append(
                {
                    "line": line,
                    "field_group": row.get("field_group"),
                    "issues": validation["issues"],
                    "missing_fields": validation["missing_fields"],
                    "extra_fields": validation["extra_fields"],
                    "forbidden_keys": validation["forbidden_keys"],
                }
            )
    missing_groups = sorted(set(SCID_CAPTURE_GROUPS) - set(counts))
    ok = not failures and (allow_empty or bool(rows))
    return {
        "ok": ok,
        "path": str(path),
        "row_count": len(rows),
        "counts_by_group": dict(sorted(counts.items())),
        "missing_groups": missing_groups,
        "failures": failures[:100],
        "failure_count": len(failures),
        "safe_flags": {
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
        "candidate_boundary": {
            "expected_prospective_candidates_from_accepted_g12": 3014,
            "verifier_claim_scope": "schema_and_redaction_only_no_result_scoring",
        },
        "allow_empty": allow_empty,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify SCID forward source-capture JSONL rows without scoring outcomes."
    )
    parser.add_argument("--path", default=SCID_FORWARD_SOURCE_CAPTURE_PATH)
    parser.add_argument("--allow-empty", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = verify(Path(args.path), allow_empty=args.allow_empty)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"SCID verifier ok={report['ok']} rows={report['row_count']} failures={report['failure_count']}")
        print(f"counts_by_group={json.dumps(report['counts_by_group'], sort_keys=True)}")
        if report["failures"]:
            print(json.dumps(report["failures"], indent=2, sort_keys=True))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
