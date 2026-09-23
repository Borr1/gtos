"""Isolate GBPJPY LONG adverse cluster from default-off implementation rows."""

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
INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_OB_EXACT_BOUNDS_REQUIREMENT_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_FVG_OB_EXACT_BOUNDS_REQUIREMENT_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_GBPJPY_LONG_ADVERSE_RECLASS_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_GBPJPY_LONG_ADVERSE_RECLASS_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_GBPJPY_LONG_ADVERSE_RECLASS_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

TARGET_BRANCHES = {
    "IMPLEMENT_SHADOW_SCORER_CAPTURED_METADATA_DEFAULT_OFF",
    "IMPLEMENT_SHADOW_SCORER_SWING_PROTECTED_STOP_DEFAULT_OFF",
}
NEW_BRANCH = "REDESIGN_GBPJPY_LONG_STRUCTURAL_FVG_OB_ADVERSE_CLUSTER_AVOID_FILTER_CANDIDATE"


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
    return (
        row.get("action_class") == "IMPLEMENT_DEFAULT_OFF"
        and row.get("symbol") == "GBPJPY"
        and row.get("side") == "LONG"
        and row.get("branch_decision") in TARGET_BRANCHES
    )


def materialize(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    generated = utc_now()
    output: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    for source in rows:
        row = {key: value for key, value in source.items() if key != "_source_line_no"}
        row["generated_utc"] = generated
        if is_target(row):
            before_proxy = safe_float(row.get("after_proxy_r"))
            row["before_gbpjpy_long_adverse_action_class"] = row.get("action_class")
            row["before_gbpjpy_long_adverse_branch_decision"] = row.get("branch_decision")
            row["action_class"] = "REDESIGN"
            row["coverage_status"] = "REDESIGN_REQUIRED_GBPJPY_LONG_ADVERSE_CLUSTER"
            row["branch_decision"] = NEW_BRANCH
            row["implementation_decision"] = NEW_BRANCH
            row["current_action"] = "REDESIGN_GBPJPY_LONG_STRUCTURAL_FVG_OB_AVOID_OR_CONTEXT_FILTER"
            row["implementation_candidate"] = "REDESIGN_GBPJPY_LONG_STRUCTURAL_FVG_OB_AVOID_OR_CONTEXT_FILTER"
            row["next_action"] = "REDESIGN_GBPJPY_LONG_STRUCTURAL_FVG_OB_AVOID_OR_CONTEXT_FILTER"
            row["decision_evidence"] = (
                "CURRENT_GBPJPY_LONG_STRUCTURAL_FVG_OB_DEFAULT_OFF_ROWS_SHOW_ALL_NUMERIC_PROXY_ROWS_NEGATIVE"
            )
            row["scoring_boundary"] = (
                "CURRENT_CLAIM_NOT_IMPLEMENTED_FOR_GBPJPY_LONG_UNTIL_AVOID_OR_CONTEXT_FILTER_REDESIGN"
            )
            row["gbpjpy_long_adverse_reclass_status"] = "RECLASSIFIED_IMPLEMENT_TO_REDESIGN_AVOID_FILTER_CANDIDATE"
            row["underlying_intelligence_preserved"] = True
            row["missed_opportunity_audit"] = {
                "kill_scope": "NOT_KILLED_REDESIGN_ADVERSE_CLUSTER",
                "preserve_as": "GBPJPY_LONG_AVOID_INVERSE_OR_CONTEXT_FILTER_CANDIDATE",
                "unsupported_current_claim": "BROAD_STRUCTURAL_OR_FVG_OB_DEFAULT_OFF_IMPLEMENTATION_FOR_GBPJPY_LONG",
                "what_was_tried": "CONDITION_SPLIT_BY_BRANCH_SYMBOL_SIDE_ON_CURRENT_PROXY_ROWS",
                "what_could_make_it_work": (
                    "SOURCE_BOUND_FILTER_THAT_SEPARATES_ADVERSE_GBPJPY_LONG_CONTEXTS_OR_INVERSE_AVOID_RULE"
                ),
                "next_route": (
                    "TEST_GBPJPY_LONG_BY_SESSION_TIMEFRAME_REGIME_SOURCE_AND_AS_AVOID_OR_INVERSE_FILTER"
                ),
            }
            stats["gbpjpy_long_adverse_rows_reclassified"] += 1
            if before_proxy is not None:
                stats["gbpjpy_long_adverse_numeric_rows_reclassified"] += 1
        else:
            row["gbpjpy_long_adverse_reclass_status"] = "NOT_TARGET_ROW"
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
    reclassified = [
        row
        for row in output_rows
        if row.get("gbpjpy_long_adverse_reclass_status")
        == "RECLASSIFIED_IMPLEMENT_TO_REDESIGN_AVOID_FILTER_CANDIDATE"
    ]
    reclassified_values = [value for row in reclassified if (value := safe_float(row.get("after_proxy_r"))) is not None]
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_ACTION_AFTER_GBPJPY_LONG_ADVERSE_RECLASS",
        "claim_boundary": (
            "Reclassifies GBPJPY LONG rows inside current structural/FVG-OB default-off scorer candidates as "
            "redesign/avoid-filter candidates because all numeric current proxy rows in that condition are negative. "
            "Underlying structural and FVG/OB intelligence is preserved; this is not a mechanism kill."
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
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "reclassified_gbpjpy_long_rows": len(reclassified),
        "reclassified_gbpjpy_long_numeric_proxy_rows": len(reclassified_values),
        "reclassified_gbpjpy_long_proxy_r_sum": round(sum(reclassified_values), 8),
        "reclassified_group_counts": counter(reclassified, "branch_decision"),
        "reclassified_primitive_counts": counter(reclassified, "primitive_family"),
        "repair_stats": stats,
        "previous_plate_decision": input_summary.get("plate_decision"),
        "plate_decision": "GBPJPY_LONG_ADVERSE_CLUSTER_RECLASSIFIED_TO_REDESIGN_AVOID_FILTER_CANDIDATE",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(
        json.dumps(
            {
                "rows_written": len(output_rows),
                "reclassified_rows": len(reclassified),
                "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
                "proxy_r_sum_after": after_proxy["proxy_r_sum"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
