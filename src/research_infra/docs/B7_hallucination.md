# B7 — Hallucination Rate Systematic Measurement

**Status:** Phase 1 research deliverable (research kickoff 2026-04-26).
**Cost:** $0 — pure-Python file system + regex + structured-record join.
**Branch:** `feat/research-b7-hallucination` (v1) + `feat/research-f13-b7-v2-role-stratified` (v2).
**Owner module:** `src/research_infra/hallucination_measurement.py`.
**CLI driver:** `scripts/research/run_b7_hallucination.py`.

> **Recommended metric for K54 + Phase 2 prompt research:** the
> **MSO-grounded hallucinated_pct** from B7-v2 (F13). It is the
> apples-to-apples per-instrument comparison; v1's all-roles rate
> conflates real grounding failures with a TP forward-derivation
> measurement artifact (see "F13 — role-stratified v2" below).

## What this measures

For every historical AI evaluation we have on disk, we compare every
price the AI cited (in its trade parameters, in its reasoning JSON
sub-fields, and in its free-text explanation) against the MSO
`raw_data` the AI was given. Each cited price is classified into one of:

* **ACCURATE** — the price exists in the MSO at the role the AI claimed,
  within `--tolerance-ticks` (default 5).
* **MISATTRIBUTED** — the price exists in the MSO but at a *different*
  role/label (e.g. AI called a "swing high" an "OB top").
* **HALLUCINATED** — the price has NO match anywhere in the MSO
  (within tolerance), at any role.

Aggregations are emitted per-instrument, per-period (calendar month +
H1/H2-2026 partition), per-framework, and per-role.

## Why it matters (decay decomposition)

A1 (`research/decay_diagnostic/A1_dumb_baseline/`) has confirmed that
the H2-2026 XAUUSD WR decay (64.5% H1 → 24.0% H2) is **AI-side, not
regime-side**: the mechanical OB-pullback baseline holds steady while
the AI side collapses. B7 is one of the B-series tasks that decomposes
the AI-side collapse into concrete failure modes:

| Task | Hypothesis |
|------|------------|
| B7   | The AI is hallucinating prices not in the MSO. |
| B12  | The AI's confidence score is mis-calibrated relative to outcomes. |
| B14  | Walk-level decisions diverge from realized R (see memory). |
| K53  | An anti-pattern classifier on losers replicates OOS. |

If B7 finds H1→H2 hallucination spiked, hallucination is the (or *a*)
decay mechanism and we feed the answer into K54 (see "K54 handoff"
below). If hallucination stayed flat across H1→H2, we **rule it out**
and proceed to B12/B14/K53.

## Inputs (what's on disk for B7)

The work this task can do is bounded by what got persisted alongside
the AI evaluations.

### Precise arm — `knowledge_base/trade_records/{SYMBOL}/*.json`

148 records as of 2026-04-26 (CANDIDATEs only; April 2026 only).
Each record carries the FULL MSO at decision time under `mso`, the
FULL AI response under `ai_response`, and pre-paired `mso_value` /
`ai_value` blocks under
`decision_pipeline.level2_verification.checks`. This is the
source-of-truth for paired comparison — every cited price has a known
MSO ground-truth.

We extract:

* **trade_parameters**: `entry_price`, `stop_loss`, `take_profit_1/2/3`
* **reasoning.h1_setup**: `poi_price_level` (role-typed by `poi_type`),
  `explanation` regex
* **reasoning.daily_bias**: `protected_swing_level`
* **reasoning.liquidity_sweep**: `sweep_price`
* **reasoning.overall_reasoning**: regex over the free text

### Coarse arm — `knowledge_base/live_evaluations/{SYMBOL}/*.jsonl`

1,240 records as of 2026-04-26 (NO_TRADE + CANDIDATE; 2026-04-06 →
2026-04-24 only). These are **flat**: they carry `overall_reasoning` +
`no_trade_reason` strings but **no MSO**. We cannot reconstruct paired
ground-truth from them alone.

Substitute MSO: a 168-bar H1 lookback window from
`data/historical_2026/{SYMBOL}_H1.csv`. We treat any cited price
within tolerance of any candle's high / low / close in the window as
ACCURATE; otherwise HALLUCINATED. The coarse arm cannot detect
MISATTRIBUTED (no role labels in the candle stand-in).

