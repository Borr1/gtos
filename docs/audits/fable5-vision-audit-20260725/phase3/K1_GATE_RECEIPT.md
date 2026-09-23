# K1 — the generation port's acceptance gate: the full verdict

**Session K deliverable 2.** Written 2026-07-27; revised after the VPS bars landed, again after the
archive's index/oil coverage gap was corrected, and **finally after the archive was completed to all
43 FTMO symbols × D1/H4/M15**. This version is measured on the complete archive: there is no
remaining coverage excuse anywhere in it.

---

## 0. Verdict, stated first

> **K1 is NOT PASSED.**
>
> | | | |
> |---|---|---|
> | **K1-a** | the port evaluates the same sleeves × symbols live evaluated, per cycle | **PASSED** — 20,093/20,093 cycles, both namespaces, zero disagreements |
> | **K1-b** | the port produces the same intents live produced, from the same bars | **FAILED** — 2,282/2,640 cycles agree on count (86.44 %); 358 enumerated below |
> | **K1-c** | those intents size to the same units | **NOT REACHED** — gated on K1-b |
> | **K1-d** | the comparator itself is validated | **PASSED** — §5 |

The gate demanded *zero disagreements, or an enumerated and classified list*. It is the second. The
disagreements are enumerated in §3 and machine-readable in `receipts/K1B_DISAGREEMENTS.json`.

**What is worth saying plainly:** completing the archive did not rescue K1-b — it removed the last
excuse. Evidence-gap misses went to **zero**, 7 of the 28 previously bar-blocked intents reproduced,
21 became genuine misses, and count agreement moved *down* 0.15 pp. Every residual disagreement is now
a real one.

**And the residual has a structure, which is the most useful thing in this receipt.** Splitting the
sleeves by whether their rule is path-dependent within the session:

| class | agreed | live-only | **live-recall** |
|---|---:|---:|---:|
| **per-bar** — each bar judged on its own (`fx_jpy`, `fx_jpy_ny`, `idxrev`, the `mx_*` D1 sleeves) | 160 | 7 | **96 %** |
| **first-of-day** — emits only on the session's *first* qualifying event (`asian_fade`, `asia_pdl_fade`, `orb_crypto_london`, `metal_session_reversion`, `ny_crypto_momentum`, `kz_london_crypto_low`, `liq_asia_up_low_metal`) | 40 | 175 | **19 %** |

`fx_jpy` and `fx_jpy_ny` reproduce at **100 %** — every live decision bar matched at offset 0.0. The
five-fold gap tracks the *structural* property of the sleeve, not its symbol, timeframe or data
quality. §3.5 explains why, and it changes what K1-b's failure means.

---

## 1. What the bars changed

The earlier receipt's §3 named three blocking gaps. All three are closed:

| gap | requirement | delivered |
|---|---|---|
| H4 warmup | 46.2 calendar days | 43 symbols; earliest 2000-03-29 (EURUSD) — **per-symbol varies**: oils 2020-12-30, metal crosses and SPX500 2021-01-21 |
| M15 warmup | 49.7 days | 2024-01-01 → 2026-07-27, **43 symbols** |
| D1 warmup | > 200 days | 43 symbols, same per-symbol caveat |

The wiring was a wiring job, as promised: `CsvBarSource` gained gzip, the raw MT5 broker-epoch
encoding, and the export's sidecar schema. **No caller changed**, and the `BarSource` protocol did
not move.

**One correction I should record against myself:** the first pull was missing every index and oil
family, and I attributed that to the canonical-vs-broker-name crossing. That was right — the pull was
keyed on canonical GTOS names while FTMO exposes `UK100.cash`, `US500.cash`, `USOIL.cash` — and it has
been fixed and re-pulled. It is the same crossing that broke my own replay driver twice (§5). Three
independent instances in one session is a strong argument that the canonical↔broker boundary wants a
single enforced helper rather than care.

