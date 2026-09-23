# Session AQ — contract truth (wave 11, blocks B1400–B1453)

**The estate's one standing admission was a property of a repair that had not landed.**
`mx_btcusd @ target_5R` ADMITS at two of three cost bands under the contract its evidence
describes, and **REJECTS at all four bands under the contract the live book was running** —
p 0.0011 → 0.0564 at mid, fold positivity 5/5 → 3/5 with the two most recent folds negative.
The repair is three lines in `execution_packets.py`, it moves no armed sleeve, and it landed
this session.

Receipts: `phase11/receipts/`. Nothing touched the VPS, no broker-capable script ran,
`config/agent_config.yaml` and `config/profiles/redacted_account.yaml` are untouched. H1 drift is
2 UNHYDRATED-LFS at session start and 2 at session end — unchanged.

---

## 0. What was found, in order of how much it matters

**1. The `mx_*` D1 cohort's live time stop was one D1 bar against an eighty-D1-bar research
horizon, and the number 96 is the conversion ratio itself.** `time_stop_bars` is **M15 bars
that PRINTED**, for every sleeve, whatever grid the sleeve decides on
(`execution.py:8953-8958` counts them, `:9010` compares them). `vol_compression` — a D1
sleeve declared four lines earlier in the same dict — carries `7680` with the comment *"D1
research horizon: 80 D1 bars ~= 7680 M15 bars"*. The fourteen `mx_*` sleeves carried **96**,
which is exactly `M15_BARS_PER["D1"]`. No claim about anyone's intent is needed: the two
cannot both be right, and 96 is the ratio, not a horizon. **14 declared in the spec, 12 in
the active registry, 10 generating trades.**

**2. The value of the repair is signed BOTH WAYS, and that is the finding AD's unit table
could not carry.** AD measured the units (B750) and filed 49 informational rows. It did not
gate the cohort at the ratified rule. Measured at RECORDED / mid band, the repair is worth
**+0.272 R/day** on `mx_btcusd` and **−0.591 R/day** on `mx_us100` — four of the nine
measurable sleeves gain and five lose. **On five of the ten the accidental one-bar stop was
better than the research horizon**, and both ATR-mean-reversion sleeves flip from strongly
negative to positive under it. The unit repair still lands, because a spec must mean what it
says; but for those five the follow-up is to declare a short horizon *deliberately* on the
evidence rather than inherit one from a bug. That is an exit-frontier decision, and it is
routed as one.

**3. Both changes are necessary for the admission and neither is sufficient.** At mid band,
on RECORDED: the sleeve's own 2R target at the repaired horizon gives p 0.0064 (REJECT); the
5R exit under the old one-bar time stop gives p 0.0564 (REJECT); both together give p 0.0011
(ADMIT). The admission is an interaction, not a sum — the exit-contract analogue of the
superadditivity AL measured on the population axis.

**4. The ratified hour-01 entry convention is CONFIRMED on evidence the decision did not
have, and it does not make the cohort admissible.** A three-mechanism exact re-derivation on
the M15 grid — including `donchian_20_breakout`, which AM's frontier never covered — puts
hour 01 at **+0.1108 R/trade net against hour 00** and **+0.0368 against AH's hour 04**. All
three mechanisms improve; the newly-covered one improves the most (+0.1540). But **0 of 72
gated arms admit**, best p 0.3800, an order of magnitude from the rank-1 bar. The convention
is a cost repair worth taking. It is not an edge.

**5. The convention is measured on 2024+, and the reason is narrower than I first published
— see §5, this was refuted.** An hour-01 fill needs a bar closing at broker 01:00. In the
**matched FTMO feed** (`vps-bars-20260727`, the archive these trades were generated on) the D1
grid closes at 00:00 and the H4 grid at 00/04/08/12/16/20, so only M15 carries it and M15
starts 2023-12-31. But the repo's own `data/` tree **does** hold H1 series, and for four of the
fourteen cohort symbols they reach back to 2022-01-03. They are a different capture and they
carry **no `.timebase.json` sidecar**, which `CsvBarSource` refuses outright (`generation.py:229`,
the F7 fail-closed rule) — so they are unusable as they stand, not absent. That makes the
capture requirement **smaller and cheaper than the one I filed**, and it is refiled.

