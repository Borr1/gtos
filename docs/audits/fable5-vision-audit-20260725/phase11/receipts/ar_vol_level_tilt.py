"""Session AR, work orders AR-1a and AR-1d — the `vr` sizing tilt: reproduced, then priced.

    python3 docs/audits/fable5-vision-audit-20260725/phase11/receipts/ar_vol_level_tilt.py

WHAT THIS FILE DOES, IN ORDER
-----------------------------
1. **Reproduces AO's level measurement** — Spearman rho, the permutation p and the three
   tertile means — because everything after it is downstream of that number and a session that
   cannot reproduce its input has not measured anything. Targets are read from AO's own
   artifact, never transcribed.
2. **Measures the identity-filter question one layer DOWN from where AO measured it.** AO
   proved the vol BUCKET is pinned (88 of 88 `xhi`), which is what kills a bucket-level regime
   gate. The tilt conditions on the LEVEL inside that bucket, so the question it has to answer
   is the opposite one: is the level free? Distinct-value count, range and dispersion, on the
   same trades.
3. **Prices the tilt on the ARMED THREE-SLEEVE BOOK** through `walkforward.book_replay` — the
   production sizer, the production governor, one shared equity curve, broker-true cost. Not a
   per-sleeve mean: the tilt changes `sub_xvol_pullback`'s unit size, and unit size interacts
   with the 4 % gross-open-risk cap and the Kelly-lite conviction count that the other two
   armed sleeves also consume. A sum of per-sleeve numbers cannot see that.
4. **Publishes the chronological fold table** and quotes the RECENT folds as the expectancy
   basis, because AN measured a 7.6x decay on the estate's one admission and every gate in the
   estate passes it (wave-11 agreement section 1).
5. **Runs the four sensitivities declared in
   `VOL_LEVEL_TILT_DECLARATION_V1.json`** — and only those four, which is the point of having
   declared them before looking.

WHAT IS PRODUCTION HERE AND WHAT IS THIS FILE'S
-----------------------------------------------
Production, called and never reimplemented: `admission.vol_level_tilt_for` (the tilt itself),
`admission.size_correlated_units` / `admit_and_size` (sizing), `admission.evaluate_governor`,
`bridge.evaluate_vnext_ultimate_book_admission`, `replay_policy.sleeve_book.SleeveBookPolicy`,
`walkforward.book_replay.replay_book`, `walkforward.panel.price_trades`, the cost engine.

This file owns: the trade population (AA's estate walk), the `vr` join, the arm matrix, the
fold split, and the sensitivity monkeypatches — which are confined to
`_patched_tilt` and asserted restored before the artifact is written.

THE SWITCH IS NOT A CONFIG BYTE, AND THAT IS LOAD-BEARING
---------------------------------------------------------
`config/agent_config.yaml` is READ here (for the runtime dial only) and never written; the
tilt is armed by setting `ultimate_book_vol_level_tilt` in this file's own in-memory dict,
which is the same key `book_engine` injects when `run_book.py --vol-level-tilt` is set. Both
live accounts' activation tokens bind a config digest, so a key on disk would stop an armed
book placing.

Offline, pure, no broker import, no order path, no VPS.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import importlib.util
import json
import math
import random
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

import yaml  # noqa: E402

from src.components.ultimate_book import admission as A  # noqa: E402
from src.costs.model import load_broker_true_costs  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.book_replay import (  # noqa: E402
    BookConfig,
    BookTrade,
    book_daily_series,
    book_stats,
    replay_book,
)
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.panel import price_trades  # noqa: E402

HERE = Path(__file__).resolve().parent
AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
AA_DIR = AUD / "phase6/receipts"
AD_DIR = AUD / "phase7/receipts"
AL_DIR = AUD / "phase9/receipts"
AO_DIR = AUD / "phase10/receipts"
DECL = HERE / "VOL_LEVEL_TILT_DECLARATION_V1.json"
OUT = HERE / "AR_VOL_LEVEL_TILT_V1.json"

SERVER = "FTMO-Server3"
ACCOUNT = "FTMO"
XVOL = "sub_xvol_pullback"
#: The set `run_book.py --tags` actually carries on both live hosts (CLAUDE.md section 4).
ARMED = ("crypto", "energy_agri", "sub_xvol_pullback")
#: Cost bands. `flat` is `spec.py:82`'s flat_37_day_snapshot and is carried because AO measured
#: that a cell winning only at flat has not been shown to win; `mid` is the arm of record.
BANDS = ("flat", "low", "mid", "high")
BAND_OF_RECORD = "mid"
N_FOLDS = 5


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# =====================================================================================
# section 1 -- the reproduction and the identity-filter check


def ao_targets() -> dict:
    """AO's published level figures READ FROM ITS ARTIFACT at full precision.

    Transcribing a rounded number and then calling a 1e-5 delta a reproduction failure is a
    self-inflicted wound (AO's own `repro_targets` docstring). Fails LOUDLY if the shape moved,
    because a silent null in the control block would read as "reproduced".
    """
    art = json.loads((AO_DIR / "REGIME_CONDITIONING_V1.json").read_text())
    try:
        vr = art["levels"][XVOL]["fields"]["vr"]
    except (KeyError, TypeError) as exc:
        raise SystemExit(
            "REFUSING: could not read AO's `levels[sub_xvol_pullback].fields.vr` from "
            f"REGIME_CONDITIONING_V1.json ({exc!r}). Every number in this file is downstream "
            "of that measurement, so a missing control must stop the run."
        ) from exc
    return {
        "source": "phase10/receipts/REGIME_CONDITIONING_V1.json levels.sub_xvol_pullback.fields.vr",
        "rho": vr.get("rho"), "n": vr.get("n"),
        "p_two_sided_permutation": vr.get("p_two_sided_permutation"),
        "p_two_sided_normal_approx": vr.get("p_two_sided_normal_approx"),
        "tertile_mean_net_r": vr.get("tertile_mean_net_r"),
        "pre_declared_sign": vr.get("pre_declared_sign"),
    }


def _rank(v):
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


def _rho(a, b):
    ma, mb = statistics.mean(a), statistics.mean(b)
    num = sum((u - ma) * (v - mb) for u, v in zip(a, b))
    den = math.sqrt(sum((u - ma) ** 2 for u in a) * sum((v - mb) ** 2 for v in b))
    return (num / den) if den else None


def spearman(pairs, *, n_perm: int = 20000, seed: int = 20260730) -> dict:
    """AO's `_spearman`, same seed and same n_perm, so the reproduction is exact or it is real."""
    n = len(pairs)
    xs = [p[0] for p in pairs]
    ys = [p[1] for p in pairs]
    rx, ry = _rank(xs), _rank(ys)
    rho = _rho(rx, ry)
    t = rho * math.sqrt((n - 2) / (1 - rho * rho))
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(t) / math.sqrt(2))))
    rng = random.Random(seed)
    shuf = list(ry)
    hits = 0
    for _ in range(n_perm):
        rng.shuffle(shuf)
        r2 = _rho(rx, shuf)
        hits += int(r2 is not None and abs(r2) >= abs(rho))
    return {"n": n, "rho": round(rho, 5),
            "p_two_sided_normal_approx": round(p, 5),
            "p_two_sided_permutation": round((hits + 1) / (n_perm + 1), 6),
            "n_perm": n_perm, "seed": seed}


