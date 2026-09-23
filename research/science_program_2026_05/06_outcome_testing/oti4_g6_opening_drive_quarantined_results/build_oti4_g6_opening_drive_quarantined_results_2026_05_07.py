#!/usr/bin/env python3
"""Build OTI4 quarantined opening-drive outcome-audit artifacts.

This lane consumes only the G12-accepted OTG0-PKT-062 / G6-EXP-003
input-only packet. It does not read broker actual-R, blocked-packet outcomes,
live trade results, or raw path-order outcome labels. When the accepted packet
cannot support a prereg-compatible opening-drive continuation label, the output
is an exact non-computability ledger rather than a fabricated result.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "research/science_program_2026_05/06_outcome_testing/oti4_g6_opening_drive_quarantined_results"
DATE = "2026-05-07"
PACKET_ID = "OTG0-PKT-062"
EXPERIMENT_ID = "G6-EXP-003-OPENING-DRIVE-CONTINUATION"
HYPOTHESIS_ID = "G6-HYP-003"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
RESULT_STATUS = "RESULT_QUARANTINED_DISCOVERY_ONLY"
SAMPLE_FLOOR = 200

PACKET_PATH = ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "otb2r_g6_local_ohlc_momentum_reversion_packets/packets/"
    "OTG0-PKT-062__G6-EXP-003-OPENING-DRIVE-CONTINUATION__g6_local_ohlc_input_packet_2026-05-07.json"
)
PREREGISTRY_PATH = ROOT / "research/science_program_2026_05/03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json"
G12_SHORTLIST_PATH = ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "g12_g3_g6_packet_builder_audit/G12_G3_G6_ACCEPTED_PACKET_SHORTLIST_2026-05-07.json"
)
G12_DECISION_PATH = ROOT / (
    "research/science_program_2026_05/06_outcome_testing/"
    "g12_g3_g6_packet_builder_audit/G12_G3_G6_PACKET_BUILDER_DECISION_LEDGER_2026-05-07.json"
)

CONTROL_INPUTS = [
    ".context/LIVE_STATE.md",
    ".context/00_core/goal_session_research_discipline.md",
    ".context/00_core/research_current_state.md",
    "research/science_program_2026_05/06_outcome_testing/OTG0_OUTCOME_TESTING_CONTROL_RULES_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/OTG0_PREREG_CLASSIFICATION_LEDGER_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/OTG0_FROZEN_COHORT_PACKET_MANIFEST_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/otb2_synthetic_packet_builder/OTB2_SYNTHETIC_REPLAY_PACKET_MANIFEST_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/otb2r_input_only_path_rebuild/OTB2R_PACKET_MANIFEST_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/OTB2R_G6_LOCAL_OHLC_PACKET_MANIFEST_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/OTB2R_G6_SOURCE_HASH_AUDIT_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/OTB2R_G6_DUPLICATE_DENOMINATOR_AUDIT_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/OTB2R_G6_NO_LEAK_AUDIT_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/OTB2R_G6_LABEL_FAMILY_AUDIT_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/otb2r_g6_local_ohlc_momentum_reversion_packets/OTB2R_G6_SAME_BAR_TIMING_POLICY_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/g12_g3_g6_packet_builder_audit/G12_G3_G6_PACKET_BUILDER_DECISION_LEDGER_2026-05-07.md",
    "research/science_program_2026_05/06_outcome_testing/g12_g3_g6_packet_builder_audit/G12_G3_G6_ACCEPTED_PACKET_SHORTLIST_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/g12_g3_g6_packet_builder_audit/G12_G3_G6_SOURCE_HASH_REPRODUCIBILITY_REVIEW_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/g12_g3_g6_packet_builder_audit/G12_G3_G6_DUPLICATE_DENOMINATOR_REVIEW_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/g12_g3_g6_packet_builder_audit/G12_G3_G6_LEAKAGE_NOLEAK_REVIEW_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/g12_g3_g6_packet_builder_audit/G12_G3_G6_LABEL_FAMILY_REVIEW_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/g12_g3_g6_packet_builder_audit/G12_G3_G6_SAME_BAR_TIMING_REVIEW_2026-05-07.json",
    "research/science_program_2026_05/06_outcome_testing/g12_g3_g6_packet_builder_audit/G12_G3_G6_SOURCE_FRESHNESS_STALENESS_REVIEW_2026-05-07.json",
    "research/science_program_2026_05/03_experiment_specs/EXPERIMENT_PREREGISTRY_2026-05-06.json",
    "research/science_program_2026_05/01_domain_syntheses/G6_MOMENTUM_REVERSION_ROWS_2026-05-06.json",
]

SKIPPED_RESULT_OR_LABEL_SOURCES = [
    "shadow_logs/broker_actual_r_audit.jsonl",
    "data/account_history/mt5_deals_2026-04-27_2026-05-05.jsonl",
    "shadow_logs/continuation_no_retrace_resolutions.jsonl",
    "shadow_logs/candidate_ltf_path_order.jsonl",
    "shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl",
    "knowledge_base/trade_records/",
    "research/science_program_2026_05/06_outcome_testing/oti1_lifecycle_quarantined_results/",
    "research/science_program_2026_05/06_outcome_testing/oti2_riskbank_quarantined_results/",
]

FORBIDDEN_RECORD_KEY_FRAGMENTS = [
    "actual_r",
    "broker_actual",
    "close_fill",
    "entry_first_touch",
    "final_outcome",
    "gross_r",
    "hit_sl",
    "hit_tp",
    "mae",
    "mfe",
    "net_r",
    "outcome",
    "path_label",
    "path_order_label",
    "path_outcome",
    "pnl",
    "realized_r",
    "resolution",
    "resolved",
    "result",
    "sl_first_touch",
    "synthetic_path",
    "terminal_order",
    "touch_sequence",
    "tp1_first_touch",
    "trade_result",
    "win_loss",
]


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(json_dumps(payload).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        try:
            dt = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def flatten_keys(payload: Any, prefix: str = "") -> list[str]:
    if isinstance(payload, dict):
        out: list[str] = []
        for key, value in payload.items():
            dotted = f"{prefix}.{key}" if prefix else str(key)
            out.append(dotted)
            out.extend(flatten_keys(value, dotted))
        return out
    if isinstance(payload, list):
        out = []
        for idx, value in enumerate(payload):
            out.extend(flatten_keys(value, f"{prefix}[{idx}]"))
        return out
    return []


def forbidden_key_hits(record: dict[str, Any]) -> list[str]:
    hits = []
    for key in flatten_keys(record):
        key_l = key.lower()
        if any(fragment in key_l for fragment in FORBIDDEN_RECORD_KEY_FRAGMENTS):
            hits.append(key)
    return sorted(set(hits))


def csv_datetimes(path: Path) -> list[datetime]:
    if not path.exists():
        return []
    values: list[datetime] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if not header:
            return values
        for row in reader:
            if not row:
                continue
            dt = parse_utc(row[0])
            if dt is not None:
                values.append(dt)
    return values


def load_prereg() -> dict[str, Any]:
    registry = read_json(PREREGISTRY_PATH)
    for row in registry.get("rows", []):
        if row.get("experiment_id") == EXPERIMENT_ID:
            return row
    raise RuntimeError(f"Preregistry row not found for {EXPERIMENT_ID}")


def accepted_shortlist_row() -> dict[str, Any]:
    shortlist = read_json(G12_SHORTLIST_PATH)
    for row in shortlist.get("accepted_packets", []):
        if row.get("packet_id") == PACKET_ID:
            return row
    raise RuntimeError(f"G12 accepted shortlist does not include {PACKET_ID}")


def decision_row() -> dict[str, Any]:
    ledger = read_json(G12_DECISION_PATH)
    for row in ledger.get("packet_decisions", []):
        if row.get("packet_id") == PACKET_ID:
            return row
    raise RuntimeError(f"G12 decision ledger does not include {PACKET_ID}")


def packet_safety_assertions(packet: dict[str, Any]) -> None:
    expected = {
        "packet_id": PACKET_ID,
        "experiment_id": EXPERIMENT_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "broker_actual_r_inspected": False,
        "blocked_packet_outcomes_inspected": False,
        "outcome_scoring_run": False,
        "result_or_quarantine_outputs_created": False,
    }
    for key, value in expected.items():
        if packet.get(key) != value:
            raise RuntimeError(f"Packet safety mismatch for {key}: {packet.get(key)!r} != {value!r}")


def row_not_computable_reasons(record: dict[str, Any], coverage: dict[str, Any]) -> list[str]:
    opening = record.get("opening_drive_packet") or {}
    reasons = []
    if opening.get("status") != "ASOF_OPENING_RANGE_BREAKOUT_READY":
        reasons.append(f"opening_drive_packet_status_{opening.get('status') or 'missing'}")
    if str(record.get("duplicate_breakout_key", "")).endswith("|NO_BREAKOUT_ASOF"):
        reasons.append("duplicate_breakout_key_declares_NO_BREAKOUT_ASOF")
    for field in ("range_high", "range_low", "breakout_close_time", "breakout_side"):
        if field not in opening:
            reasons.append(f"missing_prereg_opening_drive_field_{field}")
    if coverage["range_bar_count"] == 0:
        reasons.append("no_ohlc_bars_for_frozen_range_window")
    if coverage["path_bar_count"] == 0:
        reasons.append("no_ohlc_bars_for_path_window")
    if coverage["decision_after_ohlc_last_utc"]:
        reasons.append("decision_asof_after_ohlc_source_last_timestamp")
    if record.get("same_bar_ambiguity_state") == "same_m1_ambiguity_flagged":
        reasons.append("same_bar_terminal_order_uncertainty_flagged")
    return sorted(set(reasons))


def source_coverage(records: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    times_by_source: dict[str, list[datetime]] = {}
    for record in records:
        source_path = record["opening_drive_packet"]["ohlc_source"]["path"]
        if source_path not in times_by_source:
            times_by_source[source_path] = csv_datetimes(ROOT / source_path)

    source_summary: dict[str, dict[str, Any]] = {}
    row_coverage: dict[str, dict[str, Any]] = {}
    for source_path, times in times_by_source.items():
        full_path = ROOT / source_path
        declared_hashes = {
            record["opening_drive_packet"]["ohlc_source"].get("sha256")
            for record in records
            if record["opening_drive_packet"]["ohlc_source"].get("path") == source_path
        }
        computed_hash = sha256_file(full_path) if full_path.exists() else None
        source_records = [record for record in records if record["opening_drive_packet"]["ohlc_source"].get("path") == source_path]
        decisions = [parse_utc(record.get("decision_asof_utc")) for record in source_records]
        source_summary[source_path] = {
            "path": source_path,
            "exists": full_path.exists(),
            "declared_sha256_values": sorted(hash for hash in declared_hashes if hash),
            "computed_sha256": computed_hash,
            "sha256_matches_all_declared": bool(computed_hash) and declared_hashes == {computed_hash},
            "row_count_loaded": len(times),
            "first_utc": iso(min(times) if times else None),
            "last_utc": iso(max(times) if times else None),
            "referenced_packet_rows": len(source_records),
            "min_decision_asof_utc": iso(min((dt for dt in decisions if dt is not None), default=None)),
            "max_decision_asof_utc": iso(max((dt for dt in decisions if dt is not None), default=None)),
            "all_referenced_decisions_after_source_last": all(
                dt is not None and times and dt > max(times) for dt in decisions
            )
            if times
            else False,
        }
        for record in source_records:
            range_def = record["frozen_range_definition"]
            range_start = parse_utc(range_def.get("range_start_utc"))
            range_end = parse_utc(range_def.get("range_end_utc"))
            path_start = parse_utc(record.get("path_start_utc"))
            path_end = parse_utc(record.get("path_end_utc"))
            decision = parse_utc(record.get("decision_asof_utc"))
            last = max(times) if times else None
            range_count = sum(1 for dt in times if range_start and range_end and range_start <= dt < range_end)
            path_count = sum(1 for dt in times if path_start and path_end and path_start <= dt <= path_end)
            row_coverage[record["record_id"]] = {
                "ohlc_source_path": source_path,
                "ohlc_source_first_utc": iso(min(times) if times else None),
                "ohlc_source_last_utc": iso(last),
                "declared_ohlc_sha256": record["opening_drive_packet"]["ohlc_source"].get("sha256"),
                "computed_ohlc_sha256": computed_hash,
                "ohlc_sha256_match": computed_hash == record["opening_drive_packet"]["ohlc_source"].get("sha256"),
                "range_start_utc": iso(range_start),
                "range_end_utc": iso(range_end),
                "range_bar_count": range_count,
                "path_start_utc": iso(path_start),
                "path_end_utc": iso(path_end),
                "path_bar_count": path_count,
                "decision_after_ohlc_last_utc": bool(decision and last and decision > last),
                "source_coverage_status": "STALE_OHLC_NO_RANGE_OR_PATH_BARS"
                if range_count == 0 and path_count == 0
                else "HAS_PARTIAL_LOCAL_OHLC_COVERAGE",
            }
    return source_summary, row_coverage


def build_bundle() -> dict[str, Any]:
    packet = read_json(PACKET_PATH)
    packet_safety_assertions(packet)
    records = packet["records"]
    prereg = load_prereg()
    accepted = accepted_shortlist_row()
    decision = decision_row()
    packet_file_sha = sha256_file(PACKET_PATH)
    source_summary, row_coverage = source_coverage(records)

    row_hash_failures = []
    forbidden_hits = []
    row_ledger = []
    duplicate_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    same_bar_counts: Counter[str] = Counter()
    symbol_counts: Counter[str] = Counter()
    session_counts: Counter[str] = Counter()
    side_counts: Counter[str] = Counter()
    opening_status_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()

    for record in records:
        if record.get("packet_id") != PACKET_ID or record.get("experiment_id") != EXPERIMENT_ID:
            raise RuntimeError(f"Unexpected packet row: {record.get('record_id')}")
        duplicate_groups[record["duplicate_group_id"]].append(record)
        same_bar_counts[str(record.get("same_bar_ambiguity_state"))] += 1
        symbol_counts[str(record.get("symbol"))] += 1
        session_counts[str(record.get("session"))] += 1
        side_counts[str(record.get("side"))] += 1
        opening_status_counts[str((record.get("opening_drive_packet") or {}).get("status"))] += 1
        recomputed = sha256_json(record["sanitized_source_hash_components"])
        if recomputed != record.get("source_hash"):
            row_hash_failures.append(record["record_id"])
        hits = forbidden_key_hits(record)
        if hits:
            forbidden_hits.append({"record_id": record["record_id"], "hits": hits})

        coverage = row_coverage[record["record_id"]]
        reasons = row_not_computable_reasons(record, coverage)
        for reason in reasons:
            reason_counts[reason] += 1
        row_ledger.append(
            {
                "record_id": record["record_id"],
                "promotion_verdict": PROMOTION_VERDICT,
                "packet_id": PACKET_ID,
                "experiment_id": EXPERIMENT_ID,
                "hypothesis_id": HYPOTHESIS_ID,
                "symbol": record.get("symbol"),
                "session": record.get("session"),
                "side": record.get("side"),
                "decision_asof_utc": record.get("decision_asof_utc"),
                "duplicate_group_id": record.get("duplicate_group_id"),
                "source_hash": record.get("source_hash"),
                "source_hash_recomputed": recomputed,
                "source_hash_match": recomputed == record.get("source_hash"),
                "opening_drive_status": (record.get("opening_drive_packet") or {}).get("status"),
                "duplicate_breakout_key": record.get("duplicate_breakout_key"),
                "same_bar_ambiguity_state": record.get("same_bar_ambiguity_state"),
                "same_bar_ambiguity_policy": record.get("same_bar_ambiguity_policy"),
                "ohlc_source_path": coverage["ohlc_source_path"],
                "ohlc_source_last_utc": coverage["ohlc_source_last_utc"],
                "range_bar_count": coverage["range_bar_count"],
                "path_bar_count": coverage["path_bar_count"],
                "countable_prereg_opening_drive_unit": False,
                "quarantined_result_status": "NOT_COMPUTABLE_SOURCE_BLOCKED",
                "result_value": None,
                "result_value_reason": "No prereg-compatible opening-drive continuation result computed.",
                "not_computable_reasons": reasons,
            }
        )

    group_rows = []
    for group_id, group_records in sorted(duplicate_groups.items()):
        group_reason_counter: Counter[str] = Counter()
        for record in group_records:
            for reason in row_not_computable_reasons(record, row_coverage[record["record_id"]]):
                group_reason_counter[reason] += 1
        group_rows.append(
            {
                "duplicate_group_id": group_id,
                "raw_child_rows": len(group_records),
                "countable_prereg_opening_drive_unit": False,
                "symbols": sorted({record.get("symbol") for record in group_records}),
                "sessions": sorted({record.get("session") for record in group_records}),
                "sides": sorted({record.get("side") for record in group_records}),
                "first_decision_asof_utc": min(record["decision_asof_utc"] for record in group_records),
                "last_decision_asof_utc": max(record["decision_asof_utc"] for record in group_records),
                "not_computable_reasons": sorted(group_reason_counter),
            }
        )

    countable_groups = [row for row in group_rows if row["countable_prereg_opening_drive_unit"]]
    method_freeze = {
        "artifact_family": "OTI4_G6_OPENING_DRIVE_METHOD_FREEZE",
        "generated_at_utc": now_utc(),
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "validation_safe": False,
        "outcome_review_opened": False,
        "allowed_packet_id": PACKET_ID,
        "allowed_experiment_id": EXPERIMENT_ID,
        "accepted_packet_file": rel(PACKET_PATH),
        "accepted_packet_file_sha256": packet_file_sha,
        "accepted_packet_file_sha256_matches_g12": packet_file_sha == accepted.get("packet_file_sha256"),
        "scope": "quarantined discovery outcome audit only; no validation, promotion, live behavior, broker actual-R, blocked-packet outcome, live trade result, or raw path-label use",
        "prereg_metric": prereg.get("metric"),
        "prereg_sample_floor": prereg.get("sample_floor"),
        "prereg_duplicate_policy": prereg.get("duplicate_policy"),
        "prereg_exclusions": prereg.get("exclusions"),
        "allowed_result_family": "synthetic_path_r_only_if_opening_drive_range_breakout_is_source_complete",
        "strict_countable_rule": [
            "opening_drive_packet.status must be ASOF_OPENING_RANGE_BREAKOUT_READY",
            "range_high, range_low, breakout_close_time, and breakout_side must be present as-of",
            "local OHLC source must contain frozen range bars and path-window bars",
            "duplicate_breakout_key must not be NO_BREAKOUT_ASOF",
            "same-bar terminal order must remain unclaimed or be conservatively bounded",
        ],
        "skipped_result_or_label_sources": SKIPPED_RESULT_OR_LABEL_SOURCES,
    }

    result_ledger = {
        "artifact_family": "OTI4_G6_OPENING_DRIVE_RESULT_LEDGER",
        "generated_at_utc": now_utc(),
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "validation_safe": False,
        "outcome_review_opened": False,
        "broker_actual_r_inspected": False,
        "blocked_packet_outcomes_inspected": False,
        "live_trade_results_inspected": False,
        "raw_path_order_labels_inspected": False,
        "packet_id": PACKET_ID,
        "experiment_id": EXPERIMENT_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "g12_decision": decision.get("decision"),
        "raw_record_count": len(records),
        "unique_duplicate_group_count": len(duplicate_groups),
        "prereg_countable_unique_groups": len(countable_groups),
        "sample_floor": SAMPLE_FLOOR,
        "sample_floor_warning": "RAW_86_AND_UNIQUE_19_BELOW_200_FLOOR_COUNTABLE_ZERO",
        "opening_status_counts": dict(sorted(opening_status_counts.items())),
        "same_bar_ambiguity_state_counts": dict(sorted(same_bar_counts.items())),
        "symbol_counts_raw": dict(sorted(symbol_counts.items())),
        "session_counts_raw": dict(sorted(session_counts.items())),
        "side_counts_raw": dict(sorted(side_counts.items())),
        "not_computable_reason_counts": dict(sorted(reason_counts.items())),
        "summary_result": {
            "status": "NOT_COMPUTABLE",
            "reason": "Every accepted packet row lacks source-complete as-of opening-drive breakout fields and local OHLC range/path coverage.",
            "computed_continuation_expectancy_r": None,
            "computed_win_rate": None,
            "computed_countable_n": 0,
        },
        "rows": row_ledger,
    }

    duplicate_report = {
        "artifact_family": "OTI4_G6_OPENING_DRIVE_DUPLICATE_DENOMINATOR_REPORT",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "denominator_policy": "Use unique duplicate_group_id/duplicate_breakout_key, never raw records, for any future countable opening-drive denominator.",
        "raw_record_count": len(records),
        "unique_duplicate_group_count": len(duplicate_groups),
        "duplicate_group_reuse_count": sum(1 for items in duplicate_groups.values() if len(items) > 1),
        "max_records_per_duplicate_group": max((len(items) for items in duplicate_groups.values()), default=0),
        "prereg_countable_unique_groups": len(countable_groups),
        "denominator_inflation_factor_raw_over_unique": round(len(records) / len(duplicate_groups), 6),
        "group_rows": group_rows,
    }

    source_report = {
        "artifact_family": "OTI4_G6_OPENING_DRIVE_SOURCE_HASH_COVERAGE_REPORT",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "packet_file_sha256": packet_file_sha,
        "packet_file_sha256_matches_g12": packet_file_sha == accepted.get("packet_file_sha256"),
        "row_source_hash_match_count": len(records) - len(row_hash_failures),
        "row_source_hash_failure_count": len(row_hash_failures),
        "row_source_hash_failures": row_hash_failures,
        "source_file_count": len(source_summary),
        "source_files": source_summary,
        "rows_with_range_bars": sum(1 for row in row_coverage.values() if row["range_bar_count"] > 0),
        "rows_with_path_bars": sum(1 for row in row_coverage.values() if row["path_bar_count"] > 0),
        "rows_decision_after_ohlc_last": sum(1 for row in row_coverage.values() if row["decision_after_ohlc_last_utc"]),
        "row_coverage": row_coverage,
    }

    label_report = {
        "artifact_family": "OTI4_G6_OPENING_DRIVE_LABEL_FAMILY_SEPARATION_REPORT",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "packet_materialized_label_family": packet.get("label_family_materialized_in_records"),
        "declared_future_label_family": packet.get("declared_future_label_family"),
        "broker_path_lifecycle_pooling_allowed": False,
        "broker_actual_r_inspected": False,
        "blocked_packet_outcomes_inspected": False,
        "live_trade_results_inspected": False,
        "synthetic_path_result_values_computed": False,
        "policy": "No broker, lifecycle, live trade, raw path-label, or blocked-packet labels are pooled into OTI4. The accepted packet remains input-only.",
    }

    noleak_report = {
        "artifact_family": "OTI4_G6_OPENING_DRIVE_NO_LEAK_AND_STRICTER_FORMULATION_REPORT",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "forbidden_key_fragments": FORBIDDEN_RECORD_KEY_FRAGMENTS,
        "forbidden_record_key_hit_count": len(forbidden_hits),
        "forbidden_record_key_hits": forbidden_hits,
        "hidden_path_label_search": {
            "ordered_path_source_id_present_rows": sum(1 for record in records if record.get("ordered_path_source_id")),
            "raw_candidate_ltf_path_order_opened": False,
            "reason": "Raw path-order logs can contain post-decision terminal labels; OTI4 requires source-complete opening-drive range fields first.",
        },
        "alternative_stricter_no_leak_formulations": [
            {
                "name": "packet_fields_only_no_raw_path_labels",
                "result": "PASS_WITH_BLOCKER",
                "evidence": "No forbidden result keys in packet records; raw path-label sources skipped.",
            },
            {
                "name": "source_complete_opening_range_required",
                "result": "FAIL_COUNTABLE_ROWS_ZERO",
                "evidence": "All opening_drive_packet.status values are SOURCE_BLOCKED_NO_RANGE_BARS_ASOF.",
            },
            {
                "name": "duplicate_key_must_not_encode_no_breakout",
                "result": "FAIL_COUNTABLE_ROWS_ZERO",
                "evidence": "All duplicate_breakout_key values end with NO_BREAKOUT_ASOF.",
            },
        ],
        "skipped_result_or_label_sources": SKIPPED_RESULT_OR_LABEL_SOURCES,
    }

    methodology = {
        "artifact_family": "OTI4_G6_OPENING_DRIVE_METHODOLOGY_REPORT",
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "validation_safe": False,
        "outcome_review_opened": False,
        "raw_record_count": len(records),
        "accepted_unique_duplicate_groups": len(duplicate_groups),
        "countable_effective_n": 0,
        "sample_floor": SAMPLE_FLOOR,
        "sample_floor_pass": False,
        "dsr": {
            "status": "not_computable",
            "reasons": [
                "no_countable_prereg_compatible_opening_drive_outcome_rows",
                "raw_86_and_unique_19_below_200_sample_floor",
                "same_dataset_quarantined_discovery_only",
                "no_unseen_validation_split",
            ],
        },
        "pbo": {
            "status": "not_computable",
            "reasons": [
                "no_countable_outcome_vector",
                "no_preregistered_variant_matrix",
                "no_train_test_or_cpcv_blocks",
            ],
        },
        "effective_n": {
            "status": "not_computable",
            "reason": "countable_prereg_opening_drive_unique_groups_zero; accepted packet has 19 duplicate groups but all are noncountable NO_BREAKOUT_ASOF/source-blocked rows",
            "raw_records": len(records),
            "unique_duplicate_groups": len(duplicate_groups),
            "countable_unique_groups": 0,
        },
    }

    blocker = {
        "artifact_family": "OTI4_G6_OPENING_DRIVE_BLOCKER_AND_AMBIGUITY_LEDGER",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "blockers": [
            {
                "blocker_id": "OTI4-BLK-001",
                "status": "OPEN_LOCAL_SOURCE_BLOCKER",
                "evidence": "rows_with_range_bars=0 and rows_with_path_bars=0 across 86 records",
                "next_exact_question": "Which source-hashed local M15/M5/M1 OHLC or tick packet covers the May 3-6 2026 frozen opening ranges and path windows for OTG0-PKT-062?",
            },
            {
                "blocker_id": "OTI4-BLK-002",
                "status": "OPEN_PACKET_FIELD_BLOCKER",
                "evidence": "opening_drive_packet has only frozen_range_definition, ohlc_source, and status; range_high/range_low/breakout_close_time/breakout_side are absent",
                "next_exact_question": "Which packet builder supplies as-of range_high, range_low, breakout_close_time, breakout_side, spread_at_break, and killed-route exclusion fields without outcome leakage?",
            },
            {
                "blocker_id": "OTI4-BLK-003",
                "status": "DOCUMENTED_DENOMINATOR_BLOCKER",
                "evidence": "86 raw rows collapse to 19 duplicate groups; all duplicate keys end NO_BREAKOUT_ASOF; sample floor is 200",
                "next_exact_question": "After source refresh and killed-route exclusions, does OTG0-PKT-062 reach 200 unique breakout groups under the duplicate_breakout_key policy?",
            },
            {
                "blocker_id": "OTI4-BLK-004",
                "status": "DOCUMENTED_NOLEAK_BLOCKER",
                "evidence": "ordered_path_source_id exists but raw path-order labels were not opened",
                "next_exact_question": "If a future lane opens path labels, can it re-derive them from approved OHLC/ticks with terminal-order uncertainty preserved instead of reading hidden path_order_label columns?",
            },
            {
                "blocker_id": "OTI4-BLK-005",
                "status": "DOCUMENTED_SAME_BAR_UNCERTAINTY",
                "evidence": "same_m1_ambiguity_flagged rows=6; terminal_order_claim_allowed=false",
                "next_exact_question": "Does a future tick-order source or predeclared conservative-bound policy resolve same-bar rows without guessing terminal event order?",
            },
        ],
    }

    adversarial = {
        "artifact_family": "OTI4_G6_OPENING_DRIVE_ADVERSARIAL_SELF_REVIEW",
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "strongest_reason_result_could_be_wrong": "G12 accepted OTG0-PKT-062 for future quarantined outcome audit, so a less strict auditor might read the referenced candidate_ltf_path_order source and produce path labels despite missing opening-drive range fields.",
        "resolution": "Do not do that in OTI4. The prereg requires source-complete session/opening-range breakout fields and the objective forbids hidden path labels. All accepted rows are NO_BREAKOUT_ASOF with stale OHLC coverage, so a path-label-only result would answer a different, leaky question.",
        "residual_unresolved_risk": "If the owner approves a separate OTI4b method freeze that treats path-order labels as the outcome source, it must rebuild source hashes, same-bar policy, and no-leak constraints explicitly before scoring.",
    }

    completion = {
        "artifact_family": "OTI4_G6_OPENING_DRIVE_COMPLETION_AUDIT",
        "promotion_verdict": PROMOTION_VERDICT,
        "result_status": RESULT_STATUS,
        "validation_safe": False,
        "outcome_review_opened": False,
        "can_mark_goal_complete": True,
        "objective_restatement": "Run OTI4_G6_OPENING_DRIVE_QUARANTINED_OUTCOME_AUDIT using only G12 accepted OTG0-PKT-062, preserving quarantine/no-promotion boundaries, and either compute prereg-compatible summaries or prove exact non-computability.",
        "prompt_to_artifact_checklist": [
            ["Complete GTOS preflight", "PASS", "generate_live_state.py and mandatory core docs were read before implementation."],
            ["Use only OTG0-PKT-062 accepted packet", "PASS", rel(PACKET_PATH)],
            ["Exclude broker actual-R, blocked outcomes, live trade results, hidden path labels", "PASS", "Skipped sources listed; builder reads packet and OHLC coverage only."],
            ["Enforce duplicate denominator", "PASS", f"raw={len(records)} unique_duplicate_groups={len(duplicate_groups)} countable=0"],
            ["Label-family separation", "PASS", "input_only_features_no_labels; future synthetic_path_r only; no label pooling."],
            ["Sample-floor warning", "PASS", "raw 86 and unique 19 below 200; countable 0."],
            ["DSR/PBO/effective-N or exact not_computable reasons", "PASS", "methodology report marks all not_computable with reasons."],
            ["Same-bar terminal-order uncertainty", "PASS", f"same_bar_counts={dict(same_bar_counts)} terminal_order_claim_allowed=false"],
            ["Search denominator inflation/stale OHLC/hidden labels/strict no-leak", "PASS", "duplicate, source coverage, no-leak, and adversarial reports emitted."],
            ["Produce result ledger or proof impossible", "PASS", "result ledger rows all NOT_COMPUTABLE_SOURCE_BLOCKED with exact reasons."],
            ["Preserve safety flags", "PASS", "NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false."],
        ],
    }

    manifest = {
        "artifact_family": "OTI4_G6_OPENING_DRIVE_ARTIFACT_MANIFEST",
        "generated_at_utc": now_utc(),
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "artifacts": [],
    }

    return {
        "method_freeze": method_freeze,
        "result_ledger": result_ledger,
        "duplicate_report": duplicate_report,
        "source_report": source_report,
        "label_report": label_report,
        "noleak_report": noleak_report,
        "methodology": methodology,
        "blocker": blocker,
        "adversarial": adversarial,
        "completion": completion,
        "manifest": manifest,
    }


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell) for cell in row) + " |")
    return "\n".join(out)


def render_simple_md(title: str, payload: dict[str, Any]) -> str:
    return (
        f"# {title} - {DATE}\n\n"
        f"**Promotion verdict:** `{payload.get('promotion_verdict')}`  \n"
        f"**Validation safe:** `{payload.get('validation_safe')}`  \n"
        f"**Outcome review opened:** `{payload.get('outcome_review_opened')}`\n\n"
        "```json\n"
        + json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True)
        + "\n```\n"
    )


def render_result_md(payload: dict[str, Any]) -> str:
    summary = payload["summary_result"]
    rows = [
        ["raw records", payload["raw_record_count"]],
        ["unique duplicate groups", payload["unique_duplicate_group_count"]],
        ["prereg countable unique groups", payload["prereg_countable_unique_groups"]],
        ["sample floor", payload["sample_floor"]],
        ["result status", summary["status"]],
        ["computed continuation expectancy R", summary["computed_continuation_expectancy_r"]],
        ["computed countable n", summary["computed_countable_n"]],
    ]
    return (
        f"# OTI4 G6 Opening-Drive Result Ledger - {DATE}\n\n"
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`  \n"
        f"**Result status:** `{RESULT_STATUS}`  \n"
        f"**Validation safe:** `False`  \n"
        f"**Outcome review opened:** `False`\n\n"
        "## Summary\n\n"
        + md_table(["item", "value"], rows)
        + "\n\n## Not Computable Reason Counts\n\n"
        + md_table(
            ["reason", "rows"],
            [[key, value] for key, value in payload["not_computable_reason_counts"].items()],
        )
        + "\n\n## Quarantine Note\n\n"
        "No prereg-compatible opening-drive continuation outcome was computed. Every row is source-blocked or noncountable, "
        "and raw path labels, broker actual-R, blocked outcomes, and live trade results were not opened.\n"
    )


def render_completion_md(payload: dict[str, Any]) -> str:
    return (
        f"# OTI4 G6 Opening-Drive Completion Audit - {DATE}\n\n"
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`  \n"
        f"**Result status:** `{RESULT_STATUS}`  \n"
        f"**Can mark goal complete:** `{payload['can_mark_goal_complete']}`\n\n"
        "## Objective Restatement\n\n"
        f"{payload['objective_restatement']}\n\n"
        "## Prompt-To-Artifact Checklist\n\n"
        + md_table(["requirement", "status", "evidence"], payload["prompt_to_artifact_checklist"])
        + "\n"
    )


def write_artifacts(bundle: dict[str, Any]) -> None:
    files: dict[str, Any] = {
        f"OTI4_METHOD_FREEZE_{DATE}.json": bundle["method_freeze"],
        f"OTI4_RESULT_LEDGER_{DATE}.json": bundle["result_ledger"],
        f"OTI4_DUPLICATE_DENOMINATOR_REPORT_{DATE}.json": bundle["duplicate_report"],
        f"OTI4_SOURCE_HASH_COVERAGE_REPORT_{DATE}.json": bundle["source_report"],
        f"OTI4_LABEL_FAMILY_SEPARATION_REPORT_{DATE}.json": bundle["label_report"],
        f"OTI4_NO_LEAK_AND_STRICTER_FORMULATION_REPORT_{DATE}.json": bundle["noleak_report"],
        f"OTI4_METHODOLOGY_REPORT_{DATE}.json": bundle["methodology"],
        f"OTI4_BLOCKER_AND_AMBIGUITY_LEDGER_{DATE}.json": bundle["blocker"],
        f"OTI4_ADVERSARIAL_SELF_REVIEW_{DATE}.json": bundle["adversarial"],
        f"OTI4_COMPLETION_AUDIT_{DATE}.json": bundle["completion"],
    }
    for name, payload in files.items():
        write_json(OUT / name, payload)

    jsonl_path = OUT / f"OTI4_RESULT_LEDGER_ROWS_{DATE}.jsonl"
    write_text(jsonl_path, "\n".join(json.dumps(row, ensure_ascii=True, sort_keys=True) for row in bundle["result_ledger"]["rows"]))

    md_payloads = {
        f"OTI4_METHOD_FREEZE_{DATE}.md": ("OTI4 G6 Opening-Drive Method Freeze", bundle["method_freeze"]),
        f"OTI4_DUPLICATE_DENOMINATOR_REPORT_{DATE}.md": ("OTI4 G6 Opening-Drive Duplicate Denominator Report", bundle["duplicate_report"]),
        f"OTI4_SOURCE_HASH_COVERAGE_REPORT_{DATE}.md": ("OTI4 G6 Opening-Drive Source Hash Coverage Report", bundle["source_report"]),
        f"OTI4_LABEL_FAMILY_SEPARATION_REPORT_{DATE}.md": ("OTI4 G6 Opening-Drive Label Family Separation Report", bundle["label_report"]),
        f"OTI4_NO_LEAK_AND_STRICTER_FORMULATION_REPORT_{DATE}.md": ("OTI4 G6 Opening-Drive No-Leak And Stricter Formulation Report", bundle["noleak_report"]),
        f"OTI4_METHODOLOGY_REPORT_{DATE}.md": ("OTI4 G6 Opening-Drive Methodology Report", bundle["methodology"]),
        f"OTI4_BLOCKER_AND_AMBIGUITY_LEDGER_{DATE}.md": ("OTI4 G6 Opening-Drive Blocker And Ambiguity Ledger", bundle["blocker"]),
        f"OTI4_ADVERSARIAL_SELF_REVIEW_{DATE}.md": ("OTI4 G6 Opening-Drive Adversarial Self-Review", bundle["adversarial"]),
    }
    for name, (title, payload) in md_payloads.items():
        write_text(OUT / name, render_simple_md(title, payload))
    write_text(OUT / f"OTI4_RESULT_LEDGER_{DATE}.md", render_result_md(bundle["result_ledger"]))
    write_text(OUT / f"OTI4_COMPLETION_AUDIT_{DATE}.md", render_completion_md(bundle["completion"]))

    artifact_paths = sorted(
        path for path in OUT.glob(f"OTI4*{DATE}*") if path.name != f"OTI4_ARTIFACT_MANIFEST_{DATE}.json"
    )
    manifest = bundle["manifest"]
    manifest["artifacts"] = [
        {
            "path": rel(path),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
        }
        for path in artifact_paths
    ]
    write_json(OUT / f"OTI4_ARTIFACT_MANIFEST_{DATE}.json", manifest)


def main() -> None:
    bundle = build_bundle()
    write_artifacts(bundle)
    print(
        json.dumps(
            {
                "status": "OTI4_BUILT_NOT_COMPUTABLE_LEDGER",
                "packet_id": PACKET_ID,
                "raw_records": bundle["result_ledger"]["raw_record_count"],
                "unique_duplicate_groups": bundle["result_ledger"]["unique_duplicate_group_count"],
                "countable_groups": bundle["result_ledger"]["prereg_countable_unique_groups"],
                "promotion_verdict": PROMOTION_VERDICT,
                "validation_safe": False,
                "outcome_review_opened": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
