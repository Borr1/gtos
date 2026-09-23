#!/usr/bin/env python3
"""Build a no-fill entry-geometry repair/proxy packet.

This packet consumes the no-fill challenger packet and turns readiness labels
into same-resource proxy classes. It preserves every branch row and emits only
geometry/source/proxy evidence; it does not score outcomes, R, PnL,
expectancy, win-rate, live-readiness, or promotion.
"""

from __future__ import annotations

import hashlib
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
REPO = ROUTE_DIR.parents[3]

CHALLENGER_RESULT_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_CHALLENGER_RESULT_2026-05-16.json"
CHALLENGER_INPUT_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_CHALLENGER_INPUT_JOIN_2026-05-16.jsonl"
CHALLENGER_BRANCH_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_CHALLENGER_BRANCH_PACKET_2026-05-16.jsonl"
CHALLENGER_READINESS_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_CHALLENGER_READINESS_LEDGER_2026-05-16.jsonl"
CHALLENGER_DENOMINATOR_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_CHALLENGER_DENOMINATOR_LEDGER_2026-05-16.jsonl"

PATH_FOLLOW_PATH = REPO / "shadow_logs" / "candidate_path_follow.jsonl"
LTF_PATH_ORDER_PATH = REPO / "shadow_logs" / "candidate_ltf_path_order.jsonl"
NOFILL_FORWARD_CAPTURE_PATH = REPO / "shadow_logs" / "nofill_forward_source_capture.jsonl"

RESULT_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_RESULT_2026-05-16.json"
CANDIDATE_LEDGER_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_CANDIDATE_LEDGER_2026-05-16.jsonl"
BRANCH_LEDGER_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_BRANCH_LEDGER_2026-05-16.jsonl"
SPREAD_PROXY_LEDGER_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_SPREAD_LEDGER_2026-05-16.jsonl"
BUCKET_LEDGER_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_BUCKET_LEDGER_2026-05-16.jsonl"
QUESTION_LEDGER_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_QUESTION_LEDGER_2026-05-16.jsonl"
SUMMARY_PATH = ROUTE_DIR / "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_SUMMARY_2026-05-16.md"

OUTPUT_MANIFEST_PATH = ROUTE_DIR / "OUTPUT_MANIFEST_2026-05-15.json"
SPRINT_LEDGER_PATH = ROUTE_DIR / "SPRINT_OPERATING_LEDGER_2026-05-15.jsonl"

SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}

CLAIM_BOUNDARY = (
    "No-fill entry-geometry repair/proxy packet only. Rows are geometry, "
    "source, spread-proxy, and path-proxy labels; no validation, R/PnL, "
    "expectancy, win-rate, live-readiness, or live behavior change is claimed."
)

NOFILL_LABEL = "continued_without_entry_touch_to_tp_area"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {"_parse_error": True, "_line_no": line_no}


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def source_manifest() -> tuple[list[dict[str, Any]], str]:
    paths = [
        CHALLENGER_RESULT_PATH,
        CHALLENGER_INPUT_PATH,
        CHALLENGER_BRANCH_PATH,
        CHALLENGER_READINESS_PATH,
        CHALLENGER_DENOMINATOR_PATH,
        PATH_FOLLOW_PATH,
        LTF_PATH_ORDER_PATH,
        NOFILL_FORWARD_CAPTURE_PATH,
    ]
    rows: list[dict[str, Any]] = []
    for path in paths:
        if path.exists():
            rows.append(
                {
                    "path": str(path.relative_to(REPO)).replace("\\", "/"),
                    "sha256": sha256_file(path),
                    "status": "HASHED",
                }
            )
        else:
            rows.append(
                {
                    "path": str(path.relative_to(REPO)).replace("\\", "/"),
                    "sha256": "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED",
                    "status": "MISSING_FAIL_CLOSED",
                }
            )
    manifest_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode("utf-8")).hexdigest()
    return rows, manifest_hash


def sort_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("asof_latest_candle_utc") or row.get("checked_candle_time_utc") or ""),
        str(row.get("created_at_utc") or row.get("backfilled_at_utc") or row.get("capture_write_completed_at_utc") or ""),
        str(row.get("row_key") or row.get("candidate_id") or ""),
    )


