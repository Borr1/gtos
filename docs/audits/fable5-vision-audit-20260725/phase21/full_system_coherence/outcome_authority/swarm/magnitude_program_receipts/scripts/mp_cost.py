"""MAGNITUDE PROGRAM — vectorised broker-true cost layer, validated against the authority.

The authority is `src.costs.model.cost_r` (2.0 ms/call). This study prices ~14 M
(event x exit contract) rows, so the four terms are decomposed and vectorised:

    cost_R = (spread_price + commission_price + nights * swap_price_per_night) / sl
             + slippage_r                       # fixed R, does NOT rescale with the stop

Every component is taken from the same artifacts the authority reads
(`BROKER_TRUE_COSTS_V1_1.json`, `SPREAD_MODEL_V1.json`); `spread_price` and the broker
clock come from the authority's own functions. `validate()` re-prices a random sample of
real rows through `cost_r` and reports the max absolute deviation.

Decisions taken explicitly (per the cost artifact's own guidance):
  * `spread_band="mid"` — the era model, not the 2026 tick snapshot. Charging 2026
    spreads to 2014 bars understates FX by up to 5.7x in this window.
  * V1_1 — corrects the two false `zero` FTMO oil commissions to $5.00/lot.
  * Favourable swap is floored to zero (the authority's rule): a carry credit is never
    booked as income here.
"""
import functools, json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path("/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725")
COSTS_V11 = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"

# archive symbol -> cost-model canon symbol
SYMMAP = {"GER40_cash": "GER40", "JP225_cash": "JP225", "UK100_cash": "UK100",
          "US100_cash": "NAS100", "US500_cash": "SPX500"}
BAR_HOURS = {"D1": 24.0, "H4": 4.0}


def canon(sym):
    return SYMMAP.get(sym, sym)


@functools.lru_cache(maxsize=1)
def _truth():
    return json.loads(COSTS_V11.read_text())


@functools.lru_cache(maxsize=1)
def _truth_obj():
    from src.costs.model import load_broker_true_costs
    return load_broker_true_costs(COSTS_V11)


@functools.lru_cache(maxsize=256)
def _rec(account, canon_symbol):
    """The instrument record, resolved through the authority's own canon->broker map."""
    name, rec = _truth_obj().resolve_instrument(account, canon_symbol)
    return name, rec


@functools.lru_cache(maxsize=4)
def _rule(server="FTMO-Server3"):
    from src.utils.broker_clock import resolve_rule
    return resolve_rule(server)


