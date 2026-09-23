# Gate G1a receipt — Phase 1, the shadow reducer and the first economics check GTOS has had

**Assessed 2026-07-26** by the Phase 1 Session A implementation session, on branch
`phase1/shadow-reducer` in `worktrees/phase1-shadow-reducer-20260726`. Evidence tags per
`OPUS_IMPLEMENTATION_PROMPT.md` §4: **[MEASURED]** (ran/observed here), **[VERIFIED]** (read directly
in code or sealed artifacts), **[INFERRED]**, **[HYP]**.

`FULL_VISION_PLAN.md` Phase 1 item 1 states G1a as: *"agreement with the analyzer within float
tolerance, or a filed economic defect — either outcome is a win and is the first genuine economics
check in GTOS history."*

**Outcome: a filed economic defect.** It is not the defect this session first thought it had found,
and the difference is recorded in §3 rather than quietly corrected.

---

## 1. What was built

`docs/audits/fable5-vision-audit-20260725/phase1/shadow_reducer_v2.py` — 1,000 lines, **zero imports
from `src/`**, standard library only. Enforced by AST census, not by grep, in
`tests/test_shadow_reducer_v2.py::TestZeroEngineImports` (4 tests, including one that verifies the
census can actually fail, and one that closes the `importlib` / `sys.path` / `exec` loophole an
import census alone would miss) [MEASURED].

Run over **five arm-windows**: the four sealed January arms and the April S1R1 partial.
Output: `docs/audits/fable5-vision-audit-20260725/phase1/receipts/five_arm_windows.json`.

Invocation is in §8. It reads the sealed ledgers from
`worktrees/replay-accel-engine-20260719` and writes nothing outside `--out`.

---

## 2. The control: the reducer reads the evidence correctly [MEASURED]

Re-summing the ledgers in the sealed audit's own row-set conventions reproduces **24 of 24** economics
values across the four January arms, to the printed digit — `physical_gross_r`, `execution_cost_r`,
`physical_net_r`, `scoreable_net_cash`, `scoreable_accepted_risk_cash`, `cash_per_accepted_risk_dollar`.
Zero failures.

Two row-set facts had to be established empirically rather than assumed, and both were initially got
wrong from the prompt's own summary table:

- **`execution_cost_r` sums `cost_r` over ALL physical rows**, not scoreable ones. For S0R0 the
  90-row sum is `6.76829763` and matches the seal; the 88-row sum is `6.67549763` and matches nothing.
- **`q` divides scoreable net cash by `accepted_risk_cash` (all rows), not by
  `scoreable_accepted_risk_cash`** (`analyze_b7_5_selection_sizing_matrix.py:1459`). S0R0:
  `-201.311668 / 9000.0 = -0.022367963111`, which is what the seal reports. Dividing by `8800.0`
  gives `-0.022876…`, which matches nothing in the audit.

**Correction to `SESSION_A_SHADOW_REDUCER.md` §3's table.** Its `q` column is computed on the
scoreable denominator. The sealed values are:

| Arm | scoreable_net_cash | accepted_risk_cash | scoreable risk cash | sealed q |
|---|---:|---:|---:|---:|
| S0R0 | −201.311668 | 9,000.00 | 8,800.00 | **−0.022367963** |
| S1R0 | −550.596129 | 7,700.00 | 7,500.00 | **−0.071505991** |
| S0R1 | −5,432.330113 | 40,876.62 | 39,880.69 | **−0.132895771** (prompt: −0.136) |
| S1R1 | −6,596.056676 | 37,770.23 | 36,777.83 | **−0.174636414** (prompt: −0.179) |

The prompt's signs and magnitudes are right, so its sanity check passes; the last two q values are not
the sealed ones.

---

## 3. What this session claimed, and what an adversarial pass took off it

Recorded because the corrections are load-bearing, and because a receipt that only lists what survived
is not a receipt.

