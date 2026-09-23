# Sleeve-book defect register — reproduced faithfully, recorded separately

**Session H deliverable 3.** Written 2026-07-26 while porting the live `ultimate_book` W7 book into
`SleeveBookPolicy`.

**None of these is fixed.** `SESSION_H` requires the port to reproduce the live semantics exactly,
including the parts that look wrong, because the module's entire value is that it measures what
actually trades — a policy that silently improved on the book would stop being a measurement of it and
would reopen F1 instead of closing it. So each entry below is *reproduced* by the policy and *recorded*
here, with what the correct behaviour would be and what it would be worth. Two channels, not mixed.

Every claim is `[MEASURED]` from source at HEAD or from the VPS runtime-learning packets, with
`file:line`. Where magnitude could not be measured, that is said.

**Ranked by economic consequence.** D0 outranks the rest and was found last, while measuring which sleeves the validation actually covers.

---

## D0 — Over 38 live days the book placed 145 trades, none of them from a train-validated sleeve

**Severity: highest in this register. Live-realized. Bears directly on OD-1.**

**[MEASURED]** across all 99,112 runtime-learning packets, the 145 `unit_placed` events decompose as:

| sleeve | registry confidence | registry status | placements | share |
|---|---:|---|---:|---:|
| `idxrev` | 0.15 | **breadth_falsified** | 41 | 28.3 % |
| `fx_jpy` | 0.15 | **breadth_falsified** | 22 | 15.2 % |
| `asia_pdl_fade` | 0.25 | candidate book | 20 | 13.8 % |
| `ny_crypto_momentum` | 0.35 | candidate book | 18 | 12.4 % |
| `asian_fade` | 0.40 | candidate book | 17 | 11.7 % |
| `fx_jpy_ny` | 0.15 | forward_only | 9 | 6.2 % |
| `metal_session_reversion` | 0.40 | candidate book | 9 | 6.2 % |
| `mx_*` (3 sleeves) | 0.025 | market expansion | 5 | 3.4 % |
| `kz_london_crypto_low` | 0.10 | candidate book | 2 | 1.4 % |
| `orb_crypto_london` | 0.35 | candidate book | 2 | 1.4 % |

- **Placements by the five train-validated core sleeves — `metals_core` (1.00), `crypto` (0.85),
  `energy_agri` (0.80), `metals_softband` (0.50), `metals_ob_micro` (0.30): zero.** Not one, on either
  account, in 38 days. They appear in the packet stream only as per-symbol-slot config skips.
- **Placements by the two sleeves the registry itself marks `breadth_falsified`: 63, or 43.4 %.**
  `admission.py:195-199` on `idxrev`: "failed-breakout fade; data_depth FALSIFIED train (−0.065R, 5 deep
  idx) → demoted to breadth, not deleted". `:200-204` on `fx_jpy`: "data_depth FALSIFIED train (−0.103R
  11.5yr) → demoted to breadth, not deleted".
- **Weighted mean confidence of placed units: 0.2312**, against a core-8 registry mean of **0.4875**.
- `idxrev` alone accounts for **64,370 of the 94,196** sleeve-bearing packets (68 %).

Two contributing causes, measured separately and not conflated:

1. **Signal frequency.** The core sleeves are H4 with tight vol/FVG-cascade gates. On their *configured*
   symbols (XAUUSD, XAGUSD, BTCUSD — all present in both live profiles) they were evaluated on every
   cycle and produced **no firing signal** in the window. A sleeve emitting no intent emits no packet
   (`book_engine.py:528-529`), which is why they are near-invisible in the stream rather than absent.
2. **Instrument config.** Of `metals_core`'s declared 6-symbol universe, **4 are absent from both live
   profiles** — XAUEUR, XAGEUR, XAUAUD, XAGAUD, each skipped `profile_missing_instrument_config` 216
   times per metals sleeve. `crypto` lost DASHUSD the same way (216 skips). So the three metals sleeves
   ran a **2-of-6** effective universe and `crypto` a 1-of-2, against the universes their registry
   declares and their validation was computed on.

