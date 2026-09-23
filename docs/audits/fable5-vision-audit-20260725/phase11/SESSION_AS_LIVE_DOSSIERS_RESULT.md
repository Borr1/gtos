# Session AS — the live-activation dossiers and the fleet map (wave 11, blocks B1500–B1548)

**The estate's next live change is one line away from being a no-op, and the no-op would have armed
the contract the evidence rejects.** `mx_btcusd @ target_5R` activates by editing `final_target_r`
in `SLEEVE_EXIT_PROFILES` — except that for the whole `mx_*` cohort `final_from_intent=True` wins at
`execution_packets.py:249-256` and the profile's value is never read. The naive edit resolves to
**2.0 / TP 102,000**, while the spec, the diff and the commit message all say 5R. (The runtime logs
would correctly say 2R — an adversarial pass corrected me on that, and the direction matters: the
deception is in the source, not in the telemetry.)

**And the armed book's newest sleeve has an archive net expectancy of +0.041 R/trade.** `fx_jpy`
needs 73 fills to earn back the 3 R floor it would reach in 7.5 at the rate its own 32 live fills
ran at — **about 20× faster down than up**. That is not a forecast; it is the arithmetic of arming a
near-zero-expectancy sleeve, and it is why the pre-registered stop conditions this session built are
**risk bounds and not tests**.

Receipts under `phase11/receipts/`. **One file under `src/` was modified** — `execution.py`, to fix
a live `KeyError` on the adopt path that an adversarial pass found and that hits four of the five
armed sleeves (§0.8). Neither proposed exit-contract diff was landed. Nothing touched the VPS, no
broker-capable script ran, `config/agent_config.yaml` and `config/profiles/redacted_account.yaml` are
untouched. H1 drift is 2 `UNHYDRATED-LFS` at session start and 2 at session end — unchanged, and
`execution.py` is bound by none of the three seal mechanisms.

---

## 0. What was found, in order of how much it matters

**1. The obvious activation path for `mx_btcusd` is a no-op, and it fails silently.**
`final_from_intent=True` plus a generator that always sets `target_dist = 2.0 × risk`
(`market_expansion_d1.py:18`, `:223`) means `final_target_r` is computed from the intent and the
profile's own value at `:260` is unreachable. Proved by driving the real `build_book_trade_params`
under four profile states. The correct diff drops `final_from_intent` **and** sets 5.0; blast radius
**1 of 34** sleeves, **0 armed**. The generator route also works and moves **14**. Pinned by
`test_the_naive_mx_edit_is_a_noop`, which is a regression guard: if it ever starts *failing*, the
resolution order has changed and the dossier must be re-derived before anything lands.

**2. Neither change ends the parked B7.5 campaign option, measured across all three seal
mechanisms.** `execution_packets.py` and `market_expansion_d1.py` are in none of R2's 43
`input_bindings`, R1's 44, the runner's 21 `code_authority_paths`, or the two files in
`config_file_hashes` that feed `shared_execution_contract_digest_sha256`. **There is no owner
question to route here.** CLAUDE.md is explicit that the drift check alone is the wrong citation, so
all three were checked and the answer is pinned by a test.