### 3a. WITHDRAWN — "exact agreement on price-derived exits is a control on my arithmetic"

The reducer agrees with the ledger to a summed delta of **0.000000** on `path_end_mark_to_market`
(22 rows) and `time_stop_close_mark_from_m1` (36 rows). This session first reported that as a control
proving its arithmetic against the engine's.

**It is a tautology.** Verified in source directly rather than taken on report [VERIFIED]:

- `dynamic_execution_policy.py:641` books path-end as `exit_r=last.close_r`; `:626` books time-stop as
  `exit_r=obs.close_r`.
- `v4_timewarp_simulated_live_research_loop.py:60803` builds each observation as
  `r_value = (price - entry)/risk` (LONG) / `(entry - price)/risk` (SHORT) with `close_r = r_value`,
  and `:60816-60823` appends that same `price` to `observation_quote_details`.
- `:61216-61222` matches `exit_quote_detail` **by index only**, and `:61296` stamps it as `exit_price`.

So on those rows the engine's formula *is* the reducer's formula. Agreement was guaranteed. What it
does establish, weakly, is that the reducer uses the engine's own geometry.

### 3b. WITHDRAWN — "`exit_price` is the fill price"

It is the quote on the observation the exit landed on, not a transacted price. The reducer's docstring
said "This is the real thing"; that sentence is gone and the mechanism is documented in its place.

### 3c. CORRECTED — target exits are conservative, not optimistic

The first framing said threshold exits are "systematically better than the fill implies". False for
targets: `final_target` books `target_r` and the recorded quote is **better**, mean **+0.067389 R**,
**0 of 8 adverse** [MEASURED]. That is correct behaviour for a resting limit, which legitimately fills
*at* its level. The finding is specific to stops and giveback closes.

### 3d. REFUTED — the half-spread hypothesis

This session's own leading worry was that entry is a mid (`latest_closed_m15_close`) while exit is a
quote side (`tick_ask` for SHORT, `tick_bid` for LONG), making part of the gap an accounting boundary
rather than a defect. The asymmetry is real but does not explain the numbers: over 234 disagreeing rows
`|delta|/spread_r` has median **0.289** and max **27.6**, correlation with `spread_r` is **+0.080**
(−0.027 on the stop family), and the residual against a half-spread has a standard deviation 4.3× its
mean. Decisively, `final_target` deltas are uniformly **positive**, and a quote-side penalty is adverse
in both directions [MEASURED].

### 3e. CORRECTED — the cash headline was double-counting the engine's own allowance

The first cash restatement charged the **full** measured gap on top of a `cost_r` that already
contains `expected_slippage_r`. The price-derived R embeds the realised slip, so leaving the modelled
allowance in cost charges the same thing twice. The reducer's own code comment warned about exactly
this risk and then concluded that holding cost at the ledger value "cancels both" — a non-sequitur;
holding it fixed is what locks the double-count in.

The headline is now **netted per trade** — each trade's own allowance against its own gap — which is
roughly **2.4× smaller**. The un-netted figure is retained as
`cash_delta_UPPER_BOUND_gap_not_netted`, since the engine documents nothing about what the 0.02
covers, so the truth is bracketed rather than asserted.

### 3f. FIXED — five defects in the reducer, found by an adversarial code pass

| # | defect | fix |
|---|---|---|
| 1 | `MIN_RISK_DISTANCE` was an absolute constant, so a **one-ULP stop at BTCUSD/NAS100/US30 scale** cleared it and yielded R ≈ 1e11 with no cap downstream | floor is now relative to `entry_price` |
| 2 | **negative `risk_cash` was accepted** — weaker than the analyzer it checks, which raises `trade_risk_not_positive` (`analyze…:787-790`) | refuses on `<= 0` |
| 3 | `classify_exit_family`'s LEVEL set **omitted `trailing_stop`, `tp1_*`, `final_target_after_tp1_same_bar`, `stop_first_same_bar_conservative` and the three `same_bar_*_ambiguous` branches**, all of which book a threshold. Harmless on January/April, would silently under-report on May/March | all seven added; UNKNOWN is now a **third family**, excluded *and* counted, instead of folding into MARK |
| 4 | a `--sealed-arm` naming no `--arm-window` was **silently discarded**, and the window then printed "no binding was given" — a false statement | hard `parser.error` |
| 5 | the receipt carried no `tool_sha256`, so nothing bound an output to the code that made it | added |

