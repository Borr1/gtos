# Session AK — the sleeve-supply lane: four generators judged for the first time, and the armed sleeve nobody had swept

**Branch `phase8/sleeve-supply`. Blocks B950–B984. Not merged.**
**Scoped verification (agreement §2): 399 passed, 0 failed** — receipt in §9.

---

## 0. Headline

Four sleeves in this repository have a generator and **no entry in any of `sleeves/registry.py`'s
three `SleeveSpec` tables**, so `active_specs` can never return them and `GenerationPort` can never
drive them — and no **walk-forward gate** run in this programme had ever judged them (established
by receipt search: no phase3–7 gate receipt and no pre-AK trial-ledger row carries any of the four).
Three of them do carry recorded every-split economics and explicit quarantine verdicts from the
2026-06-17 principal audit (`candidate_registry.py:48-85`, `:209-223`), so read what follows as the
broker-true restatement of a recorded verdict rather than a first look. They are gated now:
**7,919 trades over the whole archive**, at each sleeve's own authored exit contract, in AA's own
32-sleeve family at AA's `declared_family_size = 69`.

| sleeve | n | gross R/trade | pooled OOS R/day | raw p | failing gates | best exit cell |
|---|---:|---:|---:|---:|---|---|
| `ny_index_momentum` | 465 | +0.2404 | **+0.0758** | 0.2281 | **significance ONLY** | `prerollover_flat_h22` **+0.1065** |
| `session_leadlag_genuine` | 919 | +0.2901 | −0.0415 | 0.6935 | all five | `trail_a2_g0.5_prod` −0.0282 |
| `vol_squeeze` | 1,490 | +0.2006 | −0.1960 | 0.9945 | four | `time_stop_12` −0.1068 |
| `structural_retest` | 5,045 | +0.1446 | — | — | NOT_EVALUABLE, coverage 58.0 % | no cell evaluable |

**But the largest thing this lane found was not one of them.** AD's exit sweep covered 25 of the
29 sleeves AA generated. Four had trades and **no exit frontier anywhere** — and one of them is
armed:

| sleeve | n | as-walked R/day | best cell | best R/day | failing at best |
|---|---:|---:|---|---:|---|
| **`sub_xvol_pullback` — ARMED** | 88 | **+1.0264** | `target_4R` | **+1.1565** | **significance ONLY** |
| `asia_pdl_fade` | 2,827 | −0.0686 | `stop_2.5x_tgtscale` | **+0.0846** | **significance ONLY** |
| `orb_crypto_london` | 858 | −0.1344 | `stop_3x_tgtscale` | −0.0254 | all five |
| `liq_asia_up_low_metal` | 157 | — | — | — | NOT_EVALUABLE |

`sub_xvol_pullback`'s raw p of **0.0061** is AA's, not mine — AA published it and I want that
stated before anything else in this document is read. What was missing was its **exit surface**,
and it turns out to be the sleeve with the highest pooled OOS R/day in the estate, on 88 trades
over 3 evaluable folds. AD's `WORK_LIST` is its own prompt's value order and simply did not name
it; nothing about it was excluded on evidence.

**`asia_pdl_fade` is the result that changes what the next session should do.** The estate's
largest first-of-day sleeve — 2,827 trades, which AA measured gross-positive at +0.196 R/trade —
goes from −0.0686 to **+0.0846 R/day with 5 of 5 OOS folds positive** on a single stop-width
change, and then fails **significance alone**. Neither AA nor AD had ever swept an exit on it.

Seven other things this lane settled:

1. **`structural_retest` carried the F7 clock defect, uncorrected, for four months — and an
   adversarial pass then found a second site that is worse, in `BUILT`, and I did not repair it.**
   The sleeve's session boundaries are the same pair `wave1_structure_setups_ict.session_id`
   (`:93-97`) mined on the broker-clock research archive — so they are **server** hours — and it
   compared them to true UTC. Repaired (B950), and it is not cosmetic: the bucket is this sleeve's
   whitelist key, so the repair changes **which trades exist** — 5,045 trades at +0.1147 R/trade
   gross against the unrepaired 6,474 at +0.0680, with only 3,620 shared.

   **My claim that it was the ONLY raw-UTC site was false (B971).** `substrate.py:75-84`
   `_utc_hour` returns the raw UTC hour and `substrate_engine.py:102-108` cuts it on the
   **identical** 8/16 boundaries. `sub_mid_dn_revert` is backed by that code, sits in
   `registry.py:55` `BUILT`, and carries `session=ny` as one of seven cell conditions. Measured:
   **185,548 of 370,808 H4 bars — 50.04 % — bucket into a different session**, at UTC close-hours
   05/06/13/14/21/22. Not costing money today (`sub_xvol_pullback` is built `need_hour=False`);
   one `--tags` change away. **Deliberately not repaired**: correcting it changes the sleeve's
   generated set and therefore its `SURVIVOR_BOOK_V1` carry tier and AD's B753 restatement — a
   re-derivation, not a port. Four tests pin it. My causal story was wrong too: per
   `IMPLEMENTATION_STATE.md:706-709` the F7 pass scoped by **config reachability**, not registry
   membership.

2. **The estate's only short-side mechanism now has economics.** 4,235 of `structural_retest`'s
   5,045 trades are SHORT, and all three of its authored whitelist cells are gross-positive:
   crypto-NY-short +0.0685 (n=3,644), metal-London-short +0.2103 (n=591), index-Asian-long
   +0.2525 (n=810). Neither account carries deliberate short exposure today.

3. **The sleeve that could be sized and could not fire now has a generator in this package, and it
   reproduces the MECHANISM — not the R.** `session_leadlag_genuine` (`admission.py:267-277`,
   conf 0.15). Its `LEGS` table is element-for-element identical to `LL_FWD`, and on the matching
   span it reproduces the population closely — **n 368 against the registry's 390, win
   34.9 %/35.2 % against 35.0 %/36.7 %**. It does not reproduce the R, and an adversarial pass on
   my own claim is why that is stated: the registry's +0.46 is **net** of the legacy flat-R cost
   model and my +0.4986 was **gross**, and 2025-06-01 is KB5's coverage start rather than its
   declared `year >= 2025` window. §5.3 has the common-basis numbers.

4. **A correction to AF's own instrument — and my own first version of it was wrong, which is the
   more useful half.** AF's two-clause coherence test is computed on per-member **gross** R
   (`af_repairs.py:820`). Measured over the **identical row population**, **5** sleeves and cells
   cohere on gross and do not cohere on net: `vol_squeeze`, `ny_index_momentum`,
   `session_leadlag_genuine`, and the crypto and index `structural_retest` cells. My first draft
   said 8, because it read gross from the trades and net from `diagnostics.by_symbol` — different
   populations, since the gate drops the 2026-03 `reserved_blackout` rows from the priced set and
   `coverage_frac` excludes blackout drops from its denominator, so a cell reads coverage 1.00
   while up to 18 % of its rows never reach the net basis. One "flip" was purely that artifact and
   two more are k=1 degenerate cells. My causal story was wrong as well: within these sleeves the
   stop rule is one symbol-agnostic ATR constant and the data invert the R-unit explanation —
   XAUAUD's *tighter* stop pays 0.10 R against XAGAUD's 0.53 R. The fix is one field: the gate
   already emits `mean_gross_r` beside `mean_net_r` over identical rows.

5. **A pre-declared cell decomposition turns a coverage refusal into verdicts.**
   `structural_retest` is NOT_EVALUABLE at 58.0 % coverage and no exit change can move that — all
   59 cells return NOT_EVALUABLE, which is the sweep confirming it rather than me asserting it.
   Its three whitelist cells are declared in its own source and two are fully priceable; all three
   are gated. Same for `session_leadlag_genuine`'s four declared legs, and there the answer is
   sharp: **one leg of four carries it.** `US30_cash->USDJPY@T2.0` is +0.2774 R/day at p 0.113
   failing significance alone, and **+0.5637 at `stop_1.5x_tgtscale`** — the stop-width
   prescription confirmed on the leg it was prescribed for.

6. **A latent generator defect worth 24 % of a trade set.** `structural_retest._htf_trend_at`
   (`:82-103`) chunks its HTF blocks from index 0 of the **window**, so which absolute bars it
   reads depends on `bar_count mod 16`. Measured at 513 against 528 on three symbols: **jaccard
   0.759**, 169 trades only at 513 and 79 only at 528. `bar_count` is not a free parameter for this
   generator. Two things I first said about it and withdrew (B964): 513 is the **smallest** aligned
   length above the `MIN_BARS = 512` floor and not the only one — every `bar_count ≡ 1 (mod 16)` is
   aligned — and the phase changes **trade/no-trade, not direction**, because each
   `(class, session)` appears once in `WHITELIST` and the direction flips on 0 of the 782 shared
   bars. Filed, not repaired: fixing the chunking changes the rule the three whitelist cells were
   verified under.

