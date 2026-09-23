"""Reclassify accepted SOURCE repair replay rows as default-off candidates.

The current source-cost/spread repair surface has accepted SOURCE rows whose
branch decisions and implementation candidates already name a default-off
replay queue, but their action class remained KEEP. This plate aligns the
action class with the repaired source decision without changing proxy R,
exact R, live behavior, or shadow logs.
"""

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
INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_DUPLICATE_MERGE_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_DUPLICATE_MERGE_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_ACTION_RECLASS_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_ACTION_RECLASS_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_ACTION_RECLASS_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

TARGET_PRIMITIVE = "source_cost_spread_bar_proxy_implication"
TARGET_BRANCHES = {
    "KEEP_SOURCE_ACCEPTED_AFTER_M15_ORDERING_POSITIVE_PROXY",
    "KEEP_SOURCE_ACCEPTED_CONFIRMED_CHALLENGER_REPLAY_QUEUE",
}


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
        row.get("primitive_family") == TARGET_PRIMITIVE
        and row.get("action_class") == "KEEP"
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
            branch = str(row.get("branch_decision") or "")
            before_proxy = safe_float(row.get("after_proxy_r"))
            row["before_source_accepted_action_reclass_action_class"] = row.get("action_class")
            row["before_source_accepted_action_reclass_current_action"] = row.get("current_action")
            row["action_class"] = "IMPLEMENT_DEFAULT_OFF"
            row["coverage_status"] = "OBSERVABLE_CANDIDATE_READY_DEFAULT_OFF"
            row["source_accepted_action_reclass_status"] = "RECLASSIFIED_KEEP_TO_IMPLEMENT_DEFAULT_OFF"
            if branch == "KEEP_SOURCE_ACCEPTED_AFTER_M15_ORDERING_POSITIVE_PROXY":
                row["implementation_candidate"] = (
                    "IMPLEMENT_DEFAULT_OFF_SOURCE_ACCEPTED_REPLAY_WITH_BOUNDED_POSITIVE_M15_PROXY"
                )
                row["current_action"] = (
                    "IMPLEMENT_DEFAULT_OFF_SOURCE_ACCEPTED_REPLAY_WITH_BOUNDED_POSITIVE_M15_PROXY"
                )
                row["next_action"] = (
                    "IMPLEMENT_DEFAULT_OFF_SOURCE_ACCEPTED_REPLAY_WITH_BOUNDED_POSITIVE_M15_PROXY"
                )
                row["source_accepted_action_reclass_evidence"] = (
                    "Accepted SOURCE branch has computed positive bounded M15 ordering proxy; reclassify from "
                    "passive keep queue to default-off observable replay candidate."
                )
                stats["accepted_source_positive_proxy_rows_reclassified"] += 1
                if before_proxy is not None:
                    stats["accepted_source_positive_numeric_rows_reclassified"] += 1
            else:
                row["implementation_candidate"] = (
                    "IMPLEMENT_DEFAULT_OFF_SOURCE_ACCEPTED_CONFIRMED_REPLAY_WITH_EXACT_TICK_REPAIR_REQUIREMENT"
                )
                row["current_action"] = (
                    "IMPLEMENT_DEFAULT_OFF_SOURCE_ACCEPTED_CONFIRMED_REPLAY_WITH_EXACT_TICK_REPAIR_REQUIREMENT"
                )
                row["next_action"] = (
                    "IMPLEMENT_DEFAULT_OFF_SOURCE_ACCEPTED_CONFIRMED_REPLAY_WITH_EXACT_TICK_REPAIR_REQUIREMENT"
                )
                row["source_accepted_action_reclass_evidence"] = (
                    "Accepted SOURCE branch is confirmed by bar-spread proxy but lacks a scalar current R; "
                    "reclassify as default-off replay candidate with exact tick/source repair requirement."
                )
                stats["accepted_source_confirmed_no_scalar_rows_reclassified"] += 1
            stats["source_accepted_rows_reclassified_to_implement_default_off"] += 1
        else:
            row["source_accepted_action_reclass_status"] = "NOT_TARGET_ROW"
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
        if row.get("source_accepted_action_reclass_status") == "RECLASSIFIED_KEEP_TO_IMPLEMENT_DEFAULT_OFF"
    ]
    reclassified_values = [
        value for row in reclassified if (value := safe_float(row.get("after_proxy_r"))) is not None
    ]
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_ACTION_RECLASS",
        "claim_boundary": (
            "Aligns accepted SOURCE repair replay rows with their repaired default-off branch decisions. "
            "Proxy R and exact R are unchanged; accepted no-scalar rows remain source-repair candidates, "
            "not validation or promotion evidence."
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
        "reclassified_source_accepted_rows": len(reclassified),
        "reclassified_source_accepted_numeric_proxy_rows": len(reclassified_values),
        "reclassified_source_accepted_proxy_r_sum": round(sum(reclassified_values), 8),
        "reclassified_branch_counts": counter(reclassified, "branch_decision"),
        "repair_stats": stats,
        "previous_plate_decision": input_summary.get("plate_decision"),
        "plate_decision": "SOURCE_ACCEPTED_REPLAY_ROWS_RECLASSIFIED_AS_IMPLEMENT_DEFAULT_OFF",
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