**Correct behaviour.** For cause 2: either configure the four metals crosses and DASHUSD, or narrow the
registry universes to what the profiles support so the declared universe and the traded universe agree.
Silently running a third of a sleeve's universe while carrying the confidence weight validated on all of
it is the defect. For cause 1: nothing to fix — a sleeve that does not fire is working as designed.

**What it would be worth.** This reframes what the W7 fortnight measured. `SECOND_AUDIT.md` and OD-1
record that the book "went live 2026-06-18 → 07-02, underperformed, and he deactivated it"
(`FULL_VISION_PLAN.md:42-45`), with FTMO ≈ −5.3 %. That drawdown was produced by a trade mix whose
weighted confidence was **47 % of the core book's**, in which the two falsified-and-retained-for-breadth
sleeves were the two largest contributors and the four highest-confidence sleeves contributed nothing.

It is therefore not evidence about the W7 core book's edge. It is evidence about the candidate book, the
market-expansion book, and the breadth residue — which is a different question, and a much less
interesting one to have answered at the cost of 5 % of a funded account.

This does not reverse OD-1: the broad system may still be the right activation candidate for reasons
that have nothing to do with W7. It does mean the specific inference "W7 underperformed live, therefore
W7's edge is doubtful" is not supported by this evidence, and Session E's W7 forensics lane should be
told before it attributes the drawdown to the book.

**Self-correction, recorded.** The first version of this entry claimed the core sleeves "never generated
a single intent … because their symbols are not configured". That was wrong and was caught by checking
which symbols actually carried the skip: XAUUSD, XAGUSD and BTCUSD **are** configured in both profiles,
so those sleeves were evaluated normally and simply did not fire. Only the four metals crosses and
DASHUSD are unconfigured. The corrected claim is narrower — zero placements, two separable causes — and
the config gap is a universe reduction, not a total blackout.

---

## D1 — The gross-cap shed is first-fit, not lowest-conviction-first, and can leave 28 % of deployable risk on the table

**Severity: medium (latent — the cap never bound in the W7 fortnight). Live-reachable.**
**Substantially corrected 2026-07-26 after adversarial review; see the correction note at the end.**

`admission.py:1279-1284` documents two properties:

> deciding in **DESCENDING-CONVICTION** order so the cap sheds the LOWEST-conviction units first (it
> must **NEVER** starve the highest-conviction metals_core — the prior natural/alphabetical-cluster
> order did, a known `W7_LIVE_ENGINE_BUILD_PLAN` hazard)

**The second property holds. The first does not.**

The algorithm is a **first-fit-descending greedy**: units are *considered* in descending conviction, and
each is admitted iff it fits the *remaining* headroom. That does guarantee the strongest unit is tested
against the **full** headroom, so `metals_core` is admitted whenever its own risk fits — the strongest
guarantee any shed policy can give, and exactly what the comment's second clause promises. Under the
alphabetical order the comment blames, metals **is** starved at 0.0400/0.0336/0.0250 headroom
[MEASURED]. The descending order delivers what it claims.

What it does **not** do is "shed the lowest-conviction units first". It sheds by *fit*. At full 0.0400
headroom with four clusters firing (`metals_core` 1.00, `crypto` 0.85, `energy_agri` 0.80, `idxrev`
0.15, half-Kelly na=4, no de-risk):

| headroom | admitted | shed | deployed | max deployable |
|---:|---|---|---:|---:|
| 0.0400 | `metals` (1.241), `index` (0.186) | **`crypto` (1.055), `energy` (0.993)** | 0.028543 | 0.028543 |
| 0.0250 | `metals` (1.241) | `crypto`, `energy`, `index` | 0.024820 | 0.024820 |
| 0.0200 | `energy` (0.993) | `metals`, `crypto`, `index` | 0.019856 | 0.019856 |
| 0.0150 | `index` (0.186) | `metals`, `crypto`, `energy` | 0.003723 | 0.003723 |

It sheds the **second- and third-strongest** units while admitting the **weakest**. Anyone reasoning
about cap behaviour from the comment would predict the opposite.

