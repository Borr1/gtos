from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}
NO_TAG = "NO_SYSTEM_IMPLICATION_TAG"


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
ROUTE_DIR = Path(__file__).resolve().parent


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("/", "\\")


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if isinstance(row, dict):
                row["_source_line_no"] = line_no
                rows.append(row)
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def artifact_record(label: str, path: Path) -> dict[str, Any]:
    return {
        "label": label,
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256(path),
    }


def sanitize(value: str) -> str:
    sanitized = re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_")
    return sanitized or "MISSING"


def normalized_tags(row: dict[str, Any]) -> list[str]:
    tags = row.get("evidence", {}).get("system_implication_tags") or []
    normalized = [str(tag) for tag in tags if str(tag).strip()]
    return normalized or [NO_TAG]


def queue_class_for_tag(tag: str) -> str:
    if tag == NO_TAG:
        return "READY8_OR_PRIOR_CONTROL_FAILURE_INTELLIGENCE_QUEUE"
    if tag.startswith("ACTIVE_") or tag.endswith("_REQUIRED") or "REQUIRED" in tag:
        return "ACTIVE_REPAIR_STRESS_OR_SOURCE_REQUIREMENT_QUEUE"
    if "AVOID" in tag or "FAR_MISS" in tag:
        return "AVOID_FILTER_OR_FAILURE_CONTROL_QUEUE"
    if "ENTRY_GEOMETRY" in tag or "MARKET_ENTRY" in tag or "RETEST" in tag or "NEAR_MISS" in tag:
        return "ENTRY_OR_RETEST_REDESIGN_QUEUE"
    if "M1" in tag or "M15" in tag or "ORDERING" in tag or "FILL_BAR" in tag:
        return "PATH_ORDERING_OR_FILLABILITY_STRESS_QUEUE"
    if "SOURCE" in tag or "SPREAD" in tag or "SIERRA" in tag:
        return "SOURCE_ACQUISITION_OR_COST_STRESS_QUEUE"
    if "BASELINE" in tag or "PRESERVE" in tag:
        return "PRESERVE_DESCRIPTOR_OR_CONTROL_QUEUE"
    return "GENERAL_SYSTEM_IMPLICATION_QUEUE"


