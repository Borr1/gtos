# G4 — were the silent high-confidence sleeves silent by frequency or by defect?

**Session K deliverable 3.** Written 2026-07-27 while building the generation port (Stage 1.3a).

**The answer is frequency, and it is settled by direct measurement rather than by inference.**
Replaying the port over the live window's **own bars** produces **zero intents across ~990 generator
invocations per sleeve** — exactly what live produced. The generators ran, on the real bars, and found
no signal. The hypothesis the session prompt did not name — *generated, then killed downstream* — is
refuted separately and outright (§2): no intent from any of the five ever existed.

**Read Revision 4 first; it supersedes the rest of this document's quantitative apparatus.** The
revision banners run newest-first. Everything below Revision 2 is the superseded reasoning, kept
because in this document the corrections have been more instructive than the original answers — four
revisions, and each one moved a verdict.

> **Revised 2026-07-27** after a commissioned adversarial pass refuted three of five claims in this
> document's first draft, including its headline p-value. The verdict below is the surviving one;
> everything withdrawn is in §7. The first draft said "three of five are frequency, one is not at
> p = 3.5 × 10⁻⁵, one sits on the line" — that was built on a mis-specified denominator, an
> uncalibrated control, and an unverified claim about how the archive fires were distributed.


> ## REVISION 4 — 2026-07-27. The question was directly measurable and I never measured it.
>
> A commissioned adversarial pass ran the one experiment this document should have opened with:
> **replay the five sleeves over the live window's own bars.** Result, which I reproduced
> independently before accepting it:
>
> | sleeve | generator invocations, 2026-06-18…07-24 | fires |
> |---|---:|---:|
> | `metals_core` | 990 | **0** |
> | `metals_softband` | 990 | **0** |
> | `metals_ob_micro` | 990 | **0** |
> | `crypto` | 440 | **0** |
> | `energy_agri` | 332 | **0** |
>
> (BTCUSD-driven grid; the XAUUSD grid gives 960/960/960/320/320, also all zero.)
>
> **The port, fed the live window's own bars, produces exactly what live produced: nothing.** So G4's
> answer is a *direct reproduction*, not an inference:
>
> - **H-defect is refuted directly.** Each generator ran ~990 times on the real bars and returned
>   `None` every time. That is a sleeve correctly finding no signal, not a sleeve unable to fire.
> - **H-freq is confirmed directly.** There is no residual to explain and no p-value to argue about.
>
> **Everything in §5 and in Revision 3 that transfers a rate from another window is therefore
> superseded scaffolding — and it was also wrong.** The adversarial pass established:
>
> - The single control calibration is **unsound**: measured per sleeve on the live window it spans
>   **6.4×** (0.36 for `fx_jpy` to 2.31 for `kz_london_crypto_low`), and **2.25×** even within the
>   per-bar family. Every P(0) that used it is unsound.
> - "The archive over-predicts live by ~2×" is **false in aggregate**: over the same 2,640 cycles live's
>   own attribution-gap-free counter sums to **706** and the port to **585** — the port *under*-generates
>   by 17 %.
> - The "control reproduced on two archives, two symbol sets" claim is **refuted**: `idxrev`'s surface
>   is the same fixed 5-tuple in both, the in-tree window is a strict subset of the VPS window, and
>   both divide the same numerator 157. It is an arithmetic identity, not a reproduction.
> - Empirical P(0) over 1,934 rolling 38-day windows — no model, no calibration — is **0.369**
>   (`metals_core`), 0.375, 0.816, **0.284** (`crypto`), 0.638 (`energy_agri`), and **0.075 for all five
>   being zero together.** My Poisson figures were off by 10–14× and even my fire-day model by 30–125 %.
>
> **The headline is unchanged and now rests on a measurement instead of a model: all five silent core
> sleeves are silent because they had no signal, on the actual bars, in the actual window.**
>
> Two corrections of fact that survive into the register: `energy_agri`'s rate is not a scalar
> (0.429 % over 5.6 y, 0.529 % over 2024-26, 1.325 % in 2026) and truncation explains only **1.24×** of
> the 5.6× I attributed to it — the other **4.53×** is the window change. And the oils' H4 history
> begins **2020-12-30**, not 2000-03-29; that date is EURUSD's alone.
>
> §5 below is kept as the superseded first answer, because the correction is the point.


