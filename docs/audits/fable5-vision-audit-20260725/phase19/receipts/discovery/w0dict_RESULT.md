# w0-dictionary — LANE RESULT

**Deliverable: `w0_DATA_DICTIONARY.md`** (687 lines) in this directory. This file is the lane receipt;
the dictionary is the product. Machine twin: `w0_DICTIONARY.json` (all 78 fields with profile, meaning,
source line, trust class, flags, and enum distribution).

Everything below was measured this session, not quoted. Scripts: `w0_dictionary_trace.py` (traces every
field name across all 677 files in `src/`), `w0_dictionary_meta.py` (curated meanings), `w0_dictionary_build.py`
(generator). Raw measurement receipts: `w0_DICT_{ENUMS,COSTGATE,OVERCHARGE,IDENTITIES,SRCTRACE,ASSETS}.json`.

---

## D1 — THE BINDING COST GATE IS THE SPREAD CAP (0.10), NOT THE 0.15 TOTAL

`broker_net_cost_engine.py:pretrade_cost_refusal_reasons` has **two independent cost limbs**, and the
swarm brief names only the weaker one.

| limb | source | config | rows tripped | share of pool |
|---|---|---|---:|---:|
| `spread_r_exceeds_selected_cell_limit` | `:859-866` | `selected_cell_pretrade_max_spread_r: 0.10` (`config/agent_config.yaml:715`) | **17,258** | **62.40%** |
| `total_cost_r_exceeds_limit` | `:923-927` | `selected_cell_pretrade_max_total_cost_r: 0.15` (`config/agent_config.yaml:716`) | 20,074 | 72.58% |

Decomposition of the 20,448 refusals (n=27,658, exhaustive):

| | count | share of refusals |
|---|---:|---:|
| spread limb only | 374 | 1.83% |
| total limb only | 3,190 | 15.60% |
| **both** | **16,884** | **82.57%** |
| PASSED (neither) | 7,210 | — |

**The spread cap alone binds 17,258 / 20,448 = 84.40% of every refusal.** Spread is exactly the term
measured overcharged 7.3–8.5×, and `spread_r` is **mean 0.5642 R of the 0.6632 R total = 85.07%** of every
charge in the pool. Formula: `spread_r = |ask - bid| / sl_distance` (`broker_net_cost_engine.py:298-306`) —
the division is correct, the fed bid/ask are not.

### Pricing the overcharge directly against the gates

| spread divided by | PASS both gates | share of pool | vs shipped |
|---|---:|---:|---:|
| 1.0× (shipped) | 7,210 | 26.07% | 1.00× |
| 2.0× | 10,205 | 36.90% | 1.42× |
| 4.0× | 13,492 | 48.78% | 1.87× |
| **7.3× (measured low)** | **16,444** | **59.45%** | **2.28×** |
| **8.5× (measured high)** | **17,149** | **62.00%** | **2.38×** |
| spread → 0 (upper bound) | 22,488 | 81.31% | 3.12× |

**The 2.28×–2.38× reproduces the established "fixing costs makes the system trade ~2.2–2.4× MORE" from
twelve full month-replays, to two significant figures, from a completely independent computation.** That is
a hard validation of this gate model — and it locates the mechanism: the extra trades come almost entirely
from the **spread** limb, not the total-cost limb. Receipt: `w0_DICT_OVERCHARGE.json`, `w0_DICT_COSTGATE.json`.

---

## D2 — `final_blocker_class` IS A SUBSTRING CASCADE WITH FIXED PRECEDENCE, NOT A CAUSAL ATTRIBUTION

Two independent classifiers, both string-matching, both rank cost first.

**Cascade** (`moonshot_scheduler_v4_best_trade_allocator.py:14265-14349`), first match wins:

`cost_authority` (:14282) → `selector_materialization` (:14293) → `scheduler_selection` (:14303) →
`package_authority` (:14314) → `marketable_guard` (:14316) → `stop_hazard` (:14318) → `daily_lockout` (:14325)
→ `headroom` (:14332) → `lifecycle_authority` (:14339) → `risk_basis_missing` (:14346) →
`lifecycle_expiry` (:14348) → **`fill_realism` (:14349) = the FALLTHROUGH DEFAULT**.

So the 148 `fill_realism` rows in the blocker census mean **"no pattern matched"**, not "fill realism blocked it".

**Precedence table** (`order_blocker_precedence.py:172-188`): `source_or_signature_authority` 0,
**`cost_authority` 1**, `poi_lifecycle_terminal` 2, `session_authority` 3, `execution_fillability` 4,
`risk_safety` 5, `order_lifecycle` 6, `scheduler_selection` 7, `other` 8, `generic_selector_alias` 9, `unknown` 10.
Lowest wins. **Whenever a candidate carries several co-blockers, cost wins the tie-break by construction.**