**6. A whole run of nulls used to look exactly like a result, and now does not.** The first
run of the entry-hour gate returned 72 arms, every one `NOT_EVALUABLE` on
`port_fidelity_unmeasured`, because the caller had not wrapped `run_gate` in
`family.fidelity_scope`. Nothing in the result said so. The arms tabulated cleanly, one per
entry hour and cost band. `GateResult.family["wipeout"]` now fires when **not one** submitted
sleeve reaches a null, names the dominant refusal class, and for the fidelity class names the
fix — and stays silent the moment a single sleeve is scored, which is pinned by its own test
so it cannot decay into noise.

---

## 1. AQ-1 — the D1 time-stop truth, both sides of it

Driver `phase11/receipts/aq_contract_truth.py`, artifact `AQ_CONTRACT_TRUTH_V1.json`.
Three contracts per sleeve, all expressed in the sleeve's own bars so `exits.replay` can run
them, each gated on **RECORDED** at all four cost bands plus an `ALL_ERAS` control:

| contract | what it is |
|---|---|
| `PUBLISHED` | stop / native target / `maxbars=80`, no time stop — AA's walk, and what every published economic number in this estate describes |
| `LIVE_TRUE` | the same plus a time stop at the declared M15 value divided by the sleeve's own **measured printed-bar ratio** — what `run_book.py` ran |
| `REPAIRED` | the same at the repaired declaration, capped at `maxbars` |

**Control C1, and it is not a formality.** For the mis-scaled D1 cohort `REPAIRED` must be
**R-identical** to `PUBLISHED`, because a time stop at 80 own bars fires on the same bar
`maxbars` does, at the same close. **2,086 of 2,086 trades identical to the bit.** The driver
refuses to publish if it fails.

### Side A — the spec is wrong (12 in the registry, 10 generating)

RECORDED / mid band. `Δ` is `REPAIRED − LIVE_TRUE`: what the repair is worth.

| sleeve | n | live stop | published R/day | live-true R/day | **Δ** | med hold pub→live |
|---|---:|---:|---:|---:|---:|---|
| `mx_btcusd_d1_donchian_20_breakout` | 232 | 1 bar | 0.3894 | 0.1172 | **+0.2722** | 72 h → 24 h |
| `mx_ethusd_d1_donchian_20_breakout` | 217 | 1 | 0.0240 | −0.0434 | +0.0674 | 72 → 24 |
| `mx_cadjpy_d1_volume_surge_reversal` | 192 | 1 | −0.2035 | −0.2559 | +0.0523 | 96 → 24 |
| `mx_jp225_cash_d1_volume_surge_reversal` | 64 | 1 | 0.1977 | 0.1565 | +0.0412 | 120 → 24 |
| `mx_nzdjpy_d1_donchian_20_breakout` | 349 | 1 | −0.2353 | −0.1562 | −0.0792 | 144 → 24 |
| `mx_us30_cash_d1_volume_surge_reversal` | 121 | 1 | 0.0612 | 0.1449 | −0.0837 | 96 → 24 |
| `mx_ger40_cash_d1_volume_surge_reversal` | 110 | 1 | −0.0082 | 0.1152 | −0.1234 | 96 → 24 |
| `mx_us500_cash_d1_atr_mean_reversion` | 54 | 1 | −0.4577 | 0.0990 | **−0.5567** | 120 → 24 |
| `mx_us100_cash_d1_atr_mean_reversion` | 62 | 1 | −0.4498 | 0.1415 | **−0.5913** | 120 → 24 |
| `mx_avausd_d1_donchian_20_breakout` | 34 | 1 | — | — | NOT_EVALUABLE | — |

`mx_avausd` keeps only 34 of 189 trades on RECORDED and they fall in one evaluable fold, so
the gate refuses on `insufficient_sample`. That is reported as unknown, not as zero.
`mx_eu50_cash` and `mx_fra40_cash` generate nothing — the archive has no `EU50.cash` or
`FRA40.cash` series — and the spec's other two, `mx_aus200_cash` and `mx_spn35_cash`, are not
in the active registry at all. The repair covers all fourteen regardless, because a spec
should be right whether or not it currently fires.

