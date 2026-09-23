"""CB-1 -- the frozen trade-outcome identity tuple, and its comparator.

**This module is the permission slip.** Every deletion the train lane makes is
licensed by one sentence: *the deleted thing is not in the tuple and nothing in
the tuple is computed from it*. So the tuple is defined once, here, versioned,
and the comparator that decides acceptance reads it rather than a list written
out again somewhere else.

Field names were taken from the sealed January S1R1 arm of record's own
`*_TRADE_LEDGER.jsonl` (72 rows, 1,428 keys per row, 1,295 of them scalar), not
from memory. That matters: `fast_engine.bench.TRADE_ECONOMIC_FIELDS` names ten
fields that **do not exist on a trade row** (`exit_price`, `stop_price`,
`target_price`, `net_cash`, `gross_cash`, `exact_r`, `r_multiple`,
`exit_reason`, `lots`, `volume`). That list is dead code there -- the extractor
prunes every scalar instead -- but a comparator built on it would have compared
ten `None`s to ten `None`s and reported identity. Absence has to fail loudly,
which is why `trade_tuples` refuses a row that is missing a required field
rather than defaulting it.

## What is INSIDE the tuple

Fourteen fields, in three groups, each justified:

* **instance** -- `candidate_id`, `decision_time_utc`, `symbol`, `direction`.
  Which decision, taken when, on what. Two runs that disagree here took
  different decisions.
* **execution** -- `entry_time_utc`, `entry_price`, `exit_time_utc`,
  `close_reason`. The fill and the exit. `close_reason` is in because
  `stop_loss` and `time_stop` at the same price and time are different
  contracts, and the estate has already been bitten once by a time-stop unit
  (CLAUDE.md, AQ's `time_stop_bars` repair).
* **economics + sizing** -- `final_r` (gross policy R), `cost_r` (what the
  broker-true cost engine charged), `net_r` (the cost-true outcome; the estate
  quotes this one), `risk_cash` (money at risk -- the multiplier that turns R
  into P&L), `approved_risk_pct` (the sizing decision itself), and
  `headline_result_exclusion_reason` (whether the trade counts in the arm's
  headline at all; a trade that silently flips to excluded changes the arm's
  economics without moving a single price).

`net_r == final_r - cost_r` on the sealed rows, so the three are redundant by
one degree of freedom **on the frozen engine**. They are all three in the tuple
precisely so that a cut which breaks that relation is caught rather than
cancelled out.

## What is deliberately OUTSIDE the tuple -- the deletion licence

Named, because a reader must be able to check the licence rather than trust it:

* **run-namespace-derived ids** -- `simulated_order_id`, `simulated_trade_id`,
  `package_replay_*_bound_order_id`/`_trade_id`. The engine refuses to reuse an
  output namespace and stamps it INTO row values, so these differ between two
  runs of the frozen engine itself (AX measured 84 of 328 raw differences from
  exactly this). They carry no economics.
* **provenance digests** -- `packet_sidecar_id`, `scheduler_packet_sidecar_id`,
  `*_packet_hash_sha256`, `*_projection_sha256`. AX's control run proved these
  are the complete residue of frozen-vs-frozen: 244 differences, 7 field names,
  **0 moved quantities**. They prove; they do not decide.
* **attribution/authority projections** -- the ~1,280 remaining scalar fields
  per row. Kept ONLY where a decision reads them (that is the whole of `cuts`,
  and the reason the authority hash is memoised rather than skipped).
* **receipts and ledgers** -- the post-hoc re-certification of already-written
  rows, and the evidence tree's own integrity artifacts.
* **timings** -- `*_seconds`, `*_elapsed`, `host`, `pid`, `*_generated_at`.

## What is outside the tuple but still GATED

Row counts on all five ledgers, and the missed-opportunity diagnostic pool
aggregate. Neither is per-trade identity, and both are checked anyway: the
missed pool is the substrate AW's separability mine reads (JANUARY_BANK 3's
+/-38,317 R), so a lane that silently changed it would be fast and useless.
"""

from __future__ import annotations

import math
from typing import Any, Iterable, Mapping, Sequence

#: Bumped when a FIELD moves in or out. A comparison receipt records it, so an
#: acceptance claim can never be read against a tuple it was not measured under.
TUPLE_VERSION = "gtos.train_engine.trade_identity.v1"

