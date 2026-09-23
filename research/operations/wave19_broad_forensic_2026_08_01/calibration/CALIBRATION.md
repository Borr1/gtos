# EV-CALIBRATION — the broad-V4 belief layer vs reality (Session FA, wave-19 forensic)

**Analyst:** EV-CALIBRATION (Fable 5) · **Date:** 2026-08-01
**Inputs:** January compact scoreable pool `CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz` (27,658 rows) and
February compact pool `CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz` (24,239 rows). No March data touched,
no live-forward data touched. All numbers computed from raw pool rows by
`ev_calibration_analysis.py` and `decomposition_check.py` in this directory; receipts:
`BELIEF_INVENTORY.json`, `CALIBRATION_TABLES.json`, `EV_SIGN_TABLE.json`, `COST_BELIEF.json`,
`DECOMPOSITION_CHECK.json`.

**Realized-event definition (declared up front):** primary event = `opportunity_net_proxy_r > 0`.
Sensitivity event = gross positive, `gross_r = opportunity_net_proxy_r + cost_r > 0`. February
carries an explicit `opportunity_gross_r`; the derivation matches it to max |diff| 5.0e-9 over all
24,239 rows, so the January derivation is trusted.

**Cross-checks:** every published aggregate reconciles exactly — January n 27,658, net sum
−24,357.199, net mean −0.880657, gross mean −0.217496, cost mean 0.663161 (spread 0.564213,
commission 0.065224, slippage 0.02, swap 0.013723), positive 7,706 (27.862 %), executable
7,210 / 20,448; February n 24,239, gross mean −0.150551, net mean −0.640021, positive share
0.309336 = the committed "observed precision".

---

## 1. Belief inventory — nine fields, four quantities, one of them a hardcoded constant

The nine belief fields are three exact-duplicate pairs plus one identity plus one constant:

| field | what it actually is | distinct (Jan/Feb) |
|---|---|---|
| `candidate_probability` | continuous model output | 26,844 / 21,890 |
| `candidate_ev_r` | **affine transform of p** — corr(p, ev) = 0.99997 both windows; implied win-payoff k = (ev+1)/p − 1 ∈ [1.393, 1.473] | 26,892 / 21,890 |
| `expectancy_r` | **byte-equal to `candidate_ev_r`** on 27,658/27,658 and 24,239/24,239 rows | dup |
| `expected_net_r` | **identity `candidate_ev_r − expected_cost_r`** on 100 % of rows (within 1e-6) | 27,087 / 21,947 |
| `candidate_confidence` | **constant 0.55 on all 51,897 rows of both windows.** `confidence_default_applied` is true on 100 % of rows. Source: `REPLAY_MISSING_CONFIDENCE_DEFAULT = 0.55` (`src/components/ultimate_candidate_package.py:72`), returned by `_replay_candidate_confidence` when no confidence key exists (`:2064`). Confidence is never computed for this family — it is a fallback that always fires. | 1 / 1 |
| `fill_probability` | continuous | 23,813 / 19,876 |
| `entry_quality_fill_probability` | **byte-equal to `fill_probability`** | dup |
| `execution_fill_probability` | 70.3 % of Jan rows are exactly 0.92 (19,452) and 1.5 % exactly 0.95; Feb 70.4 % at 0.92 — a template default with a continuous minority tail; null on 152 / 68 rows | 7,400 / 6,512 |
| `limit_fillability_probability` | **byte-equal to `execution_fill_probability`** | dup |

So the independent belief content per row is: **p, a fill probability, and a mostly-templated
execution-fill probability.** EV, expectancy and expected-net add zero information beyond p and
the (self-identical) cost field.

**The structural fiction:** `candidate_probability` min is 0.584 (Jan) / 0.580 (Feb) and
`candidate_ev_r` min is +0.398 / +0.387. **The belief layer cannot express a candidate with
sub-coin-flip probability or negative pre-cost EV.** Every one of 51,897 rows was believed to be a
winner before costs, in a family whose realized gross mean is −0.218 / −0.151 R and realized net
mean −0.881 / −0.640 R.

