# Three-month postmortem — the MARKET-top-choice rule over February, April, May 2026

**Status: DEVELOPMENT POSTMORTEM, not a rule.** Written after the February PASS and the
April+May REJECT were both read. Feb/Apr/May 2026 + January + Oct/Nov development are OPEN
development data for this pipeline; **every replay, filter, geometry walk and threshold in
this document is therefore in-sample for any future claim**, and each section repeats the
label where a number could be mistaken for validation. No new frozen rule is declared.
No unread window was touched: June/July 2026 do not exist for this pipeline, March 2026
was not read (the month-sliced M1 sources make it physically impossible for any walk here
to touch a March or June bar — `postmortem/pm_geometry.py` docstring), and the two reserve
days 2025-10-31 / 2025-11-05 were not read.

Branch `wave21/three-month-postmortem`, base `56d2e27d9`. Every number below is cited to a
machine receipt in `postmortem/` or to one of the two sealed results in this directory.
Scripts: `pm_extract.py` (population + frozen re-run), `pm_regime.py` (regime-spine dials),
`pm_analysis.py` (completion/separators/stand-downs/family scope), `pm_geometry.py`
(geometry walks), `pm_lifecycle_shape.py` (occupancy + MFE), `pm_ranking_health.py`
(calibration + guards), `pm_jan_replay.py` (January under the frozen rule), `pm_bars.py`
(pass-bar pricing).

---

## 0. Reproduction integrity — the ground every claim stands on

The entire analysis chain was rebuilt from the committed scorers (`w21_score_aprmay_r3b.py`
→ committed r2 scorer → the frozen ridge → `candidate_funnel_analysis.py`), loaders reused
byte-identically, and the full prequential re-run **reproduces both sealed results exactly**
[`postmortem/PM_RERUN_INTEGRITY_V1.json`]:

| window | selected (mine/sealed) | keys match in order | max abs Δpredicted | actual net R (mine/sealed) |
|---|---|---|---|---|
| February | 106 / 106 | yes | 0.0 | +14.168399 / +14.168399 |
| April+May | 67 / 67 | yes | 0.0 | −2.611858 / −2.611858 |

January under the frozen rule reproduces the rule-of-record's development finding exactly:
52 selected, +10.53639 R [`postmortem/PM_JAN_FROZEN_RULE_V1.json`
`verification_vs_development_finding`; `MARKET_TOP_CHOICE_VALIDATION_RULE_V1_1.json`
`development_finding`]. Population extraction matches the sealed populations row-for-row
(Feb 121,302 occurrences; April 124,284 + May 123,226 = 247,510)
[`PM_RERUN_INTEGRITY_V1.json` `population`;
`FEBRUARY_MARKET_TOP_CHOICE_VALIDATION_RESULT_R2.json` `population.occurrences`;
`APRIL_MAY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json` `population.occurrences`]. The
geometry control re-walk reproduced the recorded lifecycle of **all** selected+near-selected
candidates with **0 mismatches** [`postmortem/PM_GEOMETRY_V1.json` `control`].

---

## 1. The sealed record, restated

All figures from `FEBRUARY_MARKET_TOP_CHOICE_VALIDATION_RESULT_R2.json` and
`APRIL_MAY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json` unless cited otherwise.

| | Jan (dev) | Feb (PASS) | April | May | Apr+May (REJECT) |
|---|---|---|---|---|---|
| selected / resolved | 52 / 51 | 106 / 105 | 50 / 49 | 17 / 17 | 67 / 66 |
| actual net R | +10.536 | +14.168 | −7.742 | +5.130 | −2.612 |
| worst-case net R | — | +13.144 | −8.815 | +5.130 | −3.685 |
| TARGET / STOP / TIME_STOP | — | 20 / 40 / 45 | 1 / 19 / 29 | 3 / 4 / 10 | 4 / 23 / 39 |
| target rate of resolved | — | 19.0 % | 2.0 % | 17.6 % | 6.1 % |
| discipline − naive mixed (worst-case) | — | +18.9 | — | — | +6.6 |
| max daily-close drawdown (worst-case basis) | — | 6.95 R | — | — | 15.47 R [`postmortem/PM_PASS_BARS_V1.json` `window_stats`] |