**Nothing is outstanding.** The archive was completed to all 43 FTMO symbols × D1/H4/M15 on
2026-07-27 and `FTMO_COVERAGE_GAPS` is now empty *and derived by set-difference* rather than
accumulated from successes. The new M15 index data was verified the same way as the rest: UK100 M15
rebuilt from the FTMO tick archive agrees **92/92** on 2026-07-08.

**What completing it did to K1-b**, measured rather than assumed:

| | M15 partial | M15 complete |
|---|---:|---:|
| port intents | 555 | **585** |
| agreed | 193 | **200** |
| live-only | 189 | **182** |
| port-only | 362 | **385** |
| count agreement | 86.59 % | **86.44 %** |
| live-only blocked by missing bars | 28 | **0** |

Of the 28 previously bar-blocked intents, **7 now reproduce and 21 became genuine misses.** Count
agreement went *down*. **Completing the data did not move K1-b toward passing; it removed the last
excuse for it failing.**

---

## 2. K1-a — the generation surface, reproduced at 100 % [MEASURED]

Unchanged from the earlier receipt and re-verified. `bridge.broker_profile_generation` is present on
20,093 live packets; running the port under each advancing-timeframe combination reproduces **every**
distinct live telemetry block on both namespaces — 6 of 6 on FTMO (3,525 cycles), 4 of 4 on
redacted_account (16,568) — including redacted_account's exact 8-element unsupported-symbol list. Zero
disagreements. This half needed no bars at all.

---

## 3. K1-b — enumerated, not summarised

Replay: all **2,640** distinct live FTMO cycles, driven at each cycle's own `created_at_utc`, under
each cycle's own flags recovered by `packet_validation.config_from_bridge`, with the tag set implied
by its generation telemetry. FTMO only — the redacted_account pull is 7 of 43 symbols and would bias any
cross-broker claim.

### 3.1 Count level — the level at which zero is achievable

Live's `bridge.n_candidates_in` is written by the bridge from the intent list itself, so unlike the
per-intent packets it has **no attribution gap**. It is therefore the honest denominator.

| | cycles | candidates |
|---|---:|---:|
| agree exactly | **2,282 / 2,640 (86.44 %)** | |
| port over-generated | 160 | +201 |
| port under-generated | 198 | −265 |
| live counter total | | 706 |
| port total | | 585 |

### 3.2 Identity level, and why it cannot reach zero

| | count |
|---|---:|
| live intents **named** (sleeve, symbol, decision_bar_iso) | 383 |
| …of a live counter total of | 706 |
| port intents | 585 |
| agreed | 200 |
| live-only | 182 |
| port-only | 385 |

**Live names only 54 % of its own candidates.** `unit_admitted` is sleeve-null on 81 % of rows and
`unit_shadow` on 41 % (D15/C6), so a port intent live also had can still be unmatchable. A worked
example: cycle `2026-07-08T06:15:44` has `n_candidates_in = 3` and the port produced exactly 3 — but
live named only one of them. That is not a disagreement; it is an unreadable record.

### 3.3 The 182 live-only intents, classified

| class | count | disposition |
|---|---:|---|
| **evidence gap — no bars at the sleeve's own timeframe** | **0** | the archive is complete |
| **genuine output difference** | **182** | §3.4, §3.5 |

There is no longer any coverage-based excuse in this table.

**And the port-only side, tested against live's own counter** — for each cycle, can live's
`n_candidates_in` accommodate the extra intents the port produced?

| | intent-instances | share |
|---|---:|---:|
| explained by live's **unnamed** candidates (D15 attribution gap) | 175 | 44.2 % |
| **unexplained** — live's own counter says no such candidate existed | **221** | **55.8 %** |

So the divergence is genuinely two-way: 182 live intents the port does not produce, and 221 port
intent-instances live's counter says did not exist.

### 3.4 The 182, and what they are not

Every one is **M15**, and they concentrate in the session-anchored sleeves
(`asian_fade` 38, `asia_pdl_fade` 81, `metal_session_reversion` 22, `orb_crypto_london` 13,
`ny_crypto_momentum` 11, `kz_london_crypto_low` 5, `liq_asia_up_low_metal` 5, `idxrev` 5).

