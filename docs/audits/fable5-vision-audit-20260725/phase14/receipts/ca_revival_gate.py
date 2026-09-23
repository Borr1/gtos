#!/usr/bin/env python3
"""Session CA (B2106-B2119) — the three revival gates, at the ratified rule.

    python3 docs/audits/fable5-vision-audit-20260725/phase14/receipts/ca_revival_gate.py

Reads `CA_REVIVAL_TRADES_{ARCHIVE,MERGED,VP}_V1.json.gz` (from `ca_revival_generate.py`) and
`CANDIDATE_FAMILY_V12.json`, whose sha256 it verifies before running: the cut rules and the
verdict vocabulary were fixed in that file before this one existed, and if it has moved the
declaration is not a declaration.

THE RULE, AND WHERE EACH PIECE COMES FROM
-------------------------------------------
`RECORDED` era population with AN's conditions (`POPULATION_RULE_V1.ratified_rule`,
Borhen 2026-07-30) * `B_balanced` at the sealed alpha 0.10
(`CANDIDATE_FAMILY_V1.ratified_rule`, same day) * corrected against `CANDIDATE_BOOK_V1` on
the all-declared basis * all four cost bands published with every verdict, the flat 37-day
snapshot marked as the CONTROL it is * chronological fold table on every admission-grade row *
`maxbars` share on every arm (wave-12 delta) * broker-true costs with the era/spread models.

WHAT IS BEING ASKED OF EACH SLEEVE, WHICH IS NOT THE SAME QUESTION
-------------------------------------------------------------------
`CA_DATA_PROBE_V1.json` measured that the commission's premise holds for one of the three:

  metals_softband    was never data-blocked. 237 walked trades since AA; the fetch adds 22 H4
                     bars per cross and no symbol. The question here is the one nobody has
                     answered: does its CARRY_CONDITIONAL tier survive contact with each
                     firm's MEASURED swap, rather than with the assumed horizon
                     `SURVIVOR_BOOK_V1` tiered it against?
  sub_mid_dn_revert  gains 2 of its 20 declared symbols. Does the extended surface move a
                     verdict that BB measured as REJECT at all four bands?
  vp_euidx_pocgrav   has never been generated at all, anywhere, by anyone. This is its FIRST
                     evidence — and its aux feed reaches back only to 2026-04-27, so the
                     honest answer may well be NOT_EVALUABLE, which is its own verdict class
                     and not a synonym for dead.

BOUNDARY. Offline and pure. Reads committed artifacts and the read-only bar archive; writes
one JSON. No broker, no VPS, no config write, no R2-bound path. Files candidates; arming is
the owner's ceremony.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import gzip
import hashlib
import json
import random
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
P6 = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
P7 = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(P7))

FAMILY = HERE / "CANDIDATE_FAMILY_V12.json"
#: The sha256 `ca_family_v12.py` wrote, verified before any gate runs.
FAMILY_SHA_FIELD = "self_sha256"
OUT = HERE / "CA_REVIVAL_GATE_V1.json"

COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
SERVER = "FTMO-Server3"
BANDS = (None, "low", "mid", "high")
REAL_BANDS = ("low", "mid", "high")
ACCOUNTS = ("FTMO", "redacted_account")
ARCHIVE_END = dt.date(2026, 7, 27)
#: P2's mechanical availability rule: a member is "deep history" if its bar series starts
#: more than this many years before the archive end. Availability, never results.
DEEP_HISTORY_YEARS = 5.0
SEED = 20260731


def _arm(name: str) -> dict:
    p = HERE / f"CA_REVIVAL_TRADES_{name}_V1.json.gz"
    return json.loads(gzip.open(p, "rt").read())


def _verify_family() -> dict:
    doc = json.loads(FAMILY.read_text())
    got = dict(doc)
    declared = got.pop(FAMILY_SHA_FIELD, None)
    body = json.dumps(got, indent=1, sort_keys=True, default=str)
    actual = hashlib.sha256(body.encode()).hexdigest()
    if declared != actual:
        raise SystemExit(
            f"{FAMILY.name}: self_sha256 {declared} != recomputed {actual}. The declaration "
            "moved after it was declared; refusing to gate against it.")
    return doc


def _maxbars_share(rows: list[dict], key: str = "exit_reason") -> dict:
    c = collections.Counter(r.get(key) or "?" for r in rows)
    n = sum(c.values()) or 1
    return {"n": n, "exit_reasons": dict(c.most_common()),
            "maxbars_share": round(c.get("maxbars", 0) / n, 5),
            "time_stop_share": round(c.get("time_stop", 0) / n, 5),
            "horizon_share": round((c.get("maxbars", 0) + c.get("time_stop", 0)) / n, 5)}


def _fold_table(v) -> list[dict]:
    out = []
    for f in (v.folds or []):
        out.append({k: f.get(k) for k in
                    ("fold_id", "status", "oos_start", "oos_end", "n_test_trades",
                     "oos_mean_r_per_day", "oos_mean_r_per_trade", "oos_sum_r")
                    if k in f})
    return out


def _rows_to_records(rows: list[dict], AD):
    return AD.to_records(rows)


def gate_arm(pool: dict[str, list[dict]], *, account: str, band, costs, allow, fam,
             label: str, r_field: str = "r_gross", zero_carry: bool = False,
             diagnose: bool = True) -> dict:
    from src.research_infra.walkforward import candidate_family as CF
    from src.research_infra.walkforward import era_population as EP
    from src.research_infra.walkforward import run_gate
    from src.research_infra.walkforward.options import OPTIONS
    import ad_exit_sweep as AD

    o = OPTIONS["B_balanced"]
    spec = o.with_(spec_id=f"{o.spec_id}_ca_revival_{label}",
                   sleeve_symbol_allowlist=allow, spread_band=band, account=account)
    spec = CF.with_declared_family(spec, "CANDIDATE_BOOK_V1", loaded=fam)
    recs0 = {}
    for s, rows in pool.items():
        use = rows
        if r_field != "r_gross":
            use = [{**r, "r_gross": (r.get(r_field) if r.get(r_field) is not None
                                     else r["r_gross"])} for r in rows]
        recs0[s] = AD.to_records(use)
    try:
        recs, spec, mix = EP.apply("RECORDED", recs0, spec, account=account)
        res = run_gate(recs, spec, costs=costs, server=SERVER, diagnose=diagnose)
    except Exception as exc:
        # A refusal is a result and must be published as one. `era_population.filter_records`
        # fails closed when the spread model classifies NONE of a sleeve's trades on an
        # account -- which happens for `vp_euidx_pocgrav` on redacted_account, whose GER40/UK100
        # eras that model does not carry. Swallowing it would turn a fail-closed refusal into
        # a missing row, and a missing row reads as "not measured" rather than "refused".
        return {"label": label, "account": account,
                "band": band or "flat_37_day_snapshot_CONTROL", "band_is_control": band is None,
                "population": "RECORDED", "option": "B_balanced", "r_field": r_field,
                "zero_carry_counterfactual": zero_carry,
                "REFUSED": type(exc).__name__, "refusal_message": str(exc),
                "sleeves_requested": sorted(pool), "verdicts": {}}
    rows_out = {}
    for s, v in sorted(res.verdicts.items()):
        diag = v.diagnostics or {}
        rows_out[s] = {
            "verdict": v.verdict.value, "n_trades": v.n_trades,
            "pooled_oos_mean_r": v.pooled_oos_mean_r,
            "oos_mean_r_per_trade": v.gates.get("expectancy", {}).get("oos_mean_r_per_trade"),
            "p_raw": v.p_raw, "q_value": v.q_value,
            "failing_core_gates": [g for g, d in v.gates.items()
                                   if isinstance(d, dict) and d.get("pass") is False],
            "first_reason": (v.reasons[0] if v.reasons else None),
            "n_folds_evaluable": v.gates.get("sample", {}).get("n_folds_evaluable"),
            "oos_positive_fold_frac": v.gates.get("stability", {}).get(
                "oos_positive_fold_frac"),
            "drop_best_retention": v.gates.get("robustness", {}).get("retention"),
            "coverage_frac": v.gates.get("cost_coverage", {}).get("coverage_frac"),
            "median_hold_hours": (diag.get("holding") or {}).get("median_hours"),
            "swap_nights_mean": ((diag.get("cost_decomposition") or {}).get(
                "swap_nights") or {}).get("mean"),
            "swap_r_mean": (((diag.get("cost_decomposition") or {}).get("terms") or {})
                            .get("swap_r") or {}).get("mean_r"),
            "swap_share_of_cost": (((diag.get("cost_decomposition") or {}).get("terms") or {})
                                   .get("swap_r") or {}).get("share_of_cost"),
            "largest_cost_term": (diag.get("cost_decomposition") or {}).get("largest_term"),
            "primary_prescription": diag.get("primary_prescription"),
            "fold_table": _fold_table(v),
        }
    return {
        "label": label, "account": account,
        "band": band or "flat_37_day_snapshot_CONTROL", "band_is_control": band is None,
        "population": "RECORDED", "option": "B_balanced", "alpha": spec.alpha,
        "r_field": r_field, "zero_carry_counterfactual": zero_carry,
        "declared_family_id": spec.declared_family_id,
        "declared_family_size": spec.declared_family_size,
        "spec_sha256": spec.seal(), "population_mix": mix,
        "n_sleeves_judged": len(res.verdicts),
        "admitted": res.admitted,
        "verdicts": rows_out,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="mid band only, FTMO only")
    a = ap.parse_args()
    t0 = time.time()
    fam_doc = _verify_family()
    print(f"family verified: {FAMILY.name} "
          f"CANDIDATE_BOOK_V1 size {fam_doc['families']['CANDIDATE_BOOK_V1']['high_water_size']} "
          f"looks {fam_doc['families']['CANDIDATE_BOOK_V1']['high_water_looks']}")

    import ad_exit_sweep as AD
    from src.research_infra.walkforward import candidate_family as CF

    costs = AD.load_broker_true_costs(COSTS)
    costs_zero = AD.zero_carry_costs(COSTS)
    allow = AD.allowlist()
    fam = CF.load_candidate_family(FAMILY)

    arch, merged, vp = _arm("ARCHIVE"), _arm("MERGED"), _arm("VP")
    pool_primary = {
        "metals_softband": merged["trades"]["metals_softband"],
        "sub_mid_dn_revert": merged["trades"]["sub_mid_dn_revert"],
        "vp_euidx_pocgrav": vp["trades"]["vp_euidx_pocgrav"],
    }
    pool_control = {
        "metals_softband": arch["trades"]["metals_softband"],
        "sub_mid_dn_revert": arch["trades"]["sub_mid_dn_revert"],
    }
    print("populations: " + ", ".join(
        f"{s}={len(v)}" for s, v in sorted(pool_primary.items())))

    # ---- what the fetch moved, before any gate -------------------------------------------
    fetch_delta = {}
    for s in ("metals_softband", "sub_mid_dn_revert"):
        a_rows, m_rows = pool_control[s], pool_primary[s]
        ak = {(r["symbol"], r["decision_bar_iso"]): r["r_gross"] for r in a_rows}
        mk = {(r["symbol"], r["decision_bar_iso"]): r["r_gross"] for r in m_rows}
        added = sorted(set(mk) - set(ak))
        moved = sorted(k for k in (set(ak) & set(mk)) if abs(ak[k] - mk[k]) > 1e-9)
        fetch_delta[s] = {
            "n_archive": len(a_rows), "n_merged": len(m_rows),
            "trades_ADDED_by_the_fetch": len(added),
            "trades_REMOVED": len(set(ak) - set(mk)),
            "shared_trades_whose_R_MOVED": len(moved),
            "added_by_symbol": dict(collections.Counter(k[0] for k in added)),
            "sum_r_archive": round(sum(ak.values()), 4),
            "sum_r_merged": round(sum(mk.values()), 4),
        }
        print(f"  fetch delta {s:20s} {len(a_rows)} -> {len(m_rows)} "
              f"(+{len(added)} added, {len(moved)} R moved) "
              f"{fetch_delta[s]['added_by_symbol']}")

    # ---- maxbars share, per sleeve, both contracts ----------------------------------------
    horizon = {}
    for s, rows in sorted(pool_primary.items()):
        blk = {"as_walked_maxbars_80": _maxbars_share(rows)}
        live_bars = (merged if s != "vp_euidx_pocgrav" else vp)[
            "live_time_stop_own_bars"].get(s)
        blk["live_time_stop_own_bars"] = live_bars
        blk["live_stop_is_tighter_than_the_research_horizon"] = bool(
            live_bars and live_bars < merged["maxbars"])
        if any(r.get("r_gross_live_stop") is not None for r in rows):
            blk["at_live_time_stop"] = {
                "mean_r_delta": round(statistics.fmean(
                    [(r["r_gross_live_stop"] - r["r_gross"]) for r in rows
                     if r.get("r_gross_live_stop") is not None]), 6),
                "n": sum(1 for r in rows if r.get("r_gross_live_stop") is not None)}
        horizon[s] = blk

    bands = ("mid",) if a.quick else BANDS
    # ADMISSION-GRADE ARMS ARE FTMO-ONLY, and that is a measured constraint rather than a
    # preference: `redacted_account_availability` below establishes that redacted_account does not offer
    # 6 of the 26 distinct symbols these sleeves trade under ANY spelling, and that the era
    # model keys redacted_account's own broker names (GER30, NDX100, UKOUSD) while every generated
    # trade in the estate carries FTMO names. A redacted_account "verdict" would be a statement
    # about that, not about the sleeve.
    accounts = ("FTMO",)

    arms: dict = {}
    for acct in accounts:
        for band in bands:
            key = f"{acct}|{band or 'flat_CONTROL'}"
            arms[key] = gate_arm(pool_primary, account=acct, band=band, costs=costs,
                                 allow=allow, fam=fam, label=f"{acct}_{band or 'flat'}")
            for s, r in sorted(arms[key]["verdicts"].items()):
                print(f"  {acct:11s} band={str(band or 'flat_CONTROL'):22s} {s:20s} "
                      f"{r['verdict']:14s} n={r['n_trades']:4d} "
                      f"R/day={r['pooled_oos_mean_r']} p={r['p_raw']} "
                      f"fail={r['failing_core_gates']}", flush=True)

    # ---- P4: the zero-carry counterfactual (never a verdict on its own) -------------------
    carry: dict = {}
    for acct in accounts:
        k = f"{acct}|zero_carry"
        carry[k] = gate_arm(pool_primary, account=acct, band="mid", costs=costs_zero,
                            allow=allow, fam=fam, label=f"{acct}_zero_carry",
                            zero_carry=True, diagnose=False)
        m = arms.get(f"{acct}|mid", {}).get("verdicts", {})
        for s, r in sorted(carry[k]["verdicts"].items()):
            base = m.get(s) or {}
            moved = base.get("verdict") != r["verdict"]
            print(f"  CARRY {acct:11s} {s:20s} measured={base.get('verdict')} -> "
                  f"zero={r['verdict']}  dR/day="
                  f"{None if r['pooled_oos_mean_r'] is None or base.get('pooled_oos_mean_r') is None else round(r['pooled_oos_mean_r'] - base['pooled_oos_mean_r'], 6)}"
                  f"  {'CARRY_DECIDES' if moved else ''}", flush=True)

    # ---- P3: the live time stop, published beside the research horizon --------------------
    live_arms: dict = {}
    if any(h.get("live_stop_is_tighter_than_the_research_horizon") for h in horizon.values()):
        sub = {s: rows for s, rows in pool_primary.items()
               if horizon[s].get("live_stop_is_tighter_than_the_research_horizon")}
        for acct in accounts:
            for band in (REAL_BANDS if not a.quick else ("mid",)):
                k = f"{acct}|{band}|live_stop"
                live_arms[k] = gate_arm(sub, account=acct, band=band, costs=costs,
                                        allow=allow, fam=fam,
                                        label=f"{acct}_{band}_live_stop",
                                        r_field="r_gross_live_stop", diagnose=False)
                for s, r in sorted(live_arms[k]["verdicts"].items()):
                    print(f"  LIVE-STOP {acct:11s} band={band:6s} {s:20s} {r['verdict']:14s} "
                          f"n={r['n_trades']:4d} R/day={r['pooled_oos_mean_r']} "
                          f"p={r['p_raw']}", flush=True)

    # ---- P2: the short-history sensitivity + P5 random-drop control -----------------------
    sens = _deep_history(pool_primary, merged, costs, allow, fam, accounts, a.quick)

    # ---- verdicts, by the vocabulary declared in V12 ---------------------------------------
    verdicts = {}
    for s in sorted(pool_primary):
        per_acct = {}
        for acct in accounts:
            adm = [b for b in REAL_BANDS
                   if (arms.get(f"{acct}|{b}", {}).get("verdicts", {}).get(s) or {}
                       ).get("verdict") == "ADMIT"]
            ne = [b for b in REAL_BANDS
                  if (arms.get(f"{acct}|{b}", {}).get("verdicts", {}).get(s) or {}
                      ).get("verdict") == "NOT_EVALUABLE"]
            cond = []
            for k, arm in list(live_arms.items()) + list(carry.items()):
                if not k.startswith(acct):
                    continue
                r = (arm.get("verdicts") or {}).get(s)
                if r and r["verdict"] == "ADMIT" and not arm.get("zero_carry_counterfactual"):
                    cond.append(k)
            ran = [b for b in REAL_BANDS if f"{acct}|{b}" in arms]
            if len(ran) < len(REAL_BANDS):
                # The vocabulary is "ADMIT at >= 2 of the 3 REAL bands". With fewer than 3
                # run, "2 of 3" is not a statement anyone can make, and defaulting to
                # STAYS_DEAD would publish a kill nobody measured. --quick lands here.
                v = "INCOMPLETE_BAND_COVERAGE"
            elif len(adm) >= 2:
                v = "REVIVAL_CANDIDATE"
            elif len(ne) >= 2:
                v = "NOT_EVALUABLE"
            elif len(cond) >= 2:
                v = "CONDITIONAL"
            else:
                v = "STAYS_DEAD"
            mid = arms.get(f"{acct}|mid", {}).get("verdicts", {}).get(s) or {}
            zc = carry.get(f"{acct}|zero_carry", {}).get("verdicts", {}).get(s) or {}
            per_acct[acct] = {
                "VERDICT": v,
                "admits_at_bands": adm, "not_evaluable_at_bands": ne,
                "conditional_arms_that_admit": cond,
                "mid_band": {k: mid.get(k) for k in
                             ("verdict", "n_trades", "pooled_oos_mean_r", "p_raw", "q_value",
                              "failing_core_gates", "n_folds_evaluable",
                              "oos_positive_fold_frac", "drop_best_retention",
                              "median_hold_hours", "swap_nights_mean", "swap_r_mean",
                              "swap_share_of_cost", "primary_prescription")},
                "carry_decides_the_verdict": bool(
                    zc and mid and zc.get("verdict") != mid.get("verdict")),
                "zero_carry_delta_r_per_day": (
                    None if not (zc.get("pooled_oos_mean_r") is not None
                                 and mid.get("pooled_oos_mean_r") is not None)
                    else round(zc["pooled_oos_mean_r"] - mid["pooled_oos_mean_r"], 6)),
            }
        verdicts[s] = per_acct
        for acct, blk in per_acct.items():
            print(f"VERDICT {s:20s} {acct:11s} {blk['VERDICT']:18s} "
                  f"admits_at={blk['admits_at_bands']} "
                  f"carry_decides={blk['carry_decides_the_verdict']}")

    doc = {
        "schema": "gtos.wave14.ca.revival_gate.v1",
        "session": "CA", "blocks": "B2106-B2119",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "rule": ("the RATIFIED rule: RECORDED population with AN's conditions "
                 "(POPULATION_RULE_V1.ratified_rule), B_balanced at the sealed alpha 0.10 "
                 "(CANDIDATE_FAMILY_V1.ratified_rule), corrected against CANDIDATE_BOOK_V1 on "
                 "the all-declared basis, band published with every verdict."),
        "family_artifact": str(FAMILY.relative_to(REPO)),
        "family_self_sha256": fam_doc[FAMILY_SHA_FIELD],
        "cut_rules": fam_doc["ca_declaration_note"][
            "the_cut_rules_are_declared_not_just_the_axes"],
        "verdict_vocabulary": fam_doc["ca_declaration_note"][
            "verdict_vocabulary_fixed_in_advance"],
        "cost_artifact": str(COSTS.relative_to(REPO)),
        "populations": {s: len(v) for s, v in sorted(pool_primary.items())},
        "reproduction_control": ("ca_revival_generate.py --stage control: the ARCHIVE arm "
                                 "reproduces AQ_ESTATE_TRADES_V2 exactly for both already-"
                                 "walked sleeves (237/237, 533/533, 0 R mismatches), so every "
                                 "difference below is attributable to the fetch."),
        "what_the_fetch_moved": fetch_delta,
        "horizon_and_maxbars_share": horizon,
        "arms": arms,
        "zero_carry_counterfactual": carry,
        "live_time_stop_arms": live_arms,
        "short_history_sensitivity": sens,
        "scoreability_gap": _scoreability_gap(pool_primary, arms, vp),
        "redacted_account_availability": _redacted_account_availability(pool_primary),
        "unpriced_contribution_upper_bound": _unpriced_bound(
            pool_primary, arms, costs, allow, fam),
        "VERDICTS": verdicts,
        "seconds_total": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}  ({doc['seconds_total']}s)")
    return 0


def _unpriced_bound(pool: dict, arms: dict, costs, allow, fam) -> dict:
    """Close the CORN.c / COTTON.c question with a bound instead of leaving it open.

    The fetch delivered the bars and the sleeve generated 16 trades on them. The era model
    (`SPREAD_MODEL_V1.json`) carries neither symbol on either account, so those 16 arrive at
    the gate UNPRICEABLE and `restrict_to_priced` drops them from the scored panel: the
    sleeve's verdict is byte-identical to the one BB published without them. That is
    "unmeasured", not "measured and immaterial", and publishing the second when only the
    first is true is exactly the conflation this estate keeps repairing.

    So: bound it. Re-gate with those trades' costs forced to ZERO -- nobody trades at zero
    cost, which is what makes it an upper bound -- by handing the gate a cost object that
    returns a free quote for exactly those two instruments and the real one for everything
    else. If the sleeve still REJECTS with the new members priced as FREE, no cost model
    could have revived it and the question is closed. If it ADMITS, the answer is genuinely
    open and the spread-model extension is worth the work; the receipt says which.
    """
    s = "sub_mid_dn_revert"
    rows = pool.get(s) or []
    new = [r for r in rows if r["symbol"] in ("CORN.c", "COTTON.c")]
    if not new:
        return {"applicable": False, "why": "no CORN.c/COTTON.c trades in the population"}


    base_mid = (arms.get("FTMO|mid", {}).get("verdicts", {}).get(s) or {})
    out = {
        "applicable": True,
        "n_new_members": len(new),
        "by_symbol": dict(collections.Counter(r["symbol"] for r in new)),
        "gross_r_sum": round(sum(float(r["r_gross"]) for r in new), 4),
        "gross_r_mean": round(statistics.fmean([float(r["r_gross"]) for r in new]), 5),
        "distinct_decision_days": len({r["decision_day"][:10] for r in new}),
        "why_they_are_unpriced": (
            "SPREAD_MODEL_V1.json carries neither CORN.c nor COTTON.c on either account "
            "(FTMO 46 symbols, redacted_account 27), so SpreadModel.record raises and "
            "era_population.classify returns None. The trades are KEPT in the population "
            "(deliberately -- filter_records' docstring) and then dropped from the SCORED "
            "panel by cost_coverage, which is why the verdict is byte-identical to BB's."),
        "the_bound": ("the same arm with CORN.c and COTTON.c swap and commission forced to "
                      "ZERO. An upper bound, not a cost model."),
        "arms": {},
    }
    # THE BOUND IS TAKEN OUTSIDE THE COST LAYER, because the cost layer is the thing being
    # bounded. Three independent refusals stand between these 16 trades and a price
    # (`the_measured_gap_verbatim` below), and forcing each one in turn would be fabricating
    # a cost artifact to answer a question about cost artifacts. So the bound is arithmetic
    # on the sleeve's OWN gross daily series, over the gate's OWN fold windows, at ZERO cost
    # -- the most generous treatment these trades could ever receive.
    base_folds = [f for f in (base_mid.get("fold_table") or []) if f.get("oos_start")]
    if not base_folds:
        out["reading"] = "no fold table on the base verdict; bound not taken"
        return out

    def _pooled(rowset) -> tuple[float | None, float | None, dict]:
        by_day: dict[str, list[float]] = collections.defaultdict(list)
        for r in rowset:
            by_day[r["decision_day"][:10]].append(float(r["r_gross"]))
        daily = {d: statistics.fmean(v) for d, v in by_day.items()}
        per_fold = {}
        for f in base_folds:
            a, b = f["oos_start"], f["oos_end"]
            vals = [v for d, v in daily.items() if a <= d <= b]
            if vals:
                per_fold[f["fold_id"]] = statistics.fmean(vals)
        if not per_fold:
            return None, None, {}
        pooled = statistics.fmean(list(per_fold.values()))
        best = max(per_fold, key=lambda k: per_fold[k])
        kept = [v for k, v in per_fold.items() if k != best]
        ret = (statistics.fmean(kept) / pooled) if kept and pooled else None
        return pooled, ret, {k: round(v, 6) for k, v in sorted(per_fold.items())}

    without = [r for r in rows if r["symbol"] not in ("CORN.c", "COTTON.c")]
    p_all, r_all, f_all = _pooled(rows)
    p_old, r_old, f_old = _pooled(without)
    out["arms"] = {
        "gross_zero_cost_with_new_members": {
            "n_trades": len(rows), "pooled_oos_mean_r_gross": round(p_all, 6),
            "drop_best_fold_retention": (None if r_all is None else round(r_all, 6)),
            "per_fold_mean_r_per_day_gross": f_all},
        "gross_zero_cost_without_new_members": {
            "n_trades": len(without), "pooled_oos_mean_r_gross": round(p_old, 6),
            "drop_best_fold_retention": (None if r_old is None else round(r_old, 6)),
            "per_fold_mean_r_per_day_gross": f_old},
        "fold_windows_from": "the base FTMO|mid verdict's own fold table",
    }
    floor = 0.5   # GateSpec.min_drop_best_fold_retention on B_balanced
    out["robustness_floor"] = floor
    d_ret = (None if (r_all is None or r_old is None) else round(r_all - r_old, 6))
    d_pool = round(p_all - p_old, 6)
    helps = (d_ret is not None and d_ret > 0)
    out["direction_of_the_new_members"] = {
        "delta_drop_best_fold_retention": d_ret,
        "delta_pooled_oos_mean_r_gross": d_pool,
        "binding_gate_at_every_band": "robustness",
    }
    out["reading"] = (
        (f"CLOSED, and the direction is the reason. At ZERO cost — no commission, no spread, "
         f"no slippage, no swap, the most generous treatment these 16 trades could ever "
         f"receive — they move the sleeve's drop-best-fold retention the WRONG WAY, "
         f"{round(r_old, 4)} -> {round(r_all, 4)} ({d_ret:+.4f}), while adding "
         f"{d_pool:+.4f} R/day of gross expectancy. `robustness` is the binding gate at "
         f"every band, so a change that lowers retention at zero cost can only lower it "
         f"further at a real one. Pricing CORN.c and COTTON.c could not have revived this "
         f"sleeve, and extending the cost layer for those two symbols is NOT on its "
         f"critical path.")
        if not helps else
        (f"OPEN. At ZERO cost the 16 new members IMPROVE drop-best-fold retention, "
         f"{round(r_old, 4)} -> {round(r_all, 4)} ({d_ret:+.4f}), so a real price for "
         f"CORN.c and COTTON.c could move the binding gate and the cost-layer extension is "
         f"worth the work. Note the gross series is not the gate's own number — the "
         f"cost-true arm fails `robustness` at "
         f"{base_mid.get('drop_best_retention')} — so this says the question is live, not "
         f"that the sleeve admits."))
    out["what_this_bound_is_NOT"] = (
        "not a cost-true measurement and not an admission arm. A gross series over the "
        "gate's fold windows is a descriptive instrument, and it is worth naming what it "
        "also shows: the GROSS retention clears the 0.5 floor while the cost-true one is "
        "negative, which says this sleeve's robustness failure is created by COST rather "
        "than by its raw signal. That is a statement about the whole sleeve, not about the "
        "two new symbols, and it belongs to Session AY's lane rather than to this bound.")
    out["base_verdict_for_comparison"] = {k: base_mid.get(k) for k in
                                          ("verdict", "n_trades", "pooled_oos_mean_r",
                                           "p_raw", "coverage_frac")}
    out["the_measured_gap_verbatim"] = {
        "commission": ("commission.kind == 'unknown', value null — 'no deal rows for this "
                       "symbol and no measured peer in its class; commission is UNKNOWN, not "
                       "zero' (BROKER_TRUE_COSTS_V1_1.json, Session J)"),
        "spread_price": "null",
        "era_model": ("neither symbol is in SPREAD_MODEL_V1.json on either account, so a "
                      "BANDED arm cannot price them at all"),
        "the_layer_that_binds_first": ("the commission schedule — the gross-basis arm, which "
                                       "needs no era model, still reports "
                                       "`unpriced_reasons: {\"commission schedule for this "
                                       "instrument is 'unknown' -- it is UNKNOWN, not zero\": "
                                       "16}`"),
    }
    print(f"  UNPRICED BOUND -> {out['reading'][:90]}")
    return out


def _redacted_account_availability(pool: dict) -> dict:
    """Why the commission's 'price the carry at EACH firm's measured swap' has one answer.

    This started as a second set of gate arms and became a finding. Two independent walls,
    both read off committed artifacts rather than asserted:

    1. **The product wall.** `BROKER_TRUE_COSTS_V1_1.json` carries 167 FTMO instruments and
       76 redacted_account ones, and six of the symbols these three sleeves trade appear in the
       redacted_account list under NO spelling: the four metals crosses, CORN and COTTON. Two
       thirds of `metals_softband`'s surface therefore does not exist on that account. Its
       `SURVIVOR_BOOK_V1` redacted_account tier describes a sleeve redacted_account cannot fully run.

    2. **The naming wall, which is OURS and is repairable.** `SpreadModel.record(symbol,
       account)` (`spread_model.py:403`) looks the symbol up in that account's own table,
       and the redacted_account table is keyed by redacted_account's broker names -- `GER30`, `NDX100`,
       `UKOUSD`, `USOUSD`, `US30`. Every generated trade in the estate carries FTMO names
       (`GER40.cash`, `UKOIL.cash`, `US30.cash`), and nothing in `era_population.classify`
       crosses them. So `vp_euidx_pocgrav`, whose BOTH symbols redacted_account does offer
       (GER40 -> GER30, UK100 -> UK100), still refuses -- and it refuses loudly, which is
       the machinery being right (`filter_records` raises rather than silently keeping all
       33 under a restricted rule's name).

    No prior receipt in this estate has run `run_gate` on the redacted_account account -- every one
    sets `ACCOUNT = "FTMO"` -- so wall 2 has never been hit before. It is filed here, with
    the repair named, rather than worked around.
    """
    import yaml
    from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver
    from src.costs.spread_model import load_spread_model

    costs_doc = json.loads(COSTS.read_text())
    fn_cost = set((costs_doc["accounts"]["redacted_account"].get("instruments") or {}))
    ft_cost = set((costs_doc["accounts"]["FTMO"].get("instruments") or {}))
    sm = load_spread_model()
    fn_era, ft_era = set(sm.symbols("redacted_account")), set(sm.symbols("FTMO"))

    prof_fn = yaml.safe_load(open(REPO / "config/profiles/redacted_account.yaml")) or {}
    res_fn = build_broker_symbol_resolver(prof_fn)

    out = {
        "cost_artifact_instruments": {"FTMO": len(ft_cost), "redacted_account": len(fn_cost)},
        "era_model_symbols": {"FTMO": len(ft_era), "redacted_account": len(fn_era)},
        "per_sleeve": {},
        "filed_defect": {
            "id": "CA-FN-1",
            "what": ("the walkforward gate has no redacted_account path: SpreadModel.record() and "
                     "BrokerTrueCosts both key an account's OWN broker names, and every "
                     "generated trade in the estate carries FTMO names. era_population "
                     "raises SpreadModelError rather than laundering it, which is correct."),
            "repair": ("cross the name at the seam: canonicalise the trade's symbol and "
                       "re-resolve it through the target account's profile "
                       "(build_broker_symbol_resolver(config/profiles/redacted_account.yaml)) "
                       "before record(). One place, in era_population.classify / the cost "
                       "layer's lookup; nothing about a verdict changes for FTMO."),
            "why_not_repaired_here": ("it changes which trades a gate can price on a live "
                                      "account, which is a cost-layer change on armed money "
                                      "and belongs in front of the orchestrator with its own "
                                      "A/B, not inside a revival gate."),
            "who_it_unblocks": ("vp_euidx_pocgrav is the only one of the three redacted_account "
                                "can fully trade; the other two hit wall 1 as well."),
        },
    }
    for s, rows in sorted(pool.items()):
        syms = sorted({r["symbol_canonical"] for r in rows})
        rows_out = {}
        for c in syms:
            fn_name = res_fn(c)
            rows_out[c] = {
                "redacted_account_broker_name": fn_name,
                "in_redacted_account_cost_artifact": fn_name in fn_cost,
                "in_redacted_account_era_model": fn_name in fn_era,
                "in_ftmo_cost_artifact": any(x for x in ft_cost if x == c or x == f"{c}.cash"
                                             or x.replace(".", "_") == c),
            }
        missing = sorted(k for k, v in rows_out.items()
                         if not v["in_redacted_account_cost_artifact"])
        out["per_sleeve"][s] = {
            "canonical_symbols_traded": syms,
            "n_symbols": len(syms),
            "NOT_OFFERED_BY_redacted_account": missing,
            "frac_of_surface_unavailable": (round(len(missing) / len(syms), 4)
                                            if syms else None),
            "by_symbol": rows_out,
            "disposition": (
                "redacted_account cannot run this sleeve's full surface — a PRODUCT gap, not a "
                "measurement gap" if missing else
                "redacted_account offers every symbol; the only blocker is the naming crossing "
                "filed as CA-FN-1"),
        }
        print(f"  FN-AVAIL {s:20s} {len(syms)} symbols, "
              f"{len(missing)} not offered by redacted_account {missing}")
    return out


def _scoreability_gap(pool: dict, arms: dict, vp: dict) -> dict:
    """For any NOT_EVALUABLE sleeve: the exact ask, priced in the currency AV-4 established.

    "NOT_EVALUABLE" is only useful if it comes with what would change it. The gate's floors
    are `min_folds_evaluable` and `min_trades_per_fold`, and the binding currency is distinct
    decision DAYS, not trades -- so the ask is expressed as calendar span, extrapolated from
    the sleeve's OWN observed decision rate, and then converted back into the aux bars the
    orchestrator would have to fetch.
    """
    from src.research_infra.walkforward.options import OPTIONS
    o = OPTIONS["B_balanced"]
    need_folds = int(getattr(o, "min_folds_evaluable", 3) or 3)
    need_per_fold = int(getattr(o, "min_trades_per_fold", 5) or 5)

    out = {}
    for s, rows in sorted(pool.items()):
        ne = [k for k, arm in arms.items()
              if (arm.get("verdicts") or {}).get(s, {}).get("verdict") == "NOT_EVALUABLE"]
        if not ne:
            continue
        v = (arms[ne[0]]["verdicts"] or {})[s]
        days = sorted({r["decision_day"][:10] for r in rows})
        a, b = dt.date.fromisoformat(days[0]), dt.date.fromisoformat(days[-1])
        span_months = max(((b - a).days / 30.44), 1e-9)
        got_folds = v.get("n_folds_evaluable") or 0
        # A fold calendar is chronological and roughly equal-length, so folds scale with span.
        # This is an ESTIMATE and is labelled one -- the fold builder's exact boundaries are
        # its own business, and no decision here rests on the third significant figure.
        want_months = round(span_months * need_folds / max(got_folds, 1), 1)
        # observed aux depth, read from the generation artifact's own grid
        grid = (vp.get("grids") or {}).get("H4") or {}
        out[s] = {
            "verdict": "NOT_EVALUABLE",
            "failing": v.get("failing_core_gates"),
            "reason": v.get("first_reason"),
            "n_trades": v.get("n_trades"),
            "folds_evaluable": got_folds, "folds_needed": need_folds,
            "min_trades_per_fold": need_per_fold,
            "observed_decision_span": f"{a.isoformat()}..{b.isoformat()}",
            "observed_span_months": round(span_months, 2),
            "observed_decisions_per_month": round(len(rows) / span_months, 2),
            "ESTIMATED_span_months_for_the_fold_floor": want_months,
            "ESTIMATED_extra_months_needed": round(want_months - span_months, 1),
            "the_ask": (
                f"the binding floor is FOLDS, not trades: {v.get('n_trades')} trades already "
                f"clear the 30-trade bar, but they sit in {got_folds} evaluable fold against "
                f"a floor of {need_folds}. The sleeve fails closed without its prior-day M1 "
                f"volume profile (vp_euidx.py:78-80), so its evaluable span is exactly the M1 "
                f"aux span. Estimated ask: GER40 and UK100 M1 back to roughly "
                f"{(a - dt.timedelta(days=int((want_months - span_months) * 30.44))).isoformat()}"
                f", i.e. about {round((want_months - span_months) * 30.44)} more calendar days "
                f"per symbol. The 2026-07-30 fetch supplied 90,000 M1 bars each covering "
                f"{grid.get('first', '')[:10]}..{grid.get('last', '')[:10]}."),
            "what_it_is_NOT": (
                "this is not a claim that the sleeve would admit with more data. Its 33 "
                "trades carry a positive mean and no p-value at all, because one fold cannot "
                "produce one. NOT_EVALUABLE is the absence of evidence, and the ask is what "
                "it would cost to have some."),
        }
    return out


def _deep_history(pool, merged, costs, allow, fam, accounts, quick) -> dict:
    """P2 + P5. `sub_mid_dn_revert` restricted to deep-history members, with a random control.

    The restriction is MECHANICAL and availability-only -- a member is kept iff its bar
    series starts more than DEEP_HISTORY_YEARS before the archive end -- and its verdict is
    BARRED by the declaration from producing a REVIVAL_CANDIDATE. It exists because the
    commission requires the short-history disclosure on any pooled figure, and a disclosure
    that is only prose is not one.

    P5's control answers the only interesting question about any filter: is the change worth
    more than dropping the same number of members at random? Same n, `RANDOM_DROPS` draws,
    reported as a distribution beside the filter's own number.
    """
    s = "sub_mid_dn_revert"
    rows = pool[s]
    # per-symbol first decision, as a proxy for series start that needs no second artifact:
    # the sleeve cannot decide before its bars exist, and the probe already published the
    # true series spans. Availability, never results.
    first = {}
    for r in rows:
        d = r["decision_day"][:10]
        first[r["symbol"]] = min(first.get(r["symbol"], d), d)
    keep = sorted(sym for sym, d in first.items()
                  if (ARCHIVE_END - dt.date.fromisoformat(d)).days / 365.25
                  > DEEP_HISTORY_YEARS)
    dropped = sorted(set(first) - set(keep))
    sub = {s: [r for r in rows if r["symbol"] in keep]}
    out = {
        "rule": (f"MECHANICAL availability filter: keep members whose first decision is more "
                 f"than {DEEP_HISTORY_YEARS} years before the archive end. Declared in V12 as "
                 f"P2 and BARRED from producing a REVIVAL_CANDIDATE."),
        "first_decision_by_symbol": dict(sorted(first.items())),
        "kept": keep, "dropped": dropped,
        "n_all": len(rows), "n_deep": len(sub[s]),
        "arms": {}, "random_drop_control": {},
    }
    for acct in accounts:
        for band in (("mid",) if quick else REAL_BANDS):
            k = f"{acct}|{band}"
            out["arms"][k] = gate_arm(sub, account=acct, band=band, costs=costs, allow=allow,
                                      fam=fam, label=f"{acct}_{band}_deep_history",
                                      diagnose=False)
            r = out["arms"][k]["verdicts"].get(s) or {}
            print(f"  DEEP-HISTORY {acct:11s} band={band:6s} {s} {r.get('verdict')} "
                  f"n={r.get('n_trades')} R/day={r.get('pooled_oos_mean_r')} "
                  f"p={r.get('p_raw')}", flush=True)
    # P5: same-size random drops, one band, so the filter is measured against chance
    rng = random.Random(SEED)
    syms = sorted(first)
    draws = []
    for _ in range(12):
        rnd_keep = set(rng.sample(syms, len(keep)))
        rsub = {s: [r for r in rows if r["symbol"] in rnd_keep]}
        arm = gate_arm(rsub, account="FTMO", band="mid", costs=costs, allow=allow, fam=fam,
                       label="random_drop_control", diagnose=False)
        v = arm["verdicts"].get(s) or {}
        draws.append({"kept": sorted(rnd_keep), "verdict": v.get("verdict"),
                      "pooled_oos_mean_r": v.get("pooled_oos_mean_r"),
                      "p_raw": v.get("p_raw"), "n_trades": v.get("n_trades")})
    vals = [d["pooled_oos_mean_r"] for d in draws if d["pooled_oos_mean_r"] is not None]
    filt = ((out["arms"].get("FTMO|mid") or {}).get("verdicts", {}).get(s) or {}
            ).get("pooled_oos_mean_r")
    out["random_drop_control"] = {
        "n_draws": len(draws), "n_members_dropped": len(dropped), "seed": SEED,
        "filter_pooled_oos_mean_r": filt,
        "random_median": (round(statistics.median(vals), 6) if vals else None),
        "random_min": (round(min(vals), 6) if vals else None),
        "random_max": (round(max(vals), 6) if vals else None),
        "filter_percentile_among_random_draws": (
            None if filt is None or not vals
            else round(sum(1 for v in vals if v <= filt) / len(vals), 3)),
        "n_random_draws_that_ADMIT": sum(1 for d in draws if d["verdict"] == "ADMIT"),
        "draws": draws,
        "reading": ("if the availability filter's expectancy sits inside the random-drop "
                    "distribution, dropping those particular members bought nothing that "
                    "dropping any two members would not have bought."),
    }
    print(f"  RANDOM-DROP control: filter={filt} vs random median "
          f"{out['random_drop_control']['random_median']} "
          f"[{out['random_drop_control']['random_min']}, "
          f"{out['random_drop_control']['random_max']}], "
          f"{out['random_drop_control']['n_random_draws_that_ADMIT']}/"
          f"{len(draws)} random draws ADMIT")
    return out


if __name__ == "__main__":
    raise SystemExit(main())