### Side B — the spec is right and the LABEL is wrong (10 sleeves)

These sleeves' `time_stop_bars` is correctly scaled. Their published economics simply never
applied it. `ERROR` is `published − live_true`: how much the published figure overstates
(positive) or understates (negative) the contract the book runs.

| sleeve | tf | stop (own bars) | n | published | live-true | **error** | trunc |
|---|---|---:|---:|---:|---:|---:|---:|
| `asian_fade` | M15 | 48 | 257 | −0.1528 | −1.0360 | **+0.8832** | 0.0 % |
| `metal_session_reversion` | M15 | 24 | 837 | −0.1030 | −0.4080 | +0.3050 | 0.1 % |
| `kz_london_crypto_low` | M15 | 32 | 194 | −0.8722 | −0.6400 | −0.2322 | 23.4 % |
| `ny_crypto_momentum` | M15 | 20 | 354 | −0.4513 | −0.2481 | −0.2032 | 37.0 % |
| `liq_asia_up_low_metal` | M15 | 16 | 157 | −0.8950 | −0.8084 | −0.0866 | 11.5 % |
| `fx_jpy_ny` · `idxrev` · `fx_jpy` · `asia_pdl_fade` · `vss_fxcross_london_up_low` | | | | | | ≤ 0.007 | |

`asian_fade` is the worst: its published figure is **0.88 R/day better** than its own live
contract, and its truncation fraction is **zero** — the damage is not the time stop cutting
trades short, it is the *trailing runner* contract interacting with it. The five below the
line are immaterial and are filed as INFORMATIONAL rather than dressed up.

### The repair

`src/components/ultimate_book/execution_packets.py` — **unbound by R2**, checked before
editing (`exit_policy_v4.py` and `config/agent_config.yaml` are bound; neither was touched).

* `M15_BARS_PER = {"M15": 1, "H4": 16, "D1": 96}` and `time_stop_m15(n_native_bars, grid)`,
  which **raises** on an unknown grid rather than defaulting to 1 — defaulting would silently
  reproduce the defect the helper exists to prevent.
* `RESEARCH_HORIZON_NATIVE_BARS = 80`, the estate-wide research horizon.
* The `mx_*` block and `vol_compression` now use the **same expression**, so they cannot
  drift apart again. 96 → 7680.
* The conversion is **calendar**, because a spec is per sleeve while the printed-bar ratio is
  per symbol (96 on a 24/7 symbol, 92 on a session index, 84 on UKOIL). On the five session
  symbols the repaired value therefore runs **4.348 % PAST** the 80-bar horizon — looser than
  research, never tighter, which is the safe direction for a backstop. Quantified per sleeve
  in `spec_audit.rounding_residual`.

**The armed three are H4, are 1280 = 80 × 16, and are unaffected** — asserted by the driver,
which raises rather than publishing if any armed sleeve would move, and pinned by name, value
and grid in the test file. The package arms nothing by itself.

**Tests** — `tests/ultimate_book/test_time_stop_units.py`, 45 tests:
the unit is pinned **behaviourally** by driving the real `check_time_stop_and_close` against
the real budget (fires at 7680 printed M15 bars, not at 7679, and not at 96); the blast radius
is pinned against a frozen pre-repair snapshot, so "exactly the fourteen moved" is a
measurement; and a coverage test fails if a sleeve is ever added without a snapshot row, so
the blast-radius test cannot silently stop covering the registry.
`tests/ultimate_book/test_market_expansion_runtime_generator.py` pinned the defect at two
sites and was updated with the reason in place.

---

## 2. AQ-2 — the hour-01 entry re-derivation

Driver `phase11/receipts/aq_entry_hour_01.py`, artifacts `AQ_ENTRY_HOUR01_V1.json` and
`AQ_ENTRY_HOUR01_TRADES.json.gz`. Cohort: the 42 FX D1 members (3 mechanisms × 14 symbols)
and their 3 pooled families. Every arm is replayed on the **M15** grid so the exit resolution
is constant and only the entry instant moves, and a decision bar contributes to an arm only
if **every** arm can reach it — otherwise the shift is confounded with the reachability guard.

