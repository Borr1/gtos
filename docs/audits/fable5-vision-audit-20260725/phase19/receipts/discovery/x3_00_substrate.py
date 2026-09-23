#!/usr/bin/env python3
"""x3_00_substrate — build the PRE-CLOSE + FORWARD M1 tape for every January candidate.

The wave-19 path sidecar starts at the M1 bar labelled T+1 (T = decision instant), so it
cannot see (a) the forming M15 bar the decision was made ON, nor (b) the first 60 seconds
after the decision.  Both are needed to price earliness.  This rebuilds the tape directly
from the generator's own M1 sources and A/Bs the forward half against the sealed sidecar.

Convention (verified in this script, not assumed):
  * M1 rows are labelled by OPEN time, in true UTC.
  * bar labelled `T-1` spans [T-1, T) and its CLOSE is the decision instant price.
  * offset k (minutes) => enter at the close of bar labelled `T+k-1`, i.e. at instant T+k,
    then walk bars labelled T+k, T+k+1, ... (each fully in the future of the entry).
  * k = 0 is the M15 close = the shipped contract's entry instant.

Writes x3_TAPE.npz  (prices, float32, NaN where the minute has no bar).
"""
from __future__ import annotations
import csv, gzip, json, os, sys, collections
from datetime import datetime
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import w0_ws  # noqa: E402

M1_ROOT = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
           "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
M1_JAN = os.path.join(M1_ROOT, "bridge_ftmo_m1_202601")
M1_DEC = os.path.join(M1_ROOT, "bridge_ftmo_m1_202512")

OFF_LO, OFF_HI = -20, 120          # bar labels kept, relative to T (minutes)
NOFF = OFF_HI - OFF_LO + 1         # 141


def epoch_min(iso: str) -> int:
    return int(datetime.fromisoformat(iso).timestamp()) // 60


def load_m1(symbol):
    """{epoch_minute: (o,h,l,c)} for Dec+Jan."""
    out = {}
    for d in (M1_DEC, M1_JAN):
        p = os.path.join(d, f"{symbol}_M1.csv")
        if not os.path.isfile(p):
            continue
        with open(p, newline="") as fh:
            rd = csv.reader(fh)
            next(rd)
            for row in rd:
                out[epoch_min(row[0])] = (float(row[1]), float(row[2]),
                                          float(row[3]), float(row[4]))
    return out