> ## REVISION 3 — 2026-07-27, after the VPS bars landed. Two verdicts moved.
>
> The rates below were re-measured on the corrected VPS bar archive (43 FTMO symbols, H4 from
> 2000-03-29) instead of the in-tree archive, which lacked the four metal crosses, DASHUSD, and a
> complete `USOIL.cash`. **Three of the five point rates were wrong by 3-6x**, and they moved in both
> directions:
>
> | sleeve | published rate | corrected | x | corrected P(0) Poisson | P(0) fire-day |
> |---|---:|---:|---:|---:|---:|
> | `energy_agri` | 2.966 % | **0.529 %** | **0.2** | 0.086 | 0.409 |
> | `metals_core` | 0.104 % | **0.391 %** | 3.8 | 0.027 | 0.262 |
> | `crypto` | 0.289 % | **1.075 %** | 3.7 | 0.024 | 0.126 |
> | `metals_softband` | 0.313 % | 0.323 % | 1.0 | 0.050 | 0.205 |
> | `metals_ob_micro` | 0.104 % | **0.029 %** | 0.3 | 0.762 | 0.752 |
>
> **`energy_agri` is no longer the anomaly.** Its published rate came from a `USOIL.cash` series of
> 390 bars ending 2026-04-02; the truncation warmup-gated most of the window out of the denominator
> and inflated the rate 5.6x. D17 closes as natural frequency.
>
> **The anomaly moved to `metals_core` and `crypto`** — both of which previously rested on a *single*
> fire across two symbols and now rest on 93 and 70. Under Poisson they sit at p ~ 0.025; under the
> clustering-aware model the adversarial pass established for these event-driven sleeves, at
> 0.13-0.26.
>
> **The headline is unchanged: all five remain consistent with natural frequency.** But the cadence
> is ~2x faster than published — `metals_core` **~35 intents/yr**, not 9-17; the five combined
> **~126/yr**, not 55-90 — so *"far too short"* is better stated as *"too short, with the observed
> zero at the edge of what frequency comfortably explains."*
>
> ~~The control is now reproduced independently: `idxrev` calibrates at 0.532 on the VPS archive
> against 0.54 on the local one. Two archives, two symbol sets, same factor.~~ **STRUCK by Revision 4
> — an arithmetic identity, not a reproduction: same 5-symbol surface, overlapping windows, same
> numerator.**
>
> Full working: `K1_GATE_RECEIPT.md` §4. Machine-readable: `receipts/G4_GENERATION_RATE.json` (v2).
> The §5 table below is the superseded first measurement, kept because the corrections are the point.



**Evidence standard.** Every claim is `[MEASURED]` from source at HEAD, from the 99,112 VPS
runtime-learning packets, or from a replay of the **production** generator code over the in-tree bar
archive, with `file:line`. Where a magnitude could not be measured, that is said. Claims made and
then withdrawn during the session are kept in §7.

---

## 1. The question, restated precisely

The prompt asks whether the five silent high-confidence sleeves were *"silent because of natural
signal frequency, or because of a generation defect."* Those are not the only two worlds. A sleeve
can also generate normally and be killed between generation and placement — and the A8 metals
confluence gate (`admission.py:1083-1084`), which is **live `true`** (`agent_config.yaml:1315`) and
armed with populated features (`metals.py:145-163`), is exactly such a killer sitting on the metals
path. So there are three hypotheses, and they are separable:

| | hypothesis | what it would mean |
|---|---|---|
| **H-freq** | the generator ran and legitimately found nothing | the book is honest and slow; OD-3 is about cadence and account choice |
| **H-defect** | the generator ran and could not fire | the book has never been tried; its 2015–2026 validation was never deployed |
| **H-filtered** | it fired and was killed after generation | the book is being throttled by a gate, not by its own signal |

