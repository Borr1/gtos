# Session CH — the two measurements that arm levers (wave 15, B2450–B2499)

Findings first. Session CH measured both levers and recommends arming neither. P1-HIST does
not earn an `mx_btcusd` weight step; the JPY hour-01 intervention does not beat every declared
random control and its ratified gate is not evaluable. The quiet-book handoff is closed with
separate current-set thresholds for both accounts.

Nothing here touched the VPS, ran a broker-capable script, edited `config/agent_config.yaml`
or `config/profiles/redacted_account.yaml`, changed an R2-bound path, armed/reweighted/promoted a
sleeve, or read a March 2026 outcome.

## 0. Decision table

| work order | finding | action |
|---|---|---|
| CH-1 — `mx_btcusd` P1-HIST | **NO PROMOTION:** M1 FAIL, strict M2 UNREACHABLE, M3 PASS, M4 FAIL | no owner page; no weight-step request |
| CH-2 — `sub_mid_dn_revert --entry-hour` | **DO-NOT-ARM:** positive small-sample arithmetic, but every gate NOT_EVALUABLE and random s1 beats h01 | keep the whole-sleeve flag off |
| CH-3 — current-book silence | FTMO WARN/ALERT **14/21** weekday sessions; redacted_account **15/22** | command center and silence check now cite the per-account receipt |

## 1. P1-HIST: the historical ladder does not promote `mx_btcusd`

The four looks are the four CE declared. Low/mid/high cost bands are sensitivities of each
look, not additional hypotheses.

| milestone | state | measured result |
|---|---|---|
| M1 — cross-broker BTC | **FAIL** | redacted_account generation produced 193 unique target-5R candidates. All 3 bands REJECT. Mid is -0.06475 R/day, -0.04198 R/trade, lifetime -0.19291 R/trade, 2/5 positive folds, raw p 0.5874, q 1.0. Recent-two is +0.02655, which does not rescue the negative claim. |
| M2 — cross-instrument mechanism | **UNREACHABLE** | ETH is positive (+0.45663 R/day; recent-two +1.01082) but REJECTS on robustness and significance. NZDJPY is negative (-0.49593; recent-two -0.76287) and REJECTS. AVA has only one evaluable fold and is NOT_EVALUABLE at every band. The all-three strict rule cannot be met. |
| M3 — repair interaction persists | **PASS** | AU identity is exact on 318/318 rows with zero mismatch; the five `maxbars -> time_stop` relabels are expected and the live time stop remains 7,680 M15 bars. |
| M4 — recent regime | **FAIL** | BTC and ETH are positive, NZDJPY is negative, AVA is not evaluable. |

The resulting false-promotion statement is deliberately narrow: the strict approximately
0.05 analytic form is **unreachable**, not passed. CE's looser 0.13–0.35 form is not silently
substituted. It is an analytic bound with named assumptions, not a bootstrap measurement.
`all_historical_milestones_pass=false`, `owner_request=NONE`, and the offline session leaves
the required live veto unresolved. Receipt:
`receipts/CH_PROMOTION_MILESTONES_V1.json` (B2459–B2462).

## 2. Entry hour: positive arithmetic is not an arming-grade effect

### 2.1 Population and gate

The sanctioned archive contains 499,995 rows across five JPY M15 files. The reader discarded
10,620 March rows before decoding a single OHLC cell. The stored JPY intent funnel is:

| stage | rows |
|---|---:|
| stored `sub_mid_dn_revert` JPY intents | 330 |
| both committed and +60-minute path available after maximum-horizon guard | 38 |
| implemented broker-hour-00 deferrals among those | 12 |
| retained by the ratified RECORDED population | 26 |
| hour-00, RECORDED and gate-priced | **7** |

Every h00/h01/inverse/random arm is NOT_EVALUABLE at every band. The gate reports 42 scored
observations but only two evaluable chronological folds; three of five folds are thin (60%
against a 34% ceiling). Four years of raw capture therefore do not create an admission-grade
effective sample.

### 2.2 Per-member mid-band economics