**Control against AM: 2,466 shared (member, decision bar, shift) keys, 0 `r_gross`
mismatches, same `maxbars_m15`.** `donchian_20_breakout` is new coverage with no counterpart.

Exact re-derivation, 1,724 decision bars, 2024-01-04 … 2026-07-23, mid band, per trade:

| arm | gross | cost | **net** | Δ net vs h00 | spread saved | gross given up |
|---|---:|---:|---:|---:|---:|---:|
| hour 00 (control) | +0.00924 | 0.18236 | **−0.17313** | — | — | — |
| **hour 01 (ratified)** | +0.00288 | 0.06526 | **−0.06237** | **+0.11075** | 0.11738 | 0.00635 |
| hour 04 (AH comparator) | −0.03568 | 0.06344 | **−0.09913** | +0.07400 | 0.11995 | 0.04492 |

Hour 04 saves marginally *more* spread and gives up **7×** more gross doing it. That is
precisely the shape the owner decision asserted — *"right about the direction and wrong about
the dose"* — now measured on the third mechanism as well. Per mechanism, Δ net at hour 01:
`donchian_20_breakout` **+0.1540**, `atr_mean_reversion` +0.0725, `volume_surge_reversal`
+0.0574. All three improve; only `volume_surge_reversal` is net-positive at any arm.

**Two cost defects AM disclosed are repaired here**: `side` is now passed to `cost_r` (AM's
helper priced 45 % of rows LONG when they were short), and the hold clamp is *asserted* not
assumed — **0 rows clamped** at 1 h and 4 h against a 72 h median. Slippage stays hour-blind
because that is a property of `cost_r`, not of the driver; a driver must not invent an hour
profile the cost model does not have.

**The gate: 0 of 72 arms admit.** 3 families × 3 hours × 4 bands × 2 multiplicity bills. Best
p **0.3800** (`fam_donchian_20_breakout_fx_d1`, hour 01, flat). Hour 01 is the only arm where
that family's pooled R/day changes sign (−0.2196 → +0.0316 at mid). No near miss, and no
repair on this axis closes it.

**Multiplicity, declared and committed before the gate ran.**
`phase11/receipts/aq_family_v4.py` imports nothing from the measurement driver and its commit
(`436dbb5c7`) precedes the measurement. It raises `MECHANISM_CROSS_V1` **276 → 321** with the
45 entry-convention cells, taking the *more expensive* of the two defensible readings — the
cheaper one (an entry-timing change is an exit-cell-class re-measurement, which AI §0 charges
zero) is stated in the file and deliberately not taken, because it is the reading that would
be convenient if a cell admitted. Every arm is **also** gated at the un-raised 276 and both
q-values published. Hour 00 is the declared member itself and hour 04 was already paid for
inside AH's 180-look bill; declaring either again would double-count. Cut rule: entry hour
from the fixed set {00, 01, 04} — no threshold, no median split, no data-dependent choice.

**The capture requirement, corrected after an adversarial pass refuted my first version.**
I published *"no available bar grid closes at broker 01:00"* and that is false. `data/` holds
H1 series for **12 of the 14** cohort symbols, and for **4** of them (`GBPUSD`, `USDJPY` from
2022-01-03; `GBPJPY`, `NZDUSD` from 2023-01-16) they predate the M15 archive. Two things keep
them from being a free extension, and both are fixable rather than fatal:

* **no `.timebase.json` sidecar** on any pre-2024 H1 file, so `CsvBarSource` refuses them
  (`generation.py:229`) and their broker-clock alignment is unverified — which is exactly the
  F7 defect that cost this programme a three-hour offset once already. Every H1 file that
  *does* carry a sidecar (`data/historical_2026/`, 12 symbols) starts 2025-10-01 or later.
* **a different capture** from the FTMO D1 the trades were generated on, so an arm built on
  them would be cross-feed and would need its own parity control.

So the requirement is now two smaller items, not one large one: **(a)** verify and stamp a
timebase for the four existing pre-2024 H1 files — that alone buys 4/14 symbols over ~2 extra
years and is a day's work, not a capture; **(b)** the matched FTMO intraday feed for the other
ten, back as far as it goes. Neither reaches 2001. The 26-year claim stays cost-only.

---

## 3. AQ-3 — `sub_mid_dn_revert`, the artifact of record