7. **The single most live-relevant thing in the session, and it was incidental.** A sleeve the
   sizer **refuses** as `unknown_sleeve` is still counted in the Kelly-lite conviction breadth and
   still sizes every other unit that day **up by 32.49 %**. `admission.py:1143-1148` counts
   distinct sleeves across all of today's intents, `:1163-1165` refuses the unknown one afterwards,
   and `precount_intent_filter` — "the ONE definition of the DROPPING pre-count filters" — has no
   known-sleeve check. Measured in `book_replay` against the armed three: 13/31/35/21 of 162
   placements resized, **all upward**. Not live-reachable today (B325: generation and sizing
   resolve the same set); reachable the moment a generation spec lands without the matching
   confidence weight — **which is exactly the registry edit AA §4 routed and I am re-proposing**.
   Two tests pin it (B970).

**Nothing admitted.** 0 of 4 new sleeves, 0 of 7 cells, 0 of 4 gap sleeves. That is not the
headline and §8 is why: every one leaves with a prescription that has a number attached, **six** of
them fail **significance alone** at their best cell — which no exit change can pay, and which is the
owner decision AF §11 already routed, now with six customers instead of one (§6 item 3) — and two
leave with an exact data capture.

**What I got wrong is in §7, and there are four.** One of them I found by reading my own output,
two by an adversarial pass over my own claims, and one by a sibling session's test going red.

---

## 1. What was built

Everything is additive. `sleeves/registry.py` is **untouched** — FTMO is armed, and adding a spec
there changes what `active_specs` resolves for everything that reads it.

### 1.1 `walkforward/supply.py` — research-side specs for generators the production path cannot reach