The table below uses the affected-row denominator: only RECORDED, priced hour-00 rows actually
shifted by the h01 arm. The receipt also carries the common-population denominator used for
matched arm ranking.

| member | matched | raw h00 | priced RECORDED h00 | gross Δ R/affected | cost saved R/affected | net Δ R/affected |
|---|---:|---:|---:|---:|---:|---:|
| AUDJPY | 7 | 2 | 1 | 0.00000 | +0.25432 | **+0.25432** |
| CHFJPY | 8 | 2 | 2 | 0.00000 | +0.44177 | **+0.44177** |
| EURJPY | 9 | 3 | 1 | +4.00000 | +0.24752 | **+4.24752** |
| GBPJPY | 13 | 4 | 3 | 0.00000 | +0.24625 | **+0.24625** |
| USDJPY | 1 | 1 | 0 | n/a | n/a | **not measured** |
| **pooled affected** |  |  | **7** | **+0.57143** | **+0.30345** | **+0.87488** |

On the full 26-row RECORDED JPY population, h01 is +0.15385 gross plus +0.08170 cost saved
= **+0.23554 R/trade**. The gross result is not broad: it is one EURJPY target flip; the
other three measured members are cost-only and USDJPY has no priced RECORDED hour-00 row.
The recent-two-fold planning mean is +1.40581 R/day, but the gate remains NOT_EVALUABLE.

### 2.3 Declared controls and recommendation

| arm | mid net Δ R/trade versus h00 |
|---|---:|
| inverse-cheapest matched | -0.00009 |
| random s0 | +0.01880 |
| **random s1** | **+0.31772** |
| random s2 | +0.01636 |
| random s3 | +0.06534 |
| random s4 | +0.17131 |
| **h01 ratified** | **+0.23554** |

H01 is positive at all three real cost bands, beats the inverse and four random controls,
and has a positive recent-two mean. It does **not** beat random s1. The preregistered rule
requires it to beat every matched control, so
`economic_rule_passed_on_jpy_surface=false` and the recommendation is **DO-NOT-ARM**.

That is not the only boundary. The current CLI selects the whole sleeve, while this gate
measures only JPY crosses. Metals-at-reopen remain unmeasured and in the arming decision's
scope. Even a favourable JPY counterfactual could not silently authorize the whole-sleeve
flag. Receipt: `receipts/CH_JPY_ENTRY_HOUR_GATE_V1.json` (B2463–B2467).

## 3. Current-account silence thresholds

`receipts/CH_QUIET_BOOK_THRESHOLDS_V1.json` uses BB's full-symbol-surface denominator and a
2,000-draw, 21-session moving-block bootstrap over 2024-10-29..2026-07-27.

| account set | sleeves | fills/week | WARN after | ALERT after | observed false alarms/year WARN / ALERT |
|---|---:|---:|---:|---:|---:|
| FTMO current | 5 | 1.6071 | **14** weekday sessions | **21** | 2.25 / 0.00 |
| redacted_account current | 4 | 1.3839 | **15** weekday sessions | **22** | 1.50 / 0.00 |

`scripts/book_silence_check.py` now requires the account and reads its p95/p99 pair;
`scripts/gtos_command_center.py` computes weekday sessions and treats WARN as a first-class
state before ALERT. No literal fallback threshold was added (B2457–B2458).

## 4. Trial integrity and March boundary

- The protocol fixed **12 looks before gating**: 4 P1-HIST plus h00, h01, inverse and five
  random entry controls. Every real cost band is a sensitivity.
- The family ratchet is V13 -> V25. `CANDIDATE_BOOK_V1` moves 53/51 -> 57/55;
  `B7_5_SEPARABILITY_MINE_V1` moves 514/492 -> 522/500.
- The trial ledger contains exactly 4 `CH_P1_HIST_V1` and 8 `CH_ENTRY_HOUR_V1` rows.
- D1 ingestion discarded 110 March rows before OHLC; JPY M15 ingestion discarded 10,620.
  Candidate lookback and maximum label-path intersections were then removed. Both receipts
  state `march_2026.status=OUTCOME_UNREAD`.
- Nothing was armed, reweighted or promoted, and no owner page was created.

