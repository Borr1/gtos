# LANE G2 — THE REPLAY LANE: WHAT IT CAN RUN, WHAT IT MEASURED, WHAT IS BLOCKED

**Built 2026-08-12. Measurement and inventory only: no broker call, no VPS touch, no config
byte, no `src/` edit, no git write, no live path.** Code and receipts: `g2_replay/`.
Standing artifact — updated as work completes, so an interrupted session is inherited rather
than rediscovered.

Owner's instruction for this lane: *"keeping the replay lane always active so that progress
never stops it only accelerates more."* Everything below completed in minutes-to-hours. **No
sealed month-arm replay was launched** (16.5 h each; the cost and the blockers are in §1.2).

---

## 0. HEADLINE

> ### The replay lane has TWO surfaces and only the cheap one can run today. The cheap one is enough: it walked the entire 22,343-decision estate at two corrected cost geometries in 35 seconds.
>
> | | sealed B7.5 arm replay | light-weight bar re-walk |
> |---|---|---|
> | cost | **~16.5 h** per month-window (4 arms) | **35 s** full-estate walk; ~3 h full regeneration |
> | months it can run | **January + April 2026 only** | any window the bar archive covers, **1992-2026** |
> | runnable from this worktree | **NO** — 3 path fuses (§1.2) | **YES** |
> | disk it needs | 9.3 GB (must not be deleted) | **65 MB** |
>
> ### The flat slippage constant is WRONG ON THE SLEEVE ESTATE, in a direction nobody had measured, and the size is the largest single correction G2 found.
>
> `expected_slippage_r = 0.02` (`config/agent_config.yaml:740`) was adjudicated CORRECT to
> within 4 % — **at the sealed funnel window's barrier mix of 52.0 % stops**
> (`RECON_SLIPPAGE_ADJUDICATION_V1` §0). The sleeve estate's mix is **67.9 % stop-or-trail**.
> Charging RECON's own barrier-conditional legs instead of the flat constant costs the estate
> **−0.006706 R/trade, day-clustered CI95 [−0.00705, −0.00636], p ≈ 0, n = 22,343 over 3,016
> decision days** — i.e. **−$3.35 per trade / −$74,913 over the estate's history at $500/R.**
> It is not a wash per sleeve and the sign flips: `asian_fade` −0.01932, `metal_session_reversion`
> −0.01932, against `sub_xvol_pullback` **+0.00340** and `idxrev` **+0.00284** (both overcharged
> today). Of the armed three, two are overcharged and one undercharged; the armed set nets
> **−0.002076 R/trade, CI [−0.00492, +0.00064]** — not separable from zero, which is the
> honest read.
>
> ### The B10 hour-surface repair CANNOT move the sleeve estate's published R, and that is a property of the labeller, not evidence the defect is small.
>
> `exits.replay`'s `entry_price` is *"the anchor every level and every realised R is measured
> from"* (`exits.py:317`). Shifting the entry by the spread moves the stop **and** the target
> with it, so a `stop` exit is exactly −1 R and a `target` exit exactly +kR **whatever spread
> was charged.** Only `trail` and `maxbars` exits can move: **1,408 of 22,343 rows (6.3 %)**.
> Measured: the symbol-hour repair changes R on **624 rows (2.79 %)** and the estate-level
> effect is **−0.000999 R/trade, CI [−0.00337, +0.00134], p 0.399 — inert.**
> **The defect is real and it lands in the price domain**, where the repair is
> **−0.000871 R/trade of cost, CI [−0.00307, +0.00151]** estate-wide but **±0.02 R/trade per
> sleeve** (`sub_mid_dn_revert` −0.01561, `asian_fade` −0.01979, `metal_session_reversion`
> +0.00523, `mx_cadjpy` +0.00427). **Price it through cost accounting — the funnel, the cost
> gate, net expectancy — never through the sleeve estate's barrier-labelled R.**
>
> ### The single most decision-relevant number G2 produced is not a correction at all. It is the level.
>
> The estate's **shipped spread cost is 0.1916 R per trade** (mean `spread_price / stop_dist`,
> n = 22,343). The **armed three sit at 0.0416 — 4.6× cheaper than the estate they were drawn
> from.** Two sleeves are structurally uneconomic before any edge question is asked:
> `liq_asia_up_low_metal` at **1.2257** (spread is 123 % of its own stop distance) and
> `asia_pdl_fade` at **0.8920**. No exit contract, entry hour or sizing rule repairs a sleeve
> whose entry cost is its stop.
>
> ### The paired harness answered 32.2 months of prospective shadow accumulation in 88 seconds — and F3's hour lever does not transfer.
>
> B8 built the harness and it had never been run since. G2 seeded three questions and ran them
> on sealed history: **all three resolved**, each effect bounded strictly *inside* its own
> ±0.02 R/trade decision bar. F3's train-selected hour set {0, 8, 21, 22, 23}, measured at
> **+0.0210 R [+0.0110, +0.0302]** on the funnel pool, returns **+0.00321 [−0.00764, +0.01356]**
> on the sleeve estate — G2's whole interval sits below F3's lower bound, so the lever is
> largely **funnel-local**. The constructive half: dropping the **rollover hour alone** gives a
> *larger* point estimate (+0.00588) while refusing **1,639 fewer** decisions, so hours
> {8, 21, 22, 23} are worth keeping on this surface. Posed prospectively these three would have
> cost **17.6 + 13.5 + 1.1 months** of shadow accumulation.