**Where it actually costs deployed risk.** On the four-cluster set above, first-fit-descending achieves
the **maximum feasible subset sum at every headroom** — the unused headroom is unit granularity, not
greed. But the property does not hold in general. Searching 4,000 random cluster sets drawn from the
live 13-cluster confidence map [MEASURED]:

```
headroom 0.031   FFD admits {crypto, jpy_fx}                    = 0.021718
                 optimal    {energy, metal_reversion, jpy_fx}   = 0.030404
                 shortfall  0.008687  =  28.6 % of deployable risk
```

FFD takes the large high-conviction unit first and is then unable to fit two mid-sized ones that
together would have deployed far more.

**Correct behaviour.** Proportional scaling: when `Σ unit_risk > available`, scale every sized unit by
`available / Σ unit_risk` rather than dropping units. It preserves the validated structure exactly — the
book's risk is *defined* as one unit per cluster at `base × conf`, and scaling keeps each cluster's
share proportional to its conviction — deploys the full headroom by construction, and cannot starve any
sleeve. A strict ascending-conviction shed is **worse**, not better: on the table above it deploys
0.00000 at both 0.0200 and 0.0150, because it drops the only units that fit.

**What it would be worth.** Bounded by how often the cap binds, which in the recorded fortnight was
**never**: all **668** distinct recorded units carry `reason: "sized"`, **zero** carry
`gross_risk_cap_would_exceed`, and the maximum `would_total_risk_pct / available_gross_risk_pct` reached
was **0.4654** [MEASURED]. So this is latent. When it does bind, the cost is up to ~29 % of deployable
risk in the adverse configuration above, plus the mis-prediction cost of the wrong comment.

**A related fact worth separating from the shed.** Live `available_gross_risk_pct` ranged **0.0 → 0.04**
across 1,754 distinct governor states, with a minimum non-zero of **0.0197** — *below* one half-Kelly
`metals_core` unit (0.02482). Four distinct states sat there. So the regime in which the book's
strongest sleeve cannot be admitted at all **is** live-reachable. That is a consequence of the cap and
the joint daily tightening, not of the shed order, and no shed algorithm can fix it.

**Correction note.** The first version of this entry claimed both documented properties fail, that at
0.0150 headroom the shed "admits its weakest and sheds its strongest — the exact outcome the comment
calls impossible", and that it "under-deploys: 0.0037 against 0.0150 available". Two of those three were
wrong. `metals_core` needs 0.02482 and **no shed order can admit it at 0.0150** — the cap starves it,
not the ordering, so the outcome was misattributed. And 0.003723 **is** the maximum deployable at that
headroom, so it does not under-deploy there. It also cited `available_gross_risk_pct` as
"0.0336–0.0337 in the recorded packets"; the true range is 0.0 → 0.04 and only 4 of 1,754 states fall in
that interval. The surviving claim — first-fit, not lowest-first, with a real 28.6 % shortfall case — is
narrower and was found by searching for it rather than by assuming it.

## D2 — One cycle, two Kelly day-counts: same-bar units sized 1.66× apart across the UTC midnight boundary

**Severity: medium. Live-realized on 4 cycles.**
**Mechanism corrected 2026-07-26 after adversarial review; see the correction note.**

`admission.py:1101-1106` builds `n_active_by_day` from the intents' `decision_day` and
`:1144-1148` resolves the Kelly multiplier once per day key. So a cycle whose intents carry two
`decision_day` values produces **two different Kelly multipliers on units decided from the same
`size_correlated_units` call**.

**[MEASURED]** over the whole packet stream, keyed on distinct `bridge` states so the count does not
depend on my cycle grouping:

| | count |
|---|---:|
| bridge states with ≥2 distinct Kelly **counts** | **12** |
| …of which ≥2 distinct **multipliers** (sizing actually differs) | **4** |
| …same-bin (two counts, identical multiplier, **zero** size effect) | 8 |
| bridge states carrying `would_units` at all | 884 |

So the consequential rate is **4 of 884 = 0.45 %**, not 1.4 %.