**Two sleeve families reproduce exactly.** `fx_jpy` and `fx_jpy_ny`: every one of live's 27 USDJPY
decision bars is matched at **offset 0.0 minutes**, and there are **zero** live-only intents for
either. So the machinery — clock, bar selection, warmup, session logic — is demonstrably capable of
exact reproduction.

**What I eliminated, each by measurement rather than argument:**

| candidate cause | test | result |
|---|---|---|
| wrong bar values | rebuilt M15 from the FTMO tick archive | **96/96** (EURUSD) and **92/92** (UK100) identical |
| wrong decision bar | port's `times[-1]` vs live's `decision_bar_iso` | identical (11:30 for a cycle at 11:45:12) |
| wrong replay clock | measured live's bar→cycle lag | exactly one bar interval; min 15.0 m at M15, 240 m at H4 |
| missing history | re-ran at 210/230/260/300/400/600 bars | identical output at every depth |
| coverage | per-timeframe bar availability, complete archive | **0 of the 182 lack bars** |
| live not evaluating that bar | live cycle at 05:15:31 | present, `spec_count=10`, `n_candidates_in=0` |
| the two server-clock implementations disagreeing | `_server_clock` vs `fx_jpy._to_server_local` | identical on all probes, summer and winter |

The worked case: on 2026-07-08 the port emits `asian_fade`/EURUSD on the 05:00 bar; live evaluated
that same bar and recorded **zero** candidates, then emitted its own on the 11:30 bar. `asian_fade`
emits only on the day's **first** Asian-range break (`asian_fade.py:96-99`), so live's Asian range must
have been wider than the archive's — but the range is computed from bars the archive reproduces
tick-exactly.

**The one candidate left standing** is that live's MT5 returned a *different bar series* at that
instant than a `copy_rates_range` pull returns for the same window six weeks later — a shorter
in-terminal history, an un-backfilled gap, or a since-revised bar. **The live record does not preserve
the bars a cycle consumed**, so this is not decidable from the export. That is D15 again, biting the
measurement that discovered it.

**I am not classifying these 161 as a port defect, and not as a live defect.** They are
`evidence_gap:live_input_bars_unrecoverable`, and the honest consequence is that **K1-b cannot be
closed by any amount of replay work** — it needs the live book to record what it read. That is a
concrete, cheap change (D15's counter proposal, extended with a bar-series digest per fetch) and it
is the precondition for K1-b ever passing.

### 3.5 The residual has a mechanism: path dependence amplifies an input difference the record does not keep

Splitting all 17 sleeves that produced any intent on either side, by whether their rule is
**path-dependent within the session**:

| class | agreed | live-only | port-only | **live-recall** |
|---|---:|---:|---:|---:|
| **per-bar** — each bar judged on its own | 160 | 7 | 161 | **96 %** |
| **first-of-day** — emits only on the session's *first* qualifying event | 40 | 175 | 224 | **19 %** |

Per sleeve:

| sleeve | class | agreed | live-only | recall |
|---|---|---:|---:|---:|
| `fx_jpy` | per-bar | 54 | 0 | **100 %** |
| `fx_jpy_ny` | per-bar | 45 | 0 | **100 %** |
| `mx_nzdjpy_d1_donchian_20_breakout` | per-bar | 5 | 0 | 100 % |
| `vol_compression` | per-bar | 3 | 0 | 100 % |
| `idxrev` | per-bar | 49 | 5 | 91 % |
| `asia_pdl_fade` | first-of-day | 35 | 81 | 30 % |
| `metal_session_reversion` | first-of-day | 2 | 22 | 8 % |
| `asian_fade` | first-of-day | 3 | 38 | 7 % |
| `orb_crypto_london` | first-of-day | 0 | 13 | 0 % |
| `ny_crypto_momentum` | first-of-day | 0 | 11 | 0 % |
| `kz_london_crypto_low` | first-of-day | 0 | 5 | 0 % |
| `liq_asia_up_low_metal` | first-of-day | 0 | 5 | 0 % |

**The split tracks a structural property of the rule, not the symbol, the timeframe, or the data.**
`fx_jpy` and `asian_fade` are both M15 FX sleeves reading the same archive through the same clock;
one reproduces perfectly and the other at 7 %.

**Why.** A first-of-day rule is a *latch*. `asian_fade` emits "ONLY if that first break is bar i"
(`asian_fade.py:98`); `asia_pdl_fade` takes "the FIRST Asian bar today to sweep+reclaim the PDL (one
fade per day)" (`:97`). So a single differing bar early in the session flips which bar becomes "the
first", and from that moment live and the port are latched to different bars **for the rest of the
day** — and never re-sync, because the latch is per-day. A per-bar sleeve has no memory: one
differing bar costs exactly one bar.