A `ResearchSleeveSpec` carries the five facts a `SleeveSpec` carries plus four the live one does
not: the **authored exit contract** (none of the four has a `SLEEVE_EXIT_PROFILES` row, so each
sleeve's own docstring is the only statement of what its research validated), the provenance with
`file:line`, why the production path cannot reach it, and an exact **prefilter**.

The driver walks bar series directly and calls the production generator, which is AF's measured
approach (`SESSION_AF_FAMILY_EXPANSION_RESULT.md` §1: 10 of 10 trade counts and median holds exact
against `W_MX_PILOT.json`) applied to sleeves in no registry rather than symbols in no registry.

**The prefilters are necessary conditions and the exactness is measured, not argued.**
`structural_retest` costs O(window) per decision bar — a 513-long ATR list plus a 513-step HTF
chunking — against 2.7 M M15 bars, so a naive walk is hours. Each spec therefore carries a cheap
predicate evaluated from full-series arrays. The safety argument is that `atr14` reads only
`bars[j-14 .. j]` (`primitives.py:23-30`), so any window index ≥ 14 sees the same number the
generator will. That is an argument, so the driver additionally walks one real symbol per spec
with the prefilter **disabled**:

| spec | parity symbol | with prefilter | without | identical trade sets |
|---|---|---:|---:|---|
| `vol_squeeze` | US30_cash | 367 | 367 | **yes** |
| `ny_index_momentum` | SPX500 | 79 | 79 | **yes** |
| `structural_retest` | XAUUSD | 77 | 77 | **yes** |
| `session_leadlag_genuine` | AUDJPY | 1,178 | 1,178 | **yes** |

`REGISTRY_EDIT_PROPOSAL` publishes the one-line edit AA §4 routed to Borhen as **data** — table,
exact line, what else it needs, why it is live-safe — so this document and the receipt cannot
disagree about what is being proposed. `LIVE_WIRING_GAP` records what `session_leadlag_genuine`
would need, which is §1.2's finding.

### 1.2 `sleeves/session_leadlag.py` — the generator, and why it was never a one-line edit

`session_leadlag_genuine` has been registered and sizeable since wave 6 and had no generator, so
it could be sized and could never fire. AA §2.6 called it *"the estate's only artifact with no
evidence of any kind reachable from this machine."*

**It was not an oversight.** Every other sleeve in the package is a function of one symbol's own
bars. This one reads a **leader** instrument and trades a **follower**, and the generator contract
(`registry.py:37`) hands a generator one symbol's bars plus at most one `aux_*` feed that
`bar_provider` fills from *the same symbol* at a second timeframe — `vp_euidx`'s M1 volume profile
is the only user. **There is no cross-symbol channel in the generation path at all.** So wiring
this sleeve was never a registry edit; it needs a feed the engine does not have. The smallest
sufficient change is in `supply.LIVE_WIRING_GAP` and it is an owner decision, not a research one.

The generator takes the leader feed as an explicit keyword and **returns None when it is absent**,
which makes it live-safe by construction: registered before the engine can supply leaders, it
emits nothing rather than something wrong.

The mechanism is `KB6_session_stacks.py:52-58`'s four `LL_FWD` legs driving
`KB5_leadlag_subh4.py:145-185`, verbatim, with two deliberate departures, both stated in the
module docstring and both published as A/Bs: the session gate is on the **server** clock (KB5's
own `_session_ok` comment calls its windows "winter UTC" and its data is broker wall clock), and
`min_gap` is applied by the driver rather than remembered by the generator, because a generator
that remembered its own last fire would not be a pure function of the decision bar and every
leak-freedom claim in this package rests on that.

### 1.3 The F7 repair `structural_retest` never got

`_server_clock`'s docstring states the rule for the whole package: *"Every sleeve in this package
was mined on the broker-clock research archive, so each `DECISION_HOUR` / `ASIA_*` / `LONDON_*`
constant in them is an **FTMO server** hour."* Nine sleeve files import it.
`structural_retest.py:47-53` did not — it returned `t.hour` — and its `_session` boundaries (8, 16)
are a verbatim port of `wave1_structure_setups_ict.session_id:93-97`, which read `t.hour` off the
research CSV archive. So the sleeve compared true UTC to a server constant: 2 h out in winter, 3 h
in summer.

Why the B29/B54 pass missed it: those nine are all in a production registry and this one is not,
so it was never in the deployed set the repair enumerated.
`tests/ultimate_book/test_sleeve_server_clock.py` covered the nine and omitted this one; it now
covers it, at both DST seasons, and asserts the two boundary hours land in **different** buckets
under the two clocks — because the bucket is this sleeve's whitelist key, so a shifted bucket
changes whether a bar can trade **and in which direction**.

### 1.4 `fidelity.py` — a harder absence than any existing entry carries

The four sleeves were not in the fidelity register, so `fidelity_for` returned UNMEASURED and the
gate refused all four for a reason that has nothing to do with fidelity. They are added to
`_STRUCTURE_BY_CODE` with their class read from the generator and a citation — and with a stamp
that says something no existing entry says:

> THIS SLEEVE HAS NO LIVE PATH: it is reachable from no production generation registry, so there
> has never been a cycle in which the live engine could call it and its live record is
> structurally EMPTY rather than thin.

That is harder than `vss_fxcross_london_up_low`'s caveat ("registered, but all 55 of its live rows
are generation-side refusals"). The class rate is still transferred, for the same reason the
fifteen authored `mx_*` specs and every `register_surface_expansion` member get it — the rate is a
claim about how faithfully a code path of that *shape* reproduces live decisions — and the stamp
travels into every verdict so the two cannot be confused. A test asserts the stamp is confined to
exactly those four and that no registered sleeve carries it.

---

## 2. What the walk measured

**7,919 trades in 212 s** over the FTMO archive: H4 2018-2026 for `vol_squeeze`, M15 2024-2026 for
the other three (the M15 archive begins 2024-01-02, which is §8's binding constraint on two of
them).

Two labellings per trade, and the second is the one that matters:

* `r_gross` — the sleeve's **authored** exit contract;
* `r_gross_plain` — stop/target/MAXBARS-80, AA's and AF's convention.

AD §6.2 measured retrospectively that the live contract and the plain labelling differ materially
on 15 of 25 sleeves and that nobody had checked. Asking it at generation time costs nothing:

| sleeve | authored contract | authored R/trade | plain R/trade | authored − plain |
|---|---|---:|---:|---:|
| `ny_index_momentum` | `time_stop` 20, no target | +0.1996 | +0.0221 | **+0.1774** |
| `session_leadlag_genuine` | per leg (3× 4R target, 1× trail), 64 bars | +0.2925 | +0.1143 | **+0.1782** |
| `structural_retest` | 2R + `time_stop` 32 | +0.1147 | +0.1202 | −0.0055 |
| `vol_squeeze` | fixed 3R target, no time stop | +0.2105 | +0.2105 | **0.0000** |

`vol_squeeze`'s zero is correct rather than a bug: its authored contract *is* target + MAXBARS, so
its numbers are directly estate-comparable — the same property AD found for every H4 sleeve. The
other two are the AD §6.2 shape found before anything was published about them.

### 2.1 The clock A/B, which changes which trades exist

| sleeve | repaired (server) | authored (raw UTC) | shared |
|---|---|---|---:|
| `structural_retest` | n=5,045, +0.1147 R/trade, ΣR +578.5 | n=6,474, +0.0680, ΣR +440.0 | 3,620 |
| `session_leadlag_genuine` | n=919, +0.2925, ΣR +268.8 | n=2,965, +0.0336, ΣR +99.5 | 315 |

Read the second row: an unrepaired `session_leadlag_genuine` would have traded a **3.2× larger,
essentially edgeless** population, sharing only 315 of 919 trades with the rule the research
validated. The repaired reading is primary because the server clock is the clock the rules were
mined on; both are published because the *unrepaired* reading is what a live sleeve would have
done, and that is worth knowing about a sleeve that is registered for sizing.

### 2.2 The three whitelist cells, and the side the estate does not trade

`structural_retest` is 4,235 SHORT against 810 LONG. Its three authored cells, at gross:

| cell | direction | n | R/trade gross | member coherence (gross) |
|---|---|---:|---:|---|
| crypto · NY · dn · high | **SHORT** | 3,644 | +0.0685 | on the priceable 3: ratio 0.042, 3/3 positive |
| metal · London · dn · high | **SHORT** | 591 | +0.2103 | on the priceable 6: ratio 0.681, 6/6 positive |
| index · Asian · up · high | LONG | 810 | +0.2525 | ratio 0.808, 6/6 positive |

As **one** 23-member family the sleeve is a mixture (ratio 1.053, not all positive) — which is the
coherence test correctly diagnosing that it pools three different mechanisms. Split into the cells
its own source declares, each coheres on gross. §4 is what happens at net.

### 2.3 The HTF window-phase defect

`_htf_trend_at` (`structural_retest.py:82-103`) iterates from index 0 of the window in 16-bar blocks
and sets `completed_at_i` **before** appending the block bar `i` closes, so the reference block is
`[16·(⌊i/16⌋−1), 16·⌊i/16⌋−1]` in **window** coordinates — exact for every window length in
[513, 4000), 0 mismatches. Which ABSOLUTE bars that is depends on `bar_count mod 16`: the block ends
adjacent to the decision bar iff `bar_count ≡ 1 (mod 16)`, and 16 bars earlier when
`bar_count ≡ 0 (mod 16)`.

Measured over the real archive on BTCUSD, XAUUSD and SPX500: **951 trades at 513, 861 at 528, 782
shared — jaccard 0.759.** 169 exist only at the aligned phase and 79 only at the misaligned one. So
the same bar is traded or not traded on nothing but how much history the caller supplied.

**Three things about this that a first draft claimed and that are withdrawn** (§7.4), because each
would have cost a reader something:

* **513 is the SMALLEST aligned length above the `MIN_BARS = 512` floor, not the only one.** Every
  `bar_count ≡ 1 (mod 16)` is equally aligned — 529, 545, 561, … — which follows from 512 being
  32 × 16. Anyone needing a longer warmup has not lost the alignment.
* **The phase changes trade/no-trade, not direction.** Each `(class, session)` appears exactly once
  in `WHITELIST`, so a fixed bar can match at most one regime; measured, the direction flips on **0**
  of the 782 shared bars.
* **"the last completed H4 block" overstates what 513 restores.** The block is a rolling 16-bar
  aggregate ending at `i-1`; it starts on a calendar H4 open on only **6.5 %** of those 951 trades
  and is not even 16 contiguous M15 bars on **9.8 %** (spanning up to 3,405 minutes across a
  weekend). There is no HTF grid here to align to, so no repair should be scoped as restoring one.

**Not repaired**, and the reason is the line between a port and a re-derivation: anchoring the
chunking on `i` is two lines, and it changes the rule the three whitelist cells were verified under.

## 3. The exit frontiers — 881 cells gated, 764 of them evaluable, over 15 sleeves and cells

Every sweep here is AD's `plan_for` / `resimulate` / `summarize`, **imported** rather than
reimplemented, so any difference between this frontier and AD's is a difference in the sleeve and
not in the instrument. `AK_EXIT_FRONTIER_V2.json` uses AD's schema so the two concatenate.

**"Gated" is 881 and "produced a metric" is 764**, and the difference is not noise: 117 cells came
back NOT_EVALUABLE — all 59 of `structural_retest`'s and all 58 of `liq_asia_up_low_metal`'s,
because a coverage or sample refusal is a property of the population and no exit change moves it.
Both counts are stated because "881 gated" alone reads as 881 answers.

**And the stop-width cells are a legitimate re-simulation here, checked per sleeve rather than
inherited.** The agreement calls stop width a *generation*-level repair, and AD established per
sleeve that its own set's entry signals do not read the stop. Re-checked for the four gap sleeves:
`asia_pdl_fade:108`, `liq_asia_up_low_metal:192,205` and `orb_crypto_london:115` all compute the
stop AFTER every gate, and `substrate.py:112` takes it from `(stop_atr, target_R)` after
`cell_matches`. The only test on the value anywhere is `orb_crypto_london:116`'s `stop_dist <= 0`,
which scaling by k > 0 preserves — AD's `vss_fxcross` argument, verbatim. So a k× stop changes the
geometry of the same candidate set and nothing else.

### 3.1 AD's gap, closed — and one of the four is armed

The gap is **computed**, not transcribed: the sleeves with `n > 0` in `AA_ESTATE_TRADES.json.gz`
minus the sleeve keys in `EXIT_FRONTIER_V1.json` and `EXIT_FRONTIER_V1_TRAIL.json`.

**`sub_xvol_pullback` is armed and trading real money, and its exit surface was the largest
unmeasured one in the estate.** AA measured its capture ratio at 0.604 — the best of any sleeve —
and its pooled OOS at +1.0264 R/day on raw p 0.006099. Its frontier:

| cell | pooled OOS R/day | failing |
|---|---:|---|
| `target_4R` | **+1.1565** | significance |
| `as_walked` / `target_3R` / `partial_3R_be` / `partial_3R_nobe` | +1.0264 | significance |

+0.130 R/day from widening the target, at raw p 0.0078 (against 0.0061 as-walked — the mean rises
and the p **worsens**, which is why the two must not be quoted from different cells), drop-best
retention 0.639, coverage 1.00, and **n = 88**.

**The fold arithmetic needs stating because the artifact looks self-contradictory and is not.**
`n_folds_evaluable` is **3** while `oos_positive_fold_frac` is **0.75** — a fraction that cannot
have 3 as its denominator. The gate's `sample` gate counts a fold evaluable only if it clears the
per-fold trade floor, while `stability` divides by every OOS fold and counts a thin one as
non-positive (`gate.py:680-687`). So it is 3 positive of 4 OOS folds, of which 3 are evaluable. The
thinness is the whole caveat, and §7.5 is why the comparison to `mx_btcusd` was withdrawn rather
than softened.

**`asia_pdl_fade` is the one a next session should pick up.** 2,827 trades, the largest
first-of-day sleeve, gross +0.196 R/trade in AA's walk, and it had no exit frontier:

| cell | pooled OOS R/day | OOS folds positive | retention | failing |
|---|---:|---:|---:|---|
| `stop_2.5x_tgtscale` | **+0.0846** | **5/5** | 0.554 | **significance** |
| `stop_3x_tgtscale` | +0.0757 | — | — | significance |
| `stop_2x_tgtscale` | +0.0433 | — | — | lifetime, robustness, significance |
| `as_walked` | −0.0686 | — | — | all five |

A single stop-width change is worth **+0.1533 R/day** and takes every OOS fold positive. Its
coverage at the best cell is 0.812, so it runs on its priceable subset under option B, stamped.
`orb_crypto_london` improves +0.109 to −0.0254 and stays negative on every gate;
`liq_asia_up_low_metal` (n=157) is NOT_EVALUABLE at every cell, so its blocker is the population
and not the exit.

### 3.2 The four new sleeves

| sleeve | as-walked (plain) | best cell | best R/day | Δ | failing at best |
|---|---:|---|---:|---:|---|
| `ny_index_momentum` | −0.1301 | `prerollover_flat_h22` | **+0.1065** | +0.2366 | **significance** |
| `session_leadlag_genuine` | −0.1666 | `trail_a2_g0.5_prod` | −0.0282 | +0.1384 | all five |
| `vol_squeeze` | −0.1960 | `time_stop_12` | −0.1068 | +0.0892 | expectancy, stability, robustness, significance |
| `structural_retest` | — | — | — | — | NOT_EVALUABLE at every one of 59 cells |

`ny_index_momentum`'s top five cells are all ≥ +0.100 and four of the five fail significance
alone, which is a plateau rather than a spike: `prerollover_flat_h22` +0.1065, `time_stop_12`
+0.1046, `target_5R` +0.1028, `prerollover_flat_h0` +0.1020, `flat_before_every_rollover` +0.1008.

`vol_squeeze`'s best cells are all carry cells (`time_stop_12`, `time_stop_16`,
`flat_before_triple_swap`), which is the right shape — swap is **86 %** of its cost (0.1722 R of a
0.1996 R total) on a 48 h median hold. But carry is not its whole problem and I want to be exact
about that: at the best cell it still fails **expectancy, stability and robustness**, with 1 of 5
OOS folds positive. Its edge lives in one fold. So the honest prescription is carry **then**
regime, and the carry half is measured while the regime half is a next step.

`structural_retest` returning NOT_EVALUABLE at all 59 cells is the measurement that says its
blocker is the population: an exit change cannot move a coverage refusal, and now that is a
receipt rather than an argument.

### 3.3 The per-cell frontiers, where the parent could not be swept

