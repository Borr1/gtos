"""Select concrete source guard actions from moonshot guard specs."""

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
    apply_guard_selection,
    safe_float,
    summarize_guard_selection,
)

ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_LOCAL_UNIFIED_ACTION_INTAKE_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_GUARD_SELECTION_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_GUARD_SELECTION_SUMMARY_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_GUARD_SELECTION_OUTPUT_MANIFEST_{DATE}.json"

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


def read_guard_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("main_action_class") != "GUARD_SPEC":
                continue
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


def add_guard_payload(
    row: dict[str, Any],
    *,
    sequence: int,
    generated_utc: str,
    input_sha256: str,
) -> dict[str, Any]:
    selected = apply_guard_selection(row)
    selected.pop("_input_line_no", None)
    selected["guard_selection_row_id"] = f"MAIN-ORCH24-MOONSHOT-GUARD-SELECTION-{sequence:06d}"
    selected["source_input_line_no"] = row["_input_line_no"]
    selected["source_input_ledger"] = INPUT_LEDGER.name
    selected["source_input_sha256"] = input_sha256
    selected["generated_utc"] = generated_utc
    selected["safe_flags"] = SAFE_FLAGS
    selected["counted_exact_r"] = False
    selected["counted_proxy_r"] = False
    selected["candidate_use_allowed_now"] = False
    selected["runtime_score_allowed"] = False
    selected["live_effect"] = False
    selected["guard_not_standalone_promotion"] = True
    selected["missed_opportunity_audit"] = {
        "what_was_tried": "branch-local guard spec was imported and classified on main",
        "why_not_live_or_independently_countable": (
            "guard row is source-completeness/control metadata; proxy delta, when present, is not broker actual R"
        ),
        "mechanism_remains_useful": selected.get("computed_decision"),
        "downstream_path": selected.get("downstream_path"),
        "next_action": selected.get("guard_selection_decision"),
    }
    return selected


def build() -> dict[str, Any]:
    generated_utc = datetime.now(UTC).isoformat()
    input_sha256 = sha256_file(INPUT_LEDGER)
    input_rows = read_guard_rows(INPUT_LEDGER)
    selected_rows = [
        add_guard_payload(row, sequence=index, generated_utc=generated_utc, input_sha256=input_sha256)
        for index, row in enumerate(input_rows, 1)
    ]

    summary = summarize_guard_selection(selected_rows)
    summary.update(
        {
            "route_id": "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION",
            "date": DATE,
            "generated_utc": generated_utc,
            "input_ledger": {
                "path": str(INPUT_LEDGER),
                "sha256": input_sha256,
                "size_bytes": INPUT_LEDGER.stat().st_size,
                "guard_rows": len(input_rows),
            },
            "safe_flags": SAFE_FLAGS,
            "source_confidence_guard_rows": summary["guard_selection_class_counts"].get("SOURCE_CONFIDENCE_GUARD", 0),
            "denominator_guard_rows": summary["guard_selection_class_counts"].get("DENOMINATOR_GUARD", 0),
            "adverse_context_guard_rows": summary["guard_selection_class_counts"].get(
                "DENOMINATOR_GUARD_ADVERSE_CONTEXT", 0
            ),
            "source_repair_rows": summary["guard_selection_class_counts"].get("SOURCE_REPAIR", 0),
            "unclassified_rows": summary["guard_selection_class_counts"].get("UNCLASSIFIED", 0),
            "denominator_guard_proxy_delta_reference_sum_not_r": proxy_sum(
                selected_rows, lambda row: row.get("guard_selection_class") == "DENOMINATOR_GUARD"
            ),
            "adverse_context_guard_proxy_delta_reference_sum_not_r": proxy_sum(
                selected_rows, lambda row: row.get("guard_selection_class") == "DENOMINATOR_GUARD_ADVERSE_CONTEXT"
            ),
            "source_repair_proxy_delta_reference_sum_not_r": proxy_sum(
                selected_rows, lambda row: row.get("guard_selection_class") == "SOURCE_REPAIR"
            ),
            "guard_class_by_source_component": {
                component: dict(
                    Counter(row["guard_selection_class"] for row in selected_rows if row.get("source_component") == component)
                )
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
        "description": "Concrete source-confidence and denominator guard selection for moonshot guard specs.",
        "input_files": {
            "moonshot_action_intake_ledger": summary["input_ledger"],
        },
        "output_files": {
            "guard_selection_ledger": {
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
            "source_confidence_guard_rows": summary["source_confidence_guard_rows"],
            "denominator_guard_rows": summary["denominator_guard_rows"],
            "adverse_context_guard_rows": summary["adverse_context_guard_rows"],
            "source_repair_rows": summary["source_repair_rows"],
            "proxy_delta_reference_rows": summary["proxy_delta_reference_rows"],
            "proxy_delta_reference_sum_not_r": summary["proxy_delta_reference_sum_not_r"],
        },
        "safe_flags": SAFE_FLAGS,
    }
    write_json(MANIFEST_PATH, manifest)
    return summary


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
