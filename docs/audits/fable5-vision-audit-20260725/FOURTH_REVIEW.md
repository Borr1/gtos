# Fourth review — the build

**Fable 5. Commissioned by Borhen 2026-07-29, after FTMO went live. Brief:
`FOURTH_REVIEW_BRIEF.md`. This is not an audit. It is the plan that takes 37 sleeves and a
half-built architecture to a working, learning, shipping system — sequenced so the next waves can be
cut from it directly, the way wave 3 was cut from `THIRD_REVIEW.md` §4.**

The burden of proof in this document is inverted, per the brief and per the owner's explicit,
repeated instruction: **the default assumption is that a sleeve can be made to work, and the job of
every measurement is to find out how.** A sleeve leaves the active queue only after its enumerated
repair paths fail, and then it is parked with its list, not killed. Verification here is pointed at
repairs — does the fix do what it claims, is the arithmetic right, is the live account untouched —
never at manufacturing grounds for rejection.

One boundary is terrain, not caution, and every session cut from this plan inherits it verbatim:
**a live funded FTMO account is trading real money on the project's VPS right now.** Nothing in this
plan touches the VPS, edits `config/agent_config.yaml` (the activation token binds its digest
`ffe16657feaf`; one byte stops the armed book placing), runs a broker-capable script, or changes
what is armed. Every VPS-side change in this plan ships as an owner-executed carry package in the
Session AC lane.

---

## 0. The verdict in one page

**The estate is not 4 working sleeves and 33 failures. It is 4 shipped and 33 artifacts that were
never measured by an instrument capable of telling Borhen what to fix — plus 4 more the brief did
not count (§1.6).** Between waves 3 and 5
this programme built, piece by piece and without noticing, almost the entire machine needed to
repair the estate rather than grade it:

- a **34-year, 43-symbol, zero-gap bars archive** on this machine (`vps-bars-20260727`, 4,358,938
  rows, sha-verified) — landed 2026-07-27, and almost nothing has been pointed at it;
- a **generation port** that turns bars into intents through the production sleeve code
  (Session K, 96 % live-recall on per-bar sleeves; Session Y is repairing the first-of-day half);
- a **broker-truth cost layer** that reproduces realized charges to 0.00298 R (Session J);
- an **exit simulator** inside the walk-forward panel that replays every trade's path — which means
  **holding time, the number that decided OD-3, is now computable for every sleeve in the estate**
  without a single new fill;
- a **walk-forward gate** with seven real gates, a sealed spec, and refuter-hardened statistics
  (Session W) — currently wired to emit verdicts, one flag short of emitting prescriptions;
- a **validation-integrity library** (15 modules, 94/94 green) containing the diversifier
  certification, the deflated Sharpe, PBO, permutation nulls, and a **trial-budget ledger that has
  never been run**;
- **firm-rules MCs** at each firm's measured rules, including the governed live sizing path
  (Sessions Q and V);
- a **closed learning loop** reading live realized evidence at broker truth (Session R) — wired,
  today, so that it can only ever subtract.

The plan below does four things, in order of leverage:

1. **Repoints the gate from verdicts to prescriptions** (§2, §4.1). Every REJECT already contains
   the information about which of {entry, exit, session, symbol surface, sizing, pairing, regime
   gate, cost geometry} failed and by how much. One session turns that into a machine-readable
   repair queue, and the "killing machine" becomes the diagnostic head of a fixing machine.
2. **Walks the whole estate through generation + exit simulation at broker truth** (§3, §6) —
   all 41 authored artifacts (the brief's census is corrected in §1.6: one double-count out,
   five uncounted artifacts in), over 34 years where the data reaches, with holds, swap nights,
   MFE/MAE and per-gate margins captured per trade. This
   closes holding time for the three carry-conditional sleeves, replaces `metals_ob_micro`'s n=7
   with a real sample, gives every candidate its first broker-true history, and produces the
   cost-true per-sleeve splits the learning loop needs. Zero sealed-replay hours; zero VPS contact;
   March 2026 stays outcome-unread behind W's sealed blackout.
3. **Builds the improvement machinery the charter names and nobody started** (§4.5–§4.9, §5):
   parameter-surface sweeps, regime conditioning (the armed book's own §7 problem has a buildable
   answer), swap-aware exits, symbol-surface expansion across the 43 instruments, a spread model
   from the 263.9 M ticks, the feature/label stores, and a first meta-label model — each validated
   through the same gate, each logged in the trial ledger so aggression and honesty coexist.
4. **Ships along a capital ladder that already exists** (§7): FTMO #1 carries the armed four and
   the repairs that clear the arming standard; **redacted_account's fourth survivor is already sitting
   measured and unarmed** (`vp_euidx_pocgrav` — UNCONDITIONAL there); the three challenge accounts
   are the shipping surface for the candidate book, which converts "waiting for forward data" into
   "forward data as a by-product of shipping."

**Cost to the whole of §6:** roughly 14–18 agent-sessions across three waves at 3–4 concurrent,
~0 sealed-replay machine-hours, two owner data-fetch ceremonies, one owner VPS carry (already in
flight as Session AC). The constraint budget this plan spends is agent-hours, which the owner has
said are not scarce.

---

## 1. Corrections first — where the brief and the estate's own records are wrong

The brief asks for this plainly, and it matters because a repair plan built on wrong diagnoses
repairs the wrong things. Each item below was verified against the artifact this week, by me or by
Session W's result, before it changed anything downstream.

**1.1 `idxrev` is not "negative before cost." It is zero-edge gross on a huge sample.**
`SURVIVOR_BOOK_V1.json` records `gross_r +0.00585` on **n=6,473** [verified by direct read]. The
artifact's own `killed_reason` string is wrong for this sleeve (right for `metals_ob_micro`), and
Session W already flagged it. The distinction decides the repair: a genuinely negative sleeve wants
an inverse test; a zero-mean sleeve with 6,473 trades is an **average over heterogeneous
conditions** — the classic profile of a sleeve that needs conditioning, not burial. It was also the
only live-profitable sleeve in the live window (B63). §3.2 gives it a real repair path.

**1.2 `metals_ob_micro` was never measured. Seven trades is not a verdict.** Gross −0.5 on n=**7**
[direct read]. Under the standards this programme applies everywhere else, that is `NOT_EVALUABLE`,
not `DEAD`. The repair is trivially cheap: regenerate at scale over the archive and get a real n.

**1.3 `fx_jpy` and `fx_jpy_ny` are not "measured dead live."** At their **measured** live carry —
zero swap on 41 of 41 live JPY positions — both are net-positive on the validation stream
(+0.0412 and +0.0462, `SURVIVOR_BOOK_V1.json` `net_r.n0`), and `fx_jpy`'s tier is
`MEASURED_LIVE_CARRY`, a *surviving* tier backed by a structural bound (its 21:00 exit ceiling
cannot cross a rollover; N §8.1). The "measured dead" story rests on the 41-trade live cluster's
−0.453 R pooled gross, whose signal-level p of 0.0059 becomes **0.0706 after Bonferroni and does
not survive** (W §1, `read_g1b.md:115`). The honest state: **thin real edge, heavy commission
share, one bad small live sample.** That is a cost-geometry repair case (§3.2), not a corpse.

**1.4 The carry blocker is already dead, and the brief still prices it as a fetch.** The
orchestrator's concession ("the carry-conditional sleeves were killed on a dimension nobody
measured… `data/mt5_research_exports/` doesn't exist on this machine") was true in wave 3. The
bars export that closes it **landed on this machine on 2026-07-27** — D1/H4 to 1992, M15 from
2024, both brokers, zero gaps — and Session W's panel already simulates exits over it. Holding
time for `metals_softband`, `vp_euidx_pocgrav` and `sub_mid_dn_revert` is now **one generation run
away**, not one fetch away. Nothing needs `bridge_ftmo_deep_h4_*`.