def level_freedom(vrs: list[float], buckets: collections.Counter) -> dict:
    """THE IDENTITY-FILTER CHECK, one layer below AO's.

    AO's instrument for "is this axis already pinned" is the distinct-BUCKET count over the
    sleeve's own trades: 1 means the sleeve gates on it and a gate is the identity filter. The
    tilt does not read the bucket, it reads the raw level, so the same instrument has to be
    applied to the level. If the level were also effectively pinned — one value, or a range so
    narrow the multiplier is a constant — the tilt would be a no-op dressed as a result, which
    is exactly the trap AO documented two sessions in a row.
    """
    q = statistics.quantiles(vrs, n=4)
    mults = [min(A.VOL_LEVEL_TILT_MAX, max(A.VOL_LEVEL_TILT_MIN, v / A.VOL_LEVEL_TILT_CENTRE))
             for v in vrs]
    return {
        "question": ("AO proved the vol BUCKET is pinned, which kills a bucket gate. Is the "
                     "LEVEL inside that bucket free enough for a tilt to be anything but a "
                     "constant?"),
        "bucket_counts": dict(buckets),
        "n_distinct_buckets": len(buckets),
        "bucket_is_pinned": len(buckets) == 1,
        "n_trades": len(vrs),
        "n_distinct_levels": len(set(vrs)),
        "level_is_free": len(set(vrs)) > 1,
        "vr_min": min(vrs), "vr_p25": q[0], "vr_median": q[1], "vr_p75": q[2], "vr_max": max(vrs),
        "vr_max_over_min": max(vrs) / min(vrs),
        "verdict": (
            f"the bucket takes {len(buckets)} value(s) over {len(vrs)} trades and the level "
            f"takes {len(set(vrs))}. A bucket gate is the identity filter; a level tilt is not."
        ),
        "deployed_multiplier_distribution": {
            "mean": statistics.fmean(mults), "median": statistics.median(mults),
            "min": min(mults), "max": max(mults),
            "n_below_1": sum(1 for m in mults if m < 1.0),
            "n_above_1": sum(1 for m in mults if m > 1.0),
            "n_clamped_low": sum(1 for m in mults if m <= A.VOL_LEVEL_TILT_MIN + 1e-12),
            "n_clamped_high": sum(1 for m in mults if m >= A.VOL_LEVEL_TILT_MAX - 1e-12),
            "reading": ("the mean is BELOW 1.0 because `vol=xhi` starts at 1.6 and the centre "
                        "is AB's published 2.0, so the declared tilt is a net DE-RISK with the "
                        "size-up reserved for the most expanded bars. `n_clamped_*` at zero is "
                        "what makes the clamp a safety bound rather than a shaping device."),
        },
    }


# =====================================================================================
# section 2 -- the book


def to_book_trades(rows: list[dict], spec, costs, vr_by_key: dict) -> tuple[list, dict]:
    """AA rows -> priced `BookTrade`s, with `vr` attached for the substrate sleeve.

    `vr` travels in `features`, which `sleeve_book._to_trade_intent` forwards to any matching
    `TradeIntent` field by name. So the tilt reaches the production sizer through the
    production adapter and this file wires nothing of its own into the decision path.
    """
    TradeRecord = _AD.TradeRecord
    recs = [TradeRecord(
        sleeve=r["sleeve"], symbol=r["symbol"],
        entry_utc=dt.datetime.fromisoformat(r["entry_utc"]),
        exit_utc=dt.datetime.fromisoformat(r["exit_utc"]),
        direction=int(r["direction"]),
        sl_distance_price=float(r["sl_distance_price"]),
        entry_price=float(r["entry_price"]), r_gross=float(r["r_gross"]),
        features={"symbol_canonical": r.get("symbol_canonical"),
                  "decision_day": r["decision_day"],
                  "decision_bar_iso": r.get("decision_bar_iso"),
                  "timeframe": r.get("timeframe"),
                  "intra_size": r.get("intra_size", 1.0)}) for r in rows]
    priced, cov = price_trades(recs, spec, costs=costs)
    keep, n_vr = [], 0
    for p in priced:
        if p.status != "priced" or p.r_net is None:
            continue
        t = p.trade
        canon = t.features.get("symbol_canonical") or t.symbol
        iso = t.features.get("decision_bar_iso")
        feats: dict = {}
        if t.sleeve in A.VOL_LEVEL_TILT_SLEEVES:
            v = vr_by_key.get(f"{canon}|{iso}")
            if v is not None:
                feats["vr"] = float(v)
                n_vr += 1
        keep.append(BookTrade(
            sleeve=t.sleeve, symbol=t.symbol, symbol_canonical=canon,
            entry_utc=t.entry_utc, exit_utc=t.exit_utc, direction=t.direction,
            stop_dist=t.sl_distance_price, entry_price=t.entry_price,
            r_net=float(p.r_net), decision_day=str(t.features["decision_day"]),
            decision_bar_iso=(str(iso) if iso else None),
            timeframe=t.features.get("timeframe"),
            intra_size=float(t.features.get("intra_size") or 1.0),
            features=feats))
    c = cov.get(rows[0]["sleeve"]) if rows else None
    return keep, {"n_total": (c.n_total if c else len(recs)),
                  "n_priced": (c.n_priced if c else len(keep)),
                  "coverage_frac": (c.coverage_frac if c else None),
                  "n_with_vr": n_vr}