| cell | as-walked | best cell | best R/day | Δ | failing at best |
|---|---:|---|---:|---:|---|
| `fam_session_leadlag_us30_cash_usdjpy_t2.0` | +0.2774 | `stop_1.5x_tgtscale` | **+0.5637** | +0.2863 | **significance** |
| `fam_session_leadlag_us30_cash_ger40_trail` | −0.6653 | `trail_a2_g0.5_prod` | +0.0830 | **+0.7482** | robustness, significance |
| `fam_session_leadlag_us30_cash_audjpy_t2.0` | −0.0818 | `stop_3x_tgtscale` | +0.0808 | +0.1626 | lifetime, robustness, significance |
| `fam_session_leadlag_usdjpy_audjpy_t2.0` | −0.1013 | `stop_1.25x_tgtfix` | −0.0453 | +0.0560 | four |
| `fam_structural_retest_index_asian_long` | +0.0113 | `target_5R` | +0.0461 | +0.0348 | robustness, significance |
| `fam_structural_retest_metal_london_short` | −0.2521 | `stop_2.5x_tgtscale` | **+0.1875** | **+0.4396** | robustness, significance |
| `fam_structural_retest_crypto_ny_short` | −0.3631 | `stop_3x_tgtfix` | −0.1854 | +0.1776 | all five |

The first row is the stop-width prescription confirmed on the leg it was written for: widening
KB5's `0.5 × ATR` stop by half **doubles** the leg's R/day. The second row's as-walked is the
plain labelling and this leg's authored geometry is the trail, so `trail_a2_g0.5_prod` is its own
contract rather than a repair — the +0.748 is the size of the mislabelling, not of a fix, and it is
the same trap AD §7.2 recorded for the two `trailing_runner` sleeves.

---

## 4. The correction to AF's coherence test — and to my own first version of it

AF §0 leaves one rule behind: before spending a session on breadth, check the members **agree**
(dispersion ratio `sd/|mean| < 1`) **and** that what they agree on is **positive**. Exactly 2 of
AF's 30 families passed it. It is computed on per-member **gross** R (`af_repairs.py:820` builds
`[r["r_gross"] for r in … if r["engine_reachable"]]`; the artifact key is `member_mean_r_gross`).

Run here on both bases over the **identical row population**:

| sleeve / cell | k | gross ratio | gross all + | net ratio | net all + | flip |
|---|---:|---:|---|---:|---|---|
| `vol_squeeze` | 5 | 0.394 | yes | 44.84 | **no** | **yes** |
| `ny_index_momentum` | 6 | 0.537 | yes | 0.866 | **no** | **yes** |
| `session_leadlag_genuine` | 3 | 0.613 | yes | 4.93 | **no** | **yes** |
| `fam_structural_retest_crypto_ny_short` | 3 | 0.168 | yes | 0.331 | **no** | **yes** |
| `fam_structural_retest_index_asian_long` | 6 | 0.780 | yes | 1.101 | **no** | **yes** |
| `fam_structural_retest_metal_london_short` | 6 | **1.502** | **no** | 1.499 | no | no — see below |
| `structural_retest` (as one 15-member family) | 15 | 1.138 | no | 48.27 | no | no |
| four single-member legs | 1 | 0.0 | — | 0.0 | — | degenerate |

**Five genuine multi-member flips.** Every sleeve that coheres on gross stops cohering once broker
truth is charged.

### 4.1 My first version said eight, and the difference is a confound I told a refuter to look for

The first draft read gross from the trades and net from `diagnostics.by_symbol`. Those are
**different populations**: `by_symbol` covers `status == "priced"` trades only, and the trades
include the rows the gate drops for the default 2026-03 `reserved_blackout` (`spec.py:98`,
`panel.py:242-249`). Nothing warns you, because **`coverage_frac` excludes blackout drops from its
denominator** (`panel.py:313,323`) — so a cell reads `coverage_frac 1.00` while up to 18 % of its
rows never reach the net basis.

On `fam_structural_retest_metal_london_short` that mismatch **manufactured a flip**: 76 of its 416
rows are March-2026, and on the matched population its gross ratio is **1.502 with 3 of 6 members
negative**, so it does not cohere on gross either and was never a flip. Two more of the original
eight are k=1 cells where `sd = 0` makes the test pass vacuously. And `structural_retest` itself is
not among the flips — it fails on gross too.

The fix was one field away the whole time: `by_symbol` already emits `mean_gross_r` beside
`mean_net_r` over identical rows (`diagnostics.py:316-317`). Both readings are published — the
matched pair is authoritative and the unmatched one is kept under
`gross_basis_unmatched_population` so the correction is visible rather than overwritten.

### 4.2 And my causal explanation was wrong in the direction that mattered

I wrote that cost in R scales inversely with the R unit, so a tight-stop member pays several times
what a wide-stop member pays. Within a sleeve that is not what happens: the stop rule is one
**symbol-agnostic ATR constant** (`structural_retest.py:126-163` returns
`max(structural + STOP_BUF*a, ATR_STOP_FLOOR*a)` for all 23 members), so there is no tight-stop
member. And the data invert the ordering — `structural_retest`'s XAUAUD has the *tighter* relative
stop and pays **0.10 R** against XAGAUD's **0.53 R**; `ny_index_momentum`'s **widest**-stop member
(JP225) is its **most expensive**. The spread is the instrument's own spread and swap drag.

**What the correction does not do:** it does not move any of AF's published verdicts. AF's
repair-queue routing already read the mean's sign as well as the ratio, so no AF row changes. What
changes is the prescription a reader carries away — and the honest version is smaller and sharper
than my first one: **run the two-clause test on the `mean_gross_r`/`mean_net_r` pair the gate
already emits, never on gross-from-trades against net-from-diagnostics.**

## 5. The three sleeves whose story is not "reject"

### 5.1 `ny_index_momentum` — significance alone, and the blocker is archive depth

+0.0758 R/day at the authored contract, **+0.1065** at `prerollover_flat_h22`, raw p 0.1513 at the
best cell, 5 folds evaluable, **80 % of OOS folds positive**, drop-best retention 0.850, cost
coverage 1.00, spread the largest cost term at 0.0711 R against a 0.2404 R gross.

Significance is not an exit question and it is not a breadth question either: the sleeve already
pools six indices and they cohere on gross. **What binds is n = 465 against the research's own
pooled n = 863**, and the reason is that the M15 archive begins 2024-01-02.

**The ask is exact:** M15 bars for SPX500, GER40, UK100, US30_cash, NAS100 and JP225 before
2024-01-02 — one read-only export of the shape that already ran on 2026-07-27. At the authored
contract's p 0.2281 it admits under BH α = 0.10 against a family of **0** looks, so depth is the
only lever; at the best cell's p 0.1513 the same is true. This is the cheapest thing in this
document that would move a verdict.

### 5.2 `structural_retest` — a capture, not a decision

NOT_EVALUABLE at **58.0 %** cost coverage. Eight of its 23 symbols have no file in the tick
archive, so `cost_r` refuses them and the retained fraction falls under the 60 % floor:
**ADAUSD, DOTUSD, LTCUSD, XCUUSD, XPDUSD, XPTUSD, XRPUSD, XTZUSD** — 2,112 trades. (The artifact's
ask list carries a ninth name, `AUS200_cash`, which is on the index cell's authored surface and has
no bars in the archive either — a different gap, and the artifact records the reason per symbol.)

That is a **spread capture**, not a commission question, which makes it materially cheaper than
`energy_agri`'s NATGAS blocker (AF §3.3, where no re-run or capture would help because the
commission is unknown with no peer to transfer from). The same read-only VPS tick export that
produced `vps-ticks-20260726` closes it.

Meanwhile the cells are gated, and the honest reading of them is:

| cell | n (priceable) | pooled OOS R/day | raw p | failing | prescription |
|---|---:|---:|---:|---|---|
| index · Asian · up · high | 810 | **+0.0228** | 0.3896 | robustness, significance | `REGIME_GATE_OR_PARK` |
| metal · London · dn · high | 416 | −0.2517 | 0.9651 | all five | `COST_GEOMETRY` |
| crypto · NY · dn · high | 1,707 | −0.3869 | 1.0000 | all five | `COST_GEOMETRY` |

**The two SHORT cells are gross-positive and net-negative, and the gap is cost on a tight stop** —
the same shape as `session_leadlag_genuine`.

**The index LONG cell is the only one that survives costing, and it is the false positive a careful
reader should name.** Its drop-best retention is **−1.371** as-walked and **−1.273** at its best
cell — negative retention means dropping the single best OOS fold takes the pooled mean below zero
by more than its own magnitude, so the entire +0.0228 / +0.0461 is **one fold**, on 3 of 5 folds
positive. A completeness pass over this session flagged it as the thing a reader would call a false
positive, and it was right: the number was published in §5.2 and handed to AH in §6.5 without the
retention figure. It is not a small caveat — it is the difference between "the cell survives
costing" and "one fold does".

**The restriction is stated because it is a narrower hypothesis than the cell.** For the crypto
cell it is large: 3 of 8 symbols and 1,707 of 3,644 trades. Priceability is outcome-independent —
it is a property of what was captured, never of what it returned, which is the argument
`coverage_policy="restrict_to_priced"` rests on and the one AF used for `era_class == RECORDED` —
but a reader must be able to see that the crypto verdict is about BTCUSD/ETHUSD/DASHUSD and not
about eight crypto instruments. Every dropped symbol and count is in the artifact.