Shape of the damage: April was +4.46 R cumulative through 04-08, then a nine-session
stretch 04-09 → 04-21 summing −11.7 R (worst day 04-10: −6.30 R on 8 trades, 7 of them
`session_open_range_break`, five of those stopped index longs), and −3.61 more on 04-28.
May traded 17 times in 21 days (10 no-trade days) and was +5.13. The rule's own ridge
abstained hard in Apr/May — 2,712 `top_below_0p10` windows vs 1,164 in February — so the
throttle was already engaging [both sealed results, `days.*.policies.market_top_abstain`].

April's selection concentrated: JP225 `session_open_range_break` alone was 15 of 50 April
trades; JP225 was a February winner (+2.92 R on 15) and an April+May loser (−2.73 on 18)
[sealed results, `pooled.market_top_abstain.net_by_symbol/symbols`].

---

## 2. April autopsy

### 2.1 The tape completed normally; the rule's picks did not

Completion of the full eligible candidate population (geometry-valid, cost ≤ 0.2 R),
occurrence-level [`postmortem/PM_AUTOPSY_V1.json` `completion_tables`]:

| month | eligible | filled | target rate of filled | time-stop rate |
|---|---|---|---|---|
| Oct/Nov dev | 37,308 | 7,029 | 20.3 % | 32.5 % |
| Jan | 61,609 | 12,415 | 16.4 % | 36.7 % |
| Feb | 85,940 | 18,585 | **18.7 %** | 34.2 % |
| April | 71,256 | 15,470 | **16.2 %** | 38.7 % |
| May | 70,511 | 15,274 | 17.1 % | 35.9 % |

**April's population target-completion barely moved (18.7 % → 16.2 %), while the rule's
selected completion collapsed 19.0 % → 2.0 %.** February's picks completed at the
population rate; April's completed at one-eighth of it. The "completion collapse" is a
property of what the rule selected, not of the tape. Candidate-dedup versions of the same
tables (one row per candidate_id at first occurrence) tell the same story — Feb 16.6 %,
April 14.6 %, May 15.0 % [`completion_tables.*.candidate_dedup_first`]. This finding reframes the whole autopsy:
the object under repair is the ranking, not a market regime.

### 2.2 Regime characterization (regime-spine dials, same source data)

Wave-6 regime spine (`src/research_infra/regime_spine/state.py` `build_frame`, verbatim)
over the hold's own H4 series, bars ≥ 2026-06-01 dropped before framing
[`postmortem/PM_REGIME_MONTHS_V1.json`]; medians per month:

| dial (H4, ALL symbols) | Jan | Feb | April | May |
|---|---|---|---|---|
| vol_regime (ATR14/ATR100) p50 | 1.098 | 0.907 | **0.863** | 0.974 |
| \|slope50\|/ATR p50 | 3.24 | 2.81 | **3.73** | 3.04 |
| compression_5_over_20 p50 | 1.019 | 0.965 | 0.965 | 0.965 |

Per class, April's signature is concentrated in indices: index \|slope50\| p50 **5.63**
(Feb 2.66) at vol_regime 0.82 (Feb 0.98) — strongly trending, volatility-contracting index
tape; metals bottomed in February (vol_regime p50 0.634), not April. January — the month
the rule was developed on — was the high-vol month in every class.

**But the vol story fails as a lever.** The regime tables suggest "April was low-vol", and
a candidate-level stand-down on the M15 closed-bar vol_regime was replayed through the
frozen selection (predictions cached from the exact re-run, occupancy preserved)
[`PM_AUTOPSY_V1.json` `stand_down_replays_in_sample`, all IN-SAMPLE]:

| overlay (candidate-level) | Feb | April | May | 3-month total |
|---|---|---|---|---|
| frozen baseline | +14.17 | −7.74 | +5.13 | **+11.56** |
| SD1: skip vol_regime < 0.80 | +8.45 | −4.75 | +6.06 | +9.76 |
| SD2: skip vol_regime < 0.90 | +3.10 | −3.13 | +6.64 | +6.61 |
| SD3: SD2 on `session_open_range_break` only | +5.02 | −4.80 | +6.37 | +6.59 |

