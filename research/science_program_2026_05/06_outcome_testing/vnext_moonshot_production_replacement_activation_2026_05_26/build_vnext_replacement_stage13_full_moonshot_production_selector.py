from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"
STAGE_ID = "stage_13_full_moonshot_production_selector"
REPO_ROOT = Path(__file__).resolve().parents[4]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.broader_origin_generators import SESSION_WINDOWS  # noqa: E402

ROUTE_DIR = Path(__file__).resolve().parent

OLD_THREE_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_BRANCH_ORIGIN_AUDIT_SUMMARY_{DATE}.json"
BROADER_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_CANDIDATE_CONTRACT_LEDGER_{DATE}.jsonl"
BROADER_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_REPLAY_SUMMARY_{DATE}.json"
MARKET_ACTIVATION_MAP = ROUTE_DIR / f"VNEXT_REPLACEMENT_MARKET_SOURCE_ACTIVATION_MAP_{DATE}.json"
OUTSIDE_SESSION_GROUP_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_OPPORTUNITY_GROUP_LEDGER_{DATE}.jsonl"
OUTSIDE_SESSION_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_OPPORTUNITY_SUMMARY_{DATE}.json"
OUTSIDE_SESSION_SHARD_MANIFEST = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_OUTSIDE_SESSION_OPPORTUNITY_SHARD_MANIFEST_{DATE}.jsonl"

OUTPUT_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_FULL_MOONSHOT_PRODUCTION_SELECTOR_SUMMARY_{DATE}.json"
OUTPUT_ALLOWLIST = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_ACTIVATION_ALLOWLIST_{DATE}.json"

MIN_GROUP_ROWS = 20
SELECTED_POLICY = "be_after_trigger"
EXPLICIT_24H_SESSION_SYMBOLS = {"BTCUSD", "ETHUSD"}
SYMBOL_ALIASES = {
    "US30": "US30_cash",
    "US30.CASH": "US30_cash",
    "UKOIL": "UKOIL_cash",
    "USOIL": "USOIL_cash",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix().replace("\\", "/")


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def metric_blank() -> dict[str, float | int]:
    return {
        "performance_rows": 0,
        "total_r": 0.0,
        "wins": 0,
        "gross_win_r": 0.0,
        "gross_loss_r": 0.0,
    }


def add_metric(target: dict[str, Any], value: float) -> None:
    target["performance_rows"] += 1
    target["total_r"] += value
    if value > 0:
        target["wins"] += 1
        target["gross_win_r"] += value
    elif value < 0:
        target["gross_loss_r"] += abs(value)


def finalize_metric(metric: dict[str, Any]) -> dict[str, Any]:
    rows = int(metric.get("performance_rows") or 0)
    total = float(metric.get("total_r") or 0.0)
    gross_loss = float(metric.get("gross_loss_r") or 0.0)
    gross_win = float(metric.get("gross_win_r") or 0.0)
    return {
        "performance_rows": rows,
        "selected_count": rows,
        "total_r": total,
        "expectancy_r": total / rows if rows else None,
        "win_rate": float(metric.get("wins") or 0) / rows if rows else None,
        "wins": int(metric.get("wins") or 0),
        "gross_win_r": gross_win,
        "gross_loss_r": gross_loss,
        "profit_factor": gross_win / gross_loss if gross_loss else None,
    }


def combine_metrics(*metrics: dict[str, Any]) -> dict[str, Any]:
    combined = metric_blank()
    for metric in metrics:
        combined["performance_rows"] += int(metric.get("performance_rows") or 0)
        combined["total_r"] += float(metric.get("total_r") or 0.0)
        combined["wins"] += int(metric.get("wins") or 0)
        combined["gross_win_r"] += float(metric.get("gross_win_r") or 0.0)
        combined["gross_loss_r"] += float(metric.get("gross_loss_r") or 0.0)
    return finalize_metric(combined)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
            count += 1
    return count


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def group_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    source_fields = row.get("source_fields") or {}
    return (
        str(row.get("origin_family") or ""),
        canonical_symbol(row.get("symbol")),
        str(row.get("_production_route_session") or source_fields.get("session_at_candidate") or "missing_session"),
        str(row.get("side") or ""),
    )


def outside_group_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("origin_family") or ""),
        canonical_symbol(row.get("symbol")),
        str(row.get("repaired_route_session") or "moonshot_extended"),
        str(row.get("side") or ""),
        str(row.get("utc_hour_bucket") or ""),
    )


