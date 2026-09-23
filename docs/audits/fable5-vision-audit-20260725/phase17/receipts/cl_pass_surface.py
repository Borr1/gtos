#!/usr/bin/env python3
"""Session CL: price every evidence-supported armed-set extension without touching TEST.

This is an offline composition tool.  It never imports a broker client, never calls a live
entrypoint and never writes config.  Two protections are load-bearing:

* the estate reader checks decision/entry/exit timestamps before it indexes ``r_gross`` or
  any other outcome field; a row whose label span intersects March 2026 is discarded first;
* the D1 market-expansion reader is Session CH's timestamp-first reader.  It discards March
  OHLC before decoding a price and refuses any generator/label shoulder that intersects the
  protected month.  It also stops at the end of the used-once VAL band, so live-forward
  observations never enter this receipt.

The portfolio arithmetic is the existing firm-rule machinery: confidence-weighted daily
unit-R, live half-Kelly day bins, a 2.0% nominal unit dial, and ``mc_firm_rules.mc`` with the
per-firm L4 phase-1 and P2 two-step rules.  The source population differs from the W7 cache:
this uses the broker-true archive estate so it can compose the *current* FTMO five (including
mx@target_5R) and the current redacted_account four on one population.  Results are therefore
reported separately for pre-2025 (the out-of-window expectation) and the used-once 2025+
selection/VAL band.  No result is an admission test and no trial-budget row is written.
"""

from __future__ import annotations

import argparse
import bisect
import collections
import datetime as dt
import gzip
import hashlib
import importlib.util
import json
import math
import statistics
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml

REPO = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import mc_firm_rules as Q  # noqa: E402
from src.components.ultimate_book import admission as ADM  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs import load_broker_true_costs  # noqa: E402
from src.research_infra.replay_policy.generation import (  # noqa: E402
    GenerationPort,
    InMemoryBarSource,
)
from src.research_infra.walkforward import TradeRecord  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.panel import price_trades  # noqa: E402
from src.utils.config import apply_profile_overrides  # noqa: E402

AUDIT = REPO / "docs/audits/fable5-vision-audit-20260725"
ESTATE = AUDIT / "phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz"
SURVIVOR = REPO / "research/operations/w7_recost_2026_07_27/SURVIVOR_BOOK_V1.json"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
CH_DRIVER = AUDIT / "phase15/receipts/ch_lever_measurements.py"
CH_MILESTONES = AUDIT / "phase15/receipts/CH_PROMOTION_MILESTONES_V1.json"
AE_RESULT = AUDIT / "phase7/SESSION_AE_LEARNING_DIRECTION_RESULT.md"
CI_RESULT = AUDIT / "phase15/SESSION_CI_THIRD_PARTY_M1_RESULT.md"
OUT = HERE / "CL_PASS_SURFACE_PRICING_V1.json"
MD_OUT = HERE / "CL_PASS_SURFACE_PRICING_V1.md"

BARS = Path("/Users/borr/GTOSActive/vps-bars-20260727")
MX = "mx_btcusd_d1_donchian_20_breakout"
BLACKOUT = (dt.date(2026, 3, 1), dt.date(2026, 3, 31))
DATA_START = dt.date(2015, 1, 1)
VAL_END = dt.date(2026, 5, 31)
DIAL = 0.020
MATERIAL_P2_DROP = 0.020

ACCOUNTS = {
    "FTMO": {
        "profile": "operator_profile",
        "server": "FTMO-Server3",
        "bars": "FTMO_BTCUSD_D1.csv.gz",
        "baseline": (
            "crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert", MX,
        ),
    },
    "redacted_account": {
        "profile": "redacted_account",
        "server": "redacted_account-Server 2",
        "bars": "redacted_account_BTCUSD_D1.csv.gz",
        "baseline": (
            "crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert",
        ),
    },
}

