#!/usr/bin/env python3
"""l11_lib — bar-level R-path substrate for lane l11 (exit-contract design).

Builds ONE npz cache from w0_R_PATHS + w0_WORKING_SET + w0cap2_DECISION_ANCHOR so that
every later pass is a numpy operation on (N, 120) float32 arrays instead of a JSON stream.

Conventions, inherited and NOT re-litigated here:
  * population TAKEABLE = born != born_past_stop  (w0-capture, zero look-ahead)
  * fill REAL           = fill at bar 0 if mkt_r_prev_close <= 0, else first bar with adv <= 0
  * tie inside a bar    = the STOP is taken
  * every *_r is signed for the trade's own side
  * horizon             = hard 2 h (<=120 M1 bars)
"""
from __future__ import annotations

import gzip
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.join(HERE, "w0_WORKING_SET.jsonl.gz")
RP = os.path.join(HERE, "w0_R_PATHS.jsonl.gz")
ANCHOR = os.path.join(HERE, "w0cap2_DECISION_ANCHOR_V1.jsonl.gz")
CACHE = os.path.join(HERE, "l11_SUBSTRATE_V1.npz")
META = os.path.join(HERE, "l11_SUBSTRATE_META_V1.json")

NB = 120
WS_FIELDS = ["candidate_id", "decision_time_utc", "origin_family", "symbol", "side",
             "spread_r", "commission_r", "expected_slippage_r", "swap_cost_r", "cost_r",
             "is_first_emission", "risk_distance", "session_bucket", "gross_r",
             "policy_target_r", "utc_hour_bucket"]


def born_class(mk):
    if mk is None:
        return "unknown"
    if mk <= -1.0 + 1e-12:
        return "born_past_stop"
    if mk < -1e-12:
        return "born_marketable"
    if mk <= 1e-12:
        return "born_at_limit"
    return "born_resting"


def build(verbose=True):
    anch = {}
    with gzip.open(ANCHOR, "rt") as fh:
        for line in fh:
            if not line.strip():
                continue
            a = json.loads(line)
            anch[(a["candidate_id"], a["decision_time_utc"])] = a.get("mkt_r_prev_close")

    wsr = {}
    with gzip.open(WS, "rt") as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            wsr[(r["candidate_id"], r["decision_time_utc"])] = r

    keys, fam, sym, side, day = [], [], [], [], []
    born, firstem = [], []
    spread, comm, slip, swap, costfr, gross_pool, ptr = [], [], [], [], [], [], []
    nb = []
    FAV = np.full((len(wsr), NB), np.nan, dtype=np.float32)
    ADV = np.full((len(wsr), NB), np.nan, dtype=np.float32)
    CLS = np.full((len(wsr), NB), np.nan, dtype=np.float32)
    i = 0
    with gzip.open(RP, "rt") as fh:
        for line in fh:
            if not line.strip():
                continue
            p = json.loads(line)
            k = (p["candidate_id"], p["decision_time_utc"])
            r = wsr[k]
            n = len(p["fav"])
            FAV[i, :n] = p["fav"]
            ADV[i, :n] = p["adv"]
            CLS[i, :n] = p["cls"]
            nb.append(n)
            keys.append(k)
            fam.append(r["origin_family"] or "unknown")
            sym.append(r["symbol"])
            side.append(r["side"])
            day.append(r["decision_time_utc"][:10])
            born.append(born_class(anch.get(k)))
            firstem.append(bool(r.get("is_first_emission")))
            spread.append(float(r.get("spread_r") or 0.0))
            comm.append(float(r.get("commission_r") or 0.0))
            slip.append(float(r.get("expected_slippage_r") or 0.0))
            swap.append(float(r.get("swap_cost_r") or 0.0))
            costfr.append(float(r.get("cost_r") or 0.0))
            gross_pool.append(float(r.get("gross_r") or 0.0))
            ptr.append(float(r.get("policy_target_r") or 2.0))
            i += 1
    N = i
    assert N == len(wsr), (N, len(wsr))

    np.savez_compressed(
        CACHE,
        fav=FAV[:N], adv=ADV[:N], cls=CLS[:N],
        nb=np.array(nb, dtype=np.int16),
        fam=np.array(fam), sym=np.array(sym), side=np.array(side), day=np.array(day),
        born=np.array(born), firstem=np.array(firstem, dtype=bool),
        spread=np.array(spread, dtype=np.float32), comm=np.array(comm, dtype=np.float32),
        slip=np.array(slip, dtype=np.float32), swap=np.array(swap, dtype=np.float32),
        costfr=np.array(costfr, dtype=np.float32),
        gross_pool=np.array(gross_pool, dtype=np.float32),
        ptr=np.array(ptr, dtype=np.float32),
        cid=np.array([k[0] for k in keys]), dt=np.array([k[1] for k in keys]),
    )
    meta = {"n": N, "born_counts": {b: born.count(b) for b in sorted(set(born))},
            "n_families": len(set(fam)), "n_symbols": len(set(sym)),
            "n_days": len(set(day))}
    with open(META, "w") as fh:
        json.dump(meta, fh, indent=1)
    if verbose:
        print(json.dumps(meta))
    return meta


class Sub:
    """Loaded substrate + derived fill index."""

    def __init__(self, path=CACHE):
        z = np.load(path, allow_pickle=False)
        for k in ("fav", "adv", "cls", "nb", "fam", "sym", "side", "day", "born",
                  "firstem", "spread", "comm", "slip", "swap", "costfr", "gross_pool",
                  "ptr", "cid", "dt"):
            setattr(self, k, z[k])
        self.N = len(self.nb)
        self.valid = ~np.isnan(self.fav)                       # (N,120) bar exists
        # REAL fill: bar 0 if born at-or-through market, else first bar with adv <= 0
        at_mkt = np.isin(self.born, ["born_at_limit", "born_marketable", "born_past_stop"])
        touch = (self.adv <= 1e-12) & self.valid
        first_touch = np.where(touch.any(1), touch.argmax(1), -1)
        self.fill = np.where(at_mkt, 0, first_touch).astype(np.int32)
        self.fill[(~at_mkt) & (first_touch < 0)] = -1
        # STRICT: no bar-0 assumption for anyone -- entry must be traded on the path
        self.fill_strict = first_touch.astype(np.int32)
        self.takeable = self.born != "born_past_stop"
        self.filled = self.fill >= 0

    def cost_r(self, spread_div=7.3, slip_mult=1.0, extra=0.0):
        """Corrected cost in R at the ORIGINAL risk distance (position size unchanged)."""
        return (self.spread / spread_div + self.comm + self.slip * slip_mult
                + self.swap + extra)

    def mask(self, population="TAKEABLE", family=None, firstem=False):
        m = self.takeable.copy() if population == "TAKEABLE" else np.ones(self.N, bool)
        if population == "PASTSTOP":
            m = ~self.takeable
        if family is not None:
            m &= (self.fam == family)
        if firstem:
            m &= self.firstem
        return m


def load():
    if not os.path.exists(CACHE):
        build()
    return Sub()


if __name__ == "__main__":
    build()
    s = Sub()
    print("N", s.N, "takeable", int(s.takeable.sum()), "filled&takeable",
          int((s.takeable & s.filled).sum()))