---

## 1. WHAT THE REPLAY LANE CAN RUN RIGHT NOW

This did not exist in one place before. Everything below is measured, not inferred.

### 1.1 The fast surface — the one that runs

| component | path | measured |
|---|---|---|
| bar archive | `/Users/borr/GTOSActive/vps-bars-20260727/` | **65 MB**, 150 `.csv.gz` + 150 `.timebase.json`, **43 symbols × {M15, H4, D1}**, **4,358,938 rows**; M15 2024-01-01→2026-07-27, H4/D1 **1992-02-18**→2026-07-27; `FTMO_COVERAGE_GAPS: []` |
| decision store | `phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz` | 1,266,124 B, **22,324 unique candidates**, 32 sleeves (29 generating), 1,239 duplicates dropped, `seconds_total: 10735.8` (~2.98 h full regeneration) |
| quote-corrected rows | `phase20/forward/receipts/R1_ESTATE_ROWS_V2.json.gz` | 704,933 B, 22,354 rows, per-trade `r_new_{low,mid,high}` |
| machinery | `src/research_infra/walkforward/` | 20 modules, ~1.2 MB; offline, imports no broker module |
| paired harness | `swarm2/breakthrough/b8_paired_shadow/` | C1 **22,343 rows, 0 mismatches, max abs error 0.0** |
| parsed-series cache | `/Users/borr/.claude/jobs/adb9e69b/tmp/b8_cache/series_5b2eed1f2d3a267f.pkl` | 355 MB — **load 2.6 s** against ~108 s cold |

**Measured loop costs on this machine, today:**

| operation | cost |
|---|---|
| substrate load (cached) | **2.6 s** |
| full-estate walk, two cost geometries, 22,343 decisions | **35.2 s** |
| one paired B8 question, ~10 k pairs | **~23 s** |
| `run_gate` re-score on stored trades (no bars) | **minutes** |
| full estate regeneration from bars | **~3 h** |

**The lane's whole day-to-day capability costs 65 MB of disk.** Everything ≥1 GB in the tree
is sealed-arm or lane-input infrastructure.

### 1.2 The sealed surface — and the exact reason it will not start

`b7_5_post_acceleration_runner.py run-arm` needs 18 required arguments. Present on this
machine: decision contract, January + April execution seals, source bundles (196 MB / 198 MB),
source authority, selection receipt, prepared-pack authority, and the pinned tick manifest at
`/Users/borr/Documents/gtos/repo/ai-trading-agent/data/mt5_research_exports/bridge_ftmo_ticks_micro_2025_2026/manifest.json`
(sha256 `2362858a…1da0ca`, `attempt5:187-193`).

**Three blockers, all path fuses rather than missing bytes:**

1. The typed-cache (165 MB), tick-sparse-cache (1.3 GB) and prepared-day-packs (1.2 GB) live
   in `worktrees/replay-accel-engine-20260719`, not at the harness constants' paths. H4:
   sealed authority pins **absolute** paths, so copying them here is rejected
   (`fresh_source_authority_path_binding_mismatch`).
