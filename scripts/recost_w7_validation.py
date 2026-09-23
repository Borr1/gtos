"""Re-cost the W7 core-book validation at broker-true costs (Stage 1.2, Session N).

    python3 scripts/recost_w7_validation.py --out research/operations/w7_recost_2026_07_27

WHAT THIS IS. The W7 book's 2015-2026 validation is the programme's only positive
full-window result, and `THIRD_REVIEW.md` §1.2 calls it *invalid rather than negative* --
contaminated by a cost model that charges zero commission (F38) and an erosion step that
credits cost back (F39). This restates it against `src.costs.cost_r`, per account, and
publishes what survives.

THE ARITHMETIC, AND WHY IT IS EXACT
-----------------------------------
`geometry_lib.simulate` subtracts a scalar cost in R at the end of every trade
(`:36,38,43,44,53,55,60,61`), and `wins()` clips the result to [-1.3, +5]. So for every
cached row

    R_cached  =  wins(R_geometric - charged_cost_r)

The winsor is **inert on this book** -- asserted at runtime, not assumed: the extreme
cached values are -1.1601 and +4.8111, both strictly inside the clip. Therefore

    R_gross  =  R_cached + charged_cost_r          [exact, every row]
    R_true   =  R_gross  - true_cost_r

and `charged_cost_r` is recoverable two independent ways: from source (the class map in
`ULTIMATE_REAL_COST_MAP.json` through `w1.cost_for`, divided by each sleeve's `stop_atr`)
and from the data (a full stop-out books exactly `-1 - charged_cost_r`). Both are computed
and required to agree, because a silent disagreement here would corrupt every downstream
number.

Note what this makes irrelevant: **the F39 "what did the map contain" band does not reach
this restatement.** Whatever the map's 0.0459 *meant*, 0.0459 is what was subtracted, so
adding it back recovers the geometric R either way. The band is published where it does
bite -- on the size of the erosion-step error -- not here. See `f39_band` in the output.

STOP DISTANCE IS THE WHOLE PROBLEM
----------------------------------
Commission in R is `usd_per_lot / (sl_distance_price * usd_per_price_unit_per_lot)`, so it
is a property of the trade, not the instrument (`src/costs/model.py:16-22`, B112). The
caches carry no stop distance. Three tiers, each stamped on every row:

  T1_LEDGER    exact `resim.sd` from `D4_COMBINED_TRADE_LEDGER.jsonl`, joined on
               (sleeve, sym, date).  ~87% of rows.
  T2_SYMBOL    the symbol's own ATR, recovered from D4 rows of another sleeve by dividing
               out that sleeve's `stop_atr`, then multiplied by this sleeve's. Same symbol,
               same instrument, adjacent years.
  T3_CLASS     no D4 presence for the symbol at all -> the instrument class's median
               `sl/price` ratio. MODELLED, banded, and reported separately.

D4 is used **only** as a stop-distance coordinate source. Its R column is a re-simulation
that diverges from the consumed series (mean |d| 0.60 R on metals) and is never read here.

PRICE ERA
---------
`notional_bp` commission (metals, crypto) scales with price, and these rows span 2015-2026
while the broker export is a 2026 snapshot. Charging a 2026 gold price against a 2015 stop
would overstate commission ~3.4x. Resolved by measuring `atr_frac = ATR/price` per symbol
from in-tree price history and deriving the contemporaneous price from the row's own stop:
`price = sl / (stop_atr * atr_frac)`. In the commission ratio the price then cancels, which
is the point -- the estimate depends on a dimensionless volatility ratio, not on a price
level. Where real prices exist for the row's date they are used instead, and the two are
cross-checked against each other (`price_basis_agreement` in the output).
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import json
import math
import pickle
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.costs.coverage import Coverage  # noqa: E402
from src.costs.model import (  # noqa: E402
    CostTruthError,
    cost_r,
    legacy_class_cost_r,
    load_broker_true_costs,
    rollover_nights,
)

ROUTE = REPO / "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
W3_CACHE = ROUTE / "INTEG_W3_streams_cache.pkl"
W5_CACHE = ROUTE / "INTEG_W5_new_streams_cache.pkl"
D4_LEDGER = ROUTE / "D4_COMBINED_TRADE_LEDGER.jsonl"
COST_MAP = ROUTE / "ULTIMATE_REAL_COST_MAP.json"

# --------------------------------------------------------------------------------------
# The book of record. 8 core sleeves (INTEG_portfolio_build_w2.SLEEVE_CONF) + the clean_3
# additions (KB7_growth_kelly_sizing.CLEAN3). Confidence weights are quoted from source.
# --------------------------------------------------------------------------------------
CORE8_CONF = {
    "metals_core": 1.00,
    "crypto": 0.85,
    "energy_agri": 0.80,
    "metals_softband": 0.50,
    "metals_ob_micro": 0.30,
    "fx_jpy_ny": 0.15,
    "idxrev": 0.15,
    "fx_jpy": 0.15,
}
CORE8_ORDER = [
    "metals_core", "metals_softband", "metals_ob_micro", "crypto",
    "energy_agri", "idxrev", "fx_jpy", "fx_jpy_ny",
]  # INTEG_portfolio_build_w3.GENS insertion order -- the matrix column order
CLEAN3_CONF = {"sub_xvol_pullback": 0.45, "vp_euidx_pocgrav": 0.30, "sub_mid_dn_revert": 0.20}
BOOK_CONF = {**CORE8_CONF, **CLEAN3_CONF}

# stop_atr per sleeve: sl_distance_price = stop_atr * ATR14(timeframe), from source.
#   metals_*      g.fvg_signals supplies sd directly (H4 structural) -> no fixed multiple
#   crypto        INTEG_portfolio_build.py:161  sd = 2.0 * a
#   idxrev        INTEG_portfolio_build.py:182  STOP_ATR = 1.5
#   fx_jpy(_ny)   INTEG_portfolio_build.py:233 / KB.session_open_mom -> 1.0 * ATR14(M15)
#   vp_euidx      KB5_fold_new_sleeves.py:87    stop_dist = 1.0 * a
#   substrate     SUBSTRATE_corrcheck.parse_cell 'g1.0_3.0' -> stop_atr 1.0
SLEEVE_STOP_ATR = {
    "metals_core": None, "metals_softband": None, "metals_ob_micro": None,
    "crypto": 2.0, "energy_agri": None, "idxrev": 1.5,
    "fx_jpy": 1.0, "fx_jpy_ny": 1.0,
    "sub_xvol_pullback": 1.0, "vp_euidx_pocgrav": 1.0, "sub_mid_dn_revert": 1.0,
}
# The cost the generator charged is `class_cost / stop_atr` wherever the generator applied
# that rescale (idxrev :196, substrate.outcome :254). Elsewhere it is the class cost flat.
SLEEVE_COST_DIVISOR = {
    "idxrev": 1.5,
    "sub_xvol_pullback": 1.0, "sub_mid_dn_revert": 1.0,
}
# Exit horizon in HOURS, read off D4's own `resim.maxbars` x `resim.stream` timeframe and
# confirmed against source (`compounding_sleeve.exit_state_d` maxbars=80,
# `INTEG_portfolio_build.gen_idxrev` MAXBARS=60, `gen_fx_jpy` maxbars=48 on M15,
# `substrate.MAXBARS` 80). It caps how many rollovers a sleeve's trade can *possibly*
# cross, which is what makes a uniform nights sweep wrong: the two JPY sleeves close
# within 12 h and cannot pay three nights of carry no matter what is assumed.
SLEEVE_HORIZON_H = {
    "metals_core": 320.0, "metals_softband": 320.0, "metals_ob_micro": 320.0,
    "crypto": 320.0, "energy_agri": 320.0, "idxrev": 240.0,
    "fx_jpy": 12.0, "fx_jpy_ny": 12.0,
    "sub_xvol_pullback": 320.0, "vp_euidx_pocgrav": 320.0, "sub_mid_dn_revert": 320.0,
}
def _measured_nights(horizon_h):
    """(mean, max) charged nights for a hold of `horizon_h`, from `rollover_nights` itself.

    An earlier version scaled by 5/7 on the reasoning that weekend midnights are not
    charged. That reads `rollover_nights:239` and stops two lines early: `:241-243` collects
    the weekend on the triple-swap weekday at weight 3.0, so **a full week charges 7 nights,
    not 5** (measured: 7.04 mean over all 168 entry hours). The old factor understated every
    H4 sleeve's ceiling by 1.40x. It also made the JPY sleeves' ceiling 1.0 and the docstring
    claim that they "cannot pay three nights" -- false: a 12 h hold that crosses a Wednesday
    midnight charges exactly 3.
    """
    base = dt.datetime(2026, 3, 2, 12, 0, tzinfo=dt.timezone.utc)   # a Monday
    vals = [rollover_nights(base + dt.timedelta(hours=k), horizon_h,
                            server="FTMO-Server3", rollover3days_weekday=3)[0]
            for k in range(168)]
    return round(statistics.fmean(vals), 3), round(max(vals), 3)


LIVE_TRADE_ROWS = (REPO /
                   "docs/audits/fable5-vision-audit-20260725/phase1/w7_forensics/LIVE_TRADE_ROWS.jsonl")


def live_carry():
    """Measured carry per sleeve, from the live W7 window's own broker deal records.

    `LIVE_TRADE_ROWS.jsonl` carries `holding_seconds` and the broker's realized `swap` for
    every W7-era position. Three of this book's eleven sleeves fired live -- `idxrev`,
    `fx_jpy`, `fx_jpy_ny` -- on the same symbols and under the same exit horizon as the
    validation (live `time_stop_bars` 960/48/48 M15 = 240/12/12 h; validation `MAXBARS` 60
    H4 = 240 h and `maxbars` 48 M15 = 12 h). So for those three, holding time is not an
    assumption.

    Derived from the file rather than transcribed, so it moves if the file does.
    """
    if not LIVE_TRADE_ROWS.is_file():
        return {}
    out = collections.defaultdict(lambda: dict(n=0, n_swap=0, holds=[]))
    for line in LIVE_TRADE_ROWS.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("stack_era") != "w7_book":
            continue
        sl = r.get("sleeve_id")
        hs = r.get("holding_seconds")
        if sl not in BOOK_CONF or hs is None:
            continue
        b = out[sl]
        b["n"] += 1
        b["holds"].append(float(hs) / 3600.0)
        if abs(float(r.get("swap") or 0.0)) > 1e-9:
            b["n_swap"] += 1
    res = {}
    for sl, b in out.items():
        h = sorted(b["holds"])
        res[sl] = dict(
            n=b["n"], n_paid_swap=b["n_swap"],
            share_paid_swap_pct=round(100.0 * b["n_swap"] / b["n"], 1),
            median_hold_h=round(statistics.median(h), 3),
            mean_hold_h=round(statistics.fmean(h), 3), max_hold_h=round(max(h), 3),
            horizon_h=SLEEVE_HORIZON_H[sl],
            horizon_fraction_median_pct=round(100.0 * statistics.median(h) / SLEEVE_HORIZON_H[sl], 1),
            # The number the cost model consumes. Zero paid swap is a broker fact, not a
            # model output -- it is the realized `swap` field on every one of those deals.
            measured_nights=(0.0 if b["n_swap"] == 0
                             else round(_measured_nights(statistics.fmean(h))[0], 3)),
            basis=("MEASURED_LIVE_ZERO_SWAP" if b["n_swap"] == 0 else "MEASURED_LIVE_MEAN_HOLD"))
    return res


LIVE_CARRY = live_carry()

# `fx_jpy` is the one sleeve whose zero-carry is *structural* as well as measured, and the
# distinction decides its tier. It gates on `hour >= 8` and enters on the 4th M15 bar
# (`INTEG_portfolio_build.py:227-229`) = 09:00 broker; `simulate` cannot exit past bar i+48
# (`geometry_lib.py:33,50`), so the ceiling is 21:00 the same broker day -- three hours short
# of a rollover, and 0 midnights on 292 of 292 sample days.
#
# That rests on the export column being broker-server-local, which is MEASURED, not assumed:
# the FX week opens Monday 00:00 (56 of 60 symbol-weeks) and closes Friday 23:45 (60 of 60);
# a UTC column would open Sunday ~21:00. The premise is load-bearing -- under a UTC reading
# the 21:00 ceiling would land at 00:00 broker in summer, exactly the rollover instant.
#
# `fx_jpy_ny` is NOT protected. Same 48-bar ceiling, but `session_open_mom(..., 15, 4, ...)`
# enters 16:00, so the ceiling is 04:00 the NEXT broker day -- it crosses a midnight on
# roughly four days in five, and a Friday entry spans the weekend to Monday 04:15 (60.75 h).
# Its nine live positions all closed inside 1.26 h and paid nothing, but that is an
# observation, not a bound, so it stays carry-conditional with the evidence recorded.
CARRY_STRUCTURAL = {"fx_jpy"}

_NIGHTS = {k: _measured_nights(v) for k, v in SLEEVE_HORIZON_H.items()}
# The *expected* nights for a trade held to its horizon -- the honest central case.
SLEEVE_MEAN_NIGHTS = {k: v[0] for k, v in _NIGHTS.items()}
# The worst reachable crossing count -- a stress bound, not a verdict.
SLEEVE_MAX_NIGHTS = {k: v[1] for k, v in _NIGHTS.items()}

# Bar timeframe the sleeve's ATR is measured on -- decides which price series can price it.
SLEEVE_TF = {s: "H4" for s in BOOK_CONF}
SLEEVE_TF["fx_jpy"] = "M15"
SLEEVE_TF["fx_jpy_ny"] = "M15"

# Research symbol -> broker symbol. Independently derived two ways and required to agree:
#   (a) scripts/w7_live_forensics.py:212-231, built from the brokers' own traded-symbol sets
#   (b) mechanical `_cash`->`.cash` / `_c`->`.c` normalisation, verified against the
#       instrument set actually present in BROKER_TRUE_COSTS_V1.json
SYMBOL_MAP = {
    "FTMO": {
        "NAS100": "US100.cash", "US30_cash": "US30.cash", "SPX500": "US500.cash",
        "UK100": "UK100.cash", "GER40": "GER40.cash", "JP225": "JP225.cash",
        "AUS200_cash": "AUS200.cash", "EU50_cash": "EU50.cash", "FRA40_cash": "FRA40.cash",
        "USOIL_cash": "USOIL.cash", "UKOIL_cash": "UKOIL.cash", "US2000_cash": "US2000.cash",
        "N25_cash": "N25.cash", "DXY_cash": "DXY.cash", "NATGAS_cash": "NATGAS.cash",
        "CORN_c": "CORN.c", "COTTON_c": "COTTON.c", "SOYBEAN_c": "SOYBEAN.c",
        "WHEAT_c": "WHEAT.c", "HEATOIL_c": "HEATOIL.c",
    },
    "redacted_account": {
        "NAS100": "NDX100", "US30_cash": "US30", "GER40": "GER30",
        "UKOIL_cash": "UKOUSD", "USOIL_cash": "USOUSD", "AUS200_cash": "AUS200",
        "FRA40_cash": "FRA40", "US2000_cash": "US2000",
    },
}

WINSOR = (-1.3, 5.0)


def wins(r: float) -> float:
    return max(WINSOR[0], min(WINSOR[1], r))


# --------------------------------------------------------------------------------------
# 1. Load the book exactly as KB7_growth_kelly_sizing.build_deploy_matrix does
# --------------------------------------------------------------------------------------
def load_book_rows():
    w3 = pickle.load(open(W3_CACHE, "rb"))
    w5 = pickle.load(open(W5_CACHE, "rb"))
    rows = []
    for sl in CORE8_ORDER:
        for r in w3[sl]:
            rows.append(dict(sleeve=sl, sym=r["sym"], date=r["date"], year=r["year"],
                             R=float(r["R"]), intra_size=float(r.get("intra_size", 1.0)),
                             source="W3"))
    for sl in CLEAN3_CONF:
        for r in w5[sl]:
            # KB7_growth_kelly_sizing.candidate_daily reads r['R'] only -- clean_3 carries
            # no intra_size into the deploy matrix.
            rows.append(dict(sleeve=sl, sym=r["sym"], date=r["date"], year=r["year"],
                             R=float(r["R"]), intra_size=1.0, source="W5"))
    return rows


# --------------------------------------------------------------------------------------
# 2. Recover the charged cost -- from source AND from the data, and require agreement
# --------------------------------------------------------------------------------------
def asset_class_by_symbol():
    from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL
    return dict(ASSET_CLASS_BY_SYMBOL)


def d4_charged_costs():
    """(sleeve, sym) -> the cost the D4 re-sim recorded charging. Third witness."""
    seen = collections.defaultdict(collections.Counter)
    for line in D4_LEDGER.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        c = (r.get("resim") or {}).get("cost")
        if c is not None:
            seen[(r["sleeve"], r["sym"])][round(float(c), 8)] += 1
    return {k: v.most_common(1)[0][0] for k, v in seen.items()}


def charged_cost_table(rows):
    """{(sleeve, sym): cost | "VARIABLE"} from the data first, source second.

    Witness A  source      -- ULTIMATE_REAL_COST_MAP class value / the sleeve's stop_atr
    Witness B  D4 re-sim   -- `resim.cost`, what that ledger records charging
    Witness C  stop-outs   -- **the only witness that reads the consumed series.** A full
                             stop books exactly `-(1 + charged_cost)`, so every row in
                             (-1.35, -1.0] hands back the cost it paid.

    **A dispersed witness C is a finding, not a missing witness.** An earlier version of
    this function required >=2 *identical* rows before it would accept C, and recorded a
    pair with a spread of values as "unverifiable". That inverted the signal: a spread
    means the generator charged a *per-trade* cost, and the two sleeves that do
    (`INTEG_portfolio_build_w3.py:89` scales metals_core by `0.5*ATR/sd_h4`, and the energy
    cascade does the same at `EXEC_exit_variants.py:45`) were precisely the ones it
    excused. Witnesses A and B cannot catch that -- both read the same flat class map, and
    D4's metals re-sim is the series the session brief warns diverges by 0.60 R.

    So: C is computed first and its *dispersion* decides. Flat pairs take the flat value and
    must agree with A and B. Variable pairs are marked VARIABLE and priced per row by
    `variable_cost_table`.
    """
    cmap = json.loads(COST_MAP.read_text())
    acls = asset_class_by_symbol()
    gc = cmap["_global_median"]
    d4c = d4_charged_costs()
    out, checks = {}, []
    pairs = sorted({(r["sleeve"], r["sym"]) for r in rows})

    # Scaling is a property of the *generator*, so it is a sleeve-level fact. A pair is
    # evidence of it two ways: dispersed stop-outs, or a single stop-out that disagrees
    # with the flat source value. Either promotes the whole sleeve, because a pair with
    # one stop-out cannot show dispersion and would otherwise be silently mispriced --
    # metals_core/XAUAUD is exactly that case (n=1, 0.014993 against a source 0.0459).
    variable_sleeves = set()
    for sleeve, sym in pairs:
        klass = acls.get(sym)
        src = cmap.get(klass, gc) / SLEEVE_COST_DIVISOR.get(sleeve, 1.0)
        tail = [-1.0 - round(r["R"], 9) for r in rows
                if r["sleeve"] == sleeve and r["sym"] == sym and -1.35 < r["R"] <= -1.0]
        if not tail:
            continue
        if len({round(x, 6) for x in tail}) > 1 or abs(tail[0] - src) > 5e-4:
            variable_sleeves.add(sleeve)
    for sleeve, sym in pairs:
        klass = acls.get(sym)
        base = cmap.get(klass, gc)
        div = SLEEVE_COST_DIVISOR.get(sleeve, 1.0)
        src_cost = base / div
        cand = [r["R"] for r in rows if r["sleeve"] == sleeve and r["sym"] == sym]
        tail = sorted(-1.0 - round(v, 9) for v in cand if -1.35 < v <= -1.0)
        distinct = len({round(x, 6) for x in tail})
        variable = sleeve in variable_sleeves
        d4v = d4c.get((sleeve, sym))
        wit = {"A_source": round(src_cost, 8)}
        if d4v is not None:
            wit["B_d4_resim"] = d4v
        if tail and not variable:
            wit["C_stopout"] = round(tail[0], 8)
        if variable:
            out[(sleeve, sym)] = "VARIABLE"
            agree = True                     # per-row; checked in variable_cost_table
            charged = None
        else:
            out[(sleeve, sym)] = src_cost
            vals = list(wit.values())
            agree = max(vals) - min(vals) < 5e-4
            charged = round(src_cost, 6)
        checks.append(dict(sleeve=sleeve, sym=sym, asset_class=klass,
                           class_used=(klass if klass in cmap else "_global_median"),
                           cost_divisor=div, charged_cost_r=charged,
                           charge_kind=("per_trade" if variable else "flat"),
                           witnesses=wit, n_witnesses=len(wit), n_rows=len(cand),
                           n_stopouts=len(tail), n_distinct_stopout_costs=distinct,
                           stopout_cost_min=(round(tail[0], 6) if tail else None),
                           stopout_cost_median=(round(statistics.median(tail), 6) if tail else None),
                           stopout_cost_max=(round(tail[-1], 6) if tail else None),
                           agree=bool(agree)))
    return out, checks


def variable_cost_table(rows, charged):
    """Per-row charged cost for the pairs whose generator scaled it by stop tightness.

    `metals_core` charges `class_cost * (0.5 * ATR14(H4) / sd_h4)` per trade
    (`INTEG_portfolio_build_w3.py:89`); the energy cascade does the same
    (`EXEC_exit_variants.py:45`). Exact wherever the row is a clean stop-out -- it hands
    back its own cost. Elsewhere the pair's stop-out median is used, and the min/max are
    carried as a band, because that estimate is **biased high**: a tighter stop pays a
    bigger multiplier *and* stops out more often, so the stop-out subsample
    over-represents expensive trades. The band is published rather than smoothed away.
    """
    per_pair = collections.defaultdict(list)
    for r in rows:
        k = (r["sleeve"], r["sym"])
        if charged.get(k) == "VARIABLE" and -1.35 < r["R"] <= -1.0:
            per_pair[k].append(-1.0 - round(r["R"], 9))
    sleeve_pool = collections.defaultdict(list)
    for (sl, _), v in per_pair.items():
        sleeve_pool[sl].extend(v)
    band = {}
    for r in rows:
        k = (r["sleeve"], r["sym"])
        if charged.get(k) != "VARIABLE":
            continue
        if -1.35 < r["R"] <= -1.0:
            r["charged_cost_r"] = -1.0 - round(r["R"], 9)
            r["charged_basis"] = "EXACT_STOPOUT"
        else:
            pool = per_pair.get(k) or sleeve_pool.get(r["sleeve"]) or []
            r["charged_cost_r"] = statistics.median(pool) if pool else 0.0
            r["charged_basis"] = ("PAIR_STOPOUT_MEDIAN" if per_pair.get(k)
                                  else "SLEEVE_STOPOUT_MEDIAN")
        pool = per_pair.get(k) or sleeve_pool.get(r["sleeve"]) or [r["charged_cost_r"]]
        band[k] = (min(pool), statistics.median(pool), max(pool), len(pool))
    return band


# --------------------------------------------------------------------------------------
# 3. Stop distance
# --------------------------------------------------------------------------------------
def load_d4_stops():
    """(sleeve, sym, isodate) -> [(sd, dir), ...] and (sym, year) -> [atr, ...].

    ATR is only recoverable from a sleeve whose stop is a *known* multiple of it, and only
    transferable to a sleeve reading the same timeframe -- so the ATR pools are keyed by
    timeframe. Mixing the M15 JPY sleeves with the H4 book here is the same error as
    reading an H4 bar series for them.
    """
    exact = collections.defaultdict(list)
    atr_sy = collections.defaultdict(list)
    atr_s = collections.defaultdict(list)
    for line in D4_LEDGER.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        rs = r.get("resim") or {}
        sd = rs.get("sd")
        if not sd:
            continue
        exact[(r["sleeve"], r["sym"], r["date"])].append((float(sd), rs.get("d")))
        k = SLEEVE_STOP_ATR.get(r["sleeve"])
        if k:  # only sleeves with a known ATR multiple can yield an ATR
            tf = SLEEVE_TF[r["sleeve"]]
            atr_sy[(tf, r["sym"], r["year"])].append(float(sd) / k)
            atr_s[(tf, r["sym"])].append(float(sd) / k)
    return exact, atr_sy, atr_s


def attach_stops(rows, exact, atr_sy, atr_s, prices):
    """Stamp sl_price + stop_tier on every row. Derived, never defaulted silently.

    T1_LEDGER      exact `resim.sd` for this (sleeve, sym, date)
    T2_PRICE_ATR   ATR14 measured from in-tree bars at the row's own date x this sleeve's
                   stop_atr -- the row's own volatility, just from a different bar source
    T2_SYMBOL_YEAR the symbol's ATR that year, recovered from a D4 sleeve with a known
                   stop_atr; T2_SYMBOL falls back to all years
    UNPRICED       none of the above. Published as a coverage fact; never guessed.
    """
    cursor = collections.defaultdict(int)
    for r in rows:
        key = (r["sleeve"], r["sym"], r["date"].isoformat())
        k_self = SLEEVE_STOP_ATR.get(r["sleeve"])
        r["side"] = None
        if key in exact:
            lst = exact[key]
            i = cursor[key]
            sd, d = lst[i] if i < len(lst) else (statistics.median(x[0] for x in lst), None)
            r["sl_price"] = sd
            r["side"] = "LONG" if (d or 0) > 0 else ("SHORT" if (d or 0) < 0 else None)
            cursor[key] += 1
            r["stop_tier"] = "T1_LEDGER"
            continue
        ps = prices.get(r["sym"])
        # Only when the sleeve's ATR timeframe matches the bar series. fx_jpy/fx_jpy_ny
        # stop at 1.0 x ATR14(M15) and the in-tree series are H4: reading an H4 ATR for
        # them inflates the stop ~5x, which would silently divide their commission by 5.
        if k_self and ps and SLEEVE_TF.get(r["sleeve"]) == ps["tf"]:
            for back in range(0, 8):
                atr = ps["atr_by_date"].get(r["date"] - dt.timedelta(days=back))
                if atr:
                    r["sl_price"] = atr * k_self
                    r["stop_tier"] = "T2_PRICE_ATR"
                    break
            if r.get("sl_price"):
                continue
        atr, tier = None, None
        tf = SLEEVE_TF.get(r["sleeve"])
        if (tf, r["sym"], r["year"]) in atr_sy:
            atr, tier = statistics.median(atr_sy[(tf, r["sym"], r["year"])]), "T2_SYMBOL_YEAR"
        elif (tf, r["sym"]) in atr_s:
            atr, tier = statistics.median(atr_s[(tf, r["sym"])]), "T2_SYMBOL"
        if atr is not None and k_self:
            r["sl_price"] = atr * k_self
            r["stop_tier"] = tier
            continue
        r["sl_price"] = None
        r["stop_tier"] = "UNPRICED_NO_STOP"
    return rows


# --------------------------------------------------------------------------------------
# 4. Price history: atr_frac per symbol, and per-date closes where in-tree
# --------------------------------------------------------------------------------------
def _read_bars(path):
    T, C, H, L = [], [], [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            try:
                t = dt.datetime.strptime(row["time"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    t = dt.datetime.strptime(row["time"], "%Y-%m-%d")
                except ValueError:
                    continue
            except KeyError:
                continue
            try:
                H.append(float(row["high"])); L.append(float(row["low"])); C.append(float(row["close"]))
            except (KeyError, ValueError):
                continue
            T.append(t)
    return T, C, H, L


PRICE_DIRS = ("data/historical", "data/historical_2022_2023", "data/historical_2026", "data")


def price_series(symbols):
    """{sym: {'by_date': {date: close}, 'atr_frac': .., 'atr_by_date': {..}, ..}}

    Every in-tree H4 series for the symbol is pooled: the union gives the widest date
    coverage, and `atr_frac = median(ATR14 / close)` is measured on the longest single
    contiguous file (pooling disjoint windows would corrupt the true-range chain).
    `atr_frac` is the load-bearing quantity -- it is what lets a 2015 row be priced from a
    2026 export without ever quoting a 2026 price against a 2015 stop.
    """
    out = {}
    for sym in symbols:
        found = []
        for tf in ("H4", "H1", "D1"):
            for base in PRICE_DIRS:
                p = REPO / base / f"{sym}_{tf}.csv"
                if p.is_file():
                    T, C, H, L = _read_bars(p)
                    if len(C) >= 60:
                        found.append((tf, p, T, C, H, L))
            if found:
                break                      # never mix timeframes for one symbol
        if not found:
            continue
        by_date, atr_by_date = {}, {}
        best = max(found, key=lambda f: len(f[3]))
        for tf, p, T, C, H, L in found:
            trs = [0.0]
            for i in range(1, len(C)):
                trs.append(max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])))
            for i in range(15, len(C)):
                d = T[i].date()
                by_date.setdefault(d, C[i])
                atr_by_date.setdefault(d, statistics.fmean(trs[i - 14:i]))
        tf, p, T, C, H, L = best
        trs = [max(H[i] - L[i], abs(H[i] - C[i - 1]), abs(L[i] - C[i - 1])) for i in range(1, len(C))]
        fracs = [statistics.fmean(trs[i - 15:i - 1]) / C[i]
                 for i in range(16, len(C)) if C[i] > 0]
        fracs = [f for f in fracs if f > 0]
        if not fracs:
            continue
        out[sym] = dict(by_date=by_date, atr_by_date=atr_by_date,
                        atr_frac=statistics.median(fracs), tf=tf, n=len(by_date),
                        paths=[str(q.relative_to(REPO)) for _, q, *_ in found],
                        first=min(by_date), last=max(by_date))
    return out


def effective_stop_atr(rows, prices):
    """Measured `sl / ATR14` per (sleeve, sym) and per sleeve.

    Three sleeve families take their stop from a structure (the FVG leg for metals_*, the
    energy sleeve's own ledger) rather than a fixed ATR multiple, so `SLEEVE_STOP_ATR` is
    None for them and their rows cannot be inverted to a price analytically. The multiple
    is recoverable empirically wherever a row has both a ledger stop and an in-tree ATR at
    its own date; measured here and transferred within the sleeve.
    """
    per_pair = collections.defaultdict(list)
    for r in rows:
        if r["stop_tier"] != "T1_LEDGER" or not r["sl_price"]:
            continue
        ps = prices.get(r["sym"])
        if not ps:
            continue
        for back in range(0, 8):
            atr = ps["atr_by_date"].get(r["date"] - dt.timedelta(days=back))
            if atr:
                per_pair[(r["sleeve"], r["sym"])].append(r["sl_price"] / atr)
                break
    pair = {k: statistics.median(v) for k, v in per_pair.items() if len(v) >= 3}
    sleeve = collections.defaultdict(list)
    for (sl, sym), v in pair.items():
        sleeve[sl].append(v)
    return pair, {k: statistics.median(v) for k, v in sleeve.items()}


def resolve_price(row, prices, atr_frac_by_class, class_of, k_pair, k_sleeve):
    """(entry_price, basis).

    Price is needed for `notional_bp` commission and for swap modes 5/6. Where the row's
    own date is covered by in-tree bars the real close is used. Otherwise the price is
    *derived from the row's own stop* -- `price = sl / (stop_atr * atr_frac)` -- so the
    estimate rests on a dimensionless volatility ratio rather than on a 2026 price level
    quoted against a 2015 stop. Never falls back to the broker snapshot.
    """
    sym, d = row["sym"], row["date"]
    ps = prices.get(sym)
    if ps:
        for back in range(0, 8):
            hit = ps["by_date"].get(d - dt.timedelta(days=back))
            if hit:
                return hit, "P1_INTREE_BARS"
    # A close is timeframe-free; an `atr_frac` is not. `attach_stops` already refuses to
    # read an H4 ATR for an M15 sleeve; this path did not, and inverting an M15-scale stop
    # through an H4 atr_frac understates the derived price ~4-5x for the JPY sleeves.
    if ps and SLEEVE_TF.get(row["sleeve"]) != ps["tf"]:
        return None, "P4_TIMEFRAME_MISMATCH"
    k = (SLEEVE_STOP_ATR.get(row["sleeve"])
         or k_pair.get((row["sleeve"], sym)) or k_sleeve.get(row["sleeve"]))
    af, basis = None, None
    if ps:
        af, basis = ps["atr_frac"], "P2_SELF_ATRFRAC"
    else:
        kl = class_of.get(sym)
        if kl in atr_frac_by_class:
            af, basis = atr_frac_by_class[kl], "P3_CLASS_ATRFRAC"
    if af and k and row.get("sl_price"):
        return row["sl_price"] / (k * af), basis
    return None, "P4_UNAVAILABLE"


# --------------------------------------------------------------------------------------
# 5. main
# --------------------------------------------------------------------------------------
def build(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="research/operations/w7_recost_2026_07_27")
    ap.add_argument("--spread-percentile", default="p50")
    ap.add_argument("--nights", type=float, default=1.0,
                    help="modelled rollover nights per trade (swap band centre)")
    args = ap.parse_args(argv)
    outdir = REPO / args.out
    outdir.mkdir(parents=True, exist_ok=True)

    rows = load_book_rows()
    charged, cost_checks = charged_cost_table(rows)

    bad = [c for c in cost_checks if not c["agree"]]
    if bad:
        raise SystemExit(f"charged-cost witness disagreement on {len(bad)} pairs: {bad[:5]}")

    # gross reconstruction + winsor inertness assertion
    lo = min(r["R"] for r in rows)
    hi = max(r["R"] for r in rows)
    winsor_inert = lo > WINSOR[0] + 1e-9 and hi < WINSOR[1] - 1e-9
    for r in rows:
        c = charged[(r["sleeve"], r["sym"])]
        if c != "VARIABLE":
            r["charged_cost_r"] = c
            r["charged_basis"] = "FLAT"
    variable_band = variable_cost_table(rows, charged)
    for r in rows:
        r["R_gross"] = r["R"] + r["charged_cost_r"]

    exact, atr_sy, atr_s = load_d4_stops()
    truth = load_broker_true_costs()
    class_of = {}
    for sym in sorted({r["sym"] for r in rows}):
        for acct in ("FTMO", "redacted_account"):
            bs = SYMBOL_MAP[acct].get(sym, sym)
            try:
                class_of[sym] = truth.instrument(acct, bs)["instrument_class"]
                break
            except CostTruthError:
                continue

    prices = price_series(sorted({r["sym"] for r in rows}))
    attach_stops(rows, exact, atr_sy, atr_s, prices)
    atr_frac_by_class = collections.defaultdict(list)
    for sym, ps in prices.items():
        if class_of.get(sym):
            atr_frac_by_class[class_of[sym]].append(ps["atr_frac"])
    atr_frac_by_class = {k: statistics.median(v) for k, v in atr_frac_by_class.items()}

    k_pair, k_sleeve = effective_stop_atr(rows, prices)
    for r in rows:
        r["entry_price"], r["price_basis"] = resolve_price(
            r, prices, atr_frac_by_class, class_of, k_pair, k_sleeve)

    for acct in ("FTMO", "redacted_account"):
        price_rows(rows, acct, truth, args)
        transfer_unpriced(rows, acct, class_of)

    return dict(rows=rows, cost_checks=cost_checks, winsor_inert=winsor_inert,
                lo=lo, hi=hi, prices=prices, class_of=class_of,
                atr_frac_by_class=atr_frac_by_class, truth=truth, args=args,
                outdir=outdir, k_pair=k_pair, k_sleeve=k_sleeve,
                variable_band={f"{k[0]}:{k[1]}": dict(min=round(v[0], 6),
                                                      median=round(v[1], 6),
                                                      max=round(v[2], 6), n_stopouts=v[3])
                               for k, v in variable_band.items()})


# --------------------------------------------------------------------------------------
# 6. Cost every row through src.costs.cost_r, per account
# --------------------------------------------------------------------------------------
def price_rows(rows, account, truth, args):
    """Stamp `cost_<account>` on every row: the four terms, the coverage class, or the
    exact refusal reason. `cost_r` is the only thing that produces a cost number here.

    Era handling. `cost_r` charges the **2026-measured** spread in absolute price units
    against whatever stop it is given. A 2015 gold stop is ~1/3 of a 2026 one in cash, so
    the raw spread term would be overstated by the price ratio. The spread component is
    therefore rescaled by `entry_price / mid_price_median` -- the one term where the
    2026 snapshot does not travel. Commission and the price-denominated swap modes are
    already era-correct because the row's own `entry_price` is passed in.
    """
    key = f"cost_{account}"
    for r in rows:
        bs = SYMBOL_MAP[account].get(r["sym"], r["sym"])
        r[f"broker_symbol_{account}"] = bs
        if not r["sl_price"]:
            r[key] = dict(status="refused", reason="no stop distance resolvable for this row",
                          stage="stop_distance")
            continue
        # Side decides which swap leg is adverse. D4 records the direction for the rows it
        # covers; where it does not, both legs are priced and the mean charged, with the
        # spread between them carried as the row's own swap uncertainty.
        sides = [r["side"]] if r["side"] else ["LONG", "SHORT"]
        try:
            cbs = [cost_r(bs, account, holding_hours=24.0,
                          sl_distance_price=r["sl_price"], entry_price=r["entry_price"],
                          side=s, spread_percentile=args.spread_percentile, costs=truth)
                   for s in sides]
        except CostTruthError as e:
            r[key] = dict(status="refused", reason=str(e).split(".")[0], stage="cost_r")
            continue
        cb = cbs[0]
        rec = truth.instrument(account, bs)
        mid = (rec.get("spread_price") or {}).get("mid_price_median")
        era = 1.0
        if mid and r["entry_price"]:
            era = float(r["entry_price"]) / float(mid)
        spread_era = cb.spread_r.value * era
        # swap_r from a 24 h call is exactly one night's drag (entry_utc omitted, so
        # nights = holding_hours/24). Kept per-night so the book can be swept over the
        # holding-time band rather than committed to one unmeasured number.
        swap_per_night = statistics.fmean(c.swap_r.value for c in cbs)
        base = cb.commission_r.value + spread_era + cb.slippage_r.value
        total = base + swap_per_night * args.nights
        r[key] = dict(
            status="priced",
            commission_r=cb.commission_r.value,
            spread_r_raw=cb.spread_r.value,
            spread_r=spread_era,
            spread_era_mult=era,
            swap_r_per_night=swap_per_night,
            swap_r=swap_per_night * args.nights,
            swap_side_spread=(max(c.swap_r.value for c in cbs) - min(c.swap_r.value for c in cbs)),
            side_basis=("D4_LEDGER" if r["side"] else "BOTH_LEGS_MEAN"),
            slippage_r=cb.slippage_r.value,
            cost_ex_swap_r=base,
            total_r=total,
            coverage=cb.total_r.coverage.name,
            commission_coverage=cb.commission_r.coverage.name,
            spread_coverage=cb.spread_r.coverage.name,
            slippage_coverage=cb.slippage_r.coverage.name,
            # The pair that decides the answer. Swap is a modelled band (no entry instant
            # exists for these rows) and slippage is a live-geometry constant, so quoting
            # the weakest-of-four as *the* coverage would hide that commission and spread
            # are the measured terms.
            core_coverage=min(cb.commission_r.coverage, cb.spread_r.coverage,
                              key=lambda c: c.strength).name,
            commission_kind=cb.detail["commission"]["kind"],
            instrument_class=cb.detail.get("instrument_class"),
        )
    return rows


def transfer_unpriced(rows, account, class_of):
    """Give every refused row a class-transferred cost, clearly labelled.

    The transfer takes the median priced **ex-swap cost and swap-per-night separately**, from
    the same instrument class within the same sleeve (falling back to the class across
    sleeves), because cost in R is a property of the trade's stop geometry and geometry is a
    sleeve property.

    Transferring the *total* instead -- which an earlier version did -- freezes the row at
    whatever `--nights` the run was built with and makes it inert to the carry sweep, in
    exactly the column that decides survive/die. It also silently poured one night of carry
    into the published `true_cost_ex_swap_r` and diluted the published `swap_r_per_night` by
    the transferred share (up to 66% of a sleeve's rows). Both are fixed by keeping the two
    terms apart.

    Rows that still cannot be reached stay `unpriced` and are reported as a set-difference
    from the full book, never dropped silently.
    """
    key = f"cost_{account}"
    pool_sleeve_class = collections.defaultdict(lambda: ([], []))
    pool_class = collections.defaultdict(lambda: ([], []))
    for r in rows:
        c = r[key]
        if c["status"] == "priced":
            kl = class_of.get(r["sym"])
            for pool in (pool_sleeve_class[(r["sleeve"], kl)], pool_class[kl]):
                pool[0].append(c["cost_ex_swap_r"])
                pool[1].append(c["swap_r_per_night"])
    for r in rows:
        c = r[key]
        if c["status"] != "refused":
            continue
        kl = class_of.get(r["sym"])
        src, vals = None, None
        if (r["sleeve"], kl) in pool_sleeve_class and pool_sleeve_class[(r["sleeve"], kl)][0]:
            src, vals = f"sleeve={r['sleeve']} class={kl}", pool_sleeve_class[(r["sleeve"], kl)]
        elif kl in pool_class and pool_class[kl][0]:
            src, vals = f"class={kl} (all sleeves)", pool_class[kl]
        if vals:
            ex, sw = vals
            c.update(status="transferred",
                     transfer_ex_swap_r=statistics.median(ex),
                     transfer_swap_r_per_night=statistics.median(sw),
                     total_r=statistics.median(ex) + statistics.median(sw),
                     transferred_from=src, n_pool=len(ex),
                     coverage="TRANSFERRED", core_coverage="TRANSFERRED",
                     instrument_class=kl)
        else:
            c.update(status="unpriced", coverage="ABSENT", core_coverage="ABSENT",
                     instrument_class=kl)
    return rows


# --------------------------------------------------------------------------------------
# 7. Restate the book and re-run the LOCKED MC
# --------------------------------------------------------------------------------------
def _route_mc():
    """The route's own MC engine, imported rather than reimplemented -- a reimplementation
    that drifted by one constant would invalidate every comparison in this file."""
    sys.path.insert(0, str(ROUTE))
    import INTEG_portfolio_build_w2 as W2  # noqa: E402
    return W2


def row_cost(r, account, nights, unpriced_policy, class_medians):
    """Total true cost in R for one row at `nights` of carry, clipped to what the sleeve's
    own exit horizon allows. Returns (cost, status)."""
    c = r[f"cost_{account}"]
    n = min(nights, SLEEVE_MAX_NIGHTS[r["sleeve"]])
    if c["status"] == "priced":
        return c["cost_ex_swap_r"] + c["swap_r_per_night"] * n, "priced"
    if c["status"] == "transferred":
        return c["transfer_ex_swap_r"] + c["transfer_swap_r_per_night"] * n, "transferred"
    if unpriced_policy == "legacy":
        return r["charged_cost_r"], "unpriced_legacy"
    if unpriced_policy == "drop":
        return None, "dropped"
    return class_medians.get(r["sleeve"], 0.0), "unpriced_sleevemedian"


def build_matrix_from(rows, r_field):
    """Rebuild the 11-column deploy matrix exactly as KB7_growth_kelly_sizing does.

    Core-8: day-mean of R_sized (= R * intra_size) x sleeve confidence, over the W3 day
    axis. clean_3: day-mean of raw R x confidence (`candidate_daily` reads 'R', not
    'R_sized'). all_days is the union; column order is CORE8_ORDER + CLEAN3.
    """
    per = {sl: collections.defaultdict(list) for sl in BOOK_CONF}
    for r in rows:
        v = r.get(r_field)
        if v is None:
            continue
        per[r["sleeve"]][r["date"]].append(v * (r["intra_size"] if r["source"] == "W3" else 1.0))
    daily = {sl: {d: statistics.fmean(v) * BOOK_CONF[sl] for d, v in dd.items()}
             for sl, dd in per.items()}
    core_days = sorted(set().union(*[set(daily[sl]) for sl in CORE8_ORDER]))
    all_days = sorted(set(core_days) | set().union(*[set(daily[sl]) for sl in CLEAN3_CONF]))
    sleeves = list(CORE8_ORDER) + list(CLEAN3_CONF)
    M = [[daily[sl].get(day, 0.0) for sl in sleeves] for day in all_days]
    comb_core = [sum(daily[sl].get(d, 0.0) for sl in CORE8_ORDER) for d in core_days]
    return all_days, sleeves, M, statistics.pstdev(comb_core)


KELLY_BINS = ((1, 1), (2, 3), (4, 99))
KELLY_SIZEUP = (0.85, 1.10, 1.60)
KELLY_CAP = 1.75


def kelly_mult(na):
    for (lo, hi), m in zip(KELLY_BINS, KELLY_SIZEUP):
        if lo <= na <= hi:
            return min(m, KELLY_CAP)
    return 1.0


def variant_stats(rows, r_field, sd_book, W2, dials=(0.0125, 0.015, 0.020)):
    all_days, sleeves, M, _ = build_matrix_from(rows, r_field)
    nact = [sum(1 for v in row if abs(v) > 1e-9) for row in M]
    Mk = [[v * kelly_mult(nact[i]) for v in M[i]] for i in range(len(M))]
    comb_flat = [sum(r) for r in M]
    comb_kelly = [sum(r) for r in Mk]
    out = {}
    for label, comb in (("flat", comb_flat), ("kelly", comb_kelly)):
        sd = statistics.pstdev(comb)
        vs = sd_book / sd if sd else 0.0
        mc = {}
        for d in dials:
            res = W2.mc_series(comb, d * vs, seed_base=1)
            mc[f"{d*100:.2f}%"] = dict(
                p_pass=round(res["p_pass"], 5), p_fail_dd=round(res["p_fail_dd"], 5),
                med_days=res["med_days_pass"],
                monthly_pct=round(statistics.fmean(comb) * d * vs * 21 * 100, 3))
        out[label] = dict(mean=round(statistics.fmean(comb), 5), std=round(sd, 5),
                          vs=round(vs, 4), n_days=len(all_days),
                          mean_fwd=round(statistics.fmean(
                              [v for v, dd in zip(comb, all_days) if dd.year >= 2025]), 5),
                          mc=mc)
    out["sleeve_contribution_kelly"] = {
        s: round(sum(Mk[i][j] for i in range(len(Mk))), 3) for j, s in enumerate(sleeves)}
    return out


# --------------------------------------------------------------------------------------
# 8. Per-sleeve economics, break-even carry, placebo, F39 band
# --------------------------------------------------------------------------------------
NIGHT_GRID = (0.0, 1.0, 2.0, 3.0)


def _bh(be):
    h = _hours_for_nights(be) if (be is not None and be > 0) else None
    return round(h, 2) if h is not None else None


def _hours_for_nights(target):
    """Smallest hold, in hours, whose expected charged nights reaches `target`."""
    if target is None or target <= 0:
        return None
    lo, hi = 0.0, 24.0 * 60
    if _measured_nights(hi)[0] < target:
        return None
    for _ in range(40):
        mid = (lo + hi) / 2
        if _measured_nights(mid)[0] < target:
            lo = mid
        else:
            hi = mid
    return hi


def sleeve_table(rows, account, class_medians):
    """Per-sleeve gross edge, charged cost, true cost, and the carry break-even.

    `break_even_nights` converts the one input this restatement genuinely cannot measure --
    how long each trade was held -- into a decision-grade number: the nights of carry the
    sleeve's own gross edge can absorb before its cost-true edge reaches zero. No exit
    index survives in any cache, so quoting one hold and calling it the answer would be
    inventing the number that matters most.
    """
    out = {}
    for sl in list(CORE8_ORDER) + list(CLEAN3_CONF):
        rs = [r for r in rows if r["sleeve"] == sl]
        if not rs:
            continue
        gross = statistics.fmean(r["R_gross"] for r in rs)
        charged = statistics.fmean(r["charged_cost_r"] for r in rs)
        exswap, pernight, stat = [], [], collections.Counter()
        for r in rs:
            c = r[f"cost_{account}"]
            stat[c["status"]] += 1
            if c["status"] == "priced":
                exswap.append(c["cost_ex_swap_r"])
                pernight.append(c["swap_r_per_night"])
            elif c["status"] == "transferred":
                exswap.append(c["transfer_ex_swap_r"])
                pernight.append(c["transfer_swap_r_per_night"])
            else:
                exswap.append(class_medians.get(sl, 0.0))
                pernight.append(0.0)
        ex = statistics.fmean(exswap)
        pn = statistics.fmean(pernight)
        # A sleeve with NO cost coverage at all is not a cheap sleeve.
        #
        # The loop above gives an `unpriced` row `class_medians.get(sl, 0.0)` ex-swap and a
        # ZERO swap rate. That is a reasonable imputation while some row in the class is
        # priced and supplies the median. When the WHOLE class refuses, the fallbacks
        # collapse to 0.0 + 0.0, `net = gross - 0 - 0*cap` is just gross, and the sleeve is
        # published `UNCONDITIONAL` -- the most permissive survivor tier there is -- BECAUSE
        # its cost is unknown. Absence read as zero, in the column that decides survive/die.
        #
        # It is live now, not hypothetical: wave 21 (`7d6bbca7a`) made the cost layer refuse a
        # JPY-denominated cash-per-lot commission without an `entry_utc`, because a 2026
        # symbol-spec snapshot is not a historical USD/JPY rate. The layer says NOT_EVALUABLE
        # and fails CLOSED; this function turned that into 0.0 and failed OPEN. `fx_jpy`
        # (530 rows) and `fx_jpy_ny` (197) both went to UNCONDITIONAL at ex=0.0, pn=0.0.
        #
        # So: no priced and no transferred row => no tier. NOT_EVALUABLE propagates the
        # upstream refusal instead of overwriting it with a number nothing measured.
        priced_or_transferred = stat["priced"] + stat["transferred"]
        cost_evaluable = priced_or_transferred > 0
        cap = SLEEVE_MAX_NIGHTS[sl]
        live = LIVE_CARRY.get(sl)
        # `mean_n` keeps its published meaning -- carry if the trade is held to its horizon.
        # The live measurement is ADDED alongside it rather than substituted into it, so a
        # reader comparing against the previous version sees the same field mean the same
        # thing, and can see separately which sleeves the live window actually decided.
        mean_n = SLEEVE_MEAN_NIGHTS[sl]
        net = {f"n{int(n)}": round(gross - ex - pn * min(n, cap), 5) for n in NIGHT_GRID}
        net["n_horizon_mean"] = round(gross - ex - pn * mean_n, 5)
        net["n_max"] = round(gross - ex - pn * cap, 5)
        be = ((gross - ex) / pn) if pn > 1e-12 else None
        cov = collections.Counter()
        for r in rs:
            c = r[f"cost_{account}"]
            cov[c.get("core_coverage", c.get("coverage", "ABSENT"))] += 1
        # Swap is charged on the ADVERSE leg, so direction decides it. D4 supplies the
        # direction for the rows it covers; where it does not, both legs are priced and the
        # mean charged. Four sleeves are 100% direction-less and the two legs can differ by
        # 39x (FTMO vp_euidx_pocgrav), so the assumption is published rather than buried.
        pr = [r for r in rs if r[f"cost_{account}"]["status"] == "priced"]
        nodir = sum(1 for r in rs if not r["side"])
        spread = [r[f"cost_{account}"].get("swap_side_spread", 0.0) for r in pr]
        d4_long = sum(1 for r in rs if r["side"] == "LONG")
        d4_short = sum(1 for r in rs if r["side"] == "SHORT")
        out[sl] = dict(
            conf=BOOK_CONF[sl], n=len(rs),
            first=min(r["date"] for r in rs).isoformat(),
            last=max(r["date"] for r in rs).isoformat(),
            gross_r=round(gross, 5), charged_cost_r=round(charged, 5),
            cached_net_r=round(gross - charged, 5),
            true_cost_ex_swap_r=round(ex, 5), swap_r_per_night=round(pn, 5),
            net_r=net,
            max_nights=cap, horizon_mean_nights=SLEEVE_MEAN_NIGHTS[sl],
            measured_carry_nights=(live["measured_nights"] if live else None),
            net_r_at_measured_carry=(round(gross - ex - pn * live["measured_nights"], 5)
                                     if live else None),
            carry_basis=("MEASURED_LIVE_STRUCTURAL" if (live and sl in CARRY_STRUCTURAL)
                         else live["basis"] if live else "MODELLED_HELD_TO_HORIZON"),
            live_carry=live,
            horizon_hours=SLEEVE_HORIZON_H[sl],
            break_even_nights=(round(be, 2) if be is not None else None),
            # Break-even expressed as the hold length that reaches it -- the honest unit,
            # because "nights" hides that a 12 h sleeve and a 320 h sleeve are being asked
            # the same question. Compared against the sleeve's own maximum hold.
            # `_hours_for_nights` averages over all 168 entry instants, so it is only
            # meaningful for a sleeve whose entry hour is unconstrained. `fx_jpy` enters at
            # a fixed 09:00 broker and its 12 h ceiling lands at 21:00, crossing zero
            # midnights -- so no reachable hold takes it to break-even, and quoting an
            # averaged "8 h" would read as a threshold it can actually reach. Suppressed.
            break_even_hold_hours=(None if sl in CARRY_STRUCTURAL else _bh(be)),
            break_even_note=("entry hour is fixed at 09:00 broker and the 12 h ceiling lands "
                             "at 21:00, crossing zero rollovers on 292 of 292 sample days, so "
                             "no reachable hold reaches break-even"
                             if sl in CARRY_STRUCTURAL else None),
            # Three tiers, because "survives" is not one question:
            #   UNCONDITIONAL  break-even hold exceeds the sleeve's own maximum hold, so no
            #                  holding time it can physically reach takes its edge to zero
            #   CARRY_CONDITIONAL  survives iff the *mean* hold is under break_even_hold_hours
            #   DEAD_BEFORE_COST   negative gross of every broker cost
            cost_evaluable=cost_evaluable,
            priced_or_transferred_rows=priced_or_transferred,
            survivor_tier=("NOT_EVALUABLE_NO_COST_COVERAGE" if not cost_evaluable else
                           "DEAD_BEFORE_COST" if gross - ex <= 0 else
                           "UNCONDITIONAL" if (net["n_max"] > 0) else
                           # Promotion out of the conditional tier needs a STRUCTURAL bound,
                           # not just a favourable sample -- the live window never reached
                           # any sleeve's ceiling, so it cannot testify about carry there.
                           "MEASURED_LIVE_CARRY" if (live and sl in CARRY_STRUCTURAL and
                                                     gross - ex - pn * live["measured_nights"] > 0) else
                           "CARRY_CONDITIONAL_LIVE_SUPPORTED" if (
                               live and gross - ex - pn * live["measured_nights"] > 0) else
                           "CARRY_CONDITIONAL"),
            # Same fail-closed as `survivor_tier`, and this is the pair that actually reaches a
            # portfolio: `mc_firm_rules.build_cells` selects `SURVIVORS_ONLY` on
            # `survives_at_max_carry`. With no cost coverage `net["n_max"]` is plain gross, so
            # an uncosted sleeve would be SELECTED INTO the survivor book and then priced by
            # the Monte Carlo as if it were free.
            survives_to_horizon=bool(cost_evaluable and net["n_horizon_mean"] > 0),
            survives_at_max_carry=bool(cost_evaluable and net["n_max"] > 0),
            carry_headroom=(round(be / mean_n, 2) if be is not None and mean_n else None),
            cost_multiple=round(ex / charged, 2) if charged else None,
            status=dict(stat), coverage=dict(cov),
            direction=dict(
                rows_without_direction=nodir,
                share_without_direction_pct=round(100.0 * nodir / len(rs), 1),
                d4_long=d4_long, d4_short=d4_short,
                swap_side_spread_mean_r=(round(statistics.fmean(spread), 5) if spread else None),
                note=("swap charged as the mean of both legs where direction is unknown; "
                      "the spread between legs is the sleeve's own direction uncertainty")),
        )
    return out


def placebo(rows, account, class_medians, n_perm=1000, seed=20260727):
    """Null control: is a sleeve's survival a property of *which symbols cost what*, or
    just of its gross edge?

    The per-symbol true-cost vector is permuted across symbols -- the cost distribution is
    preserved exactly, only its assignment to instruments is destroyed -- and each sleeve's
    verdict recomputed. A sleeve that survives in ~all permutations was never decided by
    cost truth; its survival is a gross-edge fact and the re-cost did not settle it. Saying
    which sleeves those are is the difference between a measurement and a decoration.
    """
    import random as _r
    rng = _r.Random(seed)
    by_sleeve = collections.defaultdict(list)
    cost_by_sym = collections.defaultdict(list)
    for r in rows:
        c = r[f"cost_{account}"]
        v = (c["cost_ex_swap_r"] if c["status"] == "priced"
             else c["total_r"] if c["status"] == "transferred"
             else class_medians.get(r["sleeve"], 0.0))
        cost_by_sym[r["sym"]].append(v)
        by_sleeve[r["sleeve"]].append(r)
    cost_by_sym = {k: statistics.fmean(v) for k, v in cost_by_sym.items()}
    syms = sorted(cost_by_sym)
    vals = [cost_by_sym[s] for s in syms]
    real = {sl: statistics.fmean(r["R_gross"] - cost_by_sym[r["sym"]] for r in rs)
            for sl, rs in by_sleeve.items()}
    hits = collections.Counter()
    for _ in range(n_perm):
        perm = vals[:]
        rng.shuffle(perm)
        pm = dict(zip(syms, perm))
        for sl, rs in by_sleeve.items():
            if statistics.fmean(r["R_gross"] - pm[r["sym"]] for r in rs) > 0:
                hits[sl] += 1
    return {sl: dict(real_net_r_ex_swap=round(real[sl], 5), survives_real=real[sl] > 0,
                     placebo_survival_rate=round(hits[sl] / n_perm, 4),
                     cost_truth_decided=bool((real[sl] > 0) != (hits[sl] / n_perm > 0.5)))
            for sl in sorted(real)}


def f39_band(rows, account):
    """Where the F39 ambiguity actually bites, quantified both ways.

    Reading A -- the map was spread-only: commission was never in the baseline, so the book
    is optimistic by the full commission plus the erosion credit.
    Reading B -- the map was spread+commission: the credit returned a commission proxy that
    had legitimately been charged, so the optimism is commission net of the map's share.

    Neither reading changes `R_gross`, so neither changes the restatement -- what they
    change is the attribution of the error between F38 and F39. Both are published because
    the map has no generator and the record cannot settle it.
    """
    ero = {"HEATOIL_c": -1.506, "NATGAS_cash": -0.2647, "UKOIL_cash": -0.0372,
           "USDJPY": 0.0179, "USOIL_cash": 0.037, "XAGUSD": -0.005, "XAUUSD": 0.019}
    fanned = ["metals_core", "metals_softband", "metals_ob_micro", "energy_agri",
              "fx_jpy", "fx_jpy_ny"]
    per_sleeve = {}
    for sl in fanned:
        rs = [r for r in rows if r["sleeve"] == sl]
        if not rs:
            continue
        credit = statistics.fmean(ero.get(r["sym"], 0.0) for r in rs)
        legacy = statistics.fmean(r["charged_cost_r"] for r in rs)
        pr = [r for r in rs if r[f"cost_{account}"]["status"] == "priced"]
        comm = statistics.fmean(r[f"cost_{account}"]["commission_r"] for r in pr) if pr else None
        per_sleeve[sl] = dict(
            erosion_credit_applied_r=round(credit, 5),
            legacy_charge_r=round(legacy, 5),
            true_commission_r=(round(comm, 5) if comm is not None else None),
            readingA_spread_only_optimism_r=(round(credit + comm, 5) if comm is not None else None),
            readingB_commission_inclusive_optimism_r=(
                round(credit + max(0.0, comm - legacy), 5) if comm is not None else None),
            n_priced=len(pr), n=len(rs))
    return dict(
        note=("The applied erosion is mean(tick_real - modeled); tick_real is gross of all "
              "cost while modeled is net of the cost map (KB7_tick_mc.py:38, "
              "KB7_tick_truth.py:64 sets COMMISSION_R identically 0). The credit therefore "
              "contains the cost map itself -- measured at +0.1144 R for USDJPY against a "
              "map value of 0.1148. The like-for-like comparator `tick_costmap` is computed "
              "on the adjacent line and published per-symbol in KB7_TICK_TRUTH_RESULT.json; "
              "it was simply not the key selected. That is a key-selection error with a "
              "correct answer, not a map-content question. The A/B readings below are the "
              "separate, smaller ambiguity about what the map contained."),
        applied_erosion=ero, fanned_to=fanned, per_sleeve=per_sleeve)


# --------------------------------------------------------------------------------------
# 9. Calendar-day restatement
# --------------------------------------------------------------------------------------
def calendar_restatement(rows):
    """The book's 'days' are not the calendar's, and the headline monthly % assumes they are.

    `INTEG_W7_final_book.grid` reports `monthly_pct = mean(daily) * risk * 21`, i.e. it
    treats every one of the 1,679 rows in the series as one of 21 trading days in a month.
    They are not: they are *days on which the book fired at least once*, spread over
    eleven years, and in the early years the book fires a handful of times a year. The
    ratio below is the correction factor, and it is not close to 1.
    """
    days = sorted({r["date"] for r in rows})
    first, last = days[0], days[-1]
    sessions = sum(1 for i in range((last - first).days + 1)
                   if (first + dt.timedelta(days=i)).weekday() < 5)
    months = (last.year - first.year) * 12 + (last.month - first.month) + 1
    per_year = collections.Counter(d.year for d in days)
    fwd = [d for d in days if d.year >= 2025]
    f_first, f_last = fwd[0], fwd[-1]
    f_sessions = sum(1 for i in range((f_last - f_first).days + 1)
                     if (f_first + dt.timedelta(days=i)).weekday() < 5)
    f_months = (f_last.year - f_first.year) * 12 + (f_last.month - f_first.month) + 1
    return dict(
        note=("monthly_pct in INTEG_W7_FINAL_RESULT.json multiplies the per-book-day mean "
              "by 21. Over the full window the book fires on %.1f%% of weekday sessions, so "
              "21 book-days is roughly %.1f calendar months of trading; the forward window "
              "is much denser and close to the stated basis."
              % (100.0 * len(days) / sessions, 21.0 / (len(days) / months))),
        full_window=dict(
            first=first.isoformat(), last=last.isoformat(), book_days=len(days),
            weekday_sessions=sessions, density_pct=round(100.0 * len(days) / sessions, 2),
            calendar_months=months, book_days_per_month=round(len(days) / months, 2),
            headline_basis_book_days_per_month=21,
            monthly_pct_overstatement_x=round(21.0 / (len(days) / months), 2)),
        forward_2025_plus=dict(
            first=f_first.isoformat(), last=f_last.isoformat(), book_days=len(fwd),
            weekday_sessions=f_sessions, density_pct=round(100.0 * len(fwd) / f_sessions, 2),
            calendar_months=f_months, book_days_per_month=round(len(fwd) / f_months, 2),
            monthly_pct_overstatement_x=round(21.0 / (len(fwd) / f_months), 2)),
        book_days_per_year=dict(sorted(per_year.items())))


# --------------------------------------------------------------------------------------
# 10. Sensitivities -- the things that could flip the answer, each moved on its own
# --------------------------------------------------------------------------------------
def sensitivities(rows, account, class_medians, sd_book, W2, truth):
    """Each entry moves ONE assumption and reports the book mean at 1 night of carry.

    The point is decision-invariance: if the verdict is the same across the whole set, the
    modelling choices did not produce it. Where a sensitivity does move the verdict, that
    is the measurement the next session has to go and take.
    """
    out = {}

    def book_mean(policy):
        for r in rows:
            c, _ = row_cost(r, account, 1.0, policy, class_medians)
            r["R_sens"] = None if c is None else r["R_gross"] - c
        v = variant_stats(rows, "R_sens", sd_book, W2, dials=(0.020,))["kelly"]
        return dict(mean=v["mean"], mean_fwd=v["mean_fwd"], n_days=v["n_days"],
                    p_pass_200=v["mc"]["2.00%"]["p_pass"])

    out["unpriced_as_sleeve_median"] = book_mean("sleeve_median")
    out["unpriced_dropped"] = book_mean("drop")
    out["unpriced_keep_legacy_charge"] = book_mean("legacy")

    # book composition: the published final book drops HEATOIL_c + NATGAS_cash (T2), and
    # those two are exactly the symbols with no FTMO tick file, so the comparison to the
    # headline is only apples-to-apples with them removed.
    keep = [r for r in rows if r["sym"] not in ("HEATOIL_c", "NATGAS_cash")]
    for r in keep:
        c, _ = row_cost(r, account, 1.0, "sleeve_median", class_medians)
        r["R_sens"] = None if c is None else r["R_gross"] - c
    v = variant_stats(keep, "R_sens", sd_book, W2, dials=(0.020,))["kelly"]
    out["published_composition_drop_HEATOIL_NATGAS"] = dict(
        mean=v["mean"], mean_fwd=v["mean_fwd"], n_days=v["n_days"],
        p_pass_200=v["mc"]["2.00%"]["p_pass"],
        note="matches INTEG_W7_FINAL_RESULT.json dropped_symbols")

    # FTMO oil is class-'index' by its broker path ("Cash II CFD\\") and therefore inherits
    # the index class's ZERO commission, while the identical instruments on redacted_account are
    # class-'energy' and MEASURED at $5.00/lot. Charging FN's measured rate is the honest
    # upper bound on that misclassification.
    if account == "FTMO":
        for r in rows:
            c, _ = row_cost(r, account, 1.0, "sleeve_median", class_medians)
            add = 0.0
            if r["sym"] in ("USOIL_cash", "UKOIL_cash") and r["sl_price"]:
                rec = truth.instrument("FTMO", SYMBOL_MAP["FTMO"][r["sym"]])
                add = 5.0 / (r["sl_price"] * rec["usd_per_price_unit_per_lot"])
            r["R_sens"] = None if c is None else r["R_gross"] - c - add
        v = variant_stats(rows, "R_sens", sd_book, W2, dials=(0.020,))["kelly"]
        out["ftmo_oil_charged_redacted_account_rate"] = dict(
            mean=v["mean"], mean_fwd=v["mean_fwd"], n_days=v["n_days"],
            p_pass_200=v["mc"]["2.00%"]["p_pass"],
            note=("USOIL.cash/UKOIL.cash are instrument_class 'index' via "
                  "build_broker_true_costs.py:106 matching their 'Cash II CFD' path head, "
                  "so they inherit the index class's zero commission. Their redacted_account "
                  "twins are 'energy' and MEASURED at $5.00/lot."))
    for r in rows:
        r.pop("R_sens", None)
    return out


def analyse(st):
    rows, truth, args = st["rows"], st["truth"], st["args"]
    W2 = _route_mc()
    out = dict(
        schema="gtos.w7_recost.v1", generated_by="scripts/recost_w7_validation.py",
        inputs=dict(
            w3_cache=str(W3_CACHE.relative_to(REPO)), w5_cache=str(W5_CACHE.relative_to(REPO)),
            d4_ledger=str(D4_LEDGER.relative_to(REPO)),
            broker_truth="research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json"),
        book=dict(sleeves=list(CORE8_ORDER) + list(CLEAN3_CONF), conf=BOOK_CONF,
                  n_rows=len(rows), winsor_inert=st["winsor_inert"],
                  cached_R_min=round(st["lo"], 6), cached_R_max=round(st["hi"], 6)),
        charged_cost_witnesses=st["cost_checks"],
        variable_charge_pairs=dict(
            note=("These (sleeve, symbol) pairs were charged a PER-TRADE cost by their "
                  "generator -- class_cost * (0.5*ATR14(H4)/sd_h4) at "
                  "INTEG_portfolio_build_w3.py:89 and EXEC_exit_variants.py:45 -- not the "
                  "flat class value. Detected from the dispersion of their own stop-out "
                  "rows, which is the only witness that reads the consumed series. Exact "
                  "on stop-outs; elsewhere the pair's stop-out median, which is biased "
                  "high (tight stops pay more AND stop out more), so the band is the "
                  "honest range."),
            bands=st["variable_band"],
            charged_basis=dict(collections.Counter(
                r.get("charged_basis") for r in st["rows"]))),
        stop_distance=dict(
            tiers=dict(collections.Counter(r["stop_tier"] for r in rows)),
            measured_stop_atr_by_sleeve={k: round(v, 4) for k, v in st["k_sleeve"].items()},
            side_basis=dict(collections.Counter(r["side"] or "UNKNOWN_BOTH_LEGS" for r in rows))),
        price_basis=dict(collections.Counter(r["price_basis"] for r in rows)),
        atr_frac_by_class={k: round(v, 6) for k, v in st["atr_frac_by_class"].items()},
        price_series={k: dict(tf=v["tf"], first=str(v["first"]), last=str(v["last"]),
                              atr_frac=round(v["atr_frac"], 6), paths=v["paths"])
                      for k, v in st["prices"].items()},
        night_grid=list(NIGHT_GRID), accounts={})

    # --- pipeline parity: charge the LEGACY cost and reproduce the published base variant
    for r in rows:
        r["R_legacy"] = r["R"]
    _, _, _, sd_book = build_matrix_from(rows, "R_legacy")
    pub = json.loads((ROUTE / "INTEG_W7_FINAL_RESULT.json").read_text())
    base = variant_stats(rows, "R_legacy", sd_book, W2, dials=(0.015,))["flat"]
    out["pipeline_parity"] = dict(
        note=("Null control for the machinery itself: charge every row exactly what the "
              "validation charged and the rebuilt book must reproduce the published `base` "
              "variant. Any drift here invalidates every other number in this file."),
        rebuilt=dict(mean=base["mean"], std=base["std"], n_days=base["n_days"],
                     sd_book=round(sd_book, 5)),
        published=dict(mean=pub["variant_daily"]["base"]["mean"],
                       std=pub["variant_daily"]["base"]["std"], n_days=pub["n_days"],
                       sd_book=pub["sd_book"]),
        matches=dict(
            mean=abs(base["mean"] - pub["variant_daily"]["base"]["mean"]) < 5e-5,
            std=abs(base["std"] - pub["variant_daily"]["base"]["std"]) < 5e-5,
            n_days=base["n_days"] == pub["n_days"],
            sd_book=abs(sd_book - pub["sd_book"]) < 5e-5))

    for acct in ("FTMO", "redacted_account"):
        pool = collections.defaultdict(list)
        for r in rows:
            c = r[f"cost_{acct}"]
            if c["status"] == "priced":
                pool[r["sleeve"]].append(c["cost_ex_swap_r"])
        class_medians = {k: statistics.median(v) for k, v in pool.items()}
        acc = dict(sleeves=sleeve_table(rows, acct, class_medians),
                   placebo=placebo(rows, acct, class_medians),
                   f39_band=f39_band(rows, acct),
                   row_status=dict(collections.Counter(r[f"cost_{acct}"]["status"] for r in rows)),
                   unpriced=dict(collections.Counter(
                       f"{r['sleeve']}:{r['sym']}" for r in rows
                       if r[f"cost_{acct}"]["status"] == "unpriced")),
                   sensitivities=sensitivities(rows, acct, class_medians, sd_book, W2, truth),
                   book={})
        for nights in NIGHT_GRID:
            for r in rows:
                c, _ = row_cost(r, acct, nights, "sleeve_median", class_medians)
                r["R_true"] = None if c is None else r["R_gross"] - c
            acc["book"][f"nights_{int(nights)}"] = variant_stats(rows, "R_true", sd_book, W2)
        out["accounts"][acct] = acc

    out["calendar"] = calendar_restatement(rows)
    out["published_headline"] = dict(
        variant_daily=pub["variant_daily"], sd_book=pub["sd_book"], n_days=pub["n_days"],
        mc_final_150=pub["mc_volmatched_all"]["final"]["1.50%"],
        mc_final_200=pub["mc_volmatched_all"]["final"]["2.00%"],
        sleeve_contribution_final=pub["sleeve_contribution_final"])
    return out


def main(argv=None):
    st = build(argv)
    out = analyse(st)
    p = st["outdir"] / "W7_RECOST_V1.json"
    p.write_text(json.dumps(out, indent=1, default=str))
    print(f"wrote {p.relative_to(REPO)}")
    return out


if __name__ == "__main__":
    main()
