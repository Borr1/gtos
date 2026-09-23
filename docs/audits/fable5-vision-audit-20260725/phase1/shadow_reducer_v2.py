#!/usr/bin/env python3
"""Shadow reducer v2 — recompute every trade's R from PRICES, independently.

WHY THIS EXISTS
===============
GTOS carries roughly 54,000 lines of proof machinery. The second independent
audit (`SECOND_AUDIT.md` §1 verdict E3, §3.5) established what all of it does
and does not attest:

    The route analyzer *does* independently re-sum economics from ledger rows
    with per-row identity checks (`pnl_cash == risk_cash x net_r` @1e-6; stress
    recompute @1e-8). But **nothing anywhere recomputes a trade's R from
    prices**: the analyzer contains zero `entry_price` / `exit_price` /
    `stop_loss` references, so an engine-side per-trade R defect is certified by
    the whole chain.

So the sealed evidence attests *byte custody* and *internal arithmetic
consistency*. It does not attest that the R the engine wrote down is the R the
prices imply. This file answers that question and only that question.

CONTRACT OF THIS FILE
=====================
1. **Zero imports from `src/`.** Standard library only. A reducer that imports
   the engine it checks proves nothing. This is enforced by
   `test_shadow_reducer_v2.py::test_reducer_imports_nothing_from_src`.
2. **Refuse rather than compute through.** F17: the replay's `normalize_row`
   silently coerces unparseable OHLCV to `0.0` and drops bad-time rows
   (`v4:4640-4667`). A `0.0` price in a ledger may be a coercion artifact rather
   than a real value. Every input is classified before use, and any row that
   cannot be recomputed honestly is REFUSED and counted, never estimated.
3. **No inference from the answer.** Where an exit price is absent, this reducer
   does NOT back it out of the recorded R (e.g. "gross_r is -1.0 so the exit
   must have been the stop"). That would assume the thing under test. Such rows
   are refused and reported as coverage loss.
4. **No clock-conditioned claims.** F7: every research timestamp is broker time
   labelled UTC, 2-3 h off. A price is a price, so R recomputation is unaffected
   — but nothing here is bucketed by session or hour, deliberately.

WHAT THE ENGINE ACTUALLY BOOKS — read this before interpreting any number here
==============================================================================
Established by direct source read, and it reframes the whole measurement. The
replay's exit simulator closes a trade in one of two ways
(`src/research/dynamic_execution_policy.py`):

  * **Level exits** — the R is a *threshold*, and no price is consulted:
        stop          `close(reason=stop_reason, exit_r=stop_r, obs=obs)`      :428
        giveback      `giveback_exit_r = best_mfe - policy.giveback_close_r`   :509
        final target  `exit_r = policy.final_target_r`                         :462-467
  * **Mark exits** — the R *is* the observation's own price-derived R:
        path end      `close(reason="path_end_mark_to_market", exit_r=last.close_r, ...)` :641
        time stop     `close(reason="time_stop", exit_r=obs.close_r, obs=obs)`            :626

`final_r = partial_realized_r + remaining_fraction * exit_r` (:379).

And `exit_price` is **not a fill price**. It is the quote on the observation
whose index the exit landed on: `exit_quote_detail` is matched by
`detail["index"] == result.exit_index`
(`v4_timewarp_simulated_live_research_loop.py:61216-61222`) and stamped at
`:61296`. The observation's own R is built from that same quote at `:60803`
(`r_value = (price - entry)/risk` LONG, `(entry - price)/risk` SHORT), with
`close_r = r_value`, and the quote is appended to `observation_quote_details`
at `:60816-60823`.

**Two consequences that govern how this file's output must be read:**

1. On **mark exits**, this reducer's formula is *algebraically identical* to the
   engine's, so agreement is a TAUTOLOGY, not a validation. An earlier revision
   of this file reported that agreement as a control proving the reducer's
   arithmetic. It proves no such thing, and the claim has been withdrawn. What
   it does confirm is that this reducer uses the engine's own geometry.
2. On **level exits**, the difference between the price-derived R and the booked
   R is not an arithmetic disagreement. It is the distance the market travelled
   PAST the threshold before the crossing was observed — i.e. **unmodelled exit
   gap-through**. The engine grants exactly zero of it.

That second quantity is what this file measures, and it is named
`unmodelled_exit_gap_through_r` throughout rather than "delta" or
"disagreement", because calling it a disagreement mislabels a real
execution-realism gap as an arithmetic defect.

**The one genuine control** is `sealed_shape_ledger_aggregates`: re-summing the
ledger in the sealed audit's own row-set conventions and reproducing all of its
economics values. That checks that this reducer reads the evidence correctly,
and it is independent of everything above.

WHAT IT RECOMPUTES
==================
Per trade, from `entry_price`, `stop_loss`, `direction` and the exit quote:

    risk_distance      = |entry_price - stop_loss|                  (price units)
    signed_move        = (exit - entry)   if LONG
                         (entry - exit)   if SHORT
    gross_r            = signed_move / risk_distance
    cost_r             = spread_r + swap_cost_r + commission_r + expected_slippage_r
    net_r              = gross_r - cost_r
    pnl_cash           = net_r * risk_cash

and the headline aggregates, which are named exactly as the sealed matrix audit
names them in its per-arm `economics` block:

    physical_gross_r · execution_cost_r · physical_net_r ·
    scoreable_net_cash · scoreable_accepted_risk_cash

plus the derived `cash_per_accepted_risk_dollar` (q = net cash / risk cash).

USAGE
=====
    python3 shadow_reducer_v2.py --arm-window <name>=<trade_ledger.jsonl> [...]
                                 [--matrix-audit <MATRIX_AUDIT.json>]
                                 [--out receipts/<name>.json]
                                 [--json]

Read-only. It opens ledgers for reading and writes nothing outside --out.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterator, Optional

SCHEMA = "gtos.phase1.shadow_reducer_v2.v1"

# Ratio comparisons use a relative tolerance; float64 summation over a few
# hundred terms cannot drift further than this.
REL_TOL = 1e-9
ABS_TOL = 1e-9

# The risk distance must be a real fraction of the price, not merely non-zero.
# An absolute floor is instrument-scale-blind: at BTCUSD/NAS100/US30 magnitudes a
# ONE-ULP stop clears any fixed epsilon and yields an R in the 1e11 range, which
# would silently destroy an arm total (there is no cap or outlier gate anywhere
# downstream). Relative floor: a stop closer than this fraction of entry is
# degenerate at any price scale.
MIN_RISK_DISTANCE_FRACTION_OF_ENTRY = 1e-9
# Absolute backstop for the pathological case of a very small entry price.
MIN_RISK_DISTANCE = 1e-12

DIRECTION_LONG = "LONG"
DIRECTION_SHORT = "SHORT"

# How the engine booked the exit R, per `dynamic_execution_policy.py`. The
# distinction decides whether a row MEASURES anything: on a mark exit this
# reducer's formula is the engine's own, so agreement is tautological.
EXIT_FAMILY_LEVEL = "level"      # R is a threshold; the quote is the crossing tick
EXIT_FAMILY_MARK = "mark"        # R IS the quote's own R — comparison is a tautology
EXIT_FAMILY_UNKNOWN = "unknown"  # not classified against source; excluded and COUNTED

# Every branch enumerated from `src/research/dynamic_execution_policy.py`. A
# reason is LEVEL when the branch passes a threshold constant as `exit_r`, and
# MARK when it passes an observation's own `close_r`.
_LEVEL_EXIT_REASONS = {
    "stop_loss",                            # :428  exit_r=stop_r
    "giveback_close",                       # :533  exit_r=best_mfe - giveback_close_r
    "final_target",                         # :464  exit_r=policy.final_target_r
    "trailing_stop",                        # :498  exit_r=stop_r
    "tp1_full_or_all_partial_close",        # :453  threshold
    "final_target_after_tp1_same_bar",      # :457  threshold
    "stop_first_same_bar_conservative",     # :420  threshold
    # Same-bar ambiguity books a hardcoded exit_r=0.0 (:412, :491, :516). That
    # is a level too — and classifying it MARK would zero out precisely the
    # defect it represents.
    "same_bar_stop_close_ambiguous",
    "same_bar_giveback_close_ambiguous",
    "same_bar_trailing_close_ambiguous",
    # Raw fixed-target geometry, assigned categorically at v4:58883-58901.
    "stop_reached_before_target",
    "target_reached_before_stop",
}
_MARK_EXIT_REASONS = {
    "path_end_mark_to_market",              # :641  exit_r=last.close_r
    "time_stop",                            # :627  exit_r=obs.close_r
    "abort_adverse_close",                  # :624  exit_r=obs.close_r
    "early_cut_no_progress",                # :635  exit_r=obs.close_r
    "max_bars_mark_to_market",              # :638  exit_r=obs.close_r
    "stale_thesis_close",                   # :556  exit_r=obs.close_r
    "time_stop_close_mark_from_m1",         # M1 proxy of the time-stop mark
}

# The trade ledger composes the policy reason as `selected_policy_replay:<reason>`.
_POLICY_REPLAY_PREFIX = "selected_policy_replay:"


def classify_exit_family(close_reason: str) -> str:
    """Level vs mark vs unknown, decided against the engine's own branches.

    UNKNOWN is a distinct family rather than a silent fold into MARK. Folding it
    into MARK would exclude it from the measurement — the safe direction — but
    would also make an unrecognised reason indistinguishable from a verified
    mark exit in the output, so a future policy (trailing, TP1) could
    under-report without any signal. Unknown rows are excluded AND counted.
    """
    bare = close_reason
    if bare.startswith(_POLICY_REPLAY_PREFIX):
        bare = bare[len(_POLICY_REPLAY_PREFIX):]
    if bare in _LEVEL_EXIT_REASONS:
        return EXIT_FAMILY_LEVEL
    if bare in _MARK_EXIT_REASONS:
        return EXIT_FAMILY_MARK
    return EXIT_FAMILY_UNKNOWN

# Cost components the engine sums into `cost_r`. Recomputed here from parts so a
# defect in the engine's own summation is visible rather than inherited.
COST_COMPONENT_KEYS = (
    "spread_r",
    "swap_cost_r",
    "commission_r",
    "expected_slippage_r",
)


# ---------------------------------------------------------------------------
# Value classification — the F17 boundary
# ---------------------------------------------------------------------------

class Refusal(Exception):
    """Raised when a value cannot be used honestly. Carries a machine reason."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