**The mechanism is the UTC midnight boundary and per-symbol bar recency — not D1 timeframes.** All four
consequential cycles fire within minutes of 00:00 or 21:00 UTC, and in each the intents' last *closed*
bars straddle a UTC date boundary:

```
redacted_account 2026-06-19T01:00   asia_pdl_fade CHF-basket M15 bar 06-19T00:45  na=1  x0.748
                              idxrev        JP225      H4  bar 06-18T21:00  na=3  x0.991
ftmo       2026-06-24T21:05   vol_compression XTZUSD   D1  bar 06-22T21:00  na=1  x0.748   <- 2 days stale
                              idxrev          GER40    H4  bar 06-24T13:00  na=9  x1.241
                              mx_nzdjpy       NZDJPY   D1  bar 06-22T21:00  na=9  x1.241   <- re-stamped to 06-24
redacted_account 2026-06-25T01:00   idxrev          GER40    H4  bar 06-24T16:00  na=10 x1.241
                              idxrev          UK100    H4  bar 06-25T00:00  na=1  x0.748   <- SAME SLEEVE
ftmo       2026-07-14T01:00   idxrev          JP225    H4  bar 07-13T21:00  na=7  x1.241
                              asia_pdl_fade   CHFJPY   M15 bar 07-14T00:45  na=1  x0.748
```

The third case is the decisive one: **`idxrev` against `idxrev`** — one sleeve, one timeframe, two
symbols, whose last closed H4 bars happen to fall either side of midnight. It also emits **two
`index|idxrev` units in one cycle**, which is legal because the correlated-unit key is
`(decision_day, cluster)`.

Worst observed size effect: **×1.241 against ×0.748 on units from the same bar — a 1.66× ratio.** In the
06-19 case the pair is 0.991 vs 0.748, a 24.5 % difference.

**Correct behaviour — and why the obvious fixes do not work.** Measured against the four cycles by
recomputing day keys from the recorded bar stamps:

| candidate fix | cycles unified |
|---|---:|
| make `vol_compression` re-stamp like the 14 `mx_*` sleeves | **1 of 4** |
| key the decision day off the bar **close** rather than its open | **2 of 4** |
| key the decision day off the **cycle runtime** (what `mx_*` already does) | **4 of 4** |

Only the third works, because only it is bar-independent — and no bar-derived key can unify the
`idxrev`-vs-`idxrev` case, where two symbols genuinely have last-closed bars on different UTC days.
Note that a runtime key is what the 14 `mx_*` sleeves already use, so the live book already contains
both conventions.

**What it would be worth.** Directly: on 4 of 884 unit-bearing cycles (0.45 %), one unit was sized
24.5–66 % away from the conviction the book actually had. Indirectly, and larger: it means the Kelly
tilt — the mechanism the 2.0 % dial was certified with — is not a function of the book's conviction
alone but also of which symbols happened to close a bar before midnight.

**Risk-envelope consequence of the only working fix, for the owner.** Moving to a runtime day key merges
intents that currently split across two `(decision_day, cluster)` buckets into one, so it *reduces* the
number of independent correlated units on those cycles — tightening the envelope, the safe direction —
while raising the Kelly count for the previously-under-binned unit, which raises its size. Net effect is
not one-signed and would need an MC pass. This is squarely B54 Part 2 territory and is the owner's call;
see `DAY_KEYS_IN_THE_LIVE_BOOK.md` §4.

**Correction note.** The first version of this entry said the cause was D1 bars keying `decision_day`
off the bar open while the `mx_*` sleeves re-stamp from the wall clock, and reported the effect on "12
recorded cycles … 1.66×". Both were overstated. Only **4** of the 12 change sizing at all; the other 8
carry two counts that land in the same half-Kelly bin and are economically inert. And the stated
mechanism explains only one of the four consequential cycles — the dominant mechanism is the UTC
midnight boundary with per-symbol bar recency, which is why it can occur inside a single sleeve on a
single timeframe. The two fixes originally proposed repair 1 and 2 of the 4 respectively; neither
repairs the `idxrev`-vs-`idxrev` case, and the original write-up asserted the broader one "makes every
timeframe agree and removes the special case", which is false on its own headline cycle.