#: The gate. Order is fixed: the tuple is compared positionally.
TRADE_IDENTITY_FIELDS: tuple[str, ...] = (
    "candidate_id",
    "decision_time_utc",
    "symbol",
    "direction",
    "entry_time_utc",
    "entry_price",
    "exit_time_utc",
    "close_reason",
    "final_r",
    "cost_r",
    "net_r",
    "risk_cash",
    "approved_risk_pct",
    "headline_result_exclusion_reason",
)

#: Orders include the ones that never became trades. A cut that silently stopped
#: placing an order would leave the trade set unchanged if that order never
#: filled, so orders are gated separately rather than folded into the trade set.
ORDER_IDENTITY_FIELDS: tuple[str, ...] = (
    "candidate_id",
    "decision_time_utc",
    "symbol",
    "direction",
    "risk_cash",
    "approved_risk_pct",
)

#: The per-day economic roll-up. Catches a divergence that cancels out across
#: trades -- two compensating sign errors inside one day.
DAY_IDENTITY_FIELDS: tuple[str, ...] = (
    "day",
    "decision_day",
    "start_day",
)

#: Absolute float tolerance. ZERO by commission ("tuple-set equality, zero
#: tolerance"). Kept as a named constant so that a future session that wants a
#: tolerance has to change a declared number in a receipt rather than loosen a
#: comparison quietly.
FLOAT_TOLERANCE = 0.0


class IdentityExtractionError(ValueError):
    """A row could not be reduced to an identity tuple. Never silently skipped."""


def _canonical(value: Any) -> Any:
    """Normalise one field value for comparison.

    Floats are compared by exact bit value after a nan fold; the whole point of
    the zero-tolerance gate is that 4377.82 and 4377.8200000001 are a failure.
    """

    if isinstance(value, float):
        if math.isnan(value):
            return "__nan__"
        return value
    if isinstance(value, bool):  # before int: bool IS an int in Python
        return f"__bool__{value}"
    return value