AM repaired `substrate._session_hour` (raw UTC hour compared against broker-hour session
constants; 50.04 % of H4 bars mis-bucketed; `session=ny` moves from server-hour {20, 00} to
{16, 20}) and measured the A/B. It never regenerated the artifact everything downstream
reads, and said so. Every session since has had to remember the substitution by hand.

`phase11/receipts/AQ_ESTATE_TRADES_V2.json.gz` (sha256 `010461d43156…`) is AA's estate with
this sleeve's population replaced: **503 → 533** trades, 235 shared, jaccard 0.293, mean R
0.3996 → 0.4784. Every other sleeve is byte-identical.

**The control that makes reuse legal rather than lazy**: AM's *authored-clock* arm must BE
AA's labelling, and it is — **503/503 keys, 0 `r_gross` mismatches, identical ΣR**. If AM
reproduces AA on the authored clock, its repaired arm is a correct regeneration of the same
generator on the fixed clock, and re-running AA's ~30-machine-minute H4 generation would
produce the same rows. `aq_estate_v2.py` refuses to write if that control fails.

Gated at the ratified rule on the re-clocked population (band table, RECORDED, family V3):

| band | verdict | n | R/day | p_raw | drop-best retention |
|---|---|---:|---:|---:|---:|
| flat *(control)* | REJECT | 325 | 0.2308 | 0.0252 | +0.475 |
| low | REJECT | 325 | 0.1475 | 0.1125 | −0.002 |
| mid | REJECT | 325 | 0.1206 | 0.1635 | −0.270 |
| high | REJECT | 325 | 0.0791 | 0.2608 | −1.043 |

**AN's warning holds exactly and I am restating it rather than softening it**: the nearness is
**flat-band only**. p 0.0252 at the control snapshot becomes **0.1635 at mid** — a 6.5×
proximity loss — and `drop_best_retention` goes **positive → negative** across the same step,
so at every real band this sleeve fails robustness as well as significance. Its p reproduces
AN's to the digit (0.16348365163483652). The fold means are
`[−0.337, +0.249, −0.444, +0.402, +0.734]` — the decay runs the *opposite* way to `mx_btcusd`,
strongest most recently, which is a fact worth having and is not an admission.

**Still stale downstream, filed as a REJECT row**: `AA_ESTATE_WALK.json`,
`EXIT_FRONTIER_V1.json`, `AD_CARRY_TIERS_RESTATED_V1.json` and `SURVIVOR_BOOK_V1.json` are all
still built on the 503. Cost to rebuild from the V2 artifact: ~2 min, ~27 min, then arithmetic.

---

## 4. AQ-4 — the challenge dossier

`phase11/MX_BTCUSD_CHALLENGE_DOSSIER.md`, generated by `aq_btc_dossier.py` from committed
artifacts with the JSON path stamped on every figure. Nothing on it is transcribed; if an
input moves, the generator dies rather than printing a stale number.

**Parity control**: this session re-derived the admission from AA's stored intents rather than
reading AN's number back. p `0.0010998900109989002`, R/day `0.981691283069039`, n `232` and
all five fold means reproduce the ratified decision **exactly**. Only q moves — 0.0385 → 0.0429
— because the family is V3's 39 rather than V2's 35, and p is family-invariant. The dossier
refuses to write if parity fails.

The page carries: the four-cell contract truth table; the band table phrased as *"admits at two
of three cost bands"* with `flat` marked as a control, never a bare ADMIT; the BH arithmetic at
39 (rank-1 bar 0.0025641, p 2.33× inside; Bonferroni bar 0.0012821, p 1.17× inside; still
admits to m = 90 at α 0.10); the permutation floor and its 11.0× headroom; the chronological
fold table with the 7.6× decay and the instruction to size on **+0.198 R/day**, not on 0.982;
the same folds under the pre-repair contract, where the two most recent are negative; AL's
adversarial scoreboard including the attack that did *not* survive; the 78-trade band caveat
with its 13-trade tail; and the eligibility-not-allocation framing at registry weight 0.025.

---

## 5. What I got wrong