def classify_price(raw: Any, field_name: str) -> float:
    """Return a usable price, or raise Refusal naming exactly what was wrong.

    The whole point of this function is that "price is zero" and "price was
    unparseable" are DIFFERENT refusals with different reasons, and neither is
    ever silently turned into a number. F17's coercion writes `0.0`; a genuine
    zero price does not exist for any instrument in the 24-symbol surface, so an
    exact 0.0 is refused as a suspected coercion artifact rather than used.
    """
    if raw is None:
        raise Refusal(f"{field_name}_absent", "key missing or null")
    if isinstance(raw, bool):
        # bool is a subclass of int; a boolean in a price slot is a schema fault.
        raise Refusal(f"{field_name}_unparseable", f"bool in price slot: {raw!r}")
    if isinstance(raw, str):
        stripped = raw.strip()
        if not stripped:
            raise Refusal(f"{field_name}_absent", "empty string")
        if "_" in stripped:
            # Python accepts "1_234.5" as a numeric literal. No JSON producer
            # emits that, so treating it as a number would be inventing data.
            raise Refusal(f"{field_name}_unparseable", f"underscore literal: {raw!r}")
        try:
            value = float(stripped)
        except ValueError:
            raise Refusal(f"{field_name}_unparseable", f"str not a float: {raw!r}") from None
    elif isinstance(raw, (int, float)):
        value = float(raw)
    else:
        raise Refusal(f"{field_name}_unparseable", f"{type(raw).__name__}: {raw!r}")

    if not math.isfinite(value):
        raise Refusal(f"{field_name}_unparseable", f"non-finite: {value!r}")
    if value == 0.0:
        # Distinguished from "unparseable" on purpose: this is the F17 signature.
        raise Refusal(
            f"{field_name}_zero",
            "exactly 0.0 — indistinguishable from a normalize_row coercion artifact",
        )
    if value < 0.0:
        raise Refusal(f"{field_name}_negative", f"{value!r}")
    return value


def classify_number(raw: Any, field_name: str, *, allow_zero: bool = True) -> float:
    """Like classify_price but for non-price quantities (R values, cash, costs).

    Zero is legitimate here — `commission_r` is genuinely 0.0 throughout — so
    zero is allowed by default and only absence/unparseability refuses.
    """
    if raw is None:
        raise Refusal(f"{field_name}_absent", "key missing or null")
    if isinstance(raw, bool):
        raise Refusal(f"{field_name}_unparseable", f"bool: {raw!r}")
    if isinstance(raw, str):
        stripped = raw.strip()
        if not stripped:
            raise Refusal(f"{field_name}_absent", "empty string")
        try:
            value = float(stripped)
        except ValueError:
            raise Refusal(f"{field_name}_unparseable", f"str not a float: {raw!r}") from None
    elif isinstance(raw, (int, float)):
        value = float(raw)
    else:
        raise Refusal(f"{field_name}_unparseable", f"{type(raw).__name__}: {raw!r}")
    if not math.isfinite(value):
        raise Refusal(f"{field_name}_unparseable", f"non-finite: {value!r}")
    if not allow_zero and value <= 0.0:
        # `<= 0`, not `== 0`. The sealed analyzer refuses a non-positive
        # risk_cash outright (`analyze_b7_5_selection_sizing_matrix.py:787-790`,
        # raises `trade_risk_not_positive`); an earlier revision of this reducer
        # blocked only exact zero and would therefore admit a negative-risk row
        # and emit a sign-flipped pnl_cash — weaker than the thing it checks.
        raise Refusal(f"{field_name}_not_positive", f"{value!r}")
    return value