The raw ledger carries `package_replay_order_executable_final_co_blockers`
(`v4_timewarp_simulated_live_research_loop.py:13692`) but **it is not projected into the pool**. The pool
therefore cannot tell you what else would have blocked a row.

**Consequence: the 73.93% cost_authority share is an UPPER BOUND on cost's causal role, not a measurement of it.**
Use `miss_reason` (32 values, `v4_timewarp:92629`) when causality matters — it is the raw text the cascade classifies.

---

## D3 — THE POOL CONTAINS ZERO EXECUTED TRADES, AND IT IS 18.03% OF THE LEDGER

The raw ledger `CJ_RECLOCKED_S0R0_V7_MISSED_OPPORTUNITY_LEDGER.jsonl` holds **153,425 rows**
(`phase16/receipts/CJ_RECLOCKED_POOL_S0R0_V1.json` → `rows`). The pool is the **27,658 (18.03%)** that pass
the scoreability gate at `v4_timewarp_simulated_live_research_loop.py:28130-28140`.

That gate reads `diagnostic_scoreable = not headline_r_scoreable and opportunity_net_proxy_r is not None and (...)`.
**It requires `not headline_r_scoreable`** — so any candidate that reached headline execution is *excluded by
construction*. `missed_opportunity_r_scoreability_status` is the constant `diagnostic_opportunity_r_scoreable`
on all 27,658 rows **because that is the filter that built the pool**, and
`missed_opportunity_non_executable_diagnostic_scoreable` is `True` on all 27,658 for the same reason.

**The 125,767 non-scoreable ledger rows are not on this machine.** The ledger path does not exist in any
worktree (searched `/Users/borr/GTOSActive` to depth 8). They are unrecoverable without a re-run.

---

## D4 — TRUST CENSUS: ONLY 29 OF 78 FIELDS ARE USABLE, AND 19 CARRY ZERO INFORMATION

| trust class | fields | meaning |
|---|---:|---|
| `TRUST` | **29** | measured, populated, free of the cost defect |
| `DEGENERATE` | 15 | exact duplicate of another column, or ≤2 effective states |
| `CONSTANT` | 14 | one value across all 27,658 rows |
| `CONTAMINATED` | 9 | inherits the spread overcharge or a value derived from it |
| `DIAGNOSTIC` | 6 | replay bookkeeping, no live consumer |
| `UNPOPULATED` | 5 | 100% null |

**Five exact-duplicate pairs, verified at 1e-12 over all 27,658 rows** (`w0_DICT_IDENTITIES.json`):
`cost_r == expected_cost_r` · `candidate_ev_r == expectancy_r` · `fill_probability == entry_quality_fill_probability`
· `execution_fill_probability == limit_fillability_probability` · `direction == side`.

**Three families collapse 1:1:** `origin_family == framework == route_family`;
`session_bucket == authority_session == kill_zone`.

**Three columns are ONE BIT.** Exact identity, n=27,658, zero exceptions:
`broker_pretrade_cost_executable == False` ⟺ `pretrade_cost_packet_status == "REFUSED"` ⟺
`final_blocker_class == "cost_authority"` — 20,448 / 7,210 on all three.

**The 14 constants:** `expected_slippage_r` 0.02 · `fallback_execution_surcharge_r` 0.0 ·
`guarded_market_fallback_extra_cost_r` 0.0 · `candidate_confidence` 0.55 · `confidence_default_applied` True ·
`source_completeness` 1.0 · `fill_realism_executable` True · `entry_fill_executable` True ·
`dynamic_geometry_policy` `momentum_exhaustion` · `selected_policy_for_expected_net_r` `momentum_exhaustion` ·
`decision_timeframe` M15 · `market_timeframe` M15 · `missed_opportunity_r_scoreability_status` ·
`missed_opportunity_non_executable_diagnostic_scoreable`.

**The 5 unpopulated:** `setup_family`, `bucket_source_family`, `commission_r_broker_true_measured`,
`commission_r_repair_status`, `swap_horizon_repair_status`.

---

## D5 — CORRECTION: `execution_fill_probability` IS NOT A FLAT 0.92

The brief states it is "a flat constant 0.92 for every symbol and session (poi_execution_lifecycle.py:176-178)".