Every vol stand-down **loses money over the three months** — the whole February tape
ran low (ALL-symbol H4 p50 0.907), so February's winners sat below the cut too: SD2
removes 20 of February's 106 trades and −11.1 R of its net. The identified April regime is real as description and useless as a
filter. Labeled in-sample and reported as a negative result.

### 2.3 Is any decision-time feature a separator? (closed-bar only, leakage-audited)

Leakage audit: every regime feature is taken from the last M15 bar whose open+15m ≤
decision time; the join covered 100 % of occurrences with min closed-bar margin 0.0 s ≥ 0
[`PM_AUTOPSY_V1.json` `leakage_audit`]. The frozen predecision features are closed-bar by
construction (`broader_origin_generators._predecision_features`).

Population-level AUCs of 19 named decision-time features for target-completion, per month
[`PM_AUTOPSY_V1.json` `separator_scan_in_sample`]: **nothing separates**. Best
non-mechanical AUCs sit in 0.44–0.53 (noise). The only strong AUCs are the mechanical
stop-geometry channel (`stop_distance_atr`/`risk_over_atr`/`target_distance_atr` ≈ 0.31
for completion — a tighter stop puts the 2R target closer) and its SORB twin
`session_open_range_width_atr` (≈ 0.30), which are completion-vs-payoff trade-offs, not
quality signals (their positive-net AUCs are ≈ 0.53–0.55).

On the selected trades, the loser-vs-winner contrast pointed at the local M15 trend
(losers' median slope50 −0.97 vs winners −0.06 in Apr/May) [`PM_AUTOPSY_V1.json`
`selected_trade_contrast`] — and the replayed filter **refuted it**: skipping candidates
that fight the local trend (direction × slope50 < −0.5) guts February to −0.28 R because
February's profit was substantially counter-trend (+8.24 R in the against_gt_1 bucket vs
+2.76 aligned) [`postmortem/PM_RANKING_HEALTH_V1.json` `signed_trend_contrast_selected`,
`alignment_filter_SD6`]. See §6.

**What actually broke, measured:** the score itself carries almost no per-candidate
calibration anywhere [`PM_RANKING_HEALTH_V1.json` `calibration_by_decile`]:

| month | n resolved eligible | top-decile realized mean | pred ≥ 0.10 cohort: n / realized mean / predicted mean |
|---|---|---|---|
| Feb | 74,271 | −0.010 | 1,352 / **−0.072** / +0.146 |
| April | 62,579 | −0.024 | 709 / −0.031 / +0.131 |
| May | 62,900 | −0.010 | 398 / +0.009 / +0.126 |

Even in the PASS month, the model's confident cohort realized a *negative* mean. The
February +14.2 lived entirely in the last selection stage (top-1 per window + MARKET-only
+ occupancy) landing on winners. April is the same machine when that concentration stops
landing. A month like February is therefore consistent with a thin per-window edge — and
also with selection luck; the score's own magnitude cannot tell them apart. That is the
central fact the V2 spec (§5) and the pass bars are built around.

### 2.4 The stand-down quantification the brief asked for

"If the rule had stood down on the identified regime" — priced for every candidate
stand-down tested (§2.2 table, all negative on the three-month total), and for the two
decision-time-available guards that survive inspection [`PM_RANKING_HEALTH_V1.json`
`trailing_brake_SD5`; `PM_AUTOPSY_V1.json` `stand_down_replays_in_sample` SD4]. All rows
IN-SAMPLE — the rules were written after reading all three months:

| guard | Feb | April+May pooled | 3-month total | what it buys |
|---|---|---|---|---|
| frozen baseline | +14.17 | −2.61 | +11.56 | — |
| SD5 trailing brake k=5, x=3 R (stand down after −3 R over prior 5 days) | +12.11 | −0.88 | +11.23 | worst-run truncation: 6 Apr/May days stood down; Apr+May max drawdown (actual-day basis) 14.4 → 12.7 R |
| SD5 k=5, x=2 R | +12.11 | −2.01 | +10.10 | earlier brake, more false stops |
| SD4 family scope: `liquidity_sweep_reclaim` only | +7.93 | +1.54 (Apr +0.45 wc −0.63, May +1.10) | **+9.47** (wc +8.40) | positive in all three months, max daily drawdown ≤ 5.1 R, ~43 trades/3 months |

