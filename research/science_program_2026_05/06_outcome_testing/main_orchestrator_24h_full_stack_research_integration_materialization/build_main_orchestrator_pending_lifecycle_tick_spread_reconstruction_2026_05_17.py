"""Reconstruct pending-lifecycle decision spreads from local tick parquet."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
DATE = "2026-05-17"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = find_repo_root(ROUTE_DIR)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(ROUTE_DIR) not in sys.path:
    sys.path.insert(0, str(ROUTE_DIR))

from build_main_orchestrator_pending_lifecycle_decision_spread_repair_2026_05_17 import (  # noqa: E402
    PENDING_LIMIT_STRATEGY_ID,
    SAFE_FLAGS,
    apply_pending_scorer as base_apply_pending_scorer,
    counter,
    has_metadata_gap,
    kill_audit_present,
    latest_by_candidate,
    latest_path_by_candidate,
    nested_status_counter,
    pending_proxy_summary,
    proxy_summary,
    read_json,
    read_jsonl,
    safe_float,
    sha256_file,
    utc_now,
    write_json,
    write_jsonl,
)
from src.research_infra.live_mechanical_shadow import (  # noqa: E402
    build_strategy_outcome_rows,
    latest_lifecycle_for_candidate_asof,
    latest_ltf_for_candidate_asof,
    latest_nofill_forward_capture_by_candidate,
    latest_pending_tick_spread_reconstruction_by_candidate,
    latest_structural_metadata_by_candidate,
    merge_structural_metadata_candidate,
    read_jsonl as read_shadow_jsonl,
)


INPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_NOFILL_FORWARD_SPREAD_REPAIR_LEDGER_{DATE}.jsonl"
INPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_NOFILL_FORWARD_SPREAD_REPAIR_SUMMARY_{DATE}.json"
SCORER_SOURCE = REPO_ROOT / "src/research_infra/live_mechanical_shadow.py"
TEST_SOURCE = REPO_ROOT / "tests/test_live_mechanical_shadow.py"
PREVIOUS_BUILDER = (
    ROUTE_DIR / "build_main_orchestrator_pending_lifecycle_nofill_forward_spread_repair_2026_05_17.py"
)

SHADOW_INPUTS = {
    "strategy_follow_candidates": REPO_ROOT / "shadow_logs/strategy_follow_candidates.jsonl",
    "candidate_path_follow": REPO_ROOT / "shadow_logs/candidate_path_follow.jsonl",
    "pending_limit_lifecycle": REPO_ROOT / "shadow_logs/pending_limit_lifecycle.jsonl",
    "candidate_ltf_path_order": REPO_ROOT / "shadow_logs/candidate_ltf_path_order.jsonl",
    "live_structural_strategy_metadata": REPO_ROOT / "shadow_logs/live_structural_strategy_metadata.jsonl",
    "nofill_forward_source_capture": REPO_ROOT / "shadow_logs/nofill_forward_source_capture.jsonl",
}

RECONSTRUCTION_LEDGER = ROUTE_DIR / (
    f"MAIN_ORCH24_PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION_SOURCE_LEDGER_{DATE}.jsonl"
)
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / (
    f"MAIN_ORCH24_PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION_OUTPUT_MANIFEST_{DATE}.json"
)

NOFILL_DERIVATION = "DERIVED_FROM_NOFILL_FORWARD_SOURCE_CAPTURE_DECISION_SPREAD"
LEGACY_DERIVATION = "DERIVED_FROM_PENDING_LIFECYCLE_LEGACY_SPREAD_AS_DECISION_SPREAD_PROXY"
TICK_DERIVATION = "DERIVED_FROM_TICK_PARQUET_AT_OR_BEFORE_DECISION_SPREAD"
MISSING_STATUS = "SOURCE_NOT_CAPTURED_IN_CURRENT_ROW"
SUCCESS_STATUS = "TICK_PARQUET_AT_OR_BEFORE_DECISION_WITHIN_2S_SOURCE_SAFE"
UNSAFE_STATUS = "TICK_PARQUET_NO_PRIOR_TICK_WITHIN_2S_SOURCE_UNSAFE"
MAX_PRIOR_TICK_AGE_SECONDS = 2.0
SPREAD_SCALE = 100.0


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def decision_time_from_candidate_id(candidate_id: str, symbol: str) -> datetime | None:
    prefix = f"{symbol}_"
    if not candidate_id.startswith(prefix):
        return None
    return parse_utc(candidate_id[len(prefix) :])


def tick_source_path(symbol: str, decision_time: datetime) -> Path:
    return REPO_ROOT / "data" / "ticks" / symbol / f"{decision_time.date().isoformat()}.parquet"


def utc_np_datetime(value: datetime) -> np.datetime64:
    utc_value = value.astimezone(timezone.utc).replace(tzinfo=None)
    return np.datetime64(utc_value, "us")


def utc_iso_from_np_datetime(value: np.datetime64) -> str:
    micros = value.astype("datetime64[us]").astype("int64")
    return datetime.fromtimestamp(micros / 1_000_000.0, tz=timezone.utc).isoformat()


def offset_seconds(tick: np.datetime64, decision: np.datetime64) -> float:
    return float((tick - decision) / np.timedelta64(1, "s"))


def row_decision_spread_status(row: dict[str, Any]) -> str:
    statuses = row.get("pending_lifecycle_source_capture_statuses")
    if not isinstance(statuses, dict):
        return ""
    return str(statuses.get("decision_spread_value_source_safe") or "")


def target_pending_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    targets = []
    for row in rows:
        if row.get("strategy_id") != PENDING_LIMIT_STRATEGY_ID:
            continue
        if row_decision_spread_status(row) in {MISSING_STATUS, LEGACY_DERIVATION}:
            targets.append(row)
    return targets


class TickFileCache:
    def __init__(self) -> None:
        self._cache: dict[Path, dict[str, Any]] = {}

    def get(self, path: Path) -> dict[str, Any]:
        if path in self._cache:
            return self._cache[path]
        table = pq.read_table(path, columns=["ts_utc", "bid", "ask"])
        payload = {
            "ts_utc": table["ts_utc"].to_numpy(zero_copy_only=False),
            "bid": table["bid"].to_numpy(zero_copy_only=False),
            "ask": table["ask"].to_numpy(zero_copy_only=False),
            "sha256": sha256_file(path),
            "size_bytes": path.stat().st_size,
            "row_count": table.num_rows,
        }
        self._cache[path] = payload
        return payload


def nearest_tick_payload(payload: dict[str, Any], decision_time: datetime) -> dict[str, Any]:
    timestamps = payload["ts_utc"]
    decision_np = utc_np_datetime(decision_time)
    before_idx = int(np.searchsorted(timestamps, decision_np, side="right")) - 1
    after_idx = int(np.searchsorted(timestamps, decision_np, side="left"))
    out: dict[str, Any] = {}
    if before_idx >= 0:
        tick = timestamps[before_idx]
        bid = float(payload["bid"][before_idx])
        ask = float(payload["ask"][before_idx])
        out.update(
            {
                "prior_tick_ts_utc": utc_iso_from_np_datetime(tick),
                "prior_tick_offset_seconds": round(offset_seconds(tick, decision_np), 6),
                "prior_tick_bid": bid,
                "prior_tick_ask": ask,
                "prior_tick_spread_cents": round((ask - bid) * SPREAD_SCALE, 12),
            }
        )
    if after_idx < len(timestamps):
        tick = timestamps[after_idx]
        bid = float(payload["bid"][after_idx])
        ask = float(payload["ask"][after_idx])
        out.update(
            {
                "next_tick_ts_utc": utc_iso_from_np_datetime(tick),
                "next_tick_offset_seconds": round(offset_seconds(tick, decision_np), 6),
                "next_tick_bid": bid,
                "next_tick_ask": ask,
                "next_tick_spread_cents": round((ask - bid) * SPREAD_SCALE, 12),
            }
        )
    return out


def reconstruct_tick_spread_rows(rows: list[dict[str, Any]], generated_utc: str) -> list[dict[str, Any]]:
    cache = TickFileCache()
    attempts: list[dict[str, Any]] = []
    for source in sorted(target_pending_rows(rows), key=lambda row: str(row.get("candidate_id") or "")):
        candidate_id = str(source.get("candidate_id") or "")
        symbol = str(source.get("symbol") or source.get("broker_symbol") or "")
        decision_time = parse_utc(source.get("decision_time_utc")) or decision_time_from_candidate_id(
            candidate_id,
            symbol,
        )
        before_status = row_decision_spread_status(source)
        attempt: dict[str, Any] = {
            "schema_version": "pending_lifecycle_tick_spread_reconstruction_v1",
            "created_at_utc": generated_utc,
            "candidate_id": candidate_id,
            "symbol": symbol,
            "decision_time_utc": decision_time.isoformat() if decision_time else None,
            "before_decision_spread_status": before_status,
            "before_decision_spread_value_source_safe": source.get(
                "pending_lifecycle_decision_spread_value_source_safe"
            ),
            "max_prior_tick_age_seconds": MAX_PRIOR_TICK_AGE_SECONDS,
            "tick_lookup_method": "LATEST_TICK_AT_OR_BEFORE_DECISION_TIME",
        }
        if not symbol or decision_time is None:
            attempt["decision_spread_status"] = "CANDIDATE_SYMBOL_OR_DECISION_TIME_NOT_PARSEABLE"
            attempts.append(attempt)
            continue
        path = tick_source_path(symbol, decision_time)
        attempt["tick_source_path"] = str(path.relative_to(REPO_ROOT))
        if not path.exists():
            attempt["decision_spread_status"] = "TICK_PARQUET_FILE_NOT_FOUND"
            attempts.append(attempt)
            continue
        payload = cache.get(path)
        attempt["tick_source_sha256"] = payload["sha256"]
        attempt["tick_source_size_bytes"] = payload["size_bytes"]
        attempt["tick_source_row_count"] = payload["row_count"]
        attempt.update(nearest_tick_payload(payload, decision_time))
        prior_offset = attempt.get("prior_tick_offset_seconds")
        if isinstance(prior_offset, (int, float)) and -MAX_PRIOR_TICK_AGE_SECONDS <= prior_offset <= 0:
            attempt["decision_spread_status"] = SUCCESS_STATUS
            attempt["decision_spread_value_source_safe"] = attempt["prior_tick_spread_cents"]
            attempt["decision_spread_unit"] = "spread_cents"
            attempt["tick_ts_utc"] = attempt["prior_tick_ts_utc"]
            attempt["tick_offset_seconds"] = prior_offset
            attempt["tick_bid"] = attempt["prior_tick_bid"]
            attempt["tick_ask"] = attempt["prior_tick_ask"]
        else:
            attempt["decision_spread_status"] = UNSAFE_STATUS
            attempt["decision_spread_unit"] = "spread_cents"
            attempt["source_requirement"] = (
                "Need a decision-time quote snapshot or tick at-or-before decision within "
                f"{MAX_PRIOR_TICK_AGE_SECONDS:g}s; current parquet lacks a source-safe prior tick."
            )
        attempts.append(attempt)
    return attempts


def build_pending_recompute_map(
    generated_utc: str,
    tick_spread_rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    candidates = latest_by_candidate(read_shadow_jsonl(SHADOW_INPUTS["strategy_follow_candidates"]))
    paths = latest_path_by_candidate(read_shadow_jsonl(SHADOW_INPUTS["candidate_path_follow"]))
    pending_lifecycle_rows = read_shadow_jsonl(SHADOW_INPUTS["pending_limit_lifecycle"])
    ltf_rows = read_shadow_jsonl(SHADOW_INPUTS["candidate_ltf_path_order"])
    structural_metadata = latest_structural_metadata_by_candidate(
        read_shadow_jsonl(SHADOW_INPUTS["live_structural_strategy_metadata"])
    )
    nofill_forward = latest_nofill_forward_capture_by_candidate(
        read_shadow_jsonl(SHADOW_INPUTS["nofill_forward_source_capture"])
    )
    tick_spreads = latest_pending_tick_spread_reconstruction_by_candidate(tick_spread_rows)
    recomputed: dict[str, dict[str, Any]] = {}
    for cid in sorted(candidates):
        candidate = merge_structural_metadata_candidate(candidates[cid], structural_metadata.get(cid))
        path = paths.get(cid)
        if not path:
            continue
        pending = latest_lifecycle_for_candidate_asof(candidate, path, pending_lifecycle_rows)
        ltf = latest_ltf_for_candidate_asof(candidate, path, ltf_rows)
        for row in build_strategy_outcome_rows(
            candidate,
            path,
            pending_lifecycle_row=pending,
            ltf_row=ltf,
            nofill_forward_capture_row=nofill_forward.get(cid),
            tick_spread_reconstruction_row=tick_spreads.get(cid),
            created_at_utc=generated_utc,
        ):
            if row.get("strategy_id") == PENDING_LIMIT_STRATEGY_ID:
                recomputed[str(row.get("candidate_id") or "")] = row
    return recomputed


def mark_before(row: dict[str, Any]) -> None:
    for field in (
        "branch_decision",
        "decision_evidence",
        "scoring_boundary",
        "implementation_candidate",
        "implementation_decision",
        "current_action",
        "next_action",
        "after_proxy_r",
        "pending_lifecycle_decision_spread_value_source_safe",
        "pending_lifecycle_decision_spread_unit",
        "pending_lifecycle_decision_spread_reconstruction_source",
        "pending_lifecycle_decision_spread_reconstruction_source_status",
        "pending_lifecycle_source_capture_statuses",
        "pending_lifecycle_source_capture_derivations",
        "pending_lifecycle_source_capture_complete",
    ):
        row[f"before_pending_tick_spread_reconstruction_{field}"] = row.get(field)


def apply_pending_scorer(row: dict[str, Any], scorer_row: dict[str, Any]) -> None:
    base_apply_pending_scorer(row, scorer_row)
    for field in (
        "pending_lifecycle_decision_spread_reconstruction_source",
        "pending_lifecycle_decision_spread_reconstruction_source_created_at_utc",
        "pending_lifecycle_decision_spread_reconstruction_source_status",
        "pending_lifecycle_decision_spread_reconstruction_tick_ts_utc",
        "pending_lifecycle_decision_spread_reconstruction_tick_offset_seconds",
        "pending_lifecycle_decision_spread_reconstruction_tick_source_path",
        "pending_lifecycle_decision_spread_reconstruction_tick_source_sha256",
    ):
        if field in scorer_row:
            row[field] = scorer_row.get(field)


def repair_status(row: dict[str, Any]) -> str:
    if row.get("strategy_id") != PENDING_LIMIT_STRATEGY_ID:
        return "NOT_PENDING_LIFECYCLE_ROW"
    statuses = row.get("pending_lifecycle_source_capture_statuses")
    if not isinstance(statuses, dict):
        return "PENDING_LIFECYCLE_RECOMPUTE_APPLIED_NO_INTERNAL_LIFECYCLE"
    before_statuses = row.get("before_pending_tick_spread_reconstruction_pending_lifecycle_source_capture_statuses")
    before_status = ""
    if isinstance(before_statuses, dict):
        before_status = str(before_statuses.get("decision_spread_value_source_safe") or "")
    derivation = statuses.get("decision_spread_value_source_safe")
    if derivation == TICK_DERIVATION and before_status == LEGACY_DERIVATION:
        return "PENDING_LIFECYCLE_DECISION_SPREAD_UPGRADED_FROM_LEGACY_TO_TICK_PARQUET"
    if derivation == TICK_DERIVATION:
        return "PENDING_LIFECYCLE_DECISION_SPREAD_REPAIRED_FROM_TICK_PARQUET"
    if before_status == MISSING_STATUS and derivation == MISSING_STATUS:
        return "PENDING_LIFECYCLE_TICK_PARQUET_NOT_SOURCE_SAFE_DECISION_SPREAD_GAP_REMAINS"
    if derivation == NOFILL_DERIVATION:
        return "PENDING_LIFECYCLE_NOFILL_FORWARD_SOURCE_PRESERVED"
    return "PENDING_LIFECYCLE_RECOMPUTE_APPLIED_NO_TICK_SPREAD_CHANGE"


def materialize_rows(
    rows: list[dict[str, Any]],
    recomputed: dict[str, dict[str, Any]],
    attempts_by_candidate: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    output: list[dict[str, Any]] = []
    stats: Counter[str] = Counter()
    generated = utc_now()
    for source in rows:
        row = {key: value for key, value in source.items() if key != "_source_line_no"}
        row["generated_utc"] = generated
        if row.get("strategy_id") != PENDING_LIMIT_STRATEGY_ID:
            row["pending_lifecycle_tick_spread_reconstruction_status"] = "NOT_PENDING_LIFECYCLE_ROW"
            output.append(row)
            continue
        stats["pending_rows"] += 1
        mark_before(row)
        candidate_id = str(row.get("candidate_id") or "")
        attempt = attempts_by_candidate.get(candidate_id)
        if attempt:
            row["pending_lifecycle_tick_spread_reconstruction_attempt_status"] = attempt.get(
                "decision_spread_status"
            )
            row["pending_lifecycle_tick_spread_reconstruction_attempt_source_path"] = attempt.get(
                "tick_source_path"
            )
            row["pending_lifecycle_tick_spread_reconstruction_attempt_source_requirement"] = attempt.get(
                "source_requirement"
            )
        scorer_row = recomputed.get(candidate_id)
        if scorer_row is None:
            row["pending_lifecycle_tick_spread_reconstruction_status"] = (
                "PENDING_LIFECYCLE_RECOMPUTE_MISSING"
            )
            stats["recompute_missing"] += 1
            output.append(row)
            continue
        apply_pending_scorer(row, scorer_row)
        status = repair_status(row)
        row["pending_lifecycle_tick_spread_reconstruction_status"] = status
        stats[status] += 1
        if row.get("before_pending_tick_spread_reconstruction_branch_decision") != row.get("branch_decision"):
            stats["branch_changed"] += 1
        if safe_float(row.get("before_pending_tick_spread_reconstruction_after_proxy_r")) != safe_float(
            row.get("after_proxy_r")
        ):
            stats["proxy_changed"] += 1
        if (
            row.get("before_pending_tick_spread_reconstruction_pending_lifecycle_source_capture_complete")
            != row.get("pending_lifecycle_source_capture_complete")
        ):
            stats["source_capture_complete_changed"] += 1
        if (
            row.get("before_pending_tick_spread_reconstruction_pending_lifecycle_decision_spread_reconstruction_source")
            != row.get("pending_lifecycle_decision_spread_reconstruction_source")
        ):
            stats["spread_reconstruction_source_changed"] += 1
        output.append(row)
    return output, dict(stats)


def tick_source_files(attempts: list[dict[str, Any]]) -> list[Path]:
    paths = []
    for row in attempts:
        rel = row.get("tick_source_path")
        if rel:
            path = REPO_ROOT / str(rel)
            if path.exists():
                paths.append(path)
    return sorted(set(paths), key=lambda path: str(path))


def build_manifest(output_paths: list[Path], attempts: list[dict[str, Any]]) -> dict[str, Any]:
    inputs = [
        INPUT_LEDGER,
        INPUT_SUMMARY,
        SCORER_SOURCE,
        TEST_SOURCE,
        PREVIOUS_BUILDER,
        *SHADOW_INPUTS.values(),
        *tick_source_files(attempts),
    ]
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
    generated = utc_now()
    attempts = reconstruct_tick_spread_rows(input_rows, generated)
    write_jsonl(RECONSTRUCTION_LEDGER, attempts)
    recomputed = build_pending_recompute_map(generated, attempts)
    attempts_by_candidate = {str(row.get("candidate_id") or ""): row for row in attempts}
    output_rows, stats = materialize_rows(input_rows, recomputed, attempts_by_candidate)
    write_jsonl(OUTPUT_LEDGER, output_rows)

    before_proxy = proxy_summary(input_rows)
    after_proxy = proxy_summary(output_rows)
    pending_rows = [row for row in output_rows if row.get("strategy_id") == PENDING_LIMIT_STRATEGY_ID]
    input_pending = [row for row in input_rows if row.get("strategy_id") == PENDING_LIMIT_STRATEGY_ID]
    kill_rows = [row for row in output_rows if row.get("action_class") == "KILL"]
    tick_rows = [
        row
        for row in pending_rows
        if (row.get("pending_lifecycle_source_capture_statuses") or {}).get(
            "decision_spread_value_source_safe"
        )
        == TICK_DERIVATION
    ]
    success_attempts = [row for row in attempts if row.get("decision_spread_status") == SUCCESS_STATUS]
    unsafe_attempts = [row for row in attempts if row.get("decision_spread_status") != SUCCESS_STATUS]
    source_requirement_rows = [
        {
            "candidate_id": row.get("candidate_id"),
            "decision_spread_status": row.get("decision_spread_status"),
            "source_requirement": row.get("source_requirement"),
            "tick_source_path": row.get("tick_source_path"),
            "prior_tick_ts_utc": row.get("prior_tick_ts_utc"),
            "next_tick_ts_utc": row.get("next_tick_ts_utc"),
            "next_tick_offset_seconds": row.get("next_tick_offset_seconds"),
        }
        for row in unsafe_attempts
    ]
    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": utc_now(),
        "evidence_class": "MAIN_ORCH24_PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION",
        "claim_boundary": (
            "Pending lifecycle decision-spread source completeness after reconstructing source-safe "
            "at-or-before decision spreads from local tick parquet. This changes current source "
            "completeness, branch decisions, and decision-spread source values where stronger tick "
            "evidence exists; R values, exact-R claims, validation safety, live behavior, and broker "
            "operations remain closed."
        ),
        "rows": len(output_rows),
        "pending_rows": len(pending_rows),
        "tick_reconstruction_attempt_rows": len(attempts),
        "tick_reconstruction_success_rows": len(success_attempts),
        "tick_reconstruction_unsafe_rows": len(unsafe_attempts),
        "tick_reconstruction_success_candidates": sorted(
            str(row.get("candidate_id") or "") for row in success_attempts
        ),
        "tick_reconstruction_source_requirements_remaining": source_requirement_rows,
        "decision_repair_stats": stats,
        "status_counts": counter(output_rows, "pending_lifecycle_tick_spread_reconstruction_status"),
        "attempt_status_counts": counter(attempts, "decision_spread_status"),
        "before_pending_branch_counts": counter(input_pending, "branch_decision"),
        "after_pending_branch_counts": counter(pending_rows, "branch_decision"),
        "before_pending_source_complete_counts": counter(input_pending, "pending_lifecycle_source_capture_complete"),
        "after_pending_source_complete_counts": counter(pending_rows, "pending_lifecycle_source_capture_complete"),
        "before_pending_decision_spread_status_counts": nested_status_counter(
            input_pending,
            "decision_spread_value_source_safe",
        ),
        "after_pending_decision_spread_status_counts": nested_status_counter(
            pending_rows,
            "decision_spread_value_source_safe",
        ),
        "tick_parquet_decision_spread_rows_after": len(tick_rows),
        "legacy_decision_spread_rows_after": sum(
            1
            for row in pending_rows
            if (row.get("pending_lifecycle_source_capture_statuses") or {}).get(
                "decision_spread_value_source_safe"
            )
            == LEGACY_DERIVATION
        ),
        "nofill_forward_decision_spread_rows_after": sum(
            1
            for row in pending_rows
            if (row.get("pending_lifecycle_source_capture_statuses") or {}).get(
                "decision_spread_value_source_safe"
            )
            == NOFILL_DERIVATION
        ),
        "remaining_pending_decision_spread_gaps": sum(
            1
            for row in pending_rows
            if (row.get("pending_lifecycle_source_capture_statuses") or {}).get(
                "decision_spread_value_source_safe"
            )
            == MISSING_STATUS
        ),
        "before_action_class_counts": input_summary.get("after_action_class_counts"),
        "after_action_class_counts": counter(output_rows, "action_class"),
        "all_metadata_gaps_after": sum(1 for row in output_rows if has_metadata_gap(row)),
        "kill_scope_audited_rows_after": sum(1 for row in kill_rows if kill_audit_present(row)),
        "exact_r_rows": sum(1 for row in output_rows if row.get("exact_r") is not None),
        "numeric_proxy_rows_before": before_proxy["numeric_proxy_rows"],
        "numeric_proxy_rows_after": after_proxy["numeric_proxy_rows"],
        "proxy_r_sum_before": before_proxy["proxy_r_sum"],
        "proxy_r_sum_after": after_proxy["proxy_r_sum"],
        "proxy_r_sum_delta": round(after_proxy["proxy_r_sum"] - before_proxy["proxy_r_sum"], 8),
        "before_pending_proxy_summary": pending_proxy_summary(input_rows),
        "after_pending_proxy_summary": pending_proxy_summary(output_rows),
        "pending_proxy_r_sum_delta": round(
            pending_proxy_summary(output_rows)["pending_proxy_r_sum"]
            - pending_proxy_summary(input_rows)["pending_proxy_r_sum"],
            8,
        ),
        "previous_plate_decision": input_summary.get("plate_decision"),
        "plate_decision": "PENDING_LIFECYCLE_TICK_SPREAD_RECONSTRUCTION_ACCEPTED_ONE_MARKET_CLOSED_GAP_REMAINS",
        "safe_flags": SAFE_FLAGS,
    }
    write_json(OUTPUT_SUMMARY, summary)
    write_json(OUTPUT_MANIFEST, build_manifest([RECONSTRUCTION_LEDGER, OUTPUT_LEDGER, OUTPUT_SUMMARY], attempts))
    print(
        json.dumps(
            {
                "rows_written": len(output_rows),
                "pending_rows": len(pending_rows),
                "tick_reconstruction_attempt_rows": len(attempts),
                "tick_reconstruction_success_rows": len(success_attempts),
                "tick_reconstruction_unsafe_rows": len(unsafe_attempts),
                "remaining_pending_decision_spread_gaps": summary[
                    "remaining_pending_decision_spread_gaps"
                ],
                "legacy_decision_spread_rows_after": summary["legacy_decision_spread_rows_after"],
                "pending_branch_counts": summary["after_pending_branch_counts"],
                "pending_decision_spread_status_counts": summary[
                    "after_pending_decision_spread_status_counts"
                ],
                "proxy_r_sum_after": summary["proxy_r_sum_after"],
                "pending_proxy_r_sum": summary["after_pending_proxy_summary"]["pending_proxy_r_sum"],
                "plate_decision": summary["plate_decision"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