# Only evidence-supported, currently-unarmed direct extensions.  This is deliberately not
# "all registry names": a default-off generator with a historical idea is not an arming
# candidate until an existing receipt supports the extension.  Incubation cells are carried
# in a separate CL receipt and do not enter this direct-arming price grid.
EXTENSIONS = {
    "fx_jpy": {"sleeves": ("fx_jpy",), "weights": {"fx_jpy": 0.15}},
    "fx_jpy_ny": {"sleeves": ("fx_jpy_ny",), "weights": {"fx_jpy_ny": 0.15}},
    "fx_jpy_pair": {
        "sleeves": ("fx_jpy", "fx_jpy_ny"),
        "weights": {"fx_jpy": 0.15, "fx_jpy_ny": 0.15},
    },
    # AE's decision is DOWN_WEIGHT x0.50, so the only honest price is the evidence-directed
    # 0.50 weight rather than the stale 1.00 registry confidence.
    "metals_core_downweighted": {
        "sleeves": ("metals_core",), "weights": {"metals_core": 0.50},
    },
    # AE says KEEP, while the per-account survivor artifact says carry-conditional.  It is
    # enumerated and priced, not recommended.
    "metals_softband": {
        "sleeves": ("metals_softband",), "weights": {"metals_softband": 0.50},
    },
    "mx_btcusd_target5": {"sleeves": (MX,), "weights": {MX: 0.025}},
    "vp_euidx_pocgrav": {
        "sleeves": ("vp_euidx_pocgrav",), "weights": {"vp_euidx_pocgrav": 0.30},
    },
}

