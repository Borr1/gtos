# Session CA — the revival gates and the fill-truth restatement (wave 14, B2100–B2149)

**Owner authority:** Borhen's 2026-07-31 Training-Lane ratification and the standing
directives (own judgment; build/improve/fix, never refute-and-stop; Workflow opt-in standing).
**Arms nothing.** No config byte moved, no R2-bound path was touched, no broker-capable script
was run, the VPS was not contacted. H1 drift check: **2, both `UNHYDRATED-LFS`** — the
documented condition, not a seal break.

Receipts under `phase14/receipts/`: `CA_DATA_PROBE_V1.json`, `CA_REVIVAL_TRADES_{ARCHIVE,
MERGED,VP}_V1.json.gz`, `CA_REVIVAL_GATE_V1.json`, `CA_FILL_TRUTH_RESTATE_V1.json`,
`CA_FIRST_WEEK_V1.json`, `CA_MX_INCUBATION_V1.json`, `CANDIDATE_FAMILY_V12.json`; drivers
`ca_revival_generate.py`, `ca_revival_gate.py`, `ca_family_v12.py`, `ca_fill_truth_restate.py`,
`ca_first_week.py`, `ca_armed_set_amendment.py`, `ca_mx_incubation.py`. Owner pages:
`phase14/ARMED_BOOK_AT_FILL_TRUTH.md` and `phase14/MX_BTCUSD_INCUBATION_DOSSIER.md`.
A/B: `phase14/SESSION_CA_AB.md` — **0 bad → 0 bad, 0 regressed, 269 → 279 passing**
(+10 net new) over 12 files, tool-emitted `gtos-ab-receipt-v1`, scope widened past the
import closure's 7 on both sides with the difference declared.

---

## 0. The findings, in the order they matter

### 1. A live sleeve was armed with no stop rule, and a live monitor could not pass its own critical check

Both found without a single fill, and both fixed.

**`mx_btcusd_d1_donchian_20_breakout` has been trading real money on FTMO since 2026-07-31
~01:26 UTC with no row in `FIVE_SLEEVE_STOP_CONDITIONS_V1.json` at all** — no risk floor, no
evidence floor, no carry alert, no hold-time alert, no promotion rule. The Training Lane
constitution ratified the same day requires pre-registered stop **and** promotion rules
written *before* arming. They are written now, derived rather than chosen, and the dossier's
own header records that the order was wrong.

**And `S6_book_composition` — the condition whose own text is "read this first; nothing below
matters if it is wrong" — would have fired CRITICAL on both accounts against a correct host
read.** Its `expected_tags` still held `fx_jpy` (pulled 2026-07-30 ~14:57Z) and not
`mx_btcusd`, and it was ONE flat list while the two accounts now run different books. A
CRITICAL that is always wrong is worse than no check: it trains its reader to skip it.

Derived thresholds for the incubant, from **one** object — the gate's own `diagnose=True`
decomposition at the ratified rule on the `target_5R` contract it actually runs, which
reproduces the standing admission exactly (n 232, +0.982 R/day, p 0.0011):

| rule | value | measured false-trip / false-promotion |
|---|---:|---:|
| S1a risk floor | **−9.089 R** | 0.070 |
| S1b evidence floor | −9.09 R | 0.070 |
| S3 carry: alert / stop | 34.0 / 40.6 nights | — |
| S4 hold: alert | 360 h (3× the 120 h median) | — |
| **P1 promotion ceiling** | **+34.0 R** | 0.097 |

The promotion rule is the exact mirror of S1b: the shallowest 0.5 R step a **zero-mean**
sleeve reaches within 60 fills with probability ≤ 0.10. Its honest calendar at this sleeve's
live fill rate (0.270/week) is **~51 months**. That is the price of promotion on evidence, not
a schedule — and it is an argument for a cheaper instrument, not for a looser threshold.

### 2. The commission's premise held for one sleeve of three, and the correction is mechanical

`CARRYCOND_FETCH_20260730.md` reports `missing: []` on all three and reads it as "the three
dead sleeves' data blockade is broken". Measured against the archive the estate actually
generates from:

| sleeve | was it data-blocked? | what the 2026-07-30 fetch adds |
|---|---|---|
| `metals_softband` | **no, and never was** | 22 H4 bars per cross (0.26 %), **zero symbols** |
| `sub_mid_dn_revert` | partly — 2 of its 20 declared symbols | CORN.c (5 trades), COTTON.c (11) |
| `vp_euidx_pocgrav` | **yes** — no M1 aux existed anywhere | GER40/UK100 M1 from 2026-04-27 |