The honest summary: **no tested closed-bar regime or candidate feature separates April
from February without destroying February.** The two guards that keep the three months
positive are (i) the rule's own trailing P&L (a brake, roughly economics-neutral, tail
−2.9 R smaller), and (ii) scoping to the one family whose rule-selected record is stable
(§3). April's specific loss was not avoidable by any dial we could have frozen in March —
on this evidence it was the cost of running an uncalibrated ranking at full family scope.

---

## 3. Family scope

### 3.1 The families standalone are not edges — selection is the object

Family population economics (eligible occurrences, dedup to one row per candidate_id at
first occurrence, complete-cost rows) [`postmortem/PM_FAMILY_SCOPE_V1.json`]:
**every family is net-negative in almost every month at the generic 2.0R/2h contract.**
`liquidity_sweep_reclaim` standalone: Oct/Nov −78.0, Jan −218.1, Feb −284.4, April −266.3,
May −151.6 (sum −998 R over ~9,000 filled dedup candidates). The three-month headline
"+13.6 Feb lsr" is a property of **rule-selected** lsr, not of the family. Any scoped
claim must therefore be written as *rule ∘ family*, never family alone.

### 3.2 Rule ∘ family across the four scored months

| family | Jan [`PM_JAN_FROZEN_RULE_V1.json` `pooled`] | Feb [sealed] | April [sealed] | May [sealed] | verdict |
|---|---|---|---|---|---|
| `liquidity_sweep_reclaim` | **+4.40** (n=24; 8T/10S/6TS) | **+13.64** (n=24) | **+0.70** (n=3) | **+0.31** (n=2) | positive in ALL four scored months; n thin in Apr/May |
| `session_open_range_break` | +1.00 (n=4) | +1.90 (n=76) | −5.90 (n=38) | +4.99 (n=10) | sign-unstable; carried April's damage |
| `displacement_continuation` | +0.47 (n=9) | — (n=0) | −2.54 (n=9) | +1.73 (n=4) | in-and-out of selection, unstable |
| `structural_distance_extreme` | +5.90 (n=13) | −1.37 (n=6) | — | — | January's #2 earner, then negative and gone |
| `regime_transition_break` | −1.23 (n=2) | — | — | — | trace |
| `cross_asset_lead_lag` | — | — | — | −1.90 (n=1) | one trade, negative |

(January family split from the frozen-rule reproduction; the sealed rule file carries only
the headline. Feb/April/May from the sealed `net_by_family`/`families` blocks.)

**Is the scoped claim stable?** Rule∘lsr is the only cell positive in every scored month
(n = 24 / 24 / 3 / 2), and its Apr/May sample is 5 trades — stability of sign, not yet of
magnitude. `structural_distance_extreme` is the cautionary twin: +5.90 in January looked
just as scoped-worthy and went negative the next month. The sealed
April+May result itself classifies the window `FAMILY_SPECIFIC_EDGE:liquidity_sweep_reclaim`
[`APRIL_MAY...RESULT_V1.json` `family_robustness`]. Per the owner's direction, this
concentration is read as a **feature of the rule, not a defect**: §5 carries the scoped
path as a first-class structural option, priced by the SD4 replay (+9.47 R actual /
+8.40 R worst-case over the three months, drawdown ≤ 5.1 R, in-sample).

### 3.3 The other families, honestly

`session_open_range_break` is 72 % of February's trade count but only 13 % of its net; in
April it is 76 % of the trades and 76 % of the loss. Its rule-selected record is
noise-around-zero with one −5.9 month. `displacement_continuation` traded 9 times in January
(+0.47), vanished from February's selection, then split −2.5/+1.7 in Apr/May. Nothing outside lsr has a stable rule-selected record to scope
to.

---

## 4. Geometry and lifecycle (incl. owner-directed occupancy and time-shape analyses)

### 4.1 The actual contract, measured

