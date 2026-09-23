"""w0-capture: what closes a winning trade at +1.04 R when its target is 2R?

Offline research tool.  Reads only:
  * CJ's re-clocked January S0R0 diagnostic pool (27,658 rows, true UTC)
  * CQ's ordered-path sidecar (the engine's own 120-minute M1_CONSERVATIVE path)
  * the January M1 bar sources the sidecar was built from (content-hash verified)

It never imports a broker module, never writes into a sealed route, and never
reads April/May packs.

Three questions, in order:
  1. RECONCILE  -- does a pure geometry walker (target / stop / mark-at-horizon)
     reproduce the sealed ``opportunity_net_proxy_r``?  Rows where it does NOT
     are rows an exit POLICY moved -> that is hypothesis (B), measured directly.
  2. HORIZON    -- re-walk the same candidates against the SAME geometry with the
     120-minute wall lifted to 4h / 8h / 24h / 3d / 5d / 10d.  That is (A).
  3. LEAKAGE    -- MFE/MAE forensics: money that was on the table before the exit.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

LANE_ROOT = Path(
    "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence"
    "/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1"
)
REPO = Path(__file__).resolve().parents[6]
POOL = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools"
    / "CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz"
)
SIDECAR = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools"
    / "CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz"
)
M1_DIR = LANE_ROOT / "sources/bars/bridge_ftmo_m1_202601"
MANIFEST = LANE_ROOT / "manifests/january_2026.json"

TOL = 1e-9
INF = np.int64(1 << 62)
HORIZONS_MIN = [120, 240, 480, 720, 1440, 2880, 4320, 7200, 14400]
MAX_HORIZON_MIN = max(HORIZONS_MIN)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_utc(text: str) -> dt.datetime:
    return dt.datetime.fromisoformat(text)


def epoch_us(when: dt.datetime) -> int:
    return int(when.timestamp() * 1_000_000)


# ---------------------------------------------------------------- sources


def load_m1_sources(verify: bool) -> dict[str, dict[str, np.ndarray]]:
    manifest = json.loads(MANIFEST.read_text())
    expected = {}
    for raw in manifest.get("bar_sources") or []:
        if raw.get("timeframe") != "M1" or raw.get("source_family") != "bridge_ftmo_m1_202601":
            continue
        sym = str(raw.get("mapped_symbol") or raw.get("symbol") or "")
        expected[sym] = (str(raw.get("sha256") or ""), int(raw.get("row_count") or 0))
    series: dict[str, dict[str, np.ndarray]] = {}
    for sym, (want_sha, want_rows) in sorted(expected.items()):
        path = M1_DIR / f"{sym}_M1.csv"
        if not path.is_file():
            raise SystemExit(f"m1_source_missing:{sym}")
        if verify:
            got = sha256_file(path)
            if got != want_sha:
                raise SystemExit(f"m1_source_hash_mismatch:{sym}:{got}!={want_sha}")
        times, o, h, l, c = [], [], [], [], []
        with path.open("r", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            header = next(reader)
            if header[:5] != ["time", "open", "high", "low", "close"]:
                raise SystemExit(f"m1_columns_invalid:{sym}:{header}")
            for row in reader:
                times.append(epoch_us(parse_utc(row[0])))
                o.append(float(row[1]))
                h.append(float(row[2]))
                l.append(float(row[3]))
                c.append(float(row[4]))
        t = np.asarray(times, dtype=np.int64)
        if len(t) != want_rows:
            raise SystemExit(f"m1_row_count_mismatch:{sym}:{len(t)}!={want_rows}")
        if np.any(t[1:] <= t[:-1]):
            raise SystemExit(f"m1_time_not_strict:{sym}")
        series[sym] = {
            "t": t,
            "open": np.asarray(o, dtype=np.float64),
            "high": np.asarray(h, dtype=np.float64),
            "low": np.asarray(l, dtype=np.float64),
            "close": np.asarray(c, dtype=np.float64),
        }
    return series


POOL_FIELDS = (
    "candidate_id",
    "decision_time_utc",
    "symbol",
    "side",
    "entry_price",
    "stop_loss",
    "take_profit_1",
    "policy_target_r",
    "raw_target_r",
    "cost_r",
    "opportunity_net_proxy_r",
    "origin_family",
    "final_blocker_class",
    "dynamic_geometry_policy",
    "decision_timeframe",
    "selector_action",
    "effective_selector_action",
    "candidate_probability",
    "expected_net_r",
    "fill_probability",
    "utc_hour_bucket",
)


def load_pool() -> list[dict]:
    rows = []
    with gzip.open(POOL, "rt") as fh:
        for line in fh:
            raw = json.loads(line)
            rows.append({k: raw.get(k) for k in POOL_FIELDS})
    return rows


def load_sidecar_terminals() -> dict[tuple[str, str], dict]:
    """Sidecar last-bar close and observation count, keyed by join key."""
    out = {}
    with gzip.open(SIDECAR, "rt") as fh:
        for line in fh:
            raw = json.loads(line)
            obs = raw.get("ordered_path_observations") or []
            key = (raw["candidate_id"], raw["decision_time_utc"])
            out[key] = {
                "n": len(obs),
                "last_close": float(obs[-1]["close"]) if obs else None,
                "last_time": obs[-1]["time_utc"] if obs else None,
                "tick": raw.get("ordered_tick_source") is not None,
            }
    return out


# ---------------------------------------------------------------- walker


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-verify-hashes", action="store_true")
    ap.add_argument("--out", type=Path, default=Path(__file__).with_name("W0_CAPTURE_HORIZON_V1.json"))
    ap.add_argument("--rowdump", type=Path, default=None)
    args = ap.parse_args()

    series = load_m1_sources(verify=not args.no_verify_hashes)
    pool = load_pool()
    side_terminals = load_sidecar_terminals()
    print(f"pool rows={len(pool)} symbols={len(series)} sidecar={len(side_terminals)}", file=sys.stderr)

    n = len(pool)
    nh = len(HORIZONS_MIN)
    # per-row outputs
    gross_rec = np.full(n, np.nan)          # sealed recorded gross R
    target_r = np.full(n, np.nan)
    walk_gross = np.full((n, nh), np.nan)   # pure geometry gross at each horizon
    walk_out = np.zeros((n, nh), dtype=np.int8)  # 1 target 2 stop 3 mark 0 no-data
    mfe = np.full((n, nh), np.nan)
    mae = np.full((n, nh), np.nan)
    t_target_min = np.full((n, nh), np.nan)  # minutes from decision to first target touch
    t_stop_min = np.full((n, nh), np.nan)
    bars_avail = np.zeros((n, nh), dtype=np.int32)
    # MFE before the recorded (120-min) exit, over the FULL max window
    mfe_pre_exit = np.full(n, np.nan)

    fam = [r["origin_family"] for r in pool]
    blk = [r["final_blocker_class"] for r in pool]
    pol = [r["dynamic_geometry_policy"] for r in pool]

    skipped = {"no_geom": 0, "no_symbol": 0, "no_bars": 0}
    for i, r in enumerate(pool):
        sym = r["symbol"]
        s = series.get(sym)
        if s is None:
            skipped["no_symbol"] += 1
            continue
        entry = r["entry_price"]
        stop = r["stop_loss"]
        tp = r["take_profit_1"]
        side = str(r["side"] or "").upper()
        if entry is None or stop is None or tp is None or side not in ("LONG", "SHORT"):
            skipped["no_geom"] += 1
            continue
        base = abs(float(entry) - float(stop))
        if not (base > 0):
            skipped["no_geom"] += 1
            continue
        tgt_d = (float(tp) - float(entry)) / base if side == "LONG" else (float(entry) - float(tp)) / base
        target_r[i] = tgt_d
        net = r["opportunity_net_proxy_r"]
        cost = r["cost_r"]
        if net is not None and cost is not None:
            gross_rec[i] = float(net) + float(cost)

        d_us = epoch_us(parse_utc(r["decision_time_utc"]))
        t = s["t"]
        start = int(np.searchsorted(t, d_us, side="right"))
        end_max = int(np.searchsorted(t, d_us + MAX_HORIZON_MIN * 60_000_000, side="right"))
        if start >= end_max:
            skipped["no_bars"] += 1
            continue
        hi = s["high"][start:end_max]
        lo = s["low"][start:end_max]
        cl = s["close"][start:end_max]
        tt = t[start:end_max]
        if side == "LONG":
            fav = (hi - entry) / base
            adv = (entry - lo) / base
            term = (cl - entry) / base
        else:
            fav = (entry - lo) / base
            adv = (hi - entry) / base
            term = (entry - cl) / base
        rf = np.maximum.accumulate(fav)
        ra = np.maximum.accumulate(adv)
        # first index reaching target / stop over the FULL window
        gi_t = int(np.searchsorted(rf, tgt_d - TOL, side="left"))
        gi_s = int(np.searchsorted(ra, 1.0 - TOL, side="left"))

        for j, hmin in enumerate(HORIZONS_MIN):
            e = int(np.searchsorted(tt, d_us + hmin * 60_000_000, side="right"))
            if e <= 0:
                continue
            bars_avail[i, j] = e
            it = gi_t if gi_t < e else -1
            iss = gi_s if gi_s < e else -1
            mfe[i, j] = rf[e - 1]
            mae[i, j] = ra[e - 1]
            if it >= 0:
                t_target_min[i, j] = (tt[it] - d_us) / 60_000_000
            if iss >= 0:
                t_stop_min[i, j] = (tt[iss] - d_us) / 60_000_000
            if it >= 0 and (iss < 0 or it < iss):
                walk_gross[i, j] = tgt_d
                walk_out[i, j] = 1
            elif iss >= 0 and (it < 0 or iss < it):
                walk_gross[i, j] = -1.0
                walk_out[i, j] = 2
            elif it >= 0 and iss >= 0 and it == iss:
                # same-bar ambiguity -> engine's conservative stop close
                walk_gross[i, j] = -1.0
                walk_out[i, j] = 2
            else:
                walk_gross[i, j] = max(-1.0, min(float(term[e - 1]), tgt_d))
                walk_out[i, j] = 3
        # MFE strictly before the 120-minute recorded exit boundary
        e120 = int(bars_avail[i, 0])
        if e120 > 0:
            mfe_pre_exit[i] = rf[e120 - 1]

    print(f"skipped={skipped}", file=sys.stderr)

    ok = np.isfinite(gross_rec) & np.isfinite(walk_gross[:, 0])
    print(f"reconcilable rows={int(ok.sum())}", file=sys.stderr)

    # ---------------------------------------------------- 1. RECONCILE
    diff = walk_gross[:, 0] - gross_rec
    close = ok & (np.abs(diff) <= 0.02)
    recon = {
        "rows_compared": int(ok.sum()),
        "match_within_0p02R": int(close.sum()),
        "match_share": float(close.sum() / max(1, ok.sum())),
        "mean_abs_diff_R": float(np.nanmean(np.abs(diff[ok]))),
        "mean_signed_diff_walk_minus_recorded_R": float(np.nanmean(diff[ok])),
        "recorded_lower_than_pure_walk_rows": int((ok & (diff > 0.02)).sum()),
        "recorded_higher_than_pure_walk_rows": int((ok & (diff < -0.02)).sum()),
        "recorded_lower_mean_gap_R": float(np.nanmean(diff[ok & (diff > 0.02)])) if int((ok & (diff > 0.02)).sum()) else None,
        "recorded_higher_mean_gap_R": float(np.nanmean(diff[ok & (diff < -0.02)])) if int((ok & (diff < -0.02)).sum()) else None,
    }

    # outcome classes on the RECORDED gross
    tr = np.where(np.isfinite(target_r), target_r, 2.0)
    cls_target = ok & (gross_rec >= tr - 0.02)
    cls_stop = ok & (gross_rec <= -0.98)
    cls_subwin = ok & (gross_rec > 0.02) & (gross_rec < tr - 0.02)
    cls_scratch = ok & (np.abs(gross_rec) <= 0.02)
    cls_partloss = ok & (gross_rec < -0.02) & (gross_rec > -0.98)
    classes = {
        "target": cls_target,
        "full_stop": cls_stop,
        "sub_target_winner": cls_subwin,
        "scratch": cls_scratch,
        "partial_loss": cls_partloss,
    }
    class_counts = {k: int(v.sum()) for k, v in classes.items()}
    class_share = {k: float(v.sum() / max(1, ok.sum())) for k, v in classes.items()}

    # what does the pure walker say each recorded class was, at 120m?
    outmap = {0: "no_data", 1: "target", 2: "stop", 3: "mark_at_horizon"}
    walker_by_class = {}
    for k, m in classes.items():
        cnt = {}
        for code, name in outmap.items():
            cnt[name] = int((m & (walk_out[:, 0] == code)).sum())
        walker_by_class[k] = cnt

    # ---------------------------------------------------- 2. HORIZON
    horizon_rows = []
    base_mask = ok
    for j, hmin in enumerate(HORIZONS_MIN):
        m = base_mask & np.isfinite(walk_gross[:, j])
        g = walk_gross[m, j]
        o = walk_out[m, j]
        horizon_rows.append(
            {
                "horizon_minutes": hmin,
                "n": int(m.sum()),
                "gross_mean_R": float(g.mean()),
                "share_target": float((o == 1).mean()),
                "share_stop": float((o == 2).mean()),
                "share_mark": float((o == 3).mean()),
                "win_rate_gross_gt0": float((g > 0).mean()),
                "mean_winner_R": float(g[g > 0].mean()) if (g > 0).any() else None,
                "mean_loser_R": float(g[g < 0].mean()) if (g < 0).any() else None,
                "mean_mark_R_of_mark_rows": float(g[o == 3].mean()) if (o == 3).any() else None,
                "mfe_mean_R": float(np.nanmean(mfe[m, j])),
                "mae_mean_R": float(np.nanmean(mae[m, j])),
            }
        )

    # per-family horizon lift 120m -> 1440m -> 14400m
    fam_rows = {}
    families = sorted({f for f in fam if f})
    for f in families:
        fm = base_mask & np.asarray([x == f for x in fam])
        if fm.sum() == 0:
            continue
        rec = {}
        for j, hmin in enumerate(HORIZONS_MIN):
            mm = fm & np.isfinite(walk_gross[:, j])
            if mm.sum() == 0:
                continue
            g = walk_gross[mm, j]
            o = walk_out[mm, j]
            rec[str(hmin)] = {
                "n": int(mm.sum()),
                "gross_mean_R": float(g.mean()),
                "share_target": float((o == 1).mean()),
                "share_stop": float((o == 2).mean()),
                "win_rate": float((g > 0).mean()),
            }
        rec["n"] = int(fm.sum())
        rec["recorded_gross_mean_R"] = float(np.nanmean(gross_rec[fm]))
        fam_rows[f] = rec

    # ---------------------------------------------------- 3. LEAKAGE
    # (a) sub-target winners: how far did price actually go, and when?
    sub = cls_subwin
    j120 = 0
    lastj = len(HORIZONS_MIN) - 1
    def frac(mask_num, mask_den):
        d = int(mask_den.sum())
        return (int(mask_num.sum()), d, float(mask_num.sum() / d) if d else None)

    sub_reach_120 = sub & (mfe[:, j120] >= tr - TOL)
    sub_reach_full = sub & (mfe[:, lastj] >= tr - TOL)
    sub_reach_1d = sub & (mfe[:, HORIZONS_MIN.index(1440)] >= tr - TOL)
    # of those that eventually reach target, did they take a full stop first?
    sub_reach_full_nostop = sub_reach_full & (walk_out[:, lastj] == 1)
    leakage_sub = {
        "n_sub_target_winners": int(sub.sum()),
        "recorded_gross_mean_R": float(np.nanmean(gross_rec[sub])),
        "mfe_within_120m_mean_R": float(np.nanmean(mfe[sub, j120])),
        "mfe_within_1d_mean_R": float(np.nanmean(mfe[sub, HORIZONS_MIN.index(1440)])),
        "mfe_within_10d_mean_R": float(np.nanmean(mfe[sub, lastj])),
        "reached_target_within_120m": frac(sub_reach_120, sub),
        "reached_target_within_1d": frac(sub_reach_1d, sub),
        "reached_target_within_10d": frac(sub_reach_full, sub),
        "reached_target_within_10d_without_stopping_first": frac(sub_reach_full_nostop, sub),
        "walk_gross_10d_mean_R": float(np.nanmean(walk_gross[sub, lastj])),
        "delta_10d_minus_recorded_R": float(np.nanmean(walk_gross[sub, lastj] - gross_rec[sub])),
    }

    # (b) full stops: how much was on the table before the stop?
    st = cls_stop
    st_mfe120 = mfe_pre_exit
    on_table = {}
    for thr in (0.5, 1.0, 1.5, 2.0):
        m = st & (st_mfe120 >= thr - TOL)
        on_table[f"mfe_ge_{thr}R_before_120m_horizon"] = frac(m, st)
    # more precisely: MFE strictly before the stop bar (within 120m)
    leakage_stop = {
        "n_full_stops": int(st.sum()),
        "mfe_within_120m_mean_R": float(np.nanmean(mfe[st, j120])),
        "on_table_before_horizon": on_table,
        "reached_target_within_10d": frac(st & (mfe[:, lastj] >= tr - TOL), st),
        "walk_gross_10d_mean_R": float(np.nanmean(walk_gross[st, lastj])),
    }

    # (c) headline decomposition of recoverable R/trade
    mean_rec = float(np.nanmean(gross_rec[ok]))
    mean_pure120 = float(np.nanmean(walk_gross[ok, j120]))
    per_h = {}
    for j, hmin in enumerate(HORIZONS_MIN):
        m = ok & np.isfinite(walk_gross[:, j])
        per_h[str(hmin)] = float(np.nanmean(walk_gross[m, j]))
    recover = {
        "recorded_gross_mean_R": mean_rec,
        "pure_geometry_120m_gross_mean_R": mean_pure120,
        "B_exit_policy_cost_R_per_trade": mean_pure120 - mean_rec,
        "pure_geometry_by_horizon_gross_mean_R": per_h,
        "A_horizon_wall_cost_R_per_trade_120m_to_1d": per_h["1440"] - per_h["120"],
        "A_horizon_wall_cost_R_per_trade_120m_to_10d": per_h["14400"] - per_h["120"],
        "total_A_plus_B_vs_recorded_at_10d_R_per_trade": per_h["14400"] - mean_rec,
        "mean_frozen_cost_R": float(np.nanmean([r["cost_r"] for r in pool if r["cost_r"] is not None])),
    }

    result = {
        "schema": "gtos-w0-capture-horizon-v1",
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "billed": False,
        "broker_live_authority": False,
        "february_2026_economics_read": False,
        "april_may_packs_read": False,
        "inputs": {
            "pool": str(POOL.relative_to(REPO)),
            "pool_sha256": sha256_file(POOL),
            "sidecar": str(SIDECAR.relative_to(REPO)),
            "m1_dir": str(M1_DIR),
            "m1_hashes_verified": not args.no_verify_hashes,
            "manifest": str(MANIFEST),
        },
        "source_facts": {
            "walk_horizon_minutes": 120,
            "horizon_set_at": "v4_timewarp_simulated_live_research_loop.py:378 REPAIRED_PENDING_EXPIRY_MINUTES=120",
            "horizon_applied_at": "v4_timewarp_simulated_live_research_loop.py:92468-92478 expiry=min(asof+pending_expiry, day_end)",
            "mark_to_market_at_horizon": "v4_timewarp_simulated_live_research_loop.py:63323-63410 attach_close_mark",
            "final_r_rule": "v4_timewarp_simulated_live_research_loop.py:60302-60357 path_final_r",
            "net_proxy_formula": "v4_timewarp_simulated_live_research_loop.py:92577-92580 missed_net_proxy_r = missed_final_r - expected_cost_r",
        },
        "recorded_outcome_classes": {"counts": class_counts, "shares": class_share},
        "reconciliation": recon,
        "walker_verdict_by_recorded_class_at_120m": walker_by_class,
        "horizon_sweep": horizon_rows,
        "horizon_sweep_by_family": fam_rows,
        "leakage_sub_target_winners": leakage_sub,
        "leakage_full_stops": leakage_stop,
        "recoverable_decomposition": recover,
    }
    args.out.write_text(json.dumps(result, indent=1, sort_keys=True))
    print(json.dumps(result["recoverable_decomposition"], indent=1))
    print(json.dumps(result["reconciliation"], indent=1))
    print(json.dumps(result["recorded_outcome_classes"], indent=1))
    print("horizon sweep:")
    for row in horizon_rows:
        print(
            f"  {row['horizon_minutes']:>6}m n={row['n']:>6} gross={row['gross_mean_R']:+.4f} "
            f"tgt={row['share_target']:.3f} stop={row['share_stop']:.3f} mark={row['share_mark']:.3f} "
            f"win={row['win_rate_gross_gt0']:.3f} mfe={row['mfe_mean_R']:.3f} mae={row['mae_mean_R']:.3f}"
        )
    print(json.dumps(result["leakage_sub_target_winners"], indent=1))
    print(json.dumps(result["leakage_full_stops"], indent=1))
    print(json.dumps(result["walker_verdict_by_recorded_class_at_120m"], indent=1))

    if args.rowdump:
        np.savez_compressed(
            args.rowdump,
            gross_rec=gross_rec,
            target_r=target_r,
            walk_gross=walk_gross,
            walk_out=walk_out,
            mfe=mfe,
            mae=mae,
            t_target_min=t_target_min,
            t_stop_min=t_stop_min,
            horizons=np.asarray(HORIZONS_MIN),
            family=np.asarray(fam, dtype=object),
            blocker=np.asarray(blk, dtype=object),
            policy=np.asarray(pol, dtype=object),
            cid=np.asarray([r["candidate_id"] for r in pool], dtype=object),
            cost_r=np.asarray([r["cost_r"] if r["cost_r"] is not None else np.nan for r in pool], dtype=np.float64),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
