"""m3-2 — the estate's standing admission, re-gated at the RATIFIED rule with the
corrected walker.

    python3 .../m3/m3_regate.py --stage parity   # C2: reproduce AN's published p_raw
    python3 .../m3/m3_regate.py --stage grid     # the decision grid

THE RATIFIED RULE, SPELLED OUT (nothing here is chosen by this file)
--------------------------------------------------------------------
  population        RECORDED with AN's conditions
                    (`phase10/receipts/POPULATION_RULE_V1.json -> ratified_rule`,
                     Borhen 2026-07-30)
  option            B_balanced, alpha = 0.10, BH FDR (`options.py:88-104`)
  declared family   CANDIDATE_BOOK_V1 at the wave-18 tip **V27**
                    (59 declared / 57 looks), all_declared basis
  band              the three era-aware bands; the flat 37-day snapshot is carried as a
                    CONTROL only, per AG's rule and AN's `band_is_control`

FOUR ARMS, BECAUSE TWO THINGS CHANGE AND THEY MUST BE SEPARABLE
----------------------------------------------------------------
Lane r1's correction moves the WALK. It also, arithmetically, moves what the COST model is
entitled to charge, and the two are different claims:

    walk=old  spread=charged   the published arm. Must reproduce AN's p_raw. (C2)
    walk=new  spread=charged   the corrected walk with the spread still charged.
                               This DOUBLE COUNTS and is published as the strictly
                               conservative bound, labelled as such.
    walk=new  spread=removed   **the arm that is arithmetically right.**
    walk=old  spread=removed   isolates the cost change from the walk change.

Why removing it is right, and why it is not a favour to the candidate. Under FILL
anchoring the transacted entry is `close + direction * spread` and both exit legs hang off
it (`ultimate_book/order_router.py:66-73`). A long buys the ask and sells the bid; when its
stop fires it realises exactly `-1 R` and that R already contains the round-trip spread. So
`costs.model.cost_r`'s spread term — one full spread charged as a level on every trade,
mean 0.1917 R across this estate — is the same money a second time. Note the direction:
removing it makes every published NET number LESS negative, so this arm is the one that
must be argued for, and the argument is above. The `spread=charged` arm is kept precisely
so a reader who rejects the argument still has a verdict.

Nothing about the seven gates, the folds, the null or alpha is touched. The only patched
object is `panel.cost_r`, in-process, restored and asserted restored.
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import dataclasses
import datetime as dt
import gzip
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))
AD_DIR = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
sys.path.insert(0, str(AD_DIR))

import ad_exit_sweep as AD  # noqa: E402

from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import era_population as EP  # noqa: E402
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

HERE = Path(__file__).resolve().parent
SUB = HERE / "M3_SUBSTRATE_V1.json.gz"
P9 = REPO / "docs/audits/fable5-vision-audit-20260725/phase9/receipts"
P10 = REPO / "docs/audits/fable5-vision-audit-20260725/phase10/receipts"
P18 = REPO / "docs/audits/fable5-vision-audit-20260725/phase18/receipts"
DECL_V27 = P18 / "CANDIDATE_FAMILY_V27.json"
DECL_V2 = P9 / "CANDIDATE_FAMILY_V2.json"
AN_OUT = P10 / "POPULATION_RULE_V1.json"
OUT = HERE / "M3_REGATE_V1.json"

BTC = "mx_btcusd_d1_donchian_20_breakout"
XVOL = "sub_xvol_pullback"
SUBMID = "sub_mid_dn_revert"
CELLS = (BTC, XVOL, SUBMID)
SERVER, ACCOUNT = "FTMO-Server3", "FTMO"

#: AN's two configs, verbatim. `X_btc5R` carries the standing admission.
CONFIGS = {
    "X_btc5R": {BTC: "target_5R", XVOL: "target_4R", SUBMID: "reclocked"},
    "Y_btc4R": {BTC: "target_4R", XVOL: "target_4R", SUBMID: "reclocked"},
}
BANDS = (None, "low", "mid", "high")
POPS = EP.CANDIDATE_RULES + ("RECORDED_UNDECIDABLE",)
WALKS = ("old", "qs_low", "qs_mid", "qs_high")
BAND_OF_WALK = {"old": None, "qs_low": "low", "qs_mid": "mid", "qs_high": "high"}


# =====================================================================================
# the one patched object
# =====================================================================================

@contextlib.contextmanager
def spread_term_removed():
    """Zero `cost_r`'s spread term in-process, keeping every other term and its coverage.

    `panel.py:72` imports `cost_r` by name, so rebinding that one attribute is the whole
    patch: `run_gate` -> `price_trades` -> `cost_r` is the only path a cost reaches a
    verdict on. The breakdown is rebuilt with `dataclasses.replace` so nothing else — the
    coverage class, the detail block, the swap night count `charged_nights` reads — moves.
    Restored and asserted restored.
    """
    from src.costs.model import Measure
    from src.research_infra.walkforward import panel as P

    original = P.cost_r

    def patched(symbol, account, *a, **kw):
        b = original(symbol, account, *a, **kw)
        zero = dataclasses.replace(
            b.spread_r, value=0.0,
            provenance=(b.spread_r.provenance +
                        " | ZEROED by m3: under FILL anchoring the corrected walk already "
                        "charges the round-trip spread as geometry"))
        total = dataclasses.replace(
            b.total_r, value=(b.commission_r.value + b.swap_r.value + b.slippage_r.value),
            provenance="sum of commission + swap + slippage (spread zeroed by m3)")
        assert isinstance(zero, Measure)
        return dataclasses.replace(b, spread_r=zero, total_r=total)

    P.cost_r = patched
    try:
        yield
    finally:
        P.cost_r = original
        assert P.cost_r is original


# =====================================================================================

def load_substrate() -> dict:
    d = json.load(gzip.open(SUB, "rt"))
    return d["data"]


def rows_for(sub: dict, walk: str, config: str) -> dict[str, list[dict]]:
    out = {s: list(r) for s, r in sub[walk]["base"].items()}
    for sleeve, exit_name in CONFIGS[config].items():
        out[sleeve] = sub[walk]["variants"][f"{sleeve}|{exit_name}"]
    return out


def _row(sv, res, spec, **stamp) -> dict:
    st = sv.gates.get("stability", {}) if sv is not None else {}
    fam = res.family["multiplicity"]
    base = {**stamp,
            "alpha": spec.alpha, "multiplicity": spec.multiplicity,
            "coverage_policy": spec.coverage_policy,
            "declared_family_size": spec.declared_family_size,
            "declared_family_id": spec.declared_family_id,
            "effective_family_size": fam["effective_family_size"],
            "n_sleeves_judged": fam["n_sleeves_judged_this_run"],
            "spec_sha256": spec.seal(), "spec_id": spec.spec_id}
    if sv is None:
        return {**base, "verdict": "ABSENT"}
    cov = sv.coverage or {}
    return {**base,
            "verdict": sv.verdict.value, "n_trades": sv.n_trades,
            "pooled_oos_mean_r": sv.pooled_oos_mean_r,
            "p_raw": sv.p_raw, "q_value": sv.q_value,
            "failing_core_gates": [g for g in ("expectancy", "lifetime", "stability",
                                               "robustness", "significance")
                                   if not sv.gates.get(g, {}).get("pass")],
            "fold_means": st.get("fold_means"),
            "oos_positive_fold_frac": st.get("oos_positive_fold_frac"),
            "n_folds_evaluable": sv.gates.get("sample", {}).get("n_folds_evaluable"),
            "drop_best_retention": sv.gates.get("robustness", {}).get("retention"),
            "oos_mean_r_per_trade": sv.gates.get("expectancy", {}).get("oos_mean_r_per_trade"),
            "coverage_frac": cov.get("coverage_frac"),
            "weakest_coverage": cov.get("weakest_coverage"),
            "reasons": list(sv.reasons)}


def run_arm(sub, costs, allow, fam, *, walk: str, config: str, pop: str, band, option: str,
            spread_charged: bool) -> dict:
    t0 = time.time()
    o = OPTIONS[option]
    spec = o.with_(spec_id=f"{o.spec_id}_m3_{config}_{walk}"
                          f"{'' if spread_charged else '_nospread'}",
                   sleeve_symbol_allowlist=allow, spread_band=band)
    spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=fam)
    recs0 = {s: AD.to_records(r) for s, r in rows_for(sub, walk, config).items()}
    recs, spec, mix = EP.apply(pop, recs0, spec, account=ACCOUNT)
    ctx = contextlib.nullcontext() if spread_charged else spread_term_removed()
    with ctx:
        res = run_gate(recs, spec, costs=costs, server=SERVER)
    el = time.time() - t0
    stamp = {"walk": walk, "walk_band": BAND_OF_WALK[walk], "spread_charged": spread_charged,
             "config": config, "exit": CONFIGS[config], "population": pop,
             "band": band if band is not None else "flat_37_day_snapshot",
             "band_is_control": band is None, "option": option,
             "population_mix": mix, "seconds": round(el, 2)}
    return {s: _row(res.verdicts.get(s), res, spec, sleeve=s, **stamp) for s in CELLS}


# =====================================================================================

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="grid", choices=("parity", "grid"))
    args = ap.parse_args()

    sub = load_substrate()
    costs = AD.load_broker_true_costs(AD.COSTS)
    allow = AD.allowlist()
    fam27 = CF.load_candidate_family(DECL_V27)
    fam2 = CF.load_candidate_family(DECL_V2)
    print(f"family V27  CANDIDATE_BOOK_V1: all_declared="
          f"{fam27.effective_size('CANDIDATE_BOOK_V1', 'all_declared')} "
          f"looks={fam27.effective_size('CANDIDATE_BOOK_V1', 'looks_taken')}", flush=True)
    print(f"family V2   CANDIDATE_BOOK_V1: all_declared="
          f"{fam2.effective_size('CANDIDATE_BOOK_V1', 'all_declared')} "
          f"looks={fam2.effective_size('CANDIDATE_BOOK_V1', 'looks_taken')}", flush=True)

    doc: dict = {
        "schema": "gtos.wave20.m3.regate.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "what": ("the estate's standing admission and its two co-judged cells, re-gated at "
                 "the ratified rule with lane r1's quote-side-corrected walker"),
        "substrate": str(SUB.relative_to(REPO)),
        "ratified_rule": {
            "population": "RECORDED", "option": "B_balanced", "alpha": 0.10,
            "family": "CANDIDATE_BOOK_V1", "basis": "all_declared",
            "family_artifact": str(DECL_V27.relative_to(REPO)),
            "source": str(AN_OUT.relative_to(REPO)) + " -> ratified_rule; "
                      "phase8/receipts/CANDIDATE_FAMILY_V1.json -> ratified_rule"},
        "family_sizes": {
            "V27_all_declared": fam27.effective_size("CANDIDATE_BOOK_V1", "all_declared"),
            "V27_looks_taken": fam27.effective_size("CANDIDATE_BOOK_V1", "looks_taken"),
            "V2_all_declared": fam2.effective_size("CANDIDATE_BOOK_V1", "all_declared"),
            "V2_looks_taken": fam2.effective_size("CANDIDATE_BOOK_V1", "looks_taken")},
    }

    # ---- C2: the published arm must reproduce AN's p_raw ----------------------------
    #: AN keys its arms `config|option|population|band|sleeve` with band in
    #: {flat,low,mid,high} (`POPULATION_RULE_V1.json -> grid.arms`).
    want = json.load(open(AN_OUT))["grid"]["arms"]
    print(f"AN published arms: {len(want)}", flush=True)

    checks = []
    t0 = time.time()
    for config in ("X_btc5R",):
        for pop in ("ALL_ERAS", "RECORDED", "DECIDABLE", "RECORDED_AND_DECIDABLE"):
            got = run_arm(sub, costs, allow, fam2, walk="old", config=config, pop=pop,
                          band="mid", option="B_balanced", spread_charged=True)
            for s in CELLS:
                ref = want.get(f"{config}|B_balanced|{pop}|mid|{s}")
                checks.append({
                    "cell": f"{s}@{CONFIGS[config][s]}", "population": pop,
                    "an_p_raw": (ref or {}).get("p_raw"), "here_p_raw": got[s]["p_raw"],
                    "an_n": (ref or {}).get("n_trades"), "here_n": got[s]["n_trades"],
                    "an_verdict": (ref or {}).get("verdict"), "here_verdict": got[s]["verdict"],
                    "an_pooled": (ref or {}).get("pooled_oos_mean_r"),
                    "here_pooled": got[s]["pooled_oos_mean_r"]})
            print(f"  C2 {pop:24s} {time.time()-t0:5.0f}s", flush=True)
    def _close(a, b, tol=5e-4):
        return (a is None and b is None) or (
            a is not None and b is not None and abs(float(a) - float(b)) <= tol)
    doc["C2_parity_vs_AN"] = {
        "note": ("run at AN's OWN declared family (V2) so p_raw is comparable; the grid "
                 "below uses the V27 tip, which moves q and never p_raw"),
        "n_identical_p_raw": sum(1 for c in checks if _close(c["an_p_raw"], c["here_p_raw"])),
        "n_checked": len(checks),
        "n_identical_n_trades": sum(1 for c in checks if c["an_n"] == c["here_n"]),
        "checks": checks}
    print(json.dumps(doc["C2_parity_vs_AN"], indent=1)[:4000])

    if args.stage == "parity":
        OUT.with_name("M3_REGATE_PARITY_V1.json").write_text(json.dumps(doc, indent=1))
        return 0

    # ---- the grid --------------------------------------------------------------------
    grid = []
    for config in CONFIGS:
        for walk in WALKS:
            for pop in POPS:
                for band in BANDS:
                    # the walk's own band and the cost band must agree; the `old` walk is
                    # priced on all four, as AN priced it.
                    if walk != "old" and band != BAND_OF_WALK[walk]:
                        continue
                    for option in ("B_balanced", "A_strict"):
                        for charged in (True, False):
                            r = run_arm(sub, costs, allow, fam27, walk=walk, config=config,
                                        pop=pop, band=band, option=option,
                                        spread_charged=charged)
                            grid.extend(r[s] for s in CELLS)
            print(f"  {config:9s} walk={walk:8s} arms={len(grid)} "
                  f"{time.time()-t0:6.0f}s", flush=True)
    doc["grid"] = grid
    doc["n_arms"] = len(grid)
    doc["generated"] = dt.datetime.now(dt.timezone.utc).isoformat()
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True))
    print("WROTE", OUT, len(grid), "rows")

    # ---- the headline the owner asked for --------------------------------------------
    def pick(sleeve, walk, charged, pop="RECORDED", band="mid", option="B_balanced",
             config="X_btc5R"):
        for r in grid:
            if (r["sleeve"] == sleeve and r["walk"] == walk and r["config"] == config
                    and r["spread_charged"] is charged and r["population"] == pop
                    and r["band"] == band and r["option"] == option):
                return r
        return None
    for s in CELLS:
        print(f"\n=== {s} @ {CONFIGS['X_btc5R'][s]} — RECORDED / mid / B_balanced / V27")
        for walk in ("old", "qs_mid"):
            for charged in (True, False):
                r = pick(s, walk, charged)
                if r:
                    print(f"  walk={walk:7s} spread_charged={str(charged):5s} "
                          f"n={r['n_trades']} verdict={r['verdict']:14s} "
                          f"pooled={r['pooled_oos_mean_r']} p={r['p_raw']} q={r['q_value']} "
                          f"fail={r['failing_core_gates']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
