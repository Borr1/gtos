"""G2 — seed the B8 paired harness with the estate's open questions and run them on history.

B8 built and validated the harness (C1: 22,343 rows, 0 mismatches, max abs error 0.0) and
seeded eight questions. It was never deployed and no lane has run it since. This module adds
the questions the swarm's own forensic lanes generated, and runs them **on sealed history**,
where the answer costs zero calendar days.

THE DESIGN CHOICE THAT MAKES THESE WORTH RUNNING: EVERY ONE IS A TRANSFER TEST
------------------------------------------------------------------------------
F3 selected its levers on the **funnel candidate pool** (Feb/Apr/May 2026 train, Jun/Jul test,
~150 k modelled fills over 24 symbols and 5 months). The **sleeve estate** is a different
population: 22,343 real sleeve decisions, 29 sleeves, 2000-2026, its own generators, its own
exit contracts. A lever that survives on both surfaces is a property of markets; one that
survives on the funnel and dies on the estate is a property of the funnel's candidate
density. Neither had been measured.

The pass bars, the pairing, the day-clustered intervals, the sequential monitor and the
multiplicity ledger are all B8's, unmodified — so a G2 answer and a B8 answer can sit on the
same page. Every arm registered here is appended to the SAME ledger and the family never
shrinks: these questions cost multiplicity, and the receipt says so.

NO WRITES OUTSIDE THIS DIRECTORY. No src/ edit, no config byte, no broker, no VPS, no git.
"""

from __future__ import annotations

import datetime as dt
import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[9]
B8 = REPO / ("docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/"
             "outcome_authority/swarm2/breakthrough")
for p in (str(REPO), str(B8)):
    if p not in sys.path:
        sys.path.insert(0, p)

from b8_paired_shadow.arms import (  # noqa: E402
    Arm, ArmUnavailable, PairingClass, exit_arm, published_policy, selection_arm,
)
from b8_paired_shadow.causality import AsOf, InfoInput, InformationSet  # noqa: E402
from b8_paired_shadow.evaluate import run_question  # noqa: E402
from b8_paired_shadow.paired_stats import MultiplicityLedger  # noqa: E402
from b8_paired_shadow.questions import Question  # noqa: E402
from b8_paired_shadow.substrate import Intent, Substrate  # noqa: E402
from src.utils.broker_clock import resolve_rule, utc_to_broker_naive  # noqa: E402

OUT = Path(__file__).resolve().parent / "receipts"
BAND = "mid"
DECLARED = "2026-08-12 lane G2, replay lane"
SERVER = "FTMO-Server3"
USD_PER_R = 500.0

#: F3's train-selected set (`F3_LEVERS.json -> L2_drop_worst_entry_broker_hours_trainselected`),
#: chosen on Feb/Apr/May 2026 funnel fills and priced on Jun/Jul at +0.0210 R [+0.0110, +0.0302]
#: over 14.3 % of the book. Carried here VERBATIM -- re-selecting the hour set on the estate
#: would be a second look and would make the transfer test circular.
F3_WORST_BROKER_HOURS = (0, 8, 21, 22, 23)

#: B10 measured the broker-midnight rollover as an FX-only spread event: at broker hour 0 the
#: JPY crosses quote 7.5x-18.6x their own reference median, crypto is exempt (BTCUSD 1.01x)
#: and every cash CFD is shut. This isolates that single hour from F3's five.
ROLLOVER_BROKER_HOUR = 0


def _broker_hour(it: Intent, sub: Substrate) -> int:
    rule = resolve_rule(SERVER)
    return utc_to_broker_naive(sub.entry_instant(it), rule).hour


def hour_exclusion_predicate(hours: tuple[int, ...]) -> Callable[[Intent, Substrate],
                                                                tuple[bool, str]]:
    def _pred(it: Intent, sub: Substrate) -> tuple[bool, str]:
        try:
            h = _broker_hour(it, sub)
        except Exception as exc:
            raise ArmUnavailable(f"broker clock unresolvable: {exc}") from None
        if h in hours:
            return False, f"entry_broker_hour={h} in {list(hours)}"
        return True, ""
    return _pred


HOUR_INFO = InformationSet(
    inputs=(
        InfoInput("intent.entry_utc -> broker wall hour", AsOf.DECISION_INSTANT,
                  note="src.utils.broker_clock.utc_to_broker_naive; fails closed on an "
                       "unregistered server"),
        InfoInput("F3's hour set", AsOf.CONSTANT,
                  note="selected on the FUNNEL pool (Feb/Apr/May 2026 train). Carried "
                       "verbatim so the estate read is a transfer test, not a second fit."),
    ),
    rationale="the entry instant is known at the decision; the hour set is a frozen "
              "constant selected on a disjoint surface.")


