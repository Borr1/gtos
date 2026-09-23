from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
ROUTE_DIR = REPO_ROOT / "research/operations/vnext_live_activation_active_repair_companion_2026_05_28"
SUMMARY_PATH = ROUTE_DIR / "LIVE_STARVATION_INTELLIGENCE_SUMMARY.json"
LEDGER_PATH = ROUTE_DIR / "LIVE_STARVATION_INTELLIGENCE_LEDGER.jsonl"
REFUSAL_BREAKDOWN_PATH = ROUTE_DIR / "LIVE_STARVATION_INTELLIGENCE_REFUSAL_BREAKDOWN.jsonl"
VERIFY_PATH = ROUTE_DIR / "LIVE_STARVATION_INTELLIGENCE_VERIFICATION.json"
CONFIG_PATH = REPO_ROOT / "config/agent_config.yaml"
redacted_account_PROFILE_PATH = REPO_ROOT / "config/profiles/redacted_account.yaml"
RUNTIME_LOG = REPO_ROOT / "shadow_logs/gtos_vnext_runtime_decisions.jsonl"
REPLACEMENT_LOG = REPO_ROOT / "shadow_logs/gtos_vnext_replacement_monitoring.jsonl"
TRADE_RECORD_ROOT = REPO_ROOT / "knowledge_base/trade_records"
ORDER_LIFECYCLE_LEDGER = ROUTE_DIR / "LIVE_ORDER_LIFECYCLE_LEDGER.jsonl"
DYNAMIC_LIFECYCLE_LEDGER = ROUTE_DIR / "LIVE_DYNAMIC_EXECUTION_LIFECYCLE_LEDGER.jsonl"
BROKER_DEAL_LEDGER = ROUTE_DIR / "LIVE_BROKER_DEAL_RECONCILIATION_LEDGER.jsonl"

STALE_LABEL_RE = re.compile(
    r"live_current_j46_j49|\bJ46\b|\bJ49\b|fixed[- ]?1\.5R|legacy_fixed_1_5r|legacy_fixed_1\.5r",
    re.IGNORECASE,
)


def _read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
    except (OSError, json.JSONDecodeError):
        return rows
    return rows


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _mtime_utc(path: Path) -> datetime:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _get(data: Any, *path: str) -> Any:
    value = data
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def _normalize_origin(value: Any) -> str:
    text = str(value or "unknown").strip()
    if text.startswith("origin_"):
        text = text[len("origin_") :]
    return text or "unknown"


def _match_key(value: Any) -> str:
    return str(value or "").strip().lower()


def _runtime_config(config_path: Path = CONFIG_PATH) -> dict[str, Any]:
    try:
        config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except OSError:
        return {}
    runtime = config.get("gtos_vnext_runtime") if isinstance(config, dict) else {}
    return runtime if isinstance(runtime, dict) else {}


def _counter_to_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))


def _contract(config_path: Path = CONFIG_PATH) -> tuple[list[str], list[str]]:
    runtime = _runtime_config(config_path)
    symbols = runtime.get("moonshot_dynamic_execution_router_broker_native_eligible_symbols") or []
    origins = runtime.get("moonshot_dynamic_execution_router_activated_origin_families") or []
    return [str(item) for item in symbols], [_normalize_origin(item) for item in origins]


def _local_path(path_text: Any) -> Path | None:
    if not path_text:
        return None
    path = Path(str(path_text))
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def _read_allowlist_entries(path_text: Any) -> list[dict[str, Any]]:
    path = _local_path(path_text)
    if path is None:
        return []
    payload = _read_json(path, {})
    entries = payload.get("entries") if isinstance(payload, dict) else None
    return [entry for entry in entries or [] if isinstance(entry, dict)]


def _read_risk_rows(path_text: Any) -> list[dict[str, Any]]:
    path = _local_path(path_text)
    if path is None or not path.exists():
        return []
    return _read_jsonl(path)


def _broker_alias_map(profile_path: Path = redacted_account_PROFILE_PATH) -> dict[str, str]:
    try:
        profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    except OSError:
        return {}
    instruments = profile.get("instruments") if isinstance(profile, dict) else {}
    aliases: dict[str, str] = {}
    if isinstance(instruments, dict):
        for symbol, cfg in instruments.items():
            market = cfg.get("market") if isinstance(cfg, dict) else {}
            aliases[str(symbol)] = str((market or {}).get("mt5_symbol") or symbol)
    return aliases


def _metric_value(row: dict[str, Any], key: str) -> float | None:
    for source in (row, row.get("metrics") if isinstance(row.get("metrics"), dict) else None):
        if not isinstance(source, dict):
            continue
        try:
            value = source.get(key)
            if value is not None:
                return float(value)
        except (TypeError, ValueError):
            return None
    return None


def _selector_metrics_positive(row: dict[str, Any], *, min_rows: int) -> bool:
    selected = _metric_value(row, "selected_count")
    if selected is None:
        selected = _metric_value(row, "performance_rows")
    expectancy = _metric_value(row, "expectancy_r")
    profit_factor = _metric_value(row, "profit_factor")
    return bool(
        selected is not None
        and selected >= min_rows
        and expectancy is not None
        and expectancy > 0
        and profit_factor is not None
        and profit_factor > 1
    )


def _promotion_evidence_verified(runtime_cfg: dict[str, Any]) -> dict[str, Any]:
    path = _local_path(runtime_cfg.get("moonshot_dynamic_execution_router_policy_promotion_evidence_path"))
    payload = _read_json(path, {}) if path else {}
    counts = payload.get("policy_counts") if isinstance(payload.get("policy_counts"), dict) else {}
    return {
        "path": str(path.relative_to(REPO_ROOT)) if path and path.exists() else str(path) if path else None,
        "status": payload.get("status") if isinstance(payload, dict) else None,
        "issue_count": payload.get("issue_count") if isinstance(payload, dict) else None,
        "checked_rows": payload.get("checked_rows") if isinstance(payload, dict) else None,
        "policy_counts": counts,
        "verified": (
            isinstance(payload, dict)
            and payload.get("status") == "verified"
            and payload.get("issue_count") == 0
            and int(payload.get("checked_rows") or 0) > 0
            and int(counts.get("momentum_exhaustion") or 0) > 0
            and int(counts.get("partial_be_runner") or 0) > 0
        ),
    }


