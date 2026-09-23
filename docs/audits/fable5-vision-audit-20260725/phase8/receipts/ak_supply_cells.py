"""The pre-declared cell decomposition: turn two refusals into verdicts, and run AF's coherence test.

    python3 docs/audits/fable5-vision-audit-20260725/phase8/receipts/ak_supply_cells.py

WHY THIS EXISTS
---------------
`ak_supply_gate.py` returned `NOT_EVALUABLE / DATA_PATH` for `structural_retest` at 58.0 % cost
coverage: eight of its twenty-three symbols have no file in the tick archive, so `cost_r` refuses
them and the retained fraction falls under the 60 % floor (`GateSpec.min_retained_trade_frac`).
That refusal is correct and it is not an ending. The sleeve is not one hypothesis — it is a
**whitelist of three (class, session, regime, vol) cells declared in its own source** before any
outcome here was seen (`structural_retest.py:40-44`), and two of the three are fully priceable.

So the cells are judged. Same for `session_leadlag_genuine`, whose four legs are declared verbatim
in `KB6_session_stacks.py:52-58` and which differ in geometry (one trails, three take a 4 R
target) — pooling them under one name is what the sleeve does, and asking which leg carries it is
a question the sleeve's own table already poses.

WHAT MAKES THIS NOT A POST-HOC SPLIT, AND THE ONE PLACE IT IS A NARROWER HYPOTHESIS
-----------------------------------------------------------------------------------
Three properties, in descending order of how much they matter:

1. **The cells are in the source, not in the results.** `WHITELIST` and `LL_FWD` were written by
   the research that produced these sleeves. Nothing here chose a partition after seeing a number.
2. **Every cell is taken.** All three whitelist cells and all four legs are gated, in a fixed
   order, and each is a look in the ledger. No cell is reported because it won.
3. **The priceable restriction is outcome-independent** — a symbol's presence in the tick archive
   is a property of what was captured, never of what it returned. That is the same argument
   `GateSpec.coverage_policy="restrict_to_priced"` rests on and the same one AF used for
   `era_class == RECORDED`.

**Where it IS weaker, stated plainly:** a cell restricted to its priceable symbols is a NARROWER
hypothesis than the cell on its authored surface, and for the crypto cell the restriction is
large — 3 of 8 symbols, 1,707 of 3,644 trades. That is published per cell (`dropped_symbols`,
`n_trades_dropped`), the parent's full-surface refusal is kept beside it, and the exact tick
capture that would close the gap is named. A reader must be able to see that the crypto verdict
is about BTCUSD/ETHUSD/DASHUSD and not about eight crypto instruments.

AF's TWO-CLAUSE COHERENCE TEST, RUN ON EVERYTHING
--------------------------------------------------
`SESSION_AF_FAMILY_EXPANSION_RESULT.md` §0 leaves one rule behind: before spending a session on
breadth, check that the members AGREE (dispersion ratio `sd/|mean| < 1`) **and** that what they
agree on is POSITIVE. Exactly 2 of AF's 30 families passed it. It costs nothing on trades that
already exist, so it runs here on all four new sleeves and on every cell.
"""

from __future__ import annotations

import gzip
import json
import os
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"))

import yaml  # noqa: E402

import ad_exit_sweep as AD  # noqa: E402
from src.components.ultimate_book.sleeves import session_leadlag as SL  # noqa: E402
from src.components.ultimate_book.sleeves import structural_retest as SR  # noqa: E402
from src.components.ultimate_book.symbol_map import build_broker_symbol_resolver  # noqa: E402
from src.costs import load_broker_true_costs  # noqa: E402
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import run_gate  # noqa: E402
from src.research_infra.walkforward import supply as SUP  # noqa: E402
from src.research_infra.walkforward.fidelity import (  # noqa: E402
    clear_surface_expansions,
    fidelity_for,
    register_surface_expansion,
)
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402

AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"
AK_IN = HERE / "AK_SUPPLY_TRADES.json.gz"
OUT = HERE / "AK_SLEEVE_CELLS_V1.json"
SERVER = AD.SERVER


def coherence(per_member_mean: dict[str, float]) -> dict:
    """AF's two-clause test. `ratio` alone is sign-blind — that was AF's own §8 correction."""
    vals = list(per_member_mean.values())
    if not vals:
        return {"k": 0}
    m = statistics.fmean(vals)
    sd = statistics.stdev(vals) if len(vals) > 1 else 0.0
    ratio = (sd / abs(m)) if m else None
    all_pos = all(v > 0 for v in vals)
    return {
        "k": len(vals), "mean": round(m, 6), "sd": round(sd, 6),
        "dispersion_ratio": (round(ratio, 4) if ratio is not None else None),
        "all_members_positive": all_pos,
        "coheres": bool(ratio is not None and ratio < 1.0 and all_pos),
        "per_member_mean_r_gross": {k: round(v, 6) for k, v in sorted(per_member_mean.items())},
        "rule": ("AF §0: dispersion ratio sd/|mean| < 1 AND every member positive. The ratio "
                 "alone is sign-blind — a family agreeing on being uniformly bad scores as "
                 "tight as one agreeing on being good (AF §8 item 4). Exactly 2 of AF's 30 "
                 "families passed both clauses."),
    }


#: `structural_retest`'s three whitelist cells, keyed as the source keys them.
SR_CLASSES = {
    "crypto": SR._CRYPTO, "metal": SR._METAL, "index": SR._INDEX,
}
SR_CELLS = {
    f"{cls}_{sess.lower()}_{'short' if reg == 'dn' else 'long'}": (cls, sess, reg, vol)
    for (cls, sess, reg, vol) in sorted(SR.WHITELIST)
}


def sr_cell_of(symbol: str) -> str | None:
    cls = SR._CLASS_OF.get(symbol)
    for name, (c, _s, _r, _v) in SR_CELLS.items():
        if c == cls:
            return name
    return None


def priced_symbols(costs, account: str, symbols, resolve) -> tuple[set[str], dict[str, str]]:
    """Which of `symbols` `cost_r` can price, and why not for the rest.

    Asked of the cost artifact directly rather than inferred from a gate refusal string, so the
    answer is a property of the artifact and survives a change to the refusal's wording.
    """
    ok: set[str] = set()
    why: dict[str, str] = {}
    inst = ((costs.doc.get("accounts") or {}).get(account) or {}).get("instruments") or {}
    for s in symbols:
        rec = inst.get(resolve(s))
        if rec is None:
            why[s] = f"no instrument record for {resolve(s)} on {account}"
            continue
        sp = (rec.get("spread_price") or {})
        has_spread = bool(sp.get("by_session") or sp.get("median") or sp.get("p50"))
        comm = (rec.get("commission") or {}).get("kind")
        if not has_spread:
            why[s] = f"no measured spread for {resolve(s)} on {account} (no tick-archive file)"
        elif comm in (None, "unknown"):
            why[s] = f"commission is UNKNOWN for {resolve(s)} with no peer to transfer from"
        else:
            ok.add(s)
    return ok, why


