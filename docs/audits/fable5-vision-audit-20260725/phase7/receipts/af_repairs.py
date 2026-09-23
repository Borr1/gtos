"""The named repairs from Session AF's work list, each executed with its number.

    python3 docs/audits/fable5-vision-audit-20260725/phase7/receipts/af_repairs.py

Six, in the order the prompt sets them:

  R1 PRODUCTION SURFACE      the armed `crypto` and `energy_agri` sleeves' OWN symbol sets,
                             pooled and judged, so "the class dilutes the sleeve" can be
                             read against "the sleeve as configured". The sets come from
                             `crypto.ON_SURFACE` and `energy_agri.ON_SURFACE`, i.e. from
                             production code, so choosing them is not a selection.
  R2 ATR-MR INVERSE          continuation on the same trigger. Not a sign flip on stored R
                             — the geometry is asymmetric (1R stop, 2R target), so the
                             inverse has to be RE-SIMULATED, which it is.
  R3 REGIME CONDITIONING     every trade labelled with Session AB's three published dials
                             at its own decision bar, then the pre-declared home of mean
                             reversion (`PERSISTENCE < -0.1`, AB's own `revert` band) tested
                             as a gate. The full conditional map is published for every
                             family — that is work-list item 7's deliverable.
  R4 SESSION FILTER CEILING  AG measured the FX family paying 13x-38x spread at broker hour
                             00, which is exactly where a D1 bar closes and therefore where
                             every one of these trades enters. This prices the BOUND on what
                             moving entry to the cheap hour can buy, per family.
  R5 NZDJPY BREAK            the break date, the conditioning variable, the gated re-walk.
  R6 GER40 THREE-WAY         AA's automatic split (excursion the exit missed -> AD; no
                             excursion -> inverse; else park with list) read off the
                             diagnosed run rather than argued.

Every variant is logged to the shared trial ledger. Offline and pure.
"""

from __future__ import annotations

import collections
import datetime as dt
import glob
import gzip
import json
import math
import os
import statistics
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(REPO))

from src.components.ultimate_book.admission import winsorize_R  # noqa: E402
from src.components.ultimate_book.bar_provider import TF_D1, TF_H4, WARMUP  # noqa: E402
from src.components.ultimate_book.bar_provider import decision_day_of  # noqa: E402
from src.components.ultimate_book.primitives import Bar, atr14, autocorr, vol_ratio  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs.model import cost_r, load_broker_true_costs  # noqa: E402
from src.costs.spread_model import load_spread_model  # noqa: E402
from src.research_infra.replay_policy.generation import CsvBarSource  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
    measured_n_trials,
)
from src.research_infra.walkforward import TradeRecord, run_gate  # noqa: E402
from src.research_infra.walkforward import family as fam  # noqa: E402
from src.research_infra.walkforward.exits import ExitPolicy, replay  # noqa: E402
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from af_family_generate import (  # noqa: E402
    BARS,
    MAXBARS,
    TF_MINUTES,
    TF_NAME,
    engine_reachable,
    load_archive,
    warm_cluster_for,
)

HERE = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
TRADES = HERE / "AF_FAMILY_TRADES.json.gz"
ADMISSION = HERE / "FAMILY_ADMISSION_V1.json"
OUT = HERE / "AF_REPAIRS_V1.json"
COSTS = REPO / "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json"
SERVER = "FTMO-Server3"
BAND = "mid"

#: Session AB's published dials (`AB_REGIME_DIALS_V1.json`), with AB's own band edges. Used
#: as-is: a conditioning variable invented by the session that needs it to work is a fitted
#: variable, and the whole point of §5.2 is that the gate is a NAMED, MONITORED quantity.
DIALS = {
    "VOL_REGIME": {"what": "atr14 / its own 100-bar mean (primitives.vol_ratio)",
                   "bands": {"lo": 0.85, "mid": 1.15, "hi": 1.60, "xhi": 2.00}},
    "PERSISTENCE": {"what": "lag-1 autocorrelation of the last 60 bar-to-bar changes "
                            "(primitives.autocorr)",
                    "bands": {"revert": -0.10, "random": 0.0, "trend": 0.10}},
    "TREND_STATE": {"what": "(close - close[-50]) / atr14 — the substrate slope50",
                    "bands": {"dn": -1.5, "flat": 0.0, "up": 1.5}},
}


def bucket(name: str, v: float | None) -> str:
    if v is None:
        return "na"
    if name == "VOL_REGIME":
        return ("lo" if v < 0.85 else "mid" if v < 1.15 else "hi" if v < 1.60 else "xhi")
    if name == "PERSISTENCE":
        return "revert" if v < -0.10 else ("trend" if v >= 0.10 else "random")
    return "dn" if v < -1.5 else ("up" if v >= 1.5 else "flat")


# ======================================================================================
def label_regimes(art, series) -> dict[str, dict[str, dict]]:
    """AB's three dials at every trade's own decision bar. Leak-free by construction.

    The dials read only bars at or before the decision bar — the same window the generator
    saw — so conditioning on them is a rule the live book could apply at decision time.
    """
    per_series: dict[tuple, dict[str, tuple]] = {}
    out: dict[str, dict[str, dict]] = {}
    for member, rows in art["trades"].items():
        if not rows:
            out[member] = {}
            continue
        key = (rows[0]["symbol_canonical"], rows[0]["timeframe"])
        if key not in per_series:
            bars, times = series[key]
            atrs = [atr14(bars, k) for k in range(len(bars))]
            per_series[key] = (bars, {t: k for k, t in enumerate(times)}, atrs)
        bars, idx, atrs = per_series[key]
        got: dict[str, dict] = {}
        for r in rows:
            i = idx.get(dt.datetime.fromisoformat(r["decision_bar_iso"]))
            if i is None:
                continue
            a = atrs[i]
            got[r["decision_bar_iso"]] = {
                "VOL_REGIME": vol_ratio(atrs, i),
                "PERSISTENCE": autocorr(bars, i, 60),
                "TREND_STATE": ((bars[i].c - bars[i - 50].c) / a
                                if i >= 50 and a > 0 else None),
            }
        out[member] = got
    return out


