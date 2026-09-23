"""The estate's open questions, seeded as paired treatments.

Every question here is one the estate is currently waiting on either a 16.5 h sealed replay
or a multi-year live record to answer.  Each declares, before it is run:

* the **arms** -- what is varied and what is held;
* the **pairing class**, which fixes what n means;
* the **pass bar** -- the effect size and direction that would change a decision, and the
  alpha it must clear;
* the **population**, named rather than chosen after the look.

The pass bars are written as *decision thresholds*, not as predictions.  A question whose
measured effect is inside its own bar is answered NO, and that is a result.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Sequence

from .arms import (
    COST_BAND_INFO,
    Arm,
    PairingClass,
    ex_ante_cost_predicate,
    exit_arm,
    partial_be_policy,
    published_policy,
    run_on_grid,
    run_on_own_grid,
    selection_arm,
    spread_geometry_predicate,
    target_r_policy,
)
from .causality import AsOf, InfoInput, InformationSet
from .substrate import TF_M15, Intent, Substrate

#: The entry-hour treatment reads a CLOCK RULE and nothing else -- `broker_clock.resolve_rule`
#: is a registered, fail-closed calendar, not a fitted quantity.
ENTRY_HOUR_INFO = InformationSet(
    inputs=(
        InfoInput("broker_clock.resolve_rule(server)", AsOf.CONSTANT,
                  note="US DST calendar, measured over 81 weekly boundaries per broker; "
                       "fails closed on an unregistered server"),
        InfoInput("target broker hour", AsOf.CONSTANT),
        InfoInput("intent.stop_dist", AsOf.DECISION_INSTANT),
        InfoInput("spread_model(symbol, fill_instant, band)", AsOf.FITTED_ON_FULL_HISTORY),
    ),
    rationale="deferring an entry to a named wall-clock hour needs a calendar, not a "
              "forecast; the only fitted input is the cost model shared by every arm.")

DECLARED = "2026-08-12"

#: The estate's economic convention: spread-only at the mid band (`r_new_mid`).  Treatment
#: DIFFERENCES are what this harness publishes, so a common residual cost cancels exactly.
BAND = "mid"


@dataclass
class Question:
    id: str
    headline: str
    pairing_class: PairingClass
    control: Arm
    treatment: Arm
    population: Callable[[Substrate], Sequence[Intent]]
    population_label: str
    pass_bar: dict[str, Any]
    #: Optional extra arms evaluated alongside, e.g. a confound control.
    aux: list[tuple[str, Arm]] = field(default_factory=list)
    notes: str = ""


# ---------------------------------------------------------------- Q1 / Q2: frontier exits ---
def _frontier(sleeve: str, live_r: float, frontier_r: float, evidence: str) -> tuple[Arm, Arm]:
    ctrl = exit_arm(
        f"{sleeve}@live_{live_r:g}R",
        lambda it: published_policy(it),
        band=BAND, dimension="exit_contract", is_control=True, declared_at=DECLARED,
        rationale=f"the contract the live book runs today for {sleeve}")
    treat = exit_arm(
        f"{sleeve}@target_{frontier_r:g}R",
        lambda it, k=frontier_r: target_r_policy(it, k),
        band=BAND, dimension="exit_contract", declared_at=DECLARED,
        rationale=f"--frontier-exits {sleeve} ({evidence})")
    return ctrl, treat


def q_frontier_xvol() -> Question:
    ctrl, treat = _frontier("sub_xvol_pullback", 3.0, 4.0,
                            "AK_EXIT_FRONTIER_V2.json / FRONTIER_EXIT_OVERRIDES")
    return Question(
        id="Q1_frontier_sub_xvol_pullback_target_4R",
        headline="Does --frontier-exits sub_xvol_pullback (target_4R) beat the live 3R "
                 "contract on an ARMED sleeve?",
        pairing_class=PairingClass.TRADE_PAIRED, control=ctrl, treatment=treat,
        population=lambda s: s.by_sleeve("sub_xvol_pullback"),
        population_label="every sub_xvol_pullback decision in the estate store",
        pass_bar={
            "direction": "treatment_greater",
            "effect_threshold_r_per_trade": 0.10,
            "alpha": 0.05,
            "decision_if_pass": "put the 4R contract in front of the owner with the "
                                "sequential receipt; it is an ARMED sleeve so arming it is "
                                "a live risk change and remains Borhen's call",
            "decision_if_fail": "leave --frontier-exits off for this sleeve; AU already "
                                "REJECTED it at all four bands (p 0.0080 vs a 0.002083 bar) "
                                "and AS handoff 3 is 'do not propose it'",
        },
        notes="AU measured this cell REJECT at the ratified rule while AK measured it a "
              "winner at a standard that does not govern the estate. The paired harness "
              "settles the magnitude; the admission bar is the estate's, not this lane's.")


def q_frontier_btc() -> Question:
    ctrl, treat = _frontier("mx_btcusd_d1_donchian_20_breakout", 2.0, 5.0,
                            "phase11/MX_BTCUSD_CHALLENGE_DOSSIER.md")
    return Question(
        id="Q2_frontier_mx_btcusd_target_5R",
        headline="Does target_5R beat the 2R spec on mx_btcusd -- the cell whose ADMIT "
                 "flipped to REJECT under A1b's corrected null?",
        pairing_class=PairingClass.TRADE_PAIRED, control=ctrl, treatment=treat,
        population=lambda s: s.by_sleeve("mx_btcusd_d1_donchian_20_breakout"),
        population_label="all 318 mx_btcusd decisions",
        pass_bar={
            "direction": "treatment_greater",
            "effect_threshold_r_per_trade": 0.20,
            "alpha": 0.05,
            "decision_if_pass": "the exit-contract magnitude is real; the ADMISSION is "
                                "still governed by the corrected permutation null (D-2), "
                                "which this does not re-open",
            "decision_if_fail": "the 5R contract adds nothing and the sleeve stays disarmed",
        },
        notes="DISARMED on FTMO 2026-08-05 (host 2fa77722d). This question is about the "
              "exit contract's magnitude, not about re-arming.")


# ---------------------------------------------------------------- Q3: the scale-out ---------
def q_energy_scaleout() -> Question:
    ctrl = exit_arm(
        "energy_agri@plain_4R",
        lambda it: published_policy(it),
        band=BAND, dimension="exit_contract", is_control=True, declared_at=DECLARED,
        rationale="the plain stop+4R+maxbars contract every published energy_agri number "
                  "is measured under")
    treat = exit_arm(
        "energy_agri@partial_be_runner_2R",
        lambda it: partial_be_policy(it, 2.0, frac=0.5, be=True),
        band=BAND, dimension="exit_contract", declared_at=DECLARED,
        rationale="the LIVE contract (execution_packets.py:93-94): 50 % off at 2R, stop to BE")
    return Question(
        id="Q3_energy_agri_scale_out",
        headline="What does energy_agri's live partial_be_runner scale-out cost against the "
                 "plain exit its published economics describe?",
        pairing_class=PairingClass.TRADE_PAIRED, control=ctrl, treatment=treat,
        population=lambda s: s.by_sleeve("energy_agri"),
        population_label="all 67 energy_agri decisions on its live ON_SURFACE",
        pass_bar={
            "direction": "two_sided",
            "effect_threshold_r_per_trade": 0.15,
            "alpha": 0.05,
            "decision_if_pass": "an ARMED sleeve's live exit contract differs materially "
                                "from its published economics; the restatement goes to the "
                                "owner with the sign",
            "decision_if_fail": "the scale-out is economically neutral and the published "
                                "figures describe the live contract",
        },
        notes="INDEPENDENT CONFIRMATION of three prior instruments that disagree in "
              "magnitude: AD Section 6.2 (-0.308 R/day, n=67), AU (+0.2302 R/day restamp "
              "error at every band) and swarm2 Lane 8 (-0.28829 R/trade paired, t -2.385, "
              "n=72 on an EXPANDED surface). Lane 8's arms are reproduced here on the "
              "estate's own 67-decision population, so a sign agreement is a fourth "
              "instrument and a disagreement is a finding.")


# ---------------------------------------------------------------- Q4: the spread floor ------
def q_spread_floor(sleeves: Sequence[str] = ("sub_mid_dn_revert", "sub_xvol_pullback",
                                             "crypto", "energy_agri"),
                   limit: float = 0.10) -> Question:
    base = exit_arm(
        "armed4@live_contract",
        lambda it: published_policy(it),
        band=BAND, dimension="admission", is_control=True, declared_at=DECLARED,
        rationale="the armed four under their published contract, no generation-side floor")
    treat = selection_arm(
        base, f"armed4@spread_geometry_floor_{limit:g}",
        spread_geometry_predicate(limit, band=BAND),
        dimension="admission", declared_at=DECLARED,
        rationale=f"run_book.py --spread-geometry-floor at spread_r <= {limit} "
                  f"(SPREAD_GEOMETRY_FLOOR_DEFAULT_LIMIT)")
    want = tuple(sleeves)
    return Question(
        id="Q4_spread_geometry_floor_armed_four",
        headline="What does the wave-13 generation-side spread floor do to the armed four?",
        pairing_class=PairingClass.SELECTION_PAIRED, control=base, treatment=treat,
        population=lambda s, w=want: s.by_sleeve(*w),
        population_label=f"every decision of {', '.join(want)}",
        pass_bar={
            "direction": "treatment_greater",
            "effect_threshold_r_per_trade": 0.05,
            "alpha": 0.05,
            "decision_if_pass": "the floor is a REPAIR on the armed set and goes to the "
                                "owner as a launcher-flag change (no config byte, no token "
                                "re-mint)",
            "decision_if_fail": "the floor is a no-op on this set at this limit; AY's "
                                "measured +0.426/+0.264 R/day repairs do not reproduce",
        },
        notes="SELECTION class. Most decisions clear the floor and contribute an exact 0; "
              "the whole signal is in the discordant set and the harness powers off it.")


# ---------------------------------------------------------------- Q5: the entry hour --------
def _grid_policy(it: Intent, timeframe: int):
    """The published contract re-expressed on `timeframe`, holding the WALL-CLOCK horizon.

    80 native bars is the research horizon every published estate number carries.  Moving to
    a finer grid without converting the ceiling would shorten the trade, which is a second
    treatment and would contaminate the entry-timing answer.
    """
    from src.components.ultimate_book.execution_packets import M15_BARS_PER
    from .substrate import MAXBARS, TF_NAME

    ratio = M15_BARS_PER[TF_NAME[it.timeframe]] // M15_BARS_PER[TF_NAME[timeframe]]
    pol = published_policy(it, maxbars=MAXBARS * max(ratio, 1))
    return pol


def q_entry_hour(sleeve: str = "sub_mid_dn_revert", hour: int = 1) -> Question:
    """Three arms, because two would confound entry timing with grid resolution.

    A  control      -- entry at the decision-bar close, replayed on the M15 grid
    B  treatment    -- entry deferred to broker hour `hour`, replayed on the M15 grid
    (aux) native    -- entry at the decision-bar close on the sleeve's OWN grid

    ``B - A`` is the entry-timing effect at constant grid: the answer.
    ``A - native``  is the grid-resolution effect at constant entry: the confound, priced.
    """
    ctrl = Arm(
        name=f"{sleeve}@entry_decision_close_m15grid",
        dimension="entry_timing", declared_at=DECLARED,
        rationale="the entry the book takes today (decision-bar close), replayed on M15 so "
                  "the deferred arm's finer grid is not charged to the treatment",
        information_set=ENTRY_HOUR_INFO, is_control=True,
        fn=lambda it, sub: run_on_grid(it, sub, TF_M15, _grid_policy, BAND))
    treat = Arm(
        name=f"{sleeve}@entry_broker_hour_{hour}",
        dimension="entry_timing", declared_at=DECLARED,
        rationale=f"run_book.py --entry-hour {sleeve}:{hour}, the RATIFIED convention of "
                  f"phase9/OWNER_DECISION_ENTRY_HOUR.md",
        information_set=ENTRY_HOUR_INFO,
        fn=lambda it, sub, h=hour: run_on_grid(it, sub, TF_M15, _grid_policy, BAND,
                                               defer_to_broker_hour=h))
    native = Arm(
        name=f"{sleeve}@entry_decision_close_native",
        dimension="grid_confound", declared_at=DECLARED,
        rationale="same entry instant, the sleeve's own decision grid -- isolates the "
                  "grid-resolution effect so it cannot be read as entry timing",
        information_set=COST_BAND_INFO,
        fn=lambda it, sub: run_on_own_grid(it, sub, published_policy(it), BAND))
    return Question(
        id=f"Q5_entry_hour_{sleeve}_h{hour}",
        headline=f"Is the ratified hour-{hour} entry convention worth anything on {sleeve}?",
        pairing_class=PairingClass.ENTRY_PAIRED, control=ctrl, treatment=treat,
        population=lambda s, sl=sleeve: s.by_sleeve(sl),
        population_label=f"every {sleeve} decision with M15 archive coverage",
        pass_bar={
            "direction": "treatment_greater",
            "effect_threshold_r_per_trade": 0.05,
            "alpha": 0.05,
            "decision_if_pass": "--entry-hour goes to the owner for this sleeve; it is a "
                                "launcher flag, no config byte and no token re-mint",
            "decision_if_fail": "ratified but not worth arming on this sleeve",
        },
        aux=[("grid_confound_control", native)],
        notes="M15 archive coverage starts 2023-12-31, so this question is answerable only "
              "on the forward window. That is a coverage bound, reported, not a filter "
              "chosen after the look.")


# ---------------------------------------------------------------- Q6: the cluster cap -------
def sleeve_cluster_map() -> dict[str, str]:
    """sleeve -> cluster, read from the registry the book itself resolves."""
    from src.components.ultimate_book.sleeves import registry as REG

    out: dict[str, str] = {}
    for name in ("BUILT", "CANDIDATE_BUILT", "MARKET_EXPANSION_BUILT"):
        d = getattr(REG, name, None)
        if isinstance(d, dict):
            for tag, spec in d.items():
                out[tag] = getattr(spec, "cluster", "unknown")
    return out


def cap_builder(*, per_sleeve_symbol_day: bool, per_cluster_day: bool,
                clusters: dict[str, str], cluster_exempt: frozenset[str] = frozenset()):
    """The L4 / L5 admission ledger, as the book actually applies it.

    L4 -- `book_owner.py:2055-2056` -> `placement_ledger.already_placed_today(sleeve, symbol,
    decision_day)`: one unit per (sleeve, symbol, decision_day), any bar.

    L5 -- `book_owner.py:2064-2066` -> `placement_ledger.cluster_placed_today_other_bar
    (cluster, decision_day, decision_bar_iso)`: blocks a later-bar same-cluster re-fire and
    **explicitly allows every member of the SAME bar's unit** (`:181`,
    `any(b != decision_bar_iso)`), because admission's correlated unit places one order per
    member on one bar and those members ARE the unit.

    THAT SAME-BAR EXEMPTION IS EASY TO MISS AND IT IS WORTH 14 DECISIONS ON THE ARMED THREE
    ALONE.  An earlier draft here blocked every same-day same-cluster repeat and produced 73
    accepted decisions where the book produces 87 -- a 16 % understatement of the capped book,
    entirely inside the cap whose price the question is asking for.

    `cluster_exempt` mirrors `self._cluster_cap_exempt` ("jpy exempt for the live trial").
    """

    def _accept(order):
        seen_l4: set[tuple] = set()
        cluster_bars: dict[tuple, set[str]] = {}
        out: set[tuple] = set()
        for it in order:
            cl = clusters.get(it.sleeve, it.sleeve)
            if per_sleeve_symbol_day and (it.sleeve, it.symbol, it.decision_day) in seen_l4:
                continue
            if per_cluster_day and cl and cl not in cluster_exempt:
                bars = cluster_bars.get((cl, it.decision_day))
                # Blocked only by a placement on a DIFFERENT bar of the same day.
                if bars and any(b != it.decision_bar_iso for b in bars):
                    continue
            if per_sleeve_symbol_day:
                seen_l4.add((it.sleeve, it.symbol, it.decision_day))
            if per_cluster_day:
                cluster_bars.setdefault((cl, it.decision_day), set()).add(it.decision_bar_iso)
            out.add(it.key)
        return out

    return _accept


def q_cluster_cap_spec() -> dict[str, Any]:
    """The cluster-cap question is BOOK_PAIRED and runs through
    :func:`evaluate.book_daily_difference`, not :func:`evaluate.run_question`."""
    return {
        "id": "Q6_cluster_cap_L5",
        "headline": "What does the one-unit-per-cluster-per-day cap cost the estate, "
                    "measured as a paired daily difference rather than as two books?",
        "pairing_class": PairingClass.BOOK_PAIRED.value,
        "control": "cap ON (L4+L5), the certified risk envelope for the 2.0 % dial",
        "treatment": "cap OFF (L4 only), the rung-2 relaxation",
        "pass_bar": {
            "direction": "two_sided",
            "effect_threshold_r_per_day": 0.05,
            "alpha": 0.05,
            "decision_if_pass": "the cap has a measurable price; Lane 4 rung 2 already "
                                "REJECTS it on p_fail_daily 0.0000 -> 0.0264, so a positive "
                                "R price is a trade the owner prices, not a recommendation",
            "decision_if_fail": "the cap is economically free and the rung-2 debate is over",
        },
        "notes": "The risk side is NOT measurable here: this harness has no equity path and "
                 "no governor. It prices the R and says nothing about p_fail_daily.",
    }


# ---------------------------------------------------------------- Q7: the ex-ante cost gate -
def q_ex_ante_cost_gate(limit: float = 0.20, lag_days: int = 0,
                        suffix: str = "") -> Question:
    """The funnel's own eligibility gate, asked of the SLEEVE surface for the first time.

    A sibling lane pre-registered this as a paired contrast and measured **+0.04786 R/day,
    t 3.50, P(effect <= 0) 0.0003, resolving in 36 days at 80 % power against 481 days for
    the same question asked absolutely.**  It is the estate's cheapest causally clean open
    question, which is exactly the shape this harness exists to answer, so it is seeded here
    on an independent surface: their instrument is the funnel, this one is the 29-sleeve
    estate.  Agreement across the two is a real corroboration; disagreement localises to the
    surface, which is a result either way.
    """
    base = exit_arm(
        f"estate@live_contract{suffix}", lambda it: published_policy(it), band=BAND,
        dimension="admission", is_control=True, declared_at=DECLARED,
        rationale="every estate decision under its published contract, no cost gate")
    treat = selection_arm(
        base, f"estate@ex_ante_cost_gate_{limit:g}{suffix}",
        ex_ante_cost_predicate(limit, band=BAND, lag_days=lag_days),
        dimension="admission", declared_at=DECLARED,
        rationale=f"refuse any decision whose modelled pre-trade cost_r exceeds {limit} "
                  f"(candidate_funnel_analysis.py:52's own constant), "
                  f"{'lagged ' + str(lag_days) + 'd' if lag_days else 'at the decision instant'}",
        information_set=InformationSet(
            inputs=(
                InfoInput("spread_model(symbol, entry_instant, band)",
                          AsOf.FITTED_ON_FULL_HISTORY,
                          note="AG's era/hour spread model, evaluated at the decision"),
                InfoInput("EXPECTED_SLIPPAGE_R = 0.02", AsOf.CONSTANT,
                          note="RECON_SLIPPAGE_ADJUDICATION_V1: correct within 4 %"),
                InfoInput("intent.stop_dist", AsOf.DECISION_INSTANT),
            ),
            rationale="an EX-ANTE gate by construction: every input is knowable before the "
                      "trade is placed. No day-level aggregate of any kind."))
    return Question(
        id=f"Q7_ex_ante_cost_gate_{limit:g}{suffix}",
        headline=f"Does refusing decisions whose modelled cost_r exceeds {limit} improve the "
                 f"estate, measured as a paired contrast?",
        pairing_class=PairingClass.SELECTION_PAIRED, control=base, treatment=treat,
        population=lambda s: s.forward(),
        population_label="the full 29-sleeve estate, forward window (2025+)",
        pass_bar={
            "direction": "treatment_greater",
            "effect_threshold_r_per_trade": 0.02,
            "alpha": 0.05,
            "decision_if_pass": "the ex-ante cost gate is a REPAIR on the sleeve surface as "
                                "well as the funnel; it becomes a generation-side proposal "
                                "with the sibling lane's funnel measurement alongside",
            "decision_if_fail": "the gate's funnel value does not transfer to the sleeve "
                                "surface, which localises it to candidate density rather "
                                "than to cost",
        },
        notes="SIBLING CORROBORATION: measured on the funnel at +0.04786 R/day, t 3.50, "
              "P(<=0) 0.0003, 36 days to answer against 481 unpaired. This is the same "
              "treatment on a different surface.")


def all_questions() -> list[Question]:
    return [q_frontier_xvol(), q_frontier_btc(), q_energy_scaleout(), q_spread_floor(),
            q_entry_hour(), q_ex_ante_cost_gate()]