Minor, also fixed: `"1_234.5"` parsed as a number (Python underscore literal; no JSON producer emits
it). Noted and not fixed: `Decimal` is refused as unparseable — conservative, and it never appears in
JSON.

### 3g. FIXED — a mis-binding in the reducer itself

An earlier revision matched an arm to a sealed comparand by substring, and silently reconciled the
**April** S1R1 partial against **January's** S1R1 seal — a different window with no audit of its own.
Binding is now explicit via `--sealed-arm WINDOW=ARM`; an unbound window reports
`no_sealed_comparand_reason` rather than a wrong comparison. This is exactly the class of error the
tooling exists to prevent, so it is recorded rather than silently repaired.

---

## 4. The finding: F31 — the replay's exit model grants zero gap-through [MEASURED]

**Mechanism** [VERIFIED]. The replay closes a trade two ways:

| family | how R is booked | `dynamic_execution_policy.py` |
|---|---|---|
| **level** | a threshold; **no price consulted** | stop `:428` · giveback `:509` · final target `:462-467` |
| **mark** | the observation's own price-derived R | path end `:641` · time stop `:626` |

`final_r = partial_realized_r + remaining_fraction * exit_r` (`:379`), and `exit_index = obs.index`.

On a level exit the engine fires *because* the observed R has already crossed the threshold — in tick
mode each observation is one executable close-side quote with
`open_r = high_r = low_r = close_r = r_value` (`v4_timewarp…:60797-60810`) — and then books the
**threshold**, discarding the crossing observation's own R. It holds the executable value and does not
use it.

**Measurement.** Over the 212 covered level-exit rows in the four sealed January arms — every one
`terminal_r_source == "tick"` with `executable_close_side == true`, and headline `gross_r` equal to the
exit block's `final_r` on all 212 [MEASURED]:

| close_reason | rows | adverse | Σ gap-through R | mean |
|---|---:|---:|---:|---:|
| `selected_policy_replay:stop_loss` | 107 | 107/107 | −4.901273 | −0.045806 |
| `selected_policy_replay:giveback_close` | 97 | 97/97 | −3.733123 | −0.038486 |
| `selected_policy_replay:final_target` | 8 | 0/8 | +0.539109 | +0.067389 |
| **net** | **212** | | **−8.095288** | −0.038186 |

All 107 stop rows book exactly **−1.0**; all 8 target rows book exactly **+2.0**. The giveback identity
`final_r == mfe_r − giveback_close_r` holds **exactly on 121/121** giveback rows across the four arms,
with `transitions[0].index == exit_index` on 121/121 [MEASURED].

**It is not compensated.** The engine charges a flat `expected_slippage_r = 0.02` per trade
(`agent_config.yaml:740`, consumed `broker_net_cost_engine.py:544-556`, summed `:578-584`):

| arm | level rows | measured gap-through | full slippage budget | shortfall |
|---|---:|---:|---:|---:|
| S0R0 | 58 | −1.98637 | 1.800 | 0.18637 |
| S1R0 | 52 | −2.12031 | 1.540 | 0.58031 |
| S0R1 | 55 | −1.94705 | 1.720 | 0.22705 |
| S1R1 | 47 | −2.04155 | 1.440 | 0.60155 |
| **four arms** | **212** | **−8.0953** | **6.500** | **1.5953** |