**3. `sub_xvol_pullback @ target_4R` had never been judged at the rule that governs it — and at that
rule it is worth MORE and still rejects.** AK's frontier carries no population key and no
`spread_band` key: ALL_ERAS, flat band, family 69. Re-gated at RECORDED × 4 bands × the declared
family of 48 (48 arms, control reproduces AK's cell to the digit), the change is **+0.3435 R/day**
against +0.1301 at AK's standard — **2.6×** — and **REJECTS at every band**, raw p 0.007999 against
a rank-1 bar of 0.002083, **3.8× above it**. It also buys carry on the sleeve whose largest cost
term is swap (nights 4.27 → 6.46, median hold 92 → 123 h). **Recommendation: do not propose it.**
The binding constraint is sample.

**4. The "+1.157 R/day" everyone is quoting — including this session's own commission and
CLAUDE.md — is the LEVEL of the cell, not the improvement.** `as_walked` is 1.0264. The change at
AK's own standard is **+0.130**. Reading the level as the delta overstates it 8.9×.

**5. `fx_jpy`'s live record is a real loss and not a significant one, and both halves have to be
said.** 32 live fills, −9.269 R gross / −13.948 R net trade-weighted. On an exact sign-flip
permutation over **day** blocks, per account, it is distinguishable neither from zero (p 0.365 /
0.398) nor from the archive gross it was armed on (p 0.163 / 0.223). Thirty-two fills over thirteen
days cannot establish an edge in either direction.

**6. A gross-negative tripwire that reads only the trade weighting reports a sleeve's worst number
as its verdict.** The same 21 FTMO fills are −0.2487 R/fill trade-weighted and −0.1450 day-weighted
— a 42 % attenuation, because losing days carry four fills and winning days carry one. And pooling
the two accounts into one day block flips the pooled figure **positive**, which is an artifact of
the pooling. Both repairs are in the pre-registered conditions.

**7. All five armed sleeves' live time stops are unit-correct.** Four declare 1280 printed M15 bars,
which for these symbols is **measured at exactly 80 of their own bars** — the research `maxbars`
(AD's `m15_per_own_bar_trade_weighted` = 16.0; the same field reads 92 rather than 96 on three
`mx_*` sleeves, so the identity is a measurement and not arithmetic). `fx_jpy` is 48 of 80 with
0.2 % of trades truncated — a trade count whose R-weighted figure is ~20× larger, so "immaterial" is
fair for the count and generous for the economics. None is in the mis-scaled `mx_*` cohort. This is
the positive result of the contract-fidelity sweep and it belongs beside AQ's Side-B table, which
found ten sleeves where the answer is the other way.

**8. An adversarial pass found a live defect on armed money that is not mine, and this session
fixed it.** `execution.py:3003` read `params["trigger_r"]` unconditionally, but
`_vnext_time_stop_params` correctly returns no such key — so rehydrating **any** `time_stop`
position raised `KeyError('trigger_r')`. That is **four of the five armed sleeves**, and the live
caller (`book_owner.py:2729`) has **no try/except** on the authority-true branch. Fixed, with a test
that fails in exactly the four sleeves when reverted.

**9. The fleet is 18.8 machine-hours excluding the parked campaign, and its cheapest item is a
precondition for the next activation.** F15 — a read-only `copy_rates` probe on the two terminals,
0.2 MH — decides whether `mx_btcusd` can be armed at all, because after AQ's repair a short feed
makes its time stop **inert** rather than late. The parked campaign is 72× the cost of the item that
would move an armed sleeve.

---

## 1. AS-1 — the live five-sleeve book, monitored

Artifacts: `AS_LIVE_SLEEVE_BASIS_V1.json`, `FIVE_SLEEVE_STOP_CONDITIONS_V1.json`, the tool
`scripts/book_sleeve_telemetry.py`, the page `phase11/FIVE_SLEEVE_OPERATOR_PAGE.md`, 28 tests.

### 1.1 What the two newly-armed sleeves actually are

The expansion receipt says both were armed on explicit owner risk acceptance and that neither passes
an admission standard. It does not say what their expectancy is. Computed from AD's carry artifact
as `archive_gross − cost_ex_swap − swap_per_night × measured_nights_mean`:

| account · sleeve | archive net R/trade | risk floor | fills to earn it back | fills to reach it at the live prior |
|---|---:|---:|---:|---:|
| FTMO · `crypto` | +1.03128 | −12.38 | 12.0 | — |
| FTMO · `sub_xvol_pullback` | +1.24597 | −14.95 | 12.0 | — |
| FTMO · `energy_agri` | +0.43215 | −5.19 | 12.0 | — |
| FTMO · `sub_mid_dn_revert` | +0.23939 | −3.00 | 12.5 | — |
| **FTMO · `fx_jpy`** | **+0.04101** | −3.00 | **73.1** | **7.5** |
| **redacted_account · `fx_jpy`** | **+0.01905** | −3.00 | **157.5** | **6.0** |

The asymmetry in the last row is the point. The floor is a pre-registered price for finding out; on
`fx_jpy` that price is reached about 20× faster than the sleeve can earn it back at its own archive
rate. Nothing about that says the sleeve will lose — it says what it costs to be wrong about it, and
that number was not written down before.

`fx_jpy` is also a **zero-carry** sleeve: break-even **0.317 nights on FTMO, 0.051 on redacted_account**,
archive p90 zero nights, swap charged on 0 of its 32 live positions. One night of carry on one trade
in twenty ends the redacted_account edge.

### 1.2 The live-fill prior, and the two ways to read it

Only `fx_jpy` has ever filled live among the armed five. From the 2026-07-25 export — the only live
corpus on this machine:

| | FTMO | redacted_account |
|---|---:|---:|
| fills / day blocks | 21 / 13 | 11 / 8 |
| gross R/fill, trade-weighted | −0.2487 | −0.3679 |
| gross R/fill, **day**-weighted | −0.1450 | −0.1278 |
| net R total | −8.451 | −5.498 |
| closes | 15 sl · 5 tp · 1 expert | 9 sl · 2 tp |
| swap charged | 0 / 21 | 0 / 11 |
| **p vs zero** (exact sign-flip over day blocks) | **0.3652** | **0.3984** |
| **p vs the archive gross (+0.28235)** | **0.1631** | **0.2227** |

**The loss is real and it is not significant.** Both statements are true, they are about different
questions, and a monitoring tool that reports only one of them is lying by omission in one direction
or the other. The trade-weighted total is what left the account; the day-blocked permutation is what
that establishes.

Two instrument findings came out of this corpus:

- **The two weightings differ by 42 %** on the same fills, because losing days carry up to four
  fills and winning days carry one. The decision day is the dependence unit (Session R, lag-1 rho
  0.511). `CANARY_OPERATOR_PAGE.md`'s C3 reads only the trade weighting; S2 now requires **both**.
- **Pooling the accounts flips the sign.** The pooled day-weighted figure is **+0.0563** while both
  accounts are individually negative. Two independent books sharing a calendar day is not a block.
  I published the pooled figure in my own working notes before catching this; every figure in the
  artifacts is per account.

### 1.3 The stop conditions — and the one I got wrong first

A first cut had **one** floor at `-max(3.0, 12 × |expectancy|)`, justified by a claim about its
false-alarm rate that I had never computed. Computing it **refuted the claim**, and the refutation
is worth more than the original number:

| account · sleeve | risk floor | fires on a HEALTHY sleeve | evidence floor | its false-alarm rate |
|---|---:|---:|---:|---:|
| FTMO · `crypto` | −12.38 | 0.0 % | −12.38 | 0.0 % |
| FTMO · `energy_agri` | −5.19 | **35 %** | −11.19 | 10.5 % |
| FTMO · `sub_xvol_pullback` | −14.95 | 0.0 % | −14.95 | 0.0 % |
| FTMO · `fx_jpy` | −3.00 | **74 %** | −18.00 | 9.2 % |
| FTMO · `sub_mid_dn_revert` | −3.00 | **58 %** | −13.50 | 9.8 % |

Measured by bootstrap over each sleeve's **own** centred archive R distribution, 60-fill horizon,
20,000 draws, fixed seed — not assumed normal, because these distributions have a stop-out mass at
−1 R and a long right tail and a normal approximation understates the left tail exactly where the
question lives.

**The cause is structural, not a bad constant.** `fx_jpy`'s expectancy is +0.041 R/trade against a
per-trade dispersion of **1.611 R**. A near-zero-drift walk with that step size passes −3 R almost
surely. **There is no threshold on that sleeve that is both tight and sound** — and that is itself
the finding about arming a near-zero-expectancy sleeve.

So S1 is now two conditions. **S1a, the risk floor**, is a statement of the owner's tolerance and a
perfectly good one; it now carries its measured false-alarm rate on every trip, so nobody reads it
as evidence. **S1b, the evidence floor**, is the depth at which a trip means something. On `crypto`
and `sub_xvol_pullback` the two coincide — their expectancy dwarfs their dispersion. **The gap only
opens on the sleeves armed without a passed gate**, which is not a coincidence.

### 1.3b The rest of the conditions

Six plus the unchecked rule, all derived from a named basis field and pre-registered before any
post-arming fill exists. S1 the net-R floor; S2 gross-negative on both weightings; S3 carry against
measured p90 (alert) and break-even (stop); S4 hold time at 3× the archive median; S5 the stop-out
run at 6 (look) / 9 (act), calibrated from the live corpus's own 24-of-32 stop rate; S6 book
composition, which is first because nothing else means anything if it is wrong; S7 unchecked, which
exits 3 and never 0.

A first cut of S3 was `min(break_even, 2 × p90)` and collapsed to a degenerate **0.0** for a
zero-carry sleeve — the right answer for the wrong reason. Restated as `alert = p90, stop =
break_even`, with the zero-carry case named in the artifact.

### 1.4 The tool, and the thing it will not do

`scripts/book_sleeve_telemetry.py` is read-only: no MT5 import, no config write, no VPS. Against the
historical corpus it reports **0 post-arming fills, verdict UNCHECKED, exit 3** — the correct
answer, and it is pinned by a test, because "nothing is wrong" and "nothing was checked" are
different and collapsing them is how `.tools/monitor_books.py` sat mute through the window it was
meant to be watching.

The pre-arming prior never enters an evaluation, enforced rather than intended:
`test_pre_arming_losses_do_not_trip_any_condition` drives 40 pre-arming fills at −1 R each and
asserts every condition stays `UNCHECKED`.

**One defect in my own tool, found by its own test.** `signflip_p` enumerated 2ⁿ and returned
`p=None` above 20 day blocks — so *more* data would have produced a *weaker* statement, and 20 day
blocks is the normal case after a month of trading. Now exact to 20 and a **data-seeded** Monte
Carlo above, with the resolution floor reported always. Pinned by determinism,
boundary-agreement (|Δp| < 0.01) and shift-equivariance tests.

### 1.5 The de-arm procedure, and the half that costs money

Removing a sleeve from `--tags` stops **new generation only**. `book_engine.py:493` applies tags;
`book_owner.py:503` and `:2694` call `active_specs(None, …)` with tags **not** applied, so a
de-tagged sleeve's open position stays adopted and exit-managed. That is the safe direction and is
why de-arming needs no flatten.

But narrowing `--tags` mid-day does **not** reduce that day's conviction count:
`RunningConvictionLedger.update_and_count` unions the day's firing sleeves and `admission.py:1188`
takes `na = max(na, override)`. The other four keep the five-sleeve multiplier until the decision day
rolls. **De-arm at a day boundary if the size step matters.** And never reach for
`live_broker_authority: false` — H8: it returns before flattening and degrades routine exit
management to observe-only.

---

## 2. AS-2 — the exit-contract activation dossier

`phase11/EXIT_CONTRACT_ACTIVATION_DOSSIER.md`, machine sibling
`AS_EXIT_CONTRACT_ACTIVATION_V1.json`, 15 tests.

### 2.1 `mx_btcusd @ target_5R`

| | |
|---|---|
| **spec diff** | add an explicit `SLEEVE_EXIT_PROFILES["mx_btcusd_d1_donchian_20_breakout"]` entry with `final_target_r=5.0` and **no** `final_from_intent`; `time_stop_bars` stays at 7680 |
| **blast radius** | 1 of 34 sleeves, **0 armed** — measured by resolving every registered sleeve's `trade_params` before and after |
| **H1 / R2 / seal** | **unbound by all three mechanisms.** No owner question to route. |
| **token** | none. The token binds the *config* digest; this is source. No re-mint. |
| **rollback** | delete the entry; the cohort comprehension restores the default. A revert changes the next entry only — an open position keeps the broker-side TP set at entry (`execution.py:3488`). |
| **sizing basis** | **+0.1981 R/day**, the recent two folds — not the pooled 0.9817. |
| **precondition** | F15: measure the terminal's `copy_rates` ceiling first. A short feed makes the repaired time stop **inert**. |

The admission is an interaction: the time-stop repair alone is p 0.0064 (REJECT), the 5R target alone
under the old stop is p 0.0564 (REJECT), both together p 0.0011 (ADMIT). Any package citing the cell
must name the repair.

And the bill has moved since ratification: the declared family ratcheted **39 → 48**, so the BH
rank-1 bar goes 0.0025641 → **0.0020833** and the admission is **1.89× inside** rather than 2.33×.
It still admits.

### 2.2 `sub_xvol_pullback @ target_4R` — measured, and not recommended

**Control first.** AK's published cell reproduces here to the digit at ALL_ERAS / flat (R/day
1.1564749458527503, p 0.007799220077992201), so every difference below is the standard and not the
instrument.