def to_records(rows, sleeve=None, regimes=None, keep=None) -> list[TradeRecord]:
    out = []
    for r in rows:
        if not r["engine_reachable"]:
            continue
        reg = (regimes or {}).get(r["decision_bar_iso"], {})
        if keep is not None and not keep(reg):
            continue
        out.append(TradeRecord(
            sleeve=(sleeve or r["member"]), symbol=r["symbol"],
            entry_utc=dt.datetime.fromisoformat(r["entry_utc"]),
            exit_utc=dt.datetime.fromisoformat(r["exit_utc"]),
            direction=r["direction"], sl_distance_price=r["sl_distance_price"],
            entry_price=r["entry_price"], r_gross=r["r_gross"],
            features={"regime": reg, "member": r["member"]}))
    return out


def judge(trades_by_sleeve, allow, declared, n_trials, cost_obj, label,
          option="C_exploratory") -> dict:
    spec = OPTIONS[option].with_(
        spec_id=f"{OPTIONS[option].spec_id}_af_repair_{label}", spread_band=BAND,
        declared_family_size=declared, n_trials=n_trials,
        n_trials_basis="MEASURED from the shared prospective trial ledger",
        sleeve_symbol_allowlist=allow)
    r = run_gate(trades_by_sleeve, spec, costs=cost_obj, server=SERVER)
    return {
        "spec_sha256": spec.seal(), "option": option, "band": BAND,
        "declared_family_size": declared, "admitted": r.admitted,
        "rows": {s: {"verdict": v.verdict.value, "n_trades": v.n_trades,
                     "pooled_oos_mean_r": v.pooled_oos_mean_r, "p_raw": v.p_raw,
                     "q_value": v.q_value,
                     "oos_positive_fold_frac": v.gates.get("stability", {})
                     .get("oos_positive_fold_frac"),
                     "n_folds_evaluable": v.gates.get("sample", {}).get("n_folds_evaluable"),
                     "first_reason": (v.reasons[0][:300] if v.reasons else None)}
                 for s, v in sorted(r.verdicts.items())},
    }


# ======================================================================================
def main() -> dict:
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AF")
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    res = build_broker_symbol_resolver(prof)
    costs = load_broker_true_costs(COSTS)
    smodel = load_spread_model()
    with gzip.open(TRADES, "rt") as fh:
        art = json.load(fh)
    adm = json.loads(ADMISSION.read_text())
    series, _files = load_archive(res)
    nt = int(measured_n_trials(ledger_paths=[REPO / DEFAULT_TRIAL_LEDGER])["n_trials"])

    members = {}
    for f, info in adm["grid"]["families"].items():
        key = f.split("_", 1)[1].rsplit("_", 2)[0]
        tf = {"D1": TF_D1, "H4": TF_H4}[info["timeframe"]]
        for sym in info["symbols"]:
            m = fam.member_name(key, sym, tf)
            members[m] = fam.FamilyMember(
                member=m, mechanism_key=key, mechanism=info["mechanism"],
                parent_sleeve=info["parent_sleeve"], symbol=sym, broker_symbol=res(sym),
                timeframe=tf, asset_class=info["asset_class"],
                is_authored_cell=(info["timeframe"] == info["authored_timeframe"]),
                profile_supported=True)

    print("labelling regimes at every decision bar ...", flush=True)
    regimes = label_regimes(art, series)

    out: dict = {
        "schema": "gtos.walkforward.af_repairs.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase7/receipts/"
                         "af_repairs.py"),
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "band": BAND, "option": "C_exploratory",
        "dials": DIALS,
        "baseline_declared_family_size": adm["multiplicity"]["declared_family_size"],
    }

    out["R1_production_surface"] = r1(art, members, regimes, costs, nt, ledger, adm)
    out["R2_atr_mr_inverse"] = r2(art, members, series, costs, nt, ledger, res)
    out["R3_regime_conditioning"] = r3(art, members, regimes, costs, nt, ledger, adm)
    out["R4_session_filter_ceiling"] = r4(art, members, costs, smodel, ledger)
    out["R5_nzdjpy_break"] = r5(art, members, regimes, costs, nt, ledger)
    out["R6_ger40_three_way"] = r6(art, members)
    out["R7_era_validity"] = r7(art, members, regimes, costs, smodel, nt, ledger)
    out["R8_best_cell_and_dilution"] = r8(art, members, costs, smodel, nt, ledger)

    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)} ({OUT.stat().st_size/1e3:.0f} KB)")
    print(f"ledger: {ledger.n_written} rows, {ledger.write_errors} errors")
    return out