**Measured over the pool: 7,400 distinct values, range 0.0401331 .. 0.95, mean 0.805058, 152 nulls (0.55%).**
`0.92` covers **19,452 rows = 70.32%**. It is the value of the `limit_marketable` branch at
`src/components/poi_execution_lifecycle.py:174-176` (`atr_component = 0.92; risk_component = 0.92`), which is
one branch of a two-branch function — the `else` at `:178-181` computes a distance-scaled value. The correct
file is `src/components/poi_execution_lifecycle.py`, not `src/research_infra/`.

**What IS constant in the fill group and matters more:** `fill_realism_executable` and `entry_fill_executable`
are `True` on **all 27,658 rows**. The pool asserts every candidate was fillable and never tests it — which is
the same defect W0-F2 priced at **+0.2776 R/trade of manufactured edge**.

---

## D6 — `limit_marketable_at_decision` IS 85.19% NULL, AND THE NULLS ARE STRUCTURAL

23,563 of 27,658 rows are null; only 3,175 True / 920 False. **The single most important fill question in the
pool is unanswered on 6 of every 7 rows.**

The non-null count **4,095 exactly equals** `scheduler_materialization_status == "scheduler_option_materialized"`
(4,095). The field is written during scheduler materialization (`poi_execution_lifecycle.py:224`), so every row
that dies at or before the cost gate never gets it. **The nulls are not missing data — they are rows that never
reached the stage that would answer the question.** Any fill lane must condition on
`scheduler_materialization_status`, not filter on `limit_marketable_at_decision is not None`, or it will silently
select the 14.81% of the pool that survived the cost gate.

---

## D7 — BELIEF IS OVER-CONFIDENT 2.21× AND STRUCTURALLY INCAPABLE OF SAYING "NO"

| field | measured | against |
|---|---|---|
| `candidate_probability` | mean **0.765762**, min **0.584298**, max 0.966289 | measured gross win rate **0.3468** |
| `candidate_ev_r` | mean **+0.86675**, **min +0.398495** — positive on every one of 27,658 rows | pool gross mean **−0.2175 R** |
| `candidate_confidence` | constant **0.55**, `confidence_default_applied` True on every row | — |

**Over-confidence factor 0.765762 / 0.3468 = 2.21×.** The minimum predicted probability is 0.5843: the generator
**never emits a candidate it believes is worse than a coin flip**, and `candidate_ev_r` is never negative, so the
belief layer cannot express a reject. The only belief field that can go negative is `expected_net_r`
(min −18.169), and it does so **only** because the contaminated `cost_r` is subtracted — its negative tail is the
spread overcharge, not a belief. Written at `components/ultimate_candidate_package.py:1724-1727` / `:2985-2988`;
`expected_net_r` at `components/learned_edge_layer_v4.py:469` (`p_fill * net_r_value`) and
`components/executable_value_semantics.py:114`.

---

## D8 — WHICH FIELDS INHERIT THE COST DEFECT, EXACTLY

**Contaminated (9):** `spread_r` (is the defect) · `cost_r` · `expected_cost_r` ·
`broker_pretrade_diag_expected_cost_r` · `old_proxy_vs_broker_calibrated_delta_r` · `expected_net_r` ·
**`opportunity_net_proxy_r` (the outcome column)** · `candidate_probability` and `candidate_ev_r` (contaminated
by miscalibration, a different defect — see D7).

The *verdicts* the defect produces are equally unusable as economics: `pretrade_cost_packet_status`,
`broker_pretrade_cost_executable`, `final_blocker_class == "cost_authority"`, and both cost limbs of
`selector_reason` (50.28% packet refusal + 23.33% EV-negative-after-cost = **73.61% of all selector rejections
are cost-derived**).

**Clean:** `gross_r` in the working set = `opportunity_net_proxy_r + cost_r`
(`w0_build_working_set_v2.py:301`) — the *exact algebraic inverse* of the engine's own subtraction, so adding
back the identical `cost_r` cancels the error exactly. Pool gross mean **−0.2175 R**. Also clean:
`commission_r` (mean 0.0652 R, broker-true), `swap_cost_r` (mean 0.0137 R), all path geometry, all
identity/time/session/price fields.

---

## D9 — ASSET INVENTORY (measured row counts, not manifest claims)