**The five sleeves** are the `train_validated` core sleeves — `metals_core` (conf 1.00),
`crypto` (0.85), `energy_agri` (0.80), `metals_softband` (0.50), `metals_ob_micro` (0.30)
(`admission.py:156-188`). Their confidence sums to **3.45 of core-8's 3.90 = 88.5 %**; the only
core-8 sleeves that placed are the three 0.15-confidence ones, which is B63's "11.5 % of core-8's
confidence weight" restated exactly (0.45 / 3.90).

---

## 2. H-filtered is refuted — no intent ever existed [MEASURED]

**The load-bearing evidence is unit membership, not the skip-reason split.** Stated that way round
because the skip-reason split — which an earlier draft of this section led with — is *not* sufficient
on its own, and the adversarial pass was right to break it (§7.5).

- **The decisive test.** An intent that exists is named in `bridge.would_units[].sleeve_members`,
  `bridge.realized_units[].sleeve_members`, `unit.sleeve_members`, `admission_unit_members[].sleeve`,
  `candidate_id`, or `ultimate_book_intent_id`. Across all 99,112 packets those six fields name 16–18
  distinct sleeves each, and **none of the five appears in any of them**, exact-match.
- **The supporting split.** `_generate_intents` emits exactly two skip reasons before
  `spec.generator()` is called — `profile_missing_instrument_config` (`book_engine.py:446-458`) and
  `future_decision_bar_time` (`:490-497`) — and `future_decision_bar_time` has exactly one emitter
  tree-wide. But `profile_missing_instrument_config` has a **second** emitter inside
  `run_cycle`'s placement loop (`book_owner.py:1567-1574`), on an intent that already exists and
  under a *different* predicate (`_profile_supports_symbol`, `:428-432`, which has an extra
  base-symbol escape). So the reason string alone does not prove pre-generator. The five are excluded
  from that second path by having zero unit membership — it fires only on a **sized** `realized_unit`
  (`book_owner.py:1550-1552`).

**A trap for anyone re-running this check:** a substring scan appears to find `crypto` in 7,271
`candidate_id`s and 328 `sleeve_members`. Those are `ny_crypto_momentum`, `orb_crypto_london`,
`kz_london_crypto_low`, and the *cluster* named `crypto`. Use exact matching or you will "refute"
this section falsely.

Classifying all 15,768 `unit_*` packets on the split:

| sleeve | packets | pre-generator | post-generation | any `candidate_id` or unit membership, ever |
|---|---:|---:|---:|:--|
| `metals_core` | 871 | **871** | **0** | **none** |
| `metals_softband` | 871 | **871** | **0** | **none** |
| `metals_ob_micro` | 871 | **871** | **0** | **none** |
| `crypto` | 219 | **219** | **0** | **none** |
| `energy_agri` | 4 | **4** | **0** | **none** |
| `vss_fxcross_london_up_low` | 94 | 94 | 0 | none |
| *(contrast)* `idxrev` | 241 | 10 | 231 | yes |
| *(contrast)* `fx_jpy` | 152 | 38 | 114 | yes |

**No intent attributable to any of the five ever existed** — not in `candidate_id`, not in
`bridge.would_units[].sleeve_members`, not in `bridge.realized_units[]`, not in
`admission_unit_members[]`. **H-filtered is dead.** The A8 gate never had anything to gate; nor did
the cost screen, the spread screen, the damage guard, or the gross cap.

A sixth sleeve is in the same state and is **not** in the prompt's list of five:
**`vss_fxcross_london_up_low`** — a declared candidate-book sleeve (conf 0.12), 94 packets, 100 %
pre-generator, zero intents in 38 days.

---

## 3. The denominator — scheduled slots, which is **not** the same as generator invocations [MEASURED]

A generator that runs and returns `None` leaves **no trace at all** (`book_engine.py:528-529`), so
the denominator has to be derived. **Corrected 2026-07-27 after the adversarial pass; the first
version of this section overstated both its independence and what it was counting** (§7.6, §7.7).

