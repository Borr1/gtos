"""Repair stale KEEP branch labels on accepted SOURCE implementation rows."""

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
INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_HYPOTHETICAL_MERGE_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_PENDING_HYPOTHETICAL_MERGE_SUMMARY_{DATE}.json"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_BRANCH_LABEL_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_BRANCH_LABEL_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_BRANCH_LABEL_REPAIR_OUTPUT_MANIFEST_{DATE}.json"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

BRANCH_REPAIRS = {
    "KEEP_SOURCE_ACCEPTED_AFTER_M15_ORDERING_POSITIVE_PROXY": (
        "IMPLEMENT_DEFAULT_OFF_SOURCE_ACCEPTED_AFTER_M15_ORDERING_POSITIVE_PROXY"
    ),
    "KEEP_SOURCE_ACCEPTED_CONFIRMED_CHALLENGER_REPLAY_QUEUE": (
        "IMPLEMENT_DEFAULT_OFF_SOURCE_ACCEPTED_CONFIRMED_REPLAY_REQUIRES_EXACT_SOURCE"
    ),
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
        row.get("source_accepted_action_reclass_status") == "RECLASSIFIED_KEEP_TO_IMPLEMENT_DEFAULT_OFF"
        and row.get("action_class") == "IMPLEMENT_DEFAULT_OFF"
        and row.get("branch_decision") in BRANCH_REPAIRS
    )


def materialize(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    generated = utc_now()
    output: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    for source in rows:
        row = {key: value for key, value in source.items() if key != "_source_line_no"}
        row["generated_utc"] = generated
        if is_target(row):
            old_branch = str(row.get("branch_decision") or "")
            new_branch = BRANCH_REPAIRS[old_branch]
            row["before_source_accepted_branch_label_repair_branch_decision"] = old_branch
            row["before_source_accepted_branch_label_repair_implementation_decision"] = row.get(
                "implementation_decision"
            )
            row["branch_decision"] = new_branch
            row["implementation_decision"] = new_branch
            row["source_accepted_branch_label_repair_status"] = "REPAIRED_STALE_KEEP_BRANCH_TO_IMPLEMENT_DEFAULT_OFF"
            row["source_accepted_branch_label_repair_evidence"] = (
                "Action class and current action were already default-off implementation candidates; "
                "branch_decision now matches the concrete implementation decision."
            )
            stats["source_accepted_stale_keep_branch_labels_repaired"] += 1
            if safe_float(row.get("after_proxy_r")) is not None:
                stats["source_accepted_numeric_branch_labels_repaired"] += 1
        else:
            row["source_accepted_branch_label_repair_status"] = "NOT_TARGET_ROW"
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
        if row.get("source_accepted_branch_label_repair_status")
        == "REPAIRED_STALE_KEEP_BRANCH_TO_IMPLEMENT_DEFAULT_OFF"
    ]
    repaired_values = [value for row in repaired if (value := safe_float(row.get("after_proxy_r"))) is not None]
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_ACTION_AFTER_SOURCE_ACCEPTED_BRANCH_LABEL_REPAIR",
        "claim_boundary": (
            "Repairs stale KEEP branch labels on accepted SOURCE default-off implementation rows. "
            "Proxy R, exact R, action classes, and safe flags are unchanged."
        ),
        "rows": len(output_rows),
        "exact_r_rows": sum(1 for row in output_rows if row.get("exact_r") is not None),
        "action_class_counts_after": counter(output_rows, "action_class"),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "repaired_source_accepted_branch_labels": len(repaired),
        "repaired_source_accepted_numeric_proxy_rows": len(repaired_values),
        "repaired_source_accepted_proxy_r_sum": round(sum(repaired_values), 8),
        "repaired_branch_counts": counter(repaired, "branch_decision"),
        "repair_stats": stats,
        "previous_plate_decision": input_summary.get("plate_decision"),
        "plate_decision": "SOURCE_ACCEPTED_DEFAULT_OFF_BRANCH_LABELS_REPAIRED",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([OUTPUT_LEDGER, OUTPUT_SUMMARY]))
    print(
        json.dumps(
            {
                "rows_written": len(output_rows),
                "repaired_branch_labels": len(repaired),
                "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
                "proxy_r_sum_after": after_proxy["proxy_r_sum"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
