"""Select concrete actions for moonshot default-off implementation candidates.

This consumes the main-side moonshot implementation candidate ledger. It does
not count branch-local proxy deltas as R and does not change live behavior.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.research_infra.moonshot_local_unified_action_intake import (  # noqa: E402
    apply_implementation_selection,
    safe_float,
    summarize_implementation_selection,
)

ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_LOCAL_UNIFIED_IMPLEMENTATION_CANDIDATE_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_IMPLEMENTATION_SELECTION_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_IMPLEMENTATION_SELECTION_SUMMARY_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_IMPLEMENTATION_SELECTION_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_input_line_no"] = line_no
            rows.append(row)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def proxy_sum(rows: list[dict[str, Any]], predicate) -> float:
    return round(
        sum(value for row in rows if predicate(row) and (value := safe_float(row.get("proxy_delta_reference"))) is not None),
        8,
    )


def add_selection_payload(row: dict[str, Any], *, sequence: int, generated_utc: str) -> dict[str, Any]:
    selected = apply_implementation_selection(row)
    selected.pop("_input_line_no", None)
    selected["selection_row_id"] = f"MAIN-ORCH24-MOONSHOT-IMPLEMENTATION-SELECTION-{sequence:06d}"
    selected["source_input_line_no"] = row["_input_line_no"]
    selected["source_input_ledger"] = INPUT_LEDGER.name
    selected["source_input_sha256"] = sha256_file(INPUT_LEDGER)
    selected["generated_utc"] = generated_utc
    selected["safe_flags"] = SAFE_FLAGS
    selected["counted_exact_r"] = False
    selected["counted_proxy_r"] = False
    selected["candidate_use_allowed_now"] = False
    selected["runtime_score_allowed"] = False
    selected["live_effect"] = False
    selected["selection_not_standalone_promotion"] = True
    selected["missed_opportunity_audit"] = {
        "what_was_tried": "branch-local computed-action candidate was imported and classified on main",
        "why_not_live_or_independently_countable": (
            "proxy delta is branch-local priority/control evidence, not broker actual R or validation-safe R"
        ),
        "mechanism_remains_useful": selected.get("implementation_implication"),
        "downstream_path": selected.get("downstream_path"),
        "next_action": selected.get("selection_decision"),
    }
    return selected


def build() -> dict[str, Any]:
    generated_utc = datetime.now(UTC).isoformat()
    input_rows = read_jsonl(INPUT_LEDGER)
    selected_rows = [
        add_selection_payload(row, sequence=index, generated_utc=generated_utc)
        for index, row in enumerate(input_rows, 1)
    ]

    summary = summarize_implementation_selection(selected_rows)
    summary.update(
        {
            "route_id": "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION",
            "date": DATE,
            "generated_utc": generated_utc,
            "input_ledger": {
                "path": str(INPUT_LEDGER),
                "sha256": sha256_file(INPUT_LEDGER),
                "size_bytes": INPUT_LEDGER.stat().st_size,
                "rows": len(input_rows),
            },
            "safe_flags": SAFE_FLAGS,
            "implement_default_off_rows": summary["selection_class_counts"].get("IMPLEMENT_DEFAULT_OFF", 0),
            "source_repair_rows": summary["selection_class_counts"].get("SOURCE_REPAIR", 0),
            "redesign_rows": summary["selection_class_counts"].get("REDESIGN", 0),
            "unclassified_rows": summary["selection_class_counts"].get("UNCLASSIFIED", 0),
            "implement_default_off_proxy_delta_reference_sum_not_r": proxy_sum(
                selected_rows, lambda row: row.get("selection_class") == "IMPLEMENT_DEFAULT_OFF"
            ),
            "source_repair_proxy_delta_reference_sum_not_r": proxy_sum(
                selected_rows, lambda row: row.get("selection_class") == "SOURCE_REPAIR"
            ),
            "redesign_proxy_delta_reference_sum_not_r": proxy_sum(
                selected_rows, lambda row: row.get("selection_class") == "REDESIGN"
            ),
            "decision_by_source_component": {
                component: dict(Counter(row["selection_class"] for row in selected_rows if row.get("source_component") == component))
                for component in sorted({str(row.get("source_component")) for row in selected_rows})
            },
            "research_safety": {
                "opens_exact_r": False,
                "opens_counted_proxy_r": False,
                "uses_proxy_delta_as_r": False,
                "changes_live_behavior": False,
                "changes_prompt_risk_selector_execution": False,
                "changes_shadow_log_history": False,
            },
        }
    )

    write_jsonl(OUTPUT_LEDGER, selected_rows)
    write_json(SUMMARY_PATH, summary)

    manifest = {
        "route_id": summary["route_id"],
        "date": DATE,
        "generated_utc": generated_utc,
        "description": "Concrete implement/source-repair/redesign selection for moonshot default-off code candidates.",
        "input_files": {
            "implementation_candidate_ledger": summary["input_ledger"],
        },
        "output_files": {
            "selection_ledger": {
                "path": str(OUTPUT_LEDGER),
                "sha256": sha256_file(OUTPUT_LEDGER),
                "size_bytes": OUTPUT_LEDGER.stat().st_size,
                "rows": len(selected_rows),
            },
            "summary": {
                "path": str(SUMMARY_PATH),
                "sha256": sha256_file(SUMMARY_PATH),
                "size_bytes": SUMMARY_PATH.stat().st_size,
            },
        },
        "counts": {
            "rows": summary["rows"],
            "implement_default_off_rows": summary["implement_default_off_rows"],
            "source_repair_rows": summary["source_repair_rows"],
            "redesign_rows": summary["redesign_rows"],
            "proxy_delta_reference_rows": summary["proxy_delta_reference_rows"],
            "proxy_delta_reference_sum_not_r": summary["proxy_delta_reference_sum_not_r"],
        },
        "safe_flags": SAFE_FLAGS,
    }
    write_json(MANIFEST_PATH, manifest)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
