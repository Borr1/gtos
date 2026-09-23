#!/usr/bin/env python3
"""Session CN: TRAIN-only live-cost decision A/B for the currently armed book.

This tool is deliberately offline.  It generates entry intents from the exact live sleeve
generators over a bounded FTMO bar prefix, then runs the live pretrade packet twice on identical
inputs: the explicitly named pre-CN zero-commission comparator and the default broker-true model.
No outcome is loaded or computed.  The CSV reader stops at the first post-TRAIN timestamp before
decoding OHLCV, so March 2026 is unreachable by construction.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.components.broker_net_cost_engine import (  # noqa: E402
    BROKER_TRUE_COMMISSION_MODE,
    LEGACY_ZERO_COMMISSION_COMPARATOR_MODE,
    build_pretrade_cost_packet,
)
from src.components.ultimate_book.bar_provider import (  # noqa: E402
    TF_D1,
    TF_H4,
    decision_day_of,
)
from src.components.ultimate_book.execution_packets import resolve_exit_profile  # noqa: E402
from src.components.ultimate_book.primitives import Bar  # noqa: E402
from src.components.ultimate_book.sleeves.registry import (  # noqa: E402
    BUILT,
    MARKET_EXPANSION_BUILT,
)
from src.costs.model import CostTruthError, load_broker_true_costs  # noqa: E402
from src.utils import broker_clock  # noqa: E402
from src.utils.config import (  # noqa: E402
    apply_instrument_overrides,
    apply_profile_overrides,
    resolve_instrument_config_key,
)


SCHEMA = "gtos.session_cn.live_cost_decision_ab.v1"
TRAIN_START = datetime(2023, 1, 1, tzinfo=timezone.utc)
TRAIN_DECISION_START = datetime(2024, 1, 1, tzinfo=timezone.utc)
TRAIN_END = datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
BAR_ROOT = Path("/Users/borr/GTOSActive/vps-bars-20260727")
OUT = Path(__file__).with_name("CN_LIVE_COST_DECISION_AB_V1.json")
MX = "mx_btcusd_d1_donchian_20_breakout"
ARMED = {
    "FTMO": ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert", MX),
    "redacted_account": ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert"),
}
ACCOUNT_PROFILE = {
    "FTMO": "operator_profile",
    "redacted_account": "redacted_account",
}
TF_NAME = {TF_H4: "H4", TF_D1: "D1"}
APPROVED_COMMISSION_STATUS = "COMMISSION_INCLUDED_IN_SELECTED_CELL_RISK"


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _json_sha(value: Any) -> str:
    return _sha_bytes(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    )


def _parse_rule(path: Path):
    sidecar = Path(str(path) + ".timebase.json")
    meta = json.loads(sidecar.read_text())
    if meta.get("timebase") != "broker_server_wall_clock" or not meta.get("broker"):
        raise RuntimeError(f"unsupported or missing broker-wall-clock sidecar: {sidecar}")
    return broker_clock.resolve_rule(meta["broker"]), meta, sidecar


def load_train_prefix(path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Decode only 2023-2024 input bars; stop before decoding the first later OHLC row."""
    rule, sidecar, sidecar_path = _parse_rule(path)
    rows: list[dict[str, Any]] = []
    prefix_hash = hashlib.sha256()
    first_refused_utc = None
    previous = None
    with gzip.open(path, "rt", newline="") as handle:
        for raw in csv.DictReader(handle):
            stamp = broker_clock.broker_epoch_to_utc(float(raw["time"]), rule)
            if previous is not None and stamp < previous:
                raise RuntimeError(f"non-monotone bar source: {path} at {stamp.isoformat()}")
            previous = stamp
            if stamp > TRAIN_END:
                first_refused_utc = stamp.isoformat()
                break
            if stamp < TRAIN_START:
                continue
            # OHLCV and spread are decoded only after the hard upper-bound check above.
            row = {
                "time": stamp,
                "bar": Bar(
                    float(raw["open"]),
                    float(raw["high"]),
                    float(raw["low"]),
                    float(raw["close"]),
                    float(raw.get("tick_volume") or 0.0),
                ),
            }
            rows.append(row)
            prefix_hash.update(
                json.dumps(
                    {
                        "time": stamp.isoformat(),
                        "open": raw["open"],
                        "high": raw["high"],
                        "low": raw["low"],
                        "close": raw["close"],
                        "tick_volume": raw.get("tick_volume"),
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode()
            )
            prefix_hash.update(b"\n")
    if not rows:
        raise RuntimeError(f"no TRAIN prefix rows: {path}")
    if rows[-1]["time"] > TRAIN_END:
        raise AssertionError("hard TRAIN cutoff failed")
    return rows, {
        "path": str(path),
        "sidecar_path": str(sidecar_path),
        "sidecar_sha256": _sha_file(sidecar_path),
        "timebase": sidecar,
        "decoded_row_count": len(rows),
        "first_decoded_utc": rows[0]["time"].isoformat(),
        "last_decoded_utc": rows[-1]["time"].isoformat(),
        "first_refused_post_train_utc": first_refused_utc,
        "train_prefix_sha256": prefix_hash.hexdigest(),
        "decoded_outcome_fields": [],
    }


def _spec(tag: str):
    return MARKET_EXPANSION_BUILT[tag] if tag == MX else BUILT[tag]


def generate_train_intents(tag: str, symbol: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    spec = _spec(tag)
    prefix: list[Bar] = []
    times: list[datetime] = []
    out: list[dict[str, Any]] = []
    for row in rows:
        prefix.append(row["bar"])
        times.append(row["time"])
        if row["time"] < TRAIN_DECISION_START:
            continue
        intent = spec.generator(
            symbol,
            prefix,
            decision_day_of(row["time"]),
            bar_time=row["time"],
            bar_times=times,
            runtime_now=row["time"] + timedelta(minutes=1440 if spec.timeframe == TF_D1 else 240),
        )
        if intent is None:
            continue
        out.append({
            "sleeve": tag,
            "symbol": symbol,
            "decision_bar_utc": row["time"].isoformat(),
            "decision_day": intent.decision_day,
            "direction": "LONG" if int(intent.direction) > 0 else "SHORT",
            "source_close": row["bar"].c,
            "sl_distance": float(intent.stop_dist),
        })
    return out


def _profile_configs() -> dict[str, dict[str, Any]]:
    base = yaml.safe_load((REPO / "config/agent_config.yaml").read_text()) or {}
    return {
        account: apply_profile_overrides(base, profile)
        for account, profile in ACCOUNT_PROFILE.items()
    }


def _schedule_projection(record: dict[str, Any]) -> dict[str, Any]:
    commission = record.get("commission") or {}
    spread = record.get("spread_price") or {}
    percentiles = spread.get("percentiles") or {}
    return {
        "instrument_class": record.get("instrument_class"),
        "commission_kind": commission.get("kind"),
        "commission_schedule_value": commission.get("value"),
        "commission_schedule_unit": commission.get("unit"),
        "commission_coverage": commission.get("coverage"),
        "commission_n_round_turns": commission.get("n_round_turns"),
        "spread_p50_price": percentiles.get("p50"),
        "spread_coverage": spread.get("coverage"),
    }


def _trade_params(candidate: dict[str, Any], entry: float, stop: float) -> dict[str, Any]:
    frontier = (MX,) if candidate["sleeve"] == MX else ()
    exit_profile = resolve_exit_profile(candidate["sleeve"], frontier_exits=frontier)
    return {
        "direction": candidate["direction"],
        "entry_price": entry,
        "stop_loss": stop,
        "gtos_vnext_production_execution_path": True,
        "gtos_vnext_selected_cell_risk_pct": 0.1,
        "gtos_vnext_selected_cell_risk_cell_id": f"CN::{candidate['sleeve']}::{candidate['symbol']}",
        "gtos_vnext_selected_cell_risk_decision_basis": "session_cn_offline_same_input_ab",
        "gtos_vnext_commission_model_status": APPROVED_COMMISSION_STATUS,
        "gtos_vnext_dynamic_time_stop_bars": exit_profile.get("time_stop_bars"),
        "gtos_vnext_source_event_details": {
            "book": "armed_book_train_projection",
            "sleeve": candidate["sleeve"],
        },
    }


def project_candidate(
    candidate: dict[str, Any],
    *,
    account: str,
    account_config: dict[str, Any],
    truth,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    symbol = candidate["symbol"]
    if resolve_instrument_config_key(account_config, symbol) is None:
        return None, {"reason": "symbol_not_in_live_profile", "symbol": symbol}
    cfg = apply_instrument_overrides(account_config, symbol)
    broker_symbol = str((cfg.get("market") or {}).get("mt5_symbol") or symbol)
    try:
        truth_record = truth.instrument(account, broker_symbol)
    except CostTruthError as exc:
        return None, {
            "reason": "broker_truth_instrument_gap",
            "symbol": symbol,
            "broker_symbol": broker_symbol,
            "detail": str(exc),
        }
    schedule = _schedule_projection(truth_record)
    spread_price = schedule["spread_p50_price"]
    if spread_price is None:
        return None, {
            "reason": "broker_truth_spread_p50_gap",
            "symbol": symbol,
            "broker_symbol": broker_symbol,
            "commission_schedule": schedule,
        }

    direction = candidate["direction"]
    mid = float(candidate["source_close"])
    entry = mid + float(spread_price) / 2.0 if direction == "LONG" else mid - float(spread_price) / 2.0
    stop = entry - float(candidate["sl_distance"]) if direction == "LONG" else entry + float(candidate["sl_distance"])
    params = _trade_params(candidate, entry, stop)
    tick = SimpleNamespace(
        bid=mid - float(spread_price) / 2.0,
        ask=mid + float(spread_price) / 2.0,
        spread_cents=float(spread_price) * 100.0,
        time=candidate["decision_bar_utc"],
    )
    common = dict(
        config=cfg,
        trade_params=params,
        tick=tick,
        symbol=symbol,
        broker_symbol=broker_symbol,
        entry_price=entry,
        stop_loss=stop,
        sl_distance=float(candidate["sl_distance"]),
        risk_pct=0.1,
        # The live callers supply a fresh MT5 symbol_info snapshot.  The offline equivalent is
        # the account-specific captured symbol spec embedded in the broker-truth artifact, not
        # the thinner profile market map (which omits swap_mode on redacted_account).
        symbol_info=truth_record.get("spec"),
        asof_utc=candidate["decision_bar_utc"],
    )
    old = build_pretrade_cost_packet(
        **common,
        commission_mode=LEGACY_ZERO_COMMISSION_COMPARATOR_MODE,
    )
    new = build_pretrade_cost_packet(
        **common,
        commission_mode=BROKER_TRUE_COMMISSION_MODE,
    )
    stable_input = {
        "account": account,
        "sleeve": candidate["sleeve"],
        "symbol": symbol,
        "broker_symbol": broker_symbol,
        "decision_bar_utc": candidate["decision_bar_utc"],
        "direction": direction,
        "entry_price": entry,
        "stop_loss": stop,
        "sl_distance": candidate["sl_distance"],
        "spread_price": spread_price,
    }
    row = {
        **stable_input,
        "input_sha256": _json_sha(stable_input),
        "commission_schedule": schedule,
        "captured_symbol_spec_sha256": _json_sha(truth_record.get("spec") or {}),
        "commission_usd_per_lot_round_turn": new["commission_cost"].get("usd_per_lot_round_turn"),
        "commission_r": new.get("commission_r"),
        "spread_r": new.get("spread_r"),
        "old_total_cost_r": old.get("total_cost_r"),
        "new_total_cost_r": new.get("total_cost_r"),
        "max_total_cost_r": new.get("max_total_cost_r"),
        "old_status": old.get("status"),
        "new_status": new.get("status"),
        "old_refusal_reasons": old.get("refusal_reasons") or [],
        "new_refusal_reasons": new.get("refusal_reasons") or [],
        "new_commission_provenance": new.get("commission_cost_provenance"),
    }
    row["screen_outcome_flipped"] = row["old_status"] != row["new_status"]
    # Retain the commission's requested vocabulary while making clear that this is the binary
    # cost-screen outcome, not merely an arithmetic movement or an added refusal reason.
    row["decision_flipped"] = row["screen_outcome_flipped"]
    row["refusal_reasons_changed"] = (
        row["old_refusal_reasons"] != row["new_refusal_reasons"]
    )
    if row["old_total_cost_r"] is not None and row["new_total_cost_r"] is not None:
        row["total_cost_increase_r"] = (
            float(row["new_total_cost_r"]) - float(row["old_total_cost_r"])
        )
        row["cost_changed"] = not math.isclose(
            float(row["old_total_cost_r"]),
            float(row["new_total_cost_r"]),
            rel_tol=0.0,
            abs_tol=1e-15,
        )
    else:
        row["total_cost_increase_r"] = None
        row["cost_changed"] = row["old_total_cost_r"] != row["new_total_cost_r"]
    if row["max_total_cost_r"] is not None:
        row["old_total_cost_headroom_r"] = (
            None
            if row["old_total_cost_r"] is None
            else float(row["max_total_cost_r"]) - float(row["old_total_cost_r"])
        )
        row["new_total_cost_headroom_r"] = (
            None
            if row["new_total_cost_r"] is None
            else float(row["max_total_cost_r"]) - float(row["new_total_cost_r"])
        )
    else:
        row["old_total_cost_headroom_r"] = None
        row["new_total_cost_headroom_r"] = None
    return row, None


def _dist(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0, "min": None, "median": None, "max": None}
    return {
        "n": len(values),
        "min": min(values),
        "median": statistics.median(values),
        "max": max(values),
    }


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    old_reasons: defaultdict[str, int] = defaultdict(int)
    new_reasons: defaultdict[str, int] = defaultdict(int)
    for row in rows:
        for reason in row["old_refusal_reasons"]:
            old_reasons[str(reason)] += 1
        for reason in row["new_refusal_reasons"]:
            new_reasons[str(reason)] += 1
    return {
        "decisions": len(rows),
        "old_pass": sum(row["old_status"] == "PASSED" for row in rows),
        "new_pass": sum(row["new_status"] == "PASSED" for row in rows),
        "old_refused": sum(row["old_status"] == "REFUSED" for row in rows),
        "new_refused": sum(row["new_status"] == "REFUSED" for row in rows),
        "decision_flips": sum(bool(row["decision_flipped"]) for row in rows),
        "refusal_reason_changes": sum(
            bool(row["refusal_reasons_changed"]) for row in rows
        ),
        "cost_changed_decisions": sum(bool(row["cost_changed"]) for row in rows),
        "nonzero_commission_decisions": sum(
            row.get("commission_r") is not None
            and not math.isclose(float(row["commission_r"]), 0.0, abs_tol=1e-15)
            for row in rows
        ),
        "commission_r": _dist([
            float(row["commission_r"]) for row in rows if row.get("commission_r") is not None
        ]),
        "total_cost_increase_r": _dist([
            float(row["total_cost_increase_r"])
            for row in rows
            if row.get("total_cost_increase_r") is not None
        ]),
        "old_refusal_reason_counts": dict(sorted(old_reasons.items())),
        "new_refusal_reason_counts": dict(sorted(new_reasons.items())),
    }


def _aggregate_gaps(gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse candidate-repeated gaps without hiding how many decisions were excluded."""
    grouped: dict[str, dict[str, Any]] = {}
    for gap in gaps:
        unit = str(gap.get("gap_unit") or "candidate")
        visible = {key: value for key, value in gap.items() if key != "gap_unit"}
        key = json.dumps(
            {**visible, "gap_unit": unit},
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
        if key not in grouped:
            grouped[key] = {**visible, f"affected_{unit}_count": 0}
        grouped[key][f"affected_{unit}_count"] += 1
    return sorted(
        grouped.values(),
        key=lambda row: (
            str(row.get("account", "")),
            str(row.get("sleeve", "")),
            str(row.get("symbol", "")),
            str(row.get("reason", "")),
        ),
    )


def _decision_excerpt(row: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "account",
        "sleeve",
        "symbol",
        "broker_symbol",
        "decision_bar_utc",
        "direction",
        "entry_price",
        "stop_loss",
        "sl_distance",
        "spread_price",
        "input_sha256",
        "commission_schedule",
        "commission_r",
        "old_total_cost_r",
        "new_total_cost_r",
        "total_cost_increase_r",
        "max_total_cost_r",
        "old_total_cost_headroom_r",
        "new_total_cost_headroom_r",
        "old_status",
        "new_status",
        "old_refusal_reasons",
        "new_refusal_reasons",
        "new_commission_provenance",
        "decision_flipped",
        "refusal_reasons_changed",
    )
    return {key: row.get(key) for key in keys}


def build() -> dict[str, Any]:
    truth = load_broker_true_costs()
    configs = _profile_configs()
    source_cache: dict[tuple[str, int], tuple[list[dict[str, Any]], dict[str, Any]]] = {}
    source_receipts: dict[str, dict[str, Any]] = {}
    generated: dict[tuple[str, str], list[dict[str, Any]]] = {}
    generation_gaps: list[dict[str, Any]] = []

    all_tags = tuple(dict.fromkeys(tag for tags in ARMED.values() for tag in tags))
    for tag in all_tags:
        spec = _spec(tag)
        for symbol in spec.on_surface:
            tf_name = TF_NAME.get(spec.timeframe)
            if tf_name is None:
                generation_gaps.append({
                    "sleeve": tag, "symbol": symbol, "reason": "unsupported_timeframe",
                })
                continue
            path = BAR_ROOT / f"FTMO_{symbol}_{tf_name}.csv.gz"
            if not path.is_file():
                generation_gaps.append({
                    "sleeve": tag,
                    "symbol": symbol,
                    "reason": "ftmo_train_generation_bar_source_absent",
                    "path": str(path),
                })
                continue
            cache_key = (symbol, spec.timeframe)
            if cache_key not in source_cache:
                source_cache[cache_key] = load_train_prefix(path)
                source_receipts[f"{symbol}:{tf_name}"] = source_cache[cache_key][1]
            generated[(tag, symbol)] = generate_train_intents(
                tag, symbol, source_cache[cache_key][0]
            )

    decisions: list[dict[str, Any]] = []
    raw_projection_gaps: list[dict[str, Any]] = []
    for account, tags in ARMED.items():
        for tag in tags:
            for symbol in _spec(tag).on_surface:
                candidates = generated.get((tag, symbol))
                if candidates is None:
                    raw_projection_gaps.append({
                        "account": account,
                        "sleeve": tag,
                        "symbol": symbol,
                        "reason": "generation_input_gap",
                        "gap_unit": "surface_slot",
                    })
                    continue
                for candidate in candidates:
                    projected, gap = project_candidate(
                        candidate,
                        account=account,
                        account_config=configs[account],
                        truth=truth,
                    )
                    if projected is not None:
                        decisions.append(projected)
                    elif gap is not None:
                        raw_projection_gaps.append({
                            "account": account,
                            "sleeve": tag,
                            "gap_unit": "candidate",
                            **gap,
                        })

    per_account: dict[str, Any] = {}
    per_sleeve: dict[str, Any] = {}
    per_symbol: dict[str, Any] = {}
    for account in ARMED:
        account_rows = [row for row in decisions if row["account"] == account]
        per_account[account] = _summarize(account_rows)
        for tag in ARMED[account]:
            rows = [row for row in account_rows if row["sleeve"] == tag]
            per_sleeve[f"{account}::{tag}"] = _summarize(rows)
        for symbol in sorted({row["symbol"] for row in account_rows}):
            rows = [row for row in account_rows if row["symbol"] == symbol]
            summary = _summarize(rows)
            summary["broker_symbol"] = rows[0]["broker_symbol"]
            summary["commission_schedule"] = rows[0]["commission_schedule"]
            summary["commission_usd_per_lot_round_turn"] = _dist([
                float(row["commission_usd_per_lot_round_turn"])
                for row in rows
                if row.get("commission_usd_per_lot_round_turn") is not None
            ])
            per_symbol[f"{account}::{symbol}"] = summary

    flips = [_decision_excerpt(row) for row in decisions if row["decision_flipped"]]
    gate_disposition_changes = [
        _decision_excerpt(row)
        for row in decisions
        if row["decision_flipped"] or row["refusal_reasons_changed"]
    ]
    closest_old_passes = sorted(
        (
            _decision_excerpt(row)
            for row in decisions
            if row["old_status"] == "PASSED"
            and row.get("new_total_cost_headroom_r") is not None
        ),
        key=lambda row: float(row["new_total_cost_headroom_r"]),
    )[:20]
    decision_digest_rows = [
        {
            key: row.get(key)
            for key in (
                "input_sha256", "old_status", "new_status", "old_total_cost_r",
                "new_total_cost_r", "commission_r", "decision_flipped",
                "refusal_reasons_changed", "total_cost_increase_r",
            )
        }
        for row in decisions
    ]
    source_paths = [
        "src/components/permissions.py",
        "src/components/execution.py",
        "src/components/broker_net_cost_engine.py",
        "src/costs/model.py",
        "src/components/ultimate_book/book_owner.py",
        "src/components/ultimate_book/packet_economics.py",
        "src/components/ultimate_book/sleeves/registry.py",
        "config/agent_config.yaml",
        "config/profiles/operator_profile.yaml",
        "config/profiles/redacted_account.yaml",
        "research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json",
    ]
    return {
        "schema": SCHEMA,
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "purpose": "same-input old-zero-commission comparator vs default broker-true live cost gate",
        "armed_set": {key: list(value) for key, value in ARMED.items()},
        "population": {
            "lane": "TRAIN",
            "warmup_start_utc": TRAIN_START.isoformat(),
            "decision_start_utc": TRAIN_DECISION_START.isoformat(),
            "hard_end_utc": TRAIN_END.isoformat(),
            "generation_source": "exact live sleeve generators over FTMO broker-wall-clock bars converted to true UTC",
            "cost_projection": "each account's BROKER_TRUE_COSTS_V1 p50 spread + commission schedule, current profile symbol spec, historical candidate entry/stop geometry",
            "result_boundary": "entry decisions and costs only; no trade outcome, exit path, R result, March 2026 or live-forward TEST row read",
            "val_used": False,
            "test_used": False,
            "march_2026_outcomes_read": False,
        },
        "input_hashes": {path: _sha_file(REPO / path) for path in source_paths},
        "train_bar_prefixes": source_receipts,
        "generation_gaps": generation_gaps,
        "generated_intent_counts": {
            f"{tag}::{symbol}": len(rows)
            for (tag, symbol), rows in sorted(generated.items())
        },
        "projection_gaps": _aggregate_gaps(raw_projection_gaps),
        "projection_gap_counts_by_unit": {
            "candidate": sum(
                str(gap.get("gap_unit")) == "candidate" for gap in raw_projection_gaps
            ),
            "surface_slot": sum(
                str(gap.get("gap_unit")) == "surface_slot" for gap in raw_projection_gaps
            ),
        },
        "summary": {
            "all": _summarize(decisions),
            "per_account": per_account,
            "per_sleeve": per_sleeve,
            "per_symbol": per_symbol,
        },
        "decision_flips": flips,
        "gate_disposition_changes": gate_disposition_changes,
        "closest_old_passes_after_commission": closest_old_passes,
        "decision_rows_sha256": _json_sha(decision_digest_rows),
        "decision_row_count": len(decisions),
        "decision_flip_count": len(flips),
        "gate_disposition_change_count": len(gate_disposition_changes),
        "commission_modes": {
            "before": LEGACY_ZERO_COMMISSION_COMPARATOR_MODE,
            "after": BROKER_TRUE_COMMISSION_MODE,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    doc = build()
    rendered = json.dumps(doc, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not args.output.is_file() or args.output.read_text() != rendered:
            raise SystemExit(f"STALE_OR_MISSING:{args.output}")
        print(f"PASS {args.output} rows={doc['decision_row_count']} flips={doc['decision_flip_count']}")
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered)
    print(f"wrote {args.output} rows={doc['decision_row_count']} flips={doc['decision_flip_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