def classify_direction(raw: Any) -> str:
    if raw is None:
        raise Refusal("direction_absent", "key missing or null")
    text = str(raw).strip().upper()
    if text in (DIRECTION_LONG, "BUY"):
        return DIRECTION_LONG
    if text in (DIRECTION_SHORT, "SELL"):
        return DIRECTION_SHORT
    raise Refusal("direction_unknown", f"{raw!r}")


# ---------------------------------------------------------------------------
# Per-trade recomputation
# ---------------------------------------------------------------------------

@dataclass
class TradeRecomputation:
    """One trade, recomputed from prices, alongside what the ledger recorded."""

    trade_id: str
    symbol: str
    direction: str
    trading_day: str
    close_reason: str
    exit_family: str
    terminal_r_source: str
    exit_price_provenance: str

    entry_price: float
    stop_loss: float
    exit_price: float
    risk_distance: float

    # Recomputed here, from prices only.
    recomputed_gross_r: float
    recomputed_cost_r: float
    recomputed_net_r: float
    recomputed_pnl_cash: float

    # Recorded by the engine.
    ledger_gross_r: float
    ledger_cost_r: float
    ledger_net_r: float
    ledger_pnl_cash: float
    ledger_risk_cash: float
    # The engine's own allowance for execution slip — a flat constant per trade.
    ledger_expected_slippage_r: float

    @property
    def gross_r_delta(self) -> float:
        """Price-derived R minus booked R. Costs appear on neither side.

        On a LEVEL exit this is the market's excursion past the threshold before
        the crossing was observed — unmodelled exit gap-through. On a MARK exit
        it is identically zero by construction and measures nothing.
        """
        return self.recomputed_gross_r - self.ledger_gross_r

    @property
    def unmodelled_exit_gap_through_r(self) -> float:
        """The gap-through, zero on mark exits so it can be summed safely."""
        if self.exit_family != EXIT_FAMILY_LEVEL:
            return 0.0
        return self.gross_r_delta

    @property
    def net_r_delta(self) -> float:
        return self.recomputed_net_r - self.ledger_net_r

    @property
    def pnl_cash_delta(self) -> float:
        return self.recomputed_pnl_cash - self.ledger_pnl_cash

    # -- Cost-neutral restatement -------------------------------------------
    # The headline projection uses the LEDGER's own `cost_r`, not this
    # reducer's reconstruction of it. Two measured reasons, pulling opposite
    # ways, and using the ledger value cancels both:
    #
    #   * the price-derived gross R is taken from a real quote-side fill, so it
    #     already embeds realised spread/slippage; subtracting the engine's
    #     modelled cost on top would double-count it, and
    #   * on 14 of 88 sealed S0R0 rows the engine's `cost_r` EXCEEDS the sum of
    #     its four named components (always in that direction), so this
    #     reducer's component sum under-charges those rows.
    #
    # Holding cost fixed at the ledger value isolates the one thing under test.
    @property
    def cost_neutral_net_r(self) -> float:
        return self.recomputed_gross_r - self.ledger_cost_r

    @property
    def cost_neutral_net_r_delta(self) -> float:
        # Identical to gross_r_delta by construction; kept explicit so the
        # cash figure below is obviously a pure re-expression of it.
        return self.cost_neutral_net_r - self.ledger_net_r

    @property
    def gross_gap_pnl_cash_delta(self) -> float:
        """UPPER BOUND on the cash impact — the full gap, nothing netted.

        Correct only if `expected_slippage_r` is understood to cover something
        other than exit slip. Since the engine documents nothing about what the
        constant covers, this bound is reported but is NOT the headline.
        """
        return self.unmodelled_exit_gap_through_r * self.ledger_risk_cash

    @property
    def netted_gap_through_r(self) -> float:
        """The defensible figure: gap-through net of the allowance already charged.

        The engine charges `expected_slippage_r` on this trade and books its R at
        the threshold. The price-derived R already embeds the realised slip. So
        restating the trade at the price-derived R while ALSO leaving the modelled
        slippage in `cost_r` charges the same thing twice.

        Netting it per-trade — the trade's own allowance against its own gap — is
        what `shortfall_r` reports, and it is roughly 2.4x smaller than the
        un-netted figure on the sealed January arms. An earlier revision published
        the un-netted number as the headline; that was the double-count its own
        comment warned about.
        """
        if self.exit_family != EXIT_FAMILY_LEVEL:
            return 0.0
        return self.unmodelled_exit_gap_through_r + self.ledger_expected_slippage_r

    @property
    def cost_neutral_pnl_cash_delta(self) -> float:
        return self.netted_gap_through_r * self.ledger_risk_cash


@dataclass
class RefusedTrade:
    trade_id: str
    symbol: str
    trading_day: str
    close_reason: str
    reason: str
    detail: str
    ledger_gross_r: Optional[float] = None
    ledger_net_r: Optional[float] = None
    ledger_pnl_cash: Optional[float] = None


def resolve_exit_price(row: dict) -> tuple[float, str]:
    """Resolve the exit price and say where it came from.

    Two admissible sources:

      1. `selected_execution_policy_replay_exit.exit_price` — the quote on the
         observation the exit landed on. **Not a fill price**: it is stamped by
         matching `exit_quote_detail["index"] == result.exit_index`
         (`v4_timewarp_simulated_live_research_loop.py:61216-61222,61296`). On a
         level exit this is the tick that CROSSED the threshold, so it sits past
         it.
      2. `close_mark_price` — the M1-proxy mark used when the tick path did not
         produce a terminal fill.

    Deliberately NOT a third tier: rows whose recorded `gross_r` is exactly
    -1.0 or exactly the target could have their exit price *inferred* as the
    stop or the target. That inference assumes precisely what this reducer
    exists to test, so those rows are refused instead.
    """
    exit_block = row.get("selected_execution_policy_replay_exit")
    if isinstance(exit_block, dict) and exit_block.get("exit_price") is not None:
        return classify_price(exit_block.get("exit_price"), "exit_price"), \
            "selected_execution_policy_replay_exit.exit_price"
    if row.get("close_mark_price") is not None:
        return classify_price(row.get("close_mark_price"), "exit_price"), "close_mark_price"
    raise Refusal(
        "exit_price_absent",
        "neither selected_execution_policy_replay_exit.exit_price nor close_mark_price "
        "is present; refusing to infer it from the recorded R",
    )


