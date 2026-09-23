# B4 — The three Phase-1 open questions that gate repairs (candidate_probability clamp, the 0.92 fill template, binary_population vs close-reason)

**Session FA continuation (OD-BROAD-FORENSIC-2), Phase B item 4. 2026-08-04.**
Code investigated read-only in `/Users/borr/GTOSActive/worktrees/fa2-integration-20260803`
(branch `phase19/fa2-integration`); all `file:line` cites are that tree. Measured substrate:
the A0 identity-fence 2-day January lane arm
`research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/FA2_FENCE_S0R0_2D/`
— row counts verified by `wc -l`: MISSED 8,448 / DECISION 4,608 / SCORECARD 96 / TRADE 4.
Scan scriptlet: `phase1_open_questions_scan.py` (this directory); machine-readable mirror:
`PHASE1_OPEN_QUESTIONS.json`. Evidence class: **DIAGNOSTIC** (billed:false, development
window). No March-2026 bytes, no live-forward bytes were read.

---

## Q1 — candidate_probability: where computed, where clamped

**CLAIM (Phase 1).** Pool min p 0.584/0.580 (Jan/Feb), max ~0.97; open question "where
`candidate_probability` is computed and whether [0.58, 0.97] is a clamp"; probability
includes `0.04 × sha256(origin_family_name)`; a hardcoded 0.55 confidence constant; the
layer cannot express a loser (min EV +0.398).

**MECHANISM (the full chain, replay path).**

1. **Feature signal** — `v4_timewarp_simulated_live_research_loop.py:53660`
   (`candidate_feature_signal`). The hash term is real and content-free:
   ```python
   family_hash = int(stable_sha256(str(candidate.get("origin_family") or ""))[:8], 16) / 0xFFFFFFFF   # :53681
   follow_strength = _clamp_float(extreme*0.22 + trend*0.18 + volbal*0.16 + rr*0.16
                                  + mso_follow*0.24 + family_hash*0.04, 0.05, 0.98)                   # :53682-53694
   ```
   `reliability = clamp(0.50·source_complete + 0.20·volbal + 0.20·mso_follow + 0.10·(1−mixed), 0.20, 0.98)` (`:53694-53701`).
2. **Debate context** — `build_probability_context` (`:58091`). Builds FIVE sources; four
   support **the candidate's own side** by construction — `selector`, `market_state`,
   `lifecycle` stance-FOLLOW, plus stance-DIRECT `source_completeness`, which the support
   table credits at full weight (`probability_debate_v4.py:640-642`); the only counterweight
   is the MIXED `cost` source, which contributes `opposition[side] = 0.35 × w_cost`
   (`:633-634`).
   The context computes `base_probability = clamp(0.35 + 0.38·follow_strength +
   0.18·reliability − 0.15·cost_r, 0.20, 0.88)` (`:58199-58204`) — **a dead wire: no code in
   `probability_debate_v4.py` ever reads `base_probability`**. The returned dict
   (`:58197-58213`) also omits top-level `cost_r` and `candidate_direction`.
3. **Debate engine** — `probability_debate_v4.py`:
   ```python
   raw = sigmoid(logit(prior) + support*1.65 - opposition*1.45
                 - missing_source_penalty*mult - cost_penalty)          # :657-663
   calibrated = clamp(raw*w + 0.50*(1.0-w))   # w = max(0.35, avg_reliability)   # :754-758
   ev_r = calibrated*rr - (1-calibrated)*1.0 - cost_r - uncertainty*0.20        # :673-678
   ```
   `prior` for long/short = 0.34; the +0.08 direction-match boost needs
   `context["candidate_direction"]`, which the **replay** builder never passes (`:722-738`) —
   only the runtime builder does (`build_probability_debate_context_from_runtime`, `:934`,
   `:1094-1096`). `cost_penalty = context.get("cost_r")·0.7 = 0` in replay (`:748-752`), and
   `_reward_loss_cost` likewise reads `context.get("cost_r")` → **the thesis EV subtracts a
   cost of zero** (`:760-775`; rr defaults 1.5). The fence ledger stamps this per row:
   `ev_direct_cost_term_status = "probability_context_omits_cost_r_so_debate_cost_r_is_zero"`.