def _estate_base(suffix: str) -> Arm:
    return exit_arm(
        f"estate@live_contract{suffix}", lambda it: published_policy(it), band=BAND,
        dimension="admission", is_control=True, declared_at=DECLARED,
        rationale="every estate decision under its published contract, no gate")


def q_f3_hour_exclusion() -> Question:
    base = _estate_base("_g2h")
    treat = selection_arm(
        base, "estate@drop_f3_worst_broker_hours",
        hour_exclusion_predicate(F3_WORST_BROKER_HOURS),
        dimension="admission", declared_at=DECLARED,
        rationale=f"refuse decisions entering at broker hours {list(F3_WORST_BROKER_HOURS)} "
                  f"-- F3's train-selected lever, carried verbatim onto the sleeve estate",
        information_set=HOUR_INFO)
    return Question(
        id="G2Q1_f3_hour_exclusion_on_estate",
        headline="Does F3's train-selected worst-hour exclusion transfer from the funnel "
                 "candidate pool to the 29-sleeve estate?",
        pairing_class=PairingClass.SELECTION_PAIRED, control=base, treatment=treat,
        population=lambda s: s.intents,
        population_label="the full 29-sleeve estate, all history (2000-2026)",
        pass_bar={
            "direction": "treatment_greater",
            "effect_threshold_r_per_trade": 0.02,
            "alpha": 0.05,
            "decision_if_pass": "the hour lever is a property of markets, not of the "
                                "funnel's candidate density; it becomes a generation-side "
                                "proposal on the sleeve surface with F3's funnel receipt "
                                "alongside, and `run_book.py --entry-hour` is the mechanism",
            "decision_if_fail": "the lever is funnel-local. F3's +0.0210 R stands for the "
                                "funnel and does NOT license an estate-side hour filter.",
        },
        notes="TRANSFER TEST. F3 measured +0.0210 R/trade [+0.0110, +0.0302] on Jun/Jul 2026 "
              "funnel fills, dropping 14.3 % of the book. Different population, same "
              "treatment, frozen hour set.")


def q_rollover_hour_only() -> Question:
    base = _estate_base("_g2r")
    treat = selection_arm(
        base, "estate@drop_rollover_hour",
        hour_exclusion_predicate((ROLLOVER_BROKER_HOUR,)),
        dimension="admission", declared_at=DECLARED,
        rationale="refuse decisions entering in the broker-midnight rollover hour only -- "
                  "B10 measured JPY crosses at 7.5x-18.6x their reference median there",
        information_set=HOUR_INFO)
    return Question(
        id="G2Q2_rollover_hour_only",
        headline="Is the broker-midnight rollover hour, on its own, worth refusing on the "
                 "sleeve estate?",
        pairing_class=PairingClass.SELECTION_PAIRED, control=base, treatment=treat,
        population=lambda s: s.intents,
        population_label="the full 29-sleeve estate, all history (2000-2026)",
        pass_bar={
            "direction": "treatment_greater",
            "effect_threshold_r_per_trade": 0.02,
            "alpha": 0.05,
            "decision_if_pass": "B10's rollover finding has an estate-side price and the "
                                "single-hour filter is the cheapest form of F3's lever",
            "decision_if_fail": "the rollover spread spike does not cost the estate enough "
                                "to pay for the decisions it would refuse -- which localises "
                                "F3's five-hour result to the other four hours",
        },
        notes="MECHANISM ISOLATION of G2Q1. B10: crypto exempt (BTCUSD 1.01x), every cash "
              "CFD shut at 21:00 UTC, exposure lands on the JPY crosses.")


def q_symbol_hour_spread(sleeves: tuple[str, ...] | None = None) -> Question:
    """The B10 hour-surface repair, as a paired ARM rather than as a restatement.

    G2-M1 measured this in the price domain over the whole estate. This asks the narrower
    question the harness is built for: does the repair change what the estate EARNS? It is
    expected to be near-inert by construction (`exits.replay:317` anchors every level on the
    entry price, so a barrier exit is +/-kR whatever spread is charged) and the question is
    registered anyway, because "near-inert by construction" is a claim that should carry a
    measured discordance rather than an argument.
    """
    from g2_replay.symbol_hour_arm import symbol_hour_exit_arm

    base = _estate_base("_g2s")
    treat = symbol_hour_exit_arm("estate@symbol_hour_spread", declared_at=DECLARED)
    return Question(
        id="G2Q3_symbol_hour_spread_repair",
        headline="Does substituting by_symbol_hour_of_week for by_class_hour_of_week "
                 "(spread_model.py:396) change what the sleeve estate earns?",
        pairing_class=PairingClass.TRADE_PAIRED, control=base, treatment=treat,
        population=(lambda s: s.intents) if sleeves is None
        else (lambda s: s.by_sleeve(*sleeves)),
        population_label="the full 29-sleeve estate, all history (2000-2026)",
        pass_bar={
            "direction": "two_sided",
            "effect_threshold_r_per_trade": 0.02,
            "alpha": 0.05,
            "decision_if_pass": "the hour defect reaches the R label and every published "
                                "sleeve figure needs restating",
            "decision_if_fail": "the defect is real in the price domain and does NOT reach "
                                "the barrier-labelled R; it must be priced through cost "
                                "accounting (the funnel, the cost gate, net expectancy) and "
                                "not through the sleeve estate's R",
        },
        notes="B10 §0: spread_model.py:396 reads only the class table; the symbol table "
              "exists for 36 FTMO symbols, is read by no code, and agrees with 300,538,915 "
              "ticks to a median 0.64 %.")