## D3 — The running-conviction pre-count omits the A8 gate, and A8 is armed live

**Severity: medium. Live-reachable; magnitude unmeasurable from the export.**

`book_engine._running_conviction_override` states it "Replicates the SAME pre-count filters the
admission/bridge path applies (drop_w7 + vp_acceptance) BEFORE counting — CORRECTNESS-CRITICAL:
counting a sleeve the full-day path would drop could push the running count ABOVE the full-day union
and break the validated bound" (`book_engine.py:758-762`).

It applies exactly two filters (`:771-776`). `size_correlated_units` applies **three more** before
computing `n_active_by_day` (`admission.py:1078-1091` → `:1101-1106`): `learning_rerate`,
`metals_confluence_gate`, `symbol_damage_guard`.

Two of the three are inert live (`ultimate_book_learning_rerate: {}`; the engine never passes
`symbol_damage_metrics`, `book_engine.py:741-746`). **`metals_confluence_gate` is `true`**
(`agent_config.yaml:1310`) and does reject metals intents that carry the A8 features — which
`metals.py:216-218` populates. So a `metals_core`/`metals_softband` intent that A8 rejects still enters
the persisted running set, and `na = max(per_cycle, running)` (`admission.py:1145-1146`) can only carry
it *upward*. The stated bound is violated in the size-increasing direction.

**Correct behaviour.** Apply the same A8 filter before counting, or better, have one function compute
the pre-count intent set and call it from both paths — the duplication is the defect, and it has
already drifted once.

**What it would be worth.** One extra distinct sleeve in the count can cross a bin edge: na 3→4 moves
the half-Kelly multiplier 0.991→1.241, a **25 % size increase** on every unit that day. Unmeasurable
from the export because the packets do not record the A8 feature fields, so it is not knowable how
often A8 actually rejected. Recording those fields would make it measurable.

---

## D4 — The unit packet drops `direction` on every event type except placements

**Severity: low (evidence, not economics). Corrected 2026-07-26 after adversarial review.**

`build_runtime_learning_packet` reads the side off the *intent* (`runtime_learning_packet.py:225`) and
falls back to `outcome["direction"]` / `unit["direction"]` (`:230-231`). The cycle-summary emitter passes
`outcome` without a direction field, so the side is dropped for the events it emits.

**[MEASURED]** over the 15,768 `unit_*` packets, checking all three places the side can survive:

| event type | packets | side present | |
|---|---:|---:|---:|
| `unit_placed` | 145 | **145** | **100.0 %** |
| `unit_shadow` | 545 | 543 | 99.6 % |
| `unit_admitted` | 440 | 139 | 31.6 % |
| `unit_skipped` | 14,638 | 306 | 2.1 % |
| **total** | **15,768** | **1,133** | **7.19 %** |

Sources: `packet.direction` 852, `outcome.admission_unit_members[].direction` **277**, `candidate_id` 4.

**The shape of the gap matters more than its size.** 14,638 of 15,768 unit packets (92.8 %) are
`unit_skipped`, and **13,254 of those are `profile_missing_instrument_config`** — symbols the account has
no instrument config for, so no bar was fetched and no intent existed to carry a side. Another 919 are
`future_decision_bar_time`. For every packet that represents an actual **placement**, the side is
recorded **100 %** of the time.

**Correct behaviour.** Emit `direction` on `unit_admitted` (31.6 % today) — it is available at the call
site. The `unit_skipped` config-rejection packets have no intent and nothing to emit.

**What it would be worth.** No number the book sizes: `size_correlated_units` reads the side once, to
check `direction in (1, -1)` (`admission.py:1124-1125`), and never again. What it costs is
validatability on admitted-but-unplaced units. This session's validation does not validate side, and
says so.