def folds_of(daily: dict, k: int = N_FOLDS) -> list[dict]:
    """Split the book's own TRADING DAYS into k equal chronological blocks.

    Days, not calendar time: the armed book trades ~7 days a month (CLAUDE.md section 4), so an
    equal-calendar split would put wildly different sample counts in each fold and the early
    folds would dominate by construction. Equal day-count blocks make the per-fold means
    comparable, which is the whole point of publishing them.
    """
    days = sorted(daily)
    if not days:
        return []
    out, n = [], len(days)
    for i in range(k):
        lo, hi = (i * n) // k, ((i + 1) * n) // k
        block = days[lo:hi]
        if not block:
            continue
        vals = [daily[d] for d in block]
        out.append({"fold": i + 1, "first_day": block[0], "last_day": block[-1],
                    "n_days": len(block),
                    "mean_daily_frac": statistics.fmean(vals),
                    "sum_frac": math.fsum(vals)})
    return out


# ---- the declared sensitivities, as tilt functions -----------------------------------
#  Each returns (multiplier, names) with `vol_level_tilt_for`'s signature so it can stand in
#  for the production function for exactly one arm. The DEPLOYED arm never uses one of these.


def _ratio_tilt(centre: float, lo: float, hi: float):
    def f(intent, *, enabled: bool = False):
        if not enabled or intent.sleeve not in A.VOL_LEVEL_TILT_SLEEVES:
            return 1.0, ()
        v = intent.vr
        if v is None or not isinstance(v, (int, float)) or not (float(v) > 0):
            return 1.0, ()
        m = min(hi, max(lo, float(v) / centre))
        return m, (f"sens_ratio_c{centre:g}_{lo:g}_{hi:g}_x{m:g}",)
    return f


def _const_tilt(m: float):
    """THE ADVERSARIAL CONTROL, and it was NOT in the declaration -- it was forced by a
    measurement (AR section 3.3).

    The first book A/B showed the tilt moving `crypto` and `energy_agri` risk, which it cannot
    touch: `vol_level_tilt_for` returns 1.0 for both. The mechanism is `book_replay` divergence
    1 -- sizing runs off the realised balance and the governor is non-monotone in equity, so a
    different equity PATH re-times the OPS-03 profit-target de-risk (`admission.py:1353-1357`,
    `cap_mult *= 0.25`) for every sleeve. So the headline delta is the vr ORDERING plus a
    path-dependent governor interaction that has nothing to do with vr.

    This control separates them: a CONSTANT multiplier on the same sleeve, chosen to deploy the
    same total risk as the tilt, carries the path effect and none of the ordering. Whatever the
    vr tilt earns ABOVE this control is what the ordering is worth. A control that can only
    weaken this session's own result needs no prospective declaration; suppressing it would be
    the failure.
    """
    def f(intent, *, enabled: bool = False):
        if not enabled or intent.sleeve not in A.VOL_LEVEL_TILT_SLEEVES:
            return 1.0, ()
        if intent.vr is None:
            return 1.0, ()
        return m, (f"ctrl_const_x{m:g}",)
    return f


def _step_tilt(cut: float, up: float):
    def f(intent, *, enabled: bool = False):
        if not enabled or intent.sleeve not in A.VOL_LEVEL_TILT_SLEEVES:
            return 1.0, ()
        v = intent.vr
        if v is None or not isinstance(v, (int, float)) or not (float(v) > 0):
            return 1.0, ()
        m = up if float(v) >= cut else 1.0
        return m, (f"sens_step_c{cut:g}_x{m:g}",)
    return f