| population | band | `as_walked` (= the live 3R contract) | `target_4R` | Δ | verdict |
|---|---|---:|---:|---:|---|
| **RECORDED** | mid | 1.0215 | 1.3651 | **+0.3435** | REJECT |
| ALL_ERAS | mid | 1.0438 | 1.1739 | +0.1301 | REJECT |

The delta is identical across all four bands, which is a check rather than a coincidence: the band
charges spread, both arms hold the same entries, so the spread term cancels in the difference.

It rejects on `significance`: q 0.384, raw p 0.007999 against a rank-1 bar of 0.10/48 = 0.002083 —
**3.8× above it**, not a near miss, on n 85 with 3 evaluable folds. It also moves swap nights
4.2692 → 6.4615 and median hold 92 → 123 h on the sleeve whose largest cost term is swap, and its
`maxbars` share goes **4/88 → 8/88** (the wave-12 delta: an exit sweep that does not report its
truncation share is quoting a frontier it has not priced).

**One thing worth having from this that is not about the change at all:** `as_walked` and the
sleeve's declared 3R target are the **same arm to the digit**. That is a live-contract fidelity
confirmation on armed money — this sleeve's walk baseline *is* what the book runs, so it does not
carry the labelling error AQ's Side-B table found on ten others.

---

## 3. AS-3 — the replay fleet map