# ------------------------------------------------------------------ R1
def r1(art, members, regimes, costs, nt, ledger, adm) -> dict:
    """The armed sleeves' OWN surfaces, pooled — the control for the class result."""
    SETS = {
        "prod_crypto_ac60_BTC_DASH": ("crypto_h4_donchian_ac60", TF_H4,
                                      ("BTCUSD", "DASHUSD"), "crypto.py:24 ON_SURFACE"),
        "prod_energy_fvg_USOIL_UKOIL": ("energy_fvg_retest", TF_H4,
                                        ("USOIL_cash", "UKOIL_cash"),
                                        "energy_agri.py:20 ON_SURFACE"),
        "prod_mx_donchian_crypto_authored": ("donchian_20_breakout", TF_D1,
                                             ("BTCUSD", "ETHUSD", "AVAUSD"),
                                             "market_expansion_d1.py:32-35 — the three "
                                             "crypto donchian tags the estate authored"),
    }
    pooled, allow, ms_by = {}, {}, {}
    for name, (key, tf, syms, why) in SETS.items():
        ms = [members[fam.member_name(key, s, tf)] for s in syms]
        ms_by[name] = ms
        by = {m.member: to_records(art["trades"][m.member],
                                   regimes=regimes.get(m.member)) for m in ms}
        pooled[name] = fam.pool_family(name, by, ms)
        allow[name] = tuple(sorted({m.broker_symbol for m in ms}))
    with _fid(list(pooled), members, SETS):
        g = judge(pooled, allow, adm["multiplicity"]["declared_family_size"] + len(SETS),
                  nt, costs, "production_surface")
    rows = {}
    for name, (key, tf, syms, why) in SETS.items():
        rows[name] = {**g["rows"][name], "symbols": list(syms), "source": why,
                      "n_members": len(syms)}
        ledger.record(mechanism=fam.MECHANISMS[key].mechanism, sleeve=name,
                      variant={"scope": "production_surface", "symbols": list(syms),
                               "timeframe": TF_NAME[tf], "band": BAND},
                      outcome="evaluated", metric=g["rows"][name]["pooled_oos_mean_r"],
                      metric_name="pooled_oos_mean_r", spec_sha256=g["spec_sha256"],
                      note="AF R1 — the sleeve's own configured surface, pooled")
    print("R1 production surfaces:")
    for n, r in rows.items():
        print(f"   {n:34s} n={r['n_trades']:5d} mean={_f(r['pooled_oos_mean_r'])} "
              f"p={_f(r['p_raw'])} {r['verdict']}")
    return {"why": ("the class-level families dilute a sleeve whose edge may be symbol-"
                    "specific. These are the surfaces production actually declares, so "
                    "they are the control, and choosing them is not a selection."),
            "spec_sha256": g["spec_sha256"], "sets": rows}


class _fid:
    """Fidelity records for the ad-hoc pooled sets in R1/R3/R5."""

    def __init__(self, names, members, sets=None, parent=None):
        self.names, self.members, self.sets, self.parent = names, members, sets, parent

    def __enter__(self):
        from src.research_infra.walkforward import fidelity as f

        for n in self.names:
            par = self.parent
            if par is None and self.sets is not None:
                key, tf, syms, _why = self.sets[n]
                par = fam.MECHANISMS[key].parent_sleeve
            f.register_surface_expansion(f"fam_{n}" if not n.startswith("fam_") else n,
                                         parent=par, symbol=n, timeframe="pooled",
                                         surface_note="AF repair variant")
            f._SURFACE_EXPANSIONS[n] = f._SURFACE_EXPANSIONS[
                f"fam_{n}" if not n.startswith("fam_") else n]
        return self

    def __exit__(self, *a):
        from src.research_infra.walkforward import fidelity as f

        f.clear_surface_expansions()
        return False


def _f(x, n=4):
    return "-" if x is None else f"{x:.{n}f}"


# ------------------------------------------------------------------ R2
def r2(art, members, series, costs, nt, ledger, res) -> dict:
    """Continuation on the ATR-MR trigger. Re-simulated, because -R is not the inverse.

    The contract is a 1R stop and a 2R target, so flipping direction changes which barrier
    is hit first and by how much. Negating stored R would answer a question about a
    symmetric instrument that does not exist here.
    """
    from src.components.ultimate_book.sleeves import market_expansion_d1 as mx

    ms = [m for m in members.values() if m.mechanism_key == "atr_mean_reversion"]
    warm = WARMUP.get(warm_cluster_for(fam.MECHANISMS["atr_mean_reversion"].parent_sleeve),
                      200)
    inv: dict[str, list[TradeRecord]] = {}
    stats: dict[str, dict] = {}
    with fam.expanded_surface(ms) as gens:
        for m in ms:
            bars, times = series[(m.symbol, m.timeframe)]
            ivl = dt.timedelta(minutes=TF_MINUTES[m.timeframe])
            reach = engine_reachable(times, sorted(t + ivl for t in times), ivl, warm)
            rows: list[TradeRecord] = []
            for i in sorted(reach):
                if i >= len(bars) - 2:
                    continue
                it = gens[m.member](m.symbol, bars[max(0, i - 259):i + 1],
                                    decision_day_of(times[i]), bar_time=times[i],
                                    bar_times=times[max(0, i - 259):i + 1],
                                    aux_bars=None, aux_times=None, runtime_now=times[i] + ivl)
                if it is None:
                    continue
                d = -int(it.direction)          # THE INVERSE
                sd = float(it.stop_dist)
                pol = ExitPolicy(target_dist=(float(it.target_dist) if it.target_dist
                                              else None), maxbars=MAXBARS, label="plain")
                pr = replay(bars, i, d, stop_dist=sd, policy=pol)
                rows.append(TradeRecord(
                    sleeve=f"inv_{m.member}", symbol=m.broker_symbol,
                    entry_utc=times[i] + ivl, exit_utc=times[pr.exit_index] + ivl,
                    direction=d, sl_distance_price=sd, entry_price=float(bars[i].c),
                    r_gross=float(winsorize_R(pr.r_gross)), features={}))
            inv[m.member] = rows
    by_class: dict[str, list[TradeRecord]] = collections.defaultdict(list)
    for m in ms:
        for t in inv[m.member]:
            by_class[f"fam_inv_atr_mean_reversion_{m.asset_class}_d1"].append(
                TradeRecord(sleeve=f"fam_inv_atr_mean_reversion_{m.asset_class}_d1",
                            symbol=t.symbol, entry_utc=t.entry_utc, exit_utc=t.exit_utc,
                            direction=t.direction, sl_distance_price=t.sl_distance_price,
                            entry_price=t.entry_price, r_gross=t.r_gross, features={}))
    allow = {k: tuple(sorted({t.symbol for t in v})) for k, v in by_class.items()}
    with _fid(list(by_class), members,
              parent=fam.MECHANISMS["atr_mean_reversion"].parent_sleeve):
        g = judge(dict(by_class), allow, 276 + len(by_class), nt, costs, "atr_mr_inverse")
    print("R2 ATR-MR inverse:")
    for k, r in sorted(g["rows"].items()):
        print(f"   {k:44s} n={r['n_trades']:5d} mean={_f(r['pooled_oos_mean_r'])} "
              f"p={_f(r['p_raw'])} {r['verdict']}")
        ledger.record(mechanism="d1_atr_mean_reversion_INVERSE", sleeve=k,
                      variant={"scope": "inverse_family", "band": BAND},
                      outcome="evaluated", metric=r["pooled_oos_mean_r"],
                      metric_name="pooled_oos_mean_r", spec_sha256=g["spec_sha256"],
                      note="AF R2 — continuation on the mean-reversion trigger")
    fwd = {f: adm_mean(art, members, "atr_mean_reversion", f) for f in
           sorted({m.asset_class for m in ms})}
    return {"why": ("AA prescribes INVERSE_TEST where a negative expectancy has no "
                    "excursion to keep. The mechanism is negative on all five classes, so "
                    "the inverse is the standing question rather than an afterthought."),
            "method": ("re-simulated with direction negated through the same "
                       "walkforward.exits.replay; NOT a sign flip on stored R, because the "
                       "1R/2R geometry is asymmetric"),
            "spec_sha256": g["spec_sha256"],
            "gross_r_per_trade_forward_vs_inverse": fwd,
            "rows": g["rows"]}