4. **Attachment** — `v4_timewarp:58385-58386` and `:67448`:
   `candidate_probability = safe_float(thesis.get("probability"), 0.55)`. The 0.55 here is a
   **fallback for a missing thesis**, distinct from the confidence constant:
   `REPLAY_MISSING_CONFIDENCE_DEFAULT = 0.55` at `ultimate_candidate_package.py:72`, returned
   at `:2064` (scheduler mirror `v4_timewarp:26625`) — that one is Phase 1's
   `candidate_confidence ≡ 0.55`.
5. **Clamp inventory on the path** — `follow_strength` [0.05, 0.98]; `reliability`
   [0.20, 0.98]; source strengths [0.05, 0.98]/[0.05, 0.95]; logit-input guard
   [0.001, 0.999]; final calibration clamp [0, 1]; dead `base_probability` [0.20, 0.88].
   **No [0.58, 0.97] clamp exists anywhere.**
6. **Consumers** — EV (step 3, inside the same thesis); `expected_net_r = ev − cost_r`
   (`:67450`); scheduler ranking `_candidate_edge_score`
   (`moonshot_scheduler_v4_best_trade_allocator.py:15755-15777`, the
   `max(0, p−0.50)·0.25` term plus the executable-transfer composite); threshold gates only —
   `dynamic_budget_package_min_probability` default 0.58 (`v4_timewarp:30141-30144`),
   `SOURCE_BOUND_ROUTER_REFUSAL_MIN_PROBABILITY = 0.70` (`:11674`), selector reduce-risk
   floors 0.85/0.80 (allocator `:8752`, `:8757`). **No sizing quantity scales continuously
   with probability** — every sizing-adjacent use is a min-threshold gate.

**MEASURED (fence MISSED ledger, 8,448 rows; scriptlet `phase1_open_questions_scan.py`).**

| quantity | value |
|---|---|
| candidate_probability n / null | 8,448 / 0 |
| min / max | **0.6012429993** / **0.9641304360** |
| mean; q25/q50/q75 | 0.7590; 0.6863 / 0.7432 / 0.8360 |
| rows exactly at observed min / max | **1 / 1** (no point mass at any bound) |
| rows < 0.58 / > 0.97 / = 0.55 | **0 / 0 / 0** (the :58385 fallback never fired) |
| largest atoms | 0.61839671 × 743, 0.734630815 × 307, 0.667230471 × 113 (repeated identical-feature candidates, not clamps) |
| candidate_ev_r min / rows ≤ 0 | **+0.4420** / **0** of 8,448 |
| expectancy_r ≡ candidate_ev_r | **8,448 / 8,448** byte-equal (duplicate field) |
| expected_net_r = ev − cost (1e−6) | 8,448 / 8,448; **3,619 (42.8 %) ≤ 0** — cost alone creates every negative expectation |
| hash-term live probe (10 family names, identical candidate, real code path) | thesis p spans **0.004463** (0.772543→0.777007); thesis EV spans **0.0114 R** |

**VERDICT.** The "[0.58, 0.97] clamp" hypothesis is **REFUTED** — no such clamp exists in
code and the empirical distribution has zero mass at any bound; the envelope is emergent
from (a) shrinkage-to-0.50 calibration with weight ≤ 0.98 and (b) a jury packed 4-of-5
FOLLOW with opposition capped at 0.35·w_cost, which structurally cannot express p ≲ 0.60.
The hash term is **CONFIRMED live** (measured through the real path). The 0.55 is **two
different constants**: a confidence default (confirmed at `ultimate_candidate_package.py:72`)
and a probability fallback that fired on 0/8,448 fence rows. The "+EV floor" is **CONFIRMED
structural**: with cost_r = 0 inside the debate, rr ≥ 1.5 and p ≥ 0.60, EV = p·rr − (1−p) −
unc·0.2 cannot go negative — min measured +0.442.

**REPAIR IMPLICATION (R-BELIEF author).** Removing the hash term means deleting
`family_hash*0.04` from `v4_timewarp:53682-53694` (and its `family_hash_signal` export /
`candidate_generation_rank_key` tiebreak at `:56777-56791`) — worth ~0.45 pp of
content-free probability noise and ~1.1 cR of EV noise per family name. But the hash is the
smallest defect on this path. The load-bearing repairs are: (1) **wire cost into the debate
context** — add top-level `"cost_r"` to the dict returned at `:58197-58213`; that is the
exact key `_reward_loss_cost` (`:760-775`) and `_action_cost_penalty` (`:748-752`) already
read, and the runtime builder already passes (`:1094-1096`) — a replay/live divergence, not
a new feature; (2) **unpack the jury** — recalibration cannot reach base-rate honesty
(realized positive share 0.279/0.309) while four of five sources FOLLOW the candidate by
construction and the only opposition is 0.35·w_cost; either the source construction or the
calibration map (`:754-758`, shrinkage target 0.50) must change; (3) delete the dead
`base_probability` wire (`:58199-58204`) or make the debate read it — as shipped it is the
only place cost touches probability directly and it goes nowhere; (4) also pass
`candidate_direction` if the +0.08 prior boost is intended in replay. The scheduler's
`max(0, p−0.50)·0.25` term (allocator `:15774`) is degenerate under the current floor
— every candidate collects a positive bonus, compressing rank discrimination; re-derive
after recalibration.

