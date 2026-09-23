# Session Y — the first-of-day path was never broken. The comparison was.

**Stage 5, wave 5. Blocks B480–B509.** Worktree `worktrees/wave5-first-of-day-20260729`,
branch `phase5/first-of-day-port`. Written 2026-07-29.

---

## 0. Verdict, stated first

> **K1-b's first-of-day failure is a code-lineage artefact, not a port defect and not path
> dependence.** The live FTMO book ran commit `redacted_host`; mainline carries the F7/B29 clock
> repair the VPS has never been given. Replaying the same port over the same bars with the
> deployed clock helpers restored recovers **175 of the 175** missing intents, adds **0** new
> misses, and takes count agreement over the 2,640 live cycles from **86.44 % to 98.86 %**.
>
> | | K1's figure (mainline arm) | lineage-matched arm |
> |---|---:|---:|
> | count agreement, 2,640 cycles | 2282 (86.44 %) | **2610 (98.86 %)** |
> | live-only intents | 182 | **7** |
> | the seven "first-of-day" sleeves | 40/215 = **18.6 %** | 215/215 = **100 %** |
>
> **All seven candidate sleeves are now scoreable**, with the ceiling stamped. Two of the
> seven were never first-of-day. The remaining residual is **7 live-only intents on two
> sleeves whose source is identical in both lineages**, so it is a genuine port-vs-live
> difference and it is enumerated in §5.
>
> **K was not careless.** Its classification of the five real latches is confirmed from
> source and is exactly *why* a 3 h shift was catastrophic for them and merely annoying
> elsewhere. K was missing an axis — replay had no notion of *which code generation* it was
> running — and that axis is now an explicit, guarded input.

**Disagreement with my prompt, per working agreement §2.** The prompt says "K's §3.5 has the
mechanism. Read it before you write anything." I read it and then refuted it. It also frames
my job as "repair the first-of-day generation path"; the path needed no repair, and what I
built is an instrument that makes the lineage a declared input. §8 lists what I withdrew of
my own.

---

## 1. What K1-b was actually comparing

`K1_GATE_RECEIPT.md` §3.5 splits the sleeves by whether their rule is path-dependent within
the session and reports 96 % live-recall for per-bar sleeves against 19 % for first-of-day
ones, concluding (§6) that *"no amount of replay work moves the second number, because the
quantity that decides it is not recorded anywhere."*

**Ten sleeve files differ between mainline and the deployed tree** [MEASURED, B482]. Verified
three ways, all byte-identical: `git show redacted_host:<path>`, the read-only export at
`vps-export-20260725/extracted/20_src/…`, and `…/13_packet_repo/src/…`.

| group | sleeves | the diff |
|---|---|---|
| **nine** | `asian_fade`, `asia_pdl_fade`, `orb_crypto_london`, `metal_session_reversion`, `liq_asia_up_low_metal`, `vss_fxcross_london_up_low`, `ny_crypto_momentum`, `kz_london_crypto_low`, `ny_index_momentum` | **exactly** the `_hour`/`_day`/`_hm` helper and nothing else |
| **one** | `fx_jpy` | its own `_to_server_local` — the **EU** EET/EEST DST calendar where mainline uses the measured **US** one |

`src/components/ultimate_book/sleeves/_server_clock.py` **does not exist at `redacted_host`**, in
either export tree, anywhere. So the deployed nine compare **raw UTC** hours against constants
that are FTMO **server** hours. Over 2026-06-18..07-24 the server offset is a constant **+3 h**
(and the EU and US calendars agree over the entire window, so `fx_jpy`'s diff is inert here —
see the control in §4). Mainline therefore evaluates every session window **3 h earlier in
UTC** than live did: a London open at 05:00 UTC against one that opened at 08:00 UTC.

The seven K calls "first-of-day" are the nine minus the two K did not compare:
`ny_index_momentum` (zero rows on either namespace; also absent from the deployed allowlist,
`agent_config.yaml:1274-1283`) and `vss_fxcross_london_up_low` (55 FTMO rows, **all** of them
`unit_skipped / future_decision_bar_time`, i.e. generation-side refusals — never candidates).

### A replay-free confirmation

Histogram live's own `decision_bar_iso` UTC hours against each sleeve's constants
[MEASURED, refuter-produced and independently checked]:

| sleeve | its constant | live fires at | mainline would fire at |
|---|---|---|---|
| `ny_crypto_momentum` | `DECISION_HOUR = 17` | **17:00 UTC, 11/11** | 14:00 UTC — **0 observed** |
| `kz_london_crypto_low` | `DECISION_HOUR = 12` | **12:00 UTC, 5/5** | 09:00 UTC — **0 observed** |
| `orb_crypto_london` | break window 8..11 | 8, 9, 10 | 5, 6 |
| `metal_session_reversion` | NY 14..21 | 14..19 | 11..16 |
| `fx_jpy` / `fx_jpy_ny` (control) | — | 5,6 / 12,13 | **identical** |

Six of seven discriminate and all six point at the deployed lineage. **`asian_fade` does not
discriminate** — its live hours 8–15 lie inside both the deployed 8–21 window and mainline's
5–18 — and it is 41 of the 215, so this table alone does not carry the finding. The replay
does.

---

## 2. The instrument

`src/research_infra/replay_policy/generation_lineage.py` makes the code generation an
explicit, guarded input to a replay instead of an accident of which checkout you are standing
in. `deployed_lineage()` installs the pre-repair helpers into the ten sleeve modules and
restores them exactly on exit.

It is a **measurement instrument, not a repair**. Nothing here changes live behaviour: it is
inert unless a caller enters the context manager, and nothing on the live path imports it —
`run_book.py`'s full transitive `src.*` closure is 113 modules and contains neither
`generation_lineage` nor `replay_policy` [MEASURED, refuter-verified].

Fail-closed properties, each a test:

* **Behavioural guards, mandatory.** Every swapped attribute must read the mainline value
  before the swap and the deployed value after. `_to_server_local`'s probe sits on a **DST
  seam** (2026-03-10, after the US switch and before the EU one) because a summer probe passes
  under both calendars and certifies nothing.
* **Re-entry refused on an explicit marker**, not on a probe. An earlier revision took a
  public `verify=False`; a refuter measured that it let a nested or cross-thread caller in
  silently, because the second entry's post-swap probe reads what the first entry installed.
  There is now no way to switch the probes off.
* **The register cannot drift.** A test asserts `set(DEPLOYED_HELPERS) ==
  clock_dependent_sleeves()`, scanning source for any clock import, and that every
  clock *consumer* (`metals.py:157`) is covered by a registered owner. The first revision
  keyed that invariant on `_server_clock` alone and therefore missed `fx_jpy` — the one entry
  that reaches an armed sleeve. A refuter caught it; the invariant is now wider on purpose.

---

## 3. The measurement [MEASURED, B483–B485]

The wave-3 scratchpad K's driver read (`/private/tmp/claude-501/…/k1`) no longer exists, so
K1-b was not reproducible. `phase5/receipts/y_cycles.py` rebuilds the corpus from the sealed
export instead. It lands on K's numbers exactly: **2,640 FTMO cycles, `n_candidates_in`
summing to 706, 383 distinct named live intents.**

**The 383 reconciliation** [B481]. All named rows total 915 triples. Subtracting the
`unit_skipped / future_decision_bar_time` rows (534 triples) gives exactly **383**. That
exclusion is mechanically correct — `book_engine.py:503-510` appends to `generation_skips`
and `:511` `continue`s **before** any intent exists — and the record proves it without the
source argument: all 534 sit in **11 cycles whose own `n_candidates_in` is 0**. A refuter
swept every subset of the 90 observed skip reasons: 275 subsets reach 383 and **every one
contains `future_decision_bar_time`**; it is the unique minimal rule.

### FTMO, both arms, same 2,640 cycles

| | mainline | `vps_redacted_host` |
|---|---:|---:|
| count agreement | **2282 / 2640 = 86.44 %** | **2610 / 2640 = 98.86 %** |
| port over-generated | 160 cycles (+201) | 9 cycles (+13) |
| port under-generated | 198 cycles (−265) | 21 cycles (−32) |
| live named (covered) | 383 (382) | 383 (382) |
| port intents | 585 | 617 |
| agreed / live-only / port-only | 200 / **182** / 385 | 375 / **7** / 242 |

The mainline column reproduces `K1_GATE_RECEIPT.md` §3.1 and §3.2 **exactly**, including the
per-sleeve table of §3.5 — from a corpus rebuilt independently of K's.

### The seven, per sleeve