def _new_cell(symbol: str, origin_family: str) -> dict[str, Any]:
    return {
        "schema_version": "vnext_live_starvation_cell_v1",
        "symbol": symbol,
        "origin_family": origin_family,
        "raw_candidate_rows": 0,
        "dynamic_rows": 0,
        "dynamic_skip_rows": 0,
        "repaired_candidate_rows": 0,
        "final_broker_ready_candidates": 0,
        "order_rows": 0,
        "fill_rows": 0,
        "close_rows": 0,
        "trade_record_rows": 0,
        "candidate_packet_rows": 0,
        "native_live_writer_packet_rows": 0,
        "post_reload_runtime_rows": 0,
        "post_reload_stale_label_hits": 0,
        "session_counts": Counter(),
        "policy_counts": Counter(),
        "execution_policy_id_counts": Counter(),
        "refusal_reason_counts": Counter(),
        "final_outcome_counts": Counter(),
        "source_mode_counts": Counter(),
        "selected_cell_state_counts": Counter(),
        "prop_action_counts": Counter(),
        "geometry_state_counts": Counter(),
        "old_system_leakage_counts": Counter(),
        "latest_candle_utc": None,
        "latest_event_utc": None,
        "latest_candidate_id": None,
        "latest_refusal_reasons": [],
        "classification": "no_live_shape_observed",
        "classification_reason": "no_raw_or_dynamic_candidate_rows_in_window",
    }


def _touch_latest(cell: dict[str, Any], *, event_dt: datetime | None, candle: Any, candidate_id: Any = None) -> None:
    if event_dt is not None:
        current = _parse_dt(cell.get("latest_event_utc"))
        if current is None or event_dt > current:
            cell["latest_event_utc"] = event_dt.isoformat()
    candle_dt = _parse_dt(candle)
    if candle_dt is not None:
        current_candle = _parse_dt(cell.get("latest_candle_utc"))
        if current_candle is None or candle_dt > current_candle:
            cell["latest_candle_utc"] = candle_dt.isoformat()
    if candidate_id:
        cell["latest_candidate_id"] = str(candidate_id)


def _cell(cells: dict[tuple[str, str], dict[str, Any]], symbol: Any, origin: Any) -> dict[str, Any]:
    key = (str(symbol or "unknown"), _normalize_origin(origin))
    if key not in cells:
        cells[key] = _new_cell(*key)
    return cells[key]


def _runtime_source(row: dict[str, Any]) -> dict[str, Any]:
    decision = row.get("decision") if isinstance(row.get("decision"), dict) else {}
    source_event = decision.get("source_event") if isinstance(decision.get("source_event"), dict) else {}
    router_record = decision.get("router_record") if isinstance(decision.get("router_record"), dict) else {}
    route_dimensions = router_record.get("route_dimensions") if isinstance(router_record.get("route_dimensions"), dict) else {}
    event = decision.get("event") if isinstance(decision.get("event"), dict) else {}
    return source_event or route_dimensions or event


def _session_candidates(source: dict[str, Any]) -> set[str]:
    route_session = _match_key(source.get("route_session"))
    session_bucket = _match_key(source.get("session_bucket")).removesuffix("_broad")
    candidates = {item for item in (route_session, session_bucket) if item}
    if route_session == "off_kz_broad" or session_bucket == "off_kz":
        candidates.add("off_configured_session")
    return candidates


def _current_policy_set(runtime_cfg: dict[str, Any], source: dict[str, Any]) -> set[str]:
    primary = _match_key(
        runtime_cfg.get("moonshot_dynamic_execution_router_policy") or "momentum_exhaustion"
    )
    policies = {primary} if primary else set()
    family = _normalize_origin(
        source.get("candidate_origin_family")
        or source.get("origin_family")
        or source.get("route_family")
        or source.get("framework")
    )
    exceptions = {
        _match_key(item)
        for item in runtime_cfg.get(
            "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner",
            [],
        )
    }
    exception_policy = _match_key(
        runtime_cfg.get("moonshot_dynamic_execution_router_momentum_exception_policy")
    )
    if family in exceptions and exception_policy:
        policies.add(exception_policy)
    return policies


def _policy_allowed_by_current_contract(
    entry_policy: Any,
    *,
    runtime_cfg: dict[str, Any],
    source: dict[str, Any],
    promotion_evidence: dict[str, Any],
) -> tuple[bool, str]:
    entry = _match_key(entry_policy)
    current = _current_policy_set(runtime_cfg, source)
    if entry in current:
        return True, "exact_selected_policy_selector_match"
    if (
        bool(runtime_cfg.get("moonshot_dynamic_execution_router_allow_stage13_be_selector_policy_bridge"))
        and promotion_evidence.get("verified") is True
        and entry == "be_after_trigger"
        and bool(current & {"momentum_exhaustion", "partial_be_runner"})
    ):
        return True, "stage13_be_policy_bridge_to_current_promoted_policy"
    return False, "policy_identity_mismatch_after_momentum_partial_promotion"


def _allowlist_failed_dimensions(
    entry: dict[str, Any],
    source: dict[str, Any],
    *,
    runtime_cfg: dict[str, Any],
    promotion_evidence: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str], int]:
    failed: list[dict[str, Any]] = []
    matched: list[str] = []
    score = 0

    def check(field: str, live: Any, candidate: Any, *, normalize: bool = True) -> None:
        nonlocal score
        live_value = _normalize_origin(live) if normalize else str(live or "")
        candidate_value = _normalize_origin(candidate) if normalize else str(candidate or "")
        if live_value == candidate_value:
            matched.append(field)
            score += 1
        else:
            failed.append({"field": field, "live": live_value, "allowlist": candidate_value})

    check("symbol", source.get("symbol"), entry.get("symbol"), normalize=False)
    check(
        "candidate_origin_family",
        source.get("candidate_origin_family") or source.get("origin_family") or source.get("framework"),
        entry.get("origin_family") or entry.get("candidate_origin_family"),
    )
    check("side", str(source.get("side") or "").upper(), str(entry.get("side") or "").upper(), normalize=False)

    entry_session = _match_key(entry.get("route_session") or entry.get("session_bucket")).removesuffix("_broad")
    if entry_session in _session_candidates(source):
        matched.append("route_session")
        score += 1
    else:
        failed.append(
            {
                "field": "route_session",
                "live": sorted(_session_candidates(source)),
                "allowlist": entry_session,
            }
        )

    entry_hour = _match_key(entry.get("utc_hour_bucket"))
    if entry_hour:
        live_hour = _match_key(source.get("utc_hour_bucket"))
        if entry_hour == live_hour:
            matched.append("utc_hour_bucket")
            score += 1
        else:
            failed.append({"field": "utc_hour_bucket", "live": live_hour, "allowlist": entry_hour})
    else:
        matched.append("utc_hour_bucket_not_dimensioned")
        score += 1

    policy_allowed, policy_reason = _policy_allowed_by_current_contract(
        entry.get("selected_policy"),
        runtime_cfg=runtime_cfg,
        source=source,
        promotion_evidence=promotion_evidence,
    )
    if policy_allowed:
        matched.append(policy_reason)
        score += 1
    else:
        failed.append(
            {
                "field": "selected_policy",
                "live": sorted(_current_policy_set(runtime_cfg, source)),
                "allowlist": entry.get("selected_policy"),
                "reason": policy_reason,
            }
        )

    proof = _match_key(entry.get("proof_class"))
    if proof in {
        "positive_origin_native_dynamic_replay_row_level_proof",
        "positive_outside_session_origin_native_dynamic_replay_row_level_proof",
    }:
        matched.append("proof_class")
        score += 1
    else:
        failed.append({"field": "proof_class", "live": "positive_origin_native_dynamic_replay_row_level_proof", "allowlist": proof})

    action = _match_key(entry.get("activation_action"))
    if action == "trade_vnext_broader_origin_candidate":
        matched.append("activation_action")
        score += 1
    else:
        failed.append({"field": "activation_action", "live": "trade_vnext_broader_origin_candidate", "allowlist": action})

    min_rows = int(runtime_cfg.get("moonshot_dynamic_execution_router_broader_origin_min_group_rows") or 20)
    if _selector_metrics_positive(entry, min_rows=min_rows):
        matched.append("positive_selector_metrics")
        score += 1
    else:
        failed.append(
            {
                "field": "positive_selector_metrics",
                "live": f"selected_count>={min_rows}, expectancy>0, profit_factor>1",
                "allowlist": entry.get("metrics"),
            }
        )
    return failed, matched, score


