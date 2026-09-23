# Wave 21 cost-truth closure

Status: **source-backed implementation closure; no strategy replay result and no activation
authority.** The machine-readable receipt is `COST_TRUTH_CLOSURE_V1.json`; regenerate it
offline with
`python3 docs/audits/fable5-vision-audit-20260725/phase21/cost/audit_cost_truth.py`
from the repository root.

## Result-moving component facts

On the fixed, hash-bound 22,354-row AQ trade substrate, 18,592 rows (83.1708%) have every
new input and 3,762 are `NOT_EVALUABLE`; none is filled with zero or a pooled default.
On the 18,592-row intersection:

- using elapsed wall-clock time instead of tradable-bar hours adds **61.695405 R** total
  cost (**+0.003318385 R/trade**) and changes 1,168 rows;
- historical FX for cash-per-lot commission plus price-domain slippage changes cost by **-118.531900 R**
  (**-0.006375425 R/trade**) versus the same corrected-holding comparator with the modern
  FX snapshot and constant-in-R slippage;
- that second comparison moves 11 cached-gross trade net signs. It is a component A/B,
  not a new strategy result;
- 2,752 AQ rows land in `SCHEDULE` spread eras. All 2,752 are now undecidable; 2,386 of
  them otherwise have complete inputs and carry `MODELLED` unless strict decidability is
  requested, in which case they refuse;
- 79 priceable rows predate 2007. The corrected 1987-2006 DST rule changes swap R on zero
  of those particular rows, while still removing the timestamp defect. Dates before 1987
  fail closed.

## Behavioral contract closed

- A non-USD-profit cash-per-lot commission is converted with the last D1 bar whose
  **completion UTC is strictly earlier** than entry UTC; no current snapshot fallback
  exists. Measured-zero commission is identically zero, while notional-bp numerator and
  denominator FX cancel exactly in R, so neither consumes that D1 input. Spread, slippage
  and swap are price displacement divided directly by stop and consume no cash conversion.
- FX, slippage and symbol-authority compact inputs are verified against the repository-
  contained cost-input manifest before every cache lookup; a same-path byte change fails
  closed rather than returning a retained parse.
- Slippage is an exact-account, exact-profile-symbol adverse displacement in price units
  divided by the trade's stop. Missing cells are `NOT_EVALUABLE`.
- Profile symbol aliases are read from the two hash-bound live YAML profiles. Punctuation,
  `_cash`, undeclared artifact membership and direct-record shortcuts grant no identity.
- A quote-side gross excludes an additional spread deduction only after the source bytes,
  SHA-256, physical row, trade identity, account, exact profile symbol, instant, side,
  bid/ask, fill, stop and gross basis reconcile. The observed spread may differ from a model
  percentile; it is attributed once and deducted zero additional times.
- Complete totals preserve the FD identity, in order:
  `spread + expected_slippage + swap + commission`. The shared packet completeness API
  emits `NOT_EVALUABLE` when any finite source witness or that identity is absent.
- `pretrade_expected_cost` is a Selector/Scheduler estimate only. Final simulated
  economics accepts only a COMPLETE `post_lifecycle_component_cost` packet built from
  actual entry/exit elapsed time and hash-bound quote geometry; it reuses no pretrade
  components. Expected slippage remains honestly source-bound, so the packet explicitly
  says broker-realized cost is `NOT_EVALUABLE_NO_BROKER_DEAL_COMPONENTS`.

## Remaining captures

The exact requirements are structured in the receipt. The economically material gaps are:
reconciled price-domain slippage for the 3,762 AQ rows (including redacted_account `USOUSD` and
`UKOUSD`); decision-time/era spread observations for `SCHEDULE` cells; date-indexed
historical swap schedules; FX outside the captured strictly-completed D1 extent where a
cash-per-lot conversion consumes it; a fully
bound quote-geometry row wherever gross is fill-anchored; and broker-calendar evidence
before 1987. Until those inputs exist, the affected rows remain `NOT_EVALUABLE`.