def adm_mean(art, members, key, asset_class) -> dict:
    fwd = [r["r_gross"] for m in members.values()
           if m.mechanism_key == key and m.asset_class == asset_class
           for r in art["trades"][m.member] if r["engine_reachable"]]
    return {"n": len(fwd),
            "mean_r_gross_forward": (round(statistics.fmean(fwd), 5) if fwd else None)}


# ------------------------------------------------------------------ R3
def r3(art, members, regimes, costs, nt, ledger, adm) -> dict:
    """AB's dials as gates, and the full conditional map (work-list item 7)."""
    fams = fam._by_family(list(members.values()))
    cmap: dict[str, dict] = {}
    for f, ms in sorted(fams.items()):
        per_dial: dict[str, dict] = {}
        for dial in DIALS:
            acc: dict[str, list[float]] = collections.defaultdict(list)
            for m in ms:
                reg = regimes.get(m.member, {})
                for r in art["trades"][m.member]:
                    if not r["engine_reachable"]:
                        continue
                    acc[bucket(dial, reg.get(r["decision_bar_iso"], {}).get(dial))].append(
                        r["r_gross"])
            per_dial[dial] = {b: {"n": len(v), "mean_r_gross": round(statistics.fmean(v), 5)}
                              for b, v in sorted(acc.items()) if v}
        cmap[f] = per_dial

    # TWO PRE-DECLARED GATES, both on AB's PERSISTENCE dial and both with a production
    # precedent rather than a fitted threshold:
    #   * mean reversion trades a mean-reverting tape  -> keep `revert` (< -0.10);
    #   * a breakout trades a persistent one           -> keep `trend`  (>= +0.10). The
    #     armed `crypto` sleeve already gates its own donchian on exactly this quantity
    #     at exactly this sign (`crypto.py:25`, AC_THR = 0.15 on `autocorr(B, i, 60)`),
    #     so the rule is precedented in production code, not invented here.
    GATES = {"atr_mean_reversion": "revert",
             "donchian_20_breakout": "trend",
             "crypto_h4_donchian_ac60": "trend"}
    gated: dict[str, list[TradeRecord]] = {}
    for f, ms in sorted(fams.items()):
        want = GATES.get(ms[0].mechanism_key)
        if want is None:
            continue
        name = f"{f}_gate_persistence_{want}"
        rows: list[TradeRecord] = []
        for m in ms:
            rows.extend(to_records(
                art["trades"][m.member], sleeve=name, regimes=regimes.get(m.member),
                keep=lambda reg, w=want: bucket("PERSISTENCE", reg.get("PERSISTENCE")) == w))
        if rows:
            gated[name] = rows
    allow = {k: tuple(sorted({t.symbol for t in v})) for k, v in gated.items()}
    with _fid(list(gated), members,
              parent=fam.MECHANISMS["atr_mean_reversion"].parent_sleeve):
        g = judge(gated, allow, 276 + len(gated), nt, costs, "persistence_gates")
    print("R3 families gated on AB's PERSISTENCE dial (revert for MR, trend for breakout):")
    for k, r in sorted(g["rows"].items()):
        print(f"   {k:56s} n={r['n_trades']:5d} mean={_f(r['pooled_oos_mean_r'])} "
              f"p={_f(r['p_raw'])} {r['verdict']}")
        ledger.record(mechanism="regime_gated_family", sleeve=k,
                      variant={"scope": "regime_gated_family", "dial": "PERSISTENCE",
                               "band_kept": k.rsplit("_", 1)[-1], "band": BAND},
                      outcome="evaluated", metric=r["pooled_oos_mean_r"],
                      metric_name="pooled_oos_mean_r", spec_sha256=g["spec_sha256"],
                      note="AF R3 — AB dial as an explicit gate")
    return {"why": ("mean reversion is supposed to live in a mean-reverting tape and a "
                    "breakout in a persistent one. AB's PERSISTENCE dial names both states "
                    "and publishes their bands, and the armed `crypto` sleeve already gates "
                    "its own donchian on the same quantity at the same sign "
                    "(crypto.py:25) — so these are named monitored variables with a "
                    "production precedent, not fitted thresholds."),
            "conditional_map": cmap, "spec_sha256": g["spec_sha256"], "gated": g["rows"]}


