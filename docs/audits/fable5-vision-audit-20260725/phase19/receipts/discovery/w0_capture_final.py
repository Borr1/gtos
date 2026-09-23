"""w0-capture, definitive pass: the fill contract, the horizon wall, and the
exit rule, each priced separately against the sealed January pool.

Fill rule used here is DIRECTIONAL, which is the permissive (anti-cherry-pick)
reading of a resting limit:
    LONG  buy-limit  fills at the first bar with  low  <= entry_price
    SHORT sell-limit fills at the first bar with  high >= entry_price
Rows the pool marks ``fill_realism_class == source_safe_immediate_marketable``
are filled at the decision instant regardless.

Arms scored with the declared contract (target = take_profit_1 = 2R, stop = -1R,
conservative same-bar resolution, mark-to-market at the horizon):

  R0  engine record                     -- opportunity_net_proxy_r + cost_r
  R1  fill_at_decision                  -- what step 1 measured (free instant fill)
  R2  directional_fill, unfilled = -1R  -- pessimistic
  R3  directional_fill, unfilled = 0R   -- the never-measured contract:
                                           "if it fills it fills, if not we do not trade"
Each at 120 min (the engine's wall) and at 24 h / 10 d (wall lifted).
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime as dt
import gzip
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[6]
LANE_ROOT = Path(
    "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence"
    "/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1"
)
M1_DIR = LANE_ROOT / "sources/bars/bridge_ftmo_m1_202601"
MANIFEST = LANE_ROOT / "manifests/january_2026.json"
POOL = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools"
    / "CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
)
HORIZONS = [120, 480, 1440, 14400]


def eus(w: dt.datetime) -> int:
    return int(w.timestamp() * 1_000_000)


def load_m1():
    man = json.loads(MANIFEST.read_text())
    want = {
        str(r.get("mapped_symbol") or r.get("symbol")): int(r.get("row_count") or 0)
        for r in (man.get("bar_sources") or [])
        if r.get("timeframe") == "M1" and r.get("source_family") == "bridge_ftmo_m1_202601"
    }
    out = {}
    for sym, rows in sorted(want.items()):
        t, o, h, l, c = [], [], [], [], []
        with (M1_DIR / f"{sym}_M1.csv").open("r", encoding="utf-8") as fh:
            rd = csv.reader(fh)
            next(rd)
            for r in rd:
                t.append(eus(dt.datetime.fromisoformat(r[0])))
                o.append(float(r[1])); h.append(float(r[2])); l.append(float(r[3])); c.append(float(r[4]))
        assert len(t) == rows
        out[sym] = (np.asarray(t, np.int64), np.asarray(o), np.asarray(h), np.asarray(l), np.asarray(c))
    return out


def bracket(hr, lr, cr, target, start):
    n = len(hr)
    if start >= n:
        return None, 0, np.nan, np.nan
    f = hr[start:]; a = lr[start:]
    rf = np.maximum.accumulate(f); ra = np.maximum.accumulate(-a)
    it = int(np.searchsorted(rf, target - 1e-9, side="left"))
    iss = int(np.searchsorted(ra, 1.0 - 1e-9, side="left"))
    m = len(f)
    it = it if it < m else -1
    iss = iss if iss < m else -1
    mfe = float(rf[-1]); mae = float(ra[-1])
    if it >= 0 and (iss < 0 or it < iss):
        return float(target), 1, mfe, mae
    if iss >= 0 and (it < 0 or iss < it):
        return -1.0, 2, mfe, mae
    if it >= 0 and iss >= 0 and it == iss:
        return -1.0, 4, mfe, mae
    return float(max(-1.0, min(cr[-1], target))), 3, mfe, mae


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path(__file__).with_name("W0_CAPTURE_FINAL_V1.json"))
    args = ap.parse_args()
    series = load_m1()
    pool = [json.loads(x) for x in gzip.open(POOL, "rt")]
    n = len(pool)

    rec = np.full(n, np.nan)
    cost = np.full(n, np.nan)
    fam = np.empty(n, dtype=object)
    imm = np.zeros(n, bool)
    filled = {h: np.zeros(n, bool) for h in HORIZONS}
    fillmin = np.full(n, np.nan)
    W = {h: np.full(n, np.nan) for h in HORIZONS}     # walk R given fill
    Wcode = {h: np.zeros(n, np.int8) for h in HORIZONS}
    Wdec = {h: np.full(n, np.nan) for h in HORIZONS}  # walk R, fill at decision
    MFE = {h: np.full(n, np.nan) for h in HORIZONS}
    MFEdec = {h: np.full(n, np.nan) for h in HORIZONS}

    for i, r in enumerate(pool):
        fam[i] = r.get("origin_family")
        imm[i] = str(r.get("fill_realism_class")) == "source_safe_immediate_marketable"
        if r.get("cost_r") is not None:
            cost[i] = float(r["cost_r"])
            if r.get("opportunity_net_proxy_r") is not None:
                rec[i] = float(r["opportunity_net_proxy_r"]) + float(r["cost_r"])
        t, o, h, l, c = series[r["symbol"]]
        entry = float(r["entry_price"]); stop = float(r["stop_loss"])
        side = str(r["side"]).upper()
        risk = abs(entry - stop)
        d = eus(dt.datetime.fromisoformat(r["decision_time_utc"]))
        s0 = int(np.searchsorted(t, d, side="right"))
        for hmin in HORIZONS:
            e = int(np.searchsorted(t, d + hmin * 60_000_000, side="right"))
            if s0 >= e or risk <= 0:
                continue
            hh = h[s0:e]; ll = l[s0:e]; cc = c[s0:e]
            if side == "LONG":
                hr = (hh - entry) / risk; lr = (ll - entry) / risk; cr = (cc - entry) / risk
                touch = np.nonzero(ll <= entry)[0]
            else:
                hr = (entry - ll) / risk; lr = (entry - hh) / risk; cr = (entry - cc) / risk
                touch = np.nonzero(hh >= entry)[0]
            v, code, mfe, _mae = bracket(hr, lr, cr, 2.0, 0)
            Wdec[hmin][i] = np.nan if v is None else v
            MFEdec[hmin][i] = mfe
            fi = 0 if imm[i] else (int(touch[0]) if len(touch) else -1)
            if fi >= 0:
                filled[hmin][i] = True
                if hmin == HORIZONS[0]:
                    fillmin[i] = (t[s0 + fi] - d) / 60_000_000
                v, code, mfe, _mae = bracket(hr, lr, cr, 2.0, fi)
                W[hmin][i] = np.nan if v is None else v
                Wcode[hmin][i] = code
                MFE[hmin][i] = mfe

    ok = np.isfinite(rec)
    N = int(ok.sum())

    def book(vals, mask, label):
        v = vals[mask]
        v = v[np.isfinite(v)]
        w = v[v > 0]; lo = v[v < 0]
        return {
            "label": label,
            "n": int(len(v)),
            "gross_mean_R": float(v.mean()) if len(v) else None,
            "win_rate": float((v > 0).mean()) if len(v) else None,
            "mean_winner_R": float(w.mean()) if len(w) else None,
            "mean_loser_R": float(lo.mean()) if len(lo) else None,
            "payoff": float(abs(w.mean() / lo.mean())) if len(w) and len(lo) else None,
        }

    res = {
        "schema": "gtos-w0-capture-final-v1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "billed": False,
        "broker_live_authority": False,
        "february_2026_economics_read": False,
        "april_may_packs_read": False,
        "pool_rows": n,
        "fill_rule": "directional limit touch; immediate-marketable rows fill at decision",
    }

    # ---------------- 1. the phantom-fill population
    f120 = filled[120]
    nf = ok & ~f120
    res["phantom_fill"] = {
        "n_unfilled_within_120m": int(nf.sum()),
        "share_of_pool": float(nf.sum() / N),
        "engine_recorded_gross_mean_R_on_unfilled": float(np.nanmean(rec[nf])),
        "engine_recorded_R_total_on_unfilled": float(np.nansum(rec[nf])),
        "engine_recorded_gross_mean_R_on_filled": float(np.nanmean(rec[ok & f120])),
        "pool_gross_mean_R_all": float(np.nanmean(rec[ok])),
        "pool_gross_mean_R_if_unfilled_scored_zero": float(np.nansum(rec[ok & f120]) / N),
        "recovery_R_per_pool_trade": float(
            np.nansum(rec[ok & f120]) / N - np.nanmean(rec[ok])
        ),
        "recorded_outcome_mix_on_unfilled": {
            "full_stop_share": float(np.mean(rec[nf] <= -0.98)),
            "target_share": float(np.mean(rec[nf] >= 1.98)),
            "sub_target_winner_share": float(np.mean((rec[nf] > 0.02) & (rec[nf] < 1.98))),
            "partial_loss_share": float(np.mean((rec[nf] < -0.02) & (rec[nf] > -0.98))),
        },
        "still_unfilled_at_8h": int((ok & ~filled[480]).sum()),
        "still_unfilled_at_24h": int((ok & ~filled[1440]).sum()),
        "still_unfilled_at_10d": int((ok & ~filled[14400]).sum()),
        "fill_delay_minutes_p50": float(np.nanpercentile(fillmin, 50)),
        "fill_delay_minutes_p90": float(np.nanpercentile(fillmin, 90)),
    }

    # ---------------- 2. books
    books = [book(rec, ok, "R0 engine record (all rows)")]
    for h in HORIZONS:
        books.append(book(Wdec[h], ok, f"R1 fill-at-decision bracket, {h}m horizon"))
    for h in HORIZONS:
        m = ok & filled[h]
        books.append(book(W[h], m, f"R2 directional-fill bracket, filled only, {h}m horizon"))
    # R3: unfilled scored 0
    for h in HORIZONS:
        v = np.where(filled[h], W[h], 0.0)
        v = np.where(ok, v, np.nan)
        books.append(book(v, ok, f"R3 directional-fill bracket, unfilled=0R, {h}m horizon"))
    res["books"] = books

    # ---------------- 3. cost-charged view (frozen cost model, charged only when filled)
    def net_book(vals, mask, charge_mask, label):
        v = np.where(charge_mask, vals - cost, vals)
        v = v[mask]
        v = v[np.isfinite(v)]
        return {"label": label, "n": int(len(v)), "net_mean_R": float(v.mean()) if len(v) else None}

    res["net_books_frozen_cost"] = [
        net_book(rec, ok, np.ones(n, bool), "R0 engine record - frozen cost on every row"),
        net_book(
            np.where(filled[120], W[120], 0.0), ok, filled[120],
            "R3 unfilled=0R, frozen cost charged only on filled rows, 120m",
        ),
        net_book(
            np.where(filled[1440], W[1440], 0.0), ok, filled[1440],
            "R3 unfilled=0R, frozen cost charged only on filled rows, 24h",
        ),
    ]

    # ---------------- 4. per family under R3 @120m and @24h
    famrows = []
    for f in sorted({str(x) for x in fam}):
        m = ok & (fam == f)
        if not m.sum():
            continue
        v120 = np.where(filled[120], W[120], 0.0)
        v1440 = np.where(filled[1440], W[1440], 0.0)
        famrows.append(
            {
                "family": f,
                "n": int(m.sum()),
                "unfilled_share_120m": float(np.mean(~filled[120][m])),
                "recorded_gross_mean_R": float(np.nanmean(rec[m])),
                "R3_gross_mean_R_120m": float(np.nanmean(v120[m])),
                "R3_gross_mean_R_24h": float(np.nanmean(v1440[m])),
                "delta_R3_120m_minus_recorded": float(np.nanmean(v120[m]) - np.nanmean(rec[m])),
                "filled_only_gross_mean_R_120m": float(np.nanmean(W[120][m & filled[120]])),
                "mean_cost_R": float(np.nanmean(cost[m])),
                "R3_net_frozen_120m": float(
                    np.nanmean(np.where(filled[120][m], v120[m] - cost[m], v120[m]))
                ),
            }
        )
    famrows.sort(key=lambda r: -r["delta_R3_120m_minus_recorded"] * r["n"])
    res["per_family_R3"] = famrows

    # ---------------- 5. the mission's two forensic questions, on the FILLED population
    m = ok & filled[120]
    v = W[120]
    tgt = 2.0
    sub = m & (v > 0.02) & (v < tgt - 0.02)      # sub-target winners under the honest walk
    subrec = m & (rec > 0.02) & (rec < tgt - 0.02)  # sub-target winners as RECORDED
    stp = m & (rec <= -0.98)

    def fr(a, b):
        d = int(b.sum())
        return [int(a.sum()), d, float(a.sum() / d) if d else None]

    reach = {h: (MFE[h] >= tgt - 1e-9) for h in HORIZONS}
    res["sub_target_winner_forensics_recorded_basis"] = {
        "n": int(subrec.sum()),
        "recorded_gross_mean_R": float(np.nanmean(rec[subrec])),
        "mfe_mean_R_120m": float(np.nanmean(MFE[120][subrec])),
        "reached_2R_within_120m": fr(subrec & reach[120], subrec),
        "reached_2R_by_8h": fr(subrec & reach[480], subrec),
        "reached_2R_by_24h": fr(subrec & reach[1440], subrec),
        "reached_2R_by_10d": fr(subrec & reach[14400], subrec),
        "never_reached_2R_by_10d": fr(subrec & ~reach[14400], subrec),
        "honest_walk_gross_mean_R_120m": float(np.nanmean(W[120][subrec])),
        "honest_walk_gross_mean_R_24h": float(np.nanmean(W[1440][subrec])),
    }
    res["full_stop_forensics_recorded_basis"] = {
        "n": int(stp.sum()),
        "honest_walk_says_target_first_120m": fr(stp & (Wcode[120] == 1), stp),
        "honest_walk_says_stop_first_120m": fr(stp & (Wcode[120] == 2), stp),
        "honest_walk_says_same_bar_120m": fr(stp & (Wcode[120] == 4), stp),
        "honest_walk_says_mark_120m": fr(stp & (Wcode[120] == 3), stp),
        "mfe_ge_1R_within_120m": fr(stp & (MFE[120] >= 1.0), stp),
        "mfe_ge_2R_within_120m": fr(stp & (MFE[120] >= 2.0), stp),
        "R_gap_honest_minus_recorded_total": float(np.nansum(W[120][stp] - rec[stp])),
        "R_gap_per_pool_trade": float(np.nansum(W[120][stp] - rec[stp]) / N),
    }

    # ---------------- 6. exit-class census under the honest walk
    codes = {1: "target_2R", 2: "stop_1R", 3: "mark_at_horizon", 4: "same_bar_conservative_stop"}
    cen = {}
    for h in HORIZONS:
        mm = ok & filled[h]
        cc = collections.Counter(Wcode[h][mm].tolist())
        cen[str(h)] = {codes.get(k, str(k)): float(v2 / mm.sum()) for k, v2 in sorted(cc.items())}
        cen[str(h)]["n_filled"] = int(mm.sum())
    res["exit_class_census_honest_walk"] = cen

    # ---------------- 7. headline decomposition
    v120 = np.where(filled[120], W[120], 0.0)
    v1440 = np.where(filled[1440], W[1440], 0.0)
    base = float(np.nanmean(rec[ok]))
    res["decomposition_R_per_pool_trade"] = {
        "engine_recorded_gross": base,
        "step1_phantom_fill_removal": float(np.nansum(rec[ok & f120]) / N) - base,
        "step2_honest_walk_on_filled_rows_120m": float(np.nanmean(v120[ok])) - float(np.nansum(rec[ok & f120]) / N),
        "step3_horizon_120m_to_24h": float(np.nanmean(v1440[ok])) - float(np.nanmean(v120[ok])),
        "total_honest_24h_gross": float(np.nanmean(v1440[ok])),
        "total_swing_vs_recorded": float(np.nanmean(v1440[ok])) - base,
    }

    args.out.write_text(json.dumps(res, indent=1, sort_keys=True))
    print(json.dumps(res["phantom_fill"], indent=1))
    print("\nBOOKS")
    for b in res["books"]:
        print(
            f"  {b['label']:<58} n={b['n']:>6} gross={(b['gross_mean_R'] or 0):+.4f} "
            f"win={(b['win_rate'] or 0):.3f} winMean={(b['mean_winner_R'] or 0):+.3f} "
            f"losMean={(b['mean_loser_R'] or 0):+.3f} payoff={(b['payoff'] or 0):.2f}"
        )
    print("\nNET (frozen cost)")
    for b in res["net_books_frozen_cost"]:
        print(f"  {b['label']:<62} n={b['n']:>6} net={b['net_mean_R']:+.4f}")
    print("\nPER FAMILY (R3)")
    for r in famrows:
        print(
            f"  {r['family']:<32} n={r['n']:>5} unfill={r['unfilled_share_120m']:.3f} "
            f"rec={r['recorded_gross_mean_R']:+.4f} R3_120={r['R3_gross_mean_R_120m']:+.4f} "
            f"R3_24h={r['R3_gross_mean_R_24h']:+.4f} d={r['delta_R3_120m_minus_recorded']:+.4f} "
            f"filledOnly={r['filled_only_gross_mean_R_120m']:+.4f} netFroz={r['R3_net_frozen_120m']:+.4f}"
        )
    print("\nEXIT CENSUS")
    print(json.dumps(res["exit_class_census_honest_walk"], indent=1))
    print("\nSUB-TARGET")
    print(json.dumps(res["sub_target_winner_forensics_recorded_basis"], indent=1))
    print("\nFULL STOPS")
    print(json.dumps(res["full_stop_forensics_recorded_basis"], indent=1))
    print("\nDECOMPOSITION")
    print(json.dumps(res["decomposition_R_per_pool_trade"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
