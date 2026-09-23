# p2 — THE TAKE-PROFIT: reproduced exactly, then taken apart

**Wave 20 forward, lane p2. 2026-08-07.** Owner standing approval to land
(*"even if it touches live i approve it, i give full approval"*).

Commission: the forensic's lane g3 found *"the stop is not the defect, the fixed take-profit
is"* — deleting it worth **+0.25 to +1.50 bps/trade** across three reversion families at two
horizons, **six of six bootstrap CIs excluding zero**, traced to one key,
`config/agent_config.yaml:39` `min_rr: 1.5  # vNext sanity floor only`. p2 was told to establish
the blast radius, reproduce the measurement on the repaired walker, design the repair properly,
measure it on the broad families *and* the sleeve estate, reconcile with AD, and land it.

---

## 0. THE ANSWER

**g3's number is right and g3's conclusion is not.** p2 reproduced the measurement to four
decimals through a completely different code path, then applied three controls the original did
not have. The effect survives all three in magnitude and **fails the one that matters**:

| control | what happened to +0.25…+1.50 bps |
|---|---|
| quote-side-repaired walker (`029b2fc1c`) | survives, **shrinks 23–43 %** |
| out of sample (calendar split) | survives — the second half is *larger* than the first |
| resolution: geometric ladder → every M15 bar → **every M1 minute** | survives, shrinks again; the grid explains only **0.73–1.67 %** of rows |
| **coin-flipped direction placebo** | **reproduces 71–180 % of it, at every resolution** |

At M1 resolution, at the 2 h horizon these families actually resolve at, **five of seven broad
families have a family-specific residual at or below zero.** Deleting the take-profit is not
evidence about any family's idea. It is a property of a fixed-R cap on this price process — and
the mechanism is measured, not asserted (§4).

**And the same control, turned on the sleeve estate, reaches armed money.** AD's exit frontier
has never had a side control. Across 29 sleeves the best exit cell improves on the real
directions **26 of 29** times; after the coin flip is subtracted, **18 of 29**. Median best-cell
gain **+0.1136 R/day**, of which **+0.0409 is earned — 64 % of the median exit-frontier
improvement is available on a coin flip.** On the two cells that reach a decision:

| cell | status | Δ R/day | coin-flip placebo | **earned** |
|---|---|---:|---:|---:|
| `sub_xvol_pullback @ target_4R` | **ARMED sleeve**, wired at `--frontier-exits`, default off | +0.6508 | **+0.4981** | +0.1528 (**23.5 %**) |
| `mx_btcusd @ target_5R` | the estate's **one standing admission** | +0.3936 | **+0.3139** | +0.0797 (**20.3 %**) |
| `energy_agri @ target_5R` | **ARMED sleeve** | +0.4552 | +0.2674 | +0.1877 (41.2 %) |
| `asian_fade @ target_4R` | not armed | +1.3936 | **+1.2849** | +0.1088 (**7.8 %**) |
| `metal_session_reversion @ target_5R` | not armed | +0.7927 | +0.8129 | **−0.0202 (negative)** |

With day-block intervals (§5.1) the earned component of **every one of those cells straddles
zero**. The single exception in the whole estate is `asia_pdl_fade @ target_5R`, earned
**+0.0526 R/trade [+0.0028, +0.1043]** on 2,827 trades — the forensic's own confirmed keep-list
member, arrived at from completely different evidence.

**The repair landed is therefore governance, not geometry** — and it is the one the brief
predicted: stop a risk sanity floor from silently acting as an exit policy. It moves **zero**
emissions on the whole 471,269-row population (§6) and it makes the coupling named,
provenanced, unit-tested and impossible to inherit by accident.

---

## 1. BLAST RADIUS — `min_rr`, established by execution, not by grep

`P2_BLAST_RADIUS_V1.json`, `p2_00_blast_radius.py`.

### 1.1 The armed book cannot see it. Measured two ways.

**(a) The live entrypoint's import closure.** `run_book.py` — the process both funded accounts
run — reaches **234** first-party modules. `broader_origin_generators`, `orchestrator`,
`permissions` and `expired_poi_watch` are **in none of them**. `min_rr` has no path to the
armed book.