### 5.3 `session_leadlag_genuine` — the generator reproduces the mechanism; the registry's economics do not survive cost-true measurement

**What reproduces, and it is the load-bearing claim.** The `LEGS` table
(`session_leadlag.py:114-123`) is element-for-element identical to `LL_FWD`
(`KB6_session_stacks.py:52-57`), and the trade population reproduces closely on the matching span:
**n 368 against the registry's 390**, win **34.9 %** (2025) and **35.2 %** (2026) against the
registry's **35.0 %** and **36.7 %**. Two code paths, different data, the same mechanism and the
same population.

**What does not reproduce, and my first draft claimed it did.** An adversarial pass over this very
claim found the asymmetry, and then a second one my own §7 had not caught:

* **Basis.** `KB5_leadlag_subh4.py:150,178-182` passes `cost=cost_for(follower)` into `simulate`,
  which subtracts it as a flat R deduction — so the registry's **+0.46 is NET** of the legacy cost
  model (0.1148 R on the JPY crosses, 0.0638 R on GER40; 0.1011 R weighted over these 406 trades)
  and my +0.4986 is **GROSS**. On a common basis: **+0.3975 against +0.4598, −13.5 %.** The omitted
  cost term is 1.6× the residual gap, so the apparent agreement was an artifact of the mismatch.
* **Window.** 2025-06-01 is KB5's **coverage start**, not its forward window. `KB5:197-198` and
  `KB6:297` define forward as `year >= 2025`. On that declared window the walk is
  **+0.3716 gross / +0.2708 legacy-net on n=565** — 41 % below the registry — and the mean rises
  monotonically as earlier data is cut (+0.2925 on n=919 → +0.3716 on n=565 → +0.4986 on n=406),
  which is exactly what a flattering cut looks like.
* **`min_gap` semantics differ.** Mine is per **follower** (`ak_supply_generate.py`
  `apply_min_gap`); KB5's is per **leg**, each `mine_pair` call holding its own `last_idx`. AUDJPY
  is the follower of two legs, so KB5 can post two same-bar AUDJPY trades and this generator
  cannot. Not the same construction, and it is worth 41 % of the compared number
  (+0.2075 → +0.2925 over 2,041 → 919 trades).

**And the finding that survives all of that is bigger than the reproduction.** At broker truth over
the whole 2.5-year archive the sleeve is **−0.0415 R/day** and the entire distance is cost: spread
0.1776 R plus commission 0.1283 R plus slippage 0.0177 = **0.3239 R/trade**, which is **3.2× the
legacy model's 0.101**, against a stop of `0.5 × ATR`. So the registry's +0.46 R — the number
`admission.py:271-277` carries and the number that justified registering this sleeve at conf 0.15 —
is over-stated by roughly 0.22 R/trade by a cost model that under-charges it. That is a
Session-J/N-class cost finding on a sleeve the book can already size.

Its prescription is therefore not carry, not breadth, and not the exit families in general — it is
the **stop width**, and the cells confirm it rather than propose it:
`US30_cash->USDJPY@T2.0` at +0.2774 R/day, p 0.1131, failing significance alone, and **+0.5637 at
`stop_1.5x_tgtscale`**. The remaining questions are `declared_family_size` and the engine change in
§6.

## 6. What is next, and for whom

**Borhen — five decisions and two data captures, all with numbers.**

1. **A live sizing hazard that the registry edit AA §4 routed would ARM.** A sleeve the sizer
   refuses as `unknown_sleeve` is still counted in the Kelly-lite conviction breadth and still sizes
   every other unit that day **up by 32.49 %** (`admission.py:1143-1148` counts, `:1163-1165`
   refuses afterwards, `precount_intent_filter` has no known-sleeve check). Not reachable today —
   B325 measured that generation and `effective_registry` resolve the same set. It becomes reachable
   the instant a generation spec is added **without** the matching `admission` confidence weight.
   `REGISTRY_EDIT_PROPOSAL`'s `also_needs` already said "a confidence weight if it is ever to be
   sized"; this makes that line load-bearing rather than tidy. **The safe order for those three
   edits is: confidence weight first, spec second.**

2. **A clock defect in `BUILT` that I did not repair.** `sub_mid_dn_revert` buckets **50.04 % of its
   370,808 archive H4 bars into the wrong session** (§0 item 1). Not costing money today; one
   `--tags` change away. The repair is one line and it is a **re-derivation**, because it changes the
   sleeve's generated set and therefore its `SURVIVOR_BOOK_V1` carry tier and AD's B753 restatement.
   That is a session, not a patch, and it is worth commissioning.

3. **`declared_family_size`, again, and it now has five customers instead of one.** AF §11 routed it
   as *"the only thing standing between the estate's best new-edge candidate and a verdict."*
   Five more sleeves and cells now fail **significance alone**, with the largest family each would
   admit against under BH α = 0.10:

   | candidate | best cell | R/day | raw p | admits against ≤ |
   |---|---|---:|---:|---:|
   | `sub_xvol_pullback` (ARMED) | as-walked | +1.0264 | 0.0061 | 16 |
   | `fam_session_leadlag_us30_cash_usdjpy_t2.0` | `stop_1.5x_tgtscale` | +0.5637 | 0.0130 | 7 |
   | `vol_compression` | `time_stop_20` | +0.4445 | 0.0243 | 4 |
   | `mx_jp225_cash_d1_volume_surge_reversal` | `target_5R` | +0.6163 | 0.0313 | 3 |
   | `asia_pdl_fade` | `stop_2.5x_tgtscale` | +0.0846 | 0.0659 | 1 |
   | `ny_index_momentum` | `prerollover_flat_h22` | +0.1065 | 0.1513 | 0 |

   **Read the right-hand column with its floor.** The gate corrects against
   `max(sleeves judged in the run, declared_family_size)` (`gate.py:797`), and this run judged 36 to
   43 — so a family of 16 is not reachable by declaring it; it would require judging fewer sleeves.
   `AK_SUPPLY_GATE_V1.json` → `family_size_sensitivity` carries q at 69, at AF's 276, at the
   ledger's measured count and at the run's own size, padded exactly as the gate pads and verified
   to reproduce the gate's own q at 69.

4. **Whether to build the cross-symbol feed** `session_leadlag_genuine` needs
   (`supply.LIVE_WIRING_GAP`): a `SleeveSpec` field, a `book_engine` fetch, and a staleness rule for
   the second series. The sleeve is −0.0415 R/day pooled and one of its four legs is +0.5637 at its
   repaired stop. §5.3 also shows its registered +0.46 R is over-stated by ~0.22 R/trade by the
   legacy cost model, which is an argument for re-deciding the registration itself.

5. **The three registry entries** AA §4 routed, with the two things that routing did not say:
   `structural_retest` cannot take a careless `bar_count` (§2.3), and `registry.py:130-134` treats an
   **empty** candidate allowlist as **all** candidates, so an entry is inert only while the deployed
   allowlist stays non-empty. None of the three has evidence that would justify arming it today.

6. **M15 bars before 2024-01-02 for six indices** — §5.1. The cheapest verdict-moving item here.

7. **Tick spread for eight symbols** — §5.2. Takes `structural_retest` from 58.0 % coverage to
   100 % and unlocks 2,112 trades on the estate's only short-side mechanism.

### 6.4 The diversifier door: it cannot be answered here, for two reasons and not one

Run against the three sleeves `run_book.py --tags` actually carries, at each candidate's repaired
exit cell. **Every candidate was refused, and the reasons that matter are structural.**

**Reason one — the armed book's day count.** It replays to 162 placements over **144 trading days**
spanning 2006-05-15..2026-06-04. The door's `correlation_sample` guard needs **30** overlapping
days.

**And a number I got wrong, which a completeness pass caught in the result doc AND in block B974.**
I wrote *"~7 book-days a month, exactly as `CLAUDE.md` §4 says."* 144 days over 241 months is
**0.598 book-days/month** — wrong by **11.7×**, and it made the door's unavailability read as
expected rather than as a **12× disagreement between the replay's frequency and the live
expectation**, which is itself an unreported finding this session should have raised. `CLAUDE.md`
§4's ~7 book-days/month is for the *armed* window; the archive replay of the same three sleeves is
two orders of magnitude thinner, and nobody had put the two side by side. Corrected in both places.

**Reason two, and it is not the book's fault — the candidate solo books HALT.** `certify_guarded`'s
correlation, PSR and block-permutation all read the *candidate's own* daily series, and that series
is truncated by the governor's max-drawdown entry block:

| candidate | cell | solo placed / offered | solo span | halted |
|---|---|---:|---|---|
| `asian_fade` | `trail_a2_g0.5_prod` | 237 / 1,275 (18.6 %) | 2024-01-04 .. **2024-06-18** | **yes** |
| `asian_fade` | `trail_a2_g0.5_honest` | 146 / 1,275 (11.5 %) | 2024-01-04 .. **2024-04-15** | **yes** |
| `kz_london_crypto_low` | `stop_3x_tgtscale` | 281 / 283 | 208 days | no |
| `metal_session_reversion` | composite | 245 / 798 | stops in 2024 | yes |