def latest_by_candidate(path: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(path):
        if row.get("_parse_error"):
            continue
        candidate_id = row.get("candidate_id")
        if not candidate_id:
            continue
        current = latest.get(candidate_id)
        if current is None or sort_key(row) >= sort_key(current):
            latest[candidate_id] = row
    return latest


def numeric(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def rounded(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 6)


def valid_tp_geometry(side: str, proposed_entry: float | None, take_profit_1: float | None) -> tuple[bool, float | None]:
    if proposed_entry is None or take_profit_1 is None:
        return False, None
    if side == "LONG":
        return proposed_entry < take_profit_1, rounded(take_profit_1 - proposed_entry)
    if side == "SHORT":
        return proposed_entry > take_profit_1, rounded(proposed_entry - take_profit_1)
    return False, None


def spread_capture_rows() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    by_candidate: dict[str, dict[str, Any]] = {}
    values_by_symbol: dict[str, list[float]] = defaultdict(list)
    rows_by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in read_jsonl(NOFILL_FORWARD_CAPTURE_PATH):
        if row.get("_parse_error"):
            continue
        candidate_id = row.get("candidate_id")
        value = numeric(row.get("decision_spread_value_source_safe"))
        symbol = row.get("symbol")
        if candidate_id and value is not None:
            by_candidate[candidate_id] = row
        if symbol and value is not None and row.get("decision_spread_status") == "QUOTE_SNAPSHOT_CAPTURED_SOURCE_SAFE":
            values_by_symbol[symbol].append(value)
            rows_by_symbol[symbol].append(row)
    symbol_proxy: dict[str, dict[str, Any]] = {}
    for symbol, values in values_by_symbol.items():
        symbol_proxy[symbol] = {
            "symbol": symbol,
            "proxy_value": rounded(statistics.median(values)),
            "proxy_source_count": len(values),
            "proxy_source_min": rounded(min(values)),
            "proxy_source_max": rounded(max(values)),
            "proxy_source_hashes": sorted({str(row.get("spread_source_hash")) for row in rows_by_symbol[symbol]}),
        }
    return by_candidate, symbol_proxy


def spread_for(candidate_id: str, symbol: str, exact_by_candidate: dict[str, dict[str, Any]], symbol_proxy: dict[str, dict[str, Any]]) -> dict[str, Any]:
    exact = exact_by_candidate.get(candidate_id)
    if exact:
        return {
            "decision_spread_status_after_proxy": "EXACT_DECISION_SPREAD_CAPTURED_SOURCE_SAFE",
            "decision_spread_value_after_proxy": rounded(numeric(exact.get("decision_spread_value_source_safe"))),
            "decision_spread_proxy_source": "nofill_forward_source_capture.candidate_exact",
            "decision_spread_proxy_source_count": 1,
            "decision_spread_unit": exact.get("decision_spread_unit"),
        }
    proxy = symbol_proxy.get(symbol)
    if proxy:
        return {
            "decision_spread_status_after_proxy": "SYMBOL_MEDIAN_DECISION_SPREAD_PROXY_SOURCE_SAFE",
            "decision_spread_value_after_proxy": proxy["proxy_value"],
            "decision_spread_proxy_source": "nofill_forward_source_capture.symbol_median",
            "decision_spread_proxy_source_count": proxy["proxy_source_count"],
            "decision_spread_unit": "spread_cents",
        }
    return {
        "decision_spread_status_after_proxy": "SPREAD_PROXY_UNAVAILABLE_FAIL_CLOSED",
        "decision_spread_value_after_proxy": None,
        "decision_spread_proxy_source": "no_same_symbol_forward_capture_spread_rows",
        "decision_spread_proxy_source_count": 0,
        "decision_spread_unit": None,
    }


def path_proxy_class(
    branch: dict[str, Any],
    input_row: dict[str, Any],
    readiness_row: dict[str, Any],
    ltf_row: dict[str, Any] | None,
    path_row: dict[str, Any] | None,
) -> dict[str, Any]:
    side = str(branch.get("side") or input_row.get("side") or "")
    proposed_entry = numeric(branch.get("proposed_entry_price_input_only"))
    take_profit_1 = numeric(branch.get("take_profit_1"))
    valid_geometry, tp_room = valid_tp_geometry(side, proposed_entry, take_profit_1)
    if not valid_geometry:
        return {
            "geometry_status": "TP1_NOT_BEYOND_PROPOSED_ENTRY_ROUTE_SPLIT_REQUIRED",
            "path_proxy_status": "NO_PATH_PROXY_GEOMETRY_INVALID_FOR_ORIGINAL_TP1",
            "proxy_projection_status": "ROUTE_SPLIT_INVALID_TP1_GEOMETRY",
            "side_adjusted_tp_room": tp_room,
            "proxy_source_detail": "branch proposed entry is at or beyond original TP1 in side-adjusted direction",
        }

    ltf_status = readiness_row.get("ltf_status")
    source_status = input_row.get("source_status") or {}
    path_order_label = source_status.get("path_order_label") or (ltf_row or {}).get("path_order_label")
    tick_order_claim_status = source_status.get("tick_order_claim_status")
    path_label = input_row.get("path_label") or (path_row or {}).get("path_label")
    touched_entry = (path_row or {}).get("touched_entry")
    hit_tp1 = (path_row or {}).get("hit_tp1")

    if ltf_status == "M1_PATH_RECOVERED" and path_order_label == "tp1_area_reached_without_entry_touch":
        return {
            "geometry_status": "TP1_BEYOND_PROPOSED_ENTRY",
            "path_proxy_status": "M1_RECOVERED_TP_AREA_BRANCH_ENVELOPE_FEASIBLE_ORDER_AMBIGUOUS",
            "proxy_projection_status": "NO_SCORE_PROXY_READY_M1_RECOVERED_ORDER_AMBIGUOUS",
            "side_adjusted_tp_room": tp_room,
            "proxy_source_detail": "M1 recovery proves TP1 area reached without original-entry touch; branch entry and TP order remains unscored without tick sequence",
            "m1_bar_count": (ltf_row or {}).get("m1_bar_count"),
            "tp1_first_touch_utc": (ltf_row or {}).get("tp1_first_touch_utc"),
            "tick_order_claim_status": tick_order_claim_status,
        }

    if path_label == NOFILL_LABEL and (hit_tp1 is True or path_order_label == "tp1_area_reached_without_entry_touch") and touched_entry is not True:
        return {
            "geometry_status": "TP1_BEYOND_PROPOSED_ENTRY",
            "path_proxy_status": "M15_ENVELOPE_TP_AREA_BRANCH_FEASIBLE_LTF_SOURCE_BLOCKED",
            "proxy_projection_status": "NO_SCORE_PROXY_AVAILABLE_M15_ENVELOPE_ONLY_LTF_REQUIRED",
            "side_adjusted_tp_room": tp_room,
            "proxy_source_detail": "M15/latest path envelope labels TP1 area reached without original-entry touch; lower-timeframe order remains source-blocked",
            "tick_order_claim_status": tick_order_claim_status,
        }

    return {
        "geometry_status": "TP1_BEYOND_PROPOSED_ENTRY",
        "path_proxy_status": "PATH_PROXY_UNSUPPORTED_BY_CURRENT_JOIN",
        "proxy_projection_status": "NO_SCORE_PROXY_UNAVAILABLE_SOURCE_GAP",
        "side_adjusted_tp_room": tp_room,
        "proxy_source_detail": "current joins do not establish a no-fill TP-area path envelope for this branch",
        "tick_order_claim_status": tick_order_claim_status,
    }


def update_manifest(outputs: dict[str, Any], generated_at: str) -> None:
    manifest = read_json(OUTPUT_MANIFEST_PATH)
    if not manifest:
        manifest = {"route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H", "outputs": []}
    existing = [row for row in manifest.get("outputs", []) if row.get("artifact") != RESULT_PATH.name]
    existing.append(
        {
            "artifact": RESULT_PATH.name,
            "category": "nofill_entry_geometry_repair_proxy_packet",
            "generated_utc": generated_at,
            "counts": outputs["counts"],
            "safe_flags": SAFE_FLAGS,
            "claim_boundary": CLAIM_BOUNDARY,
        }
    )
    manifest["outputs"] = existing
    manifest["last_updated_utc"] = generated_at
    OUTPUT_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_sprint_ledger(outputs: dict[str, Any], generated_at: str) -> None:
    row = {
        "timestamp_utc": generated_at,
        "event_type": "route_artifact_built",
        "route": "nofill_entry_geometry_repair_proxy_packet",
        "artifact": RESULT_PATH.name,
        "counts": outputs["counts"],
        "not_completion": True,
        "safe_flags": SAFE_FLAGS,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    with SPRINT_LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def main() -> int:
    generated_at = now_utc()
    manifest_rows, manifest_hash = source_manifest()

    challenger_result = read_json(CHALLENGER_RESULT_PATH)
    input_rows = [row for row in read_jsonl(CHALLENGER_INPUT_PATH) if not row.get("_parse_error")]
    branch_rows = [row for row in read_jsonl(CHALLENGER_BRANCH_PATH) if not row.get("_parse_error")]
    readiness_rows = [row for row in read_jsonl(CHALLENGER_READINESS_PATH) if not row.get("_parse_error")]
    denominator_rows = [row for row in read_jsonl(CHALLENGER_DENOMINATOR_PATH) if not row.get("_parse_error")]

    inputs_by_candidate = {row["candidate_id"]: row for row in input_rows}
    readiness_by_branch = {row["branch_id"]: row for row in readiness_rows}
    ltf_by_candidate = latest_by_candidate(LTF_PATH_ORDER_PATH)
    path_by_candidate = latest_by_candidate(PATH_FOLLOW_PATH)
    spread_exact, spread_symbol_proxy = spread_capture_rows()

    nofill_input_rows = [row for row in input_rows if row.get("is_nofill_tp_area") is True]
    nofill_candidate_ids = {row["candidate_id"] for row in nofill_input_rows}

    spread_proxy_rows: list[dict[str, Any]] = []
    for symbol, proxy in sorted(spread_symbol_proxy.items()):
        spread_proxy_rows.append(
            {
                "symbol": symbol,
                "evidence_class": "NOFILL_ENTRY_GEOMETRY_REPAIR_SPREAD_PROXY",
                "claim_boundary": CLAIM_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
                "source_manifest_hash": manifest_hash,
                "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
                **proxy,
            }
        )

    branch_proxy_rows: list[dict[str, Any]] = []
    branch_count_by_candidate: dict[str, Counter[str]] = defaultdict(Counter)
    for branch in branch_rows:
        candidate_id = branch["candidate_id"]
        input_row = inputs_by_candidate[candidate_id]
        readiness_row = readiness_by_branch.get(branch["branch_id"], {})
        ltf_row = ltf_by_candidate.get(candidate_id)
        path_row = path_by_candidate.get(candidate_id)
        spread = spread_for(candidate_id, branch.get("symbol") or input_row.get("symbol"), spread_exact, spread_symbol_proxy)
        path_proxy = path_proxy_class(branch, input_row, readiness_row, ltf_row, path_row)
        lifecycle_audit_status = (input_row.get("source_status") or {}).get("lifecycle_audit_status")
        lifecycle_proxy_status = "LIFECYCLE_SOURCE_DOCUMENTED"
        if lifecycle_audit_status == "PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED":
            lifecycle_proxy_status = "LIFECYCLE_ACTION_REQUIRED_STRESS_LABEL"
        elif lifecycle_audit_status in {None, "MISSING"}:
            lifecycle_proxy_status = "LIFECYCLE_MISSING_PATH_PROXY_ONLY"

        proxy_projection_status = path_proxy["proxy_projection_status"]
        if (
            proxy_projection_status != "ROUTE_SPLIT_INVALID_TP1_GEOMETRY"
            and spread["decision_spread_status_after_proxy"] == "SPREAD_PROXY_UNAVAILABLE_FAIL_CLOSED"
        ):
            proxy_projection_status = "NO_SCORE_PROXY_BLOCKED_SPREAD_UNAVAILABLE"

        row = {
            "branch_id": branch["branch_id"],
            "candidate_id": candidate_id,
            "symbol": branch.get("symbol"),
            "side": branch.get("side"),
            "framework": branch.get("framework"),
            "branch_type": branch.get("branch_type"),
            "decision_time_utc": branch.get("decision_time_utc"),
            "original_entry_price": branch.get("original_entry_price"),
            "proposed_entry_price_input_only": branch.get("proposed_entry_price_input_only"),
            "take_profit_1": branch.get("take_profit_1"),
            "stop_loss": branch.get("stop_loss"),
            "original_readiness_status": readiness_row.get("readiness_status"),
            "original_blocker_codes": readiness_row.get("blocker_codes", []),
            "lifecycle_proxy_status": lifecycle_proxy_status,
            "evidence_class": "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_BRANCH",
            "claim_boundary": CLAIM_BOUNDARY,
            "not_scored": True,
            "safe_flags": SAFE_FLAGS,
            "source_manifest_hash": manifest_hash,
            "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
            **spread,
            **path_proxy,
            "proxy_projection_status": proxy_projection_status,
        }
        branch_proxy_rows.append(row)
        branch_count_by_candidate[candidate_id][proxy_projection_status] += 1

    candidate_rows: list[dict[str, Any]] = []
    for input_row in nofill_input_rows:
        candidate_id = input_row["candidate_id"]
        counts = branch_count_by_candidate[candidate_id]
        candidate_rows.append(
            {
                "candidate_id": candidate_id,
                "symbol": input_row.get("symbol"),
                "side": input_row.get("side"),
                "framework": input_row.get("framework"),
                "decision_time_utc": input_row.get("decision_time_utc"),
                "path_label": input_row.get("path_label"),
                "branch_count": sum(counts.values()),
                "proxy_projection_status_counts": dict(sorted(counts.items())),
                "has_m1_recovered": (input_row.get("source_status") or {}).get("ltf_status") == "M1_PATH_RECOVERED",
                "has_forward_capture": (input_row.get("source_status") or {}).get("forward_capture_status") == "PRESENT",
                "evidence_class": "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_CANDIDATE",
                "claim_boundary": CLAIM_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
                "source_manifest_hash": manifest_hash,
                "source_file_hash_status": "HASHED_SOURCE_MANIFEST",
            }
        )

    bucket_rows: list[dict[str, Any]] = []
    bucket_axes = {
        "proxy_projection_status": Counter(row["proxy_projection_status"] for row in branch_proxy_rows),
        "path_proxy_status": Counter(row["path_proxy_status"] for row in branch_proxy_rows),
        "geometry_status": Counter(row["geometry_status"] for row in branch_proxy_rows),
        "lifecycle_proxy_status": Counter(row["lifecycle_proxy_status"] for row in branch_proxy_rows),
        "decision_spread_status_after_proxy": Counter(row["decision_spread_status_after_proxy"] for row in branch_proxy_rows),
        "candidate_proxy_status_combo": Counter(
            "|".join(f"{status}:{count}" for status, count in sorted((row["proxy_projection_status_counts"]).items()))
            for row in candidate_rows
        ),
    }
    for axis, counter in bucket_axes.items():
        for bucket, count in sorted(counter.items()):
            bucket_rows.append(
                {
                    "bucket_axis": axis,
                    "bucket": bucket,
                    "count": count,
                    "evidence_class": "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_BUCKET",
                    "claim_boundary": CLAIM_BOUNDARY,
                    "safe_flags": SAFE_FLAGS,
                }
            )

    question_rows: list[dict[str, Any]] = []
    question_id = 1
    for status, count in sorted(bucket_axes["proxy_projection_status"].items()):
        if status == "ROUTE_SPLIT_INVALID_TP1_GEOMETRY":
            action = "split branch into target-retargeting or entry-router redesign; original TP1 cannot be reused for this proposed entry"
        elif status == "NO_SCORE_PROXY_READY_M1_RECOVERED_ORDER_AMBIGUOUS":
            action = "build tick/order reconstruction or same-bar ambiguity stress for M1 recovered rows"
        elif status == "NO_SCORE_PROXY_AVAILABLE_M15_ENVELOPE_ONLY_LTF_REQUIRED":
            action = "attempt MT5/Sierra/public/free lower-timeframe extraction; otherwise build M15 envelope stress controls"
        elif status == "NO_SCORE_PROXY_BLOCKED_SPREAD_UNAVAILABLE":
            action = "search local quote/spread sources or broaden symbol spread proxy before branch projection"
        else:
            action = "preserve source gap and seek same-resource repair or proxy"
        question_rows.append(
            {
                "question_id": f"NOFILL-REPAIR-PROXY-QUESTION-{question_id:03d}",
                "question": "What immediate same-resource action follows from this no-fill repair/proxy status?",
                "proxy_projection_status": status,
                "branch_count": count,
                "next_same_resource_action": action,
                "evidence_class": "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_QUESTION",
                "claim_boundary": CLAIM_BOUNDARY,
                "safe_flags": SAFE_FLAGS,
            }
        )
        question_id += 1

    counts = {
        "branch_proxy_rows": len(branch_proxy_rows),
        "bucket_rows": len(bucket_rows),
        "candidate_proxy_rows": len(candidate_rows),
        "challenger_branch_rows": len(branch_rows),
        "challenger_denominator_rows": len(denominator_rows),
        "challenger_input_rows": len(input_rows),
        "challenger_readiness_rows": len(readiness_rows),
        "nofill_candidate_rows": len(nofill_candidate_ids),
        "question_rows": len(question_rows),
        "source_manifest_rows": len(manifest_rows),
        "spread_proxy_symbol_rows": len(spread_proxy_rows),
    }
    result = {
        "route_id": "WEEKEND_MECHANICAL_EDGE_FACTORY_ABSOLUTE_NORTH_STAR_60H",
        "schema": "nofill_entry_geometry_repair_proxy_packet_v1",
        "generated_utc": generated_at,
        "evidence_class": "NOFILL_ENTRY_GEOMETRY_REPAIR_PROXY_ONLY",
        "claim_boundary": CLAIM_BOUNDARY,
        "safe_flags": SAFE_FLAGS,
        "not_completion": "This repair/proxy packet does not complete the 60-hour moonshot objective.",
        "counts": counts,
        "upstream_challenger_counts": challenger_result.get("counts", {}),
        "proxy_projection_status_counts": dict(sorted(bucket_axes["proxy_projection_status"].items())),
        "path_proxy_status_counts": dict(sorted(bucket_axes["path_proxy_status"].items())),
        "geometry_status_counts": dict(sorted(bucket_axes["geometry_status"].items())),
        "lifecycle_proxy_status_counts": dict(sorted(bucket_axes["lifecycle_proxy_status"].items())),
        "decision_spread_status_after_proxy_counts": dict(sorted(bucket_axes["decision_spread_status_after_proxy"].items())),
        "source_manifest": manifest_rows,
        "source_manifest_hash": manifest_hash,
        "next_same_resource_work": [
            "build M1/tick same-bar ambiguity stress for recovered rows",
            "build M15 envelope stress controls for source-blocked rows",
            "split invalid TP1 geometry into target-retargeting and market-entry redesign branches",
            "attempt lower-timeframe reconstruction for source-blocked rows from owned/current/free sources",
        ],
    }

    write_jsonl(CANDIDATE_LEDGER_PATH, candidate_rows)
    write_jsonl(BRANCH_LEDGER_PATH, branch_proxy_rows)
    write_jsonl(SPREAD_PROXY_LEDGER_PATH, spread_proxy_rows)
    write_jsonl(BUCKET_LEDGER_PATH, bucket_rows)
    write_jsonl(QUESTION_LEDGER_PATH, question_rows)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(
        "\n".join(
            [
                "# No-Fill Entry Geometry Repair/Proxy Packet",
                "",
                f"Generated UTC: `{generated_at}`",
                "",
                "This packet preserves every no-fill branch from the challenger packet and converts readiness blockers into same-resource proxy classes without scoring outcomes.",
                "",
                "## Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in counts.items()),
                "",
                "## Proxy Projection Status Counts",
                "",
                *(f"- `{key}`: `{value}`" for key, value in sorted(bucket_axes["proxy_projection_status"].items())),
                "",
                "## Immediate Work",
                "",
                "- Build M1/tick same-bar ambiguity stress for recovered rows.",
                "- Build M15 envelope stress controls for source-blocked rows.",
                "- Split invalid TP1 geometry into target-retargeting and market-entry redesign branches.",
                "- Attempt lower-timeframe reconstruction from owned/current/free sources for source-blocked rows.",
                "",
                "No validation, R/PnL, expectancy, win-rate, live-readiness, promotion, or live behavior-change claim is made.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    update_manifest(result, generated_at)
    append_sprint_ledger(result, generated_at)
    print(json.dumps({"ok": True, "counts": counts, "proxy_projection_status_counts": result["proxy_projection_status_counts"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