The budget is levied on all 325 physical rows and still covers only **80.3 %**. Netting each trade's
own allowance against its own gap leaves **−3.855 R uncovered** across the four arms.

And **8.0953 R is a lower bound**: 47 level-family rows carried no executable close-side quote and were
refused, never imputed. An independent verifier that *does* impute them at pooled per-reason means puts
the full-window figure at **−10.169 R / 63.9 % coverage**; that number is cited as corroboration, not
adopted, because imputing is what this reducer refuses to do. The refused rows are also **not random** —
they are precisely the `stop_reached_before_target` / `target_reached_before_stop` rows, i.e. the
population most likely to gap through is the population least measured.

**Nothing is spare on the entry side.** Across all four arms, `entry_price` vs
`limit_requested_entry_price` shows **zero adverse rows** and +2.93 to +3.08 R per arm of *favourable*
drift, already banked in `gross_r`. Realised adverse entry slippage in this window is zero, so the 0.02
is not being consumed there and released to the exit side.

**It is declared as an omission, not as a compensation.** The rows carry
`net_cost_scope = "broker_calibrated_pretrade_cost_rebased_to_effective_fill_r_not_close_side_all_in"`
and `close_side_all_in_cost_status = "not_joined_in_replay_net_proxy_r"` — the engine states the close
side is not costed. No artifact anywhere claims the 0.02 discharges it, and
`B7_5_SELECTION_SIZING_EXPERIMENT_PROTOCOL.json` contains **zero occurrences of the string
"slippage"** [MEASURED]. So "undeclared" is too strong; "stated boundary, uncompensated" is right.

### 4a. What it does and does not change

**The campaign's decision is undisturbed** [MEASURED]. Restating every covered level-exit trade at its
price-derived R, **netting each trade's own `expected_slippage_r`** so the allowance the engine already
charged is not charged twice (§3e). The un-netted upper bound is shown alongside, because what the 0.02
covers is undocumented and the honest position is a bracket, not a point:

| arm | sealed q | restated q | sealed cash | restated cash | upper bound |
|---|---:|---:|---:|---:|---:|
| S0R0 | −0.022368 | **−0.031550** | −201.31 | **−283.95** | −399.95 |
| S1R0 | −0.071506 | **−0.085536** | −550.60 | **−658.63** | −762.63 |
| S0R1 | −0.132896 | **−0.142697** | −5,432.33 | **−5,832.99** | −6,381.80 |
| S1R1 | −0.174636 | **−0.197938** | −6,596.06 | **−7,476.15** | −7,993.71 |

Netted, the four-arm gap is **−3.855 R** and the cash impact **−1,471**; un-netted, −8.095 R and
−2,412.

- **Arm ordering unchanged**: S0R0 > S1R0 > S0R1 > S1R1, sealed and restated — on both the netted and
  the un-netted basis.
- **All four factorial classifications unchanged**, largest shift **0.0135** against the protocol's
  symmetric materiality band of **0.1** — an order of magnitude inside it.
- The per-trade gap of **0.029–0.035 R** already sits inside the campaign's own
  `extra_cost_0.05r_per_trade` stress band, whose classifications are unchanged at 0.05.

**Absolute economics move materially.** S0R0's q goes from −0.0224 to **−0.0316** netted (−0.0444 at
the upper bound) — the reference arm loses **1.4× to 2.0×** what the seal states per risk dollar. Any
absolute claim carried into April, May or the sealed March challenge inherits that understatement
unless bounded.

**So F31 is an absolute-economics and canary-readiness defect, not a campaign-blocking one.**

---

## 5. The three live-path test gaps (plan Phase 1 item 3)

| gap | file | tests | verification |
|---|---|---:|---|
| **F12** SHORT `_compute_r` | `tests/test_exit_wiring_short_r.py` | 18 | mutation-proven |
| profile overlay + account currency | `tests/test_sizing_profile_overlay_and_currency.py` | 14 | real profiles + real broker export |
| live-config truth (E1c/F8) | `tests/test_live_config_truth.py` | 27 | behavioural, against shipped config |
| the reducer itself | `tests/test_shadow_reducer_v2.py` | 85 | AST census + refusal semantics + every §3f fix |