**I mislabelled the "both repairs" paragraph in the first cut of the dossier**, and it was the
single most load-bearing sentence on the page. I wrote that *"the exit target alone (2R → 5R,
no time stop) gives p 0.0064"* — but p 0.0064 is the **2R, no-time-stop** cell, i.e. the
*time-stop* repair alone. The exit-target change alone is p 0.0564. Both numbers were correct
and the labels were swapped, which would have told a reader the opposite of the truth about
which change does what. Caught on reading the generated page, before commit. The paragraph is
now three explicit bullets naming the cell each p belongs to.

**My first entry-hour gate produced 72 clean-looking NOT_EVALUABLE arms and I nearly wrote
them up as a result.** The cause was mine — no `family.fidelity_scope` around `run_gate`, which
every research cohort outside the production registry needs. What saved it was reading the
`reasons` field of one arm rather than the verdict column. That is too thin a margin, so the
gate now reports the condition itself (`family["wipeout"]`) and the driver raises on it. It is
the third instance this programme has logged of the silent-null class, and the first where the
null was a whole grid rather than a field.

**I stated the mis-scaled cohort as "12 generating" in my own commission's framing and it is
10.** CLAUDE.md §4 says *"the twelve generating `mx_*` D1 sleeves"*. Twelve are in the active
registry; **ten generate a trade**, because the archive has no `EU50.cash` or `FRA40.cash`
series. Fourteen are declared in `SLEEVE_EXIT_PROFILES`. Three different counts, all true of
different sets, and the correction is in CLAUDE.md with this session's commit.

**I assumed AD's exit frontier answered AQ-1 and it does not.** The frontier does contain a
`time_stop_1` cell per D1 sleeve, and reading its delta against `as_walked` gives a table that
looks like the answer. It is at the **flat** band, on **ALL_ERAS**, at the historical 69-look
family — none of which is the ratified rule. On `mx_btcusd` the flat/all-eras delta reads
+0.1405 R/day and the ratified-rule delta is **+0.2722**, a 1.9× difference. The shortcut was
tempting and would have published a number nobody could reproduce from the standing protocol.

**My own driver could not survive its own repair, and it destroyed its artifact proving it.**
`aq_contract_truth.py --stage audit` reads the live `SLEEVE_EXIT_PROFILES`, so once 96 → 7680
had landed it reported *"0 sleeves mis-scaled"* and assembled that over the complete artifact —
wiping the walk and admission stages, because the stage cache is deliberately not committed
(2.9 MB duplicating the artifact byte for byte). Restored from the git index and fixed twice
over: the pre-repair declaration is now **frozen** in the driver so the measurement survives
its subject being fixed, `AQ_AS_OF=live` is a standing **regression check** that must report
zero mis-scaled sleeves forever after B1404, and both drivers' assemblers now fall back to the
artifact of record so a single-stage run can never null out a stage it did not touch. A
measurement of a defect that dies when the defect is fixed is not a measurement.

**I published an absence I had not searched for, and an adversarial pass refuted it.** I wrote
that the hour-01 convention *"cannot be validated before 2024 from any data on this machine"*
and that *"no available bar grid closes at broker 01:00"*. I had checked the matched FTMO bar
archive and the tick archive, and both are as I said. I did not check the repo's own `data/`
tree, which holds H1 series for **12 of the 14** cohort symbols and pre-2024 coverage for
**4**. The scoped claim — that the exact re-derivation on the matched feed is 2024+ — survives
untouched; the sweeping one does not, and it is the sweeping one that sets a capture
requirement. Corrected in §2, in the artifact, and in the repair row, which now asks for
something considerably cheaper. **An absence is a measurement and has to be searched for like
one**; "I looked in the obvious place and it was not there" is not the same claim.

---

## 6. Ledger, repairs, blocks

* **Trial ledger** — 723 rows this session (`research/operations/trial_budget/TRIAL_LEDGER.jsonl`,
  session `AQ`): 507 `contract_truth_grid`, 216 `entry_hour01_regate`. 12 admitted, 612
  rejected, 99 not-evaluable. The 216 are **three** runs of 72 — the first was the fidelity
  wipeout and its rows stay in the ledger, because a look taken cannot be un-taken (B1267).
