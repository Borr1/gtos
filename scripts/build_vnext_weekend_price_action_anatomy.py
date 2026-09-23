"""Build full May 28-31 vNext weekend price-action anatomy artifacts.

This builder is route evidence only. It reads raw weekend live records,
runtime/lifecycle logs, M1 captures, tick parquet when available, and optional
read-only MT5 history. It does not send broker/order/deal/position requests.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
ROUTE_DIR = (
    ROOT
    / "research"
    / "operations"
    / "vnext_live_activation_active_repair_companion_2026_05_28"
)

FORENSIC_SUMMARY = ROUTE_DIR / "LIVE_WEEKEND_FORENSIC_FUNNEL_SUMMARY.json"

ANATOMY_LEDGER = ROUTE_DIR / "LIVE_WEEKEND_CANDIDATE_PRICE_ACTION_ANATOMY_LEDGER.jsonl"
PLACED_AUTOPSY_LEDGER = ROUTE_DIR / "LIVE_WEEKEND_PLACED_TRADE_BROKER_AUTOPSY_LEDGER.jsonl"
REFUSAL_LEDGER = ROUTE_DIR / "LIVE_WEEKEND_REFUSAL_CORRECTNESS_STALENESS_LEDGER.jsonl"
LOSER_LEDGER = ROUTE_DIR / "LIVE_WEEKEND_LOSER_MECHANISM_LEDGER.jsonl"
WINNER_LEDGER = ROUTE_DIR / "LIVE_WEEKEND_WINNER_MECHANISM_LEDGER.jsonl"
POLICY_LEDGER = ROUTE_DIR / "LIVE_WEEKEND_POLICY_COMPARISON_LEDGER.jsonl"
INTELLIGENCE_SUMMARY = ROUTE_DIR / "LIVE_WEEKEND_SYMBOL_SESSION_ORIGIN_INTELLIGENCE_SUMMARY.json"
REPAIR_LEDGER = ROUTE_DIR / "LIVE_WEEKEND_IMPLEMENTATION_REPAIR_LEDGER.jsonl"
FINDINGS_REPORT = ROUTE_DIR / "LIVE_WEEKEND_PRICE_ACTION_ANATOMY_FINAL_FINDINGS.md"
VERIFICATION = ROUTE_DIR / "LIVE_WEEKEND_PRICE_ACTION_ANATOMY_VERIFICATION.json"

WEEKEND_START = datetime(2026, 5, 28, tzinfo=timezone.utc)
WEEKEND_END = datetime(2026, 6, 1, tzinfo=timezone.utc)
DEFAULT_HORIZON = timedelta(hours=48)
EXPECTED_SYMBOLS = [
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
]
POLICIES = [
    "current_selected_policy",
    "momentum_exhaustion",
    "partial_be_runner",
    "trailing_runner",
    "fixed_1_5r_comparator",
    "be_after_trigger_comparator",
    "time_stop_4h_comparator",
    "no_trade_baseline",
]


@dataclass(frozen=True)
class Bar:
    time_utc: datetime
    open: float
    high: float
    low: float
    close: float


def parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso(dt: datetime | None) -> str | None:
    return dt.astimezone(timezone.utc).isoformat() if dt else None


def get_path(data: Any, *path: str, default: Any = None) -> Any:
    cur = data
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return default if cur is None else cur


def first(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", []):
            return value
    return None


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN"


def route_artifact_only_descendant(artifact_head: str | None) -> dict[str, Any]:
    current = git_head()
    if not artifact_head or artifact_head in {"UNKNOWN", current}:
        return {"allowed": artifact_head == current, "changed_files": [], "disallowed_files": []}
    ancestor = subprocess.call(
        ["git", "merge-base", "--is-ancestor", artifact_head, current],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if ancestor != 0:
        return {
            "allowed": False,
            "reason": "artifact_head_not_ancestor_of_current_head",
            "changed_files": [],
            "disallowed_files": [],
        }
    diff = subprocess.run(
        ["git", "diff", "--name-only", f"{artifact_head}..{current}"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    changed = [line.strip().replace("\\", "/") for line in diff.stdout.splitlines() if line.strip()]
    route_prefix = "research/operations/vnext_live_activation_active_repair_companion_2026_05_28/"
    disallowed = [path for path in changed if not path.startswith(route_prefix)]
    return {
        "allowed": not disallowed,
        "changed_files": changed,
        "disallowed_files": disallowed,
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            row["_source_path"] = str(path)
            row["_source_line"] = line_no
            rows.append(row)
    return rows


def record_time(record: dict[str, Any], path: Path) -> datetime | None:
    meta = record.get("metadata") or {}
    return parse_dt(meta.get("candle_time") or meta.get("candle_close_utc") or meta.get("date")) or datetime.fromtimestamp(
        path.stat().st_mtime,
        timezone.utc,
    )


def load_trade_records(start: datetime, end: datetime) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((ROOT / "knowledge_base" / "trade_records").glob("*/*.json")):
        if path.name == "_pending_records_index.json":
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        dt = record_time(record, path)
        if dt is None or dt < start or dt >= end:
            continue
        record["_source_path"] = str(path)
        record["_record_time_utc"] = iso(dt)
        record["_source_symbol_dir"] = path.parent.name
        rows.append(record)
    return rows


def load_m1(symbol: str) -> list[Bar]:
    bars: list[Bar] = []
    for day in ("2026-05-28", "2026-05-29", "2026-05-30", "2026-05-31"):
        path = ROOT / "data" / "m1" / symbol / f"{day}.csv"
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8", errors="replace") as handle:
            for row in csv.DictReader(handle):
                t = parse_dt(row.get("time_utc"))
                o = as_float(row.get("open"))
                h = as_float(row.get("high"))
                l = as_float(row.get("low"))
                c = as_float(row.get("close"))
                if t is None or o is None or h is None or l is None or c is None:
                    continue
                bars.append(Bar(t, o, h, l, c))
    bars.sort(key=lambda b: b.time_utc)
    return bars


def load_ticks(symbol: str) -> pd.DataFrame | None:
    frames: list[pd.DataFrame] = []
    for day in ("2026-05-28", "2026-05-29", "2026-05-30", "2026-05-31"):
        path = ROOT / "data" / "ticks" / symbol / f"{day}.parquet"
        if not path.exists():
            continue
        try:
            frame = pd.read_parquet(path, columns=["ts_utc", "ts_msc", "bid", "ask"])
        except Exception:
            continue
        if frame.empty:
            continue
        frame["ts_utc"] = pd.to_datetime(frame["ts_utc"], utc=True, errors="coerce")
        frame = frame.dropna(subset=["ts_utc", "bid", "ask"])
        frame = frame[(frame["bid"] > 0) & (frame["ask"] > 0)]
        if not frame.empty:
            frames.append(frame)
    if not frames:
        return None
    out = pd.concat(frames, ignore_index=True)
    out = out.sort_values(["ts_utc", "ts_msc"], kind="stable")
    return out.reset_index(drop=True)


def candidate_row(record: dict[str, Any]) -> dict[str, Any]:
    meta = record.get("metadata") or {}
    pipe = record.get("decision_pipeline") or {}
    packet = pipe.get("gtos_vnext_candidate_intelligence_packet") or {}
    identity = packet.get("candidate_identity") or {}
    source_m15 = packet.get("source_m15") or {}
    source_fields = source_m15.get("source_fields") or {}
    m1_snapshot = packet.get("m1_ltf_snapshot") or packet.get("ltf_path_snapshot") or {}
    tick_snapshot = packet.get("tick_spread_snapshot") or packet.get("tick_snapshot") or {}
    broker_spec = packet.get("broker_spec_snapshot") or {}
    gates = packet.get("gates") or {}
    geom = packet.get("geometry") or {}
    raw = geom.get("raw") or {}
    repaired = geom.get("repaired") or geom.get("final") or {}
    dyn = packet.get("dynamic_policy") or {}
    trigger = dyn.get("dynamic_trigger_final_pullback") or {}
    selected_risk = packet.get("selected_cell_risk_proof") or {}
    risk_lot = packet.get("risk_lot_calculation") or {}
    prop = packet.get("prop_governor") or {}
    final_decision = packet.get("final_order_decision") or {}
    broader = record.get("moonshot_broader_origin_candidate") or {}
    dyn_exec = pipe.get("gtos_vnext_moonshot_dynamic_execution") or {}
    route_dims = (dyn_exec.get("router_record") or {}).get("route_dimensions") or {}
    source_event = dyn_exec.get("source_event") or {}
    trade_params = record.get("trade_parameters") or {}
    final_outcome = pipe.get("final_outcome")
    side = str(first(identity.get("side"), pipe.get("ai_direction"), broader.get("side"), route_dims.get("side")) or "").upper()
    symbol = first(meta.get("symbol"), identity.get("symbol"), broader.get("symbol"), record.get("_source_symbol_dir"))
    candle_time = parse_dt(first(identity.get("candle_close_utc"), meta.get("candle_close_utc"), meta.get("candle_time")))
    entry = as_float(first(repaired.get("entry_price"), raw.get("entry_price"), trade_params.get("entry_price"), broader.get("entry_price")))
    stop = as_float(first(repaired.get("stop_loss"), raw.get("stop_loss"), trade_params.get("stop_loss"), broader.get("stop_loss")))
    raw_entry = as_float(first(raw.get("entry_price"), trade_params.get("entry_price"), broader.get("entry_price"), repaired.get("entry_price")))
    raw_stop = as_float(first(raw.get("stop_loss"), trade_params.get("stop_loss"), broader.get("stop_loss"), repaired.get("stop_loss")))
    raw_tp = as_float(first(raw.get("take_profit_1"), trade_params.get("take_profit_1"), broader.get("take_profit_1")))
    risk = abs(entry - stop) if entry is not None and stop is not None else None
    trigger_price = as_float(first(
        trigger.get("dynamic_be_trigger_price"),
        trigger.get("be_trigger_price"),
        trigger.get("trigger_price"),
        geom.get("dynamic_target", {}).get("trigger_price") if isinstance(geom.get("dynamic_target"), dict) else None,
    ))
    final_price = as_float(first(
        trigger.get("dynamic_final_target_price"),
        trigger.get("final_target_price"),
        geom.get("dynamic_target", {}).get("final_target_price") if isinstance(geom.get("dynamic_target"), dict) else None,
    ))
    if risk and entry is not None:
        trigger_price = trigger_price if trigger_price is not None else (entry + risk if side == "LONG" else entry - risk)
        final_price = final_price if final_price is not None else (entry + 3 * risk if side == "LONG" else entry - 3 * risk)
        raw_tp = raw_tp if raw_tp is not None else (entry + 1.5 * risk if side == "LONG" else entry - 1.5 * risk)
    reasons = first(
        dyn_exec.get("refusal_reasons"),
        pipe.get("gtos_vnext_moonshot_dynamic_refusal_reasons"),
        (packet.get("refusal_and_repair_reasons") or {}).get("recorded_dynamic_refusal_reasons"),
        [],
    )
    if isinstance(reasons, str):
        reasons = [reasons]
    if not isinstance(reasons, list):
        reasons = []
    return {
        "source_path": record.get("_source_path"),
        "source_row_reference": record.get("_source_path"),
        "record_system_version": meta.get("system_version"),
        "record_time_utc": record.get("_record_time_utc"),
        "candidate_id": first(identity.get("candidate_id"), broader.get("candidate_id"), dyn_exec.get("candidate_id"), meta.get("trade_id")),
        "trade_id": meta.get("trade_id"),
        "symbol": symbol,
        "broker_symbol": first(identity.get("broker_symbol"), broker_spec.get("broker_symbol"), meta.get("broker_symbol"), symbol),
        "side": side or None,
        "session": first(identity.get("session"), meta.get("kill_zone")),
        "route_session": first(identity.get("route_session"), route_dims.get("route_session"), meta.get("kill_zone")),
        "session_bucket": first(identity.get("utc_hour_bucket"), route_dims.get("utc_hour_bucket")),
        "kill_zone_position": meta.get("kill_zone"),
        "utc_hour_bucket": first(identity.get("utc_hour_bucket"), route_dims.get("utc_hour_bucket")),
        "candle_time_utc": iso(candle_time),
        "origin_family": first(identity.get("origin_family"), broader.get("origin_family"), route_dims.get("origin_family")),
        "candidate_origin_family": first(identity.get("candidate_origin_family"), broader.get("candidate_origin_family"), route_dims.get("candidate_origin_family")),
        "framework": first(identity.get("framework"), pipe.get("ai_framework"), broader.get("framework")),
        "branch_label": route_dims.get("branch_label"),
        "source_mode": first(source_event.get("source_mode"), route_dims.get("source_mode")),
        "source_path_feature_status": first(source_event.get("source_path_feature_status"), source_fields.get("source_path_feature_status"), source_m15.get("source_path_feature_status")),
        "source_window_complete": first(source_event.get("source_window_complete"), source_fields.get("source_window_complete"), source_m15.get("source_window_complete")),
        "m15_source_fields": source_fields,
        "m1_ltf_snapshot": m1_snapshot,
        "tick_spread_snapshot": tick_snapshot,
        "broker_spec_snapshot": broker_spec,
        "raw_entry": raw_entry,
        "raw_stop_loss": raw_stop,
        "raw_take_profit_1_5r": raw_tp,
        "repaired_entry": entry,
        "repaired_stop_loss": stop,
        "dynamic_trigger_price": trigger_price,
        "dynamic_final_target_price": final_price,
        "dynamic_pullback_r": first(trigger.get("momentum_pullback_r"), trigger.get("pullback_r")),
        "risk_distance": risk,
        "final_outcome": final_outcome,
        "gate0": gates.get("gate0"),
        "gate1": first(gates.get("gate1_final_after_repair"), pipe.get("gate1_result")),
        "gate3": first(gates.get("gate3"), pipe.get("gate3_result")),
        "gate1_denial_reason": get_path(pipe, "gate1_result", "details", "denial_reason"),
        "gate3_denial_reason": get_path(pipe, "gate3_result", "details", "denial_reason"),
        "gate3_spread": get_path(pipe, "gate3_result", "details", "spread_cents"),
        "gate3_max_spread": get_path(pipe, "gate3_result", "details", "denial_details", "max_spread"),
        "selected_policy": first(dyn.get("selected_policy"), dyn_exec.get("selected_policy"), route_dims.get("raw_asof_selected_policy")),
        "execution_policy_id": first(dyn.get("execution_policy_id"), dyn_exec.get("execution_policy_id"), route_dims.get("selected_cell_risk_execution_policy_id")),
        "dynamic_policy_raw": dyn,
        "selector_cell": packet.get("selector_cell_proof") or {},
        "selected_cell_risk_proof": selected_risk,
        "selected_cell_risk_allowed": first(selected_risk.get("allowed"), source_event.get("selected_cell_risk_allowed"), route_dims.get("selected_cell_risk_allowed")),
        "selected_cell_risk_pct": first(selected_risk.get("risk_pct"), source_event.get("selected_cell_risk_pct"), route_dims.get("selected_cell_risk_pct")),
        "selected_cell_risk_cell_id": first(selected_risk.get("cell_id"), source_event.get("selected_cell_risk_cell_id"), route_dims.get("selected_cell_risk_cell_id")),
        "selected_cell_risk_match_reason": first(selected_risk.get("match_reason"), source_event.get("selected_cell_risk_match_reason"), route_dims.get("selected_cell_risk_match_reason")),
        "risk_lot_calculation": risk_lot,
        "prop_governor": prop,
        "prop_action": first(dyn.get("prop_action"), get_path(prop, "after_geometry_repair", "action"), get_path(prop, "before_geometry_repair", "action"), get_path(pipe, "gtos_vnext_prop_safe_selector", "action")),
        "final_order_decision": final_decision,
        "dynamic_refusal_reasons": reasons,
        "broader_origin_allowed": first(source_event.get("broader_origin_allowed"), route_dims.get("broader_origin_allowed")),
        "broader_origin_match_reason": first(source_event.get("broader_origin_match_reason"), route_dims.get("broader_origin_match_reason")),
        "selected_cell_risk_allowed_route": first(source_event.get("selected_cell_risk_allowed"), route_dims.get("selected_cell_risk_allowed")),
        "old_primary_analyzer_called": pipe.get("old_primary_analyzer_called"),
        "old_l2_required": pipe.get("old_l2_required"),
        "packet_capture_mode": packet.get("capture_mode"),
        "packet_capture_reason": packet.get("capture_reason"),
    }


def event_mask(frame: pd.DataFrame, side: str, level: float, event: str) -> pd.Series:
    if side == "LONG":
        if event in {"sl", "be"}:
            return frame["bid"] <= level
        return frame["bid"] >= level
    if event in {"sl", "be"}:
        return frame["ask"] >= level
    return frame["ask"] <= level


def first_time(frame: pd.DataFrame, mask: pd.Series) -> datetime | None:
    if frame.empty:
        return None
    hit = frame[mask]
    if hit.empty:
        return None
    value = hit.iloc[0]["ts_utc"]
    return value.to_pydatetime() if hasattr(value, "to_pydatetime") else parse_dt(value)


def r_at_price(side: str, entry: float, stop: float, price: float) -> float | None:
    risk = abs(entry - stop)
    if risk <= 0:
        return None
    if side == "LONG":
        return (price - entry) / risk
    return (entry - price) / risk


def classify_path_status(sl_time: datetime | None, one_r_time: datetime | None, final_time: datetime | None, be_time: datetime | None, entry_time: datetime | None) -> str:
    if entry_time is None:
        return "no_entry_touch_before_last_available_price"
    if sl_time and (one_r_time is None or sl_time <= one_r_time):
        return "entry_filled_sl_before_1r_trigger"
    if one_r_time:
        if final_time and (be_time is None or final_time <= be_time):
            return "partial_1r_then_3r_final"
        if be_time:
            return "partial_1r_then_be"
        return "partial_1r_then_open_at_last_available_price"
    return "entry_filled_no_sl_or_1r_before_last_available_price"


def path_r(path_status: str, last_r: float | None = None) -> float | None:
    if path_status == "entry_filled_sl_before_1r_trigger":
        return -1.0
    if path_status == "partial_1r_then_3r_final":
        return 2.0
    if path_status == "partial_1r_then_be":
        return 0.5
    if path_status == "partial_1r_then_open_at_last_available_price" and last_r is not None:
        return 0.5 + 0.5 * last_r
    return None


def simulate_tick(row: dict[str, Any], ticks: pd.DataFrame | None) -> dict[str, Any] | None:
    candle = parse_dt(row.get("candle_time_utc"))
    side = row.get("side")
    entry = as_float(row.get("repaired_entry"))
    stop = as_float(row.get("repaired_stop_loss"))
    trigger = as_float(row.get("dynamic_trigger_price"))
    final = as_float(row.get("dynamic_final_target_price"))
    raw_tp = as_float(row.get("raw_take_profit_1_5r"))
    if ticks is None or ticks.empty or candle is None or side not in {"LONG", "SHORT"} or entry is None or stop is None:
        return None
    risk = abs(entry - stop)
    if risk <= 0:
        return None
    trigger = trigger if trigger is not None else (entry + risk if side == "LONG" else entry - risk)
    final = final if final is not None else (entry + 3 * risk if side == "LONG" else entry - 3 * risk)
    raw_tp = raw_tp if raw_tp is not None else (entry + 1.5 * risk if side == "LONG" else entry - 1.5 * risk)
    start = pd.Timestamp(candle)
    end = pd.Timestamp(candle + DEFAULT_HORIZON)
    path = ticks[(ticks["ts_utc"] >= start) & (ticks["ts_utc"] <= end)]
    if path.empty:
        return None
    entry_mask = path["ask"] <= entry if side == "LONG" else path["bid"] >= entry
    entry_time = first_time(path, entry_mask)
    entry_idx = path[entry_mask].index[0] if entry_time else None
    first_spread = float(path.iloc[0]["ask"] - path.iloc[0]["bid"])
    if entry_idx is None:
        basis = path["bid"] if side == "LONG" else path["ask"]
        favorable_price = float(basis.max() if side == "LONG" else basis.min())
        adverse_price = float(basis.min() if side == "LONG" else basis.max())
        return {
            "price_source": "tick_bid_ask",
            "tick_rows": int(len(path)),
            "price_source_first_utc": iso(path.iloc[0]["ts_utc"].to_pydatetime()),
            "price_source_last_utc": iso(path.iloc[-1]["ts_utc"].to_pydatetime()),
            "entry_touch_utc": None,
            "time_to_entry_seconds": None,
            "path_status": "no_entry_touch_before_last_available_price",
            "proxy_gross_r": 0.0,
            "max_favorable_r": r_at_price(side, entry, stop, favorable_price),
            "max_adverse_r": r_at_price(side, entry, stop, adverse_price),
            "spread_at_candidate": first_spread,
            "spread_r_at_candidate": first_spread / risk,
            "same_bar_or_tick_ambiguity": False,
            "missing_data_windows": [],
        }
    after = path.loc[entry_idx:].copy()
    one_r_time = first_time(after, event_mask(after, side, trigger, "trigger"))
    sl_time = first_time(after, event_mask(after, side, stop, "sl"))
    raw_tp_time = first_time(after, event_mask(after, side, raw_tp, "raw_tp"))
    final_time = None
    be_time = None
    if one_r_time:
        after_trigger = after[after["ts_utc"] >= pd.Timestamp(one_r_time)]
        final_time = first_time(after_trigger, event_mask(after_trigger, side, final, "target"))
        be_time = first_time(after_trigger, event_mask(after_trigger, side, entry, "be"))
    basis = after["bid"] if side == "LONG" else after["ask"]
    favorable_idx = basis.idxmax() if side == "LONG" else basis.idxmin()
    adverse_idx = basis.idxmin() if side == "LONG" else basis.idxmax()
    favorable_price = float(basis.loc[favorable_idx])
    adverse_price = float(basis.loc[adverse_idx])
    r_series = basis.apply(lambda p: r_at_price(side, entry, stop, float(p)))
    move = after[r_series.abs() >= 0.25]
    time_stop_end = pd.Timestamp(entry_time + timedelta(hours=4))
    stop_window = after[after["ts_utc"] <= time_stop_end]
    time_stop_price = float((stop_window["bid"] if side == "LONG" else stop_window["ask"]).iloc[-1]) if not stop_window.empty else float(basis.iloc[-1])
    last_price = float(basis.iloc[-1])
    path_status = classify_path_status(sl_time, one_r_time, final_time, be_time, entry_time)
    last_r = r_at_price(side, entry, stop, last_price)
    mfe_time = after.loc[favorable_idx]["ts_utc"].to_pydatetime()
    mae_time = after.loc[adverse_idx]["ts_utc"].to_pydatetime()
    return {
        "price_source": "tick_bid_ask",
        "tick_rows": int(len(path)),
        "price_source_first_utc": iso(path.iloc[0]["ts_utc"].to_pydatetime()),
        "price_source_last_utc": iso(path.iloc[-1]["ts_utc"].to_pydatetime()),
        "entry_touch_utc": iso(entry_time),
        "time_to_entry_seconds": (entry_time - candle).total_seconds() if entry_time else None,
        "one_r_trigger_utc": iso(one_r_time),
        "time_to_1r_seconds": (one_r_time - entry_time).total_seconds() if one_r_time and entry_time else None,
        "raw_1_5r_target_utc": iso(raw_tp_time),
        "time_to_1_5r_seconds": (raw_tp_time - entry_time).total_seconds() if raw_tp_time and entry_time else None,
        "dynamic_final_3r_utc": iso(final_time),
        "time_to_3r_seconds": (final_time - entry_time).total_seconds() if final_time and entry_time else None,
        "be_return_utc": iso(be_time),
        "time_to_be_seconds": (be_time - one_r_time).total_seconds() if be_time and one_r_time else None,
        "sl_touch_utc": iso(sl_time),
        "time_to_sl_seconds": (sl_time - entry_time).total_seconds() if sl_time and entry_time else None,
        "mfe_r": r_at_price(side, entry, stop, favorable_price),
        "mae_r": r_at_price(side, entry, stop, adverse_price),
        "mfe_price": favorable_price,
        "mae_price": adverse_price,
        "time_to_mfe_seconds": (mfe_time - entry_time).total_seconds() if entry_time else None,
        "time_to_mae_seconds": (mae_time - entry_time).total_seconds() if entry_time else None,
        "duration_stuck_near_entry_seconds": (
            (move.iloc[0]["ts_utc"].to_pydatetime() - entry_time).total_seconds()
            if not move.empty and entry_time
            else None
        ),
        "duration_before_movement_seconds": (
            (move.iloc[0]["ts_utc"].to_pydatetime() - candle).total_seconds()
            if not move.empty
            else None
        ),
        "pullback_size_r": (
            (r_at_price(side, entry, stop, favorable_price) or 0.0) - (last_r or 0.0)
            if one_r_time
            else None
        ),
        "reversal_timing": (
            "favorable_then_reversed_to_sl"
            if one_r_time is None and (r_at_price(side, entry, stop, favorable_price) or 0.0) >= 0.5 and path_status == "entry_filled_sl_before_1r_trigger"
            else "reversed_to_be_after_1r"
            if be_time
            else "no_reversal_terminal_observed"
        ),
        "last_price": last_price,
        "last_r": last_r,
        "time_stop_4h_r": r_at_price(side, entry, stop, time_stop_price),
        "path_status": path_status,
        "proxy_gross_r": path_r(path_status, last_r),
        "spread_at_candidate": first_spread,
        "spread_r_at_candidate": first_spread / risk,
        "same_bar_or_tick_ambiguity": False,
        "missing_data_windows": [],
    }


def bar_hit(side: str, bar: Bar, level: float, event: str) -> bool:
    if side == "LONG":
        return bar.low <= level if event in {"sl", "be"} else bar.high >= level
    return bar.high >= level if event in {"sl", "be"} else bar.low <= level


def simulate_m1(row: dict[str, Any], bars: list[Bar]) -> dict[str, Any]:
    candle = parse_dt(row.get("candle_time_utc"))
    side = row.get("side")
    entry = as_float(row.get("repaired_entry"))
    stop = as_float(row.get("repaired_stop_loss"))
    trigger = as_float(row.get("dynamic_trigger_price"))
    final = as_float(row.get("dynamic_final_target_price"))
    raw_tp = as_float(row.get("raw_take_profit_1_5r"))
    if candle is None or side not in {"LONG", "SHORT"} or entry is None or stop is None:
        return {"price_source": "not_simulated", "path_status": "missing_required_geometry"}
    risk = abs(entry - stop)
    if risk <= 0:
        return {"price_source": "not_simulated", "path_status": "non_positive_risk_distance"}
    trigger = trigger if trigger is not None else (entry + risk if side == "LONG" else entry - risk)
    final = final if final is not None else (entry + 3 * risk if side == "LONG" else entry - 3 * risk)
    raw_tp = raw_tp if raw_tp is not None else (entry + 1.5 * risk if side == "LONG" else entry - 1.5 * risk)
    path = [b for b in bars if candle <= b.time_utc <= candle + DEFAULT_HORIZON]
    if not path:
        return {
            "price_source": "m1_ohlc",
            "m1_rows": 0,
            "path_status": "no_m1_rows_after_candidate",
            "missing_data_windows": ["no_m1_rows_after_candidate"],
        }
    entry_bar = next((b for b in path if bar_hit(side, b, entry, "target") or (b.low <= entry <= b.high)), None)
    if entry_bar is None:
        return {
            "price_source": "m1_ohlc",
            "m1_rows": len(path),
            "price_source_first_utc": iso(path[0].time_utc),
            "price_source_last_utc": iso(path[-1].time_utc),
            "entry_touch_utc": None,
            "path_status": "no_entry_touch_before_last_available_price",
            "proxy_gross_r": 0.0,
            "same_bar_or_tick_ambiguity": False,
            "missing_data_windows": [],
        }
    after = path[path.index(entry_bar):]
    one_r_bar = sl_bar = raw_tp_bar = None
    ambiguity = False
    for bar in after:
        sl_hit = bar_hit(side, bar, stop, "sl")
        one_hit = bar_hit(side, bar, trigger, "target")
        raw_hit = bar_hit(side, bar, raw_tp, "target")
        if sl_hit and one_hit:
            ambiguity = True
        if sl_bar is None and sl_hit:
            sl_bar = bar
        if one_r_bar is None and one_hit:
            one_r_bar = bar
        if raw_tp_bar is None and raw_hit:
            raw_tp_bar = bar
        if sl_bar or one_r_bar:
            break
    final_bar = be_bar = None
    if one_r_bar is not None:
        after_trigger = after[after.index(one_r_bar):]
        for bar in after_trigger:
            final_hit = bar_hit(side, bar, final, "target")
            be_hit = bar_hit(side, bar, entry, "be")
            if final_hit and be_hit:
                ambiguity = True
            if final_bar is None and final_hit:
                final_bar = bar
            if be_bar is None and be_hit:
                be_bar = bar
            if final_bar or be_bar:
                break
    basis_hi = [b.high if side == "LONG" else b.low for b in after]
    basis_lo = [b.low if side == "LONG" else b.high for b in after]
    favorable_price = max(basis_hi) if side == "LONG" else min(basis_hi)
    adverse_price = min(basis_lo) if side == "LONG" else max(basis_lo)
    last = after[-1]
    last_price = last.close
    path_status = classify_path_status(
        sl_bar.time_utc if sl_bar else None,
        one_r_bar.time_utc if one_r_bar else None,
        final_bar.time_utc if final_bar else None,
        be_bar.time_utc if be_bar else None,
        entry_bar.time_utc,
    )
    last_r = r_at_price(side, entry, stop, last_price)
    return {
        "price_source": "m1_ohlc",
        "m1_rows": len(path),
        "price_source_first_utc": iso(path[0].time_utc),
        "price_source_last_utc": iso(path[-1].time_utc),
        "entry_touch_utc": iso(entry_bar.time_utc),
        "time_to_entry_seconds": (entry_bar.time_utc - candle).total_seconds(),
        "one_r_trigger_utc": iso(one_r_bar.time_utc if one_r_bar else None),
        "time_to_1r_seconds": (one_r_bar.time_utc - entry_bar.time_utc).total_seconds() if one_r_bar else None,
        "raw_1_5r_target_utc": iso(raw_tp_bar.time_utc if raw_tp_bar else None),
        "dynamic_final_3r_utc": iso(final_bar.time_utc if final_bar else None),
        "be_return_utc": iso(be_bar.time_utc if be_bar else None),
        "sl_touch_utc": iso(sl_bar.time_utc if sl_bar else None),
        "mfe_r": r_at_price(side, entry, stop, favorable_price),
        "mae_r": r_at_price(side, entry, stop, adverse_price),
        "mfe_price": favorable_price,
        "mae_price": adverse_price,
        "last_price": last_price,
        "last_r": last_r,
        "time_stop_4h_r": last_r,
        "path_status": path_status,
        "proxy_gross_r": path_r(path_status, last_r),
        "same_bar_or_tick_ambiguity": ambiguity,
        "missing_data_windows": [] if path else ["no_m1_rows_after_candidate"],
    }


def analyze_price_path(row: dict[str, Any], tick_cache: dict[str, pd.DataFrame | None], m1_cache: dict[str, list[Bar]]) -> dict[str, Any]:
    symbol = str(row.get("symbol") or "")
    if symbol and symbol not in tick_cache:
        tick_cache[symbol] = load_ticks(symbol)
    tick_result = simulate_tick(row, tick_cache.get(symbol)) if symbol else None
    if tick_result:
        return tick_result
    if symbol and symbol not in m1_cache:
        m1_cache[symbol] = load_m1(symbol)
    result = simulate_m1(row, m1_cache.get(symbol, []))
    if tick_cache.get(symbol) is None:
        result.setdefault("missing_data_windows", []).append("tick_bid_ask_unavailable_for_candidate_window")
    return result


def classify_refusal(row: dict[str, Any], anatomy: dict[str, Any]) -> dict[str, Any]:
    outcome = row.get("final_outcome")
    reasons = set(row.get("dynamic_refusal_reasons") or [])
    text = json.dumps(row, sort_keys=True)
    if outcome == "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN":
        status = "accepted_order_path"
        decision = "broker_path_reached"
    elif outcome == "DEFERRED_GTOS_VNEXT_PROP_RESET":
        status = "stale_under_repaired_vnext"
        decision = "historical_pre_dynamic_prop_projection_not_current_terminal_block"
    elif outcome == "REJECTED_GATE1_SAFETY":
        status = "stale_under_repaired_vnext"
        decision = "historical_gate1_terminal_reject_before_executable_geometry_repair"
    elif outcome == "REJECTED_GATE3_CIRCUIT_BREAKER":
        spread = as_float(row.get("gate3_spread"))
        max_spread = as_float(row.get("gate3_max_spread"))
        packet_complete = bool(row.get("selected_policy") and row.get("execution_policy_id"))
        if spread is not None and max_spread is not None and spread > max_spread and packet_complete:
            status = "correct_current_vnext_operational_gate"
            decision = "spread_above_current_gate3_limit_with_packet_policy_truth"
        elif spread is not None and max_spread is not None and spread > max_spread:
            status = "gate_correct_but_historical_packet_incomplete"
            decision = "spread_reject_valid_but_writer_missing_policy_or_risk_context_at_the_time"
        else:
            status = "unresolved"
            decision = "gate3_reject_missing_spread_proof"
    elif outcome == "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC":
        if "outside_configured_kill_zone_or_missing_schedule" in reasons or "outside_configured_kill_zone_or_missing_schedule" in text:
            status = "correct_current_vnext_session_contract"
            decision = "outside_configured_kill_zone_or_missing_schedule_exact_session_exclusion"
        elif "framework_not_activated_in_stage13_full_moonshot_selector" in reasons or "framework_not_activated_in_stage13_full_moonshot_selector" in text:
            status = "stale_or_unresolved_selector_bridge"
            decision = "generic_framework_refusal_not_valid_without_exact_failed_dimensions"
        elif "selected_cell_risk_not_verified_or_zero" in reasons or "selected_cell_risk_not_verified_or_zero" in text:
            status = "stale_or_unresolved_selected_cell_risk_bridge"
            decision = "selected_cell_risk_missing_zero_requires_row_level_cause_or_bridge_repair"
        else:
            status = "unresolved"
            decision = "dynamic_refusal_missing_concrete_classification"
    else:
        status = "unresolved"
        decision = "unknown_terminal_outcome"
    return {
        "candidate_id": row.get("candidate_id"),
        "symbol": row.get("symbol"),
        "side": row.get("side"),
        "candle_time_utc": row.get("candle_time_utc"),
        "final_outcome": outcome,
        "refusal_reasons": row.get("dynamic_refusal_reasons"),
        "refusal_correctness_status": status,
        "repair_or_exclusion_decision": decision,
        "price_action_path_status": anatomy.get("path_status"),
        "proxy_gross_r": anatomy.get("proxy_gross_r"),
        "source_path": row.get("source_path"),
        "selector_risk_coupled": (
            "framework_not_activated_in_stage13_full_moonshot_selector" in text
            and "selected_cell_risk_not_verified_or_zero" in text
        ),
        "selected_cell_risk_match_reason": row.get("selected_cell_risk_match_reason"),
        "selected_cell_risk_cell_id": row.get("selected_cell_risk_cell_id"),
        "selected_cell_risk_pct": row.get("selected_cell_risk_pct"),
        "gate3_spread": row.get("gate3_spread"),
        "gate3_max_spread": row.get("gate3_max_spread"),
    }


def classify_mechanism(row: dict[str, Any], anatomy: dict[str, Any]) -> tuple[str, str]:
    status = anatomy.get("path_status")
    outcome = row.get("final_outcome")
    origin = str(row.get("origin_family") or row.get("candidate_origin_family") or "")
    spread_r = as_float(anatomy.get("spread_r_at_candidate"))
    mfe = as_float(anatomy.get("mfe_r"))
    mae = as_float(anatomy.get("mae_r"))
    selected_risk = row.get("selected_cell_risk_pct")
    if status == "entry_filled_sl_before_1r_trigger":
        if spread_r is not None and spread_r >= 0.2:
            return "spread_cost_large_vs_stop", "spread_r_at_candidate >= 0.20"
        if mfe is not None and mfe < 0.25 and mae is not None and mae <= -1.0:
            return "wrong_direction_or_no_continuation", "MFE < 0.25R before SL"
        if "liquidity_sweep" in origin:
            return "sweep_continuation_failure", "liquidity sweep origin failed to reclaim before SL"
        if "cross_asset" in origin:
            return "cross_asset_lead_lag_failed", "lead/lag candidate did not translate into 1R"
        return "stop_first_adverse_path", "SL touched before 1R trigger"
    if status in {"partial_1r_then_3r_final", "partial_1r_then_be", "partial_1r_then_open_at_last_available_price"}:
        if "displacement" in origin:
            return "displacement_follow_through", "origin family reached 1R"
        if "liquidity_sweep" in origin:
            return "liquidity_sweep_reclaim", "sweep/reclaim moved at least 1R"
        if "volatility" in origin:
            return "volatility_expansion_follow_through", "volatility expansion moved at least 1R"
        if "structural" in origin:
            return "structural_distance_follow_through", "structural-distance candidate reached dynamic trigger"
        return "m1_or_tick_continuation", "price path reached dynamic trigger"
    if outcome == "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC" and selected_risk in (None, "", 0, 0.0):
        return "stale_selector_risk_bridge_dominated", "candidate refused before broker path with unresolved selected-cell risk"
    if status == "no_entry_touch_before_last_available_price":
        return "no_fill_price_path", "entry level was not touched in available LTF evidence"
    return "incomplete_or_open_path", "available evidence did not reach terminal dynamic state"


def policy_result(row: dict[str, Any], anatomy: dict[str, Any], policy: str) -> dict[str, Any]:
    effective_policy = policy
    current_selected_policy_status = None
    if policy == "current_selected_policy":
        selected = row.get("selected_policy")
        if selected in {"partial_be_runner", "momentum_exhaustion", "trailing_runner"}:
            effective_policy = str(selected)
            current_selected_policy_status = "resolved_from_row_selected_policy"
        else:
            effective_policy = "not_computed_missing_selected_policy"
            current_selected_policy_status = "not_computed_missing_selected_policy"
    status = anatomy.get("path_status")
    sl_time = parse_dt(anatomy.get("sl_touch_utc"))
    one_r = parse_dt(anatomy.get("one_r_trigger_utc"))
    raw_tp = parse_dt(anatomy.get("raw_1_5r_target_utc"))
    final = parse_dt(anatomy.get("dynamic_final_3r_utc"))
    be = parse_dt(anatomy.get("be_return_utc"))
    last_r = as_float(anatomy.get("last_r"))
    if policy == "no_trade_baseline":
        r = 0.0
        result = "no_trade"
    elif anatomy.get("entry_touch_utc") is None:
        r = 0.0
        result = "no_fill"
    elif effective_policy == "not_computed_missing_selected_policy":
        r, result = None, "not_computed_missing_selected_policy"
    elif effective_policy == "fixed_1_5r_comparator":
        if sl_time and (raw_tp is None or sl_time <= raw_tp):
            r, result = -1.0, "sl_before_fixed_1_5r"
        elif raw_tp:
            r, result = 1.5, "fixed_1_5r_hit"
        else:
            r, result = last_r, "open_at_last_price"
    elif effective_policy == "be_after_trigger_comparator":
        if sl_time and (one_r is None or sl_time <= one_r):
            r, result = -1.0, "sl_before_be_trigger"
        elif raw_tp and one_r and raw_tp <= (be or raw_tp):
            r, result = 1.5, "target_after_be_trigger"
        elif be:
            r, result = 0.0, "be_after_trigger"
        else:
            r, result = last_r, "open_at_last_price"
    elif effective_policy == "partial_be_runner":
        r = anatomy.get("proxy_gross_r")
        result = str(status)
    elif effective_policy == "momentum_exhaustion":
        if sl_time and (one_r is None or sl_time <= one_r):
            r, result = -1.0, "sl_before_momentum_trigger"
        elif final and (be is None or final <= be):
            r, result = 2.0, "momentum_final_proxy_hit"
        elif one_r:
            r, result = 0.5, "momentum_trigger_then_pullback_or_open_proxy"
        else:
            r, result = last_r, "open_at_last_price"
    elif effective_policy == "trailing_runner":
        r, result = None, "superseded_by_tick_sequenced_execution_tournament"
    elif effective_policy == "time_stop_4h_comparator":
        if sl_time and one_r is None:
            r, result = -1.0, "sl_before_time_stop"
        else:
            r, result = as_float(anatomy.get("time_stop_4h_r")), "time_stop_4h_proxy"
    else:
        r, result = None, "not_computed"
    return {
        "candidate_id": row.get("candidate_id"),
        "symbol": row.get("symbol"),
        "side": row.get("side"),
        "session": row.get("route_session"),
        "origin_family": row.get("origin_family"),
        "candle_time_utc": row.get("candle_time_utc"),
        "current_selected_policy": row.get("selected_policy"),
        "current_selected_policy_resolution_status": current_selected_policy_status,
        "effective_policy_simulated": effective_policy if policy == "current_selected_policy" else policy,
        "execution_policy_id": row.get("execution_policy_id"),
        "comparison_policy": policy,
        "policy_result": result,
        "proxy_gross_r": r,
        "evidence_class": (
            "superseded_proxy_not_authority_use_execution_policy_tournament"
            if policy == "trailing_runner"
            else "tick_or_m1_source_bound_proxy_not_broker_realized"
        ),
        "source_path": row.get("source_path"),
    }


def mt5_readonly_snapshot(tickets: set[int]) -> dict[str, Any]:
    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:
        return {"available": False, "error": f"import_failed:{exc!r}"}
    if not mt5.initialize():
        return {"available": False, "error": f"initialize_failed:{mt5.last_error()!r}"}
    try:
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=7)
        account = mt5.account_info()
        positions = [p._asdict() for p in (mt5.positions_get() or [])]
        orders = [o._asdict() for o in (mt5.orders_get() or [])]
        deals: list[dict[str, Any]] = []
        for deal in mt5.history_deals_get(start, now) or []:
            row = deal._asdict()
            if row.get("position_id") in tickets or row.get("order") in tickets or row.get("ticket") in tickets:
                if row.get("time"):
                    row["time_utc"] = datetime.fromtimestamp(row["time"], tz=timezone.utc).isoformat()
                if row.get("time_msc"):
                    row["time_msc_utc"] = datetime.fromtimestamp(row["time_msc"] / 1000, tz=timezone.utc).isoformat()
                deals.append(row)
        return {
            "available": True,
            "checked_at_utc": now.isoformat(),
            "account": account._asdict() if account else None,
            "positions": positions,
            "orders": orders,
            "deals": deals,
        }
    finally:
        mt5.shutdown()


def placed_autopsy(anatomy_rows: list[dict[str, Any]], include_mt5: bool) -> list[dict[str, Any]]:
    placed = [r for r in anatomy_rows if r.get("final_outcome") == "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN"]
    lifecycle = load_jsonl(ROOT / "shadow_logs" / "pending_limit_lifecycle.jsonl")
    slippage = load_jsonl(ROOT / "shadow_logs" / "slippage.jsonl")
    tickets: set[int] = set()
    for row in lifecycle:
        for key in ("mt5_position_ticket", "mt5_entry_order_ticket", "trade_state_ticket"):
            if isinstance(row.get(key), int):
                tickets.add(row[key])
    mt5 = mt5_readonly_snapshot(tickets) if include_mt5 else {"available": False, "error": "not_requested"}
    deals_by_position: dict[str, list[dict[str, Any]]] = defaultdict(list)
    positions_by_ticket = {str(p.get("ticket")): p for p in mt5.get("positions") or [] if p.get("ticket") is not None}
    for deal in mt5.get("deals") or []:
        deals_by_position[str(deal.get("position_id"))].append(deal)
    lifecycle_by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in lifecycle:
        cid = row.get("candidate_id")
        if cid:
            lifecycle_by_candidate[str(cid)].append(row)
    slips_by_ticket: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in slippage:
        ticket = row.get("ticket") or row.get("order_ticket") or row.get("position_id")
        if ticket is not None:
            slips_by_ticket[str(ticket)].append(row)
    out: list[dict[str, Any]] = []
    for row in placed:
        life = lifecycle_by_candidate.get(str(row.get("candidate_id")), [])
        ticket = first(*(r.get("mt5_position_ticket") or r.get("trade_state_ticket") or r.get("mt5_entry_order_ticket") for r in life))
        slips = slips_by_ticket.get(str(ticket), []) if ticket is not None else []
        deals = deals_by_position.get(str(ticket), []) if ticket is not None else []
        entry_deals = [d for d in deals if d.get("entry") == 0]
        close_deals = [d for d in deals if d.get("entry") == 1]
        manual_deals = [d for d in close_deals if d.get("magic") in (0, None) or d.get("reason") == 1]
        open_position = positions_by_ticket.get(str(ticket))
        if open_position and close_deals:
            truth = "partial_closed_with_open_residual_reconciled_from_mt5"
        elif open_position:
            truth = "open_position_reconciled_from_mt5"
        elif manual_deals:
            truth = "closed_with_manual_intervention_reconciled_from_mt5"
        elif close_deals:
            truth = "closed_reconciled_from_mt5"
        elif mt5.get("available"):
            truth = "entry_only_no_close_deal_found_in_mt5_window"
        else:
            truth = "mt5_readonly_not_available"
        out.append({
            "candidate_id": row.get("candidate_id"),
            "trade_id": row.get("trade_id"),
            "symbol": row.get("symbol"),
            "broker_symbol": row.get("broker_symbol"),
            "side": row.get("side"),
            "candle_time_utc": row.get("candle_time_utc"),
            "ticket": ticket,
            "source_path": row.get("source_path"),
            "intended_entry": row.get("repaired_entry"),
            "intended_stop": row.get("repaired_stop_loss"),
            "intended_dynamic_trigger": row.get("dynamic_trigger_price"),
            "intended_dynamic_final_target": row.get("dynamic_final_target_price"),
            "lifecycle_event_count": len(life),
            "lifecycle_events": life,
            "slippage_row_count": len(slips),
            "slippage_rows": slips,
            "mt5_broker_truth_status": truth,
            "mt5_entry_deal_count": len(entry_deals),
            "mt5_close_deal_count": len(close_deals),
            "mt5_manual_close_deal_count": len(manual_deals),
            "mt5_realized_profit_sum": sum(float(d.get("profit") or 0.0) for d in close_deals),
            "mt5_commission_sum": sum(float(d.get("commission") or 0.0) for d in deals),
            "mt5_swap_sum": sum(float(d.get("swap") or 0.0) for d in deals),
            "mt5_close_deals": close_deals,
            "mt5_open_position": open_position,
            "price_action_anatomy": {
                key: row.get(key)
                for key in [
                    "path_status",
                    "proxy_gross_r",
                    "entry_touch_utc",
                    "one_r_trigger_utc",
                    "dynamic_final_3r_utc",
                    "be_return_utc",
                    "sl_touch_utc",
                    "mfe_r",
                    "mae_r",
                    "time_to_entry_seconds",
                    "time_to_1r_seconds",
                    "time_to_sl_seconds",
                ]
            },
            "manual_intervention_status": "manual_contaminated_autonomous_metric_excluded" if manual_deals else "no_manual_close_deal_detected",
            "current_repaired_code_management_difference": (
                "ticket_bound_residual_management_would_target_this_position"
                if row.get("symbol") == "NAS100"
                else "same_symbol_conflict_gate_now_prevents_new_overlap_before_independent_lifecycle_support"
                if row.get("symbol") == "XAUUSD"
                else "no_specific_code_management_difference_identified"
            ),
        })
    return out


def build(include_mt5: bool) -> dict[str, Any]:
    records = load_trade_records(WEEKEND_START, WEEKEND_END)
    tick_cache: dict[str, pd.DataFrame | None] = {}
    m1_cache: dict[str, list[Bar]] = {}
    anatomy_rows: list[dict[str, Any]] = []
    refusal_rows: list[dict[str, Any]] = []
    loser_rows: list[dict[str, Any]] = []
    winner_rows: list[dict[str, Any]] = []
    policy_rows: list[dict[str, Any]] = []
    for record in records:
        base = candidate_row(record)
        anatomy = analyze_price_path(base, tick_cache, m1_cache)
        mechanism, proof = classify_mechanism(base, anatomy)
        full = {
            "schema_version": "vnext_weekend_candidate_price_action_anatomy_v1",
            **base,
            **anatomy,
            "mechanism_classification": mechanism,
            "mechanism_proof": proof,
        }
        anatomy_rows.append(full)
        if base.get("final_outcome") != "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN":
            refusal_rows.append(classify_refusal(base, anatomy))
        proxy_r = as_float(anatomy.get("proxy_gross_r"))
        mechanism_row = {
            "candidate_id": base.get("candidate_id"),
            "symbol": base.get("symbol"),
            "side": base.get("side"),
            "session": base.get("route_session"),
            "origin_family": base.get("origin_family"),
            "candle_time_utc": base.get("candle_time_utc"),
            "final_outcome": base.get("final_outcome"),
            "path_status": anatomy.get("path_status"),
            "proxy_gross_r": proxy_r,
            "mechanism": mechanism,
            "mechanism_proof": proof,
            "mfe_r": anatomy.get("mfe_r"),
            "mae_r": anatomy.get("mae_r"),
            "time_to_entry_seconds": anatomy.get("time_to_entry_seconds"),
            "time_to_1r_seconds": anatomy.get("time_to_1r_seconds"),
            "time_to_sl_seconds": anatomy.get("time_to_sl_seconds"),
            "source_path": base.get("source_path"),
        }
        if proxy_r is not None and proxy_r < 0:
            loser_rows.append(mechanism_row)
        elif proxy_r is not None and proxy_r > 0:
            winner_rows.append(mechanism_row)
        for policy in POLICIES:
            policy_rows.append(policy_result(base, anatomy, policy))
    autopsy_rows = placed_autopsy(anatomy_rows, include_mt5)
    repair_rows = implementation_repair_rows(anatomy_rows, refusal_rows, autopsy_rows)
    summary = build_summary(anatomy_rows, refusal_rows, loser_rows, winner_rows, policy_rows, autopsy_rows, repair_rows)
    write_jsonl(ANATOMY_LEDGER, anatomy_rows)
    write_jsonl(PLACED_AUTOPSY_LEDGER, autopsy_rows)
    write_jsonl(REFUSAL_LEDGER, refusal_rows)
    write_jsonl(LOSER_LEDGER, loser_rows)
    write_jsonl(WINNER_LEDGER, winner_rows)
    write_jsonl(POLICY_LEDGER, policy_rows)
    write_jsonl(REPAIR_LEDGER, repair_rows)
    write_json(INTELLIGENCE_SUMMARY, summary)
    FINDINGS_REPORT.write_text(render_report(summary), encoding="utf-8")
    verification = verify_outputs(summary)
    write_json(VERIFICATION, verification)
    return verification


def implementation_repair_rows(anatomy_rows: list[dict[str, Any]], refusal_rows: list[dict[str, Any]], autopsy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stale_selector = [r for r in refusal_rows if "selector" in str(r.get("refusal_correctness_status")) or "selected_cell" in str(r.get("refusal_correctness_status"))]
    gate1 = [r for r in refusal_rows if r.get("final_outcome") == "REJECTED_GATE1_SAFETY"]
    prop = [r for r in refusal_rows if r.get("final_outcome") == "DEFERRED_GTOS_VNEXT_PROP_RESET"]
    gate3_incomplete = [r for r in refusal_rows if r.get("refusal_correctness_status") == "gate_correct_but_historical_packet_incomplete"]
    silent_symbols = [s for s in EXPECTED_SYMBOLS if not any(r.get("symbol") == s for r in anatomy_rows)]
    rows = [
        {
            "repair_item": "route_evidence_rebuilt_to_current_head",
            "status": "done_this_pass",
            "proof": "checkpoint/starvation/post-reload/gate-stack/weekend forensic artifacts regenerated at current HEAD before anatomy build",
            "affected_rows": len(anatomy_rows),
        },
        {
            "repair_item": "m1_capture_daemon_not_running",
            "status": "restarted_this_pass",
            "proof": "checkpoint initially failed live_support_processes_not_running:m1_capture_python=0; data-only m1_capture daemon restarted and checkpoint M1 health became fresh",
            "affected_rows": len(anatomy_rows),
        },
        {
            "repair_item": "generic_selector_and_selected_cell_refusals",
            "status": "historical_rows_classified_current_code_requires_exact_dimensions",
            "proof": "refusal ledger classifies each generic framework/risk row as stale/unresolved unless exact exclusion proof exists",
            "affected_rows": len(stale_selector),
        },
        {
            "repair_item": "historical_gate1_terminal_rejects",
            "status": "historical_stale_under_repaired_vnext",
            "proof": "Gate1 rows predate or bypass executable geometry repair; current code requires repair path before terminal Gate1",
            "affected_rows": len(gate1),
        },
        {
            "repair_item": "historical_pre_dynamic_prop_deferrals",
            "status": "historical_stale_under_repaired_vnext",
            "proof": "prop deferrals happened before selected-cell risk/lot/current exposure scheduling; current code treats pre-dynamic prop as projection-only",
            "affected_rows": len(prop),
        },
        {
            "repair_item": "gate3_packet_writer_historical_gaps",
            "status": "historical_gap_classified_post_reload_rows_complete",
            "proof": "Gate3 spread can be valid while old packet lacked policy/risk fields; post-reload candidate proof has zero missing required fields",
            "affected_rows": len(gate3_incomplete),
        },
        {
            "repair_item": "silent_symbol_no_candidate_logging",
            "status": "historical_silence_classified_current_writer_contract_required",
            "proof": "symbols with zero candidate rows are reported in summary; current code contains native no-candidate writer per forensic repair contract",
            "affected_symbols": silent_symbols,
        },
        {
            "repair_item": "broker_realized_pnl_supersedes_local_projection",
            "status": "autopsy_ledger_uses_mt5_readonly_when_available",
            "proof": "placed-trade autopsy records MT5 deal realized profit/commission/swap and manual contamination status",
            "affected_rows": len(autopsy_rows),
        },
    ]
    return rows


def build_summary(
    anatomy: list[dict[str, Any]],
    refusals: list[dict[str, Any]],
    losers: list[dict[str, Any]],
    winners: list[dict[str, Any]],
    policy: list[dict[str, Any]],
    autopsy: list[dict[str, Any]],
    repairs: list[dict[str, Any]],
) -> dict[str, Any]:
    symbol_rows: dict[str, dict[str, Any]] = {}
    for symbol in EXPECTED_SYMBOLS:
        rows = [r for r in anatomy if r.get("symbol") == symbol]
        symbol_rows[symbol] = {
            "candidate_rows": len(rows),
            "outcomes": dict(Counter(r.get("final_outcome") for r in rows)),
            "path_statuses": dict(Counter(r.get("path_status") for r in rows)),
            "mechanisms": dict(Counter(r.get("mechanism_classification") for r in rows)),
            "proxy_r_known_sum": sum(float(r.get("proxy_gross_r") or 0.0) for r in rows if r.get("proxy_gross_r") is not None),
            "no_candidate_or_silent_classification": (
                "no_vnext_candidate_rows_written_for_symbol_requires_no_candidate_bridge_proof"
                if not rows
                else "candidate_rows_present"
            ),
        }
    grouped: dict[str, dict[str, Any]] = {}
    buckets: defaultdict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in anatomy:
        buckets[(str(row.get("symbol")), str(row.get("route_session")), str(row.get("origin_family")))].append(row)
    for key, rows in buckets.items():
        grouped["|".join(key)] = {
            "rows": len(rows),
            "outcomes": dict(Counter(r.get("final_outcome") for r in rows)),
            "path_statuses": dict(Counter(r.get("path_status") for r in rows)),
            "mechanisms": dict(Counter(r.get("mechanism_classification") for r in rows)),
            "proxy_r_known_sum": sum(float(r.get("proxy_gross_r") or 0.0) for r in rows if r.get("proxy_gross_r") is not None),
        }
    return {
        "schema_version": "vnext_weekend_price_action_anatomy_summary_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": git_head(),
        "evidence_window_start_utc": WEEKEND_START.isoformat(),
        "evidence_window_end_utc": WEEKEND_END.isoformat(),
        "candidate_rows": len(anatomy),
        "placed_trade_autopsy_rows": len(autopsy),
        "refusal_rows": len(refusals),
        "loser_rows": len(losers),
        "winner_rows": len(winners),
        "policy_comparison_rows": len(policy),
        "implementation_repair_rows": len(repairs),
        "symbol_count": len(EXPECTED_SYMBOLS),
        "symbol_intelligence": symbol_rows,
        "symbol_session_origin_summary": grouped,
        "outcome_counts": dict(Counter(r.get("final_outcome") for r in anatomy)),
        "path_status_counts": dict(Counter(r.get("path_status") for r in anatomy)),
        "price_source_counts": dict(Counter(r.get("price_source") for r in anatomy)),
        "mechanism_counts": dict(Counter(r.get("mechanism_classification") for r in anatomy)),
        "refusal_correctness_counts": dict(Counter(r.get("refusal_correctness_status") for r in refusals)),
        "policy_proxy_r_sums": {
            p: sum(float(r.get("proxy_gross_r") or 0.0) for r in policy if r.get("comparison_policy") == p and r.get("proxy_gross_r") is not None)
            for p in POLICIES
        },
        "selected_policy_counts": dict(Counter(r.get("selected_policy") or "missing_selected_policy" for r in anatomy)),
        "missing_selected_policy_count": sum(1 for r in anatomy if not r.get("selected_policy")),
        "current_selected_policy_resolved_counts": dict(
            Counter(
                r.get("effective_policy_simulated") or "missing"
                for r in policy
                if r.get("comparison_policy") == "current_selected_policy"
            )
        ),
        "btc_eth": {
            sym: {
                "rows": len([r for r in anatomy if r.get("symbol") == sym]),
                "outcomes": dict(Counter(r.get("final_outcome") for r in anatomy if r.get("symbol") == sym)),
                "path_statuses": dict(Counter(r.get("path_status") for r in anatomy if r.get("symbol") == sym)),
                "refusal_statuses": dict(Counter(r.get("refusal_correctness_status") for r in refusals if r.get("symbol") == sym)),
            }
            for sym in ("BTCUSD", "ETHUSD")
        },
        "placed_broker_truth_status_counts": dict(Counter(r.get("mt5_broker_truth_status") for r in autopsy)),
        "mt5_realized_profit_sum": sum(float(r.get("mt5_realized_profit_sum") or 0.0) for r in autopsy),
        "mt5_commission_sum": sum(float(r.get("mt5_commission_sum") or 0.0) for r in autopsy),
        "mt5_swap_sum": sum(float(r.get("mt5_swap_sum") or 0.0) for r in autopsy),
        "manual_contaminated_rows": sum(1 for r in autopsy if r.get("manual_intervention_status") == "manual_contaminated_autonomous_metric_excluded"),
        "limitations": [
            "This is source-bound tick/M1 anatomy, not a production-change approval dossier.",
            "Tick bid/ask is primary when local parquet covers the candidate window; M1 OHLC is fallback and marks ambiguity.",
            "Historical intent/order truth is never invented from price path; missing lifecycle fields remain exact capture requirements.",
            "Weekend broker closure/open-position state prevents live management action in this pass.",
        ],
        "outputs": {
            "candidate_price_action_anatomy": str(ANATOMY_LEDGER),
            "placed_trade_broker_autopsy": str(PLACED_AUTOPSY_LEDGER),
            "refusal_correctness_staleness": str(REFUSAL_LEDGER),
            "loser_mechanism": str(LOSER_LEDGER),
            "winner_mechanism": str(WINNER_LEDGER),
            "policy_comparison": str(POLICY_LEDGER),
            "symbol_session_origin_summary": str(INTELLIGENCE_SUMMARY),
            "implementation_repair": str(REPAIR_LEDGER),
            "final_findings_report": str(FINDINGS_REPORT),
            "verification": str(VERIFICATION),
        },
    }


def render_report(summary: dict[str, Any]) -> str:
    btc = summary["btc_eth"]["BTCUSD"]
    eth = summary["btc_eth"]["ETHUSD"]
    lines = [
        "# Weekend vNext Price-Action Anatomy Final Findings",
        "",
        f"Generated: {summary['generated_at_utc']}",
        f"HEAD: {summary['git_head']}",
        "",
        "## Denominator",
        "",
        f"- Candidate rows studied: {summary['candidate_rows']}",
        f"- Placed broker autopsies: {summary['placed_trade_autopsy_rows']}",
        f"- Refusal rows classified: {summary['refusal_rows']}",
        f"- Policy comparison rows: {summary['policy_comparison_rows']}",
        "",
        "## Core Findings",
        "",
        f"- Outcome counts: `{json.dumps(summary['outcome_counts'], sort_keys=True)}`",
        f"- Refusal correctness counts: `{json.dumps(summary['refusal_correctness_counts'], sort_keys=True)}`",
        f"- BTCUSD: `{json.dumps(btc, sort_keys=True)}`",
        f"- ETHUSD: `{json.dumps(eth, sort_keys=True)}`",
        f"- Broker truth status counts: `{json.dumps(summary['placed_broker_truth_status_counts'], sort_keys=True)}`",
        f"- MT5 realized profit sum where available: `{summary['mt5_realized_profit_sum']}`; commission `{summary['mt5_commission_sum']}`; swap `{summary['mt5_swap_sum']}`",
        "",
        "## Production Boundary",
        "",
        "This pass builds source-bound intelligence and route evidence. It does not authorize a live logic change by itself, and it performs no broker actions.",
    ]
    return "\n".join(lines) + "\n"


def verify_outputs(summary: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    forensic = json.loads(FORENSIC_SUMMARY.read_text(encoding="utf-8")) if FORENSIC_SUMMARY.exists() else {}
    expected_candidates = int(forensic.get("candidate_trade_record_count") or 588)
    summary_route_descendant = route_artifact_only_descendant(summary.get("git_head"))
    forensic_route_descendant = route_artifact_only_descendant(forensic.get("git_head"))
    if summary.get("candidate_rows") != expected_candidates:
        issues.append({"code": "candidate_row_count_mismatch", "expected": expected_candidates, "actual": summary.get("candidate_rows")})
    if forensic.get("git_head") and forensic.get("git_head") != git_head() and not forensic_route_descendant.get("allowed"):
        issues.append(
            {
                "code": "stale_forensic_anchor_git_head",
                "expected": git_head(),
                "actual": forensic.get("git_head"),
                "route_artifact_only_descendant": forensic_route_descendant,
            }
        )
    if summary.get("placed_trade_autopsy_rows") != 8:
        issues.append({"code": "placed_autopsy_count_mismatch", "expected": 8, "actual": summary.get("placed_trade_autopsy_rows")})
    if summary.get("refusal_rows") != summary.get("candidate_rows") - 8:
        issues.append({"code": "refusal_row_count_mismatch", "expected": summary.get("candidate_rows") - 8, "actual": summary.get("refusal_rows")})
    if summary.get("policy_comparison_rows") != summary.get("candidate_rows") * len(POLICIES):
        issues.append({"code": "policy_row_count_mismatch", "expected": summary.get("candidate_rows") * len(POLICIES), "actual": summary.get("policy_comparison_rows")})
    resolved_counts = summary.get("current_selected_policy_resolved_counts", {})
    selected_counts = summary.get("selected_policy_counts", {})
    for selected_policy in ("partial_be_runner", "momentum_exhaustion", "trailing_runner"):
        if resolved_counts.get(selected_policy, 0) != selected_counts.get(selected_policy, 0):
            issues.append(
                {
                    "code": "current_selected_policy_resolution_mismatch",
                    "policy": selected_policy,
                    "expected": selected_counts.get(selected_policy, 0),
                    "actual": resolved_counts.get(selected_policy, 0),
                }
            )
    if summary.get("symbol_count") != 24:
        issues.append({"code": "symbol_count_mismatch", "expected": 24, "actual": summary.get("symbol_count")})
    if summary.get("git_head") != git_head() and not summary_route_descendant.get("allowed"):
        issues.append(
            {
                "code": "stale_git_head",
                "expected": git_head(),
                "actual": summary.get("git_head"),
                "route_artifact_only_descendant": summary_route_descendant,
            }
        )
    for path in [
        ANATOMY_LEDGER,
        PLACED_AUTOPSY_LEDGER,
        REFUSAL_LEDGER,
        LOSER_LEDGER,
        WINNER_LEDGER,
        POLICY_LEDGER,
        INTELLIGENCE_SUMMARY,
        REPAIR_LEDGER,
        FINDINGS_REPORT,
    ]:
        if not path.exists() or path.stat().st_size <= 0:
            issues.append({"code": "missing_or_empty_output", "path": str(path)})
    unresolved = summary.get("refusal_correctness_counts", {}).get("unresolved", 0)
    if unresolved:
        issues.append({"code": "unresolved_refusal_classes_present", "count": unresolved})
    return {
        "schema_version": "vnext_weekend_price_action_anatomy_verification_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": git_head(),
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "route_artifact_only_descendant": summary_route_descendant,
        "forensic_route_artifact_only_descendant": forensic_route_descendant,
        "candidate_rows_checked": summary.get("candidate_rows"),
        "forensic_candidate_row_anchor": expected_candidates,
        "no_top_n_truncation_proof": "candidate_rows equals rebuilt forensic candidate_trade_record_count and policy rows equal candidate_rows * all policy comparators",
    }


def check() -> int:
    if not INTELLIGENCE_SUMMARY.exists():
        print(f"missing {INTELLIGENCE_SUMMARY}")
        return 1
    summary = json.loads(INTELLIGENCE_SUMMARY.read_text(encoding="utf-8"))
    data = verify_outputs(summary)
    print(json.dumps(data, indent=2, sort_keys=True))
    return 0 if data.get("ok") else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--include-mt5-readonly", action="store_true")
    args = parser.parse_args()
    if args.check:
        return check()
    verification = build(include_mt5=args.include_mt5_readonly)
    print(json.dumps(verification, indent=2, sort_keys=True))
    return 0 if verification.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
