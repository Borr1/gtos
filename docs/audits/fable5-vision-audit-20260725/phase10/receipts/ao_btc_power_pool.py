"""Session AO, item 3 — `mx_btcusd`'s power pool: AL §10 item 1, never run.

    python3 docs/audits/fable5-vision-audit-20260725/phase10/receipts/ao_btc_power_pool.py

THE QUESTION, AND WHY IT IS NOT THE ONE AF ANSWERED
--------------------------------------------------
AF refuted the nine-symbol crypto cluster as **DIVERSIFICATION**: dispersion ratio 4.74,
best-to-worst 1.80 R/trade, prescription `MEMBER_CONDITIONING_NOT_BREADTH`. That is a
statement about whether the members are one thing. **Pooling for POWER is a different
question**: `mx_btcusd @ target_5R` rests on 318 trades on one symbol over nine years, and the
gate's null is a day-blocked sign flip on the pooled DAILY series, so more series means more
blocks and a better-resolved p — *if* the extra series carry comparable per-day edge.

THE PREDICTION, STATED BEFORE THE RUN BECAUSE IT IS FALSIFIABLE AND IT DECIDES THE READING
-----------------------------------------------------------------------------------------
Pooling buys resolution as **sqrt(blocks)** and spends effect size linearly. AL §2 measured
exactly that trade going the wrong way on `sub_xvol_pullback`'s threshold variant: n rose
88 -> 406, blocks rose only 11 -> 24 (sqrt 1.48x) and the per-trade edge fell 3.3x, so the
t-statistic went DOWN. Nine crypto symbols break out on the same days -- a donchian-20 breakout
is a common-factor event -- so the prediction here is:

  * `n_trades` grows a lot (318 -> ~1,207 over all nine);
  * `n_oos_days` grows much less, because the days overlap;
  * and if the siblings' per-day contribution is worse than BTC's, the pooled p is WORSE than
    the solo p despite the extra trades.

Every arm therefore reports `n_trades`, `n_oos_days` and their ratio, so the mechanism is
visible rather than inferred. If the pooled cell admits where the solo cell is band-fragile
(AL A4: solo REJECTS at `band_high`, p 0.0051), that is the robustness the admission lacks —
and that specific comparison is the one the commission asked for, so it is run at every band.

THE MEMBER SETS, DECLARED AS LITERALS BEFORE THE RUN
---------------------------------------------------
`POOL_ARMS` below. Two of the four inclusion rules are outcome-INDEPENDENT and two are not,
and the split is stamped on every arm:

  solo_btc                 the control -- must reproduce AL's 232 / +0.98169 / p 0.0011
  pool_all9                every member of AF's family. No selection of any kind.
  pool_n_ge_100            members with >= 100 reachable trades. OUTCOME-INDEPENDENT: trade
                           count is decided by the generator and the archive, never by a
                           return -- the same class of restriction as `look_taken` and
                           `coverage_policy` (`candidate_family.py:120-124`).
  pool_coherent_positive   AK §4's two-clause test on the NET basis. This IS selection on the
                           outcome and it is labelled that way on every row; AH §4.2 measured
                           member selection inside these families as worth -0.0045 R/trade
                           out of sample (a coin flip), which is the prior it has to beat.

THE COMMISSION'S CITATION, CORRECTED
-----------------------------------
It says "the coherent-positive members per AK §4's net-basis table". AK §4's table covers
`vol_squeeze`, `ny_index_momentum`, `session_leadlag_genuine` and three `structural_retest`
cells — **not** the donchian crypto family, which is AF's. What AK §4 supplies is the RULE
(run the two-clause test on the `mean_gross_r` / `mean_net_r` pair the gate already emits over
one matched population, never gross-from-trades against net-from-diagnostics), and that rule is
what is applied here to AF's family. Said out loud because a reader following the citation
would find a table that does not contain these members.

Offline, pure, no broker import, no config edit.
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import importlib.util
import json
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
    measured_n_trials,
)
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward import candidate_family as CF  # noqa: E402
from src.research_infra.walkforward import fidelity as FID  # noqa: E402

HERE = Path(__file__).resolve().parent
AUD = REPO / "docs/audits/fable5-vision-audit-20260725"
AA_DIR = AUD / "phase6/receipts"
AD_DIR = AUD / "phase7/receipts"
AF_DIR = AUD / "phase7/receipts"
DECL = HERE / "CANDIDATE_FAMILY_V3.json"
OUT = HERE / "BTC_POWER_POOL_V1.json"

SERVER = "FTMO-Server3"
ACCOUNT = "FTMO"
POOL = "fam_ao_btc_power_pool_crypto_d1"
BTC_AA = "mx_btcusd_d1_donchian_20_breakout"
BTC_AF = "mxf_donchian_20_breakout_btcusd_d1"
AF_FAMILY = "fam_donchian_20_breakout_crypto_d1"

BAND_ARMS: tuple[tuple[str, str | None, tuple[str, ...]], ...] = (
    ("flat", None, ("ALL_ERAS",)),
    ("low", "low", ("RECORDED",)),
    ("mid", "mid", ("ALL_ERAS", "RECORDED", "DECIDABLE")),
    ("high", "high", ("RECORDED",)),
)

#: The member sets, and the ONE thing about each that a reader has to know: whether its
#: inclusion rule could have seen a return. Declared as a literal before the run.
POOL_ARMS: dict[str, dict] = {
    "solo_btc": {
        "rule": "BTCUSD only",
        "outcome_independent": True,
        "why": ("the control. It must reproduce AL's solo figures exactly, or every pooled "
                "number below is measuring this file's plumbing instead of the pool."),
    },
    "pool_all9": {
        "rule": "every member of AF's fam_donchian_20_breakout_crypto_d1",
        "outcome_independent": True,
        "why": ("the primary arm and the only one with no selection at all. If pooling for "
                "power works, it works here."),
    },
    "pool_n_ge_100": {
        "rule": "members with >= 100 reachable trades",
        "outcome_independent": True,
        "why": ("five of the nine members carry 33-37 trades, which is fewer than one trade "
                "per year of archive; a member that thin adds a noisy daily series without "
                "adding a resolvable block. The n >= 100 floor is a property of the generator "
                "and the archive and cannot see a return -- the same class of restriction as "
                "`Member.look_taken` (candidate_family.py:120-124)."),
        "min_n": 100,
    },
    "pool_coherent_positive": {
        "rule": ("AK §4's two-clause test on the NET basis: members whose own net mean R is "
                 "positive, on the matched priced population the gate itself emits"),
        "outcome_independent": False,
        "why": ("this IS selection on the outcome. It is run because the commission names it, "
                "and it is reported against the prior AH §4.2 established: carrier selection "
                "inside these families is worth -0.004525 R/trade trade-weighted out of "
                "sample, i.e. nothing. Any gain here has to be read against that."),
    },
}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_EST_MEMO: dict = {}


def _est(smodel, symbol, entry_utc, band):
    k = (symbol, entry_utc, band)
    if k not in _EST_MEMO:
        try:
            e = smodel.estimate(symbol, ACCOUNT, entry_utc, band=band)
            _EST_MEMO[k] = (e.era_class, bool(e.decidable))
        except Exception as exc:  # noqa: BLE001
            _EST_MEMO[k] = (f"UNPRICEABLE:{type(exc).__name__}", False)
    return _EST_MEMO[k]


def _restrict(recs: dict, pop: str, smodel, band: str | None) -> tuple[dict, dict]:
    if pop == "ALL_ERAS":
        return recs, {}
    if band is None:
        raise ValueError(f"population {pop!r} needs a band")
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
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    t0 = time.time()

    AA = _load(AA_DIR / "aa_estate_walk.py", "ao_pool_aa")
    AD = _load(AD_DIR / "ad_exit_sweep.py", "ao_pool_ad")
    from src.costs.spread_model import load_spread_model

    smodel = load_spread_model()
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AO")
    fam = CF.load_candidate_family(DECL)
    m_all = fam.effective_size("CANDIDATE_BOOK_V1")
    declared_names = {m.name for m in fam.family("CANDIDATE_BOOK_V1").members}
    if POOL not in declared_names:
        raise SystemExit(f"REFUSING: {POOL} is not declared in {DECL.name}. The pool is a new "
                         f"hypothesis and must be in the prospective declaration before it is "
                         f"gated.")
    print(f"declared family {m_all}; {POOL} declared: True")

    aa_raw = json.load(gzip.open(AA_DIR / "AA_ESTATE_TRADES.json.gz", "rt"))
    base_rows = {s: list(r) for s, r in aa_raw["trades"].items()}
    af_raw = json.load(gzip.open(AF_DIR / "AF_FAMILY_TRADES.json.gz", "rt"))
    members = list(af_raw["grid"]["families"][AF_FAMILY]["symbols"])
    member_names = [m for m in af_raw["trades"]
                    if m.startswith("mxf_donchian_20_breakout_") and m.endswith("_d1")
                    and m.split("_")[-2].upper() in {s.upper() for s in members}]
    if len(member_names) != 9:
        raise SystemExit(f"REFUSING: expected 9 crypto D1 donchian members, found "
                         f"{len(member_names)}: {sorted(member_names)}")
    costs = AA.load_broker_true_costs(AA.COSTS_V1_1)
    series, index, _res = AD.load_bars()
    rule = AD.resolve_rule(SERVER)
    print(f"loaded {len(series)} bar series in {time.time()-t0:.0f}s")

    #  AF rows carry `member`; AA rows carry `sleeve`. Everything else the exit re-simulation
    #  and `to_records` read is present and identical -- proved by the control below, not
    #  assumed.
    def af_rows(member: str, sleeve: str) -> list[dict]:
        return [dict(r, sleeve=sleeve, r_gross_plain=r["r_gross"], intra_size=1.0,
                     bar_decision_day=r["decision_day"], exit_policy="plain",
                     features={"bar_decision_day": r["decision_day"]},
                     _member=member, _symbol=r["symbol"])
                for r in af_raw["trades"][member] if r["engine_reachable"]]

    out = {
        "schema": "gtos.wave10.ao.btc_power_pool.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "session": "AO", "blocks": "B1300-B1349",
        "question": ("does pooling `mx_btcusd` with its eight donchian-D1 crypto siblings as "
                     "ONE hypothesis buy the POWER the solo cell lacks -- and does it admit "
                     "where the solo cell is band-fragile (AL A4: solo REJECTS at band_high, "
                     "p 0.0051)?"),
        "prediction_stated_before_the_run": (
            "pooling buys resolution as sqrt(blocks) and spends effect size linearly. A "
            "donchian-20 breakout is a common-factor event, so nine crypto symbols fire on "
            "overlapping DAYS: `n_trades` should grow ~3.8x while `n_oos_days` grows much "
            "less. If the siblings' per-day contribution is worse than BTC's, the pooled p is "
            "WORSE than the solo p despite the extra trades -- which is what AL §2 measured on "
            "the threshold variant (n 88->406, blocks 11->24, per-trade edge /3.3, t DOWN)."),
        "af_refutation_this_does_not_contradict": (
            "AF refuted this cluster as DIVERSIFICATION (dispersion ratio 4.74, "
            "MEMBER_CONDITIONING_NOT_BREADTH). Diversification asks whether the members are "
            "one thing; power asks whether more series resolve one p. Both can be true, and "
            "the dispersion is re-measured here on the NET basis per AK §4's correction so the "
            "incoherence the pool is being run DESPITE is priced rather than ignored."),
        "commission_citation_corrected": (
            "the commission cites 'the coherent-positive members per AK §4's net-basis table'. "
            "AK §4's table covers vol_squeeze / ny_index_momentum / session_leadlag_genuine / "
            "three structural_retest cells -- not this family, which is AF's. What AK §4 "
            "supplies is the RULE (two-clause test on the gate's own matched "
            "mean_gross_r / mean_net_r pair), and that is what is applied."),
        "members": sorted(member_names),
        "pool_arms_declared": POOL_ARMS,
        "declared_family": {
            "path": str(DECL.relative_to(REPO)), "sha256": fam.sha256,
            "all_declared": m_all,
            "membership_sha256": fam.membership_of("CANDIDATE_BOOK_V1"),
            "bh_rank_1_at_alpha_0.10": round(0.10 / m_all, 6),
            "bh_rank_2_at_alpha_0.10": round(0.20 / m_all, 6),
            "pool_is_a_declared_member": True,
        },
        "controls": {}, "member_basis": {}, "arms": {},
    }

    # ---- C1: AF's BTC member must BE AA's, exactly ----------------------------------------
    aa_btc = base_rows[BTC_AA]
    af_btc = af_rows(BTC_AF, POOL)
    aa_keys = {(r["symbol"], r["decision_bar_iso"]): r for r in aa_btc}
    af_keys = {(r["symbol"], r["decision_bar_iso"]): r for r in af_btc}
    same_r = sum(1 for k, r in af_keys.items()
                 if k in aa_keys and abs(aa_keys[k]["r_gross"] - r["r_gross"]) < 1e-12)
    out["controls"]["af_btc_member_is_aa_btc_sleeve"] = {
        "question": ("the pool is built from AF's artifact and the solo comparator from AA's. "
                     "Are AF's and AA's BTC populations the SAME trades with the same r_gross? "
                     "If not, every pool-vs-solo difference below is partly an artifact "
                     "difference."),
        "n_aa": len(aa_keys), "n_af": len(af_keys),
        "n_key_intersection": len(set(aa_keys) & set(af_keys)),
        "n_r_gross_identical_to_1e-12": same_r,
        "identical": len(aa_keys) == len(af_keys) == same_r == len(set(aa_keys) & set(af_keys)),
        "aa_only": sorted(f"{s}|{i}" for s, i in (set(aa_keys) - set(af_keys)))[:10],
        "af_only": sorted(f"{s}|{i}" for s, i in (set(af_keys) - set(aa_keys)))[:10],
    }
    print(f"CONTROL AF-btc == AA-btc: {same_r}/{len(aa_keys)} identical -> "
          f"{out['controls']['af_btc_member_is_aa_btc_sleeve']['identical']}")

    # ---- the exits -----------------------------------------------------------------------
    variants = {
        "as_walked": AD.AS_WALKED,
        "target_5R": AD.Variant(name="target_5R", family="target", target_mode="fixed_r",
                                target_r=5.0),
    }

    # per member, per exit, the rows
    per_member: dict[str, dict[str, list[dict]]] = {}
    for m in sorted(member_names):
        rows0 = af_rows(m, POOL)
        per_member[m] = {}
        for vn, v in variants.items():
            if vn == "as_walked":
                per_member[m][vn] = rows0
            else:
                rs, _tel = AD.resimulate(rows0, v, series, index, costs, ACCOUNT, rule)
                per_member[m][vn] = rs
        print(f"  {m:44s} as_walked n={len(per_member[m]['as_walked']):4d} "
              f"target_5R n={len(per_member[m]['target_5R']):4d}")

    # ---- the member basis: gross AND net over ONE matched population (AK §4's rule) -------
    #  Run the pool once with diagnose=True to get the gate's own priced rows, then take
    #  per-member gross and net from the SAME rows. AK §4.1's defect was reading gross from
    #  trades and net from `diagnostics.by_symbol`, which are different populations.
    allow = dict(AA.allowlist())
    from src.research_infra.walkforward.options import OPTIONS
    o = OPTIONS["B_balanced"]

    def _pool_recs(names: list[str], exit_name: str) -> dict:
        rows = [r for m in names for r in per_member[m][exit_name]]
        recs = {s: AD.to_records(r) for s, r in base_rows.items()}
        recs[POOL] = AD.to_records(rows)
        return recs

    def _register(names: list[str]):
        FID.clear_surface_expansions()
        FID.register_surface_expansion(
            POOL, parent=BTC_AA, symbol=f"{len(names)} crypto symbols", timeframe="D1",
            surface_note=("Session AO power pool: the donchian-D1 crypto family judged as ONE "
                          "series. `TRANSFERRED_CLASS` is the conservative stamp -- the book "
                          "has live recall for the parent's own symbol only, and the eight "
                          "siblings were never observed live."))

    syms_of = {m: sorted({r["symbol"] for r in per_member[m]["as_walked"]})
               for m in member_names}
    all9 = sorted(member_names)
    _register(all9)
    allow[POOL] = tuple(sorted({s for m in all9 for s in syms_of[m]}))
    spec = o.with_(spec_id=f"{o.spec_id}_ao_pool_basis", sleeve_symbol_allowlist=allow,
                   spread_band="mid")
    spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=fam)
    res = run_gate(_pool_recs(all9, "target_5R"), spec, costs=costs, diagnose=True,
                   server=SERVER)
    priced = res.priced_by_sleeve.get(POOL) or []
    if not priced:
        raise SystemExit("REFUSING: no priced rows for the pool under diagnose=True; the "
                         "member basis cannot be measured and a silent null here would read "
                         "as 'measured'.")
    by_sym_g, by_sym_n = collections.defaultdict(list), collections.defaultdict(list)
    for p in priced:
        if p.status != "priced" or p.r_net is None:
            continue
        by_sym_g[p.trade.symbol].append(p.trade.r_gross)
        by_sym_n[p.trade.symbol].append(p.r_net)
    basis = {}
    for sym in sorted(by_sym_g):
        basis[sym] = {"n_priced": len(by_sym_g[sym]),
                      "mean_gross_r": round(statistics.mean(by_sym_g[sym]), 5),
                      "mean_net_r": round(statistics.mean(by_sym_n[sym]), 5)}

    def _disp(vals):
        v = [x for x in vals if x is not None]
        if len(v) < 2:
            return None, 0, len(v)
        m = statistics.mean(v)
        return ((statistics.pstdev(v) / abs(m)) if m else float("inf"),
                sum(1 for x in v if x > 0), len(v))
    gr, gp, gk = _disp([b["mean_gross_r"] for b in basis.values()])
    nr, np_, nk = _disp([b["mean_net_r"] for b in basis.values()])
    coherent = sorted(s for s, b in basis.items() if b["mean_net_r"] > 0)
    out["member_basis"] = {
        "basis_note": ("gross and net over the SAME priced rows the gate emitted, at "
                       "target_5R / mid band. AK §4.1's defect was gross-from-trades against "
                       "net-from-diagnostics, which are different populations."),
        "per_symbol": basis,
        "two_clause_test": {
            "gross": {"dispersion_ratio": gr, "n_positive": gp, "k": gk,
                      "coheres": bool(gr is not None and gr < 1.0 and gp == gk)},
            "net": {"dispersion_ratio": nr, "n_positive": np_, "k": nk,
                    "coheres": bool(nr is not None and nr < 1.0 and np_ == nk)},
            "af_published_gross_ratio_on_its_own_basis": 4.74,
            "af_basis": ("AF measured 4.74 on gross R at its own exit and cost basis; this row "
                         "is at target_5R and the mid band, so it is a DIFFERENT stamp and the "
                         "two must not be differenced."),
        },
        "coherent_positive_symbols_on_net": coherent,
        "coherent_positive_is_selection_on_the_outcome": True,
    }
    print(f"\nmember basis: gross ratio {gr} ({gp}/{gk} positive), net ratio {nr} "
          f"({np_}/{nk} positive); coherent-positive on net: {coherent}")

    # ---- resolve the four member sets -----------------------------------------------------
    sets: dict[str, list[str]] = {
        "solo_btc": [BTC_AF],
        "pool_all9": all9,
        "pool_n_ge_100": sorted(m for m in all9
                                if len(per_member[m]["as_walked"]) >= 100),
        "pool_coherent_positive": sorted(
            m for m in all9 if set(syms_of[m]) & set(coherent)),
    }
    for k, v in sets.items():
        out["pool_arms_declared"][k]["members_resolved"] = v
        out["pool_arms_declared"][k]["k_members"] = len(v)
        out["pool_arms_declared"][k]["symbols"] = sorted(
            {s for m in v for s in syms_of[m]})
    print("\nmember sets:")
    for k, v in sets.items():
        print(f"  {k:24s} k={len(v)} {[m.split('_')[-2] for m in v]}")

    # ---- the grid -------------------------------------------------------------------------
    band_arms = tuple((lb, bv, tuple(p for p in ps if not (args.quick and p == "DECIDABLE")))
                      for lb, bv, ps in BAND_ARMS)
    for arm_name, names in sets.items():
        _register(names)
        allow[POOL] = tuple(sorted({s for m in names for s in syms_of[m]}))
        for exit_name in sorted(variants):
            recs_all = _pool_recs(names, exit_name)
            for band_label, band_val, pops_here in band_arms:
                for pop in pops_here:
                    recs, mix = _restrict(recs_all, pop, smodel, band_val)
                    key = f"{arm_name}|{exit_name}|band={band_label}|{pop}"
                    if POOL not in recs:
                        out["arms"][key] = {"pool_arm": arm_name, "exit": exit_name,
                                            "spread_band": band_label, "population": pop,
                                            "skipped": "no trade survives the restriction"}
                        continue
                    sp = o.with_(spec_id=f"{o.spec_id}_ao_pool",
                                sleeve_symbol_allowlist=allow,
                                **({"spread_band": band_val} if band_val else {}))
                    sp = CF.with_declared_family(sp, "CANDIDATE_BOOK_V1", loaded=fam)
                    r = run_gate(recs, sp, costs=costs, server=SERVER)
                    sv = r.verdicts.get(POOL)
                    arm = {
                        "pool_arm": arm_name, "k_members": len(names),
                        "outcome_independent_inclusion": POOL_ARMS[arm_name][
                            "outcome_independent"],
                        "exit": exit_name, "spread_band": band_label, "population": pop,
                        "spread_band_meaning": ("spec.py:82 flat_37_day_snapshot"
                                                if band_val is None else
                                                f"era-banded `{band_val}`"),
                        "declared_family_size": sp.declared_family_size,
                        "declared_family_id": sp.declared_family_id,
                        "effective_family_size": r.family["multiplicity"][
                            "effective_family_size"],
                        "n_sleeves_judged": r.family["multiplicity"][
                            "n_sleeves_judged_this_run"],
                        "spec_sha256": sp.seal(),
                        "era_mix": mix.get(POOL),
                        "fidelity_stamp": "TRANSFERRED_CLASS via register_surface_expansion",
                        **({} if sv is None else row_of(sv)),
                    }
                    out["arms"][key] = arm
                    ledger.record(
                        mechanism="power_pool", sleeve=POOL,
                        variant={"pool_arm": arm_name, "k_members": len(names),
                                 "exit": exit_name, "band": band_label, "population": pop,
                                 "declared_family_size": sp.declared_family_size},
                        window="full_archive", spec_sha256=sp.seal(),
                        outcome={"ADMIT": "admitted", "REJECT": "rejected",
                                 "NOT_EVALUABLE": "not_evaluable"}.get(
                            (sv.verdict.value if sv else ""), "evaluated"),
                        metric=(sv.pooled_oos_mean_r if sv else None),
                        metric_name="pooled_oos_mean_r",
                        note=f"AO power pool {key}")
                    print(f"  {key:56s} n={arm.get('n_trades')} days={arm.get('n_oos_days')} "
                          f"{arm.get('verdict')} R/d={arm.get('pooled_oos_mean_r')} "
                          f"p={arm.get('p_raw')}", flush=True)
    FID.clear_surface_expansions()

    # ---- C2: the solo arm must reproduce AL's published figures ---------------------------
    solo = out["arms"].get("solo_btc|target_5R|band=mid|RECORDED") or {}
    out["controls"]["solo_reproduces_AL"] = {
        "question": ("AL published `mx_btcusd @ target_5R` on RECORDED@mid at n 232, pooled "
                     "+0.98169 R/day, p_raw 0.0011. Does the solo arm reproduce it through "
                     "this file's pool plumbing and AF's trade artifact?"),
        "al_published": {"n_trades": 232, "pooled_oos_mean_r": 0.98169, "p_raw": 0.0011},
        "here": {"n_trades": solo.get("n_trades"),
                 "pooled_oos_mean_r": solo.get("pooled_oos_mean_r"),
                 "p_raw": solo.get("p_raw"), "verdict": solo.get("verdict")},
        "n_matches": solo.get("n_trades") == 232,
        "r_matches_to_1e-4": bool(solo.get("pooled_oos_mean_r") is not None
                                  and abs(solo["pooled_oos_mean_r"] - 0.98169) < 1e-4),
        "p_matches_to_1e-4": bool(solo.get("p_raw") is not None
                                  and abs(solo["p_raw"] - 0.0011) < 1e-4),
        "note": ("AL's q was 0.0385 at m=35; here m=39, so q MUST differ and p_raw must not. "
                 "AL published R/day and p to 5 and 4 significant figures respectively, so the "
                 "tolerance is theirs, not a slack this file chose."),
    }
    print(f"\nCONTROL solo vs AL: n {solo.get('n_trades')} R/day "
          f"{solo.get('pooled_oos_mean_r')} p {solo.get('p_raw')}")

    # ---- the power accounting, which is the whole point -----------------------------------
    power = {}
    for exit_name in sorted(variants):
        for band_label, _bv, pops_here in band_arms:
            for pop in pops_here:
                base = out["arms"].get(f"solo_btc|{exit_name}|band={band_label}|{pop}")
                if not base or base.get("n_oos_days") is None:
                    continue
                rows = {}
                for arm_name in sets:
                    a = out["arms"].get(f"{arm_name}|{exit_name}|band={band_label}|{pop}")
                    if not a or a.get("n_trades") is None:
                        continue
                    rows[arm_name] = {
                        "k_members": a.get("k_members"),
                        "n_trades": a.get("n_trades"), "n_oos_days": a.get("n_oos_days"),
                        "trades_vs_solo": (round(a["n_trades"] / base["n_trades"], 3)
                                           if base.get("n_trades") else None),
                        "days_vs_solo": (round(a["n_oos_days"] / base["n_oos_days"], 3)
                                         if base.get("n_oos_days") else None),
                        "R_per_day": a.get("pooled_oos_mean_r"),
                        "R_per_trade": a.get("oos_mean_r_per_trade"),
                        "p_raw": a.get("p_raw"), "verdict": a.get("verdict"),
                        "drop_best_retention": a.get("drop_best_retention"),
                        "oos_positive_fold_frac": a.get("oos_positive_fold_frac"),
                        "outcome_independent_inclusion": a.get(
                            "outcome_independent_inclusion"),
                    }
                power[f"{exit_name}|band={band_label}|{pop}"] = {
                    "solo_n_trades": base.get("n_trades"),
                    "solo_n_oos_days": base.get("n_oos_days"),
                    "solo_p_raw": base.get("p_raw"),
                    "arms": rows,
                }
    out["power_accounting"] = {
        "why": ("the gate's null is a day-blocked sign flip on the pooled DAILY series "
                "(`stats.block_permutation_p`), so the n that buys resolution is DAYS, not "
                "trades. `days_vs_solo` beside `trades_vs_solo` is the whole mechanism: "
                "pooling helps only when the days grow, and the ratio between the two columns "
                "measures how much of the extra sample is a common-factor duplicate."),
        "rows": power,
    }

    # ---- the answer -----------------------------------------------------------------------
    admits = sorted(k for k, a in out["arms"].items() if a.get("verdict") == "ADMIT")
    band_frag = {}
    for arm_name in sets:
        row = {}
        for bl in ("low", "mid", "high"):
            a = out["arms"].get(f"{arm_name}|target_5R|band={bl}|RECORDED")
            if a:
                row[bl] = {"p_raw": a.get("p_raw"), "verdict": a.get("verdict"),
                           "R_per_day": a.get("pooled_oos_mean_r")}
        band_frag[arm_name] = row
    out["band_fragility_the_commission_asked_about"] = {
        "question": ("AL A4: the SOLO cell admits at band low and mid and REJECTS at band_high "
                     "(p 0.0051). Does any pooled arm admit across the whole envelope?"),
        "rows": band_frag,
        "reading": ("an arm that admits at all three bands is the robustness the solo "
                    "admission lacks; an arm that admits at fewer is worse than the solo cell "
                    "and pooling has cost rather than bought."),
    }
    out["answer"] = {
        "admitting_arms": admits,
        "any_pooled_arm_admits": bool([k for k in admits if not k.startswith("solo_")]),
        "best_pooled_p": min(
            [(a["p_raw"], k) for k, a in out["arms"].items()
             if a.get("p_raw") is not None and not k.startswith("solo_")],
            default=None),
        "best_solo_p": min(
            [(a["p_raw"], k) for k, a in out["arms"].items()
             if a.get("p_raw") is not None and k.startswith("solo_")],
            default=None),
        "rank_1_bar": round(0.10 / m_all, 6), "rank_2_bar": round(0.20 / m_all, 6),
    }
    out["seconds_total"] = round(time.time() - t0, 1)
    out["trial_ledger"] = measured_n_trials(ledger_paths=[REPO / DEFAULT_TRIAL_LEDGER])
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e6:.2f} MB)")
    print(json.dumps(out["answer"], indent=1, default=str))
    return out


if __name__ == "__main__":
    main()
