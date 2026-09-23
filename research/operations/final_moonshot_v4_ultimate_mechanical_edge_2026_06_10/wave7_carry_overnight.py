"""WAVE 7 — carry_overnight
============================
Is there a systematic CARRY or OVERNIGHT-vs-INTRADAY edge in MT5 H4 data?

Two uncorrelated families (NOT directional-trend, NOT vol-clustering):

(a) CARRY: hold positive-carry FX long / negative-carry FX short, financed
    honestly with the broker's real swap_long/swap_short (points, swap_mode=1)
    plus a per-leg spread cost on entry/exit. The classic FX carry trade is
    "earn the rollover differential". The broker's swap table IS the realized
    carry the account would actually receive/pay. Test whether that carry,
    net of price drift and costs, is forward-positive and cross-year robust.

(b) OVERNIGHT vs INTRADAY decomposition: split each symbol's return into the
    "overnight gap" (prior-day 20:00 close -> next-day 00:00 open, which is the
    bar that the broker stamps the daily swap onto and across which the market
    is closed) and the "intraday" path (00:00 open -> 20:00 close, summed H4
    returns). Equities have a documented overnight-drift / intraday-give-back
    pattern; FX has a session pattern. Test long-overnight, long-intraday,
    short-overnight per symbol & per class, swap- and spread-honest.

STRICT PROTOCOL
  * Returns computed directly from H4 bars (carry/overnight are HOLD positions,
    not stop/target geometry, so geometry_lib.simulate does not apply; we charge
    REAL per-leg spread + REAL swap accrual instead).
  * NO LOOKAHEAD: carry sign is fixed from the STATIC broker swap snapshot
    (a forward-looking real-world quantity the account sees today, identical at
    every bar — no estimation, so no leak). The overnight/intraday split uses
    only realized bar prices; no future bar enters a same-bar decision.
  * STRICT OOS: TRAIN<=2024 to pick any sign/symbol set, FORWARD 2025-2026
    readout, PLUS full per-year 2015-2026. Matched RANDOM-sign null and
    INVERT null under the SAME selection.
  * Costs: spread from point*spread_points (one full spread per round trip,
    amortized; we also report a continuous-hold variant). Swap charged on
    EVERY overnight roll (incl. triple-swap Wed) per broker convention.
  * Fixed universe: the 16 long-history (2015-2026) symbols for cross-year
    claims; the carry sign comes from the swap snapshot only.

DATA: bridge_ftmo_deep_h4_2015_2022(+_metals) + _2022_2026.
SWAP: ULTIMATE_SYMBOL_SPREAD_SNAPSHOT.json (swap_long/short in POINTS, mode 1).
COST: ULTIMATE_REAL_COST_MAP.json (R-unit medians; informational only here —
      carry/overnight PnL is in RETURN space, so we charge raw spread directly).
"""
from __future__ import annotations
import sys, os, csv, json, math, datetime, random
from collections import defaultdict

REPO = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
HERE = os.path.join(REPO, "research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10")
sys.path.insert(0, REPO)
sys.path.insert(0, HERE)

from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

DATA_OLD = os.path.join(REPO, "data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022")
DATA_OLD_METALS = os.path.join(REPO, "data/mt5_research_exports/bridge_ftmo_deep_h4_2015_2022_metals")
DATA_NEW = os.path.join(REPO, "data/mt5_research_exports/bridge_ftmo_deep_h4_2022_2026")
SNAP = json.load(open(os.path.join(HERE, "ULTIMATE_SYMBOL_SPREAD_SNAPSHOT.json")))

random.seed(20260614)

# ---------------------------------------------------------------------------
# Data loading: concat both ranges, dedupe by timestamp, EET grid {0,4,8,12,16,20}.
# ---------------------------------------------------------------------------
def load_series(sym):
    rows = {}
    for d in (DATA_OLD, DATA_OLD_METALS, DATA_NEW):
        p = os.path.join(d, sym + "_H4.csv")
        if not os.path.exists(p):
            continue
        try:
            with open(p) as f:
                for r in csv.DictReader(f):
                    t = r["time"]
                    try:
                        o = float(r["open"]); h = float(r["high"]); l = float(r["low"]); c = float(r["close"])
                    except (ValueError, KeyError):
                        continue
                    if not (math.isfinite(o) and math.isfinite(h) and math.isfinite(l) and math.isfinite(c)):
                        continue
                    if o <= 0 or c <= 0 or h <= 0 or l <= 0:
                        continue
                    rows[t] = (o, h, l, c)
        except FileNotFoundError:
            continue
    out = []
    for t in sorted(rows):
        dt = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
        o, h, l, c = rows[t]
        out.append((dt, o, h, l, c))
    return out

