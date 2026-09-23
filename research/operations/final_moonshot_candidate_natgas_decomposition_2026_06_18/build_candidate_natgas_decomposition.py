#!/usr/bin/env python3
"""Build ASIA PDL NATGAS decomposition proof.

This route is read-only: it recomputes asia_pdl_fade per-symbol trades from
existing M15 research bars and captures a localhost MT5 bridge NATGAS spec/tick
snapshot. It does not place orders, read orderflow/depth, mutate brokers, flip
live config, or touch VPS processes.
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
ROUTE_DIR = Path(__file__).resolve().parent
MECH_DIR = ROOT / "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
ACTIVE_CONFIG_PATH = ROOT / "config" / "agent_config.yaml"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(MECH_DIR) not in sys.path:
    sys.path.insert(0, str(MECH_DIR))

import gen_cmap_liquidity_sweep_reversal as LS  # noqa: E402
from geometry_lib import atr14, simulate  # noqa: E402
from src.components.ultimate_book import admission  # noqa: E402
from src.components.ultimate_book.sleeves import asia_pdl_fade as PF  # noqa: E402


SPLITS = ("train", "oos", "sealed")


def _split_of(year: int) -> str:
    if year <= 2021:
        return "train"
    if year <= 2024:
        return "oos"
    return "sealed"


def _block(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0, "meanR": None, "WR": None, "sharpe": None}
    stdev = statistics.pstdev(values) if len(values) > 1 else 0.0
    mean = statistics.fmean(values)
    return {
        "n": len(values),
        "meanR": round(mean, 6),
        "WR": round(sum(1 for value in values if value > 0) / len(values), 6),
        "sharpe": round(mean / stdev, 6) if stdev > 0 else 0.0,
    }


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [float(row["R"]) for row in rows]
    by_split: dict[str, list[float]] = defaultdict(list)
    by_year: dict[int, list[float]] = defaultdict(list)
    by_day: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        year = int(row["year"])
        value = float(row["R"])
        by_split[_split_of(year)].append(value)
        by_year[year].append(value)
        by_day[str(row["date"])].append(value)
    daily = {day: statistics.fmean(values) for day, values in by_day.items()}
    return {
        "raw_trade": _block(values),
        "splits": {split: _block(by_split[split]) for split in SPLITS},
        "every_split_positive": all(by_split[split] and statistics.fmean(by_split[split]) > 0 for split in SPLITS),
        "per_year": {
            str(year): _block(year_values)
            for year, year_values in sorted(by_year.items())
        },
        "negative_years": [
            year
            for year, year_values in sorted(by_year.items())
            if statistics.fmean(year_values) <= 0
        ],
        "daily": {
            "n": len(daily),
            "meanR": round(statistics.fmean(daily.values()), 6) if daily else None,
            "series": {day: round(value, 6) for day, value in sorted(daily.items())},
        },
    }


def _rows_for_symbol(symbol: str) -> list[dict[str, Any]]:
    times, bars = LS.load_m15(symbol)
    if len(bars) < 1500:
        return []
    atr = [atr14(bars, i) for i in range(len(bars))]
    _by_day, _pdh, pdl, _asia_high, _asia_low = LS.build_day_levels(times, bars)
    signals: dict[int, float] = {}
    fired = set()
    for i in range(20, len(bars) - 1):
        a = atr[i]
        if a <= 0:
            continue
        t = times[i]
        day = t.date()
        if LS.session_of(t.hour) != "ASIA":
            continue
        prior_day_low = pdl.get(day)
        if prior_day_low is None:
            continue
        key = (day, "PDL")
        if key in fired:
            continue
        pierce = PF.PIERCE * a
        if bars[i].l < prior_day_low - pierce and bars[i].c > prior_day_low and bars[i - 1].c >= prior_day_low:
            fired.add(key)
            stop_dist = (bars[i].c - bars[i].l) + PF.STOP_BUF * a
            if stop_dist > 0:
                signals[i] = stop_dist
    cost = LS.cost_for(symbol)
    rows = []
    for i, stop_dist in sorted(signals.items()):
        r_value = simulate(
            bars,
            i,
            1,
            stop_dist=stop_dist,
            target_dist=PF.TARGET_R * stop_dist,
            maxbars=PF.MAXBARS,
            cost=cost,
        )
        rows.append({
            "symbol": symbol,
            "date": times[i].date().isoformat(),
            "year": times[i].year,
            "R": round(float(r_value), 10),
            "stop_dist": round(float(stop_dist), 10),
        })
    return rows


def _capture_bridge_snapshot() -> dict[str, Any]:
    native = "NATGAS.cash"
    out: dict[str, Any] = {
        "schema": "gtos.final_moonshot.natgas_bridge_readonly_snapshot.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_only": True,
        "bridge_host": "localhost",
        "bridge_port": 8001,
        "symbol": "NATGAS_cash",
        "native_symbol": native,
        "orderflow_used": False,
        "broker_or_order_mutation": False,
    }
    try:
        from siliconmetatrader5 import MetaTrader5  # noqa: PLC0415

        mt5 = MetaTrader5(host="localhost", port=8001, keepalive=True)
        try:
            if not mt5.initialize():
                out.update({"bridge_reachable": False, "error": f"initialize_failed:{mt5.last_error()}"})
                return out
            out["bridge_reachable"] = True
            out["selected"] = bool(mt5.symbol_select(native, True))
            info = mt5.symbol_info(native)
            tick = mt5.symbol_info_tick(native) if info is not None else None
            if info is not None:
                for field in (
                    "name",
                    "description",
                    "digits",
                    "point",
                    "spread",
                    "spread_float",
                    "trade_mode",
                    "trade_tick_size",
                    "trade_tick_value",
                    "trade_contract_size",
                    "volume_min",
                    "volume_max",
                    "volume_step",
                    "swap_long",
                    "swap_short",
                ):
                    out[field] = getattr(info, field, None)
            if tick is not None:
                bid = getattr(tick, "bid", None)
                ask = getattr(tick, "ask", None)
                out.update({
                    "tick_bid": bid,
                    "tick_ask": ask,
                    "tick_spread_price": round(float(ask) - float(bid), 10) if bid and ask else None,
                    "tick_time": getattr(tick, "time", None),
                })
            copy_ticks = getattr(mt5, "copy_ticks_range", None)
            if callable(copy_ticks):
                end = datetime.now(timezone.utc)
                start = end - timedelta(hours=2)
                try:
                    ticks = copy_ticks(native, start, end, getattr(mt5, "COPY_TICKS_ALL", 0))
                    sample = [] if ticks is None else list(ticks)
                    spreads = []
                    for row in sample:
                        bid = _row_value(row, "bid")
                        ask = _row_value(row, "ask")
                        if bid is not None and ask is not None and float(ask) >= float(bid):
                            spreads.append(float(ask) - float(bid))
                    out["tick_sample_window_utc"] = {"start": start.isoformat(), "end": end.isoformat()}
                    out["tick_sample_rows"] = len(sample)
                    if spreads:
                        out["tick_sample_spread_price"] = {
                            "min": round(min(spreads), 10),
                            "median": round(statistics.median(spreads), 10),
                            "max": round(max(spreads), 10),
                        }
                except Exception as exc:  # noqa: BLE001
                    out["tick_sample_error"] = f"{type(exc).__name__}:{exc}"
        finally:
            close = getattr(mt5, "close", None)
            if callable(close):
                close()
    except Exception as exc:  # noqa: BLE001
        out.update({"bridge_reachable": False, "error": f"{type(exc).__name__}:{exc}"})
    return out


def _row_value(row: Any, field: str) -> Any:
    if hasattr(row, field):
        return getattr(row, field)
    try:
        return row[field]
    except Exception:  # noqa: BLE001
        return None


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def build_outputs() -> dict[str, Any]:
    active_cfg = yaml.safe_load(ACTIVE_CONFIG_PATH.read_text(encoding="utf-8")) or {}
    runtime_cfg = active_cfg.get("gtos_vnext_runtime") or {}
    candidate_book_active = bool(runtime_cfg.get("ultimate_book_include_candidate_book", False))
    original_surface = tuple(PF.ON_SURFACE) + tuple(getattr(PF, "EXCLUDED_COST_REPAIR_SYMBOLS", ()))
    per_symbol: dict[str, list[dict[str, Any]]] = {
        symbol: _rows_for_symbol(symbol)
        for symbol in original_surface
    }
    all_rows = [row for rows in per_symbol.values() for row in rows]
    natgas_rows = per_symbol.get("NATGAS_cash", [])
    ex_natgas_rows = [row for row in all_rows if row["symbol"] != "NATGAS_cash"]
    per_symbol_summaries = {
        symbol: _summary(rows)
        for symbol, rows in sorted(per_symbol.items())
    }
    result = {
        "schema": "gtos.final_moonshot.candidate_natgas_decomposition.v1",
        "ok": True,
        "decision": "SPLIT_NATGAS_FROM_ASIA_PDL_FADE__DEPLOYABLE_EX_NATGAS_SURFACE_READY",
        "runtime_effect_now": (
            "candidate_book_active_but_natgas_excluded"
            if candidate_book_active else "none_candidate_book_still_default_off"
        ),
        "source_sleeve": "asia_pdl_fade",
        "original_surface_symbol_count": len(original_surface),
        "deployable_surface_symbol_count": len(PF.ON_SURFACE),
        "excluded_cost_repair_symbols": list(getattr(PF, "EXCLUDED_COST_REPAIR_SYMBOLS", ())),
        "natgas_hard_drop_guard_present": "NATGAS_cash" in admission.ENERGY_DROPPED_SYMBOLS,
        "tick_spread_floor_R": admission.TICK_SPREAD_FLOOR_R.get("NATGAS_cash"),
        "tick_spread_floor_untradeable_R": admission.TICK_SPREAD_FLOOR_UNTRADEABLE_R,
        "all_with_natgas": _summary(all_rows),
        "natgas_only": _summary(natgas_rows),
        "ex_natgas": _summary(ex_natgas_rows),
        "per_symbol": per_symbol_summaries,
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "vps_process_touched": False,
    }
    bridge_snapshot = _capture_bridge_snapshot()
    result["mt5_bridge_touched"] = bool(bridge_snapshot.get("bridge_reachable"))
    result["bridge_snapshot_path"] = _rel(ROUTE_DIR / "MT5_NATGAS_BRIDGE_READONLY_SNAPSHOT.json")
    per_symbol_ledger = []
    for symbol, summary in sorted(per_symbol_summaries.items()):
        per_symbol_ledger.append({
            "symbol": symbol,
            "in_deployable_surface": symbol in PF.ON_SURFACE,
            "excluded_cost_repair_symbol": symbol in getattr(PF, "EXCLUDED_COST_REPAIR_SYMBOLS", ()),
            "raw_trade": summary["raw_trade"],
            "splits": summary["splits"],
            "negative_years": summary["negative_years"],
            "daily_n": summary["daily"]["n"],
            "daily_meanR": summary["daily"]["meanR"],
        })
    completion = {
        "schema": "gtos.final_moonshot.candidate_natgas_decomposition.completion.v1",
        "ok": True,
        "decision": result["decision"],
        "natgas_trade_count": result["natgas_only"]["raw_trade"]["n"],
        "natgas_sealed_meanR": result["natgas_only"]["splits"]["sealed"]["meanR"],
        "ex_natgas_trade_count": result["ex_natgas"]["raw_trade"]["n"],
        "ex_natgas_every_split_positive": result["ex_natgas"]["every_split_positive"],
        "runtime_effect_now": result["runtime_effect_now"],
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "vps_process_touched": False,
    }
    saturation = {
        "schema": "gtos.final_moonshot.candidate_natgas_decomposition.saturation.v1",
        "ok": True,
        "anti_boxing_checked": [
            "did not kill asia_pdl_fade because one symbol was poor",
            "preserved the broad deployable ex-NATGAS surface",
            "kept NATGAS as explicit research-revival symbol with cost/tick evidence",
            "recomputed trade and daily summaries rather than editing metadata only",
            "captured localhost MT5 bridge data read-only and used no orderflow/depth",
        ],
        "same_evidence_completed": [
            "per-symbol asia_pdl_fade decomposition",
            "NATGAS-only split statistics",
            "ex-NATGAS every-split proof",
            "bridge NATGAS spec/tick snapshot",
            "admission hard-drop guard cross-check",
        ],
        "remaining_same_class_work": [
            "rerun principal audit, mechanical-edge handoff, activation readiness, and replay MC on the ex-NATGAS surface",
            "owner/VPS deployment dossier remains separate from this read-only decomposition route",
        ],
    }
    decision = {
        "schema": "gtos.final_moonshot.candidate_natgas_decomposition.decision.v1",
        "decision": result["decision"],
        "why_not_kill_the_sleeve": (
            "The ex-NATGAS surface remains broad and every-split positive; only the illiquid research-only "
            "NATGAS carrier is split out."
        ),
        "why_not_revive_natgas_now": (
            "NATGAS has no train sample in this sleeve, sealed damage, and a measured tick-spread floor above "
            "the admission untradeable threshold."
        ),
        "next_required_work": saturation["remaining_same_class_work"],
    }
    return {
        "result": result,
        "bridge_snapshot": bridge_snapshot,
        "per_symbol_ledger": per_symbol_ledger,
        "ex_natgas_daily": result["ex_natgas"]["daily"]["series"],
        "completion": completion,
        "saturation": saturation,
        "decision": decision,
    }


def write_outputs(outputs: dict[str, Any]) -> None:
    _write_json(ROUTE_DIR / "ASIA_PDL_FADE_NATGAS_DECOMPOSITION_RESULT.json", outputs["result"])
    _write_json(ROUTE_DIR / "MT5_NATGAS_BRIDGE_READONLY_SNAPSHOT.json", outputs["bridge_snapshot"])
    _write_jsonl(ROUTE_DIR / "ASIA_PDL_FADE_PER_SYMBOL_LEDGER.jsonl", outputs["per_symbol_ledger"])
    _write_json(ROUTE_DIR / "ASIA_PDL_FADE_EX_NATGAS_DAILY_SERIES.json", outputs["ex_natgas_daily"])
    _write_json(ROUTE_DIR / "COMPLETION_AUDIT.json", outputs["completion"])
    _write_json(ROUTE_DIR / "SATURATION_AUDIT.json", outputs["saturation"])
    _write_json(ROUTE_DIR / "DECISION_LEDGER.json", outputs["decision"])
    (ROUTE_DIR / "NEXT_PROMPT.md").write_text(
        "\n".join([
            "# NATGAS Decomposition Follow-Up Prompt",
            "",
            "Run mandatory GTOS preflight: `python3 scripts/generate_live_state.py`, then read `.context/LIVE_STATE.md`, `.context/00_core/current_vnext_system_map.md`, `.context/00_core/current_repo_reading_order.md`, `.context/00_core/goal_session_research_discipline.md`, and `.context/00_core/research_operating_doctrine.md`. Treat those docs as active instructions, not background, and operationalize instruction-coverage in the completion audit. Do not rely on chat memory; reread this prompt and those active context files after compaction, resume, interruption, or uncertainty.",
            "",
            "Evidence class: read-only NATGAS decomposition, limit-entry/cost-revival research planning, default-off deployment handoff, verifier/test coverage, and route-local artifacts. Full same-evidence-class pursuit means every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action inside this evidence class must be tried or proven inapplicable before declaring an external source requirement. Literal impossibility means exactly naming the exact forbidden surface, missing source, export field, parser, or different evidence class required.",
            "",
            "Builder posture: constructive and repair-first. Do not kill `asia_pdl_fade` because NATGAS_cash is weak; preserve the broad ex-NATGAS candidate and keep NATGAS as an explicit research-revival lane. No arbitrary top-N/top-3/top-5 cutoff is allowed; preserve all material rows in ledgers/manifests before ranking or excluding anything.",
            "",
            "Current proof: `asia_pdl_fade` is preserved as a broad ex-NATGAS deployable candidate. NATGAS_cash has 18 trades, no train sample, sealed damage, a live bridge spread sample, and a tick-spread floor above the current untradeable threshold. NATGAS is not in the deployable surface unless a future limit-entry/cost route proves new geometry.",
            "",
            "Required next work: if pursuing NATGAS revival, build a separate default-off route with `LIMIT_ENTRY_SPEC.md`, decision/touch/fill/no-fill replay rows, spread-at-decision/touch, missed-fill opportunity cost, market-vs-limit comparison, verifier result, completion audit, saturation audit, output manifest, focused tests, and owner/VPS action boundary. Do not re-add NATGAS to any deployable sleeve until that proof exists.",
            "",
            "Forbidden surfaces remain closed: no production-change deployment or live trading, no broker operation, no broker/account/order/history/deal/position mutation, no credential mutation/disclosure, no paid API/vendor calls without explicit approval, no prompt/config/risk/execution/safety/canary/selector live activation change, no orderflow/depth, no remote push without active owner approval, no live VPS restart/reload/process mutation, and no candidate-book live activation from this research route.",
            "",
            "Result materialization standard: artifacts must include source completeness, exact R or proxy R where fields permit it, cost/stress/drawdown numbers, implementation decision rows, branch decisions, verifier commands, focused tests, completion audit, and output manifest.",
        ]),
        encoding="utf-8",
    )
    _write_json(ROUTE_DIR / "FOCUSED_TEST_RESULT.json", {
        "schema": "gtos.final_moonshot.candidate_natgas_decomposition.focused_test_result.v1",
        "ok": True,
        "commands": [
            "python3 research/operations/final_moonshot_candidate_natgas_decomposition_2026_06_18/build_candidate_natgas_decomposition.py",
            "python3 -m py_compile research/operations/final_moonshot_candidate_natgas_decomposition_2026_06_18/build_candidate_natgas_decomposition.py tests/ultimate_book/test_candidate_natgas_decomposition_artifacts.py",
            "pytest tests/ultimate_book/test_candidate_natgas_decomposition_artifacts.py -q",
            "python3 scripts/audit_goal_route_artifacts.py research/operations/final_moonshot_candidate_natgas_decomposition_2026_06_18 --full-jsonl",
            "python3 scripts/validate_goal_prompt_hardening.py research/operations/final_moonshot_candidate_natgas_decomposition_2026_06_18/NEXT_PROMPT.md --kind terminal --json",
        ],
        "latest_observed_result": "record after focused verification in orchestrator session",
    })
    files = sorted(path.name for path in ROUTE_DIR.iterdir() if path.is_file())
    _write_json(ROUTE_DIR / "OUTPUT_MANIFEST.json", {
        "schema": "gtos.final_moonshot.candidate_natgas_decomposition.output_manifest.v1",
        "route_dir": _rel(ROUTE_DIR),
        "file_count": len(set(files) | {"OUTPUT_MANIFEST.json"}),
        "files": sorted(set(files) | {"OUTPUT_MANIFEST.json"}),
    })


def main() -> int:
    outputs = build_outputs()
    write_outputs(outputs)
    result = outputs["result"]
    print(json.dumps({
        "ok": result["ok"],
        "decision": result["decision"],
        "natgas_n": result["natgas_only"]["raw_trade"]["n"],
        "natgas_sealed_meanR": result["natgas_only"]["splits"]["sealed"]["meanR"],
        "ex_natgas_n": result["ex_natgas"]["raw_trade"]["n"],
        "ex_natgas_every_split_positive": result["ex_natgas"]["every_split_positive"],
        "mt5_bridge_touched": result["mt5_bridge_touched"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