So `n_overlap = 5, 5, 10` are properties of an 81–89 %-truncated series of a *recorded* cause, and
only `kz_london_crypto_low` (overlap 11) tests the armed book's day count unaided. My first draft
attributed all four to the book. Both causes are now captured per cell in the artifact
(`candidate_solo_book.truncation`), which they were not before.

### 6.4.1 The honest trail bound — the rule the commission set, and it changes the answer

**It did not run in my first version, because of a missing underscore.** `pick_cells` built
`best[:-len("_prod")] + "honest"` → `trail_a2_g0.5honest`, which is in no frontier, so the lookup
was always False and only the PRODUCTION bound was certified — on the one candidate B613 measured
as 95.8 % intrabar sequencing. Fixed and re-run, and the difference is the whole finding:

| `asian_fade` cell | bound | cell pooled | Δ book return | Δ book Sharpe |
|---|---|---:|---:|---:|
| `trail_a2_g0.5_prod` | production | −0.0093 | **+6.468 pp** | −0.0735 |
| `trail_a2_g0.5_honest` | intrabar-honest | **−0.3463** | **−29.553 pp** | −0.1778 |

The commission's rule is *"where the honest bound flips the sign, the verdict is the honest
bound's."* The **pooled mean** does not flip sign — both are negative — so the rule as literally
written does not fire. **The book-level consequence flips completely**: the one number that looked
worth having, a 6.5-percentage-point improvement in the armed book's return, becomes a
29.6-percentage-point destruction of it at the honest bound. So the honest reading is that
`asian_fade`'s ~zero-mean repair is a production-trail artifact at book level, not only at
sleeve level, and B613's rule generalises further than its own wording.

### 6.4.2 The rest of the door

| candidate | cell | Δ return | Δ Sharpe | corr | overlap | failed guards |
|---|---|---:|---:|---:|---:|---|
| `kz_london_crypto_low` | `stop_3x_tgtscale` | +0.005 pp | −0.0466 | 0.026 | 11 | blackout, lifetime, corr-sample, book_return |
| `metal_session_reversion` | composite | **−27.197 pp** | −0.1527 | −0.122 | 10 | lifetime, corr-sample, book_return |
| `metal_session_reversion` | `stop_3x_tgtscale` | −25.472 pp | −0.1454 | nan | 5 | same |
| `ny_index_momentum` | `prerollover_flat_h22` | — | — | nan | 0 | **cannot be placed at all** |

`metal_session_reversion` destroying 27 pp of return is the `book_return` guard earning its place.
All of them also fail `lifetime_expectancy`, which is the door working as designed on a ~zero-mean
sleeve: the repair for those is standalone expectancy, not correlation.

**And the four new sleeves cannot reach the door at all**, one layer below generation:
`book_replay` rejected 449 / 1,469 / 2,803 / 873 of their priced trades with
`unit:fail_closed:unknown_sleeve`, because none is in `admission.effective_registry`. So
`ny_index_momentum`'s row is evidence about the door's reachability and not about the sleeve, and it
is labelled that way. It is also what led to §6 item 1.

### 6.5 Sessions AI and AH

**Session AI (candidate book).** `AK_CANDIDATE_DOSSIER_V1.json`: four rows at their best-known
cells, each with the per-fold OOS series attached and `q` at four family sizes with the BH rank-1
threshold each implies, so "q = 1.0" stops hiding how far from admission a sleeve is. It also
carries a pairwise fold-series agreement table, because two candidates whose good folds are the
*same* folds do not diversify each other however uncorrelated their daily series look — with the
caveat that fold calendars are per sleeve, so read it as a shape hint and use the daily series for
anything load-bearing.

**Session AH (conditioning + entry economics).** Four rows are yours. `vol_squeeze` has 1 of 5 OOS
folds positive at its best carry cell — a regime question with a carry repair already priced
underneath it. `fam_structural_retest_index_asian_long` fails `robustness` at +0.0461 **with drop-best retention −1.273, i.e. one fold carries all of it** (§5.2). The
net-basis coherence table (§4) names, per sleeve, which member goes negative once cost is charged —
that is member conditioning with the members already identified. And `session_leadlag_genuine`'s
entry hour is an AH-shaped question: its legs are session-gated and §5.3 shows the whole sleeve is
a cost-geometry problem on a 0.5 × ATR stop.

**Whoever owns the exit lane next.** `asia_pdl_fade` at `stop_2.5x_tgtscale` — +0.0846 R/day, 5 of
5 OOS folds positive, 2,827 trades, failing significance alone — is the strongest unfinished exit
result in the estate, and it took one cell.

**Nobody, yet.** The `structural_retest` HTF chunking fix (§2.3). Two lines, and it invalidates the
three verified whitelist cells, so it needs a re-derivation session.

## 7. What I got wrong

**Eight, and the provenance of each matters more than the error.** Six were found by an adversarial
pass over my own claims — eight refuters, each told to default to refuted, spending Borhen's
standing Workflow opt-in on exactly the thing it is for. Two of the six had already been half-caught
by my own drafting and were made worse by it, which is worth saying: a caveat that names the right
risk and understates it is more dangerous than no caveat.

### 7.1 "`structural_retest` was the only sleeve still on raw UTC" — false, and the site still open is worse

`substrate.py:75-84` `_utc_hour` returns the raw UTC hour and `substrate_engine.py:102-108` cuts it
on the **identical** 8/16 boundaries. `sub_mid_dn_revert` is backed by it and sits in
`registry.py:55` `BUILT` with `session=ny` as a cell condition. Measured: **185,548 of 370,808 H4
bars (50.04 %) bucket differently.**

And my own first attempt to *dismiss* the refutation was wrong too. I reasoned that on an
`00/04/08/12/16/20` UTC H4 grid a +2/+3 shift never crosses the 8 or 16 boundary, so an H4 sleeve
could not be affected — which is true of that grid and false of this archive, whose H4 closes
convert to **odd** UTC hours (01/02/05/06/09/10/13/14/17/18/21/22). Six of those twelve shift. The
lesson is the ordinary one: I reasoned about a grid instead of measuring the one on disk.

My causal story was wrong as well. I said the F7/B29/B54 pass missed `structural_retest` because it
is in no registry. The pass's own record says otherwise — `IMPLEMENTATION_STATE.md:706-709` sets
`substrate.py` aside *"because `include_clean3` is false, so it cannot generate live"*, i.e. it
scoped by **config reachability**. Registry membership demonstrably did not get a sleeve repaired.

### 7.2 The coherence correction was eight flips and is five, on a confound I asked for

§4.1. Gross from the trades against net from `diagnostics.by_symbol` are different populations
because of the March-2026 blackout, and `coverage_frac` cannot show it. One flip was purely that
artifact, two were k=1 degenerate, and `structural_retest` was never a flip at all. §4.2: my causal
explanation inverted the data. Both are corrected in the artifact, not only here — the unmatched
reading is retained under its own key so the correction is visible.

Worth naming the near-miss: I wrote the refuter's prompt with *"clause (d) is the most likely
defect — check it hardest"*, because the population question had occurred to me and I published
anyway. Suspecting a probe and shipping it is not the same as suspecting it.

### 7.3 The `session_leadlag_genuine` reproduction was gross-versus-net **and** the wrong window

My §7 draft caught the first half: `mine_pair` passes `cost=cost_for(follower)` into `simulate`
(`KB5_leadlag_subh4.py:150,178-182`), so the registry's +0.46 is net of the legacy model and my
+0.4986 was gross. What it did not catch is that **2025-06-01 is KB5's coverage start, not its
declared forward window** (`year >= 2025`, `KB5:197-198`) — and it is the most flattering cut
available, with the mean rising monotonically as earlier data is dropped. On the declared window the
walk is +0.3716 gross / +0.2708 legacy-net on n=565, 41 % below the registry. `min_gap` semantics
differ too (per-follower here, per-leg there). §5.3 now states what reproduces (mechanism,
population) and what does not (the R).

### 7.4 "513 is the only aligned phase" — false; and one of my own citations was stale at birth

Every `bar_count ≡ 1 (mod 16)` is equally aligned, because `MIN_BARS = 512` is `32 × 16`; 513 is
merely the smallest above the floor. The test that was supposed to pin the word is named
`…only_at_the_513_phase` and evaluated two values. Two more in the same finding:
**"and hence a different DIRECTION" is structurally impossible** — each `(class, session)` appears
once in `WHITELIST`, and the direction flips on **0** of the 782 bars present at both phases; and
calling the 513 block "the last completed H4 block" overstates it, since it is a calendar H4 candle
on only 6.5 % of those trades. Finally the `file:line` was wrong at HEAD in two places
(`supply.py`, `ak_repair_rows.py`): `_htf_trend_at` is at `:82-103`, and it was **my own B950
commit** that moved it +16 lines while writing `:66-87`.

### 7.5 I framed `sub_xvol_pullback`'s p-value as a discovery, and then over-claimed the comparison

The p is AA's: `AA_ESTATE_WALK.json` run `B_balanced|v1_1` has `p_raw 0.006099390060993901`,
reproduced byte-identically here. What is mine is the 58-cell frontier.