def recompute_trade(row: dict) -> TradeRecomputation:
    """Recompute one trade's R from its prices. Raises Refusal if it cannot."""
    direction = classify_direction(row.get("direction") or row.get("side"))
    entry_price = classify_price(row.get("entry_price"), "entry_price")
    stop_loss = classify_price(row.get("stop_loss"), "stop_loss")
    exit_price, exit_provenance = resolve_exit_price(row)

    # The R denominator is the entry-to-stop distance, in price units.
    risk_distance = abs(entry_price - stop_loss)
    minimum = max(MIN_RISK_DISTANCE, entry_price * MIN_RISK_DISTANCE_FRACTION_OF_ENTRY)
    if risk_distance <= minimum:
        raise Refusal(
            "degenerate_risk_distance",
            f"|entry {entry_price} - stop {stop_loss}| = {risk_distance} "
            f"<= {minimum} ({MIN_RISK_DISTANCE_FRACTION_OF_ENTRY} of entry)",
        )

    # A stop on the profitable side of entry is not a stop. Catching this here
    # rather than letting it produce a plausible-looking R is the point.
    if direction == DIRECTION_LONG and stop_loss >= entry_price:
        raise Refusal(
            "stop_wrong_side",
            f"LONG with stop {stop_loss} >= entry {entry_price}",
        )
    if direction == DIRECTION_SHORT and stop_loss <= entry_price:
        raise Refusal(
            "stop_wrong_side",
            f"SHORT with stop {stop_loss} <= entry {entry_price}",
        )

    signed_move = (
        exit_price - entry_price if direction == DIRECTION_LONG
        else entry_price - exit_price
    )
    recomputed_gross_r = signed_move / risk_distance

    # Costs are recomputed from their components rather than read from `cost_r`,
    # so an error in the engine's own summation shows up as a disagreement.
    cost_parts = {
        key: classify_number(row.get(key), key) for key in COST_COMPONENT_KEYS
    }
    recomputed_cost_r = sum(cost_parts.values())

    recomputed_net_r = recomputed_gross_r - recomputed_cost_r
    ledger_risk_cash = classify_number(row.get("risk_cash"), "risk_cash", allow_zero=False)
    recomputed_pnl_cash = recomputed_net_r * ledger_risk_cash

    exit_block = row.get("selected_execution_policy_replay_exit") or {}

    return TradeRecomputation(
        trade_id=str(row.get("simulated_trade_id") or ""),
        symbol=str(row.get("symbol") or ""),
        direction=direction,
        trading_day=str(row.get("trading_day") or ""),
        close_reason=str(row.get("close_reason") or ""),
        exit_family=classify_exit_family(str(row.get("close_reason") or "")),
        terminal_r_source=str(exit_block.get("terminal_r_source") or ""),
        exit_price_provenance=exit_provenance,
        entry_price=entry_price,
        stop_loss=stop_loss,
        exit_price=exit_price,
        risk_distance=risk_distance,
        recomputed_gross_r=recomputed_gross_r,
        recomputed_cost_r=recomputed_cost_r,
        recomputed_net_r=recomputed_net_r,
        recomputed_pnl_cash=recomputed_pnl_cash,
        ledger_gross_r=classify_number(row.get("gross_r"), "gross_r"),
        ledger_cost_r=classify_number(row.get("cost_r"), "cost_r"),
        ledger_net_r=classify_number(row.get("net_r"), "net_r"),
        ledger_pnl_cash=classify_number(row.get("pnl_cash"), "pnl_cash"),
        ledger_risk_cash=ledger_risk_cash,
        ledger_expected_slippage_r=cost_parts["expected_slippage_r"],
    )


# ---------------------------------------------------------------------------
# Arm-window reduction
# ---------------------------------------------------------------------------

def iter_rows(path: Path) -> Iterator[dict]:
    """Stream a JSONL ledger. Rows are ~500 KB; never load the file whole (H3)."""
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise Refusal("row_unparseable", f"{path.name}:{line_number}: {exc}") from None
            if not isinstance(row, dict):
                raise Refusal("row_not_object", f"{path.name}:{line_number}")
            yield row


def _sum(values) -> float:
    """Deterministic summation. math.fsum keeps the comparison honest at 1e-9."""
    return math.fsum(values)