**(b) The armed sleeves' take-profits come from somewhere else, and the builder has no config
argument to read the key from.** `build_book_trade_params`'s live signature is
`(sized_unit, intent, geometry, account_state, *, profile_namespace, frontier_exits=())`
(`execution_packets.py:506-507`) — no `config`. Executed for every armed sleeve:

| sleeve | profile source | resolved `final_target_r` | implied RR on a 1.0 stop |
|---|---|---:|---:|
| `crypto` | `SLEEVE_EXIT_PROFILES:80` | 4.0 | 4.0 |
| `energy_agri` | `:93` | 4.0 | 4.0 |
| `sub_xvol_pullback` | `:84` | 3.0 | 3.0 |
| `sub_mid_dn_revert` | `:85` | 3.0 | 3.0 |

**No armed sleeve's target derives from `min_rr`.** That is the answer to the brief's first
question, and it is what made the rest of the lane safe to run at speed.

### 1.2 Where it does act as a target

| site | role | reachable from `run_book.py` |
|---|---|---|
| `broader_origin_generators.py:2489-2492` (at the PARENT `eeb73b090`; after this lane, `:2561` / `:2634` / `:2691`) → `:322` → `_candidate` | **THE defect.** the only source of `target_rr`; becomes `take_profit_1` for all eleven broad families | no |
| `orchestrator.py:5062-5065` → `:5111-5113` | `final_target_r = max(tp.risk_reward_ratio, min_rr)` then rebuilds `take_profit_1` off the LIVE fill. **Both terms are `min_rr`** for a broad candidate, because the generator already set `risk_reward_ratio = min_rr` | no |
| `permissions.py:2116, 2149-2150, 2160-2161` | rebuilds the TP at `min_rr` when auto-correcting inverted geometry — **dead**: `config/agent_config.yaml:43` is `inverted_geometry_policy: reject`, so `:2138-2143` returns an `ExecutionDenial` first | no |
| `expired_poi_watch.py:204/483/560`, `batch_backtest.py:815-817`, `backtest_runner.py:691-693` | **FLOOR** — a rejection threshold. The documented use | no |
| `dumb_baseline.py`, `ob_zone_test.py`, `ob_zone_original_geometry.py`, `simulate_t7_live_period.py:990-999` | research harnesses that also use it as a target | no |

---

## 2. REPRODUCTION — g3's number, through different code

`p2_10_regen.py`, `p2_20_walk.py`, `P2_TARGET_DELETION_V1.json`.

g3 re-implemented three families' arithmetic by hand in numpy. p2 **drives the production
generator** — `_generate_single_symbol_candidates`, unmodified — over the same 24-symbol,
12-month true-UTC M15 tape, which is both an independent check and the only honest basis for
measuring a change to that function.

**Control, family counts:** `structural_distance_extreme` 36,803 vs g3's 36,803 (exact);
`liquidity_sweep_reclaim` 69,307 vs 69,307 (exact); `range_extreme_reversion` 276,249 vs
276,246 (**3 rows**, 0.001 %, a window-edge boundary at index 51). Two implementations, one
tape, the same answer.

**Control, economics** — on g3's own convention (`UNCORRECTED`: spread 0, both legs unshifted
on the bid tape, the geometric horizon ladder), at 2 h:

| family | g3 shipped | p2 shipped | g3 Δ(no target) | p2 Δ(no target) |
|---|---:|---:|---:|---:|
| `structural_distance_extreme` | −0.2505 | **−0.2505** | +0.6623 | **+0.6623** |
| `liquidity_sweep_reclaim` | −0.1973 | **−0.1973** | +0.5110 | **+0.5110** |
| `range_extreme_reversion` | +0.0575 | +0.0577 | +0.2465 | +0.2463 |

Reproduced. Everything after this point is a correction to the reading, not to the arithmetic.

### 2.1 The repaired walker

Three conventions, all published (`p2_20_walk.py` docstring for the derivations):

- `UNCORRECTED` — the pre-`029b2fc1c` convention. The control.
- `LIVE` — what `orchestrator.py:5075-5124` + `execution.py:3247`/`:6953` actually do on a BID
  tape: LONG fills at the ask and its absolute stop resolves on the bid unshifted; SHORT fills
  at the bid exactly and **both** exit legs transact on the ask, so each triggers one spread
  lower. That asymmetry is imposed by the archive, not chosen.
