# Generation defects — reproduced faithfully, recorded separately

**Session K deliverable 4.** Written 2026-07-27 while building the generation port (Stage 1.3a) and
answering G4.

**None of these is fixed.** The port reproduces every one of them, including the ones that are
plainly wrong, because the entire value of this lane is that it measures **what actually trades**. A
port that silently improved on the book would stop being a measurement of the book and would reopen
F1 instead of closing it. Continues Session H's `SLEEVE_BOOK_DEFECT_REGISTER.md`, whose numbering
this extends — H used D0–D12, so this starts at **D13**.

**Evidence standard.** Every claim is `[MEASURED]` from source at HEAD, from the 99,112 VPS
runtime-learning packets, or from a replay of the production generators, with `file:line`. Where
magnitude could not be measured, that is said.

**Ranked by economic consequence.** D13 outranks the rest because it is the one that makes a replay
of the live book non-reproducible; D15 outranks its severity class because it is the reason G4's one
open question cannot be closed from the record already on disk.

---

## D13 — Twelve of the 29 live sleeves take their `decision_day` from the wall clock, not from the bar

**Severity: high. Live-realized; and it is the single largest obstacle to reproducible replay.**

`market_expansion_d1.next_open_decision_day` returns the **runtime wall-clock date**
(`sleeves/market_expansion_d1.py:147-161`), and that value overrides the bar-derived `decision_day`
on every market-expansion intent (`:217-221`). `runtime_now` is supplied by the engine from
`datetime.now(timezone.utc)` (`book_engine.py:405`, passed at `:525`), and market-expansion is the
**only** consumer of that kwarg anywhere in the book.

`decision_day` is not cosmetic. It is:

- the correlated-risk-unit bucket key — `buckets[(it.decision_day, cluster)]` (`admission.py:1108-1113`);
- the Kelly-lite day key (`admission.py:1103-1106`) and the running-count store key (`book_engine.py:779`);
- the per-day placement cap key (`book_owner.py:1601-1602`, `placement_ledger.py:92-94`);
- the cluster/day cap key (`book_owner.py:1611-1617`).

**Consequence.** Replaying the same bars at a different moment yields a different risk bucket, a
different Kelly count and a different ledger key for 12 of 29 sleeves. Two replays of the identical
window are not guaranteed to agree, and neither is guaranteed to agree with what live did — through
no fault of either. The port therefore reports its replay clock as part of its provenance and
reproduces the behaviour rather than substituting the bar date.

**Correct behaviour.** The decision day for a D1 sleeve deciding on the close of day *N* and
intending to act at the open of day *N+1* is a genuine modelling choice, and the wall clock is a
defensible proxy for it **live**, where evaluation happens seconds after the close. It is
indefensible in replay. The fix is to derive it from the bar (`bar_time + 1 day`, which the function
already implements as its own fallback at `:162-170`) and let live and replay agree. That changes
live risk bucketing, so it is an owner decision, not an engineering one — and it is adjacent to,
but distinct from, the B54 Part 2 day-key decision already queued.

**What it would be worth.** It is a precondition for any bit-reproducible replay of the
market-expansion book. It does not affect the 8 core or 9 candidate sleeves, so it does not touch
G4. Magnitude on live sizing is **unmeasured** — it would require re-deriving the 44 market-expansion
unit packets under both conventions.

---

## D14 — Generation output depends on persisted disk state and on the order bars were first seen

**Severity: medium. Live-reachable; magnitude unmeasurable from the export.**

`_normalize_future_bar_times` (`book_engine.py:355-402`) can shift the whole `times` series, and when
the broker offset is unavailable it **searches** 30-minute offsets from 1800 s to 18000 s and accepts
the first that makes the bar look fresh (`:306-308`). The accepted offset is memoized on
`((symbol, timeframe, count), raw_bar_iso)` (`:272-274`) and **persisted** to
`pipeline_state/ultimate_book/<namespace>/bar_time_repair.json` (`:119-121`, written `:337-353`,
loaded `:314-335`). When it fires, `bar_cache` is rewritten (`:486-487`) and both `decision_day`
(`:518`) and `decision_bar_iso` (`:535`) move — and `decision_bar_iso` is the placement-ledger
idempotency key.

