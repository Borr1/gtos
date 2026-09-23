"""h1-01 -- the per-candidate broker-true cost ledger, at full resolution.

Emits one row per candidate carrying EVERY cost term in three units (price, bps of
notional, R) plus every conditioning axis and the repaired-contract gross, so that
h1_02 can tabulate any cell without re-deriving anything.

COST BASIS -- four terms, each with a stated provenance class
------------------------------------------------------------
1. SPREAD   tick-truthed and HOUR-AWARE. `L10X_TICK_SPREAD_V1.json`'s
            `spread_bps_median_by_broker_hour`, FTMO, full population
            (300,538,915 ticks, 2026-06-18..07-24, no sampling), keyed on the
            candidate's own BROKER wall hour. The broker offset is +2 h in
            January/February 2026 and +3 h from 2026-03-08 (US DST, measured via
            src.utils.broker_clock) -- using UTC as the key would mis-bucket the
            rollover spike by two to three hours.
            Convention: ONE full bid/ask crossing per round turn
            (`BROKER_TRUE_COSTS_V1.conventions.spread`, broker_net_cost_engine.py:294).
2. COMMISSION  from the repo's shipped `BROKER_TRUE_COSTS_V1.json` (FTMO), round turn,
            `notional_bp` or `per_lot`, converted to price units through
            `usd_per_price_unit_per_lot`. THIS IS NOT the basis the swarm used: e_lib's
            `_CRYPTO_BPS` normalises a live-window price-unit measurement by a JANUARY
            price, which understates BTCUSD commission 1.47x (see h1_RESULT.md H1-F9).
3. SLIPPAGE  measured price-unit entry slippage per symbol from real broker deals
            (`L10X_LIVE_COST_PRICEUNITS_V1.json`, 12 symbols), clamped at >= 0; for the
            other 12 the class median in bps of price. Basis stamped per row.
4. SWAP     adverse swap per rollover crossing, side-aware, from the instrument spec
            (`swap_long`/`swap_short`, `swap_mode`, `point`). Charged per CROSSING of the
            broker's 00:00, not per elapsed hour (BROKER_TRUE_COSTS_V1.conventions.swap).
            The pool's horizon is 2 h so most rows cross nothing -- but the rows decided
            in the two broker hours before midnight DO, and that is an hour-of-day cost
            term nothing in this estate has ever charged.

ERA: the tick archive is a 37-day 2026Q2/Q3 window and the pool is 2026 Q1. The
`era_ratio` from src/costs/spread_model.py (bar-recorded, ratios only) is carried per
(symbol, month) as a SENSITIVITY column -- never silently folded into the headline.

usage: python3 h1_01_cost_rows.py
"""
from __future__ import annotations

import gzip
import json
import os
import statistics as st
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

D = os.path.dirname(os.path.abspath(__file__))
ROOT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
sys.path.insert(0, ROOT)

from src.utils.broker_clock import resolve_rule, utc_to_broker_naive  # noqa: E402

SERVER = resolve_rule("FTMO-Server3")
TICK = json.load(open(f"{D}/L10X_TICK_SPREAD_V1.json"))
LIVE = json.load(open(f"{D}/L10X_LIVE_COST_PRICEUNITS_V1.json"))
BT = json.load(open("/tmp/BTC_V1.json"))["accounts"]["FTMO"]["instruments"]

# pool symbol -> tick-archive series (FTMO)
TMAP = {"XAUUSD": "XAUUSD", "UK100": "UK100_cash", "SPX500": "US500_cash",
        "NAS100": "US100_cash", "US30_cash": "US30_cash", "GBPUSD": "GBPUSD",
        "GER40": "GER40_cash", "JP225": "JP225_cash", "USDCAD": "USDCAD",
        "BTCUSD": "BTCUSD", "EURJPY": "EURJPY", "ETHUSD": "ETHUSD", "XAGUSD": "XAGUSD",
        "USDCHF": "USDCHF", "USDJPY": "USDJPY", "EURGBP": "EURGBP", "NZDUSD": "NZDUSD",
        "EURUSD": "EURUSD", "UKOIL_cash": "UKOIL_cash", "GBPJPY": "GBPJPY",
        "AUDJPY": "AUDJPY", "USOIL_cash": "USOIL_cash", "AUDUSD": "AUDUSD",
        "CHFJPY": "CHFJPY"}