**The best available source is the launcher log**, `05_shadow_logs/ultimate_book_launcher.jsonl.gz` —
5,237 `action=="cycle"` rows carrying `advanced_tf` per namespace. It is genuinely independent of the
packet stream and it disagrees with it:

| | launcher log | packet-derived | delta |
|---|---:|---:|---:|
| FTMO H4-advancing cycles | **291** | 281 | −10 |
| redacted_account H4-advancing cycles | **226** | 216 | −10 |

The packet stream is missing ten H4-advancing cycles per namespace — cycles that emitted no
runtime-learning packet at all. Use **291 / 226**.

**Two things the earlier draft got wrong, both material:**

1. **"Derived two independent ways that agree exactly" was false.** On FTMO there is no second path
   at all — FTMO reports `broker_unsupported_symbol_slot_count = 0` in every cycle, so no
   `profile_missing` skips exist there to count. And on redacted_account the two "paths"
   (`active_spec_count` at `book_engine.py:441` and the unsupported-skip list at `:455-457`) are two
   fields of the **same telemetry dict, incremented in the same loop iteration** — one measurement
   reported twice.
2. **Both paths count *scheduled* (sleeve, symbol) slots, not generator invocations.** The
   `profile_missing` check runs at `:446-458`, **before** the bar fetch, the `enough()` warmup gate
   (`:468`) and the 2-interval staleness gate (`:499`) — and the latter two `continue` with no record
   (D15). Every slot lost to them is counted as if the generator ran.

**How large is that gap? Large, and measurably so.** `DEFAULT_REF_SYMBOL[16388] = ["XAUUSD",
"BTCUSD"]` (`launcher.py:49`) with ANY-advance semantics (`:162`): BTCUSD trades 24/7, metals and oil
do not. So an H4 cycle fires all weekend on BTCUSD's bar while every metals/oil/index series is > 8 h
stale and staleness-gated at `:499-500`. **74 of FTMO's 291 H4-advancing cycles (25.4 %) and 6 of
redacted_account's 226 fall inside the Fri 21:00 → Sun 21:00 UTC closed-market window** — all 52 FTMO
H4-only cycles are Saturdays and Sundays. Recorded as **D20**.

So the honest statement:

> **`metals_core` was *spec-active* on 6 × 291 + 2 × 226 = 2,198 scheduled symbol-slots, of which at
> most ~1,742 were on an open market, and it produced zero intents. The true number of generator
> invocations is not measurable from the live record** — which is D15 biting the very measurement
> that discovered it.

The earlier figure of 2,118 was neither the scheduled count nor the invocation count.

---

## 4. The prompt, B99b and D0 are wrong about `metals_core`'s universe [MEASURED]

> "`metals_core` … ran a **2-of-6 symbol universe** because four of its declared symbols are absent
> from **both live profiles**." — `SESSION_K_GENERATION_PORT.md:34-35`, restating
> `SLEEVE_BOOK_DEFECT_REGISTER.md:56-58` (D0) and `IMPLEMENTATION_STATE.md:3046-3049` (B99b).

Measured against the profile instrument maps, resolved through the same
`symbol_map.build_broker_symbol_resolver` the live engine uses (`book_owner.py:150-152`):

| profile | instruments | `metals_core` supported |
|---|---:|---|
| `operator_profile` — **the live FTMO profile** (`run_book_supervisor.ps1:86-87`) | 42 | **6 of 6** |
| `redacted_account` — the live redacted_account profile | 32 | **2 of 6** (XAUEUR/XAGEUR/XAUAUD/XAGAUD absent) |
| `ftmo` (legacy) | 27 | 6 of 6 |

The source comments say so too (`metals.py:24-25`: *"The crosses are FTMO-only"*), and the packets
agree: `(metals_core, XAUEUR)` has **216 `profile_missing_instrument_config` skips on redacted_account** and **1 `future_decision_bar_time` on FTMO** -- two different classes, and the FTMO one positively proves the symbol was bar-backed, not merely configured. (`XAGEUR` has no such packet; see D16.)