---

## Q2 — the 0.92 fill template

**CLAIM (Phase 1).** A "0.92 fill-probability template" of unknown origin.

**MECHANISM.** Two distinct fill quantities exist on the replay path; the 0.92 belongs to
the second:

1. **`fill_probability` (top-level ledger field) is a heuristic, not the template** —
   `v4_timewarp:58240-58247`:
   ```python
   heuristic_fill_probability = _clamp_float(0.25 + thesis_p*0.35
       + source_complete*0.20 + volatility_balance*0.20, 0.05, 0.95)
   ```
   aliased to `entry_quality_fill_probability` and `fill_probability` (`:58259-58260`);
   stamped by the ledger itself `fill_probability_authority_class =
   "predecision_model_prior_not_fill_execution_authority"`.
2. **The 0.92 is `execution_fill_probability`**, from the marketable-limit branch of
   `predecision_limit_fillability_from_geometry` — `poi_execution_lifecycle.py:123`, template
   at `:176-178`:
   ```python
   if limit_marketable:
       atr_component = 0.92
       risk_component = 0.92
       reason = "limit_price_marketable_at_decision"
   ...
   fill_probability = max(0.03, min(0.95, atr_component*0.70 + risk_component*0.30))  # :192-195
   ```
   `0.92·0.70 + 0.92·0.30 = 0.92` exactly. **One constant for every symbol and every
   session** — the function receives only side/entry/stop/current/atr14; no symbol, no
   session, no spread, no tick input. The non-marketable branch is distance-scaled
   (`1/(1+d^1.35)`, `1/(1+d^1.10)`) and saturates at the 0.95 ceiling when the limit sits at
   the market. Wired into the replay via `candidate_predecision_limit_fillability_signal`
   (`v4_timewarp:53854`), clamped again [0.03, 0.95] at `:58249-58257`.
3. **Consumers of the 0.92** (trade-row keys, code sites): the risk-expression ladder's
   full-risk floor 0.8 (`v4_timewarp:29470-29487`), the passive-limit fallback ceiling
   `max_limit_fill_probability_for_fallback` 0.85 (`:38476-38488`), the stop-hazard guard
   min 0.5 (`:21510-21516`). All three gates compare a **constant** against their
   thresholds, so for every marketable-limit candidate they are decided at code-write time,
   not by the market. The scheduler score consumes the *heuristic* at weight 0.10
   (allocator `:15755-15777`).
4. The train engine already knows: `decision_semantics.py:1429-1446` stamps exact-0.92 rows
   `marketable_limit_constant_template_non_authoritative` /
   `modeled_template_not_measured`, `authoritative_execution_fill_probability = None`.

**MEASURED.**

| quantity | value |
|---|---|
| MISSED `fill_probability` (heuristic): n, range | 8,448; [0.667987, **0.95**] |
| rows exactly 0.92 | **0** of 8,448 |
| rows at the 0.95 ceiling | **1,619 (19.2 %)** — the heuristic's own clamp binds |
| rows at the 0.05 floor | 0 |
| `execution_fill_probability` on MISSED rows | **ABSENT** (key present on 0 of 8,448; only `fill_probability` exists there) |
| `limit_marketable_at_decision` on MISSED | null 8,115 / True 135 / False 198 |
| TRADE rows (4) | 3 of 4 carry `execution_fill_probability = 0.92` exactly (`limit_marketable_at_decision: true`, source `predecision_limit_fillability.fill_probability`); the 4th carries 0.95 (distance branch at its ceiling, `limit_marketable: false`). 4 of 4 executed trades ride a modeled constant. |
| propagation on trade rows | the same 0.92 appears as `package_risk_expression_execution_fill_probability`, `passive_limit_fallback_envelope_limit_fill_probability`, `predecision_stop_hazard_guard_limit_fill_probability`, `scheduler_execution_fill_probability` — one template, four gate surfaces |