# pool symbol -> BROKER_TRUE_COSTS_V1 instrument key (FTMO)
BMAP = {"XAUUSD": "XAUUSD", "SPX500": "US500.cash", "NAS100": "US100.cash",
        "US30_cash": "US30.cash", "UK100": "UK100.cash", "GER40": "GER40.cash",
        "JP225": "JP225.cash", "BTCUSD": "BTCUSD", "ETHUSD": "ETHUSD",
        "XAGUSD": "XAGUSD", "USDJPY": "USDJPY", "GBPUSD": "GBPUSD",
        "USDCAD": "USDCAD", "USDCHF": "USDCHF", "NZDUSD": "NZDUSD",
        "UKOIL_cash": "UKOIL.cash", "EURUSD": "EURUSD", "USOIL_cash": "USOIL.cash",
        "GBPJPY": "GBPJPY", "EURGBP": "EURGBP", "AUDJPY": "AUDJPY",
        "EURJPY": "EURJPY", "AUDUSD": "AUDUSD", "CHFJPY": "CHFJPY"}
# pool symbol -> l10 measured live price-unit slippage key
SLIPMAP = {"XAUUSD": "ftmo:XAUUSD", "SPX500": "ftmo:US500.cash",
           "US30_cash": "ftmo:US30.cash", "UK100": "ftmo:UK100.cash",
           "GER40": "ftmo:GER40.cash", "JP225": "ftmo:JP225.cash",
           "BTCUSD": "ftmo:BTCUSD", "ETHUSD": "ftmo:ETHUSD", "EURUSD": "ftmo:EURUSD",
           "GBPUSD": "ftmo:GBPUSD", "USDJPY": "ftmo:USDJPY", "GBPJPY": "ftmo:GBPJPY"}

MONTHS = {"JAN": "2026-01", "FEB": "2026-02", "MAR": "2026-03"}


# ----------------------------------------------------------------- cost terms
def broker_wall(dt_iso):
    u = datetime.fromisoformat(dt_iso)
    if u.tzinfo is None:
        u = u.replace(tzinfo=timezone.utc)
    return utc_to_broker_naive(u, SERVER)


def spread_bps(sym, broker_hour):
    """(hour-aware bps, flat-median bps, basis)."""
    tk = TICK.get("ftmo:" + TMAP.get(sym, sym))
    if not tk:
        return None, None, "NO_TICK_SERIES"
    flat = tk.get("spread_bps_median")
    byh = tk.get("spread_bps_median_by_broker_hour") or {}
    nbyh = tk.get("n_by_broker_hour") or {}
    h = byh.get(str(broker_hour))
    n = nbyh.get(str(broker_hour), 0)
    if h is None or n < 500:          # a thin hour is not a measurement
        return flat, flat, "MEASURED_TICK_FLAT_THIN_HOUR"
    return h, flat, "MEASURED_TICK_BY_BROKER_HOUR"


def comm_px(sym, entry_price):
    rec = BT.get(BMAP.get(sym, sym))
    if rec is None:
        return None, "NO_BROKER_RECORD"
    blk = rec["commission"]
    kind = blk.get("kind")
    upu = float(rec.get("usd_per_price_unit_per_lot") or 0.0)
    cov = blk.get("coverage")
    if kind == "zero":
        return 0.0, f"BROKER_TRUE_ZERO[{cov}]"
    if not upu:
        return None, "NO_CASH_TO_PRICE_CONVERSION"
    if kind == "per_lot":
        return float(blk["value"]) / upu, f"BROKER_TRUE_PER_LOT[{cov}]"
    if kind == "notional_bp":
        cs = float((rec.get("spec") or {}).get("trade_contract_size") or 0.0)
        if not cs:
            return None, "NO_CONTRACT_SIZE"
        usd = float(blk["value"]) / 1e4 * cs * float(entry_price)
        return usd / upu, f"BROKER_TRUE_NOTIONAL_BP[{cov}]"
    return None, f"UNKNOWN_KIND_{kind}"