# ------------------------------------------------------------------ R4
def r4(art, members, costs, smodel, ledger) -> dict:
    """What can an entry-session filter buy? The spread term, priced at both hours.

    A D1 bar closes at broker 00:00 and this family enters at that close, which is the hour
    AG measured at 13x-38x for FX. The BOUND on a session filter is the spread term's fall
    when the same trade is priced at the cheap hour. It is a bound and not a forecast: a
    real re-entry two hours later also enters at a different PRICE, which moves R, and that
    needs H4 bars and a re-simulation (named as the follow-on, not smuggled in here).
    """
    rows: dict[str, dict] = {}
    fams = fam._by_family(list(members.values()))
    for f, ms in sorted(fams.items()):
        if ms[0].timeframe != TF_D1:
            continue
        d_spread, base, hours = [], [], collections.Counter()
        for m in ms:
            for r in art["trades"][m.member]:
                if not r["engine_reachable"]:
                    continue
                e = dt.datetime.fromisoformat(r["entry_utc"])
                hours[e.hour] += 1
                try:
                    a = cost_r(m.broker_symbol, "FTMO", r["hold_hours"],
                               sl_distance_price=r["sl_distance_price"],
                               entry_price=r["entry_price"],
                               side=("LONG" if r["direction"] > 0 else "SHORT"),
                               entry_utc=e, spread_band=BAND, spread_model=smodel,
                               costs=costs)
                    b = cost_r(m.broker_symbol, "FTMO", r["hold_hours"],
                               sl_distance_price=r["sl_distance_price"],
                               entry_price=r["entry_price"],
                               side=("LONG" if r["direction"] > 0 else "SHORT"),
                               entry_utc=e + dt.timedelta(hours=2), spread_band=BAND,
                               spread_model=smodel, costs=costs)
                except Exception:  # noqa: BLE001 - an unpriceable member is reported, not fixed
                    continue
                base.append(float(a.total_r.value))
                d_spread.append(float(a.spread_r.value) - float(b.spread_r.value))
        if not base:
            continue
        rows[f] = {
            "n_priced": len(base),
            "entry_hours_utc": dict(sorted(hours.items())),
            "mean_total_cost_r_at_entry_hour": round(statistics.fmean(base), 5),
            "mean_spread_r_saved_by_plus2h": round(statistics.fmean(d_spread), 5),
            "max_spread_r_saved": round(max(d_spread), 5),
            "share_of_total_cost": (round(statistics.fmean(d_spread)
                                          / statistics.fmean(base), 4)
                                    if statistics.fmean(base) else None),
        }
        ledger.record(mechanism=ms[0].mechanism, sleeve=f,
                      variant={"scope": "session_filter_ceiling", "shift_hours": 2,
                               "band": BAND},
                      outcome="evaluated",
                      metric=rows[f]["mean_spread_r_saved_by_plus2h"],
                      metric_name="mean_spread_r_saved_per_trade",
                      note="AF R4 — bound on an entry-session filter, spread term only")
    print("R4 session-filter ceiling (D1 families, +2 h):")
    for f, r in sorted(rows.items(), key=lambda kv: -kv[1]["mean_spread_r_saved_by_plus2h"]):
        print(f"   {f:44s} n={r['n_priced']:5d} cost={r['mean_total_cost_r_at_entry_hour']:.4f} "
              f"saved={r['mean_spread_r_saved_by_plus2h']:+.5f} R "
              f"({100*(r['share_of_total_cost'] or 0):.1f}% of cost)")
    return {"why": ("AG measured broker hour 00 at 13x-38x for the FX family, and a D1 bar "
                    "closes at exactly that hour."),
            "method": ("same trade, same geometry, spread term re-priced with entry_utc + "
                       "2 h through the same spread model. A BOUND: a real re-entry also "
                       "moves the entry price and therefore R."),
            "families": rows}


# ------------------------------------------------------------------ R5
def r5(art, members, regimes, costs, nt, ledger) -> dict:
    """NZDJPY donchian: where the lifetime edge breaks, and whether a dial explains it."""
    m = members[fam.member_name("donchian_20_breakout", "NZDJPY", TF_D1)]
    rows = [r for r in art["trades"][m.member] if r["engine_reachable"]]
    by_year: dict[int, list[float]] = collections.defaultdict(list)
    for r in rows:
        by_year[int(r["entry_utc"][:4])].append(r["r_gross"])
    years = sorted(by_year)
    cum, best = 0.0, None
    series_y = [(y, len(by_year[y]), round(statistics.fmean(by_year[y]), 4)) for y in years]
    # Chow-style split on the year axis: the split maximising |mean(before) - mean(after)|
    # with both sides >= 30 trades. Reported with the null, because the best split of a
    # random series is never zero.
    flat = [(int(r["entry_utc"][:4]), r["r_gross"]) for r in rows]
    for k in range(len(years)):
        cut = years[k]
        a = [v for y, v in flat if y < cut]
        b = [v for y, v in flat if y >= cut]
        if len(a) < 30 or len(b) < 30:
            continue
        d = abs(statistics.fmean(a) - statistics.fmean(b))
        if best is None or d > best[0]:
            best = (d, cut, len(a), len(b), statistics.fmean(a), statistics.fmean(b))
    perm = _split_null([v for _y, v in flat], [y for y, _v in flat], years)
    dials: dict[str, dict] = {}
    for dial in DIALS:
        acc: dict[str, list[float]] = collections.defaultdict(list)
        reg = regimes.get(m.member, {})
        for r in rows:
            acc[bucket(dial, reg.get(r["decision_bar_iso"], {}).get(dial))].append(
                r["r_gross"])
        dials[dial] = {b: {"n": len(v), "mean_r_gross": round(statistics.fmean(v), 5)}
                       for b, v in sorted(acc.items()) if v}
    # TWO gates, and the difference between them is the whole methodological point.
    #   PRE-DECLARED: a donchian BREAKOUT should want a persistent tape, and the armed
    #     `crypto` sleeve gates its own donchian on exactly that quantity at exactly that
    #     sign (`crypto.py:25`). Its q is a significance claim.
    #   POST-HOC: the dial bucket with the best mean. Its q is NOT a significance claim and
    #     is labelled so. An earlier revision of this file reported only the post-hoc pick,
    #     and its own `n >= 100` floor excluded PERSISTENCE==trend at n=94 — the
    #     mechanistically right bucket, missed by six trades, in favour of one six trades
    #     larger and 0.08 R worse. The floor is gone and both are published.
    cases = [("PERSISTENCE", "trend", "pre_declared")]
    cand = [(d, b, x["mean_r_gross"], x["n"]) for d, bs in dials.items()
            for b, x in bs.items() if x["n"] >= 30 and (d, b) != ("PERSISTENCE", "trend")]
    cand.sort(key=lambda t: -t[2])
    if cand:
        cases.append((cand[0][0], cand[0][1], "post_hoc_best"))
    cells, meta = {}, {}
    for dial, band, kind in cases:
        name = f"mxf_nzdjpy_d1_gate_{dial}_{band}".lower()
        cells[name] = to_records(art["trades"][m.member], sleeve=name,
                                 regimes=regimes.get(m.member),
                                 keep=lambda reg, d=dial, b=band: bucket(d, reg.get(d)) == b)
        meta[name] = (f"{dial}=={band}", kind)
    with _fid(list(cells), members, parent=m.parent_sleeve):
        g = judge(cells, {k: (m.broker_symbol,) for k in cells}, 276 + len(cells), nt,
                  costs, "nzdjpy_gates")
    gated = {}
    for name, (gate, kind) in meta.items():
        gated[name] = {"gate": gate, "selection": kind, **g["rows"][name],
                       "spec_sha256": g["spec_sha256"]}
        ledger.record(mechanism=m.mechanism, sleeve=name,
                      variant={"scope": "regime_gated_member", "gate": gate,
                               "selection": kind},
                      outcome="evaluated", metric=g["rows"][name]["pooled_oos_mean_r"],
                      metric_name="pooled_oos_mean_r", spec_sha256=g["spec_sha256"],
                      note=f"AF R5 — nzdjpy conditioned, {kind}")
    print(f"R5 nzdjpy: break {best[1] if best else None} "
          f"(null p {perm['p']}), gates:")
    for n, x in gated.items():
        print(f"   {n:44s} [{x['selection']:14s}] n={x['n_trades']:4d} "
              f"mean={_f(x['pooled_oos_mean_r'])} p={_f(x['p_raw'])} {x['verdict']}")
    return {
        "member": m.member, "n": len(rows),
        "mean_r_gross_lifetime": round(statistics.fmean(r["r_gross"] for r in rows), 5),
        "by_year": series_y,
        "best_split": (None if best is None else {
            "cut_year": best[1], "n_before": best[2], "n_after": best[3],
            "mean_before": round(best[4], 5), "mean_after": round(best[5], 5),
            "abs_delta": round(best[0], 5),
            "null_p": perm["p"], "null_note": perm["note"]}),
        "dial_buckets": dials,
        "gated_rewalk": gated,
        "honesty": ("the `post_hoc_best` gate is chosen AFTER seeing the bucket means, so "
                    "its q is not a significance claim — it is the size of the best "
                    "conditioning available, which is what a repair queue needs. The "
                    "`pre_declared` one is a real test. The split date carries its own "
                    "permutation null for the same reason."),
    }