## 5. Delivered

| artifact | purpose |
|---|---|
| `receipts/CH_MEASUREMENT_PROTOCOL_V1.json` + `receipts/ch_declare.py` | frozen 12-look protocol and prospective family ratchet |
| `receipts/CANDIDATE_FAMILY_V14.json` … `V25.json` | one successor per declared look |
| `receipts/ch_lever_measurements.py` | inert, staged P1/entry/quiet measurement driver |
| `receipts/CH_PROMOTION_MILESTONES_V1.json` | P1-HIST findings and false-promotion state |
| `receipts/CH_JPY_ENTRY_HOUR_GATE_V1.json` | 32 gate sensitivities, matched controls, per-member and paired economics |
| `receipts/CH_QUIET_BOOK_THRESHOLDS_V1.json` | current FTMO/redacted_account silence thresholds |
| `receipts/SESSION_CH_AB_RECEIPT.md` + `receipts/session_ch_ab/` | tool-emitted ZERO-baseline fence, scope and after capture |
| `scripts/book_silence_check.py`, `scripts/gtos_command_center.py` | per-account consumers of the quiet receipt |
| `tests/research_infra/test_ch_measurement_protocol.py`, `test_ch_lever_measurements.py` | declaration, outcome-unread, inert-port, denominator and calibration pins |

## 6. Verification

The focused CH/BB/command-center suite is **73 passed**. The final tool-derived 11-file scope
is **226 passed, 1 skipped, 0 failed, 0 errored** against the committed suite-wide ZERO
baseline of **12,476 passed, 0 bad**. `receipts/SESSION_CH_AB_RECEIPT.md` is the tool-emitted
`gtos-ab-receipt-v1` fence: **0 -> 0 bad, 0 regressed** (B2468).

## 7. What I got wrong

1. **My first inverse control ranked total cost.** Total cost includes realized hold and swap,
   so the outcome would have selected the supposedly outcome-blind placebo. I corrected it
   before either gate ran to mid-band zero-hold entry spread-R. No arm identity or look count
   changed (B2454).
2. **I assumed the bridge's numeric cells were ordinary float strings.** They are sometimes
   literal `np.float64(...)` strings. The strict parser now accepts only that narrow wrapper
   and finite numbers, never `eval`; March poison-cell tests prove the timestamp guard runs
   first.
3. **I initially measured the M15 forward shoulder as 1,280 × 15 wall-clock minutes.** That
   undercounts weekends. The final pre-run guard uses the actual 1,280th printed M15 bar plus
   a conservative 60-calendar-day generator shoulder.
4. **My first quiet-rate denominator began at each sleeve's first favourable trade.** That
   diluted FTMO/redacted_account to 1.23/1.03 fills per week. I rejected those bytes and used BB's
   `FULL_SURFACE_from`, producing 1.6071/1.3839 before B2458 landed.
5. **The first entry receipt exposed only the 26-row population average.** That made it too
   easy to read 26 interventions where only seven rows were actually shifted and gate-priced.
   After the run I added the affected-only denominator and five-member table, then regenerated
   from the same frozen arms with `ledger=False`. The ledger remains exactly eight looks and
   the verdict is unchanged (B2467).

## 8. Handoff

1. **No `mx_btcusd` promotion ceremony.** P1-HIST did not pass, so there is no owner request
   and no weight change to consider from this work.
2. **Keep `--entry-hour sub_mid_dn_revert` off.** The measured rule fails before the
   whole-sleeve transfer boundary is even reached.
3. **If the entry question is reopened, it needs a newly declared data-snapshot look.** The
   present five-file fetch starts in 2022 while the stored JPY intent archive begins
   2000-05-26; 292 of 330 intents remain outside the matched/guarded population. Backfill the
   same five symbols further toward that start with sanctioned timebase/hash sidecars, then
   ratchet the family before running — do not reuse `CH_ENTRY_HOUR_V1` as if the larger sample
   were the same look.
4. **The quiet thresholds are ready for the existing monitor consumers.** Deployment to any
   host is outside Session CH; no VPS state was changed here.