`phase11/REPLAY_FLEET_MAP.md` and `AS_FLEET_MAP_V1.json`. **15 members, 54.8 MH total, 18.8
excluding the parked campaign** — the entire remaining fleet is less than one sealed month-window.

It is executable: it checks every driver path on disk and refuses to write if one is missing. **5 of
15 have a driver that exists; 7 need one written**, and that is usually the larger cost. The check
caught a bad path in this session's own first draft.

Top five by value per machine-hour:

| # | id | member | value | MH | value/MH |
|---:|---|---|---:|---:|---:|
| 1 | **F15** | measure the terminal's `copy_rates` ceiling before any `mx_*` arms | 5 | 0.2 | **25.0** |
| 2 | **F2** | restamp `SLEEVE_DOSSIER_V1.json`'s `time_stop_bars_m15` | 3 | 0.2 | 15.0 |
| 3 | **F4** | re-gate `sub_xvol_pullback @ target_4R` at the ratified rule | 5 | 0.4 | 12.5 · **done this session** |
| 4 | **F1** | rebuild the four artifacts on `sub_mid_dn_revert`'s repaired clock | 4 | 0.5 | 8.0 |
| 5 | **F14** | the RESERVE-account activation gate | 3 | 0.5 | 6.0 |

Three things the ordering says out loud, and they are in the document because an ordered list without
them is just a table:

- **the cheapest item is a precondition**, not a nice-to-have (F15);
- **the parked campaign is 72× the item that would move an armed sleeve** (F13 at 36 MH against F1
  at 0.5), and it cannot legally run until a pooled evaluator that does not exist anywhere is
  written and sealed;
- **the highest-value walkforward item is retrospective** (F6): re-gating published receipts at each
  sleeve's live exit contract is the only item that can change a number already in front of the
  owner.

The RESERVE gate is written as a **checkable condition** rather than a date — and the map says
plainly that until both accounts have ≥ 30 post-arming fills the condition is UNCHECKABLE, because
the honest time to write such a condition is before anyone wants to act on it.

One member is priced at **value 1**: F9, extending the hour-01 convention. AQ gated 72 arms at 0
admits, best p 0.3800. It is on the map because the commission named it, at what it is worth. A
fleet map that prices everything it is asked about at 4/5 is not a map.

---

## 4. Ledger, repairs, blocks, A/B

- **Trial ledger** — 48 rows, session `AS`, mechanism `xvol_exit_regate`
  (`research/operations/trial_budget/TRIAL_LEDGER.jsonl`).
- **Repair queue** — 8 rows appended, **179 → 187**, 0 collisions
  (`phase6/receipts/REPAIR_QUEUE_APPEND.jsonl`).
- **Blocks** — B1500–B1548 in `IMPLEMENTATION_STATE.md`; B1549 unused. No range borrowed.
- **A/B** — `phase11/SESSION_AS_AB.md`. Scoped to the 4 test files the change set reaches; copy-back,
  never `git checkout`, all 19 files sha-verified on restore. **0 bad → 0 bad, 0 regressed, 0 fixed**
  over the 2 shared files (17 passed on both sides), **+40 net new passing tests**. Full-suite A/B is
  the orchestrator's.
- **H1 drift** — 2 `UNHYDRATED-LFS` at start, 2 at end, unchanged. No bound file touched.