The comparison to `mx_btcusd` was materially overstated three ways, none of which my first draft
stated. **(1)** The p is computed on the pooled OOS **daily** series, not on trades: 31 days / 71
trades over 16.4 years against 266 / 266 over 7.4, with 2 of 5 folds test-empty or test-thin and
72 % of legs gold/silver crosses (up to 9 on one day). The honest gap is **8.6×**, not 3.6× — and
B853 had already retired the trade-count denominator for **this exact sleeve** one wave earlier.
**(2)** 0.0061 against 0.0064 is three resample draws on a `(k+1)/10001` grid, inside Monte-Carlo
noise, and the q is **identical** at every published bill. Worse, the p I quoted and the R/day I
quoted come from **different cells** — `target_4R`'s p is 0.0078, which is *worse* than
`mx_btcusd`'s. **(3)** `pooled_oos_mean_r` is a per-active-day conditional, not a rate: at ~1.9
active days a year against ~35.9, the larger per-day number annualises to **2.1–6.0 R/yr against
8.35**. The comparison is withdrawn; the frontier stands.

### 7.6 My first `_summary` crashed on its own output

`collections.Counter(...).items()` yields `(symbol, count)` and I called `len()` on the count. Three
specs' work lost, fixed, re-run. Found by reading the traceback.

### 7.7 The repair-row script was not idempotent and double-appended

The first corrected re-run put 44 AK rows in a queue that should have 22. Fixed by replacing AK's
own rows while preserving every other session's line byte-for-byte — "append, never overwrite"
protects a *sibling's* rows, and leaving two contradictory versions of one finding is not what it
asks for.

### 7.8 Two of a sibling module's tests went red on my change, and their fixture was the defect

`test_a_sleeve_with_no_observation_still_fails_closed` and
`test_a_fidelity_unmeasured_sleeve_is_never_scored_however_good_it_looks` used `ny_index_momentum`
as their stand-in for "a name with no fidelity record", and B951 gave it one. Verified as caused by
exactly that change: with the four new entries popped from `FIDELITY_REGISTER` at run time both
pass, with them present both fail. The specimen is now **derived at run time** with its absence
asserted — AA §3.4's fix for its analogue, and the right one because this is the **third** amendment
to these two tests (Session Y moved them off `asian_fade` at B490).

**And one environment note, because it will cost the next session an hour.** The agreement's §2 says
a suspected regression is verified at the merge-base. A fresh `git worktree` at the merge-base is
**not** a usable comparison for this file: the sparse-checkout cone excludes `research/operations/`,
so the cost artifact is absent and **25 of the file's 60 tests fail there** for reasons unrelated to
any change. The targeted in-worktree A/B is what actually isolates a cause.

### 7.9 Five more, from the completeness pass, and two of them voided a commission requirement

The eighth refuter and the completeness critic returned after I had already committed the first
write-up. Both found real things.

* **The honest trail bound never ran** — a missing underscore in `pick_cells` (§6.4.1, B982). The
  commission required both bounds and the artifact silently had one, on the worst possible
  candidate. Fixed, re-run, and the honest bound turns +6.5 pp of book return into −29.6 pp.
* **The dossier's fold series was `[None, …]` on every row** — `oos_mean_r` where `diagnostics`
  emits `test_mean_r` (B983). Session AI's named input was blank inside a well-formed artifact,
  and §6.5 claimed it was attached. Fixed, and the fix returns *absent* rather than
  *present-but-blank* on a future rename.
* **"~7 book-days a month" was wrong by 11.7×** (B984). And the real finding underneath is one
  nobody had compared: the archive replay of the armed three is ~12× thinner than the live
  expectation.
* **The `n_overlap` failures are partly the candidates' own halted books**, not only the armed
  book's day count (B984). `asian_fade` places 237 of 1,275 and stops in June 2024.
* **The one `structural_retest` cell I called a survivor has drop-best retention −1.273** (B984) —
  one fold carries all of it, and I published the mean without the retention.

Two smaller ones worth recording because they are the same class: `SLEEVE_SUPPLY_V1.json`, the
commission's **named** deliverable, did not exist (B981) — the evidence was in five files and no
index mapped it; and **zero tests covered the receipt-driver layer** that produced every published
number, in a session where that layer broke three times (B985).

**And one place the critic was wrong and measurement settled it differently from both of us.** It
read `AUS200_cash` as a cost-artifact gap needing a regeneration. Measured: the artifact **has** it,
as `AUS200.cash`, with `spread_price.by_session` populated and `commission.kind = "zero"` — fully
priced. It is unreachable because `build_broker_symbol_resolver` returns `AUS200_cash` unchanged
while mapping `US500_cash → US500.cash` and `US100_cash → US100.cash`. So it needs **one line in the
profile symbol map**, not a capture and not a regeneration — and the tick ask now separates three
defects where I had merged them into one.

### 7.10 What the adversarial pass could NOT refute

`AD_EXIT_SWEEP_COVERAGE_25_OF_29` came back `refuted: false` with three refinements folded in
above: AD's coverage set is `WORK_LIST` (17) + `MX_FAMILY` (7) **plus the trail pair run separately
under `AD_ONLY`**; `sub_xvol_pullback` is in fact named once in `ad_exit_sweep.py:161`, in
`TARGET_CONVENTION`, so the script carried the metadata to sweep it and never listed it; and
`liq_asia_up_low_metal` was still NOT_EVALUABLE in AD's own baseline, which is why sweeping it
returns no gated metric. The refuter also independently killed the two available "excluded on
evidence" defences: AD swept four sleeves that are below AA's fidelity floor **and**
NOT_EVALUABLE in AA's walk, and its own baseline gate scored two of the four as REJECT on the same
run.

**The prefilter refuter also came back `refuted: false`, and it did the work I had left undone.**
It widened the parity run from one symbol per spec to **every symbol of every spec — 37 walks,
5,045 + 2,041 + 465 + 1,490 rows — plus both authored-UTC populations (7,492 and 429): 0 candidates
dropped anywhere.** It also found a stronger version of my argument: no generator can read a window
index below 14 at any `bar_count`, because each one's warmup floor exceeds its deepest ATR lookback
by ≥ 14 (`vol_squeeze` 87 vs `j-60`, `ny_index_momentum` 520 vs `j-480`, `structural_retest` 512 vs
`j-99`). Forcing `vol_squeeze` to `bar_count = 88` still gives identical trade sets.

**But it found two real defects in my JUSTIFICATION, and one is a factual error in a production
docstring.**

* **`supply.py`'s clock-memo justification was factually wrong.** I wrote that the transition is
  "02:00 local, which is 07:00 UTC in both directions". `broker_clock.py:130,136` puts the **autumn**
  transition at **06:00 UTC**, not 07:00. The conclusion survives — both instants are whole UTC
  hours, so no two bars in one UTC hour can straddle one, measured over 783,094 bars and across all
  six 2024–2026 transitions — but the cited reason was wrong and is corrected in the file.
* **`structural_retest`'s vol gate is the one comparison that is not the same float expression on
  both sides.** The prefilter uses a running sum with subtraction; `generate()` recomputes a fresh
  100-term sum. Algebraically equal, **not bit-equal** — max relative difference **1.255e-13** — and
  the 1.4 boundary is exactly reachable because prices are quantised: on XTZUSD at
  2025-07-11T22:30Z the generator reads exactly 1.4 and the prefilter 1.4000000000000101. Both
  passed, so nothing was dropped, but that gate's necessity is **measured-safe rather than proven**:
  1 at-risk bar in 1,424,028, 0 of them in a whitelisted cell. Recorded in the module.

## 8. Every sleeve leaves with a prescription

**23 repair-queue rows appended, session `AK`**, to `phase6/receipts/REPAIR_QUEUE_APPEND.jsonl` —
`O_APPEND` per row, one new key `appends.AK` in `REPAIR_QUEUE_V1.json`, AA's
`rows`/`summary`/`diagnostics` and AD's 49 rows preserved byte-for-byte.

| prescription | n | what it means |
|---|---:|---|
| `CANDIDATE_BOOK_INPUT_FOR_AI` | 4 | the dossier rows, at four family sizes each |
| `DIVERSIFIER_DOOR_MEASURED` | 4 | §6.4 — including that the door cannot be answered at 144 book-days |
| `EXIT_REPAIR_LANDED_SIGNIFICANCE_REMAINS` | 2 | `sub_xvol_pullback` (ARMED), `asia_pdl_fade` |
| `SAMPLE_M15_DEPTH` | 1 | `ny_index_momentum` — the ask is archive depth, not more symbols |
| `DATA_PATH_TICK_SPREAD` | 1 | `structural_retest` — eight symbols, 2,112 trades, a capture not a decision |
| `COST_GEOMETRY_STOP_WIDTH` | 1 | `session_leadlag_genuine` — the 0.5×ATR stop, confirmed at leg level |
| `MEMBER_CONDITIONING_NOT_BREADTH` | 1 | its four legs are a mixture at net; one carries it |
| `CARRY_THEN_EXIT` | 1 | `vol_squeeze` — swap is 86 % of cost, and 1 of 5 folds is positive |
| `EXIT_REPAIR_PARTIAL` | 1 | `orb_crypto_london` |
| `COVERAGE_OR_SAMPLE_BEFORE_EXIT` | 1 | `liq_asia_up_low_metal` |
| **`F7_CLOCK_SITE_STILL_OPEN`** | **1** | **`sub_mid_dn_revert` — 50.04 % of its H4 bars, in `BUILT`, not repaired and why** |
| `F7_CLOCK_REPAIR_LANDED` | 1 | closes the B29/B54 pass's own coverage question for `structural_retest` |
| `GENERATOR_HTF_PHASE_DEPENDENCE` | 1 | §2.3 — filed, not repaired, with the reason |
| `COHERENCE_TEST_BASIS` | 1 | §4, against `AF_REPAIRS_V1.json` |
| `LIVE_WIRING_GAP_CROSS_SYMBOL_FEED` | 1 | owner decision, with the smallest sufficient change named |
| `REGISTRY_ENTRY_OWNER_DECISION` | 1 | AA §4's three edits, plus the sizing hazard in §6 item 1 |