The coarse arm is **opt-out** via `--no-live-evaluations`. The CLI
report tags each row with its `record_source` so an analyst can
slice precise-only.

## Tolerance choice

Default: **5 ticks**, with the per-instrument tick table mirroring
`src.research_infra.dumb_baseline`:

| Instrument | Tick | 5-tick tolerance |
|---|---:|---:|
| XAUUSD | 0.01 | $0.05 |
| XAGUSD | 0.001 | $0.005 |
| US30_cash, NAS100 | 0.01 | $0.05 |
| USDJPY, GBPJPY, EURJPY | 0.001 | 0.005 (≈ 0.5 pip) |
| GBPUSD, EURUSD | 0.00001 | 0.00005 (≈ 0.5 pip) |

Why 5: it's the broker's minimum-quoted-precision floor. Tighter would
over-flag rounding-induced mismatches between the AI's quoted price
(3-5 dp) and the broker's tick grid; looser would hide real
hallucinations on tight-FX pairs. The CLI flag `--tolerance-ticks` lets
you sweep this.

The default mirrors `verification.sl_beyond_ob_tick_floor` in
`agent_config.yaml`, which is the closest production-side analogue.

## Classification rules (canonical)

For each cited price `p` with role `r` and instrument symbol `s`:

```
tick = TICK_SIZE[s]
tol  = tolerance_ticks * tick

# Step 1: same-role match
if any v in MSO_PRICE_SET.by_role[r] where abs(p - v) <= tol:
    return ACCURATE

# Step 2: synthesized roles (entry/sl/tp don't appear in MSO directly)
if r in {entry_price, stop_loss, take_profit}:
    if any v in MSO_PRICE_SET.all_values where abs(p - v) <= tol:
        return ACCURATE

# Step 3: cross-role match
if any v in MSO_PRICE_SET (any role != r) where abs(p - v) <= tol:
    return MISATTRIBUTED

return HALLUCINATED
```

`MSO_PRICE_SET` is built by `build_mso_price_set` over:

* every TF's `order_blocks[*].high`/`.low`/`(high+low)/2`/`.open`/`.close`
* every TF's `breaker_blocks[*].high`/`.low`/midpoint
* every TF's `fair_value_gaps[*].high`/`.low`/midpoint
* every TF's `swings[*].price` (typed `high`/`low`)
* every TF's last-candle `close`/`high`/`low` (→ `current_price`)
* `session_levels.{asian_high,asian_low,pdh,pdl,session_high,session_low,london_high,london_low}`
* `equal_highs[*].price` (→ `swing_high`); `equal_lows[*].price` (→ `swing_low`)

For the coarse arm, the price set is built from raw OHLCV with
candle high/low/close pushed to a generic `any` bucket.

## Realized-R join (walk-level + outcome discipline)

