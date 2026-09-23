"""Close standalone-FVG source-repair rows when selected POI type is non-FVG.

The FVG scorer needs full FVG gap/lock metadata to score a true FVG row, but it
does not need those fields to exclude a candidate whose decision-time selected
H1 POI was already captured as OB/breaker/etc. This plate converts those rows
from source-repair requirements into row-level kill decisions without changing
proxy R, appending shadow logs, or opening live behavior.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-17"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
ROUTE_DIR = Path(__file__).resolve().parent
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

INPUT_ACTION_LEDGER = (
    ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_SRC_ENTRY_M15_REPAIRS_LEDGER_2026-05-16.jsonl"
)
INPUT_FVG_SCORER_LEDGER = (
    ROUTE_DIR / "MAIN_ORCH24_FVG_STRUCTURAL_SCORER_CANDIDATE_RECOMPUTE_LEDGER_2026-05-16.jsonl"
)
INPUT_STRATEGY_FOLLOW = Path("shadow_logs/strategy_follow_candidates.jsonl")
INPUT_FVG_OB = Path("shadow_logs/fvg_ob_confluence.jsonl")

OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STANDALONE_FVG_POI_TYPE_REPAIR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STANDALONE_FVG_POI_TYPE_REPAIR_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_STANDALONE_FVG_POI_TYPE_REPAIR_OUTPUT_MANIFEST_{DATE}.json"

TARGET_SOURCE_DECISION = "SOURCE_CAPTURE_REQUIRED_FOR_STANDALONE_FVG_SCORER"
REPAIRED_KILL_DECISION = (
    "KILL_STANDALONE_FVG_SCORER_FOR_NON_FVG_POI_ROWS_DECISION_TIME_POI_TYPE_REPAIR"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_source_line_no"] = line_no
            rows.append(row)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_utc(value: Any) -> datetime:
    if value is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def latest_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current = parse_utc(row.get("created_at_utc"))
        previous = parse_utc(latest.get(cid, {}).get("created_at_utc"))
        if current >= previous:
            latest[cid] = row
    return latest


def selected_poi_type_from_sources(
    candidate_id: str,
    strategy_follow: dict[str, dict[str, Any]],
    fvg_ob: dict[str, dict[str, Any]],
) -> tuple[str | None, str, int | None]:
    candidate = strategy_follow.get(candidate_id) or {}
    h1_setup = candidate.get("h1_setup")
    if isinstance(h1_setup, dict):
        poi_type = str(h1_setup.get("poi_type") or "").upper()
        if poi_type:
            return (
                poi_type,
                "shadow_logs/strategy_follow_candidates.jsonl:h1_setup.poi_type",
                candidate.get("_source_line_no"),
            )

    row = fvg_ob.get(candidate_id) or {}
    fields = row.get("decision_time_fields")
    if isinstance(fields, dict):
        poi_type = str(fields.get("h1_poi_type") or "").upper()
        if poi_type:
            return (
                poi_type,
                "shadow_logs/fvg_ob_confluence.jsonl:decision_time_fields.h1_poi_type",
                row.get("_source_line_no"),
            )

    return None, "NO_DECISION_TIME_SELECTED_POI_TYPE_SOURCE_FOUND", None


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def proxy_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [safe_float(row.get("after_proxy_r")) for row in rows]
    numeric = [value for value in values if value is not None]
    total = sum(numeric)
    return {
        "numeric_proxy_rows": len(numeric),
        "proxy_r_sum": round(total, 8),
        "proxy_r_mean": round(total / len(numeric), 8) if numeric else None,
    }


def build_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    generated = utc_now()
    action_rows = read_jsonl(INPUT_ACTION_LEDGER)
    fvg_rows = read_jsonl(INPUT_FVG_SCORER_LEDGER)
    strategy_follow = latest_by_candidate(read_jsonl(INPUT_STRATEGY_FOLLOW))
    fvg_ob = latest_by_candidate(read_jsonl(INPUT_FVG_OB))

    fvg_source_candidates = {
        str(row.get("candidate_id") or "")
        for row in fvg_rows
        if row.get("implementation_decision") == TARGET_SOURCE_DECISION
    }

    out: list[dict[str, Any]] = []
    repair_source_counts: Counter[str] = Counter()
    selected_poi_counts: Counter[str] = Counter()
    repaired_candidate_ids: set[str] = set()
    source_bound_fvg_candidate_ids: set[str] = set()
    missing_poi_candidate_ids: set[str] = set()

    for row in action_rows:
        clean = {k: v for k, v in row.items() if k != "_source_line_no"}
        clean["generated_utc"] = generated
        clean["route_id"] = ROUTE_ID
        clean["safe_flags"] = SAFE_FLAGS

        is_standalone_fvg_source_repair = (
            clean.get("implementation_decision") == TARGET_SOURCE_DECISION
        )
        if not is_standalone_fvg_source_repair:
            clean["standalone_fvg_poi_type_repair_status"] = "NOT_TARGET_ROW"
            out.append(clean)
            continue

        cid = str(clean.get("candidate_id") or "")
        poi_type, poi_source, poi_source_line = selected_poi_type_from_sources(
            cid, strategy_follow, fvg_ob
        )
        selected_poi_counts[poi_type or "MISSING"] += 1
        clean["standalone_fvg_poi_type_repair_source"] = poi_source
        clean["standalone_fvg_poi_type_repair_source_line_no"] = poi_source_line
        clean["standalone_fvg_selected_poi_type"] = poi_type

        if poi_type and poi_type != "FVG":
            clean["standalone_fvg_poi_type_repair_status"] = "REPAIRED_KILL_NON_FVG_SELECTED_POI"
            clean["action_class"] = "KILL"
            clean["coverage_status"] = "KILLED_WITH_DECISION_TIME_SOURCE_EVIDENCE"
            clean["branch_decision"] = "KILL_ROW_NOT_STANDALONE_FVG_POI"
            clean["implementation_decision"] = REPAIRED_KILL_DECISION
            clean["current_action"] = "KILL_NON_FVG_SELECTED_POI_FROM_STANDALONE_FVG_SCORER"
            clean["data_requirement_state"] = "CLOSED_BY_DECISION_TIME_SELECTED_POI_TYPE"
            clean["next_action"] = (
                "Do not score standalone FVG for this row; selected POI was not FVG at decision time."
            )
            clean["decision_evidence"] = "DECISION_TIME_SELECTED_POI_TYPE_IS_NOT_FVG"
            clean["scoring_boundary"] = "NO_STANDALONE_FVG_PROXY_R_FOR_NON_FVG_SELECTED_POI"
            clean["proxy_r_delta"] = 0.0
            clean["no_live_behavior"] = True
            clean["no_shadow_log_append"] = True
            repair_source_counts[poi_source] += 1
            repaired_candidate_ids.add(cid)
        elif poi_type == "FVG":
            clean["standalone_fvg_poi_type_repair_status"] = (
                "UNCHANGED_TRUE_FVG_POI_STILL_NEEDS_GAP_LOCK_METADATA"
            )
            clean["data_requirement_state"] = "FVG_POI_REMAINS_SOURCE_BOUND_TO_GAP_LOCK_METADATA"
            source_bound_fvg_candidate_ids.add(cid)
        else:
            clean["standalone_fvg_poi_type_repair_status"] = (
                "UNCHANGED_SELECTED_POI_TYPE_NOT_CAPTURED"
            )
            missing_poi_candidate_ids.add(cid)

        out.append(clean)

    before_action_counts = Counter(row.get("action_class") for row in action_rows)
    after_action_counts = Counter(row.get("action_class") for row in out)
    before_decision_counts = Counter(row.get("implementation_decision") for row in action_rows)
    after_decision_counts = Counter(row.get("implementation_decision") for row in out)
    before_proxy = proxy_stats(action_rows)
    after_proxy = proxy_stats(out)

    summary = {
        "route_id": ROUTE_ID,
        "evidence_class": "MAIN_ORCH24_ACTION_AFTER_STANDALONE_FVG_POI_TYPE_REPAIR",
        "generated_utc": generated,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": (
            "Versioned action queue after standalone-FVG selected-POI-type repair. "
            "Rows with decision-time non-FVG selected POI are killed for the standalone FVG scorer; "
            "true FVG rows remain source-bound to gap/lock metadata. No live behavior, shadow append, "
            "promotion, validation-safe claim, or exact broker R is opened."
        ),
        "rows": len(out),
        "input_action_rows": len(action_rows),
        "input_fvg_scorer_rows": len(fvg_rows),
        "source_repair_candidate_ids_in_fvg_scorer": len(fvg_source_candidates),
        "repaired_action_rows": sum(
            1 for row in out if row.get("standalone_fvg_poi_type_repair_status") == "REPAIRED_KILL_NON_FVG_SELECTED_POI"
        ),
        "repaired_candidate_ids": len(repaired_candidate_ids),
        "source_bound_true_fvg_candidate_ids": len(source_bound_fvg_candidate_ids),
        "missing_selected_poi_type_candidate_ids": len(missing_poi_candidate_ids),
        "selected_poi_type_counts_on_target_rows": dict(sorted(selected_poi_counts.items())),
        "repair_source_counts": dict(sorted(repair_source_counts.items())),
        "before_action_class_counts": dict(sorted(before_action_counts.items())),
        "action_class_counts": dict(sorted(after_action_counts.items())),
        "action_class_delta_vs_previous": {
            key: after_action_counts.get(key, 0) - before_action_counts.get(key, 0)
            for key in sorted(set(before_action_counts) | set(after_action_counts))
            if after_action_counts.get(key, 0) - before_action_counts.get(key, 0)
        },
        "before_implementation_decision_counts": dict(sorted(before_decision_counts.items())),
        "implementation_decision_counts": dict(sorted(after_decision_counts.items())),
        "standalone_fvg_source_repair_rows_before": before_decision_counts.get(
            TARGET_SOURCE_DECISION, 0
        ),
        "standalone_fvg_source_repair_rows_after": after_decision_counts.get(
            TARGET_SOURCE_DECISION, 0
        ),
        "standalone_fvg_kill_rows_after": after_decision_counts.get(
            REPAIRED_KILL_DECISION, 0
        ),
        "proxy_before": before_proxy,
        "proxy_after": after_proxy,
        "numeric_proxy_row_delta": after_proxy["numeric_proxy_rows"] - before_proxy["numeric_proxy_rows"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "exact_r_rows": 0,
        "plate_decision": "STANDALONE_FVG_NON_FVG_SELECTED_POI_SOURCE_REPAIR_CONSUMED",
    }
    return out, summary


def build_manifest(summary: dict[str, Any]) -> dict[str, Any]:
    outputs = {
        "ledger": OUTPUT_LEDGER,
        "summary": OUTPUT_SUMMARY,
    }
    inputs = {
        "input_action_ledger": INPUT_ACTION_LEDGER,
        "input_fvg_scorer_ledger": INPUT_FVG_SCORER_LEDGER,
        "strategy_follow_candidates": INPUT_STRATEGY_FOLLOW,
        "fvg_ob_confluence": INPUT_FVG_OB,
    }
    return {
        "route_id": ROUTE_ID,
        "evidence_class": summary["evidence_class"],
        "generated_utc": summary["generated_utc"],
        "safe_flags": SAFE_FLAGS,
        "inputs": {
            name: {
                "path": str(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else None,
                "bytes": path.stat().st_size if path.exists() else None,
            }
            for name, path in inputs.items()
        },
        "outputs": {
            name: {
                "path": str(path),
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
            for name, path in outputs.items()
        },
        "summary_counts": {
            "rows": summary["rows"],
            "repaired_action_rows": summary["repaired_action_rows"],
            "standalone_fvg_source_repair_rows_after": summary[
                "standalone_fvg_source_repair_rows_after"
            ],
            "numeric_proxy_row_delta": summary["numeric_proxy_row_delta"],
            "proxy_r_sum_delta": summary["proxy_r_sum_delta"],
        },
    }


def main() -> None:
    rows, summary = build_rows()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest(summary))
    print(
        json.dumps(
            {
                "ok": True,
                "rows": summary["rows"],
                "repaired_action_rows": summary["repaired_action_rows"],
                "standalone_fvg_source_repair_rows_after": summary[
                    "standalone_fvg_source_repair_rows_after"
                ],
                "proxy_r_sum_delta": summary["proxy_r_sum_delta"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