Native geometry is **exactly 2.0R target for 5,714 of 5,714** walked candidates
[`postmortem/PM_GEOMETRY_V1.json` `native_risk_reward_ratio_distribution`], and the real
horizon is a **2-hour window**: selected time-stops die at p25=p50=p75=120 minutes in
every family, winners resolve at median ≈ 46 min, stops at ≈ 46 min
[`postmortem/PM_LIFECYCLE_SHAPE_V1.json` `lifecycle_shape.selected`]. So the frozen book
is an intraday 2-hour contract; a time-stop death is two hours of drift, and 43–59 % of
resolved selected trades per month ended that way (§1).

### 4.2 Occupancy cost: measured, and near-zero

The owner's hypothesis — long holds block the symbol slot while dying — was replayed
exactly (frozen loop, plus tracking of every window whose unconstrained top-ranked
candidate was excluded because its symbol was occupied, with the occupier's eventual
outcome) [`PM_LIFECYCLE_SHAPE_V1.json` `occupancy`]:

- February: **2** blocked-top windows across 20 days (forgone dedup net +2.68 R, one
  blocker died at TIME_STOP);
- April: **0**; May: **0**.

At the 2-hour contract on a 24-symbol surface with 1–2 concurrent positions, same-symbol
occupancy is not where the bleed is. (Caveat: under a longer/swing contract — §4.4 —
holds lengthen and this cost would need re-measuring; the measurement is contract-specific,
and the replay records blocked tops only when they would actually have traded.)

### 4.3 Time-shape: the early-exit signal exists, and its naive pricing loses money

Max-favorable-excursion walks on the same M1 tape (selected + near-selected, filled;
approximations recorded in the receipt) [`PM_LIFECYCLE_SHAPE_V1.json`]:

- **Signal: candidates that have not reached 0.25 × target (0.5 R MFE) by 60–120 min
  complete to target 0 / 190 times** across the three big families
  (`session_open_range_break` 0/128, `liquidity_sweep_reclaim` 0/24,
  `displacement_continuation` 0/38), with mean nets −0.61 to −0.73 vs +0.22 to +0.71 for
  the above-threshold cohort at the same 0.25× threshold [`lifecycle_shape.selected_plus_near.*.mfe_signal`].
- **Pricing: exiting them early still loses.** An exit-at-bar-close rule at 60 min prices
  at −1.0 to −8.7 R over the three months depending on threshold
  [`early_exit_pricing_selected`] — by the time the signal fires, the mark is already most
  of the way to the eventual terminal, and the time stop recovers part of it. At ≥120 min
  there is nothing left to exit (the window IS 120 min).

The signal is therefore proposed in §5 as a **candidate-quality feature** (in effect: an
entry-quality proxy learnable pre-trade) and as a properly-priced management rule only if
V2 models exits better than bar-close marks. The owner's instinct — "a good candidate
shouldn't take all the time" — is confirmed as a *label* property; converting it to
money requires either better exit modelling or moving it into selection.

### 4.4 Family-specific geometry: it moves SORB, it does not rescue April, lsr is already right

Geometry variants re-walked with the same M1 lifecycle machinery (native entry, native
2-hour expiry unless stated; each variant's R in units of its own risk; deductible scaled
1/stop_mult; swap holding-time dependence not re-modelled) [`PM_GEOMETRY_V1.json`]. All
IN-SAMPLE — variant argmaxes were read after all three months.

Selected set, three months pooled, per family (net R sum):

| variant | SORB (n=124) | lsr (n=29) | displacement (n=13) |
|---|---|---|---|
| native 2.0R / 2h | +1.00 | **+14.64** | −0.81 |
| t1p0 (target 1R) | +3.19 | +9.74 | −0.62 |
| t3p0 (target 3R) | +3.34 | +13.60 | −0.81 |
| s0p75_t2 (stop ×0.75, target 2R of new risk) | **+7.18** | +5.58 | +0.59 |
| s1p5_t2 (stop ×1.5, target 2R of new risk) | +4.63 | +8.04 | +0.99 |
| h2x (4-hour horizon) | +6.40 | +8.87 | +0.40 |

- **`session_open_range_break`'s generic contract is its own worst cell** — every
  alternative beats native, best +6.2 R over three months (s0p75_t2). The professional
  review's "family targets UNCHOSEN" is confirmed and it is SORB where it costs.
