"""Materialize exact-R bridge joins for the current action ledger."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROUTE_DIR = Path(__file__).resolve().parent

ACTION_LEDGER = ROUTE_DIR / "MAIN_ORCH24_ACTION_AFTER_ENTRY_OFFSET_CONCENTRATION_GUARD_LEDGER_2026-05-17.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / "MAIN_ORCH24_EXACT_R_BRIDGE_SEARCH_LEDGER_2026-05-17.jsonl"
SUMMARY_PATH = ROUTE_DIR / "MAIN_ORCH24_EXACT_R_BRIDGE_SEARCH_SUMMARY_2026-05-17.json"
MANIFEST_PATH = ROUTE_DIR / "MAIN_ORCH24_EXACT_R_BRIDGE_SEARCH_OUTPUT_MANIFEST_2026-05-17.json"

BROKER_ACTUAL_R = Path("shadow_logs/broker_actual_r_audit.jsonl")
ACCOUNT_PNL_TRUTH = Path("shadow_logs/account_pnl_truth_reconciliation.jsonl")
ACCOUNT_TRUTH = Path("shadow_logs/account_truth_reconciliation_status.jsonl")
PENDING_LIFECYCLE = Path("shadow_logs/pending_limit_lifecycle.jsonl")
PENDING_JOIN_BACKFILL = Path("shadow_logs/pending_limit_lifecycle_join_backfill.jsonl")
J46_J49_OUTCOMES = Path("shadow_logs/j46_j49_shadow_outcomes.jsonl")
ACCOUNT_HISTORY_DIR = Path("data/account_history")
ACCOUNT_HISTORY_FILES = sorted(ACCOUNT_HISTORY_DIR.glob("mt5_deals_*.jsonl"))

SOURCE_PATHS_SEARCHED = [
    str(BROKER_ACTUAL_R),
    str(ACCOUNT_PNL_TRUTH),
    str(ACCOUNT_TRUTH),
    str(PENDING_LIFECYCLE),
    str(PENDING_JOIN_BACKFILL),
    str(J46_J49_OUTCOMES),
    *(str(path) for path in ACCOUNT_HISTORY_FILES),
]

RESULT_SCOPE = {
    "result_use": "RESULT_MATERIALIZATION_REQUIRED",
    "source_operation": "LOCAL_LOG_AND_READONLY_ACCOUNT_HISTORY_SEARCH",
    "runtime_change": "NONE_FROM_SEARCH",
    "ledger_effect": "EXACT_R_OWNER_REFERENCE_AND_UNRESOLVED_ROW_DISPOSITION",
}


def read_jsonl(path: Path) -> list[tuple[int, dict[str, Any]]]:
    rows: list[tuple[int, dict[str, Any]]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_no, line in enumerate(handle, 1):
            if line.strip():
                rows.append((line_no, json.loads(line)))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def numeric(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def candidate_time_parts(candidate_id: str | None) -> tuple[str | None, str | None, str | None]:
    if not candidate_id or "_" not in candidate_id:
        return None, None, None
    symbol, raw_ts = candidate_id.split("_", 1)
    day = raw_ts[:10] if len(raw_ts) >= 10 else None
    hhmm = None
    if "T" in raw_ts and len(raw_ts.split("T", 1)[1]) >= 5:
        hhmm = raw_ts.split("T", 1)[1][:5].replace(":", "")
    return symbol, day, hhmm


def pending_trade_aliases(trade_id: str | None) -> list[str]:
    if not trade_id:
        return []
    aliases = [trade_id]
    if trade_id.startswith("lim_"):
        aliases.append("lim_filled_" + trade_id[4:])
    parts = trade_id.split("_")
    if len(parts) >= 4 and parts[0] == "lim":
        symbol = parts[1]
        day = parts[2]
        hhmm = parts[3][:4]
        session = "london"
        if hhmm >= "1300":
            session = "ny"
        elif hhmm < "0400":
            session = "tokyo"
        aliases.append(f"{symbol}_{day}_{session}_{hhmm}")
    return list(dict.fromkeys(aliases))


def build_sources() -> dict[str, Any]:
    account_history_rows = []
    deal_by_ticket: dict[int, dict[str, Any]] = {}
    order_to_position: dict[int, int] = {}
    position_to_deals: dict[int, list[dict[str, Any]]] = defaultdict(list)
    source_row_counts = {}
    for path in ACCOUNT_HISTORY_FILES:
        rows = read_jsonl(path)
        source_row_counts[str(path)] = len(rows)
        for line_no, row in rows:
            item = {**row, "_source_path": str(path), "_source_line": line_no}
            account_history_rows.append(item)
            ticket = row.get("ticket")
            order = row.get("order")
            position_id = row.get("position_id")
            if isinstance(ticket, int):
                deal_by_ticket[ticket] = item
            if isinstance(order, int) and isinstance(position_id, int):
                order_to_position[order] = position_id
            if isinstance(position_id, int):
                position_to_deals[position_id].append(item)

    exact_by_trade: dict[str, dict[str, Any]] = {}
    exact_by_position: dict[int, dict[str, Any]] = {}
    exact_by_candidate: dict[str, dict[str, Any]] = {}
    local_r_by_trade: dict[str, dict[str, Any]] = {}
    local_r_by_fill: dict[str, dict[str, Any]] = {}

    for line_no, row in read_jsonl(BROKER_ACTUAL_R):
        source_row_counts[str(BROKER_ACTUAL_R)] = source_row_counts.get(str(BROKER_ACTUAL_R), 0) + 1
        value = numeric(row.get("broker_actual_r"))
        if value is None:
            continue
        links = row.get("source_links") if isinstance(row.get("source_links"), dict) else {}
        source = {
            "exact_r": value,
            "exact_r_source_type": "BROKER_ACTUAL_R_AUDIT",
            "source_path": str(BROKER_ACTUAL_R),
            "source_line": line_no,
            "trade_id": row.get("trade_id"),
            "candidate_id": row.get("candidate_id"),
            "ticket": row.get("ticket"),
            "broker_profit": None,
            "mt5_deal_id": links.get("mt5_export_deal_id"),
            "mt5_order_id": links.get("mt5_export_order_id") or row.get("ticket"),
        }
        if row.get("trade_id"):
            exact_by_trade[str(row["trade_id"])] = source
        if row.get("candidate_id"):
            exact_by_candidate[str(row["candidate_id"])] = source
        if isinstance(row.get("ticket"), int):
            exact_by_position[int(row["ticket"])] = source

    for line_no, row in read_jsonl(ACCOUNT_PNL_TRUTH):
        source_row_counts[str(ACCOUNT_PNL_TRUTH)] = source_row_counts.get(str(ACCOUNT_PNL_TRUTH), 0) + 1
        result_r = numeric(row.get("result_r"))
        local_payload = {
            "local_r": result_r,
            "local_r_source_type": row.get("r_evidence_class"),
            "source_path": str(ACCOUNT_PNL_TRUTH),
            "source_line": line_no,
            "trade_id": row.get("trade_id"),
            "broker_profit": row.get("broker_profit"),
            "mt5_deal_id": row.get("mt5_deal_id"),
            "mt5_order_id": row.get("mt5_order_id"),
        }
        if row.get("trade_id") and result_r is not None:
            local_r_by_trade[str(row["trade_id"])] = local_payload

        exact_r = numeric(row.get("broker_actual_r"))
        if (
            exact_r is not None
            and row.get("actual_r_claim_allowed") is True
            and row.get("r_evidence_class") == "ACCOUNT_HISTORY_REALIZED_R"
        ):
            exact_source = {
                "exact_r": exact_r,
                "exact_r_source_type": "ACCOUNT_HISTORY_REALIZED_R",
                "source_path": str(ACCOUNT_PNL_TRUTH),
                "source_line": line_no,
                "trade_id": row.get("trade_id"),
                "candidate_id": None,
                "ticket": None,
                "broker_profit": row.get("broker_profit"),
                "mt5_deal_id": row.get("mt5_deal_id"),
                "mt5_order_id": row.get("mt5_order_id"),
            }
            if row.get("trade_id"):
                exact_by_trade[str(row["trade_id"])] = exact_source
            order = row.get("mt5_order_id")
            deal = row.get("mt5_deal_id")
            position = None
            if isinstance(order, int):
                position = order_to_position.get(order)
            if position is None and isinstance(deal, int):
                deal_row = deal_by_ticket.get(deal)
                if deal_row and isinstance(deal_row.get("position_id"), int):
                    position = int(deal_row["position_id"])
            if position is not None:
                exact_by_position[position] = exact_source

    for line_no, row in read_jsonl(J46_J49_OUTCOMES):
        source_row_counts[str(J46_J49_OUTCOMES)] = source_row_counts.get(str(J46_J49_OUTCOMES), 0) + 1
        fill_id = row.get("fill_id")
        actual_close = row.get("actual_close") if isinstance(row.get("actual_close"), dict) else {}
        value = numeric(actual_close.get("realized_R"))
        if fill_id and value is not None:
            local_r_by_fill[str(fill_id)] = {
                "local_r": value,
                "local_r_source_type": "J46_J49_ACTUAL_CLOSE",
                "source_path": str(J46_J49_OUTCOMES),
                "source_line": line_no,
                "trade_id": fill_id,
                "broker_deal_reconciled": actual_close.get("broker_deal_reconciled"),
            }

    pending_by_candidate: dict[str, dict[str, Any]] = {}
    for line_no, row in read_jsonl(PENDING_LIFECYCLE):
        source_row_counts[str(PENDING_LIFECYCLE)] = source_row_counts.get(str(PENDING_LIFECYCLE), 0) + 1
        candidate_id = row.get("candidate_id")
        if not candidate_id:
            continue
        current = pending_by_candidate.get(str(candidate_id))
        current_ts = str(current.get("timestamp_utc") if current else "")
        row_ts = str(row.get("timestamp_utc") or "")
        if current is None or row_ts >= current_ts:
            pending_by_candidate[str(candidate_id)] = {**row, "_source_line": line_no}

    for path in [ACCOUNT_TRUTH, PENDING_JOIN_BACKFILL]:
        source_row_counts[str(path)] = len(read_jsonl(path))

    return {
        "source_row_counts": source_row_counts,
        "exact_by_trade": exact_by_trade,
        "exact_by_candidate": exact_by_candidate,
        "exact_by_position": exact_by_position,
        "local_r_by_trade": local_r_by_trade,
        "local_r_by_fill": local_r_by_fill,
        "pending_by_candidate": pending_by_candidate,
        "position_to_deals": position_to_deals,
        "order_to_position": order_to_position,
        "deal_by_ticket": deal_by_ticket,
    }


def row_trade_keys(row: dict[str, Any], pending: dict[str, Any] | None) -> list[str]:
    keys: list[str] = []
    for key in ("trade_id", "pending_lifecycle_trade_id"):
        if row.get(key):
            keys.extend(pending_trade_aliases(str(row[key])))
    if pending:
        for key in ("trade_id",):
            if pending.get(key):
                keys.extend(pending_trade_aliases(str(pending[key])))
    return list(dict.fromkeys(keys))


def choose_exact(row: dict[str, Any], pending: dict[str, Any] | None, sources: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    candidate_id = row.get("candidate_id")
    if candidate_id and candidate_id in sources["exact_by_candidate"]:
        return sources["exact_by_candidate"][candidate_id], "candidate_id"

    for trade_key in row_trade_keys(row, pending):
        if trade_key in sources["exact_by_trade"]:
            return sources["exact_by_trade"][trade_key], f"trade_id:{trade_key}"

    for position_id in pending_position_ids(pending, sources):
        if position_id in sources["exact_by_position"]:
            return sources["exact_by_position"][position_id], f"position_id:{position_id}"
    return None, None


def pending_position_ids(pending: dict[str, Any] | None, sources: dict[str, Any]) -> list[int]:
    if not pending:
        return []
    ids: list[int] = []
    for key in ("trade_state_ticket", "mt5_position_ticket", "mt5_order_ticket", "pending_ticket"):
        if isinstance(pending.get(key), int):
            ids.append(int(pending[key]))
    entry_order = pending.get("mt5_entry_order_ticket")
    if isinstance(entry_order, int):
        mapped = sources["order_to_position"].get(int(entry_order))
        ids.append(int(mapped) if mapped is not None else int(entry_order))
    entry_deal = pending.get("mt5_entry_deal_ticket")
    if isinstance(entry_deal, int):
        deal_row = sources["deal_by_ticket"].get(int(entry_deal))
        if deal_row and isinstance(deal_row.get("position_id"), int):
            ids.append(int(deal_row["position_id"]))
    join_keys = pending.get("filled_order_position_join_keys")
    if isinstance(join_keys, list):
        for item in join_keys:
            if not isinstance(item, str) or ":" not in item:
                continue
            name, raw_value = item.split(":", 1)
            try:
                value = int(raw_value)
            except ValueError:
                continue
            if name in {"trade_state_ticket", "mt5_position_ticket"}:
                ids.append(value)
            elif name == "mt5_entry_order_ticket":
                mapped = sources["order_to_position"].get(value)
                ids.append(int(mapped) if mapped is not None else value)
            elif name == "mt5_entry_deal_ticket":
                deal_row = sources["deal_by_ticket"].get(value)
                if deal_row and isinstance(deal_row.get("position_id"), int):
                    ids.append(int(deal_row["position_id"]))
    return list(dict.fromkeys(ids))


def choose_local_r(row: dict[str, Any], pending: dict[str, Any] | None, sources: dict[str, Any]) -> dict[str, Any] | None:
    for trade_key in row_trade_keys(row, pending):
        if trade_key in sources["local_r_by_trade"]:
            return sources["local_r_by_trade"][trade_key]
        if trade_key in sources["local_r_by_fill"]:
            return sources["local_r_by_fill"][trade_key]
    return None


def exact_owner_row_ids(action_rows: list[dict[str, Any]], exact_candidates: set[str]) -> dict[str, str]:
    owners: dict[str, str] = {}
    for row in action_rows:
        candidate_id = row.get("candidate_id")
        if candidate_id not in exact_candidates:
            continue
        if row.get("strategy_id") == "PENDING_LIMIT_LIFECYCLE":
            owners[str(candidate_id)] = str(row.get("row_id"))
    for row in action_rows:
        candidate_id = row.get("candidate_id")
        if candidate_id in exact_candidates and candidate_id not in owners:
            owners[str(candidate_id)] = str(row.get("row_id"))
    return owners


def missing_reason(
    row: dict[str, Any],
    pending: dict[str, Any] | None,
    local_r: dict[str, Any] | None,
    sources: dict[str, Any],
) -> tuple[str, str]:
    position_ids = pending_position_ids(pending, sources)
    if position_ids:
        position_id = position_ids[0]
        deals = sources["position_to_deals"].get(position_id, [])
        close_deals = [deal for deal in deals if deal.get("entry") == 1]
        if not close_deals:
            return (
                f"mt5_account_history_close_deal_for_position_id={position_id}",
                "EXACT_R_NOT_COMPUTABLE_ACCOUNT_HISTORY_EXPORT_MISSING_POSITION_CLOSE",
            )
        return (
            f"account_history_realized_r_for_position_id={position_id}",
            "EXACT_R_NOT_COMPUTABLE_ACCOUNT_HISTORY_DEAL_FOUND_BUT_R_RECONCILIATION_MISSING",
        )
    if local_r is not None:
        return (
            "account_history_realized_r_for_local_result",
            "EXACT_R_NOT_COMPUTABLE_LOCAL_R_ONLY_ACCOUNT_HISTORY_REALIZED_R_MISSING",
        )
    if pending and pending.get("fill_no_fill_label") == "internal_filled_broker_ticket_known":
        return (
            "filled_lifecycle_ticket_or_position_id",
            "EXACT_R_NOT_COMPUTABLE_FILLED_LIFECYCLE_ROW_LACKS_ACCOUNT_POSITION_IDENTIFIER",
        )
    return (
        "filled_trade_state_ticket_or_account_position_id",
        "EXACT_R_NOT_COMPUTABLE_NO_FILLED_ORDER_OR_POSITION_IDENTIFIER_IN_CURRENT_ROW",
    )


def build() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    generated_utc = datetime.now(timezone.utc).isoformat()
    sources = build_sources()
    action_pairs = read_jsonl(ACTION_LEDGER)
    action_rows = [row for _, row in action_pairs]

    candidate_exact: dict[str, tuple[dict[str, Any], str]] = {}
    candidate_pending: dict[str, dict[str, Any] | None] = {}
    candidate_local: dict[str, dict[str, Any] | None] = {}
    for row in action_rows:
        candidate_id = row.get("candidate_id")
        if not candidate_id:
            continue
        pending = sources["pending_by_candidate"].get(str(candidate_id))
        candidate_pending[str(candidate_id)] = pending
        exact, match_method = choose_exact(row, pending, sources)
        if exact is not None and str(candidate_id) not in candidate_exact:
            candidate_exact[str(candidate_id)] = (exact, str(match_method))
        if str(candidate_id) not in candidate_local:
            candidate_local[str(candidate_id)] = choose_local_r(row, pending, sources)

    owner_by_candidate = exact_owner_row_ids(action_rows, set(candidate_exact))
    output_rows: list[dict[str, Any]] = []
    before_exact_rows = sum(1 for row in action_rows if numeric(row.get("exact_r")) is not None)

    for index, (source_line, row) in enumerate(action_pairs, 1):
        candidate_id = row.get("candidate_id")
        pending = candidate_pending.get(str(candidate_id)) if candidate_id else None
        trade_keys = row_trade_keys(row, pending)
        position_keys = []
        if pending:
            for key in (
                "pending_ticket",
                "trade_state_ticket",
                "mt5_position_ticket",
                "mt5_order_ticket",
                "mt5_entry_order_ticket",
                "mt5_entry_deal_ticket",
            ):
                if pending.get(key) is not None:
                    position_keys.append(f"{key}:{pending.get(key)}")
            if isinstance(pending.get("filled_order_position_join_keys"), list):
                position_keys.extend(str(item) for item in pending["filled_order_position_join_keys"])
            position_keys = list(dict.fromkeys(position_keys))
        exact_tuple = candidate_exact.get(str(candidate_id)) if candidate_id else None
        local_r = candidate_local.get(str(candidate_id)) if candidate_id else None

        exact_r = None
        exact_status = "EXACT_R_NOT_FOUND"
        exact_source = None
        exact_match_method = None
        owner_row_id = owner_by_candidate.get(str(candidate_id)) if candidate_id else None
        is_owner = owner_row_id == row.get("row_id")
        if exact_tuple is not None:
            exact_source, exact_match_method = exact_tuple
            exact_r = exact_source["exact_r"]
            exact_status = (
                "EXACT_R_COUNTED_ON_OWNER_ROW"
                if is_owner
                else "EXACT_R_REFERENCE_ONLY_OWNER_ROW"
            )

        missing_identifier = None
        exact_join_decision = None
        if exact_tuple is None:
            missing_identifier, exact_join_decision = missing_reason(row, pending, local_r, sources)
        else:
            exact_join_decision = (
                "IMPLEMENT_EXACT_R_ON_PENDING_LIFECYCLE_OWNER_ROW"
                if is_owner
                else "MERGE_EXACT_R_REFERENCE_TO_PENDING_LIFECYCLE_OWNER_ROW"
            )

        symbol, day, hhmm = candidate_time_parts(str(candidate_id) if candidate_id else None)
        candidate_symbol = symbol or row.get("symbol")
        strategy_or_family_id = (
            row.get("strategy_id")
            or row.get("primitive_family")
            or row.get("source_capture_surface")
            or row.get("source_plate")
        )
        output_rows.append(
            {
                "schema_version": "main_orch24_exact_r_bridge_search_v1",
                "route_id": "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION",
                "generated_utc": generated_utc,
                "row_id": f"MAIN-ORCH24-EXACTR-BRIDGE-{index:05d}",
                "source_action_row_id": row.get("row_id"),
                "source_action_line": source_line,
                "candidate_id": candidate_id,
                "candidate_symbol": candidate_symbol,
                "symbol": candidate_symbol,
                "candidate_day": day,
                "candidate_hhmm": hhmm,
                "strategy_id": row.get("strategy_id"),
                "strategy_or_family_id": strategy_or_family_id,
                "primitive_family": row.get("primitive_family"),
                "source_capture_surface": row.get("source_capture_surface"),
                "source_artifact": row.get("source_artifact"),
                "source_line_no": row.get("source_line_no"),
                "action_class": row.get("action_class"),
                "branch_decision": row.get("branch_decision"),
                "input_exact_r": row.get("exact_r"),
                "input_proxy_r": row.get("after_proxy_r")
                if row.get("after_proxy_r") is not None
                else row.get("strategy_proxy_r"),
                "searched_source_paths": SOURCE_PATHS_SEARCHED,
                "searched_candidate_keys": [key for key in [candidate_id, row.get("pending_lifecycle_candidate_id")] if key],
                "searched_trade_keys": trade_keys,
                "searched_order_position_keys": position_keys,
                "pending_lifecycle_trade_id": pending.get("trade_id") if pending else None,
                "pending_lifecycle_fill_label": pending.get("fill_no_fill_label") if pending else None,
                "pending_lifecycle_trade_state_ticket": pending.get("trade_state_ticket") if pending else None,
                "pending_lifecycle_source_line": pending.get("_source_line") if pending else None,
                "exact_r_bridge_status": exact_status,
                "exact_r": exact_r if is_owner else None,
                "exact_r_reference": exact_r,
                "exact_r_owner_row_id": owner_row_id,
                "exact_r_match_method": exact_match_method,
                "exact_r_source_type": exact_source.get("exact_r_source_type") if exact_source else None,
                "exact_r_source_path": exact_source.get("source_path") if exact_source else None,
                "exact_r_source_line": exact_source.get("source_line") if exact_source else None,
                "exact_r_mt5_order_id": exact_source.get("mt5_order_id") if exact_source else None,
                "exact_r_mt5_deal_id": exact_source.get("mt5_deal_id") if exact_source else None,
                "exact_r_broker_profit": exact_source.get("broker_profit") if exact_source else None,
                "local_non_account_r_reference": local_r.get("local_r") if local_r else None,
                "local_non_account_r_source_type": local_r.get("local_r_source_type") if local_r else None,
                "local_non_account_r_source_path": local_r.get("source_path") if local_r else None,
                "local_non_account_r_source_line": local_r.get("source_line") if local_r else None,
                "missing_identifier": missing_identifier,
                "exact_join_decision": exact_join_decision,
                "implementation_decision": exact_join_decision,
                "result_scope": RESULT_SCOPE,
            }
        )

    status_counts = Counter(row["exact_r_bridge_status"] for row in output_rows)
    decision_counts = Counter(row["exact_join_decision"] for row in output_rows)
    missing_counts = Counter(row["missing_identifier"] for row in output_rows if row["missing_identifier"])
    exact_owner_rows = [row for row in output_rows if row["exact_r_bridge_status"] == "EXACT_R_COUNTED_ON_OWNER_ROW"]
    exact_reference_rows = [row for row in output_rows if row["exact_r_reference"] is not None]
    local_non_account_rows = [row for row in output_rows if row["local_non_account_r_reference"] is not None]
    summary = {
        "schema_version": "main_orch24_exact_r_bridge_search_summary_v1",
        "generated_utc": generated_utc,
        "input_action_ledger": str(ACTION_LEDGER),
        "input_action_rows": len(action_rows),
        "before_exact_r_rows": before_exact_rows,
        "after_exact_r_owner_rows": len(exact_owner_rows),
        "exact_r_owner_row_delta": len(exact_owner_rows) - before_exact_rows,
        "after_exact_r_reference_rows": len(exact_reference_rows),
        "after_unique_exact_r_candidates": len(candidate_exact),
        "after_exact_r_owner_sum": round(sum(row["exact_r"] for row in exact_owner_rows if row["exact_r"] is not None), 10),
        "after_exact_r_reference_sum": round(sum(row["exact_r_reference"] for row in exact_reference_rows), 10),
        "local_non_account_r_reference_rows": len(local_non_account_rows),
        "local_non_account_r_reference_sum": round(
            sum(row["local_non_account_r_reference"] for row in local_non_account_rows), 10
        ),
        "exact_r_status_counts": dict(sorted(status_counts.items())),
        "exact_join_decision_counts": dict(sorted(decision_counts.items())),
        "missing_identifier_counts": dict(sorted(missing_counts.items())),
        "source_row_counts": sources["source_row_counts"],
        "source_paths_searched": SOURCE_PATHS_SEARCHED,
        "result_scope": RESULT_SCOPE,
    }
    manifest = {
        "schema_version": "main_orch24_exact_r_bridge_search_manifest_v1",
        "generated_utc": generated_utc,
        "outputs": {
            str(OUTPUT_LEDGER): {"rows": len(output_rows), "sha256": None},
            str(SUMMARY_PATH): {"rows": 1, "sha256": None},
        },
        "inputs": {
            str(ACTION_LEDGER): {"rows": len(action_rows), "sha256": sha256_file(ACTION_LEDGER)},
            **{
                path: {
                    "rows": sources["source_row_counts"].get(path, 0),
                    "sha256": sha256_file(Path(path)),
                }
                for path in SOURCE_PATHS_SEARCHED
            },
        },
        "result_scope": RESULT_SCOPE,
    }
    return output_rows, summary, manifest


def main() -> None:
    output_rows, summary, manifest = build()
    write_jsonl(OUTPUT_LEDGER, output_rows)
    write_json(SUMMARY_PATH, summary)
    manifest["outputs"][str(OUTPUT_LEDGER)]["sha256"] = sha256_file(OUTPUT_LEDGER)
    manifest["outputs"][str(SUMMARY_PATH)]["sha256"] = sha256_file(SUMMARY_PATH)
    write_json(MANIFEST_PATH, manifest)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