| sleeve | mainline agreed / live-only | matched agreed / live-only | recall |
|---|---:|---:|---:|
| `asia_pdl_fade` | 35 / 81 | **116 / 0** | 30 % → **100 %** |
| `asian_fade` | 3 / 38 | **41 / 0** | 7 % → **100 %** |
| `metal_session_reversion` | 2 / 22 | **24 / 0** | 8 % → **100 %** |
| `orb_crypto_london` | 0 / 13 | **13 / 0** | 0 % → **100 %** |
| `ny_crypto_momentum` | 0 / 11 | **11 / 0** | 0 % → **100 %** |
| `kz_london_crypto_low` | 0 / 5 | **5 / 0** | 0 % → **100 %** |
| `liq_asia_up_low_metal` | 0 / 5 | **5 / 0** | 0 % → **100 %** |
| **total** | **40 / 175** | **215 / 0** | **18.6 % → 100 %** |

**175 recovered, 0 newly missed.**

---

## 4. Controls — and one of them is worth much less than the other

A refuter was right that the obvious control is near-tautological, so it is split here.

**(a) Source identical, therefore untouched by the shim** — `idxrev` 49/5/41,
`vol_compression` 3/0/2, the whole `mx_*` family. Byte-identical in both arms. This proves
determinism and that no state leaks between arms. It is not specificity: the shim cannot move
them.

**(b) Shimmed, but inert in this window** — `fx_jpy` 54/0/102 and `fx_jpy_ny` 45/0/12. These
**are** swapped, and their diff is the EU-vs-US DST calendar, which coincides on every day of
the window. Predicted identical output; re-ran the entire 2,640-cycle deployed arm after
adding `fx_jpy` to the register and the port output is **byte-identical across all 2,640
cycles, 0 differing**. A falsifiable prediction that held.

**(c) The over-fit control, which is the strongest** [B488, refuter-produced]. Deliberately
wrong shims: the same instrument with the effective clock set to `UTC + K`, over the same 800
cycles.

| effective clock | count agree | seven agreed | live-only | live-recall |
|---|---:|---:|---:|---:|
| mainline (K = +3) | 84.00 % | 22 | 79 | 21.8 % |
| K = +2 (1 h wrong) | 86.62 % | 38 | 63 | 37.6 % |
| K = +1 (2 h wrong) | 89.25 % | 53 | 48 | 52.5 % |
| **K = 0 (correct)** | **98.62 %** | **101** | **0** | **100.0 %** |
| K = −1 (4 h wrong) | 86.88 % | 41 | 60 | 40.6 % |

A fitted parameter has a broad optimum. This is a **delta function** — 47.5 recall points
between the correct shim and the best wrong one — and the four narrow-window or
exact-`(hour, minute)` sleeves score **exactly zero under every wrong shim** and 100 % only at
K = 0. `asia_pdl_fade` alone is partly rescuable by a wrong clock (76 % at K = +1) because its
ASIA window is hours wide: **a single-sleeve headline would have been fittable; the
seven-sleeve one is not.**

**(d) The hold-out: redacted_account** [MEASURED, B489]. A completely independent namespace, 2,569
cycles, never used to derive anything. K excluded it because its bar pull is 14 of 43 symbols.

| | mainline | `vps_redacted_host` |
|---|---:|---:|
| count agreement | 2096 / 2569 = 81.59 % | 2188 / 2569 = 85.17 % |
| live-only (covered) | **57** | **1** |
| `orb_crypto_london` | 0 / 23 = 0 % | **23 / 0 = 100 %** |
| `kz_london_crypto_low` | 0 / 13 = 0 % | **13 / 0 = 100 %** |
| `ny_crypto_momentum` | 0 / 11 = 0 % | **11 / 0 = 100 %** |
| `asia_pdl_fade` | 10 / 9 = 53 % | **19 / 0 = 100 %** |

**56 of 57 recovered, 0 newly missed.** The count-level residual is dominated by the 14-of-43
bar coverage (the port under-generates on 380 cycles), which is exactly why K excluded this
namespace and why only the identity-level result is quoted from it.