def swap_px_per_night(sym, side, entry_price):
    rec = BT.get(BMAP.get(sym, sym))
    if rec is None:
        return None, "NO_BROKER_RECORD"
    spec = rec.get("spec") or {}
    raw = spec.get("swap_long" if str(side).upper() in ("LONG", "BUY") else "swap_short")
    mode = spec.get("swap_mode")
    if raw is None or mode is None:
        return None, "NO_SWAP_SPEC"
    if float(raw) >= 0:
        return 0.0, "FAVOURABLE_OR_ZERO"
    adv = abs(float(raw))
    if int(mode) == 1:
        pt = spec.get("point")
        if not pt:
            return None, "NO_POINT"
        return adv * float(pt), "SPEC_POINTS"
    if int(mode) in (5, 6):
        return float(entry_price) * (adv / 100.0) / 360.0, "SPEC_ANNUAL_PCT"
    return None, f"UNKNOWN_SWAP_MODE_{mode}"


def rollover_crossings(dt_iso, hold_minutes=120):
    """How many broker 00:00 boundaries a `hold_minutes` hold crosses, and the triple-swap
    weight (Wednesday->Thursday rollover carries 3 nights on MT5 mode 3)."""
    w0 = broker_wall(dt_iso)
    w1 = w0 + timedelta(minutes=hold_minutes)
    n = 0
    nights = 0.0
    d = w0.date()
    while True:
        d = d + timedelta(days=1)
        b = datetime(d.year, d.month, d.day)
        if b > w1:
            break
        n += 1
        # MT5 ENUM_DAY_OF_WEEK: the rollover INTO this date. swap_rollover3days=3 means the
        # Wednesday->Thursday crossing is charged 3x.
        nights += 3.0 if b.weekday() == 3 else 1.0
    return n, nights


# ------------------------------------------------- slippage: measured + class fallback
def build_slip_table():
    out, bps_by_class = {}, defaultdict(list)
    for sym in TMAP:
        rec = BT.get(BMAP.get(sym, sym)) or {}
        klass = rec.get("instrument_class")
        k = SLIPMAP.get(sym)
        px = (LIVE.get(k) or {}).get("slip_px") if k else None
        mid = ((rec.get("spread_price") or {}).get("mid_price_median"))
        if px is not None and mid:
            v = max(float(px), 0.0)
            out[sym] = (v / float(mid) * 1e4, "MEASURED_LIVE_DEALS")
            bps_by_class[klass].append(v / float(mid) * 1e4)
    cls_med = {k: st.median(v) for k, v in bps_by_class.items() if v}
    glob = st.median([x for v in bps_by_class.values() for x in v])
    for sym in TMAP:
        if sym in out:
            continue
        klass = (BT.get(BMAP.get(sym, sym)) or {}).get("instrument_class")
        out[sym] = (cls_med.get(klass, glob),
                    f"MODELLED_CLASS_MEDIAN[{klass}]" if klass in cls_med
                    else "MODELLED_GLOBAL_MEDIAN")
    return out, cls_med, glob


SLIP_BPS, SLIP_CLS, SLIP_GLOB = build_slip_table()