**Consequence.** Two runs over identical bars can disagree if one inherits a latch the other does
not. A replay that points at the live `pipeline_state/` inherits live's latch history; one that does
not, does not.

**How the port handles it.** `GenerationPort` defaults `state_root` to a fresh temp directory
(`generation.py`, `GenerationPort.__init__`) so a replay can neither read nor write the live latch —
the live file is safety-relevant state and a research replay has no business mutating it. Passing the
live root is supported and explicit, for the case where reproducing a latched run *is* the goal.

**Correct behaviour.** The offset search is a reasonable live repair for a broker feed that lies
about bar times. It should be recorded in the decision packet rather than only in a side file, so a
replay can be told which offset applied instead of having to re-derive or inherit it.

**What it would be worth.** Nothing today — no evidence any latch fired during the live window
(the file is not in the VPS export's `04_pipeline_state/ultimate_book/*/`). It is a correctness trap
for every future replay, which is why it is recorded now rather than after it bites.

---

## D15 — A warmup failure and a no-signal decision are the same observation: nothing

**Severity: medium (observability), and it is load-bearing — it is why D17 was published wrong twice
and why K1-b is undecidable.**

Three distinct generation outcomes leave **no record of any kind**:

| outcome | source | record |
|---|---|---|
| bars empty, or `enough(bars, cluster)` false | `book_engine.py:468-469` — bare `continue` | **none** |
| bar older than `2 × interval` | `book_engine.py:499-500` — bare `continue` | **none** |
| generator ran and returned `None` | `book_engine.py:528-529` | **none** |

Only two generation skips are ever recorded — `profile_missing_instrument_config` (`:446-458`) and
`future_decision_bar_time` (`:490-497`).

**Consequence, measured — and this defect has now cost the session twice.**

1. **It produced D17 and then produced it wrong a second time.** `energy_agri` looked anomalous at
   p = 3.5e-5, then "suggestive", and is now withdrawn entirely. The rate that drove both versions was
   measured against a `USOIL.cash` series of 390 bars ending 2026-04-02 — and because `enough()` fails
   **silently**, nothing in the measurement said the denominator was being gated away. A truncated
   series is indistinguishable from a full one at this seam.
2. **It is half of why K1-b is undecidable** (D21). A warmup failure, a stale-bar skip and a genuine
   no-signal decision are the same observation — nothing — so live's record cannot say what its
   generator saw or whether it ran.

Both are the same root cause: the seam that decides whether a generator runs keeps no record of the
decision or of its input.

**Correct behaviour.** Emit a counted, per-(sleeve, symbol) generation outcome per cycle —
`evaluated / warmup_short(n_bars) / stale_bar / no_signal / intent` — as counters, not packets, so
the cost is a handful of integers per cycle rather than 95 rows. The book already carries the right
shape: `bridge.broker_profile_generation` (`book_engine.py:423-430`) is exactly this at slot level
and survives into the packets on 20,093 cycles. Extending it with a per-outcome histogram is a small
change to a file that is **not** decision-contract-bound (verified against R2: no file under
`src/components/ultimate_book/` is bound), so it costs no re-seal.

**What it would be worth.** It converts G4's remaining question from *"needs a bar-availability
probe"* to *"already answered in the record"*, and it is the denominator every future
generation-frequency claim needs. It is the highest value-per-line item in this register.

---

## D16 — `metals_core`'s four crosses are absent from **one** live profile, not both; on FTMO it ran 6-of-6 and still produced nothing

**Severity: high as a correction — it removes the standing explanation for half the G4 evidence.**

**Corrects `SLEEVE_BOOK_DEFECT_REGISTER.md:56-58` (D0), `IMPLEMENTATION_STATE.md:3046-3049` (B99b),
`THIRD_REVIEW.md:113-116` (§1.2 item 1) and `SESSION_K_GENERATION_PORT.md:34-35`**, all of which say
the four symbols are *"absent from both live profiles"*.

`[MEASURED]` — resolved through the same `symbol_map.build_broker_symbol_resolver` the live engine
uses (`book_owner.py:150-152`), against the merged profile instrument maps:

| profile | instruments | `metals_core` supported | note |
|---|---:|---|---|
| `operator_profile` | 42 | **6 of 6** | the live FTMO profile (`run_book_supervisor.ps1:86-87`) |
| `redacted_account` | 32 | **2 of 6** | XAUEUR/XAGEUR/XAUAUD/XAGAUD absent |
| `ftmo` (legacy) | 27 | 6 of 6 | |

Corroborated three ways: the source comments say so (`metals.py:24-25`, `metals_ob_micro.py:22-27`,
`substrate.py:44-48`); the port reproduces redacted_account's exact 19-slot/8-symbol unsupported list
against live; and the packets say so — **more strongly than this entry first stated.** The redacted_account
side is 216 `profile_missing_instrument_config` skips for `(metals_core, XAUEUR)`; the FTMO side is
**1 `future_decision_bar_time`**, which is a *different* reason emitted at `book_engine.py:490-497`
and reachable **only after** `supports()` returned True, bars were fetched and `enough()` passed. The
first version described these as one 217-skip class split 216/1; they are two different classes, and
the FTMO one positively proves the symbol was bar-backed rather than merely configured.
(`metals_core`'s `profile_missing` total is exactly **864 = 4 × 216** — no 217th skip exists.)

Five of the six FTMO `metals_core` symbols carry such a packet. **`XAGEUR` carries none**, so it has
no positive bar-backed evidence and inherits the D15 blind spot; it belongs on D17's probe list.

Full slot counts: **FTMO 95/95 supported, redacted_account 76/95.**

**Consequence.** On FTMO — one of two live accounts, 291 H4-advancing cycles — `metals_core` had its complete
declared universe and produced nothing. The instrument-config story explains the redacted_account half of
the evidence and **none** of the FTMO half. Any argument of the form *"the anchor sleeve was
hobbled by a config gap"* is now bounded to one account.

**What it would be worth.** It does not change the G4 verdict (which is frequency for `metals_core`)
but it removes a false comfort that would otherwise have been carried into OD-3.

---

## D17 — WITHDRAWN 2026-07-27. `energy_agri` is not anomalous; the rate that made it look so was a truncation artefact

**Severity: NONE. Withdrawn. Kept in full because the correction is more instructive than the claim.**

This entry was published twice and was wrong both times, in the same direction — toward a defect that
does not exist.

1. **First version:** p = 3.5 x 10^-5, "survives Bonferroni", fires "spread across the window".
   The adversarial pass refuted it: the 14 archive fires are one 11-day March episode, and the process
   is overdispersed (index of dispersion 4.26 daily), so Poisson was the wrong model.
2. **Second version:** downgraded to "suggestive, model-dominated". Still wrong, for a different
   reason found when the VPS bars landed: **the rate itself was a truncation artefact.** The archive's
   `USOIL.cash` series was **390 bars ending 2026-04-02**, so `enough(bars,"energy")` warmup-gated
   most of the window out of the denominator and inflated the rate **5.6x**.

`[MEASURED on the corrected archive]` — 42 fires over 7,938 true invocations = **0.529 %/invocation**
(published: 2.966 %). Live open-market slots 874 -> expected 4.62 raw, **2.46 calibrated**, observed 0.
**P(0) = 0.086 Poisson, 0.409 counting fire-days.** Not anomalous on any reading.

**The bar-count probe this entry asked for is no longer needed** — but not for the reason the second
correction gave. **Corrected again 2026-07-27 by the adversarial pass:**

- `USOIL_cash`/`UKOIL_cash` H4 run **2020-12-30 / 2020-12-28** -> 2026-07-26, **not** 2000-03-29. That
  date is EURUSD's; per-symbol history varies widely (metal crosses and SPX500 begin 2021-01-21).
- The series are **not** gappy: 3,963/3,964 and 3,964/3,964 bars on the XAUUSD H4 grid, zero flat bars,
  zero zero-volume bars — better coverage than the indices the control runs on.
- **The rate is not a scalar and the stated cause was wrong by 4.5x.** Per year: 2021 0.793 %, 2022
  0.258 %, 2023 0.032 %, 2024 0.129 %, 2025 0.485 %, 2026 1.325 %; two half-years are exactly 0/3,096.
  Decomposing my "5.6x truncation artefact" on the *same* window gives truncation **1.24x** and the
  window change **4.53x**. I attributed all of it to truncation.

**What actually settles this entry** is the measurement neither correction made: replaying
`energy_agri` over the **live window's own bars** gives **0 fires / 332 invocations** — exactly live's
zero. Empirical P(0) over 1,934 rolling 38-day windows is **0.638**. There is nothing to explain, and
that conclusion needs no rate at all.

**The lesson, which outlives the entry.** This sleeve got **three** confident wrong answers before a
right one, and each was wrong in a different way: a wrong model (Poisson on a clustered process), a
wrong denominator (a truncated series, invisible because `enough()` fails silently — D15), and a wrong
attribution (blaming truncation for a window effect 4.5x larger). What finally settled it was not a
better model but **measuring the thing directly on the window in question.** The register keeps the
entry rather than deleting it because three successive wrong answers about one sleeve, all of them
inferential and all of them avoidable by one direct replay, is the most useful signal in this file.

**Superseded text follows.**

`[MEASURED]` — 14 archive fires over 472 **true generator invocations** (2.966 %/invocation; the
first version divided by 960 scheduled slots and understated the rate 2×). Live open-market slots
874 → expected 25.9 raw, ~14 after the control's 0.54 calibration. **Observed 0.**

**Why the p-value is not quotable.** All 14 fires fall in **2026-03-02 … 03-12** — 5 distinct days,
8 distinct instants, with USOIL and UKOIL firing *together* at 6 of the 8, so they are not
independent draws. One 11-day March oil episode. That is the sleeve behaving as designed:
`energy_agri.py:1-11` documents a `vr >= 2.0` "supply-shock vol ignition" trigger, which is an
event-driven, clustered arrival process. Measured index of dispersion **4.26 daily / 7.65 weekly**
against Poisson's required 1.0. P(zero) spans **5e-12 (naive Poisson) to 0.09–0.15 (counting
episodes or fire-days)**, and the clustered model is the one that matches the measured process.

The positive control on the same replay — `idxrev`, expected 290 vs **157 distinct live intents**,
ratio **0.54** — rules out a systematic driver error but is itself only good to a factor of ~2.

**The two surviving hypotheses**, which D15 prevents the record from separating:

1. a genuine generation defect specific to `energy_agri` in the live configuration;
2. the live MT5 feed returning < 200 H4 bars for `USOIL.cash` / `UKOIL.cash`, warmup-gating the
   sleeve silently. Plausible: these are `.cash` CFD symbols whose history is shallower than spot,
   and the depth probe (`vps-ticks-20260726/MARKET_DATA_DEPTH_PROBE.json`) measured **M1 depth
   starting only 2026-04-17** for at least one FTMO symbol, so shallow series on this broker are not
   hypothetical.

**How to settle it, cheaply.** One read-only bar-count check on the incoming VPS export: fetch 260 H4
bars for `USOIL.cash`, `UKOIL.cash`, `USOUSD`, `UKOUSD` on both brokers and count what comes back.
`< 200` proves hypothesis 2 and closes this as a data gap. `≥ 200` leaves hypothesis 1 and makes it
a code defect worth a session.

**What it would be worth.** `energy_agri` carries confidence 0.80 — the second-highest in the book.
If it is defect 1, a sleeve holding 20.5 % of core-8's confidence weight has never fired in
production. **Do not report this as a confirmed defect, and do not quote a p-value for it.** Add
`XAGEUR` to the same probe: it is the one FTMO `metals_core` symbol with no bar-backed evidence
anywhere in the packets (the other five each have at least one `future_decision_bar_time` packet,
which proves they were bar-backed and passed warmup at least once), so it carries the same D15 blind
spot.

---

## D20 — The H4 cycle fires all weekend on BTCUSD's bar, and five of six H4 sleeves are silently staleness-gated on 25 % of cycles

**Severity: low live (costs nothing), medium for measurement — it inflates every generation
denominator by ~25 %.**

`[MEASURED]` — `DEFAULT_REF_SYMBOL[16388] = ["XAUUSD", "BTCUSD"]` (`launcher.py:49`), and
`_latest_closed_bar_iso` advances if **any** reference symbol is newer (`launcher.py:162`). BTCUSD
trades 24/7; metals, oil and indices do not. So an H4 cycle fires through the weekend on BTCUSD's
bar, and on those cycles every metals/oil/index series is more than two intervals stale and is
dropped at `book_engine.py:499-500` — with **no record** (D15).

**74 of FTMO's 291 H4-advancing cycles (25.4 %)** and 6 of redacted_account's 226 fall inside the
Fri 21:00 → Sun 21:00 UTC closed-market window. All 52 FTMO H4-only cycles are Saturdays and
Sundays. Corroborated in the archive: of 678 driven closes, 187 are calendar-closed and XAUUSD is
staleness-gated at 181 of them (96.8 % agreement).

**Consequence.** Live it is free — the guard does exactly its job and no wrong trade results. But any
statement of the form *"sleeve X was evaluated N times"* built on cycle counts is inflated by ~25 %
for the five non-crypto H4 sleeves, and this entry exists because **G4's own first draft made that
error** (`G4_GENERATION_VERDICT.md` §7.6).

**Correct behaviour.** Either give the H4 reference set per-cluster (metals sleeves keyed on a metals
reference), or record the staleness drop as a counter — which is D15, and is the better fix because
it makes the gap visible instead of assuming it away.

**What it would be worth.** Nothing live. It is a precondition for any future generation-frequency
claim being right the first time.

---

## D18 — Two sleeves declare a wider symbol surface to the sizer than they can ever generate on

**Severity: low today (dead surface), latent.**

`[MEASURED]` — `admission.SleeveSpec.symbols` vs `sleeves/registry.SleeveSpec.on_surface`:

| sleeve | admission surface | generation surface | declared but ungenerable |
|---|---:|---:|---|
| `energy_agri` | 4 (`admission.py:176`) | 2 (`sleeves/energy_agri.py:20`) | `CORN_c`, `COTTON_c` |
| `idxrev` | 8 (`admission.py:197`) | 5 (`sleeves/index_jpy.py:18`) | `EU50_cash`, `FRA40_cash`, `US2000_cash` |

All other 27 sleeves agree.

**Consequence.** The registry advertises a breadth the generator cannot deliver. Nothing sizes today
because an intent can only exist for a symbol the generator emits, so the extra names are inert. They
are, however, exactly the kind of latent mismatch that becomes a live 1.6× breadth error the moment
someone builds a per-sleeve breadth or diversification calculation off the admission registry —
which is the natural place to look.

**Correct behaviour.** One surface, or an explicit assertion at import that the two agree for every
sleeve. **What it would be worth.** Nothing today; it removes a trap.

---

## D19 — `vss_fxcross_london_up_low` is a sixth sleeve that never generated, and it is in nobody's list

**Severity: low (scope correction).**

`[MEASURED]` — 94 packets over 38 days, **100 % pre-generator**, zero `candidate_id`, zero unit
membership, zero placements. Identical evidential signature to the prompt's five.

It is a declared candidate-book sleeve (`agent_config.yaml:1283`, confidence 0.12,
`candidate_registry.py:158-163`) with the `..._oos_decay_watch_aux_required` status. It requires a D1
aux feed (`sleeves/registry.py:92-95`), which is the obvious first place to look — an aux feed that
returns nothing produces no intent and, per D15, no record.

**Consequence.** Every statement of the form "five silent sleeves" undercounts. The correct statement
is **five silent *train-validated core* sleeves, and six silent sleeves overall**.

**What it would be worth.** Small — it carries 0.12 confidence. Recorded so the census is right.

---

## D21 — The live book does not record the bars it read, and that alone blocks K1-b permanently

**Severity: high for measurement. It is the reason K1 cannot be closed by any amount of replay.**

`[MEASURED]` — replaying all 2,640 live FTMO cycles from the corrected VPS bar archive reproduces
live's candidate **count** on 2,282 (86.44 %). 182 of the residual per-intent differences survive
every mechanical explanation:

| candidate cause | test | result |
|---|---|---|
| wrong bar values | M15 rebuilt from the FTMO tick archive | **96/96 bars identical** |
| wrong decision bar | port `times[-1]` vs live `decision_bar_iso` | identical |
| wrong replay clock | live bar->cycle lag measured | exactly one interval (15.0 m at M15) |
| insufficient history | re-ran at 210/230/260/300/400/600 bars | identical output at every depth |
| coverage | per-timeframe availability, complete 43-symbol archive | **0 of the 182 lack bars** |
| live never evaluated the bar | live cycle at 05:15:31, `spec_count=10` | present, `n_candidates_in=0` |
| the two server-clock copies disagreeing | `_server_clock` vs `fx_jpy._to_server_local` | identical, both seasons |

And `fx_jpy`/`fx_jpy_ny` reproduce **exactly** — all 27 live USDJPY decision bars matched at offset
0.0 minutes, zero live-only intents — so the machinery is demonstrably capable of exact reproduction.

**What is left** is that live's MT5 returned a different bar series at that instant than
`copy_rates_range` returns for the same window six weeks later: a shorter in-terminal history, an
un-backfilled gap, or a since-revised bar. **Nothing in the record preserves it.** A worked case:
`asian_fade` emits only on the day's first Asian-range break (`asian_fade.py:96-99`); on 2026-07-08
the port breaks at 05:00 and live at 11:30, which requires live's Asian range to have been wider —
computed from bars the archive reproduces tick-exactly.

**Correct behaviour.** Record, per `get_closed_bars` call, `(symbol, timeframe, n_bars,
first_bar_iso, last_bar_iso)` and ideally a digest of the closes. A handful of integers per cycle, on
`book_engine.py` which is **not** decision-contract-bound, so no re-seal.

**Sharpened 2026-07-27 on the completed archive.** With all 43 FTMO symbols × D1/H4/M15 present the
coverage excuse is gone (evidence-gap misses = 0) and count agreement moved **down** to 86.44 %. The
residual then resolves by a *structural* property of the sleeve, not by data:

| class | live-recall |
|---|---:|
| per-bar (each bar judged on its own) | **96 %** |
| first-of-day (emits only on the session's first qualifying event) | **19 %** |

`fx_jpy` and `asian_fade` are both M15 FX sleeves on the same archive through the same clock; one
reproduces at 100 %, the other at 7 %. A first-of-day rule is a **latch** (`asian_fade.py:98`
"ONLY if that first break is bar i"; `asia_pdl_fade.py:97` "the FIRST Asian bar today"), so one
differing bar early in a session flips which bar is "first" and live and replay stay diverged for the
whole day. That also explains why the offsets scatter (−108..+84 bars) instead of being constant, and
why only 4 % of misses pair within ±2 bars.

**What it would be worth.** It converts K1-b from undecidable to decidable for the per-bar sleeves —
already 96 % — and it is the second independent argument for D15's counter: D15 wants to know
*whether* the generator ran, D21 wants to know *what it ran on*. For the **seven path-latched
sleeves** the bar digest may not be sufficient and the latch itself should be emitted
(`first_break_bar_iso` per sleeve/symbol/session).

**The finding that outlives the gate:** for those seven sleeves **replay is not a verification method
at all** — not this port's, and not anyone's — until the book records either its inputs or its latch.
That is a statement about the live book's testability, and it is worth more than a K1 pass.

---

## D22 — The bar export recorded no failures, so a total absence of eleven symbol families was invisible

**Severity: medium (process). Fixed by the owner on 2026-07-27; recorded because the failure mode
recurs.**

The first VPS bar pull requested canonical GTOS names (`UK100`, `SPX500`, `USOIL_cash`) while FTMO
exposes those instruments under **dotted broker symbols** (`UK100.cash`, `US500.cash`,
`USOIL.cash`) — the crossing `symbol_map.py:12-15` exists to bridge. `symbol_info` returned `None`,
the symbols were dropped, and `BARS_MANIFEST.json` was **rebuilt from success sidecars**, so it
carried no record that anything had been requested and failed. The gap was undetectable from the
manifest.

It surfaced only because the port generated zero `idxrev` intents and `idxrev` was the positive
control. **A control that is expected to fire is what makes a silent coverage gap loud.**

Now fixed: 43 symbols at H4 and D1, sidecars carry `broker_symbol`, and the manifest carries an
explicit `FTMO_COVERAGE_GAPS` list.

**Why it is in this register rather than only in the ingest note:** this is the **third** instance in
one session of the canonical<->broker crossing producing a silent empty result — the other two were my
own replay driver (bar files keyed canonically; `book_engine.py:461` fetches the broker name). Three
independent instances is an argument that the boundary wants a single enforced helper that raises on
an unresolvable symbol, rather than care at each call site.

---

## Not defects — three things that look like defects and are not

Recorded because each cost verification time, and the next session should not re-spend it.

1. **`active_specs` returning 32 while the live book is 29.** Not a defect: the DF-1 filter
   (`book_engine.py:439-440`) skips any spec absent from `effective_registry`, and the three extras
   are exactly the clean_3 sleeves (`sub_xvol_pullback`, `sub_mid_dn_revert`, `vp_euidx_pocgrav`)
   that `include_clean3: false` drops. Generation is 29. **But** two other `active_specs` call sites
   do **not** apply DF-1 — `launcher.py:111-118` (which builds `_tf_tags`) and
   `book_owner.py:471-490` (manageable symbols) — so they see 32. Harmless today because clean_3
   introduces no new timeframe and its symbols are covered; worth knowing before someone relies on
   either as the census.
2. **`effective_registry()` returning 8 rather than 29.** Not a defect and not a wrong claim in the
   third review — the function's market-expansion arm needs the *policy-resolved allowlist*, not the
   raw config value. Called bare it returns the core 8; called as live calls it (with the 9-name
   candidate allowlist and `resolve_market_expansion_sleeves("positive_weighted12_after_swap")`) it
   returns exactly 29. A reader reproducing "29 sleeves" naively will get 8 and think the docs are
   wrong. They are not.
3. **The A8 metals confluence gate as an explanation for the metals silence.** Armed and live
   (`admission.py:1083-1084`, `agent_config.yaml:1315`), and it *would* drop metals intents failing
   3-of-4 — but no metals intent ever reached admission (`G4_GENERATION_VERDICT.md` §2), so it is
   causally irrelevant to G4. It remains a real risk for the day the metals sleeves do fire, and
   Session H's D3 (the running-conviction pre-count omitting this gate) is unaffected.