## 2. Probability calibration — worse than knowing nothing, and it replicates

Predicted probability vs the primary event (net > 0):

| | January | February |
|---|---|---|
| mean predicted p | 0.7658 | 0.7638 |
| realized rate (net) | 0.2786 | 0.3093 |
| realized rate (gross) | 0.3470 | 0.3734 |
| Brier (model) | 0.4316 | 0.4198 |
| Brier (base rate) | 0.2010 | 0.2136 |
| **Brier skill** | **−1.147** | **−0.965** |
| Brier skill, gross-event sensitivity | −0.759 | −0.662 |

The model's Brier score is roughly **double** the score of a constant forecast at the base rate,
in both windows, under both event definitions. Every one of the ten predicted-probability deciles
over-predicts, by +0.376 to +0.544 (Jan) and +0.381 to +0.536 (Feb) — the January top decile
predicts 0.923 and realizes 0.466; the February top decile predicts 0.905 and realizes 0.370.
Ranking content is thin and decays: corr(p, gross-positive outcome basis) — Jan reliability runs
0.123 → 0.466 roughly monotone; Feb runs 0.212 → 0.370 with a mid-table hump (deciles 4–6 realize
more than deciles 8–9). Pearson(p, realized gross) = **0.0738 (Jan) → 0.0066 (Feb)**: as a
discriminator of pre-cost outcome, the probability is indistinguishable from noise in February.
The miscalibration replicates across windows almost unchanged; the tiny ordering signal does not.

Per-family (see `CALIBRATION_TABLES.json → per_origin_family`): every family in both windows has
mean predicted p between 0.72 and 0.84 against realized net rates of 0.08–0.45 — there is no
family where the belief is honest.

## 3. EV calibration — a constant +1.0 R fiction, and the "correlation" is the cost term

- **Mean bias (expected − realized), net basis:** January **+1.0842 R/row** (believed +0.2036,
  realized −0.8807); February **+1.0119 R/row** (believed +0.3718, realized −0.6400). Identical
  bias on the gross basis by construction (the cost term cancels): candidate_ev mean 0.8667 vs
  realized gross −0.2175 (Jan), 0.8613 vs −0.1506 (Feb).
- **Correlation, and where it comes from.** Pearson(expected_net, net) = 0.722 (Jan) / 0.496
  (Feb), Spearman 0.562 / 0.443 — *looks* informative. But `expected_cost_r == cost_r` exactly on
  every row (§4), so the same known cost number sits on both sides with coefficient −1.
  Pearson(**−cost**, net) alone = **0.725 (Jan) / 0.510 (Feb)** — the cost term reproduces the
  entire correlation by itself. The edge component — Pearson(candidate_ev, realized gross) — is
  **0.0737 (Jan) / 0.0067 (Feb)** (Spearman 0.106 / 0.033). **All of expected_net_r's apparent
  predictive power is the diagnostic's own cost charge predicting itself; the model's edge belief
  is ~orthogonal to reality.**
- **Family × direction sign table** (`EV_SIGN_TABLE.json`): realized mean net is **negative in
  all 20 cells of both windows (40/40)**. Fiction cells (mean expected_net > 0 while realized
  net < 0): **January 16 of 20 cells, covering 67.0 % of rows; February 18 of 20, covering
  92.6 % of rows.** On the pre-cost comparison (candidate_ev vs gross): 18/20 and 16/20. The four
  January non-fiction cells are non-fiction only because expectation was *also* negative
  (`current_fvg_fill`, `structural_distance_extreme`) — nowhere is expectation negative and
  reality positive. The worst cells: `current_breaker_re_entry` believed +0.04/+0.22 and realized
  −1.64/−1.32 (Jan), believed +0.54/+0.43 and realized −1.06/−1.06 (Feb).

## 4. Cost-belief check — the only honest layer, and it is honest by tautology