**Correction note.** The first version claimed "`direction` is absent from 94.6 % of unit packets, so the
live book's trade side is largely unrecoverable", resting the side truth on "699 packets plus the 150
trade records". Adversarial review found a third source the claim and the measuring code both missed —
`outcome.admission_unit_members[].direction`, which recovers **277** packets whose side survives nowhere
else. Corrected: 1,133 recoverable (7.19 %), 92.81 % not, and the gap is concentrated entirely in
non-placements. `_direction_of` in `packet_validation.py` now reads that source; before the fix it
silently defaulted those 277 to `+1` while reporting the side as unrecorded.

## D5 — A shed unit loses its sizing audit trail

**Severity: low. Live-reachable.**

`_enforce_gross_open_risk_cap` rebuilds the shed unit with eight positional arguments
(`admission.py:1297-1298`), omitting the ninth field `overlays_applied`, which defaults to `()`. So a
unit shed by the cap keeps its confidence but loses the record of *why* it had that confidence — the
`kelly_lite_naN_xM`, `ladder_stepK` and `coloss_breaker` tags all vanish.

Reproduced; pinned by `test_gross_cap_shedding_zeroes_the_unit_and_labels_it`.

**Correct behaviour.** Carry `u.overlays_applied` through the rebuild.

**What it would be worth.** Nothing economically. It costs exactly the forensics that D1 needs: a shed
unit's tags are what would let an analyst reconstruct, after the fact, whether the cap shed a top-bin
Kelly day or a bottom-bin one. Given D1, that is the information you would most want and least have.

---

## D6 — `bridge.py` claims `admission.py` is a byte-identical copy of the route module. It is not.

**Severity: low (documentation), but it misdirects.**

`bridge.py:45-47`:

> Vendored into src (production must not import the research route dir …). **admission.py is a
> byte-identical copy of the route deploy module** (ultimate_book_live_package.py); a numeric-parity
> test asserts they stay identical.

**[MEASURED]** `src/components/ultimate_book/admission.py` is **1,741 lines**,
`research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/ultimate_book_live_package.py`
is **1,330**; SHA-256s differ. `admission.py` is a strict superset carrying 15 top-level names the
route module has no equivalent for, including `candidate_book_registry`, `market_expansion_registry`,
`resolve_market_expansion_sleeves`, `compute_stress_derisk_state`, `_enforce_gross_open_risk_cap`,
`_metals_confluence_pass`, `_learning_mult`, `A8_CONFLUENCE_SLEEVES`, `CANDIDATE_BOOK_PROFILE`,
`MARKET_EXPANSION_PROFILE`. `admit_and_size` in `admission.py` takes **9 parameters** the route version
does not.

**Correct behaviour.** Say what is true: `admission.py` is the live authority and the route module is
its ancestor; parity is asserted on the shared numeric core only.

**What it would be worth.** It cost this session a wrong first assumption — the route module was read
first as "the live sizing package", and it is not. Anyone porting, auditing or fixing the sizing chain
from the route copy would be working on code that has not been live since the candidate book and
market-expansion book were armed.

---

## D7 — `derisk_start_dd_pct` is configured, visible, and inert

**Severity: low. Live.**

`agent_config.yaml:1333` sets `ultimate_book_derisk_start_dd_pct: 0.07` with the comment "shrink size
from −7 % toward the −10 % wall". In `smooth` mode — which is what live runs
(`agent_config.yaml:1340`, and all 99,112 packets record `derisk_mode: "smooth"`) —
`evaluate_governor` never reads it: `admission.py:1260-1266` takes the `if` branch and
`derisk_start_dd_pct` appears only in the `elif`/`else`.

**Correct behaviour.** Either mark the key mode-specific in config, or have the smooth branch validate
that it is unset. An operator reading the config file today would reasonably believe full size is held
to −7 %; in fact size shrinks from the first basis point of drawdown.

**What it would be worth.** No behaviour change. It removes a live operator-mental-model error on the
key that governs how fast the book de-risks into the max-DD wall.

---

## D8 — `bridge.DEFAULT_CONFIG` disagrees with the live YAML on the two keys that decide the dial

**Severity: low as written (nothing live reads it), high if anything ever falls back to it.**