def parse_utc(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def minute_of_day(value: str) -> int:
    hour, minute = value.split(":", 1)
    return int(hour) * 60 + int(minute)


def minute_in_window(minute: int, start: str, end: str) -> bool:
    start_min = minute_of_day(start)
    end_min = minute_of_day(end)
    if start_min <= end_min:
        return start_min <= minute < end_min
    return minute >= start_min or minute < end_min


def production_session_from_timestamp(symbol: str, timestamp: Any) -> str | None:
    parsed = parse_utc(timestamp)
    if parsed is None:
        return None
    windows = SESSION_WINDOWS.get(symbol) or SESSION_WINDOWS.get(symbol.upper())
    if not windows:
        return None
    current_minute = parsed.hour * 60 + parsed.minute
    for name, start, end in windows:
        if minute_in_window(current_minute, start, end):
            return str(name)
    return "off_configured_session"


def production_route_session_for_row(row: dict[str, Any]) -> tuple[str, bool, str]:
    source_fields = row.get("source_fields") or {}
    symbol = canonical_symbol(row.get("symbol"))
    raw_session = str(source_fields.get("session_at_candidate") or "missing_session")
    timestamp = row.get("decision_time_utc") or row.get("candle_time_utc")
    derived_session = production_session_from_timestamp(symbol, timestamp)

    if derived_session is None:
        if raw_session == "missing_session":
            return raw_session, False, "missing_session_timestamp_not_repairable"
        if raw_session == "off_configured_session" and symbol not in EXPLICIT_24H_SESSION_SYMBOLS:
            return raw_session, False, "stale_inherited_off_configured_session_timestamp_not_repairable"
        if raw_session == "off_configured_session":
            return raw_session, True, "explicit_crypto_24h_contract"
        return raw_session, True, "configured_session_contract_without_timestamp_repair"

    if derived_session == "off_configured_session" and symbol not in EXPLICIT_24H_SESSION_SYMBOLS:
        return derived_session, False, "outside_configured_session_not_production_executable"
    if derived_session == "off_configured_session":
        return derived_session, True, "explicit_crypto_24h_contract"
    if raw_session in {"missing_session", "off_configured_session"}:
        return derived_session, True, f"repaired_{raw_session}_to_configured_session"
    if raw_session != derived_session:
        return derived_session, True, "repaired_raw_session_to_timestamp_configured_session"
    return derived_session, True, "configured_session_contract"


def canonical_symbol(value: Any) -> str:
    raw = str(value or "")
    return SYMBOL_ALIASES.get(raw.upper().replace(".", "_"), raw)


def append_selected_group(
    *,
    allowlist_entries: list[dict[str, Any]],
    selected_metric: dict[str, Any],
    selected_family_counts: Counter[str],
    selected_symbol_counts: Counter[str],
    selected_session_counts: Counter[str],
    selected_side_counts: Counter[str],
    family: str,
    symbol: str,
    session: str,
    side: str,
    proof: str,
    metrics: dict[str, Any],
    session_proof_class_counts: dict[str, Any],
    utc_hour_bucket: str | None = None,
) -> None:
    rows = int(metrics.get("performance_rows") or 0)
    selected_family_counts[family] += rows
    selected_symbol_counts[symbol] += rows
    selected_session_counts[session] += rows
    selected_side_counts[side] += rows
    for field in ("performance_rows", "total_r", "wins", "gross_win_r", "gross_loss_r"):
        selected_metric[field] += float(metrics.get(field) or 0.0)
    entry = {
        "origin_family": family,
        "candidate_origin_family": f"origin_{family}",
        "symbol": symbol,
        "route_session": session,
        "side": side,
        "selected_policy": SELECTED_POLICY,
        "proof_class": proof,
        "session_proof_class_counts": dict(sorted(session_proof_class_counts.items())),
        "metrics": metrics,
        "min_group_rows": MIN_GROUP_ROWS,
        "activation_action": "TRADE_VNEXT_BROADER_ORIGIN_CANDIDATE",
    }
    if utc_hour_bucket:
        entry["utc_hour_bucket"] = utc_hour_bucket
        entry["session_expansion_contract"] = "named_moonshot_hour_bucket_allowlist"
    allowlist_entries.append(entry)


def main() -> None:
    old_summary = json.loads(OLD_THREE_SUMMARY.read_text(encoding="utf-8"))
    broader_summary = json.loads(BROADER_SUMMARY.read_text(encoding="utf-8"))
    market_map = json.loads(MARKET_ACTIVATION_MAP.read_text(encoding="utf-8"))
    outside_summary = json.loads(OUTSIDE_SESSION_SUMMARY.read_text(encoding="utf-8")) if OUTSIDE_SESSION_SUMMARY.exists() else {}
    eligible_symbols = {
        canonical_symbol(symbol)
        for symbol in market_map.get("broker_native_activation_eligible_symbols", [])
    }
    exact_excluded_symbols = {
        canonical_symbol(symbol)
        for symbol in market_map.get("broker_native_exact_excluded_symbols", [])
    }
    old_selector = old_summary["repaired_selector"]
    old_metrics = old_selector["comparator_metrics_on_selected_rows"][SELECTED_POLICY]

    groups: dict[tuple[str, str, str, str], dict[str, Any]] = defaultdict(metric_blank)
    blocker_counts: Counter[str] = Counter()
    non_ready_counts: Counter[str] = Counter()
    family_total_counts: Counter[str] = Counter()
    source_path_counts: Counter[str] = Counter()
    session_reconciliation_counts: Counter[str] = Counter()
    session_reconciliation_symbol_counts: Counter[str] = Counter()
    group_session_status_counts: dict[tuple[str, str, str, str], Counter[str]] = defaultdict(Counter)
    exclusion_action_counts: Counter[str] = Counter()
    exclusion_proof_counts: Counter[str] = Counter()
    same_bar_blocked_rows = 0
    broker_excluded_counts: Counter[str] = Counter()
    outside_session_rows_seen = 0
    for row in iter_jsonl(BROADER_LEDGER):
        family = str(row.get("origin_family") or "")
        family_total_counts[family] += 1
        if row.get("source_path"):
            source_path_counts[str(row.get("source_path"))] += 1
        if row.get("row_type") != "candidate_contract":
            blocker_counts[str(row.get("activation_ready_blocker_class"))] += 1
            continue
        symbol = canonical_symbol(row.get("symbol"))
        if symbol in exact_excluded_symbols:
            broker_excluded_counts[f"{symbol}:broker_contract_invalid_or_unavailable"] += 1
            continue
        if eligible_symbols and symbol not in eligible_symbols:
            broker_excluded_counts[f"{symbol}:broker_native_contract_not_verified"] += 1
            continue
        if not row.get("activation_ready"):
            blocker = str(row.get("activation_ready_blocker_class"))
            blocker_counts[blocker] += 1
            non_ready_counts[family] += 1
            if blocker == "selected_policy_ordered_ltf_or_tick_path_required":
                same_bar_blocked_rows += 1
            continue
        final_r = row.get("origin_native_dynamic_final_r")
        if final_r is None:
            blocker_counts["activation_ready_missing_dynamic_final_r"] += 1
            continue
        route_session, session_allowed, session_status = production_route_session_for_row(row)
        session_reconciliation_counts[session_status] += 1
        session_reconciliation_symbol_counts[f"{symbol}:{session_status}"] += 1
        if not session_allowed:
            outside_session_rows_seen += 1
            continue
        row["_production_route_session"] = route_session
        group_session_status_counts[group_key(row)][session_status] += 1
        add_metric(groups[group_key(row)], float(final_r))

    ledger_rows: list[dict[str, Any]] = []
    allowlist_entries: list[dict[str, Any]] = []
    selected_metric = metric_blank()
    selected_group_count = 0
    selected_family_counts: Counter[str] = Counter()
    selected_symbol_counts: Counter[str] = Counter()
    selected_session_counts: Counter[str] = Counter()
    selected_side_counts: Counter[str] = Counter()

    ledger_rows.append(
        {
            "schema_version": "vnext_replacement_stage13_full_moonshot_production_selector_v1",
            "route_id": ROUTE_ID,
            "stage_id": STAGE_ID,
            "row_type": "old_three_framework_component",
            "selector_component": "ob_fvg_breaker_follow_or_repaired_branch",
            "final_action": "activate_existing_full_moonshot_old_three_selector",
            "selected_policy": SELECTED_POLICY,
            "activated_frameworks": old_selector["activated_frameworks"],
            "metrics": old_metrics,
            "coverage": old_selector["coverage"],
            "evidence_path": rel(OLD_THREE_SUMMARY),
        }
    )

    for key, raw_metric in sorted(groups.items()):
        family, symbol, session, side = key
        metrics = finalize_metric(raw_metric)
        rows = int(metrics["performance_rows"])
        exp = metrics["expectancy_r"]
        pf = metrics["profit_factor"]
        if rows >= MIN_GROUP_ROWS and exp is not None and exp > 0 and (pf is None or pf > 1):
            action = "activate_broader_origin_group"
            proof = "positive_origin_native_dynamic_replay_row_level_proof"
            selected_group_count += 1
            append_selected_group(
                allowlist_entries=allowlist_entries,
                selected_metric=selected_metric,
                selected_family_counts=selected_family_counts,
                selected_symbol_counts=selected_symbol_counts,
                selected_session_counts=selected_session_counts,
                selected_side_counts=selected_side_counts,
                family=family,
                symbol=symbol,
                session=session,
                side=side,
                proof=proof,
                metrics=metrics,
                session_proof_class_counts=dict(sorted(group_session_status_counts[key].items())),
            )
        elif rows < MIN_GROUP_ROWS and exp is not None and exp > 0 and (pf is None or pf > 1):
            action = "exclude_insufficient_row_level_positive_ev_proof"
            proof = "insufficient_executable_source_after_repo_local_replay"
        else:
            action = "exclude_negative_expectancy_or_pf_collapse"
            proof = "negative_expectancy_or_profit_factor_collapse_after_origin_native_replay"
        if action.startswith("exclude"):
            exclusion_action_counts[action] += rows
            exclusion_proof_counts[proof] += rows
        ledger_rows.append(
            {
                "schema_version": "vnext_replacement_stage13_full_moonshot_production_selector_v1",
                "route_id": ROUTE_ID,
                "stage_id": STAGE_ID,
                "row_type": "broader_origin_group_decision",
                "origin_family": family,
                "candidate_origin_family": f"origin_{family}",
                "symbol": symbol,
                "route_session": session,
                "side": side,
                "selected_policy": SELECTED_POLICY,
                "min_group_rows": MIN_GROUP_ROWS,
                "metrics": metrics,
                "final_action": action,
                "proof_class": proof,
                "session_proof_class_counts": dict(sorted(group_session_status_counts[key].items())),
                "source_evidence_path": rel(BROADER_LEDGER),
                "source_summary_path": rel(BROADER_SUMMARY),
            }
        )

    outside_session_expansion_metric = metric_blank()
    outside_session_expanded_group_count = 0
    outside_session_action_counts: Counter[str] = Counter()
    outside_session_proof_counts: Counter[str] = Counter()
    outside_session_group_rows = 0
    if OUTSIDE_SESSION_GROUP_LEDGER.exists():
        for outside_row in iter_jsonl(OUTSIDE_SESSION_GROUP_LEDGER):
            if outside_row.get("row_type") != "outside_session_group_decision":
                continue
            outside_session_group_rows += 1
            metrics = outside_row.get("metrics") or {}
            rows = int(metrics.get("performance_rows") or 0)
            action = str(outside_row.get("final_action") or "")
            proof = str(outside_row.get("proof_class") or "")
            family = str(outside_row.get("origin_family") or "")
            symbol = canonical_symbol(outside_row.get("symbol"))
            utc_hour_bucket = str(outside_row.get("utc_hour_bucket") or "")
            session = f"moonshot_{utc_hour_bucket}" if utc_hour_bucket else str(
                outside_row.get("repaired_route_session") or "moonshot_extended"
            )
            side = str(outside_row.get("side") or "")
            outside_session_action_counts[action] += rows
            outside_session_proof_counts[proof] += rows
            if action == "expand_production_execution_moonshot_extended_session":
                selected_group_count += 1
                outside_session_expanded_group_count += 1
                for field in ("performance_rows", "total_r", "wins", "gross_win_r", "gross_loss_r"):
                    outside_session_expansion_metric[field] += float(metrics.get(field) or 0.0)
                append_selected_group(
                    allowlist_entries=allowlist_entries,
                    selected_metric=selected_metric,
                    selected_family_counts=selected_family_counts,
                    selected_symbol_counts=selected_symbol_counts,
                    selected_session_counts=selected_session_counts,
                    selected_side_counts=selected_side_counts,
                    family=family,
                    symbol=symbol,
                    session=session,
                    side=side,
                    proof="positive_outside_session_origin_native_dynamic_replay_row_level_proof",
                    metrics=metrics,
                    session_proof_class_counts={
                        "outside_configured_session_repaired_to_named_moonshot_hour_bucket": rows
                    },
                    utc_hour_bucket=utc_hour_bucket,
                )
                ledger_action = "activate_broader_origin_group"
                ledger_proof = "positive_outside_session_origin_native_dynamic_replay_row_level_proof"
            else:
                exclusion_action_counts[action] += rows
                exclusion_proof_counts[proof] += rows
                ledger_action = action
                ledger_proof = proof
            ledger_rows.append(
                {
                    "schema_version": "vnext_replacement_stage13_full_moonshot_production_selector_v1",
                    "route_id": ROUTE_ID,
                    "stage_id": STAGE_ID,
                    "row_type": "broader_origin_group_decision",
                    "origin_family": family,
                    "candidate_origin_family": f"origin_{family}",
                    "symbol": symbol,
                    "route_session": session,
                    "utc_hour_bucket": utc_hour_bucket,
                    "side": side,
                    "selected_policy": SELECTED_POLICY,
                    "min_group_rows": int(outside_row.get("min_group_rows") or MIN_GROUP_ROWS),
                    "metrics": metrics,
                    "final_action": ledger_action,
                    "source_final_action": action,
                    "proof_class": ledger_proof,
                    "session_proof_class_counts": {
                        "outside_configured_session_repaired_to_named_moonshot_hour_bucket": rows
                    },
                    "source_evidence_path": rel(OUTSIDE_SESSION_GROUP_LEDGER),
                    "source_summary_path": rel(OUTSIDE_SESSION_SUMMARY),
                    "source_shard_manifest": rel(OUTSIDE_SESSION_SHARD_MANIFEST),
                }
            )

    broader_selected_metrics = finalize_metric(selected_metric)
    outside_session_expansion_metrics = finalize_metric(outside_session_expansion_metric)
    combined_metrics = combine_metrics(old_metrics, broader_selected_metrics)
    no_trade_comparator = {
        "selected_broader_rows": broader_selected_metrics["performance_rows"],
        "no_overlay_total_r": 0.0,
        "captured_total_r_vs_no_overlay": broader_selected_metrics["total_r"],
        "captured_expectancy_vs_no_overlay": broader_selected_metrics["expectancy_r"],
    }
    summary = {
        "schema_version": "vnext_replacement_stage13_full_moonshot_production_selector_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "generated_at_utc": utc_now(),
        "status": "selector_extended_beyond_old_three",
        "selected_policy": SELECTED_POLICY,
        "input_artifacts": {
            "old_three_full_moonshot_summary": rel(OLD_THREE_SUMMARY),
            "broader_origin_replay_summary": rel(BROADER_SUMMARY),
            "broader_origin_replay_ledger": rel(BROADER_LEDGER),
            "market_activation_map": rel(MARKET_ACTIVATION_MAP),
            "outside_session_opportunity_summary": rel(OUTSIDE_SESSION_SUMMARY),
            "outside_session_opportunity_group_ledger": rel(OUTSIDE_SESSION_GROUP_LEDGER),
            "outside_session_opportunity_shard_manifest": rel(OUTSIDE_SESSION_SHARD_MANIFEST),
        },
        "output_paths": {
            "selector_ledger": rel(OUTPUT_LEDGER),
            "summary": rel(OUTPUT_SUMMARY),
            "broader_origin_allowlist": rel(OUTPUT_ALLOWLIST),
        },
        "old_three_component_metrics": old_metrics,
        "broader_origin_selected_metrics": broader_selected_metrics,
        "broader_origin_outside_session_expansion_metrics": outside_session_expansion_metrics,
        "combined_production_selector_metrics": combined_metrics,
        "old_three_selected_rows": old_metrics["performance_rows"],
        "broader_origin_selected_rows": broader_selected_metrics["performance_rows"],
        "broader_origin_outside_session_expanded_rows": outside_session_expansion_metrics["performance_rows"],
        "broader_origin_outside_session_expanded_group_count": outside_session_expanded_group_count,
        "broader_origin_outside_session_group_rows": outside_session_group_rows,
        "broader_origin_outside_session_rows_seen": outside_session_rows_seen,
        "broader_origin_outside_session_opportunity_summary": outside_summary,
        "broader_origin_outside_session_action_counts": dict(sorted(outside_session_action_counts.items())),
        "broader_origin_outside_session_proof_counts": dict(sorted(outside_session_proof_counts.items())),
        "combined_selected_rows": combined_metrics["performance_rows"],
        "broader_origin_selected_group_count": selected_group_count,
        "broader_origin_selected_family_counts": dict(sorted(selected_family_counts.items())),
        "broader_origin_selected_symbol_counts": dict(sorted(selected_symbol_counts.items())),
        "broader_origin_selected_session_counts": dict(sorted(selected_session_counts.items())),
        "broader_origin_selected_side_counts": dict(sorted(selected_side_counts.items())),
        "broader_origin_exclusion_action_counts": dict(sorted(exclusion_action_counts.items())),
        "broader_origin_exclusion_proof_counts": dict(sorted(exclusion_proof_counts.items())),
        "broader_origin_non_ready_blocker_counts": dict(sorted(blocker_counts.items())),
        "broader_origin_session_reconciliation_counts": dict(sorted(session_reconciliation_counts.items())),
        "broader_origin_session_reconciliation_symbol_counts": dict(sorted(session_reconciliation_symbol_counts.items())),
        "broader_origin_explicit_24h_session_symbols": sorted(EXPLICIT_24H_SESSION_SYMBOLS),
        "broader_origin_broker_excluded_counts": dict(sorted(broker_excluded_counts.items())),
        "broader_origin_same_bar_blocked_rows": same_bar_blocked_rows,
        "broader_origin_total_family_rows": dict(sorted(family_total_counts.items())),
        "source_path_counts": dict(source_path_counts.most_common()),
        "comparison": {
            "old_three_comparators": old_selector["comparator_metrics_on_selected_rows"],
            "broader_origin_no_overlay_comparator": no_trade_comparator,
            "broader_origin_fixed_1_5r_comparator_available_in_row_level_replay": True,
            "broader_origin_old_gtos_j46_j49_comparator_status": (
                "not_semantically_defined_for_non_current_origin_rows_because_old_gtos_generated_no_candidate_rows; "
                "no_overlay comparator is the exact opportunity-capture baseline"
            ),
        },
        "allowlist_entry_count": len(allowlist_entries),
        "full_moonshot_completion_rule": (
            "old-three OB/FVG/breaker positive selector plus every broader-origin "
            "symbol/session/side group and every outside-session symbol/family/side/hour-bucket group "
            "with origin-native BE-after-trigger positive EV and PF>1; negative/PF-collapse, same-bar "
            "ambiguous, no executable rows, strict missing-entry, and underpowered positive groups are "
            "excluded with row-level evidence"
        ),
    }
    allowlist = {
        "schema_version": "vnext_replacement_stage13_broader_origin_activation_allowlist_v1",
        "route_id": ROUTE_ID,
        "stage_id": STAGE_ID,
        "generated_at_utc": summary["generated_at_utc"],
        "selected_policy": SELECTED_POLICY,
        "min_group_rows": MIN_GROUP_ROWS,
        "entries": allowlist_entries,
    }

    write_jsonl(OUTPUT_LEDGER, ledger_rows)
    write_json(OUTPUT_ALLOWLIST, allowlist)
    write_json(OUTPUT_SUMMARY, summary)
    print(json.dumps({
        "combined_selected_rows": summary["combined_selected_rows"],
        "broader_origin_selected_rows": summary["broader_origin_selected_rows"],
        "allowlist_entry_count": summary["allowlist_entry_count"],
        "combined_expectancy_r": summary["combined_production_selector_metrics"]["expectancy_r"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