**VERDICT.** **CONFIRMED, with the origin pinned and one correction of emphasis**: the 0.92
is not the pool's `fill_probability` field (that is the heuristic, which never equals 0.92);
it is the marketable-limit constant of `poi_execution_lifecycle.py:176-178`, present only on
scheduler-materialized candidates — and on this arm that means **100 % of executed trades
carried a modeled template (75 % exactly 0.92, 25 % the 0.95 ceiling)** while the gates
comparing it to 0.8/0.85/0.5 believed they were measuring something.

**REPAIR IMPLICATION (R-BELIEF / R-SCHEMA author; P1 dependency).** An honest fill
probability needs, per candidate: symbol- and session-conditional fill frequency for
marketable limits (spread- and distance-conditioned), measured from the tick corpus — that
is exactly **P1 (fill truth from tick captures)** with HP's M1-acceptance rule, which turns
the 492/10,810 full-tick/M1-only split into a measurement. P1 was NOT run here (it is
SCHEDULED-ON-NEED per the WAVE20 supersession register); until it lands, every
`execution_fill_probability` consumer decision (full-risk tier, fallback envelope,
stop-hazard) is a constant-vs-constant comparison and should be treated as unmeasured. For
R-SCHEMA: the MISSED rows carry no execution-fill field at all, so any pool-level study of
fill beliefs on missed opportunities silently studies the heuristic — the two fields must
never be merged under one name (the `decision_semantics.py:1429-1446` authority stamps are
the right pattern; extend them to the MISSED projection).

---

## Q3 — binary_population vs close-reason mismatch (finding L)

**CLAIM (Phase 1 / register row L).** Feb `binary_population` (950/3,660) vs close-reason
counts (2,811/11,499) — "do not quote 0.206 next to 0.309 until pinned"; suspicion that a
row counted scoreable-negative might actually be a time-stop/expiry, or vice versa.

**MECHANISM.**

1. **`binary_population` is an analysis-layer construct; the engine never builds it.** Zero
   hits in `src/`. Builders: `aw_separability_mine.py:950` (defined on native gross exactly
   −1.0 / +2.0), `cd_pool.py:382` (the pool receipts' generation — reconstructed
   `net_proxy + cost` within 1e−9 of fixed endpoints, because the compact pool has no native
   gross field), and the wave19-sol repair `analyze_decision_defects.py:396`, whose
   `DEFECT_REGISTER.json` already registered "Generic binary_population mixes exact contract
   endpoints with terminal first-touch outcomes" and whose repaired analyzer emits three
   explicit blocks (`exact_contract_endpoint_population`,
   `terminal_outcome_first_touch_population`, `binary_population` as
   `deprecated_alias_of` the former), pinned by
   `test_ln_definitions_are_explicit_and_not_interchangeable`.
2. **The exits' vocabulary** — `path_final_r`, `v4_timewarp:60302-60359`:
   `target_reached_before_stop` returns `target_r` exactly (`:60337-60338`);
   `stop_reached_before_target` returns −1.0 exactly (`:60339-60342`); same-bar ambiguity
   returns −1.0 as `same_bar_ambiguity_conservative_stop_close` (`:60345-60350`); everything
   else becomes `time_stop_close_mark_from_{source}` with
   ```python
   bounded_close_r = max(-1.0, min(float(close_mark_r), target_r ...))   # :60351
   ```
   — **the clamp that CAN land a time-stop/expiry exactly on −1.0 or the target**, i.e. the
   structural back-door finding L feared. A second vocabulary layer exists: the
   selected-policy replay overwrites the oracle terminal (`:62446`,
   `selected_policy_replay:*`, `profit_harvest_*`), so TRADE rows carry both layers.
3. **Feb resolution inherited** (RECONCILE_A_Q.md row L, verified there): on native gross
   every binary-close row sits on its endpoint — 2,880 targets (2,811 + 69
   `selected_policy_replay:final_target`) and 12,192 stops (11,499 + 693
   `selected_policy_replay:stop_loss`); the 950/3,660 is the reconstruction-float-exact
   SUBSET.

**MEASURED (fence arm, 8,448 MISSED rows; 1,412 scoreable with native `opportunity_gross_r`).**