The cause is mechanical and will recur: `av_deep_h4_ingest.py:78-81` searches exactly two
roots, both `data/mt5_research_exports/`, and **the bar archive the estate walk generates from
is neither** — it is `/Users/borr/GTOSActive/vps-bars-20260727`. Four of the six symbols
`metals_softband` needs were in that archive the whole time, and `AA_ESTATE_TRADES.json.gz`
has held 237 of its trades since 2026-07-29.

**Control:** the archive-only arm regenerates `AQ_ESTATE_TRADES_V2` exactly — 237/237 and
533/533 with zero `r_gross` mismatches — so every difference in the merged arm is the fetch's
and nothing else's.

### 3. Zero `REVIVAL_CANDIDATE`s, and each "no" has a different shape

At the ratified rule (RECORDED with AN's conditions, `B_balanced` α 0.10, `CANDIDATE_BOOK_V1`
all-declared, all four bands published, chronological fold table, `maxbars` share reported):

| sleeve | verdict | n (RECORDED, mid) | R/day | p | failing |
|---|---|---:|---:|---:|---|
| `metals_softband` | **STAYS_DEAD** | 221 | +0.0902 | 0.283 | robustness, significance |
| `sub_mid_dn_revert` | **STAYS_DEAD** | 341 | +0.1206 | 0.163 | robustness, significance |
| `vp_euidx_pocgrav` | **NOT_EVALUABLE** | 33 | — | — | sample |

- **`metals_softband` is not carry-conditional in any sense that decides its verdict.** Zero
  carry is worth **+0.155 R/day** and moves no verdict at any band. Its
  `SURVIVOR_BOOK_V1` CARRY_CONDITIONAL tier compared a break-even hold to an *assumed*
  horizon; measured against its realised one, `robustness` is what kills it — one fold carries
  the expectancy, and dropping it retains 24.8 %.
- **`sub_mid_dn_revert`'s new members changed nothing, and "nothing" needed a bound.** The
  gate's verdict is byte-identical to BB's *without* them, because the cost layer refuses
  CORN.c and COTTON.c at three independent points: `commission.kind == "unknown"` (value null
  — *"UNKNOWN, not zero"*), `spread_price` null, and neither symbol in `SPREAD_MODEL_V1` on
  either account. Bounded outside the cost layer: at **zero cost** the 16 new trades move
  drop-best-fold retention the **wrong way** (0.7103 → 0.6850) while adding +0.0164 R/day
  gross. Since `robustness` is the binding gate at every band, a real price can only be worse.
  **Closed: extending the cost layer for those two symbols is not on this sleeve's critical
  path.**
- **`vp_euidx_pocgrav` has its first evidence anywhere: 33 trades, +0.486 R/trade gross,
  2026-05-05 … 2026-07-08.** It is NOT_EVALUABLE, which is its own verdict class and not a
  synonym for dead. The binding floor is *folds*, not trades — 33 already clear the 30-trade
  bar but sit in **1** evaluable fold against a floor of 3 — and its evaluable span *is* its
  M1 aux span. **Priced ask: GER40 and UK100 M1 back to ~2025-12-29, about 128 more calendar
  days each.**

One thing worth naming beyond these three: `sub_mid_dn_revert`'s **gross** drop-best retention
clears the 0.5 floor while its cost-true one is negative. That sleeve's robustness failure is
created by cost, not by its raw signal — a statement about the whole sleeve, and Session AY's
lane rather than this one's.

### 4. The redacted_account arms became a finding instead of a verdict

They were withdrawn from admission grade after measurement, not before, and what they measured
is worth keeping:

1. **A product wall.** `BROKER_TRUE_COSTS_V1_1.json` carries 167 FTMO instruments and **76**
   redacted_account ones, and six of the symbols these sleeves trade appear in the redacted_account list
   under **no spelling**: the four metals crosses, CORN and COTTON. **Two thirds of
   `metals_softband`'s surface does not exist on that account** — its `SURVIVOR_BOOK_V1`
   redacted_account tier describes a sleeve redacted_account cannot fully run.
