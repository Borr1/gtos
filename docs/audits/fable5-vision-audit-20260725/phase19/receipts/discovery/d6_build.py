"""d6_build — per-trade dataset for the surviving candidate (forming-bar decision).

Streams one month's pbg_run output, keeps ONLY the close-arm row (k=15) and the
FIRST partial row (min k < 15) per setup key, prices both on the same M1 tape with
the same h1 four-term hour-aware broker-true cost model PB used, and writes one
row per (setup, arm) to a compact JSONL.gz.

Everything downstream (gating, ablation, pooling, bands) reads that file, so no
analysis ever re-walks the tape.

    python3 d6_build.py --in /tmp/pbg_full_jan --month 202601 --out /tmp/d6/trades/202601.jsonl.gz
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PBG = HERE.parent / "pbg"
REPO = HERE.parents[5]
sys.path.insert(0, str(PBG))
sys.path.insert(0, str(REPO))
os.chdir(REPO)

import pbg_econ as E  # noqa: E402
import pbg_lib as L  # noqa: E402

AT_MARKET = (
    "displacement_continuation",
    "liquidity_sweep_reclaim",
    "structural_distance_extreme",
    "volatility_compression_expansion",
    "session_open_range_break",
    "regime_transition_break",
    "cross_asset_lead_lag",
)
POI = ("current_fvg_fill", "current_ob_retest", "current_breaker_re_entry")
EARLY5 = (
    "displacement_continuation",
    "liquidity_sweep_reclaim",
    "session_open_range_break",
    "regime_transition_break",
    "volatility_compression_expansion",
)


def setup_key(r):
    if r["f"].startswith("current_"):
        return (r["s"], r["f"], r["d"], r["b"], r["cid"])
    return (r["s"], r["f"], r["d"], r["b"])


def load_rows(indir):
    for p in sorted(glob.glob(os.path.join(indir, "pbg_*.jsonl.gz"))):
        with gzip.open(p, "rt") as fh:
            for line in fh:
                yield json.loads(line)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="indir", required=True)
    ap.add_argument("--month", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    # ---- pass 1: keep close row and first-partial row per setup key
    best = {}  # key -> [close_row_or_None, first_partial_row_or_None]
    n_rows = 0
    for r in load_rows(args.indir):
        n_rows += 1
        k = setup_key(r)
        slot = best.get(k)
        if slot is None:
            slot = best[k] = [None, None]
        if r["k"] == 15:
            if slot[0] is None:
                slot[0] = r
        else:
            if slot[1] is None or r["k"] < slot[1]["k"]:
                slot[1] = r

    tape = E.Tape(L.SYMBOLS, [args.month])
    cm = E.CostModel()

    def price(r, d0=None):
        i = tape.idx(r["t"])
        entry = r["e"]
        d = abs(entry - r["sl"]) if d0 is None else d0
        if not (d > 0):
            return None
        stop_eff = entry - d if r["d"] == "L" else entry + d
        limit = r["f"].startswith("current_")
        fn = E.walk_limit if limit else E.walk
        out = {}
        for tgt in (2.0, 1.5):
            w = fn(tape, r["s"], i, entry=entry, stop=stop_eff,
                   long=(r["d"] == "L"), target_r=tgt)
            if w is None:
                return None
            out[tgt] = w
        # the generator's OWN emitted take-profit, expressed in R of this arm's stop
        tp = r.get("tp") or 0.0
        own_r = None
        if tp:
            own_r = (tp - entry) / d if r["d"] == "L" else (entry - tp) / d
        w_own = None
        if own_r and own_r > 0:
            w_own = fn(tape, r["s"], i, entry=entry, stop=stop_eff,
                       long=(r["d"] == "L"), target_r=own_r)
        cpx, terms = cm.cost_px(r["s"], r["t"], entry, r["d"] == "L")
        g2, ex2, eb2, nb2 = out[2.0]
        g15, ex15, _, _ = out[1.5]
        rec = {
            "g2": g2, "x2": ex2, "eb2": eb2, "nb2": nb2,
            "g15": g15, "x15": ex15,
            "cr": (0.0 if ex2 == "no_fill" else cpx / d),
            "cr15": (0.0 if ex15 == "no_fill" else cpx / d),
            "d": d, "e": entry,
            "hr": cm.broker_hour(r["t"]),
            "sp_r": terms["spread"] / d, "cm_r": terms["commission"] / d,
            "sl_r": terms["slippage"] / d, "sw_r": terms["swap"] / d,
        }
        if w_own is not None:
            rec["gown"] = w_own[0]
            rec["xown"] = w_own[1]
            rec["own_r"] = own_r
        return rec

    n_out = 0
    with gzip.open(args.out, "wt") as fh:
        for key, (ck, pk) in best.items():
            sym, fam, side, bar = key[0], key[1], key[2], key[3]
            base = {"m": args.month, "s": sym, "f": fam, "sd": side, "b": bar,
                    "cohort": ("POI" if fam in POI else "ATM"),
                    "e5": fam in EARLY5}
            tc = price(ck) if ck is not None else None
            tp_ = price(pk) if pk is not None else None
            td0 = price(pk, d0=tc["d"]) if (pk is not None and tc is not None) else None
            rec = dict(base)
            rec["paired"] = bool(tc and tp_)
            rec["k"] = pk["k"] if pk is not None else None
            rec["earliness"] = (15 - pk["k"]) if pk is not None else None
            rec["day_close"] = ck["t"][:10] if ck is not None else None
            rec["day_part"] = pk["t"][:10] if pk is not None else None
            rec["t_close"] = ck["t"] if ck is not None else None
            rec["t_part"] = pk["t"] if pk is not None else None
            if tc:
                rec["C"] = tc
            if tp_:
                rec["P"] = tp_
            if td0:
                rec["D"] = td0
            if tc or tp_:
                fh.write(json.dumps(rec, separators=(",", ":")) + "\n")
                n_out += 1

    print(json.dumps({
        "month": args.month, "rows_read": n_rows, "setups": len(best),
        "written": n_out,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }))


if __name__ == "__main__":
    main()