def _split_null(vals, yrs, years, n_perm=2000) -> dict:
    """How large is the best year-split of a randomly reordered series? Seeded, not timed."""
    import random

    def best_of(v):
        b = 0.0
        for cut in years:
            a = [x for y, x in zip(yrs, v) if y < cut]
            c = [x for y, x in zip(yrs, v) if y >= cut]
            if len(a) < 30 or len(c) < 30:
                continue
            b = max(b, abs(statistics.fmean(a) - statistics.fmean(c)))
        return b

    obs = best_of(vals)
    rng = random.Random(20260730)
    v = list(vals)
    ge = 0
    for _ in range(n_perm):
        rng.shuffle(v)
        if best_of(v) >= obs:
            ge += 1
    return {"observed_best_abs_delta": round(obs, 5),
            "p": round((1 + ge) / (n_perm + 1), 4),
            "note": (f"the largest |mean split| over {n_perm} shuffles of the same returns "
                     f"against the same year labels; a break date is only a break if it "
                     f"beats the best split of noise")}


# ------------------------------------------------------------------ R6
def r6(art, members) -> dict:
    """GER40 volume-surge: AA's three-way split, read off the path rather than argued."""
    out = {}
    for sym in ("GER40", "JP225", "US30_cash", "SPX500", "NAS100", "UK100"):
        m = members[fam.member_name("volume_surge_reversal", sym, TF_D1)]
        rows = [r for r in art["trades"][m.member] if r["engine_reachable"]]
        if not rows:
            continue
        pos = [r for r in rows if r["mfe_r"] > 0]
        gross = statistics.fmean(r["r_gross"] for r in rows)
        cap = (sum(r["r_gross"] for r in pos) / sum(r["mfe_r"] for r in pos)) if pos else None
        frac1r = sum(1 for r in rows if r["mfe_r"] >= 1.0) / len(rows)
        pres = ("COST_GEOMETRY_or_ADMIT" if gross > 0 else
                ("EXIT_REPAIR" if frac1r >= 0.30 else "INVERSE_TEST"))
        out[m.member] = {
            "symbol": sym, "n": len(rows), "mean_r_gross": round(gross, 5),
            "mean_mfe_r": round(statistics.fmean(r["mfe_r"] for r in rows), 4),
            "mean_mae_r": round(statistics.fmean(r["mae_r"] for r in rows), 4),
            "capture_ratio": (round(cap, 4) if cap is not None else None),
            "frac_reaching_1r": round(frac1r, 4),
            "prescription": pres,
            "exit_reasons": dict(collections.Counter(r["exit_reason"] for r in rows)),
        }
    print("R6 index volume-surge three-way:")
    for k, r in out.items():
        print(f"   {r['symbol']:11s} n={r['n']:4d} gross={r['mean_r_gross']:+.4f} "
              f"MFE={r['mean_mfe_r']:.3f} cap={r['capture_ratio']} "
              f"frac1R={r['frac_reaching_1r']:.2f} -> {r['prescription']}")
    return {"rule": ("AA's automatic split: gross > 0 -> cost geometry; gross <= 0 with "
                     "excursion the exit missed -> EXIT_REPAIR (route to AD); no excursion "
                     "-> INVERSE_TEST. 'Excursion' is >= 30 % of trades reaching 1 R, which "
                     "is the line AA's own table draws between `idxrev` (0.26) and every "
                     "sleeve it prescribed EXIT_REPAIR for."),
            "members": out}


