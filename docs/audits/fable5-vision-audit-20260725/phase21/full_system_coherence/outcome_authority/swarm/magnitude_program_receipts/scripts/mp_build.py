"""MAGNITUDE PROGRAM — Task 1 kill test, stage 1: build breakout events + first-touch outcomes.

Source (unmutated, read-only):
  /Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/
    cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/deep_universe_h4d1_2014_2026
  24 symbols, H4 + D1, 2014-01 -> 2026-06, time_column_basis "true_utc".

Construction rules (all pre-decision; no lookahead):
  * Channel at bar t uses highs/lows of bars [t-N, t-1] ONLY.
  * ATR14/ATR50 at bar t use bars <= t.
  * Trigger fires on the CLOSE of bar t.
  * Entry is the OPEN of bar t+1 (executable; never the trigger bar's own close).
  * Barriers are measured from the entry price, over bars t+1 .. t+H.
  * A bar that spans both barriers is scored STOP (pessimistic; Lane I's rule).
  * Gap-through on the stop is filled at that bar's OPEN when the open is already
    beyond the stop -> realised loss worse than -1R. Recorded separately.

Outputs (float32 parquet, /tmp/mag_program/out):
  events_{grid}.parquet   one row per trigger
  out_{grid}.parquet      one row per (trigger x exit contract)
"""
import json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

SRC = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/"
           "cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/deep_universe_h4d1_2014_2026")
OUT = Path("/tmp/mag_program/out")
SEED = 20260812

# --- the scan grid (Task 1 is a MAP, declared as a scan; Task 2's family is declared from
#     structure, not from this scan's winner) -------------------------------------------------
CHANNELS = (10, 20, 40, 55)
STOPS = (1.0, 1.5, 2.0)          # stop distance in ATR14 units
TARGETS = (1.0, 2.0, 3.0, 5.0)   # target distance in R (= multiples of the stop)
HORIZ = {"D1": (5, 20, 80), "H4": (30, 120, 480)}   # equal wall clock: 5d / 20d / 80d


def atr(h, l, c, n):
    pc = np.r_[np.nan, c[:-1]]
    tr = np.nanmax(np.c_[h - l, np.abs(h - pc), np.abs(l - pc)], axis=1)
    return pd.Series(tr).rolling(n, min_periods=n).mean().to_numpy()


def roll(x, n, fn):
    return getattr(pd.Series(x).rolling(n, min_periods=n), fn)().to_numpy()