2. **A naming wall, filed as CA-FN-1 and repairable.** `SpreadModel.record(symbol, account)`
   looks the symbol up in that account's own table, and the redacted_account table is keyed by
   redacted_account's broker names (`GER30`, `NDX100`, `UKOUSD`, `USOUSD`, `US30`) while every
   generated trade in the estate carries FTMO names. So `vp_euidx_pocgrav` — whose **both**
   symbols redacted_account does offer — still refuses, and it refuses *loudly*, which is
   `era_population` being right. **No prior receipt in this estate has run `run_gate` on the
   redacted_account account**; every one sets `ACCOUNT = "FTMO"`. The repair is one symbol crossing
   at the seam; it is routed rather than done here because it changes which trades a gate can
   price on a live account.

### 5. A fail-closed loader was failing open into silence

The carry-conditional bridge export was stamped by the **sanctioned** sidecar writer, which
emits schema 1 and has **no encoding field at all**: `time_column_basis` states which *clock*,
never whether the column is an MT5 epoch or an ISO string. `CsvBarSource._load` inferred the
encoding from the sidecar *schema*, so every row of all 8 files raised `fromisoformat`, was
`continue`d, and each series loaded as `[]` — **with no error**. An empty series is
indistinguishable from an absent symbol, so a merged-bar run would silently have dropped four
symbols off `metals_softband`'s surface and read as a smaller-but-fine result.

Repaired: the encoding is decoded from the token (a bare number is an epoch; an ISO stamp
always carries a `-` or a `:`), unparseable cells are counted and published on `describe()`,
and a file that has data rows but yields **zero** usable bars now raises. An absent file and
an all-dropped-by-declared-window file both stay legal empties. Seven behavioural tests,
including one against the real export's bytes.

`CARRYCOND_FETCH_20260730.md`'s *"CsvBarSource ACCEPTS all files"* was true. *"Loads any
bars"* was never checked.

### 6. BB's highest-value handoff is closed — negatively, with a proof

Handoff 1 asked for `book_days` re-derived on the W7 recost cache population, *"the highest-
value item here — it changes numbers already in front of Borhen."* It cannot be done, and the
reason is structural rather than a shortage of evidence:

- The only clause the caches can express is the **day key** (they carry
  `{sleeve, sym, date, year, R}`; the occupancy clause needs exit times and *no exit index
  survives in any cache*). The day-key clause **cannot move `book_days` at all** — it keeps
  the first row of every (sleeve, symbol, day), so no day can be emptied. Measured 382 → 382,
  173 → 173, 117 → 117.
- **Clause isolation on the archive**, where both clauses run: day-key alone costs 164 fills
  and **zero** book-days; symbol-occupancy alone costs **89** book-days.

So the entire calendar-clock effect belongs to the clause the caches cannot express. The
economic half is **bracketed, not corrected**: keep-first 5.370 %/mo, keep-last 4.537,
published 4.955 between them — the sign is set by an intra-day ordering the cache does not
record. `SURVIVORS_BOTH_ACCOUNTS_3` reproduces `BOOKS_MC_V1` exactly on `%/mo` (4.501),
`book_days` (117) and calendar days (60), which is the control that makes the rest readable.

### 7. The armed book's own cadence, restated for the sets that are actually running

Full detail in `ARMED_BOOK_AT_FILL_TRUTH.md`. The three lines that matter:

- **FTMO suppresses 41.4 % of its decisions**, redacted_account 32.1 %. 1.67 and 1.39
  live-equivalent fills/week; 5.09 and 4.23 book-days per calendar month.
- **`crypto` lost 12.7 points of fill rate the moment `mx_btcusd` was armed** (48.1 % → 60.8 %
  suppressed). Both trade BTCUSD and the book holds one position per broker symbol.
- **The frontier contract costs the book 51 fills (6.8 %)** against arming `mx_btcusd` at its
  committed 2R — `mx` keeps 134 of its own 318 decisions instead of 180. It is still the right
  contract on the economics; the cadence price had simply never been measured.

And the part that should change how the estate plans: AS's stop conditions move **no
threshold** at fill truth, but their calendars are years. S1b's 60-fill evidence floor needs
**46.7 months** on `crypto`, **95.6** on `energy_agri`, **193.5** on `sub_xvol_pullback`,
**51.2** on `mx_btcusd`. Only `sub_mid_dn_revert`'s risk floor (5.9 months) can fire inside an
evaluation window. **The live stream cannot be the evidence base on this cadence.**

