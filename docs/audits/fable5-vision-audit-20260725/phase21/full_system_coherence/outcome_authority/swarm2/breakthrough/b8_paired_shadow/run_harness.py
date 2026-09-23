"""CLI: run the controls, run the seeded questions, write the receipts.

    python3 -m b8_paired_shadow.run_harness --controls --questions --out receipts/

Nothing here reaches a broker, a network, or the VPS.  The only writes are the receipt
files under `--out`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path
from typing import Any

from . import controls as CTL
from .arms import PairingClass
from .causality import CausalityLedger, within_day_split
from .evaluate import book_daily_difference, run_question
from .paired_stats import MultiplicityLedger, SequentialMonitor, obf_boundary
from .questions import (
    all_questions,
    cap_builder,
    q_cluster_cap_spec,
    q_entry_hour,
    sleeve_cluster_map,
)
from .substrate import Substrate

HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "receipts"

#: Lane 4 §7.1's measured shadow arrival rate for the full 29-sleeve estate.  Carried so the
#: harness's own days-to-answer can be shown against the projection it is testing.
LANE4_SHADOW_RATE_PER_MONTH = 542.6


def _json(o: Any) -> Any:
    if isinstance(o, dt.datetime):
        return o.isoformat()
    if isinstance(o, PairingClass):
        return o.value
    if isinstance(o, set):
        return sorted(o)
    return str(o)


def run_controls(sub: Substrate, out: Path) -> dict[str, Any]:
    t0 = time.time()
    res = CTL.run_all(sub)
    res["seconds"] = round(time.time() - t0, 1)
    res["generated"] = dt.datetime.now(dt.timezone.utc).isoformat()
    (out / "B8_CONTROLS_V1.json").write_text(json.dumps(res, indent=1, default=_json))
    print(f"[controls] all_pass={res['all_pass']}  ({res['seconds']}s)")
    for k in ("C1", "C2", "C3", "C4", "C5", "C6"):
        print(f"   {k}: pass={res[k].get('pass')}")
    return res


def _temporal_companions(q, res, pop, sub, ledger, causal: CausalityLedger) -> dict[str, Any]:
    """The lag and past/future companions, run automatically rather than on request.

    A sibling lane's only OOS-predictive finding survived walk-forward, strictly-prior
    training, daily refit and FOUR permutation nulls, and was killed by exactly these two
    tests.  They are therefore not optional here: every question carries them, and a question
    for which one is meaningless says NOT_APPLICABLE with a reason.
    """
    from .questions import q_ex_ante_cost_gate

    out: dict[str, Any] = {}
    kept = [i for i in pop if True]
    # -- (1) the within-day PAST vs FUTURE screen: applicable to every question ------------
    try:
        arms = [q.control, q.treatment]
        from .evaluate import evaluate_arms

        r2, k2 = evaluate_arms(kept, arms, sub)
        deltas = [r2[q.treatment.name].outcomes[i.key].r - r2[q.control.name].outcomes[i.key].r
                  for i in k2]
        out["within_day_split"] = within_day_split(
            deltas, [i.entry_utc for i in k2], [i.decision_day for i in k2])
    except Exception as exc:
        out["within_day_split"] = {"error": f"{type(exc).__name__}: {exc}"}

    # -- (2) the one-day lag, where the treatment reads time-indexed market state ----------
    decl = causal.rows.get(q.treatment.name, {})
    if not decl.get("lag_companion_applicable"):
        out["lag_1d"] = {
            "status": "NOT_APPLICABLE",
            "why": "the treatment reads no time-indexed market state -- lagging 'apply a 4R "
                   "target' by a day is still 'apply a 4R target'. A fabricated companion "
                   "that always passes is worse than none.",
        }
        return out
    if not q.id.startswith("Q7"):
        out["lag_1d"] = {"status": "NOT_IMPLEMENTED_FOR_THIS_ARM",
                         "why": "the lag hook is threaded through the cost/spread predicates "
                                "(arms.ex_ante_cost_predicate, arms.spread_geometry_predicate); "
                                "an arm whose only time-indexed input is the shared cost "
                                "anchor cannot be lagged without changing the CHARGED cost, "
                                "which would be a second treatment."}
        return out
    try:
        lagged = q_ex_ante_cost_gate(limit=0.20, lag_days=1, suffix="_lag1d")
        rl = run_question(lagged.id, lagged.control, lagged.treatment,
                          list(lagged.population(sub)), sub,
                          pairing_class=lagged.pairing_class)
        causal.register(lagged.treatment.name, lagged.treatment.information_set)
        ledger.register(lagged.treatment.name, question=lagged.id,
                        dimension=lagged.treatment.dimension,
                        declared_at=lagged.treatment.declared_at,
                        rationale=lagged.treatment.rationale,
                        p_value=rl.summary.p_block, reported=True)
        base_mean = res.summary.mean
        out["lag_1d"] = {
            "status": "MEASURED", "n": rl.n_paired,
            "mean_unlagged": round(base_mean, 6),
            "mean_lagged_1d": round(rl.summary.mean, 6),
            "ci95_block_lagged": list(rl.summary.ci95_block) if rl.summary.ci95_block else None,
            "retention": (round(rl.summary.mean / base_mean, 4) if base_mean else None),
            "reading": "a gate whose value evaporates under a one-day lag is reading "
                       "contemporaneous state. That can still be legitimate live -- the "
                       "spread IS observable at the decision -- but it is a different claim "
                       "from 'this gate encodes a persistent property'.",
        }
    except Exception as exc:
        out["lag_1d"] = {"status": "ERROR", "error": f"{type(exc).__name__}: {exc}"}
    return out


def run_questions(sub: Substrate, out: Path, ledger: MultiplicityLedger) -> dict[str, Any]:
    qs = list(all_questions()) + [q_entry_hour("mx_btcusd_d1_donchian_20_breakout", 1)]
    causal = CausalityLedger()
    payload: dict[str, Any] = {"questions": {}, "generated": dt.datetime.now(dt.timezone.utc).isoformat()}
    for q in qs:
        t0 = time.time()
        pop = list(q.population(sub))
        for a in (q.control, q.treatment, *[x[1] for x in q.aux]):
            causal.register(a.name, a.information_set)
            ledger.register(a.name, question=q.id, dimension=a.dimension,
                            declared_at=a.declared_at, rationale=a.rationale)
        # Price the question's OWN pass bar as well as the standard grid, so a question
        # whose bar is 0.20 R is not reported against a 0.10 R clock it never declared.
        own = q.pass_bar.get("effect_threshold_r_per_trade")
        effects = tuple(sorted({0.10, 0.05, 0.02, 0.01} | ({own} if own else set()),
                               reverse=True))
        try:
            res = run_question(q.id, q.control, q.treatment, pop, sub,
                               pairing_class=q.pairing_class, effects=effects,
                               alpha=q.pass_bar.get("alpha", 0.05))
        except Exception as exc:
            payload["questions"][q.id] = {"error": f"{type(exc).__name__}: {exc}",
                                          "population_size": len(pop)}
            print(f"[question] {q.id}: FAILED {type(exc).__name__}: {exc}")
            continue

        d = res.as_dict()
        d["headline"] = q.headline
        d["population_label"] = q.population_label
        d["pass_bar"] = q.pass_bar
        d["notes"] = q.notes
        d["seconds"] = round(time.time() - t0, 1)

        # The verdict against the sleeve's OWN pre-declared bar.
        bar = q.pass_bar
        thr = bar.get("effect_threshold_r_per_trade")
        m = res.summary.mean
        ci = res.summary.ci95_block
        direction = bar.get("direction")
        if ci and thr is not None:
            if direction == "treatment_greater":
                verdict = "PASS" if ci[0] > thr else ("REJECT" if ci[1] < thr else "UNRESOLVED")
            else:
                verdict = ("PASS" if (abs(m) > thr and (ci[0] > 0 or ci[1] < 0))
                           else ("REJECT" if (ci[0] > -thr and ci[1] < thr) else "UNRESOLVED"))
        else:
            verdict = "UNRESOLVED"
        d["verdict_against_own_bar"] = verdict

        # Sequential monitoring, at the horizon the question's own pass bar implies.
        from .paired_stats import n_to_detect

        planned = int(min(1e7, max(1, round(n_to_detect(res.summary.sd, thr or 0.05,
                                                        alpha=bar.get("alpha", 0.05))))))
        mon = SequentialMonitor(q.id, planned_n=planned, alpha=bar.get("alpha", 0.05))
        d["sequential"] = {"planned_n_for_own_bar": planned,
                           "look": mon.look(res.summary, label="first look on sealed history"),
                           "boundary_schedule": {
                               f"t={t:g}": round(obf_boundary(t, bar.get("alpha", 0.05)), 4)
                               for t in (0.25, 0.5, 0.75, 1.0)}}

        # Aux arms (confound controls) are run as their own contrast against the control.
        for label, aux_arm in q.aux:
            try:
                ax = run_question(f"{q.id}::{label}", aux_arm, q.control, pop, sub,
                                  pairing_class=q.pairing_class)
                d.setdefault("aux", {})[label] = {
                    "contrast": f"{q.control.name} - {aux_arm.name}",
                    "n": ax.n_paired,
                    "mean": round(ax.summary.mean, 6),
                    "sd": round(ax.summary.sd, 6),
                    "ci95_block": list(ax.summary.ci95_block) if ax.summary.ci95_block else None,
                    "reading": aux_arm.rationale,
                }
                ledger.register(aux_arm.name, question=f"{q.id}::{label}",
                                dimension=aux_arm.dimension, declared_at=aux_arm.declared_at,
                                rationale=aux_arm.rationale, p_value=ax.summary.p_block,
                                reported=True)
            except Exception as exc:
                d.setdefault("aux", {})[label] = {"error": f"{type(exc).__name__}: {exc}"}

        ledger.register(q.treatment.name, question=q.id, dimension=q.treatment.dimension,
                        declared_at=q.treatment.declared_at, rationale=q.treatment.rationale,
                        p_value=res.summary.p_block, reported=True)

        d["causality"] = {
            "control": causal.rows.get(q.control.name),
            "treatment": causal.rows.get(q.treatment.name),
        }
        d["temporal_companions"] = _temporal_companions(q, res, pop, sub, ledger, causal)
        payload["questions"][q.id] = d
        print(f"[question] {q.id}: n={res.n_paired} mean={m:+.4f} sd={res.summary.sd:.4f} "
              f"disc={res.summary.discordance:.2%} verdict={verdict} ({d['seconds']}s)")

    # Q6 is BOOK_PAIRED and runs through a different estimator.
    spec = q_cluster_cap_spec()
    clusters = sleeve_cluster_map()
    from .arms import exit_arm, published_policy
    from .questions import BAND

    base = exit_arm("estate@live_contract", lambda it: published_policy(it), band=BAND,
                    dimension="admission", declared_at="2026-08-12", is_control=True,
                    rationale="every estate decision under its published contract")
    same = exit_arm("estate@live_contract_dup", lambda it: published_policy(it), band=BAND,
                    dimension="admission", declared_at="2026-08-12",
                    rationale="identical contract: the throttle, not the exit, is the treatment")
    from src.safety.armed_set import armed_sleeves

    # TWO populations, because the cap's price is a property of the BOOK it caps and Lane 4
    # priced it on the armed set alone.  Running only the estate would answer a question
    # nobody asked; running only the armed four would not test the instrument's reach.
    pops = {
        "full_estate_forward": (sub.forward(), "the full 29-sleeve estate, forward (2025+)"),
        "armed_four_forward": (sub.forward(sub.by_sleeve(*sorted(armed_sleeves()))),
                               "the ARMED four, forward (2025+)"),
        # Lane 4 §2.1 priced the cap on the THREE-sleeve book of the time. Reproducing its
        # +5.8 % trade-count effect on that exact set is the book layer's own control; the
        # armed-four number above is a different book and must not be read against it.
        "lane4_armed_three_forward": (
            sub.forward(sub.by_sleeve("crypto", "energy_agri", "sub_xvol_pullback")),
            "crypto + energy_agri + sub_xvol_pullback -- Lane 4 §2.1's exact population, "
            "which it measured at 4.637 -> 4.904 trades/month (+5.8 %) with L5 off"),
    }
    book_out: dict[str, Any] = dict(spec)
    for label, (pop, plabel) in pops.items():
        try:
            book = book_daily_difference(
                pop, base, same, sub,
                cap_control=cap_builder(per_sleeve_symbol_day=True, per_cluster_day=True,
                                        clusters=clusters),
                cap_treatment=cap_builder(per_sleeve_symbol_day=True, per_cluster_day=False,
                                          clusters=clusters))
            book["population_label"] = plabel
            book_out[label] = book
            dd = book["daily_difference"]
            print(f"[question] {spec['id']}/{label}: days={book['n_days']} "
                  f"accepted {book['accepted_control']}->{book['accepted_treatment']} "
                  f"mean_delta_R_per_day={dd['mean']:+.4f} ci={dd['ci95_block']}")
        except Exception as exc:
            book_out[label] = {"error": f"{type(exc).__name__}: {exc}"}
            print(f"[question] {spec['id']}/{label}: FAILED {type(exc).__name__}: {exc}")
    payload["questions"][spec["id"]] = book_out

    ledger.flush()
    payload["multiplicity"] = ledger.benjamini_hochberg()
    payload["causality"] = causal.as_dict()
    (out / "B8_CAUSALITY_LEDGER_V1.json").write_text(
        json.dumps(payload["causality"], indent=1, default=_json))
    payload["lane4_shadow_rate_per_month"] = LANE4_SHADOW_RATE_PER_MONTH
    (out / "B8_QUESTIONS_V1.json").write_text(json.dumps(payload, indent=1, default=_json))
    return payload


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--controls", action="store_true")
    ap.add_argument("--questions", action="store_true")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--archive", default=None)
    args = ap.parse_args(argv)
    if not (args.controls or args.questions):
        args.controls = args.questions = True

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    sub = (Substrate.load(archive=args.archive) if args.archive else Substrate.load())
    print(f"[substrate] {len(sub.intents)} decisions, {len(sub.series)} series")

    ok = True
    if args.controls:
        res = run_controls(sub, out)
        ok = bool(res.get("all_pass"))
        if not ok:
            print("[controls] FAILED — the harness does not reproduce known truth. "
                  "Questions are still run so the failure can be diagnosed, but NO number "
                  "below is publishable until C1-C6 are green.")
    if args.questions:
        run_questions(sub, out, MultiplicityLedger.load(out / "B8_MULTIPLICITY_LEDGER.jsonl"))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