# ------------------------------------------------------------------ R7
def r7(art, members, regimes, costs, smodel, nt, ledger) -> dict:
    """Is the cost the verdict rests on inside the model's validated range? Mostly not.

    R4 came back with FX D1 families paying 0.46-0.50 R of TOTAL cost per trade, 80 % of it
    spread, and a +0.40 R saving from a two-hour entry shift. A spread charge of half the
    risk unit is not a market, so the probe was suspected before it was believed — the
    working agreement's rule — and it does not survive.

    THE COMPOUNDING. `spread_model_v1` composes multiplicatively: anchor x era_ratio x
    hour-of-week multiplier. Measured here on NZDUSD in the 2000s: **era_ratio 13.7 x
    hour_mult 14.4 = 198x the modern base**, i.e. spread_r 1.78 — 178 % of the stop. On
    EURUSD's 2000s the same product is 32.6 x 14.7 = 479x, spread_r 0.46.

    Each factor was validated ALONE and the product never was. AG validated the era term on
    H4 block pairs, which are all-hours medians (skill 0.33-0.58), and the hour term inside
    the 37-day tick window, where era_ratio is 1 by construction. AG's own §10 item 1 says
    the 20x-50x pre-2010 FX eras are `SCHEDULE`-class — the broker's backfilled constant —
    and that "nothing validates it" there. Multiplying an unvalidated 30x by an unvalidated
    15x is the part nobody wrote down.

    THE FIX AVAILABLE TODAY is the same instrument the gate already uses for coverage:
    restrict to the population the model MEASURED. `era_class == RECORDED` is a property of
    the broker's own bar data, not of returns, so restricting on it is outcome-independent —
    the identical argument `GateSpec.coverage_policy = restrict_to_priced` rests on. The
    families are re-walked on their RECORDED-era subset and both are published.
    """
    fams = fam._by_family(list(members.values()))
    per_fam: dict[str, dict] = {}
    keep_rows: dict[str, list[TradeRecord]] = {}
    for f, ms in sorted(fams.items()):
        cls = collections.Counter()
        rec_r, all_r = [], []
        rows: list[TradeRecord] = []
        for m in ms:
            for r in art["trades"][m.member]:
                if not r["engine_reachable"]:
                    continue
                e = dt.datetime.fromisoformat(r["entry_utc"])
                try:
                    est = smodel.estimate(m.broker_symbol, "FTMO", e, band=BAND)
                except Exception:  # noqa: BLE001 - unpriceable is reported by the gate
                    cls["unpriceable"] += 1
                    continue
                cls[est.era_class] += 1
                all_r.append(est.era_ratio * (est.intraweek_mult or 1.0))
                if est.era_class == "RECORDED":
                    rec_r.append(est.era_ratio * (est.intraweek_mult or 1.0))
                    rows.append(TradeRecord(
                        sleeve=f"{f}_recorded_eras", symbol=m.broker_symbol,
                        entry_utc=e, exit_utc=dt.datetime.fromisoformat(r["exit_utc"]),
                        direction=r["direction"],
                        sl_distance_price=r["sl_distance_price"],
                        entry_price=r["entry_price"], r_gross=r["r_gross"], features={}))
        n = sum(cls.values())
        per_fam[f] = {
            "n": n, "era_class_mix": dict(cls),
            "recorded_frac": (round(cls.get("RECORDED", 0) / n, 4) if n else None),
            "mean_total_spread_multiple_vs_modern_base": (
                round(statistics.fmean(all_r), 2) if all_r else None),
            "max_total_spread_multiple": (round(max(all_r), 1) if all_r else None),
            "n_recorded": len(rows),
        }
        if len(rows) >= 30:
            keep_rows[f"{f}_recorded_eras"] = rows
    allow = {k: tuple(sorted({t.symbol for t in v})) for k, v in keep_rows.items()}
    with _fid(list(keep_rows), members, parent="mx_btcusd_d1_donchian_20_breakout"):
        g = judge(keep_rows, allow, 276 + len(keep_rows), nt, costs, "recorded_eras_only")
    print("R7 recorded-era-only re-walk:")
    for k, r in sorted(g["rows"].items(), key=lambda kv: -(kv[1]["pooled_oos_mean_r"] or -9)):
        print(f"   {k:56s} n={r['n_trades']:5d} mean={_f(r['pooled_oos_mean_r'])} "
              f"p={_f(r['p_raw'])} {r['verdict']}")
        ledger.record(mechanism="family_recorded_eras", sleeve=k,
                      variant={"scope": "era_class_restricted", "keep": "RECORDED",
                               "band": BAND},
                      outcome="evaluated", metric=r["pooled_oos_mean_r"],
                      metric_name="pooled_oos_mean_r", spec_sha256=g["spec_sha256"],
                      note="AF R7 — restricted to the eras the spread model measured")
    return {
        "defect": ("spread_model_v1 composes anchor x era_ratio x hour_of_week "
                   "multiplicatively and each factor was validated alone. Their PRODUCT "
                   "reaches 198x the modern base on NZDUSD in the 2000s (era 13.7 x hour "
                   "14.4), charging spread_r 1.78 — 178 % of the risk unit. AG's own "
                   "SESSION_AG_SPREAD_MODEL_RESULT §10 item 1 says the pre-2010 FX eras are "
                   "SCHEDULE-class and unvalidated; nothing states that the product of two "
                   "unvalidated multipliers is worse than either."),
        "consequence": ("every mid/low/high verdict on a deep-history FX member is "
                        "dominated by that product. The non-FX classes are unaffected: "
                        "fourteen symbols do not quote at the rollover at all (AG §5), "
                        "which R4 independently reproduces as a ~0.00 R hour saving on "
                        "metals, indices, energy and crypto."),
        "route": "Session AG's lane / the cost-geometry lane. Not repaired here.",
        "restriction_is_outcome_independent": (
            "era_class is a property of the broker's bar data, not of returns — the same "
            "argument GateSpec.coverage_policy='restrict_to_priced' rests on."),
        "by_family": per_fam, "spec_sha256": g["spec_sha256"], "rewalk": g["rows"],
    }


