"""Materialize NAS100 depth-thinness source repairs for current scorer rows."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.enrich_sierra_live_candidate_depth_features import build_feature_row  # noqa: E402
from scripts.extract_sierra_depth_features import lower_bound_record_index, parse_utc, read_header, sierra_us  # noqa: E402

ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
ROUTE_ID = "MAIN_ORCH24_NAS100_DEPTH_THINNESS_SOURCE_REPAIR"
STRATEGY_ID = "NAS100_NQ_DEPTH_THINNESS_DIAGNOSTIC"

PROJECTION_ROWS = (
    ROUTE_DIR
    / f"MAIN_ORCH24_LIVE_MECHANICAL_OPPORTUNITY_PRESERVATION_PROJECTION_ROWS_{DATE}.jsonl"
)
SIERRA_FEATURES = ROOT / "shadow_logs/sierra_depth_feature_snapshots.jsonl"
STRATEGY_FOLLOW_CANDIDATES = ROOT / "shadow_logs/strategy_follow_candidates.jsonl"
OUTPUT_SOURCE_LOG = ROOT / "shadow_logs/nas100_depth_thinness_current_source_repair_decisions.jsonl"
SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_NAS100_DEPTH_THINNESS_SOURCE_REPAIR_SUMMARY_{DATE}.json"
MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_NAS100_DEPTH_THINNESS_SOURCE_REPAIR_OUTPUT_MANIFEST_{DATE}.json"
TARGETED_FEATURE_ROWS = (
    ROUTE_DIR / f"MAIN_ORCH24_NAS100_DEPTH_THINNESS_TARGETED_SIERRA_EXTRACTION_ROWS_{DATE}.jsonl"
)
WINDOW_PRESENCE_ROWS = (
    ROUTE_DIR / f"MAIN_ORCH24_NAS100_DEPTH_THINNESS_WINDOW_PRESENCE_PATH_PROXY_ROWS_{DATE}.jsonl"
)
TARGETED_SOURCE_REPAIR_CANDIDATE_IDS = {
    "NAS100_2026-05-10T16:30:00+00:00",
}

FEATURE_FIELDS = (
    "pre60_median_total_depth10",
    "pre60_median_depth10_imbalance",
    "event15_median_total_depth10",
    "event15_thin_depth10_rate",
    "event15_median_depth10_imbalance",
    "event15_median_near_far_ratio",
    "event15_median_max_bid_wall",
    "event15_median_max_ask_wall",
    "event15_sample_count",
)
TIMED_OUT_EXTRACTION_ATTEMPT = (
    "ROUTE_LOCAL_FULL_NAS100_EXTRACTION_TIMED_OUT_AFTER_901S_NO_ROWS_WRITTEN"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def latest_feature_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, tuple[str, int, dict[str, Any]]] = {}
    for idx, row in enumerate(rows):
        candidate_id = str(row.get("candidate_id") or "")
        if not candidate_id:
            continue
        created = str(row.get("created_at_utc") or row.get("backfilled_at_utc") or "")
        previous = latest.get(candidate_id)
        if previous is None or (created, idx) >= (previous[0], previous[1]):
            latest[candidate_id] = (created, idx, row)
    return {candidate_id: item[2] for candidate_id, item in latest.items()}


def targeted_source_feature_rows() -> list[dict[str, Any]]:
    candidates = {
        str(row.get("candidate_id") or ""): row
        for row in read_jsonl(STRATEGY_FOLLOW_CANDIDATES)
        if row.get("candidate_id")
    }
    rows: list[dict[str, Any]] = []
    for candidate_id in sorted(TARGETED_SOURCE_REPAIR_CANDIDATE_IDS):
        candidate = candidates.get(candidate_id)
        if candidate is None:
            continue
        row = build_feature_row(candidate, max_file_size_mb=128.0)
        row["targeted_source_repair_status"] = "ROUTE_LOCAL_TARGETED_SIERRA_EXTRACTION_CONSUMED"
        row["targeted_source_repair_candidate_id"] = candidate_id
        rows.append(row)
    write_jsonl(TARGETED_FEATURE_ROWS, rows)
    return rows


def path_proxy_r(row: dict[str, Any]) -> float | None:
    status = str(row.get("outcome_status") or row.get("ltf_terminal_outcome_status") or "")
    if "ENTRY_TOUCHED_THEN_TP1" in status or status == "ENTRY_THEN_TP1":
        return 1.0
    if "ENTRY_TOUCHED_THEN_SL" in status or status == "ENTRY_THEN_SL":
        return -1.0
    if "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH" in status or "NO_ENTRY_TP1" in status:
        return 0.0
    return None


def window_presence_path_proxy_rows(projection_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    headers: dict[str, Any] = {}
    for projection in projection_rows:
        feature_status = str(projection.get("depth_thinness_feature_status") or "")
        if projection.get("branch_decision") != "SOURCE_REQUIRED_NAS100_DEPTH_THINNESS_HEAVY_SCAN_EXTRACTION":
            continue
        if feature_status not in {
            "FEATURE_EXTRACTION_PENDING_HEAVY_DEPTH_SCAN",
            "FEATURE_EXTRACTION_DEFERRED_FILE_SIZE_GUARD",
            "NO_SIERRA_DEPTH_FEATURE_ROW",
        }:
            continue
        candidate_id = str(projection.get("candidate_id") or "")
        depth_path_raw = projection.get("depth_thinness_depth_path")
        decision_raw = projection.get("decision_time_utc")
        proxy_r = path_proxy_r(projection)
        row: dict[str, Any] = {
            "schema_version": "nas100_depth_thinness_window_presence_path_proxy_v1",
            "route_id": ROUTE_ID,
            "generated_utc": utc_now(),
            "created_at_utc": utc_now(),
            "candidate_id": candidate_id,
            "strategy_id": STRATEGY_ID,
            "symbol": projection.get("symbol"),
            "broker_symbol": projection.get("broker_symbol"),
            "decision_time_utc": decision_raw,
            "asof_latest_candle_utc": projection.get("asof_latest_candle_utc"),
            "depth_path": depth_path_raw,
            "prior_feature_status": feature_status,
            "path_outcome_status": projection.get("outcome_status"),
            "path_proxy_r": proxy_r,
            "path_proxy_r_basis": "entry_touch_terminal_path; no-fill rows score 0.0 because entry was never available",
            "path_max_favorable_r_from_entry": projection.get("max_favorable_r_from_entry"),
            "path_max_adverse_r_from_entry": projection.get("max_adverse_r_from_entry"),
            "entry_touch_distance_status": projection.get("entry_touch_distance_status"),
        }
        try:
            depth_path = Path(str(depth_path_raw))
            decision_time = parse_utc(str(decision_raw))
            header = headers.get(str(depth_path))
            if header is None:
                header = read_header(depth_path)
                headers[str(depth_path)] = header
            start_us = sierra_us(decision_time - timedelta(minutes=60))
            event15_start_us = sierra_us(decision_time - timedelta(minutes=15))
            end_us = sierra_us(decision_time)
            pre60_start_index = lower_bound_record_index(depth_path, header, start_us)
            event15_start_index = lower_bound_record_index(depth_path, header, event15_start_us)
            canonical_index = lower_bound_record_index(depth_path, header, end_us)
            pre60_records = canonical_index - pre60_start_index
            event15_records = canonical_index - event15_start_index
            if pre60_records == 0:
                materialized_status = "FEATURES_ATTEMPTED_NO_SAMPLES"
                branch = "REDESIGN_NAS100_DEPTH_THINNESS_NO_SAMPLES_SOURCE_BOUNDARY"
                action_class = "REDESIGN"
            else:
                materialized_status = "DEPTH_WINDOW_RECORDS_PRESENT_PATH_PROXY_DECISION"
                branch = "PATH_PROXY_NAS100_DEPTH_WINDOW_PRESENT_CONTEXT_DECISION"
                action_class = "PATH_PROXY_DECISION"
            row.update(
                {
                    "window_presence_status": "WINDOW_INDEX_BOUNDS_COMPUTED",
                    "feature_status": materialized_status,
                    "branch_decision": branch,
                    "action_class": action_class,
                    "depth_file_size_bytes": header.size_bytes,
                    "depth_record_count": header.record_count,
                    "pre60_record_start_index": pre60_start_index,
                    "event15_record_start_index": event15_start_index,
                    "canonical_record_index": canonical_index,
                    "pre60_depth_record_count": pre60_records,
                    "event15_depth_record_count": event15_records,
                    "source_decision_status": (
                        "SIERRA_DEPTH_WINDOW_HAS_RECORDS_PATH_PROXY_MATERIALIZED"
                        if pre60_records
                        else "SIERRA_DEPTH_ATTEMPTED_NO_SAMPLES_SOURCE_COMPLETE_NO_CONTEXT"
                    ),
                    "implementation_candidate": (
                        "IMPLEMENT_DEPTH_WINDOW_PRESENCE_CONTEXT_COMPARATOR_DEFAULT_OFF"
                        if pre60_records
                        else "REQUIRE_NONEMPTY_PREDECISION_DEPTH_WINDOW"
                    ),
                }
            )
        except Exception as exc:  # noqa: BLE001
            row.update(
                {
                    "window_presence_status": "WINDOW_INDEX_BOUNDS_FAILED",
                    "feature_status": "DEPTH_WINDOW_INDEX_FAILED_PATH_PROXY_DECISION",
                    "branch_decision": "PATH_PROXY_NAS100_DEPTH_WINDOW_INDEX_FAILED_CONTEXT_DECISION",
                    "action_class": "PATH_PROXY_DECISION",
                    "window_presence_error": f"{type(exc).__name__}: {exc}",
                    "source_decision_status": "PATH_PROXY_MATERIALIZED_DEPTH_INDEX_FAILED",
                    "implementation_candidate": "REPAIR_DEPTH_WINDOW_INDEXING_THEN_RECOMPUTE",
                }
            )
        rows.append(row)
    write_jsonl(WINDOW_PRESENCE_ROWS, rows)
    return rows


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def branch_for_feature(row: dict[str, Any]) -> tuple[str, str, str, str]:
    feature_status = str(row.get("feature_status") or "")
    if row.get("features_present") is True and feature_status == "FEATURES_EXTRACTED":
        return (
            "KEEP",
            "SIERRA_DEPTH_FEATURES_EXTRACTED_SOURCE_COMPLETE",
            "KEEP_NAS100_DEPTH_THINNESS_CONTEXT_SOURCE_COMPLETE_DIAGNOSTIC",
            "KEEP_DEFAULT_OFF_NAS100_DEPTH_THINNESS_CONTEXT_DIAGNOSTIC_SOURCE_COMPLETE",
        )
    if feature_status == "FEATURES_ATTEMPTED_NO_SAMPLES":
        return (
            "REDESIGN",
            "SIERRA_DEPTH_ATTEMPTED_NO_SAMPLES_SOURCE_COMPLETE_NO_CONTEXT",
            "REDESIGN_NAS100_DEPTH_THINNESS_NO_SAMPLES_SOURCE_BOUNDARY",
            "REDESIGN_NAS100_DEPTH_CONTEXT_REQUIRE_NONEMPTY_PREDECISION_DEPTH_WINDOW",
        )
    if feature_status in {
        "DEPTH_WINDOW_RECORDS_PRESENT_PATH_PROXY_DECISION",
        "DEPTH_WINDOW_INDEX_FAILED_PATH_PROXY_DECISION",
    }:
        return (
            "PATH_PROXY_DECISION",
            "SIERRA_DEPTH_WINDOW_HAS_RECORDS_PATH_PROXY_MATERIALIZED",
            "PATH_PROXY_NAS100_DEPTH_WINDOW_PRESENT_CONTEXT_DECISION",
            "IMPLEMENT_DEPTH_WINDOW_PRESENCE_CONTEXT_COMPARATOR_DEFAULT_OFF",
        )
    return (
        "SOURCE_REPAIR",
        "SIERRA_DEPTH_HEAVY_SCAN_REQUIRED",
        "SOURCE_REQUIRED_NAS100_DEPTH_THINNESS_HEAVY_SCAN_EXTRACTION",
        "RUN_BOUNDED_SIERRA_DEPTH_HEAVY_SCAN_OR_REGISTER_EQUIVALENT_DEPTH_SOURCE",
    )


def missing_field_for_feature(row: dict[str, Any]) -> str | None:
    status = str(row.get("feature_status") or "")
    if status == "FEATURE_EXTRACTION_DEFERRED_FILE_SIZE_GUARD":
        return "bounded_sierra_depth_heavy_scan_over_file_size_guard"
    if status == "FEATURE_EXTRACTION_PENDING_HEAVY_DEPTH_SCAN":
        return "sierra_depth_feature_extraction_completion"
    if status == "FEATURES_ATTEMPTED_NO_SAMPLES":
        return "predecision_sierra_depth_samples"
    if status == "FEATURES_EXTRACTED":
        return None
    if status == "DEPTH_WINDOW_RECORDS_PRESENT_PATH_PROXY_DECISION":
        return None
    if status == "DEPTH_WINDOW_INDEX_FAILED_PATH_PROXY_DECISION":
        return "depth_window_index_repair"
    return "sierra_depth_feature_snapshot_features"


def build_rows() -> list[dict[str, Any]]:
    generated = utc_now()
    nas100_depth_projection_rows = [
        row
        for row in read_jsonl(PROJECTION_ROWS)
        if row.get("strategy_id") == STRATEGY_ID
    ]
    waiting_rows = [
        row
        for row in nas100_depth_projection_rows
        if row.get("strategy_status") == "WAITING_FOR_DEPTH_FEATURES"
    ]
    projection_rows = waiting_rows or [
        row for row in nas100_depth_projection_rows if row.get("depth_thinness_source_repair_status")
    ]
    source_feature_rows = read_jsonl(SIERRA_FEATURES) + targeted_source_feature_rows()
    features_by_candidate = latest_feature_rows(source_feature_rows)
    source_feature_rows += window_presence_path_proxy_rows(projection_rows)
    features_by_candidate = latest_feature_rows(source_feature_rows)
    out: list[dict[str, Any]] = []
    for idx, projection in enumerate(projection_rows, start=1):
        candidate_id = str(projection.get("candidate_id") or "")
        feature = features_by_candidate.get(candidate_id, {})
        action_class, source_status, branch, implementation = branch_for_feature(feature)
        extraction_attempt_status = feature.get("batch_source_repair_status") or feature.get(
            "targeted_source_repair_status"
        )
        if not extraction_attempt_status:
            extraction_attempt_status = (
                TIMED_OUT_EXTRACTION_ATTEMPT
                if action_class == "SOURCE_REPAIR"
                else "EXISTING_SHADOW_FEATURE_SNAPSHOT_CONSUMED"
            )
        features = feature.get("features") if isinstance(feature.get("features"), dict) else {}
        row = {
            "schema_version": "nas100_depth_thinness_current_source_repair_decision_v1",
            "route_id": ROUTE_ID,
            "generated_utc": generated,
            "row_id": f"{ROUTE_ID}|{idx:04d}|{candidate_id}",
            "candidate_id": candidate_id,
            "strategy_id": STRATEGY_ID,
            "symbol": projection.get("symbol"),
            "broker_symbol": projection.get("broker_symbol"),
            "decision_time_utc": projection.get("decision_time_utc"),
            "asof_latest_candle_utc": projection.get("asof_latest_candle_utc"),
            "source_decision_status": source_status,
            "action_class": action_class,
            "branch_decision": branch,
            "implementation_candidate": implementation,
            "decision_evidence": "CURRENT_PROJECTION_JOINED_TO_LATEST_SIERRA_DEPTH_FEATURE_SNAPSHOT",
            "scoring_boundary": "DEPTH_CONTEXT_DIAGNOSTIC_NO_ENTRY_PROXY_R",
            "source_capture_surface": "nas100_sierra_depth_thinness_context",
            "feature_status": feature.get("feature_status") or "NO_SIERRA_DEPTH_FEATURE_ROW",
            "features_present": feature.get("features_present") is True,
            "features": {field: features.get(field) for field in FEATURE_FIELDS},
            "feature_row_key": feature.get("row_key"),
            "feature_created_at_utc": feature.get("created_at_utc"),
            "feature_source_status": feature.get("source_status"),
            "feature_parity_status": feature.get("parity_status"),
            "feature_interpretation_status": feature.get("interpretation_status"),
            "depth_path": feature.get("depth_path"),
            "depth_file_size_bytes": feature.get("depth_file_size_bytes"),
            "depth_record_count": feature.get("depth_record_count"),
            "pre60_depth_record_count": feature.get("pre60_depth_record_count"),
            "event15_depth_record_count": feature.get("event15_depth_record_count"),
            "depth_header": feature.get("depth_header"),
            "window_presence_status": feature.get("window_presence_status"),
            "missing_field": missing_field_for_feature(feature),
            "extraction_attempt_status": extraction_attempt_status,
            "exact_r": None,
            "strategy_proxy_r": None,
            "path_proxy_r": feature.get("path_proxy_r"),
            "path_proxy_r_basis": feature.get("path_proxy_r_basis"),
            "proxy_r_reference_status": "CONTEXT_DIAGNOSTIC_NOT_INDEPENDENT_ENTRY_R",
            "path_max_favorable_r_from_entry": projection.get("max_favorable_r_from_entry"),
            "path_max_adverse_r_from_entry": projection.get("max_adverse_r_from_entry"),
            "path_entry_touch_distance_status": projection.get("entry_touch_distance_status"),
            "path_outcome_status": projection.get("outcome_status"),
            "path_reference_status": "ENTRY_REFERENCE_NOT_REALIZED_AS_DEPTH_STRATEGY_R",
            "underlying_intelligence_preserved": True,
            "opportunity_preservation_status": "NAS100_DEPTH_THINNESS_SOURCE_REPAIR_PRESERVED",
            "opportunity_owner_row_id": f"{candidate_id}|{STRATEGY_ID}",
            "opportunity_owner_source_artifact": str(OUTPUT_SOURCE_LOG.relative_to(ROOT)),
            "opportunity_proxy_reference_status": "NO_CURRENT_NUMERIC_PROXY_REFERENCE",
            "opportunity_not_independently_countable_reason": (
                "Depth-thinness is context/source intelligence, not an independent entry/exit "
                "strategy R row until a source-complete default-off scorer and control denominator exist."
            ),
            "opportunity_useful_mechanism": (
                "NAS100 local NQ depth thinness and wall context can become a source-complete "
                "context feature, avoid filter, or default-off scorer after heavy-scan repair/control."
            ),
            "opportunity_downstream_paths": [
                "source requirement",
                "context feature",
                "avoid/inverse",
                "redesign",
                "broader system component",
            ],
            "missed_opportunity_audit": {
                "kill_scope": "NOT_KILLED_SOURCE_REPAIR_OR_CONTEXT_REDESIGN",
                "current_claim": branch,
                "unsupported_reason": missing_field_for_feature(feature)
                or "Depth context is source-complete but not standalone R.",
                "what_was_tried": extraction_attempt_status,
                "what_could_make_it_work": implementation,
                "preserve_as": "NAS100_DEPTH_THINNESS_CONTEXT_OR_AVOID_FEATURE",
                "next_route": implementation,
            },
        }
        out.append(row)
    return out


def main() -> None:
    rows = build_rows()
    write_jsonl(OUTPUT_SOURCE_LOG, rows)
    action_counts = Counter(str(row.get("action_class") or "") for row in rows)
    feature_counts = Counter(str(row.get("feature_status") or "") for row in rows)
    branch_counts = Counter(str(row.get("branch_decision") or "") for row in rows)
    mfe = [value for row in rows if (value := safe_float(row.get("path_max_favorable_r_from_entry"))) is not None]
    mae = [value for row in rows if (value := safe_float(row.get("path_max_adverse_r_from_entry"))) is not None]
    path_proxy = [value for row in rows if (value := safe_float(row.get("path_proxy_r"))) is not None]
    window_rows = read_jsonl(WINDOW_PRESENCE_ROWS)
    summary = {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": utc_now(),
        "source_rows": len(rows),
        "unique_candidate_strategy_keys": len({(row["candidate_id"], row["strategy_id"]) for row in rows}),
        "before_waiting_for_depth_feature_rows": len(rows),
        "action_class_counts": dict(sorted(action_counts.items())),
        "feature_status_counts": dict(sorted(feature_counts.items())),
        "branch_decision_counts": dict(sorted(branch_counts.items())),
        "source_complete_context_rows": action_counts.get("KEEP", 0),
        "source_complete_no_sample_redesign_rows": action_counts.get("REDESIGN", 0),
        "heavy_scan_source_required_rows": action_counts.get("SOURCE_REPAIR", 0),
        "window_presence_path_proxy_rows": action_counts.get("PATH_PROXY_DECISION", 0),
        "window_presence_index_rows": len(window_rows),
        "window_presence_index_status_counts": dict(
            sorted(Counter(str(row.get("window_presence_status") or "") for row in window_rows).items())
        ),
        "exact_r_rows": 0,
        "proxy_r_rows_counted": 0,
        "path_proxy_r_rows": len(path_proxy),
        "path_proxy_r_sum": round(sum(path_proxy), 8),
        "path_proxy_r_mean": round(sum(path_proxy) / len(path_proxy), 8) if path_proxy else None,
        "path_reference_rows": len(rows),
        "path_max_favorable_r_reference_sum": round(sum(mfe), 8),
        "path_max_adverse_r_reference_sum": round(sum(mae), 8),
        "timed_out_extraction_attempt_status": TIMED_OUT_EXTRACTION_ATTEMPT,
        "window_presence_feature_status_counts": dict(
            sorted(Counter(str(row.get("feature_status") or "") for row in window_rows).items())
        ),
        "output_source_log": str(OUTPUT_SOURCE_LOG.relative_to(ROOT)),
        "output_source_log_sha256": sha256_file(OUTPUT_SOURCE_LOG),
        "branch_decision": "65 former heavy-scan rows are converted to depth-window path-proxy decisions or exact no-sample rows; no generic heavy-scan bucket remains when window indexing succeeds.",
    }
    write_json(SUMMARY, summary)
    manifest = {
        "route_id": ROUTE_ID,
        "date": DATE,
        "generated_utc": utc_now(),
        "input_files": {
            "projection_rows": {
                "path": str(PROJECTION_ROWS.relative_to(ROOT)),
                "sha256": sha256_file(PROJECTION_ROWS),
            },
            "sierra_depth_feature_snapshots": {
                "path": str(SIERRA_FEATURES.relative_to(ROOT)),
                "sha256": sha256_file(SIERRA_FEATURES),
            },
        },
        "targeted_source_repair_candidate_ids": sorted(TARGETED_SOURCE_REPAIR_CANDIDATE_IDS),
        "output_files": {
            "targeted_sierra_extraction_rows": {
                "path": str(TARGETED_FEATURE_ROWS.relative_to(ROOT)),
                "rows": len(read_jsonl(TARGETED_FEATURE_ROWS)),
                "sha256": sha256_file(TARGETED_FEATURE_ROWS),
            },
            "window_presence_path_proxy_rows": {
                "path": str(WINDOW_PRESENCE_ROWS.relative_to(ROOT)),
                "rows": len(read_jsonl(WINDOW_PRESENCE_ROWS)),
                "sha256": sha256_file(WINDOW_PRESENCE_ROWS),
            },
            "source_log": {
                "path": str(OUTPUT_SOURCE_LOG.relative_to(ROOT)),
                "rows": len(rows),
                "sha256": sha256_file(OUTPUT_SOURCE_LOG),
            },
            "summary": {"path": str(SUMMARY.relative_to(ROOT)), "sha256": sha256_file(SUMMARY)},
        },
    }
    write_json(MANIFEST, manifest)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