* **Repair queue** — 29 rows appended (`phase6/receipts/REPAIR_QUEUE_APPEND.jsonl`, 127 → 156):
  10 `TIME_STOP_UNIT_REPAIRED*` (5 of them flagged `..._BUT_THE_ACCIDENT_WAS_FAVOURABLE`, 1
  `..._VALUE_NOT_MEASURABLE_ON_RECORDED`), 10 `RESTAMP_PUBLISHED_ECONOMICS_AT_THE_LIVE_CONTRACT`,
  `THE_ADMISSION_IS_CONTINGENT_ON_THE_TIME_STOP_REPAIR`,
  `REBUILD_THE_DOWNSTREAM_ARTIFACTS_ON_THE_REPAIRED_CLOCK`,
  `CAPTURE_INTRADAY_BARS_TO_VALIDATE_THE_RATIFIED_ENTRY_CONVENTION`,
  `ENTRY_CONVENTION_CONFIRMED_BUT_THE_COHORT_STILL_DOES_NOT_ADMIT`,
  `A_WHOLE_RUN_OF_NULLS_NOW_FALLS_LOUDLY`, and — found by a completeness sweep for other
  consumers of the repaired value — `THE_ONE_TRUTH_PER_SLEEVE_ARTIFACT_IS_STALE_ON_THE_REPAIRED_FIELD`:
  `SLEEVE_DOSSIER_V1.json` carries `time_stop_bars_m15: 96` for **12** sleeves as a current
  claim with three derived fields that are now false. There are **no code consumers** of the
  old value anywhere in the tree, which is precisely why that one is easy to miss.
  **26 rows, 127 → 153.** 0 cross-session collisions.
* **A/B** — `phase11/receipts/SESSION_AQ_AB.md`. Scoped to the 21 files the import closure
  reaches; copy-back, never `git checkout`, with all five restored files sha256-verified.
  **0 bad → 0 bad, 0 regressed, +52 net new passing tests.** The tool refused the 21-file diff
  because the two new test files do not exist on the before side, so the comparison is over the
  19 shared files and the new 52 are counted separately. Full-suite A/B is the orchestrator's.
* **Reproducibility** — `aq_contract_truth.py --stage all` re-run from a cold cache **after**
  the repair landed reproduces its committed artifact exactly: 0 leaf differences outside the
  `seconds` timing fields, over both the walk (15 arms) and admission (24 arms) trees, and C1
  comes back 2,086/2,086 again. The comparator is nan-aware — a naive one reported 254 false
  differences, every one a `nan != nan` on `drop_best_retention`, which is the same trap AN
  caught in its own work at B1266.
* **Blocks** — B1400–B1453 in `IMPLEMENTATION_STATE.md`. The commissioned range B1400–B1449 is fully used; B1450–B1453 carry the adversarial pass and its four corrections and are borrowed from **above** AR's B1450–B1499 range — flagged for the orchestrator in the handoff below.

---

## 6a. The adversarial pass, and the one claim it refuted

Eight load-bearing claims were put to a verifier instructed to refute them and to default to
"refuted" when uncertain. **Five came back CONFIRMED and three of those stronger than I had
claimed**: C1's logic was checked with 4,000 randomised replays and boundary probes at
0/1/5/79/80/81 bars (0 mismatches on `r_gross`, `exit_index`, `bars_held` — only
`exit_reason` changes), the 2,086 denominator was independently recomputed with no key
collisions, and AM-reproduces-AA holds under three progressively stricter keys with **all 22
common fields** matching, not just `r_gross`. The blast-radius claim survived a side-by-side
load of both module versions; the apparent 35-sleeve difference in `build_book_trade_params`
is wall-clock nondeterminism in the headroom snapshot's `captured_at_utc`, proved by calling
the same module twice.

**One claim was refuted, and it is the one I would most want refuted before Borhen read it.**
I published that the hour-01 convention *"cannot be validated before 2024 from any data on
this machine"*. `data/` holds H1 series for 12 of the 14 cohort symbols and pre-2024 coverage
for four. I had checked the matched FTMO archive and the ticks — both are as I said — and
never searched the repo's own tree. §2 and §5 carry the correction and the repair row is
superseded by a cheaper one.