@functools.lru_cache(maxsize=400_000)
def _spread_cached(symbol, account, y, q, broker_how):
    """Spread in price units.

    The model is `anchor x era_ratio[quarter] x intraweek_mult[broker-wall hour-of-week]`,
    so (era quarter, broker-wall hour-of-week) determines the estimate exactly. The
    representative instant is built in BROKER WALL time and converted back to UTC, which
    is what the model's own `hour_of_week_brokerwall` term reads.
    """
    from src.costs.spread_model import spread_price
    from src.utils.broker_clock import broker_naive_to_utc
    bw = datetime(y, 3 * (q - 1) + 2, 15) + timedelta(hours=int(broker_how) % 24)
    bw = bw + timedelta(days=(int(broker_how) // 24 - bw.weekday()) % 7)
    try:
        at = broker_naive_to_utc(bw, _rule())
        est = spread_price(symbol, account, at, band="mid")
        return float(est.spread_price), f"{est.coverage}|{est.era_class}|dec={est.decidable}", True
    except Exception as exc:                     # noqa: BLE001 — recorded, never silently zeroed
        return float("nan"), f"REFUSED:{type(exc).__name__}", False


@functools.lru_cache(maxsize=400_000)
def _fx_upu(profit_currency, contract_size, broker_date_iso, server):
    """USD per price unit per lot at a historical date — the authority's own conversion.

    `cost_r` refuses a cash-per-lot commission in a non-USD profit currency without this
    (`model.py:1200-1222`): the 2026 spec snapshot is not a historical default.
    """
    from src.costs.fx_conversion import load_historical_fx
    fx = load_historical_fx()
    r = fx.rate_at(profit_currency, datetime.fromisoformat(broker_date_iso).replace(
        tzinfo=timezone.utc), server=server)
    return float(contract_size) / r.profit_currency_per_usd, r.coverage.value


@functools.lru_cache(maxsize=256)
def _slip(account, broker_symbol, rec_slip_value_r):
    """Entry slippage.

    Returns (price_units, fixed_R, coverage). The authority's price-domain model
    (`SLIPPAGE_PRICE_V1.json`) covers 15 of these 24 symbols on FTMO; where it refuses
    (NOT_EVALUABLE) the fallback is the cost artifact's own pooled TRANSFERRED `value_r`,
    charged as a FIXED R that does not dilute when the stop is widened — the
    conservative direction for a study whose main lever is a wider stop.
    """
    from src.costs.slippage_model import load_slippage_model, SlippageModelError
    try:
        e = load_slippage_model().estimate(account, broker_symbol)
        return float(e.expected_adverse_price), 0.0, f"PRICE:{e.coverage}:n={e.n}"
    except SlippageModelError:
        return 0.0, float(rec_slip_value_r), "POOLED_R:TRANSFERRED"


def commission_price(rec, entry_px, upu=None):
    """Round-turn commission in PRICE units (vectorised over entry_px)."""
    c = rec["commission"]
    kind = c.get("kind")
    spec = rec.get("spec") or {}
    if upu is None:
        upu = float(spec["trade_tick_value"]) / float(spec["trade_tick_size"])
    if kind == "zero":
        return np.zeros_like(entry_px), "zero"
    if kind == "per_lot":
        return float(c["value"]) / np.asarray(upu, dtype=float) * np.ones_like(entry_px), \
            c.get("coverage", "")
    if kind == "notional_bp":
        # value/1e4 * contract_size * price  (USD) -> / upu (USD per price unit per lot).
        # Numerator and denominator carry the same profit-currency conversion, which
        # cancels exactly in R (model.py:1230-1244) -> the snapshot upu is correct here.
        cs = float(spec["trade_contract_size"])
        snap = float(spec["trade_tick_value"]) / float(spec["trade_tick_size"])
        return (float(c["value"]) / 1e4 * cs * entry_px) / snap, c.get("coverage", "")
    raise ValueError(f"commission kind {kind!r} is UNKNOWN, not zero")


def swap_night_price(rec, side, entry_px):
    """Adverse swap for ONE charged night, in price units. Favourable -> 0.0."""
    spec = rec.get("spec") or {}
    raw = spec.get("swap_long" if side == "LONG" else "swap_short")
    mode = int(spec.get("swap_mode"))
    if raw is None or float(raw) >= 0:
        return np.zeros_like(entry_px)
    adverse = abs(float(raw))
    if mode == 1:
        return np.full_like(entry_px, adverse * float(spec["point"]))
    if mode in (5, 6):
        return entry_px * (adverse / 100.0) / 360.0
    raise ValueError(f"swap_mode {mode} needs post-sizing volume conversion")


# ---- exact, vectorised rollover-night counting ------------------------------------------
_CAL_START = datetime(2013, 1, 1)


@functools.lru_cache(maxsize=64)
def _night_cum(rollover_weekday):
    """Cumulative charged-night weight by calendar date ordinal, broker wall clock.

    weight(d) = 0 on Sat/Sun, 3 on the triple-swap weekday, else 1  (MT5 dow: Sun=0).
    """
    days = pd.date_range(_CAL_START, "2028-12-31", freq="D")
    dow = (days.weekday.to_numpy() + 1) % 7            # MT5 numbering
    w = np.where((dow == 0) | (dow == 6), 0.0,
                 np.where(dow == int(rollover_weekday), 3.0, 1.0))
    return days, np.cumsum(w)


def rollover_nights_vec(entry_utc_ns, holding_hours, rollover_weekday, rule=None):
    """Charged nights over each hold. Broker wall clock = NY + 7h (US DST calendar)."""
    from src.utils.broker_clock import offset_seconds_at_utc
    rule = rule or _rule()
    t = pd.DatetimeIndex(pd.to_datetime(entry_utc_ns, utc=True))
    t_end = t + pd.to_timedelta(np.asarray(holding_hours, dtype=float), unit="h")

    def _bw(ix):
        # offset changes only at DST boundaries; resolve per unique day, then map
        off = {d: offset_seconds_at_utc(d.to_pydatetime(), rule) for d in ix.normalize().unique()}
        o = pd.Series(ix.normalize()).map(off).to_numpy(float)
        return ix.tz_localize(None) + pd.to_timedelta(o, unit="s")

    start, end = _bw(t), _bw(pd.DatetimeIndex(t_end))
    days, cum = _night_cum(rollover_weekday)
    i0 = np.searchsorted(days.values, pd.DatetimeIndex(start).normalize().values)
    i1 = np.searchsorted(days.values, pd.DatetimeIndex(end).normalize().values)
    return cum[np.clip(i1, 0, len(cum) - 1)] - cum[np.clip(i0, 0, len(cum) - 1)]


def event_cost_inputs(events, account="FTMO"):
    """Per-event, contract-independent cost inputs. Adds columns in place-safe copy."""
    from src.utils.broker_clock import offset_seconds_at_utc
    ev = events.copy().reset_index(drop=True)
    t = pd.DatetimeIndex(pd.to_datetime(ev["entry_time"], utc=True))
    off = {d: offset_seconds_at_utc(d.to_pydatetime(), _rule()) for d in t.normalize().unique()}
    o = pd.Series(t.normalize()).map(off).to_numpy(float)
    bw = pd.DatetimeIndex(t.tz_localize(None) + pd.to_timedelta(o, unit="s"))
    ev["_y"] = bw.year.to_numpy()
    ev["_q"] = bw.quarter.to_numpy()
    ev["_how"] = (bw.weekday.to_numpy() * 24 + bw.hour.to_numpy())
    ev["broker_hour"] = bw.hour.to_numpy().astype("int8")
    sp, cov, dec = [], [], []
    for sym, y, q, how in zip(ev["symbol"].map(canon), ev["_y"], ev["_q"], ev["_how"]):
        a, b, c = _spread_cached(sym, account, int(y), int(q), int(how))
        sp.append(a); cov.append(b); dec.append(c)
    ev["spread_price"] = sp
    ev["spread_cov"] = cov
    ev["spread_ok"] = dec
    comm = np.full(len(ev), np.nan)
    swapn = np.full(len(ev), np.nan)
    slip = np.full(len(ev), np.nan)
    rollw = np.full(len(ev), np.nan)
    slipr = np.full(len(ev), np.nan)
    slipcov = np.array(["" ] * len(ev), dtype=object)
    server = _truth()["accounts"][account]["server"]
    bdate = pd.Series(bw.normalize().strftime("%Y-%m-%d"), index=ev.index)
    for sym, g in ev.groupby("symbol", observed=True):
        bname, rec = _rec(account, canon(sym))
        spec = rec.get("spec") or {}
        px = g["entry_px"].to_numpy(float)
        pc = str(spec.get("currency_profit") or "")
        upu = None
        if pc and pc != "USD" and rec["commission"].get("kind") == "per_lot":
            upu = np.array([_fx_upu(pc, float(spec["trade_contract_size"]), d, server)[0]
                            for d in bdate.loc[g.index]], dtype=float)
        cp, _ = commission_price(rec, px, upu=upu)
        comm[g.index] = cp
        for side, gg in g.groupby("side", observed=True):
            swapn[gg.index] = swap_night_price(rec, side, gg["entry_px"].to_numpy(float))
        sp_, sr_, scov_ = _slip(account, bname,
                                float((rec.get("slippage") or {}).get("value_r", 0.0132)))
        slip[g.index] = sp_
        slipr[g.index] = sr_
        slipcov[g.index] = scov_
        rollw[g.index] = float((rec.get("swap") or {}).get("swap_rollover3days_weekday",
                               (rec.get("spec") or {}).get("swap_rollover3days", 3)))
    ev["comm_price"] = comm
    ev["swap_night_price"] = swapn
    ev["slip_price"] = slip
    ev["slip_fixed_r"] = slipr
    ev["slip_cov"] = slipcov
    ev["rollover_wd"] = rollw
    return ev.drop(columns=["_y", "_q", "_how"])


def validate(events, n=1500, account="FTMO", seed=20260812):
    """Re-price a random sample through the authority. Returns (max_abs_dev, table)."""
    from src.costs.model import cost_r, load_broker_true_costs
    truth = load_broker_true_costs(COSTS_V11)
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(events), size=min(n, len(events)), replace=False)
    rows = []
    for i in idx:
        e = events.iloc[int(i)]
        if not e["spread_ok"] or not np.isfinite(e["spread_price"]):
            continue
        hold_h = float(rng.choice([24.0, 120.0, 480.0, 1920.0]))
        sl = float(e["atr14"]) * float(rng.choice([1.0, 1.5, 2.0]))
        ts = pd.Timestamp(e["entry_time"]).to_pydatetime()
        try:
            b = cost_r(canon(e["symbol"]), account, hold_h, sl_distance_price=sl,
                       entry_price=float(e["entry_px"]), side=e["side"], entry_utc=ts,
                       spread_band="mid", costs=truth)
        except Exception as exc:                              # noqa: BLE001
            rows.append({"sym": e["symbol"], "err": type(exc).__name__}); continue
        nights = rollover_nights_vec(np.array([e["entry_time"]]), np.array([hold_h]),
                                     int(e["rollover_wd"]))[0]
        mine = ((float(e["spread_price"]) + float(e["comm_price"]) + float(e["slip_price"])
                 + nights * float(e["swap_night_price"])) / sl + float(e["slip_fixed_r"]))
        rows.append({"sym": e["symbol"], "side": e["side"], "hold_h": hold_h, "sl": sl,
                     "authority": float(b.total_r.value), "vectorised": mine,
                     "dev": abs(float(b.total_r.value) - mine),
                     "auth_swap": float(b.swap_r.value), "my_swap": nights * float(e["swap_night_price"]) / sl,
                     "auth_spread": float(b.spread_r.value), "my_spread": float(e["spread_price"]) / sl,
                     "auth_comm": float(b.commission_r.value), "my_comm": float(e["comm_price"]) / sl,
                     "auth_slip": float(b.slippage_r.value),
                     "my_slip": float(e["slip_price"]) / sl + float(e["slip_fixed_r"])})
    tab = pd.DataFrame(rows)
    dev = tab["dev"].dropna() if "dev" in tab else pd.Series(dtype=float)
    return (float(dev.max()) if len(dev) else float("nan")), tab