2. `attempt5:15501-15507` raises `attempt5_tick_sparse_cache_root_mismatch` unless the root
   resolves to `ATTEMPT5_TICK_SPARSE_CACHE_ROOT` **and is not a symlink** — and that
   constant's parent directory (`research/operations/replay_acceleration_real_s0r0_2026_07_19/`)
   **does not exist in this worktree.** A plain CLI `run-arm` from here fails on this check.
   The documented way round is `docs/audits/opus5-architecture-20260725/receipts/profile_day_harness.py`,
   which mirrors `run_sealed_arm`'s prelude instead of going through the CLI.
3. **Only January and April 2026 have a sealed-arm path at all.** There is no source bundle,
   execution seal, or typed/tick cache for February, May, June or July — those months were
   read through the funnel/lane path, never the B7.5 sealed-arm path.

**Exact unblock, if a sealed arm is ever wanted again:** run from
`worktrees/replay-accel-engine-20260719` (9.3 GB, **do not delete it — the sealed-arm
capability for January and April dies with it**), via the profile harness rather than the CLI,
and budget 16.5 h per month-window. `CLAUDE.md` §4's two hard preconditions still stand: the
pooled promote/reject evaluator does not exist, and the pooling weights are unsealed.

### 1.3 The lane windows — what is materialized

Registry: `/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/LANE_INPUT_REGISTRY.json`
(45,144 B). **Note the code's `DEFAULT_LANE_ROOT` (`lane_rematerialization.py:70-74`) is
repo-relative and that directory does not exist in this worktree** — every lane invocation
must pass an explicit lane root pointing at the hold.

**13 windows registered; 11 pack-built (17 GB of packs + 17 GB of sources = 34 GB, all
outside the repo); 2 NOT_BUILT.**

| window | split | packs | status for G2 |
|---|---|---|---|
| june / august / september / december **2025** | lane_validation | 28 / 30 / 30 / 31 days | **THE VALIDATION CURRENCY — spend nothing.** Never *funnel*-read; **not** outcome-virgin (they are the selection surface that picked the armed sleeves, `LM_MAT_RESULT.md` §2) |
| october / november 2025 | lane_validation | 31 / 29 | consumed by the Jun/Jul scorer bootstrap (prereg V1_3, `241640fce`); only days **2025-10-31** and **2025-11-05** remain reserved |
| **march 2026** | reserved_unread_one_shot | 31 | **the only genuinely outcome-unread month.** Double-fused: `guard.authorize_window` refuses every March day without `march_one_shot`, and `LaneInputRegistry` refuses a registry with `march_window_registered` true |
| february / april / may 2026 | — | 28 / 30 / 31 | SEALED-READ (Feb PASS, Apr+May REJECT) |
| **june / july 2026** | lane_validation | **0 — NOT_BUILT** | sources only. **Blocked by code, not data:** the `WINDOWS` naming table carries neither name on `main` **or** in this worktree (0 grep hits each); both exist only in the uncommitted `JUNJUL_MACHINERY_PATCH_V1_3.diff`. june_2026 carries **168 `bar_sources`** after the three lead-in supplements; every other window carries 96 |

Ticks in the hold cover **4 symbols only** (EURUSD, USDJPY, XAUUSD, XAGUSD) across 7 month-dirs
(16.2 GB); six windows have zero tick coverage.

### 1.4 Disk

**11 GB free.** `GTOSActive` is 180 GB; `worktrees/` alone is 81 GB. **You cannot hydrate a
fresh typed + tick-sparse cache pair for a new month** — January's pair alone is 1.47 GB, a
fresh run needs ~1.2 GB of prepared packs, and `attempt5:181` declares 768 MiB of streaming
transient headroom on top. Largest reclaimable candidates that cost no capability:
`hermes-evidence-hold-20260727/w21-tmp-lab-recovery-20260810` (2.4 GB) and the duplicate April
pack root (R1 vs R2, 1.2 GB each). **G2 deleted nothing and wrote 7.3 MB.**

---

## 2. G2-M1 / M2 — THE SLEEVE ESTATE RESTATED AT CORRECTED GEOMETRY

Code `g2_replay/estate_geometry_restate.py` + `aggregate_restate.py`; receipts
`g2_replay/receipts/G2_M1_RESTATEMENT_V1.json` (per sleeve, per year, armed set) and
`G2_M1_ROWS.json` (all 22,343 rows, both geometries).