# ------------------------------------------------------------------- era ratios
def build_era_table():
    from src.costs.spread_model import load_spread_model, SpreadModelError
    m = load_spread_model()
    ERA_SYM = {"SPX500": "US500.cash", "NAS100": "US100.cash", "US30_cash": "US30.cash",
               "UK100": "UK100.cash", "GER40": "GER40.cash", "JP225": "JP225.cash",
               "UKOIL_cash": "UKOIL.cash", "USOIL_cash": "USOIL.cash"}
    out = {}
    for sym in TMAP:
        for mk, ym in MONTHS.items():
            t = datetime(int(ym[:4]), int(ym[5:7]), 15, 12, tzinfo=timezone.utc)
            try:
                e = m.estimate(ERA_SYM.get(sym, sym), "FTMO", t, band="mid")
                lo = m.estimate(ERA_SYM.get(sym, sym), "FTMO", t, band="low")
                hi = m.estimate(ERA_SYM.get(sym, sym), "FTMO", t, band="high")
                out[(sym, mk)] = {"era_ratio": e.era_ratio, "era": e.era,
                                  "era_class": e.era_class, "decidable": e.decidable,
                                  "coverage": e.coverage.value,
                                  "era_ratio_low": lo.era_ratio,
                                  "era_ratio_high": hi.era_ratio}
            except SpreadModelError as exc:
                out[(sym, mk)] = {"era_ratio": 1.0, "era": None,
                                  "era_class": "UNPRICEABLE", "decidable": False,
                                  "coverage": "MODELLED", "err": str(exc)[:120],
                                  "era_ratio_low": 1.0, "era_ratio_high": 1.0}
    return out


ERA = build_era_table()


# ------------------------------------------------------------------- zone joins
def load_zones():
    z = {}
    srcs = [
        (f"{ROOT}/docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/"
         "CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"),
        (f"{ROOT}/docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/"
         "CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz"),
        f"{D}/h1_MAR_ZONES_V1.jsonl.gz",
    ]
    for p in srcs:
        if not os.path.isfile(p):
            continue
        for line in gzip.open(p, "rt"):
            if not line.strip():
                continue
            r = json.loads(line)
            z[(r.get("candidate_id"), r.get("decision_time_utc"))] = {
                "kill_zone": r.get("kill_zone"),
                "session_bucket": r.get("session_bucket"),
                "authority_session": r.get("authority_session"),
                "utc_hour_bucket": r.get("utc_hour_bucket"),
                "decision_timeframe": r.get("decision_timeframe"),
            }
    return z


ZONES = load_zones()


# --------------------------------------------------------------------- main
CONTRACT_KEYS = ["K0_INC", "K0_TRAIL025", "K1_TRAIL025", "K2_TRAIL025", "K3_TRAIL025",
                 "K5_TRAIL025", "K10_TRAIL025", "K15_TRAIL025", "K20_TRAIL025",
                 "K30_TRAIL025", "K45_TRAIL025", "K60_TRAIL025", "K5_INC", "K5_STOPONLY",
                 "K0_STOPONLY", "K5_TS90S1", "K5_T3S1"]