---

## 5. The adversarial pass

Six load-bearing claims went to verifiers instructed to refute and to default to "refuted" when
uncertain, each followed by an independent judge. **None was refuted outright; all six came back
CONFIRMED_BUT_NARROWER.** Between them they found:

- **one live defect on armed money** (§0.8 / B1535) — not mine, pre-existing, now fixed and pinned;
- **three defects in my own instruments** — `failing_gates` silently always empty because gate values
  are dicts and I tested `is False`; `maxbars_share` stamped from the pre-population row set; and a
  count rendered as authority (`n_code_authority_paths`) scraped rather than parsed, publishing 20
  where the tuple has 21;
- **a coverage gap**: my blast-radius instrument drove one of **two** production resolvers, and the
  other one is unguarded — under the naive edit the broker gets 2R and the rehydration payload gets
  5R. My own B1535 fix is what makes that divergence reachable;
- **four stale or overstated citations**, one of them dead code.

Every one is repaired in the published text or in the driver. Full detail at B1535–B1539 and B1548.
The corrections that change what a reader would conclude are in §6 below.

---

## 6. What I got wrong

**I read the pooled day-weighted `fx_jpy` figure as a finding before I split it by account.** My
first calculation put 32 fills into 13 day blocks keyed on `day_key_broker_server` **across both
accounts**, and got +0.0563 R/fill day-weighted against −0.2897 trade-weighted. I was about to write
that the day structure rescues the sleeve. It does not: per account both weightings are negative
(−0.1450 / −0.1278), and the positive pooled figure is an artifact of averaging two independent books
inside one calendar day. The attenuation finding survives and is real; the sign flip was mine.

**My own permutation test returned nothing in the case that matters most.** `signflip_p` enumerated
2ⁿ and gave up above 20 day blocks — so a book with two months of trading days would have got no p
at all, while a book with two weeks got one. More data producing a weaker statement is exactly
backwards. Caught by a test I wrote asserting that the power disclosure names its own floor; the
fix is exact-then-seeded-MC with the floor always reported.

**I wrote a stop condition whose formula collapsed to zero and was right by accident.** S3's first
cut was `stop = min(break_even_nights, 2 × p90)`. For `fx_jpy`, `p90` is 0 nights, so the stop became
"any carry at all" — which happens to be *approximately* correct for a sleeve whose break-even is
0.051 nights, and is arrived at by a term that has nothing to do with the reason. A threshold that
is right for the wrong reason is a threshold nobody can defend when it fires.

**My blast-radius driver raised on the case it was built to measure.** The first version asserted "no
candidate moves an armed sleeve" and died on `sub_xvol_pullback` — which *is* armed, and whose being
armed is the entire reason that change needs an owner decision. The assertion I wanted was "no
candidate moves a sleeve it does not name", plus `touches_armed_money` as a first-class reported
fact. A guard that cannot distinguish "the thing I am measuring" from "a defect" stops the
measurement.

**I quoted AK's `target_4R` figure as an improvement before checking it against `as_walked`.** The
commission says "+1.157 R/day frontier" and CLAUDE.md says "`target_4R` +1.157 R/day"; both are the
*level* of the cell. The improvement is +0.130 at AK's own standard. I inherited the phrasing and
would have republished it. The correction is in the dossier and in the repair queue, and the
re-derived number at the ratified rule (+0.3435) is larger anyway — which is not a defence of the
misreading, because it could as easily have been smaller.

**I initially cited `src/components/ultimate_book/exit_policy_v4.py` as unbound.** The bound path is
`src/components/exit_policy_v4.py` — a different file. My membership probe reported "unbound"
truthfully about a path that does not exist. The probe now enumerates the contract's own path list
rather than testing a hand-written candidate set against it, which is how the correct file was found.
The same class of error survived into the committed artifact for a second path
(`candidate_registry.py`, which lives under `sleeves/`) and an adversarial pass caught that one.

**I justified a stop condition with a number I never computed, and computing it refuted me.** The
S1 comment said the multiple was "the smallest under which a sleeve running at its OWN measured
expectancy has < 5 % chance of tripping on noise at n = 30 (see `power` below)". There was no
`power` below. The measured rate is **74 %** on `fx_jpy`, 58 % on `sub_mid_dn_revert`, 35 % on
`energy_agri`. A justification with a dangling forward-reference to a computation that does not
exist is worse than no justification, because it reads as measured.