**Two corrections landed 2026-08-12 and no published sleeve figure carries either.** B10
priced the hour defect on the **sealed funnel record** (282 trades) and the **candidate pool**
(146,745 fills); RECON adjudicated the slippage constant on the **sealed window**. Neither
touched the **sleeve estate** — the 22,343-decision, 29-sleeve, 2000-2026 store every
published sleeve number is measured on. That gap is what M1/M2 closes.

**Method.** Every decision tuple is held; only the charged cost moves. Fill authority is
`walkforward.exits.replay`. Control is the estate's own convention (`r_new_mid`: entry
anchored at `close + direction × spread`, shipped model, band `mid`). Treatment substitutes
`by_symbol_hour_of_week` for `by_class_hour_of_week` as an **external multiplier on the
returned spread** — deliberately not a patch to `spread_model.py`, which is reachable from the
live cost path. Intervals are B8's day-clustered block bootstrap (2,000 draws, seed 20260812).
Coverage: the symbol table resolves for **19,858 of 22,343 rows (88.9 %)**; on **9,084 rows
(40.7 %)** it differs from the class table, ratio range 0.348→5.235, median 0.968.

### 2.1 The estate

| quantity | value | CI95 (day-clustered) | n |
|---|---:|---|---:|
| shipped spread cost `spread_r` | **0.191563** | — | 22,343 |
| same at the symbol-hour repair | 0.192434 | — | 22,343 |
| Δ cost_r from the hour repair (**price domain — read this one**) | **−0.000871** | [−0.003067, +0.001513] | 22,343 |
| Δ R/trade from the hour repair (label domain) | −0.000999 | [−0.003371, +0.001342], p 0.399 | 22,343 |
| **Δ R/trade from barrier-conditional slippage** | **−0.006706** | **[−0.00705, −0.00636], p ≈ 0** | 22,343 |
| Δ R/trade, round trip incl. the uncharged entry leg | −0.013336 | — | 22,343 |
| **composed** | **−0.007705** | **[−0.010015, −0.005346], p ≈ 0** | 22,343 |

**In dollars at $500/R** (declared basis, linear — halve for $250/R, double for $1,000/R):
composed **−$3.85 per trade**, **−$28.54 per book-day**, **−$86,078** over the estate's
3,016 decision days.

### 2.2 Why the hour repair is inert on R and what to do about it

`exits.py:317`: `entry_price` is *"the anchor every level and every realised R is measured
from."* Barriers move with the entry, so R is spread-invariant on `stop` and `target` exits.
Measured consequence:

| exit reason | rows | rows whose R moved under the repair |
|---|---:|---:|
| stop | 14,120 | 30 |
| target | 6,815 | 27 |
| **trail** | 1,042 | **484** |
| **maxbars** | 366 | **83** |

Of the 9,084 rows where the spread genuinely changed, **8,460 produced a bit-identical R**;
`ratio ≠ 1 ∧ exit ∈ {trail, maxbars}` is 568 rows and **567 of them moved**. The mechanism is
exact, not statistical. **Reversal condition:** this inertness is a property of *this* labeller
under barrier exits. Any contract whose exit is not a fixed multiple of the stop — a time
stop, a scale-out, a trail, or any live fill — re-exposes the full price-domain effect. The
armed set's `maxbars` share is **13.7 %**, more than double the estate's 6.3 %, which is why
its hour-repair delta is the largest of any grouping G2 measured (+0.014893 R/trade in the
label domain, CI [+0.000001, +0.046154]).

### 2.3 Per-sleeve — the correction has a sign, and it is not the same sign twice

Sorted by composed price-domain + slippage delta. `sprd_r` is the **shipped** spread cost as a
fraction of the sleeve's own stop distance — the column that decides whether a sleeve can ever
be economic.