def _nearest_allowlist_candidate(
    entries: list[dict[str, Any]],
    source: dict[str, Any],
    *,
    runtime_cfg: dict[str, Any],
    promotion_evidence: dict[str, Any],
) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    for entry in entries:
        failed, matched, score = _allowlist_failed_dimensions(
            entry,
            source,
            runtime_cfg=runtime_cfg,
            promotion_evidence=promotion_evidence,
        )
        candidate = {
            "symbol": entry.get("symbol"),
            "origin_family": entry.get("origin_family") or entry.get("candidate_origin_family"),
            "side": entry.get("side"),
            "route_session": entry.get("route_session") or entry.get("session_bucket"),
            "utc_hour_bucket": entry.get("utc_hour_bucket"),
            "selected_policy": entry.get("selected_policy"),
            "proof_class": entry.get("proof_class"),
            "activation_action": entry.get("activation_action"),
            "metrics": entry.get("metrics"),
            "score": score,
            "matched_dimensions": matched,
            "failed_dimensions": failed,
        }
        if best is None or score > int(best.get("score") or -1) or (
            score == int(best.get("score") or -1)
            and len(failed) < len(best.get("failed_dimensions") or [])
        ):
            best = candidate
    return best


def _risk_row_policy(row: dict[str, Any]) -> str:
    if row.get("selected_policy"):
        return _match_key(row.get("selected_policy"))
    sizing = row.get("dynamic_execution_sizing_policy")
    if isinstance(sizing, dict):
        return _match_key(sizing.get("selected_policy"))
    return ""


def _risk_failed_dimensions(
    row: dict[str, Any],
    source: dict[str, Any],
    *,
    runtime_cfg: dict[str, Any],
    promotion_evidence: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str], int]:
    failed: list[dict[str, Any]] = []
    matched: list[str] = []
    score = 0

    def add_match(field: str) -> None:
        nonlocal score
        matched.append(field)
        score += 1

    live_symbol = str(source.get("symbol") or "").upper().replace(".", "_")
    row_symbol = str(row.get("symbol") or row.get("broker_alias") or "").upper().replace(".", "_")
    if live_symbol == row_symbol:
        add_match("symbol")
    else:
        failed.append({"field": "symbol", "live": live_symbol, "risk_row": row_symbol})

    live_family = _normalize_origin(
        source.get("candidate_origin_family")
        or source.get("origin_family")
        or source.get("framework")
    )
    row_family = _normalize_origin(row.get("family") or row.get("candidate_origin_family") or row.get("framework"))
    if live_family == row_family:
        add_match("candidate_origin_family")
    else:
        failed.append({"field": "candidate_origin_family", "live": live_family, "risk_row": row_family})

    live_side = str(source.get("side") or "").upper()
    row_side = str(row.get("side") or "").upper()
    if not row_side or live_side == row_side:
        add_match("side")
    else:
        failed.append({"field": "side", "live": live_side, "risk_row": row_side})

    row_session = _match_key(row.get("route_session") or row.get("session_bucket")).removesuffix("_broad")
    if row_session in _session_candidates(source):
        add_match("route_session")
    else:
        failed.append({"field": "route_session", "live": sorted(_session_candidates(source)), "risk_row": row_session})

    row_hour = _match_key(row.get("utc_hour_bucket"))
    if row_hour:
        live_hour = _match_key(source.get("utc_hour_bucket"))
        if row_hour == live_hour:
            add_match("utc_hour_bucket")
        else:
            failed.append({"field": "utc_hour_bucket", "live": live_hour, "risk_row": row_hour})
    else:
        add_match("utc_hour_bucket_not_dimensioned")

    selected = _match_key(source.get("selected_cell_risk_selected_policy") or source.get("selected_policy"))
    row_policy = _risk_row_policy(row)
    if not row_policy or row_policy == selected:
        add_match("selected_policy")
    else:
        policy_allowed, reason = _policy_allowed_by_current_contract(
            row_policy,
            runtime_cfg=runtime_cfg,
            source=source,
            promotion_evidence=promotion_evidence,
        )
        if policy_allowed and bool(
            runtime_cfg.get("moonshot_dynamic_execution_router_allow_policy_invariant_selected_cell_risk_geometry")
        ):
            add_match("policy_invariant_selected_cell_risk_geometry")
        else:
            failed.append({"field": "selected_policy", "live": selected, "risk_row": row_policy, "reason": reason})
    return failed, matched, score


def _nearest_risk_candidate(
    rows: list[dict[str, Any]],
    source: dict[str, Any],
    *,
    runtime_cfg: dict[str, Any],
    promotion_evidence: dict[str, Any],
) -> dict[str, Any] | None:
    best: dict[str, Any] | None = None
    for row in rows:
        failed, matched, score = _risk_failed_dimensions(
            row,
            source,
            runtime_cfg=runtime_cfg,
            promotion_evidence=promotion_evidence,
        )
        candidate = {
            "risk_cell_id": row.get("risk_cell_id"),
            "symbol": row.get("symbol"),
            "broker_alias": row.get("broker_alias"),
            "selector_component": row.get("selector_component"),
            "family": row.get("family") or row.get("candidate_origin_family"),
            "side": row.get("side"),
            "route_session": row.get("route_session") or row.get("session_bucket"),
            "utc_hour_bucket": row.get("utc_hour_bucket"),
            "selected_policy": row.get("selected_policy") or _risk_row_policy(row),
            "effective_risk_per_trade_pct": row.get("effective_risk_per_trade_pct"),
            "risk_decision_basis": row.get("risk_decision_basis"),
            "exact_unresolved_or_excluded_reasons": row.get("exact_unresolved_or_excluded_reasons") or [],
            "score": score,
            "matched_dimensions": matched,
            "failed_dimensions": failed,
        }
        if best is None or score > int(best.get("score") or -1) or (
            score == int(best.get("score") or -1)
            and len(failed) < len(best.get("failed_dimensions") or [])
        ):
            best = candidate
    return best