Per memory `feedback_walk_level_evidence_not_predictive`, walk-level
evidence on its own is not predictive of realized R. Hallucination is
necessarily a walk-level metric (it's about behavior, not outcome),
but we still surface realized R per CAND when it's joinable so the
H1→H2 verdict carries both signals.

The CLI emits `rows.jsonl` with `realized_r` populated when
`decision_pipeline.final_outcome.r_multiple` or `exit.r_multiple` is
present. Downstream analysis can group by classification × outcome to
test whether hallucinated CANDs lose more than accurate CANDs (this is
not a B7 deliverable — it's K54+ tooling).

## Coverage caveats

1. **No H1-2026 evaluation data on disk.** Both the trade_records and
   live_evaluations corpora start at April 2026. The H1→H2 delta we
   surface is between **early-April-2026 (calendar H1)** and **mid-April-
   2026 (calendar H2)** if the dataset spans both — but in practice
   April only is available. The first published `rates.json` will report
   `h1_h2_delta_pp = None` until an H1-2026 backfill is sourced.
   - Backfill candidates: `logs/agent_*.log` (parsing required),
     batch_sessions in `knowledge_base_backtest/sessions/`.
   - Backfill is OUT OF SCOPE for B7 v1; tracked as a K54 sub-task.

2. **trade_records is CANDIDATE-only.** The hallucination rate on
   NO_TRADE evaluations is best read off the live_evaluations coarse
   arm. Mixing in the same numerator is dilutional — the CLI emits
   per-source rows.jsonl so the analyst can slice.

3. **Regex coverage is finite.** The regex set in
   `EXPLANATION_PATTERNS` covers the most common AI phrasings observed
   in the corpus (current price, OB pair, breaker pair, FVG pair, swing
   high/low, sweep, equilibrium). It does NOT cover every possible
   phrasing — e.g. "the resistance at 4720" is not captured. We
   under-extract on purpose to avoid false-classifying counts (5 BOS,
   3 candles) as prices. The regex set is easy to extend.

4. **OHLCV stand-in for coarse arm cannot detect MISATTRIBUTED.** A
   candle high IS both a swing high and (potentially) an OB top in the
   same value, so role-fidelity isn't separable without an MSO. The
   coarse arm only emits ACCURATE / HALLUCINATED.

## F13 — role-stratified v2 (B7-v2)

**Branch:** `feat/research-f13-b7-v2-role-stratified`.
**Outputs:** `research/ai_behavior/B7_hallucination_v2_role_stratified/`
(`rates_all.json`, `rates_mso_grounded.json`, `report_by_role.md`).

### Why v2

B7-v1 (commit `9611c58`) measured per-instrument hallucination but
flagged `take_profit` at **38.5%** hallucinated — the most-hallucinated
role in the v1 by-role table. This is a definitional artifact: TP is
forward-projected (`entry + N × R`), it is not drawn from the MSO, so
"hallucinated" relative to the MSO is nonsense for that role. F9
(commit `cffb99c`) confirmed the artifact accounts for **40.3% of
US30's headline 23.4% hallucination rate**.

F13 stratifies every cited price into one of three role classes via
`ROLE_TAXONOMY`:

| Role class | Members | Interpretation |
|---|---|---|
| **MSO_GROUNDED** | `current_price`, `entry_price`, `stop_loss`, `ob_high`, `ob_low`, `ob_mid`, `ob_body`, `breaker_high`, `breaker_low`, `breaker_mid`, `fvg_high`, `fvg_low`, `fvg_mid`, `swing_high`, `swing_low`, `protected_swing`, `sweep_price`, `liquidity_high`, `liquidity_low` | Should match MSO data. A `hallucinated` verdict is a **real grounding failure**. |
| **FORWARD_DERIVED** | `take_profit`, `trailing_stop_target` | Computed from entry + R or future targets. Not expected to match MSO; "hallucination" measurement is meaningless. |
| **AMBIGUOUS** | `equilibrium` | Case-by-case. Excluded from the strict MSO-grounded rate. |

Unknown / novel roles default to AMBIGUOUS so they do not silently
inflate the MSO-grounded rate.

### v2 metric — MSO-grounded hallucinated_pct

The single per-instrument number to use for K54 + Phase 2 prompt
research is `by_instrument_mso_grounded[*].hallucinated_pct`. It is
emitted alongside the v1 metric so any analysis can compare both.

The CLI defaults to `--by-role-class` ON; the v2 artifacts
(`rates_mso_grounded.json`, `report_by_role.md`) are always present
for new runs. The v1 `rates.json` + `report.md` paths remain stable
for backward compatibility.

### Per-instrument old-vs-new (April 2026 corpus, tolerance=5 ticks)

| Instrument | All-roles rate (v1) | MSO-grounded rate (v2) | Delta |
|---|---:|---:|---:|
| US30_cash | 23.4% | **15.5%** | -7.92pp |
| XAUUSD | 13.1% | **5.7%** | -7.40pp |
| GBPJPY | 10.7% | **8.8%** | -1.84pp |
| USDJPY | 4.3% | **3.4%** | -0.91pp |
| GBPUSD | 2.3% | **0.8%** | -1.42pp |

Per-instrument ranking: 4 of 5 instruments rank the same; **GBPJPY**
and **XAUUSD** swap order (XAU drops below GBPJPY in the v2 view
because XAU's all-roles rate was inflated by FORWARD_DERIVED TP
hallucinations more than GBPJPY's). Conclusion: the v1 all-roles
ranking was NOT apples-to-apples; the v2 MSO-grounded ranking is.

### v2 implementation summary

* `ROLE_TAXONOMY: Dict[str, RoleClass]` — canonical role → class map.
* `role_class_of(role) -> RoleClass` — defensive accessor with
  AMBIGUOUS default.
* `PriceClassification.role_class` — auto-derived in `__post_init__`
  from the role at construction time.
* `HallucinationReport.by_instrument_role_class` — flat list of
  per-instrument × per-role-class rows. Every report carries this
  field; v1-shape callers consuming `.by_instrument` are unaffected.
* `HallucinationReport.by_instrument_mso_grounded` — convenience
  filter to the MSO_GROUNDED rows only.
* `measure_hallucination_rate_by_role_class(seq, tolerance_ticks)` —
  convenience wrapper returning a 2-deep dict
  `{instrument: {role_class: row}}`.
* CLI `--by-role-class` flag (default ON) emits the v2 artifacts.

### Backward compatibility

The original `measure_hallucination_rate(seq, tolerance_ticks)`
signature is unchanged; the v1 schema (`by_instrument`, `by_role`, …)
is still emitted with identical field shape. The v2 fields appear
additively on the same `HallucinationReport`. The 20 v1 tests still
pass; 6 new v2 tests cover taxonomy completeness, role classification
correctness, MSO-grounded-only rate calculation, auto-derivation in
`PriceClassification`, and backward-compat round-trip of both schemas.

## Out of scope

* **Re-running AI on historical CANDs.** This is Phase 2 A4 and
  requires API spend. Held for CEO authorization.
* **Modifying production code.** B7 is observational only.
* **Proposing system changes.** That's K54 handoff (see below).

## K54 handoff (post-Monday)

This module **measures**. K54 (the post-Monday research kickoff)
decides what to do with the measurement. Candidate K54 subtasks:

1. **Hallucination shadow logger.** Add a per-evaluation logger that
   runs the same classification at decision time and writes to
   `shadow_logs/hallucination_classifications.jsonl`. Additive, log-
   only — does not block trades. Telegram-alert on rate spikes
   (rolling-50, threshold tbd).
2. **Tool-use grounding step.** Wire `src/components/ai_tools/`
   (currently scaffolded but not wired per `research/tool_use_grounding/
   DESIGN.md`) so the AI must call `verify_ob_exists(price)` before
   citing it. Tool returns `True` only if the price matches an OB in
   the MSO within tolerance. Costs ≈ 1 extra round-trip per CAND;
   measurable in canary.
3. **Tighten L2 verifier.** `h1_poi_exists` already checks AI POI vs
   MSO OBs but with loose `near` semantics. K54 can tighten to
   bit-exact match on the OB high/low pair when the role is `OB`.
4. **Backfill H1-2026 evaluation stream.** Parse `logs/agent_*.log`
   into a synthetic live_evaluations stream, OR reseed from
   batch_sessions, so the H1→H2 delta reported here is meaningful.

## File map

| File | Purpose |
|---|---|
| `src/research_infra/hallucination_measurement.py` | Pure-Python module: parse, classify, aggregate (v1 + v2 role-stratified). |
| `scripts/research/run_b7_hallucination.py` | CLI driver — emits rates.json, rows.jsonl, report.md (+ rates_mso_grounded.json, report_by_role.md when `--by-role-class` is on, default). |
| `tests/research_infra/test_hallucination_measurement.py` | 26-test pytest suite (parse, classify, aggregate, OHLCV provider, edge cases + 6 F13 v2 tests for taxonomy, role-class auto-derivation, per-class rates, backward compat). |
| `src/research_infra/docs/B7_hallucination.md` | This document. |
| `research/ai_behavior/B7_hallucination/` | v1 output sink. |
| `research/ai_behavior/B7_hallucination_v2_role_stratified/` | v2 (F13) output sink — has both v1 + v2 artifacts. |

## Reproducibility

```bash
# F13 — role-stratified (default ON for new runs)
python scripts/research/run_b7_hallucination.py \
    --output-dir research/ai_behavior/B7_hallucination_v2_role_stratified

# v1-only legacy mode (no role-stratified outputs)
python scripts/research/run_b7_hallucination.py \
    --output-dir research/ai_behavior/B7_hallucination \
    --no-by-role-class

# Sweep tolerance
python scripts/research/run_b7_hallucination.py \
    --output-dir research/ai_behavior/B7_hallucination_tol3 \
    --tolerance-ticks 3

# Precise-arm only
python scripts/research/run_b7_hallucination.py \
    --output-dir research/ai_behavior/B7_hallucination_precise \
    --no-live-evaluations
```

```bash
# Tests
pytest tests/research_infra/test_hallucination_measurement.py -v
```