**(e) The counter-hypothesis, killed** [refuter-produced]. If the live feed were
broker-time-labelled-as-UTC (the second audit's known data defect), the *deployed* comparison
would have been the correct one and the direction of the repair inverted. It is not:
`RealMT5.get_candles` is identical in both lineages and both convert via `_broker_epoch_to_utc`
(mainline `:248-265`, deployed `:242-259`; the whole `mt5_real.py` diff is a pure insertion,
the activation token). Live `decision_bar_iso` is genuinely UTC.

**(f) The engine layer is inert on the generation path** [MEASURED, B496]. `book_engine.py`
also differs between the lineages (24 hunks), and the only generation-path difference is the
bar-time repair. Over a 220-cycle sample spanning the whole window,
`_resolve_repair_offset_seconds` was called **12,325 times and returned `None` every time** —
the archive's bars are clean UTC and never look future, so both lineages take the same early
return. The arm is therefore "the deployed **clock** inside an otherwise-mainline engine",
which is stated as a scope limit in §6 rather than glossed.

---

## 5. The residual, enumerated

**7 live-only intents**, on two sleeves whose source is **identical** in both lineages — so
these are genuine port-vs-live differences, not clock artefacts:

| sleeve | live-only | decision bars |
|---|---:|---|
| `idxrev` | 5 | GER40 06-26T16:00, SPX500 06-25T14:00, UK100 06-19T15:00 + 06-25T14:00, US30_cash 06-25T14:00 |
| `mx_avausd_d1_donchian_20_breakout` | 2 | AVAUSD 06-18T22:00 and 06-18T23:00 |

**`idxrev`: the live terminal's H4 index series lags the archive by one bar at the 21:05
cycle** [MEASURED; the *cause* is UNVERIFIED]. The archive's H4 grid is UTC
{01, 05, 09, 13, **17**, 21} every day. **Live's H4 `decision_bar_iso` never contains 17:00
across the entire 38-day record** — at 21:xx cycles it stamps 13:00 (742 of 1,021 `idxrev`
rows). The port, whose archive has the 17:00 bar, evaluates it. That is D15 in its most
concrete form to date: not "the record does not preserve the bars", but a specific, repeating
one-bar lag on index CFDs at the broker's own day rollover (21:00 UTC = server 00:00). Why the
terminal lags there is not decidable from the export.

**`mx_avausd`: a decision-bar *stamp* difference, not a missing trade.** Live stamps
`2026-06-18T22:00` and `T23:00` for a D1 bar; the port stamps `21:00`. D1 bars open at 21:00
UTC (server 00:00), so live's stamp carries an un-repaired broker offset — the same
leaked-zero-offset defect wave 3 fixed in `_resolve_repair_offset_seconds`.

**30 count-level disagreeing cycles, and the switch is not monotone at count level**
[B494 — this is a correction a refuter forced]. 358 → 30 is **332 cycles fixed and 4 newly
broken** (26 still broken). The four newly broken are 06-22T00:15, 07-06T01:14, 07-16T06:45,
07-23T08:45; in each the port emits an `asia_pdl_fade`/`orb_crypto_london` intent live's
counter says did not exist. Identity level **is** monotone (0 newly missed).

---

## 6. The fidelity ceiling each sleeve can now be judged at

`src/research_infra/walkforward/fidelity.py` is Session W's plug-in point and this is what
plugs into it. **I did not move the floor, the verdict logic, or `scoreable()`** — those are
W's design and Borhen's decision.

| sleeve | class | basis | live-recall | identity precision | scoreable at 0.50 |
|---|---|---|---:|---:|---|
| `asia_pdl_fade` | first_of_day | lineage-matched | **100 %** (116/0) | 69 % | **yes** |
| `asian_fade` | first_of_day | lineage-matched | **100 %** (41/0) | 84 % | **yes** |
| `metal_session_reversion` | first_of_day | lineage-matched | **100 %** (24/0) | 86 % | **yes** |
| `orb_crypto_london` | first_of_day | lineage-matched | **100 %** (13/0) | 93 % | **yes** |
| `liq_asia_up_low_metal` | first_of_day | lineage-matched | **100 %** (5/0) | 100 % | **yes** |
| `ny_crypto_momentum` | **fixed_decision_bar** | lineage-matched | **100 %** (11/0) | 48 % | **yes** |
| `kz_london_crypto_low` | **fixed_decision_bar** | lineage-matched | **100 %** (5/0) | 42 % | **yes** |
| `vss_fxcross_london_up_low` | per_bar | transferred | 96 % | — | yes, **but see below** |
| `ny_index_momentum` | unknown | **unmeasured** | — | — | **no** |

**Seven of the nine become scoreable. Two do not, for opposite reasons.**

* **`ny_index_momentum`** is genuinely unmeasured: zero rows on either namespace, and it is
  not in the deployed allowlist. It is deliberately **absent** from the register so it fails
  closed rather than inheriting a 100 % class rate it did nothing to earn. What would fix it:
  nothing available — it has to be deployed and observed, or scored with an explicit
  UNMEASURED stamp on the verdict.
* **`vss_fxcross_london_up_low`** carries a 96 % *transferred* stamp resting on **nothing
  observed for it in 38 days**: all 55 of its FTMO live rows are generation-side refusals, so
  it is 0 agreed / 0 live-only on both arms. Its stamp now says so. This is the one row on the
  table I would not trust, and it is a live-allowlist sleeve.

### Two classification corrections [B486]

`ny_crypto_momentum` (`:88-89`) and `kz_london_crypto_low` (`:88-90`) fire only when the
decision bar's `(hour, minute)` equals a fixed constant — no scan of earlier bars, no latch.
They are **`FIXED_DECISION_BAR`**, not first-of-day, so K's 19 % class rate was computed over
a mixed population. Verified from source; the five with a genuine latch are `asian_fade`
(`:101`, `:115`), `asia_pdl_fade` (`:99`, `:107`), `orb_crypto_london` (`:107`, `:114`),
`metal_session_reversion` (`:98`, `:106`, `:108`) and `liq_asia_up_low_metal`
(`_already_fired_today` `:139`, called `:191`, `:204`).

### What 100 % does not entitle a gate to — the scope limit, stated because it is the largest

Stamped on every raised row, and this was a refuter's top-ranked demand:

> **measured on 2026-06-18..07-24 only — 38 summer days at a constant +3 h broker offset,
> under the deployed clock, with the latch resetting at 00:00 UTC. NOT measured at the winter
> +2 h offset, NOT on a DST transition day, and NOT under mainline's 21:00 UTC latch reset.**

The third clause is the sharpest: under **mainline** `_day` is `server_day`, so a
first-of-day latch resets at **21:00 UTC**, putting the Sunday open and Friday close *inside*
a day rather than on its boundary. The deployed arm, where `_day` is UTC, never exercises
that partition. A walk-forward gate scores multi-year history across every DST transition;
nothing here measures the port at +2 h or on a transition day.

### Precision, because recall alone is not honest [B492]

`live_recall` has no precision term. Across the seven: **215 agreed against 83 port-only =
72.1 %**, and by thirds of the window it falls **99.1 % → 58.4 % → 53.1 %** while recall stays
pinned at 100 %.

**That fall is a property of the record, not of the port** [MEASURED]:

| segment | live counter | live *named* | naming rate | port total |
|---|---:|---:|---:|---:|
| first third | 288 | 279 | **96.9 %** | 279 |
| second third | 202 | 89 | **44.1 %** | 197 |
| last third | 216 | 88 | **40.7 %** | 211 |

Live's complete counter stays flat and the port keeps tracking it; live simply stops *naming*
its candidates (D15/C6). The give-away is that **`fx_jpy` — best recall in K's table, 100 %,
identical source in both lineages — has the worst identity precision here, 34.6 %.** Nothing
about `fx_jpy` degraded.

The honest precision statement is at **count level**, where live's counter has no attribution
gap: the port produced **687** candidate-instances against live's **706**.

**Recommendation to W and to Borhen, not a change I made:** `scoreable()` gates on recall
alone, so a generator emitting 40 % junk would pass it. A precision floor belongs in
`GateSpec` beside `fidelity_floor`. The admission standard is not mine to move.

---

## 7. Findings for the live book — published before landing, per the prompt's trap

**Nothing I changed touches the armed FTMO sleeves.** `crypto`, `energy_agri`, `metals_core`
and `sub_xvol_pullback` are none of them in `DEPLOYED_HELPERS`; `generation_lineage` is
imported by nothing on the live path; and their fidelity records are `TRANSFERRED_CLASS` off
`_CLASS_TOTALS[PER_BAR] = (160, 7)`, **which I did not change** — so their stamps are
byte-identical to before this session.

Four things I found that do bear on the live book:

**7.1 The F7/B29 clock repair has never been carried to the VPS** [MEASURED, B497]. Eight of
the nine repaired sleeves are in the deployed candidate allowlist
(`agent_config.yaml:1274-1283`) and are today running session logic 3 h from where it was
mined. **None of the eight is armed** — `run_book.py --tags` bounds FTMO to the four
survivors — so there is no live money exposure through them. It is a carry gap, and Session S
already owns the packet-carry runbook.

**7.2 `metals_core` is ARMED and its A8 `session_hour` runs on the stale EU calendar**
[MEASURED, B498]. `metals.py:157` imports `_to_server_local` from `fx_jpy` **at call time**;
`session_hour` is one of four A8 confluence legs (`0 <= session_hour <= 6`, K = 3 of 4,
`metals_confluence_gate.py:51`, `:29`); the gate is armed at `agent_config.yaml:1315` and
`bridge.metals_confluence_gate` is `true` on **41,271 / 41,271** FTMO packet rows; and
`A8_CONFLUENCE_SLEEVES = {metals_core, metals_softband}` (`admission.py:981`), with the drop
at `admission.py:1044-1045`.

Measured, from the archive's own H4 grid (UTC {01, 05, 09, 13, 17, 21}) on a divergence day:

| | server hours | ASIAN-eligible |
|---|---|---|
| mainline (US, NY+7, +3) | 04, 08, 12, 16, 20, 00 | **2 of 6** |
| deployed VPS (EU EET, +2) | 03, 07, 11, 15, 19, 23 | **1 of 6** |

Exactly **one H4 bar per day flips** — the 21:00 UTC bar — and the VPS is the **restrictive**
side: it can only *lose* a `metals_core` entry mainline would keep, and only when the other
three legs score exactly 2. Divergence windows: **2026-10-25 → 2026-11-01** (next),
2027-03-14 → 03-28, 2027-10-31 → 11-07; the spring 2026 window 03-08 → 03-28 sits almost
entirely inside the **sealed March replay window**. Exposure in the observed window is
**zero** — `metals_core` produced 5 FTMO packet rows in 38 days and all five are
`future_decision_bar_time` skips — so this is prospective, not realised. *(Two refuters gave
different flip counts here; both were wrong in different directions and the table above is
derived from the archive grid directly.)*

**7.3 The deployed engine refused 534 decision-bar slots in 8 days** [MEASURED, B500].
`unit_skipped / future_decision_bar_time`, concentrated on 06-29, 06-30, 07-06, 07-07, 07-08,
07-10, 07-15, 07-24, and including armed sleeves (`metals_core` 5, `crypto` 2, `energy_agri`
2). This is the leaked-zero-broker-offset defect mainline repaired in wave 3
(`book_engine._resolve_repair_offset_seconds`, persisted latch) and the VPS has not received.
It is the same carry as 7.1.

**7.4 The live book records nothing about which code lineage it is running** [B502]. This
entire finding depended on a human knowing the VPS sits at `redacted_host`. A commit/lineage stamp
in the runtime learning packet is now the **cheapest missing capture in the programme** — a
single string per cycle, on a file that is not decision-contract-bound. It would have turned
this session into a five-minute check.

---

## 8. What I got wrong, and withdrew

* **"The 0 % recall of the two fixed-bar sleeves discriminates the clock story from the latch
  story."** Withdrawn. A refuter pointed out that K's own table contains two *genuine* latch
  sleeves that also measured exactly 0 % (`orb_crypto_london` 0/13, `liq_asia_up_low_metal`
  0/5), so the latch story demonstrably produces 0 % in this dataset. At the observed low-end
  sleeve rates the likelihood ratio is ~3:1 — under two bits. The finding never needed it: the
  hour distributions and the replay are dispositive.
* **"Every one of the nine diffs is exactly the `_hour`/`_day`/`_hm` helper."** Wrong as a
  description of the mainline↔VPS delta: there are **ten** differing files and the tenth,
  `fx_jpy`, differs in `_to_server_local`. Worse, my first register omitted it — and it is the
  one entry that reaches an armed sleeve. Fixed, re-run, byte-identical in-window.
* **"Don't fix `vss_fxcross_london_up_low`'s mixed clock because it is a live-registry
  sleeve."** Right call, wrong reason, and the reason mattered. The mixed clock is **not a
  defect**: `_daystr`'s only consumer is `_d1_up_regime`, which compares it to `decision_day`
  — and `decision_day` is `bar_provider.decision_day_of`, the signal bar's **UTC** date
  (`bar_provider.py:86-88`, sole caller `book_engine.py:531`). The two are deliberately on the
  same calendar; converting `_daystr` to `server_day` would *create* the mismatch. Rationale
  replaced in the register.
* **"Two of the six H4 bars per day flip the A8 ASIAN leg."** Wrong arithmetic — 7 is not in
  `0..6`. It is one bar, and I re-derived the grid from the archive rather than trusting
  either refuter's figure.
* **`server_clock_importers()` as the register's drift invariant.** Too narrow; it is what let
  `fx_jpy` escape. Widened to `clock_dependent_sleeves()` plus a consumer check.
* **`pre_b29_hour` applied to `vss_fxcross_london_up_low`.** The deployed version guards its
  string parse with `try/except ValueError`; mine would have raised. Inert on the replay path
  (bar times are datetimes) but "transcribed verbatim" was false as worded. Separate faithful
  variant added.

---

## 9. What K's §6 still buys, and one thing it does not

**Narrowed, not retired.** K's §6 asks the live book to record (1) the bars it read and (2)
the latch it set. Both still earn their keep:

* Only (1) explains the residual — 7 live-only, 30 disagreeing cycles, and the 17:00 H4 index
  bar live never stamps.
* Only (1)+(2) can settle **precision**. Splitting the 83 port-only intents into false
  positives versus the 46 % of candidates live never names needs exactly the per-fetch bar
  tuple and the latch stamp. That is the question the fidelity number now turns on.
* (2) is still the only way to *verify* a latch directly rather than re-derive a session and
  hope. My result shows the latch is **reproducible when the clock matches**, which is
  strictly weaker.

**What is retired** is one sentence: *"No amount of replay work moves the second number."*
Replay work moved it from 19 % to 100 %.

**And one precondition is added:** §7.4 — stamp the code lineage.

---

## 10. Reproduce

```bash
python3 docs/audits/fable5-vision-audit-20260725/phase5/receipts/y_cycles.py /tmp/cycles.pkl
python3 docs/audits/fable5-vision-audit-20260725/phase5/receipts/y_k1b_replay.py \
        --lineage mainline       --cycles /tmp/cycles.pkl --out /tmp/raw_mainline.json
python3 docs/audits/fable5-vision-audit-20260725/phase5/receipts/y_k1b_replay.py \
        --lineage vps_redacted_host  --cycles /tmp/cycles.pkl --out /tmp/raw_deployed.json
python3 docs/audits/fable5-vision-audit-20260725/phase5/receipts/y_k1b_analyse.py \
        /tmp/raw_mainline.json /tmp/raw_deployed.json --cycles /tmp/cycles.pkl \
        -o /tmp/Y_K1B_LINEAGE.json
# hold-out
python3 .../y_k1b_replay.py --namespace redacted_account_live_bee34003 --lineage mainline      --out /tmp/fn_a.json
python3 .../y_k1b_replay.py --namespace redacted_account_live_bee34003 --lineage vps_redacted_host --out /tmp/fn_b.json

python3 -m pytest tests/test_replay_policy_generation_lineage.py \
                  tests/research_infra/test_fidelity_register_matches_receipt.py \
                  tests/research_infra/test_walkforward_gate.py -q
```

Each full arm is ~6 minutes (FTMO) / ~2–22 minutes (redacted_account) on this machine. Requires the
bar archive at `/Users/borr/GTOSActive/vps-bars-20260727/` and the packet export at
`/Users/borr/GTOSActive/vps-export-20260725/`, both outside the repo.

Machine-readable: `phase5/receipts/Y_K1B_LINEAGE.json`,
`phase5/receipts/Y_K1B_LINEAGE_redacted_account.json`.

---

## 11. What is not mine, and what I did not do

* **I did not score the seven.** Session W owns the admission standard, Session X the
  book-level question. §6 is what tells the gate they are now judgeable, not a verdict on any
  of them.
* **I did not move the gate.** `fidelity_floor`, `fidelity_refusal_is_hard` and `scoreable()`
  are untouched. The precision floor is a recommendation in §6.
* **I did not touch the VPS**, arm, disarm, mint or revoke anything, run any broker-capable
  script, or edit `config/agent_config.yaml`.
* **I did not fix the VPS carry gaps in §7.1/§7.3.** They are Session S's runbook and an
  owner-executed ceremony.
* **[UNVERIFIED] today's VPS host state.** Every deployed-lineage claim rests on the
  2026-07-25 read-only export plus commit `redacted_host`.
* **[UNVERIFIED] the port at a winter offset or across a DST transition.** §6's scope stamp.
* **[UNVERIFIED] whether the 242 port-only intents are false positives.** §6 and §9; it needs
  K's capture.