- `expected_cost_r` equals `cost_r` **byte-exactly on 27,658/27,658 (Jan) and 24,239/24,239 (Feb)
  rows, max |diff| 0.0.** The cost "belief" is not a forecast that turned out right — it is the
  same number written into two slots. It can never be wrong ex post, and it also cannot be
  validated as a prediction. It is, however, the only component of `expected_net_r` that tracks
  anything real, which is why §3's decomposition comes out the way it does.
- `old_proxy_vs_broker_calibrated_delta_r` (legacy proxy minus broker-true, per row): January
  mean **+0.431 R** (p50 +0.041, p75 +0.452, p95 +2.374, max +18.60; 41.8 % negative, 0 % zero);
  February mean **+0.280 R** (p95 +1.560, max +11.65; 36.4 % negative). The legacy cost proxy
  under-charged the family by ~0.3–0.4 R/row on average, with a violent right tail — the
  broker-true repair moved real mass.
- **Spread sanity by symbol:** continuous and plausible for 21 of 24 symbols, but three are
  placeholders, not measurements: **BTCUSD `spread_r` = 0.0001 on every row of both windows**
  (2,118 rows; its cost is carried by commission instead, e.g. 0.206 R in the sampled row),
  **UKOIL_cash constant 0.02580**, **USOIL_cash constant 0.02700**. At the other extreme the
  measured means are brutal: SPX500 2.353 R and NAS100 2.216 R mean spread (Jan) — the spread
  alone exceeds 2 R at this family's stop geometry, which is why `broker_pretrade_cost_executable`
  is false on 73.9 % / 82.2 % of rows.

## 5. The decision-relevant number — why it picked losers

Deciles of `expected_net_r` vs realized mean net (`CALIBRATION_TABLES.json → decision_relevance`):

| | Jan believed | Jan realized | Feb believed | Feb realized |
|---|---|---|---|---|
| believed-WORST decile | −2.523 | **−3.507** | −1.416 | **−2.262** |
| believed-BEST decile | +1.161 | **−0.158** | +1.085 | **−0.228** |

Beliefs are **not anti-informative in ordering** pool-wide — believed-best realizes ~3.3 R/row
better than believed-worst — but §3 shows that ordering is almost entirely the known cost term
(it ranks cheap-to-trade rows above expensive ones), not edge. The forensic answer to "why did it
pick the losers" is sharper than anti-informativeness: **every decile of belief realizes
negative.** The system's believed-best tenth believes +1.16 and collects −0.16 (Jan); +1.08 and
−0.23 (Feb). Within-day (the scheduler's actual comparison set), top-quintile-by-expected_net
realizes −0.196 (Jan) / −0.243 (Feb); ranked by pre-cost EV against gross reality, the within-day
top quintile realizes −0.080 / −0.113 — still negative. And on the broker-executable subset the
ordering *inverts* in February: top decile −0.274 vs bottom decile −0.186. **A perfect executor of
these beliefs loses money at every belief level; the belief layer's job was to find the positive
27.9 % / 30.9 % of rows, and at its most confident it finds 46.6 % / 37.0 % of them while pricing
them as 92 % / 91 % certainties with +1 R of phantom expectancy.**

## 6. Verdict

The belief layer is fiction in the precise sense that matters: (1) one of its fields is a
hardcoded 0.55 that fired on 100 % of 51,897 rows; (2) three more are duplicates/identities that
add no information; (3) the probability is structurally incapable of predicting below 0.58 and the
EV below +0.39, in a family that loses on 70 % of rows; (4) its Brier score is ~2× worse than
knowing only the base rate, replicated in a second, never-before-read month; (5) its EV is biased
+1.01 to +1.08 R/row with edge-vs-reality correlation of 0.07 (Jan) → 0.007 (Feb); and (6) the
only calibrated component is the cost model, which is calibrated because it is the same number
compared with itself. Every downstream ranking, admission and sizing decision that consumed
`expected_net_r` was fed a signal whose informative part was "this row is cheap to trade" and
whose edge part was noise with a +1 R optimism offset.