WINDOWS = {
    "OUT_OF_WINDOW_PRE_2025": (dt.date(2015, 1, 1), dt.date(2024, 12, 31)),
    "IN_WINDOW_USED_ONCE_2025_PLUS": (dt.date(2025, 1, 1), VAL_END),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def date_of(raw: Any) -> dt.date:
    return dt.date.fromisoformat(str(raw)[:10])


def datetime_of(raw: Any) -> dt.datetime:
    value = dt.datetime.fromisoformat(str(raw))
    return value if value.tzinfo else value.replace(tzinfo=dt.timezone.utc)


def interval_hits_blackout(a: dt.date | dt.datetime, b: dt.date | dt.datetime) -> bool:
    ad = a.date() if isinstance(a, dt.datetime) else a
    bd = b.date() if isinstance(b, dt.datetime) else b
    lo, hi = sorted((ad, bd))
    return not (hi < BLACKOUT[0] or lo > BLACKOUT[1])


def eligible_day(day: dt.date) -> bool:
    return DATA_START <= day <= VAL_END and not (BLACKOUT[0] <= day <= BLACKOUT[1])


def resolvers() -> dict[str, Any]:
    # Read-only.  The two token-bound files remain byte-identical; this merely applies the
    # already-committed profile mapping so cost_r receives broker symbols, not research names.
    base = yaml.safe_load((REPO / "config/agent_config.yaml").read_text()) or {}
    return {
        account: build_broker_symbol_resolver(
            apply_profile_overrides(base, str(meta["profile"])))
        for account, meta in ACCOUNTS.items()
    }


def safe_estate_records() -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    """Project estate rows after the TEST checks and before touching outcome fields."""
    doc = json.loads(gzip.open(ESTATE, "rt").read())
    projected: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    seen = kept = 0
    dropped = collections.Counter()
    for sleeve, rows in (doc.get("trades") or {}).items():
        for row in rows:
            seen += 1
            # These are intent/timestamp fields.  No outcome key is indexed above this fence.
            decision = date_of(row["decision_day"])
            entry = datetime_of(row["entry_utc"])
            exit_ = datetime_of(row["exit_utc"])
            if decision < DATA_START or decision > VAL_END:
                dropped["outside_train_val"] += 1
                continue
            if interval_hits_blackout(entry, exit_) or not eligible_day(decision):
                dropped["label_or_decision_intersects_protected_month"] += 1
                continue
            projected[sleeve].append({
                "sleeve": str(row["sleeve"]),
                "symbol": str(row["symbol"]),
                "symbol_canonical": str(row.get("symbol_canonical") or row["symbol"]),
                "entry_utc": entry,
                "exit_utc": exit_,
                "direction": int(row["direction"]),
                "sl_distance_price": float(row["sl_distance_price"]),
                "entry_price": float(row["entry_price"]),
                # First outcome access in this function.  Poison in a protected row must
                # never reach this conversion; a focused test pins that order.
                "r_gross": float(row["r_gross"]),
                "decision_day": decision,
            })
            kept += 1
    return dict(projected), {
        "rows_seen": seen,
        "rows_projected": kept,
        "rows_dropped": dict(sorted(dropped.items())),
        "protected_outcome_fields_accessed": 0,
        "reader_order": "decision_entry_exit_before_r_gross",
    }


def generate_mx_target5(account: str, ch: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Regenerate the live target-5R cell on one broker through CH's safe bar reader."""
    meta = ACCOUNTS[account]
    series = ch.load_safe_series(
        BARS / str(meta["bars"]), symbol="BTCUSD", timeframe=ch.TF_D1,
        server=str(meta["server"]),
    )
    base = yaml.safe_load((REPO / "config/agent_config.yaml").read_text()) or {}
    merged = apply_profile_overrides(base, str(meta["profile"]))
    runtime = dict(merged.get("gtos_vnext_runtime") or {})
    runtime.update({
        "ultimate_book_include_market_expansion_book": True,
        "ultimate_book_market_expansion_policy": "explicit_allowlist",
        "ultimate_book_market_expansion_sleeves": [MX],
    })
    source = InMemoryBarSource(label=f"CL {account} BTC D1 TEST-sanitized")
    source.add("BTCUSD", ch.TF_D1, [
        {"time": t.isoformat(), "open": b.o, "high": b.h, "low": b.l,
         "close": b.c, "volume": b.v}
        for t, b in zip(series.times, series.bars)
    ])
    resolver = build_broker_symbol_resolver(merged)
    port = GenerationPort(runtime, source, namespace=f"cl_{account.lower()}_btc",
                          account=account, broker_symbol=resolver)
    if MX not in port.active_sleeve_names():
        raise RuntimeError(f"{account}: {MX} absent from the in-memory generation port")

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    drops = collections.Counter()
    for i in range(19, len(series.bars) - ch.MAX_D1 - 1):
        now = series.times[i + 1]
        decision = series.times[i].date()
        if decision < DATA_START:
            continue
        if decision > VAL_END:
            break  # no generator or outcome access on the live-forward tail
        if series.times[i + ch.MAX_D1].date() > VAL_END:
            drops["max_label_path_exits_val"] += 1
            continue
        if ch.interval_hits_blackout(series.times[i - 19], series.times[i + ch.MAX_D1]):
            drops["generator_or_label_shoulder_intersects_protected_month"] += 1
            continue
        got = port.generate(now, tags=[MX])
        for cand in got.candidates:
            if cand.sleeve != MX or not cand.decision_bar_iso:
                continue
            key = str(cand.decision_bar_iso)
            if key in seen:
                continue
            seen.add(key)
            stamp = dt.datetime.fromisoformat(key)
            j = bisect.bisect_left(series.times, stamp)
            if j >= len(series.times) or series.times[j] != stamp:
                drops["generated_decision_bar_absent"] += 1
                continue
            intent = {
                "sleeve": MX, "symbol": cand.symbol, "symbol_canonical": "BTCUSD",
                "direction": cand.direction, "sl_distance_price": cand.stop_dist,
                "target_dist": cand.target_dist, "decision_bar_iso": key,
                "decision_day": cand.decision_day,
                "entry_utc": (series.times[j] + dt.timedelta(days=1)).isoformat(),
                "timeframe": ch.TF_D1,
            }
            labelled = ch._replay_intent(
                intent, series, j, target_r=5.0, maxbars=ch.MAX_D1,
                row_id=f"{MX}:{account}:{key}",
            )
            rows.append({
                "sleeve": MX, "symbol": str(labelled["symbol"]),
                "symbol_canonical": "BTCUSD",
                "entry_utc": datetime_of(labelled["entry_utc"]),
                "exit_utc": datetime_of(labelled["exit_utc"]),
                "direction": int(labelled["direction"]),
                "sl_distance_price": float(labelled["sl_distance_price"]),
                "entry_price": float(labelled["entry_price"]),
                "r_gross": float(labelled["r_gross"]),
                "decision_day": date_of(labelled["decision_day"]),
            })
    return rows, {
        "source": series.evidence(),
        "n_target5_rows": len(rows),
        "drops": dict(sorted(drops.items())),
        "generation_port": port.describe(),
        "protected_ohlc_decoded": 0,
        "live_forward_outcome_accessed": 0,
    }


def to_trade(row: Mapping[str, Any], resolver: Any) -> TradeRecord:
    canonical = str(row.get("symbol_canonical") or row["symbol"])
    return TradeRecord(
        sleeve=str(row["sleeve"]), symbol=str(resolver(canonical)),
        entry_utc=row["entry_utc"], exit_utc=row["exit_utc"],
        direction=int(row["direction"]),
        sl_distance_price=float(row["sl_distance_price"]),
        entry_price=float(row["entry_price"]), r_gross=float(row["r_gross"]),
        features={"decision_day": row["decision_day"], "symbol_canonical": canonical},
    )


def price_account(
    account: str,
    estate: Mapping[str, Sequence[Mapping[str, Any]]],
    mx_rows: Sequence[Mapping[str, Any]],
    resolver: Any,
    survivor: Mapping[str, Any],
) -> tuple[dict[str, dict[str, dict[str, float]]], dict[str, Any]]:
    """Return sleeve -> carry basis -> day -> mean net R, at this account's costs."""
    source = {s: list(rows) for s, rows in estate.items()}
    source[MX] = list(mx_rows)  # target5 replaces the estate's as-walked 2R cell
    wanted = set(ACCOUNTS[account]["baseline"])
    for spec in EXTENSIONS.values():
        wanted.update(spec["sleeves"])
    trades = [to_trade(r, resolver) for s in sorted(wanted) for r in source.get(s, ())]
    spec = OPTIONS["B_balanced"].with_(
        spec_id=f"cl_pass_surface_{account.lower()}", account=account,
        spread_band="mid",
    )
    priced, coverage = price_trades(trades, spec, costs=load_broker_true_costs(COSTS))
    actual: dict[str, dict[str, list[float]]] = collections.defaultdict(
        lambda: collections.defaultdict(list))
    worst: dict[str, dict[str, list[float]]] = collections.defaultdict(
        lambda: collections.defaultdict(list))
    stress = survivor["accounts"][account]["sleeves"]
    for p in priced:
        if p.status != "priced" or p.r_net is None:
            continue
        sleeve = p.trade.sleeve
        day = p.trade.day(spec.day_key).isoformat()
        actual[sleeve][day].append(float(p.r_net))
        components = p.components or {}
        swap_actual = float(components.get("swap_r", 0.0))
        rec = stress.get(sleeve) or {}
        per_night = rec.get("swap_r_per_night")
        max_nights = rec.get("max_nights")
        if per_night is None or max_nights is None:
            stressed = float(p.r_net)  # mx has no W7 carry row; retain replay-realized carry
        else:
            stressed = float(p.r_net) + swap_actual - float(per_night) * float(max_nights)
        worst[sleeve][day].append(stressed)

    def collapse(src: Mapping[str, Mapping[str, Sequence[float]]]) -> dict[str, dict[str, float]]:
        return {
            sleeve: {day: statistics.fmean(vals) for day, vals in sorted(days.items())}
            for sleeve, days in sorted(src.items())
        }

    out = {
        sleeve: {
            "ACTUAL_REALIZED_HOLD": collapse(actual).get(sleeve, {}),
            "W7_MAX_CARRY_STRESS": collapse(worst).get(sleeve, {}),
        }
        for sleeve in sorted(wanted)
    }
    return out, {
        "account": account,
        "spread_band": "mid",
        "cost_artifact": str(COSTS.relative_to(REPO)),
        "cost_artifact_sha256": sha256(COSTS),
        "coverage": {k: v.as_dict() for k, v in sorted(coverage.items())},
        "worst_carry_method": (
            "replace each priced W7 trade's realized swap_r with the account-specific "
            "SURVIVOR_BOOK_V1 swap_r_per_night * max_nights; mx@target5 has no W7 carry "
            "row and retains replay-realized carry"
        ),
    }


def half_kelly(active_count: int) -> float:
    for lo, hi, mult in ADM.KELLY_LITE_BINS_HALF:
        if lo <= active_count <= hi:
            return float(mult)
    return 1.0


def window_months(start: dt.date, end: dt.date) -> int:
    count = 0
    cursor = dt.date(start.year, start.month, 1)
    while cursor <= end:
        if not (cursor.year == 2026 and cursor.month == 3):
            count += 1
        cursor = (dt.date(cursor.year + 1, 1, 1) if cursor.month == 12
                  else dt.date(cursor.year, cursor.month + 1, 1))
    return count


def eligible_weekdays(start: dt.date, end: dt.date) -> int:
    return sum(
        1 for n in range((end - start).days + 1)
        if (start + dt.timedelta(days=n)).weekday() < 5
        and not (BLACKOUT[0] <= start + dt.timedelta(days=n) <= BLACKOUT[1])
    )


def compose(
    daily: Mapping[str, Mapping[str, Mapping[str, float]]],
    sleeves: Sequence[str],
    weights: Mapping[str, float],
    carry: str,
    start: dt.date,
    end: dt.date,
) -> tuple[list[float], dict[str, Any]]:
    days = sorted({
        day for sleeve in sleeves for day in (daily.get(sleeve, {}).get(carry, {}) or {})
        if start <= date_of(day) <= end
    })
    comb: list[float] = []
    for day in days:
        vals = [float(daily.get(s, {}).get(carry, {}).get(day, 0.0)) * float(weights[s])
                for s in sleeves]
        n_active = sum(abs(v) > 1e-12 for v in vals)
        comb.append(sum(vals) * half_kelly(n_active))
    if not comb:
        return [], {"book_days": 0}
    return comb, {
        "book_days": len(comb),
        "eligible_weekday_sessions": eligible_weekdays(start, end),
        "eligible_calendar_months": window_months(start, end),
        "mean_unit_r_per_book_day": statistics.fmean(comb),
        "worst_unit_r_day": min(comb),
        "first_book_day": days[0],
        "last_book_day": days[-1],
    }


def mc_cell(comb: Sequence[float], cell: Mapping[str, Any], account: str, paths: int) -> dict[str, Any]:
    if not comb:
        return {"status": "NOT_PRICEABLE", "reason": "no broker-priced daily series"}
    risk = DIAL
    result: dict[str, Any] = {"status": "PRICED", **cell, "eff_risk_pct": risk * 100}
    result["expected_pct_per_calendar_month"] = round(
        float(cell["mean_unit_r_per_book_day"]) * risk
        * float(cell["book_days"]) / float(cell["eligible_calendar_months"]) * 100,
        6,
    )
    rules = {r.label: r for r in Q.rule_sets(account)[0]}
    for label, out_key in (("L4_FIRM_TRUE_PH1", "phase1"), ("P2_BOTH_PHASES", "two_step")):
        got = Q.mc(list(comb), risk, rules[label], paths, seed_base=1)
        median = got["med_days_pass"]
        result[out_key] = {
            "p_pass": round(got["p_pass"], 6),
            "se_p_pass": round(got["se_p_pass"], 6),
            "p_fail_dd": round(got["p_fail_dd"], 6),
            "p_fail_daily": round(got["p_fail_daily"], 6),
            "p_timeout": round(got["p_timeout"], 6),
            "median_book_days_to_pass": median,
            "median_calendar_days_to_pass": (
                round(median * int(cell["eligible_weekday_sessions"]) / int(cell["book_days"]))
                if median else None
            ),
            "payout_clock_statistic": "median calendar days among passing paths",
        }
    return result


def registry_weights() -> dict[str, float]:
    out = {k: float(v.confidence) for k, v in ADM.SLEEVE_REGISTRY.items()}
    out.update({k: float(v.confidence) for k, v in ADM.CLEAN3_REGISTRY.items()})
    mx, err = ADM.resolve_market_expansion_sleeves(
        policy="positive_weighted12_after_swap", explicit_sleeves=())
    if err:
        raise RuntimeError(err)
    out.update({k: float(v.confidence) for k, v in ADM.market_expansion_registry(mx).items()})
    return out


def evidence_disposition(account: str, name: str, has_series: bool) -> dict[str, Any]:
    if name == "vp_euidx_pocgrav":
        return {
            "decision": "DO_NOT_ARM",
            "reason": ("CI solved time depth but the UK100 POC comparability gate still fails; "
                       "this archive-estate repricing is descriptive and cannot substitute for "
                       "an admissible broker-comparable outcome series"),
            "source": str(CI_RESULT.relative_to(REPO)),
        }
    if name in ("fx_jpy", "fx_jpy_ny", "fx_jpy_pair"):
        return {
            "decision": "DO_NOT_ARM",
            "reason": ("AE's broker-true learning actuator says GATE x0.00 for both JPY sleeves; "
                       "carry survival is necessary and not sufficient"),
            "source": str(AE_RESULT.relative_to(REPO)),
        }
    if name == "metals_core_downweighted":
        return {
            "decision": "DO_NOT_REINTRODUCE",
            "reason": ("AE says DOWN_WEIGHT x0.50 on a -0.205 R/trade, 232-trade/118-day OOS; "
                       "pricing the half-weight does not overturn that sleeve-level veto"),
            "source": str(AE_RESULT.relative_to(REPO)),
        }
    if name == "metals_softband":
        return {
            "decision": "DO_NOT_ARM",
            "reason": "AE says KEEP, but the per-account artifact remains CARRY_CONDITIONAL on both firms",
            "source": str(SURVIVOR.relative_to(REPO)),
        }
    if name == "mx_btcusd_target5" and account == "redacted_account":
        return {
            "decision": "DO_NOT_ARM",
            "reason": ("CH's broker-local replication generated 193 target-5R candidates and "
                       "REJECTED at low/mid/high; mid OOS is negative"),
            "source": str(CH_MILESTONES.relative_to(REPO)),
        }
    if name == "mx_btcusd_target5":
        return {"decision": "ALREADY_ARMED", "reason": "present in the FTMO baseline"}
    return {"decision": "DO_NOT_ARM" if has_series else "NOT_PRICEABLE"}


def coverage_for(sleeves: Sequence[str], pricing_meta: Mapping[str, Any]) -> dict[str, Any]:
    rows = {
        sleeve: pricing_meta["coverage"].get(sleeve, {
            "coverage_frac": 0.0,
            "n_total": 0,
            "n_priced": 0,
            "n_unpriced": 0,
            "unpriced_reasons": {"no archive candidate series": 1},
        })
        for sleeve in sleeves
    }
    return {
        "complete": all(float(row.get("coverage_frac", 0.0)) == 1.0 for row in rows.values()),
        "sleeves": rows,
    }


def has_window_series(
    daily: Mapping[str, Mapping[str, Mapping[str, float]]],
    sleeve: str,
    carry: str,
    start: dt.date,
    end: dt.date,
) -> bool:
    return any(start <= date_of(day) <= end
               for day in daily.get(sleeve, {}).get(carry, {}))


def build(paths: int) -> dict[str, Any]:
    required = (ESTATE, SURVIVOR, COSTS, CH_DRIVER, CH_MILESTONES)
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"required CL inputs absent: {missing}")
    ch = load_module("cl_ch_safe_driver", CH_DRIVER)
    estate, estate_guard = safe_estate_records()
    resolver = resolvers()
    survivor = json.loads(SURVIVOR.read_text())
    weights = registry_weights()

    account_docs: dict[str, Any] = {}
    for account, meta in ACCOUNTS.items():
        mx_rows, mx_meta = generate_mx_target5(account, ch)
        daily, pricing_meta = price_account(account, estate, mx_rows, resolver[account], survivor)
        baseline = tuple(meta["baseline"])
        base_weights = {s: weights[s] for s in baseline}
        cells: dict[str, Any] = {}
        for carry in ("ACTUAL_REALIZED_HOLD", "W7_MAX_CARRY_STRESS"):
            cells[carry] = {}
            for window, (start, end) in WINDOWS.items():
                comb, shape = compose(daily, baseline, base_weights, carry, start, end)
                base = mc_cell(comb, shape, account, paths)
                base["broker_truth_coverage"] = coverage_for(baseline, pricing_meta)
                variants: dict[str, Any] = {}
                for name, ext in EXTENSIONS.items():
                    if name == "mx_btcusd_target5" and account == "FTMO":
                        variants[name] = {
                            "status": "ALREADY_IN_BASELINE",
                            "disposition": evidence_disposition(account, name, True),
                        }
                        continue
                    sleeves = tuple(dict.fromkeys((*baseline, *ext["sleeves"])))
                    candidate_weights = {**base_weights, **ext["weights"]}
                    missing_series = [
                        sleeve for sleeve in ext["sleeves"]
                        if sleeve not in baseline
                        and not has_window_series(daily, sleeve, carry, start, end)
                    ]
                    if missing_series:
                        variants[name] = {
                            "status": "NOT_PRICEABLE",
                            "reason": "no broker-priced candidate day series in this window",
                            "missing_candidate_series": missing_series,
                            "sleeves": list(sleeves),
                            "weights": candidate_weights,
                            "broker_truth_coverage": coverage_for(sleeves, pricing_meta),
                            "disposition": evidence_disposition(account, name, False),
                        }
                        continue
                    got_comb, got_shape = compose(
                        daily, sleeves, candidate_weights, carry, start, end)
                    got = mc_cell(got_comb, got_shape, account, paths)
                    if got.get("status") == "PRICED" and base.get("status") == "PRICED":
                        got["marginal_vs_current"] = {
                            "phase1_p_pass": round(
                                got["phase1"]["p_pass"] - base["phase1"]["p_pass"], 6),
                            "two_step_p_pass": round(
                                got["two_step"]["p_pass"] - base["two_step"]["p_pass"], 6),
                            "expected_pct_per_calendar_month": round(
                                got["expected_pct_per_calendar_month"]
                                - base["expected_pct_per_calendar_month"], 6),
                            "two_step_calendar_days": (
                                got["two_step"]["median_calendar_days_to_pass"]
                                - base["two_step"]["median_calendar_days_to_pass"]
                                if got["two_step"]["median_calendar_days_to_pass"] is not None
                                and base["two_step"]["median_calendar_days_to_pass"] is not None
                                else None
                            ),
                        }
                        got["marginal_vs_current"][
                            "two_step_median_calendar_days_to_payout"
                        ] = got["marginal_vs_current"]["two_step_calendar_days"]
                        drop = got["marginal_vs_current"]["two_step_p_pass"]
                        got["MATERIAL_TWO_STEP_P_PASS_REDUCTION"] = bool(
                            drop <= -MATERIAL_P2_DROP)
                    got["sleeves"] = list(sleeves)
                    got["weights"] = candidate_weights
                    got["broker_truth_coverage"] = coverage_for(sleeves, pricing_meta)
                    got["disposition"] = evidence_disposition(
                        account, name, got.get("status") == "PRICED")
                    variants[name] = got
                cells[carry][window] = {"CURRENT_ARMED_BASELINE": base, "extensions": variants}
        account_docs[account] = {
            "current_armed_set": list(baseline),
            "current_weights": base_weights,
            "candidate_survivor_tiers": {
                name: {
                    sleeve: (
                        survivor["accounts"][account]["sleeves"].get(sleeve, {})
                        .get("survivor_tier", "NO_W7_SURVIVOR_ROW")
                    )
                    for sleeve in ext["sleeves"]
                }
                for name, ext in EXTENSIONS.items()
            },
            "mx_target5_generation": mx_meta,
            "pricing": pricing_meta,
            "cells": cells,
        }

    # Hard controls: archive VP repricing must never be promoted into admission authority,
    # every result uses the current account baseline, and the TEST reader order is explicit.
    vp_cells = [
        account_docs[a]["cells"][c][w]["extensions"]["vp_euidx_pocgrav"]
        for a in account_docs for c in ("ACTUAL_REALIZED_HOLD", "W7_MAX_CARRY_STRESS")
        for w in WINDOWS
    ]
    controls = {
        "vp_archive_price_never_used_as_admission": all(
            x.get("status") == "NOT_PRICEABLE"
            and x.get("disposition", {}).get("decision") == "DO_NOT_ARM"
            for x in vp_cells),
        "estate_protected_outcome_fields_accessed": estate_guard["protected_outcome_fields_accessed"],
        "mx_protected_ohlc_decoded": sum(
            v["mx_target5_generation"]["protected_ohlc_decoded"] for v in account_docs.values()),
        "mx_live_forward_outcome_accessed": sum(
            v["mx_target5_generation"]["live_forward_outcome_accessed"] for v in account_docs.values()),
        "material_p2_drop_threshold_abs": MATERIAL_P2_DROP,
    }
    if not controls["vp_archive_price_never_used_as_admission"]:
        raise RuntimeError("vp_euidx_pocgrav archive repricing gained promotion authority")
    if any(controls[k] != 0 for k in (
        "estate_protected_outcome_fields_accessed", "mx_protected_ohlc_decoded",
        "mx_live_forward_outcome_accessed",
    )):
        raise RuntimeError(f"TEST access control failed: {controls}")

    return {
        "schema": "gtos.phase17.cl.pass_surface_pricing.v1",
        "session": "CL",
        "blocks": "B2650-B2669",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "arms_nothing": True,
        "approved_direct_additions": {"FTMO": [], "redacted_account": []},
        "question": "what each evidence-supported extension does to the current account book",
        "machinery": {
            "mc": "scripts/mc_firm_rules.py::mc imported unchanged",
            "rules": ["L4_FIRM_TRUE_PH1", "P2_BOTH_PHASES"],
            "n_paths_per_cell": paths,
            "dial": DIAL,
            "kelly": "admission.KELLY_LITE_BINS_HALF",
            "spread_band": "mid",
            "population": "AQ estate, account-repriced; mx regenerated at target_5R per broker",
        },
        "honesty_boundary": {
            "OUT_OF_WINDOW_PRE_2025": "primary expectation; 2015-01-01..2024-12-31",
            "IN_WINDOW_USED_ONCE_2025_PLUS": (
                "selection/VAL description only; 2025-01-01..2026-05-31, protected month "
                "and label shoulders excluded; never promotion evidence"
            ),
            "test": "March 2026 and live-forward observations are outcome-unread",
        },
        "inputs": {str(p.relative_to(REPO) if p.is_relative_to(REPO) else p): sha256(p)
                   for p in required},
        "estate_guard": estate_guard,
        "candidate_inventory": EXTENSIONS,
        "accounts": account_docs,
        "controls": controls,
    }


def render_markdown(doc: Mapping[str, Any]) -> str:
    lines = [
        "# CL pass-surface pricing — firm-true account deltas",
        "",
        f"Tool-emitted from `{doc['generated_by']}` at "
        f"**{doc['machinery']['n_paths_per_cell']:,} paths per MC cell**. This artifact arms "
        "nothing. The direct approved set is **empty on both accounts**.",
        "",
        "The payout-clock column is the inherited MC's **median calendar days among passing "
        "paths**, not an unconditional expectation. A lower number paired with a lower `p_pass` "
        "is survivorship bias, not a faster book.",
        "",
        "March 2026, its label shoulders, and the live-forward stream are outcome-unread. "
        f"The estate reader rejected {doc['estate_guard']['rows_dropped']} before outcome access; "
        "all protected-access counters are zero.",
        "",
    ]
    for account, account_doc in doc["accounts"].items():
        lines += [f"## {account}", ""]
        tiers = account_doc["candidate_survivor_tiers"]
        lines += ["Per-account survivor tiers read from the artifact:", ""]
        for name, sleeve_tiers in tiers.items():
            shown = ", ".join(f"`{s}` = `{tier}`" for s, tier in sleeve_tiers.items())
            lines.append(f"- `{name}`: {shown}")
        lines.append("")
        for carry, carry_doc in account_doc["cells"].items():
            for window, window_doc in carry_doc.items():
                lines += [f"### {carry} — {window}", ""]
                lines += [
                    "| set | L4 phase-1 `p_pass` | P2 two-step `p_pass` | Δ P2 | "
                    "%/calendar month | Δ %/mo | P2 median cal-days | Δ days | coverage | decision |",
                    "|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
                ]
                base = window_doc["CURRENT_ARMED_BASELINE"]
                lines.append(
                    f"| current armed baseline | {base['phase1']['p_pass']:.4f} | "
                    f"{base['two_step']['p_pass']:.4f} | — | "
                    f"{base['expected_pct_per_calendar_month']:.4f} | — | "
                    f"{base['two_step']['median_calendar_days_to_pass']} | — | "
                    f"{'complete' if base['broker_truth_coverage']['complete'] else 'PARTIAL'} | baseline |"
                )
                for name, row in window_doc["extensions"].items():
                    decision = row["disposition"]["decision"]
                    if row["status"] != "PRICED":
                        lines.append(
                            f"| `{name}` | — | — | — | — | — | — | — | "
                            f"{row['status']} | {decision} |"
                        )
                        continue
                    marginal = row["marginal_vs_current"]
                    delta_p2 = f"{marginal['two_step_p_pass']:+.4f}"
                    if row["MATERIAL_TWO_STEP_P_PASS_REDUCTION"]:
                        delta_p2 = f"**{delta_p2}**"
                    lines.append(
                        f"| `{name}` | {row['phase1']['p_pass']:.4f} | "
                        f"{row['two_step']['p_pass']:.4f} | {delta_p2} | "
                        f"{row['expected_pct_per_calendar_month']:.4f} | "
                        f"{marginal['expected_pct_per_calendar_month']:+.4f} | "
                        f"{row['two_step']['median_calendar_days_to_pass']} | "
                        f"{marginal['two_step_calendar_days']:+d} | "
                        f"{'complete' if row['broker_truth_coverage']['complete'] else 'PARTIAL'} | "
                        f"{decision} |"
                    )
                lines.append("")
        gaps = {
            sleeve: row for sleeve, row in account_doc["pricing"]["coverage"].items()
            if float(row["coverage_frac"]) < 1.0
        }
        if gaps:
            lines += [
                "Coverage boundary: this account has incomplete broker truth for "
                + ", ".join(f"`{s}` ({r['coverage_frac']:.1%})" for s, r in gaps.items())
                + ". Its numeric cells describe the priceable broker-supported subset and are "
                "not full-book authority.",
                "",
            ]
    lines += [
        "## Decision",
        "",
        "No direct extension is approved. Carry classification is not admission; AE's actuator "
        "vetoes both JPY sleeves and reintroduction of metals-core, CI leaves VP non-evaluable, "
        "and CH rejects redacted_account target-5R MX. `metals_softband` remains carry-conditional. "
        "Therefore no prospective tag or timeframe delta is justified by this grid.",
        "",
    ]
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", type=int, default=20_000)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--md-out", type=Path, default=MD_OUT)
    args = ap.parse_args(argv)
    if args.paths < 500:
        raise SystemExit("--paths must be >=500; lower counts are not decision-readable")
    doc = build(args.paths)
    args.out.write_text(json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n")
    args.md_out.write_text(render_markdown(doc))
    try:
        shown_out = args.out.relative_to(REPO)
    except ValueError:
        shown_out = args.out
    print(f"wrote {shown_out}")
    for account, rec in doc["accounts"].items():
        for window in WINDOWS:
            base = rec["cells"]["ACTUAL_REALIZED_HOLD"][window]["CURRENT_ARMED_BASELINE"]
            print(f"{account:11s} {window:34s} baseline P2={base['two_step']['p_pass']:.4f} "
                  f"%/mo={base['expected_pct_per_calendar_month']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