def main() -> dict:
    t_start = time.time()
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AK")
    aa = json.load(gzip.open(AA_IN, "rt"))
    ak = json.load(gzip.open(AK_IN, "rt"))
    costs = load_broker_true_costs(AD.COSTS)
    prof = yaml.safe_load(open(REPO / "config/profiles/operator_profile.yaml")) or {}
    resolve = build_broker_symbol_resolver(prof)

    base = OPTIONS["B_balanced"]
    out: dict = {
        "schema": "gtos.walkforward.sleeve_cells.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase8/receipts/"
                         "ak_supply_cells.py"),
        "session": "AK", "blocks": "B950-B999",
        "cost_artifact": str(AD.COSTS.relative_to(REPO)),
        "declared_before_outcomes": {
            "structural_retest": ("sleeves/structural_retest.py:40-44 WHITELIST — three "
                                  "(class, session, regime, vol) cells"),
            "session_leadlag_genuine": ("KB6_session_stacks.py:52-58 LL_FWD — four "
                                        "(leader, follower, look, z, thesis, geom, session) legs"),
        },
    }

    # ---- coherence on the four parents, GROSS basis (AF's own) ----------------------------
    out["coherence"] = {}
    for tag, meta in ak["specs"].items():
        out["coherence"][tag] = {
            "gross_basis": {
                **coherence(meta["summary_authored_exit"]["mean_r_gross_by_symbol"]),
                "note": ("no surface was widened for this sleeve — these are its AUTHORED "
                         "symbols (supply.py SUPPLY_SPECS), so no new family member was minted "
                         "and the trial count does not grow for the coherence test itself"),
            },
        }
        c = out["coherence"][tag]["gross_basis"]
        print(f"coherence(gross) {tag:26s} k={c['k']} ratio={c['dispersion_ratio']} "
              f"all_pos={c['all_members_positive']} -> {'COHERENT' if c['coheres'] else 'mixture'}")

    # ---- build the cell populations --------------------------------------------------------
    cells: dict[str, dict] = {}

    sr_rows = ak["trades"]["structural_retest"]
    for cell, (cls, sess, reg, vol) in SR_CELLS.items():
        syms = tuple(SR_CLASSES[cls])
        ok, why = priced_symbols(costs, base.account, syms, resolve)
        rows = [r for r in sr_rows if sr_cell_of(r["symbol_canonical"]) == cell]
        keep = [r for r in rows if r["symbol_canonical"] in ok]
        cells[f"fam_structural_retest_{cell}"] = {
            "parent": "structural_retest", "kind": "whitelist_cell",
            "cell": {"class": cls, "session": sess, "regime": reg, "vol_state": vol,
                     "direction": ("SHORT" if reg == "dn" else "LONG")},
            "authored_surface": list(syms),
            "priceable_surface": sorted(ok),
            "dropped_symbols": {s: why[s] for s in sorted(set(syms) - ok)},
            "n_trades_authored_surface": len(rows),
            "n_trades_priceable": len(keep),
            "n_trades_dropped": len(rows) - len(keep),
            "retained_frac": round(len(keep) / len(rows), 5) if rows else None,
            "rows": keep,
        }

    sl_rows = ak["trades"]["session_leadlag_genuine"]
    for leg in SL.LEGS:
        tag = f"{leg.leader}->{leg.follower}@{leg.geom}"
        rows = [r for r in sl_rows if r["ll_impulse"] == tag]
        ok, why = priced_symbols(costs, base.account, (leg.follower,), resolve)
        cells[f"fam_session_leadlag_{leg.leader}_{leg.follower}_{leg.geom}".lower()] = {
            "parent": "session_leadlag_genuine", "kind": "declared_leg",
            "cell": {"leader": leg.leader, "follower": leg.follower, "look": leg.look,
                     "zthr": leg.zthr, "thesis": leg.thesis, "geom": leg.geom,
                     "session": leg.session, "note": leg.note},
            "authored_surface": [leg.follower],
            "priceable_surface": sorted(ok),
            "dropped_symbols": {s: why[s] for s in sorted({leg.follower} - ok)},
            "n_trades_authored_surface": len(rows),
            "n_trades_priceable": len(rows) if ok else 0,
            "n_trades_dropped": 0 if ok else len(rows),
            "retained_frac": 1.0 if ok else 0.0,
            "rows": rows if ok else [],
        }

    # ---- fidelity records, then gate the cells inside the family ---------------------------
    clear_surface_expansions()
    registered = {}
    for name, c in sorted(cells.items()):
        rec = register_surface_expansion(
            name, parent=c["parent"],
            symbol=",".join(c["priceable_surface"]) or "(none priceable)",
            timeframe="M15",
            surface_note=(
                f"PRE-DECLARED {c['kind']} of {c['parent']}, not a symbol expansion: a SUBSET of "
                f"the parent's own authored surface, declared in the parent's source before any "
                f"outcome in this session was seen. Restricted to the symbols cost_r can price "
                f"({len(c['priceable_surface'])} of {len(c['authored_surface'])}), which is "
                f"outcome-independent; {c['n_trades_dropped']} trades dropped with reasons in "
                f"AK_SLEEVE_CELLS_V1.json -> cells.{name}.dropped_symbols"),
        )
        registered[name] = {"cls": rec.cls.value, "basis": rec.basis.value,
                            "live_recall": rec.live_recall}

    allow = dict(AD.allowlist())
    for tag, spec in SUP.SUPPLY_SPECS.items():
        allow[tag] = tuple(sorted({resolve(s) for s in spec.on_surface}))
    for name, c in cells.items():
        allow[name] = tuple(sorted({resolve(s) for s in c["priceable_surface"]}))

    # The family is AA's 32 + the four parents + the cells, so multiplicity is charged for the
    # cells too. Held at AA's declared_family_size so the parents' own verdicts do not move.
    rows_by: dict[str, list[dict]] = {s: list(v) for s, v in aa["trades"].items()}
    for tag, v in ak["trades"].items():
        rows_by[tag] = list(v)
    for name, c in cells.items():
        rows_by[name] = [{**r, "sleeve": name} for r in c["rows"]]

    spec = base.with_(spec_id=f"{base.spec_id}_ak_cells",
                      sleeve_symbol_allowlist=allow,
                      declared_family_size=AD.DECLARED_FAMILY)
    print(f"\ngating {len(rows_by)} sleeves ({len(cells)} cells) ...", flush=True)
    res = run_gate({s: AD.to_records(v) for s, v in rows_by.items()},
                   spec, costs=costs, diagnose=True, server=SERVER)

    out["gate"] = {"option": "B_balanced", "spec_id": spec.spec_id,
                   "spec_sha256": spec.seal(), "account": spec.account,
                   "declared_family_size": AD.DECLARED_FAMILY,
                   "n_sleeves_judged": len(res.verdicts)}
    out["fidelity_records"] = registered
    out["cells"] = {}
    for name, c in sorted(cells.items()):
        sv = res.verdicts.get(name)
        d = (sv.diagnostics or {}) if sv else {}
        cd = d.get("cost_decomposition") or {}
        per = {s: statistics.fmean(r["r_gross"] for r in c["rows"]
                                   if r["symbol_canonical"] == s)
               for s in c["priceable_surface"]
               if any(r["symbol_canonical"] == s for r in c["rows"])}
        out["cells"][name] = {
            **{k: v for k, v in c.items() if k != "rows"},
            "verdict": (sv.verdict.value if sv else None),
            "pooled_oos_mean_r": (sv.pooled_oos_mean_r if sv else None),
            "p_raw": (sv.p_raw if sv else None), "q_value": (sv.q_value if sv else None),
            "failing_gates": ([g for g in ("expectancy", "lifetime", "stability", "robustness",
                                           "significance")
                               if not sv.gates.get(g, {}).get("pass")] if sv else None),
            "gates": ({g: bool(v.get("pass")) for g, v in sorted(sv.gates.items())}
                      if sv else None),
            "coverage_frac": (sv.gates.get("cost_coverage", {}).get("coverage_frac")
                              if sv else None),
            "n_folds_evaluable": (sv.gates.get("sample", {}).get("n_folds_evaluable")
                                  if sv else None),
            "oos_positive_fold_frac": (sv.gates.get("stability", {}).get(
                "oos_positive_fold_frac") if sv else None),
            "drop_best_retention": (sv.gates.get("robustness", {}).get("retention")
                                    if sv else None),
            "mean_gross_r": cd.get("mean_gross_r"),
            "cost_pct_of_abs_gross": cd.get("cost_pct_of_abs_gross"),
            "cost_terms_mean_r": {k: (v or {}).get("mean_r")
                                  for k, v in sorted((cd.get("terms") or {}).items())},
            "largest_cost_term": cd.get("largest_term"),
            "by_fold": d.get("by_fold"),
            "primary_prescription": d.get("primary_prescription"),
            "reasons": (list(sv.reasons) if sv else None),
            "coherence": coherence(per),
            "fidelity_note": fidelity_for(name).basis_note,
        }
        r = out["cells"][name]
        print(f"  {name:52s} {str(r['verdict']):14s} n={r['n_trades_priceable']:5d} "
              f"pooled={r['pooled_oos_mean_r']} p={r['p_raw']} "
              f"failing={r['failing_gates']} -> {r['primary_prescription']}")
        ledger.record(
            mechanism="pre_declared_cell_gate", sleeve=name,
            variant={"parent": c["parent"], "kind": c["kind"], **c["cell"],
                     "priceable_surface": c["priceable_surface"]},
            window="full_archive", spec_sha256=spec.seal(),
            outcome={"ADMIT": "admitted", "REJECT": "rejected",
                     "NOT_EVALUABLE": "not_evaluable"}.get(
                         r["verdict"] or "", "evaluated"),
            metric=r["pooled_oos_mean_r"], metric_name="pooled_oos_mean_r",
            note="AK pre-declared cell/leg decomposition")

    # Parent verdicts recomputed in THIS family, so the report can say whether adding the cells
    # moved them (it moves BH ranks, not pooled means).
    out["parents_in_this_family"] = {
        tag: {"verdict": res.verdicts[tag].verdict.value,
              "pooled_oos_mean_r": res.verdicts[tag].pooled_oos_mean_r,
              "p_raw": res.verdicts[tag].p_raw, "q_value": res.verdicts[tag].q_value}
        for tag in SUP.SUPPLY_SPECS if tag in res.verdicts}

    # ---- the same coherence test on a NET basis, on the MATCHED population ----------------
    #
    # AF's dispersion ratio is computed on per-member GROSS R (`af_repairs.py:820` builds
    # `[r["r_gross"] for r in ... if r["engine_reachable"]]`; the artifact key is
    # `member_mean_r_gross`). Charging cost can move a member's sign, so the two bases can
    # disagree — and where they do, the rule prescribes breadth for a sleeve whose net edge sits
    # in one member.
    #
    # **CORRECTED after an adversarial pass on this session's own claim (B972).** The first
    # version of this block read gross from the trades and net from `diagnostics.by_symbol`, and
    # those are DIFFERENT POPULATIONS: `by_symbol` is built over `status == "priced"` trades
    # only, while the trades include the rows the gate drops for the default 2026-03
    # `reserved_blackout` (`spec.py:98`, `panel.py:242-249`). Nothing warns you, because
    # `coverage_frac` excludes blackout drops from its denominator (`panel.py:313,323`) — so a
    # cell reads `coverage_frac 1.0` while up to 18 % of its rows never reach the net basis. On
    # `fam_structural_retest_metal_london_short` that mismatch MANUFACTURED a flip: 76 of 416
    # rows are March-2026, and on the matched population the cell does not cohere on gross
    # either. The fix was one field away the whole time: `by_symbol` already emits
    # `mean_gross_r` beside `mean_net_r` over identical rows (`diagnostics.py:316-317`). Both
    # readings are published — the matched pair is authoritative and the unmatched one is kept
    # so the correction is visible rather than overwritten.
    def _pair_maps(sv):
        rows = (sv.diagnostics or {}).get("by_symbol", []) or []
        g = {r["symbol"]: r["mean_gross_r"] for r in rows
             if r.get("mean_gross_r") is not None}
        n = {r["symbol"]: r["mean_net_r"] for r in rows if r.get("mean_net_r") is not None}
        return g, n

    flips, degenerate, artifacts = [], [], []
    for tag in list(SUP.SUPPLY_SPECS) + sorted(cells):
        sv = res.verdicts.get(tag)
        if sv is None:
            continue
        gm, nm = _pair_maps(sv)
        g_matched, net = coherence(gm), coherence(nm)
        holder = out["coherence"].setdefault(tag, {})
        unmatched = holder.get("gross_basis") or (
            out["cells"].get(tag, {}).get("coherence") if tag in out["cells"] else None)
        holder["gross_basis_unmatched_population"] = {
            **(unmatched or {}),
            "note": ("SUPERSEDED — gross over ALL generated rows, including the ones the "
                     "2026-03 reserved_blackout removes from the net basis. Kept so the "
                     "correction is visible."),
        }
        holder["gross_basis"] = {**g_matched, "note": (
            "per-member mean GROSS R from diagnostics.by_symbol, i.e. over EXACTLY the rows the "
            "net basis uses. This is the authoritative gross reading.")}
        holder["net_basis"] = {**net, "note": (
            "per-member mean NET R from diagnostics.by_symbol, after broker-true cost.")}
        holder["bases_agree"] = (g_matched.get("coheres") == net.get("coheres"))
        holder["k"] = g_matched.get("k")
        if g_matched.get("coheres") and not net.get("coheres"):
            (degenerate if (g_matched.get("k") or 0) < 2 else flips).append(tag)
        if (unmatched or {}).get("coheres") and not g_matched.get("coheres"):
            artifacts.append(tag)
    out["coherence_basis_correction"] = {
        "what": ("AF §0's two-clause rule is computed on per-member GROSS R (af_repairs.py:820). "
                 "Measured here on gross and net over the IDENTICAL row population, the two "
                 "disagree on several sleeves, and where they do the rule prescribes breadth "
                 "for a sleeve whose net edge sits in one member."),
        "genuine_multi_member_flips": flips,
        "n_genuine_multi_member_flips": len(flips),
        "degenerate_single_member_cells": degenerate,
        "single_member_note": ("k=1 makes sd 0 and the ratio 0, so the test passes vacuously and "
                              "says nothing about breadth. Excluded from the count."),
        "flips_that_were_an_unmatched_population_ARTIFACT": artifacts,
        "artifact_note": ("these cohere on gross ONLY when gross is taken over rows the net "
                          "basis never sees — the 2026-03 reserved_blackout. On the matched "
                          "population they do not cohere on gross either, so they were never "
                          "flips. This is the correction, found by an adversarial pass on this "
                          "session's own claim (B972)."),
        "why_it_happens": ("charging broker truth can move a member's SIGN, and the cost is not "
                           "uniform across members — but NOT because the R unit differs: within "
                           "these sleeves the stop rule is one symbol-agnostic ATR constant "
                           "(e.g. structural_retest.py:126-163). The spread is dominated by the "
                           "INSTRUMENT's own spread and swap drag, which is why XAUAUD pays "
                           "0.10 R and XAGAUD 0.53 R on the same rule, and why "
                           "ny_index_momentum's WIDEST-stop member (JP225) is its most "
                           "expensive. An earlier draft of this note blamed the R unit and the "
                           "data invert that ordering."),
        "prescription": ("run the two-clause test on the `mean_gross_r` / `mean_net_r` PAIR from "
                         "diagnostics.by_symbol, never on gross-from-trades against "
                         "net-from-diagnostics. It costs nothing extra and it is the only way "
                         "the two are over the same rows."),
    }
    print(f"\ncoherence: {len(flips)} genuine multi-member flips {flips}; "
          f"{len(degenerate)} degenerate k=1 {degenerate}; "
          f"{len(artifacts)} were unmatched-population artifacts {artifacts}")

    # ---- exit frontier PER CELL ------------------------------------------------------------
    #
    # The parent `structural_retest` is NOT_EVALUABLE at every exit cell, because coverage is a
    # property of the population and no exit change moves it. So its exit repair can only be
    # measured on the cells — which is the same reason the cells exist. AD's plan, AD's
    # resimulation, AD's summary, imported.
    if os.environ.get("AK_CELL_SWEEP", "1") != "0":
        print("\n=== per-cell exit frontier ===", flush=True)
        t0 = time.time()
        series, index, _r = AD.load_bars()
        rule = AD.resolve_rule(SERVER)
        print(f"  {len(series)} series in {time.time()-t0:.0f}s", flush=True)
        n_cells_gated = 0
        for name, c in sorted(cells.items()):
            src = rows_by.get(name) or []
            if not src:
                out["cells"][name]["exit_frontier"] = {
                    "available": False, "reason": "no priceable trades in this cell"}
                continue
            plan = list(AD.plan_for(c["parent"], AD.TF_M15, {}))
            authored = SUP.SUPPLY_SPECS.get(c["parent"])
            if authored is not None:
                ts = authored.authored_exit.get("time_stop_bars")
                plan.append(AD.Variant(
                    name="authored_contract", family="authored",
                    time_stop_bars=(int(ts) if ts else None), target_mode="native",
                    note=authored.authored_exit["cite"]))
            cellres: dict[str, dict] = {}
            for v in plan:
                new_rows, tel = AD.resimulate(src, v, series, index, costs, spec.account, rule)
                if not new_rows:
                    continue
                fam = {s: AD.to_records(r if s != name else new_rows)
                       for s, r in rows_by.items()}
                g = run_gate(fam, spec, costs=costs, diagnose=True, server=SERVER)
                cellres[v.name] = {"variant": v.as_dict(),
                                   **AD.summarize(g.verdicts[name], tel, len(new_rows))}
                n_cells_gated += 1
                ledger.record(
                    mechanism="exit_repair_sweep", sleeve=name, variant=v.as_dict(),
                    window="full_archive", spec_sha256=spec.seal(),
                    outcome={"ADMIT": "admitted", "REJECT": "rejected",
                             "NOT_EVALUABLE": "not_evaluable"}.get(
                                 g.verdicts[name].verdict.value, "evaluated"),
                    metric=g.verdicts[name].pooled_oos_mean_r,
                    metric_name="pooled_oos_mean_r",
                    note=f"AK per-cell exit frontier, {v.family} cell {v.name}")
            ok = {k: x for k, x in cellres.items() if x.get("pooled_oos_mean_r") is not None}
            best = max(ok, key=lambda k: ok[k]["pooled_oos_mean_r"]) if ok else None
            base_v = (cellres.get("as_walked") or {}).get("pooled_oos_mean_r")
            out["cells"][name]["exit_frontier"] = {
                "available": True, "n_cells": len(ok),
                "as_walked_pooled_oos_mean_r": base_v,
                "best_cell": best,
                "best_pooled_oos_mean_r": (ok[best]["pooled_oos_mean_r"] if best else None),
                "delta_vs_as_walked": (round(ok[best]["pooled_oos_mean_r"] - base_v, 6)
                                       if best and base_v is not None else None),
                "best_verdict": (ok[best]["verdict"] if best else None),
                "best_failing_gates": (ok[best]["failing_gates"] if best else None),
                "cells": cellres,
            }
            f = out["cells"][name]["exit_frontier"]
            print(f"  {name:52s} as_walked {f['as_walked_pooled_oos_mean_r']} -> "
                  f"{f['best_cell']} {f['best_pooled_oos_mean_r']} "
                  f"(delta {f['delta_vs_as_walked']}) {f['best_verdict']} "
                  f"failing {f['best_failing_gates']}", flush=True)
        out["n_cell_exit_cells_gated"] = n_cells_gated

    # THREE DIFFERENT DEFECTS, not one ask — and a completeness pass got this half-right before
    # measurement finished the job. A symbol with no tick file needs a CAPTURE. A symbol the
    # RESOLVER cannot map needs one line in the profile's symbol map and is already fully priced.
    # Distinguishing them is the difference between a VPS ceremony and a one-line edit.
    dropped_all = {s: w for c in out["cells"].values()
                   for s, w in (c.get("dropped_symbols") or {}).items()}
    unmappable = sorted(s for s, w in dropped_all.items() if "no instrument record" in w)
    no_spread = sorted(s for s, w in dropped_all.items() if "no instrument record" not in w)
    # For each unmappable name, is it priced in the artifact under a DIFFERENT key?
    inst = ((costs.doc.get("accounts") or {}).get(base.account) or {}).get("instruments") or {}
    alias_hits = {}
    for sym in unmappable:
        for key in inst:
            if key.replace(".", "_") != sym:
                continue
            sp = (inst[key] or {}).get("spread_price") or {}
            alias_hits[sym] = {
                "artifact_key": key,
                "has_measured_spread": bool(sp.get("by_session") or sp.get("median")
                                            or sp.get("p50")),
                "commission_kind": ((inst[key] or {}).get("commission") or {}).get("kind"),
                "resolver_maps_it_to": resolve(sym),
            }
    out["tick_capture_ask"] = {
        "what": ("what would close structural_retest's coverage refusal at its AUTHORED surface, "
                 "i.e. take it from 58.0 % to 100 %. THREE defects, not one."),
        "symbols": sorted(dropped_all),
        "why_each": dropped_all,
        "n_trades_it_would_unlock": sum(c["n_trades_dropped"] for c in out["cells"].values()),
        "defect_1_needs_a_tick_capture": {
            "symbols": no_spread,
            "n_symbols": len(no_spread),
            "n_trades": sum(c["n_trades_dropped"] for c in out["cells"].values()),
            "state": "present in the cost artifact, NO measured spread (no tick-archive file)",
            "shape": ("the same read-only VPS tick export that produced vps-ticks-20260726 — a "
                      "spread measurement, not a commission question, so a capture (unlike "
                      "energy_agri's NATGAS commission, AF §3.3)"),
        },
        "defect_2_needs_one_line_in_the_PROFILE_SYMBOL_MAP": {
            "symbols": sorted(alias_hits),
            "detail": alias_hits,
            "state": ("already FULLY PRICED in the cost artifact under the dotted key, and "
                      "unreachable only because build_broker_symbol_resolver returns the "
                      "canonical name unchanged. The profile maps US500_cash -> US500.cash and "
                      "US100_cash -> US100.cash and has no entry for this one."),
            "cost_to_fix": "one profile entry; no capture, no artifact regeneration",
            "why_it_changes_nothing_here": ("these symbols have no bars in the archive either, so "
                                            "they generate 0 trades and none of this session's "
                                            "numbers moves. It is a wiring row, kept because the "
                                            "next session to widen this surface would pay for it."),
            "found_by": ("a completeness pass flagged AUS200_cash as a cost-artifact gap; "
                         "measurement showed the artifact HAS it (AUS200.cash, by_session "
                         "populated, commission zero) and the resolver does not"),
        },
        "defect_3_no_bars": {
            "symbols": sorted(alias_hits),
            "state": "absent from vps-bars-20260727 as well — AF §7 recorded the same for "
                     "mx_aus200_volume_surge and mx_spn35_volume_surge",
            "shape": "the bars-export ceremony AA §4 item 2 already names",
        },
    }
    clear_surface_expansions()
    out["seconds_total"] = round(time.time() - t_start, 1)
    OUT.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)} in {time.time()-t_start:.0f}s")
    print(f"ledger: {ledger.n_written} rows written, {ledger.write_errors} errors")
    return out


if __name__ == "__main__":
    main()