This is consistent with every measurement, including the ones that look contradictory:

- The bars **are** right where checked (96/96 and 92/92) — but I checked two symbol-days out of
  thousands, and this mechanism needs only **one** differing bar anywhere in a session to diverge the
  whole day.
- The bar-lag hypothesis is **refuted** as a general explanation: only 4 % of live-only intents have a
  port intent on the same (sleeve, symbol) within ±2 bars, and the nearest-neighbour offsets scatter
  from −108 to +84 bars. That is exactly what a latch that fired on a different bar produces — once
  diverged, the day's selections are unrelated, not offset by a constant.
- The port is not uniformly over- or under-generating: 160 cycles over, 198 under.

**What this changes about K1-b's failure.** It is not "the port is 86 % right". It is: **the port is
~96 % right on sleeves whose output is a function of the current bar, and the remaining error is
concentrated, by construction, in sleeves whose output is a function of the whole session's path** —
which cannot be reproduced from bars alone unless the bars are identical to the last tick, and the
record does not let anyone verify that they were.

**The consequence for the programme is sharper than a percentage.** Seven of the live book's sleeves
are path-latched. For those, *replay is not a verification method* — not this port's replay, and not
anyone's — unless the live book records either the bars it read or the latch it set. That is a
finding about the book's testability, and it is worth more than a K1 pass would have been.

---

## 4. Does this change G4 or the defect register? **Yes — materially. Stated, not slipped in.**

### 4.0 Superseded by direct measurement — read this before §4.1–§4.4

A commissioned adversarial pass ran the experiment §4 should have opened with: **replay the five
sleeves over the live window's own bars.** Reproduced independently before acceptance:

| sleeve | invocations, 2026-06-18…07-24 | fires |
|---|---:|---:|
| `metals_core` / `metals_softband` / `metals_ob_micro` | 990 each | **0** |
| `crypto` | 440 | **0** |
| `energy_agri` | 332 | **0** |

**The port on the live window's own bars produces exactly what live produced: nothing.** G4 is a
direct reproduction, not a rate transfer, so §4.1–§4.3's calibration and p-values are scaffolding
around a directly measurable quantity — and the pass showed the scaffolding was also wrong:

- the single calibration spans **6.4×** across sleeves measured on the live window (2.25× within the
  per-bar family), so every P(0) built on it is unsound;
- "the archive over-predicts live ~2×" is **false in aggregate** — live's own counter sums to 706
  against the port's 585, a 17 % *under*-generation;
- the "control reproduced on two archives" claim is an **arithmetic identity**: same 5-symbol surface,
  overlapping windows, same numerator 157;
- empirical P(0) over 1,934 rolling 38-day windows is 0.369 / 0.375 / 0.816 / 0.284 / 0.638, and
  **0.075 for all five zero together** — my Poisson figures were off 10–14×.

§4.1–§4.4 are kept below as the superseded reasoning. Two corrections of fact from them do survive
and are carried into the register: `energy_agri`'s rate is **not a scalar** (0.429 % over 5.6 y,
0.529 % 2024-26, 1.325 % in 2026) and truncation explains only **1.24×** of the 5.6× — the other
4.53× is the window change; and the oils' H4 history starts **2020-12-30**, not 2000-03-29.

### 4.1 D17 is resolved, in the opposite direction to my first draft

