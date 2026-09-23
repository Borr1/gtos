"""Materialize per-day replay ledgers for the ultimate-edge TRAIN partition.

Runs the V4 timewarp engine (production-owned shared core) day by day over the
bridge-backfilled FTMO source packages and writes one full ledger set per
trading day under ``train_ledgers/`` with prefix
``ULTIMATE_EDGE_TRAIN_<YYYYMMDD>_``. These ledgers are the counterfactual
training substrate for the learned edge layer.

Day-relative source-window overrides (the engine pins HTF/M15 lookback
constants to the 2026-03..05 route era; TRAIN spans 2025-06..2026-04):

- ``replay_history_end_utc_for_days`` -> strictly ``max(day) + 1`` (no future
  rows are even loaded; defense in depth on top of the engine's as-of cut).
- ``resolve_ftmo_history_source`` default ``start_utc``/``end_utc`` -> day -
  ``HTF_LOOKBACK_CALENDAR_DAYS`` .. day+1.
- ``M15_LIVE_LOOKBACK_START`` -> day - ``M15_LOOKBACK_CALENDAR_DAYS``.

All overrides are recorded in every day-progress row.

Safety: read-only research replay. No broker mutation, no paid API, no remote
push. SEALED partition days are refused by construction; VALIDATION days are
refused unless ``--allow-validation`` (used later for frozen-baseline gate
materialization, never for training).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

ROUTE = Path(__file__).resolve().parent
ROUTE_ID = "final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
REPO_ROOT = ROUTE.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import src.research_infra.v4_timewarp_simulated_live_research_loop as tw  # noqa: E402
from src.research_infra.learned_edge_dataset_builder import (  # noqa: E402
    load_partition_registry,
    partition_role_for_day,
)

# Mutable so geometry experiments isolate their ledgers via --ledger-subdir.
LEDGER_DIR = ROUTE / "train_ledgers"
PROGRESS_PATH = LEDGER_DIR / "ULTIMATE_EDGE_TRAIN_DAY_PROGRESS_LEDGER.jsonl"
SUMMARY_PATH = ROUTE / "ULTIMATE_EDGE_TRAIN_MATERIALIZATION_SUMMARY.json"


def _set_ledger_subdir(subdir: str) -> None:
    global LEDGER_DIR, PROGRESS_PATH, SUMMARY_PATH
    LEDGER_DIR = ROUTE / subdir
    PROGRESS_PATH = LEDGER_DIR / "ULTIMATE_EDGE_TRAIN_DAY_PROGRESS_LEDGER.jsonl"
    SUMMARY_PATH = LEDGER_DIR / "ULTIMATE_EDGE_TRAIN_MATERIALIZATION_SUMMARY.json"
REGISTRY_PATH = ROUTE / "ULTIMATE_EDGE_PARTITION_REGISTRY.jsonl"
_STOP_WIDTH_SCALE_ACTIVE = 1.0

SCHEMA_PREFIX = "ultimate_edge_train"
SOURCE_STRATEGY = (
    "one_day_source_package_per_train_day_bounded_materialization_day_relative_lookback"
)

HTF_LOOKBACK_CALENDAR_DAYS = 75
M15_LOOKBACK_CALENDAR_DAYS = 21

LEDGER_KINDS = (
    "asof",
    "candidate",
    "packet_sidecar",
    "scorecard",
    "oracle",
    "order",
    "trade",
    "event",
    "account",
    "missed",
    "winner",
    "loser",
    "exit",
    "rollup",
    "daily",
)


def _day_prefix(day: str) -> str:
    return f"ULTIMATE_EDGE_TRAIN_{day.replace('-', '')}"


def _ledger_path(day: str, kind: str) -> Path:
    kind_name = {
        "asof": "ASOF_MARKET_DATA_LEDGER",
        "candidate": "CANDIDATE_MICROSCOPE_LEDGER",
        "packet_sidecar": "PACKET_SIDECAR_LEDGER",
        "scorecard": "SELECTOR_SCHEDULER_SCORECARD",
        "oracle": "ORDERED_PATH_ORACLE_LEDGER",
        "order": "SIMULATED_ORDER_LEDGER",
        "trade": "SIMULATED_TRADE_LEDGER",
        "event": "SIMULATED_EVENT_LEDGER",
        "account": "SIMULATED_ACCOUNT_LEDGER",
        "missed": "MISSED_OPPORTUNITY_LEDGER",
        "winner": "WINNER_ANATOMY_LEDGER",
        "loser": "LOSER_ANATOMY_LEDGER",
        "exit": "EXIT_GEOMETRY_HARVEST_LEDGER",
        "rollup": "SYMBOL_SESSION_FRAMEWORK_POLICY_ROLLUP",
        "daily": "DAILY_MICROSCOPE_SUMMARY",
    }[kind]
    return LEDGER_DIR / f"{_day_prefix(day)}_{kind_name}.jsonl"


def _append_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    count = 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
            count += 1
    return count


def _write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    return _append_jsonl(path, rows)


def _completed_days() -> set[str]:
    done: set[str] = set()
    if not PROGRESS_PATH.exists():
        return done
    with PROGRESS_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("status") in {"completed", "verified_no_session_all_symbols"}:
                done.add(str(row.get("trading_day")))
    return done


def _weekdays(start_day: str, end_day: str) -> list[str]:
    start = date.fromisoformat(start_day)
    end = date.fromisoformat(end_day)
    days: list[str] = []
    cursor = start
    while cursor <= end:
        if cursor.weekday() < 5:
            days.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return days


def _install_day_relative_source_windows(day: str) -> dict[str, str]:
    """Override the engine's pinned lookback constants for one replay day."""

    day_date = date.fromisoformat(day)
    history_end = (day_date + timedelta(days=1)).isoformat()
    htf_start = (day_date - timedelta(days=HTF_LOOKBACK_CALENDAR_DAYS)).isoformat()
    m15_start = (day_date - timedelta(days=M15_LOOKBACK_CALENDAR_DAYS)).isoformat()

    def day_relative_history_end(days: Iterable[str]) -> str:
        latest = max(str(d)[:10] for d in days)
        return (date.fromisoformat(latest) + timedelta(days=1)).isoformat()

    original_resolve = tw.resolve_ftmo_history_source.__wrapped__ if hasattr(
        tw.resolve_ftmo_history_source, "__wrapped__"
    ) else tw.resolve_ftmo_history_source
    if not hasattr(tw, "_ultimate_edge_original_resolve_ftmo_history_source"):
        tw._ultimate_edge_original_resolve_ftmo_history_source = tw.resolve_ftmo_history_source

    base_resolve = tw._ultimate_edge_original_resolve_ftmo_history_source

    def day_relative_resolve(symbol: str, timeframe: str, *, min_total_rows: int,
                             start_utc: str | None = None, end_utc: str | None = None):
        return base_resolve(
            symbol,
            timeframe,
            min_total_rows=min_total_rows,
            start_utc=htf_start if start_utc in (None, tw.HTF_LOOKBACK_START) else start_utc,
            end_utc=history_end if end_utc in (None, tw.HTF_LOOKBACK_END) else end_utc,
        )

    tw.replay_history_end_utc_for_days = day_relative_history_end
    tw.resolve_ftmo_history_source = day_relative_resolve
    tw.M15_LIVE_LOOKBACK_START = m15_start
    _ = original_resolve  # keep a reference for debuggers

    return {
        "history_end_utc": history_end,
        "htf_lookback_start_utc": htf_start,
        "m15_lookback_start_utc": m15_start,
    }