- **`liquidity_sweep_reclaim`'s native contract is already near-optimal** — every change
  makes it worse. The concentrated family needs no geometry work.
- **No geometry rescues April**: across all variants April's selected set stays between
  −8.5 and −2.0 R [`PM_GEOMETRY_V1.json` `tables.selected.per_scope.april`] — the April
  trades were directionally wrong, and geometry cannot fix selection.
- Whole-set totals: native +11.56 → s1p5_t2 +16.18 (best), at the price of a 71 %
  time-stop rate (122/172) — a swing-flavored contract that parks capital; see the
  occupancy caveat in §4.2.

**Intraday-vs-swing framing (owner directive):** the measured book is a 2-hour intraday
contract for every family. The variants sketch the choice per family — SORB behaves like
an intraday-thrust family (tighter stop, nearer or unchanged target, monetize the first
hour); lsr is correctly contracted at 2.0R/2h; displacement only stops losing under
wide-stop swing variants, which is a reason to question its selection, not to swing it.
Any V2 geometry choice must be **frozen per family in the prereg before June/July**, and
the in-sample argmax above must not be silently promoted (§5.2).

---

## 5. Rule V2 proposal — spec only, no code, no new frozen rule

### 5.1 Candidate feature additions (all closed-bar, leakage-audited by the §2.3 harness)

1. **Regime dials as ridge features** (not stand-downs): M15 `vol_regime`, `slope50`,
   `comp`, `ac60`, `rng_pos` at the last closed bar, plus their family interactions.
   Motivation: no dial separates alone (§2.3), but the ridge currently cannot see regime
   at all; interactions are the cheapest place a real conditional could surface. Risk:
   more one-hot mass on 60-ish trades/month of signal; mitigated by the bar options below.
2. **Completion-rate proxies**: trailing 60-day family × symbol-class target-completion
   and time-stop rates (population-level, resolved outcomes only, lagged one full day).
   These are the quantities that actually moved between Feb-selected and Apr-selected
   cells, and they are computable live.
3. **MFE-shape priors** (§4.3): per family × symbol-class trailing fraction of fills that
   reach 0.25×target within 60 min. A pre-trade proxy for "does this cell currently
   produce trades that go anywhere".
4. **Ranking-health meta-feature / brake**: the rule's own trailing 5-day realized net
   (SD5). As a feature it lets the model damp itself; as an overlay it is priced in §2.4
   (+11.23 vs +11.56 three-month, tail −2.9 R). Either wiring is acceptable; the overlay
   is simpler to freeze.
5. **Score calibration layer**: isotonic or Platt recalibration of the ridge score against
   realized nets on the trailing window, so that "predicted ≥ 0.10 R" means something
   closer to 0.10 R than the measured −0.07 (§2.3). This is the single largest measured
   defect of V1.

### 5.2 Geometry changes (from §4.4, in-sample — must be frozen in the prereg)

- `liquidity_sweep_reclaim`: **keep native 2.0R / 2h** (measured near-optimal).
- `session_open_range_break`: choose ONE of {s0p75_t2, t1p0} in the prereg; do not carry
  the in-sample argmax as truth — carry it as the hypothesis the June/July window tests.
- `displacement_continuation`: exclude from V2-full, or admit only under the scoped bar's
  family gate; its selected record is negative and geometry-indifferent.
- Early-exit management: **not** in V2 unless exits are modelled beyond bar-close marks
  (§4.3 priced the naive version negative).

### 5.3 Structural options (the owner picks one; all three are compatible with the bars)

- **Option A — V2-full**: V1 selection + §5.1 features + §5.2 geometry, all families.
  Highest capacity, highest multiplicity; carries SORB.
- **Option B — V2-scoped (first-class, per owner direction)**: the frozen rule restricted
  to `liquidity_sweep_reclaim` (SD4 replay: +7.93 / +0.45 (wc −0.63) / +1.10 across the
  three months, wc +8.40 total, drawdown ≤ 5.1 R, ~14 trades/month). Smallest, most
  stable, thinnest sample; its honest risk is magnitude-instability outside February
  (+0.45 and +1.10 R months) — a payout engine only if June/July confirm February-like months
  recur.
