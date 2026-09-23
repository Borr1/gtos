"""Select concrete actions from moonshot controlled-score comparison rows."""

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
    apply_control_score_selection,
    safe_float,
    summarize_control_score_selection,
)

ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_LOCAL_UNIFIED_ACTION_INTAKE_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_CONTROL_SCORE_SELECTION_LEDGER_{DATE}.jsonl"
SUMMARY_PATH = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_CONTROL_SCORE_SELECTION_SUMMARY_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"MAIN_ORCH24_MOONSHOT_CONTROL_SCORE_SELECTION_OUTPUT_MANIFEST_{DATE}.json"

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


def read_control_score_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("main_action_class") != "CONTROL_SCORE":
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


def add_control_score_payload(
    row: dict[str, Any],
    *,
    sequence: int,
    generated_utc: str,
    input_sha256: str,
) -> dict[str, Any]:
    selected = apply_control_score_selection(row)
    selected.pop("_input_line_no", None)
    selected["control_score_selection_row_id"] = f"MAIN-ORCH24-MOONSHOT-CONTROL-SCORE-SELECTION-{sequence:06d}"
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
    selected["control_score_selection_not_standalone_promotion"] = True
    selected["missed_opportunity_audit"] = {
        "what_was_tried": "branch-local controlled-score comparison row was imported and selected on main",
        "why_not_live_or_independently_countable": (
            "controlled score delta is branch-local comparison evidence; it is not broker actual R or validation-safe R"
        ),
        "mechanism_remains_useful": selected.get("computed_decision"),
        "downstream_path": selected.get("downstream_path"),
        "next_action": selected.get("control_score_selection_decision"),
    }
    return selected


def build() -> dict[str, Any]:
    generated_utc = datetime.now(UTC).isoformat()
    input_sha256 = sha256_file(INPUT_LEDGER)
    input_rows = read_control_score_rows(INPUT_LEDGER)
    selected_rows = [
        add_control_score_payload(row, sequence=index, generated_utc=generated_utc, input_sha256=input_sha256)
        for index, row in enumerate(input_rows, 1)
    ]

    summary = summarize_control_score_selection(selected_rows)
    summary.update(
        {
            "route_id": "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION",
            "date": DATE,
            "generated_utc": generated_utc,
            "input_ledger": {
                "path": str(INPUT_LEDGER),
                "sha256": input_sha256,
                "size_bytes": INPUT_LEDGER.stat().st_size,
                "control_score_rows": len(input_rows),
            },
            "safe_flags": SAFE_FLAGS,
            "implement_default_off_rows": summary["control_score_selection_class_counts"].get(
                "IMPLEMENT_DEFAULT_OFF", 0
            ),
            "redesign_rows": summary["control_score_selection_class_counts"].get("REDESIGN", 0),
            "source_repair_rows": summary["control_score_selection_class_counts"].get("SOURCE_REPAIR", 0),
            "unclassified_rows": summary["control_score_selection_class_counts"].get("UNCLASSIFIED", 0),
            "implement_default_off_proxy_delta_reference_sum_not_r": proxy_sum(
                selected_rows, lambda row: row.get("control_score_selection_class") == "IMPLEMENT_DEFAULT_OFF"
            ),
            "redesign_proxy_delta_reference_sum_not_r": proxy_sum(
                selected_rows, lambda row: row.get("control_score_selection_class") == "REDESIGN"
            ),
            "source_repair_proxy_delta_reference_sum_not_r": proxy_sum(
                selected_rows, lambda row: row.get("control_score_selection_class") == "SOURCE_REPAIR"
            ),
            "control_score_class_by_source_component": {
                component: dict(
                    Counter(
                        row["control_score_selection_class"]
                        for row in selected_rows
                        if row.get("source_component") == component
                    )
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
        "description": "Concrete controlled-score comparison selection from moonshot score-with-control rows.",
        "input_files": {
            "moonshot_action_intake_ledger": summary["input_ledger"],
        },
        "output_files": {
            "control_score_selection_ledger": {
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
            "redesign_rows": summary["redesign_rows"],
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