def main():
    t0 = time.time()
    outp = f"{D}/h1_COST_ROWS_V1.jsonl.gz"
    out = gzip.open(outp, "wt")
    n = 0
    bad = defaultdict(int)
    basis = defaultdict(int)
    for mk in MONTHS:
        for line in gzip.open(f"{D}/e_{mk}_ATMKT_V1.jsonl.gz", "rt"):
            if not line.strip():
                continue
            r = json.loads(line)
            sym, ep, rd = r["symbol"], float(r["entry_price"]), float(r["risk_distance"])
            w = broker_wall(r["dt"])
            bh = w.hour
            sp_h, sp_f, sp_basis = spread_bps(sym, bh)
            if sp_h is None:
                bad["no_spread"] += 1
                continue
            cm, cm_basis = comm_px(sym, ep)
            if cm is None:
                bad["no_comm"] += 1
                cm, cm_basis = 0.0, "UNPRICED_ZERO"
            sl_bps, sl_basis = SLIP_BPS.get(sym, (0.0, "UNPRICED_ZERO"))
            sw_night, sw_basis = swap_px_per_night(sym, r["side"], ep)
            ncross, nnights = rollover_crossings(r["dt"], 120)
            sw = (sw_night or 0.0) * nnights
            era = ERA.get((sym, mk), {})

            spread_px = sp_h * ep / 1e4
            spread_px_flat = sp_f * ep / 1e4
            slip_px = sl_bps * ep / 1e4
            tot_px = spread_px + cm + slip_px + sw
            tot_px_noswap = spread_px + cm + slip_px

            o = {
                "month": mk, "cid": r["cid"], "dt": r["dt"], "day": r["day"],
                "utc_hour": r["hour"], "broker_hour": bh,
                "broker_dow": w.weekday(), "utc_dow": datetime.fromisoformat(r["dt"]).weekday(),
                "symbol": sym, "side": r["side"], "family": r["family"],
                "session": r["session"],
                "instrument_class": (BT.get(BMAP.get(sym, sym)) or {}).get("instrument_class"),
                "entry_price": ep, "risk_distance": rd, "rdp": rd / ep,
                # -------- price units
                "spread_px": spread_px, "spread_px_flat": spread_px_flat,
                "comm_px": cm, "slip_px": slip_px, "swap_px": sw,
                "total_px": tot_px, "total_px_noswap": tot_px_noswap,
                # -------- bps of notional
                "spread_bps": sp_h, "spread_bps_flat": sp_f,
                "comm_bps": cm / ep * 1e4, "slip_bps": sl_bps,
                "swap_bps": sw / ep * 1e4,
                "total_bps": tot_px / ep * 1e4,
                # -------- R
                "spread_r": spread_px / rd, "comm_r": cm / rd, "slip_r": slip_px / rd,
                "swap_r": sw / rd, "total_r": tot_px / rd,
                "total_r_noswap": tot_px_noswap / rd,
                "total_r_flat": (spread_px_flat + cm + slip_px) / rd,
                # -------- era sensitivity
                "era_ratio": era.get("era_ratio"), "era_class": era.get("era_class"),
                "era_decidable": era.get("decidable"),
                "total_r_era": ((spread_px * (era.get("era_ratio") or 1.0)) + cm + slip_px) / rd,
                "total_bps_era": ((spread_px * (era.get("era_ratio") or 1.0)) + cm + slip_px) / ep * 1e4,
                # -------- rollover
                "rollover_crossings": ncross, "rollover_nights": nnights,
                "swap_night_px": sw_night,
                # -------- frozen comparator
                "cost_frozen_r": r.get("cost_frozen"),
                "swarm_cost_true_r": r.get("cost_true"),
                # -------- bases
                "spread_basis": sp_basis, "comm_basis": cm_basis,
                "slip_basis": sl_basis, "swap_basis": sw_basis,
            }
            for k in CONTRACT_KEYS:
                if k in r:
                    o[k] = r[k]
            z = ZONES.get((r["cid"], r["dt"]))
            if z:
                o.update(z)
            else:
                bad["no_zone"] += 1
            basis[sp_basis] += 1
            basis[cm_basis] += 1
            basis[sl_basis] += 1
            out.write(json.dumps(o) + "\n")
            n += 1
    out.close()
    rec = {"rows": n, "dropped": dict(bad), "basis_counts": dict(basis),
           "slip_class_median_bps": SLIP_CLS, "slip_global_median_bps": SLIP_GLOB,
           "slip_table_bps": {k: v for k, v in sorted(SLIP_BPS.items())},
           "era_table": {f"{k[0]}|{k[1]}": v for k, v in sorted(ERA.items())},
           "seconds": round(time.time() - t0, 1), "out": outp}
    json.dump(rec, open(f"{D}/h1_COST_ROWS_V1_BUILD.json", "w"), indent=1, default=str)
    print(json.dumps({k: rec[k] for k in ("rows", "dropped", "basis_counts", "seconds")},
                     indent=1))


if __name__ == "__main__":
    main()