- **Option C — V1 + brake**: no model change; add SD5 (k=5, x=3 R) as the only overlay.
  Cheapest change that truncates April-shaped runs; does not repair calibration.

### 5.4 Pass-bar options for the NEXT prereg, priced retrospectively

Computed in `postmortem/PM_PASS_BARS_V1.json` from the sealed day series (worst-case
basis, all days; no-trade days = 0). **Retrospective verdicts are shown so the owner
chooses a standard knowing what it would have said; they are not evidence a bar
generalizes.**

| bar | definition (all gates must hold) | February | April+May |
|---|---|---|---|
| **BAR-1 — strict positivity (status quo V1_6)** | resolved ≥ 40; pooled worst-case > 0; positive > negative active days | **PASS** | **REJECT** |
| **BAR-2 — bootstrap CI + skill + drawdown** | day-resample p05 of pooled sum > 0 (20k, seed 20260811); main beats naive mixed (worst-case); max daily drawdown ≤ 8 R; resolved ≥ 40 | **REJECT** (p05 −3.45) | **REJECT** (p05 −20.59, drawdown 15.5 R) |
| **BAR-3 — relative skill + scoped family** | main beats naive mixed; pooled worst-case > −2 R; rule∘lsr positive in window; rule∘lsr positive in every scored month | **PASS** | **REJECT** (fails only the −2 R tolerance: −3.685) |

What each bar means, in one line each:

- BAR-1 is the bar that produced this quarter: it passes a +14 month and rejects a −2.6
  window; it cannot tell luck from skill and does not police drawdown.
- BAR-2 is the honest-statistics bar: **it would not have passed even February** — a
  single ~20-day month at this trade rate rarely clears a 95 % day-resample bar, which is
  precisely the sample-size statement of §2.3. Choosing it means multi-month evidence
  before any scale-up, by construction.
- BAR-3 is the scoped-continuity bar: it tracks whether the one stable cell stays stable
  and tolerates small negative full-book windows; it passed February and missed April+May
  by 1.7 R of tolerance. Suits Option B.

A sensible pairing is one bar for the full book (BAR-2) and BAR-3 for the scoped claim,
but that pairing is a choice, not a finding.

### 5.5 What this spec does NOT do

No frozen rule is declared. No June/July window exists, none was materialized, and no
outcome beyond 2026-05-29 was read. The in-sample geometry argmaxes and stand-down grids
above are hypotheses for the prereg, not results.

**Awaiting owner bar selection + June/July materialization.**

---

## 6. What I got wrong (my own passes, refuted by my own replays)

1. **The vol hypothesis.** The month tables (§2.2) read as "April failed because vol was
   low", and I built SD1–SD3 to price exactly that. The replay refuted it: every vol
   stand-down loses money over the three months because February's edge lived in low-vol
   candidates too. The regime description was right; the causal reading was wrong.
2. **The trend-alignment hypothesis.** The winners/losers medians (§2.3) pointed at
   "losers fight the local trend"; SD6 replays showed February's counter-trend trades were
   the profit (+8.24 R), and the filter guts February to −0.28 R. A median contrast on 67
   trades is not a mechanism.
3. **Reading the completion collapse as a tape property.** The brief's framing ("19 % →
   6 %") invited a market-regime explanation; the population tables (§2.1) show the tape
   completed at 16–19 % in every month. The collapse was in the rule's selections. This
   inverted where the autopsy had to look.
4. **BAR-3's first draft gated on the wrong object** — family-population stability, which
   is negative every month (§3.1). The scoped claim is rule∘family; fixed before pricing
   (`pm_bars.py` `lsr_scope_stability` docstring records the correction).
5. **The occupancy hypothesis (owner's, and mine to test) measured near-zero** at the
   current contract: 2 blocked windows in three months (§4.2). Not wrong to ask — wrong
   as a story for the bleed, and it would become live again under swing-length contracts.

Caveats that bound the above: stand-down and geometry replays reuse the frozen per-day
predictions (training population is selection-independent, so this is exact for overlays
that only filter candidates); MFE and early-exit marks approximate fills at bar close on
the BID tape with the entry spread as exit-cost proxy; geometry variants do not re-model
swap against holding time; and every improvement number in §2.4/§4.4/§5 is in-sample by
construction.