| asset | rows | cols | size | window | status |
|---|---:|---:|---:|---|---|
| `phase16/.../CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz` | 27,658 | 78 | 5.70 MB | Jan 2026 TRUE UTC | heavily read |
| `phase18/.../CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1.jsonl.gz` | 27,658 | 12 | 34.13 MB | Jan 2026 M1 | fully consumed by wave 0 |
| `phase19/discovery/w0_WORKING_SET.jsonl.gz` | 27,658 | 128 | 10.34 MB | Jan 2026 | **read this** |
| `phase19/discovery/w0_R_PATHS.jsonl.gz` | 27,658 | 10 | 23.58 MB | Jan 2026 | bar-level R |
| `phase18/.../CP_FEBRUARY_S0R0_POOL_V1.jsonl.gz` | 24,239 | **101** | 5.34 MB | Feb 2026 TRUE UTC | **USED-ONCE VAL, rejected broad V4** |
| `phase18/.../CQ_CURRENT_BREAKER_REPAIR_TRADES_V1.jsonl.gz` | 4,263 | 24 | 0.92 MB | Jan 2026 | read by CQ |
| `phase16/.../CD_REPAIRED_POOL_S0R0_V1.jsonl.gz` | 28,544 | 78 | 5.89 MB | Jan 2026 **UTC+2** | superseded by CJ |
| `phase16/.../CD_REPAIRED_POOL_S0R1_V1.jsonl.gz` | 28,546 | 78 | 5.89 MB | Jan 2026 UTC+2 | superseded |
| `phase16/.../CD_REPAIRED_POOL_S1R0_V1.jsonl.gz` | 28,552 | 78 | 5.89 MB | Jan 2026 UTC+2 | superseded |
| `phase16/.../CD_REPAIRED_POOL_S1R1_V1.jsonl.gz` | 28,553 | 78 | 5.89 MB | Jan 2026 UTC+2 | superseded |
| `phase19/forensic/walk/WALK_2D_CANDIDATES.jsonl.gz` | 8,448 | 24 | 0.81 MB | 2-day fixture | read |

**The four CD arms are the PRE-RE-CLOCK generation (UTC+2).** Row counts differ from CJ's 27,658 because
re-clocking moves candidates across session and day boundaries. Never pool a CD arm with the CJ arm; never
carry a CD-derived session or hour finding forward. Authoritative time map:
`phase18/receipts/CP_TRUE_UTC_B_TIME_MAP_V1.json` (all 83 cells negative), which supersedes AW's.

### February's pool carries 23 fields January's does not

Every January field is present in February, plus: `raw_gross_r`, `raw_net_proxy_r`,
`raw_opportunity_close_reason`, `policy_gross_r`, `opportunity_gross_r`, `opportunity_close_reason`,
`terminal_outcome`, `counterfactual_order_close_time_utc`, **`target_first_touch_utc`**,
**`stop_first_touch_utc`**, **`same_bar_ambiguity`**, **`ambiguity_resolution`**,
`terminal_r_diagnostic_outcome`, `terminal_r_diagnostic_gross_r`, `terminal_r_diagnostic_close_reason`,
`terminal_r_diagnostic_target_r`, `path_source`, `path_source_timeframe`, `path_index_source_path`,
`path_index_source_sha256`, `path_index_rows_returned`, `path_row_count`, `ordered_tick_truth_satisfied`.

**February resolves first-touch and same-bar ambiguity INLINE; January needs the separate path sidecar.**
If a lane needs a first-touch or ambiguity *method* validated, February already answers it — but February's
*economics* are spent (used-once VAL, wave 18, rejected broad V4: 0/20 positive days, precision 0.309 vs
0.606 breakeven).

### Virgin status — Wave 2's fuel

| window | pack | status |
|---|---|---|
| January 2026 | `CJ_PACKS_JANUARY_V3.json` | SPENT |
| February 2026 | `CJ_PACKS_FEBRUARY_V2.json` | **USED ONCE, REJECTED.** Method-validation only |
| March 2026 | six arms, `phase19/receipts/march/` (worktree `fa2-integration-20260803`) | READ — CLAUDE.md's "keep March outcome-unread" is overtaken |
| **April 2026** | `CJ_PACKS_APRIL_V2.json` | **ECONOMICS UNREAD — VIRGIN** |
| **May 2026** | `CJ_PACKS_MAY_V1.json` | **ECONOMICS UNREAD — VIRGIN** |

**April and May are the only two windows whose economics have never been read. Do not spend them in Wave 1.**

---

## D10 — PATHS SCHEMA, AND THE HARD 2-HOUR CEILING ON EVERY QUESTION

12 fields: `schema`, `arm_id`, `candidate_id`, `decision_time_utc`, `horizon_end_utc`, `symbol`, `side`,
`source_timeframe` (**`M1` on every row**), `source_path`, `source_sha256`, `ordered_tick_source`
(**always null — there is no tick-level path in this asset**), `ordered_path_observations`.

Each observation is `{open, high, low, close, time_utc}`. **No volume, no bid/ask, no spread** — so no
within-bar fill, queue-position or slippage question is answerable from this asset. Price-touch only.

