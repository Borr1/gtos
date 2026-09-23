"""Three admission standards, for Borhen to choose between.

This is a proposal, not a decision. Sleeve composition and the admission standard are the
owner's, the same class as the risk dial (`WAVE_5_WORKING_AGREEMENT.md` section 1). What a
session can usefully do is make the choice concrete: three internally coherent standards,
the trade-off each one buys, and — run through `receipts/w_mx_pilot.py` — exactly which
sleeves each one admits and rejects.

WHAT ALL THREE SHARE, AND WHY THOSE ARE NOT OPTIONS
----------------------------------------------------
Four properties are constant across every option because relaxing any of them would stop
the gate being a gate rather than making it more permissive:

  * **Out-of-sample only.** No in-sample statistic enters any verdict.
  * **Broker-true cost, or refusal.** `src.costs.cost_r` prices it or the trade is
    unpriced. Never a substituted number (F38).
  * **A day-blocked null.** Treating trades as iid overstated a delivered error budget by
    2.1x-7.7x on this programme's own data (B279).
  * **A fidelity floor at 0.50.** It admits the per-bar class and refuses the first-of-day
    class, which is the split K's evidence supports and no finer. Gate-spec v2 additionally
    requires an independent replay or live-record reference; same-lineage replay is accepted
    only by an explicitly sealed replay-consistency policy. Precision is disclosed, with no
    floor in these three historical option proposals.

WHAT ACTUALLY VARIES
--------------------
Three dials, and they are not independent knobs so much as one question asked three ways:
*how much of the estate are you willing to look at, and how wrong are you willing to be
about what you admit?*

  A STRICT      Bonferroni FWER at 5%. Controls the chance of admitting ANY bad sleeve.
                Refuses any sleeve broker truth cannot fully price. Wants 4 folds and 60%
                of them positive. Use when the next thing that happens is real money on a
                funded account and a single bad admission is expensive.

  B BALANCED    Benjamini-Hochberg FDR at 10%. Controls the EXPECTED FRACTION of admitted
                sleeves that are junk. Evaluates partially-priceable sleeves on their
                priceable subset, stamped. Wants 3 folds and 50% positive. Use when the
                output is a candidate book that will be sized small and watched — a book
                can carry one bad sleeve in ten; it cannot carry ten in ten.

  C EXPLORATORY BH FDR at 20%, thinner samples accepted. This is a RESEARCH TRIAGE
                standard and is labelled as such: its output is "worth generating more data
                on", never "worth arming". Use to decide where the next data capture goes.

WHY BH RATHER THAN BONFERRONI AS THE MIDDLE DEFAULT
----------------------------------------------------
Bonferroni at 21 hypotheses divides alpha by 21. On a family this size, with the sample
depths the archive actually supports, it approaches "admit nothing" — and a standard that
structurally cannot admit is not a standard, it is a decision already taken. BH controls
the quantity a book owner actually cares about. Both are offered because that argument is
contestable and the choice is not the author's to make.

THE NUMBER NONE OF THESE FIX
-----------------------------
`n_trials` for the DSR deflation. No trial-budget ledger exists in this repo — verified
2026-07-29 — so the true size of the search behind the market-expansion family is
unrecorded. Every option carries the same floor (128, from
`validation_integrity/trial_budget_ledger.DSR_TRIAL_FLOOR`) and every gate result publishes
a sweep so the reader can see where the DSR would flip. Recovering the real number is a
research task, not a threshold choice.
"""

from __future__ import annotations

from src.research_infra.walkforward.spec import GateSpec

__all__ = ["OPTIONS", "OPTION_NOTES", "STRICT", "BALANCED", "EXPLORATORY"]

_AUTHORED = "2026-07-29T00:00:00+00:00"

STRICT = GateSpec(
    spec_id="wf_gate_option_A_strict",
    authored_utc=_AUTHORED,
    author_note="Option A (Strict) — FWER control, no partial universes.",
    account="FTMO",
    multiplicity="bonferroni",
    alpha=0.05,
    coverage_policy="refuse",
    cost_coverage_floor=0.95,
    min_trades_total=50,
    min_trades_per_fold=8,
    min_folds_evaluable=4,
    min_oos_positive_fold_frac=0.75,
    min_oos_mean_r=0.0,
    min_oos_mean_r_drop_best_fold=0.0,
    min_drop_best_fold_retention=0.60,
)

BALANCED = GateSpec(
    spec_id="wf_gate_option_B_balanced",
    authored_utc=_AUTHORED,
    author_note="Option B (Balanced) — FDR control, partial universes evaluated and stamped.",
    account="FTMO",
    multiplicity="benjamini_hochberg",
    alpha=0.10,
    coverage_policy="restrict_to_priced",
    cost_coverage_floor=0.95,
    min_retained_trade_frac=0.60,
    min_trades_total=30,
    min_trades_per_fold=5,
    min_folds_evaluable=3,
    min_oos_positive_fold_frac=0.60,
    min_oos_mean_r=0.0,
    min_oos_mean_r_drop_best_fold=0.0,
    min_drop_best_fold_retention=0.50,
)

EXPLORATORY = GateSpec(
    spec_id="wf_gate_option_C_exploratory",
    authored_utc=_AUTHORED,
    author_note=(
        "Option C (Exploratory) — RESEARCH TRIAGE ONLY. A pass here means 'worth spending "
        "more data on', never 'worth arming'. Do not let a C-pass reach a book."
    ),
    account="FTMO",
    multiplicity="benjamini_hochberg",
    alpha=0.20,
    coverage_policy="restrict_to_priced",
    cost_coverage_floor=0.95,
    min_retained_trade_frac=0.50,
    min_trades_total=20,
    min_trades_per_fold=4,
    min_folds_evaluable=3,
    min_oos_positive_fold_frac=0.50,
    min_oos_mean_r=0.0,
    # Triage only: leave-one-fold-out is disabled here ON PURPOSE, because the question
    # this option answers is "is there anything here worth more data", and a one-regime
    # result is exactly the kind of thing worth more data. It is also exactly the kind of
    # thing that must never reach a book, which is why C is labelled the way it is.
    min_oos_mean_r_drop_best_fold=None,
    min_drop_best_fold_retention=None,
)

OPTIONS: dict[str, GateSpec] = {
    "A_strict": STRICT,
    "B_balanced": BALANCED,
    "C_exploratory": EXPLORATORY,
}

OPTION_NOTES: dict[str, str] = {
    "A_strict": (
        "Controls P(any bad admission) at 5% across the whole family. Refuses any sleeve "
        "broker truth cannot fully price rather than narrowing it. Buys: a clean admission "
        "you can arm. Costs: on a 21-hypothesis family at these sample depths it will "
        "admit very little, and some of what it refuses is refused for missing tick data "
        "rather than for anything about the sleeve."
    ),
    "B_balanced": (
        "Controls the expected fraction of admitted sleeves that are junk at 10%. Evaluates "
        "a partially-priceable sleeve on its priceable subset and stamps the verdict with "
        "the symbols dropped. Buys: a usable candidate book with a stated error rate. "
        "Costs: you are accepting that roughly one admitted sleeve in ten is noise, and "
        "some admissions are about a narrower sleeve than the one in the config."
    ),
    "C_exploratory": (
        "Triage. Output is a research queue, not a book. Buys: it tells you where the next "
        "data capture would pay. Costs: at 20% FDR and these sample floors, a fifth of what "
        "it surfaces is noise by construction — which is fine for choosing what to measure "
        "next and disqualifying for anything else."
    ),
}