### 8. The first live week cannot be read, and that is measurable

There is no post-arming fill record on this machine — the only `LIVE_TRADE_ROWS.jsonl` is 300
rows stamped `pre_w7_fleet` from June. And with one, the window would still be unreadable:
expected fills since each account's **current** `--tags` set took effect are **0.105** (FTMO,
10.6 h) and **0.174** (redacted_account, 21.1 h). **Zero fills is the modal outcome of a healthy
book — 90 % and 84 % of the time.** One fill is expected in 4.2 and 5.0 calendar days.
`CA_FIRST_WEEK_V1.json` carries the harness and the three-step export command; it refuses to
publish a verdict it cannot support.

---

## 1. What I got wrong

**I read a cost decomposition's sign backwards and it would have loosened a live sleeve's stop
floor by 1.7×.** `diagnostics.terms.*.mean_r` are positive cost magnitudes; I subtracted them
as signed R and got `mx_btcusd`'s net expectancy at **1.2907 R/trade** against a true
**0.7574**. Every floor derived from it — the risk floor, the evidence floor, the carry
break-even — would have been 1.7× too loose on money that is trading. Caught by an assertion I
added to the driver rather than by eye (`mean_gross − Σterms == mean_net_r`), and that
assertion now guards the file. The lesson generalises: I should have anchored on the object's
own published `mean_net_r` from the first line rather than recomputing a quantity it already
carries.

**I published "the guard is net positive on the cache population" before running my own
tie-break control.** Keep-first made the armed cell *better* (4.955 → 5.370 %/mo); keep-last
made it *worse* (→ 4.537). The result is a bracket, not a correction, and the sign is a
property of an ordering the cache does not record. I had the control in the code and reported
the first arm before reading it.

**My first `stage_stops` divided each sleeve's whole-archive decision count by the book's
common window**, which read `mx_btcusd` at 3.5 decisions/week and `sub_mid_dn_revert` at 5.87.
Both are wrong by the ratio of the sleeve's own availability span to the book's. BB's
`cadence()` already computes the right quantity per symbol over its own availability window;
I reimplemented instead of importing. The published figures use BB's.

**I tried to over-charge the multiplicity ratchet and the artifact refused me** — correctly.
I charged `sub_mid_dn_revert` +1 look for its extended surface on the argument that
over-charging is safe. `Family.__post_init__` requires `high_water_looks ≤ count(look_taken)`,
so the ratchet counts *members whose look has been taken*, not look *events*; billing it would
have needed a new member row, which raises the all-declared basis every other candidate in the
estate is corrected against — including the standing admission. Over-charging was not
conservative, it was a transfer of cost onto other hypotheses. Recorded in the declaration.

**My first unpriced-contribution bound tried to force the cost artifact free and failed
twice** — first on the wrong commission key, then because the lookup resolves `CORN.c` to
`CORN`, which has no record. The driver reported INCONCLUSIVE both times rather than a number,
which is the machinery working; but I was two attempts into fabricating a cost artifact to
answer a question *about* cost artifacts before I stopped and took the bound outside the layer
entirely. And my first summary string began with the word "CLOSED" unconditionally, before the
branch that decides it — a prejudged verdict in a receipt, which is exactly the defect this
estate keeps repairing in other people's files.

**One framing I got right only after being wrong first:** I ran redacted_account gate arms as
admission-grade and got NOT_EVALUABLE across the board. Publishing that as a verdict would have
said something false about three sleeves. It is a statement about the cost layer and the symbol
naming, and it is published as one.

---

## 2. Discipline