First bar is the M1 bar **after** the decision (decision 00:15:00 → first bar 00:16:00); last is
`decision_time + 2h`. **Every path is ≤ 120 M1 bars = a hard 2-hour cap**; 86.12% are exactly 120 (mean 116.78,
min 3, max 120). **No holding-time or time-stop question beyond 2 h is answerable from this pool at all.**

Join key is **`(candidate_id, decision_time_utc)`**, not `candidate_id` (which repeats — W0-F1: 967 ids repeat,
max 140×, 24.39% of rows). Coverage is total: 27,658 / 27,658, zero rows without a path, zero duplicate keys,
zero side-or-symbol mismatches.

---

## D11 — THE DECISION PATH, 15 STAGES (full table in `w0_DATA_DICTIONARY.md` §5)

Measured funnel over n=27,658:

| after stage | survivors | share |
|---|---:|---:|
| generated | 27,658 | 100.00% |
| **cost packet PASSED** | **7,210** | **26.07%** |
| scheduler materialized | 4,095 | 14.81% |
| reached `new_position` | 4,512 | 16.31% |
| selector said `trade` | 21 | 0.08% |
| **actually executed** | **0** | **0.00%** |

`new_position` (4,512) exceeds `scheduler_option_materialized` (4,095), so **the two are not nested** — the
lifecycle action is written on a different branch from the scheduler status. Do not build a strict funnel out
of those two columns.

Other measured stage outcomes: `selector_action` reject 83.22%, only **21 rows** reach `trade`;
`effective_admission_count` **never exceeds 2** although `matched_sleeve_count` reaches 5;
`effective_order_type` is `none` on **4,552 rows (16.46%) that never got an order type at all**;
`scheduler_preselected_then_rejected_by_finalizer` is only **196 rows** in the whole month;
`risk_finalizer_rank` runs 1..149 and is populated even on rows that never reached the finalizer.

**A deeper 596-line walkthrough already exists** at
`research/operations/wave19_broad_forensic_2026_08_01/cartographer/DECISION_CYCLE_MAP.md`
(`evaluate_candidate_v4` `v4_timewarp:67389`, `materialize_scheduler_window` `:78014`,
`allocate_decision_window` `scheduler:27866`, `finalize_scheduler_risk_admitted_selection` `:44810`,
`simulate_order` `:85822`). §5 of the dictionary is the index; that file is the manual. It was **not**
duplicated here.

---

## D12 — SMALLER FACTS OTHER LANES SHOULD NOT RE-DERIVE

- **59.88% of the pool is generated OUTSIDE any configured session** (`route_session == off_configured_session`,
  16,562 rows). ny 17.79%, london 17.60%, tokyo 4.73%. Only 1,079 rows are actually rejected for it
  (`admission_quality_off_configured_session_entry_blocked`), so off-session generation is mostly *tolerated*,
  not blocked.
- **`take_profit_1` implies exactly 2.0000 R on all 27,658 rows** — the declared contract is uniformly 2R.
  `policy_target_r` disagrees on 1,229 rows (4.44%), reaching **505.47 R**; 85% of those are
  `current_breaker_re_entry`, the family CQ's inverted-breaker candidate is built from (W0-F4).
- **`risk_per_trade_pct` has exactly four values**: 2.0% (39.08%), 0.5% (35.67%), 1.0% (17.53%), 0.25% (7.73%).
  It affects no R-denominated column in this pool.
- **`source_bound_signal_r` has only 125 distinct values over 27,658 rows** — it is a package-level aggregate
  replicated onto members, not a per-candidate quantity, and its magnitudes (to 269,276) are not R despite the
  `_r` suffix.
- **`expected_slippage_r` is a flat 0.02** and `src/research_infra/divergence_matrix.py:366` already records
  in-repo that this covers only **80.3%** of a measured **+0.539109 R** slippage distribution.
- **`admission_risk_class` has no direct writer in `src/`** — it is assembled from the admission packet and
  projected at `b7_5_diagnostic_pool.py:247`. It is a near-duplicate of `selector_action` but not identical:
  **20 `trade` vs 21**. One candidate the selector said trade, admission did not.
- **`b7_5_diagnostic_pool.py` (`PROJECTION`, `:177-276`) is the canonical field-name map** between the pool's
  raw-ledger names and the b7.5 analysis names (e.g. pool `opportunity_net_proxy_r` = analysis
  `outcome_net_proxy_r`). Six fields are renamed; the alias table is in `w0_DICTIONARY.json` → `alias`.