def trade_tuples(
    rows: Iterable[Mapping[str, Any]],
    *,
    fields: Sequence[str] = TRADE_IDENTITY_FIELDS,
    kind: str = "trade",
) -> list[tuple[Any, ...]]:
    """Reduce rows to identity tuples, refusing any row missing a field.

    Returns a LIST, not a set: duplicate tuples are meaningful (two identical
    trades is a different arm from one), so multiplicity is preserved and the
    comparator uses a multiset.
    """

    out: list[tuple[Any, ...]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise IdentityExtractionError(f"{kind}_row_{index}_not_a_mapping")
        missing = [field for field in fields if field not in row]
        if missing:
            # A missing field is the failure mode this module exists to stop.
            # Defaulting it to None would compare two Nones and pass.
            raise IdentityExtractionError(
                f"{kind}_row_{index}_missing_identity_fields:{','.join(missing)}"
            )
        out.append(tuple(_canonical(row[field]) for field in fields))
    return out


def _multiset(tuples: Iterable[tuple[Any, ...]]) -> dict[tuple[Any, ...], int]:
    counts: dict[tuple[Any, ...], int] = {}
    for item in tuples:
        counts[item] = counts.get(item, 0) + 1
    return counts


def _diff_multisets(
    baseline: list[tuple[Any, ...]],
    candidate: list[tuple[Any, ...]],
    *,
    fields: Sequence[str],
    max_examples: int = 12,
) -> dict[str, Any]:
    left, right = _multiset(baseline), _multiset(candidate)
    only_baseline = {k: v for k, v in left.items() if right.get(k, 0) < v}
    only_candidate = {k: v for k, v in right.items() if left.get(k, 0) < v}

    def render(counts: dict[tuple[Any, ...], int]) -> list[dict[str, Any]]:
        return [
            {"multiplicity": n, **dict(zip(fields, key))}
            for key, n in list(counts.items())[:max_examples]
        ]

    return {
        "baseline_rows": len(baseline),
        "candidate_rows": len(candidate),
        "identical": not only_baseline and not only_candidate,
        "only_in_baseline_count": len(only_baseline),
        "only_in_candidate_count": len(only_candidate),
        "only_in_baseline": render(only_baseline),
        "only_in_candidate": render(only_candidate),
    }


def _field_level_divergence(
    baseline: list[tuple[Any, ...]],
    candidate: list[tuple[Any, ...]],
    *,
    fields: Sequence[str],
) -> dict[str, Any]:
    """When the sets differ, say WHICH field moved.

    Matches rows on the instance prefix (candidate_id + decision_time_utc) so a
    changed price reports as "entry_price moved" rather than as two unrelated
    set differences. A reader who cannot see the moved field cannot act.
    """

    key_width = 2 if len(fields) >= 2 else 1
    by_key: dict[tuple[Any, ...], tuple[Any, ...]] = {}
    for row in baseline:
        by_key.setdefault(row[:key_width], row)
    moved: dict[str, int] = {}
    examples: list[dict[str, Any]] = []
    unmatched = 0
    for row in candidate:
        other = by_key.get(row[:key_width])
        if other is None:
            unmatched += 1
            continue
        for position, name in enumerate(fields):
            if other[position] != row[position]:
                moved[name] = moved.get(name, 0) + 1
                if len(examples) < 12:
                    examples.append(
                        {
                            "instance": list(row[:key_width]),
                            "field": name,
                            "baseline": other[position],
                            "candidate": row[position],
                        }
                    )
    return {
        "matched_on": list(fields[:key_width]),
        "fields_moved": dict(sorted(moved.items(), key=lambda kv: -kv[1])),
        "unmatched_candidate_rows": unmatched,
        "examples": examples,
    }


def compare_economics(
    baseline: Mapping[str, Any],
    candidate: Mapping[str, Any],
    *,
    require_missed_pool: bool = True,
) -> dict[str, Any]:
    """The acceptance comparator. Reads two `bench.extract_economics` payloads.

    `verdict` is `OUTCOME_IDENTICAL` only when the trade multiset, the order
    multiset, every ledger row count and the missed-opportunity diagnostic pool
    all match. Anything else names what moved.
    """

    findings: dict[str, Any] = {
        "tuple_version": TUPLE_VERSION,
        "trade_identity_fields": list(TRADE_IDENTITY_FIELDS),
        "order_identity_fields": list(ORDER_IDENTITY_FIELDS),
        "float_tolerance": FLOAT_TOLERANCE,
    }
    failures: list[str] = []

    trades = _diff_multisets(
        trade_tuples(baseline.get("trades") or (), kind="baseline_trade"),
        trade_tuples(candidate.get("trades") or (), kind="candidate_trade"),
        fields=TRADE_IDENTITY_FIELDS,
    )
    findings["trades"] = trades
    if not trades["identical"]:
        failures.append("trade_identity_set_differs")
        findings["trade_field_divergence"] = _field_level_divergence(
            trade_tuples(baseline.get("trades") or (), kind="baseline_trade"),
            trade_tuples(candidate.get("trades") or (), kind="candidate_trade"),
            fields=TRADE_IDENTITY_FIELDS,
        )

    orders = _diff_multisets(
        trade_tuples(
            baseline.get("orders") or (),
            fields=ORDER_IDENTITY_FIELDS,
            kind="baseline_order",
        ),
        trade_tuples(
            candidate.get("orders") or (),
            fields=ORDER_IDENTITY_FIELDS,
            kind="candidate_order",
        ),
        fields=ORDER_IDENTITY_FIELDS,
    )
    findings["orders"] = orders
    if not orders["identical"]:
        failures.append("order_identity_set_differs")

    base_counts = dict(baseline.get("counts") or {})
    cand_counts = dict(candidate.get("counts") or {})
    findings["counts"] = {
        "baseline": base_counts,
        "candidate": cand_counts,
        "identical": base_counts == cand_counts,
    }
    if base_counts != cand_counts:
        failures.append("ledger_row_counts_differ")

    base_pool = dict(baseline.get("missed_digest") or {})
    cand_pool = dict(candidate.get("missed_digest") or {})
    findings["missed_opportunity_pool"] = {
        "baseline": base_pool,
        "candidate": cand_pool,
        "identical": base_pool == cand_pool,
    }
    if base_pool != cand_pool:
        # The training substrate. A lane that changes it is fast and useless.
        if require_missed_pool:
            failures.append("missed_opportunity_pool_differs")
        else:
            findings["missed_opportunity_pool"]["gated"] = False

    # An all-zero pool means the aggregate silently skipped every row -- AX's
    # own instrument shipped exactly that bug. Refuse to accept on it.
    if require_missed_pool and base_pool:
        scoreable = base_pool.get("diagnostic_scoreable_rows")
        if base_pool.get("rows") and not scoreable:
            failures.append("missed_opportunity_pool_baseline_scored_nothing")

    findings["failures"] = failures
    findings["verdict"] = "OUTCOME_IDENTICAL" if not failures else "OUTCOME_DIVERGED"
    return findings