def reduce_arm_window(name: str, trade_ledger: Path) -> dict:
    """Reduce one arm-window and return a fully self-describing result block."""
    recomputed: list[TradeRecomputation] = []
    refused: list[RefusedTrade] = []
    scoreable_rows = 0
    physical_rows = 0
    unscoreable_rows = 0
    zero_price_fields: Counter = Counter()

    # Raw ledger sums, kept in the sealed audit's own row-set conventions. These
    # were established empirically against the sealed S0R0 economics block, not
    # assumed — see `sealed_shape_ledger_aggregates` below.
    all_row_risk_cash: list[float] = []
    all_row_cost_r: list[float] = []
    all_row_expected_slippage_r: list[float] = []
    scoreable_gross_r: list[float] = []
    scoreable_net_r: list[float] = []
    scoreable_pnl_cash: list[float] = []
    scoreable_risk_cash: list[float] = []
    scoreable_flag_disagreements = 0

    for row in iter_rows(trade_ledger):
        physical_rows += 1
        trade_id = str(row.get("simulated_trade_id") or "")

        # Census of exact-0.0 prices regardless of admission, so the F17 surface
        # is reported even for rows that are excluded for other reasons.
        for field_name in ("entry_price", "stop_loss", "take_profit_1"):
            if row.get(field_name) == 0.0:
                zero_price_fields[field_name] += 1
        exit_block = row.get("selected_execution_policy_replay_exit")
        if isinstance(exit_block, dict) and exit_block.get("exit_price") == 0.0:
            zero_price_fields["exit_price"] += 1

        # `risk_cash` and `cost_r` are summed over ALL physical rows, including
        # unscoreable ones — that is how the sealed audit forms
        # `accepted_risk_cash` and `execution_cost_r`. Verified against S0R0:
        # sum(cost_r) over 90 rows = 6.76829763 = sealed execution_cost_r, while
        # the 88-row sum is 6.67549763 and matches nothing.
        if row.get("risk_cash") is not None:
            all_row_risk_cash.append(float(row["risk_cash"]))
        if row.get("cost_r") is not None:
            all_row_cost_r.append(float(row["cost_r"]))
        if row.get("expected_slippage_r") is not None:
            all_row_expected_slippage_r.append(float(row["expected_slippage_r"]))

        # The analyzer's scoreability predicate is `net_proxy_r is not None`
        # (`analyze_b7_5_selection_sizing_matrix.py:791-792`), NOT the row's
        # `result_scoreable` flag. They coincide on the sealed January arms; any
        # divergence is reported rather than silently resolved.
        analyzer_scoreable = row.get("net_proxy_r") is not None
        if analyzer_scoreable != (row.get("result_scoreable") is True):
            scoreable_flag_disagreements += 1

        if not analyzer_scoreable:
            unscoreable_rows += 1
            continue
        scoreable_rows += 1

        for values, key in (
            (scoreable_gross_r, "gross_r"),
            (scoreable_net_r, "net_r"),
            (scoreable_pnl_cash, "pnl_cash"),
            (scoreable_risk_cash, "risk_cash"),
        ):
            if row.get(key) is not None:
                values.append(float(row[key]))

        try:
            recomputed.append(recompute_trade(row))
        except Refusal as refusal:
            refused.append(RefusedTrade(
                trade_id=trade_id,
                symbol=str(row.get("symbol") or ""),
                trading_day=str(row.get("trading_day") or ""),
                close_reason=str(row.get("close_reason") or ""),
                reason=refusal.reason,
                detail=refusal.detail,
                ledger_gross_r=row.get("gross_r"),
                ledger_net_r=row.get("net_r"),
                ledger_pnl_cash=row.get("pnl_cash"),
            ))

    # ---- Aggregates -------------------------------------------------------
    # Two comparands, and the distinction matters:
    #
    #   "covered"  — only the rows this reducer could recompute from prices.
    #                Recomputed vs ledger on the SAME row set: an apples-to-
    #                apples per-row comparison.
    #   "all_scoreable" — the ledger's own values over every scoreable row.
    #                This is what the sealed matrix audit reports, so it is the
    #                number to reconcile against.
    covered = recomputed

    # ---- (a) The sealed audit's own aggregates, reproduced from the ledger ---
    # Same fields, same row sets, same definitions as
    # `analyze_b7_5_selection_sizing_matrix.py::trade_economics` (:1423-1473).
    # This half re-sums the ledger exactly as the analyzer does, so agreement
    # here proves only that this reducer reads the ledger correctly. It is the
    # control, not the experiment.
    accepted_risk_cash = _sum(all_row_risk_cash)
    sealed_shape = {
        "physical_gross_r": _sum(scoreable_gross_r),
        "execution_cost_r": _sum(all_row_cost_r),          # ALL rows (:1433)
        "physical_net_r": _sum(scoreable_net_r),
        "scoreable_net_cash": _sum(scoreable_pnl_cash),
        "accepted_risk_cash": accepted_risk_cash,          # ALL rows (:1426)
        "scoreable_accepted_risk_cash": _sum(scoreable_risk_cash),
    }
    # q divides scoreable cash by ACCEPTED risk cash — the all-rows denominator
    # (`analyze_b7_5_selection_sizing_matrix.py:1459`). Dividing by the scoreable
    # denominator instead gives a different, wrong number; both are reported so
    # the distinction cannot be lost again.
    sealed_shape["cash_per_accepted_risk_dollar"] = (
        sealed_shape["scoreable_net_cash"] / accepted_risk_cash
        if accepted_risk_cash else None
    )
    sealed_shape["cash_per_SCOREABLE_risk_dollar_not_the_sealed_q"] = (
        sealed_shape["scoreable_net_cash"] / sealed_shape["scoreable_accepted_risk_cash"]
        if sealed_shape["scoreable_accepted_risk_cash"] else None
    )

    # ---- (b) The experiment: prices vs ledger, over the SAME rows ------------
    covered_ledger = {
        "gross_r": _sum(t.ledger_gross_r for t in covered),
        "cost_r": _sum(t.ledger_cost_r for t in covered),
        "net_r": _sum(t.ledger_net_r for t in covered),
        "pnl_cash": _sum(t.ledger_pnl_cash for t in covered),
        "risk_cash": _sum(t.ledger_risk_cash for t in covered),
    }
    covered_recomputed = {
        "gross_r": _sum(t.recomputed_gross_r for t in covered),
        "cost_r": _sum(t.recomputed_cost_r for t in covered),
        "net_r": _sum(t.recomputed_net_r for t in covered),
        "pnl_cash": _sum(t.recomputed_pnl_cash for t in covered),
        "risk_cash": _sum(t.ledger_risk_cash for t in covered),
    }

    # ---- (c) The economically meaningful projection -------------------------
    # What would the arm's headline cash have been if every price-covered trade
    # used its price-derived R instead of the engine's? Uncovered rows keep the
    # ledger value, and the count of those is stated alongside so the number is
    # never mistaken for a full-window restatement.
    cash_delta_over_covered = _sum(t.cost_neutral_pnl_cash_delta for t in covered)
    projected = {
        "basis": (
            "NETTED: price-derived gross R on level exits, minus the "
            "expected_slippage_r the engine already charged on that same trade. "
            "Netting is required — the price-derived R embeds the realised slip, "
            "so leaving the modelled allowance in cost_r would charge it twice."
        ),
        "sealed_scoreable_net_cash": sealed_shape["scoreable_net_cash"],
        "cash_delta_from_price_derived_r_over_covered_rows": cash_delta_over_covered,
        "cash_delta_UPPER_BOUND_gap_not_netted": _sum(
            t.gross_gap_pnl_cash_delta for t in covered
        ),
        "cash_delta_if_costs_were_also_recomputed_NOT_the_headline": _sum(
            t.pnl_cash_delta for t in covered
        ),
        "projected_scoreable_net_cash": (
            sealed_shape["scoreable_net_cash"] + cash_delta_over_covered
        ),
        "rows_repriced": len(covered),
        "rows_left_at_ledger_value": scoreable_rows - len(covered),
        "projected_cash_per_accepted_risk_dollar": (
            (sealed_shape["scoreable_net_cash"] + cash_delta_over_covered)
            / accepted_risk_cash if accepted_risk_cash else None
        ),
        "is_a_full_window_restatement": (scoreable_rows - len(covered)) == 0,
    }

    # ---- Per-row disagreement profile ------------------------------------
    gross_deltas = [t.gross_r_delta for t in covered]
    disagreeing = [t for t in covered if abs(t.gross_r_delta) > 1e-9]
    by_close_reason: dict[str, list[TradeRecomputation]] = defaultdict(list)
    for trade in covered:
        by_close_reason[trade.close_reason].append(trade)

    close_reason_profile = {}
    for reason, trades in sorted(by_close_reason.items()):
        deltas = [t.gross_r_delta for t in trades]
        close_reason_profile[reason] = {
            "exit_family": trades[0].exit_family,
            "measures_gap_through": trades[0].exit_family == EXIT_FAMILY_LEVEL,
            "trades": len(trades),
            "disagreeing": sum(1 for d in deltas if abs(d) > 1e-9),
            "sum_gross_r_delta": _sum(deltas),
            "mean_gross_r_delta": _sum(deltas) / len(deltas) if deltas else 0.0,
            "min_gross_r_delta": min(deltas) if deltas else 0.0,
            "max_gross_r_delta": max(deltas) if deltas else 0.0,
        }

    # ---- The headline measurement: unmodelled exit gap-through -------------
    level_rows = [t for t in covered if t.exit_family == EXIT_FAMILY_LEVEL]
    mark_rows = [t for t in covered if t.exit_family != EXIT_FAMILY_LEVEL]
    gaps = [t.unmodelled_exit_gap_through_r for t in level_rows]
    adverse = [g for g in gaps if g < 0]
    favourable = [g for g in gaps if g > 0]
    # The engine's own allowance for this: a flat per-trade slippage constant
    # (`agent_config.yaml:740` selected_cell_default_expected_slippage_r: 0.02,
    # consumed at `broker_net_cost_engine.py:544-556`, summed at :578-584).
    #
    # Two denominators, and the second is the fair one. The charge is levied on
    # EVERY physical row, so the whole of it is available to absorb gap-through
    # wherever it occurs — testing only the level-row share would understate the
    # engine's allowance and overstate the finding.
    slippage_allowance = _sum(t.ledger_expected_slippage_r for t in level_rows)
    slippage_allowance_all_rows = _sum(all_row_expected_slippage_r)
    gap_through = {
        "definition": (
            "price-derived R minus booked R, on LEVEL exits only (stop / "
            "giveback / final target). Mark exits are excluded because the "
            "engine books the quote's own R there, making agreement tautological."
        ),
        "level_exit_rows": len(level_rows),
        "mark_exit_rows_excluded_as_tautological": len(mark_rows),
        "sum_gap_through_r": _sum(gaps),
        "mean_gap_through_r": _sum(gaps) / len(gaps) if gaps else 0.0,
        "adverse_rows": len(adverse),
        "adverse_sum_r": _sum(adverse),
        "adverse_mean_r": _sum(adverse) / len(adverse) if adverse else 0.0,
        "favourable_rows": len(favourable),
        "favourable_sum_r": _sum(favourable),
        "max_adverse_r": min(gaps) if gaps else 0.0,
        "max_favourable_r": max(gaps) if gaps else 0.0,
        # Is the engine's modelled slippage enough to cover it?
        "modelled_expected_slippage_r_total_over_level_rows": slippage_allowance,
        "modelled_expected_slippage_r_total_over_ALL_physical_rows":
            slippage_allowance_all_rows,
        "measured_net_gap_through_r": _sum(gaps),
        "modelled_allowance_covers_measured_gap": (
            slippage_allowance_all_rows >= abs(_sum(gaps)) if gaps else None
        ),
        "shortfall_r_vs_full_slippage_budget": (
            abs(_sum(gaps)) - slippage_allowance_all_rows if _sum(gaps) < 0 else 0.0
        ),
        # The measured figure counts ONLY rows carrying an executable close-side
        # quote. Level-family rows whose exit price is absent are refused, never
        # imputed, so the total is a LOWER BOUND on the true gap-through and the
        # excluded count is stated here rather than buried.
        "measured_total_is_a_lower_bound": True,
        "level_family_rows_excluded_for_absent_exit_price": sum(
            1 for r in refused if r.reason == "exit_price_absent"
            and classify_exit_family(r.close_reason) == EXIT_FAMILY_LEVEL
        ),
    }

    worst = sorted(covered, key=lambda t: -abs(t.gross_r_delta))[:15]

    return {
        "arm_window": name,
        "trade_ledger": str(trade_ledger),
        "row_census": {
            "physical_trade_rows": physical_rows,
            "scoreable_trade_rows": scoreable_rows,
            "unscoreable_trade_rows": unscoreable_rows,
            "recomputed_from_prices": len(covered),
            "refused": len(refused),
            "price_coverage_of_scoreable": (
                len(covered) / scoreable_rows if scoreable_rows else None
            ),
            "result_scoreable_flag_vs_analyzer_predicate_disagreements":
                scoreable_flag_disagreements,
        },
        "refusals": {
            "by_reason": dict(Counter(r.reason for r in refused).most_common()),
            "ledger_net_r_withheld": _sum(
                float(r.ledger_net_r) for r in refused if r.ledger_net_r is not None
            ),
            "ledger_pnl_cash_withheld": _sum(
                float(r.ledger_pnl_cash) for r in refused if r.ledger_pnl_cash is not None
            ),
            "rows": [asdict(r) for r in refused],
        },
        "f17_zero_price_census": dict(zero_price_fields),
        "unmodelled_exit_gap_through": gap_through,
        "sealed_shape_ledger_aggregates": sealed_shape,
        "projected_economics_if_price_derived_r_were_used": projected,
        "aggregates_over_covered_rows": {
            "ledger": covered_ledger,
            "recomputed_from_prices": covered_recomputed,
            "delta": {
                key: (
                    covered_recomputed[key] - covered_ledger[key]
                    if isinstance(covered_recomputed[key], (int, float))
                    and isinstance(covered_ledger[key], (int, float))
                    else None
                )
                for key in covered_ledger
            },
        },
        "exit_price_provenance_census": dict(
            Counter(t.exit_price_provenance for t in covered).most_common()
        ),
        "exit_family_census": dict(
            Counter(t.exit_family for t in covered).most_common()
        ),
        "per_row_agreement": {
            "trades_compared": len(covered),
            "trades_agreeing_within_1e-9": len(covered) - len(disagreeing),
            # gross_r is stored to 8 dp, so 1e-9 counts storage rounding as
            # disagreement. 1e-8 is the meaningful threshold.
            "trades_disagreeing_beyond_storage_precision_1e-8": sum(
                1 for d in gross_deltas if abs(d) > 1e-8
            ),
            "trades_disagreeing": len(disagreeing),
            "sum_gross_r_delta": _sum(gross_deltas),
            "mean_gross_r_delta": _sum(gross_deltas) / len(covered) if covered else 0.0,
            "max_abs_gross_r_delta": max((abs(d) for d in gross_deltas), default=0.0),
            "sum_abs_gross_r_delta": _sum(abs(d) for d in gross_deltas),
            "deltas_negative": sum(1 for d in gross_deltas if d < -1e-9),
            "deltas_positive": sum(1 for d in gross_deltas if d > 1e-9),
        },
        "by_close_reason": close_reason_profile,
        "largest_disagreements": [
            {
                "trade_id": t.trade_id,
                "symbol": t.symbol,
                "direction": t.direction,
                "trading_day": t.trading_day,
                "close_reason": t.close_reason,
                "terminal_r_source": t.terminal_r_source,
                "exit_price_provenance": t.exit_price_provenance,
                "entry_price": t.entry_price,
                "stop_loss": t.stop_loss,
                "exit_price": t.exit_price,
                "risk_distance": t.risk_distance,
                "ledger_gross_r": t.ledger_gross_r,
                "recomputed_gross_r": t.recomputed_gross_r,
                "gross_r_delta": t.gross_r_delta,
                "ledger_pnl_cash": t.ledger_pnl_cash,
                "recomputed_pnl_cash": t.recomputed_pnl_cash,
                "pnl_cash_delta": t.pnl_cash_delta,
            }
            for t in worst
        ],
        # Identity checks the analyzer performs, re-run here on the ledger's own
        # numbers. These SHOULD pass — the analyzer already enforces them. If one
        # fails, the disagreement is in the ledger and not in this reducer.
        "ledger_internal_identities": _ledger_identity_report(covered),
    }