def numeric(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def stats(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "mean": None, "min": None, "max": None}
    return {
        "count": len(values),
        "mean": sum(values) / len(values),
        "min": min(values),
        "max": max(values),
    }


def count_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def add_counter(counter: Counter[str], value: Any) -> None:
    counter[str(value) if value is not None else "MISSING"] += 1


def make_tag_aggregate(tag: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    midpoint_values = [value for row in rows if (value := numeric(row.get("proxy_r_midpoint"))) is not None]
    conservative_values = [
        value for row in rows if (value := numeric(row.get("proxy_r_conservative"))) is not None
    ]
    optimistic_values = [value for row in rows if (value := numeric(row.get("proxy_r_optimistic"))) is not None]

    bucket_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    symbol_counts: Counter[str] = Counter()
    session_counts: Counter[str] = Counter()
    branch_queue_status_counts: Counter[str] = Counter()
    source_file_counts: Counter[str] = Counter()
    source_sha_counts: Counter[str] = Counter()

    interval_straddles_zero = 0
    midpoint_positive = 0
    midpoint_negative = 0
    midpoint_zero = 0
    source_decision_ids: list[str] = []

    for row in rows:
        evidence = row.get("evidence") or {}
        add_counter(bucket_counts, row.get("bucket"))
        add_counter(decision_counts, row.get("decision"))
        add_counter(family_counts, row.get("family"))
        add_counter(symbol_counts, row.get("symbol"))
        add_counter(session_counts, row.get("session"))
        add_counter(branch_queue_status_counts, evidence.get("branch_queue_status"))
        add_counter(source_file_counts, evidence.get("source_file"))
        add_counter(source_sha_counts, evidence.get("source_sha256"))
        source_decision_ids.append(str(row.get("decision_id")))

        midpoint = numeric(row.get("proxy_r_midpoint"))
        conservative = numeric(row.get("proxy_r_conservative"))
        optimistic = numeric(row.get("proxy_r_optimistic"))
        if midpoint is not None:
            if midpoint > 0:
                midpoint_positive += 1
            elif midpoint < 0:
                midpoint_negative += 1
            else:
                midpoint_zero += 1
        if conservative is not None and optimistic is not None and conservative <= 0 <= optimistic:
            interval_straddles_zero += 1

    return {
        "row_type": "TAG_AGGREGATE_ROW",
        "row_id": f"MAIN-ORCH24-SURVIVOR-FAILURE-IMPLICATION-TAG-{sanitize(tag)}",
        "implication_tag": tag,
        "queue_class": queue_class_for_tag(tag),
        "source_decision_rows": len(rows),
        "source_decision_ids": sorted(source_decision_ids),
        "bucket_counts": count_dict(bucket_counts),
        "decision_counts": count_dict(decision_counts),
        "family_counts": count_dict(family_counts),
        "symbol_counts": count_dict(symbol_counts),
        "session_counts": count_dict(session_counts),
        "branch_queue_status_counts": count_dict(branch_queue_status_counts),
        "source_file_counts": count_dict(source_file_counts),
        "source_sha256_counts": count_dict(source_sha_counts),
        "proxy_r_midpoint_stats": stats(midpoint_values),
        "proxy_r_conservative_stats": stats(conservative_values),
        "proxy_r_optimistic_stats": stats(optimistic_values),
        "proxy_r_midpoint_split": {
            "positive": midpoint_positive,
            "negative": midpoint_negative,
            "zero": midpoint_zero,
            "missing": len(rows) - len(midpoint_values),
            "interval_straddles_zero": interval_straddles_zero,
        },
        "safe_flags": SAFE_FLAGS,
    }


def main() -> None:
    generated_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    source_path = ROUTE_DIR / f"MAIN_ORCH24_SURVIVOR_FAILURE_IMPLEMENTATION_DECISION_LEDGER_{DATE}.jsonl"
    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_SURVIVOR_FAILURE_IMPLICATION_QUEUE_LEDGER_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_SURVIVOR_FAILURE_IMPLICATION_QUEUE_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_SURVIVOR_FAILURE_IMPLICATION_QUEUE_OUTPUT_MANIFEST_{DATE}.json"

    source_rows = read_jsonl(source_path)
    source_sha = sha256(source_path)

    source_decision_rows: list[dict[str, Any]] = []
    tag_to_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    bucket_counts: Counter[str] = Counter()
    decision_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    symbol_counts: Counter[str] = Counter()
    session_counts: Counter[str] = Counter()
    queue_presence_counts: Counter[str] = Counter()
    tag_assignment_counts: Counter[str] = Counter()
    source_file_counts: Counter[str] = Counter()

    for index, row in enumerate(source_rows, start=1):
        evidence = row.get("evidence") or {}
        tags = normalized_tags(row)
        queue_classes = sorted({queue_class_for_tag(tag) for tag in tags})
        for tag in tags:
            tag_to_rows[tag].append(row)
            tag_assignment_counts[tag] += 1
        for queue_class in queue_classes:
            queue_presence_counts[queue_class] += 1

        add_counter(bucket_counts, row.get("bucket"))
        add_counter(decision_counts, row.get("decision"))
        add_counter(family_counts, row.get("family"))
        add_counter(symbol_counts, row.get("symbol"))
        add_counter(session_counts, row.get("session"))
        add_counter(source_file_counts, evidence.get("source_file"))

        source_decision_rows.append(
            {
                "row_type": "SOURCE_DECISION_ROW",
                "row_id": f"MAIN-ORCH24-SURVIVOR-FAILURE-IMPLICATION-SOURCE-{index:06d}",
                "source_line_no": row.get("_source_line_no"),
                "source_decision_id": row.get("decision_id"),
                "source_result_id": row.get("source_result_id"),
                "bucket": row.get("bucket"),
                "decision": row.get("decision"),
                "family": row.get("family"),
                "symbol": row.get("symbol"),
                "session": row.get("session"),
                "proxy_r_conservative": row.get("proxy_r_conservative"),
                "proxy_r_midpoint": row.get("proxy_r_midpoint"),
                "proxy_r_optimistic": row.get("proxy_r_optimistic"),
                "system_implication_tags": tags,
                "queue_classes": queue_classes,
                "source_evidence": {
                    "source_file": evidence.get("source_file"),
                    "source_sha256": evidence.get("source_sha256"),
                    "branch_queue_status": evidence.get("branch_queue_status"),
                    "proxy_outcome_counts": evidence.get("proxy_outcome_counts", {}),
                },
                "input_hashes": {
                    "survivor_failure_implementation_decision_ledger": source_sha,
                },
                "safe_flags": SAFE_FLAGS,
            }
        )

    tag_aggregate_rows = [make_tag_aggregate(tag, rows) for tag, rows in sorted(tag_to_rows.items())]
    output_rows = source_decision_rows + tag_aggregate_rows
    write_jsonl(ledger_path, output_rows)

    midpoint_values = [
        value for row in source_rows if (value := numeric(row.get("proxy_r_midpoint"))) is not None
    ]
    conservative_values = [
        value for row in source_rows if (value := numeric(row.get("proxy_r_conservative"))) is not None
    ]
    optimistic_values = [
        value for row in source_rows if (value := numeric(row.get("proxy_r_optimistic"))) is not None
    ]

    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "source_ledger": rel(source_path),
        "source_ledger_sha256": source_sha,
        "source_decision_rows": len(source_rows),
        "output_ledger_rows": len(output_rows),
        "source_row_output_rows": len(source_decision_rows),
        "tag_aggregate_rows": len(tag_aggregate_rows),
        "unique_system_implication_tags": len([tag for tag in tag_to_rows if tag != NO_TAG]),
        "aggregate_groups_including_no_tag": len(tag_to_rows),
        "source_rows_without_system_implication_tags": len(tag_to_rows.get(NO_TAG, [])),
        "system_implication_tag_assignments_excluding_no_tag": sum(
            count for tag, count in tag_assignment_counts.items() if tag != NO_TAG
        ),
        "tag_assignments_including_no_tag_group": sum(tag_assignment_counts.values()),
        "bucket_counts": count_dict(bucket_counts),
        "decision_counts": count_dict(decision_counts),
        "family_counts": count_dict(family_counts),
        "symbol_counts": count_dict(symbol_counts),
        "session_counts": count_dict(session_counts),
        "source_file_counts": count_dict(source_file_counts),
        "queue_presence_counts": count_dict(queue_presence_counts),
        "system_implication_tag_counts": count_dict(tag_assignment_counts),
        "proxy_r_midpoint_stats": stats(midpoint_values),
        "proxy_r_conservative_stats": stats(conservative_values),
        "proxy_r_optimistic_stats": stats(optimistic_values),
        "plate_decision": "SURVIVOR_FAILURE_IMPLEMENTATION_TAGS_MATERIALIZED_INTO_FULL_ROW_AND_AGGREGATE_QUEUE",
        "next_use_boundary": (
            "Queue rows are research/system-design decision aids only; they are not validation, promotion, "
            "live-effect, or default-on trading logic."
        ),
        "safe_flags": SAFE_FLAGS,
    }
    write_json(summary_path, summary)

    manifest = {
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "artifact_count": 2,
        "artifacts": [
            artifact_record("implication_queue_ledger", ledger_path),
            artifact_record("summary", summary_path),
        ],
        "input_artifacts": [
            artifact_record("survivor_failure_implementation_decision_ledger", source_path),
        ],
        "safe_flags": SAFE_FLAGS,
    }
    write_json(manifest_path, manifest)

    print(
        json.dumps(
            {
                "ok": True,
                "source_decision_rows": len(source_rows),
                "tag_aggregate_rows": len(tag_aggregate_rows),
                "output_ledger": str(ledger_path),
                "summary": str(summary_path),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