def _risk_refusal_cause(
    *,
    source: dict[str, Any],
    nearest: dict[str, Any] | None,
) -> str:
    reason = _match_key(source.get("selected_cell_risk_match_reason"))
    unresolved = [
        _match_key(item)
        for item in (
            source.get("selected_cell_risk_unresolved_reasons")
            or source.get("selected_cell_risk_execution_critical_unresolved_reasons")
            or (nearest or {}).get("exact_unresolved_or_excluded_reasons")
            or []
        )
    ]
    failed = {str(item.get("field")) for item in (nearest or {}).get("failed_dimensions") or []}
    if reason == "no_exact_selected_cell_risk_match":
        if "selected_policy" in failed:
            return "policy_identity_mismatch_after_momentum_partial_promotion"
        if "route_session" in failed or "utc_hour_bucket" in failed:
            return "session_or_hour_key_mismatch"
        if "symbol" in failed:
            return "symbol_alias_or_symbol_key_mismatch"
        return "missing_ledger_row"
    if "zero_or_unresolved" in reason:
        if any(item.startswith("risk_zero") or "risk_zero" in item for item in unresolved):
            return "zero_risk_row"
        if any("commission" in item for item in unresolved):
            return "unresolved_commission_field"
        if any("spread" in item for item in unresolved):
            return "unresolved_spread_field"
        if any("broker_geometry" in item or "digits_" in item or "price_rounding" in item or "lot_rounding" in item for item in unresolved):
            return "unresolved_broker_geometry"
        if any("stale" in item or "old" in item or "be" in item for item in unresolved):
            return "stale_be_era_risk_cell"
        return "zero_risk_row_or_unresolved_selected_cell"
    if "unresolved_execution_critical" in reason:
        return "unresolved_broker_geometry_or_commission_spread"
    if source.get("selected_cell_risk_allowed") is False:
        return "real_negative_or_unsafe_cell"
    return "not_a_selected_cell_refusal"


def _refusal_breakdown_row(
    *,
    row: dict[str, Any],
    source: dict[str, Any],
    decision: dict[str, Any],
    runtime_cfg: dict[str, Any],
    allowlist_entries: list[dict[str, Any]],
    risk_rows: list[dict[str, Any]],
    broker_aliases: dict[str, str],
    promotion_evidence: dict[str, Any],
    post_reload_cutoff: datetime | None,
) -> dict[str, Any]:
    symbol = str(row.get("symbol") or source.get("symbol") or "unknown")
    nearest_allowlist = _nearest_allowlist_candidate(
        allowlist_entries,
        source,
        runtime_cfg=runtime_cfg,
        promotion_evidence=promotion_evidence,
    )
    nearest_risk = _nearest_risk_candidate(
        risk_rows,
        source,
        runtime_cfg=runtime_cfg,
        promotion_evidence=promotion_evidence,
    )
    failed_dimensions = (nearest_allowlist or {}).get("failed_dimensions") or []
    risk_failed_dimensions = (nearest_risk or {}).get("failed_dimensions") or []
    refusals = [str(item) for item in decision.get("refusal_reasons") or []]
    event_dt = _parse_dt(row.get("timestamp_utc"))
    framework_refusal = "framework_not_activated_in_stage13_full_moonshot_selector" in refusals
    risk_refusal = "selected_cell_risk_not_verified_or_zero" in refusals
    current_contract_row = bool(
        post_reload_cutoff is not None and event_dt is not None and event_dt >= post_reload_cutoff
    )
    activated_origin = _normalize_origin(
        source.get("candidate_origin_family") or source.get("origin_family") or source.get("framework")
    ) in {
        _normalize_origin(item)
        for item in runtime_cfg.get("moonshot_dynamic_execution_router_activated_origin_families", [])
    }
    would_match_current_selector = bool(nearest_allowlist and not failed_dimensions)
    risk_cause = _risk_refusal_cause(source=source, nearest=nearest_risk) if risk_refusal else "not_a_selected_cell_refusal"
    if framework_refusal and would_match_current_selector and activated_origin and current_contract_row:
        selector_classification = "selector_contract_mismatch_should_route_under_current_bridge"
        repair_decision = "runtime_selector_policy_bridge_repair_required_or_reload_pending"
        evidence_backed_exclusion = False
    elif framework_refusal and would_match_current_selector and activated_origin:
        selector_classification = "historical_selector_contract_mismatch_repaired_after_reload"
        repair_decision = "historical_pre_current_reload_row_excluded_from_live_authority_retest_required_on_new_rows"
        evidence_backed_exclusion = True
    elif framework_refusal and failed_dimensions:
        selector_classification = "outside_activated_stage13_selector"
        repair_decision = "reject_with_exact_selector_dimension_proof"
        evidence_backed_exclusion = True
    else:
        selector_classification = "selector_not_refused_or_already_allowed"
        repair_decision = "not_applicable"
        evidence_backed_exclusion = True
    selector_excludes_this_row = (
        framework_refusal
        and selector_classification == "outside_activated_stage13_selector"
        and evidence_backed_exclusion is True
        and bool(failed_dimensions)
    )
    if risk_refusal and not current_contract_row and risk_cause in {
        "policy_identity_mismatch_after_momentum_partial_promotion",
        "symbol_alias_or_symbol_key_mismatch",
        "missing_ledger_row",
    }:
        risk_repair_decision = "historical_pre_current_reload_row_excluded_from_live_authority_retest_required_on_new_rows"
        risk_evidence_backed_exclusion = True
    elif risk_refusal and selector_excludes_this_row:
        risk_repair_decision = (
            "reject_with_exact_selector_dimension_proof_selected_cell_not_applicable"
        )
        risk_evidence_backed_exclusion = True
    elif risk_refusal and risk_cause in {
        "policy_identity_mismatch_after_momentum_partial_promotion",
        "symbol_alias_or_symbol_key_mismatch",
    }:
        risk_repair_decision = "repair_selected_cell_risk_bridge_or_alias_contract"
        risk_evidence_backed_exclusion = False
    elif risk_refusal and risk_cause == "missing_ledger_row" and evidence_backed_exclusion is True:
        risk_repair_decision = "reject_with_selector_exclusion_and_missing_risk_row_proof"
        risk_evidence_backed_exclusion = True
    elif risk_refusal:
        risk_repair_decision = "reject_with_exact_selected_cell_risk_proof"
        risk_evidence_backed_exclusion = risk_cause not in {"missing_ledger_row"}
    else:
        risk_repair_decision = "not_applicable"
        risk_evidence_backed_exclusion = True
    return {
        "schema_version": "vnext_live_selector_risk_refusal_breakdown_v1",
        "timestamp_utc": row.get("timestamp_utc"),
        "candle_time_utc": row.get("candle_time_utc") or source.get("candle_time_utc"),
        "symbol": symbol,
        "broker_symbol": source.get("broker_symbol") or broker_aliases.get(symbol) or symbol,
        "side": source.get("side"),
        "framework": source.get("framework"),
        "candidate_origin_family": source.get("candidate_origin_family") or source.get("origin_family"),
        "normalized_origin_family": _normalize_origin(
            source.get("candidate_origin_family") or source.get("origin_family") or source.get("framework")
        ),
        "branch_label": source.get("branch_label"),
        "session": row.get("kill_zone") or source.get("session"),
        "route_session": source.get("route_session"),
        "session_bucket": source.get("session_bucket"),
        "kill_zone_position": source.get("kill_zone_position"),
        "utc_hour_bucket": source.get("utc_hour_bucket"),
        "selected_policy": decision.get("selected_policy"),
        "execution_policy_id": decision.get("execution_policy_id"),
        "broader_origin_allowed": source.get("broader_origin_allowed"),
        "broader_origin_match_reason": source.get("broader_origin_match_reason"),
        "repaired_branch_allowed": source.get("repaired_branch_allowed"),
        "repaired_branch_match_reason": source.get("repaired_branch_match_reason"),
        "selected_cell_risk_allowed": source.get("selected_cell_risk_allowed"),
        "selected_cell_risk_match_reason": source.get("selected_cell_risk_match_reason"),
        "selected_cell_risk_cell_id": source.get("selected_cell_risk_cell_id"),
        "risk_pct": source.get("selected_cell_risk_pct"),
        "source_mode": source.get("source_mode"),
        "source_path_feature_status": source.get("source_path_feature_status"),
        "live_generation_status": source.get("live_generation_status"),
        "source_window_complete": source.get("source_window_complete"),
        "allowlist_row_count": len(allowlist_entries),
        "selected_cell_risk_ledger_rows": source.get("selected_cell_risk_ledger_rows") or len(risk_rows),
        "nearest_allowlist_candidate": nearest_allowlist,
        "nearest_selected_cell_risk_candidate": nearest_risk,
        "exact_failed_dimensions": failed_dimensions,
        "selected_cell_risk_failed_dimensions": risk_failed_dimensions,
        "refusal_reasons": refusals,
        "post_reload_current_contract": current_contract_row,
        "selector_classification": selector_classification,
        "selector_repair_decision": repair_decision,
        "selector_evidence_backed_exclusion": evidence_backed_exclusion,
        "selected_cell_risk_refusal_cause": risk_cause,
        "selected_cell_risk_repair_decision": risk_repair_decision,
        "selected_cell_risk_evidence_backed_exclusion": risk_evidence_backed_exclusion,
        "activated_origin_family": activated_origin,
        "current_policy_set": sorted(_current_policy_set(runtime_cfg, source)),
        "promotion_evidence_status": promotion_evidence.get("status"),
        "promotion_evidence_checked_rows": promotion_evidence.get("checked_rows"),
    }