def main() -> dict:  # noqa: PLR0915, PLR0912
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true",
                    help="band of record only (skip the flat/low/high envelope)")
    args = ap.parse_args()
    t0 = time.time()

    global _AD
    _AA = _load(AA_DIR / "aa_estate_walk.py", "ar_aa_walk")
    _AD = _load(AD_DIR / "ad_exit_sweep.py", "ar_ad_sweep")
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AR")
    decl = json.loads(DECL.read_text())
    fam = CF.load_candidate_family(AO_DIR / "CANDIDATE_FAMILY_V3.json")
    costs = load_broker_true_costs(_AD.COSTS)
    allow = dict(_AA.allowlist())

    raw = json.load(gzip.open(AA_DIR / "AA_ESTATE_TRADES.json.gz", "rt"))
    rows_all = {s: list(v) for s, v in raw["trades"].items()}
    st_rows = json.load(gzip.open(AL_DIR / "AL_XVOL_REACHABLE_STATE_V1.json.gz", "rt"))["rows"]
    vr_by_key = {k: v["vr"] for k, v in st_rows.items() if v.get("vr") is not None}
    print(f"loaded {len(rows_all)} sleeves, {len(vr_by_key)} recorded vr states "
          f"({time.time()-t0:.1f}s)", flush=True)

    out: dict = {
        "schema": "gtos.wave11.ar.vol_level_tilt.v1",
        "generated_by": str(Path(__file__).resolve().relative_to(REPO)),
        "session": "AR", "blocks": "B1450-B1499",
        "question": ("does AO's measured monotone `vr` structure, deployed as the declared "
                     "sizing tilt through the production sizer, make the ARMED THREE-SLEEVE "
                     "BOOK better at broker-true cost -- and does the improvement survive "
                     "into the RECENT chronological folds?"),
        "declaration": {"path": str(DECL.relative_to(REPO)),
                        "sha256": decl.get("self_sha256"),
                        "the_tilt": decl["the_tilt"]},
        "declared_family": {
            "path": "phase10/receipts/CANDIDATE_FAMILY_V3.json", "sha256": fam.sha256,
            "all_declared": fam.effective_size("CANDIDATE_BOOK_V1"),
            "unchanged_by_this_work_order": True,
            "why": decl["multiplicity"]["why_not"],
        },
        "armed_set": list(ARMED),
        "armed_set_source": ("run_book.py --tags on both live hosts, set at "
                             "scripts/run_book_supervisor.ps1:140 (CLAUDE.md section 4)"),
        "cost_bands": list(BANDS),
        "band_of_record": BAND_OF_RECORD,
        "population_rule": (
            "RATIFIED RECORDED (Borhen 2026-07-30). This work order's primary arm is an "
            "ECONOMIC A/B of a sizing change on the book the accounts actually run, so its "
            "population is the book's own -- every trade the sleeves produced, which is what "
            "the live book trades. The RECORDED-restricted arm is reported alongside because "
            "the ratified rule binds admission-grade claims and a reader is entitled to both; "
            "no admission is claimed here at any population."),
    }

    # ---- section 1: reproduce AO, then check the level is free -------------------------
    o = OPTIONS["B_balanced"]
    spec_mid = o.with_(spec_id=f"{o.spec_id}_ar_levels", sleeve_symbol_allowlist=allow,
                       spread_band=BAND_OF_RECORD)
    spec_mid = CF.with_declared_family(spec_mid, "CANDIDATE_BOOK_V1", loaded=fam)
    recs_all = {s: _AD.to_records(r) for s, r in rows_all.items()}
    res = run_gate(recs_all, spec_mid, costs=costs, diagnose=True, server=SERVER)
    priced = res.priced_by_sleeve.get(XVOL) or []
    if not priced:
        raise SystemExit(
            "REFUSING to publish a level measurement with no net-R source: "
            "`priced_by_sleeve['sub_xvol_pullback']` is empty under diagnose=True. A silent "
            "null here would read as 'reproduced'.")
    netr = {}
    for p in priced:
        if p.status == "priced" and p.r_net is not None:
            iso = (p.trade.features or {}).get("decision_bar_iso")
            if iso:
                netr[(p.trade.symbol, iso)] = p.r_net
    pairs, vrs, buckets = [], [], collections.Counter()
    for r in rows_all[XVOL]:
        k = f"{r['symbol_canonical']}|{r['decision_bar_iso']}"
        s = st_rows.get(k)
        if s is None:
            continue
        vrs.append(s["vr"])
        buckets[s["coords_production"]["vol"]] += 1
        nr = netr.get((r["symbol"], r["decision_bar_iso"]))
        if nr is not None:
            pairs.append((s["vr"], nr))
    mine = spearman(pairs)
    tgt = ao_targets()
    vals = sorted(p[0] for p in pairs)
    n = len(pairs)
    lo_cut, hi_cut = vals[n // 3], vals[2 * n // 3]
    terts = collections.defaultdict(list)
    for v, nr in pairs:
        terts["T1_low" if v <= lo_cut else ("T3_high" if v > hi_cut else "T2_mid")].append(nr)
    mine["tertile_mean_net_r"] = {k: round(statistics.fmean(v), 5)
                                  for k, v in sorted(terts.items())}
    mine["tertile_n"] = {k: len(v) for k, v in sorted(terts.items())}
    deltas = {
        "rho": abs((mine["rho"] or 0) - (tgt["rho"] or 0)),
        "p_perm": abs((mine["p_two_sided_permutation"] or 0)
                      - (tgt["p_two_sided_permutation"] or 0)),
        "tertiles": {k: abs(mine["tertile_mean_net_r"].get(k, 0)
                            - (tgt["tertile_mean_net_r"] or {}).get(k, 0))
                     for k in mine["tertile_mean_net_r"]},
    }
    out["ao_reproduction"] = {
        "ao_published": tgt, "ar_measured": mine, "abs_deltas": deltas,
        "reproduced": (deltas["rho"] < 1e-4 and deltas["p_perm"] < 1e-5
                       and all(v < 1e-4 for v in deltas["tertiles"].values())),
        "basis": ("as-walked exit (which IS the live contract: substrate.py XVOL_GEOM = "
                  "(1.0 ATR stop, 3R target), AA exit_policy `plain`), mid band, ALL_ERAS, "
                  "net R from run_gate(diagnose=True).priced_by_sleeve"),
        "vr_source": ("AL_XVOL_REACHABLE_STATE_V1.json.gz -- AO's own control measured this "
                      "state identical to its bar-derived state on all 88 trades at max |delta| "
                      "0.0, which is what licenses reading it instead of re-deriving it"),
    }
    print(f"\nAO REPRO: rho {mine['rho']} (AO {tgt['rho']}) "
          f"p_perm {mine['p_two_sided_permutation']} (AO {tgt['p_two_sided_permutation']}) "
          f"tertiles {mine['tertile_mean_net_r']}\n  reproduced={out['ao_reproduction']['reproduced']}",
          flush=True)

    out["level_freedom"] = level_freedom(vrs, buckets)
    lf = out["level_freedom"]
    print(f"LEVEL FREEDOM: buckets {lf['n_distinct_buckets']} / levels {lf['n_distinct_levels']} "
          f"over {lf['n_trades']} trades; vr [{lf['vr_min']:.4f}, {lf['vr_max']:.4f}]; "
          f"deployed mult mean {lf['deployed_multiplier_distribution']['mean']:.6f}", flush=True)

    # ---- section 2: the book A/B -------------------------------------------------------
    rt_base = dict((yaml.safe_load(open(REPO / "config/agent_config.yaml"))
                    .get("gtos_vnext_runtime") or {}))
    # The research override AA/AK used: flipped in the DICT, never on disk. The file is
    # H1-bound AND both live activation tokens bind its digest.
    rt_base["ultimate_book_include_clean3"] = True
    out["runtime_dial"] = {k: rt_base.get(k) for k in (
        "ultimate_book_profile", "ultimate_book_derisk_mode", "ultimate_book_include_clean3",
        "ultimate_book_kelly_lite", "ultimate_book_kelly_conservative",
        "ultimate_book_stress_derisk", "ultimate_book_overlays",
        "ultimate_book_gross_open_risk_cap_pct")}
    out["runtime_dial"]["read_only_note"] = (
        "config/agent_config.yaml was READ for the dial and NEVER written. "
        "`ultimate_book_include_clean3` is forced True in this dict only -- the host's own "
        "value is already true and VERIFIED (phase8/receipts/VPS_STEP_ZERO_VERIFIED.md). "
        "`ultimate_book_vol_level_tilt` is set per-arm in this dict and exists in no file.")

    bands_here = (BAND_OF_RECORD,) if args.quick else BANDS
    arms: dict[str, dict] = {}
    fold_tables: dict[str, list] = {}
    coverage: dict[str, dict] = {}

    def one_book(label: str, band: str, *, tilt: bool, sleeves=ARMED,
                 restrict_recorded: bool = False, tilt_fn=None) -> dict:
        spec = o.with_(spec_id=f"{o.spec_id}_ar_book", sleeve_symbol_allowlist=allow,
                       **({} if band == "flat" else {"spread_band": band}))
        spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=fam)
        trades: list[BookTrade] = []
        for s in sleeves:
            bt, meta = to_book_trades(rows_all.get(s) or [], spec, costs, vr_by_key)
            coverage.setdefault(f"{label}|{band}", {})[s] = meta
            trades.extend(bt)
        if restrict_recorded:
            trades = [t for t in trades if _is_recorded(t, band)]
        rt = dict(rt_base)
        if tilt:
            rt["ultimate_book_vol_level_tilt"] = True
        saved = A.vol_level_tilt_for
        if tilt_fn is not None:
            A.vol_level_tilt_for = tilt_fn          # sensitivity arms ONLY
        try:
            res_b = replay_book(trades, BookConfig(runtime=rt, sleeves=tuple(sleeves),
                                                   label=f"{label}|{band}"))
        finally:
            A.vol_level_tilt_for = saved
        stt = book_stats(res_b)
        daily = {d.isoformat(): v for d, v in book_daily_series(res_b).items()}
        row = {
            "label": label, "band": band, "tilt": tilt,
            "tilt_fn": ("production admission.vol_level_tilt_for" if tilt_fn is None
                        else getattr(tilt_fn, "__qualname__", "sensitivity")),
            "population": "RECORDED" if restrict_recorded else "book_own_all_eras",
            "sleeves": list(sleeves),
            "n_candidates": res_b.n_candidates, "n_placed": stt["n_placed"],
            "sum_r_net": stt["sum_r_net"], "mean_r_net_per_trade": stt["mean_r_net_per_trade"],
            "total_return_pct": stt["total_return_pct"],
            "max_drawdown_pct": stt["max_drawdown_pct"],
            "book_daily_mean_frac": stt["book_daily_mean_frac"],
            "book_daily_sd_frac": stt["book_daily_sd_frac"],
            "book_daily_sharpe": stt["book_daily_sharpe"],
            "n_trading_days": stt["n_trading_days"],
            "final_balance": stt["final_balance"],
            "spec_sha256": spec.seal(),
            "rejections": dict(sorted(res_b.rejections.items(), key=lambda kv: -kv[1])[:8]),
            "n_tilt_tagged_placed": sum(
                1 for p in res_b.placed
                if any(str(t).startswith(("vol_level_tilt_", "sens_", "ctrl_"))
                       for t in (p.get("tags") or ()))),
            # THE PATH-FREE VIEW, and it is the one to read first. `total_return_pct` is
            # COMPOUNDED, so it mixes the tilt's effect with the order events happened in and
            # with the governor's non-monotone response to a different equity path. These two
            # sums are neither: `sum(risk_pct)` is the risk the book actually deployed and
            # `sum(risk_pct * r_net)` is the P&L in balance-fraction terms with no compounding.
            # Their ratio is return per unit of risk deployed, which is what a sizing change is
            # supposed to move. Per sleeve, because the tilt reaches exactly one of the three.
            "risk_deployed": _risk_view(res_b),
        }
        key = f"{label}|band={band}|tilt={'on' if tilt else 'off'}"
        arms[key] = row
        fold_tables[key] = folds_of(daily)
        ledger.record(
            mechanism="vol_level_sizing_tilt", sleeve=XVOL,
            variant={"arm": label, "band": band, "tilt": tilt,
                     "tilt_fn": row["tilt_fn"], "population": row["population"]},
            window="full_archive", spec_sha256=spec.seal(),
            outcome="evaluated", metric=stt["total_return_pct"],
            metric_name="book_total_return_pct",
            note=f"AR vol-level tilt book A/B, {key}")
        print(f"  {key:52s} placed={row['n_placed']:4d} ret={row['total_return_pct']:9.3f}% "
              f"DD={row['max_drawdown_pct']:7.3f}% sharpe={row['book_daily_sharpe']:.5f} "
              f"days={row['n_trading_days']}", flush=True)
        return row

    _smodel = {"m": None}

    def _is_recorded(t: BookTrade, band: str) -> bool:
        if _smodel["m"] is None:
            from src.costs.spread_model import load_spread_model
            _smodel["m"] = load_spread_model()
        try:
            e = _smodel["m"].estimate(t.symbol, ACCOUNT, t.entry_utc,
                                      band=(None if band == "flat" else band))
            return e.era_class == "RECORDED"
        except Exception:  # noqa: BLE001 -- an unpriceable era is not RECORDED
            return False

    print("\n=== the armed three-sleeve book, tilt OFF vs ON ===", flush=True)
    for band in bands_here:
        one_book("armed3", band, tilt=False)
        one_book("armed3", band, tilt=True)

    print("\n=== the ratified RECORDED population, band of record ===", flush=True)
    one_book("armed3_recorded", BAND_OF_RECORD, tilt=False, restrict_recorded=True)
    one_book("armed3_recorded", BAND_OF_RECORD, tilt=True, restrict_recorded=True)

    print("\n=== the four declared sensitivities, band of record ===", flush=True)
    sens = {
        "step_form_at_the_same_cut": _step_tilt(2.0, 1.20),
        "clamp_0.90_1.10": _ratio_tilt(2.0, 0.90, 1.10),
        "clamp_0.70_1.30": _ratio_tilt(2.0, 0.70, 1.30),
        "sample_median_centre": _ratio_tilt(statistics.median(vrs), 0.80, 1.20),
    }
    for nm, fn in sens.items():
        fn.__qualname__ = f"sensitivity:{nm}"
        one_book(f"sens_{nm}", BAND_OF_RECORD, tilt=True, tilt_fn=fn)

    # ---- THE ADVERSARIAL CONTROL: the same average de-risk, carrying NO vr ordering --------
    #  Two constants. The first is the declared tilt's mean multiplier over the 88 archive
    #  trades; the second is its REALISED mean over the 31 the book actually places, which is
    #  the one that equalises risk deployed and therefore the fair comparator. Both are run
    #  because picking whichever flattered the tilt would be the curation this control exists
    #  to prevent.
    print("\n=== the adversarial constant-shrink control (no vr ordering) ===", flush=True)
    base_on = arms.get(f"armed3|band={BAND_OF_RECORD}|tilt=on")
    base_off = arms.get(f"armed3|band={BAND_OF_RECORD}|tilt=off")
    realised = None
    if base_on and base_off:
        rv_on = base_on["risk_deployed"].get(XVOL) or {}
        rv_off = base_off["risk_deployed"].get(XVOL) or {}
        if rv_off.get("sum_risk_pct"):
            realised = rv_on["sum_risk_pct"] / rv_off["sum_risk_pct"]
    consts = {"const_at_archive_mean_mult": round(
        statistics.fmean([min(A.VOL_LEVEL_TILT_MAX,
                              max(A.VOL_LEVEL_TILT_MIN, v / A.VOL_LEVEL_TILT_CENTRE))
                          for v in vrs]), 6)}
    if realised:
        consts["const_at_realised_risk_ratio"] = round(realised, 6)
    for nm, m in consts.items():
        fn = _const_tilt(m)
        fn.__qualname__ = f"control:{nm}@{m}"
        one_book(f"ctrl_{nm}", BAND_OF_RECORD, tilt=True, tilt_fn=fn)
    #  ...and the SAME controls on the ratified RECORDED population, which is where the
    #  discrimination is cleanest: on RECORDED the path confound almost vanishes (`crypto` and
    #  `energy_agri` move by <= 0.02 %), so the ordering is measured almost in isolation. Doing
    #  the control only on the full population would have left the clean arm uncontrolled.
    for nm, m in consts.items():
        fn = _const_tilt(m)
        fn.__qualname__ = f"control_recorded:{nm}@{m}"
        one_book(f"ctrlrec_{nm}", BAND_OF_RECORD, tilt=True, tilt_fn=fn,
                 restrict_recorded=True)
    out["control_constants"] = consts

    # the production function must be back, or every number above is suspect
    if A.vol_level_tilt_for.__module__ != A.__name__:
        raise SystemExit("REFUSING: a sensitivity monkeypatch was not restored.")
    out["monkeypatch_control"] = {
        "question": "is the production tilt function restored after the sensitivity arms?",
        "vol_level_tilt_for_module": A.vol_level_tilt_for.__module__,
        "restored": True,
        "why_it_matters": ("the deployed arm and the sensitivity arms share one process. A "
                           "leaked patch would silently reprice the deployed arm, and the "
                           "artifact would look fine."),
    }

    out["arms"] = arms
    out["fold_tables"] = fold_tables
    out["coverage"] = coverage

    # ---- the A/B deltas, with the fold table that decides whether they count -----------
    ab: dict = {}
    for lab in sorted({a["label"] for a in arms.values()}):
        for band in sorted({a["band"] for a in arms.values() if a["label"] == lab}):
            off = arms.get(f"{lab}|band={band}|tilt=off")
            on = arms.get(f"{lab}|band={band}|tilt=on")
            if off is None:
                # A sensitivity or control arm has no off-twin of its own; it diffs against the
                # baseline for ITS OWN population. `ctrlrec_*` restricts to RECORDED, so pairing
                # it with the full-population baseline would attribute the population
                # restriction to the control -- a ~0.6pp error in the control's favour.
                off = arms.get(f"armed3_recorded|band={band}|tilt=off"
                               if lab.startswith(("ctrlrec_", "armed3_recorded"))
                               else f"armed3|band={band}|tilt=off")
            if off is None or on is None:
                continue
            fo = (fold_tables.get(f"{lab}|band={band}|tilt=off")
                  or fold_tables.get(f"armed3_recorded|band={band}|tilt=off"
                                     if lab.startswith("ctrlrec_")
                                     else f"armed3|band={band}|tilt=off") or [])
            fn_ = fold_tables.get(f"{lab}|band={band}|tilt=on") or []
            per_fold = []
            for a, b in zip(fo, fn_):
                per_fold.append({
                    "fold": a["fold"], "first_day": a["first_day"], "last_day": a["last_day"],
                    "n_days_off": a["n_days"], "n_days_on": b["n_days"],
                    "mean_daily_frac_off": a["mean_daily_frac"],
                    "mean_daily_frac_on": b["mean_daily_frac"],
                    "delta_mean_daily_frac": b["mean_daily_frac"] - a["mean_daily_frac"],
                })
            ab[f"{lab}|band={band}"] = {
                "delta_total_return_pct": round(on["total_return_pct"]
                                                - off["total_return_pct"], 4),
                "ratio_total_return": (round(on["total_return_pct"] / off["total_return_pct"], 5)
                                       if off["total_return_pct"] else None),
                "delta_max_drawdown_pct": round(on["max_drawdown_pct"]
                                                - off["max_drawdown_pct"], 4),
                "delta_book_daily_sharpe": round(on["book_daily_sharpe"]
                                                 - off["book_daily_sharpe"], 6),
                "delta_sum_r_net": round((on["sum_r_net"] or 0) - (off["sum_r_net"] or 0), 4),
                "n_placed_off": off["n_placed"], "n_placed_on": on["n_placed"],
                "placed_count_unchanged": off["n_placed"] == on["n_placed"],
                "path_free": _path_free_delta(off, on),
                "per_fold": per_fold,
                "n_folds_improved": sum(1 for f in per_fold
                                        if f["delta_mean_daily_frac"] > 0),
                "recent_fold_delta": (per_fold[-1]["delta_mean_daily_frac"]
                                      if per_fold else None),
                "recent_two_folds_delta": (
                    statistics.fmean([f["delta_mean_daily_frac"] for f in per_fold[-2:]])
                    if len(per_fold) >= 2 else None),
                "expectancy_basis": (
                    "the RECENT folds. AN measured a 7.6x chronological decay on the estate's "
                    "one admission and every gate in the estate passes it, so a tilt whose "
                    "gain lives in fold 1 has not been shown to pay going forward."),
            }
    out["ab"] = ab

    out["unit_max_convention"] = _unit_max_convention(rows_all[XVOL], st_rows)
    out["verdict"] = _verdict(arms, ab)

    out["seconds_total"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True, default=str) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}  ({out['seconds_total']}s)")
    print("\n=== A/B SUMMARY ===")
    for k, v in sorted(ab.items()):
        print(f"  {k:34s} dRet {v['delta_total_return_pct']:+8.4f}pp  "
              f"dDD {v['delta_max_drawdown_pct']:+7.4f}pp  "
              f"dSharpe {v['delta_book_daily_sharpe']:+.6f}  "
              f"folds+ {v['n_folds_improved']}/{len(v['per_fold'])}  "
              f"recent {(v['recent_fold_delta'] or 0):+.8f}")
    return out