**I said "every log would say 5R" and the logs would say 2R.** `build_book_trade_params` writes the
*resolved* value, so the runtime telemetry is correct and only the spec lies. I had the direction of
the invisibility backwards, on the sentence I called "the single most expensive thing on this page".

**I measured a blast radius through one resolver and called it the blast radius.**
`native_policy_instrumentation` is the second production consumer of the same dict and it does not
honour `final_from_intent`. My instrument could not have seen a divergence it was not looking at,
and "1 sleeve moves, 0 armed" was true of one code path stated as if it were true of the system.

**I asserted an identity as definitional that is measured** — "1280 printed M15 bars = 80 H4 bars".
It holds for the four armed H4 sleeves because those symbols print 16 M15 bars per H4 bar, and AD
measured that; it does not hold estate-wide (92, not 96, on three `mx_*` sleeves). Writing it as
arithmetic rather than as a measurement is the same conflation AQ spent a session repairing, one
wave later, by me.

**I justified the per-account split with a claim about independence that is false.** Ten of the
eleven redacted_account `fx_jpy` fills are the same signal as an FTMO fill 2–58 seconds apart, gross-R
correlation 0.9884. The split is still right — each account is its own book with its own costs and
its own floor — but I gave a statistical reason where only a bookkeeping one is available, and the
consequence is real: the two p-values I publish side by side are very nearly **one** test.

---

## 6. Handoff — for the orchestrator

1. **`mx_btcusd` activation is blocked on ONE cheap host read, and it is not a research question.**
   F15: measure the two terminals' `copy_rates` ceiling for M15. If either returns fewer than 7,680
   closed bars, an armed `mx_*` position has **no working time stop** — the backstop is inert, not
   late. 0.2 MH, read-only, orchestrator-executed, and it is the top of the fleet map.
2. **The `mx_btcusd` diff must drop `final_from_intent`, not just set `final_target_r`.** This is
   the session's headline and it is one line in a dict. `tests/ultimate_book/
   test_exit_contract_activation.py` carries the diff, its blast radius and the regression guard;
   apply it and the tests already describe what should happen.
3. **Do not propose `sub_xvol_pullback @ target_4R`.** REJECT at every band at the ratified rule,
   3.8× outside the rank-1 bar, on armed money, and it buys carry. Re-visit on sample. The re-gate
   is done and committed, so the next session need not re-run it.
4. **The five-sleeve monitoring is wired but UNFED.** `scripts/book_sleeve_telemetry.py` needs a
   `LIVE_TRADE_ROWS.jsonl` built from a post-arming VPS export. Until one exists the page correctly
   reports `UNCHECKED` / exit 3 — which is the tool working, not the tool idle. The first export
   after the first fills is what turns this on.
5. **Two published figures need correcting where they live.** CLAUDE.md's wave-8 bullet
   ("`target_4R` +1.157 R/day") states a level as an improvement; and the same bullet's framing of
   AK's frontier does not say it is ALL_ERAS at the flat band at family 69. Both are corrected in
   this session's dossier; neither is corrected at the source.
6. **The sparse-checkout gap is now two-for-two.** `research/operations/broker_truth_layer_2026_07_29`
   is absent from the committed sparse profile; AR hit it at B1473 and so did this session. The fix
   is one line in the profile and it saves the next worktree a failed run that reads like an
   expensive measurement.
7. **`execution.py`'s B1535 fix needs a deploy decision, and the books currently run the pre-fix
   code.** Adopting any open position of an armed `time_stop` sleeve raises `KeyError('trigger_r')`
   out of the book's adopt path on the host today. The file is unbound by all three seal mechanisms
   so there is no seal exposure, but it is a live-path change and taking effect needs the carry
   ceremony. **And one consequence to price before deploying:** the fix makes the adopt path reach
   the broker-TP modification it previously crashed before — intended behaviour for the armed five,
   with the values the packet builder wrote (pinned), but it is a behaviour change on live money.
8. **The fleet map is the scheduling input.** `phase11/REPLAY_FLEET_MAP.md` is generated, checks its
   own driver paths, and is ordered by value per machine-hour. F1 (0.5 MH) removes a by-hand
   substitution three sessions have had to remember about an armed sleeve; F6 (3 MH) is the only item
   that can change a number already in front of the owner.