def load(symbol, grid):
    d = pd.read_csv(SRC / f"{symbol}_{grid}.csv")
    t = pd.to_datetime(d["time"], utc=True, format="ISO8601")
    o, h, l, c = (d[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    return t, o, h, l, c


def build_symbol(symbol, grid):
    t, o, h, l, c = load(symbol, grid)
    n = len(c)
    a14, a50 = atr(h, l, c, 14), atr(h, l, c, 50)
    vol_regime = a14 / a50
    hour = t.dt.hour.to_numpy()
    year = t.dt.year.to_numpy()
    ev = []
    for N in CHANNELS:
        # prior-N extreme, strictly bars [t-N, t-1]
        pri_hi = np.r_[[np.nan], roll(h, N, "max")[:-1]]
        pri_lo = np.r_[[np.nan], roll(l, N, "min")[:-1]]
        up = c > pri_hi
        dn = c < pri_lo
        for side, sig in (("LONG", up), ("SHORT", dn)):
            idx = np.flatnonzero(sig)
            idx = idx[(idx + 1) < n]                       # need an entry bar
            ok = np.isfinite(a14[idx]) & (a14[idx] > 0) & np.isfinite(a50[idx])
            idx = idx[ok]
            if len(idx) == 0:
                continue
            ev.append(pd.DataFrame({
                "symbol": symbol, "grid": grid, "channel": np.int16(N), "side": side,
                "trig_i": idx.astype(np.int32), "entry_i": (idx + 1).astype(np.int32),
                "trig_time": t.to_numpy()[idx], "entry_time": t.to_numpy()[idx + 1],
                "entry_px": o[idx + 1].astype(np.float64),
                "trig_close": c[idx].astype(np.float64),
                "atr14": a14[idx].astype(np.float64),
                "vol_regime": vol_regime[idx].astype(np.float64),
                "entry_hour": hour[idx + 1].astype(np.int8),
                "year": year[idx].astype(np.int16),
                # break extension: how far the trigger close is beyond the channel, in ATR
                "break_ext_atr": ((c[idx] - pri_hi[idx]) / a14[idx] if side == "LONG"
                                  else (pri_lo[idx] - c[idx]) / a14[idx]),
                # entry gap: entry open vs trigger close, in ATR, signed in trade direction
                "entry_gap_atr": ((o[idx + 1] - c[idx]) / a14[idx] if side == "LONG"
                                  else (c[idx] - o[idx + 1]) / a14[idx]),
            }))
    if not ev:
        return None, None, None
    events = pd.concat(ev, ignore_index=True)
    return events, (o, h, l, c, t), n


def first_touch_block(o, h, l, c, entry_i, entry_px, atr14, side, s, k, H):
    """Vectorised first-touch for one exit contract over a set of entry indices.

    Returns (r_clean, r_gaphonest, label, mfe_atr, mae_atr, bars_held)
      label 0=stop 1=target 2=timeout
      r is in R units where 1R = s*atr14 of price.
    """
    n = len(c)
    m = len(entry_i)
    pad = np.full(H, np.nan)
    HW = sliding_window_view(np.r_[h, pad], H)          # window starting AT index i
    LW = sliding_window_view(np.r_[l, pad], H)
    OW = sliding_window_view(np.r_[o, pad], H)
    hi = HW[entry_i]                                    # bars entry_i .. entry_i+H-1
    lo = LW[entry_i]
    op = OW[entry_i]
    risk = s * atr14
    if side == "LONG":
        stop_px = entry_px - risk
        tgt_px = entry_px + k * risk
        hit_s = lo <= stop_px[:, None]
        hit_t = hi >= tgt_px[:, None]
        mfe = (np.nanmax(hi, axis=1) - entry_px) / atr14
        mae = (entry_px - np.nanmin(lo, axis=1)) / atr14
    else:
        stop_px = entry_px + risk
        tgt_px = entry_px - k * risk
        hit_s = hi >= stop_px[:, None]
        hit_t = lo <= tgt_px[:, None]
        mfe = (entry_px - np.nanmin(lo, axis=1)) / atr14
        mae = (np.nanmax(hi, axis=1) - entry_px) / atr14
    BIG = H + 1
    i_s = np.where(hit_s.any(1), hit_s.argmax(1), BIG)
    i_t = np.where(hit_t.any(1), hit_t.argmax(1), BIG)
    none = (i_s == BIG) & (i_t == BIG)
    # timeout mark-out at the close of the last bar in the window
    last_i = np.minimum(entry_i + H - 1, n - 1)
    cl = c[last_i]
    drift = ((cl - entry_px) if side == "LONG" else (entry_px - cl)) / risk
    stopped = (i_s <= i_t) & ~none
    targeted = (i_t < i_s) & ~none
    r = np.where(stopped, -1.0, np.where(targeted, k, drift))
    # gap-honest stop fill: if the stop bar's OPEN is already beyond the stop, fill at the open
    r_gap = r.copy()
    si = np.where(stopped, i_s, 0)
    stop_open = op[np.arange(m), si]
    if side == "LONG":
        worse = stopped & np.isfinite(stop_open) & (stop_open < stop_px)
        r_gap = np.where(worse, (stop_open - entry_px) / risk, r_gap)
    else:
        worse = stopped & np.isfinite(stop_open) & (stop_open > stop_px)
        r_gap = np.where(worse, (entry_px - stop_open) / risk, r_gap)
    label = np.where(none, 2, np.where(stopped, 0, 1)).astype(np.int8)
    bars = np.where(none, H, np.where(stopped, i_s + 1, i_t + 1)).astype(np.int16)
    # AMBIGUOUS: one bar reaches both barriers -- the intrabar ordering is unknowable at
    # this resolution. Scored STOP above (pessimistic). Flagged so the result can be
    # bounded under the optimistic and the exclude rules instead of assumed.
    tie = ((i_s == i_t) & ~none).astype(np.int8)
    bad = ~np.isfinite(r) | ~np.isfinite(atr14) | (atr14 <= 0)
    r[bad] = np.nan
    r_gap[bad] = np.nan
    return r, r_gap, label, mfe, mae, bars, tie


def main():
    rng = np.random.default_rng(SEED)
    grid = sys.argv[1]
    syms = sorted({p.name.rsplit("_", 1)[0] for p in SRC.glob(f"*_{grid}.csv")})
    t0 = time.time()
    all_ev, all_out = [], []
    for sym in syms:
        events, arrays, n = build_symbol(sym, grid)
        if events is None:
            continue
        o, h, l, c, tt = arrays
        # ---- matched blind-entry control: same count, same symbol, drawn from the same
        #      bar population (bars with valid atr14 and room for the longest horizon).
        valid = np.flatnonzero(np.isfinite(events["atr14"].to_numpy()))
        ctl_pool = np.flatnonzero(np.isfinite(atr(h, l, c, 14)) & np.isfinite(atr(h, l, c, 50)))
        ctl_pool = ctl_pool[(ctl_pool + 1) < n]
        a14full = atr(h, l, c, 14)
        a50full = atr(h, l, c, 50)
        blocks = []
        for (ch, side), g in events.groupby(["channel", "side"], observed=True):
            pick = rng.choice(ctl_pool, size=len(g), replace=True)
            blocks.append(pd.DataFrame({
                "symbol": sym, "grid": grid, "channel": np.int16(ch), "side": side,
                "trig_i": pick.astype(np.int32), "entry_i": (pick + 1).astype(np.int32),
                "trig_time": tt.to_numpy()[pick], "entry_time": tt.to_numpy()[pick + 1],
                "entry_px": o[pick + 1], "trig_close": c[pick],
                "atr14": a14full[pick], "vol_regime": (a14full / a50full)[pick],
                "entry_hour": tt.dt.hour.to_numpy()[pick + 1].astype(np.int8),
                "year": tt.dt.year.to_numpy()[pick].astype(np.int16),
                "break_ext_atr": np.nan, "entry_gap_atr": (o[pick + 1] - c[pick]) / a14full[pick],
            }))
        ctl = pd.concat(blocks, ignore_index=True)
        ctl["arm"] = "BLIND"
        events["arm"] = "BREAKOUT"
        both = pd.concat([events, ctl], ignore_index=True)
        both = both[np.isfinite(both["atr14"]) & (both["atr14"] > 0)].reset_index(drop=True)
        both["event_id"] = np.arange(len(both), dtype=np.int32)

        rows = []
        for side in ("LONG", "SHORT"):
            sel = both["side"].to_numpy() == side
            if not sel.any():
                continue
            ei = both.loc[sel, "entry_i"].to_numpy()
            ep = both.loc[sel, "entry_px"].to_numpy()
            aa = both.loc[sel, "atr14"].to_numpy()
            eid = both.loc[sel, "event_id"].to_numpy()
            for H in HORIZ[grid]:
                for s in STOPS:
                    for k in TARGETS:
                        r, rg, lab, mfe, mae, bars, tie = first_touch_block(
                            o, h, l, c, ei, ep, aa, side, s, k, H)
                        rows.append(pd.DataFrame({
                            "event_id": eid, "H": np.int16(H), "s": np.float32(s),
                            "k": np.float32(k), "r": r.astype(np.float32),
                            "r_gap": rg.astype(np.float32), "label": lab,
                            "mfe_atr": mfe.astype(np.float32), "mae_atr": mae.astype(np.float32),
                            "bars_held": bars, "tie": tie,
                        }))
        outs = pd.concat(rows, ignore_index=True)
        both["symbol"] = both["symbol"].astype(str)
        all_ev.append(both)
        outs["symbol"] = sym
        all_out.append(outs)
        print(json.dumps({"sym": sym, "grid": grid, "events": int(len(both)),
                          "rows": int(len(outs)), "t": round(time.time() - t0, 1)}), flush=True)

    ev = pd.concat(all_ev, ignore_index=True)
    ev["uid"] = ev["symbol"].astype(str) + "|" + ev["event_id"].astype(str)
    out = pd.concat(all_out, ignore_index=True)
    out["uid"] = out["symbol"].astype(str) + "|" + out["event_id"].astype(str)
    ev.to_parquet(OUT / f"events_{grid}.parquet")
    out.drop(columns=["event_id", "symbol"]).to_parquet(OUT / f"out_{grid}.parquet")
    print(json.dumps({"grid": grid, "symbols": int(ev.symbol.nunique()),
                      "events": int(len(ev)), "breakout_events": int((ev.arm == "BREAKOUT").sum()),
                      "outcome_rows": int(len(out)),
                      "first": str(ev.entry_time.min()), "last": str(ev.entry_time.max()),
                      "t": round(time.time() - t0, 1)}, indent=1))


if __name__ == "__main__":
    main()