`bridge.py:72` defaults `ultimate_book_profile` to `CLEAN3_W7_FIRST_CYCLE_PROFILE` (**1.25 %**) where
live runs `clean3_w7_ceiling_nom2p00` (**2.00 %**); `bridge.py:87` defaults `derisk_mode` to `"band"`
where live runs `"smooth"`. Those two together are exactly the pair the ceiling interlock checks
(`admission.py:1367-1373`), so a caller falling back to the defaults would either size the book at 62 %
of the live dial or fail the whole book closed.

**Correct behaviour.** Fail closed on an absent dial key rather than defaulting it. `SleeveBookPolicy`
does this — `strict_config=True` refuses a config missing any of nine dial keys — but the live bridge
does not.

**What it would be worth.** It is the difference between a mis-sized book and a refusal. No live path
reads the defaults today; this is a trap for the next integration, and this session walked into it
(the first draft of the port read `DEFAULT_CONFIG`).

---

## D9 — The two confluence overlays cannot fire, because nothing populates their inputs

**Severity: low (dead code). Not live-reachable.**

`overlay_sizeup_for` gates on `intent.ll_impulse` and `intent.decision_hour`
(`admission.py:876-882`). **[MEASURED]** no live generator sets either field — the only occurrence of
`ll_impulse` anywhere under `sleeves/` is a comment (`metals.py:105`); probe control confirms the fields
exist on `TradeIntent` (`admission.py:850-851`; the earlier citation of `:836,838` pointed at
docstring lines). So `leader_impulse_veto` and `session_active_stack`
are unreachable even with `overlays=True`. Live also has `overlays: false`, so they are doubly dead.

**A third kill, found by adversarial review.** Both overlays declare their `base_sleeves` as
`sub_xvol_pullback` / `sub_mid_dn_revert` (`admission.py:310-319`) — clean_3 substrate sleeves. Live runs
`include_clean3: false`, so those sleeves are not in the effective 29-sleeve registry at all, and an
intent naming one would fail closed as `unknown_sleeve` before the confidence loop ever calls
`overlay_sizeup_for`. The overlays are dead **three** ways, not two: `overlays: false`, unset input
fields, and absent base sleeves.

Separately, `SESSION_ACTIVE_HOURS = {8, 12, 16}` (`admission.py:301`) are documented as "H4 **server**
hours" and would be compared against a UTC-derived `decision_hour` — the F7/B29 defect class — so if
the field were ever populated without conversion, the overlay would fire on the wrong bar.

**Correct behaviour.** Delete both overlays, or populate the fields via `_server_clock`. Deleting is
the honest option: they are validated size-*ups*, and re-arming them is a trading decision.

**What it would be worth.** Nothing today. It removes ~40 lines of code whose presence implies a
capability the book does not have, and it removes a latent wrong-clock comparison.

---

## D10 — `account` is hard-wired to "A", so `risk_per_unit_B` is unreachable

**Severity: low today, latent. Live.**

`UltimateBookLiveEngine.__init__` defaults `account="A"` (`book_engine.py:75`) and `book_owner.py`
never passes it; `book_engine.py:743` is the only call site. So both live namespaces size from
`risk_per_unit_A`.

Harmless at every balanced dial (A == B, including the live `clean3_w7_ceiling_nom2p00`), but
`staggered_1p00_0p50` (`admission.py:679-682`) would silently run symmetric at 1.00 % on both accounts
instead of 1.00 %/0.50 %.

**Correct behaviour.** Derive the side from the namespace, or delete the staggered profile.

**What it would be worth.** Nothing until someone selects a staggered profile, at which point it is a
2× risk error on one account with no error message.

---

## D11 — When a gate blocks, the bridge discards the reason the *sizing* refused

**Severity: low (observability). Live-reachable off-host.**

`admit_and_size` can refuse before the governor runs — the 2.0 %-ceiling smooth interlock
(`admission.py:1367-1384`) or an unknown profile (`:1356-1358`). Both return their reason in the
shadow dict. `UltimateBookAdmissionDecision` has no field for it: the gate branches overwrite the
top-level `reason` with the gate's reason (`bridge.py:480-506`) and the shadow's reason is not carried
anywhere.