`energy_agri`'s measured rate is **0.529 %/invocation, not 2.966 %** — 5.6× lower. My published figure
came from an archive whose `USOIL.cash` series was **390 bars ending 2026-04-02**; the truncation
inflated the rate by warmup-gating most of the window out of the denominator.

| | expected live | observed | P(0) Poisson | P(0) fire-day |
|---|---:|---:|---:|---:|
| published | 25.9 | 0 | 5e-12 | — |
| **corrected** | **2.46** | 0 | **0.086** | **0.409** |

**`energy_agri` is no longer anomalous on any reading.** D17 closes as *natural frequency*, and the
bar-count probe I asked for is no longer needed for it. It stays in the register as a **withdrawn**
entry with the arithmetic, because a register that quietly drops its most dramatic item is worse than
one that keeps the correction visible.

### 4.2 …and two other sleeves moved the other way

| sleeve | published rate | corrected | ×  | P(0) Poisson | P(0) fire-day |
|---|---:|---:|---:|---:|---:|
| `metals_core` | 0.104 % | **0.391 %** | 3.8 | 0.027 | 0.262 |
| `crypto` | 0.289 % | **1.075 %** | 3.7 | 0.024 | 0.126 |
| `metals_softband` | 0.313 % | 0.323 % | 1.0 | 0.050 | 0.205 |
| `metals_ob_micro` | 0.104 % | **0.029 %** | 0.3 | 0.762 | 0.752 |

Both increases are the same artefact in reverse: the local archive lacked the four metal crosses and
DASHUSD, so `metals_core` rested on **one** fire across two symbols and `crypto` on **one**. They now
rest on 93 and 70.

**So the anomaly moved.** It was `energy_agri`; it is now — weakly — `metals_core` and `crypto`. And
under the clustering-aware model the adversarial pass established is the correct one for these
event-driven sleeves, **none of the five is significant**: P(0) ranges 0.13–0.75.

### 4.3 The G4 headline survives, and the control is now independently reproduced

**All five silent core sleeves remain consistent with natural frequency.** The control is the
strongest part: `idxrev` predicts 295.3 live intents against 157 observed → calibration **0.532**.

> **Struck by the second adversarial pass (§4.0).** I called this "reproduced on two archives, two
> symbol sets". It is neither: `idxrev`'s surface is the same fixed 5-tuple in both archives, the
> in-tree window is a strict *subset* of the VPS window, and both divide the same numerator 157.
> 0.5417 vs 0.5317 is an arithmetic identity, not a reproduction. `idxrev` is also the worst available
> calibrator — its own rate is the most stable of the six (±5 % over six years) while the sleeves it
> corrects vary 2.5×–41×. The calibration is **not sleeve-independent** (6.4× spread) and nothing
> should rest on it. It does not matter to G4's answer, which is now a direct measurement.

**The cadence number for OD-3 changes and gets worse for the "too slow to measure" argument:**

| | published | corrected |
|---|---|---|
| `metals_core` | 9–17 intents/yr | **≈ 35/yr** |
| five core sleeves combined | 55–90/yr | **≈ 126/yr** |

*(Both corrected again in §4.0: the defensible figures are **bands**, metals_core 31–58/yr and the five
combined 85–161/yr, and the process is bursty — metals_core's median 38-day count is 2 against a mean
of 6.05, with 36.9 % of windows at zero. "≈35/yr" reads as steady; it is not.)*

The book is roughly **2× faster** than I told you. The conclusion still holds — at 35/yr, 38 days
expects ~3.6 `metals_core` intents and zero were seen — but the margin is thinner, and *"the window
was far too short"* is now better stated as *"the window was too short, and the observed zero sits at
the edge of what frequency comfortably explains."*

### 4.4 D0/D-I is now quantified [MEASURED]

The four FTMO-only metal crosses contribute **62.4 %** of `metals_core`'s *generation* (robust to
dropping the busiest cross-days: 61.2 / 61.3 / 60.0 %), **74.0 %** of `metals_softband`'s and
**71.4 %** of `metals_ob_micro`'s. DASHUSD is **41.4 %** of `crypto`'s.