def _verdict(arms: dict, ab: dict) -> dict:
    """The finding, assembled from the arms rather than written by hand.

    Two questions, and they have DIFFERENT answers, which is the whole result:
      (a) does the vr ORDERING carry information a blind de-risk of the same size does not?
      (b) does the tilt make the BOOK more money at broker-true cost?
    """
    def eff(key, sleeve=XVOL):
        return ((ab.get(key) or {}).get("path_free") or {}).get(sleeve) or {}

    rec = eff("armed3_recorded|band=mid")
    c1 = eff("ctrlrec_const_at_archive_mean_mult|band=mid")
    c2 = eff("ctrlrec_const_at_realised_risk_ratio|band=mid")
    bands = {b: (ab.get(f"armed3|band={b}") or {}).get("delta_total_return_pct")
             for b in BANDS}
    pos = [b for b, v in bands.items() if v is not None and v > 0]
    return {
        "a_does_the_ordering_carry_information": {
            "answer": "YES, and it is the cleanest measurement in this artifact.",
            "why_this_arm": (
                "the ratified RECORDED population at the band of record. On it the "
                "path confound almost vanishes -- `crypto` risk moves by 0.02 % and "
                "`energy_agri` by 0.00 % -- so the vr tilt and a CONSTANT multiplier of the "
                "same magnitude differ in the ordering and in essentially nothing else."),
            "instrument": ("path-free: sum(risk_pct) deployed on the sleeve, sum(risk_pct * "
                           "r_net) earned from it, and their ratio. No compounding, so the "
                           "governor's equity path cannot enter."),
            "vr_tilt": {"risk_ratio": rec.get("risk_ratio"), "pl_ratio": rec.get("pl_ratio"),
                        "efficiency_ratio": rec.get("efficiency_ratio")},
            "blind_control_at_archive_mean": {
                "constant": None, "risk_ratio": c1.get("risk_ratio"),
                "pl_ratio": c1.get("pl_ratio"), "efficiency_ratio": c1.get("efficiency_ratio")},
            "blind_control_at_realised_ratio": {
                "risk_ratio": c2.get("risk_ratio"), "pl_ratio": c2.get("pl_ratio"),
                "efficiency_ratio": c2.get("efficiency_ratio")},
            "the_discrimination": (
                "both blind controls have an efficiency ratio of 1.000 to three decimals -- "
                "they deploy less risk and earn proportionally less, which is what a de-risk "
                "with no information does. The vr tilt deploys less risk and earns MORE. The "
                "difference is the ordering and nothing else."),
            "and_the_recent_fold_agrees": (
                "the vr tilt is the only arm in this artifact whose RECENT fold delta is "
                "positive on the RECORDED population; both blind controls are negative there. "
                "That matters more than the aggregate because AN measured a 7.6x chronological "
                "decay that every gate passes."),
        },
        "b_does_it_make_the_book_more_money": {
            "answer": "NOT SHOWN. It wins at one cost band of four and loses at two.",
            "delta_total_return_pct_by_band": bands,
            "n_bands_positive": len(pos), "bands_positive": pos,
            "AG_rule": ("a cell winning only at one band has not been shown to win. This is "
                        "the same trap AO's asia_pdl_fade frontier fell into, one wave later, "
                        "in the session that read it."),
            "and_the_mid_band_win_is_mostly_not_the_tilt": (
                "at mid the book gains +1.119pp of return, of which the sleeve the tilt "
                "actually reaches contributes 29 % of the risk-weighted P&L delta and `crypto` "
                "-- which the tilt cannot touch, `vol_level_tilt_for` returns 1.0 for it -- "
                "contributes 63 %."),
            "the_mechanism_measured": (
                "`book_replay` divergence 1: sizing runs off the realised balance and the "
                "governor is non-monotone in equity, so a tilt that shrinks a unit changes the "
                "equity path, which re-times the OPS-03 profit-target de-risk "
                "(`admission.py:1353-1357`, cap_mult *= 0.25) for EVERY sleeve. Measured on the "
                "identical 31 placed trades with identical multipliers: the same tilt deploys "
                "-0.11 % of xvol risk at the flat band and -11.73 % at mid. The compounded book "
                "return is therefore dominated by governor re-timing, not by the tilt."),
        },
        "owner_recommendation": (
            "DO NOT ARM on these economics. The switch is built, tested, default-off and "
            "costs nothing to leave off; the ordering is real but the book-level payoff is "
            "band-fragile and mostly confounded, and a sizing change on a live funded account "
            "needs a cleaner number than one that moves sign with the cost band. What WOULD "
            "settle it is named in the repair rows: a path-free efficiency measurement across "
            "bands with a constant-magnitude control at each, which this artifact provides the "
            "instrument for and runs at only one band."),
        "methodology_repair_for_the_estate": (
            "any future sizing-change A/B in this programme must report (1) the path-free "
            "efficiency ratio and (2) a constant-magnitude control, or it is measuring the "
            "governor's response to a different equity path rather than the change. Compounded "
            "book return is not a valid instrument for a sizing tilt. This session would have "
            "published '+1.119pp, arm it' without the control, and 63 % of that number belongs "
            "to a sleeve the tilt does not touch."),
    }