**F12, mutation-proven** [MEASURED]. With the SHORT branch of `orchestrator.py:10254-10255` sign-flipped,
**15 of 18** new tests fail (the 3 survivors assert R = 0 at entry, which is sign-invariant) while
`tests/test_exit_wiring.py` stays **14/14 green** — F12 demonstrated rather than asserted: a SHORT sign
flip flips no LONG assertion. `orchestrator.py` was restored byte-identically and `git diff` is empty.

**Sizing** [MEASURED]. `CLAUDE.md` §4's "NAS100 2×, US30_cash 0.5×" is **replay relative to live** —
NAS100 FTMO 0.50 % vs FN 0.25 %, US30_cash FTMO 1.00 % vs FN 2.00 %. The direction is now pinned,
because the bare ratios read either way. The overlay is not only the risk dial: `contract_size` is 1.0
(FTMO) vs 10.0 (FN) and `trade_tick_value` 0.01 vs 0.1 on both symbols, so for NAS100 the two factors
**compound** to a **20×** replay-vs-live lot ratio, hand-computed through the real `_calculate_lots`.

From the server export: of 19 instruments, 18 are shared and **all 18 differ**; 6 differ on
`trade_contract_size` — five index CFDs move FTMO 1.0 → FN 10.0 while **ETHUSD inverts**, 10.0 → 1.0, so
a blanket "FN is 10×" rule would size ETHUSD 100× wrong. JP225 differs in `digits` (2 vs 0), `point`
(0.01 vs 1.0), `trade_tick_size` (0.01 vs 1.0) and **`currency_base` (JPY vs USD)** but *not* in
`trade_contract_size`.

The currency finding is an absence, and it is stated as one: **there is no account-currency conversion
step anywhere in `src/`**. `_calculate_lots`'s tick-value branch multiplies raw metadata and converts
nothing; its last branch says in its own comment that it is "correct for USD-quoted instruments". What
actually protects the live path is a **refusal**: `require_broker_geometry=True` returns `None` rather
than falling through (`execution.py:9183-9192`), because `order_calc_profit` is account-currency-correct
by construction. Both the refusal and the unguarded fallback are pinned.

A trap the test also pins: JP225's `trade_tick_value` differs **98×** between brokers, but tick value
and tick size diverge together and cash-risk-per-lot agrees to under **2 %**. Comparing `trade_tick_value`
across brokers is meaningless alone.

---

## 6. Whole-suite A/B [MEASURED]

Whole suite, `--continue-on-collection-errors`, compared as failure **SETS** via
`scripts/pytest_failset.py diff` against `receipts/baseline_full_suite.json`, never as counts.

```
before 212ad7e6d ('Stop my contract test from breaking three replay tests…'): 683 bad
after  acad79826 ('Move Session D out of the phase1 folder; it is Phase 2 work'): 685 bad
unchanged: 683   fixed: 0   REGRESSED: 2
```

**Zero regressions are attributable to this session's changes.** Both entries are accounted for, and
the second is the more interesting:

| entry | cause |
|---|---|
| `test_end_to_end_integration.py::TestCrossComponentIntegration::test_high_load_integration` | the **known non-deterministic test** (pass/pass/fail over three identical runs), named as carried noise in the G0 receipt and the Session A prompt |
| `test_permissions.py::test_scheduler_v4_terminal_gate_carries_ultimate_candidate_package_shadow_packet` | **a worktree environment difference, not a code change** |

### 6a. B33 — the committed baseline is not portable across worktrees [MEASURED]