def _num(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number != number or number in (float("inf"), float("-inf")):
        return default
    return number


def run_day(day: str, config: Mapping[str, Any]) -> dict[str, Any]:
    overrides = _install_day_relative_source_windows(day)
    tw.clear_replay_row_index_caches()
    try:
        source_package = tw.build_source_package((day,))
    except Exception as exc:
        # Transient I/O (e.g. ETIMEDOUT on cold file reads) must not kill the
        # batch; record and continue — the day re-runs on resume.
        progress = {
            "schema_version": f"{SCHEMA_PREFIX}_day_progress_v1",
            "route_id": ROUTE_ID,
            "trading_day": day,
            "status": "failed_source_package_error",
            "engine_error": f"{type(exc).__name__}: {exc}",
            "source_window_overrides": overrides,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        _append_jsonl(PROGRESS_PATH, [progress])
        return progress

    progress_base: dict[str, Any] = {
        "schema_version": f"{SCHEMA_PREFIX}_day_progress_v1",
        "route_id": ROUTE_ID,
        "phase": f"ultimate_edge_train_{day.replace('-', '')}",
        "partition_role": "TRAIN",
        "trading_day": day,
        "source_window_overrides": overrides,
        "stop_width_scale": _STOP_WIDTH_SCALE_ACTIVE,
        "source_strategy": SOURCE_STRATEGY,
        "one_shot_full_tick_load_used": False,
        "missing_symbols": source_package.get("missing_symbols"),
        "primary_hydration_complete": source_package.get("primary_hydration_complete"),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    sources = source_package.get("sources") or {}
    if not sources:
        progress = {**progress_base, "status": "not_run_primary_hydration_incomplete"}
        _append_jsonl(PROGRESS_PATH, [progress])
        return progress

    # Verified-no-session day (e.g. holiday): every symbol blocked only by
    # zero M15/M1 rows for the day itself -> record and move on.
    if source_package.get("primary_hydration_complete") is not True and not sources:
        progress = {**progress_base, "status": "not_run_primary_hydration_incomplete"}
        _append_jsonl(PROGRESS_PATH, [progress])
        return progress

    campaign = tw.CampaignConfig(
        name=f"ultimate_edge_train_{day.replace('-', '')}",
        phase=f"ultimate_edge_train_{day.replace('-', '')}",
        days=(day,),
        pending_expiry_minutes=tw.REPAIRED_PENDING_EXPIRY_MINUTES,
        use_repaired_pending_expiry=True,
        partial_be_runner=False,
    )
    broker = tw.SimulatedBroker()
    try:
        result = tw.run_campaign(
            campaign=campaign,
            config=config,
            sources=sources,
            broker=broker,
            starting_order_sequence=0,
        )
    except Exception as exc:
        # One bad day must never kill the batch: record an explicit failure
        # row (resumable; the day re-runs after repair) and continue.
        progress = {
            **progress_base,
            "status": "failed_engine_error",
            "engine_error": f"{type(exc).__name__}: {exc}",
        }
        _append_jsonl(PROGRESS_PATH, [progress])
        return progress
    ledgers = result["ledgers"]
    ledger_counts = {
        kind: _write_jsonl(_ledger_path(day, kind), ledgers.get(kind, []))
        for kind in LEDGER_KINDS
    }

    trades = ledgers.get("trade", [])
    net = sum(_num(t.get("net_proxy_r")) for t in trades)
    winners = sum(1 for t in trades if _num(t.get("net_proxy_r")) > 0)
    losses = sum(1 for t in trades if _num(t.get("net_proxy_r")) < 0)
    order_status = Counter(str(o.get("order_status") or "missing") for o in ledgers.get("order", []))

    progress = {
        **progress_base,
        "status": "completed",
        "ledger_counts": ledger_counts,
        "candidate_rows": ledger_counts.get("candidate", 0),
        "filled_trades": len(trades),
        "winners": winners,
        "losses": losses,
        "net_proxy_r": round(net, 8),
        "max_drawdown_pct": round(broker.account.max_drawdown_pct, 8),
        "order_status_counts": dict(sorted(order_status.items())),
        "missing_symbol_count": len(source_package.get("missing_symbols") or []),
    }
    _append_jsonl(PROGRESS_PATH, [progress])
    return progress


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-day", required=True)
    parser.add_argument("--end-day", required=True)
    parser.add_argument("--allow-validation", action="store_true")
    parser.add_argument("--max-days", type=int, default=0, help="0 = no cap.")
    parser.add_argument(
        "--stop-width-scale",
        type=float,
        default=1.0,
        help="Geometry experiment: scale total stop distance about entry (default 1.0 = production geometry).",
    )
    parser.add_argument(
        "--min-rr", type=float, default=None,
        help="Override risk.min_rr (candidate target_rr). Study says 2.0 beats native 1.5.",
    )
    parser.add_argument(
        "--enable-microstructure", action="store_true",
        help="Enable mined microstructure origin generators (absorption + vdelta divergence).",
    )
    parser.add_argument(
        "--enable-mined-origins", action="store_true",
        help="Enable mined origin families (range_extreme_reversion) in generation.",
    )
    parser.add_argument(
        "--m1-min-rows-per-day", type=int, default=None,
        help="Override engine M1 per-day floor (short-session CFDs need ~300).",
    )
    parser.add_argument(
        "--surface-file",
        default=None,
        help="JSON with expansion_symbols + ftmo_map; extends the engine surface at runtime (committed constants untouched).",
    )
    parser.add_argument(
        "--ledger-subdir",
        default=None,
        help="Write ledgers under ROUTE/<subdir> (REQUIRED when stop-width-scale != 1.0; keeps experiments out of train_ledgers).",
    )
    args = parser.parse_args(argv)
    if args.stop_width_scale != 1.0 and not args.ledger_subdir:
        parser.error("--ledger-subdir is required when --stop-width-scale != 1.0")
    if args.ledger_subdir:
        _set_ledger_subdir(args.ledger_subdir)

    registry_rows = load_partition_registry(REGISTRY_PATH)
    completed = _completed_days()
    planned = _weekdays(args.start_day, args.end_day)

    skipped: list[dict[str, str]] = []
    runnable: list[str] = []
    for day in planned:
        if day in completed:
            skipped.append({"trading_day": day, "reason": "already_completed"})
            continue
        role, partition_id = partition_role_for_day(day, registry_rows)
        if role == "SEALED":
            skipped.append({"trading_day": day, "reason": f"sealed_partition_refused:{partition_id}"})
            continue
        if role == "VALIDATION" and not args.allow_validation:
            skipped.append({"trading_day": day, "reason": f"validation_partition_requires_flag:{partition_id}"})
            continue
        runnable.append(day)
    if args.max_days > 0:
        runnable = runnable[: args.max_days]

    config = tw.load_config(REPO_ROOT / "config/agent_config.yaml")
    if args.m1_min_rows_per_day:
        tw.M1_MIN_ROWS_PER_DAY = int(args.m1_min_rows_per_day)
    if args.enable_mined_origins:
        runtime_cfg = config.setdefault("gtos_vnext_runtime", {})
        runtime_cfg["moonshot_mined_origin_families_enabled"] = True
    if args.enable_microstructure:
        runtime_cfg = config.setdefault("gtos_vnext_runtime", {})
        runtime_cfg["moonshot_microstructure_origins_enabled"] = True
    if args.min_rr:
        risk_cfg = config.setdefault("risk", {})
        risk_cfg["min_rr"] = float(args.min_rr)
    if args.surface_file:
        surface = json.loads(Path(args.surface_file).read_text())
        expansion = tuple(surface.get("expansion_symbols") or ())
        combined = tuple(tw.GTOS_24_SYMBOL_SURFACE) + tuple(
            s for s in expansion if s not in tw.GTOS_24_SYMBOL_SURFACE
        )
        tw.GTOS_PRE_HALT_LIVE_SURFACE = combined
        tw.GTOS_24_SYMBOL_SURFACE = combined
        tw.INCLUDED_SYMBOLS = combined
        tw.FTMO_SYMBOL_MAP.update(surface.get("ftmo_map") or {})
        print(f"[surface] expanded to {len(combined)} symbols", flush=True)
    if args.stop_width_scale != 1.0:
        runtime_cfg = config.setdefault("gtos_vnext_runtime", {})
        runtime_cfg["moonshot_broader_origin_stop_width_atr_scale"] = args.stop_width_scale
        globals()["_STOP_WIDTH_SCALE_ACTIVE"] = args.stop_width_scale
    results: list[dict[str, Any]] = []
    for day in runnable:
        print(f"[train-materialize] {day} ...", flush=True)
        progress = run_day(day, config)
        print(
            f"[train-materialize] {day} -> {progress.get('status')} "
            f"candidates={progress.get('candidate_rows', 0)} fills={progress.get('filled_trades', 0)} "
            f"net={progress.get('net_proxy_r', 0.0)}",
            flush=True,
        )
        results.append(progress)
        tw.clear_replay_row_index_caches()

    completed_now = sum(1 for r in results if r.get("status") == "completed")
    summary = {
        "schema_version": f"{SCHEMA_PREFIX}_materialization_summary_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "route_id": ROUTE_ID,
        "requested_range": [args.start_day, args.end_day],
        "planned_weekdays": len(planned),
        "skipped": skipped,
        "ran_days": len(results),
        "completed_days": completed_now,
        "incomplete_days": [r["trading_day"] for r in results if r.get("status") != "completed"],
        "source_strategy": SOURCE_STRATEGY,
        "no_live_broker_mutation": True,
        "no_remote_push": True,
        "no_paid_api": True,
    }
    tw.atomic_write_json(SUMMARY_PATH, summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "skipped"}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