def main():
    rows = w0_ws.load()
    base = {}
    with gzip.open(os.path.join(HERE, "l7_BASE.jsonl.gz"), "rt") as fh:
        for line in fh:
            r = json.loads(line)
            base[(r["candidate_id"], r["decision_time_utc"])] = r

    symbols = sorted({r["symbol"] for r in rows})
    print("symbols:", len(symbols))
    tapes = {}
    for s in symbols:
        tapes[s] = load_m1(s)
        if not tapes[s]:
            print("MISSING M1:", s)

    n = len(rows)
    px = np.full((n, NOFF, 4), np.nan, dtype=np.float64)
    entry = np.zeros(n, np.float64)
    stop = np.zeros(n, np.float64)
    rdist = np.zeros(n, np.float64)
    is_long = np.zeros(n, np.bool_)
    tgt = np.zeros(n, np.float64)
    cost_r = np.zeros(n, np.float64)
    spread_r = np.zeros(n, np.float64)
    gross_r = np.zeros(n, np.float64)
    plain = np.zeros(n, np.float64)
    born = []
    fam = []
    sym = []
    day = []
    dtu = []
    cid = []
    hour = np.zeros(n, np.int16)
    firstem = np.zeros(n, np.bool_)

    missing_pre = 0
    for i, r in enumerate(rows):
        T = epoch_min(r["decision_time_utc"])
        tp = tapes[r["symbol"]]
        for j, off in enumerate(range(OFF_LO, OFF_HI + 1)):
            b = tp.get(T + off)
            if b is not None:
                px[i, j, 0] = b[0]; px[i, j, 1] = b[1]
                px[i, j, 2] = b[2]; px[i, j, 3] = b[3]
        entry[i] = r["entry_price"]; stop[i] = r["stop_loss"]
        rdist[i] = r["risk_distance"]; is_long[i] = (r["side"] == "LONG")
        tgt[i] = r["policy_target_r"]; cost_r[i] = r["cost_r"]
        spread_r[i] = r["spread_r"]; gross_r[i] = r["gross_r"]
        plain[i] = r["plain_walk_r"]
        b = base.get(w0_ws.key(r))
        born.append(b["born_state"] if b else "unknown")
        fam.append(r["origin_family"]); sym.append(r["symbol"])
        day.append(r["decision_time_utc"][:10]); dtu.append(r["decision_time_utc"])
        cid.append(r["candidate_id"])
        hour[i] = int(r["decision_time_utc"][11:13])
        firstem[i] = bool(r["is_first_emission"])
        if np.isnan(px[i, -OFF_LO - 15:-OFF_LO, 3]).all():
            missing_pre += 1

    # ---- clock/price validation: reconstruct entry price at offset -1 close ----
    e_recon = px[:, -OFF_LO - 1, 3].astype(np.float64)
    ok = ~np.isnan(e_recon)
    rel = np.abs(e_recon[ok] - entry[ok]) / np.maximum(np.abs(entry[ok]), 1e-9)
    bornarr = np.array(born)
    atm = bornarr == "born_at_limit"
    rel_atm = np.abs(e_recon[ok & atm] - entry[ok & atm]) / np.abs(entry[ok & atm])
    val = {
        "rows": n,
        "rows_with_offset_minus1_bar": int(ok.sum()),
        "at_market_rows": int(atm.sum()),
        "entry_vs_recon_prevclose_atmarket_max_rel": float(rel_atm.max()),
        "entry_vs_recon_prevclose_atmarket_median_rel": float(np.median(rel_atm)),
        "entry_vs_recon_prevclose_atmarket_exact_share": float((rel_atm < 1e-9).mean()),
        "entry_vs_recon_prevclose_all_median_rel": float(np.median(rel)),
        "rows_with_no_preclose_bars": missing_pre,
    }

    # ---- forward-half A/B against the sealed sidecar ----
    idx = {(c, d): i for i, (c, d) in enumerate(zip(cid, dtu))}
    maxdiff = 0.0
    nb_tot = nb_match = 0
    npaths = 0
    lenmis = 0
    for rp in w0_ws.iter_rpaths():
        i = idx.get((rp["candidate_id"], rp["decision_time_utc"]))
        if i is None:
            continue
        npaths += 1
        d = rdist[i]; E = entry[i]; L = is_long[i]
        # sidecar bar 1 == label T+1 -> slice offsets +1 ..
        sl = px[i, -OFF_LO + 1:, :]
        have = ~np.isnan(sl[:, 3])
        hi = sl[have, 1].astype(np.float64); lo = sl[have, 2].astype(np.float64)
        cl = sl[have, 3].astype(np.float64)
        fav = (hi - E) / d if L else (E - lo) / d
        adv = (lo - E) / d if L else (E - hi) / d
        cls = (cl - E) / d if L else (E - cl) / d
        sf = np.array(rp["fav"], np.float64)
        if len(sf) != len(fav):
            lenmis += 1
            m = min(len(sf), len(fav))
            fav, adv, cls = fav[:m], adv[:m], cls[:m]
            sf = sf[:m]
            sa = np.array(rp["adv"], np.float64)[:m]
            sc = np.array(rp["cls"], np.float64)[:m]
        else:
            sa = np.array(rp["adv"], np.float64)
            sc = np.array(rp["cls"], np.float64)
        dd = max(np.abs(fav - sf).max(initial=0), np.abs(adv - sa).max(initial=0),
                 np.abs(cls - sc).max(initial=0))
        maxdiff = max(maxdiff, float(dd))
        nb_tot += len(sf)
        nb_match += int((np.abs(fav - sf) < 5e-4).sum())
    val.update({
        "sidecar_paths_compared": npaths,
        "sidecar_length_mismatches": lenmis,
        "sidecar_bars_compared": nb_tot,
        "sidecar_fav_agree_share_5e4": nb_match / max(nb_tot, 1),
        "sidecar_max_abs_R_diff": maxdiff,
    })

    np.savez_compressed(
        os.path.join(HERE, "x3_TAPE.npz"),
        px=px, entry=entry, stop=stop, rdist=rdist, is_long=is_long, tgt=tgt,
        cost_r=cost_r, spread_r=spread_r, gross_r=gross_r, plain=plain, hour=hour,
        firstem=firstem, born=np.array(born), fam=np.array(fam), sym=np.array(sym),
        day=np.array(day), cid=np.array(cid), dtu=np.array(dtu),
        off_lo=np.array([OFF_LO]), off_hi=np.array([OFF_HI]))
    json.dump(val, open(os.path.join(HERE, "X3_SUBSTRATE_V1.json"), "w"), indent=1)
    for k, v in val.items():
        print(f"{k:52s} {v}")


if __name__ == "__main__":
    main()