So a config with a closed third gate and an uncertified dial reports only
`ultimate_book_live_activation_allowed_false`, and the fact that the book *would have refused anyway
because the dial is uncertified* is unobservable.

On the live host all four gates were open, so the recorded packets do carry the governor's reason and
nothing was lost in the fortnight. It bites on any non-live replay of a gated config — i.e. exactly
this session's use.

**Correct behaviour.** Add a `sizing_reason` field alongside `reason`.

**What it would be worth.** It is the difference between "we are not armed" and "we are not armed *and*
the dial is uncertified". `SleeveBookPolicy` works around it by exposing a
`sizing_refused_before_governor` diagnostic derived from the observable signature
(`governor is None` with no units) — a workaround, not a fix.

---

## D12 — `SESSION_H`'s named source of truth for the static registry is a different registry

**Severity: informational, but it would have misdirected the whole session.**

`SESSION_H:45-55` states that `ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl` "is your source
of truth for the static registry", and that had it been read as an unhydrated pointer, "you would have
ported nothing".

**[MEASURED]** its 82 rows contain **zero** occurrences of any live sleeve name — not `metals_core`,
`crypto`, `energy_agri`, `metals_softband`, `metals_ob_micro`, `fx_jpy_ny`, `idxrev`, `fx_jpy` (probe
control: the same probe finds `"ultimate_candidate_package"` 82 times and `"ETHUSD"` 14 times, so it can
see what it searches for). Its `sleeve_id` values are of the form
`fpsc_scheduler_lifecycle_merge_sleeve__broader_origin__liquidity_sweep_reclaim__long`, its schema is
`gtos.final_moonshot.ultimate_candidate_package.sleeve_registry.v1`, and every row carries
`default_off: true`, `runtime_effect_now: false`, `shadow_only: true`. It is the **broad** system's
outcome-mined candidate-family registry — the object `SECOND_AUDIT.md:170-176` cites when correcting the
owner's premise about signal overlap.

Nothing under `src/components/ultimate_book/**` reads it, or reads any `.jsonl` registry. The live
static registry is Python literals: `admission.SLEEVE_REGISTRY` (8 core), `candidate_book_registry()`
(9), `market_expansion_registry()` (12), resolved through `effective_registry`.

Pinned by `test_the_candidate_package_sleeve_ledger_is_not_this_registry`, which asserts empty
intersection *after* a probe control on the rows.

**What it would be worth.** Hydrating that file was harmless and it remains contract-bound for the
replay path (H1). But a session that took the prompt literally would have ported an 82-row shadow
registry of the wrong strategy family and produced a `SleeveBookPolicy` that measured nothing.

---

## Not defects — three things that look like defects and are not

Recorded because each cost verification time, and the next session should not re-spend it.

1. **The stress-derisk day offset is not a stale `+3` hardcode.** `book_engine.py:151-155` prefers the
   live-detected broker offset (`mt5.get_broker_offset_seconds()`) and falls back to the static
   `governor_daily_reset_offset_hours` **only on exception**. Since `compute_stress_derisk_state` groups
   deals by *server-local* date (`admission.py:446` decodes a broker epoch), the detected server offset
   is the correct input. An earlier draft of this register claimed otherwise; retracted. B54 reached the
   same conclusion for the governor's own window.
2. **`realized_units` being empty is not a bug.** The third gate suppresses *placement* while sizing is
   still computed in full, so `would_units` is the book's decision and `realized_units` is what bore
   risk. Reading the latter as "the decision" would make all ~99k shadow packets read as an empty book.
   `SleeveBookPolicy` reads `would_units` for exactly this reason.
3. **`include_clean3: false` under a profile named `clean3_w7_ceiling_nom2p00` is deliberate.** The
   package docstring says the W7 dials are for use "ONLY with include_clean3=True"
   (`admission.py:781`), but `agent_config.yaml:1264-1270` records the owner-approved 2026-06-15 drop of
   the three clean_3 sleeves as selection-glow, re-validated on core-8 by `CYCLE62_CORE8_REVALIDATION`.
   The docstring is stale, not the config. (This is F10's territory.)