**But "a third of the book" was the wrong inference and is withdrawn.** The book places **one
correlated risk unit per (cluster, day)** (`admission.py:1004`; `metals.py:20-26`: *"the unit splits
across more symbols, it does not stack more units"*). At unit level:

| | FTMO 6-sym | redacted_account 2-sym | crosses add |
|---|---:|---:|---:|
| metals-cluster unit-days, 2024-26 | 61 | **35 (57.4 %)** | 26 (42.6 %) |
| full history | 127 | 72 (56.7 %) | 55 (43.3 %) |

**redacted_account runs ~57 % of FTMO's metals complex at the level that actually sizes risk, not a third.**
Two further facts D-I needs: 62.4 % is *below* the 66.7 % naive symbol-count share, and **60 % of
cross fires land on the same instant as a USD-leg fire** (71 % same day) — they are substantially the
same opportunity re-expressed, not independent ones. And `metals.py:15-17` records that the four
crosses "were not on the validated data surface -> added later with data-coverage reconcile", so
**62.4 % of `metals_core`'s generation sits outside the W7 validation** — which cuts against adding
them, and is the most decision-relevant thing in this subsection.

---

## 5. K1-d — the comparator-refutation pass

**Positive control.** `idxrev` replayed through the same driver. It read **zero twice**, and both
times the comparator was wrong, not the sleeve: synthetic UTC bar closes (FTMO's H4 close on the NY+7
grid), and bar files keyed by canonical symbol when `book_engine.py:461` fetches the broker name.
Both are pinned as tests. After the fixes the control calibrates at 0.53 on two independent archives.

**A third error the control did not catch — a commissioned refuter did.** I reported the control at
ratio 1.11 using 231, which counts post-generation *packets*; distinct intents are 157, so the ratio
is 0.54. That pass refuted **three of the five claims it was given** — the denominator, the control
ratio, and the `energy_agri` p-value — and produced D20. Full record in `G4_GENERATION_VERDICT.md`
§7.5–§7.9.

**Null control.** `EmptyBarSource` → zero candidates with the engine still exercised.

**Independent verification of the bars themselves**, new in this revision: M15 bars rebuilt from the
FTMO tick archive agree with the delivered archive **96/96** on the worked day. The bar layer is not
taken on trust.

**And the discipline caught the archive's own gap.** The first pull recorded no failures, so its
absence of index/oil symbols was invisible in the manifest; it surfaced only because the port
generated zero `idxrev` intents and `idxrev` was the control. A control that is expected to fire is
what makes a silent coverage gap loud.

---

## 6. What would close K1-b

Not more replay, and not more data — completing the archive moved count agreement **down** 0.15 pp.
Two changes, and §3.5 says which one matters for which sleeve:

1. **Record the bars read.** A per-fetch `(symbol, timeframe, n_bars, first_bar_iso, last_bar_iso)`
   tuple plus a digest of the closes. A handful of integers per cycle on a file that is **not**
   decision-contract-bound. This alone would close the per-bar sleeves, which are already at 96 %.
2. **Record the latch.** For the seven first-of-day sleeves, the bar digest is necessary but may not
   be sufficient — a difference anywhere earlier in the session flips the latch. Emitting the latch
   itself (`first_break_bar_iso` per sleeve/symbol/session) makes those sleeves verifiable directly
   instead of by re-deriving a whole session and hoping it matches.

Until both exist, the honest ceiling for K1-b is **86.44 % count agreement with 358 enumerated
cycles**, and the ceiling is *structural*: **~96 % on per-bar sleeves and ~19 % on path-latched ones.**
No amount of replay work moves the second number, because the quantity that decides it is not
recorded anywhere.

---

## 7. Reproduce

```bash
python3 -m pytest tests/test_replay_policy_generation.py -q       # 19 behavioural tests
python3 docs/audits/fable5-vision-audit-20260725/phase3/receipts/g4_packets.py
```

Machine-readable: `receipts/G4_GENERATION_RATE.json` (v2), `receipts/K1B_DISAGREEMENTS.json`.