The permissions failure is **not** caused by anything in this session. It fails with *only that one
node id collected*, so none of this session's files are even imported, and no `src/` or `config/` file
differs from the baseline commit apart from one unrelated `book_engine.py` commit.

Root cause, measured:

| worktree | `…/ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl` |
|---|---|
| `phase1-shadow-reducer-20260726` (here) | **131 bytes — un-hydrated LFS pointer** |
| `claude-opus5-architecture-audit-20260725` (where the baseline was captured) | **205,754 bytes — real file** |

The test does `package["selector_packets"][0]`; with a pointer in place of the registry the list is
empty and it raises `IndexError`.

**Proven by experiment**, not by inference: copying the hydrated file in makes the test **pass**;
restoring the pointer makes it **fail** again; the restore was byte-identical (`git status` clean,
sha256 unchanged both sides).

This is B3's partial-hydration finding biting a second time, and it has a consequence for the whole
parallel-session protocol: **every Phase 1 session diffing against
`receipts/baseline_full_suite.json` from its own worktree will see this same phantom regression.**
The baseline records a commit but not the LFS hydration state of the tree that produced it. Either the
baseline needs re-anchoring per worktree, or `pytest_failset.py` needs to record hydration state
alongside the commit. Flagged for the sibling clock-truth and red-suite sessions.

### 6b. New tests, all green [MEASURED]

`147 passed` across the four new files (`test_shadow_reducer_v2.py` 85, `test_live_config_truth.py` 27,
`test_exit_wiring_short_r.py` 18, `test_sizing_profile_overlay_and_currency.py` 14). No `src/`,
`config/` or existing test file was modified by this session; every change is additive.

---

## 7. Verdict

**G1a MET, on the "filed economic defect" branch, with the gaps in §8 declared.**

The sealed analyzer's economics **survives an independent recomputation as arithmetic** — 24 of 24
values reproduced — and **does not survive it as a statement about realised economics**. The gap is not
in the ledger and not in the analyzer; both are sound. It is in the replay's exit model, and the entire
proof layer is blind to it for exactly the reason E3 predicted: nothing recomputes R from prices.

---

## 8. Declared gaps — required output, not an admission

- **Price coverage is 84.1 / 88.0 / 83.3 / 85.7 % of scoreable rows** on the four January arms. 47
  level-family rows across the four arms carry no executable close-side quote and are **refused, never
  imputed**, so −8.0953 R is a lower bound and the true figure is larger.
- **The April partial is too thin to carry a conclusion.** 39 physical rows, 31 scoreable, **8
  recomputable — 25.8 % coverage**, of which only **3** are level exits. Its reported gap-through of
  −0.316 R rests on three trades. Its `modelled_allowance_covers_measured_gap: true` is an artifact of
  that coverage and must not be read as April being clean.
- **April is 15 sealed days, not 16** [MEASURED] — the 16th (2026-04-16) has shards but no
  `COMPACT_EVENT_MANIFEST.json` and contributes zero rows to any JSONL ledger. Of the 15, only **9 are
  trading sessions**. The arm suffix is `SOURCE_REPAIRED_R5_CAP_R2`, not R3. `SESSION_A_SHADOW_REDUCER.md`
  §2's "16 sealed days" should read 15.
- **No April comparand exists.** No arm receipt, no matrix audit, no independent verification — confirmed
  by exhaustive search, not assumed. Nothing on disk validates or contradicts the April reduction.
- **`cost_r` exceeds the sum of its four named components on 14 of 88 sealed S0R0 rows**, always in that
  direction. Not pursued; it makes the engine's costing *more* conservative, and it is why the headline
  projection holds ledger `cost_r` fixed rather than reconstructing it. The fifth cost element was not
  identified.
- **8 EURUSD rows across the four arms carry `spread_r == 0.0`** with `measured_tick_spread_floor_r`
  null. A zero spread on EURUSD is not physical. Two rows per arm, consistently the same trades, so it
  cannot bias the arm contrast — but it understates absolute cost. Not investigated further.
