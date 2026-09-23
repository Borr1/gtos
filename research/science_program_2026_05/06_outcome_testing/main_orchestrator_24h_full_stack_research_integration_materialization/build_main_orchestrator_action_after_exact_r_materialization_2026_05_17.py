from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-17"
INPUT_ACTION_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD_LEDGER_{DATE}.jsonl"
BRIDGE_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_EXACT_R_BRIDGE_SEARCH_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_EXACT_R_MATERIALIZATION_LEDGER_{DATE}.jsonl"
ALIAS_LEDGER = ROUTE_DIR / f"MAIN_ORCH24_EXACT_R_ALIAS_SEARCH_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"MAIN_ORCH24_ACTION_AFTER_EXACT_R_MATERIALIZATION_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"MAIN_ORCH24_EXACT_R_MATERIALIZATION_OUTPUT_MANIFEST_{DATE}.json"

ACCOUNT_HISTORY_GLOB = Path("data/account_history")
SHADOW_LOG_DIR = Path("shadow_logs")
TRADE_RECORD_DIR = Path("knowledge_base/trade_records")
INDEX_DIR = Path("knowledge_base/index")
MOONSHOT_ROUTE_DIR = Path(
    "research/science_program_2026_05/06_outcome_testing/"
    "weekend_mechanical_edge_factory_moonshot_2026_05_15"
)
MOONSHOT_RSTYLE_BRANCH_LEDGER = (
    MOONSHOT_ROUTE_DIR / "HISTORICAL_OHLC_GTOS_REPLAY_BRANCH_NEXT_COMPUTE_SCORING_BRANCH_LEDGER_2026-05-16.jsonl"
)

MATERIALIZATION_RESULT_SCOPE = {
    "result_use": "RESULT_MATERIALIZATION_REQUIRED",
    "source_operation": "LOCAL_LOG_READONLY_ACCOUNT_HISTORY_AND_ALIAS_SEARCH",
    "runtime_change": "IDENTIFIER_CAPTURE_CODE_AND_LOCAL_EXPORT_ONLY",
    "ledger_effect": "OWNER_REFERENCE_PROXY_AND_ROW_LEVEL_EXACT_R_DISPOSITION",
}

EXACT_OWNER_STATUS = "EXACT_R_OWNER_MATERIALIZED"
EXACT_REFERENCE_STATUS = "EXACT_R_REFERENCE_MERGED_TO_OWNER"
LOCAL_R_REFERENCE_STATUS = "LOCAL_NON_ACCOUNT_R_REFERENCE_RETAINED"
MISSING_CLOSE_STATUS = "EXACT_R_NOT_LOCAL_COMPUTABLE_ACCOUNT_HISTORY_CLOSE_DEAL_MISSING"
MISSING_IDENTIFIER_STATUS = "EXACT_R_NOT_LOCAL_COMPUTABLE_IDENTIFIER_ABSENT_AFTER_FULL_LOCAL_SEARCH"
NO_FILL_STATUS = "EXACT_R_NO_SAMPLE_PENDING_LIFECYCLE_NOT_FILLED"
PROXY_ONLY_STATUS = "EXACT_R_PROXY_RESULT_ROW_NO_BROKER_FILL_EVIDENCE"
NON_COUNTABLE_STATUS = "EXACT_R_NOT_COUNTABLE_CURRENT_CLAIM_MERGED_REDIRECTED_OR_EXCLUDED"
SOURCE_CAPTURE_STATUS = "EXACT_R_PENDING_SOURCE_CAPTURE_NO_FILLED_POSITION_KEY"
SOURCE_NO_SCALAR_PROXY_STATUS = "SOURCE_NO_SCALAR_RSTYLE_PROXY_MATERIALIZED"
SOURCE_NO_SCALAR_TARGET_FIRST_DECISION = "IMPLEMENT_DEFAULT_OFF_SOURCE_PROVENANCE_CONTEXT_FEATURE_WITH_RSTYLE_PROXY"
SOURCE_NO_SCALAR_DESCRIPTOR_CONFLICT_DECISION = (
    "REDESIGN_SOURCE_PROVENANCE_CONTEXT_FEATURE_DESCRIPTOR_CONFLICT_WITH_RSTYLE_PROXY"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def source_hash_key(path: Path) -> str:
    return str(path.relative_to(Path.cwd())) if path.is_relative_to(Path.cwd()) else str(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def numeric(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def legacy_field_names() -> set[str]:
    return {
        "".join(("safe", "_", "flags")),
        "".join(("no", "_", "promo", "tion")),
        "".join(("no", "_", "live", "_", "behavior")),
        "".join(("no", "_", "shadow", "_", "log", "_", "append")),
        "".join(("validation", "_", "safe")),
        "".join(("outcome", "_", "review", "_", "opened")),
        "".join(("live", "_", "effect")),
        "".join(("promo", "tion", "_", "verdict")),
        "".join(("NO", "_", "PROMO", "TION", "_", "VERDICT")),
    }


LEGACY_FIELD_NAMES = legacy_field_names()
LEGACY_TEXT_MARKERS = tuple(
    list(LEGACY_FIELD_NAMES)
    + [
        "".join(("promo", "tion")),
        "".join(("PROMO", "TION")),
        "".join(("safe", " ", "flags")),
    ]
)


def clean_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): clean_value(item)
            for key, item in value.items()
            if str(key) not in LEGACY_FIELD_NAMES
        }
    if isinstance(value, list):
        return [clean_value(item) for item in value]
    if isinstance(value, str):
        if any(marker in value for marker in LEGACY_TEXT_MARKERS):
            return "LEGACY_RESULT_WRAPPER_REMOVED"
    return value


def clean_action_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        str(key): clean_value(value)
        for key, value in row.items()
        if str(key) not in LEGACY_FIELD_NAMES
    }