**The family was declared before any gate existed.** `CANDIDATE_FAMILY_V12.json`, committed in
`9673c2fd8` before `ca_revival_gate.py` was written; the gate verifies its `self_sha256` and
refuses to run if it moved. **Zero members added** to all four families, so the ratified
all-declared basis does not move and no other candidate's bar changes. One look:
`vp_euidx_pocgrav` converts from declared-not-taken (its `no_look_evidence` cited
`AA_ESTATE_WALK.json`'s `n_trades = 0`) to TAKEN. `CANDIDATE_BOOK_V1` 53 members / 50 → 51
looks.

**Cut rules P1–P5 and the verdict vocabulary were fixed in that file, outcome-blind**: full
declared surface as the primary population; the short-history restriction as a *sensitivity*
explicitly barred from producing a REVIVAL_CANDIDATE; the exit contract published twice
(MAXBARS 80 and the sleeve's own live time stop wherever they differ); carry as a
counterfactual that cannot produce a verdict; a random-drop control on any filter.

**The controls, run and reported:** cheapest-drop is the gate's own `robustness` term;
random-drop on the deep-history filter gives **0 of 12 draws ADMIT** with the filter's
expectancy (0.0978) *below* the random median (0.1515) — dropping those particular members
bought nothing that dropping any two would not have bought.

**`maxbars` share on every arm** (`horizon_and_maxbars_share`), and `vp_euidx_pocgrav`'s live
time stop (960 M15 = 60 H4 bars, **tighter** than the research horizon) is gated separately.

**Reproduction, verified rather than claimed:** the archive arm reproduces
`AQ_ESTATE_TRADES_V2` exactly; `metals_softband` and `sub_mid_dn_revert`'s gate figures
reproduce BB's to 16 digits; `mx_btcusd`'s incubation basis reproduces the standing admission
(232, +0.982, p 0.0011); `SURVIVORS_BOTH_ACCOUNTS_3` reproduces `BOOKS_MC_V1`'s published
`%/mo`, `book_days` and calendar days; redacted_account's four reproduce BB's fill truth exactly
(869 → 590, 32.1 %, 1.3868/wk, 4.227 book-days/mo).

**The amendment discipline on a pre-registered artifact.** `ca_armed_set_amendment.py` changes
only statements of *current fact* (`armed_tags`, `S6.expected_tags`), records the prior values
verbatim, and **hashes all seven other condition blocks before and after, refusing to write if
any moves**. `ca_mx_incubation.py` only ADDS rows for a sleeve that had none.

**H1:** two files under `src/` were edited — `research_infra/replay_policy/generation.py` and
nothing else load-bearing — and neither is R2-bound (checked before editing). Drift check
reports 2, both `UNHYDRATED-LFS`.

---

## 3. Handoff for the orchestrator

1. **`vp_euidx_pocgrav` needs one more M1 fetch and then it is decidable for the first time.**
   GER40 and UK100 M1 back to ~2025-12-29 — about 128 more calendar days each, roughly 180,000
   more bars per symbol. The 2026-07-30 fetch proved the capability; this is the same
   ceremony, longer. It is the cheapest open question in the estate: 33 trades at +0.486
   R/trade gross with no p-value because one fold cannot produce one.
2. **CA-FN-1: the walkforward gate has no redacted_account path.** Cross the symbol name at the seam
   (canonicalise, then re-resolve through `config/profiles/redacted_account.yaml`) before
   `SpreadModel.record`. Nothing about any FTMO verdict changes. It unblocks per-account
   gating for the whole estate; today redacted_account has never been gated once.
3. **Re-derive the silence thresholds for the current armed sets** (BB handoff 4, now overdue
   twice). FTMO's five fill 1.67/week against the four's 1.39, so its warn threshold is
   tighter than the 15 sessions the receipt carries. `bb_fill_truth.py` stamps which set it
   measured; re-run it per account.
4. **BB handoff 1 is closed — retire it.** No arithmetic on the W7 caches can correct the
   calendar columns, and the proof is in `CA_FILL_TRUTH_RESTATE_V1.json →
   cache_population.clause_isolation_on_the_archive`. Leaving it open invites someone to spend
   a session finding the same wall.
5. **The stop conditions' calendars are the estate's real Stage-1 risk.** S1b needs 47–194
   months per sleeve at the true fill rate. Either the estate accepts that the live stream is
   a *record* and not an *instrument*, or it needs a cheaper instrument — and that is an
   owner-facing strategic question, not a monitoring one.
6. **`ca_armed_set_amendment.py` must be re-run after every `--tags` ceremony.** It is 30
   seconds and it is the difference between S6 being the page's most trusted line and its most
   ignored one. Consider wiring it into the ceremony checklist.
7. **The three-layer blockade pattern will recur.** Bars, era model, cost artifact — a fetch
   clears one. `av_deep_h4_ingest.py` should search the bar archive as well as
   `data/mt5_research_exports/`, and its "residual ask" should report the era-model and
   commission-schedule coverage for every symbol it says is present. Two lines of code, and it
   would have said "`metals_softband` is not blocked" on 2026-07-30.
