"""Session AO, items 1/2/4 — regime conditioning for the three sleeves whose named next
lever is `REGIME_GATE_OR_PARK`, on AB's own published dials, both populations.

    python3 docs/audits/fable5-vision-audit-20260725/phase10/receipts/ao_regime_conditioning.py

THE PRE-DECLARATION DISCIPLINE, AND WHY IT COMES FIRST IN THIS FILE
------------------------------------------------------------------
Session AH §4.3 made the rule: *one bucket per mechanism, declared in source BEFORE any
result in that file was computed, chosen from what the mechanism IS plus a production
precedent where one exists.* `PRE_DECLARED` below is that declaration. Everything the file
enumerates afterwards is stamped `enumerated` and carries a within-enumeration Bonferroni
bill, so a reader can tell a hypothesis from a search.

THE MEASUREMENT THAT REFRAMES ITEMS 1 AND 4, AND IT IS ARITHMETIC RATHER THAN A RESULT
-------------------------------------------------------------------------------------
AB's five dials are `SURFACE_OPEN`, `VOL_REGIME`, `PERSISTENCE`, `HORIZON_CONFLICT` and
`TREND_STATE` (`regime_spine/dials.py:124-178`). Four of the five are, term for term, the
substrate's own confluence coordinates:

    AB dial            regime_spine/dials.py     substrate_engine.py
    VOL_REGIME         `_vol_regime` = vr_raw     `compute_state`'s `vr`      -> `_bucket_vr`
    PERSISTENCE        `_persistence` = ac60_prim `compute_state`'s `ac60`    -> `_bucket_persist`
    TREND_STATE        `_trend_state` = slope50   `compute_state`'s `slope50` -> `_bucket_slope`
    HORIZON_CONFLICT   `_horizon_conflict`        `compute_state`'s `mtf_align`

and `dials.py:97` says so in its own docstring: *"— `substrate_engine`'s `mtf_align`, by
hand."* The two substrate sleeves' cells are stated in `substrate.py:69-79`:

    sub_xvol_pullback  vol=xhi | persist=rand | trend=up  | mtf=conflict            (depth 4)
    sub_mid_dn_revert  vol=mid | trend=dn     | mtf=neutral| rngpos=mid | comp=norm
                       | persist=revert | session=ny                                (depth 7)

So **every** AB dial bucket is already a firing CONDITION of both sleeves. A bucket-level
regime gate on them cannot move a single trade — it is the identity filter. That is not a
result about the market, it is the composition of two functions, and it is why AL §10 item 2's
"AB's regime dials, unexplored for this sleeve" cannot be executed as written. §1 proves it on
the trades rather than asserting it from the source, because a numeric proof is what makes it
citable, and the two implementations differ in float accumulation
(`primitives.autocorr` uses `statistics.mean`, `substrate_engine._ac` uses `sum/n`).

WHAT CONDITIONING THEREFORE REMAINS, AND IT IS TWO THINGS
--------------------------------------------------------
(a) **The substrate coordinates a cell leaves FREE.** `cell_coords` emits seven
    (`vol, trend, mtf, rngpos, comp, persist, session`). `sub_xvol_pullback` is depth-4 and
    leaves `rngpos`, `comp` and `session` free; `sub_mid_dn_revert` is depth-7 and leaves
    none. These are not invented variables: they are the route's own vocabulary, discretized
    by the route's own bucketisers, and `sub_mid_dn_revert` gates on `rngpos` and `comp` in
    production — so conditioning `sub_xvol_pullback` on them has a production precedent
    inside its own sleeve family.
(b) **The dial LEVEL inside the pinned bucket.** `vol=xhi` is `vr >= 1.6` with no upper
    bound; `trend=up` is `slope50 > 1.5` with no upper bound; `persist=rand` is an open
    interval. A monotone tilt on the level is a conditioning statement that costs **no
    sample at all**, which matters because splitting an 88-trade sleeve is what makes it
    NOT_EVALUABLE (AL §4: n 56 -> no p at all). A level tilt is therefore routed at SIZING,
    not at admission, and the direction of each is pre-declared below.

`asia_pdl_fade` is not a substrate cell — it gates on the Asian session and a
sweep-and-reclaim only — so all four dials are genuinely free for it, and its 2,827 trades
give them resolution. It is the one sleeve here where the commission's question is askable as
posed.

R0 / THE POPULATION AXIS AND THE COST BAND, WHICH IS NOT OPTIONAL HERE
---------------------------------------------------------------------
Wave-10 agreement §2-4: the population rule is undecided, so every population-sensitive
figure is published on **both** `era_class == RECORDED` and the model's own `decidable`, plus
ALL_ERAS as the unrestricted base. The cost band travels on every arm.

**And the band is a first-class axis in this file because the two artifacts it builds on are
at a band this file's first run was not.** `al_asia_pdl_frontier.py:104-106` and
`am_submid_reclock.py:457/:528` set no `spread_band`, so every figure in
`AL_ASIA_PDL_FRONTIER_V1.json` and `SUBMID_RECLOCK_V1.json` is at `spec.py:82`'s
**flat_37_day_snapshot** — the 37-day tick measurement charged as a constant to every era.
This file therefore runs each cell at BOTH `flat` (the comparator, which must reproduce AL's
and AM's published numbers exactly) and `mid` (the banded arm), and the difference is large
enough on one sleeve to change its sign. AG's rule — a cell winning only at the flat snapshot
has not been shown to win — is what makes that comparison load-bearing rather than decorative.

Offline, pure, no broker import, no config edit.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import importlib.util
import json
import math
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.primitives import atr14, autocorr, vol_ratio  # noqa: E402
from src.components.ultimate_book.sleeves import substrate as SUB  # noqa: E402
from src.components.ultimate_book.sleeves import substrate_engine as SE  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
    measured_n_trials,
)
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import stats as S  # noqa: E402

HERE = Path(__file__).resolve().parent
AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
AA_DIR = AUD / "phase6/receipts"
AD_DIR = AUD / "phase7/receipts"
AL_DIR = AUD / "phase9/receipts"
DECL = HERE / "CANDIDATE_FAMILY_V3.json"
OUT = HERE / "REGIME_CONDITIONING_V1.json"

SERVER = "FTMO-Server3"
ACCOUNT = "FTMO"
BAND = "mid"

#: (label, `spread_band` value, populations). `flat` is `spec.py:82`'s flat_37_day_snapshot and
#: is the arm that reproduces AL's and AM's published figures; restricting the population while
#: pricing flat would be an arm nobody has published, so `flat` runs on ALL_ERAS only.
BAND_ARMS: tuple[tuple[str, str | None, tuple[str, ...]], ...] = (
    ("flat", None, ("ALL_ERAS",)),
    ("mid", "mid", ("ALL_ERAS", "RECORDED", "DECIDABLE")),
)
#: The AG envelope, run on the best cell per (sleeve, exit) only, on RECORDED.
ENVELOPE_BANDS = ("low", "high")

def repro_targets() -> dict:
    """AL's and AM's published figures READ FROM THEIR ARTIFACTS, never transcribed.

    Transcribing a rounded number out of a result doc and then declaring a 1e-5 delta a
    reproduction failure is a self-inflicted wound: AM's prose rounds +0.21048922664553704 to
    "+0.2105". Every target below is the artifact's own full-precision field, so the control is
    exact or it is a real disagreement.
    """
    al = json.loads((AL_DIR / "AL_ASIA_PDL_FRONTIER_V1.json").read_text())
    am = json.loads((AL_DIR / "SUBMID_RECLOCK_V1.json").read_text())
    out = {}
    for cell, gname in (("stop_1x_tgt_native_ts_none", "asia_pdl_fade|as_walked|ungated"),
                        ("stop_2.5x_tgt_native_ts_none",
                         "asia_pdl_fade|stop_2.5x_tgt_native_ts_none|ungated")):
        c = al["cells"][cell]
        out[gname] = {
            "source": f"AL_ASIA_PDL_FRONTIER_V1.json cells[{cell!r}]",
            "pooled_oos_mean_r": c.get("pooled_oos_mean_r"), "p_raw": c.get("p_raw"),
            "n_trades": c.get("n_trades"),
        }
    # AM's own re-clock artifact. Located by search rather than by a guessed key, and it fails
    # LOUDLY if the shape moved -- AL §8.2's silent-null failure mode is the one to avoid here.
    found = None
    stack = [("", am)]
    while stack and found is None:
        path, node = stack.pop()
        if isinstance(node, dict):
            if (node.get("n_trades") == 533 and node.get("p_raw") is not None
                    and node.get("pooled_oos_mean_r") is not None):
                found = (path, node)
                break
            for k, v in node.items():
                stack.append((f"{path}.{k}", v))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                stack.append((f"{path}[{i}]", v))
    if found is None:
        raise SystemExit(
            "REFUSING: could not locate AM's n=533 server_repaired gate row in "
            "SUBMID_RECLOCK_V1.json by search. The reproduction control is load-bearing for "
            "every mid-band claim in this file, so a missing target must stop the run rather "
            "than silently publish `null`.")
    path, node = found
    out["sub_mid_dn_revert|as_walked|ungated"] = {
        "source": f"SUBMID_RECLOCK_V1.json{path}",
        "pooled_oos_mean_r": node.get("pooled_oos_mean_r"), "p_raw": node.get("p_raw"),
        "n_trades": node.get("n_trades"),
    }
    return out

XVOL = "sub_xvol_pullback"
BTC_SLEEVE = "mx_btcusd_d1_donchian_20_breakout"
MIDDN = "sub_mid_dn_revert"
ASIA = "asia_pdl_fade"

#: The five dials, as AB published them (`AB_REGIME_DIALS_V1.json` / `regime_spine/dials.py`).
#: `SURFACE_OPEN` is 1 by construction on any bar a sleeve fired on, so it is carried as a
#: control rather than as a conditioning axis.
DIAL_SOURCE = {
    "VOL_REGIME": "regime_spine/dials.py:139-144 -> state.BarFrame.vr_raw == primitives.vol_ratio",
    "PERSISTENCE": "regime_spine/dials.py:148-154 -> state.BarFrame.ac60_prim == primitives.autocorr(...,60)",
    "HORIZON_CONFLICT": "regime_spine/dials.py:96-111 `_horizon_conflict` -- its own docstring: "
                        "\"substrate_engine's mtf_align, by hand\"",
    "TREND_STATE": "regime_spine/dials.py:170-177 -> state.BarFrame.slope50",
    "SURFACE_OPEN": "regime_spine/dials.py:118-120 -- 1 whenever the deepest warmup is met",
}

#: AB's band edges, implemented exactly as `af_repairs.bucket` does (which is itself
#: `substrate_engine`'s `_bucket_*` for the three continuous dials). Session AF chose that
#: implementation for fidelity to the engine and it is kept here for comparability: a second
#: bucketiser would make AO's cells incomparable to AF's and AH's.
BUCKET_NOTE = (
    "AB's `bands` dict {lo:0.85, mid:1.15, hi:1.6, xhi:2.0} is a mix of cut points and one "
    "representative value, not a partition: `xhi` is the open-ended top bucket and 2.0 is a "
    "representative extreme, not a cut. The cut implemented here is 1.6, which is "
    "`substrate_engine._bucket_vr` and `af_repairs.bucket` verbatim. Read `xhi` as vr >= 1.6."
)


def bucket(name: str, v):
    """`af_repairs.bucket` verbatim, extended to HORIZON_CONFLICT and SURFACE_OPEN."""
    if v is None:
        return "na"
    if name == "VOL_REGIME":
        return ("lo" if v < 0.85 else "mid" if v < 1.15 else "hi" if v < 1.60 else "xhi")
    if name == "PERSISTENCE":
        return "revert" if v < -0.10 else ("trend" if v >= 0.10 else "random")
    if name == "TREND_STATE":
        return "dn" if v < -1.5 else ("up" if v >= 1.5 else "flat")
    if name == "HORIZON_CONFLICT":
        return {-1: "conflict", 0: "neutral", 1: "aligned"}.get(int(v), "na")
    if name == "SURFACE_OPEN":
        return "open" if v else "closed"
    raise ValueError(name)


# =====================================================================================
# THE PRE-DECLARATION. Written before any number in this file was computed, and it is the
# thing that makes §2's result worth reporting whichever way it comes out.
# =====================================================================================

#: One conditioning CELL per sleeve-mechanism, on a coordinate the sleeve's own rule leaves
#: free, chosen from what the mechanism IS and from a production precedent where one exists.
#: A cell that fails is reported as a failure; the alternative -- picking the best of an
#: enumeration and calling it the mechanism's regime -- is what AH §4.3 and AF §8 item 2
#: exist to prevent.
PRE_DECLARED_CELLS = {
    XVOL: [
        {"coord": "rngpos", "want": "mid",
         "why": ("`sub_xvol_pullback` buys a PULLBACK inside an uptrend it has already "
                 "confirmed (trend=up, mtf=conflict). A pullback that is real has come off "
                 "the high, so `rngpos=high` (close in the top quartile of the 50-bar range) "
                 "is the setup not having happened yet; a pullback that has broken the host "
                 "trend is `rngpos=low`. The mechanism wants the middle, and its own sibling "
                 "cell already gates there: `sub_mid_dn_revert` carries rngpos=mid "
                 "(substrate.py:78). Production precedent inside the same cell family."),
         "precedent": "substrate.py:78 MIDDN_CONDS rngpos=mid"},
        {"coord": "comp", "want": "coil",
         "why": ("the trade is a pullback IN an expansion: `vol=xhi` says the 14-bar ATR is "
                 ">= 1.6x its own 100-bar mean, and the pullback itself is the range "
                 "CONTRACTING inside that expansion before the trend resumes. `comp` is the "
                 "5-bar true range over the 20-bar true range (substrate_engine.py:157-159), "
                 "so contraction is `comp < 0.7` = `coil`. `comp=expand` would be the "
                 "expansion still running, i.e. no pullback to buy."),
         "precedent": "substrate.py:78 MIDDN_CONDS comp=norm -- the sibling gates this "
                      "coordinate too, at a different bucket"},
    ],
    ASIA: [
        {"coord": "PERSISTENCE", "want": "revert",
         "why": ("a liquidity-sweep REVERSAL: price pierces the prior day's low and closes "
                 "back above it, and the trade is that the break was false "
                 "(asia_pdl_fade.py:16-21). It needs the tape to revert, not to continue. "
                 "This is Session AH's own pre-declaration for a reversal rule, verbatim "
                 "(`ah_conditioning.py:93-95`, `volume_surge_reversal` -> PERSISTENCE/revert), "
                 "and AB's `revert` band (< -0.10) is its published home."),
         "precedent": "ah_conditioning.py:90-95 -- the same bucket for the same mechanism class"},
    ],
    MIDDN: [
        # Declared as an ABSENCE, and the absence is the finding. sub_mid_dn_revert is a
        # depth-7 cell: `cell_coords` emits exactly seven coordinates and MIDDN_CONDS pins all
        # seven. There is no free coordinate to pre-declare a cell on, so no cell is declared
        # and §2 reports that rather than inventing one.
    ],
}

#: The LEVEL directions, inside whatever bucket the cell already pins. Each is the sign of the
#: Spearman rank correlation between the dial's raw value and the trade's net R that the
#: MECHANISM predicts. These cost no sample, so they are measured on the full population and
#: routed at SIZING (the conviction weight), never as an admission filter.
PRE_DECLARED_LEVELS = {
    XVOL: {
        "vr": (+1, "vol=xhi is vr >= 1.6 with no ceiling. A deeper volatility expansion "
                   "leaves more room for the resumption the sleeve buys, and its 3R target "
                   "is set in ATR units, so a wider expansion is a nearer target in price "
                   "terms relative to the swing that produced it."),
        "slope50": (+1, "trend=up is slope50 > 1.5 with no ceiling. The sleeve buys a "
                        "pullback in a host trend; a stronger host trend is a better thing "
                        "to buy a pullback in."),
        "ac60": (+1, "persist=rand is the OPEN interval (-0.10, 0.10). The trade is a "
                     "continuation, so inside that band the less mean-reverting half of it "
                     "should be the better half."),
    },
    MIDDN: {
        "ac60": (-1, "persist=revert is ac60 <= -0.10 with no floor. The trade IS the "
                     "reversion, so a more strongly mean-reverting tape should be better; "
                     "more negative == better means a NEGATIVE rank correlation."),
        "slope50": (-1, "trend=dn is slope50 < -1.5 with no floor, and the sleeve buys LONG. "
                        "A larger down-displacement is more to revert, so more negative "
                        "should be better -- a NEGATIVE rank correlation."),
        "vr": (-1, "vol=mid is [0.85, 1.15). A mean-reversion entry in the calmer half of "
                   "its own band faces a smaller adverse excursion against a fixed 1.0-ATR "
                   "stop, so calmer should be better."),
    },
    ASIA: {
        "PERSISTENCE": (-1, "the reversal wants a mean-reverting tape, so more negative "
                            "autocorrelation should be better."),
    },
}

#: The exits each sleeve is conditioned AT. Both the as-walked control and the banked repair,
#: because AK's warning is that the mean and the p must not be quoted from different cells.
BANKED_EXIT = {
    XVOL: ("target_4R", "AL §2 / AK: +1.3651 R/day at p 0.0080 on RECORDED, n 85 -- the "
                        "armed sleeve's best measured cell anywhere"),
    ASIA: ("stop_2.5x_tgt_native_ts_none", "AK's winner, confirmed by AL's 120-distinct-cell "
                                           "cross to 17 digits: +0.08463 R/day, 5/5 OOS folds"),
    MIDDN: ("as_walked", "AM's re-clocked population IS the repair; no exit cell has been "
                         "gated on it, so as_walked is the cell of record"),
}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# =====================================================================================
# state at a decision bar


class StateCache:
    """`substrate_engine.compute_state` + AB's dials at any (broker_symbol, tf, iso).

    One cache, three consumers. The dials are computed from AB's OWN functions
    (`primitives.vol_ratio` / `primitives.autocorr`) and the substrate coordinates from
    `substrate_engine.compute_state`, so §1's parity check compares two independent
    implementations rather than one implementation with itself.
    """

    def __init__(self, series: dict, index: dict):
        self.series = series
        self.index = index
        self._atrs: dict = {}
        self._cache: dict = {}

    def atrs(self, key):
        if key not in self._atrs:
            bars, _ = self.series[key]
            self._atrs[key] = [atr14(bars, k) for k in range(len(bars))]
        return self._atrs[key]

    def at(self, symbol: str, tf: int, iso: str):
        ck = (symbol, tf, iso)
        if ck in self._cache:
            return self._cache[ck]
        key = (symbol, tf)
        out = None
        if key in self.index:
            i = self.index[key].get(dt.datetime.fromisoformat(iso))
            bars, times = self.series[key]
            if i is not None and i >= 209:
                st = SE.compute_state(bars, i, None)
                if st is not None:
                    a = self.atrs(key)
                    out = {
                        # substrate coordinates (the route's own vocabulary)
                        "vr": st["vr"], "slope20": st["slope20"], "slope50": st["slope50"],
                        "slope100": st["slope100"], "mtf_align": st["mtf_align"],
                        "rng_pos": st["rng_pos"], "compression": st["compression"],
                        "ac60": st["ac60"],
                        "coords": SE.cell_coords(st),
                        # AB's dials, from AB's own functions
                        "VOL_REGIME": vol_ratio(a, i),
                        "PERSISTENCE": autocorr(bars, i, 60),
                        "TREND_STATE": st["slope50"],
                        "HORIZON_CONFLICT": st["mtf_align"],
                        "SURFACE_OPEN": 1,
                        "bar_index": i,
                    }
        self._cache[ck] = out
        return out


def label(rows: list[dict], sc: StateCache) -> tuple[list[dict], dict]:
    """Attach state to each trade at ITS OWN decision bar. Leak-free by construction."""
    out, miss = [], collections.Counter()
    for r in rows:
        st = sc.at(r["symbol"], int(r["timeframe"]), r["decision_bar_iso"])
        if st is None:
            miss["no_state"] += 1
            continue
        out.append(dict(r, _st=st))
    return out, dict(miss)


# =====================================================================================
# §1 the pinning proof


def pinning(labelled: dict) -> dict:
    """Per sleeve, how many DISTINCT buckets each AB dial takes over its own trades.

    1 == the dial is a firing condition of the sleeve and a bucket gate on it is the identity
    filter. Reported for every sleeve including the one where it is not 1, because the
    contrast is the evidence.
    """
    out = {}
    for sleeve, rows in sorted(labelled.items()):
        per = {}
        for d in DIAL_SOURCE:
            c = collections.Counter(bucket(d, r["_st"][d]) for r in rows)
            per[d] = {"n_distinct_buckets": len(c), "counts": dict(sorted(c.items())),
                      "pinned": len(c) == 1,
                      "source": DIAL_SOURCE[d]}
        coords = collections.Counter()
        free = {}
        for name in ("vol", "trend", "mtf", "rngpos", "comp", "persist"):
            c = collections.Counter(r["_st"]["coords"].get(name) for r in rows)
            free[name] = {"n_distinct": len(c), "counts": dict(sorted(c.items())),
                          "free": len(c) > 1}
        coords.update()
        out[sleeve] = {
            "n_trades_labelled": len(rows),
            "dials": per,
            "n_dials_pinned": sum(1 for v in per.values() if v["pinned"]),
            "substrate_coords": free,
            "n_substrate_coords_free": sum(1 for v in free.values() if v["free"]),
            "bucket_note": BUCKET_NOTE,
        }
    return out


def dial_parity(labelled: dict) -> dict:
    """Are AB's dial functions and the substrate's coordinates the SAME quantity?

    `primitives.autocorr` uses `statistics.mean` and `substrate_engine._ac` uses `sum/n`;
    `dials.py:97` claims `_horizon_conflict` IS `mtf_align`. Both are checked numerically
    rather than read off the source, because §1's whole claim rests on the identification and
    AL §8.5 is the case where a two-data-point check could not settle the mechanism it
    asserted.
    """
    out = {}
    for sleeve, rows in sorted(labelled.items()):
        dmax = {"PERSISTENCE_vs_ac60": 0.0, "TREND_STATE_vs_slope50": 0.0,
                "VOL_REGIME_vs_vr": 0.0}
        bad = collections.Counter()
        for r in rows:
            st = r["_st"]
            for lbl, a, b in (("PERSISTENCE_vs_ac60", st["PERSISTENCE"], st["ac60"]),
                              ("TREND_STATE_vs_slope50", st["TREND_STATE"], st["slope50"]),
                              ("VOL_REGIME_vs_vr", st["VOL_REGIME"], st["vr"])):
                if a is None or b is None:
                    bad[lbl + "_none"] += 1
                    continue
                dmax[lbl] = max(dmax[lbl], abs(a - b))
            if int(st["HORIZON_CONFLICT"]) != int(st["mtf_align"]):
                bad["HORIZON_CONFLICT_vs_mtf_align"] += 1
            # the bucket is what a gate reads, so bucket agreement is the decisive check
            if bucket("PERSISTENCE", st["PERSISTENCE"]) != {
                    "trend": "trend", "revert": "revert", "rand": "random"}[
                    st["coords"]["persist"]]:
                bad["PERSISTENCE_bucket_disagrees_with_coords_persist"] += 1
            if bucket("VOL_REGIME", st["VOL_REGIME"]) != st["coords"]["vol"]:
                bad["VOL_REGIME_bucket_disagrees_with_coords_vol"] += 1
            if bucket("TREND_STATE", st["TREND_STATE"]) != {
                    "up": "up", "dn": "dn", "flat": "flat"}[st["coords"]["trend"]]:
                bad["TREND_STATE_bucket_disagrees_with_coords_trend"] += 1
        out[sleeve] = {"n": len(rows), "max_abs_delta": {k: v for k, v in dmax.items()},
                       "disagreements": dict(bad),
                       "identical_to_1e-12": all(v < 1e-12 for v in dmax.values()) and not bad}
    return out


# =====================================================================================
# levels


def _spearman(pairs, *, n_perm: int = 20000, seed: int = 20260730) -> dict:
    """Rank correlation with BOTH a normal-approximation p and a permutation p.

    The normal approximation on the t-transform is what a reader expects; at n = 78 with a
    day-clustered series it is also the one that can be wrong in the permissive direction. The
    permutation null (shuffle the outcome against the dial) needs no distributional assumption
    and is the figure quoted. It is a per-TRADE null, not the gate's day-blocked one -- stated
    rather than glossed, because a level tilt is a per-trade sizing statement.
    """
    import random

    n = len(pairs)
    if n < 10:
        return {"n": n, "rho": None, "p_two_sided_normal_approx": None,
                "p_two_sided_permutation": None,
                "why_none": "fewer than 10 priced trades -- a rank correlation here would be noise"}
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]

    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1.0
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r

    rx, ry = rank(xs), rank(ys)

    def _rho(a, b):
        ma, mb = statistics.mean(a), statistics.mean(b)
        num = sum((u - ma) * (v - mb) for u, v in zip(a, b))
        den = math.sqrt(sum((u - ma) ** 2 for u in a) * sum((v - mb) ** 2 for v in b))
        return (num / den) if den else None

    rho = _rho(rx, ry)
    p = None
    if rho is not None and abs(rho) < 1:
        t = rho * math.sqrt((n - 2) / (1 - rho * rho))
        p = 2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2))))
    pp = None
    if rho is not None:
        rng = random.Random(seed)
        shuf = list(ry)
        hits = 0
        for _ in range(n_perm):
            rng.shuffle(shuf)
            r2 = _rho(rx, shuf)
            hits += int(r2 is not None and abs(r2) >= abs(rho))
        pp = (hits + 1) / (n_perm + 1)
    return {"n": n, "rho": round(rho, 5) if rho is not None else None,
            "p_two_sided_normal_approx": round(p, 5) if p is not None else None,
            "p_two_sided_permutation": round(pp, 6) if pp is not None else None,
            "n_perm": n_perm,
            "permutation_null": ("the outcome series shuffled against the dial series; a "
                                 "per-TRADE null, not the gate's day-blocked one, because a "
                                 "level tilt is a per-trade sizing statement")}


def levels(labelled: dict, netr: dict) -> dict:
    """The pre-declared level directions, measured on the FULL population (no split).

    `netr` maps trade key -> net R so the correlation is against the quantity a sizing dial
    would be paid in, not against gross.
    """
    out = {}
    for sleeve, decl in sorted(PRE_DECLARED_LEVELS.items()):
        rows = labelled.get(sleeve) or []
        per = {}
        for field, (want, why) in sorted(decl.items()):
            pairs, terts = [], collections.defaultdict(list)
            for r in rows:
                v = r["_st"].get(field)
                nr = netr.get((sleeve, r["symbol"], r["decision_bar_iso"]))
                if v is None or nr is None:
                    continue
                pairs.append((v, nr))
            sp = _spearman(pairs)
            if pairs:
                vals = sorted(p[0] for p in pairs)
                n = len(vals)
                lo_cut, hi_cut = vals[n // 3], vals[2 * n // 3]
                for v, nr in pairs:
                    t = "T1_low" if v <= lo_cut else ("T3_high" if v > hi_cut else "T2_mid")
                    terts[t].append(nr)
            per[field] = {
                "pre_declared_sign": want, "why": why, **sp,
                "sign_agrees_with_pre_declaration": (
                    None if sp["rho"] is None else bool(
                        (sp["rho"] > 0) == (want > 0))),
                "tertile_mean_net_r": {k: round(statistics.mean(v), 5)
                                       for k, v in sorted(terts.items())},
                "tertile_n": {k: len(v) for k, v in sorted(terts.items())},
                "basis": "net R per trade, broker-true, the gate's own cost engine",
            }
        agree = [v["sign_agrees_with_pre_declaration"] for v in per.values()
                 if v["sign_agrees_with_pre_declaration"] is not None]
        out[sleeve] = {
            "fields": per,
            "n_pre_declared": len(per),
            "n_sign_agrees": sum(1 for a in agree if a),
            "n_scoreable": len(agree),
            "routing": ("a level tilt costs NO sample, so it is a SIZING statement (the "
                        "conviction weight) and never an admission filter. Splitting an "
                        "88-trade sleeve is what makes it NOT_EVALUABLE -- AL §4 measured "
                        "exactly that at n=56."),
        }
    return out


# =====================================================================================
# the gate


_EST_MEMO: dict = {}


def _est(smodel, symbol, entry_utc, band):
    """Memoized `SpreadModel.estimate`. The same (symbol, entry, band) is asked once per cell
    x population arm, which is thousands of repeats on a 2,827-trade sleeve."""
    k = (symbol, entry_utc, band)
    if k not in _EST_MEMO:
        try:
            e = smodel.estimate(symbol, ACCOUNT, entry_utc, band=band)
            _EST_MEMO[k] = (e.era_class, bool(e.decidable))
        except Exception as exc:  # noqa: BLE001
            _EST_MEMO[k] = (f"UNPRICEABLE:{type(exc).__name__}", False)
    return _EST_MEMO[k]


def _restrict(recs: dict, pop: str, smodel, band: str | None = None) -> tuple[dict, dict]:
    """ALL_ERAS / RECORDED / DECIDABLE, on the model's own fields. AL's `restrict`, verbatim.

    `band` is threaded through because `estimate`'s `decidable` is a property of the band the
    estimate was taken at, so restricting on `decidable` at one band and then PRICING at
    another would be two different populations wearing one name. When the arm prices flat there
    is no band to restrict at, and the flat arm is deliberately ALL_ERAS-only for that reason.
    """
    if pop == "ALL_ERAS":
        return recs, {}
    if band is None:
        raise ValueError(f"population {pop!r} needs a band; the flat arm is ALL_ERAS-only")
    keep, mix = {}, {}
    for s, rs in sorted(recs.items()):
        cls, rows = collections.Counter(), []
        for r in rs:
            era_class, decidable = _est(smodel, r.symbol, r.entry_utc, band)
            if era_class.startswith("UNPRICEABLE:"):
                cls[era_class] += 1
                continue
            ok = (era_class == "RECORDED") if pop == "RECORDED" else decidable
            cls[f"{era_class}|{'decidable' if decidable else 'undecidable'}"] += 1
            if ok:
                rows.append(r)
        mix[s] = {"n_total": len(rs), "n_kept": len(rows), "mix": dict(sorted(cls.items())),
                  "kept_frac": round(len(rows) / len(rs), 4) if rs else None}
        if rows:
            keep[s] = rows
    return keep, mix


def row_of(sv) -> dict:
    g = sv.gates
    tel = sv.telemetry or {}
    dep = tel.get("dependence") or {}
    fl = tel.get("p_floor") or {}
    if sv.p_raw is not None and not dep:
        raise SystemExit(
            "REFUSING: a sleeve reached a null but `telemetry['dependence']` is absent, so "
            "the power accounting would publish nulls in the block whose whole subject is "
            "power. Check gate.py:746-753.")
    return {
        "verdict": sv.verdict.value, "n_trades": sv.n_trades,
        "pooled_oos_mean_r": sv.pooled_oos_mean_r,
        "oos_mean_r_per_trade": g.get("expectancy", {}).get("oos_mean_r_per_trade"),
        "p_raw": sv.p_raw, "q_value": sv.q_value,
        "failing_core_gates": [x for x in ("expectancy", "lifetime", "stability", "robustness",
                                           "significance") if not g.get(x, {}).get("pass")],
        "n_folds_evaluable": g.get("sample", {}).get("n_folds_evaluable"),
        "thin_fold_frac": g.get("sample", {}).get("thin_fold_frac"),
        "oos_positive_fold_frac": g.get("stability", {}).get("oos_positive_fold_frac"),
        "fold_means": g.get("stability", {}).get("fold_means"),
        "drop_best_retention": g.get("robustness", {}).get("retention"),
        "coverage_frac": g.get("cost_coverage", {}).get("coverage_frac"),
        # THE POWER TERMS. The null is a block sign-flip on the daily OOS series, so the n
        # that buys resolution is BLOCKS -- `telemetry.p_floor.n_blocks` -- not `n_trades`.
        # `n_oos_days` lives at `telemetry.dependence` (`gate.py:746-753`), never in
        # `gates.significance`; the first version of this function guessed the latter and
        # published `None`, which is AL §8.2's silent-null failure mode caught by its own
        # print. It now falls back LOUDLY.
        "n_oos_days": dep.get("n_oos_days"),
        "effective_n_oos_days": dep.get("effective_n_oos_days"),
        "block_days_used": dep.get("block_days_used"),
        "lag1_autocorr_oos_days": dep.get("lag1_autocorr_oos_days"),
        "n_blocks": fl.get("n_blocks"),
        "p_floor": fl.get("p_floor"),
        "p_floor_binds": g.get("significance", {}).get("p_floor_binds"),
        # THE RESOLUTION CHECK, and it is the one figure that decides whether a small p is
        # evidence or an artefact. `perm_p_floor` (`stats.py:157-168`) gives the smallest p a
        # B-block sign flip can attain: `(1 + n_perm*2**-B)/(n_perm+1)`. `gate.py:851-857`
        # refuses only when `p_raw <= p_floor`; a p ONE resolution step above the floor passes
        # silently, and AO's pair-admitting cell sits at 1.048x. Reported on every arm.
        "p_floor_headroom": ((sv.p_raw / fl["p_floor"])
                             if (sv.p_raw is not None and fl.get("p_floor")) else None),
        "first_reason": (sv.reasons[0][:260] if sv.reasons else None),
    }


def main() -> dict:  # noqa: PLR0912, PLR0915
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true",
                    help="skip the DECIDABLE population (the slow per-trade model call)")
    args = ap.parse_args()
    t0 = time.time()

    AA = _load(AA_DIR / "aa_estate_walk.py", "ao_aa_walk")
    AD = _load(AD_DIR / "ad_exit_sweep.py", "ao_ad_sweep")
    from src.costs.spread_model import load_spread_model

    smodel = load_spread_model()
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AO")
    fam = CF.load_candidate_family(DECL)
    m_all = fam.effective_size("CANDIDATE_BOOK_V1")
    print(f"declared family: all_declared {m_all}, "
          f"looks_taken {fam.effective_size('CANDIDATE_BOOK_V1', CF.LOOKS_TAKEN)}")

    raw = json.load(gzip.open(AA_DIR / "AA_ESTATE_TRADES.json.gz", "rt"))
    base_rows = {s: list(r) for s, r in raw["trades"].items()}
    am = json.load(gzip.open(AL_DIR / "AM_SUBMID_TRADES.json.gz", "rt"))
    middn_reclocked = list(am["trades"]["server_repaired"])
    for r in middn_reclocked:
        r.setdefault("sleeve", MIDDN)
    costs = AA.load_broker_true_costs(AA.COSTS_V1_1)
    series, index, _res = AD.load_bars()
    rule = AD.resolve_rule(SERVER)
    sc = StateCache(series, index)
    print(f"loaded {len(series)} bar series in {time.time()-t0:.0f}s")

    # ---- populations, per sleeve, at the as-walked labelling -----------------------------
    pops = {XVOL: base_rows[XVOL], ASIA: base_rows[ASIA], MIDDN: middn_reclocked}
    labelled, miss = {}, {}
    for s, rows in pops.items():
        labelled[s], miss[s] = label(rows, sc)
        print(f"  {s:20s} {len(rows):5d} trades -> {len(labelled[s]):5d} labelled "
              f"({miss[s] or 'no misses'})")

    out = {
        "schema": "gtos.wave10.ao.regime_conditioning.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "session": "AO", "blocks": "B1300-B1349",
        "question": ("does regime conditioning on Session AB's published dials move any of the "
                     "three sleeves whose named next lever is REGIME_GATE_OR_PARK -- and on "
                     "the two substrate sleeves, is the question even askable?"),
        "populations_published": ["ALL_ERAS", "RECORDED", "DECIDABLE"],
        "population_rule_status": (
            "UNDECIDED. Wave-10 agreement §2-4: publish every population-sensitive figure on "
            "both `era_class == RECORDED` and the model's own `decidable` until AN's package "
            "lands and Borhen ratifies. Neither is treated as the answer here."),
        "cost_band": BAND,
        "declared_family": {
            "path": str(DECL.relative_to(REPO)), "sha256": fam.sha256,
            "all_declared": m_all,
            "membership_sha256": fam.membership_of("CANDIDATE_BOOK_V1"),
            "bh_rank_1_at_alpha_0.10": round(0.10 / m_all, 6),
            "bh_rank_2_at_alpha_0.10": round(0.20 / m_all, 6),
        },
        "pre_declared": {
            "cells": PRE_DECLARED_CELLS,
            "levels": {s: {f: {"sign": v[0], "why": v[1]} for f, v in d.items()}
                       for s, d in PRE_DECLARED_LEVELS.items()},
            "discipline": ("AH §4.3: one bucket per mechanism, declared in source before any "
                           "result in this file was computed, from what the mechanism IS plus "
                           "a production precedent where one exists. Everything else in this "
                           "artifact is stamped `enumerated`."),
        },
        "banked_exit": {s: {"cell": c, "why": w} for s, (c, w) in BANKED_EXIT.items()},
        "trade_population_sources": {
            XVOL: "AA_ESTATE_TRADES.json.gz -- AA's own 88, the production cell",
            ASIA: "AA_ESTATE_TRADES.json.gz -- AA's own 2,827",
            MIDDN: ("AM_SUBMID_TRADES.json.gz `server_repaired` -- AM's RE-CLOCKED 533, per "
                    "the commission. AA's 503 describe the mis-clocked population "
                    "(AM §1.2)."),
        },
        "labelling_misses": miss,
    }

    # ---- §1 the pinning proof, and the parity that licenses it ---------------------------
    out["pinning"] = pinning(labelled)
    out["dial_parity"] = dial_parity(labelled)
    print("\nPINNING (distinct AB-dial buckets over each sleeve's own trades):")
    for s, v in sorted(out["pinning"].items()):
        print(f"  {s:20s} n={v['n_trades_labelled']:5d} "
              f"dials_pinned={v['n_dials_pinned']}/5 "
              f"free_substrate_coords={v['n_substrate_coords_free']}/6")
        for d, dv in v["dials"].items():
            print(f"      {d:18s} {dv['n_distinct_buckets']} {dv['counts']}")

    # ---- control: AL's own recorded state must reproduce for the 88 -----------------------
    st_al = json.load(gzip.open(AL_DIR / "AL_XVOL_REACHABLE_STATE_V1.json.gz", "rt"))["rows"]
    n_ok, n_chk, dmax = 0, 0, 0.0
    for r in labelled[XVOL]:
        k = f"{r['symbol_canonical']}|{r['decision_bar_iso']}"
        a = st_al.get(k)
        if a is None:
            continue
        n_chk += 1
        d = max(abs(a["vr"] - r["_st"]["vr"]), abs(a["ac60"] - r["_st"]["ac60"]),
                abs(a["rng_pos"] - r["_st"]["rng_pos"]),
                abs(a["compression"] - r["_st"]["compression"]))
        dmax = max(dmax, d)
        n_ok += int(d < 1e-12 and a["mtf_align"] == r["_st"]["mtf_align"])
    out["controls"] = {
        "state_reproduces_AL_recorded": {
            "question": ("does this file's state, computed from the archive at each decision "
                         "bar, reproduce AL's own recorded `AL_XVOL_REACHABLE_STATE_V1` "
                         "state on the 88 production trades?"),
            "n_checked": n_chk, "n_identical_to_1e-12": n_ok, "max_abs_delta": dmax,
            "identical": n_chk == len(labelled[XVOL]) == n_ok,
        },
    }
    print(f"\nCONTROL vs AL recorded state: {n_ok}/{n_chk} identical to 1e-12 "
          f"(max delta {dmax:.2e})")

    from src.research_infra.walkforward.options import OPTIONS
    allow = dict(AA.allowlist())
    base_opt_name = "B_balanced"

    # ---- levels, on net R from the ungated ALL_ERAS run ----------------------------------
    netr = {}
    for sleeve in (XVOL, ASIA, MIDDN):
        pop_rows = {s: list(r) for s, r in base_rows.items()}
        pop_rows[sleeve] = [{k: v for k, v in r.items() if k != "_st"}
                            for r in labelled[sleeve]]
        recs = {s: AD.to_records(r) for s, r in pop_rows.items()}
        o = OPTIONS[base_opt_name]
        spec = o.with_(spec_id=f"{o.spec_id}_ao_levels",
                       sleeve_symbol_allowlist=allow, spread_band=BAND)
        spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=fam)
        res = run_gate(recs, spec, costs=costs, diagnose=True, server=SERVER)
        # `run_gate(diagnose=True)` keeps the priced population at
        # `GateResult.priced_by_sleeve` (`gate.py:156-159`, `panel.PricedTrade.r_net`).
        # It is NOT in `telemetry["diagnostics"]` -- AL §8.2's failure mode was guessing a
        # key, finding none and writing a silent null, so this falls back LOUDLY.
        priced = res.priced_by_sleeve.get(sleeve) or []
        if not priced:
            raise SystemExit(
                f"REFUSING to publish a level measurement with no net-R source: "
                f"`priced_by_sleeve[{sleeve!r}]` is empty under diagnose=True. A silent null "
                f"in this block would read as 'measured'. Check gate.py:905's kept_priced.")
        n_join, n_unpriced = 0, 0
        for p in priced:
            if p.status != "priced" or p.r_net is None:
                n_unpriced += 1
                continue
            iso = (p.trade.features or {}).get("decision_bar_iso")
            if not iso:
                n_unpriced += 1
                continue
            netr[(sleeve, p.trade.symbol, iso)] = p.r_net
            n_join += 1
        out.setdefault("level_net_r_source", {})[sleeve] = {
            "from": "run_gate(diagnose=True).priced_by_sleeve -> PricedTrade.r_net",
            "n_priced_rows": len(priced), "n_joined": n_join,
            "n_unpriced_or_unkeyed": n_unpriced,
            "n_trades_labelled": len(labelled[sleeve]),
            "spec_sha256": spec.seal(),
            "caveat": ("the gate prices only what survives `coverage_policy`, so a level "
                       "correlation is measured on the PRICED subset and its n is stated "
                       "beside every rho rather than assumed equal to the population."),
        }
    out["levels"] = levels(labelled, netr)
    print("\nLEVELS (pre-declared sign vs measured Spearman on net R):")
    for s, v in sorted(out["levels"].items()):
        print(f"  {s}: {v['n_sign_agrees']}/{v['n_scoreable']} signs agree")
        for f, fv in sorted(v["fields"].items()):
            print(f"      {f:10s} declared {fv['pre_declared_sign']:+d} measured rho "
                  f"{fv['rho']} p_norm {fv.get('p_two_sided_normal_approx')} "
                  f"p_perm {fv.get('p_two_sided_permutation')} "
                  f"tertiles {fv['tertile_mean_net_r']}")

    # ---- the cells to gate ---------------------------------------------------------------
    #  Every cell is (sleeve, exit, filter). The filter is a predicate on the labelled state.
    def coord_pred(coord: str, want: str):
        return lambda r: r["_st"]["coords"].get(coord) == want

    def dial_pred(dial: str, want: str):
        return lambda r: bucket(dial, r["_st"][dial]) == want

    cells: dict[str, list[dict]] = collections.defaultdict(list)
    cells[XVOL].append({"name": "ungated", "basis": "control", "pred": None})
    for d in PRE_DECLARED_CELLS[XVOL]:
        cells[XVOL].append({"name": f"{d['coord']}=={d['want']}", "basis": "pre_declared",
                            "pred": coord_pred(d["coord"], d["want"]), "decl": d})
    # the enumeration: every bucket of the three FREE substrate coordinates
    for coord, buckets in (("rngpos", ("low", "mid", "high")),
                           ("comp", ("coil", "norm", "expand"))):
        for b in buckets:
            nm = f"{coord}=={b}"
            if any(c["name"] == nm for c in cells[XVOL]):
                continue
            cells[XVOL].append({"name": nm, "basis": "enumerated",
                                "pred": coord_pred(coord, b)})

    cells[ASIA].append({"name": "ungated", "basis": "control", "pred": None})
    for d in PRE_DECLARED_CELLS[ASIA]:
        cells[ASIA].append({"name": f"{d['coord']}=={d['want']}", "basis": "pre_declared",
                            "pred": dial_pred(d["coord"], d["want"]), "decl": d})
    for dial, buckets in (("VOL_REGIME", ("lo", "mid", "hi", "xhi")),
                          ("PERSISTENCE", ("revert", "random", "trend")),
                          ("HORIZON_CONFLICT", ("conflict", "neutral", "aligned")),
                          ("TREND_STATE", ("dn", "flat", "up"))):
        for b in buckets:
            nm = f"{dial}=={b}"
            if any(c["name"] == nm for c in cells[ASIA]):
                continue
            cells[ASIA].append({"name": nm, "basis": "enumerated",
                                "pred": dial_pred(dial, b)})

    cells[MIDDN].append({"name": "ungated", "basis": "control", "pred": None})
    # No pre-declared CELL exists: the depth-7 cell pins all six substrate coordinates plus
    # `session`, so there is no free coordinate to declare a bucket on. That absence IS the
    # item-4 answer and it is why `PRE_DECLARED_CELLS[MIDDN]` is empty.

    # ---- the DERIVED level cells ---------------------------------------------------------
    #  The DIRECTION of each was pre-declared in `PRE_DECLARED_LEVELS` before any number; the
    #  CUT was not. So these are stamped `derived_from_pre_declared_level` and are explicitly
    #  NOT admissible in this session -- admitting a cell whose cut was chosen after the level
    #  was measured is the post-hoc curation the ratchet exists to prevent (AH §5.2's handling
    #  of `VOL_REGIME==hi` for nzdjpy: "offered as a map entry rather than a claim"). What they
    #  are for is the NEXT session's pre-declaration, and the bill that would cost is priced.
    def level_pred(field: str, cut: float, above: bool):
        if above:
            return lambda r: (r["_st"].get(field) is not None and r["_st"][field] >= cut)
        return lambda r: (r["_st"].get(field) is not None and r["_st"][field] < cut)

    for sleeve, fields in ((XVOL, ("vr", "slope50", "ac60")),
                           (MIDDN, ("ac60", "slope50", "vr"))):
        rows_here = labelled[sleeve]
        want = PRE_DECLARED_LEVELS[sleeve]
        for f in fields:
            vals = sorted(r["_st"][f] for r in rows_here if r["_st"].get(f) is not None)
            if not vals:
                continue
            med = vals[len(vals) // 2]
            sign = want[f][0]
            # the half the PRE-DECLARED direction says should be the better one
            above = sign > 0
            cells[sleeve].append({
                "name": f"{f}{'>=' if above else '<'}median({med:.4f})",
                "basis": "derived_from_pre_declared_level",
                "pred": level_pred(f, med, above),
                "decl": {"field": f, "pre_declared_sign": sign, "cut": med,
                         "cut_basis": "the population's own median -- POST HOC",
                         "why": want[f][1],
                         "admissible": False,
                         "why_not_admissible": (
                             "the direction was pre-declared, the CUT was not. A cell whose "
                             "cut is chosen after the level is measured is not a prospective "
                             "hypothesis and is not declared in CANDIDATE_FAMILY_V3. Routed "
                             "as a pre-declaration for the next session with its price.")},
            })
    #  ---- the MECHANISM cuts, which are the pre-declared directions' own natural boundaries --
    #  A median is a property of the sample. These are not: each is the boundary the
    #  PRE-DECLARED direction implies, read off AB's published band dict rather than off the
    #  data. `ac60 >= 0` is literally "the less mean-reverting half" -- the exact phrase
    #  `PRE_DECLARED_LEVELS[XVOL]["ac60"]` uses -- and AB publishes `random: 0.0` as that
    #  boundary. `vr < 1.0` is "the calmer half" for a mean-reversion entry, and 1.0 is where
    #  ATR equals its own 100-bar mean, i.e. the definitional centre of `vol=mid`.
    #  **They are still NOT admissible here**, and the reason is procedural rather than
    #  statistical: they are not members of CANDIDATE_FAMILY_V3, which was written and committed
    #  before any gate ran. A cell that is not in the prospective declaration cannot be admitted
    #  by this session however principled its cut, and pretending otherwise would make the
    #  declaration decorative. What they are is a MUCH cheaper prescription than a median split,
    #  because a cut nobody read off the outcome is one a later session can declare honestly.
    cells[XVOL].append({
        "name": "ac60>=0.0_AB_random_band_centre",
        "basis": "pre_declared_direction_at_the_mechanism_cut",
        "pred": level_pred("ac60", 0.0, True),
        "decl": {"field": "ac60", "pre_declared_sign": +1, "cut": 0.0,
                 "cut_basis": ("the sign boundary of the pre-declared direction itself. "
                               "`PRE_DECLARED_LEVELS[XVOL]['ac60']` says 'the less "
                               "mean-reverting half', and zero autocorrelation IS that "
                               "boundary; AB publishes `random: 0.0` as the same point "
                               "(`regime_spine/dials.py:153`). Not a property of the sample."),
                 "why": PRE_DECLARED_LEVELS[XVOL]["ac60"][1],
                 "admissible": False,
                 "why_not_admissible": (
                     "not a member of CANDIDATE_FAMILY_V3, which was committed before any gate "
                     "ran (commit 84e39021b). A cell outside the prospective declaration is not "
                     "admissible by this session at any p, and it was RUN after the median cell "
                     "on the same axis -- so a reader should discount it as 'one of two cut "
                     "rules tried', which `mechanism_cut_bill` prices."),
                 "sequence_disclosure": ("the median cell on this axis was gated FIRST and this "
                                         "cut was added after seeing it. The DIRECTION and the "
                                         "AXIS were both pre-declared; the choice to try a "
                                         "second cut rule was not.")},
    })
    cells[MIDDN].append({
        "name": "vr<1.0_definitional_centre_of_vol_mid",
        "basis": "pre_declared_direction_at_the_mechanism_cut",
        "pred": level_pred("vr", 1.0, False),
        "decl": {"field": "vr", "pre_declared_sign": -1, "cut": 1.0,
                 "cut_basis": ("vr = 1.0 is where ATR(14) equals its own 100-bar mean -- the "
                               "definitional centre of the `vol=mid` band [0.85, 1.15) the cell "
                               "pins, and not a property of the sample."),
                 "why": PRE_DECLARED_LEVELS[MIDDN]["vr"][1],
                 "admissible": False,
                 "why_not_admissible": "not a member of CANDIDATE_FAMILY_V3.",
                 "sequence_disclosure": ("the median cell on this axis was gated FIRST. No "
                                         "principled interior cut exists for this sleeve's "
                                         "`slope50` or `ac60` axes -- both bands are unbounded "
                                         "on the side the mechanism prefers -- so those two "
                                         "stay median-cut and post-hoc.")},
    })

    #  One exception worth separating: AB's OWN artifact publishes `xhi: 2.0` as VOL_REGIME's
    #  top band value while every implementation cuts hi/xhi at 1.6 (`_bucket_vr`,
    #  `af_repairs.bucket`). So `vr >= 2.0` is a cut AB NAMED, which makes it a weaker post-hoc
    #  claim than a median. Stamped separately so a reader can weigh it differently.
    cells[XVOL].append({
        "name": "vr>=2.0_AB_published_xhi_band",
        "basis": "derived_from_pre_declared_level",
        "pred": level_pred("vr", 2.0, True),
        "decl": {"field": "vr", "pre_declared_sign": +1, "cut": 2.0,
                 "cut_basis": ("AB_REGIME_DIALS_V1.json's own VOL_REGIME `bands` dict names "
                               "xhi: 2.0. No implementation cuts there -- the engine's "
                               "`_bucket_vr` and `af_repairs.bucket` both cut hi/xhi at 1.6 -- "
                               "so 2.0 is a published-but-unimplemented boundary rather than "
                               "a number this session chose."),
                 "why": PRE_DECLARED_LEVELS[XVOL]["vr"][1],
                 "admissible": False,
                 "why_not_admissible": ("still not in CANDIDATE_FAMILY_V3, so still not "
                                        "admissible here; it is the strongest candidate for "
                                        "the next session's pre-declaration.")},
    })

    # ---- gate every cell x band x population ---------------------------------------------
    arms: dict[str, dict] = {}
    thin: dict[str, dict] = {}
    band_arms = tuple((lb, bv, tuple(p for p in ps if not (args.quick and p == "DECIDABLE")))
                      for lb, bv, ps in BAND_ARMS)

    def gate_one(sleeve, vn, cell, sub, lab_rows, band_label, band_val, pop):
        recs_pop = {s: list(r) for s, r in base_rows.items()}
        recs_pop[sleeve] = [{k: v for k, v in r.items() if k != "_st"} for r in sub]
        recs_all = {s: AD.to_records(r) for s, r in recs_pop.items()}
        recs, mix = _restrict(recs_all, pop, smodel, band_val)
        key = f"{sleeve}|{vn}|{cell['name']}|band={band_label}|{pop}"
        if sleeve not in recs:
            arms[key] = {"sleeve": sleeve, "exit": vn, "cell": cell["name"],
                         "basis": cell["basis"], "population": pop,
                         "spread_band": band_label, "n_in_cell": len(sub),
                         "n_after_restriction": 0,
                         "skipped": "no trade survives the population restriction"}
            return None
        o = OPTIONS[base_opt_name]
        spec = o.with_(spec_id=f"{o.spec_id}_ao_regime", sleeve_symbol_allowlist=allow,
                       **({"spread_band": band_val} if band_val else {}))
        spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=fam)
        res = run_gate(recs, spec, costs=costs, server=SERVER)
        sv = res.verdicts.get(sleeve)
        arm = {
            "sleeve": sleeve, "exit": vn, "cell": cell["name"], "basis": cell["basis"],
            "population": pop, "option": base_opt_name, "alpha": o.alpha,
            "multiplicity": o.multiplicity,
            "spread_band": band_label,
            "spread_band_meaning": ("spec.py:82 flat_37_day_snapshot -- the 37-day tick "
                                    "measurement charged as a constant to every era. This is "
                                    "the basis AL's asia frontier and AM's re-clock published "
                                    "at, and it is the comparator arm."
                                    if band_val is None else
                                    f"the spread model's era-banded `{band_val}` estimate"),
            "declared_family_size": spec.declared_family_size,
            "declared_family_id": spec.declared_family_id,
            "effective_family_size": res.family["multiplicity"]["effective_family_size"],
            "n_sleeves_judged": res.family["multiplicity"]["n_sleeves_judged_this_run"],
            "spec_sha256": spec.seal(),
            "n_in_cell": len(sub),
            "n_after_restriction": mix.get(sleeve, {}).get("n_kept", len(sub)),
            "cell_frac_of_ungated": round(len(sub) / len(lab_rows), 4) if lab_rows else None,
            "era_mix": mix.get(sleeve),
            **({} if sv is None else row_of(sv)),
        }
        if "decl" in cell:
            arm["pre_declaration"] = cell["decl"]
        arms[key] = arm
        ledger.record(
            mechanism="regime_conditioning_cell", sleeve=sleeve,
            variant={"cell": cell["name"], "basis": cell["basis"], "exit": vn,
                     "population": pop, "band": band_label,
                     "declared_family_size": spec.declared_family_size},
            window="full_archive", spec_sha256=spec.seal(),
            outcome={"ADMIT": "admitted", "REJECT": "rejected",
                     "NOT_EVALUABLE": "not_evaluable"}.get(
                (sv.verdict.value if sv else ""), "evaluated"),
            metric=(sv.pooled_oos_mean_r if sv else None),
            metric_name="pooled_oos_mean_r",
            note=f"AO regime conditioning, {key}")
        print(f"  {sleeve[:18]:18s} {vn[:26]:26s} {cell['name'][:26]:26s} "
              f"{band_label:4s} {pop:9s} n={arm.get('n_trades')} {arm.get('verdict')} "
              f"R/day={arm.get('pooled_oos_mean_r')} p={arm.get('p_raw')}", flush=True)
        return arm

    for sleeve in (XVOL, ASIA, MIDDN):
        exit_name, _why = BANKED_EXIT[sleeve]
        variants = {"as_walked": AD.AS_WALKED}
        if exit_name == "target_4R":
            variants[exit_name] = AD.Variant(name="target_4R", family="target",
                                             target_mode="fixed_r", target_r=4.0)
        elif exit_name.startswith("stop_"):
            variants[exit_name] = AD.Variant(name=exit_name,
                                             family="cross_stop_target_timestop",
                                             stop_mult=2.5, target_mode="scales_with_stop")
        resim: dict[str, list[dict]] = {}
        for vn, v in variants.items():
            if vn == "as_walked":
                resim[vn] = list(pops[sleeve])
            else:
                rs, _tel = AD.resimulate(pops[sleeve], v, series, index, costs, ACCOUNT, rule)
                resim[vn] = rs
        resim_lab = {vn: label(rs, sc)[0] for vn, rs in resim.items()}

        for vn, lab_rows in sorted(resim_lab.items()):
            for cell in cells[sleeve]:
                sub = [r for r in lab_rows if cell["pred"] is None or cell["pred"](r)]
                gate_name = f"{sleeve}|{vn}|{cell['name']}"
                if len(sub) < 20:
                    # A sub-20 cell is not gateable, and SILENCE about it is the AF §8 item 2
                    # failure mode: `comp==coil` misses the floor by ONE trade and it is the
                    # sleeve's own pre-declared cell. Its raw economics are published, clearly
                    # labelled as descriptive rather than gated.
                    nrs = [netr[(sleeve, r["symbol"], r["decision_bar_iso"])]
                           for r in sub
                           if (sleeve, r["symbol"], r["decision_bar_iso"]) in netr]
                    thin[gate_name] = {
                        "sleeve": sleeve, "exit": vn, "cell": cell["name"],
                        "basis": cell["basis"], "n_in_cell": len(sub),
                        "cell_frac_of_ungated": round(len(sub) / len(lab_rows), 4)
                        if lab_rows else None,
                        "mean_r_gross": (round(statistics.mean(r["r_gross"] for r in sub), 5)
                                         if sub else None),
                        "n_net_priced": len(nrs),
                        "mean_r_net_at_mid_band_as_walked": (
                            round(statistics.mean(nrs), 5) if nrs else None),
                        "mean_r_net_caveat": ("the net figure is joined from the AS-WALKED "
                                              "mid-band priced run, so it is only the net "
                                              "basis for the as_walked exit; a re-simulated "
                                              "exit changes the trade and the join does not "
                                              "follow it."),
                        "not_gateable": ("fewer than 20 trades -- below B_balanced's "
                                         "min_trades_total of 30 and every other option's "
                                         "floor. Reported descriptively, never as a verdict."),
                        **({"pre_declaration": cell["decl"]} if "decl" in cell else {}),
                    }
                    continue
                for band_label, band_val, pops_here in band_arms:
                    for pop in pops_here:
                        gate_one(sleeve, vn, cell, sub, lab_rows, band_label, band_val, pop)

        # ---- the AG band envelope, on the best cell per (sleeve, exit) at RECORDED@mid ----
        for vn in sorted(resim_lab):
            cands = [a for k, a in arms.items()
                     if a.get("sleeve") == sleeve and a.get("exit") == vn
                     and a.get("population") == "RECORDED" and a.get("spread_band") == "mid"
                     and a.get("p_raw") is not None]
            if not cands:
                continue
            best = min(cands, key=lambda a: a["p_raw"])
            cell = next(c for c in cells[sleeve] if c["name"] == best["cell"])
            sub = [r for r in resim_lab[vn] if cell["pred"] is None or cell["pred"](r)]
            for eb in ENVELOPE_BANDS:
                gate_one(sleeve, vn, cell, sub, resim_lab[vn], eb, eb, "RECORDED")
    out["arms"] = arms
    out["thin_cells_not_gateable"] = thin

    # ---- the composition, in ONE gate run, because R0 forbids composing across artifacts --
    #  AI §0's pair structure dissolved in AL §3.1 once `mx_btcusd @ target_5R` cleared rank 1
    #  alone. This asks whether it comes BACK: at m = 39, `mx_btcusd` holds rank 1 at p 0.0011
    #  and rank 2's threshold is 0.005128, so any second candidate under that bar admits
    #  ALONGSIDE it under BH's step-up. The best conditioned `sub_xvol_pullback` cell is inside
    #  it. Hand-composing two artifacts' p-values would be exactly the R0 violation AL §3.4
    #  warned about, so both are submitted to ONE gate at ONE stamp.
    comp_out = {}
    btc = BTC_SLEEVE
    btc_5r = AD.Variant(name="target_5R", family="target", target_mode="fixed_r", target_r=5.0)
    btc_rows, _btel = AD.resimulate(base_rows[btc], btc_5r, series, index, costs, ACCOUNT, rule)
    xvol_4r = AD.Variant(name="target_4R", family="target", target_mode="fixed_r", target_r=4.0)
    xvol_4r_rows, _xtel = AD.resimulate(pops[XVOL], xvol_4r, series, index, costs, ACCOUNT, rule)
    xvol_4r_lab = label(xvol_4r_rows, sc)[0]
    for cell in cells[XVOL]:
        if cell["basis"] == "control":
            continue
        sub = [r for r in xvol_4r_lab if cell["pred"](r)]
        if len(sub) < 20:
            continue
        for pop in ("ALL_ERAS", "RECORDED", "DECIDABLE"):
            pop_rows = {s: list(r) for s, r in base_rows.items()}
            pop_rows[btc] = btc_rows
            pop_rows[XVOL] = [{k: v for k, v in r.items() if k != "_st"} for r in sub]
            recs_all = {s: AD.to_records(r) for s, r in pop_rows.items()}
            recs, _mix = _restrict(recs_all, pop, smodel, BAND)
            o = OPTIONS["B_balanced"]
            spec = o.with_(spec_id=f"{o.spec_id}_ao_pair", sleeve_symbol_allowlist=allow,
                          spread_band=BAND)
            spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=fam)
            res = run_gate(recs, spec, costs=costs, server=SERVER)
            key = f"btc=target_5R|xvol=target_4R+{cell['name']}|band=mid|{pop}"
            comp_out[key] = {
                "xvol_cell": cell["name"], "xvol_basis": cell["basis"], "population": pop,
                "spread_band": BAND, "declared_family_size": spec.declared_family_size,
                "declared_family_id": spec.declared_family_id,
                "effective_family_size": res.family["multiplicity"]["effective_family_size"],
                "n_sleeves_judged": res.family["multiplicity"]["n_sleeves_judged_this_run"],
                "spec_sha256": spec.seal(),
                "admitted": sorted(res.admitted), "n_admitted": len(res.admitted),
                "rows": {s: row_of(res.verdicts[s]) for s in (btc, XVOL)
                         if s in res.verdicts},
                "admissible_in_this_session": cell["basis"] == "pre_declared",
                "why_not_admissible": (None if cell["basis"] == "pre_declared" else
                                       "the xvol cell's CUT is post-hoc; see its `decl` block"),
            }
            print(f"  PAIR {key:64s} ADMIT {sorted(res.admitted) or '-'}", flush=True)
    # the two-cut-rules-per-axis search, priced. Two rules on one pre-declared axis is a
    # search of size 2, and Bonferroni-within-2 is the honest within-axis bill.
    cutbill = {}
    for a in arms.values():
        if a.get("basis") not in ("derived_from_pre_declared_level",
                                  "pre_declared_direction_at_the_mechanism_cut"):
            continue
        if a.get("p_raw") is None:
            continue
        field = (a.get("pre_declaration") or {}).get("field")
        k = f"{a['sleeve']}|{field}|{a['exit']}|band={a['spread_band']}|{a['population']}"
        row = cutbill.setdefault(k, {"cells": {}, "n_cut_rules_tried": 0})
        row["cells"][a["cell"]] = {"p_raw": a["p_raw"], "basis": a["basis"],
                                   "R_per_day": a.get("pooled_oos_mean_r"),
                                   "verdict": a.get("verdict")}
        row["n_cut_rules_tried"] = len(row["cells"])
    for k, row in cutbill.items():
        best = min(row["cells"].values(), key=lambda c: c["p_raw"])
        row["best_p_raw"] = best["p_raw"]
        row["bonferroni_within_cut_rules"] = min(1.0, best["p_raw"] * row["n_cut_rules_tried"])
        row["rank_2_bar_at_declared_39"] = round(0.20 / m_all, 6)
        row["survives_rank_2_after_within_axis_bonferroni"] = bool(
            row["bonferroni_within_cut_rules"] <= 0.20 / m_all)
    out["mechanism_cut_bill"] = {
        "why": ("two cut rules on one pre-declared axis is a search of size 2. Charging it "
                "within the axis is the smallest honest bill; it does NOT replace the family "
                "bill, which these cells do not pay at all because they are not declared."),
        "rows": dict(sorted(cutbill.items())),
    }

    out["composition_at_the_declared_family"] = {
        "question": ("at m = 39 the BH rank-2 threshold is 0.005128. `mx_btcusd @ target_5R` "
                     "holds rank 1 at p 0.0011, so does a conditioned `sub_xvol_pullback` "
                     "admit ALONGSIDE it?"),
        "why_one_gate_run": ("BH is a step-up over the whole submitted vector, so a q is a "
                             "property of the vector and not of a row (AL §3.4's R0-on-a-column "
                             "rule). Composing AL's p with AO's by hand would be that exact "
                             "violation."),
        "arms": comp_out,
    }

    # ---- the coverage question: WHY does DECIDABLE drop the armed sleeve to n=56? ---------
    #  The commission asks whether that loss is recoverable data or structural. The answer is
    #  in the era ledger's own variance decomposition, so it is read rather than argued: a
    #  half-width dominated by `split_half_noise` on few bars is a CAPTURE requirement, one
    #  dominated by `d1_vs_h4_disagreement` is a MODEL repair (AG's timeframe reconciliation),
    #  and one dominated by `cross_instrument_dispersion` is structural -- the instrument class
    #  genuinely disagrees and no amount of extra bars narrows it.
    def coverage_attribution(sleeve: str, rows: list[dict]) -> dict:
        per_era, dropped = {}, 0
        for r in rows:
            era_class, decidable = _est(smodel, r["symbol"], dt.datetime.fromisoformat(
                r["entry_utc"]), BAND)
            if era_class != "RECORDED" or decidable:
                continue
            dropped += 1
            try:
                rec = smodel.record(r["symbol"], ACCOUNT)
                era = smodel.estimate(r["symbol"], ACCOUNT,
                                      dt.datetime.fromisoformat(r["entry_utc"]),
                                      band=BAND).era
                e = (rec.get("eras") or {}).get(era) or {}
            except Exception as exc:  # noqa: BLE001
                per_era.setdefault(f"{r['symbol']}|LOOKUP_FAILED", {
                    "n_trades": 0, "error": f"{type(exc).__name__}: {exc}"})
                per_era[f"{r['symbol']}|LOOKUP_FAILED"]["n_trades"] += 1
                continue
            key = f"{r['symbol']}|{era}"
            row = per_era.setdefault(key, {
                "n_trades": 0, "class": e.get("class"),
                "band_halfwidth_log": e.get("band_halfwidth_log"),
                "band_halfwidth_log_floored": e.get("band_halfwidth_log_floored"),
                "cross_instrument_dispersion_log": e.get("cross_instrument_dispersion_log"),
                "split_half_noise_log": e.get("split_half_noise_log"),
                "d1_vs_h4_disagreement_log": e.get("d1_vs_h4_disagreement_log"),
                "n_bars_nonzero": e.get("n_bars_nonzero"),
                "n_instrument_estimates": e.get("n_instrument_estimates"),
                "timeframe_used": e.get("timeframe_used"),
                "timeframe_references_comparable": e.get("timeframe_references_comparable"),
            })
            row["n_trades"] += 1
        # which term dominates, per era, and therefore which repair it names
        for key, row in per_era.items():
            terms = {k: row.get(k) for k in ("cross_instrument_dispersion_log",
                                             "split_half_noise_log",
                                             "d1_vs_h4_disagreement_log")}
            terms = {k: v for k, v in terms.items() if isinstance(v, (int, float))}
            if not terms:
                row["dominant_term"] = None
                row["repair_named"] = "UNKNOWN -- the era row carries no variance terms"
                continue
            dom = max(terms, key=lambda k: terms[k])
            row["dominant_term"] = dom
            row["dominant_share"] = (round(terms[dom] / sum(terms.values()), 4)
                                     if sum(terms.values()) else None)
            row["repair_named"] = {
                "split_half_noise_log": ("CAPTURE -- the estimate is noisy on the bars it has; "
                                         "more bar history for this (symbol, quarter) narrows "
                                         "it. Recoverable, and the requirement is exact."),
                "d1_vs_h4_disagreement_log": ("MODEL -- the D1 and H4 references disagree, "
                                              "which is AG's timeframe reconciliation, not a "
                                              "data gap. Recoverable in code."),
                "cross_instrument_dispersion_log": ("STRUCTURAL -- the instrument class itself "
                                                    "disperses in this quarter, so extra bars "
                                                    "for this symbol do not narrow the band. "
                                                    "Repairable only by a per-symbol era term."),
            }[dom]
        counts = collections.Counter(v.get("repair_named", "").split(" --")[0]
                                     for v in per_era.values())
        return {
            "sleeve": sleeve,
            "question": ("AL §4 measured `sub_xvol_pullback` at n=56 on DECIDABLE against 85 on "
                         "RECORDED and 88 unrestricted, and NOT_EVALUABLE there. WHICH eras "
                         "cost it those trades, and is the loss recoverable data or "
                         "structural?"),
            "n_trades_total": len(rows),
            "n_recorded_but_undecidable": dropped,
            "per_era": dict(sorted(per_era.items())),
            "n_eras": len(per_era),
            "repair_class_counts_by_era": dict(sorted(counts.items())),
            "trades_by_repair_class": dict(sorted(collections.Counter(
                [row.get("repair_named", "").split(" --")[0]
                 for row in per_era.values()
                 for _ in range(int(row["n_trades"]))]).items())),
            "how_to_read_it": (
                "these trades are in eras the model calls RECORDED -- it DID derive an era "
                "ratio from bar history -- whose band is nonetheless wider than the 0.5 "
                "decidability threshold. So the loss is not 'no data'; it is 'data that "
                "disagrees with itself'. AL §3.3's unwired hole is the other half of the same "
                "fact: an undecidable RECORDED era degrades `Coverage` not at all "
                "(`spread_model.py:440-441`), so these 32 trades price as MEASURED today."),
        }

    out["coverage_attribution"] = {
        s: coverage_attribution(s, [{k: v for k, v in r.items() if k != "_st"}
                                    for r in labelled[s]])
        for s in (XVOL, MIDDN, ASIA)
    }
    print("\nCOVERAGE ATTRIBUTION (RECORDED-but-undecidable trades, and the repair each names):")
    for s, v in sorted(out["coverage_attribution"].items()):
        print(f"  {s:20s} {v['n_recorded_but_undecidable']}/{v['n_trades_total']} in "
              f"{v['n_eras']} eras -> {v['trades_by_repair_class']}")

    # ---- the reproduction control: does the FLAT arm reproduce AL's and AM's figures? -----
    repro = {}
    for gname, tgt in repro_targets().items():
        a = arms.get(f"{gname}|band=flat|ALL_ERAS")
        got = (a or {}).get("pooled_oos_mean_r")
        gotp = (a or {}).get("p_raw")
        mid = arms.get(f"{gname}|band=mid|ALL_ERAS") or {}
        t, tp = tgt["pooled_oos_mean_r"], tgt["p_raw"]
        repro[gname] = {
            "published_source": tgt["source"],
            "published_pooled_oos_mean_r": t, "published_p_raw": tp,
            "published_n": tgt["n_trades"],
            "here_pooled_oos_mean_r": got, "here_p_raw": gotp,
            "here_n": (a or {}).get("n_trades"),
            "abs_delta_r": (abs(got - t) if (got is not None and t is not None) else None),
            "abs_delta_p": (abs(gotp - tp) if (gotp is not None and tp is not None) else None),
            "reproduces_to_1e-12": bool(
                got is not None and t is not None and abs(got - t) < 1e-12
                and gotp is not None and tp is not None and abs(gotp - tp) < 1e-12
                and (a or {}).get("n_trades") == tgt["n_trades"]),
            "mid_band_pooled_oos_mean_r": mid.get("pooled_oos_mean_r"),
            "mid_band_p_raw": mid.get("p_raw"),
            "band_move_factor": (
                round(mid["pooled_oos_mean_r"] / got, 3)
                if (got not in (None, 0) and mid.get("pooled_oos_mean_r") is not None)
                else None),
            "sign_flips_at_mid": bool(
                got is not None and mid.get("pooled_oos_mean_r") is not None
                and (got > 0) != (mid["pooled_oos_mean_r"] > 0)),
        }
    out["controls"]["flat_band_reproduces_AL_and_AM"] = {
        "question": ("AL's asia frontier and AM's re-clock set no `spread_band`, so their "
                     "published figures are at spec.py:82's flat_37_day_snapshot. Does this "
                     "file's `flat` arm reproduce them, and how far does the mid band move "
                     "them?"),
        "why_it_matters": ("without this control a reader comparing AO's mid-band numbers to "
                          "AL's flat-band numbers would read a cost-basis change as a "
                          "measurement disagreement -- the exact R0 failure AL §8.8 item 2 "
                          "recorded against itself."),
        "rows": repro,
    }
    print("\nCONTROL flat-band reproduction of AL / AM:")
    for k, v in repro.items():
        print(f"  {k:52s} exact={v['reproduces_to_1e-12']} flat {v['here_pooled_oos_mean_r']} "
              f"-> mid {v['mid_band_pooled_oos_mean_r']} "
              f"(x{v['band_move_factor']}, sign flip {v['sign_flips_at_mid']})")

    # ---- the enumeration bill ------------------------------------------------------------
    bills = {}
    band_labels = [lb for lb, _bv, _ps in band_arms] + list(ENVELOPE_BANDS)
    for sleeve in (XVOL, ASIA, MIDDN):
        for pop in ("ALL_ERAS", "RECORDED", "DECIDABLE"):
          for bl in band_labels:
            enum = [a for a in arms.values()
                    if a.get("sleeve") == sleeve and a.get("population") == pop
                    and a.get("spread_band") == bl
                    and a.get("basis") == "enumerated" and a.get("p_raw") is not None]
            if not enum:
                continue
            best = min(enum, key=lambda a: a["p_raw"])
            n_cells = len([a for a in arms.values()
                           if a.get("sleeve") == sleeve and a.get("population") == pop
                           and a.get("spread_band") == bl
                           and a.get("basis") == "enumerated"])
            bills[f"{sleeve}|band={bl}|{pop}"] = {
                "n_cells_enumerated": n_cells,
                "spread_band": bl, "population": pop,
                "best_cell": best["cell"], "best_exit": best["exit"],
                "best_p_raw": best["p_raw"],
                "bonferroni_within_enumeration": min(1.0, best["p_raw"] * n_cells),
                "max_declared_family_that_admits_at_alpha_0.10": int(0.10 / best["p_raw"]),
                "declared_family_here": m_all,
                "why": ("an enumerated cell is a SEARCH over the pre-declared hypothesis's "
                        "own parameter space, so its own p carries the enumeration as a "
                        "within-family bill. It is reported, never admitted: admitting it "
                        "would require declaring it in CANDIDATE_FAMILY, which raises the "
                        "estate-wide bill, and no enumerated cell here is close enough to "
                        "be worth that."),
            }
    out["enumeration_bills"] = bills

    # ---- the seed sweep: is the ADMIT a property of the sleeve or of `spec.seed`? ---------
    #  At 8 blocks the sign-flip null has 2**8 = 256 distinct outcomes and 10,000 draws, so
    #  `ge` (`perm_null.py:201-202`, p = (1+ge)/(n_perm+1)) counts how many draws happened to
    #  reproduce the identity sign vector: Binomial(10000, 1/256), mean 39.06, sd 6.24. If the
    #  observation is the maximum over all 256 achievable assignments -- which it is, since p
    #  sits at the floor -- then p is that count and nothing else. `spec.seed` is fixed at
    #  20260729, so the question "does this cell admit" may be a question about the seed. This
    #  sweep answers it on the production path rather than by argument.
    seed_sweep = {}
    for sweep_label, exit_name, cellname in (
            ("pair_admitting_cell", "target_4R", "ac60>=median(0.0141)"),
            ("its_ungated_parent", "target_4R", "ungated"),
    ):
        cell = next(c for c in cells[XVOL] if c["name"] == cellname)
        v = AD.Variant(name="target_4R", family="target", target_mode="fixed_r", target_r=4.0)
        rs, _t = AD.resimulate(pops[XVOL], v, series, index, costs, ACCOUNT, rule)
        lab = label(rs, sc)[0]
        sub = [r for r in lab if cell["pred"] is None or cell["pred"](r)]
        pop_rows = {ss: list(rr) for ss, rr in base_rows.items()}
        pop_rows[XVOL] = [{k2: v2 for k2, v2 in r.items() if k2 != "_st"} for r in sub]
        # `mx_btcusd` must be at `target_5R`, which is the population the ADMIT was measured
        # in. My first version left it at as-walked (p ~0.0064), where it cannot hold BH rank 1
        # -- so the sweep was asking "does xvol admit alone", a question whose answer is no at
        # every seed, and the one ADMIT it reported was BTC's own as-walked p wandering. Caught
        # by reading the per-seed rows.
        btc_v = AD.Variant(name="target_5R", family="target", target_mode="fixed_r",
                           target_r=5.0)
        pop_rows[BTC_SLEEVE] = AD.resimulate(base_rows[BTC_SLEEVE], btc_v, series, index,
                                             costs, ACCOUNT, rule)[0]
        recs_all = {ss: AD.to_records(rr) for ss, rr in pop_rows.items()}
        recs, _mix = _restrict(recs_all, "RECORDED", smodel, BAND)
        ps, verdicts_seen = [], []
        o2 = OPTIONS[base_opt_name]
        for sd in range(20260721, 20260741):
            spec2 = o2.with_(spec_id=f"{o2.spec_id}_ao_seed_{sd}",
                            sleeve_symbol_allowlist=allow, spread_band=BAND, seed=sd)
            spec2 = CF.with_declared_family(spec2, "CANDIDATE_BOOK_V1", loaded=fam)
            r2 = run_gate(recs, spec2, costs=costs, server=SERVER)
            sv2 = r2.verdicts.get(XVOL)
            if sv2 is None or sv2.p_raw is None:
                continue
            ps.append(sv2.p_raw)
            verdicts_seen.append({"seed": sd, "p_raw": sv2.p_raw,
                                  "verdict": sv2.verdict.value,
                                  "admitted_in_run": sorted(r2.admitted)})
        rank2 = 0.20 / m_all
        n_adm = sum(1 for x in verdicts_seen if x["verdict"] == "ADMIT")
        seed_sweep[sweep_label] = {
            "exit": exit_name, "cell": cellname, "population": "RECORDED",
            "spread_band": BAND, "n_seeds": len(ps),
            "seed_of_record": o2.seed,
            "p_min": min(ps) if ps else None, "p_max": max(ps) if ps else None,
            "p_mean": (statistics.mean(ps) if ps else None),
            "p_sd": (statistics.pstdev(ps) if len(ps) > 1 else None),
            "rank_2_bar": round(rank2, 6),
            "n_seeds_admitting": n_adm,
            "frac_seeds_admitting": round(n_adm / len(ps), 3) if ps else None,
            "n_seeds_with_p_below_rank_2": sum(1 for x in ps if x <= rank2),
            "distance_from_rank_2_in_seed_sd": (
                round(abs(statistics.mean(ps) - rank2) / statistics.pstdev(ps), 2)
                if len(ps) > 1 and statistics.pstdev(ps) else None),
            "binomial_prediction_for_sd_p": (
                ((10000 * (2.0 ** -8) * (1 - 2.0 ** -8)) ** 0.5) / 10001),
            "btc_at": "target_5R -- the population the ADMIT was measured in",
            "per_seed": verdicts_seen,
            "reading": ("a verdict that changes with the permutation seed is a property of the "
                        "seed. The parent arm is swept as the control: its p is far above its "
                        "own floor, so its verdict must NOT move."),
        }
        print(f"\nSEED SWEEP {sweep_label}: {n_adm}/{len(ps)} seeds ADMIT; p in "
              f"[{min(ps) if ps else None}, {max(ps) if ps else None}], sd "
              f"{statistics.pstdev(ps) if len(ps) > 1 else None}")
    #  And the same sweep on the ESTATE'S ONE ADMISSION, because "is that verdict a property of
    #  the seed" is a question AL's result deserves and nobody has asked it. Its p is far above
    #  its own floor (11x) so the prediction is that it does not move; a prediction is not a
    #  measurement, which is AL §8.5's lesson.
    btc_v2 = AD.Variant(name="target_5R", family="target", target_mode="fixed_r", target_r=5.0)
    pop_btc = {ss: list(rr) for ss, rr in base_rows.items()}
    pop_btc[BTC_SLEEVE] = AD.resimulate(base_rows[BTC_SLEEVE], btc_v2, series, index, costs,
                                        ACCOUNT, rule)[0]
    recs_btc, _m = _restrict({ss: AD.to_records(rr) for ss, rr in pop_btc.items()},
                             "RECORDED", smodel, BAND)
    o3 = OPTIONS[base_opt_name]
    bps, brows = [], []
    for sd in range(20260721, 20260741):
        sp3 = o3.with_(spec_id=f"{o3.spec_id}_ao_seed_btc_{sd}",
                       sleeve_symbol_allowlist=allow, spread_band=BAND, seed=sd)
        sp3 = CF.with_declared_family(sp3, "CANDIDATE_BOOK_V1", loaded=fam)
        r3 = run_gate(recs_btc, sp3, costs=costs, server=SERVER)
        v3 = r3.verdicts.get(BTC_SLEEVE)
        if v3 is None or v3.p_raw is None:
            continue
        bps.append(v3.p_raw)
        brows.append({"seed": sd, "p_raw": v3.p_raw, "verdict": v3.verdict.value,
                      "admitted_in_run": sorted(r3.admitted)})
    n_badm = sum(1 for x in brows if x["verdict"] == "ADMIT")
    seed_sweep["the_estate_s_one_admission"] = {
        "sleeve": BTC_SLEEVE, "exit": "target_5R", "cell": "ungated",
        "population": "RECORDED", "spread_band": BAND, "n_seeds": len(bps),
        "seed_of_record": o3.seed,
        "p_min": min(bps) if bps else None, "p_max": max(bps) if bps else None,
        "p_mean": statistics.mean(bps) if bps else None,
        "p_sd": statistics.pstdev(bps) if len(bps) > 1 else None,
        "rank_1_bar": round(0.10 / m_all, 6),
        "n_seeds_admitting": n_badm,
        "frac_seeds_admitting": round(n_badm / len(bps), 3) if bps else None,
        "n_seeds_with_p_below_rank_1": sum(1 for x in bps if x <= 0.10 / m_all),
        "distance_from_rank_1_in_seed_sd": (
            round(abs(statistics.mean(bps) - 0.10 / m_all) / statistics.pstdev(bps), 2)
            if len(bps) > 1 and statistics.pstdev(bps) else None),
        "per_seed": brows,
        "reading": ("this is the control that matters most: if the estate's ONE admission were "
                    "also seed-fragile, the finding would be about the gate rather than about "
                    "either candidate."),
    }
    print(f"\nSEED SWEEP the_estate_s_one_admission: {n_badm}/{len(bps)} seeds ADMIT; p in "
          f"[{min(bps) if bps else None}, {max(bps) if bps else None}], sd "
          f"{statistics.pstdev(bps) if len(bps) > 1 else None}")
    out["seed_sweep"] = seed_sweep

    # ---- the resolution audit: which arms' p sits at its own structural floor? ------------
    prox = {}
    for k, a in sorted(arms.items()):
        h = a.get("p_floor_headroom")
        if h is None:
            continue
        prox[k] = {"p_raw": a["p_raw"], "p_floor": a["p_floor"],
                   "p_floor_headroom": round(h, 4),
                   "n_trades": a.get("n_trades"), "n_oos_days": a.get("n_oos_days"),
                   "n_blocks": a.get("n_blocks"), "block_days_used": a.get("block_days_used"),
                   "verdict": a.get("verdict"),
                   "p_floor_binds_per_gate": a.get("p_floor_binds"),
                   "cell": a.get("cell"), "basis": a.get("basis"),
                   "population": a.get("population"), "spread_band": a.get("spread_band")}
    tight = {k: v for k, v in prox.items() if v["p_floor_headroom"] < 2.0}
    out["resolution_audit"] = {
        "why": ("`stats.perm_p_floor` gives the smallest p a B-block sign flip can attain. "
                "`gate.py:851-857` refuses only when p_raw <= p_floor and sets "
                "`p_floor_binds`; a p ONE resolution step ABOVE the floor passes with no "
                "flag at all. That is the case for the only cell in this session that "
                "admits, so the audit is not decoration."),
        "rank_2_bar_at_declared_39": round(0.20 / m_all, 6),
        "n_arms_with_a_p": len(prox),
        "n_arms_within_2x_of_their_floor": len(tight),
        "arms_within_2x_of_their_floor": tight,
        "all_arms": prox,
        "reading": ("headroom is p_raw / p_floor. Above ~5x the p is resolved by the data; near "
                    "1x it is the test's resolution limit wearing a p-value. Conditioning is "
                    "the mechanism: it halves the OOS DAYS, days set the block count, and the "
                    "floor is 2**-blocks."),
        "what_the_gate_actually_checks": (
            "CORRECTED after reading `gate.py:849-863` properly. It does NOT compare `p_raw` to "
            "`p_floor`. It refuses (NOT_EVALUABLE, `p_floor_binds=True`) only when "
            "`p_floor >= spec.alpha` -- i.e. when NO p on the series could ever be significant. "
            "At 8 blocks the floor is 0.004006 against alpha 0.10, so that guard is 25x away "
            "from firing and nothing in the gate relates the observed p to its own resolution. "
            "`p_floor_binds` reads absent on every arm below, including the ones whose p sits "
            "under the floor's expected value."),
        "why_a_p_can_sit_BELOW_its_reported_floor": (
            "`perm_p_floor` is the EXPECTED minimum, not a hard bound. "
            "`perm_null.py:201-202` computes p = (1 + ge)/(n_perm + 1) where `ge` counts draws "
            "whose null statistic >= the observation. When the observation is the maximum over "
            "all 2**B achievable sign assignments, `ge` is just the number of draws that "
            "happened to reproduce the identity assignment -- Binomial(n_perm, 2**-B). At "
            "B = 8, n_perm = 10,000 that is mean 39.06, sd 6.24, so p is 0.004006 +/- 0.000624 "
            "and lands either side of the floor by luck."),
        "binomial_arithmetic_at_8_blocks": {
            "n_perm": 10000, "n_blocks": 8, "p_identity_draw": 2.0 ** -8,
            "expected_ge": 10000 * 2.0 ** -8,
            "sd_ge": (10000 * (2.0 ** -8) * (1 - 2.0 ** -8)) ** 0.5,
            "expected_p": (1 + 10000 * 2.0 ** -8) / 10001,
            "sd_p": ((10000 * (2.0 ** -8) * (1 - 2.0 ** -8)) ** 0.5) / 10001,
            "rank_1_bar": round(0.10 / m_all, 6), "rank_2_bar": round(0.20 / m_all, 6),
            "rank_2_window_above_the_floor_in_sd": round(
                (0.20 / m_all - (1 + 10000 * 2.0 ** -8) / 10001)
                / (((10000 * (2.0 ** -8) * (1 - 2.0 ** -8)) ** 0.5) / 10001), 2),
            "rank_1_distance_below_the_floor_in_sd": round(
                ((1 + 10000 * 2.0 ** -8) / 10001 - 0.10 / m_all)
                / (((10000 * (2.0 ** -8) * (1 - 2.0 ** -8)) ** 0.5) / 10001), 2),
            "implied_ge_per_arm": {
                k: round(v["p_raw"] * 10001 - 1, 1)
                for k, v in sorted(tight.items(), key=lambda kv: kv[1]["p_raw"])},
            "reading": ("every arm below is the SAME statistical event -- the observation is the "
                        "extreme sign assignment -- and they differ only in how many of 10,000 "
                        "draws duplicated it. Rank 1 is 2.3 sd BELOW the floor, so it is "
                        "unreachable at 8 blocks; the rank-2 window is 1.8 sd wide."),
        },
    }
    print("\nRESOLUTION AUDIT: arms whose p sits within 2x of its own structural floor:")
    for k, v in sorted(tight.items(), key=lambda kv: kv[1]["p_floor_headroom"]):
        print(f"  {k[:72]:72s} p={v['p_raw']:.6f} floor={v['p_floor']:.6f} "
              f"x{v['p_floor_headroom']} days={v['n_oos_days']} blocks={v['n_blocks']} "
              f"{v['verdict']}")

    # ---- the answer ----------------------------------------------------------------------
    admits = sorted({(a["sleeve"], a["cell"], a["exit"], a["spread_band"], a["population"])
                     for a in arms.values() if a.get("verdict") == "ADMIT"})

    def _best(basis, sleeve=None):
        b = None
        for a in arms.values():
            if a.get("basis") != basis or a.get("p_raw") is None:
                continue
            if sleeve and a.get("sleeve") != sleeve:
                continue
            cand = (a["p_raw"], a["sleeve"], a["cell"], a["exit"], a["spread_band"],
                    a["population"])
            if b is None or cand < b:
                b = cand
        if b is None:
            return None
        return {"p_raw": b[0], "sleeve": b[1], "cell": b[2], "exit": b[3],
                "spread_band": b[4], "population": b[5],
                "shortfall_vs_rank_1": round(b[0] / (0.10 / m_all), 3)}

    out["answer"] = {
        "admits_at_the_sealed_alpha": [
            {"sleeve": a, "cell": c, "exit": e, "band": bd, "population": pp}
            for a, c, e, bd, pp in admits],
        "n_dials_pinned_by_the_cell": {s: v["n_dials_pinned"]
                                       for s, v in out["pinning"].items()},
        "best_by_basis": {b: _best(b) for b in
                          ("control", "pre_declared", "enumerated",
                           "derived_from_pre_declared_level")},
        "best_per_sleeve_any_basis": {
            sl: min([{"p_raw": a["p_raw"], "cell": a["cell"], "exit": a["exit"],
                      "band": a["spread_band"], "population": a["population"],
                      "basis": a["basis"], "R_per_day": a.get("pooled_oos_mean_r"),
                      "verdict": a.get("verdict"),
                      "drop_best_retention": a.get("drop_best_retention")}
                     for a in arms.values()
                     if a.get("sleeve") == sl and a.get("p_raw") is not None],
                     key=lambda d: d["p_raw"], default=None)
            for sl in (XVOL, ASIA, MIDDN)},
    }
    out["seconds_total"] = round(time.time() - t0, 1)
    nt = measured_n_trials(ledger_paths=[REPO / DEFAULT_TRIAL_LEDGER])
    out["trial_ledger"] = nt
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e6:.2f} MB)")
    print(json.dumps(out["answer"], indent=1, default=str))
    return out


if __name__ == "__main__":
    main()