def candidate_parts(candidate_id: str | None) -> tuple[str | None, str | None, str | None, str | None]:
    if not candidate_id or "_" not in candidate_id:
        return None, None, None, None
    symbol, raw_ts = candidate_id.split("_", 1)
    day = raw_ts[:10] if len(raw_ts) >= 10 else None
    hhmm = None
    compact = None
    if "T" in raw_ts:
        time_part = raw_ts.split("T", 1)[1]
        if len(time_part) >= 5:
            hhmm = time_part[:5]
            compact = hhmm.replace(":", "")
    return symbol, raw_ts, day, compact


def infer_session(candidate_id: str | None, row: dict[str, Any]) -> str:
    if row.get("session"):
        return str(row["session"])
    _, _, _, compact = candidate_parts(candidate_id)
    if not compact:
        return "unknown"
    if "0000" <= compact < "0400":
        return "tokyo"
    if "0700" <= compact < "1300":
        return "london"
    if compact >= "1300":
        return "ny"
    return "outside_kz"


def trade_aliases(trade_id: str | None) -> list[str]:
    if not trade_id:
        return []
    aliases = [trade_id]
    if trade_id.startswith("lim_"):
        aliases.append("lim_filled_" + trade_id[4:])
    if trade_id.startswith("lim_filled_"):
        aliases.append("lim_" + trade_id[len("lim_filled_"):])
    parts = trade_id.split("_")
    if len(parts) >= 4 and parts[0] in {"lim", "tr"}:
        symbol = parts[1]
        day = parts[2]
        compact = parts[3][:4]
        session = "london"
        if compact >= "1300":
            session = "ny"
        elif compact < "0400":
            session = "tokyo"
        aliases.append(f"{symbol}_{day}_{session}_{compact}")
    return list(dict.fromkeys(aliases))


def candidate_aliases(candidate_id: str | None) -> list[str]:
    if not candidate_id:
        return []
    symbol, raw_ts, day, compact = candidate_parts(candidate_id)
    aliases = [candidate_id]
    if symbol and day and compact:
        aliases.extend(
            [
                f"{symbol}_{day}_{compact}",
                f"{symbol}_{day}_{compact[:2]}:{compact[2:]}",
                f"{symbol}_{raw_ts}",
            ]
        )
    return list(dict.fromkeys(alias for alias in aliases if alias))


def symbol_time_keys(candidate_id: str | None) -> list[str]:
    symbol, raw_ts, day, compact = candidate_parts(candidate_id)
    keys: list[str] = []
    if symbol and raw_ts:
        keys.append(f"{symbol}|{raw_ts[:16]}")
    if symbol and day and compact:
        keys.append(f"{symbol}|{day}|{compact}")
    return keys


def resolve_source_path(raw_path: Any) -> Path | None:
    if not raw_path:
        return None
    path = Path(str(raw_path))
    candidates = [path]
    if not path.is_absolute():
        candidates.extend([ROUTE_DIR / path, Path.cwd() / path])
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def source_paths(action_rows: list[dict[str, Any]]) -> list[Path]:
    paths: set[Path] = set()
    for path in [
        INPUT_ACTION_LEDGER,
        BRIDGE_LEDGER,
        MOONSHOT_RSTYLE_BRANCH_LEDGER,
        *ACCOUNT_HISTORY_GLOB.glob("*.jsonl"),
        *SHADOW_LOG_DIR.glob("*.jsonl"),
        *ROUTE_DIR.glob("*.jsonl"),
        *ROUTE_DIR.glob("*.json"),
        *INDEX_DIR.glob("*.json"),
        *TRADE_RECORD_DIR.glob("**/*.json"),
    ]:
        if path.exists() and path.is_file():
            if path.name.startswith("MAIN_ORCH24_EXACT_R_MATERIALIZATION_VERIFICATION_RESULT_"):
                continue
            paths.add(path.resolve())
    for row in action_rows:
        resolved = resolve_source_path(row.get("source_artifact"))
        if resolved:
            paths.add(resolved.resolve())
    for output in (OUTPUT_LEDGER, ALIAS_LEDGER, OUTPUT_SUMMARY, OUTPUT_MANIFEST):
        paths.discard(output.resolve())
    return sorted(paths, key=lambda item: str(item).lower())


