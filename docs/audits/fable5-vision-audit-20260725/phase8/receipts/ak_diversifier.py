"""The diversifier door, run at the repaired exits, against the book that is actually armed.

    python3 docs/audits/fable5-vision-audit-20260725/phase8/receipts/ak_diversifier.py

WHAT THIS ASKS
--------------
AD moved three quarantined sleeves' best exit cells to within noise of zero:

    asian_fade                -0.780 -> -0.009  (trail_a2_g0.5_prod)
    kz_london_crypto_low      -0.592 -> -0.011  (stop_3x_tgtscale)
    metal_session_reversion   -0.796 -> -0.170  (POST_HOC_COMPOSITE)

A ~zero-mean sleeve cannot pass a standalone gate and can still raise a book's Sharpe if it is
uncorrelated — that is IR ~ IC x sqrt(breadth), and it is the shape the diversifier door exists
for. The door has never been run against the armed book. It is run here, plus
`ny_index_momentum`, which this session's gate left failing significance ALONE and which is
therefore the same shape from the other direction.

THE BOOK IS THE ONE THAT IS ARMED, NOT THE ONE THAT IS CONVENIENT
------------------------------------------------------------------
`crypto`, `energy_agri`, `sub_xvol_pullback` — the three `run_book.py --tags` carries on FTMO as
of 2026-07-29 14:25 UTC (`CLAUDE.md` §4). NOT the four survivors, NOT core-8, NOT the
account-intersection book. Session T recorded that no MC exists for the armed three; this is not
an MC, but the base book is at least the right set.

BOTH TRAIL BOUNDS, AND THE HONEST ONE WINS TIES
-----------------------------------------------
`asian_fade`'s best cell is a PRODUCTION-bound trail cell, and B613/B754 established that 95.8 %
of its apparent trail gain is intrabar sequencing on this very sleeve. The commission's rule is
followed literally: both bounds are certified, and **where the honest bound flips the sign the
verdict reported is the honest bound's.**

AND THE COMPOSITE IS NOT TAKEN ON TRUST
----------------------------------------
`metal_session_reversion`'s best cell is AD's one post-hoc composite, which AD's own §7.1
measured as WORSE than the best single cell on 17 of 25 sleeves. Both are run: the composite and
the best single non-composite cell, labelled.

WHAT `standalone_edge_ok` AND `regime_clean` ARE HERE
-----------------------------------------------------
`certify_diversifier` takes both as caller booleans and says exactly what it wants
(`portfolio_contribution.py:142-147`): a PSR-vs-zero significant AND block-permutation
directional edge, and `regime_inflation`'s `contamination_flag` clear. Neither is asserted — the
PSR and the block permutation are computed from the candidate's own daily series, and the
contamination flag is read from the walk-forward gate's own `regime_inflation` diagnostic, which
Session AE verified sound after B451 fixed its sign defect. A ~zero-mean sleeve is expected to
fail `genuine_edge`; the point is to find out WHICH door it fails at and what the incremental
Sharpe and correlation actually are, because those numbers have never been computed.
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
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
from src.costs import load_broker_true_costs  # noqa: E402
from src.research_infra.validation_integrity.dsr import (  # noqa: E402
    probabilistic_sharpe_ratio,
)
from src.research_infra.validation_integrity.perm_null import (  # noqa: E402
    block_permutation_test,
)
from src.research_infra.validation_integrity.trial_budget_ledger import (  # noqa: E402
    DEFAULT_TRIAL_LEDGER,
    TrialLedger,
)
from src.research_infra.walkforward import TradeRecord, run_gate  # noqa: E402
from src.research_infra.walkforward.book_replay import (  # noqa: E402
    BookConfig,
    BookTrade,
    book_daily_series,
    book_stats,
    replay_book,
)
from src.research_infra.walkforward.diversifier import (  # noqa: E402
    DiversifierEvidence,
    certify_guarded,
)
from src.research_infra.walkforward.options import OPTIONS  # noqa: E402
from src.research_infra.walkforward.panel import price_trades  # noqa: E402

AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"
AK_IN = HERE / "AK_SUPPLY_TRADES.json.gz"
FRONTIERS = [
    REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts/EXIT_FRONTIER_V1.json",
    REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts/EXIT_FRONTIER_V1_TRAIL.json",
    HERE / "AK_EXIT_FRONTIER_V2.json",
]
OUT = HERE / "AK_DIVERSIFIER_V1.json"
SERVER = AD.SERVER

#: The set `run_book.py --tags` carries on FTMO (CLAUDE.md §4, 2026-07-29 14:25 UTC).
ARMED = ("crypto", "energy_agri", "sub_xvol_pullback")

#: The candidates, in a fixed order declared before any certification was run.
CANDIDATES = ("asian_fade", "kz_london_crypto_low", "metal_session_reversion",
              "ny_index_momentum")

#: `certify_diversifier`'s sealed-split boundary. The last calendar year of the archive, so the
#: `oos_robust` check has a genuinely held-back tail. A date, not a result.
SEALED_START = "2025-07-01"


def load_frontiers() -> dict[str, dict]:
    """sleeve -> {cell_name: cell}, merged across every frontier artifact on disk."""
    out: dict[str, dict] = {}
    for p in FRONTIERS:
        if not p.is_file():
            print(f"  (absent: {p.name})")
            continue
        d = json.loads(p.read_text())
        for s, sl in (d.get("sleeves") or {}).items():
            if not isinstance(sl, dict) or not sl.get("cells"):
                continue
            out.setdefault(s, {}).update(sl["cells"])
    return out


def pick_cells(sleeve: str, cells: dict) -> list[dict]:
    """The cells to certify for one sleeve, with why each was picked.

    Always: the best gated cell. Additionally the honest counterpart when the best is a
    production-bound trail cell, and the best NON-composite cell when the best is the composite.
    """
    ok = {k: c for k, c in cells.items()
          if isinstance(c, dict) and c.get("pooled_oos_mean_r") is not None}
    if not ok:
        return []
    best = max(ok, key=lambda k: ok[k]["pooled_oos_mean_r"])
    picks = [{"cell": best, "why": "best gated cell on this sleeve's exit frontier",
              "bound": ("production" if best.endswith("_prod") else None)}]
    if best.endswith("_prod"):
        # `_prod` -> `_honest`, keeping the separator. The first version of this line dropped the
        # underscore (`best[:-len("_prod")] + "honest"` -> `trail_a2_g0.5honest`), so the lookup
        # below was ALWAYS False and the commission's both-bounds rule silently did not run on the
        # one candidate B613 measured as 95.8 % intrabar sequencing. Found by a completeness pass.
        honest = best[: -len("_prod")] + "_honest"
        if honest in ok:
            picks.append({"cell": honest, "bound": "intrabar_honest",
                          "why": ("B613/B754: the production trail arms and fills inside one "
                                  "bar. Both bounds are certified and where the honest bound "
                                  "flips the sign the honest verdict is the one reported")})
    if best == "POST_HOC_COMPOSITE":
        rest = {k: c for k, c in ok.items() if k != "POST_HOC_COMPOSITE"}
        if rest:
            alt = max(rest, key=lambda k: rest[k]["pooled_oos_mean_r"])
            picks.append({"cell": alt, "bound": None,
                          "why": ("AD §7.1: the composite underperforms the best single cell on "
                                  "17 of 25 sleeves, so the best single cell is certified too")})
    return picks


def variant_for(cell_name: str, cells: dict, sleeve: str, tf: int, units: dict) -> AD.Variant:
    """Rebuild the `Variant` for a named cell from the sleeve's own plan.

    Rebuilt from `plan_for` rather than reconstructed from the artifact's `variant` dict, so the
    cell certified here is bit-identically the cell the frontier gated.
    """
    plan = {v.name: v for v in AD.plan_for(sleeve, tf, units)}
    if cell_name in plan:
        return plan[cell_name]
    if cell_name == "POST_HOC_COMPOSITE":
        d = dict((cells.get(cell_name) or {}).get("variant") or {})
        d.pop("name", None)
        d.pop("family", None)
        note = d.pop("note", "")
        return AD.Variant(name="POST_HOC_COMPOSITE", family="composite", note=note, **d)
    raise KeyError(f"{sleeve}: cell {cell_name!r} is not in its plan and is not the composite")


def to_book_trades(rows: list[dict], spec, costs) -> tuple[list[BookTrade], dict]:
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
    keep: list[BookTrade] = []
    lifetime: list[float] = []
    for p in priced:
        if p.status != "priced" or p.r_net is None:
            continue
        t = p.trade
        lifetime.append(float(p.r_net))
        keep.append(BookTrade(
            sleeve=t.sleeve, symbol=t.symbol,
            symbol_canonical=t.features.get("symbol_canonical") or t.symbol,
            entry_utc=t.entry_utc, exit_utc=t.exit_utc, direction=t.direction,
            stop_dist=t.sl_distance_price, entry_price=t.entry_price,
            r_net=float(p.r_net), decision_day=str(t.features["decision_day"]),
            decision_bar_iso=(str(t.features["decision_bar_iso"])
                              if t.features.get("decision_bar_iso") else None),
            timeframe=t.features.get("timeframe"),
            intra_size=float(t.features.get("intra_size") or 1.0)))
    c = cov.get(rows[0]["sleeve"]) if rows else None
    meta = {
        "n_total": (c.n_total if c else len(recs)),
        "n_priced": (c.n_priced if c else len(keep)),
        "coverage_frac": (c.coverage_frac if c else None),
        "n_blackout": getattr(c, "n_blackout", None),
        "blackout_r_gross": getattr(c, "blackout_r_gross", None),
        "lifetime_mean_r": (statistics.fmean(lifetime) if lifetime else float("nan")),
    }
    return keep, meta


def main() -> dict:
    t_start = time.time()
    ledger = TrialLedger(REPO / DEFAULT_TRIAL_LEDGER, session="AK")
    aa = json.load(gzip.open(AA_IN, "rt"))
    ak = json.load(gzip.open(AK_IN, "rt"))
    costs = load_broker_true_costs(AD.COSTS)
    units = json.loads(AD.UNITS.read_text())
    frontiers = load_frontiers()
    print(f"frontiers merged for {len(frontiers)} sleeves")

    rows_all: dict[str, list[dict]] = {s: list(v) for s, v in aa["trades"].items()}
    for tag, v in ak["trades"].items():
        rows_all[tag] = list(v)
    tf_of = {s: {"M15": AD.TF_M15, "H4": AD.TF_H4, "D1": AD.TF_D1}[v]
             for s, v in aa["timeframe_by_sleeve"].items()}
    for tag, meta in ak["specs"].items():
        tf_of[tag] = {"M15": AD.TF_M15, "H4": AD.TF_H4, "D1": AD.TF_D1}[meta["timeframe"]]

    spec = OPTIONS["B_balanced"].with_(spec_id="B_balanced_ak_diversifier",
                                      declared_family_size=AD.DECLARED_FAMILY)
    rt = dict(yaml.safe_load(open(REPO / "config/agent_config.yaml"))
              .get("gtos_vnext_runtime") or {})
    # The research override AA used: the flag is flipped in the DICT, never on disk. The file is
    # H1-bound AND the live activation token binds its digest.
    rt["ultimate_book_include_clean3"] = True

    print("\n=== the armed book (crypto, energy_agri, sub_xvol_pullback) ===")
    base_trades: list[BookTrade] = []
    for s in ARMED:
        bt, meta = to_book_trades(rows_all.get(s) or [], spec, costs)
        print(f"  {s:20s} {meta['n_priced']}/{meta['n_total']} priced "
              f"(coverage {meta['coverage_frac']})")
        base_trades.extend(bt)
    base_res = replay_book(base_trades, BookConfig(runtime=rt, sleeves=ARMED, label="armed3"))
    base_st = book_stats(base_res)
    base_daily = {d.isoformat(): v for d, v in book_daily_series(base_res).items()}
    halted_base = sum(v for k, v in base_res.rejections.items() if "max_dd" in k)
    print(f"  armed3: n_placed {base_st['n_placed']} ret {base_st['total_return_pct']}% "
          f"DD {base_st['max_drawdown_pct']}% sharpe {base_st['book_daily_sharpe']} "
          f"days {len(base_daily)} halt {'YES' if halted_base else 'no'}")

    series, index, _res = None, None, None
    out: dict = {
        "schema": "gtos.walkforward.diversifier_run.v1",
        "generated_by": ("docs/audits/fable5-vision-audit-20260725/phase8/receipts/"
                         "ak_diversifier.py"),
        "session": "AK", "blocks": "B950-B999",
        "armed_book": {
            "sleeves": list(ARMED),
            "why_this_set": ("run_book.py --tags on FTMO as of 2026-07-29 14:25 UTC "
                             "(CLAUDE.md §4). Not the four survivors, not core-8, not the "
                             "account-intersection book."),
            "stats": base_st, "n_days": len(base_daily),
            "halted_on_max_dd_entry_block": bool(halted_base),
            "rejections": dict(sorted(base_res.rejections.items(), key=lambda kv: -kv[1])),
        },
        "sealed_start": SEALED_START,
        "cost_artifact": str(AD.COSTS.relative_to(REPO)),
        "candidates": {},
    }

    for sleeve in CANDIDATES:
        cells = frontiers.get(sleeve) or {}
        picks = pick_cells(sleeve, cells)
        if not picks:
            out["candidates"][sleeve] = {"available": False,
                                        "reason": "no gated exit cell on any frontier artifact"}
            print(f"\n### {sleeve}: no gated cell, skipped")
            continue
        if series is None:
            print("\n=== loading bars ===", flush=True)
            t0 = time.time()
            series, index, _res = AD.load_bars()
            rule = AD.resolve_rule(SERVER)
            print(f"  {len(series)} series in {time.time()-t0:.0f}s", flush=True)
        tf = tf_of[sleeve]
        out["candidates"][sleeve] = {"available": True, "cells": {}}
        for pick in picks:
            name = pick["cell"]
            v = variant_for(name, cells, sleeve, tf, units)
            cand_rows, tel = AD.resimulate(rows_all[sleeve], v, series, index, costs,
                                          spec.account, rule)
            if not cand_rows:
                out["candidates"][sleeve]["cells"][name] = {
                    "available": False, "reason": "no trade survived re-simulation", **pick}
                continue

            # the standalone gate verdict AT THIS CELL, inside the same family
            fam = {s: AD.to_records(r if s != sleeve else cand_rows)
                   for s, r in rows_all.items()}
            gres = run_gate(fam, spec, costs=costs, diagnose=True, server=SERVER)
            sv = gres.verdicts[sleeve]

            cand_bt, meta = to_book_trades(cand_rows, spec, costs)
            cand_res = replay_book(cand_bt, BookConfig(runtime=rt, sleeves=(sleeve,),
                                                       label=f"{sleeve}_solo"))
            cand_daily = {d.isoformat(): x for d, x in book_daily_series(cand_res).items()}
            # The SOLO book is what the correlation, PSR and permutation all run on, so its own
            # truncation has to be visible or `n_overlap` reads as a property of the armed book
            # when it is partly a property of this series. `asian_fade` places 237 of 1,275 and
            # stops in 2024. Added after a completeness pass over this artifact.
            halted_solo = sum(x for k, x in cand_res.rejections.items() if "max_dd" in k)
            solo_trunc = {
                "n_priced_offered": len(cand_bt),
                "n_placed": len(cand_res.placed),
                "placed_frac": round(len(cand_res.placed) / max(1, len(cand_bt)), 5),
                "first_day": (min(cand_daily) if cand_daily else None),
                "last_day": (max(cand_daily) if cand_daily else None),
                "halted_on_max_dd_entry_block": bool(halted_solo),
                "n_cycles_blocked_by_max_dd": halted_solo,
                "top_rejections": dict(sorted(cand_res.rejections.items(),
                                              key=lambda kv: -kv[1])[:5]),
                "why_this_matters": ("certify_guarded's correlation_sample, PSR and block "
                                     "permutation all read THIS series. A truncated solo book "
                                     "makes n_overlap small for a reason that is not the armed "
                                     "book's day count."),
            }
            with_res = replay_book(base_trades + cand_bt,
                                   BookConfig(runtime=rt, sleeves=tuple(ARMED) + (sleeve,),
                                              label=f"armed3+{sleeve}"))
            with_st = book_stats(with_res)
            halted_with = sum(x for k, x in with_res.rejections.items() if "max_dd" in k)

            daily_vals = list(cand_daily.values())
            psr = probabilistic_sharpe_ratio(daily_vals) if len(daily_vals) > 2 else {}
            perm = (block_permutation_test(daily_vals, block=5, n_perm=5000)
                    if len(daily_vals) > 10 else {})
            psr_p = psr.get("psr")
            perm_p = perm.get("p_value", perm.get("p"))
            standalone_ok = bool(psr_p is not None and psr_p >= 0.95
                                 and perm_p is not None and perm_p < 0.05)
            ri = (sv.telemetry or {}).get("regime_inflation") or \
                 (sv.diagnostics or {}).get("regime_inflation") or {}
            regime_clean = bool(ri.get("available") and not ri.get("contamination_flag"))

            ev = DiversifierEvidence(
                sleeve=sleeve, gate_verdict=sv.verdict.value,
                gate_reasons=tuple(sv.reasons),
                coverage_frac=float(meta["coverage_frac"] or 0.0),
                coverage_floor=spec.cost_coverage_floor,
                blackout_r_gross=float(meta.get("blackout_r_gross") or 0.0),
                n_blackout_trades=int(meta.get("n_blackout") or 0),
                lifetime_mean_r=float(meta["lifetime_mean_r"]),
                n_trades_total=int(meta["n_total"]), n_trades_priced=int(meta["n_priced"]),
                base_book_stats=base_st, with_candidate_book_stats=with_st,
                with_candidate_rejections=dict(with_res.rejections),
                book_evidence_informative=not (halted_base and halted_with),
            )
            cert = certify_guarded(base_daily, cand_daily, ev,
                                   standalone_edge_ok=standalone_ok,
                                   regime_clean=regime_clean,
                                   sealed_start=SEALED_START)
            row = {
                "available": True, **pick,
                "variant": v.as_dict(),
                "n_resimulated": len(cand_rows),
                "standalone_gate": {
                    "verdict": sv.verdict.value,
                    "pooled_oos_mean_r": sv.pooled_oos_mean_r,
                    "p_raw": sv.p_raw, "q_value": sv.q_value,
                    "failing_gates": [g for g in ("expectancy", "lifetime", "stability",
                                                  "robustness", "significance")
                                      if not sv.gates.get(g, {}).get("pass")],
                },
                "standalone_edge_inputs": {
                    "psr_vs_zero": psr_p, "psr_threshold": 0.95,
                    "block_permutation_p": perm_p, "perm_threshold": 0.05,
                    "standalone_edge_ok": standalone_ok,
                    "n_candidate_days": len(daily_vals),
                    "note": ("computed, not asserted — portfolio_contribution.py:142-145 says "
                             "exactly what it wants and this is it"),
                },
                "regime_inflation": {
                    "available": bool(ri.get("available")),
                    "contamination_flag": ri.get("contamination_flag"),
                    "fwd_all_mean_ratio": ri.get("fwd_all_mean_ratio"),
                    "recommended_magnitude_haircut": ri.get("recommended_magnitude_haircut"),
                    "regime_clean_passed_to_door": regime_clean,
                    "note": ("read from the gate's own diagnostic, which AE verified sound "
                             "after B451 fixed its sign defect"),
                },
                "candidate_solo_book": {
                    "n_placed": len(cand_res.placed), "n_days": len(cand_daily),
                    "stats": book_stats(cand_res), "truncation": solo_trunc,
                },
                "with_candidate_book": with_st,
                "halted_on_max_dd": {"base": bool(halted_base), "with": bool(halted_with)},
                "certification": cert.as_dict(),
            }
            out["candidates"][sleeve]["cells"][name] = row
            print(f"  {sleeve:24s} {name:24s} [{pick.get('bound') or 'n/a':16s}] "
                  f"cell_pooled={sv.pooled_oos_mean_r:+.4f} corr="
                  f"{cert.raw['checks']['low_correlation'].get('corr')} "
                  f"dSharpe={row['with_candidate_book']['book_daily_sharpe'] - base_st['book_daily_sharpe']:+.5f} "
                  f"dRet={row['with_candidate_book']['total_return_pct'] - base_st['total_return_pct']:+.3f}pp "
                  f"-> {cert.verdict} failed={cert.failed_guards}", flush=True)
            ledger.record(
                mechanism="diversifier_door", sleeve=sleeve,
                variant={"cell": name, "bound": pick.get("bound"),
                         "base_book": list(ARMED), "weight": 0.5},
                window="full_archive", spec_sha256=spec.seal(),
                outcome=("certified" if cert.verdict == "CERTIFIED_DIVERSIFIER"
                         else "not_certified"),
                metric=(with_st["book_daily_sharpe"] - base_st["book_daily_sharpe"]),
                metric_name="delta_book_daily_sharpe",
                note=f"AK diversifier door at the repaired exit cell {name}")

        # The rule: where the honest bound flips the sign, the honest verdict is the one reported.
        cs = out["candidates"][sleeve]["cells"]
        prod = [k for k, c in cs.items() if c.get("bound") == "production"]
        hon = [k for k, c in cs.items() if c.get("bound") == "intrabar_honest"]
        if prod and hon:
            pv = cs[prod[0]]["standalone_gate"]["pooled_oos_mean_r"]
            hv = cs[hon[0]]["standalone_gate"]["pooled_oos_mean_r"]
            flip = (pv is not None and hv is not None and (pv > 0) != (hv > 0))
            out["candidates"][sleeve]["trail_bound_rule"] = {
                "production_cell": prod[0], "production_pooled": pv,
                "honest_cell": hon[0], "honest_pooled": hv,
                "honest_bound_flips_the_sign": flip,
                "reported_verdict_is": ("the honest bound's" if flip
                                        else "the same at both bounds"),
                "honest_verdict": cs[hon[0]]["certification"]["verdict"],
                "production_verdict": cs[prod[0]]["certification"]["verdict"],
            }

    out["seconds_total"] = round(time.time() - t_start, 1)
    OUT.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)} in {time.time()-t_start:.0f}s")
    print(f"ledger: {ledger.n_written} rows written, {ledger.write_errors} errors")
    return out


if __name__ == "__main__":
    main()