## 9. Verification — the §2 scoped receipt

**Blast radius.** `python3 scripts/pytest_failset.py scope --base main --head HEAD
--include-worktree` over a 17-path diff → **10 test files** by import closure and path literal. Run
with eight more added by hand, because the drivers import `walkforward.exits`,
`walkforward.diversifier`, `walkforward.registry`, `admission.size_correlated_units` and the
candidate-registry plumbing — a scope that is too wide is free while one that is too narrow is not.

```
$ python3 -m pytest \
    tests/research_infra/test_fidelity_register_matches_receipt.py \
    tests/research_infra/test_trainer_folds.py \
    tests/research_infra/test_vig_trial_ledger_prospective.py \
    tests/research_infra/test_walkforward_book_replay.py \
    tests/research_infra/test_walkforward_family.py \
    tests/research_infra/test_walkforward_gate.py \
    tests/research_infra/test_walkforward_supply.py \
    tests/research_infra/test_wf_diagnostics.py \
    tests/ultimate_book/test_new_sleeves.py \
    tests/ultimate_book/test_sleeve_server_clock.py \
    tests/research_infra/test_walkforward_diversifier.py \
    tests/research_infra/test_wf_exits_parity.py \
    tests/research_infra/test_wf_registry_surface_reconciliation.py \
    tests/ultimate_book/test_candidate_book_consistency.py \
    tests/ultimate_book/test_candidate_promotion_plumbing.py \
    tests/ultimate_book/test_running_conviction.py \
    tests/ultimate_book/test_defect_register_repairs.py \
    tests/research_infra/test_ak_receipt_drivers.py \
    tests/test_implementation_state_block_citations.py -q
399 passed, 1 warning in 13.4s
```

**399 passed, 0 failed** at final HEAD. Three tests were red mid-session and all three are
accounted for: the two in §7.8, isolated to their cause by a targeted in-worktree A/B and fixed, and
`test_the_in_flight_wave_range_is_declared_and_shrinking`, which went red the moment B950–B979
landed because it caught this session's own in-flight entry going DEAD — the mechanism working, and
B980 is the payment.

**New tests: 65.** 44 in `test_walkforward_supply.py`, 6 in `test_sleeve_server_clock.py` (two for
`structural_retest`, one for `session_leadlag`, three pinning the `substrate.py` site that is still
open), 2 in `test_running_conviction.py` (the `unknown_sleeve` sizing hazard, the second written so
a future fix turns it red deliberately), **9 in `test_ak_receipt_drivers.py`** — the layer that
produced every published number and had zero coverage while breaking three times (B985) — plus two
rewritten in `test_walkforward_gate.py` and the `IN_FLIGHT_WAVE_RANGES` edit.

**The receipt-driver tests are the ones that matter most, and the reason is the failure mode.** Two
of that layer's three defects (B982, B983) produced a **well-formed artifact with the wrong content
inside it** — a missing underscore that made a lookup always fail, and a key name that filled a
deliverable with `None`. No traceback could catch either, and a smoke test would have passed. So
they assert on output SHAPE: the honest trail counterpart is findable, the fold-series key is the
one `diagnostics` emits and degrades to *absent* rather than to *nulls* on a rename, and AK's queue
rows are unique per `(sleeve, prescription)` so a double-append shows up.

Four more are the ones a wrong answer would have been silent about: the prefilters are fuzzed as
**necessary** conditions with a non-vacuity assertion on *both* sides (a prefilter that passes
everything and a fuzz that emits nothing are both caught); `authored_clock`'s restore of a
production module is asserted on the **exception** path; the server-clock hour memo is pinned
against the per-bar function on **both** 2026 DST transition days, with a guard test proving the
sampled day actually changes offset so the comparison cannot be vacuous; and the `unknown_sleeve`
sizing test asserts the exact half-Kelly bin crossing (0.748 → 0.991) rather than "it got bigger".

**Trial ledger.** Session `AK` wrote **953** look events —
`research/operations/trial_budget/TRIAL_LEDGER.jsonl` goes 4,785 → **5,738** (AA 1,643 · AD 2,036 ·
AF 778 · AE 328 · AK 953). The count includes the re-runs the §7 corrections forced; the schema
counts *look events*, not hypotheses, and two looks at one variant is honestly two looks. Every q-value above is at AA's `declared_family_size = 69` so it is
comparable to AA's and AD's; a reader deflating against 5,738 gets a stricter answer than this
document gives. That is the design.

**And the counts EMBEDDED in the artifacts are lower, deliberately, which a reader must know before
comparing them.** `AK_SUPPLY_GATE_V1.json` records `trial_ledger_measured: 4,796` and
`AK_CANDIDATE_DOSSIER_V1.json` records `5,734`: each is the ledger's size **at the moment that
driver ran**, and the ledger grew afterwards as the §7 and §7.9 corrections forced re-runs. They are
as-of-run snapshots, not disagreements, and the file is authoritative at **5,738**. A completeness
pass flagged the spread between them as four different published counts, which is fair — the
resolution is that only one of them is a claim about the ledger and the rest are timestamps. No q is
published at 5,738; the sensitivity table's rightmost column is its own run's count, and a reader who
wants the strictest reading has `deflation.largest_family_that_would_admit` per candidate, which is
independent of the ledger.

**H1.** Every file touched verified unbound by the R2 contract before editing:
`sleeves/structural_retest.py`, `sleeves/session_leadlag.py` (new), `walkforward/supply.py` (new),
`walkforward/fidelity.py`. The contract check reports the same **2 un-hydrated LFS pointers** it
reported at session start and nothing else — no bound path drifted.
**`config/agent_config.yaml` untouched**: the `include_clean3` research override is flipped in the
config **dict** handed to the driver, never on disk. No broker-capable script run. Nothing touched
the VPS.

**Sparse-checkout.** `research/operations/trial_budget` and
`research/operations/spread_model_2026_07_29` were both outside this worktree's cone and hydrated
with `git sparse-checkout add` — the agreement's §4 trap in its exact predicted shape, twice.

## 10. Artifacts

| path | what |
|---|---|
| `src/research_infra/walkforward/supply.py` | research specs, prefilters, the server-clock index, the F7 A/B harness, `LIVE_WIRING_GAP`, `REGISTRY_EDIT_PROPOSAL` |
| `src/components/ultimate_book/sleeves/session_leadlag.py` | the generator that did not exist |
| `src/components/ultimate_book/sleeves/structural_retest.py` | the F7 repair |
| `src/research_infra/walkforward/fidelity.py` | four entries plus the `_NO_LIVE_PATH` stamp |
| `tests/research_infra/test_walkforward_supply.py` | 44 behavioural tests |
| `phase8/receipts/ak_supply_generate.py` | the walk, both labellings, both clocks, the parity and phase measurements |
| `phase8/receipts/ak_supply_gate.py` | the gate, the family-size sensitivity, both exit sweeps |
| `phase8/receipts/ak_supply_cells.py` | the pre-declared cells, the coherence bases, the per-cell frontiers |
| `phase8/receipts/ak_diversifier.py` | the door, against the armed three |
| `phase8/receipts/ak_candidate_dossier.py` | AI's four rows |
| `phase8/receipts/ak_repair_rows.py` | the queue rows, from the artifacts |
| `phase8/receipts/AK_SUPPLY_TRADES.json.gz` | **deliverable** — 7,919 trades with path, both labellings, both clocks, reachability |
| `phase8/receipts/AK_SUPPLY_GATE_V1.json` | **deliverable** — verdicts, diagnoses, prescriptions, family-size sensitivity |
| `phase8/receipts/AK_SLEEVE_CELLS_V1.json` | **deliverable** — seven cell verdicts, coherence on both bases over matched rows, 413 per-cell exit cells, the tick ask |
| `phase8/receipts/AK_EXIT_FRONTIER_V2.json` | **deliverable** — AD's schema, 468 cells over 8 sleeves, AD's gap closed |
| `phase8/receipts/AK_DIVERSIFIER_V1.json` | **deliverable** — the door at the repaired cells |
| `phase8/receipts/AK_CANDIDATE_DOSSIER_V1.json` | **deliverable** — for Session AI |