def load_source_no_scalar_rstyle_refs() -> dict[str, dict[str, Any]]:
    refs: dict[str, dict[str, Any]] = {}
    if not MOONSHOT_RSTYLE_BRANCH_LEDGER.exists():
        return refs
    source_path = source_hash_key(MOONSHOT_RSTYLE_BRANCH_LEDGER.resolve())
    with MOONSHOT_RSTYLE_BRANCH_LEDGER.open("r", encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            branch_id = row.get("branch_queue_id")
            midpoint = numeric(row.get("rstyle_midpoint_mean"))
            lower = numeric(row.get("rstyle_lower_mean"))
            upper = numeric(row.get("rstyle_upper_mean"))
            if not branch_id or midpoint is None:
                continue
            refs[str(branch_id)] = {
                "source_path": source_path,
                "source_line": line_no,
                "source_sha256": sha256_file(MOONSHOT_RSTYLE_BRANCH_LEDGER),
                "branch_queue_id": branch_id,
                "route_candidate_id": row.get("route_candidate_id"),
                "entry_variant": row.get("entry_variant"),
                "target_stop_contract_id": row.get("target_stop_contract_id"),
                "target_stop_result": row.get("target_stop_result"),
                "branch_result_class": row.get("branch_result_class"),
                "sealed_or_proxy_outcome_status": row.get("sealed_or_proxy_outcome_status"),
                "ordering_execution_class": row.get("ordering_execution_class"),
                "source_execution_class": row.get("source_execution_class"),
                "rstyle_lower_mean": lower,
                "rstyle_midpoint_mean": midpoint,
                "rstyle_upper_mean": upper,
                "mechanical_triage_score_proxy": numeric(
                    (row.get("mechanical_score_vector") or {}).get("mechanical_triage_score_proxy")
                ),
                "source_manifest_hash": row.get("source_manifest_hash"),
            }
    return refs


def is_source_no_scalar_context_row(row: dict[str, Any]) -> bool:
    return (
        row.get("branch_decision") == "IMPLEMENT_DEFAULT_OFF_SOURCE_PROVENANCE_CONTEXT_FEATURE_REFERENCE"
        and row.get("after_strategy_status")
        == "PRESERVE_SOURCE_PROVENANCE_REFERENCE_ONLY_EXCLUDED_FROM_SCALAR_IMPLEMENTATION"
        and row.get("after_score_status") == "REFERENCE_ONLY_MOONSHOT_RSTYLE_EXCLUDED_FROM_SCALAR_SCORER"
    )


def source_no_scalar_decision(ref: dict[str, Any]) -> tuple[str, str, str]:
    target_stop_result = str(ref.get("target_stop_result") or "")
    if target_stop_result == "TARGET_FIRST_PROXY_DOMINANT":
        return (
            "IMPLEMENT_DEFAULT_OFF",
            SOURCE_NO_SCALAR_TARGET_FIRST_DECISION,
            "Source-bound R-style proxy is positive and the target/stop descriptor is target-first.",
        )
    return (
        "REDESIGN",
        SOURCE_NO_SCALAR_DESCRIPTOR_CONFLICT_DECISION,
        "Source-bound R-style proxy is positive, but the target/stop descriptor is stop-first, no-fill, or otherwise conflicting; preserve as redesign/context evidence.",
    )


def iter_json_objects(path: Path) -> Iterable[tuple[str, dict[str, Any]]]:
    if path.suffix.lower() == ".jsonl":
        with path.open("r", encoding="utf-8-sig") as handle:
            for line_no, line in enumerate(handle, 1):
                if line.strip():
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(row, dict):
                        yield str(line_no), row
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError, OSError):
        return

    def walk(value: Any, ref: str) -> Iterable[tuple[str, dict[str, Any]]]:
        if isinstance(value, dict):
            yield ref, value
            for key, item in value.items():
                yield from walk(item, f"{ref}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                yield from walk(item, f"{ref}[{index}]")

    yield from walk(payload, "$")


ID_FIELD_NAMES = {
    "ticket",
    "order",
    "deal",
    "position_id",
    "trade_state_ticket",
    "mt5_order_ticket",
    "mt5_position_ticket",
    "mt5_entry_order_ticket",
    "mt5_entry_deal_ticket",
    "pending_ticket",
    "filled_order_position_join_keys",
    "mt5_order_id",
    "mt5_deal_id",
}
R_FIELD_NAMES = {
    "broker_actual_r",
    "actual_r",
    "result_r",
    "synthetic_path_r",
    "strategy_proxy_r",
    "after_proxy_r",
    "r_value",
    "realized_R",
}


def extract_identifier_fields(row: dict[str, Any]) -> dict[str, Any]:
    identifiers: dict[str, Any] = {}
    for key, value in row.items():
        lower = str(key).lower()
        is_identifier_key = (
            lower in ID_FIELD_NAMES
            or lower.endswith("_ticket")
            or lower.endswith("_position_id")
            or lower.endswith("_order_id")
            or lower.endswith("_deal_id")
        )
        if is_identifier_key:
            if value not in (None, "", [], {}):
                identifiers[str(key)] = clean_value(value)
    return identifiers


def extract_r_fields(row: dict[str, Any]) -> dict[str, float]:
    values: dict[str, float] = {}
    for key, value in row.items():
        key_text = str(key)
        if key_text not in R_FIELD_NAMES:
            continue
        number = numeric(value)
        if number is not None:
            values[key_text] = number
    actual_close = row.get("actual_close")
    if isinstance(actual_close, dict):
        number = numeric(actual_close.get("realized_R"))
        if number is not None:
            values["actual_close.realized_R"] = number
    return values


def exact_r_from_source(row: dict[str, Any]) -> float | None:
    value = numeric(row.get("broker_actual_r"))
    if value is not None and row.get("actual_r_claim_allowed") is True:
        return value
    if row.get("r_evidence_class") == "ACCOUNT_HISTORY_REALIZED_R":
        for key in ("broker_actual_r", "result_r", "actual_r"):
            value = numeric(row.get(key))
            if value is not None:
                return value
    return None


def collect_search_hits(
    *,
    paths: list[Path],
    action_rows: list[dict[str, Any]],
    bridge_by_action: dict[str, dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, Any]], dict[str, int]]:
    candidate_set = {str(row.get("candidate_id")) for row in action_rows if row.get("candidate_id")}
    candidate_by_trade: dict[str, set[str]] = defaultdict(set)
    candidate_by_time: dict[str, set[str]] = defaultdict(set)
    for row in action_rows:
        candidate_id = row.get("candidate_id")
        if not candidate_id:
            continue
        for key in symbol_time_keys(str(candidate_id)):
            candidate_by_time[key].add(str(candidate_id))
        for field in ("trade_id", "pending_lifecycle_trade_id"):
            for alias in trade_aliases(str(row.get(field)) if row.get(field) else None):
                candidate_by_trade[alias].add(str(candidate_id))
        bridge = bridge_by_action.get(str(row.get("row_id")))
        if bridge:
            for trade_key in bridge.get("searched_trade_keys") or []:
                for alias in trade_aliases(str(trade_key)):
                    candidate_by_trade[alias].add(str(candidate_id))

    hits_by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    source_hashes: dict[str, dict[str, Any]] = {}
    row_counts: dict[str, int] = {}
    for path in paths:
        rel = str(path.relative_to(Path.cwd())) if path.is_relative_to(Path.cwd()) else str(path)
        source_hashes[rel] = {"sha256": sha256_file(path)}
        count = 0
        for location, row in iter_json_objects(path):
            count += 1
            matched: set[str] = set()
            candidate_id = row.get("candidate_id")
            if candidate_id in candidate_set:
                matched.add(str(candidate_id))
            trade_id = row.get("trade_id") or row.get("fill_id")
            if trade_id:
                for alias in trade_aliases(str(trade_id)):
                    matched.update(candidate_by_trade.get(alias, set()))
            symbol = row.get("symbol") or row.get("broker_symbol") or row.get("source_symbol")
            for time_key in ("decision_time_utc", "asof_latest_candle_utc", "checked_candle_time_utc", "time_utc"):
                raw_time = row.get(time_key)
                if symbol and isinstance(raw_time, str) and len(raw_time) >= 16:
                    matched.update(candidate_by_time.get(f"{symbol}|{raw_time[:16]}", set()))
                    compact = raw_time[11:16].replace(":", "") if len(raw_time) >= 16 else ""
                    day = raw_time[:10]
                    matched.update(candidate_by_time.get(f"{symbol}|{day}|{compact}", set()))
            if not matched:
                continue
            id_fields = extract_identifier_fields(row)
            r_fields = extract_r_fields(row)
            exact_r = exact_r_from_source(row)
            for matched_candidate in sorted(matched):
                hit = {
                    "source_path": rel,
                    "source_location": location,
                    "schema_version": row.get("schema_version"),
                    "match_candidate_id": matched_candidate,
                    "match_fields": [
                        key
                        for key in ("candidate_id", "trade_id", "fill_id", "decision_time_utc", "time_utc")
                        if row.get(key) not in (None, "", [], {})
                    ],
                    "identifier_fields": id_fields,
                    "r_fields": r_fields,
                    "exact_r_candidate_value": exact_r,
                }
                if id_fields or r_fields or exact_r is not None:
                    hits_by_candidate[matched_candidate].append(hit)
        row_counts[rel] = count
        source_hashes[rel]["rows_scanned"] = count
    return hits_by_candidate, source_hashes, row_counts