**Consequence, and it is the reason this matters rather than pedantry:** on FTMO — one of the two
live accounts, 291 H4-advancing cycles — `metals_core` had its **complete declared six-symbol universe** and
still produced nothing. The instrument-config explanation covers the redacted_account half of the evidence
and **none** of the FTMO half. Recorded as **D16**.

---

## 5. The frequency measurement, with a control [MEASURED — SUPERSEDED by Revision 4]

> **Everything in this section is superseded.** G4 is settled by direct measurement on the live
> window's own bars (Revision 4), which needs no rate transfer, no calibration and no p-value. The
> rates below are also individually wrong or unstable — see Revision 3 and Revision 4. Kept because
> the corrections are the most instructive part of this document.

The natural rate is measured by running the **production generators** — via the port, so it is the
same code, not a reimplementation — over the in-tree bar archive `data/historical_2026/`, driven at
the archive's own real H4 bar closes, 2026-01-01 … 2026-04-24 — **480 XAUUSD closes** for the
market-open rate table below (the union with BTCUSD's 24/7 closes is 678; the difference is D20).

**This window is out-of-sample for the live question and is read for *generation counts only*: no
P&L, no outcome, no ordering is read from it.** It is not one of the four sealed B7.5 campaign
windows and March stays outcome-unread in the sense §3.2 of the working agreement protects.

**The control.** `idxrev` is the same cluster of code, same timeframe, same driver — and it was the
**top live placer** (41 placements, **157 distinct intents**). If the archive replay were mis-driven,
`idxrev` would come out wrong. It broadly does not — but only broadly; see the calibration below.

The control failed twice before it passed, and both failures were real driver bugs that presented as
*"the sleeve did not fire"* — see §7. That is the entire reason a positive control was run.

**Null control:** `EmptyBarSource` → zero candidates, with the engine still exercised
(`tests/test_replay_policy_generation.py::test_empty_bar_source_generates_nothing`).

**Rates are per *true generator invocation*, measured by wrapping every `SleeveSpec.generator`** —
not per scheduled slot. The two differ a lot, because warmup and staleness gates cut before the
generator and leave no record (D15): survival is 100 % for the metals sleeves at XAUUSD closes but
only **49 %** for `energy_agri` (its `USOIL.cash` archive series is 390 bars ending 2026-04-02) and
83 % for `idxrev`. The earlier draft of this table divided by scheduled slots and understated every
rate — for `energy_agri` by 2×.

Live denominators are **open-market** H4 cycles (FTMO 217, redacted_account 220), excluding the D20
weekend cycles where these sleeves are staleness-gated.

| sleeve | archive fires | true rate/invocation | live open slots | expected | observed | P(0) Poisson |
|---|---:|---:|---:|---:|---:|---:|
| `idxrev` *(control)* | 265 | 13.263 % | 2,185 | 289.8 | **157** | — |
| **`energy_agri`** | 14 | 2.966 % | 874 | 25.9 | 0 | 5.5e-12 |
| `metals_softband` | 3 | 0.313 % | 1,742 | 5.45 | 0 | 4.3e-3 |
| `metals_core` | 1 | 0.104 % | 1,742 | 1.81 | 0 | 0.16 |
| `metals_ob_micro` | 1 | 0.104 % | 1,742 | 1.81 | 0 | 0.16 |
| `crypto` | 1 | 0.289 % | 654 | 1.89 | 0 | 0.15 |

### The control does not permit two-digit p-values, and that is the most important line here

**`idxrev`: expected 290, observed 157 distinct intents → ratio 0.54.** (By distinct
`(namespace, decision_bar_iso, symbol, direction)` it is 135 → 0.47.)

The earlier draft reported this control at **1.11**, using **231** — which is the count of
*post-generation packets*, not intents. One live intent can emit several packets as its bar is
re-evaluated; `idxrev` has intents emitting up to seven. Counting `ultimate_book_intent_id` gives
157. (`fx_jpy` is 1:1 at 114/114/114, so the inflation is specific to `idxrev`'s re-evaluation
pattern — precisely why counting packets was unsafe.)

**So the archive over-predicts live by roughly 2×**, and the honest consequence is that every λ in
the table above carries at least a factor-2 uncertainty. Multiplying through by the measured 0.54
calibration: `metals_core` 0.98, `metals_ob_micro` 0.98, `crypto` 1.02, `metals_softband` 2.94,
`energy_agri` 14.0. **No p-value below is stated to more than one significant figure, and none
should be.**

### The verdict, per sleeve

- **`metals_core`, `metals_ob_micro`, `crypto`, `metals_softband` — H-freq. Silence is unremarkable.**
  Calibrated expectations of ~1.0, ~1.0, ~1.0 and ~2.9 intents over the entire live window; P(zero)
  ≈ 0.4, 0.4, 0.4 and 0.05. **There is no anomaly to explain.** `metals_core` — the registry's
  "deepest anchor", confidence 1.00 — fires about once per **thousand** invocations. `metals_softband`
  moved into this group when the control was corrected; the earlier draft had it "on the line" at
  9.2e-3 using an uncalibrated Poisson.
- **`energy_agri` — anomalous, but the significance is model-dominated and its own clustering argues
  against the strong reading.** All 14 archive fires fall in **2026-03-02 … 03-12** — 5 distinct
  days, 8 distinct instants, and USOIL/UKOIL fire *together* at 6 of 8, so they are not independent
  draws. That is one 11-day March oil episode, which is exactly what the sleeve is built to catch
  (`energy_agri.py:1-11` documents a `vr >= 2.0` "supply-shock vol ignition" trigger). Measured
  index of dispersion: **4.26 daily, 7.65 weekly** — Poisson requires 1.0. P(zero) therefore ranges
  from 5e-12 (naive Poisson on the true rate) to **0.09–0.15** counting episodes or fire-days, which
  is the model that matches the measured process. **Suggestive, not decisive. Do not quote a
  p-value for this sleeve.** An earlier draft of this section said the fires were "spread across the
  window"; that was false and unverified — see §7.

**The headline is unchanged by all of this, and is strengthened:** all five silent core sleeves are
consistent with natural frequency once denominators and the control are computed correctly. The book
is honest and very slow.

---

## 6. What this does **not** settle, stated plainly

**6.1 — The warmup gate is invisible, and it is `energy_agri`'s alternative explanation.** When
`enough(bars, cluster)` fails, `_generate_intents` does `continue` with **no skip record**
(`book_engine.py:468-469`). So in the live packet stream, *"the generator ran and returned None"* and
*"the bar series was short and the generator never ran"* are **the same observation: nothing.** If
FTMO's live feed returned < 200 H4 bars for `USOIL.cash`/`UKOIL.cash` — plausible for `.cash` CFD
symbols with shallower history than spot — `energy_agri` would be silent with no defect at all.
**This is the leading alternative to H-defect and it is not yet excluded.** It is excluded by one
cheap check against the live bars now being exported: fetch 260 H4 bars for both energy symbols on
both brokers and count. Until then `energy_agri` is *"anomalous, cause not established"*, and I am
not calling it a code defect.

**6.2 — The archive rate is measured on fewer symbols than live ran.** `metals_core`'s rate comes
from XAUUSD/XAGUSD only (the four crosses are not in the local archive); `crypto`'s from BTCUSD only.
If the missing symbols fire at similar rates, expected live fires rise and the frequency verdict
**weakens**. Concretely, if the four metal crosses fire at the XAUUSD/XAGUSD rate, `metals_core`'s
expected live count is unchanged (the calculation already applies the rate to all live
open-market slots including the crosses) — but the *rate itself* would be better estimated. The direction
of this uncertainty is knowable and should be closed with the incoming bars.

**6.3 — Different window, possibly different regime.** The rate is measured 2026-01…04; the live
window is 2026-06…07. A sleeve whose trigger depends on volatility regime could differ. The
`idxrev` control (ratio 0.54 across exactly this window gap) bounds the transfer error at about 2x, but
it is one control on one sleeve.

**6.4 — This is generation only.** Nothing here says whether these sleeves would have been
*profitable*. It says whether they had the opportunity to be measured. They did not.

**6.5 — The M15 sleeves were not rate-measured, and the omission is declared rather than silent.**
G4 concerns the five `train_validated` core sleeves, all of which are H4, so the H4 table answers it.
An equivalent table for the 10 M15 sleeves was started and **stopped unfinished**: at ~5,300 M15
closes against sleeves declaring up to 30 symbols and up to 3,200 bars of lookback
(`liq_asia_up_low_metal`), the run was still going after ~30 minutes and was competing for CPU with
the mandatory full-suite A/B — and two or three tests in this suite are known flaky under load
(B30, B79b), so letting it run would have risked corrupting the regression evidence. **No M15 rate is
claimed here.** The one M15-adjacent fact that is claimed — `vss_fxcross_london_up_low` produced zero
intents (D19) — comes from the packets, not from a rate replay. Re-running it is cheap and
unblocked; it just needs a quiet machine.

---

## 7. Claims I made during this session and then withdrew

Kept because each cost verification time and because §A2 of the third review is the most trusted
part of that document.

1. **"The A8 metals confluence gate is a live third hypothesis for the metals silence."** Raised
   early from `admission.py:1083-1084` and it is a real armed gate — but **refuted** in §2: no metals
   intent ever reached admission, so the gate is causally irrelevant to G4. It stays in the register
   as a latent risk for when the sleeves *do* fire, not as a G4 explanation.
2. **"`idxrev` fires zero times in the archive"** — twice, and both times it was my driver, not the
   sleeve. (a) I stepped synthetic UTC multiples of four for H4 closes; FTMO's H4 bars close at UTC
   21/01/05/09/13/17 because the server runs NY+7. (b) I keyed bar files by **canonical** symbol
   while `book_engine.py:461` fetches under the **broker** symbol, so `SPX500`→`US500.cash` and every
   index/oil series silently returned nothing. Both now pinned as tests. **Had I not run a positive
   control, I would have published "all six H4 sleeves are silent, therefore systemic defect" — the
   most exciting available conclusion, and wrong.**
3. **"The runtime-learning packets carry no generation telemetry."** Reported to me by one reader and
   **false**: `bridge.broker_profile_generation` is present on 20,093 packets and carries
   `active_spec_count`, `active_symbol_slot_count`, `profile_supported_symbol_slot_count`,
   `broker_unsupported_symbol_slot_count` and the unsupported symbol list. It is the field the port
   is validated against (§8). Corrected before it reached any conclusion.
4. **"The denominator G4 needs does not exist in the live record."** Same reader, also false — §3
   derives a *scheduled-slot* denominator, though not the invocation count (see 6 below).

**Withdrawn after the commissioned adversarial pass (2026-07-27), which refuted three of five claims
it was given.** These are my errors, found by a refuter instructed to default to "refuted":

5. **"Only two skip reasons reach the packet stream, both pre-generator."** False.
   `profile_missing_instrument_config` has a **second emitter** at `book_owner.py:1567-1574`, inside
   the placement loop, on an intent that already exists and under a different predicate. I verified
   this directly. The §2 conclusion survives on unit-membership evidence, which is stronger and
   should have been the lead; the skip-reason split alone never was sufficient.
6. **"The denominator is derived two independent ways that agree exactly."** False twice over. On
   FTMO the second path does not exist at all (zero unsupported slots, so no skips to count), and on
   redacted_account the two "paths" are two fields of the same telemetry dict incremented in the same loop
   iteration. Worse, both count **scheduled slots**, not generator invocations — and the
   `ultimate_book_launcher.jsonl.gz` log, a genuinely independent source I never consulted, gives
   **291/226**, not 281/216. §3 is rewritten.
7. **"The idxrev control passes at ratio 1.11."** False, and it was the load-bearing number for the
   whole rate transfer. 231 counts post-generation *packets*; distinct intents are **157**. The
   control is **0.54** — the archive over-predicts live by ~2×. Every expectation in §5 is now
   calibrated and no p-value is quoted beyond one significant figure.
8. **"`energy_agri`'s 14 archive fires are spread across the window."** **False, and I did not check
   it before writing it.** All 14 fall in 2026-03-02 … 03-12: 5 days, 8 instants, both symbols firing
   together at 6 of 8. Measured dispersion index 4.26 daily / 7.65 weekly, so Poisson was the wrong
   model. `energy_agri` is downgraded from "not frequency, p = 3.5e-5" to "suggestive, model-
   dominated", and D17's severity with it. This is the single worst error in the first draft: an
   unverified qualitative assertion propping up the receipt's most dramatic number.
9. **"`metals_softband` is on the line at p = 9.2e-3."** Withdrawn — that used an uncalibrated
   Poisson on a scheduled-slot denominator. Calibrated, it is ~0.05 and joins the frequency group.

**What survived the pass unchanged:** §2's conclusion (no intent ever existed), §4/D16 (`metals_core`
ran 6-of-6 on FTMO — the refuter could not break it and confirmed the four crosses are full
instrument blocks, not stubs, reached without family aliasing), and the port itself.