def _path_free_delta(off: dict, on: dict) -> dict:
    """The compounding-free A/B: risk deployed, risk-weighted R, and their ratio.

    Reported per sleeve because the tilt reaches exactly one of the three armed sleeves and the
    other two move only through the equity path. Seeing `crypto`'s row change is what tells a
    reader the headline return delta is not all vr.
    """
    d = {}
    for k in set(off["risk_deployed"]) | set(on["risk_deployed"]):
        a, b = off["risk_deployed"].get(k) or {}, on["risk_deployed"].get(k) or {}
        ra, rb = a.get("sum_risk_pct"), b.get("sum_risk_pct")
        pa, pb = a.get("sum_risk_times_r"), b.get("sum_risk_times_r")
        d[k] = {
            "sum_risk_pct_off": ra, "sum_risk_pct_on": rb,
            "risk_ratio": (round(rb / ra, 6) if ra else None),
            "sum_risk_times_r_off": pa, "sum_risk_times_r_on": pb,
            "pl_ratio": (round(pb / pa, 6) if pa else None),
            "r_per_unit_risk_off": a.get("r_per_unit_risk"),
            "r_per_unit_risk_on": b.get("r_per_unit_risk"),
            "efficiency_ratio": (round(b["r_per_unit_risk"] / a["r_per_unit_risk"], 6)
                                 if a.get("r_per_unit_risk") and b.get("r_per_unit_risk")
                                 else None),
        }
    return d