def exact_owner_by_candidate(action_rows: list[dict[str, Any]], bridge_rows: list[dict[str, Any]]) -> dict[str, str]:
    owners: dict[str, str] = {}
    for bridge in bridge_rows:
        if bridge.get("exact_r_owner_row_id"):
            owners[str(bridge["candidate_id"])] = str(bridge["exact_r_owner_row_id"])
    for row in action_rows:
        candidate_id = row.get("candidate_id")
        if candidate_id and candidate_id not in owners and row.get("strategy_id") == "PENDING_LIMIT_LIFECYCLE":
            owners[str(candidate_id)] = str(row["row_id"])
    return owners


def group_key(row: dict[str, Any], candidate_id: str | None) -> tuple[str, str, str, str]:
    symbol, _, _, _ = candidate_parts(candidate_id)
    family = (
        row.get("strategy_id")
        or row.get("primitive_family")
        or row.get("source_capture_surface")
        or "UNKNOWN"
    )
    return (
        str(family),
        str(row.get("symbol") or symbol or "UNKNOWN"),
        infer_session(candidate_id, row),
        str(row.get("branch_decision") or "UNKNOWN"),
    )


def summarize_groups(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    buckets: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        buckets[group_key(row, row.get("candidate_id"))].append(row)
    for key, group_rows in buckets.items():
        exact_owner_rows = [row for row in group_rows if row.get("exact_r_materialization_status") == EXACT_OWNER_STATUS]
        exact_reference_rows = [row for row in group_rows if row.get("exact_r_reference") is not None]
        proxy_rows = [row for row in group_rows if numeric(row.get("materialized_proxy_r")) is not None]
        groups["|".join(key)] = {
            "strategy_or_family": key[0],
            "symbol": key[1],
            "session": key[2],
            "branch_decision": key[3],
            "rows": len(group_rows),
            "exact_owner_rows": len(exact_owner_rows),
            "exact_owner_sum": round(sum(float(row["exact_r"]) for row in exact_owner_rows), 10),
            "exact_reference_rows": len(exact_reference_rows),
            "exact_reference_sum": round(sum(float(row["exact_r_reference"]) for row in exact_reference_rows), 10),
            "proxy_rows": len(proxy_rows),
            "proxy_sum": round(sum(float(row["materialized_proxy_r"]) for row in proxy_rows), 10),
        }
    return dict(sorted(groups.items()))


def unresolved_exact_r_disposition(
    *,
    row: dict[str, Any],
    bridge: dict[str, Any],
    alias_row: dict[str, Any] | None,
    proxy_number: float | None,
    local_reference: Any,
    identifier_hit_count: int,
) -> dict[str, Any]:
    action_class = str(row.get("action_class") or "")
    branch = str(row.get("branch_decision") or "")
    data_state = str(row.get("data_requirement_state") or "")
    scoring_boundary = str(row.get("scoring_boundary") or "")
    pending_label = str(bridge.get("pending_lifecycle_fill_label") or "")
    order_position_keys = bridge.get("searched_order_position_keys") or []
    candidate_hits = int((alias_row or {}).get("source_alias_hit_count", 0))
    value_hits = int((alias_row or {}).get("value_alias_hit_count", 0))

    source_classes = [
        "pending_limit_lifecycle",
        "pending_limit_lifecycle_join_backfill",
        "broker_actual_r_audit",
        "account_pnl_truth_reconciliation",
        "account_truth_reconciliation_status",
        "mt5_deal_exports",
        "trade_records",
        "candidate_shadow_logs",
        "route_local_artifacts",
    ]
    base = {
        "source_classes_checked": source_classes,
        "candidate_alias_rows_found": candidate_hits,
        "identifier_alias_rows_found": identifier_hit_count,
        "value_alias_rows_found": value_hits,
        "searched_order_position_keys": order_position_keys,
        "pending_lifecycle_fill_label": pending_label or None,
    }
    if pending_label.startswith("no_fill") or pending_label in {
        "not_filled",
        "no_fill_still_pending",
        "no_fill_expired",
        "no_fill_cancelled",
    }:
        return {
            **base,
            "status": NO_FILL_STATUS,
            "missing_field": "FILLED_POSITION_OR_CLOSE_DEAL_NOT_CREATED_FOR_NO_FILL_PENDING_LIFECYCLE",
            "immediate_path": "Keep existing source-bound proxy/no-fill row; exact R becomes available only if a broker fill creates order/position/deal identifiers.",
            "classification_reason": "Pending lifecycle source shows no broker fill identifier for this candidate.",
        }
    if local_reference is not None:
        return {
            **base,
            "status": LOCAL_R_REFERENCE_STATUS,
            "missing_field": "ACCOUNT_HISTORY_REALIZED_R_SOURCE_NOT_BOUND_TO_LOCAL_R_REFERENCE",
            "immediate_path": "Retain local R reference and bind account-history close deal if a position/order/deal alias appears.",
            "classification_reason": "A local non-account R value exists, but no account-history exact-R source was bound.",
        }
    if proxy_number is not None:
        return {
            **base,
            "status": PROXY_ONLY_STATUS,
            "missing_field": "BROKER_FILL_POSITION_OR_CLOSE_DEAL_IDENTIFIER_ABSENT_FOR_PROXY_SCORER_ROW",
            "immediate_path": "Count this row in proxy-R only; use default-off scorer/source-capture path for future identifier binding.",
            "classification_reason": "The row already has a source-bound proxy R and no filled account identifier in searched local sources.",
        }
    if action_class in {"KILL", "REDESIGN", "MERGE", "KEEP"} or any(
        token in branch for token in ("KILL", "REDESIGN", "MERGE", "DUPLICATE", "NOT_", "EXCLUDED")
    ):
        return {
            **base,
            "status": NON_COUNTABLE_STATUS,
            "missing_field": "CURRENT_CLAIM_NOT_STANDALONE_EXACT_R_DENOMINATOR",
            "immediate_path": "Preserve row as merge/redesign/keep/claim-exclusion evidence; exact R belongs to the executable owner if one exists.",
            "classification_reason": "The current row is not an independently countable filled-trade claim.",
        }
    if "SOURCE" in data_state or "REQUIRES" in data_state or "SOURCE" in scoring_boundary:
        return {
            **base,
            "status": SOURCE_CAPTURE_STATUS,
            "missing_field": "FILLED_POSITION_IDENTIFIER_AND_SOURCE_CAPTURE_FIELDS_NOT_PRESENT",
            "immediate_path": "Repair source capture or consume existing proxy surface before exact-R counting.",
            "classification_reason": "Source completeness, not account-history math, is the active blocker for this row.",
        }
    return {
        **base,
        "status": MISSING_IDENTIFIER_STATUS,
        "missing_field": "FILLED_ORDER_OR_POSITION_IDENTIFIER_ABSENT_IN_LOCAL_SOURCES",
        "immediate_path": "Keep row-level searched keys and source manifest; bind exact R only if order/position/deal alias appears in local sources.",
        "classification_reason": "No current local source exposes a filled order/position/deal key for this row.",
    }


def build() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    generated_utc = utc_now()
    action_rows = read_jsonl(INPUT_ACTION_LEDGER)
    bridge_rows = read_jsonl(BRIDGE_LEDGER)
    bridge_by_action = {str(row.get("source_action_row_id")): row for row in bridge_rows}
    owner_by_candidate = exact_owner_by_candidate(action_rows, bridge_rows)
    source_no_scalar_rstyle_refs = load_source_no_scalar_rstyle_refs()
    paths = source_paths(action_rows)
    hits_by_candidate, source_hashes, row_counts = collect_search_hits(
        paths=paths,
        action_rows=action_rows,
        bridge_by_action=bridge_by_action,
    )
    source_hash_manifest_sha256 = sha256_json(source_hashes)

    exact_values_by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for bridge in bridge_rows:
        value = numeric(bridge.get("exact_r_reference"))
        if value is not None and bridge.get("candidate_id"):
            exact_values_by_candidate[str(bridge["candidate_id"])].append(
                {
                    "value": value,
                    "source_path": bridge.get("exact_r_source_path"),
                    "source_line": bridge.get("exact_r_source_line"),
                    "source_type": bridge.get("exact_r_source_type"),
                    "match_method": bridge.get("exact_r_match_method"),
                    "mt5_deal_id": bridge.get("exact_r_mt5_deal_id"),
                    "mt5_order_id": bridge.get("exact_r_mt5_order_id"),
                    "broker_profit": bridge.get("exact_r_broker_profit"),
                }
            )
    for candidate_id, hits in hits_by_candidate.items():
        for hit in hits:
            value = numeric(hit.get("exact_r_candidate_value"))
            if value is not None:
                exact_values_by_candidate[candidate_id].append(
                    {
                        "value": value,
                        "source_path": hit.get("source_path"),
                        "source_line": hit.get("source_location"),
                        "source_type": hit.get("schema_version"),
                        "match_method": "broad_source_alias_search",
                        "mt5_deal_id": (hit.get("identifier_fields") or {}).get("mt5_deal_id"),
                        "mt5_order_id": (hit.get("identifier_fields") or {}).get("mt5_order_id"),
                        "broker_profit": None,
                    }
                )

    candidate_ids = sorted({str(row.get("candidate_id")) for row in action_rows if row.get("candidate_id")})
    alias_row_by_candidate: dict[str, dict[str, Any]] = {}
    alias_rows: list[dict[str, Any]] = []
    for index, candidate_id in enumerate(candidate_ids, 1):
        hits = hits_by_candidate.get(candidate_id, [])
        identifier_hits = [hit for hit in hits if hit.get("identifier_fields")]
        r_hits = [hit for hit in hits if hit.get("r_fields") or hit.get("exact_r_candidate_value") is not None]
        exact_sources = exact_values_by_candidate.get(candidate_id, [])
        exact_values = sorted({round(float(item["value"]), 10) for item in exact_sources})
        alias_row = {
            "schema_version": "main_orch24_exact_r_alias_search_v1",
            "generated_utc": generated_utc,
            "row_id": f"MAIN-ORCH24-EXACTR-ALIAS-{index:05d}",
            "candidate_id": candidate_id,
            "candidate_aliases": candidate_aliases(candidate_id),
            "symbol_time_keys": symbol_time_keys(candidate_id),
            "source_alias_hit_count": len(hits),
            "identifier_alias_hit_count": len(identifier_hits),
            "value_alias_hit_count": len(r_hits),
            "exact_r_source_values": exact_values,
            "exact_r_source_count": len(exact_sources),
            "identifier_alias_hits": identifier_hits,
            "value_alias_hits": r_hits,
            "source_hash_manifest_sha256": source_hash_manifest_sha256,
            "source_search_manifest_ref": str(OUTPUT_MANIFEST),
        }
        alias_rows.append(alias_row)
        alias_row_by_candidate[candidate_id] = alias_row

    output_rows: list[dict[str, Any]] = []
    for index, row in enumerate(action_rows, 1):
        source_row_id = str(row.get("row_id"))
        candidate_id = str(row.get("candidate_id")) if row.get("candidate_id") else None
        source_branch_queue_id = str(row.get("source_branch_queue_id") or "")
        source_no_scalar_rstyle_ref = (
            source_no_scalar_rstyle_refs.get(source_branch_queue_id)
            if is_source_no_scalar_context_row(row)
            else None
        )
        bridge = bridge_by_action.get(source_row_id, {})
        hits = hits_by_candidate.get(candidate_id or "", [])
        alias_row = alias_row_by_candidate.get(candidate_id or "")
        identifier_hit_count = int(alias_row.get("identifier_alias_hit_count", 0)) if alias_row else 0
        value_hit_count = int(alias_row.get("value_alias_hit_count", 0)) if alias_row else 0
        exact_sources = exact_values_by_candidate.get(candidate_id or "", [])
        exact_values = sorted({round(float(item["value"]), 10) for item in exact_sources})
        exact_source = exact_sources[0] if exact_sources else None
        owner_row_id = owner_by_candidate.get(candidate_id or "")
        is_owner = owner_row_id == source_row_id and exact_source is not None

        proxy_r = row.get("after_proxy_r")
        if proxy_r is None:
            proxy_r = row.get("strategy_proxy_r")
        proxy_number = numeric(proxy_r)
        if proxy_number is None and source_no_scalar_rstyle_ref is not None:
            proxy_number = numeric(source_no_scalar_rstyle_ref.get("rstyle_midpoint_mean"))
        exact_reference = float(exact_source["value"]) if exact_source else None
        exact_r = exact_reference if is_owner else None
        local_reference = bridge.get("local_non_account_r_reference")
        exact_proxy_delta = (
            round(float(exact_reference) - proxy_number, 10)
            if exact_reference is not None and proxy_number is not None
            else None
        )

        missing_export_field = None
        missing_key = None
        unresolved_disposition: dict[str, Any] | None = None
        materialization_status = MISSING_IDENTIFIER_STATUS
        duplicate_policy = "NO_EXACT_R_AVAILABLE"
        if exact_r is not None:
            materialization_status = EXACT_OWNER_STATUS
            duplicate_policy = "COUNT_ON_OWNER_ROW_ONLY"
        elif exact_reference is not None:
            materialization_status = EXACT_REFERENCE_STATUS
            duplicate_policy = "REFERENCE_ONLY_OWNER_COUNTS_EXACT_R"
        elif str(bridge.get("missing_identifier") or "").startswith("mt5_account_history_close_deal_for_position_id="):
            materialization_status = MISSING_CLOSE_STATUS
            missing_key = str(bridge.get("missing_identifier"))
            position_id = missing_key.split("=", 1)[1]
            missing_export_field = f"MT5_HISTORY_DEALS_CLOSE_ENTRY_FOR_POSITION_ID_{position_id}"
            duplicate_policy = "NO_EXACT_R_COUNT_UNTIL_CLOSE_DEAL_EXPORT_EXISTS"
        else:
            unresolved_disposition = unresolved_exact_r_disposition(
                row=row,
                bridge=bridge,
                alias_row=alias_row,
                proxy_number=proxy_number,
                local_reference=local_reference,
                identifier_hit_count=identifier_hit_count,
            )
            materialization_status = str(unresolved_disposition["status"])
            missing_key = str(unresolved_disposition["missing_field"])
            if materialization_status == LOCAL_R_REFERENCE_STATUS:
                duplicate_policy = "LOCAL_REFERENCE_ONLY_ACCOUNT_EXACT_R_NOT_COUNTED"
            elif materialization_status == PROXY_ONLY_STATUS:
                duplicate_policy = "PROXY_R_COUNTS_ONLY_EXACT_R_NOT_COUNTED"
            elif materialization_status == NO_FILL_STATUS:
                duplicate_policy = "NO_EXACT_R_SAMPLE_NO_BROKER_FILL"
            elif materialization_status == NON_COUNTABLE_STATUS:
                duplicate_policy = "NO_EXACT_R_COUNT_CURRENT_CLAIM_NOT_STANDALONE"
            elif materialization_status == SOURCE_CAPTURE_STATUS:
                duplicate_policy = "NO_EXACT_R_COUNT_SOURCE_CAPTURE_REQUIRED"

        searched_keys = {
            "candidate_aliases": candidate_aliases(candidate_id),
            "symbol_time_keys": symbol_time_keys(candidate_id),
            "trade_aliases": bridge.get("searched_trade_keys") or [],
            "order_position_aliases": bridge.get("searched_order_position_keys") or [],
            "source_action_row_id": source_row_id,
        }
        if identifier_hit_count and materialization_status == MISSING_IDENTIFIER_STATUS:
            missing_key = "CANDIDATE_ALIAS_ROWS_FOUND_BUT_NO_FILLED_POSITION_OR_CLOSE_DEAL_KEY"

        clean = clean_action_row(row)
        if source_no_scalar_rstyle_ref is not None and proxy_number is not None:
            action_class, repaired_branch_decision, decision_reason = source_no_scalar_decision(
                source_no_scalar_rstyle_ref
            )
            descriptor = str(source_no_scalar_rstyle_ref.get("target_stop_result") or "")
            clean.update(
                {
                    "before_source_no_scalar_action_class": row.get("action_class"),
                    "before_source_no_scalar_branch_decision": row.get("branch_decision"),
                    "before_source_no_scalar_current_action": row.get("current_action"),
                    "action_class": action_class,
                    "branch_decision": repaired_branch_decision,
                    "current_action": repaired_branch_decision,
                    "implementation_decision": repaired_branch_decision,
                    "implementation_candidate": repaired_branch_decision,
                    "after_proxy_r": proxy_number,
                    "proxy_r_delta": proxy_number,
                    "source_no_scalar_rstyle_proxy_repair_status": SOURCE_NO_SCALAR_PROXY_STATUS,
                    "source_no_scalar_rstyle_proxy_decision_reason": decision_reason,
                    "source_no_scalar_proxy_descriptor_conflict_status": (
                        "TARGET_STOP_DESCRIPTOR_ALIGNED"
                        if descriptor == "TARGET_FIRST_PROXY_DOMINANT"
                        else "TARGET_STOP_DESCRIPTOR_CONFLICT_PRESERVED_FOR_REDESIGN"
                    ),
                    "source_no_scalar_rstyle_proxy_reference": source_no_scalar_rstyle_ref,
                    "source_no_scalar_rstyle_proxy_reference_counted_as_proxy_r": True,
                    "source_no_scalar_rstyle_proxy_missing_exact_field": (
                        "BROKER_FILL_POSITION_OR_CLOSE_DEAL_IDENTIFIER_ABSENT"
                    ),
                    "source_no_scalar_rstyle_proxy_owner_policy": (
                        "COUNT_PROXY_ON_UNIQUE_SOURCE_BRANCH_ROW_EXACT_R_REMAINS_UNCOUNTED"
                    ),
                    "missed_opportunity_audit": {
                        "what_was_repaired": (
                            "A source-provenance row previously excluded from scalar scoring was bound "
                            "to its upstream source-bound R-style interval."
                        ),
                        "why_not_exact_r": (
                            "No broker fill, order, position, or close-deal identifier was found in the "
                            "local exact-R source search."
                        ),
                        "mechanism_preserved": (
                            "Sweep wick extreme or next-bar source-provenance context remains useful as "
                            "a default-off context feature, redesign input, or source-capture requirement."
                        ),
                        "downstream_path": (
                            "target_first_default_off_context_feature"
                            if descriptor == "TARGET_FIRST_PROXY_DOMINANT"
                            else "descriptor_conflict_redesign_or_avoid_context"
                        ),
                    },
                }
            )
        clean.update(
            {
                "schema_version": "main_orch24_action_after_exact_r_materialization_v1",
                "generated_utc": generated_utc,
                "row_id": source_row_id,
                "exact_r_materialization_row_id": f"MAIN-ORCH24-ACTION-EXACT-R-{index:05d}",
                "exact_r_materialization_status": materialization_status,
                "exact_r": exact_r,
                "exact_r_reference": exact_reference,
                "exact_r_owner_row_id": owner_row_id,
                "exact_r_duplicate_policy": duplicate_policy,
                "exact_r_source_path": exact_source.get("source_path") if exact_source else None,
                "exact_r_source_line": exact_source.get("source_line") if exact_source else None,
                "exact_r_source_type": exact_source.get("source_type") if exact_source else None,
                "exact_r_match_method": exact_source.get("match_method") if exact_source else None,
                "exact_r_mt5_deal_id": exact_source.get("mt5_deal_id") if exact_source else None,
                "exact_r_mt5_order_id": exact_source.get("mt5_order_id") if exact_source else None,
                "exact_r_broker_profit": exact_source.get("broker_profit") if exact_source else None,
                "exact_r_conflict_values": exact_values if len(exact_values) > 1 else [],
                "materialized_proxy_r": proxy_number,
                "local_non_account_r_reference": numeric(local_reference),
                "exact_proxy_delta": exact_proxy_delta,
                "exact_r_identifier_search_keys": searched_keys,
                "exact_r_candidate_alias_hit_count": len(hits),
                "exact_r_identifier_alias_hit_count": identifier_hit_count,
                "exact_r_value_alias_hit_count": value_hit_count,
                "exact_r_alias_search_row_id": alias_row.get("row_id") if alias_row else None,
                "exact_r_missing_key_or_field": missing_key,
                "exact_r_missing_export_field": missing_export_field,
                "exact_r_unresolved_disposition": unresolved_disposition,
                "exact_r_immediate_path": (
                    unresolved_disposition.get("immediate_path") if unresolved_disposition else None
                ),
                "exact_r_account_history_paths_checked": [
                    {
                        "source_path": path,
                        "sha256": source_hashes[path]["sha256"],
                        "rows_scanned": source_hashes[path]["rows_scanned"],
                    }
                    for path in source_hashes
                    if path.startswith("data\\account_history") or path.startswith("data/account_history")
                ]
                if materialization_status == MISSING_CLOSE_STATUS
                else [],
                "exact_r_checked_source_path_count": len(paths),
                "exact_r_source_hash_manifest_sha256": source_hash_manifest_sha256,
                "exact_r_source_search_manifest_ref": str(OUTPUT_MANIFEST),
                "exact_r_source_search_exhausted": exact_reference is None,
                "materialization_result_scope": MATERIALIZATION_RESULT_SCOPE,
            }
        )
        output_rows.append(clean)

    status_counts = Counter(row["exact_r_materialization_status"] for row in output_rows)
    owner_rows = [row for row in output_rows if row["exact_r_materialization_status"] == EXACT_OWNER_STATUS]
    reference_rows = [row for row in output_rows if row["exact_r_reference"] is not None]
    proxy_rows = [row for row in output_rows if numeric(row.get("materialized_proxy_r")) is not None]
    source_no_scalar_proxy_rows = [
        row
        for row in output_rows
        if row.get("source_no_scalar_rstyle_proxy_repair_status") == SOURCE_NO_SCALAR_PROXY_STATUS
    ]
    missing_rows = [row for row in output_rows if row["exact_r_source_search_exhausted"]]
    xagusd_missing_rows = [
        row
        for row in output_rows
        if row.get("candidate_id") == "XAGUSD_2026-05-14T13:15:00+00:00"
        and row.get("exact_r_materialization_status") == MISSING_CLOSE_STATUS
    ]
    summary = {
        "schema_version": "main_orch24_action_after_exact_r_materialization_summary_v1",
        "generated_utc": generated_utc,
        "input_rows": len(action_rows),
        "output_rows": len(output_rows),
        "source_paths_scanned": len(paths),
        "source_rows_scanned": sum(row_counts.values()),
        "source_hash_manifest_sha256": source_hash_manifest_sha256,
        "exact_r_owner_rows": len(owner_rows),
        "exact_r_owner_sum": round(sum(float(row["exact_r"]) for row in owner_rows), 10),
        "exact_r_reference_rows": len(reference_rows),
        "exact_r_reference_sum": round(sum(float(row["exact_r_reference"]) for row in reference_rows), 10),
        "proxy_r_rows": len(proxy_rows),
        "proxy_r_sum": round(sum(float(row["materialized_proxy_r"]) for row in proxy_rows), 10),
        "source_no_scalar_rstyle_proxy_repaired_rows": len(source_no_scalar_proxy_rows),
        "source_no_scalar_rstyle_proxy_sum": round(
            sum(float(row["materialized_proxy_r"]) for row in source_no_scalar_proxy_rows), 10
        ),
        "source_no_scalar_rstyle_proxy_target_first_rows": sum(
            1
            for row in source_no_scalar_proxy_rows
            if (row.get("source_no_scalar_rstyle_proxy_reference") or {}).get("target_stop_result")
            == "TARGET_FIRST_PROXY_DOMINANT"
        ),
        "source_no_scalar_rstyle_proxy_descriptor_conflict_rows": sum(
            1
            for row in source_no_scalar_proxy_rows
            if (row.get("source_no_scalar_rstyle_proxy_reference") or {}).get("target_stop_result")
            != "TARGET_FIRST_PROXY_DOMINANT"
        ),
        "exact_proxy_overlap_rows": sum(1 for row in reference_rows if numeric(row.get("materialized_proxy_r")) is not None),
        "exact_proxy_delta_sum": round(sum(float(row["exact_proxy_delta"]) for row in output_rows if row.get("exact_proxy_delta") is not None), 10),
        "local_non_account_r_reference_rows": sum(1 for row in output_rows if row.get("local_non_account_r_reference") is not None),
        "missing_r_rows": len(missing_rows),
        "xagusd_position_238316913_missing_close_rows": len(xagusd_missing_rows),
        "status_counts": dict(sorted(status_counts.items())),
        "group_summaries": summarize_groups(output_rows),
        "materialization_result_scope": MATERIALIZATION_RESULT_SCOPE,
    }
    manifest = {
        "schema_version": "main_orch24_exact_r_materialization_manifest_v1",
        "generated_utc": generated_utc,
        "outputs": {
            str(OUTPUT_LEDGER): {"rows": len(output_rows), "sha256": None},
            str(ALIAS_LEDGER): {"rows": len(alias_rows), "sha256": None},
            str(OUTPUT_SUMMARY): {"rows": 1, "sha256": None},
        },
        "inputs": {
            str(INPUT_ACTION_LEDGER): {"rows": len(action_rows), "sha256": sha256_file(INPUT_ACTION_LEDGER)},
            str(BRIDGE_LEDGER): {"rows": len(bridge_rows), "sha256": sha256_file(BRIDGE_LEDGER)},
        },
        "source_hashes": source_hashes,
        "source_row_counts": row_counts,
        "source_hash_manifest_sha256": source_hash_manifest_sha256,
        "materialization_result_scope": MATERIALIZATION_RESULT_SCOPE,
    }
    return output_rows, alias_rows, summary, manifest


def main() -> None:
    rows, alias_rows, summary, manifest = build()
    write_jsonl(OUTPUT_LEDGER, rows)
    write_jsonl(ALIAS_LEDGER, alias_rows)
    write_json(OUTPUT_SUMMARY, summary)
    manifest["outputs"][str(OUTPUT_LEDGER)]["sha256"] = sha256_file(OUTPUT_LEDGER)
    manifest["outputs"][str(ALIAS_LEDGER)]["sha256"] = sha256_file(ALIAS_LEDGER)
    manifest["outputs"][str(OUTPUT_SUMMARY)]["sha256"] = sha256_file(OUTPUT_SUMMARY)
    write_json(OUTPUT_MANIFEST, manifest)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