---

## 8. Reproduce

```bash
# the pre/post-generator classification and the denominator
python3 docs/audits/fable5-vision-audit-20260725/phase3/receipts/g4_packets.py

# the natural-rate table with the idxrev control
python3 docs/audits/fable5-vision-audit-20260725/phase3/receipts/g4_rate.py

# the port's behavioural tests, including both controls
python3 -m pytest tests/test_replay_policy_generation.py -q
```

Machine-readable: `receipts/G4_GENERATION_RATE.json`.

---

## 9. What this means for OD-3

Stated as measurement, not as a recommendation — the composition and dial are Borhen's.

1. **The fortnight did not measure the book.** 88.5 % of core-8's confidence weight sits in sleeves
   whose expected firing count over the entire 38-day window was **≈ 4.2 intents combined**. Zero was
   a likely outcome. Any inference from that window about the W7 book's *core* is inference from a
   sample that was never taken — which is F1 closed at generation level, and it is now quantified
   rather than asserted.
2. **The measurable book and the validated book are nearly disjoint.** What actually traded was
   `idxrev`, `fx_jpy`, `fx_jpy_ny` (registry-falsified or forward-only) plus the candidate book. What
   was validated was the metals/energy/crypto core, which fired ~0 times.
3. **The cadence number OD-3 needs**, stated as a range because the control admits a factor-2
   uncertainty (§5) [MEASURED, annualising by 365/38 = 9.61]: across both accounts the four
   non-anomalous core sleeves generate **≈ 55–90 intents/year**; **`metals_core` alone — the
   1.00-confidence anchor — is ≈ 9–17 intents/year.** Accumulating 30 core intents takes on the order
   of **4–6 months**. A window that measures this book's core is *quarters*, not weeks, and that is a
   hard input to any activation-timeline argument. The uncertainty band does not change the
   conclusion: even the optimistic end leaves the 38-day window far too short.
4. **`energy_agri` was the one open thread and it is now closed as frequency** (Revision 3). What
   follows was written before the bars landed and is superseded; kept because the direction of the
   correction matters more than the original claim. The residual open thread is smaller and different:
   `metals_core` and `crypto` at p ~ 0.025 under an independence model they do not satisfy.

   *Superseded:* it is a weaker thread than the first draft claimed
   (§5, §7.8): its archive evidence is a single 11-day March oil episode, and under the
   clustering-aware model that matches its own documented trigger, zero in 38 days has probability
   ~0.1. It is still worth the one bar-count check (`USOIL.cash`, `UKOIL.cash`, `USOUSD`, `UKOUSD`,
   and add `XAGEUR` — the one FTMO `metals_core` symbol with no bar-backed evidence in the packets),
   because that check is cheap and settles it either way.

5. **The three-hypothesis frame is the reusable part.** H-filtered was refutable from evidence
   already on disk, in an afternoon, with no bars. Any future "sleeve X is silent" claim should be
   run through the same split before anyone schedules a replay to investigate it.