- **F17's coercion signature is absent from this evidence class** [MEASURED]. Zero exact-`0.0` values in
  any price-bearing field across all five arm-windows. Absence is expressed as JSON `null` throughout.
  The reducer's zero-price refusal never fired on real data; it is proven by unit test instead.
- **This session did not verify the tick source itself.** The reducer trusts `exit_price` as the quote at
  `exit_index`; it did not open `microstructure_ticks.jsonl.gz` to confirm that quote. Whether the
  crossing observation is the *first* executable quote past the threshold, or a later one, is
  **NOT ESTABLISHED** — and it bounds how much of the 8.1 R is genuine gap-through versus observation
  granularity.
- **No live-path claim is made.** F31 is measured in replay. H7 applies: replay does not measure the live
  system, and the live `ultimate_book` path has its own exit model that this session did not examine.
- **The netting basis is a judgement, not a measurement.** Netting `expected_slippage_r` against the gap
  assumes the constant was meant to cover exit slip. Nothing documents what it covers. Both bounds are
  published and the headline takes the conservative one, but the true figure is bracketed, not known.
- **The refused rows are not a random sample.** They are the `stop_reached_before_target` /
  `target_reached_before_stop` families — the population most likely to gap through is the population
  least measured.
- **No same-worktree baseline was captured** (§6a). The divergence was explained by direct experiment
  instead, which costs one test run rather than a second full-suite capture.

---

## 9. For the owner — one item, and it is not urgent

**F31 does not change the B7.5 decision.** Arm ordering, all four factorial classifications, and the
protocol's materiality band are all unchanged, and the measured per-trade gap already sits inside the
campaign's own 0.05 R stress band. **No re-run is indicated and nothing here blocks the April window.**

What it does change is any **absolute** economic claim. The reference arm loses about twice per risk
dollar what the seal states. That matters at exactly one place in the plan — the canary-readiness
decision, where absolute economics is the criterion rather than an arm contrast. Recommend the exit
model gains a gap-through term before any absolute number is carried to a live-activation argument;
that is Phase 2 core work, not a Phase 1 repair, and it is recorded here rather than acted on.

---

## 10. Reproduction

```bash
R=/Users/borr/GTOSActive/worktrees/replay-accel-engine-20260719/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20
P=BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_SELECTION_SIZING
S=SOURCE_REPAIRED_R3_CAP_R2_TRADE_LEDGER.jsonl
A=$R/attempt_5_typed_sparse/PHASE_D_APRIL_S1R1_R1_20260725T070249Z/BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_04_SELECTION_SIZING_S1R1_SOURCE_REPAIRED_R5_CAP_R2_TRADE_LEDGER.jsonl

python3 docs/audits/fable5-vision-audit-20260725/phase1/shadow_reducer_v2.py \
  --arm-window "JAN_S0R0=$R/${P}_S0R0_${S}" --sealed-arm JAN_S0R0=S0R0 \
  --arm-window "JAN_S1R0=$R/${P}_S1R0_${S}" --sealed-arm JAN_S1R0=S1R0 \
  --arm-window "JAN_S0R1=$R/${P}_S0R1_${S}" --sealed-arm JAN_S0R1=S0R1 \
  --arm-window "JAN_S1R1=$R/${P}_S1R1_${S}" --sealed-arm JAN_S1R1=S1R1 \
  --arm-window "APR_S1R1_PARTIAL=$A" \
  --matrix-audit research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16/B7_5_SELECTION_SIZING_DEVELOPMENT_JANUARY_SOURCE_REPAIRED_R3_CAP_R2_MATRIX_AUDIT.json \
  --out docs/audits/fable5-vision-audit-20260725/phase1/receipts/five_arm_windows.json
```

Runs in under a minute on this machine. The sealed trees are opened read-only; H4's producing-worktree
constraint does not apply because no replay is launched.
