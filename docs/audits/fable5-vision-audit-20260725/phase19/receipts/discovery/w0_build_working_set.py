#!/usr/bin/env python3
"""w0-workingset — build w0_WORKING_SET.jsonl.gz: pool JOIN path, geometry precomputed.

ONE streaming pass over the 34 MB ordered-path sidecar. Never holds it in memory.
Emits:
  w0_WORKING_SET.jsonl.gz          one row per candidate that has a usable path
  w0_WORKING_SET_BUILD_V1.json     coverage + validation receipt

Sign convention (documented in w0_WORKING_SET_README.md):
  d = risk_distance = abs(entry_price - stop_loss)
  signed R for the trade's OWN side:
      LONG :  fav(bar) = (high - entry)/d      adv(bar) = (low  - entry)/d
      SHORT:  fav(bar) = (entry - low )/d      adv(bar) = (entry - high)/d
  fav is the most FAVOURABLE R reachable inside the bar (>= 0 when price moved for us)
  adv is the most ADVERSE   R reachable inside the bar (<= 0 when price moved against us)
  mfe_r = max fav over path     mae_r = min adv over path   (mae_r is NEGATIVE normally)
Tie rule: CQ semantics — if target and stop are both first touched on the SAME bar,
which_came_first = 'stop' (conservative).
"""
from __future__ import annotations

import gzip
import json
import math
import os
import sys
from collections import Counter
from datetime import datetime, timezone

ROOT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
DISC = os.path.join(ROOT, "docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery")
POOL = os.path.join(ROOT, "docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz")
SIDE = os.path.join(ROOT, "docs/audits/fable5-vision-audit-20260725/phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz")
OUT = os.path.join(DISC, "w0_WORKING_SET.jsonl.gz")
RECEIPT = os.path.join(DISC, "w0_WORKING_SET_BUILD_V1.json")

TOL = 1e-12
STOP_R = -1.0