| sleeve | n | Δcost_r (hour) | Δslippage | Δtotal | $/trade | stop+trail | **sprd_r** |
|---|---:|---:|---:|---:|---:|---:|---:|
| asian_fade | 1,319 | −0.01979 | −0.01932 | **−0.03911** | −$19.56 | 1.00 | 0.1253 |
| sub_mid_dn_revert | 524 | −0.01561 | −0.00746 | −0.02307 | −$11.54 | 0.70 | **0.2310** |
| kz_london_crypto_low | 286 | 0.00000 | −0.01428 | −0.01428 | −$7.14 | 0.87 | 0.1769 |
| metal_session_reversion | 837 | +0.00523 | −0.01932 | −0.01409 | −$7.05 | 1.00 | 0.1618 |
| liq_asia_up_low_metal | 157 | +0.00267 | −0.01406 | −0.01139 | −$5.70 | 0.87 | **1.2257** |
| ny_crypto_momentum | 559 | 0.00000 | −0.01084 | −0.01084 | −$5.42 | 0.78 | 0.0807 |
| asia_pdl_fade | 2,827 | +0.00222 | −0.01238 | −0.01015 | −$5.08 | 0.82 | **0.8920** |
| fx_jpy_ny | 1,620 | −0.00155 | −0.00821 | −0.00976 | −$4.88 | 0.72 | 0.0706 |
| metals_core | 384 | +0.00063 | −0.00726 | −0.00664 | −$3.32 | 0.69 | 0.0546 |
| orb_crypto_london | 858 | 0.00000 | −0.00593 | −0.00593 | −$2.96 | 0.66 | 0.1068 |
| mx_nzdjpy_d1_donchian_20_breakout | 503 | +0.00282 | −0.00768 | −0.00486 | −$2.43 | 0.70 | 0.2220 |
| fx_jpy | 3,984 | +0.00435 | −0.00860 | −0.00425 | −$2.13 | 0.73 | 0.1125 |
| **energy_agri** (ARMED) | 67 | +0.00004 | −0.00358 | −0.00354 | −$1.77 | 0.60 | 0.0221 |
| mx_btcusd_d1_donchian_20_breakout | 318 | 0.00000 | −0.00164 | −0.00164 | −$0.82 | 0.55 | 0.0124 |
| **crypto** (ARMED) | 181 | +0.00312 | −0.00418 | −0.00107 | −$0.53 | 0.61 | 0.0542 |
| idxrev | 5,597 | −0.00274 | **+0.00284** | +0.00010 | +$0.05 | 0.44 | 0.0113 |
| **sub_xvol_pullback** (ARMED) | 88 | −0.00028 | **+0.00340** | **+0.00312** | **+$1.56** | 0.42 | 0.0306 |

(Full 29-sleeve table in the receipt.)

**Three things this table decides:**

1. **The flat slippage constant is a cross-subsidy.** Sleeves that stop out often pay less
   than they should; sleeves that hit target often pay more. `asian_fade` and
   `metal_session_reversion` stop or trail on **100 %** of their trades and are undercharged
   by 0.01932 R each; `sub_xvol_pullback` (42 %) and `idxrev` (44 %) are overcharged. Any
   cross-sleeve comparison made at the flat constant is tilted by up to **0.0227 R/trade**
   between the extremes — larger than most of the effects the estate has been arguing about.
2. **Two sleeves are dead on entry cost alone.** `liq_asia_up_low_metal` pays **1.2257 R** of
   spread per unit of stop distance and `asia_pdl_fade` **0.8920**. These are not close calls
   and no exit, hour or sizing treatment reaches them.
3. **The armed three are on a different cost surface from the estate that produced them** —
   0.0416 against 0.1916, a 4.6× gap. That is a real property of the selection, and it means
   estate-wide cost findings **systematically overstate** what the armed book pays.

### 2.4 G2-M3 — the flat constant biases every exit-frontier comparison, and the bias is bounded at ≤1.6 %

Code `g2_replay/exit_frontier_slippage_bias.py`; receipt
`receipts/G2_M3_EXIT_FRONTIER_SLIPPAGE_BIAS_V1.json`.

**Stated before it was measured:** an exit-contract treatment is precisely a treatment that
moves mass *between barriers*. A wider target moves trades out of `target` (slippage 0.0) into
`stop` (0.03932) and `maxbars` (0.00141). Under a flat 0.02 that migration is invisible, so a
wide-target cell should be credited with a bill it would not pay — and the estate's frontier
should over-rank it.

**The mechanism reproduces exactly.** `mx_btcusd` under `target_5R`: target mass **0.4497 →
0.2767**, stop mass **0.5503 → 0.7044**, barrier-true slippage **0.021638 → 0.027724**.

