# B7-v2 (F13) — Role-stratified hallucination rates

Harness: `B7-v2` (additive on `B7-v1`) · tolerance_ticks: 5 · records scanned: 1390 · records with classifications: 316

**Why v2.** B7-v1 (`9611c58`) measured per-instrument hallucination rates but flagged TP at 38.5% hallucinated — a definitional artifact, since TP is forward-projected (entry + N×R), NOT drawn from the MSO. F9 (`cffb99c`) confirmed that 40.3% of US30's headline 23.4% rate came from this artifact. F13 stratifies cited prices into `MSO_GROUNDED` (real grounding-failure loci), `FORWARD_DERIVED` (forward-projected; hallucination measurement meaningless here), and `AMBIGUOUS` (case-by-case). The MSO-grounded rate is the apples-to-apples per-instrument comparison.

## Per-instrument hallucination — old vs new methodology

| Instrument | All-roles rate (original) | MSO-grounded rate (new) | n MSO-grounded | delta (pp) |
|---|---:|---:|---:|---:|
| US30_cash | 23.4% | 15.5% | 239 | -7.92 |
| XAUUSD | 13.1% | 5.7% | 141 | -7.40 |
| GBPJPY | 10.7% | 8.8% | 317 | -1.84 |
| USDJPY | 4.3% | 3.4% | 446 | -0.91 |
| GBPUSD | 2.3% | 0.8% | 236 | -1.42 |

## Per-instrument × per-role-class detailed breakdown

| Instrument | Role class | n_evals | n_prices | accurate% | hallucinated% | misattributed% |
|---|---|---:|---:|---:|---:|---:|
| GBPJPY | FORWARD_DERIVED | 39 | 39 | 74.4% | 25.6% | 0.0% |
| GBPJPY | MSO_GROUNDED | 73 | 317 | 84.2% | 8.8% | 6.9% |
| GBPUSD | AMBIGUOUS | 1 | 1 | 100.0% | 0.0% | 0.0% |
| GBPUSD | FORWARD_DERIVED | 28 | 28 | 85.7% | 14.3% | 0.0% |
| GBPUSD | MSO_GROUNDED | 52 | 236 | 97.0% | 0.8% | 2.1% |
| US30_cash | FORWARD_DERIVED | 26 | 26 | 3.8% | 96.2% | 0.0% |
| US30_cash | MSO_GROUNDED | 49 | 239 | 81.2% | 15.5% | 3.3% |
| USDJPY | AMBIGUOUS | 3 | 3 | 100.0% | 0.0% | 0.0% |
| USDJPY | FORWARD_DERIVED | 43 | 43 | 86.0% | 14.0% | 0.0% |
| USDJPY | MSO_GROUNDED | 111 | 446 | 96.0% | 3.4% | 0.7% |
| XAUUSD | FORWARD_DERIVED | 12 | 12 | 0.0% | 100.0% | 0.0% |
| XAUUSD | MSO_GROUNDED | 31 | 141 | 93.6% | 5.7% | 0.7% |

## Strategic verdict

- US30's apparent hallucination rate before F13: **23.4%**. After stripping the FORWARD_DERIVED TP artifact: **15.5%** (artifact contribution: +7.92pp).
- Most-grounding-failure-prone instrument (MSO-grounded only): **US30_cash** at 15.5% (n_prices=239).
- Per-instrument ranking SHIFTS after role-stratification: ['GBPJPY', 'XAUUSD'] change rank between all-roles and MSO-grounded views. Per-instrument comparison was NOT apples-to-apples under v1.

## Reasoning

- The MSO-grounded rate is the apples-to-apples grounding-failure metric. Under v1, instruments whose AI emits more TPs (because more CANDIDATEs fire) appeared more hallucination-prone purely as a measurement artifact. Stripping FORWARD_DERIVED roles isolates the real grounding-failure rate.
- For Phase 2 prompt research (K54+) the MSO-grounded rate is the decision-relevant number. A tool-use grounding step or a tightened L2 verifier targets MSO_GROUNDED roles only — improving FORWARD_DERIVED "hallucination" is not a coherent goal.
- The FORWARD_DERIVED column is informational: it reports what fraction of TPs map onto an MSO band by accident. A high value would suggest the AI's TP placement is structurally anchored to MSO levels (a structural feature, not a hallucination); a low value confirms TP is genuinely forward-projected.

## Methodology — role taxonomy

Every cited price gets a `role_class` according to `src.research_infra.hallucination_measurement.ROLE_TAXONOMY`:

- **MSO_GROUNDED** — should match MSO data (real hallucination loci).
  - `current_price`, `entry_price`, `stop_loss`
  - `ob_high`, `ob_low`, `ob_mid`, `ob_body`
  - `breaker_high`, `breaker_low`, `breaker_mid`
  - `fvg_high`, `fvg_low`, `fvg_mid`
  - `swing_high`, `swing_low`, `protected_swing`
  - `sweep_price`, `liquidity_high`, `liquidity_low`
- **FORWARD_DERIVED** — not in MSO by construction.
  - `take_profit` (entry + N×R)
  - `trailing_stop_target`
- **AMBIGUOUS** — case-by-case.
  - `equilibrium`

Unknown / novel roles default to AMBIGUOUS so they do not silently inflate the MSO-grounded rate. New canonical roles must be added to `ROLE_TAXONOMY` explicitly.

Recommended rate for downstream consumers (K54 + Phase 2 prompt research): **MSO_GROUNDED hallucinated_pct only**. The all-roles rate from v1 conflates real grounding failures with the TP forward-derivation artifact.