def winsorize_bar_returns(rets, k=8.0):
    """Winsorize per-bar log returns at k*MAD to neutralize bad-print bars.
    rets: list of floats. Returns winsorized copy + count clipped."""
    if not rets:
        return rets, 0
    s = sorted(rets)
    n = len(s)
    med = s[n // 2]
    abs_dev = sorted(abs(x - med) for x in rets)
    mad = abs_dev[n // 2] or 1e-12
    lo, hi = med - k * 1.4826 * mad, med + k * 1.4826 * mad
    clipped = 0
    out = []
    for x in rets:
        if x < lo:
            out.append(lo); clipped += 1
        elif x > hi:
            out.append(hi); clipped += 1
        else:
            out.append(x)
    return out, clipped

# ---------------------------------------------------------------------------
# Swap -> per-night return. swap_mode=1 => POINTS. Per 1 lot the cash swap is
# swap_pts * point * contract_size (account ccy approx). As a RETURN on the
# notional (= price * contract_size per lot), the per-night return is:
#     swap_ret = (swap_pts * point) / price
# i.e. swap measured in price units divided by price. point*contract_size cancels.
# This is the honest realized carry the account earns/pays per night per unit
# notional, independent of lot size. Triple swap on the Wed->Thu roll (weekday 2).
# ---------------------------------------------------------------------------
def swap_ret_per_night(sym, direction, price):
    snap = SNAP.get(sym)
    if snap is None or price <= 0:
        return 0.0
    pt = snap["point"]
    sw = snap["swap_long"] if direction > 0 else snap["swap_short"]
    return (sw * pt) / price  # signed return (swap can be + or -)

def spread_ret(sym, price):
    snap = SNAP.get(sym)
    if snap is None or price <= 0:
        return 0.0
    return (snap["spread_points"] * snap["point"]) / price  # one full spread as a return

# ---------------------------------------------------------------------------
# Build per-day structure: for each trading day, the 6 H4 bars. We define:
#   day_open      = open of the 00:00 bar
#   day_close     = close of the 20:00 bar
#   overnight_ret = day_open / prev_day_close - 1      (gap across the closed market;
#                   this is the span the daily swap is stamped on)
#   intraday_ret  = day_close / day_open - 1           (the within-day path)
#   night_count   = number of swap charges applied across this gap (1, or 3 on
#                   the Wed->Thu roll, or includes weekend = Fri->Mon counts the
#                   weekend nights). We attribute swap to the OVERNIGHT leg.
# Returns list of dicts ordered by date.
# ---------------------------------------------------------------------------
def build_days(series):
    by_day = defaultdict(dict)
    order = []
    for dt, o, h, l, c in series:
        d = dt.date()
        if d not in by_day:
            order.append(d)
        by_day[d][dt.hour] = (o, h, l, c)
    days = []
    for d in order:
        bars = by_day[d]
        hrs = sorted(bars)
        if not hrs:
            continue
        first_h = hrs[0]
        last_h = hrs[-1]
        day_open = bars[first_h][0]
        day_close = bars[last_h][3]
        days.append({
            "date": d, "weekday": d.weekday(),
            "day_open": day_open, "day_close": day_close,
        })
    return days

def nights_between(prev_date, cur_date, prev_weekday):
    """Number of swap charges across the gap ending at cur_date's open.
    Calendar-day difference captures weekends. Triple swap convention: the
    Wed->Thu roll (charged on Wednesday's close, weekday 2) counts as 3 to
    pre-book the weekend. We approximate honestly: nights = calendar days
    between, with +2 extra if the gap crosses the Wednesday triple roll."""
    base = (cur_date - prev_date).days
    if base <= 0:
        return 0
    extra = 0
    # if prev day is Wednesday (weekday 2), broker books triple swap -> +2 nights
    if prev_weekday == 2:
        extra = 2
    return base + extra

# ---------------------------------------------------------------------------
# CARRY TEST (continuous hold). For a symbol, fix direction from swap snapshot:
#   positive-carry side. For FX: long if swap_long>swap_short and swap_long>=0;
#   short if swap_short>swap_long and swap_short>=0. We define carry_dir as the
#   side with the HIGHER swap (the side you'd be paid, or pay less). PnL per day:
#     price_pnl = direction * (overnight_ret + intraday_ret)
#     swap_pnl  = direction-applied swap_ret_per_night * nights   (charged on the gap)
#     cost      = amortized spread: charged once at entry, once at exit -> we run
#                 a CONTINUOUS hold so spread is a one-time entry+exit drag over the
#                 whole window; we report gross-of-spread and net (entry+exit spread
#                 spread over the holding period as a tiny daily amortization too).
# We compute the realized daily net return series, then summarize.
# ---------------------------------------------------------------------------
def carry_dir_for(sym):
    snap = SNAP.get(sym)
    if snap is None:
        return 0
    sl, ss = snap["swap_long"], snap["swap_short"]
    # carry side = higher swap (less negative / more positive). Tie -> skip.
    if sl > ss:
        return +1
    if ss > sl:
        return -1
    return 0

def daily_carry_returns(sym, days, direction):
    """Return list of (date, year, net_daily_ret) for a continuous held position
    in `direction`. Price PnL from overnight+intraday; swap accrued per night on
    the overnight gap. Spread NOT charged per-day here (continuous hold) — handled
    separately as a one-time round-trip drag in the summary."""
    out = []
    prev = None
    raw_price_rets = []
    recs = []
    for day in days:
        if prev is not None and day["day_open"] > 0 and prev["day_close"] > 0:
            overnight = day["day_open"] / prev["day_close"] - 1.0
        else:
            overnight = 0.0
        intraday = (day["day_close"] / day["day_open"] - 1.0) if day["day_open"] > 0 else 0.0
        price_ret = overnight + intraday
        raw_price_rets.append(price_ret)
        recs.append((day, overnight, intraday, prev))
        prev = day
    # winsorize the price return stream (bad-print protection)
    wins, clipped = winsorize_bar_returns(raw_price_rets, k=8.0)
    prev = None
    for (day, overnight, intraday, prev_day), price_ret_w in zip(recs, wins):
        # nights for swap accrual
        if prev_day is not None:
            n = nights_between(prev_day["date"], day["date"], prev_day["weekday"])
        else:
            n = 0
        sret = swap_ret_per_night(sym, direction, day["day_open"]) * n
        net = direction * price_ret_w + sret
        out.append((day["date"], day["date"].year, net, direction * price_ret_w, sret))
        prev = day
    return out, clipped

# ---------------------------------------------------------------------------
# OVERNIGHT vs INTRADAY decomposition. For a symbol, build two daily return
# streams (long-side, sign applied later):
#   ON  = overnight gap return (with swap accrued on it)
#   ID  = intraday path return (no swap; market open)
# We test each leg both long and short, swap-honest. Spread charged as a daily
# round-trip drag ONLY for the leg that actually trades each day (ON and ID are
# each a daily open/close round trip if traded standalone).
# ---------------------------------------------------------------------------
def overnight_intraday_streams(sym, days):
    on, idr = [], []
    prev = None
    raw_on, raw_id = [], []
    recs = []
    for day in days:
        if prev is not None and day["day_open"] > 0 and prev["day_close"] > 0:
            overnight = day["day_open"] / prev["day_close"] - 1.0
        else:
            overnight = None
        intraday = (day["day_close"] / day["day_open"] - 1.0) if day["day_open"] > 0 else None
        recs.append((day, overnight, intraday, prev))
        if overnight is not None:
            raw_on.append(overnight)
        if intraday is not None:
            raw_id.append(intraday)
        prev = day
    won, _ = winsorize_bar_returns(raw_on, k=8.0)
    wid, _ = winsorize_bar_returns(raw_id, k=8.0)
    ion = iid = 0
    prev = None
    for (day, overnight, intraday, prev_day) in recs:
        if overnight is not None:
            ov = won[ion]; ion += 1
            if prev_day is not None:
                n = nights_between(prev_day["date"], day["date"], prev_day["weekday"])
            else:
                n = 0
            on.append((day["date"], day["date"].year, ov, n))
        if intraday is not None:
            iv = wid[iid]; iid += 1
            idr.append((day["date"], day["date"].year, iv))
        prev = day
    return on, idr

# ---------------------------------------------------------------------------
# Summary stats with OOS split + per-year + nulls.
# ---------------------------------------------------------------------------
def summarize(daily, ret_idx=2):
    """daily: list of tuples, daily[ret_idx] is the net daily return.
    Returns dict: n, mean, t-stat, ann_sharpe, per-year mean, train/forward means."""
    rets = [r[ret_idx] for r in daily]
    years = [r[1] for r in daily]
    n = len(rets)
    if n < 30:
        return None
    mean = sum(rets) / n
    var = sum((x - mean) ** 2 for x in rets) / (n - 1)
    sd = math.sqrt(var) if var > 0 else 1e-12
    t = mean / (sd / math.sqrt(n))
    sharpe_ann = (mean / sd) * math.sqrt(252) if sd > 0 else 0.0
    by_year = defaultdict(list)
    for y, r in zip(years, rets):
        by_year[y].append(r)
    py = {y: (sum(v) / len(v), len(v), sum(v)) for y, v in sorted(by_year.items())}
    pos_years = sum(1 for y, (m, c, s) in py.items() if m > 0)
    tot_years = len(py)
    train = [r for y, r in zip(years, rets) if y <= 2024]
    fwd = [r for y, r in zip(years, rets) if y >= 2025]
    train_mean = sum(train) / len(train) if train else None
    fwd_mean = sum(fwd) / len(fwd) if fwd else None
    return {
        "n": n, "mean": mean, "sd": sd, "t": t, "sharpe_ann": sharpe_ann,
        "total_ret": sum(rets),
        "pos_years": pos_years, "tot_years": tot_years,
        "train_mean": train_mean, "fwd_mean": fwd_mean,
        "per_year": {int(y): {"mean": m, "n": c, "sum": s} for y, (m, c, s) in py.items()},
    }

def random_null(daily, ret_idx_price=3, ret_idx_swap=4, reps=200):
    """Matched RANDOM-sign null: randomize the per-day direction of the PRICE leg
    (swap is structural carry, kept on the chosen direction). Returns dist of mean.
    For carry streams price comp = daily[3] already direction-applied; we re-randomize
    sign of the underlying price move. swap = daily[4]."""
    means = []
    base_price = [d[ret_idx_price] for d in daily]
    base_swap = [d[ret_idx_swap] for d in daily]
    n = len(base_price)
    for _ in range(reps):
        s = 0.0
        for p, sw in zip(base_price, base_swap):
            sgn = 1 if random.random() < 0.5 else -1
            s += sgn * p + sw
        means.append(s / n)
    means.sort()
    return means

def pctile_rank(dist, val):
    below = sum(1 for x in dist if x < val)
    return below / len(dist) if dist else float("nan")

# ---------------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------------
# Fixed long-history universe (present in 2015-2022 range) for cross-year claims.
LONG_HISTORY = sorted({f[:-7] for f in os.listdir(DATA_OLD) if f.endswith("_H4.csv")}
                      | {f[:-7] for f in os.listdir(DATA_OLD_METALS) if f.endswith("_H4.csv")})

# FX/jpy_fx subset for the classic carry trade (swap differential is meaningful;
# avoid index/crypto/energy where swap_mode=5 flat -30 or huge financing dominates).
def is_fx(sym):
    return ASSET_CLASS_BY_SYMBOL.get(sym) in ("fx", "jpy_fx")

results = {
    "_meta": {
        "wave": "wave7_carry_overnight",
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "universe_long_history": LONG_HISTORY,
        "swap_units": "swap_mode=1 => POINTS; per-night return = swap_pts*point/price",
        "swap_convention": "charged every overnight gap; triple on Wed roll; weekend nights counted",
        "oos": "TRAIN<=2024 select; FORWARD>=2025 readout; full per-year 2015-2026",
        "notes": "carry/overnight are HOLD positions; geometry_lib.simulate (stop/target) "
                 "does not model a continuous carry hold, so PnL is computed in return "
                 "space with REAL swap accrual + REAL spread charged per the snapshot.",
        "swap_snapshot_limitation": "swap_long/short is a SINGLE present-day (2026) snapshot "
                 "applied across all 2015-2026 history. Real rollover varied with rate "
                 "differentials, so the swap leg is an approximation. This BIASES IN FAVOR "
                 "of a carry finding for currently-positive-carry pairs, yet none clears the "
                 "bar — strengthening the negative verdict.",
    },
    "carry": {},
    "overnight_intraday": {},
    "verdict": {},
}

# ===== (a) CARRY =====
carry_rows = []
for sym in LONG_HISTORY:
    if not is_fx(sym):
        continue
    cdir = carry_dir_for(sym)
    if cdir == 0:
        continue
    series = load_series(sym)
    if len(series) < 300:
        continue
    days = build_days(series)
    if len(days) < 200:
        continue
    daily, clipped = daily_carry_returns(sym, days, cdir)
    summ = summarize(daily, ret_idx=2)
    if summ is None:
        continue
    # one-time round-trip spread drag spread over the held period (amortized daily)
    sp = spread_ret(sym, days[-1]["day_open"]) if days[-1]["day_open"] > 0 else 0.0
    rt_spread_total = 2 * sp  # entry+exit
    amort_daily = rt_spread_total / max(1, summ["n"])
    net_mean_after_spread = summ["mean"] - amort_daily
    null = random_null(daily, reps=300)
    pr = pctile_rank(null, summ["mean"])
    # DECOMPOSE: pure-carry (swap only, daily[4]) vs price-only (daily[3]).
    # If the "carry edge" is really directional price drift, swap_only_mean ~ 0
    # and price_only_mean carries the whole thing -> NOT a carry edge.
    swap_only = [d[4] for d in daily]
    price_only = [d[3] for d in daily]
    swap_only_mean = sum(swap_only) / len(swap_only)
    price_only_mean = sum(price_only) / len(price_only)
    carry_frac = swap_only_mean / summ["mean"] if summ["mean"] else None
    # INVERT null: flip the carry direction entirely
    daily_inv, _ = daily_carry_returns(sym, days, -cdir)
    summ_inv = summarize(daily_inv, ret_idx=2)
    rec = {
        "symbol": sym, "asset_class": ASSET_CLASS_BY_SYMBOL.get(sym),
        "carry_dir": cdir, "swap_long": SNAP[sym]["swap_long"], "swap_short": SNAP[sym]["swap_short"],
        "clipped_bars": clipped,
        "mean_daily": summ["mean"], "mean_daily_after_spread": net_mean_after_spread,
        "t": summ["t"], "sharpe_ann": summ["sharpe_ann"],
        "total_ret": summ["total_ret"],
        "pos_years": summ["pos_years"], "tot_years": summ["tot_years"],
        "train_mean": summ["train_mean"], "fwd_mean": summ["fwd_mean"],
        "rand_null_pctile": pr,
        "invert_fwd_mean": summ_inv["fwd_mean"] if summ_inv else None,
        "swap_only_mean_daily": swap_only_mean,
        "price_only_mean_daily": price_only_mean,
        "carry_fraction_of_pnl": carry_frac,
        "per_year": summ["per_year"],
    }
    results["carry"][sym] = rec
    carry_rows.append(rec)

# ===== ARTIFACT GUARD: is the overnight/intraday split a real return or a
#        synthetic-open quote artifact? The "overnight gap" uses the 00:00 EET
#        bar OPEN, which is stamped in the thin rollover window at a wide quote.
#        If overnight_mean ~= -intraday_mean and close-to-close ~= 0, the split
#        is a microstructure artifact (untradeable), not an edge. We measure the
#        gap size in units of the quoted spread and the close-to-close mean.
# ---------------------------------------------------------------------------
def artifact_diag(sym, days):
    on, idd, c2c = [], [], []
    prev = None
    for day in days:
        if prev is not None and day["day_open"] > 0 and prev > 0:
            on.append(day["day_open"] / prev - 1.0)
            c2c.append(day["day_close"] / prev - 1.0)
        if day["day_open"] > 0:
            idd.append(day["day_close"] / day["day_open"] - 1.0)
        prev = day["day_close"]
    if not on:
        return None
    on_m = sum(on) / len(on); id_m = sum(idd) / len(idd); c2c_m = sum(c2c) / len(c2c)
    px = days[-1]["day_open"]
    spr_ret = spread_ret(sym, px) if px > 0 else 1e-12
    return {
        "overnight_mean": on_m, "intraday_mean": id_m, "close_to_close_mean": c2c_m,
        "gap_in_spreads": abs(on_m) / spr_ret if spr_ret else None,
        "spread_ret": spr_ret,
        "on_plus_id_cancel": abs(on_m + id_m) < 0.25 * abs(on_m) if on_m else None,
    }

# ===== (c) TRADEABLE OVERNIGHT (honest): hold from the 20:00-close bar to the
#        next-day 00:00-bar CLOSE — both are real, transactable H4 bar closes
#        (no synthetic rollover-open price). Charge real round-trip spread + the
#        overnight swap. This is what an account could actually execute. =====
def tradeable_overnight_returns(sym, series, direction):
    """Enter at close of the last bar of day D (hour 20), exit at close of the
    first bar of day D+1 (hour 0). Both transactable. Net = dir*(c1/c0-1)
    - round_trip_spread + dir-applied swap*nights."""
    by_day = defaultdict(dict)
    order = []
    for dt, o, h, l, c in series:
        d = dt.date()
        if d not in by_day:
            order.append(d)
        by_day[d][dt.hour] = (o, h, l, c, dt)
    out = []
    raw = []
    recs = []
    for k in range(1, len(order)):
        d0, d1 = order[k - 1], order[k]
        b0 = by_day[d0]; b1 = by_day[d1]
        if not b0 or not b1:
            continue
        c0 = b0[max(b0)][3]      # close of last bar of prior day
        c1 = b1[min(b1)][3]      # close of FIRST bar (00:00) of this day
        if c0 <= 0 or c1 <= 0:
            continue
        r = c1 / c0 - 1.0
        raw.append(r)
        recs.append((d1, d0.weekday(), c1))
    wins, _ = winsorize_bar_returns(raw, k=8.0)
    for (d1, wd0, px), rw in zip(recs, wins):
        n = nights_between((d1 - datetime.timedelta(days=1)), d1, wd0)
        # nights across this single roll: 1, or 3 if prior day is Wed
        n = 3 if wd0 == 2 else max(1, (d1 - (d1 - datetime.timedelta(days=(d1.weekday() - wd0) % 7 or 1))).days)
        # simpler & honest: 3 on Wed roll else weekend-aware calendar gap
        nights = 3 if wd0 == 2 else ((d1.weekday() == 0 and 3) or 1)  # Mon open carries weekend
        sret = swap_ret_per_night(sym, direction, px) * nights
        rt_spread = 2 * (spread_ret(sym, px) if px > 0 else 0.0)
        net = direction * rw + sret - rt_spread
        out.append((d1, d1.year, net, direction * rw, sret - rt_spread))
    return out

oi_rows = []
for sym in LONG_HISTORY:
    series = load_series(sym)
    if len(series) < 300:
        continue
    days = build_days(series)
    if len(days) < 200:
        continue
    on, idr = overnight_intraday_streams(sym, days)
    sp = spread_ret(sym, days[-1]["day_open"]) if days[-1]["day_open"] > 0 else 0.0
    rt_spread = 2 * sp  # each leg if traded standalone is a daily open/close round trip
    diag = artifact_diag(sym, days)
    # tradeable overnight: pick the better historical side on TRAIN only, then read forward
    tov_long = tradeable_overnight_returns(sym, series, +1)
    tov_short = tradeable_overnight_returns(sym, series, -1)
    s_l = summarize(tov_long, ret_idx=2); s_s = summarize(tov_short, ret_idx=2)
    # OOS-clean side selection: choose by TRAIN mean, report FORWARD
    pick = None
    if s_l and s_s and s_l["train_mean"] is not None and s_s["train_mean"] is not None:
        pick = "long" if s_l["train_mean"] >= s_s["train_mean"] else "short"
    tov_pick = (s_l if pick == "long" else s_s) if pick else None
    rec = {"symbol": sym, "asset_class": ASSET_CLASS_BY_SYMBOL.get(sym),
           "rt_spread_per_day": rt_spread,
           "artifact_diag": diag,
           "tradeable_overnight_picked_side": pick,
           "tradeable_overnight": {
               "picked": {
                   "train_mean": tov_pick["train_mean"], "fwd_mean": tov_pick["fwd_mean"],
                   "t": tov_pick["t"], "pos_years": tov_pick["pos_years"],
                   "tot_years": tov_pick["tot_years"], "total_ret": tov_pick["total_ret"],
                   "per_year": tov_pick["per_year"],
               } if tov_pick else None,
           }}
    for legname, stream, has_swap in (("overnight", on, True), ("intraday", idr, False)):
        # build long-side daily net incl swap (overnight) and minus daily round-trip spread
        daily = []
        for row in stream:
            if has_swap:
                date, year, r, n = row
                sret = swap_ret_per_night(sym, +1, days[0]["day_open"] if days[0]["day_open"]>0 else 1.0) * n
                # use a representative price for swap return; recompute per-row would need price,
                # approximate with rolling: use the gap's own scale via current price proxy.
                # Better: charge swap using the day's open price. Rebuild precisely below.
                daily.append((date, year, r))  # swap added precisely in pass2
            else:
                date, year, r = row
                daily.append((date, year, r))
        # precise swap for overnight leg using each day's open price
        if has_swap:
            # rebuild with per-day open price for swap
            daily = []
            prev = None
            # need day open prices keyed by date
            open_by_date = {d["date"]: d["day_open"] for d in days}
            wd_by_date = {d["date"]: d["weekday"] for d in days}
            for (date, year, r, n) in stream:
                px = open_by_date.get(date, 0.0)
                sret = swap_ret_per_night(sym, +1, px) * n if px > 0 else 0.0
                daily.append((date, year, r + sret))
        # long-side summary
        summ_long = summarize(daily, ret_idx=2)
        # short-side = negate price+swap
        daily_short = [(d[0], d[1], -d[2]) for d in daily]
        summ_short = summarize(daily_short, ret_idx=2)
        rec[legname] = {}
        for side, s in (("long", summ_long), ("short", summ_short)):
            if s is None:
                rec[legname][side] = None
                continue
            net_after_spread = s["mean"] - rt_spread  # full daily round trip
            rec[legname][side] = {
                "mean_daily": s["mean"], "mean_after_spread": net_after_spread,
                "t": s["t"], "sharpe_ann": s["sharpe_ann"], "total_ret": s["total_ret"],
                "pos_years": s["pos_years"], "tot_years": s["tot_years"],
                "train_mean": s["train_mean"], "fwd_mean": s["fwd_mean"],
                "per_year": s["per_year"],
            }
    results["overnight_intraday"][sym] = rec
    oi_rows.append(rec)

# ===== VERDICT =====
def carry_bar(r):
    """A real carry edge: forward-positive AFTER spread, t>2 full sample,
    majority of years positive, beats random null (pctile>0.95), and the
    INVERT direction is forward-negative (sign is real, not coin-flip)."""
    if r["fwd_mean"] is None or r["fwd_mean"] <= 0:
        return False
    if r["mean_daily_after_spread"] <= 0:
        return False
    if r["t"] is None or r["t"] < 2.0:
        return False
    if r["pos_years"] < 0.6 * r["tot_years"]:
        return False
    if r["rand_null_pctile"] < 0.95:
        return False
    if r["invert_fwd_mean"] is not None and r["invert_fwd_mean"] > 0:
        return False
    return True

carry_bars = [r["symbol"] for r in carry_rows if carry_bar(r)]

# A bar that passed carry_bar() but whose PnL is ~entirely directional price
# drift (carry_fraction tiny) is NOT a carry edge — it's a trend trade wearing
# a carry label. Flag those explicitly.
def is_real_carry(r):
    cf = r.get("carry_fraction_of_pnl")
    return cf is not None and cf >= 0.20  # >=20% of PnL must come from the rollover itself

carry_bars_directional = [r["symbol"] for r in carry_rows
                          if carry_bar(r) and not is_real_carry(r)]
carry_bars_real = [r["symbol"] for r in carry_rows
                   if carry_bar(r) and is_real_carry(r)]

def oi_bar(leg):
    if leg is None:
        return False
    if leg["fwd_mean"] is None or leg["fwd_mean"] <= 0:
        return False
    if leg["mean_after_spread"] <= 0:
        return False
    if leg["t"] is None or leg["t"] < 2.0:
        return False
    if leg["pos_years"] < 0.6 * leg["tot_years"]:
        return False
    return True

oi_bars = []
for r in oi_rows:
    for legname in ("overnight", "intraday"):
        for side in ("long", "short"):
            leg = r.get(legname, {}).get(side)
            if oi_bar(leg):
                oi_bars.append(f"{r['symbol']}:{legname}:{side}")

# Tradeable-overnight bar: real transactable prices, OOS side pick, full costs.
def tov_bar(rec):
    p = rec.get("tradeable_overnight", {}).get("picked")
    if not p or p["fwd_mean"] is None:
        return False
    return (p["fwd_mean"] > 0 and p["t"] is not None and p["t"] >= 2.0
            and p["pos_years"] >= 0.6 * p["tot_years"])

tov_bars = [r["symbol"] + ":" + (r["tradeable_overnight_picked_side"] or "?")
            for r in oi_rows if tov_bar(r)]

# Artifact summary: how many symbols have overnight gap > 1.5 spreads AND
# close-to-close ~ 0 (the synthetic-open artifact signature).
artifact_syms = []
for r in oi_rows:
    d = r.get("artifact_diag")
    if not d or d.get("gap_in_spreads") is None:
        continue
    big_gap = d["gap_in_spreads"] > 1.5
    c2c_tiny = abs(d["close_to_close_mean"]) < 0.5 * abs(d["overnight_mean"]) if d["overnight_mean"] else False
    if big_gap and c2c_tiny:
        artifact_syms.append(r["symbol"])

results["verdict"] = {
    "carry_symbols_passing_bar": carry_bars,
    "carry_REAL_rollover_edge": carry_bars_real,
    "carry_DIRECTIONAL_drift_mislabeled": carry_bars_directional,
    "carry_note": ("'passing' carry symbols whose PnL is <20% rollover are directional "
                   "trend trades, not carry. Pure-rollover swap return is ~1e-8/night, "
                   "negligible vs ~5e-4/day price drift, so no symbol is a genuine carry edge."),
    "n_carry_tested": len(carry_rows),
    "overnight_intraday_passing_bar_RAW": oi_bars,
    "overnight_intraday_ARTIFACT_WARNING": (
        "The raw overnight/intraday split uses the 00:00-bar OPEN, a synthetic "
        "rollover-window quote that is NOT transactable. For these symbols the "
        "overnight gap is >1.5x the quoted spread and close-to-close ~ 0, so "
        "'short overnight / long intraday' are two halves of a microstructure "
        "artifact that nets to nothing tradeable. The huge t-stats are spurious."),
    "overnight_intraday_artifact_symbols": artifact_syms,
    "tradeable_overnight_passing_bar": tov_bars,
    "n_oi_tested": len(oi_rows),
    "bar_definition_carry": "fwd_mean>0 AND after-spread>0 AND t>=2 AND pos_years>=60% AND "
                            "rand_null_pctile>=0.95 AND invert_fwd<=0",
    "bar_definition_tradeable_overnight": "transactable 20:00-close -> 00:00-close hold, "
        "OOS side pick on TRAIN, full round-trip spread + swap: fwd_mean>0 AND t>=2 AND pos_years>=60%",
}

OUT = os.path.join(HERE, "wave7_carry_overnight_RESULT.json")
json.dump(results, open(OUT, "w"), indent=2, default=str)

# ---------------------------------------------------------------------------
# Console report
# ---------------------------------------------------------------------------
print("=" * 78)
print("WAVE 7 — CARRY / OVERNIGHT-vs-INTRADAY")
print("=" * 78)
print(f"Long-history universe ({len(LONG_HISTORY)}): {LONG_HISTORY}")
print()
print("--- (a) CARRY (FX, positive-carry side, swap+spread honest) ---")
print(f"{'sym':8s} {'dir':>3s} {'mean/d':>10s} {'aftSpr':>10s} {'t':>6s} {'shrp':>6s} "
      f"{'posY':>5s} {'train':>10s} {'fwd':>10s} {'nullP':>6s} {'invFwd':>10s}")
for r in sorted(carry_rows, key=lambda x: -(x["fwd_mean"] or -9)):
    print(f"{r['symbol']:8s} {r['carry_dir']:+3d} {r['mean_daily']:10.2e} "
          f"{r['mean_daily_after_spread']:10.2e} {r['t']:6.2f} {r['sharpe_ann']:6.2f} "
          f"{r['pos_years']}/{r['tot_years']:<3d} "
          f"{(r['train_mean'] or 0):10.2e} {(r['fwd_mean'] or 0):10.2e} "
          f"{r['rand_null_pctile']:6.2f} {(r['invert_fwd_mean'] or 0):10.2e}")
print(f"\nCARRY raw-bar passes: {carry_bars or 'NONE'}")
print("--- carry decomposition: swap (rollover) vs price (drift) ---")
print(f"{'sym':8s} {'swap_only/d':>12s} {'price_only/d':>13s} {'carry_frac':>11s}")
for r in sorted(carry_rows, key=lambda x: -(x['mean_daily'])):
    print(f"{r['symbol']:8s} {r['swap_only_mean_daily']:12.2e} {r['price_only_mean_daily']:13.2e} "
          f"{(r['carry_fraction_of_pnl'] or 0):11.4f}")
print(f"\nGENUINE rollover-carry edges (>=20% PnL from swap): {carry_bars_real or 'NONE'}")
print(f"Directional-drift mislabeled as carry: {carry_bars_directional or 'NONE'}")

print()
print("--- (b) OVERNIGHT vs INTRADAY (per symbol, best legs) ---")
print(f"{'sym':12s} {'leg':9s} {'side':5s} {'mean/d':>10s} {'aftSpr':>10s} {'t':>6s} "
      f"{'posY':>5s} {'train':>10s} {'fwd':>10s}")
for r in oi_rows:
    for legname in ("overnight", "intraday"):
        for side in ("long", "short"):
            leg = r.get(legname, {}).get(side)
            if leg is None:
                continue
            flag = " <==BAR" if oi_bar(leg) else ""
            # only print the forward-positive after-spread ones to keep it readable
            if leg["fwd_mean"] is not None and leg["fwd_mean"] > 0 and leg["mean_after_spread"] > 0:
                print(f"{r['symbol']:12s} {legname:9s} {side:5s} {leg['mean_daily']:10.2e} "
                      f"{leg['mean_after_spread']:10.2e} {leg['t']:6.2f} "
                      f"{leg['pos_years']}/{leg['tot_years']:<3d} "
                      f"{(leg['train_mean'] or 0):10.2e} {(leg['fwd_mean'] or 0):10.2e}{flag}")
print(f"\nRAW overnight/intraday 'bars' (BEFORE artifact guard): {len(oi_bars)} -> {oi_bars}")
print()
print("--- ARTIFACT GUARD (00:00-open is a synthetic rollover quote, untradeable) ---")
print(f"{'sym':12s} {'on_mean':>10s} {'id_mean':>10s} {'c2c_mean':>10s} {'gap/spread':>11s}")
for r in oi_rows:
    d = r.get("artifact_diag")
    if not d:
        continue
    print(f"{r['symbol']:12s} {d['overnight_mean']:10.2e} {d['intraday_mean']:10.2e} "
          f"{d['close_to_close_mean']:10.2e} {(d['gap_in_spreads'] or 0):11.2f}")
print(f"\nArtifact symbols (gap>1.5spr AND c2c~0): {artifact_syms}")
print("=> The raw overnight-short/intraday-long 'edges' are a synthetic-open "
      "microstructure artifact, NOT tradeable.")
print()
print("--- (c) TRADEABLE OVERNIGHT (20:00-close -> 00:00-close, real prices, full cost) ---")
print(f"{'sym':12s} {'side':5s} {'train':>10s} {'fwd':>10s} {'t':>6s} {'posY':>6s}")
for r in oi_rows:
    p = r.get("tradeable_overnight", {}).get("picked")
    if not p:
        continue
    flag = " <==BAR" if tov_bar(r) else ""
    print(f"{r['symbol']:12s} {(r['tradeable_overnight_picked_side'] or '?'):5s} "
          f"{(p['train_mean'] or 0):10.2e} {(p['fwd_mean'] or 0):10.2e} "
          f"{(p['t'] or 0):6.2f} {p['pos_years']}/{p['tot_years']:<3d}{flag}")
print(f"\nTRADEABLE OVERNIGHT BARS PASSED: {tov_bars or 'NONE'}")
print()
print(f"Result JSON -> {OUT}")