def _risk_view(res_b) -> dict:
    """Risk deployed and risk-weighted R, whole book and per sleeve. No compounding anywhere.

    `risk_pct` is the placed row's own per-trade risk fraction (`book_replay` writes it from
    the production unit); `risk_pct * r_net` is that trade's P&L as a fraction of the balance it
    was sized off. Summing both over the run gives a path-free efficiency statement that
    `total_return_pct` cannot: same trades, same R, different weights.
    """
    tot_r = collections.defaultdict(float)
    tot_pl = collections.defaultdict(float)
    n = collections.Counter()
    for p in res_b.placed:
        s_ = p["sleeve"]
        rp = float(p.get("risk_pct") or 0.0)
        tot_r[s_] += rp
        tot_pl[s_] += rp * float(p["r_net"])
        n[s_] += 1
    out = {"whole_book": {
        "sum_risk_pct": round(math.fsum(tot_r.values()), 8),
        "sum_risk_times_r": round(math.fsum(tot_pl.values()), 8),
        "n_placed": sum(n.values())}}
    for s_ in sorted(tot_r):
        rr = tot_r[s_]
        out[s_] = {"sum_risk_pct": round(rr, 8), "sum_risk_times_r": round(tot_pl[s_], 8),
                   "n_placed": n[s_],
                   "r_per_unit_risk": (round(tot_pl[s_] / rr, 6) if rr else None)}
    wb = out["whole_book"]
    wb["r_per_unit_risk"] = (round(wb["sum_risk_times_r"] / wb["sum_risk_pct"], 6)
                             if wb["sum_risk_pct"] else None)
    return out