def all_g2_questions() -> list[Question]:
    return [q_f3_hour_exclusion(), q_rollover_hour_only(), q_symbol_hour_spread()]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sub = Substrate.load(verbose=True)
    # THE FAMILY INCLUDES B8's ARMS. Loading B8's ledger first puts every arm that lane
    # declared into the denominator, so G2's q-values are corrected against the looks the
    # estate has actually taken, not only against G2's own three. Written to a G2 path:
    # B8's receipt is another lane's and is not edited.
    b8_ledger = B8 / "b8_paired_shadow/receipts/B8_MULTIPLICITY_LEDGER.jsonl"
    ledger = MultiplicityLedger.load(b8_ledger, alpha=0.10)
    inherited = len(ledger.rows)
    ledger.path = OUT / "G2_MULTIPLICITY_LEDGER.jsonl"
    out: dict[str, Any] = {
        "lane": "G2 replay lane",
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
        "harness": "b8_paired_shadow (unmodified); questions seeded by G2",
        "usd_per_r": USD_PER_R,
        "questions": {},
    }
    for q in all_g2_questions():
        t0 = time.time()
        pop = q.population(sub)
        try:
            res = run_question(q.id, q.control, q.treatment, pop, sub,
                               pairing_class=q.pairing_class)
        except Exception as exc:
            out["questions"][q.id] = {"error": f"{type(exc).__name__}: {exc}"}
            print(f"[{q.id}] ERROR {exc}")
            continue
        d = res.as_dict() if hasattr(res, "as_dict") else json.loads(
            json.dumps(res, default=lambda o: getattr(o, "__dict__", str(o))))
        ps = d.get("paired_summary", {})
        mean = ps.get("mean")
        n = d.get("n_paired")
        bar = q.pass_bar
        thr = bar["effect_threshold_r_per_trade"]
        ci = ps.get("ci95_block") or [None, None]
        if ci[0] is None:
            verdict = "UNRESOLVED"
        elif bar["direction"] == "treatment_greater":
            verdict = "PASS" if ci[0] > thr else ("FAIL_BELOW_BAR" if ci[1] < thr
                                                  else "UNRESOLVED")
        else:
            verdict = "PASS" if (ci[0] > thr or ci[1] < -thr) else (
                "FAIL_BELOW_BAR" if (ci[0] > -thr and ci[1] < thr) else "UNRESOLVED")
        d["headline"] = q.headline
        d["population_label"] = q.population_label
        d["pass_bar"] = bar
        d["notes"] = q.notes
        d["verdict_against_own_bar"] = verdict
        d["usd"] = {
            "usd_per_r": USD_PER_R,
            "per_trade": round((mean or 0.0) * USD_PER_R, 2),
            "over_the_measured_population": round((mean or 0.0) * (n or 0) * USD_PER_R, 2),
        }
        d["seconds"] = round(time.time() - t0, 1)
        for arm in (q.control, q.treatment):
            ledger.register(arm.name, question=q.id, dimension=arm.dimension,
                            declared_at=arm.declared_at, rationale=arm.rationale,
                            p_value=(float(ps["p_block"])
                                     if arm is q.treatment and ps.get("p_block") is not None
                                     else None),
                            reported=arm is q.treatment)
        out["questions"][q.id] = d
        print(f"[{q.id}] n={n} mean={mean} ci={ci} verdict={verdict} ({d['seconds']}s)")

    ledger.flush()
    bh = ledger.benjamini_hochberg()
    bh["arms_inherited_from_b8"] = inherited
    out["multiplicity"] = bh
    (OUT / "G2_QUESTIONS_V1.json").write_text(json.dumps(out, indent=1, default=str))
    print(f"-> {OUT / 'G2_QUESTIONS_V1.json'}")


if __name__ == "__main__":
    main()
