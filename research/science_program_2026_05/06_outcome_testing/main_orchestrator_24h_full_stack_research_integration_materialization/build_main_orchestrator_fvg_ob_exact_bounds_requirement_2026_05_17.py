"""Move FVG/OB both-fire rows with missing exact bounds to source requirement."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_BRANCH_LABEL_REPAIR_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_BRANCH_LABEL_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_OB_EXACT_BOUNDS_REQUIREMENT_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_OB_EXACT_BOUNDS_REQUIREMENT_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_OB_EXACT_BOUNDS_REQUIREMENT_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

TARGET_BRANCH = "IMPLEMENT_SHADOW_SCORER_FVG_OB_BUCKET_DEFAULT_OFF_WITH_EXACT_BOUNDS_MISSING"
NEW_BRANCH = "PRESERVE_FVG_OB_BUCKET_BOTH_FIRE_EXACT_BOUNDS_REQUIRED"


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(ROUTE_DIR)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                row = json.loads(line)
                row["_source_line_no"] = line_no
                rows.append(row)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def proxy_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [value for row in rows if (value := safe_float(row.get("after_proxy_r"))) is not None]
    return {
        "numeric_proxy_rows": len(values),
        "proxy_r_sum": round(sum(values), 8),
        "proxy_r_mean": round(sum(values) / len(values), 8) if values else None,
    }


def counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(Counter(str(row.get(field) or "") for row in rows))


def is_target(row: dict[str, Any]) -> bool:
    return row.get("branch_decision") == TARGET_BRANCH


def materialize(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    generated = utc_now()
    output: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    for source in rows:
        row = {key: value for key, value in source.items() if key != "_source_line_no"}
        row["generated_utc"] = generated
        if is_target(row):
            before_proxy = safe_float(row.get("after_proxy_r"))
            row["before_fvg_ob_exact_bounds_requirement_action_class"] = row.get("action_class")
            row["before_fvg_ob_exact_bounds_requirement_after_proxy_r"] = before_proxy
            row["before_fvg_ob_exact_bounds_requirement_branch_decision"] = row.get("branch_decision")
            row["action_class"] = "PRESERVE_REQUIREMENT"
            row["coverage_status"] = "SOURCE_REQUIREMENT_EXACT_FVG_OB_BOUNDS_MISSING"
            row["branch_decision"] = NEW_BRANCH
            row["implementation_decision"] = NEW_BRANCH
            row["current_action"] = "PRESERVE_FVG_OB_EXACT_BOUNDS_AND_ENTRY_LOCK_SOURCE_REQUIREMENT"
            row["implementation_candidate"] = "PRESERVE_FVG_OB_EXACT_BOUNDS_AND_ENTRY_LOCK_SOURCE_REQUIREMENT"
            row["next_action"] = "PRESERVE_FVG_OB_EXACT_BOUNDS_AND_ENTRY_LOCK_SOURCE_REQUIREMENT"
            row["decision_evidence"] = "DECISION_TIME_FVG_OB_BUCKET_BOTH_FIRE_EXACT_BOUNDS_MISSING"
            row["scoring_boundary"] = "FVG_OB_CONFLUENCE_BUCKET_SOURCE_REQUIREMENT_EXACT_BOUNDS_MISSING"
            row["data_requirement_state"] = "EXACT_FVG_OB_BOUNDS_AND_ENTRY_LOCK_SOURCE_REQUIRED"
            row["fvg_ob_exact_bounds_requirement_status"] = (
                "MOVED_DEFAULT_OFF_ROW_TO_SOURCE_REQUIREMENT_EXACT_BOUNDS_MISSING"
            )
            row["fvg_ob_exact_bounds_proxy_reference_r"] = before_proxy
            row["after_proxy_r"] = None
            row["current_claim_proxy_counted"] = False
            row["underlying_intelligence_preserved"] = True
            row["missed_opportunity_audit"] = {
                "kill_scope": "NOT_KILLED_SOURCE_REQUIREMENT",
                "preserve_as": "FVG_OB_EXACT_BOUNDS_SOURCE_CAPTURE_REQUIREMENT",
                "unsupported_current_claim": "DEFAULT_OFF_FVG_OB_SCORER_FROM_BUCKET_ONLY_SHARED_PATH_PROXY",
                "what_was_tried": "DECISION_TIME_FVG_OB_BUCKET_BOTH_FIRE_WITH_SHARED_CANDIDATE_PATH_PROXY",
                "what_could_make_it_work": "EXACT_FVG_OB_BOUNDS_AND_ENTRY_LOCK_BINDING_AT_DECISION_TIME",
                "next_route": "CAPTURE_OR_RECONSTRUCT_EXACT_FVG_OB_BOUNDS_BEFORE_SCORING_BUCKET_ONLY_ROWS",
            }
            stats["fvg_ob_exact_bounds_rows_moved_to_source_requirement"] += 1
            if before_proxy is not None:
                stats["fvg_ob_exact_bounds_numeric_proxy_rows_excluded"] += 1
        else:
            row["fvg_ob_exact_bounds_requirement_status"] = "NOT_TARGET_ROW"
        output.append(row)
    return output, dict(stats)


def build_manifest(output_paths: list[Path]) -> dict[str, Any]:
    inputs = [INPUT_LEDGER, INPUT_SUMMARY]
    return {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "input_artifacts": {
            str(path.relative_to(REPO_ROOT)): {
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
            for path in inputs
        },
        "output_artifacts": {
            path.name: {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
            for path in output_paths
        },
        "safe_flags": SAFE_FLAGS,
    }


def main() -> None:
    input_rows = read_jsonl(INPUT_LEDGER)
    input_summary = read_json(INPUT_SUMMARY)
    output_rows, stats = materialize(input_rows)
    write_jsonl(OUTPUT_LEDGER, output_rows)

    before_proxy = proxy_summary(input_rows)
    after_proxy = proxy_summary(output_rows)
    repaired = [
        row
        for row in output_rows
        if row.get("fvg_ob_exact_bounds_requirement_status")
        == "MOVED_DEFAULT_OFF_ROW_TO_SOURCE_REQUIREMENT_EXACT_BOUNDS_MISSING"
    ]
    repaired_values = [
        value for row in repaired if (value := safe_float(row.get("fvg_ob_exact_bounds_proxy_reference_r"))) is not None
    ]
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_ACTION_AFTER_FVG_OB_EXACT_BOUNDS_REQUIREMENT",
        "claim_boundary": (
            "Moves bucket-only FVG/OB both-fire rows with missing exact bounds out of implementation R and "
            "into source-completeness requirements. The underlying confluence intelligence is preserved."
        ),
        "rows": len(output_rows),
        "exact_r_rows": sum(1 for row in output_rows if row.get("exact_r") is not None),
        "action_class_counts_before": counter(input_rows, "action_class"),
        "action_class_counts_after": counter(output_rows, "action_class"),
        "action_class_delta_vs_previous": {
            key: counter(output_rows, "action_class").get(key, 0) - counter(input_rows, "action_class").get(key, 0)
            for key in sorted(set(counter(input_rows, "action_class")) | set(counter(output_rows, "action_class")))
            if counter(output_rows, "action_class").get(key, 0) != counter(input_rows, "action_class").get(key, 0)
        },
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_delta": after_proxy["numeric_proxy_rows"] - before_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "fvg_ob_exact_bounds_rows_moved": len(repaired),
        "fvg_ob_exact_bounds_numeric_proxy_rows_excluded": len(repaired_values),
        "fvg_ob_exact_bounds_proxy_reference_r_sum": round(sum(repaired_values), 8),
        "repair_stats": stats,
        "previous_plate_decision": input_summary.get("plate_decision"),
        "plate_decision": "FVG_OB_BUCKET_ONLY_EXACT_BOUNDS_MISSING_ROWS_MOVED_TO_SOURCE_REQUIREMENT",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(
        json.dumps(
            {
                "rows_written": len(output_rows),
                "fvg_ob_exact_bounds_rows_moved": len(repaired),
                "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
                "proxy_r_sum_after": after_proxy["proxy_r_sum"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