def _iter_trade_records(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    records: list[tuple[Path, dict[str, Any]]] = []
    if not root.exists():
        return records
    for path in sorted(root.glob("*/*.json")):
        if path.name.startswith("_"):
            continue
        record = _read_json(path, {})
        if isinstance(record, dict):
            records.append((path, record))
    return records


def _record_time(path: Path, record: dict[str, Any]) -> datetime:
    packet = _get(record, "decision_pipeline", "gtos_vnext_candidate_intelligence_packet") or {}
    for value in (
        _get(packet, "candidate_identity", "candle_close_utc"),
        _get(record, "metadata", "timestamp_utc"),
        record.get("timestamp_utc"),
    ):
        parsed = _parse_dt(value)
        if parsed is not None:
            return parsed
    return _mtime_utc(path)


def _record_symbol_origin(record: dict[str, Any], path: Path) -> tuple[str, str]:
    packet = _get(record, "decision_pipeline", "gtos_vnext_candidate_intelligence_packet") or {}
    candidate = record.get("moonshot_broader_origin_candidate") or {}
    symbol = (
        _get(packet, "candidate_identity", "symbol")
        or candidate.get("symbol")
        or record.get("symbol")
        or path.parent.name
    )
    origin = (
        _get(packet, "candidate_identity", "origin_family")
        or candidate.get("origin_family")
        or candidate.get("route_family")
        or candidate.get("framework")
        or "unknown"
    )
    return str(symbol), _normalize_origin(origin)


def _add_counter(counter: Counter[str], value: Any) -> None:
    if value not in (None, "", [], {}):
        counter[str(value)] += 1


def build(
    *,
    hours: float = 12.0,
    now: datetime | None = None,
    post_reload_cutoff: datetime | None = None,
    config_path: Path = CONFIG_PATH,
    runtime_log: Path = RUNTIME_LOG,
    replacement_log: Path = REPLACEMENT_LOG,
    trade_record_root: Path = TRADE_RECORD_ROOT,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    window_start = now - timedelta(hours=hours)
    runtime_cfg = _runtime_config(config_path)
    symbols, origins = _contract(config_path)
    allowlist_entries = _read_allowlist_entries(
        runtime_cfg.get("moonshot_dynamic_execution_router_broader_origin_allowlist_path")
    )
    risk_rows = _read_risk_rows(
        runtime_cfg.get("moonshot_dynamic_execution_router_selected_cell_risk_ledger_path")
    )
    broker_aliases = _broker_alias_map()
    promotion_evidence = _promotion_evidence_verified(runtime_cfg)
    cells: dict[tuple[str, str], dict[str, Any]] = {
        (symbol, origin): _new_cell(symbol, origin)
        for symbol in symbols
        for origin in origins
    }
    stale_label_hits: list[dict[str, Any]] = []
    refusal_breakdowns: list[dict[str, Any]] = []
    replacement_refusal_counts: Counter[str] = Counter()
    runtime_rows = 0
    post_reload_rows = 0

    for row in _read_jsonl(runtime_log):
        event_dt = _parse_dt(row.get("timestamp_utc"))
        if event_dt is None or event_dt < window_start or event_dt > now + timedelta(minutes=1):
            continue
        runtime_rows += 1
        source = _runtime_source(row)
        decision = row.get("decision") if isinstance(row.get("decision"), dict) else {}
        symbol = row.get("symbol") or source.get("symbol")
        origin = source.get("origin_family") or source.get("route_family") or source.get("candidate_origin_family")
        cell = _cell(cells, symbol, origin)
        phase = row.get("phase")
        candle = row.get("candle_time_utc") or source.get("candle_time_utc")
        candidate_id = _get(decision, "evidence", "broader_origin_candidate_id")
        _touch_latest(cell, event_dt=event_dt, candle=candle, candidate_id=candidate_id)
        _add_counter(cell["session_counts"], row.get("kill_zone") or source.get("session_bucket") or source.get("route_session"))
        _add_counter(cell["source_mode_counts"], source.get("source_mode"))
        _add_counter(cell["selected_cell_state_counts"], source.get("selected_cell_risk_match_reason"))
        _add_counter(cell["prop_action_counts"], source.get("prop_governor_action") or decision.get("prop_action"))
        if post_reload_cutoff is not None and event_dt >= post_reload_cutoff:
            cell["post_reload_runtime_rows"] += 1
            post_reload_rows += 1
            line = json.dumps(row, sort_keys=True)
            if STALE_LABEL_RE.search(line):
                cell["post_reload_stale_label_hits"] += 1
                stale_label_hits.append({
                    "symbol": str(symbol),
                    "origin_family": _normalize_origin(origin),
                    "timestamp_utc": event_dt.isoformat(),
                    "phase": phase,
                })
        if phase == "broader_origin_pre_ai_candidate":
            cell["raw_candidate_rows"] += 1
        elif phase == "moonshot_dynamic_execution":
            cell["dynamic_rows"] += 1
            _add_counter(cell["policy_counts"], decision.get("selected_policy"))
            _add_counter(cell["execution_policy_id_counts"], decision.get("execution_policy_id"))
            _add_counter(cell["geometry_state_counts"], "dynamic_before_geometry")
            _add_counter(cell["old_system_leakage_counts"], decision.get("replaced_policy"))
            for reason in decision.get("refusal_reasons") or []:
                cell["refusal_reason_counts"][str(reason)] += 1
            refusals = {str(item) for item in decision.get("refusal_reasons") or []}
            if refusals & {
                "framework_not_activated_in_stage13_full_moonshot_selector",
                "selected_cell_risk_not_verified_or_zero",
            }:
                refusal_breakdowns.append(
                    _refusal_breakdown_row(
                        row=row,
                        source=source,
                        decision=decision,
                        runtime_cfg=runtime_cfg,
                        allowlist_entries=allowlist_entries,
                        risk_rows=risk_rows,
                        broker_aliases=broker_aliases,
                        promotion_evidence=promotion_evidence,
                        post_reload_cutoff=post_reload_cutoff,
                    )
                )
            if decision.get("candidate_use_allowed_now") is True:
                cell["final_broker_ready_candidates"] += 1
            else:
                cell["dynamic_skip_rows"] += 1
                cell["latest_refusal_reasons"] = [str(item) for item in decision.get("refusal_reasons") or []]

    for row in _read_jsonl(replacement_log):
        wrapper_dt = _parse_dt(row.get("timestamp_utc"))
        if wrapper_dt is None or wrapper_dt < window_start or wrapper_dt > now + timedelta(minutes=1):
            continue
        snap = row.get("snapshot") if isinstance(row.get("snapshot"), dict) else {}
        symbol = snap.get("symbol")
        source = snap.get("source_capture_completeness") if isinstance(snap.get("source_capture_completeness"), dict) else {}
        origin = _normalize_origin(_get(snap, "dynamic_exit_transition", "selected_branch"))
        cell = _cell(cells, symbol, origin)
        _touch_latest(cell, event_dt=wrapper_dt, candle=snap.get("candle_time_utc"))
        for reason in source.get("refusal_reasons") or []:
            replacement_refusal_counts[str(reason)] += 1

    for path, record in _iter_trade_records(trade_record_root):
        record_dt = _record_time(path, record)
        if record_dt < window_start or record_dt > now + timedelta(minutes=1):
            continue
        symbol, origin = _record_symbol_origin(record, path)
        cell = _cell(cells, symbol, origin)
        packet = _get(record, "decision_pipeline", "gtos_vnext_candidate_intelligence_packet")
        final_outcome = _get(record, "decision_pipeline", "final_outcome") or record.get("final_outcome")
        cell["trade_record_rows"] += 1
        if isinstance(packet, dict):
            cell["candidate_packet_rows"] += 1
            if packet.get("capture_mode") == "native_live_writer":
                cell["native_live_writer_packet_rows"] += 1
            if _get(packet, "geometry", "repair_path", "entered") is True:
                cell["repaired_candidate_rows"] += 1
        if final_outcome:
            cell["final_outcome_counts"][str(final_outcome)] += 1
            if str(final_outcome).startswith(("LIMIT_PLACED", "EXECUTED_GTOS_VNEXT")):
                cell["final_broker_ready_candidates"] += 1
        _touch_latest(
            cell,
            event_dt=record_dt,
            candle=_get(packet, "candidate_identity", "candle_close_utc") if isinstance(packet, dict) else None,
            candidate_id=_get(packet, "candidate_identity", "candidate_id") if isinstance(packet, dict) else None,
        )

    lifecycle_counts = _lifecycle_counts()
    for cell in cells.values():
        cell["order_rows"] += lifecycle_counts["orders"].get(cell["symbol"], 0)
        cell["fill_rows"] += lifecycle_counts["fills"].get(cell["symbol"], 0)
        cell["close_rows"] += lifecycle_counts["closes"].get(cell["symbol"], 0)
        _classify_cell(cell)
        for key in (
            "session_counts",
            "policy_counts",
            "execution_policy_id_counts",
            "refusal_reason_counts",
            "final_outcome_counts",
            "source_mode_counts",
            "selected_cell_state_counts",
            "prop_action_counts",
            "geometry_state_counts",
            "old_system_leakage_counts",
        ):
            cell[key] = _counter_to_dict(cell[key])

    rows = sorted(cells.values(), key=lambda item: (item["symbol"], item["origin_family"]))
    summary = _summary(
        rows,
        now=now,
        window_start=window_start,
        symbols=symbols,
        origins=origins,
        runtime_rows=runtime_rows,
        post_reload_rows=post_reload_rows,
        stale_label_hits=stale_label_hits,
        post_reload_cutoff=post_reload_cutoff,
        refusal_breakdowns=refusal_breakdowns,
        allowlist_row_count=len(allowlist_entries),
        selected_cell_risk_ledger_rows=len(risk_rows),
        promotion_evidence=promotion_evidence,
        replacement_refusal_counts=replacement_refusal_counts,
    )
    return rows, summary, refusal_breakdowns


def _lifecycle_counts() -> dict[str, Counter[str]]:
    orders: Counter[str] = Counter()
    fills: Counter[str] = Counter()
    closes: Counter[str] = Counter()
    for row in _read_jsonl(ORDER_LIFECYCLE_LEDGER):
        if row.get("status") == "no_vnext_order_lifecycle_event_observed":
            continue
        for item in row.get("orders_tail") or []:
            if isinstance(item, dict) and item.get("comment") != "preflight_test":
                orders[str(item.get("symbol") or "unknown")] += 1
    for row in _read_jsonl(DYNAMIC_LIFECYCLE_LEDGER):
        if str(row.get("status") or "").startswith("no_real_vnext"):
            continue
        symbol = row.get("symbol")
        if row.get("event") in {"fill", "partial_close", "be_transition"}:
            fills[str(symbol or "unknown")] += 1
        if row.get("event") in {"close", "momentum_pullback_close", "dynamic_final_close"}:
            closes[str(symbol or "unknown")] += 1
    for row in _read_jsonl(BROKER_DEAL_LEDGER):
        if str(row.get("status") or "").startswith("no_broker_deals"):
            continue
        symbol = row.get("symbol")
        if symbol:
            closes[str(symbol)] += 1
    return {"orders": orders, "fills": fills, "closes": closes}


def _classify_cell(cell: dict[str, Any]) -> None:
    if cell["final_broker_ready_candidates"] > 0:
        cell["classification"] = "broker_ready_shape_observed"
        cell["classification_reason"] = "at_least_one_candidate_reached_broker_ready_or_order_path"
    elif cell["dynamic_skip_rows"] > 0:
        cell["classification"] = "live_shape_refused_before_order"
        top = Counter(cell["refusal_reason_counts"]).most_common(1)
        cell["classification_reason"] = top[0][0] if top else "dynamic_router_refused_before_order"
    elif cell["raw_candidate_rows"] > 0:
        cell["classification"] = "raw_shape_no_dynamic_path"
        cell["classification_reason"] = "raw_pre_ai_candidate_observed_without_dynamic_execution_row"
    else:
        cell["classification"] = "no_live_shape_observed"
        cell["classification_reason"] = "no_raw_or_dynamic_candidate_rows_in_window"


def _sum(rows: list[dict[str, Any]], key: str) -> int:
    return int(sum(int(row.get(key) or 0) for row in rows))


def _summary(
    rows: list[dict[str, Any]],
    *,
    now: datetime,
    window_start: datetime,
    symbols: list[str],
    origins: list[str],
    runtime_rows: int,
    post_reload_rows: int,
    stale_label_hits: list[dict[str, Any]],
    post_reload_cutoff: datetime | None,
    refusal_breakdowns: list[dict[str, Any]],
    allowlist_row_count: int,
    selected_cell_risk_ledger_rows: int,
    promotion_evidence: dict[str, Any],
    replacement_refusal_counts: Counter[str],
) -> dict[str, Any]:
    class_counts = Counter(str(row.get("classification")) for row in rows)
    refusal_counts: Counter[str] = Counter()
    policy_counts: Counter[str] = Counter()
    final_counts: Counter[str] = Counter()
    active_symbols = set()
    for row in rows:
        if row.get("raw_candidate_rows") or row.get("dynamic_rows") or row.get("trade_record_rows"):
            active_symbols.add(row["symbol"])
        refusal_counts.update(row.get("refusal_reason_counts") or {})
        policy_counts.update(row.get("policy_counts") or {})
        final_counts.update(row.get("final_outcome_counts") or {})
    broker_ready = _sum(rows, "final_broker_ready_candidates")
    dynamic_skips = _sum(rows, "dynamic_skip_rows")
    raw_candidates = _sum(rows, "raw_candidate_rows")
    if broker_ready:
        flat_broker_classification = "broker_ready_candidate_exists"
    elif dynamic_skips or raw_candidates:
        flat_broker_classification = "flat_broker_state_explained_by_live_refusals"
    else:
        flat_broker_classification = "flat_broker_state_no_live_shape_observed"
    return {
        "schema_version": "vnext_live_starvation_intelligence_summary_v1",
        "generated_at_utc": now.isoformat(),
        "window_start_utc": window_start.isoformat(),
        "window_hours": round((now - window_start).total_seconds() / 3600.0, 3),
        "post_reload_cutoff_utc": post_reload_cutoff.isoformat() if post_reload_cutoff else None,
        "symbol_count": len(symbols),
        "origin_family_count": len(origins),
        "expected_symbol_origin_cells": len(symbols) * len(origins),
        "ledger_rows": len(rows),
        "extra_observed_cells": max(0, len(rows) - (len(symbols) * len(origins))),
        "runtime_rows": runtime_rows,
        "post_reload_runtime_rows": post_reload_rows,
        "post_reload_stale_label_hits": len(stale_label_hits),
        "stale_label_hit_examples": stale_label_hits[:10],
        "stage13_broader_origin_allowlist_rows": allowlist_row_count,
        "selected_cell_risk_ledger_rows": selected_cell_risk_ledger_rows,
        "policy_promotion_evidence": promotion_evidence,
        "raw_candidate_rows": raw_candidates,
        "dynamic_rows": _sum(rows, "dynamic_rows"),
        "dynamic_skip_rows": dynamic_skips,
        "repaired_candidate_rows": _sum(rows, "repaired_candidate_rows"),
        "final_broker_ready_candidates": broker_ready,
        "orders": _sum(rows, "order_rows"),
        "fills": _sum(rows, "fill_rows"),
        "closes": _sum(rows, "close_rows"),
        "trade_record_rows": _sum(rows, "trade_record_rows"),
        "candidate_packet_rows": _sum(rows, "candidate_packet_rows"),
        "native_live_writer_packet_rows": _sum(rows, "native_live_writer_packet_rows"),
        "active_symbol_count": len(active_symbols),
        "inactive_symbol_count": len(set(symbols) - active_symbols),
        "classification_counts": _counter_to_dict(class_counts),
        "refusal_reason_counts": _counter_to_dict(refusal_counts),
        "replacement_monitor_refusal_reason_counts": _counter_to_dict(replacement_refusal_counts),
        "selector_risk_refusal_breakdown_rows": len(refusal_breakdowns),
        "framework_selector_refusal_breakdown_rows": sum(
            1
            for row in refusal_breakdowns
            if "framework_not_activated_in_stage13_full_moonshot_selector"
            in (row.get("refusal_reasons") or [])
        ),
        "selected_cell_risk_refusal_breakdown_rows": sum(
            1
            for row in refusal_breakdowns
            if "selected_cell_risk_not_verified_or_zero"
            in (row.get("refusal_reasons") or [])
        ),
        "selector_refusal_classification_counts": _counter_to_dict(
            Counter(str(row.get("selector_classification")) for row in refusal_breakdowns)
        ),
        "selected_cell_risk_refusal_cause_counts": _counter_to_dict(
            Counter(str(row.get("selected_cell_risk_refusal_cause")) for row in refusal_breakdowns)
        ),
        "selector_unresolved_repair_rows": sum(
            1
            for row in refusal_breakdowns
            if row.get("selector_evidence_backed_exclusion") is not True
        ),
        "current_selector_unresolved_repair_rows": sum(
            1
            for row in refusal_breakdowns
            if row.get("post_reload_current_contract") is True
            and row.get("selector_evidence_backed_exclusion") is not True
        ),
        "historical_selector_contract_mismatch_repaired_after_reload_rows": sum(
            1
            for row in refusal_breakdowns
            if row.get("selector_classification")
            == "historical_selector_contract_mismatch_repaired_after_reload"
        ),
        "selected_cell_risk_unresolved_repair_rows": sum(
            1
            for row in refusal_breakdowns
            if row.get("selected_cell_risk_evidence_backed_exclusion") is not True
        ),
        "current_selected_cell_risk_unresolved_repair_rows": sum(
            1
            for row in refusal_breakdowns
            if row.get("post_reload_current_contract") is True
            and row.get("selected_cell_risk_evidence_backed_exclusion") is not True
        ),
        "historical_selected_cell_risk_unresolved_repair_rows": sum(
            1
            for row in refusal_breakdowns
            if row.get("post_reload_current_contract") is not True
            and row.get("selected_cell_risk_repair_decision")
            == "historical_pre_current_reload_row_excluded_from_live_authority_retest_required_on_new_rows"
        ),
        "policy_counts": _counter_to_dict(policy_counts),
        "final_outcome_counts": _counter_to_dict(final_counts),
        "flat_broker_classification": flat_broker_classification,
        "pending_native_packet_proof": _sum(rows, "native_live_writer_packet_rows") == 0,
        "pending_real_broker_lifecycle": _sum(rows, "fills") == 0 and _sum(rows, "closes") == 0,
    }


def verify(
    summary: dict[str, Any],
    rows: list[dict[str, Any]],
    refusal_breakdowns: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    refusal_breakdowns = refusal_breakdowns or []
    if summary.get("ledger_rows", 0) < summary.get("expected_symbol_origin_cells", 0):
        issues.append({
            "code": "missing_symbol_origin_cells",
            "ledger_rows": summary.get("ledger_rows"),
            "expected": summary.get("expected_symbol_origin_cells"),
        })
    if summary.get("symbol_count") != 24:
        issues.append({"code": "symbol_count_not_24", "symbol_count": summary.get("symbol_count")})
    if summary.get("origin_family_count", 0) <= 0:
        issues.append({"code": "no_activated_origin_families"})
    if summary.get("post_reload_stale_label_hits"):
        issues.append({
            "code": "post_reload_stale_label_hits",
            "count": summary.get("post_reload_stale_label_hits"),
            "examples": summary.get("stale_label_hit_examples"),
        })
    refusal_counts = summary.get("refusal_reason_counts") or {}
    framework_refusals = int(
        refusal_counts.get("framework_not_activated_in_stage13_full_moonshot_selector") or 0
    )
    selected_cell_refusals = int(refusal_counts.get("selected_cell_risk_not_verified_or_zero") or 0)
    framework_breakdowns = [
        row
        for row in refusal_breakdowns
        if "framework_not_activated_in_stage13_full_moonshot_selector"
        in (row.get("refusal_reasons") or [])
    ]
    selected_cell_breakdowns = [
        row
        for row in refusal_breakdowns
        if "selected_cell_risk_not_verified_or_zero" in (row.get("refusal_reasons") or [])
    ]
    if framework_refusals and len(framework_breakdowns) != framework_refusals:
        issues.append(
            {
                "code": "framework_refusal_breakdown_count_mismatch",
                "refusal_count": framework_refusals,
                "breakdown_rows": len(framework_breakdowns),
            }
        )
    if selected_cell_refusals and len(selected_cell_breakdowns) != selected_cell_refusals:
        issues.append(
            {
                "code": "selected_cell_refusal_breakdown_count_mismatch",
                "refusal_count": selected_cell_refusals,
                "breakdown_rows": len(selected_cell_breakdowns),
            }
        )
    missing_selector_proof = [
        row
        for row in framework_breakdowns
        if not row.get("selector_classification")
        or row.get("nearest_allowlist_candidate") is None
        or (
            not row.get("exact_failed_dimensions")
            and row.get("selector_evidence_backed_exclusion") is not False
            and row.get("selector_classification")
            != "historical_selector_contract_mismatch_repaired_after_reload"
        )
    ]
    if missing_selector_proof:
        issues.append(
            {
                "code": "framework_refusal_missing_exact_selector_proof",
                "examples": missing_selector_proof[:5],
            }
        )
    missing_risk_proof = [
        row
        for row in selected_cell_breakdowns
        if row.get("selected_cell_risk_refusal_cause")
        not in {
            "no_exact_selected_cell_match",
            "policy_identity_mismatch_after_momentum_partial_promotion",
            "session_or_hour_key_mismatch",
            "symbol_alias_or_symbol_key_mismatch",
            "zero_risk_row",
            "zero_risk_row_or_unresolved_selected_cell",
            "unresolved_broker_geometry",
            "unresolved_commission_field",
            "unresolved_spread_field",
            "stale_be_era_risk_cell",
            "missing_ledger_row",
            "real_negative_or_unsafe_cell",
            "unresolved_broker_geometry_or_commission_spread",
        }
    ]
    if missing_risk_proof:
        issues.append(
            {
                "code": "selected_cell_refusal_missing_concrete_cause",
                "examples": missing_risk_proof[:5],
            }
        )
    unresolved_selector = [
        row
        for row in framework_breakdowns
        if row.get("post_reload_current_contract") is True
        and row.get("selector_evidence_backed_exclusion") is not True
    ]
    if unresolved_selector:
        issues.append(
            {
                "code": "framework_refusal_contract_mismatch_unrepaired",
                "count": len(unresolved_selector),
                "examples": unresolved_selector[:5],
            }
        )
    unresolved_risk = [
        row
        for row in selected_cell_breakdowns
        if row.get("post_reload_current_contract") is True
        and row.get("selected_cell_risk_evidence_backed_exclusion") is not True
    ]
    if unresolved_risk:
        issues.append(
            {
                "code": "selected_cell_risk_contract_mismatch_unrepaired",
                "count": len(unresolved_risk),
                "examples": unresolved_risk[:5],
            }
        )
    for row in rows:
        for count_key in (
            "raw_candidate_rows",
            "dynamic_rows",
            "dynamic_skip_rows",
            "final_broker_ready_candidates",
            "order_rows",
            "fill_rows",
            "close_rows",
        ):
            if int(row.get(count_key) or 0) < 0:
                issues.append({"code": "negative_count", "symbol": row.get("symbol"), "origin": row.get("origin_family"), "field": count_key})
    return {
        "schema_version": "vnext_live_starvation_intelligence_verification_v1",
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "summary_path": str(SUMMARY_PATH.relative_to(REPO_ROOT)),
        "ledger_path": str(LEDGER_PATH.relative_to(REPO_ROOT)),
        "refusal_breakdown_path": str(REFUSAL_BREAKDOWN_PATH.relative_to(REPO_ROOT)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=float, default=12.0)
    parser.add_argument("--post-reload-cutoff-utc")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    cutoff = _parse_dt(args.post_reload_cutoff_utc)
    rows, summary, refusal_breakdowns = build(hours=args.hours, post_reload_cutoff=cutoff)
    result = verify(summary, rows, refusal_breakdowns)
    if args.check:
        saved_summary = _read_json(SUMMARY_PATH, {})
        saved_rows = _read_jsonl(LEDGER_PATH)
        saved_refusals = _read_jsonl(REFUSAL_BREAKDOWN_PATH)
        comparable_saved = dict(saved_summary)
        comparable_current = dict(summary)
        for volatile_key in ("generated_at_utc", "window_start_utc"):
            comparable_saved.pop(volatile_key, None)
            comparable_current.pop(volatile_key, None)
        if comparable_saved != comparable_current or saved_rows != rows or saved_refusals != refusal_breakdowns:
            result["ok"] = False
            result["issues"].append({"code": "starvation_intelligence_outputs_not_current"})
            result["issue_count"] = len(result["issues"])
    else:
        _write_json(SUMMARY_PATH, summary)
        _write_jsonl(LEDGER_PATH, rows)
        _write_jsonl(REFUSAL_BREAKDOWN_PATH, refusal_breakdowns)
        _write_json(VERIFY_PATH, result)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