def iter_gz(path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def parse_iso(s):
    return datetime.fromisoformat(s)


def main():
    # ------------------------------------------------------------------ pool
    pool = {}
    dup_pool = 0
    bad_d = 0
    for r in iter_gz(POOL):
        k = (r["candidate_id"], r["decision_time_utc"])
        if k in pool:
            dup_pool += 1
        e, s = r.get("entry_price"), r.get("stop_loss")
        if e is None or s is None or not math.isfinite(float(e)) or not math.isfinite(float(s)) or abs(float(e) - float(s)) <= 0:
            bad_d += 1
        pool[k] = r
    n_pool = len(pool)

    # ------------------------------------------------------- stream sidecar
    seen = set()
    dup_side = 0
    n_side = 0
    no_pool = 0
    no_obs = 0
    unusable_d = 0
    side_mismatch = 0
    symbol_mismatch = 0
    written = 0
    bars_hist = Counter()
    first_cross = Counter()

    # validation accumulators (recomputed FROM the emitted rows)
    v_n = 0
    v_gross_sum = 0.0
    v_cost_sum = 0.0
    v_win = 0
    v_win_sum = 0.0
    v_loss = 0
    v_loss_sum = 0.0
    v_full_target = 0
    v_full_stop = 0
    v_path_target = 0
    v_path_stop = 0
    v_path_neither = 0
    v_mfe_ge_target = 0
    v_stop_then_reverse_1r = 0

    with gzip.open(OUT, "wt", encoding="utf-8") as out:
        for row in iter_gz(SIDE):
            n_side += 1
            k = (row["candidate_id"], row["decision_time_utc"])
            if k in seen:
                dup_side += 1
                continue
            seen.add(k)
            p = pool.get(k)
            if p is None:
                no_pool += 1
                continue
            obs = row.get("ordered_path_observations") or []
            if not obs:
                no_obs += 1
                continue
            entry = float(p["entry_price"])
            stop = float(p["stop_loss"])
            d = abs(entry - stop)
            if not math.isfinite(d) or d <= 0:
                unusable_d += 1
                continue
            side = p["side"]
            if row.get("side") and row["side"] != side:
                side_mismatch += 1
            if row.get("symbol") and row["symbol"] != p.get("symbol"):
                symbol_mismatch += 1
            tgt = float(p.get("policy_target_r") or 2.0)
            is_long = side == "LONG"

            mfe = -1e18
            mae = 1e18
            i_mfe = i_mae = None
            i_tgt = i_stop = None
            for i, b in enumerate(obs):
                hi = b["high"]
                lo = b["low"]
                if is_long:
                    fav = (hi - entry) / d
                    adv = (lo - entry) / d
                else:
                    fav = (entry - lo) / d
                    adv = (entry - hi) / d
                if fav > mfe:
                    mfe = fav
                    i_mfe = i
                if adv < mae:
                    mae = adv
                    i_mae = i
                if i_tgt is None and fav >= tgt - TOL:
                    i_tgt = i
                if i_stop is None and adv <= STOP_R + TOL:
                    i_stop = i
                if i_tgt is not None and i_stop is not None:
                    # both resolved; keep scanning for full-path mfe/mae + after-stop
                    pass

            if i_stop is not None and (i_tgt is None or i_stop <= i_tgt):
                which = "stop"
            elif i_tgt is not None:
                which = "target"
            else:
                which = "neither"
            first_cross[which] += 1

            # mfe AFTER the stop bar (strictly after)
            mfe_after_stop = None
            if i_stop is not None and i_stop + 1 < len(obs):
                m = -1e18
                for b in obs[i_stop + 1:]:
                    if is_long:
                        f = (b["high"] - entry) / d
                    else:
                        f = (entry - b["low"]) / d
                    if f > m:
                        m = f
                mfe_after_stop = round(m, 6)
            elif i_stop is not None:
                mfe_after_stop = None  # stop was the last bar; no after-window

            # mae up to and INCLUDING the target bar
            mae_before_target = None
            if i_tgt is not None:
                m = 1e18
                for b in obs[: i_tgt + 1]:
                    if is_long:
                        a = (b["low"] - entry) / d
                    else:
                        a = (entry - b["high"]) / d
                    if a < m:
                        m = a
                mae_before_target = round(m, 6)

            last = obs[-1]
            if is_long:
                r_end = (last["close"] - entry) / d
            else:
                r_end = (entry - last["close"]) / d

            fb = obs[0]["time_utc"]
            lb = last["time_utc"]
            try:
                pm = (parse_iso(lb) - parse_iso(fb)).total_seconds() / 60.0
            except Exception:
                pm = None

            rec = dict(p)  # every pool field verbatim
            rec.update(
                risk_distance=d,
                mfe_r=round(mfe, 6),
                mae_r=round(mae, 6),
                bars_to_mfe=(i_mfe + 1) if i_mfe is not None else None,
                bars_to_mae=(i_mae + 1) if i_mae is not None else None,
                bars_to_target=(i_tgt + 1) if i_tgt is not None else None,
                bars_to_stop=(i_stop + 1) if i_stop is not None else None,
                which_came_first=which,
                r_at_path_end=round(r_end, 6),
                path_bars=len(obs),
                path_minutes=pm,
                first_bar_utc=fb,
                last_bar_utc=lb,
                mfe_r_after_stop=mfe_after_stop,
                mae_r_before_target=mae_before_target,
                path_horizon_end_utc=row.get("horizon_end_utc"),
                path_source_timeframe=row.get("source_timeframe"),
                path_arm_id=row.get("arm_id"),
                gross_r=round(float(p["opportunity_net_proxy_r"]) + float(p["cost_r"]), 9),
            )
            out.write(json.dumps(rec, separators=(",", ":")) + "\n")
            written += 1
            bars_hist[len(obs)] += 1

            # ---- validation, recomputed from what we just emitted ----
            gr = rec["gross_r"]
            v_n += 1
            v_gross_sum += gr
            v_cost_sum += float(p["cost_r"])
            if gr > 0:
                v_win += 1
                v_win_sum += gr
            else:
                v_loss += 1
                v_loss_sum += gr
            if gr >= tgt - 1e-9:
                v_full_target += 1
            if gr <= -1 + 1e-9:
                v_full_stop += 1
            if which == "target":
                v_path_target += 1
            elif which == "stop":
                v_path_stop += 1
            else:
                v_path_neither += 1
            if mfe >= tgt - TOL:
                v_mfe_ge_target += 1
            if mfe_after_stop is not None and mfe_after_stop >= 1.0:
                v_stop_then_reverse_1r += 1

    orphan_pool = n_pool - len(seen & set(pool.keys()))

    rec = {
        "schema": "gtos.wave19.w0.workingset.build.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": {"pool": POOL, "sidecar": SIDE},
        "output": OUT,
        "coverage": {
            "pool_rows": n_pool,
            "pool_duplicate_keys": dup_pool,
            "pool_rows_with_nonpositive_risk_distance": bad_d,
            "sidecar_rows": n_side,
            "sidecar_duplicate_keys": dup_side,
            "sidecar_rows_with_no_pool_match": no_pool,
            "sidecar_rows_with_empty_observations": no_obs,
            "sidecar_rows_dropped_unusable_risk_distance": unusable_d,
            "written": written,
            "pool_rows_without_a_path": orphan_pool,
            "side_field_mismatch_pool_vs_sidecar": side_mismatch,
            "symbol_field_mismatch_pool_vs_sidecar": symbol_mismatch,
        },
        "validation_recomputed_from_output": {
            "n": v_n,
            "gross_mean": round(v_gross_sum / v_n, 6),
            "frozen_cost_mean": round(v_cost_sum / v_n, 6),
            "gross_win_rate": round(v_win / v_n, 6),
            "winner_mean_r": round(v_win_sum / v_win, 6),
            "loser_mean_r": round(v_loss_sum / v_loss, 6),
            "payoff_ratio": round(abs((v_win_sum / v_win) / (v_loss_sum / v_loss)), 6),
            "share_gross_ge_policy_target": round(v_full_target / v_n, 6),
            "share_gross_le_minus_1": round(v_full_stop / v_n, 6),
            "path_which_came_first": {
                "target": v_path_target,
                "stop": v_path_stop,
                "neither": v_path_neither,
                "target_share": round(v_path_target / v_n, 6),
                "stop_share": round(v_path_stop / v_n, 6),
                "neither_share": round(v_path_neither / v_n, 6),
            },
            "share_mfe_ge_policy_target": round(v_mfe_ge_target / v_n, 6),
            "stopped_then_mfe_ge_1R_after": v_stop_then_reverse_1r,
        },
        "expected_established": {
            "gross_win_rate": 0.347,
            "winner_mean_r": 1.044,
            "loser_mean_r": -0.888,
            "gross_mean": -0.2175,
            "frozen_cost_mean": 0.663,
            "full_target_share": 0.111,
            "full_stop_share": 0.544,
        },
        "path_bars_histogram_top": dict(bars_hist.most_common(12)),
    }
    with open(RECEIPT, "w") as fh:
        json.dump(rec, fh, indent=1)

    c = rec["coverage"]
    v = rec["validation_recomputed_from_output"]
    print("pool=%d sidecar=%d written=%d no_pool=%d no_obs=%d dup_side=%d orphan_pool=%d"
          % (c["pool_rows"], c["sidecar_rows"], c["written"], c["sidecar_rows_with_no_pool_match"],
             c["sidecar_rows_with_empty_observations"], c["sidecar_duplicate_keys"], c["pool_rows_without_a_path"]))
    print("VALIDATE gross_mean=%.4f win=%.4f winM=%.4f lossM=%.4f cost=%.4f"
          % (v["gross_mean"], v["gross_win_rate"], v["winner_mean_r"], v["loser_mean_r"], v["frozen_cost_mean"]))
    print("VALIDATE gross>=target=%.4f gross<=-1=%.4f | PATH target=%.4f stop=%.4f neither=%.4f | mfe>=target=%.4f"
          % (v["share_gross_ge_policy_target"], v["share_gross_le_minus_1"],
             v["path_which_came_first"]["target_share"], v["path_which_came_first"]["stop_share"],
             v["path_which_came_first"]["neither_share"], v["share_mfe_ge_policy_target"]))
    print("stopped_then_reversed_>=1R:", v["stopped_then_mfe_ge_1R_after"])
    print("bars hist top:", list(bars_hist.most_common(6)))
    print("receipt:", RECEIPT)


if __name__ == "__main__":
    main()