def _ledger_identity_report(trades: list[TradeRecomputation]) -> dict:
    """Re-run the analyzer's own per-row identities against the ledger values."""
    pnl_violations = [
        t.trade_id for t in trades
        if not math.isclose(
            t.ledger_pnl_cash, t.ledger_risk_cash * t.ledger_net_r,
            rel_tol=1e-6, abs_tol=1e-6,
        )
    ]
    net_violations = [
        t.trade_id for t in trades
        if not math.isclose(
            t.ledger_net_r, t.ledger_gross_r - t.ledger_cost_r,
            rel_tol=1e-8, abs_tol=1e-8,
        )
    ]
    cost_violations = [
        t.trade_id for t in trades
        if not math.isclose(
            t.ledger_cost_r, t.recomputed_cost_r, rel_tol=1e-8, abs_tol=1e-8,
        )
    ]
    return {
        "pnl_cash_eq_risk_cash_times_net_r_at_1e-6": {
            "checked": len(trades), "violations": len(pnl_violations),
            "sample": pnl_violations[:5],
        },
        "net_r_eq_gross_r_minus_cost_r_at_1e-8": {
            "checked": len(trades), "violations": len(net_violations),
            "sample": net_violations[:5],
        },
        "cost_r_eq_sum_of_components_at_1e-8": {
            "checked": len(trades), "violations": len(cost_violations),
            "sample": cost_violations[:5],
        },
    }