**1.5 The learning-loop critique is right, with one precision that changes the fix.** Live
evidence *can* support a size-up at n ≥ 30 (`LIVE_MIN_N_SUPPORT`), but `_apply_live` composes
`min(backtest, live_cap)`, so live evidence can never lift a sleeve above its backtest half — and
**the backtest half is the legacy-cost CP4/CP5 replay**, the exact cost model F38/F39 discredited.
Session R saw this and could only bolt on a veto (`cost_true_survivor=False` blocks size-ups). So
the repair is not "delete the min()"; it is **replace the backtest half's evidence with the
cost-true splits the estate walk produces, then make the composition bidirectional with
asymmetric speed** (§4.2). R's own §7 item 4 names the missing input.

**1.6 The brief's census is wrong in both directions, and one of its 37 is a double-count.**
Verified against the authoring surfaces this week [file:line per item]:

- **`xlayer_veto_gate` is not an independent sleeve.** Its 56 cached rows are a filtered subset of
  `sub_xvol_pullback`'s 90 (corr +0.792; row 0 of both caches is the same EU50_cash 2025-10-15
  trade), and it already **ships** as the `leader_impulse_veto` size-up overlay at
  `admission.py:311-314` (1.5× size-up on its base sleeve, permutation p 0.0003). Counting it as a
  37th artifact double-counts the armed book's own fourth sleeve. It re-enters this plan as the
  **template for the overlay lane** (§4.8) — the one overlay in the estate that is already built,
  certified, and live.