**Three defects it found in my own work, all now fixed:** `_WIPEOUT_CLASSES` named
`symbol_outside_registry_universe`, a bucket **nothing can fall into** — which is the very
defect the function exists to catch, in miniature; `dominant_class` broke ties by dict
insertion order; and the dossier's parity line said "exactly" and "only q moves" in the same
breath, which is two claims where one is false.

**And two live-behaviour consequences of the repair that live outside the module it edits**,
so no blast-radius test could see them. The second matters:

* `broker_net_cost_engine.py:373-393` — `raw_holding_days` goes 1.0 → 80.0, crosses the
  1.0-day cap, and `horizon_capped` flips **True**. Both sides charge 1.0 day, so no economic
  number moves. Disclosure only.
* `execution.py:8955` — an open `mx_*` position now requests **7,744** M15 bars per tick
  instead of 160. The fetch is not the hazard. **If the terminal returns fewer than 7,680
  closed M15 bars, the count can never reach the budget and the time stop never fires at
  all** — and the wall-clock fallback does not catch it, because that path is taken only when
  the helper returns `None`, not on an honestly short count. The backstop degrades to
  **inert** rather than to late, which is the wrong direction, and the pre-repair 96 had no
  such exposure. Nothing armed is affected (H4 at 1280) and every `mx_*` sleeve is
  default-off. **Filed, not patched** — the obvious mitigation moves armed sleeves onto the
  over-counting wall-clock path and would close them *earlier*, which is not a change to make
  unmeasured at the end of a session.

---

## 7. Handoff — for the orchestrator

0. **I borrowed B1450–B1453 from AR's range.** The commissioned B1400–B1449 was fully used
   before the adversarial pass came back; its four corrections needed blocks and taking the
   next free 50 above B1500 would have separated them from the work they correct. AR should
   start at B1454, or the orchestrator should move me — either is fine, but the collision is
   real and is mine.
1. **`CANDIDATE_FAMILY_V4.json` is unratified and needs a decision.** It raises
   `MECHANISM_CROSS_V1` 276 → 321 on the conservative reading of AL §6.3. Nothing admitted at
   either bill this session, so the raise costs nothing today — but the reading itself
   (is an entry-timing cell a new hypothesis, or an exit-cell-class re-measurement?) is a
   protocol question that will bind the next session that measures an entry convention.
   `CANDIDATE_BOOK_V1` is untouched at 39.
2. **The `mx_btcusd` challenge package must now cite the repair.** OD-AI-6's package
   (AP-4) requires the exit contract named; it also requires the **time-stop unit repair**
   named, because without it the cited economics describe a contract the book cannot run.
   The dossier is written to be cited verbatim.
3. **Five sleeves want a deliberate short horizon.** `mx_us100`, `mx_us500`, `mx_ger40`,
   `mx_us30`, `mx_nzdjpy` were all *better* under the accidental one-bar stop. That is an
   exit-frontier question at the ratified rule — AD's frontier has the D1 time-stop grid
   already, but at the flat band on ALL_ERAS. Re-gating it is cheap (the grid exists) and it
   is the natural AR-2 adjacency.
4. **Four downstream artifacts are still on the defect clock** for `sub_mid_dn_revert`.
   `AQ_ESTATE_TRADES_V2.json.gz` is the input; the rebuild is ~30 machine-minutes total and it
   removes a by-hand substitution three sessions have now had to remember.
5. **`asian_fade`'s published figure overstates its live contract by 0.88 R/day** with zero
   truncation, which means the gap is the trailing-runner contract, not the time stop. Nobody
   has walked that interaction. It is the largest single labelling error in the estate.
6. **Before any `mx_*` sleeve is armed, read the `want = budget + 64` row.** The repaired
   budget makes the live time stop *inert* — not late — if the terminal returns fewer than
   7,680 closed M15 bars. Nothing armed is exposed today; measure the terminal's `copy_rates`
   ceiling before that changes.
7. **The cheapest open item is a timebase stamp, not a capture.** Four pre-2024 H1 files for
   cohort symbols already sit in `data/`; they are refused only because they carry no
   `.timebase.json`. Verifying and stamping their clock would widen the ratified convention's
   evidence by ~2 years on 4 of 14 symbols for roughly a day of work. The matched FTMO
   intraday feed for the other ten is the larger, separate ask. Neither reaches 2001.