# ---------------------------------------------------------------------------
# Reconciliation against the sealed matrix audit
# ---------------------------------------------------------------------------

SEALED_ECONOMICS_KEYS = (
    "physical_gross_r",
    "execution_cost_r",
    "physical_net_r",
    "scoreable_net_cash",
    "scoreable_accepted_risk_cash",
    "cash_per_accepted_risk_dollar",
    "scoreable_trade_rows",
    "physical_trade_rows",
    "unscoreable_trade_rows",
)


def load_sealed_economics(matrix_audit: Path) -> dict[str, dict]:
    """Extract each arm's sealed `economics` block from the matrix audit JSON."""
    data = json.loads(matrix_audit.read_text())
    out: dict[str, dict] = {}
    for arm, block in (data.get("arms") or {}).items():
        economics = block.get("economics") or {}
        out[arm] = {key: economics.get(key) for key in SEALED_ECONOMICS_KEYS}
    return out


def reconcile_with_sealed(result: dict, sealed: dict) -> dict:
    """Compare this reducer's output against the arm's sealed economics block."""
    census = result["row_census"]
    sealed_shape = result["sealed_shape_ledger_aggregates"]
    projected = result["projected_economics_if_price_derived_r_were_used"]

    def _cmp(sealed_value, ours, *, tol=1e-6):
        if sealed_value is None or ours is None:
            return {"sealed": sealed_value, "ours": ours, "delta": None, "agrees": None}
        delta = ours - sealed_value
        return {
            "sealed": sealed_value,
            "ours": ours,
            "delta": delta,
            "agrees": abs(delta) <= tol,
        }

    return {
        "row_counts": {
            "physical_trade_rows": _cmp(
                sealed.get("physical_trade_rows"), census["physical_trade_rows"], tol=0,
            ),
            "scoreable_trade_rows": _cmp(
                sealed.get("scoreable_trade_rows"), census["scoreable_trade_rows"], tol=0,
            ),
            "unscoreable_trade_rows": _cmp(
                sealed.get("unscoreable_trade_rows"), census["unscoreable_trade_rows"], tol=0,
            ),
        },
        # CONTROL. Re-sums the ledger in the sealed audit's own row-set
        # conventions. Agreement here proves this reducer reads the evidence
        # correctly; it proves nothing about economic correctness, because the
        # analyzer sums the same fields the same way.
        "control_ledger_resum_vs_sealed": {
            key: _cmp(sealed.get(key), sealed_shape.get(key))
            for key in ("physical_gross_r", "execution_cost_r", "physical_net_r",
                        "scoreable_net_cash", "scoreable_accepted_risk_cash",
                        "cash_per_accepted_risk_dollar")
        },
        # EXPERIMENT. What the sealed headline becomes when every price-covered
        # trade uses its price-derived R. Not a like-for-like "sealed vs ours"
        # comparison — it is the sealed number plus a measured correction, with
        # the uncovered row count stated.
        "experiment_price_derived_projection": {
            "sealed_scoreable_net_cash": sealed.get("scoreable_net_cash"),
            "projected_scoreable_net_cash": projected["projected_scoreable_net_cash"],
            "cash_delta": projected["cash_delta_from_price_derived_r_over_covered_rows"],
            "sealed_q": sealed.get("cash_per_accepted_risk_dollar"),
            "projected_q": projected["projected_cash_per_accepted_risk_dollar"],
            "rows_repriced": projected["rows_repriced"],
            "rows_left_at_ledger_value": projected["rows_left_at_ledger_value"],
            "is_a_full_window_restatement": projected["is_a_full_window_restatement"],
        },
        "price_coverage_of_scoreable": census["price_coverage_of_scoreable"],
        "coverage_is_complete": census["refused"] == 0,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _fmt(value, width=16, places=6) -> str:
    if value is None:
        return "—".rjust(width)
    if isinstance(value, float):
        return f"{value:>{width},.{places}f}"
    return str(value).rjust(width)


def render_text(report: dict) -> str:
    lines: list[str] = []
    add = lines.append
    add("=" * 100)
    add("SHADOW REDUCER v2 — per-trade R recomputed from prices, zero engine imports")
    add("=" * 100)

    for result in report["arm_windows"]:
        name = result["arm_window"]
        census = result["row_census"]
        agreement = result["per_row_agreement"]
        add("")
        add(f"### {name}")
        add(f"  ledger: {Path(result['trade_ledger']).name}")
        add(f"  rows: physical={census['physical_trade_rows']} "
            f"scoreable={census['scoreable_trade_rows']} "
            f"unscoreable={census['unscoreable_trade_rows']} "
            f"recomputed={census['recomputed_from_prices']} "
            f"refused={census['refused']}")
        coverage = census["price_coverage_of_scoreable"]
        add(f"  price coverage of scoreable rows: "
            f"{coverage:.4%}" if coverage is not None else "  price coverage: n/a")
        if result["refusals"]["by_reason"]:
            add(f"  refusal reasons: {result['refusals']['by_reason']}")
            add(f"  ledger net_r withheld by refusals: "
                f"{result['refusals']['ledger_net_r_withheld']:.8f}")
        if result["f17_zero_price_census"]:
            add(f"  F17 exact-0.0 price census: {result['f17_zero_price_census']}")
        else:
            add("  F17 exact-0.0 price census: none")

        add("")
        add("  [experiment] over the price-covered rows only — ledger vs prices:")
        add(f"  {'quantity':<34}{'ledger':>18}{'from prices':>18}{'delta':>18}")
        agg = result["aggregates_over_covered_rows"]
        for key in ("gross_r", "cost_r", "net_r", "pnl_cash", "risk_cash"):
            add(f"  {key:<34}{_fmt(agg['ledger'].get(key), 18, 8)}"
                f"{_fmt(agg['recomputed_from_prices'].get(key), 18, 8)}"
                f"{_fmt(agg['delta'].get(key), 18, 8)}")

        add("")
        add(f"  per-row: {agreement['trades_disagreeing']} of "
            f"{agreement['trades_compared']} disagree beyond 1e-9 "
            f"({agreement['deltas_negative']} negative, "
            f"{agreement['deltas_positive']} positive)")
        add(f"  sum gross_r delta = {agreement['sum_gross_r_delta']:.8f}   "
            f"max |delta| = {agreement['max_abs_gross_r_delta']:.8f}")

        identities = result["ledger_internal_identities"]
        add("  ledger internal identities (the analyzer's own checks, re-run): "
            + ", ".join(
                f"{k.split('_at_')[0]}={v['violations']}/{v['checked']}"
                for k, v in identities.items()
            ))

        if not result.get("sealed_reconciliation"):
            add("")
            add(f"  [no sealed comparand] {result.get('no_sealed_comparand_reason', '')}")
        if result.get("sealed_reconciliation"):
            rec = result["sealed_reconciliation"]
            add("")
            add("  [control] this reducer's ledger re-sum vs the SEALED matrix audit:")
            for key, cmp in rec["control_ledger_resum_vs_sealed"].items():
                mark = "OK " if cmp["agrees"] else ("?? " if cmp["agrees"] is None else "!! ")
                add(f"    {mark}{key:<34}sealed={_fmt(cmp['sealed'], 16, 8)}"
                    f"  ours={_fmt(cmp['ours'], 16, 8)}  delta={_fmt(cmp['delta'], 16, 8)}")
            exp = rec["experiment_price_derived_projection"]
            add("")
            add("  [experiment] sealed headline vs price-derived projection:")
            add(f"    scoreable_net_cash  sealed={_fmt(exp['sealed_scoreable_net_cash'], 16, 6)}"
                f"  projected={_fmt(exp['projected_scoreable_net_cash'], 16, 6)}"
                f"  delta={_fmt(exp['cash_delta'], 16, 6)}")
            add(f"    q                   sealed={_fmt(exp['sealed_q'], 16, 9)}"
                f"  projected={_fmt(exp['projected_q'], 16, 9)}")
            add(f"    rows repriced={exp['rows_repriced']}  "
                f"left at ledger value={exp['rows_left_at_ledger_value']}  "
                f"full restatement={exp['is_a_full_window_restatement']}")

    add("")
    add("=" * 100)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--arm-window", action="append", required=True, metavar="NAME=PATH",
        help="arm-window name and its TRADE_LEDGER.jsonl path; repeatable",
    )
    parser.add_argument("--matrix-audit", type=Path, default=None,
                        help="sealed MATRIX_AUDIT.json to reconcile against")
    parser.add_argument(
        "--sealed-arm", action="append", default=[], metavar="WINDOW=ARM",
        help=(
            "bind an arm-window to an arm in --matrix-audit, e.g. JAN_S0R0=S0R0. "
            "Binding is EXPLICIT and never inferred: an earlier revision matched "
            "the arm token as a substring of the window name and silently "
            "reconciled the April S1R1 partial against JANUARY's S1R1 seal, "
            "which is a different window with no audit of its own. A window "
            "with no binding is reduced and reported without reconciliation."
        ),
    )
    parser.add_argument("--out", type=Path, default=None, help="write the JSON report here")
    parser.add_argument("--json", action="store_true", help="print JSON instead of text")
    args = parser.parse_args(argv)

    sealed_by_arm: dict[str, dict] = {}
    if args.matrix_audit:
        sealed_by_arm = load_sealed_economics(args.matrix_audit)

    binding: dict[str, str] = {}
    for spec in args.sealed_arm:
        if "=" not in spec:
            parser.error(f"--sealed-arm expects WINDOW=ARM, got {spec!r}")
        window, _, arm = spec.partition("=")
        binding[window] = arm
    if binding and not args.matrix_audit:
        parser.error("--sealed-arm requires --matrix-audit")

    # A binding whose WINDOW matches no --arm-window must be a hard error, never
    # a silent drop. Silently discarding it downgrades a reconciled run to an
    # unreconciled one AND prints "no --sealed-arm binding was given for this
    # window", which is false — the operator gave one and it was thrown away.
    window_names = {spec.partition("=")[0] for spec in args.arm_window}
    unused = sorted(set(binding) - window_names)
    if unused:
        parser.error(
            f"--sealed-arm names no such arm-window: {unused}. "
            f"Known windows: {sorted(window_names)}"
        )

    results = []
    for spec in args.arm_window:
        if "=" not in spec:
            parser.error(f"--arm-window expects NAME=PATH, got {spec!r}")
        name, _, raw_path = spec.partition("=")
        path = Path(raw_path)
        if not path.is_file():
            parser.error(f"not a file: {path}")
        result = reduce_arm_window(name, path)
        arm = binding.get(name)
        if arm is not None:
            if arm not in sealed_by_arm:
                parser.error(
                    f"--sealed-arm {name}={arm}: arm {arm!r} is not in "
                    f"{args.matrix_audit} (has {sorted(sealed_by_arm)})"
                )
            result["sealed_arm"] = arm
            result["sealed_reconciliation"] = reconcile_with_sealed(result, sealed_by_arm[arm])
        else:
            result["sealed_arm"] = None
            result["sealed_reconciliation"] = None
            result["no_sealed_comparand_reason"] = (
                "no --sealed-arm binding was given for this window; it is reduced "
                "and reported, but nothing on disk validates or contradicts it"
            )
        results.append(result)

    # Bind the receipt to the code that produced it. Without this nothing on
    # disk connects an output to a tool revision, and a stale receipt is
    # indistinguishable from a current one.
    try:
        tool_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    except OSError:
        tool_sha256 = None

    report = {
        "schema": SCHEMA,
        "tool": "docs/audits/fable5-vision-audit-20260725/phase1/shadow_reducer_v2.py",
        "tool_sha256": tool_sha256,
        "engine_imports": [],
        "matrix_audit": str(args.matrix_audit) if args.matrix_audit else None,
        "arm_windows": results,
    }

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n")

    print(json.dumps(report, indent=1, sort_keys=True) if args.json else render_text(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