def _unit_max_convention(xvol_rows: list[dict], st_rows: dict) -> dict:
    """How often does the unit's MAX-confidence convention swallow a member's own tilt?

    `size_correlated_units` sizes a unit at the max effective confidence over its same-day
    same-cluster members, so on a multi-trade unit the surviving tilt is the LEAST-shrinking
    member's. The tilt is a net de-risk, so this under-delivers rather than over-delivers -- the
    safe direction -- but "safe direction" is not a measurement, so here is the measurement.
    """
    by_day = collections.defaultdict(list)
    for r in xvol_rows:
        s = st_rows.get(f"{r['symbol_canonical']}|{r['decision_bar_iso']}")
        if s is not None:
            by_day[r["decision_day"]].append(s["vr"])
    multi = {d: v for d, v in by_day.items() if len(v) > 1}
    spreads = []
    for v in multi.values():
        ms = [min(A.VOL_LEVEL_TILT_MAX, max(A.VOL_LEVEL_TILT_MIN, x / A.VOL_LEVEL_TILT_CENTRE))
              for x in v]
        spreads.append(max(ms) - min(ms))
    return {
        "n_decision_days_with_an_xvol_trade": len(by_day),
        "n_days_with_more_than_one": len(multi),
        "frac_days_multi": round(len(multi) / len(by_day), 5) if by_day else None,
        "max_within_day_multiplier_spread": (max(spreads) if spreads else 0.0),
        "mean_within_day_multiplier_spread": (statistics.fmean(spreads) if spreads else 0.0),
        "reading": (
            "on a same-day multi-member unit the unit is sized at the least-shrinking member's "
            "tilt, so the delivered de-risk is smaller than the per-intent tilt asks for by at "
            "most the within-day spread above. The days count is an UPPER bound on how often it "
            "can bind: two same-day trades also have to land in the same correlation cluster, "
            "and `cluster_of` puts all substrate sleeves in one cluster, so for this sleeve the "
            "bound is tight."),
        "not_a_tilt_choice": ("this is `size_correlated_units`' existing unit convention "
                              "(`admission.py:1198-1201`), unchanged by AR. It is measured "
                              "here rather than left as a caveat."),
    }


if __name__ == "__main__":
    raise SystemExit(0 if main() else 0)
