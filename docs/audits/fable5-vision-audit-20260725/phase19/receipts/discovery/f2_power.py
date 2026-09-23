"""f2_power — the detection floor of the f2 ladder.

"We measured no signal" is only a result if the measurement could have seen one.
This injects a KNOWN directional edge into the same rows, at the same instants, with
the same risk distances and the same toll, and reports what the paired test recovers.

The injection: on a random q-fraction of rows, replace the generator's own side with
the side that the realised path actually rewarded under the SHIPPED exit contract.
q = 0 is the real signal untouched.  The recovered quantity is compared to the same
PLACEBO_SIDE arm the main ladder uses, with the identical day-block bootstrap.

Output: the smallest injected edge whose CI95 excludes zero -> the floor.  Any claim
that the real signal is "zero" is only as strong as that floor.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import f2_ladder as F  # noqa: E402
import f2_run as R  # noqa: E402
import pbg_econ as E  # noqa: E402
import pbg_lib as L  # noqa: E402


def shipped_for_side(fr, long, horizon, target_r):
    rc, rh, rl = F.r_frames(fr["W_c"], fr["W_h"], fr["W_l"], fr["entry"], fr["d"],
                            long, 0, horizon)
    v, _ = F.walk_fixed(rc, rh, rl, target_r)
    return np.where(fr["ok"], v, np.nan)


def path_for_side(fr, long, horizon):
    rc, _rh, _rl = F.r_frames(fr["W_c"], fr["W_h"], fr["W_l"], fr["entry"], fr["d"],
                              long, 0, horizon)
    return np.where(fr["ok"], F.oracle_exit_close(rc), np.nan)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True)
    ap.add_argument("--month", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--horizon", type=int, default=F.HORIZON)
    ap.add_argument("--target-r", type=float, default=F.SHIPPED_TARGET_R)
    args = ap.parse_args()

    rows = F.load_close_rows(args.indir, set(F.AT_MARKET))
    tape = E.Tape(L.SYMBOLS, [args.month])
    cm = E.CostModel()
    rng = np.random.default_rng(20260806)

    fr = R.build_frame(rows, tape, cm, horizon=args.horizon, placebo=None, rng=rng)
    frp = R.build_frame(rows, tape, cm, horizon=args.horizon, placebo="side", rng=rng)

    long_real = fr["long"]
    ship_L = shipped_for_side(fr, np.ones(fr["n"], bool), args.horizon, args.target_r)
    ship_S = shipped_for_side(fr, np.zeros(fr["n"], bool), args.horizon, args.target_r)
    path_L = path_for_side(fr, np.ones(fr["n"], bool), args.horizon)
    path_S = path_for_side(fr, np.zeros(fr["n"], bool), args.horizon)
    best_long = np.where(np.nan_to_num(ship_L, nan=-9e9) >= np.nan_to_num(ship_S, nan=-9e9),
                         True, False)

    ship_placebo = shipped_for_side(frp, frp["long"], args.horizon, args.target_r)
    path_placebo = path_for_side(frp, frp["long"], args.horizon)

    ok = fr["ok"] & frp["ok"]
    day = fr["day"]

    def pick(long_vec, arr_L, arr_S):
        return np.where(long_vec, arr_L, arr_S)

    out = {
        "lane": "f2_power", "month": args.month, "n_rows": int(ok.sum()),
        "horizon_m1_bars": args.horizon, "target_r": args.target_r,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "toll_r_per_trade": float(np.nanmean(fr["cost_r"][ok])),
        "injections": {},
    }

    for q in (0.0, 0.005, 0.01, 0.02, 0.03, 0.05, 0.10, 0.20, 0.50):
        take = rng.random(fr["n"]) < q
        lv = np.where(take, best_long, long_real)
        sh = np.where(ok, pick(lv, ship_L, ship_S), np.nan)
        pa = np.where(ok, pick(lv, path_L, path_S), np.nan)
        d_sh = sh - np.where(ok, ship_placebo, np.nan)
        d_pa = pa - np.where(ok, path_placebo, np.nan)
        rec = {
            "q_fraction_replaced_with_the_winning_side": q,
            "share_side_changed_vs_real": float((lv != long_real)[ok].mean()),
            "R1_shipped": F.day_boot(d_sh, day),
            "R3_path_oracle": F.day_boot(d_pa, day),
            "R1_level_net_r_per_trade": float(np.nanmean(sh[ok] - fr["cost_r"][ok])),
        }
        out["injections"]["q=%.3f" % q] = rec
        b = rec["R1_shipped"]
        print("q=%.3f  sideflip %.4f  R1 signal %+.5f CI[%+.5f,%+.5f] p(<=0)=%.4f | "
              "R3path signal %+.5f CI[%+.5f,%+.5f] p=%.4f"
              % (q, rec["share_side_changed_vs_real"], b["mean"], b["ci95_lo"],
                 b["ci95_hi"], b["p_le_0"], rec["R3_path_oracle"]["mean"],
                 rec["R3_path_oracle"]["ci95_lo"], rec["R3_path_oracle"]["ci95_hi"],
                 rec["R3_path_oracle"]["p_le_0"]), flush=True)

    # the ceiling: what a PERFECT directional signal is worth on these very rows
    sh = np.where(ok, pick(best_long, ship_L, ship_S), np.nan)
    out["perfect_direction_ceiling"] = {
        "R1_shipped_gross": float(np.nanmean(sh)),
        "R1_shipped_net": float(np.nanmean(sh[ok] - fr["cost_r"][ok])),
        "vs_real_gross": float(np.nanmean(sh) - np.nanmean(np.where(ok, pick(long_real, ship_L, ship_S), np.nan))),
    }
    Path(args.out).write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out["perfect_direction_ceiling"], indent=1))


if __name__ == "__main__":
    main()