- `FILL_SYM` — r1's canonical `anchor = c + direction·spread`, symmetric between the sides,
  carried so the verdict cannot be an artifact of `LIVE`'s asymmetry.

The target-deletion delta at 2 h, `LIVE`: `structural_distance_extreme` +0.6623 → **+0.3796**;
`liquidity_sweep_reclaim` +0.5110 → **+0.3950**; `range_extreme_reversion` +0.2463 →
**+0.1472** (its CI now includes zero).

**The levels move far more than the deltas.** g3 reported that with the target deleted the three
families are "1.9–2.7 bps short of the 3.02 bps round-trip toll". On the repaired walker the
spread is charged **as geometry**, so the correct comparison is against
`toll_bps_nospread = 1.358` (lane m1's own artifact, `M1_FUNNEL_V1.json →
funnel.C_filled_repaired_BOTH`) — **not** 3.02, which would double-charge. At that standard the
best repaired no-target cell in the lane is `range_extreme_reversion` at 24 h, **−0.4479 bps**,
which is **1.81 bps short**; the range across the seven families is **1.81 to 2.49 bps short**.
g3's economic conclusion — *"it does not open a book"* — stands and is unchanged by anything
here; only its attribution changes.

---

## 3. THE CONTROLS — and the one it fails

`p2_30_robustness.py` / `P2_ROBUSTNESS_V1.json`; `p2_40_resolution.py` /
`P2_RESOLUTION_V1.json`.

### 3.1 Out of sample: survives

Calendar split at 2025-12-06. The delta is **larger** in the second half on 5 of 7 families at
2 h (`liquidity_sweep_reclaim` +0.0952 → +0.7116; `structural_distance_extreme` +0.2210 →
+0.5491). It did not die out of sample.

### 3.2 Resolution: survives, but shrinks

The same rows, the same geometry, only the grid on which stop-versus-target order is resolved
changes — measured against the **M1 tape** (11 of 12 months, all 24 symbols; 2025-07 is absent
from the M1 packs and is excluded from *all three* arms so the comparison is between grids and
not between populations).

Target-deletion delta, 2 h, `LIVE`:

| family | geometric ladder | every M15 bar | **every M1 minute** |
|---|---:|---:|---:|
| `structural_distance_extreme` | +0.3712 | +0.3126 | **+0.1564** |
| `liquidity_sweep_reclaim` | +0.4441 | +0.3561 | **+0.3482** |
| `range_extreme_reversion` | +0.1645 | +0.0615 | **+0.0555** |

### 3.3 Side placebo: **FAILS**

Coin-flip each emission's direction (seeded), rebuild the stop at the *same distance* on the new
side, change nothing else. The families' directional claim is destroyed and the contract is not.

2 h, `LIVE`, at M1:

| family | real | **placebo** | family-specific residual |
|---|---:|---:|---:|
| `liquidity_sweep_reclaim` | +0.3482 | +0.2488 | **+0.0994** |
| `session_open_range_break` | +0.0302 | −0.0059 | +0.0360 |
| `volatility_compression_expansion` | +0.0184 | −0.0210 | +0.0394 |
| `regime_transition_break` | −0.0585 | −0.0173 | −0.0412 |
| `displacement_continuation` | +0.1651 | +0.2389 | **−0.0738** |
| `structural_distance_extreme` | +0.1564 | **+0.2629** | **−0.1065** |
| `range_extreme_reversion` | +0.0555 | **+0.2367** | **−0.1812** |

**Five of seven at or below zero.** The one family whose residual is worth naming is
`liquidity_sweep_reclaim` at +0.0994 bps — 6 % of what g3 priced for it at 24 h, and 2.5 % of
the 1.358 bps residual toll it must clear.

*(A time placebo — the same geometry judged against another bar of the same symbol-day — is also
published. It runs strongly negative at 2 h for the reversion families, which is the expected
sign for range-conditioned setups and is why g3's own within-week placebo was discarded as
invalid. It is reported, not relied on.)*

---

## 4. THE MECHANISM — measured, so the placebo is not just an odd number

`p2_70_mechanism.py` / `P2_MECHANISM_V1.json`.

The whole delta lives on one subpopulation: rows where the take-profit arm **reaches its
target**. Everywhere else both arms resolve identically and the difference is exactly zero. So

```
delta = P(target reached) x ( E[targetless outcome | target reached] - target )
```

— a single conditional expectation: *after price has moved +2R in whatever direction you happen
to be positioned, what happens next?* Under a martingale the answer is +2R and the delta is
zero. Measured at M1, 2 h, `LIVE`:

| family | n reaching target | mean target | mean targetless outcome, same rows | **continuation premium** |
|---|---:|---:|---:|---:|
| `structural_distance_extreme` | 7,896 | 11.899 bps | 12.530 | **+0.631** |
| `liquidity_sweep_reclaim` | 11,803 | 25.381 | 27.166 | **+1.784** |
| `range_extreme_reversion` | 41,827 | 30.639 | 30.958 | **+0.319** |

And on the coin-flipped population the same premium is **as large or larger** (+1.170, +1.554,
**+1.610**). Conditional continuation after a 2R excursion is a property of the tape.

**The competing explanation is priced and refuted.** The coarse grid can book a stop where a
finer walk books a target; that would inflate the delta without any economics. Exit reasons
differ between the geometric ladder and M1 on **531/31,858 (1.67 %)**, **440/60,488 (0.73 %)**
and **2,222/239,859 (0.93 %)** of rows. Not the driver. The mechanism is continuation, and
continuation is sideless.

---

## 5. RECONCILIATION WITH AD — the part that reaches armed money

`p2_50_estate_placebo.py`, `p2_55_estate_ci.py`.

The brief asked that this be reconciled with AD's exit sweep rather than stacked on it. It
reconciles by **inheriting the same defect**.

AD's own machinery, unmodified — `ad_exit_sweep.resimulate`, AD's rows
(`phase6/receipts/AA_ESTATE_TRADES.json.gz`), AD's bar archive. The only thing that changes
between arms is `row["direction"]`, coin-flipped with a fixed seed.

- best cell improves on the real directions: **26 of 29 sleeves**
- best cell improves after subtracting the coin flip: **18 of 29**
- median best-cell Δ **+0.1136 R/day**; median **earned +0.0409 R/day** → **64 % of the median
  exit-frontier improvement is sideless**

### 5.1 With intervals, on the rows that reach a decision

Point estimates are not enough when `sub_xvol_pullback` has 88 trades. Day-block bootstrap,
4,000 reps, paired per row, on **R/trade** (`P2_ESTATE_SIDE_PLACEBO_CI_V1.json`):

| sleeve | cell | n | Δ | placebo | **earned** | earned CI95 | p(≤0) | placebo share |
|---|---|---:|---:|---:|---:|---|---:|---:|
| `sub_xvol_pullback` **ARMED** | `target_4R` | 88 | +0.2810 | +0.2151 | +0.0660 | [−0.1147, +0.2375] | 0.239 | **77 %** |
| `mx_btcusd` **admission** | `target_5R` | 318 | +0.3936 | +0.3139 | +0.0797 | [−0.1069, +0.2711] | 0.212 | **80 %** |
| `energy_agri` **ARMED** | `target_5R` | 67 | +0.2649 | +0.1557 | +0.1093 | [−0.0672, +0.2871] | 0.103 | 59 % |
| `sub_mid_dn_revert` **ARMED** | `target_5R` | 503 | +0.1115 | +0.0793 | +0.0322 | [−0.0973, +0.1564] | 0.313 | 71 % |
| `crypto` **ARMED** | `target_5R` | 181 | −0.0487 | −0.0196 | −0.0291 | [−0.1881, +0.1031] | 0.635 | — |
| `asian_fade` | `target_4R` | 1,319 | +0.6995 | +0.6449 | +0.0546 | [−0.0476, +0.1566] | 0.153 | **92 %** |
| `metals_core` | `target_4R` | 385 | +0.0575 | +0.0321 | +0.0254 | [−0.0378, +0.0966] | 0.236 | 56 % |
| **`asia_pdl_fade`** | **`target_5R`** | **2,827** | **+0.0248** | **−0.0278** | **+0.0526** | **[+0.0028, +0.1043]** | **0.019** | **−112 %** |

**Not one exit cell in the estate's headline set has a directional component distinguishable
from zero.** The two that reach a decision — the ARMED `sub_xvol_pullback @ target_4R` and the
standing admission `mx_btcusd @ target_5R` — are **77 % and 80 % placebo** with earned intervals
straddling zero. This is corroboration, not contradiction, of what the estate already decided:
AU gated `sub_xvol_pullback @ target_4R` at the ratified rule and it **REJECTS at all four
bands** (p 0.0080), and AS handoff 3 is *"do not propose it."* p2 supplies the mechanism for why
that cell looked good in the first place.

**One cell passes, and it is the forensic's own keep-list member.** `asia_pdl_fade @ target_5R`
is the single row whose earned interval excludes zero — earned **+0.0526 R/trade [+0.0028,
+0.1043]**, p 0.019, on 2,827 trades, with a **negative** placebo (its coin-flipped population
is made *worse* by the wider target). Section 5.1 of `SLEEVE_FORENSIC_REPORT.md` named
`asia_pdl_fade` the one confirmed sound-idea-wrong-contract member on completely different
evidence. It is also the one cell here with real sample. It is not proposed for arming — its
stop repair, not its target, is what that dossier prescribes — but it is the only exit cell in
the estate that survives this control, and that is worth knowing.

This does not overturn AD and is not offered as doing so: AD measured cost-true, gated,
per-sleeve economics over 1,631 cells and this is one control applied to a subset of its
variant family. What it establishes is that **the exit-frontier method has no side control, and
should have one before any further cell selection reaches a book** — the same discipline AR
established for sizing when it proved a book headline was 85 % equity-path artifact.

### 5.2 Nothing here needs carrying

`config/live_armed_set.json` declares `frontier_exits: []` on **both** accounts, and
`scripts/run_book_supervisor.ps1:104-105` sets `frontier=$null` on both rows — the frontier
contract went with `mx_btcusd`'s disarming on 2026-08-05. **No frontier exit is running on
either book.** So §5.1 asks for no ceremony and no owner decision today: it is a constraint on
the *next* exit-cell selection, not a defect in the current one. It is filed as `staged`
because the number belongs in front of Borhen the next time a frontier exit is proposed, not
because anything is waiting on him.

### 5.3 Truncation share, published

The brief requires it, because a "let it run" gain that is really "hold to the clock" is a
horizon claim in disguise. For the no-target arm at `LIVE`
(`P2_TARGET_DELETION_V1.json → no_target.exit_mix.time`): at 2 h it runs **15.7 %**
(`structural_distance_extreme`) to **87.4 %** (`regime_transition_break`); at 24 h **4.1 %** to
**45.7 %**. The families with the largest 24 h deltas are exactly the ones with the largest
truncation shares — `regime_transition_break` +1.65 bps at 45.7 % truncation,
`volatility_compression_expansion` +2.25 at 36.4 % — which is the second reason the 24 h column
is not the one to read. The 2 h column is, because these families' own median time to
resolution is **5 to 25 minutes** (g3 §1.5, §2.5).

---

## 6. WHAT LANDED

### 6.1 The repair

`src/components/broader_origin_generators.py` — **not** R2-bound (checked against the 43 bound
paths and against `replay_acceleration_attempt5_typed_sparse_runner.py:1405-1431`'s
`code_authority_paths`; it is in neither), so **no seal breaks and no option is spent.**

1. **`FAMILY_TARGET_RR`** — a declared take-profit policy per family, each row carrying a value,
   a `basis` (`FOUNDING_ARTIFACT` / `MEASURED` / `UNCHOSEN`) and a provenance string. All
   thirteen rows are `UNCHOSEN` today. **That is the finding, not an omission**: no broad-origin
   family's founding artifact names a target, and p2's own measurement says none has the
   evidence to declare a different one.
2. **`TargetRRPolicy`** — resolved once per config by `_target_rr`. It subclasses `float`
   deliberately: thirty call sites treat `target_rr` as a number, and this way the decoupling
   needs no change at any of them.
3. **`_candidate` is the one choke point** — the only place that knows both the family and the
   geometry — so the per-family decision is resolved there and nowhere else.
4. **A new family cannot silently inherit the risk floor.** With the policy on, an unregistered
   family raises `KeyError` naming `FAMILY_TARGET_RR`. That is the defect class this exists to
   remove.
5. **`risk.min_rr` does only its documented job**: it floors, and the flooring is recorded on
   the emission (`source_fields.target_decision.floored_by_min_rr`).

Default-off behind `gtos_vnext_runtime.broad_origin_target_policy_enabled`, absent from every
config in the tree.

### 6.2 The inertness proof — whole population, isolated from concurrent lanes

`p2_60_inertness.py` / `P2_INERTNESS_V2.json`. Two copies of the module loaded **by path** (the
parent's and the parent's + p2 only), both run over the full 24-symbol/12-month tape.

*(Loading by path is not fussiness: the first run attributed 371 `route_session` differences on
BTCUSD and ETHUSD to this change, and they belong to a concurrent lane's session-naming repair
in the same shared working tree. Isolating the modules removed the ambiguity instead of arguing
about it.)*

| arm | count |
|---|---:|
| **A — policy OFF vs the parent, every field, every row** | **0 / 471,269 mismatches** |
| B — take-profits that move if the key is set, at the shipped dial | **0** |
| C — exit contracts the **legacy** resolver moves when the RISK dial moves 2.0 → 0.5 | 471,269 |
| D — exit contracts the **declared** policy moves on the same dial change | 471,269 |

### 6.3 THE HONEST LIMIT OF THIS REPAIR

**C and D are the same count, and that must be said plainly.** Every declared target is 1.5;
`min_rr` is 1.5 on mainline and 2.0 in the sealed replay (`pbg_run.py:89-90`). So the floor
**binds on 100 % of emissions** and the risk dial still moves every take-profit *upward* with
it. What changes is the exposure: under the legacy resolver a dial at 0.5 shipped a **0.5R
take-profit**; under the declared policy the same dial ships **1.5R**, because the declared
target floors the damage.

**The decoupling is structural, not yet effective.** It bites the first time a family declares a
target above the floor on evidence — and p2's measurement is that no family has that evidence.
This is written into the module banner and pinned by
`test_the_floor_still_binds_and_this_test_exists_to_stop_that_being_forgotten`, which fails the
moment someone declares such a target, forcing the claim to be updated rather than left stale.

### 6.4 Tests

`tests/test_broad_origin_target_policy.py`, 16 tests, behavioural.
`test_ab_against_the_legacy_resolver` encodes the pre-repair resolver **verbatim in the test**
and asserts both directions — OFF reproduces it exactly at every `min_rr`; ON diverges exactly
where the floor was acting as a target. It is written that way so an `ImportError` can never be
mistaken for a behavioural difference.
`test_unregistered_family_fails_loud_instead_of_inheriting_the_floor` and
`test_min_rr_no_longer_moves_the_declared_target` cannot pass against the parent.

---

## 7. WHAT THIS LANE DID NOT DO

- **No target was deleted.** The measurement does not support it, and the brief's own trap —
  *"remove the cap and the winners run is exactly the shape of a result that dies out of
  sample"* — turned out to be right about the shape and wrong about the cause of death: it died
  against the placebo, not out of sample.
- **No sleeve's declared exit changed.** `SLEEVE_EXIT_PROFILES` is untouched;
  `--frontier-exits` remains default-off; the estate placebo is a measurement, not a proposal.
- **No VPS, no broker script, no live-forward P&L.**

## 8. RECEIPTS

| file | what |
|---|---|
| `P2_BLAST_RADIUS_V1.json` | import closure, armed-sleeve packets, every read site classified |
| `P2_TARGET_DELETION_V1.json` | 7 families x 2 horizons x 3 conventions, whole population |
| `P2_ROBUSTNESS_V1.json` | OOS split, side placebo, time placebo, truncation shares |
| `P2_RESOLUTION_V1.json` | **the decisive one** — the ladder to M1, real and placebo |
| `P2_MECHANISM_V1.json` | the continuation premium, and the grid explanation refuted |
| `P2_ESTATE_SIDE_PLACEBO_V1.json` | AD's frontier, 29 sleeves, real vs coin flip |
| `P2_ESTATE_SIDE_PLACEBO_CI_V1.json` | day-block bootstrap CIs on the armed rows |
| `P2_INERTNESS_V2.json` | 0/471,269, module-isolated |
| `regen/` | regenerated emissions, **not committed** — `p2_10_regen.py` rebuilds them in ~25 s |