| cell | n | published Δ R/trade | CI95 | **bias** | share of Δ | corrected |
|---|---:|---:|---|---:|---:|---:|
| `mx_btcusd` live_2R → target_5R | 318 | +0.374602 | [+0.1658, +0.5908] | **−0.00609** | 1.62 % | +0.36852 |
| `mx_ethusd` live → target_5R | 311 | +0.338191 | [+0.1334, +0.5525] | −0.00545 | 1.61 % | +0.33274 |
| `energy_agri` plain_4R → partial_be_runner_2R | 67 | −0.294338 | [−0.6077, +0.0296] | −0.00346 | 1.17 % | −0.29780 |
| `sub_xvol_pullback` live_3R → target_4R | 88 | +0.278779 | [−0.0150, +0.5212] | −0.00140 | 0.50 % | +0.27737 |
| `crypto` live → target_4R | 181 | 0.000000 | — | 0.000000 | — | 0.000000 |

**The bias is real, systematically signed, and too small to move anything.** It is negative in
all four evaluable cells — every published frontier overstates its treatment — and it is
0.5–1.6 % of the effect. **No exit-frontier verdict in the estate changes.** That closes a
methodological worry cheaply and it is worth having closed rather than argued.
(`crypto`'s two arms produce bit-identical exit mixes: its published policy already *is* a 4R
target, which is a useful incidental confirmation that the control arm is the live contract.)

**Reversal condition:** the bound holds at RECON's measured legs. It scales linearly in the
stop-leg estimate — if the stop leg were 4× larger the `mx_btcusd` bias would be ~6.5 % of
the effect and still would not flip a sign. It would matter for a contract that moves barrier
mass much harder than a target widening does: a **time-stop** change, which moves mass into
`maxbars` at 0.00141, is the case where the flat 0.02 *overstates* the bill and the sign
inverts.

---

## 3. WHAT THE PAIRED HARNESS RESOLVED ON HISTORY

B8 built the harness and seeded eight questions; **it was never deployed and no lane had run
it since.** G2 seeded three more and ran all three on sealed history. Code
`g2_replay/g2_questions.py` + `symbol_hour_arm.py`; receipt `receipts/G2_QUESTIONS_V1.json`;
ledger `receipts/G2_MULTIPLICITY_LEDGER.jsonl`.

**The harness is unmodified.** Pass bars, pairing, day-clustered intervals and the BH ledger
are B8's. The ledger is **loaded from B8's own file first**, so G2's q-values are corrected
against the whole declared family — **23 arms, 17 inherited from B8 and 6 new** — and written
to a G2 path rather than editing another lane's receipt.

**Every question is a TRANSFER TEST.** F3 selected its levers on the *funnel candidate pool*
(Feb/Apr/May 2026 train, Jun/Jul test, ~150 k modelled fills). The *sleeve estate* is a
different population: 22,343 real decisions, 29 sleeves, 2000-2026, its own generators and
exit contracts. A lever that survives both is a property of markets; one that survives on the
funnel and dies on the estate is a property of the funnel's candidate density. **Nobody had
measured which.** The hour set was carried **verbatim** — re-selecting it on the estate would
make the test circular.

### 3.1 All three resolved. Each effect is bounded strictly INSIDE its own decision bar.

Control book level is identical across all three by construction: **−0.027426 R/trade over
22,343 decisions** (11 dropped for missing bars, same 11 in every arm).