- **Three quarantined candidates are missing.** `candidate_registry.py` holds 12 authored
  candidates, not 9: `vol_squeeze`, `ny_index_momentum`, `structural_retest` sit at confidence 0.0
  with explicit redesign notes in their own `CANDIDATE_DECISION` entries ("zero book confidence
  **until** daily-unit redesign / market-state or surface redesign / cell-level rebuild") and the
  registry's own comment: *"Zero confidence is a quarantine state, not deletion."* The estate
  already contains three parked-with-list sleeves; the brief under-counts the very pattern it
  mandates. All three get rows in §3.4.
- **A registered sleeve exists that can be sized but never generated.** `session_leadlag_genuine`
  — `CLEAN4_REGISTRY`, confidence 0.15, `forward_only` (`admission.py:266-277`) — has **no
  generator** in `sleeves/registry.py` and no exit profile. A sizing entry with no generation path
  is a wiring defect either way it resolves (§3.5).
- **The mx count runs 16 authored → 14 built → 12 live**, and the two drops are different in
  kind: `mx_aus200_cash_d1_atr_mean_reversion` and `mx_ger40_cash_d1_atr_mean_reversion` are
  metadata-only (no generator; the GER40 one explicitly preserved as *"context/veto
  intelligence"* — overlay-lane input, §4.8), while `mx_aus200_cash_d1_volume_surge_reversal` and
  `mx_spn35_cash_d1_volume_surge_reversal` are **fully runtime-capable** — generators, exit
  profiles, collision-winner status, seed weight — and are excluded from live *solely* by the
  hard-coded 12-name tuple at `candidate_registry.py:425-438`. "Never judged" for those two means
  a policy list omits them, nothing more.

The working census this plan covers: **41 authored artifacts** — 36 independent tradeable sleeve
specs (the brief's 37 minus the double-count), 3 quarantined candidates, 1 generator-less
registered sleeve, 1 shipped overlay — plus 2 metadata-only mx specs preserved as intelligence.
Every one has a row in §3.

**1.7 A live-state contradiction inside CLAUDE.md itself, flagged for the orchestrator.** The
armed-state bullet says `ultimate_book_include_clean3` is now `true` "(:1200)"; the wave-4 bullet
says `false` at `:1270`. In this worktree's config, `:1200` is a symbol-list line and the flag is
**`false` at `:1270`** — mainline never flipped it. That is expected (the arming ceremony edits
the VPS host's config, whose digest the token binds), but it means **mainline holds no record of
the flag the armed set depends on**, and `sub_xvol_pullback` generates only if the host's copy is
`true`. One read-only host check — the same `--tags`-and-flags check T's canary page already
specifies — confirms the armed book is generating four sleeves, not three. Queued in §8; no
session touches the config either way.

---

## 2. The two reframes that unlock the estate, and the spine that keeps it honest

These are the intellectual core of the plan. Everything in §3–§6 is an application.

### 2.1 Reframe one: spec economics and live fidelity are different questions — stop letting one block the other

W's gate refuses to score a sleeve below a generation-fidelity floor. That made sense as
self-protection ("don't publish a number that measures the port's bug"), but it fused two
independent questions into one refusal:

- **Q1 — is the rule profitable?** Generate the sleeve's own spec over the archive with the port's
  semantics, price at broker truth, walk it forward. This is a *self-consistent* measurement of
  the rule as written. It is available **today for the whole estate**, including the seven
  first-of-day candidates the gate currently refuses.
- **Q2 — does the live engine implement the rule?** That is K1's question — a reconciliation
  between two implementations of the same spec. Its answer stamps a **transfer risk** on Q1's
  number; it does not invalidate it.

The plan therefore splits the fidelity floor into a **stamp**: every gate result carries
`fidelity_class` (MEASURED / TRANSFERRED_CLASS / DIVERGED with the live-recall number), and
`NOT_EVALUABLE`-for-fidelity ceases to exist. A sleeve whose port and live implementations
disagree gets measured on the port's semantics *and* opens a reconciliation work item — because a
live engine that does not implement its own spec is a **bug in the engine or the spec, and either
way the fix is ours to make**, not a reason the rule's economics are unknowable. Session Y's latch
repair then *raises the stamp*, never unblocks the measurement.

Two honest limits, stated so nobody discovers them later: a diverged implementation means live
performance can differ from the measured rule until reconciliation lands (that is what the stamp
prices); and for first-of-day sleeves whose live latch depends on intra-bar state no bar archive
holds, perfect reconciliation may need the live book to **record its latch** — a one-line packet
addition already queued in the AC lane (§4.10). If the record proves bars-alone can never
reproduce a latch, the spec-as-ported *becomes* the reference implementation and live is corrected
to match it. Either direction, someone fixes code; nobody waits.

### 2.2 Reframe two: every gate failure is a prescription, not a verdict

The seven gates each fail for a mechanistically different reason, and the reason names the repair.
This mapping is the "fixing machine" the orchestrator conceded was never built — and it is about
one session of work, because the gate already computes every number involved and then flattens
them into verdict-reason strings (`gate.py:93-113`, `SleeveVerdict.reasons`); the diagnostic mode
just stops flattening:

| gate that failed | what it means mechanically | the prescription it emits |
|---|---|---|
| **coverage** | broker truth cannot price the symbol | data path: tick capture order, or the §4.6 spread model with banded verdicts — never "unjudgeable" |
| **expectancy/day** with gross > 0 | the edge exists and costs eat it | **cost-geometry repair**: stop-width sweep (commission_R ∝ 1/stop), entry-timing repair (§5.5), session filter to the cheap hours |
| **expectancy/trade** with day-mean OK | a few bad trades per day drag the mean | intraday count cap, per-trade quality filter (meta-label, §4.8) |
| **lifetime** (scored window +, full history −) | the rule changed sign somewhere in history | **regime gate**: find the break, name the conditioning variable, test it explicitly (§5.2) |
| **stability** (some folds negative) | edge is regime-dependent | same conditioning path, fold-level: what distinguishes the positive folds |
| **robustness** (edge lives in one fold) | either one regime carries it, or it is noise | regime-gate to that regime and re-walk; if the gate variable cannot be named, park with list |
| **significance** (q > α, raw p small) | real-looking edge, family too big for one sleeve to clear | **breadth repair**: pool the mechanism across symbols as a *family* (IR ≈ IC·√breadth — the repo's own `portfolio_contribution.py` says this in as many words), or admit through the diversifier door (§4.4) |

Concretely: `gate.py` grows a `diagnose()` output — per-gate margin, the failing folds/symbols/
sessions, and a `prescription` enum from the table — and every estate walk writes
`REPAIR_QUEUE_V1.json` beside its verdicts. §3's per-sleeve repair paths are this table applied to
the evidence already in hand; the queue artifact keeps it applied automatically to everything the
estate walk measures next.

### 2.3 The spine: the trial-budget ledger is what lets this be aggressive and stay true

A repair campaign is a large multiple-testing exercise by construction — hundreds of variants,
sweeps, and re-walks. The programme's charter says truth is the measurement substrate; the owner
says no brakes. **Both are satisfied by one cheap mechanism:** every variant any repair session
evaluates is logged to the trial-budget ledger
(`validation_integrity/trial_budget_ledger.py` — built, tested, never run), and final admission
statistics deflate against the *measured* trial count instead of today's assumed floor of 128.

This is not a brake. No repair is slowed, no variant is forbidden, nothing waits. It is the
difference between "we tried 400 things and the ledger says the survivor still clears deflation"
and "we tried 400 things and reported the best one" — the second is how this programme got a
candidate book that failed its own placebo. The gate's own docstring already asks for it
(`gate.py:47-48`: DSR runs on an assumed floor *"on a number nobody measured"* because no ledger
exists). The ledger starts in the first wave-6 session and every session prompt cut from this
plan carries the logging requirement.

---

## 3. The repair map — the whole authored estate

Format per the brief: what underperforms · which component is responsible ({entry, exit, session,
symbol surface, sizing, pairing, regime gate, cost geometry}) · the repair · what testing it costs ·
what it is worth if it works. Costs are in agent-sessions (AS) and archive-compute (cheap: W's
pilot generated and walked 26 years × 12 sleeves inside one session). "Gate" below always means
W's gate in diagnostic mode at standard B for measurement, with the ledger logging every variant;
arming anything remains Borhen's call at the standard he chooses.

### 3.1 The armed four — live; repair = de-risk the known concentration and extend the evidence

What is actually known: they survive broker-true re-costing unconditionally (N §3), the governed
live MC clears both phases from here (V §3: 0.99823 2-step from current equity), **and every
headline is computed inside the window that selected them** (V §7: out-of-window +0.100 %/month
over ten years, negative before 2020; the repo's own `AUDIT_exec_and_untouched.md` says "NO clean
out-of-sample slice exists" and nothing cites it). The frequency ramp is the mechanism to attack:
book-day density runs 0.4 % (2015) → 28.7 % (2025), so the out-of-window silence is mostly the
sleeves *not firing*, not the sleeves losing. That is measurable, attributable, and repairable.

Two facts from W's own negative-controls run sharpen the picture. **`metals_core` ADMITs the
walk-forward gate at zero carry** (+0.635 R/day OOS, 100 % folds positive, q 0.082 on the priced
subset) and REJECTs at its structural horizon — independent confirmation that holding time, not
edge, is its open question. And **the armed book cannot currently be fully gate-scored at all on
coverage**: `crypto` is NOT_EVALUABLE at 47.9 % cost coverage (DASHUSD has no tick file),
`sub_xvol_pullback` at 93.9 % (EU50.cash blocks its universe), `metals_core` under the refuse
policy at 76.2 % (the four metal crosses are unpriced), and `energy_agri` REJECTs on significance
at minimal carry on the priced subset (OOS +0.302 R/day, 75 % folds positive, q 0.33 — a positive
edge that cannot yet clear the family bar) — the armed sleeve with the weakest statistical case. The §9
tick capture is therefore not a market-expansion nicety: **it is what makes the live book's own
gate scores computable**, and `energy_agri`'s significance question is a standing repair item on a
sleeve that is already trading (its family expansion in §5.4 is the breadth answer).

**The shared repair (Session AB, §6) — attribute the ramp, then normalize or gate:**
regenerate each sleeve's *qualifying conditions* (not just intents) over the full archive and
decompose the ramp into (a) symbol availability — `crypto`'s history starts 2024-09; several
surfaces simply did not exist earlier; (b) **fixed absolute thresholds** that recent vol/level
regimes cross more often; (c) genuine structural change. Then per cause:

- (a) is benign: restate the out-of-window economics on the surface that existed. The −0.220 %
  pre-2020 number currently mixes "sleeve lost" with "sleeve's symbols didn't exist"; separate them.
- (b) is the high-value case: re-express the threshold **scale-free** (ATR-relative, percentile),
  refit on pre-2024 data only, validate 2024+ — the *reverse* of the current contamination. If a
  normalized variant fires across 30 years with positive expectancy, the armed book's evidence
  base moves from 194 selected-window trades to thousands, and the 46.9 %-on-194-trades
  concentration doubt (N §8.2) dissolves by measurement.
- (c), where real, becomes an **explicit regime gate**: "this sleeve trades in regime R" with R a
  named, monitored variable — which converts an unconditioned bet into a conditional claim tested
  on every historical instance of R, and gives the command center something to watch live.

Cost: 1 AS (AB) for attribution + first normalization sweep; archive-compute trivial.
Value: this is the highest-value repair in the estate — it de-risks the money that is already at
risk, and every point of it comes from data on this machine today.

Per-sleeve additions:

| sleeve | specific diagnosis | specific repair beyond AB | cost | worth if it works |
|---|---|---|---|---|
| `crypto` (conf 0.85, gross 1.212 R, n=104, ~40 % of book edge — the real concentration per V §6) | short history (2024-09+), 2-symbol surface (BTCUSD+DASHUSD, ETH deliberately excluded — `crypto.py:9-15`), largest single risk; live window fired 0; gate-unscoreable on DASHUSD coverage | **it is already a donchian-20 breakout** (H4, ac60-gated, 4 R — `crypto.py:25-28`), i.e. the same mechanism family as `mx_btcusd/ethusd/avausd` (D1, 2 R): run the *family* across the archive's full crypto set and admit per-symbol/per-timeframe members through the family test; cap the whole crypto **cluster**, not the sleeve (pairing repair) | inside AA/AF | breadth on the book's largest edge; cluster cap converts "40 % on one sleeve" into "40 % on a diversified cluster" |
| `metals_core` (conf 1.0, gross 0.910, n=131) | FN-side CARRY_CONDITIONAL (BE 329 h vs 320 h ceiling — missed by 2.8 %) | **exit repair** (§5.3): swap-aware exit or −10 % time-stop tightening flips the FN tier; test over regenerated 34-year stream | inside AD | `metals_core` becomes armable on redacted_account too — a second account slot for the book's conf-1.0 sleeve |
| `energy_agri` (conf 0.8, gross 0.539, n=162) | FTMO oil commission is *unmeasured*, currently zero via the `Cash II` path-string defect (N §7); NATGAS/HEATOIL unpriced; **registry says 4 symbols but the generator's surface is 2** (USOIL/UKOIL only — `energy_agri.py:20` vs `admission.py:168-179`); weakest gate statistics of the armed four (q 0.33 at minimal carry) | land the classifier fix + re-cost (+0.0144 R/trade sensitivity already banded); reconcile the registry-vs-generator surface (CORN/COTTON are sized-for but can never fire — wiring defect); agri/energy surface extension from the archive is also its significance repair (breadth) | 0.25 AS inside AA + AF | removes a known false-zero from the live book's cost model; turns the armed book's weakest statistical case into a family-level claim |
| `sub_xvol_pullback` (conf 0.45, gross 1.307, n=90 — the highest per-trade gross in the book, and a cell selected from a substrate scan) | selection-artifact risk is the whole doubt (V: halving it costs only 0.3 %/mo — but knowing is cheap) | **parameter-surface neighborhood test** (§5.1): re-run the substrate scan cells adjacent to the selected cell over the full archive; a real edge sits on a plateau, an artifact sits on a spike | 0.5 AS inside AB | either the doubt dissolves or the book's expectation is honestly resized — both are wins for a live book |

### 3.2 The seven core non-survivors — two cost-geometry cases, three exit cases, one conditioning case, one resample

| sleeve | diagnosis (component) | repair path | cost | worth |
|---|---|---|---|---|
| `fx_jpy` (M15, GBPJPY+USDJPY, gross +0.282, n=530; net +0.041 at measured-zero carry; tier `MEASURED_LIVE_CARRY`) | **cost geometry**: commission is 0.115 R against 0.28 gross — 41 % — because stops are 1.0×ATR(M15) tight; live 41-trade sample negative but non-significant after correction; **gate-unscoreable on sample** (its validated stream spans ~1 year → 2 evaluable folds against a 3-fold floor) | (1) stop-width sweep 1.0→1.5–2.0×ATR over the archive (commission_R scales down as stop widens; R-geometry changes measured in the same run); (2) **extend the stream**: regenerate over the full M15 archive (2024+ on this machine; the §9 deep-history M15 fetch if the owner wants more) — that alone makes it gate-scoreable; (3) entry-quality filter via meta-label once §4.8 lands; (4) reconcile the spec divergences K found (live dropped the `len(lon)>=6` session-completeness filter the validation had — a live-fidelity bug with a known fix); (5) the one-unit-per-cluster envelope decision is Borhen's standing item | 0.5 AS inside AD | a conf-0.15 diversifying JPY cluster back in the book at honest cost; small but real, and the JPY cluster's correlation to the trend book is low |
| `fx_jpy_ny` (as above, enters 16:00, ceiling 04:00 next day — crosses midnight ~4/5 days) | same cost geometry + **exit**: its ceiling makes it the one JPY sleeve that can pay swap | add a **pre-rollover flat rule** (exit 23:45 broker if open) — caps swap at structurally zero, testable over the whole archive in one sweep | inside AD | converts CARRY_CONDITIONAL_LIVE_SUPPORTED into structurally carry-free |
| `metals_softband` (H4, BE 198 h of 320 h max) | **exit**: killed on a hold never measured | estate walk regenerates its realized holds (this is the §1.4 correction — one run, no fetch); if mean hold < 198 h it is alive as-is; if not, swap-aware exit / time-stop tightening sweep to find the profitable frontier; note it is the *only* generator passing `intra_size` — reconcile that live-vs-research divergence while touching it | inside AA + AD | a conf-0.5 metals sleeve back; also the cleanest test case for the swap-aware exit machinery |
| `vp_euidx_pocgrav` (H4 volume-profile, BE 251 h) | same as above on FTMO — **but it is already UNCONDITIONAL on redacted_account** (its per-account swap is the difference) | no repair needed to ship: it is redacted_account's measured fourth survivor. FTMO-side: same hold measurement + exit sweep | ships with §7.2 | an armable sleeve **today** on the second account |
| `sub_mid_dn_revert` (BE 269 h) | same exit case — and it is the **nearest miss in the whole core book**: on W's gate at minimal carry it posts OOS +0.500 R/day, **100 % folds positive, q 0.119** (REJECT only at horizon carry) | same hold measurement + sweep; if its realized holds come back short, it is essentially admitted already | inside AA + AD | conf-0.2 diversifier whose entire case turns on one measurable number |
| `idxrev` (8-index pocket sized, **5-index generator surface** — `index_jpy.py:19`; n=6,473, gross +0.006 ≈ zero; the only live-profitable sleeve in the live window) | **regime gate / conditioning**: a zero mean over 6,473 heterogeneous trades is an unconditioned average, not an absence of signal; also a registry-vs-generator surface mismatch to reconcile | slice the regenerated stream by index / session / vol regime / pocket depth; meta-label overlay (§4.8) is built for exactly this shape; the live-positive fortnight is one more slice to explain, not noise to dismiss; 24 % of its universe was class-transferred cost — §4.6 prices it honestly | 0.5–1 AS inside AA + AH | large-n, low-correlation index sleeve; even a thin conditioned edge at this n is a real book contribution |
| `metals_ob_micro` (n=7, gross −0.5) | **unmeasured** (§1.2) | regenerate at scale over 34 y of H4/M15; then standard diagnosis; if genuinely negative at scale, run the inverse per the charter's own doctrine before parking | inside AA | either a measured sleeve or a measured park — both better than a 7-trade guess |

### 3.3 Market expansion — three mechanisms, one family discipline, five data holes

The family structure is the repair lever: 14 built tags = 3 mechanisms (`donchian_20_breakout`,
`volume_surge_reversal`, `atr_mean_reversion`) × symbols, all D1, target 2R, next-open entries
(`market_expansion_d1.py:18,31-44`; exit contract `time_stop` 96 bars for all 14,
`execution_packets.py:75-94`). W judged 12 **standalone**, which charges each sleeve the full
multiplicity bill alone. The mechanism-level questions — "does donchian-20 carry edge on this
symbol class", "is volume-surge a real reversal signal" — have √breadth more power and were never
asked. Session AF asks them across all 43 archive symbols; Session X runs the diversifier door.
Two family-level facts to carry: **realized median hold is ~3 D1 bars against the 96-bar
contract**, so this family is nearly swap-free by behaviour and its repairs are entry/regime
questions, not carry ones; and the core `crypto` sleeve is the same donchian mechanism on H4
(§3.1), so the crypto rows below and the armed sleeve are one family for admission purposes.

| sleeve | W's measurement | diagnosis (component) | repair path | worth |
|---|---|---|---|---|
| `mx_btcusd_d1_donchian_20` | **+0.2446 R/day OOS, 100 % folds, raw p 0.0124, q 0.149** | significance only — one sleeve paying a 12-family bill | (1) diversifier certification vs the armed book (X — module exists, never run); (2) crypto-donchian family pool (BTC+ETH+AVA+ADA+DASH…) — family-level admission; (3) if the owner takes standard B for the candidate book, it is the first slot on a challenge account | the single fastest new-edge ship in the estate |
| `mx_ethusd_d1_donchian_20` | +0.1816, 60 % folds, robustness fail (best-fold dependent) | regime dependence | fold-conditioning: name what the good folds share (vol state, trend state); pool into the crypto-donchian family where its q-bill shrinks | family member |
| `mx_avausd_d1_donchian_20` | +0.1265, robustness fail | same | same | family member |
| `mx_nzdjpy_d1_donchian_20` | +0.0800 scored, **lifetime −0.003/trade across full history** | regime break somewhere in 26 years | find the break date, name the variable (carry regime? vol era?), gate on it; swap-aware exit for the carry leg | conditioned FX-donchian member |
| `mx_jp225_volume_surge` | +0.1985, q 0.487, 80 % folds | significance via family | volume-surge family pool across the index set | family member |
| `mx_us30_volume_surge` | +0.0584, 40 % folds — stability | fold conditioning inside family | as family | member |
| `mx_ger40_volume_surge` | −0.0112/day | entry or exit, to be split | MFE/MAE decomposition on the regenerated stream: if setups have excursion the exit misses → exit repair; if none → test the inverse; else park with list | decomposition is one query on AA's output |
| `mx_us500_atr_mr`, `mx_us100_atr_mr` | −0.2551 / −0.3518, 20 %/0 % folds | **mechanism×class mismatch**: mean-reversion against the two strongest-trending instruments in the estate | (1) inverse test (continuation on the same trigger — costs nothing extra in AA); (2) vol-regime conditioning (MR lives in range regimes); (3) run the *mechanism* over the other 40 symbols before any verdict on it — the mechanism was only ever tried on the two worst plausible hosts | either a repaired MR family elsewhere, or a continuation signal, or an honest park |
| `mx_cadjpy_volume_surge` | n/e — no measured spread | **coverage** only (its bars are on this machine, D1/H4/M15 both brokers — verified by manifest read) | price via the §4.6 spread model with banded verdicts now; VPS tick capture begins in the AC lane for a measured spread later | judged this wave instead of never |
| `mx_eu50`, `mx_fra40` | n/e — no spread *and no bars* | **data** | owner bars-export ceremony (§9, minutes of VPS time, read-only — same as the one that landed 2026-07-27); then standard walk | two sleeves move from unjudgeable to judged |
| `mx_aus200_volume_surge`, `mx_spn35_volume_surge` (never allowlisted) | never judged — and the exclusion is **only** a hard-coded 12-name tuple (`candidate_registry.py:425-438`); both are fully runtime-capable (generators, exit profiles, collision-winner status, seed weight) | same data ceremony (no bars for either symbol), then the standard walk; if either clears, the allowlist edit is a one-line policy change for the owner | completes the built family |
| `mx_aus200_atr_mr`, `mx_ger40_atr_mr` (metadata-only, no generators) | one lost its symbol-collision to volume-surge; the GER40 one is explicitly preserved as *"context/veto intelligence"* after its exact-M1 repair negated the candidate claim | route the GER40 veto intelligence to the overlay lane (§4.8); the AUS200 ATR-MR variant re-enters, if ever, through AF's mechanism-level sweep rather than as a resurrected spec | nothing lost, nothing double-built |

### 3.4 The twelve candidates — the instrument was broken, not the sleeves

These are researched mechanisms with train/oos/sealed splits, correct-entry nulls, and honest
per-sleeve caveats written into the registry itself (`candidate_registry.py:47-138`). What they
never had: broker-true cost, an uncontaminated joint book test, or — for the seven first-of-day
sleeves — a generation port that reproduces them (K1 §3.5's latch mechanism). Under §2.1 all
twelve are measurable now on spec economics; Session Y raises the fidelity stamp in parallel —
and **two need no Y at all**: `vol_compression` (per-bar, 100 % measured recall) and
`vss_fxcross_london_up_low` (per-bar by structure, `fidelity.py:213-217`) clear the existing
fidelity floor today and were simply never scored in the pilot. They walk first.

Two calibration facts for what this group is worth. **Breadth**: the unified-book record shows
`asian_fade` on 3,216 fire-days and `asia_pdl_fade` on 2,573 — against the armed book's **128
book-days in eighteen months**. Intraday candidates are where the book's decision frequency (and
therefore payout cadence) lives. **The placebo, read precisely**: the June book's Sharpe delta
(+0.1297) matched the random-day median (0.1303, p = 0.59) — meaning the *day-timing* of the
overlay added nothing beyond the trades' own returns; it does not say the sleeves are junk, it
says the joint validation could not distinguish them from their own shuffled calendar. Broker-true
cost, day-blocked nulls, and the ledger — all built since — are exactly what that validation
lacked. (The one book-level improvement in the whole record that *passes* its own placebo is the
A8 metals-confluence gate — an overlay, which is one more datum for §4.8's lane.)

| candidate (conf) | registry evidence (legacy cost) | diagnosis | repair path | worth |
|---|---|---|---|---|
| `vol_compression` (0.40, crypto D1) | splits +0.242/+0.246/+0.369, p 0.0033 — rising OOS | per-bar D1: judgeable **immediately**, no Y dependency | straight through the gate at broker truth in AA | strongest candidate; crypto-cluster member |
| `asian_fade` (0.40, EUR/GBP M15, trail) | +0.142/+0.241/+0.228, p≈0; "EURUSD positive every year 2014-2026" | first-of-day (7 % recall) | spec-economics walk now (M15 archive: 2024+ broker-true; pre-2024 M15 via the §9 deep-history fetch if the owner wants the full span); Y raises stamp; trail-exit needs the panel's trail simulation — small AA extension | FX-reversion diversifier, orthogonal to the momentum book by design |
| `ny_crypto_momentum` (0.35) | +0.102/+0.273/+0.310, n=1,702, drift-null p 0.0033 | first-of-day (0 % recall); live p90 hold = 271 % of nominal horizon — **exit-spec bug live** | walk spec now; fix the live horizon-overrun as a fidelity work item (it is a live bug whichever way the economics land) | crypto killzone member |
| `orb_crypto_london` (0.35) | +0.150/+0.098/+0.058, n=2,706, decaying splits | first-of-day (0 %); the decay pattern is the thing to explain | walk now; fold-conditioning on the decay (vol-state? year?) — prescription table row 5 | conditioned member or honest park-with-list |
| `asia_pdl_fade` (0.25, 30 symbols — the broadest surface in the estate) | +0.110/+0.015/+0.164, OOS thin, NATGAS split already applied | first-of-day (30 % recall) | walk now at broker truth across its 30-symbol surface; its breadth makes it the best *family-level* test of the sweep-reclaim mechanism; OOS-thin → fold-conditioning | breadth: 7,524 trades in its own history; even thin per-trade edge × this n matters |
| `liq_asia_up_low_metal` (0.25, 4 metals) | +0.113/+0.142/+0.168 rising, p 0.004 | first-of-day (0 %) | walk now; PDH-short carries the edge per its own note — test sides separately | metals reversion vs the deployed metals momentum — pairing value |
| `metal_session_reversion` (0.40, XAU/XAG) | +0.066/+0.076/+0.151, p≈0, n=4,458 | first-of-day (8 %) | walk now (trail exit — same AA extension as `asian_fade`) | second metals-reversion angle |
| `kz_london_crypto_low` (0.10) | +0.260/+0.154/+0.424, drift-null only marginal (p~0.085) | first-of-day (0 %) | walk now; the drift-null marginality is exactly what broker-true + day-blocked stats will settle | low-weight member; cheap to settle |
| `vss_fxcross_london_up_low` (0.12, 5 JPY/EUR crosses) | +0.077/+0.070/+0.329, OOS daily thin (+0.001) | structure to verify (squeeze-breakout; Y confirms whether it latches) | walk now; OOS-decay-watch becomes a fold-conditioning question | FX-cross squeeze diversifier |
| `vol_squeeze` (0.0 — quarantined: "same-day correlated index risk-unit contribution was a book drag") | per-trade valid, book-level drag | **pairing/sizing**, not edge: it fired *with* the index book | repair is portfolio-level: re-test under the diversifier certification with a same-day correlation cap and satellite weight; if the drag is confirmed at broker truth, park with the sizing note | the quarantine reason is exactly what §4.4's machinery adjudicates properly |
| `ny_index_momentum` (0.0 — "leave-one-out improved when dropped") | +0.178/+0.175/+0.257 per-trade, mid-vol conditioned | pairing (US-beta overlap with `vol_squeeze`/index book) | same diversifier-door re-test; its mid-vol conditioning is already the regime-gate shape §5.2 builds | either a conditioned index member or a measured park |
| `structural_retest` (0.0 — "full three-cell daily-unit audit failed", −0.071 daily) | 3 cells each every-split+ per-trade, daily-unit negative | **sizing/aggregation**: per-trade edge, day-unit loss ⇒ intraday clustering eats it (prescription row 3) | intraday count cap / cluster-day unitization, then re-audit; its crypto-SHORT cell is the system's only dedicated short — worth the one extra test on that ground alone | the estate's only short-side mechanism, rescued or honestly parked |

**The candidate book's joint story** — 76.4 % of the live trial's net loss, proxy-grade validation,
placebo-failed — is *why the walk is at broker truth through W's gate with the ledger on*, and why
book composition happens in §4.4's certified-diversifier lane rather than by another tuned
unified-MC. The June machinery already embodied book-contribution confidence; it lacked honest
cost, honest nulls, and trial accounting. Those are exactly the three things waves 3–5 built.

### 3.5 The orphans and the wiring defects — registered disposition in one session

The cache facts, read directly this week (`INTEG_W5_new_streams_cache.pkl`; rows carry only
{sleeve, sym, date, year, R} — which is Session N's "no exit index" finding in its exact shape):

| artifact | cached record | why it was dropped (route's own words) | repair path | worth |
|---|---|---|---|---|
| `leadlag_core` | **n=3,115, mean +0.116 R, sum +362.6 R**, 2018→2026, 7 symbols | book-level: *"dilutive (high-freq, low per-trade Sharpe)"*, *"the tail-variance injector"* — a **pairing/sizing kill, not an edge kill** | regenerate at broker truth (high-frequency ⇒ spread-sensitive; §4.6 prices it honestly), then through the **diversifier door**, whose no-risk-regression and correlation-ceiling conditions are precisely the instrument that adjudicates a "tail-variance injector" instead of adjectives; test at a capped satellite weight | +362 R of raw cached edge is the largest unregistered pool in the estate; even a heavily capped admission is material |
| `subh4_ll_fx` | n=357, mean +0.199 R, EURJPY **only**, 2014→2026; FWD +0.760 collapses to **+0.332 under fixed-R + winsor — still positive** | *"dilutive (thin fwd, 38 % win @ fixed R)"* | restate at fixed-R broker truth over the full archive; **symbol expansion** — one mechanism, one symbol is an accident of history, and the archive holds every JPY cross | a conditioned FX-cross member, or an honest park with its list |
| `xlayer_veto_gate` | 56 rows, +1.60 R mean — a filtered **subset** of `sub_xvol_pullback` (§1.6) | not dropped at all: **shipped** as `leader_impulse_veto` (`admission.py:311-314`, 1.5× size-up, perm p 0.0003) | none needed — it is the overlay lane's existence proof and template (§4.8) | already earning |
| `session_leadlag_genuine` | registered at conf 0.15 (`CLEAN4_REGISTRY`, `admission.py:266-277`), `forward_only`, **no generator, no exit profile** — but its own note carries real evidence: FWD **+0.46 R, n=390**, corr +0.053 vs book, *additive* on the vol-matched stress MC (Sharpe 0.1522→0.1586), with a stated graduation condition ("when a 3rd fwd year exists") | the trimmed genuine-lead subset of the same research that produced `leadlag_core`; the wiring was simply never built | **build the generator** (its 6-symbol surface and session-open mechanism are fully specified in the note; `leadlag_core`'s regeneration is the substrate) + an exit profile, walk it at broker truth — and note its graduation condition is exactly the kind of wait §2.1 converts to a measurement: 34 years of archive is more than "a 3rd forward year" | the estate's only additive-on-stress-MC forward-validated sleeve that cannot currently fire; closing the wiring is nearly free |

Every row above ends in a registry entry with status and evidence — orphaning is the one
disposition this plan forbids. Cost: 0.5–1 AS inside AA (regeneration) + AF (expansion).

---

## 4. Architecture — what gets built or fixed so the system learns

Ordered by leverage; §6 sequences them. Items 4.1–4.6 are repairs/wirings of things that exist;
4.7–4.10 are the never-started builds the charter names.

### 4.1 The gate's diagnostic mode (the fixing-machine head) — Session AA, first commit

`src/research_infra/walkforward/gate.py` emits, beside each verdict: per-gate margin (how far from
passing), the failing folds/symbols/sessions, MFE/MAE aggregates from the panel, and the §2.2
`prescription`. Output artifact `REPAIR_QUEUE_V1.json`, one row per (sleeve, prescription,
evidence). The fidelity floor becomes the §2.1 stamp. `NOT_EVALUABLE` survives only for genuine
sample-floor cases, and even then carries "what data would make it evaluable." ~0.5 AS, no new
statistics, no gate relaxed — the seven gates and their thresholds are untouched.

### 4.2 The learning direction — rebuild the actuator's evidence, then its composition

Three moves, in dependency order:

1. **Cost-true splits per sleeve** (the missing input R named): AA's estate walk emits per-sleeve
   train/oos/sealed day-series at broker truth; `learning_actuator.py`'s backtest half reads those
   instead of the legacy-cost CP4/CP5 splits. The cost-true veto then retires — the evidence
   itself is cost-true, so the patch that contained the damage is no longer needed.
2. **Bidirectional composition with asymmetric speed**: `_apply_live`
   (`learning_actuator.py:226-264`) currently takes `cap = _live_stage(ev)` and applies it only
   downward; the cost-true veto at `:242` exists solely because the backtest half was
   legacy-cost. Replace with a rule that moves both ways at evidence-appropriate speeds — brake
   on 4–8 stop-outs against the day-blocked boundary exactly as R built it; **raise** only on
   live n ≥ 30 (day-blocked, the same bar a backtest split must clear), capped per re-rate cycle
   (`MAX_UP` stays the ceiling) and never above the owner's dial. Live evidence that a sleeve
   outperforms its backtest becomes recognizable, which is the whole point of a learning loop;
   the asymmetry (fast down, slow up) is preserved because it is correct, not because it is
   timid.
3. **Fix the known limitations while inside**: the per-sleeve-per-account "family-wise" budget
   that is ~0.75 across the book (R §4 item 14), and the first-passage/point-in-time mismatch
   (item 12) — both named, neither fixed, both cheap now that the shape changes anyway.

Stays default-off and recommendation-only until Borhen turns it on; what changes is that when he
does, it can move weight in both directions on honest evidence. ~1 AS (Session AE).

### 4.3 `regime_inflation.py` — fix the module, not the call site

The flag fires on `ratio >= 1.5` where `ratio = mean_in_window / mean_all`; a negative `mean_all`
makes the ratio negative and the detector is defeated monotonically by making the concealed loss
bigger (W §4; measured: 50,000 hidden losers → flag False, verdict string "CLEAN"). W guarded its
own call site only; `portfolio_contribution.py`'s condition 1 still depends on the broken module.
Fix: compare on signed differences/effect sizes rather than a ratio of means, with the
sign-adversarial case in the tests. ~0.25 AS inside AE (or Z if Z reaches it first — its prompt
already flags it).

### 4.4 The diversifier door — wire `certify_diversifier` in as the second admission lane

`portfolio_contribution.certify_diversifier` (six conditions: genuine standalone edge, positive
contribution at fixed non-optimized satellite weight, block-permutation significance of the
*improvement*, OOS robustness, correlation ceiling, no risk regression) exists, is documented, and
has never been executed against this book. Session X is already commissioned to run it; this plan
confirms X and adds: (1) the fixed satellite weight and correlation ceiling get sealed into the
GateSpec so the second door is as tamper-evident as the first; (2) admissions through this door
are labelled `DIVERSIFIER` and their book role (satellite weight cap) travels with them into any
composition artifact; (3) the effective-sample honesty V established (correlation on ~13
overlapping days is weak evidence) is carried as a published caveat on every certificate. No
condition is relaxed, exactly as X's prompt insists.

### 4.5 The trial-budget ledger — §2.3, mechanized

Run `trial_budget_ledger.py` for real: every gate invocation, every sweep cell, every variant any
wave-6+ session evaluates appends (mechanism, sleeve, variant hash, window, outcome). DSR/PBO read
the measured count. One shared artifact, append-only, committed. ~0.25 AS inside AA, then a
standing requirement in every session prompt.

### 4.6 The spread model — make "no measured spread" a band, not a blocker, and shrink W's look-ahead

The largest disclosed bias in every deep-history number is the 37-day spread snapshot charged to
26 years (W §4 defect 4, "33–219 % of gross R on this family"). Build `spread_model_v1` from the
263.9 M ticks: per symbol-class, spread as a function of hour-of-week × volatility state, fitted
on the 37-day window, **extrapolated to history via each era's bar-based volatility** with stated
uncertainty bands; calibration check against the one in-tree second window
(`ULTIMATE_TICK_SPREAD_GOLD.json`, whose 24 % spread rise against a 9–14 % price fall already
refuted naive price-proportional scaling — N §8.5). Gate results then carry
{low, mid, high}-band verdicts; a sleeve that survives at the high band is robust to the
look-ahead, and one that flips bands gets that fact in its repair row instead of a silently
optimistic pass. Unpriced symbols (CADJPY, DASHUSD, XAUEUR/XAGEUR/XAUAUD/XAGAUD, NATGAS_cash…)
become priceable-with-bands immediately; the forward tick capture (§9) tightens the bands later.
~1 AS (Session AG). Honest limit: bands narrow the look-ahead, they do not eliminate it — only
capture does.

### 4.7 Feature store and label store v1 — the substrate the repairs already need

Not a speculative ML platform; the minimal two artifacts every §5 lane consumes:

- **Feature store**: per (symbol, day) over the full archive — vol percentile (multi-window),
  trend/range state, session statistics, carry rate, spread-band state, cross-asset context
  (dollar, index breadth). Point-in-time correct (as-of joins only), columnar, versioned. This is
  where §5.2's regime variables live so every sleeve's conditioning draws from one audited
  source instead of five ad-hoc recomputations.
- **Label store**: per intent from the estate walk — realized R at broker truth, hold hours, swap
  nights, MFE/MAE path, exit reason, fidelity stamp, gate margins. (The panel computes nearly all
  of this today and drops it at the verdict boundary; the store is mostly plumbing.)

~1.5 AS (Session AH). The partition registry Z authors governs both stores' train/validation
roles from day one, with March 2026 sealed out.

### 4.8 The model chain v1 — meta-label overlays, judged like any other sleeve

First model: per-family **meta-label** — P(win | feature-store state) for a sleeve's intents,
used as an entry-quality filter/size overlay, trained under Z's hygiene (purged/embargoed,
partition-registry enforced), validated through the same gate and ledger as everything else, and
admitted (if at all) as an overlay with its own sealed spec. Three immediate customers named by
the repair map: `idxrev` (conditioning a zero-mean n=6,473 stream), `fx_jpy` (entry-quality at
41 % commission share), `asia_pdl_fade` (OOS-thin breadth). `xlayer_veto_gate` (§3.5) is
evaluated in this lane as a candidate veto. This is the charter's "statistical learning /
meta-labeling" line made concrete. ~1–1.5 AS (Session AH second half), after 4.7.

### 4.9 The command center — extend the canary page into the daily operating view

T's `CANARY_OPERATOR_PAGE.md` + monitor already exist for the armed book. Extend, one page, one
generator, read-only: positions and governor state; gate/token/tag state with the supervisor
`--tags` check (the one CRITICAL condition that can silently widen the book); learning-lane
recommendations (§4.2) with their evidence; estate/repair-queue status (what moved through the
gate this week, what is parked with what list); and the §5.2 regime dials for the armed sleeves.
~0.5–1 AS (Session AJ), pure read-side, no VPS write.

### 4.10 Packet additions — one VPS carry, batched with AC's restart

Forward-data quality items, each one line to a few lines at the emitter, already justified by
wave-3/4 findings: realized swap/commission/fee on **every** `position_closed` (N's §9.1 — would
have made the carry question answerable from the stream alone); broker deal timestamps on every
close (N's §9.2); `spread_r` at intent time (N's §9.4 — `None` on all 99,112 packets today); and the
**first-of-day latch record** — (sleeve, day, latched bar) — which makes candidate fidelity
measurable forever after (§2.1). These ride the same owner-executed restart AC is already
composing; no separate ceremony. ~0.25 AS to spec into AC's package.

---

## 5. The improvement machinery — how sleeves get better, not just measured

Five reusable methods, each applied by the sessions in §6. Every run logs to the ledger; every
claim of improvement carries its null (the wave-3 discipline, pointed at building).

**5.1 Parameter surfaces and neighborhoods.** For any sleeve with tunable geometry (stop width,
target R, time-stop, threshold), sweep the neighborhood over the archive and publish the
*surface*, not the best cell. Decision rule: plateaus are real, spikes are artifacts; a repair
that only works at one cell is not a repair. First customers: `sub_xvol_pullback` (the selected
substrate cell's neighborhood — §3.1), `fx_jpy` stop width, every §3.3 family's threshold.

**5.2 Regime conditioning.** The estate's most common failure shape (stability/robustness/lifetime
fails; the armed book's own §7) is "edge in some periods, not others." The build answer: a small
named set of regime variables in the feature store (vol percentile, trend state, carry regime,
session), and per-sleeve conditioning tested as an explicit gate with its own OOS walk. The
deliverable is always a *named, monitored* variable — "trades only when X" — never a silent
refit. The armed-four ramp attribution (§3.1) is the flagship application.

**5.3 Exit repair.** Swap is the largest broker cost for eight of eleven core sleeves, and the
panel now measures holds. Three standard treatments, swept per sleeve over the regenerated
streams: **swap-aware exit** (close before rollover when expected remaining edge < swap/night —
`rollover_nights` already knows the triple-swap days), **time-stop surfaces** (the §5.1 sweep on
horizon), and **pre-weekend flat rules** for sleeves whose ceilings cross Friday. First
customers: the three carry-conditional sleeves, `fx_jpy_ny`, `metals_core`-on-redacted_account,
`mx_nzdjpy`.

**5.4 Symbol-surface expansion.** Every mechanism that survives anywhere is run across all 43
archive symbols (family discipline of §3.3: judged as a family with measured trial counts, then
per-symbol allocation by the diversifier door). This is where the estate stops being "37 authored
artifacts" and becomes "mechanisms × the whole tradable surface." The archive is 34 years deep on
D1/H4 precisely so that this is cheap.

**5.5 What the ticks buy that bars cannot.** Three uses, in value order: the §4.6 spread model
(priceability + look-ahead shrink); **entry-timing repair** — for M15 sleeves whose commission
share is high, measure fill quality of close-entry vs next-open vs limit-at-close over the tick
window and take the cheapest honest entry (the pilot measured +0.00152 R signed bias for the D1
family — small there, unknown for M15 until measured); and **intraday microstructure features**
for the feature store (spread-state, tick-rate) available for any forward-period validation. The
263.9 M rows cover 2026-06-18..07-24 — enough to *calibrate* models the bars then carry
backward, which is exactly how the spread model uses them.

---

## 6. The build order

Constraints honored: 3–4 concurrent sessions; this machine's memory staggering per the working
agreement; zero sealed-replay hours anywhere; the VPS only ever touched by owner-executed carries
in the AC lane; March 2026 outcome-unread behind W's sealed blackout and Z's registry.

**Already in flight (wave 5) — confirmed, with scope sharpened by this review:**

- **X — book-level + diversifier door** (commissioned): runs §4.4; scores the armed four through
  the gate *and* the diversifier test; merged-book evaluation on the real sizing path
  (`mc_governed` exists and reduces exactly — V §1). **Adopt `passes/yr` (payout-rate), not
  `p_pass`, as the composition objective** — V §6 measured `p_pass` inverting the leave-one-out
  ranking, so any composition argument on it picks the wrong book.
- **Y — first-of-day port repair** (commissioned): unchanged; its output raises §2.1 fidelity
  stamps. The latch-record packet item (§4.10) removes its ceiling for the future.
- **Z — trainer hygiene + partition registry** (commissioned): unchanged; add the
  `regime_inflation` module fix if it reaches it first (§4.3), and hand its registry to §4.7 as
  the stores' partition authority.
- **AC — the activation carry** (commissioned): unchanged; absorb §4.10's packet additions into
  its single-restart package.

**Wave 6 — the estate walk and the armed-book de-risk (3 concurrent + X/Y/Z finishing):**

| session | scope | inputs | cost |
|---|---|---|---|
| **AA — the estate walk, diagnostic** | §4.1 diagnostic mode + repair queue; §4.5 ledger start; walk the 11 core + 3 orphans + `vol_compression` (and every candidate Y has cleared by then) over the full archive with holds/swap/MFE-MAE capture; emit cost-true per-sleeve splits (§4.2 input); trail-exit support in the panel; `energy_agri` classifier fix | W's gate (merged), bars archive, `cost_r` | 1.5–2 AS |
| **AB — the armed-book regime spine** | §3.1: ramp attribution; threshold normalization refit-pre-2024/validate-2024+; `sub_xvol_pullback` neighborhood; named regime dials for the command center | AA's condition series; feature-store precursors it builds inline and hands to AH | 1–1.5 AS |
| **AG — spread model + priceability** | §4.6; re-stamp W's pilot and AA's walk with banded verdicts; priceability for the 7+ unmeasured symbols; entry-timing measurement for M15 sleeves (§5.5) | tick archive, both in-tree spread windows | 1 AS |

**Wave 7 — repairs at scale (3–4 concurrent):**

| session | scope | cost |
|---|---|---|
| **AD — exit-repair lane** | §5.3 across the three carry-conditional sleeves, `fx_jpy`/`fx_jpy_ny` (incl. stop-width sweep and the pre-rollover flat rule), `metals_core`-FN, `mx_nzdjpy`; publish per-sleeve exit frontiers | 1–1.5 AS |
| **AF — family expansion** | §5.4: the three mx mechanisms × 43 symbols; crypto-donchian family incl. the core `crypto` surface extension; family-level admission with measured trial counts; the ATR-MR inverse test | 1.5 AS |
| **AE — learning direction** | §4.2 (cost-true splits in, bidirectional composition, multiplicity + first-passage fixes); §4.3 if Z has not landed it | 1 AS |
| **AK — candidates walk** (after Y merges; can start on Y's partial output) | remaining candidates through AA's machinery incl. first-of-day at spec economics; the three quarantined re-tests through the diversifier door (`vol_squeeze`, `ny_index_momentum`) and the intraday-cap re-audit (`structural_retest`) | 1–1.5 AS |

**Wave 8 — the learning system and the shipping package (3 concurrent):**

| session | scope | cost |
|---|---|---|
| **AH — stores + meta-label v1** | §4.7 + §4.8; overlays for `idxrev`, `fx_jpy`, `asia_pdl_fade`; `xlayer_veto_gate` evaluated as veto | 2 AS |
| **AI — book assembly + shipping** | compose every admitted/repaired sleeve through the diversifier door on the real sizing path at `passes/yr`; the redacted_account arming package (§7.2); the challenge-account candidate-book package (§7.3); firm-rules MC per target account | 1.5 AS |
| **AJ — command center** | §4.9 | 0.5–1 AS |

**Dependencies stated:** AA blocks AE (splits) and AK (machinery); Y gates only the *stamp* on
first-of-day results, not their spec-economics measurement (§2.1); AH consumes AB's features and
Z's registry; AI consumes everything and is the wave that puts owner decisions on the table with
measurements attached. AB, AG, AD, AF are mutually independent — that is the parallelism. Nothing
here blocks on forward data, a sealed window, or the VPS.

**Total:** ~14–18 AS over three waves — about the cost of waves 3–4 combined, which delivered.
Sealed-replay machine-hours: **0**. The B7.5 campaign stays parked exactly as priced; no bound
file is edited by any session above (H1 membership checked per session, per the working
agreement; the walkforward/validation/learning surfaces touched here are unbound — W, R and V
each verified their lanes).

---

## 7. Shipping — the capital ladder

Four surfaces exist today: FTMO #1 (armed, ~$107.9k), redacted_account ($96.2k, gated), FTMO #2
($100k, untouched), three challenge accounts ready. The ladder ships repairs as they clear, with
Borhen holding every arming decision:

**7.1 FTMO #1 — the armed book.** No composition change from this plan until AB's regime spine
and X's gate/diversifier scores are in front of Borhen. What this plan adds to slot 5+
consideration, in likely order: `vp_euidx_pocgrav` (if its FTMO-side exit repair lands),
`fx_jpy` at repaired cost geometry, `mx_btcusd` through the diversifier door. Each arrives as a
typed owner packet with the gate result, diversifier certificate, ledger-deflated stats, and
firm-rules MC at the live dial — the OD-3 dossier pattern, per sleeve.

**7.2 redacted_account — the measured second book, armable without a single new measurement.** Its
survivor set is already in the artifact: `crypto`, `energy_agri`, `sub_xvol_pullback`,
`vp_euidx_pocgrav` (UNCONDITIONAL there). Its governor is already de-risking correctly
(`size_cap_multiplier` 0.6229 at current equity). The arming package is AC-lane work: same
ceremony shape as FTMO's, its own `--tags`, its own token. The one caution V measured carries
over: pin `derisk_mode: smooth` explicitly in any dial discussion. This is the cheapest real
diversification available to the programme — a second account on a *different* measured survivor
set.

**7.3 The challenge accounts — where the candidate book ships.** The brief is right that waiting
is a choice. A challenge account is the correct venue for the first admitted candidate book
(standard B + diversifier certificates): real broker truth, real fills, bounded cost (the
challenge fee), and its forward record accrues *while capital is being won, not while parked*.
Package per account: 3–6 admitted sleeves composed by AI at `passes/yr`, sized by the firm-rules
MC for that firm's measured rules, its own token, its own canary page. FTMO #2 stays reserved as
the second funded surface for whichever of (repaired core additions | candidate book) earns it
first on challenge evidence.

**7.4 What earns a slot, stated once.** A sleeve ships when it clears the gate at the owner's
chosen standard **or** the diversifier door at sealed conditions, with ledger-deflated stats, at
broker truth, with its fidelity stamp current and its firm-rules MC run at the target account's
dial. That is the whole bar. Nothing in it waits on calendar time; all of it is computable from
what is on this machine.

---

## 8. The owner-decision queue this plan creates

Everything else in this document is session work. These eight are Borhen's, listed once so no
session improvises them:

1. **The estate-walk standard** — confirm B as the measurement standard for §3's walks (A remains
   the arming bar; C remains the research queue). W's options doc is the input.
1b. **One read-only host check** (orchestrator, minutes): confirm `ultimate_book_include_clean3`
   is `true` on the VPS config and `--tags` is carried by the running supervisor — i.e. the armed
   book is generating four sleeves, not three. Mainline holds no record of the flag (§1.7), and
   this is exactly the check T's canary page specifies.
2. **The diversifier door's sealed constants** — satellite weight cap and correlation ceiling
   (§4.4); X proposes numbers, Borhen seals.
3. **redacted_account arming** (§7.2) — whether and when; the package will be ready.
4. **Challenge-account commissioning** (§7.3) — which firm(s), when to start the clock.
5. **The two data ceremonies** (§9) — the bars top-up export and the forward tick capture start.
6. **The learning lane's budgets** — R's two false-alarm budgets and, once §4.2 lands, the
   raise-side caps; plus whether/when to flip it from recommendation-only.
7. **The JPY one-unit-per-cluster envelope** — the standing decision batch item, now with §3.2's
   repair results as context when they land.
8. **`metals_core`-FTMO's SIZE_UP dependency** (R §4 item 15: it survives only by discarding its
   one negative split) — resolve the `MIN_N` rule before the learning lane is ever enabled.

---

## 9. What this plan does not do, and the two ceremonies it asks for

**Does not:** touch the VPS or the armed book outside the AC lane; edit `config/agent_config.yaml`
or any H1-bound path; run a sealed replay arm (the campaign stays parked, banked, priced; March
2026 stays outcome-unread — W's blackout plus Z's registry make that structural, not
aspirational); soften any gate to manufacture a pass; or commission any adversary whose output is
a reason a sleeve should not trade. Refuters in every session verify **repairs** — arithmetic,
claimed mechanism, live-account safety — per the brief's redirection of the same rigour.

**Asks for (owner ceremonies, both read-only exports of the kind that already succeeded once):**

1. **Bars top-up**: AUS200_cash, SPN35_cash, EU50_cash, FRA40_cash, US2000, HEATOIL (D1/H4/M15,
   both brokers where present) — minutes of VPS time, unblocks four never-judged sleeves and
   completes coverage for two more. Verified absent from the current archive by manifest read.
2. **Forward tick capture** for the unpriced symbols (CADJPY, DASHUSD, XAUEUR, XAGEUR, XAUAUD,
   XAGAUD, NATGAS_cash, plus the item-1 symbols once their bars exist) — starts accruing now, tightens §4.6's
   bands forever after; until then the spread model prices them with honest bands. **This capture
   is what makes the armed book itself fully gate-scoreable** (§3.1): DASHUSD blocks `crypto`,
   EU50.cash blocks `sub_xvol_pullback`, and the four metal crosses block `metals_core` under the
   refuse policy. It is the highest-priority data item in the plan for that reason, not for the
   market-expansion sleeves.

**Residual risks accepted on the owner's instruction, named so they are chosen rather than
suffered:** the spread model narrows but does not eliminate the deep-history cost look-ahead
(§4.6); spec-economics numbers for diverged first-of-day sleeves carry transfer risk until Y and
the latch record land (§2.1); and the armed book's out-of-window question (§3.1) is answered here
by measurement and conditioning, not by waiting — if the ramp attribution comes back "genuine
regime change, unconditionable," the honest output is the regime dial on the command center and
Borhen's sizing judgment, exactly as V §8 framed it.

**The one-line summary the next orchestrator session should carry:** *the killing machine gets a
diagnostic head, the whole estate walks through it over 34 years of broker-true history this
machine already holds, the repairs it prescribes are built by three parallel lanes that never
touch the live account, the learning loop is rewired to move both directions on cost-true
evidence, and the ladder ships every survivor — redacted_account's fourth sleeve first, the candidate
book to the challenge accounts, and nothing, ever again, dies without its repair list.*