# ------------------------------------------------------------------ R8
def r8(art, members, costs, smodel, nt, ledger) -> dict:
    """Why pooling failed, as a number — and the one cell both restrictions leave standing.

    THE DILUTION. The Fundamental Law's sqrt(k) is a statement about k members of EQUAL
    information coefficient. If one member carries the edge and the rest carry noise, an
    equal-weight cross-section is a dilution and not a breadth gain — the mean falls toward
    the members' average while the variance falls only as fast as their correlation allows.
    `ic_dispersion_ratio` is the crude version of that test: the cross-member standard
    deviation of per-member mean gross R, divided by the family's own mean. Above 1 the
    family is not one mechanism with k readings; it is a mixture, and pooling is the wrong
    instrument.

    THE ONE CELL. Two restrictions in this file are legitimate on their own terms — R1's
    production-declared symbol set (chosen by `market_expansion_d1.TAG_TO_RULE`, years
    before this session) and R7's `era_class == RECORDED` (a property of the broker's bar
    data). Their intersection is computed once, here, named, and logged. It is the THIRD
    restriction applied to the same returns and its q is read against the whole 276-look
    bill for exactly that reason.
    """
    fams = fam._by_family(list(members.values()))
    disp: dict[str, dict] = {}
    for f, ms in sorted(fams.items()):
        per = []
        for m in ms:
            rows = [r["r_gross"] for r in art["trades"][m.member] if r["engine_reachable"]]
            if rows:
                per.append((m.symbol, len(rows), statistics.fmean(rows)))
        if len(per) < 2:
            continue
        means = [x[2] for x in per]
        mu, sd = statistics.fmean(means), statistics.pstdev(means)
        disp[f] = {
            "n_members": len(per),
            "member_mean_r_gross": {s: round(v, 5) for s, _n, v in
                                    sorted(per, key=lambda t: -t[2])},
            "family_mean_of_member_means": round(mu, 5),
            "cross_member_sd": round(sd, 5),
            "ic_dispersion_ratio": (round(sd / abs(mu), 3) if mu else None),
            "n_members_positive": sum(1 for v in means if v > 0),
            "spread_best_minus_worst": round(max(means) - min(means), 5),
        }
    # The intersection cell.
    syms = ("BTCUSD", "ETHUSD", "AVAUSD")
    name = "fam_prod_mx_donchian_crypto_authored_recorded_eras"
    rows: list[TradeRecord] = []
    for s in syms:
        m = members[fam.member_name("donchian_20_breakout", s, TF_D1)]
        for r in art["trades"][m.member]:
            if not r["engine_reachable"]:
                continue
            e = dt.datetime.fromisoformat(r["entry_utc"])
            try:
                est = smodel.estimate(m.broker_symbol, "FTMO", e, band=BAND)
            except Exception:  # noqa: BLE001
                continue
            if est.era_class != "RECORDED":
                continue
            rows.append(TradeRecord(
                sleeve=name, symbol=m.broker_symbol, entry_utc=e,
                exit_utc=dt.datetime.fromisoformat(r["exit_utc"]), direction=r["direction"],
                sl_distance_price=r["sl_distance_price"], entry_price=r["entry_price"],
                r_gross=r["r_gross"], features={}))
    btc = members[fam.member_name("donchian_20_breakout", "BTCUSD", TF_D1)]
    solo = [t for t in rows if t.symbol == btc.broker_symbol]
    cells = {name: rows, f"{name}_BTCUSD_only": [
        TradeRecord(sleeve=f"{name}_BTCUSD_only", symbol=t.symbol, entry_utc=t.entry_utc,
                    exit_utc=t.exit_utc, direction=t.direction,
                    sl_distance_price=t.sl_distance_price, entry_price=t.entry_price,
                    r_gross=t.r_gross, features={}) for t in solo]}
    allow = {k: tuple(sorted({t.symbol for t in v})) for k, v in cells.items()}
    with _fid(list(cells), members, parent=btc.parent_sleeve):
        g = judge(cells, allow, 276 + len(cells), nt, costs, "authored_crypto_recorded")
    print("R8 authored crypto donchian x RECORDED eras:")
    for k, r in sorted(g["rows"].items()):
        print(f"   {k:56s} n={r['n_trades']:5d} mean={_f(r['pooled_oos_mean_r'])} "
              f"p={_f(r['p_raw'])} q={_f(r['q_value'])} folds+={_f(r['oos_positive_fold_frac'],2)} "
              f"{r['verdict']}")
        ledger.record(mechanism="d1_donchian_20_breakout", sleeve=k,
                      variant={"scope": "authored_set_x_recorded_eras", "band": BAND},
                      outcome="evaluated", metric=r["pooled_oos_mean_r"],
                      metric_name="pooled_oos_mean_r", spec_sha256=g["spec_sha256"],
                      note="AF R8 — the intersection of the two legitimate restrictions")
    worst = sorted(disp.items(), key=lambda kv: -(kv[1]["ic_dispersion_ratio"] or 0))[:5]
    print("   worst IC dispersion:",
          [(k.replace("fam_", ""), v["ic_dispersion_ratio"]) for k, v in worst])
    return {"dilution": {"what": ("cross-member SD of per-member mean gross R over the "
                                  "family mean. > 1 means the members are a mixture, so "
                                  "equal-weight pooling dilutes rather than adds breadth."),
                         "by_family": disp},
            "intersection_cell": {"symbols": list(syms),
                                  "restrictions": ["production-declared symbol set "
                                                   "(market_expansion_d1.TAG_TO_RULE)",
                                                   "era_class == RECORDED"],
                                  "spec_sha256": g["spec_sha256"], "rows": g["rows"]}}


if __name__ == "__main__":
    main()