| question | treatment | n | refused | Δ R/trade | CI95 (day-block) | p | verdict |
|---|---|---:|---:|---:|---|---:|---|
| **G2Q1** | drop F3's broker hours {0, 8, 21, 22, 23} | 22,343 | 5,872 (26.3 %) | **+0.003209** | [−0.00764, **+0.01356**] | 0.560 | **FAIL_BELOW_BAR** |
| **G2Q2** | drop the broker-midnight rollover hour only | 22,343 | 4,233 (18.9 %) | **+0.005881** | [−0.00367, **+0.01480**] | 0.218 | **FAIL_BELOW_BAR** |
| **G2Q3** | symbol-hour spread repair (B10's four-line fix) | 22,343 | 0 | **−0.000999** | [−0.00337, +0.00134] | 0.399 | **FAIL_BELOW_BAR** |

"FAIL_BELOW_BAR" here means something stronger than "not significant": **the entire day-clustered
interval lies inside the question's own ±0.02 R/trade decision threshold.** These are bounded
answers, not unresolved ones. At $500/R the three are worth **+$1.60, +$2.94 and −$0.50 per
trade** respectively, none separable from zero. Under BH over the 23-arm declared family, all
three q-values are **0.558 / 0.917 / 1.000 — none admits**, against 5 arms in the family that do.

### 3.2 F3's hour lever does NOT transfer at its funnel magnitude — and the failure is informative

F3 measured **+0.0210 R/trade [+0.0110, +0.0302]** dropping 14.3 % of the funnel book. On the
sleeve estate the **same treatment, same hour set**, drops **26.3 %** and returns **+0.00321
[−0.00764, +0.01356]**. G2's entire interval sits **below F3's lower bound**; F3's point
estimate is outside G2's interval. The lever is largely **funnel-local** — consistent with the
candidate-density reading rather than a market property.

**The constructive half is G2Q2.** Dropping the **rollover hour alone** returns a *larger*
point estimate (+0.00588 vs +0.00321) while refusing **1,639 fewer decisions**. So on the
sleeve estate, hours {8, 21, 22, 23} are *worth keeping*: adding them to the filter costs
about **−0.0027 R/trade** and 7.3 pp of the book. **If an hour filter is ever armed on the
sleeve surface, it should be the rollover hour alone, not F3's five** — and it still does not
clear the 0.02 bar, so today it is a ranking, not a proposal.

This corroborates B10's mechanism from an independent direction: B10 measured the rollover as
an **FX-only** spread event (JPY crosses 7.5×–18.6× their reference median, crypto exempt at
1.01×, every cash CFD shut). The estate's rollover hour carries a real cost; F3's other four
hours carry a selection effect that does not survive the population change.

### 3.3 Days-to-answer — the number the harness exists to produce

Posed **prospectively** on a deployed shadow at B8's measured estate arrival rate of
**542.65 decisions/month**, these questions would have cost:

| question | n required at its own bar | months to answer prospectively | **actual cost on history** |
|---|---:|---:|---|
| G2Q1 | 9,573 | **17.6** | **0 days** |
| G2Q2 | 7,347 | **13.5** | **0 days** |
| G2Q3 | 613 | **1.13** | **0 days** |

That is the whole case for the harness: **32.2 months of prospective shadow accumulation,
answered in 88 seconds of compute**, because the estate's decision history is already a paired
substrate. The three that remain genuinely prospective are the ones whose treatment cannot be
replayed — fill fidelity, real slippage, real partial fills — which is exactly what the live
minimal-size experiment is for.

### 3.4 The caveat that governs all of it

Every outcome here is a **modelled replay over bars**, not a broker fill. Lane H records **6 of
16 symbols with no reconciled price-domain slippage samples** (AUDJPY, CHFJPY, EURJPY,
UKOIL.cash, USOIL.cash, XAGUSD). Until that reconciliation exists the honest framing of any
B8/G2 answer is *"the contract measures X on the estate's own labeller"*, never *"the book
would have earned X."*

---

## 4. SERVING THE FORENSIC LANES

Read from their in-progress receipts, not from a plan. **No G2 measurement duplicates one of
theirs**; the three below are the gaps their own reports name.

| lane | what it needs that G2 can supply | status |
|---|---|---|
| **F1** | §14 hands off, unrun: *"a joint sweep of stop width × entry-cost band on this artifact, gated at the ratified rule."* F1's own artifact carries every column | the **`sprd_r` column in §2.3 is the entry-cost half**, per sleeve, on the estate rather than the funnel |
| **F3** | its levers were **train-selected on the funnel pool** (Feb/Apr/May 2026) and priced on Jun/Jul. Whether they transfer to another population was never asked | **G2Q1/G2Q2 (§3) are that transfer test**, hour set carried verbatim so the estate read is not a second fit |
| **F4** | `F4_BASIS_AUDIT`: `expected_slippage_r` is *"a constant 0.02 (dead)"* — a feature with zero variance | **§2.1 supplies the live variance**: barrier-conditional, −0.006706 R/trade estate-wide, ±0.0227 between sleeve extremes. It is a usable feature, not a dead column |
| **F5** | repriced the estate with four-component true cost but that is *"a repricing of already-walked trades, not a re-run at corrected geometry"* | **§2 is the re-walk**, and §2.2 says why the two agree: R is spread-invariant under barrier exits, so a repricing and a re-walk **must** agree except on trail/maxbars |

**Two cross-lane facts G2 carries forward, because they constrain every replay design:**
F4's blind control found the candidate pool underperforms hour-matched random entry by
**5.5 pp at 2 R**, and F3's wick receipt found the post-excursion adverse drift **flips
positive on transactable bar closes**. Any lever premised on selection quality or harvestable
give-back argues against both.

**Constraints honoured:** the four never-funnel-read 2025 windows and the two reserve days
(2025-10-31, 2025-11-05) were not touched by any arm; March 2026 was not read; no sealed
month-arm was launched; nothing was deleted.

---

## 5. STANDING STATUS

| item | state |
|---|---|
| replay-surface inventory (§1) | **DONE** — first single-place statement of what runs, at what cost, blocked by what |
| G2-M1/M2 full-estate walk at corrected geometry | **DONE** — `G2_M1_RESTATEMENT_V1.json`, 22,343 rows, 35 s |
| G2-M3 exit-frontier slippage bias | **DONE** — `G2_M3_..._V1.json`, 5 cells, bias bounded ≤1.6 %, no verdict moves |
| G2Q1–Q3 paired transfer tests on sealed history | **DONE and RESOLVED** — 3 questions, 88 s, 32.2 prospective months bought |
| sealed month-arm replay | **NOT LAUNCHED** — 16.5 h, and §1.2's three fuses stand |
| June/July 2026 pack build | **BLOCKED IN CODE** — `WINDOWS` carries neither name on `main`; unblock is landing `JUNJUL_MACHINERY_PATCH_V1_3.diff` |
| disk | 11 GB free; G2 wrote 7.3 MB of receipts and deleted nothing |

**Receipts written by this lane** (all under `g2_replay/`):
`receipts/G2_M1_RESTATEMENT_V1.json` (per-sleeve, per-year, armed set),
`receipts/G2_M1_ROWS.json` (22,343 rows, both geometries),
`receipts/G2_M1_META.json`,
`receipts/G2_M3_EXIT_FRONTIER_SLIPPAGE_BIAS_V1.json`,
`receipts/G2_QUESTIONS_V1.json`,
`receipts/G2_MULTIPLICITY_LEDGER.jsonl` (23 arms: 17 inherited from B8, 6 new).
Code: `estate_geometry_restate.py`, `aggregate_restate.py`, `exit_frontier_slippage_bias.py`,
`g2_questions.py`, `symbol_hour_arm.py`. Every one is re-runnable in under a minute.

### The next three things this lane should do, in order

1. **Re-gate every published sleeve verdict at the barrier-conditional slippage.** §2.1's
   −0.006706 R/trade is uniform in sign across 27 of 29 sleeves but ranges over 0.0227 R —
   large enough to move a marginal admission, and every published gate ran at the flat 0.02.
   Cost: minutes, on stored trades, via `run_gate`.
2. **Price the two structurally-dead sleeves out.** `liq_asia_up_low_metal` and
   `asia_pdl_fade` carry spread ≥ 89 % of their own stop distance. Confirm against the tape
   surface and take the kill to the owner — neither is armed, so it costs nothing but removes
   3,000 decisions of noise from every estate-wide statistic.
3. **Seed the harness with the questions G2 could not reach.** Three are ready and each is
   ~30 s of compute on the substrate that is already cached: (a) F3's **L3 narrow-stop-quintile
   drop** (`risk/ATR < 0.4139`, funnel-measured at +0.0365 R [+0.0247, +0.0480]) as a fourth
   transfer test — it needs an ATR column computed from the bars G2 already loads; (b) the
   **cluster cap isolated as its own lever** — F5 simulated it bundled with the sleeve/symbol
   cap and the gross-risk cap, so its own net-R contribution has never been separated, and B8's
   seeded `Q6_cluster_cap_L5` returned a null result that was never diagnosed; (c) **time-stop
   horizon changes at the barrier-true slippage**, which is the one contract family where §2.4's
   bias term *inverts* sign.

**What this lane deliberately did not do.** It launched no sealed month-arm (16.5 h, and the
program's two hard preconditions from `CLAUDE.md` §4 are still unmet). It touched none of the
four never-funnel-read 2025 windows, neither reserve day, and not March 2026. It deleted
nothing, wrote nothing outside `swarm2/forensics/`, made no git commit, and edited no `src/`
file, config byte, or contract-bound path — the symbol-hour repair is applied as an external
multiplier precisely so that `spread_model.py`, which is reachable from the live cost path,
stays untouched.