Close-reason counts (`terminal_outcome` ≡ `opportunity_close_reason` on **8,448/8,448**
MISSED rows): `not_filled_no_trade` 6,137;
`entry_fill_executable_terminal_r_ordered_tick_sequence_required` 899 (unscoreable);
`stop_reached_before_target` 718; `time_stop_close_mark_from_m1` 295;
`target_reached_before_stop` 137; `profit_harvest_..._protective_stop` 64;
`profit_harvest_..._giveback_close` 57; `selected_policy_replay:path_end_mark_to_market` 51;
`selected_policy_replay:giveback_close` 40; `time_stop_close_mark_from_tick` 28;
`selected_policy_replay:stop_loss` 18; `selected_policy_replay:final_target` 4.

| partition | stops | targets |
|---|---|---|
| close-reason first-touch (incl. `selected_policy_replay` terminal forms) | **736** (= 718 + 18) | **141** (= 137 + 4) |
| native gross exactly on endpoint (1e−9) | **736** | **141** own-target (140 at fixed 2.0 — one candidate had a non-2.0 target) |
| reconstructed `net_proxy + cost` within 1e−9 of fixed endpoints (= the `binary_population` method) | **160 (21.7 %)** | **31 (22.0 %)** |
| time-stop / giveback / MTM rows landing exactly on an endpoint (the :60351 clamp firing) | **0** of 535 | **0** of 535 |

Feb analogs of the capture ratio: 3,660/12,192 = 30.0 % (stops), 950/2,880 = 33.0 %
(targets) — same phenomenon, same direction, on both windows.

**VERDICT.** **CONFIRMED as a definitional artifact, and the direction is pinned.** The
mismatch is not time-stops contaminating the scoreable-negative population — on this arm the
close-reason and native-endpoint partitions agree **row-exactly** (736/736, 141/141) and the
`:60351` clamp fired zero times. The whole gap is the other direction: the
`binary_population` METHOD (net+cost reconstruction at 1e−9) **drops ~70–78 % of genuine
first-touch endpoint rows to float noise**, so any statistic computed on it (the 0.206 "hit
rate") describes a numerically-lucky subset, not the outcome population. The 0.206-vs-0.309
adjacency is a category error exactly as row L suspected — different numerators, different
denominators, different measures.

**REPAIR IMPLICATION (R-SCHEMA author).** Three rules, one asterisk. (1) Population
definitions belong to the close-reason vocabulary, never to float-exactness: the repaired
`cd_pool.py:382` triple (`exact_contract_endpoint_population` /
`terminal_outcome_first_touch_population` / deprecated alias) is the correct pattern — make
it the ONLY pattern any new analyzer may use, and never compute endpoint membership through
`net_proxy + cost` reconstruction when a native gross field exists (the full ledgers have
one; only the compact pools do not — that projection gap is itself an R-SCHEMA item).
(2) Any analyzer counting "stops" must state which vocabulary layer it counts: contract-walk
terminal (`path_final_r`) or selected-policy replay (`:62446` overwrite) — TRADE rows carry
both and they disagree on this very arm (a trade with `terminal_outcome =
stop_reached_before_target` closed as `selected_policy_replay:giveback_close`). (3) The
`:60351` clamp is a live hazard even at zero measured incidence here: a time-stop whose
close mark gaps beyond −1.0 or beyond target is silently relabeled to the exact endpoint
value while keeping its time-stop close reason — if R-SCHEMA adds one field, add
`close_mark_clamped: bool` at that line so the two populations stay separable by
construction on every future window.

---

## Cross-cutting: what the R-BELIEF spec author must not miss

1. **The belief layer's cost blindness is a one-key fix at `:58197-58213`** (add `cost_r`
   to the replay context), already stamped per-row by the wave19-sol telemetry and already
   correct on the runtime builder — the replay/live divergence means any live-path
   calibration study would measure a DIFFERENT belief system than the replay measures.
2. **`expectancy_r` is a byte-duplicate of `candidate_ev_r` on 8,448/8,448 rows** — fold
   into the R-SCHEMA dedup.
3. **The probability floor is the jury, not a clamp** — a recalibration map alone cannot
   produce honest probabilities while the source construction guarantees support ≫
   opposition; spec the source change, not just the map.
4. **19.2 % of pool rows sit at the fill heuristic's own 0.95 ceiling** and 100 % of
   executed trades ride the 0.92/0.95 templates — every downstream gate threshold
   (0.8 / 0.85 / 0.5) is currently compared against constants; P1 is the only exit from
   that circle.
