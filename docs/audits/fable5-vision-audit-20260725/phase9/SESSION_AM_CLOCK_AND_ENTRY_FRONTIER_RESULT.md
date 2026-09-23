# Session AM — the clock re-derivation, and the entry lever is one hour and not four

**Branch `phase9/clock-entry`. Blocks B1200–B1249. Not merged.**
**Scoped verification (agreement §2): see §9.**

---

## 0. Headline

**Two things this session settled, and the second one was not what it was sent to find.**

**1. `sub_mid_dn_revert` was rejected on evidence a clock defect produced.** Repaired, re-derived over
the whole archive, and A/B'd against a control arm that reproduces AA's 503 trades *exactly* — same
count, same ΣR, identical trade-key set — the sleeve is a materially different and better thing:

| | repaired (server clock) | authored (raw UTC, = AA) |
|---|---:|---:|
| trades | **533** | 503 |
| gross R/trade | **+0.4784** | +0.3996 |
| pooled OOS R/day | **+0.2105** | +0.1117 |
| raw p | **0.0198** | 0.1975 |
| OOS positive folds | **0.80** | 0.60 |
| **drop-best retention** | **+0.3609** | **−0.1988** |
| q in AA's 69-look family @ α 0.10 | **0.4554** | 1.0 |

The populations share only 235 trades (jaccard 0.293). The repair adds 298 averaging +0.4362 R and
removes 268 averaging +0.2836 R. **The robustness statistic changes sign**: on the wrong clock the whole
edge was one fold and dropping it went negative; on the right clock a third survives. It still fails
robustness and significance, so it does not admit — but AD's "nearest miss in the core book" was
measured on the wrong population, and on the right one it is a much nearer miss. AD's B753 carry
restatement **survives** (UNCONDITIONAL on both accounts) on a much thinner margin: charged nights
1.308 → 1.850 on FTMO, and redacted_account is UNCONDITIONAL by **+0.0119 R at the p99** — 1.2 % of a risk
unit.

**2. The entry lever AH routed as "move to the first H4 close" is one hour, not four.** The `fx` hour
premium is a one-hour spike (16.67× at broker 00, 1.333× at 01, 1.0 from 02), and on AH's own
16,337-trade population **one hour of delay buys 94.4 % of the cost saving four hours buy** — 93.5–98 %
across every composition and band. Where the gross can also be measured (the M15 window), the **net**
frontier peaks at **1–2 hours** and is *negative* at both 0 h and AH's 4 h: `atr_mean_reversion`'s own
optimum is 1 h (−0.162 → −0.091, still negative), `volume_surge_reversal`'s is 2 h (+0.110, and AH's
4 h gives back 32 %). A smaller change to the sleeve contract, strictly better on the axis AH found the
shift hurting. Owner decision, same class as AH's.

**And two the session was sent to find, which came back negative in a useful way.**

**3. The H4 hour-00 subset separates the two effects AH superposed — and they are independent.** Cost:
entering at broker 00 pays **0.482 R**, 48 % of the risk unit; one bar later pays 0.119 R, with 96.4 % of
the control's mirror-image *rise* attributable to the hour. The control **inverts** rather than merely
failing to move, because 11,789 of its 57,661 bars close at server 20 and one bar later lands them *on*
the rollover. Gross: my first mechanism ("the rollover distorts the mid") is **refuted by that same
control**, and the replacement is sharper — the gross gain tracks the **decision bar's** hour, with
`sign(Δgross) = −sign(pre-entry drift)` on **6 of 6** cells, r = **−0.915**.

**4. AH §6's era-anchor bias is unconfirmed, unidentifiable, and worth zero verdicts.** 12 of 43 FTMO H4
symbols are outside its scope by construction; the boundary test fails its own refutation condition
(forward and reverse disagree in sign once oriented) and is too underpowered to estimate the residual;
and — decisively — at **full** magnitude on all four of AH's entry arms it moves **0 of 42 member
verdicts, 0 of 3 family verdicts, and 0 members across zero**. The repair that survives is a **band
widening**, not a level shift: 536 eras, 0 becoming undecidable.

**Eleven things I got wrong are in §5, nine of them found by an adversarial pass over my own claims** —
including one where my own driver's docstring named the refutation condition and I published a number
that trips it.

---

## 1. `sub_mid_dn_revert` on the clock it was mined on — item 1 [B1200–B1209]

### 1.1 The repair, and what it changes

`substrate._utc_hour` returned the raw UTC hour; `substrate_engine._bucket_session` cuts it at 8 and
16 — boundaries copied verbatim from a route that parsed naive MT5 CSV stamps, i.e. **broker wall
clock** (`wave1_structure_setups_ict._load_one:71-74`). `sub_mid_dn_revert` (`registry.py:55`, `BUILT`)
carries `session=ny` as one of seven cell conditions, so the bucket is part of its firing rule.
Renamed `_session_hour` and routed through `_server_clock.server_hour`, fail-closed as before.

On this archive's grid the H4 opens are server 00/04/08/12/16/20 and **exactly three change bucket**:
server 00 (asia, read as ny), 08 (london, read as asia) and 16 (**ny**, read as london). So
`session=ny` moves from server-hour **{20, 00}** to **{16, 20}** — the two populations share only the
server-20 bars. That is why B971 measured 185,548 of 370,808 bars (50.04 %) shifting, and why this is
a re-derivation rather than a rescale.

### 1.2 The A/B, and the control that makes it a measurement

Both arms were generated through the **same** driver, the same `GenerationPort`, the same H4 union close
grid over the same symbol set, and the same labelling — the only difference is
`supply.authored_clock("substrate")`, which restores the pre-B1200 raw-UTC read. The control is that
the authored arm must *be* AA's population, and it is, exactly:

| control | AA | this driver's `authored_utc` arm |
|---|---:|---:|
| n | 503 | **503** |
| Σ R gross | 201.0 | **201.0** |
| trade keys | — | **identical set, 0 only-AA, 0 only-mine** |

So everything below is attributable to the clock and to nothing about how this driver walks the archive.

| | **repaired (server)** | authored (raw UTC) |
|---|---:|---:|
| n | **533** | 503 |
| mean R gross | **+0.4784** | +0.3996 |
| Σ R gross | **255.0** | 201.0 |
| win fraction | **0.3696** | 0.3499 |
| capture ratio (R/MFE) | **0.2641** | 0.2199 |
| median hold | 28.0 h | 28.0 h |
| p90 hold | 100.0 h | 88.0 h |
| decision-bar server hours | **{16: 298, 20: 235}** | {00: 268, 20: 235} |
| entry server hours | **{20: 298, 00: 235}** | {04: 268, 00: 235} |

**The two populations share 235 trades — exactly the server-20 bars — jaccard 0.293**, and a shared
trade is byte-identical in R across the arms (asserted, `True`). The repair therefore **adds 298 trades
and removes 268**, and the exchange is favourable in both directions:

- the 298 the repair **adds** (server-16 decision bars) average **+0.4362 R**;
- the 268 it **removes** (server-00 decision bars) average **+0.2836 R**.

Net: **+19.7 % on mean gross R and +26.9 % on ΣR, on 6 % more trades.** The sleeve was AD's "nearest
miss in the core book" measured on the wrong population; on the right one it is a *better* sleeve, not a
worse one. Every published number for it — AA's 503 rows and its `AA_ESTATE_WALK` verdict,
`EXIT_FRONTIER_V1`'s frontier, `SURVIVOR_BOOK_V1`'s tier and AD's B753 restatement — describes the
503-trade population.

**One operational consequence that links this item to item 3.** The repaired population's entries are
at server **{20, 00}**: 235 of 533 — **44 %** — still fill at the rollover. So the one-hour entry
prescription of §3 applies to this sleeve too, and it is not a `mx_*` D1 sleeve, which widens that
prescription beyond the FX D1 cohort AH scoped it to.

### 1.3 The gate verdict: the sleeve is 10× closer to admission, and its robustness statistic changes sign

`run_gate(..., diagnose=True)` on both arms, `B_balanced`, AA's `declared_family_size = 69`. **Control
first**, because it is what licenses the rest: the `authored_utc` arm reproduces AA's published verdict
for this sleeve **to full precision** — verdict `REJECT`, pooled `0.11172728506920303`, p
`0.1974802519748025`, q 1.0, all identical.

| | **repaired (server)** | authored (= AA) |
|---|---:|---:|
| verdict | REJECT | REJECT |
| n | 533 | 503 |
| pooled OOS R/day | **+0.2105** | +0.1117 |
| raw p | **0.0198** | 0.1975 |
| OOS positive folds | **0.80** | 0.60 |
| lifetime R/trade | **+0.3097** | +0.2298 |
| drop-best retention | **+0.3609** | **−0.1988** |
| gross R/trade | +0.4689 | +0.3735 |
| cost as % of \|gross\| | 9.18 % | 8.52 % |
| coverage | 1.00 | 1.00 |
| failing gates | robustness, significance | robustness, significance |
| q in AA's 69-family @ α 0.10 | **0.4554** | 1.0 |

**Read the retention row first.** `drop_best_retention` is the robustness gate's own statistic: what
survives when the best fold is removed. On the wrong clock it is **−0.1988** — the sleeve's entire edge
was one fold, and dropping it turned the sleeve negative. On the right clock it is **+0.3609**: a third
of the edge survives. That is a qualitative change in what the sleeve *is*, not a shift in a number.

Alongside it: pooled OOS R/day nearly doubles, raw p improves **10×** (0.1975 → 0.0198), OOS positive
folds go 3/5 → 4/5, and q inside AA's own 69-look family falls from 1.0 to 0.4554. Largest cost term is
`spread_r` on both arms; the primary prescription is `REGIME_GATE_OR_PARK` on both.

**It still does not admit** — robustness and significance both still fail, and 0.4554 is not 0.10. The
honest statement is that a sleeve AA rejected at p 0.20 on a mis-clocked population sits at p 0.020 on
the right one, with a robustness statistic that has changed sign, and that this is the difference
between "rejected" and "the nearest miss in the core book, for real this time". At ≤ 5 declared looks it
would admit under BH α = 0.10; the declared family is 32.

**On scope, stated rather than glossed:** this is a **1-sleeve** gate, not the 32-sleeve family run. The
family run costs ~30 machine-minutes per clock because it re-diagnoses the other 31 sleeves, which this
session does not change, and it did not finish in session. Every per-sleeve input above — expectancy,
lifetime, stability, robustness, coverage, `p_raw`, the whole diagnostics block — is computed from this
sleeve's own trades and is independent of its siblings; only `q_value` and the `significance` gate read
the family, and the q column is reconstructed from AA's **own** published p-values for the other 31
sleeves using `gate.py:797`'s padding rule (AK's `q_at`, same arithmetic). The control above is what
makes that substitution checkable rather than asserted.

### 1.4 The carry tier: AD's B753 conclusion survives the re-clock, on a much thinner margin

AD's B753 restated this sleeve from `CARRY_CONDITIONAL` to **UNCONDITIONAL on both accounts** using
AA's holds — which are the *authored-clock* holds. Re-run with `ad_carry_tiers`' own rule and helpers
imported (one implementation, not a reimplementation), changing only the hold distribution:

| cell | published | restated | mean nights | p99 | break-even | headroom | net @ mean | net @ p99 |
|---|---|---|---:|---:|---:|---:|---:|---:|
| **repaired · FTMO** | CARRY_CONDITIONAL | **UNCONDITIONAL** | 1.850 | 10.00 | 11.221 | 6.07× | +0.2263 | **+0.0295** |
| **repaired · redacted_account** | CARRY_CONDITIONAL | **UNCONDITIONAL** | 1.704 | 8.00 | 8.371 | 4.91× | +0.2133 | **+0.0119** |
| authored · FTMO *(= AD's B753)* | CARRY_CONDITIONAL | UNCONDITIONAL | 1.308 | 7.00 | 11.221 | 8.58× | +0.2394 | +0.1019 |
| authored · redacted_account *(= AD's)* | CARRY_CONDITIONAL | UNCONDITIONAL | 1.177 | 7.00 | 8.371 | 7.11× | +0.2302 | +0.0439 |

**Control: the authored arm reproduces AD's published `nights_measured` exactly** — mean 1.3082 /
1.1769 and p99 7.0 / 7.0 — and the tier rule reproduces the published tier from the artifact's own
inputs on 4 of 4 cells.

**The verdict holds and the margin does not.** Charged nights rise 1.308 → 1.850 on FTMO (+41 %) and
the p99 goes 7 → 10 (+43 %); headroom falls 8.58× → 6.07× (FTMO) and 7.11× → 4.91× (redacted_account). The
`UNCONDITIONAL` test is on the p99, and there the redacted_account margin is now **+0.0119 R — 1.2 % of a
risk unit.** On the wrong clock it was +0.0439. This sleeve is UNCONDITIONAL by a hair on redacted_account,
and anything that lengthens its tail takes it back.

**Why the nights rise, measured rather than guessed.** The wrong clock put 268 of 503 entries at
server **04**, which have 20 hours before the first midnight; the right clock puts 298 of 533 at server
**20**, which cross a midnight after four. Same median hold (28.0 h on both arms), 41 % more charged
nights — the entry hour, not the hold, is what moved.

**Population caveat, and its direction.** The edge terms (`gross_r`, `true_cost_ex_swap_r`,
`swap_r_per_night`) are the survivor book's, measured on W7 caches built on the *authored* clock; only
the holds are re-clocked. So the repaired column mixes a repaired hold distribution with an unrepaired
edge estimate — AD's §5 caveat, one layer deeper. The direction is conservative: the re-clock **raises**
gross by 19.7 %, so a fully re-clocked edge term would make the tier more secure, not less.

### 1.5 Two defects the repair introduced, and one edit withdrawn [B1201]

Neither was visible in a passing test, and both were found by A/B-ing the scoped suite — the first
against the wrong base, which is how they surfaced at all (§9).

1. **`replay_policy.generation_lineage` could not see the new clock owner.**
   `clock_dependent_sleeves()` derives the set of clock-OWNING sleeve modules by scanning this
   package's source for the literal `_server_clock import`. My first import form was
   `from . import _server_clock as _sc`, which is invisible to it — so `substrate` became a clock
   owner outside the live-lineage register, and a `deployed_lineage()` replay would have run the
   **repaired** clock for `sub_mid_dn_revert` while claiming to reproduce the VPS. That is precisely
   the silent divergence that register exists to prevent. Import form changed to the detectable one,
   with the reason in a comment so it does not get tidied back.
2. **`DEPLOYED_HELPERS` now carries `substrate: {_session_hour: pre_b1200_utc_hour}`.** The file exists
   at `redacted_host` with the raw-UTC `_utc_hour`, so the deployed behaviour is reproducible and it
   belongs in `DEPLOYED_HELPERS` rather than in `main`'s new `NO_DEPLOYED_LINEAGE`.
   `pre_b1200_utc_hour` is transcribed separately from `pre_b29_hour` for the reason
   `pre_b29_hour_vss` records — the deployed bodies differ off the happy path (this one
   `astimezone`-normalises a tz-aware stamp and *raises* on a string where `pre_b29_hour` slices it)
   and a shim that behaves differently there is not the same program. Verified behaviourally: mainline
   reads server 17 → `ny`, the deployed lineage reads UTC 14 → `london`, and the round-trip restores.

**And one edit withdrawn.** I corrected `substrate_engine._bucket_session`'s docstring ("h is the
bar's UTC hour", which B1200 made wrong on mainline) and then reverted it, because that module is a
byte-faithful copy of the locked route file whose own contract says *do NOT diverge*, and because the
lineage register derives "which modules diverged" from `git diff --name-only`, which cannot tell a
docstring from behaviour — the cosmetic edit put `substrate_engine` in that set and would have forced
a register entry for a module that owns no clock. The statement lives in `substrate._session_hour`
instead, and a new test pins the vendored file to the deployed lineage **by sha256** so the next
person has to argue the classification in the same change.

### 1.6 The armed book: the intents cannot move, the SIZE can — and the "because" I first published was not sufficient

I claimed the repair "cannot move the ARMED book, because `sub_xvol_pullback` is built
`need_hour=False`". The mechanism half is verified, independently and thoroughly: `_session_hour` has
exactly one caller in the tree (`substrate.py:119`, under `if need_hour`), `_bucket_session` exactly
one (`substrate_engine.py:189`, under `if st["hour"] is not None`), `XVOL_CONDS` has no `session`
key, `regime_spine/{state,conditions}.py` import `substrate_engine` but call only `_ac` and
`stop_target`, and a real-archive A/B returns **48 vs 48 byte-identical `sub_xvol_pullback` intents**
under the two clocks. Three files change under `src/`, none R2-bound, so no H1 re-seal.

**But the conclusion does not follow from that premise, and an adversarial pass found the channel.**
`sub_mid_dn_revert`'s firing set *does* change, and it feeds `n_active_by_day` — the Kelly-lite
conviction breadth count (`admission.py:1143-1148`), which `:1186-1189` turns into `na` and `:1199`
applies as `su_combined = min(su * kelly_mult, OVERLAY_SIZEUP_MAX)` to **every unit that day, armed
ones included**. `kelly_lite`, `kelly_conservative` and `kelly_running_count` are all `true` live.
So on a bin-edge crossing the repair moves the armed sleeves' *size* by 25–32 % — the same mechanism
AK's B970 filed and `CLAUDE.md` §4 already records as a +25.2 % event.

**Why it is inert today, stated as three conditions rather than one fact:** `sub_mid_dn_revert` is a
clean_3 sleeve, so it needs `ultimate_book_include_clean3` (mainline `false`, host **[UNVERIFIED]**);
the FTMO launcher passes `--tags crypto,energy_agri,sub_xvol_pullback`, and `--tags` can only subset;
and this repair is not on the VPS at all. Remove any one of those and the coupling is live. Filed as a
repair-queue row rather than left in prose.

---

## 2. The H4 FX hour-00 subset: the rollover effect isolated, and its own control inverts — item 2 [B1210–B1219]

AH's D1 design superposed two things it could not separate: a **cost** effect (the fill leaves the
13×–38× hour) and a **D1 mechanism** effect (a D1 signal four hours stale). Every D1 close is at the
rollover, so there was no within-cohort contrast to break them apart.

An H4 decision bar's close lands on broker 00 for one sixth of the grid, and for those the shift is
**one bar of the sleeve's own timeframe**. The same members' other-hour bars are then a control that
AH could not build. Population: AF's three H4 mechanisms × the 14 `fx`-class symbols = **42 members**,
**205,080 arm-rows**, intersected to **63,554 decision bars** where all three arms produced a trade
and arm A is engine-reachable.

**Arm A reproduces `AF_FAMILY_TRADES.json.gz` on 42 of 42 members, exact on both count and summed R.**
An adversarial pass went further and found all 68,360 arm-A rows field-identical to AF's on 16 fields
with `engine_reachable` agreeing 66,829/66,829. Read it for what it is: a **determinism control on a
shared code path** — same generators, same `replay`, same `maxbars=80`, same archive — not independent
corroboration of AF's economics. What it buys is that the arms below differ by the entry instant and
by nothing about how this driver walks the archive.

| subset | arm | n | gross R | Δgross | cost R | saving | **net Δ** | entry hours |
|---|---|---:|---:|---:|---:|---:|---:|---|
| **hour-00** | A (broker 00) | 5,893 | −0.00384 | — | **0.48209** | — | — | 00 |
| | **C (+4 h)** | 5,893 | +0.03941 | **+0.04325** | 0.11938 | **0.36271** | **+0.40596** | 04 |
| | D (+8 h) | 5,893 | +0.05670 | +0.06054 | 0.13184 | 0.35024 | +0.41078 | 08 |
| **control** | A | 57,661 | +0.00997 | — | 0.13589 | — | — | 04/08/12/16/20 |
| | C (+4 h) | 57,661 | −0.00347 | **−0.01344** | 0.21186 | **−0.07598** | **−0.08941** | **00**/08/12/16/20 |
| | D (+8 h) | 57,661 | −0.01004 | −0.02001 | 0.20789 | −0.07201 | −0.09202 | 00/04/12/16/20 |

**The control does not merely fail to move — it inverts, and the reason is the mechanism made
visible.** 11,789 of the control's 57,661 bars close at server 20, so shifting them one bar puts the
fill **into** the rollover: the control's cost *rises* by 0.076 R while the hour-00 subset's falls by
0.363 R. Same operation, opposite sign, decided entirely by which hour it lands on. The rollover, not
"one bar later", is the whole effect.

**The cost half is the finding, and it is clean.** The hour-00 A-arm pays **0.482 R** of cost — 48 % of
its risk unit — against a gross of −0.004: cost dominates gross by more than 100:1 there. Under AH's
`half_at_each` attribution the C-arm saving is 0.1817 R instead of 0.3627, so the conclusion survives
either reading and the magnitude is a range, which is AH §3.1's discipline applied. An adversarial pass
decomposed the control's cost rise and found the rollover accounts for **96.4 %** of it (hold
contributes −0.0002 R, symbol mix nothing, era drift 0.16 % of rows), and confirmed the 20 → 00
mapping is exact: the A@hour-20 key set is set-equal to the C@hour-0 key set, 11,789 = 11,789.

**The gross half is NOT what I first published, and the correction is a better finding.** My first
version read the hour-00 gross gain (+0.04325 R) together with its negative pre-entry drift (−0.0206)
as *"the rollover distorts the mid, so entering there is a bad fill in price terms too"*. An
adversarial pass refuted that with my own control, and the replacement is sharper:

1. **Moving the entry ONTO the rollover also gains gross — more, in fact.** The control's 11,789
   decision-hour-20 bars have their arm-C entry *at* broker 00, and that shift gains **+0.04952 R**
   (day-clustered t +3.69) against the hour-00 cell's +0.04325 (t +2.18). By my own metric the
   rollover fill is the *better* fill, 1.65× over. So the mid-distortion story is dead.
2. **The gain tracks the DECISION bar's hour, not the entry instant.** Across all six decision-hour
   cells `sign(Δgross A→C) = −sign(pre-entry drift)`, **6 of 6, r = −0.915**. Decision hours 00 and 20
   are the two negative-drift cells and the only two with positive Δgross. One bar of delay pays
   exactly where the intervening bar reverts against the signal — a decision-bar reversion effect,
   orthogonal to the rollover.
3. **"Drift accounts for about half the gain" was structurally impossible** and I should have seen it:
   the driver re-anchors stop and target at the shifted entry, so the achievable R set is identical
   across arms. 5,774 of 5,893 rows (98.0 %) exit at a re-anchored stop (exactly −1.0) or target
   (exactly +2.0/+4.0) in *both* arms and carry 89.8 % of the delta on rows whose R cannot see the
   entry price at all. Drift can act additively on only 119 rows (2.0 %, +0.0044, ≤ 10.2 %), and the
   whole delta is **757 flipped trades** — 419 stop→target at +0.2164 and 338 target→stop at −0.1775.
   0.0206/0.04325 = 47.6 % was a coincidence with no channel behind it.
4. **The control's pooled Δgross of −0.01344 is therefore a mixture** of cells with opposite signs, and
   should be read as "the average price of one-bar delay across five decision hours", not as a clean
   staleness constant. Pooled across arms, entry hour 00 is the 2nd-best of six entry hours on gross
   (+0.01106) and entry hour 20 the worst (−0.02706).

**Net of all that, item 2's commission is answered and the answer is cleaner than the question.** The
rollover is a **pure cost effect** (0.482 → 0.119 R, 96.4 % attributable to the hour). The gross effect
of a one-bar delay is a **separate, decision-hour reversion effect** that has nothing to do with the
rollover and is measurable on either side of it. Those are exactly the two things AH's D1 design
superposed, and they are now separated — just not by the mechanism I first proposed for the second one.

**A correction to the brief, and to my own driver's docstring.** "One sixth of an H4 FX trade's fills
land at broker 00" is not what these generators do: the decision-bar hour histogram is
`{00: 7,374, 04: 8,663, 08: 7,764, 12: 14,313, 16: 15,173, 20: 15,073}` — hours 12/16/20 fire about
twice as often as 00/04/08, because a donchian breakout needs an active session. The hour-00 share is
**10.8 %** of decision bars before intersection and **9.3 %** after, not 16.7 %.

**And 19.2 % of the hour-00 bars are structurally undroppable-but-dropped**: 1,418 of 7,374 are the
Friday-night close (server Saturday 00:00), whose next H4 close is 52 h away. That is a session gap
rather than a later fill, so `MAX_SHIFT_HOURS` removes them — counted, not assumed away. Note
`excluded_not_reachable = 0`: on the H4 union grid the two-interval freshness rule and the
weekend-gap rule select the same bars, so reachability excludes nothing the shift rule has not already
taken.

**Nothing admits, and it was never going to.** The bill is 726 declared looks (AF 276 + AH 180 + this
session's 3 arms × 45 cells × 2 subsets = 270) and the best raw p in the whole grid is 0.0324
(`mxf_energy_fvg_retest_usdchf_h4`, control, arm A) — which needs a family of ≤ 1 at α = 0.05. The
verdicts are not the deliverable; the **entry-instant decomposition** is, and 15 of 42 members are
NOT_EVALUABLE in the hour-00 subset on sample depth alone.

---

## 3. The entry lever is ONE hour, not four — item 3a [B1220–B1224]

This is the session's most useful number and it did not need a single new bar.

AH moved the FX D1 cohort's entry from the D1 close (broker 00:00) to the first H4 close (+4 h) and
measured a modelled cost saving of +0.1567 R against a gross loss of −0.015 R. It could not price
anything between 0 h and 4 h **because the H4 grid has no point there** — and its own routing to
wave 9 said so.

But the **spread** half of cost does not need a bar. Run on AH's intersected arm-B population —
**16,337 trades, the same population AH published** — at the `mid` band, re-pricing each trade at an
entry instant `h` hours later with the hold shortened by the same `h`:

| shift | cost R (`v2_damped`) | saving vs 0 h | % of the 0–8 h best | cost R (`v1_multiplicative`) |
|---:|---:|---:|---:|---:|
| **0 h** | **0.23320** | — | — | **0.50896** |
| **1 h** | **0.08563** | **0.14757** | **94.40 %** | **0.08563** |
| 2 h | 0.08131 | 0.15188 | 97.16 % | 0.08131 |
| 3 h | 0.08416 | 0.13620 | 95.35 % | 0.08416 |
| 4 h (AH's arm C hour) | 0.07723 | 0.15597 | 99.78 % | 0.07723 |
| 5 h (best on this grid) | 0.07688 | 0.15631 | 100 % | 0.07688 |
| 8 h | 0.08247 | 0.13774 | 96.43 % | 0.08247 |

**One hour of delay buys 94.40 % of the best cost saving reachable on the 0–8 h grid, and 94.9 % of
what AH's four-hour arm C actually saved.** Three corrections an adversarial pass forced into those
two numbers, none of which changes the conclusion and all of which change the wording:

- **it is the best on the 0–8 h grid, not "the best achievable".** The 8 h cap is AH's own
  `MAX_SHIFT_HOURS`. Extend the same construction to 0–24 h and the best is 18 h at 0.15734, which
  puts one hour at **93.79 %**; on 0–12 h the best is 12 h and one hour is 94.31 %. The fraction is
  also cell-specific: 97.98 % under `v1_multiplicative`, 95.04 % at band `low`, 93.46 % at band
  `high`. Every one of those is ≥ 93.5 %, which is why the conclusion holds and the single number
  does not.
- **it is not an "exact re-pricing" of the whole bill, and the reason is worth knowing.** Checked term
  by term: **swap is bit-identical (0.0158392) at every shift 0–23 h**, because `rollover_nights`
  counts midnights strictly after entry and 100 % of this population enters at broker hour 00 — it
  first moves at 24 h. Commission is not re-priced at all (it keys on the unshifted `entry_price`;
  AH's real +4 h re-walk moved it by 7.6e-8 R). Slippage is hour-blind by construction. So the total
  saving equals the **spread** saving to six decimals at every shift: this is a spread-model frontier,
  exactly and only.
- **it is not a prediction of arm C.** AH's arm C is a full re-walk, whose exit instant differs from
  the shift-0 trade on 46 % of rows; its measured saving is 0.15564 R against my synthetic +4 h
  0.15597 R. Holding the trade fixed and moving only the priced instant is what isolates the cost
  term — the gross term is measured separately in §3.1, and the two must be read together.

The reason for the shape is in the model's own hour table: the `fx` premium is a **one-hour spike** —
hour-of-day medians 16.67× at broker 00, **1.333× at 01**, 1.0 from 02 (`jpy_fx` 12.56× then 1.167×;
`metals`, `index`, `energy` and `crypto` have no cell above 1.5× anywhere in the week). **Six** of the
120 populated `fx` cells exceed 1.5×: the five daily rollovers (hour-of-week 0/24/48/72/96) at
11.0–23.2×, plus hour-of-week 119 — broker Friday 23:00 — at 1.667×, which this shift grid never
reaches. An earlier draft said "only five, all at hour-of-week ≡ 0 (mod 24)"; that missed the Friday
cell and over-counted the table at 168 rather than 120.

Four things make this readable rather than a coincidence:

- **the shift-0 level reproduces AH.** 0.23320 against AH's published 0.2327 (AH sampled 1-in-5; this
  prices every row), i.e. 0.2 % apart on the same trades. My first version of this stage priced
  17,888 rows instead of AH's intersected 16,337 and came out 6.5 % low — a population difference
  reading as a cost difference, and the parity control is what caught it.
- **the 4-hour saving reproduces AH under v1 too.** 0.50896 − 0.07723 = **0.43173** against AH §3.1's
  published `v1_multiplicative` saving of **0.4318**.
- **the conclusion survives both compositions; the fraction is not the same number in both.**
  Every *shifted* hour (1 h…8 h) is identical between `v2_damped` and `v1_multiplicative`, because
  those entries occupy broker hours 01–08 where the highest `fx`/`jpy_fx` multiplier is 1.3333, below
  `PREMIUM_FLOOR = 1.5`, so `damped_intraweek_mult` returns the reference multiplier unchanged — measured, 0 of 16,337 trades
  clear the floor at any shift 1–8 and 16,337 of 16,337 clear it at shift 0. (Hour 00 is not the only
  damped cell in the table — `fx` at broker Friday 23:00 is 1.6667 and is damped too; it is simply
  unreachable by this shift grid. An adversarial pass caught that over-generalisation.) The fraction
  therefore **does** move, because the shift-0
  level sits in both numerator and denominator: **94.4 % under v2, 98.0 % under v1.** An earlier draft
  of this section called the fraction "composition-independent", which is false and was corrected by
  an adversarial pass — the levels are, the fraction is not, and the honest statement is that one
  hour captures 94–98 % of the achievable saving on either composition.
  It **is** attribution-independent: the saving is entirely spread (0.1908 → 0.0432 = 0.1476, which
  is the whole 0.14757), so AH's `half_at_each` reading halves numerator and denominator alike and
  the fraction does not move. The *level* does not halve — swap, commission and slippage are not
  attributed at entry.
- **swap is identical at every shift** (0.0158392 R) — and it is invariant *by construction* rather
  than measured-as-stable: `rollover_nights` counts midnights strictly after entry and every trade in
  this population enters at broker hour 00, so the count first moves at a 24 h shift. Nothing in this
  table is a carry artifact.

**The frontier is not monotone**, which is worth knowing before anyone picks 3 h or 8 h: broker 03
and 08 carry their own session-open premium (`fx` 1.2× at both), so those hours are worse than 2 h and
7 h.

**Why this matters more than the 4-hour version.** AH measured that the four-hour shift costs
−0.015 R/trade of gross overall and that the loss is concentrated in the reversion members, whose
pre-entry drift runs to +0.096 R on `cadjpy` over those four hours. A one-hour delay pays a fraction
of that drift for 94 % of the saving. **The prescription is therefore not "move to the first H4
close" — it is "move off the rollover hour by one hour".** That is a smaller change to the sleeve
contract, and it is strictly better on the axis AH found the shift hurting.

**Still Borhen's, and for the same reason AH gave**: the entry convention is a contract, not a
research finding. What changed is the price of the option.

### 3.1 The gross half, measured — and AH's four hours is past the peak on both mechanisms [item 3b, B1225–B1229]

The cost half above is exact and complete. The gross half needs a price at the shifted instant, which
needs M15 bars, and the M15 archive begins 2024-01-02. So this panel is a **2.6-year window against
the cohort's 26 years** and it says so rather than extrapolating. Population: the two reversion
mechanisms × 14 `fx` symbols, **822 decision bars** where every shift produced a trade and the bar is
engine-reachable, with the exit replayed on **M15 bars for every arm including shift 0** (maxbars
7,680 = 80 trading days) so the exit resolution is constant and only the entry moves.

| shift | gross R | cost R | **net R** | pre-entry drift |
|---:|---:|---:|---:|---:|
| 0 h | +0.14105 | 0.17432 | **−0.03327** | 0 |
| **1 h** | +0.08689 | 0.05829 | **+0.02860** | +0.00817 |
| **2 h** | +0.08619 | 0.05681 | **+0.02938** ← peak | +0.01929 |
| 3 h | +0.07552 | 0.05784 | +0.01768 | +0.03015 |
| 4 h (AH's arm C) | +0.04297 | 0.05613 | **−0.01316** | +0.04139 |
| 8 h | +0.02893 | 0.05631 | −0.02738 | +0.05754 |

**Gross decays monotonically with delay and cost is flat after the first hour, so the net frontier has
an interior maximum at 1–2 hours — and AH's four-hour shift is past it, back into negative territory.**
Pre-entry drift rises monotonically from +0.008 at 1 h to +0.041 at 4 h, which is the mechanism AH
named being paid for hour by hour.

Split by mechanism, and the split is the answer to the item as written:

| mechanism | n | 0 h | 1 h | 2 h | 3 h | 4 h | 8 h |
|---|---:|---:|---:|---:|---:|---:|---:|
| `atr_mean_reversion` net | 326 | −0.1622 | **−0.0911** | −0.0934 | −0.1025 | −0.1466 | −0.1523 |
| `volume_surge_reversal` net | 496 | +0.0515 | +0.1073 | **+0.1101** | +0.0967 | +0.0745 | +0.0548 |

- **`atr_mean_reversion`'s own shift is ONE hour**, it nearly halves the loss (−0.162 → −0.091), and
  **it does not turn the mechanism positive.** Its gross is already negative at 1 h (−0.029) and falls
  to −0.087 at 4 h. So the answer to "the mechanism's repair is a shorter delay" is: yes, one hour, and
  entry timing alone does not fix it. AH's four hours costs this mechanism 0.056 R/trade against the
  one-hour cell — nearly as bad as not shifting at all.
- **`volume_surge_reversal` peaks at two hours** at +0.110 and AH's four hours gives back **32 %** of
  that. It is the mechanism carrying the pooled result.

Read the levels as within-panel only: the shift-0 cost here is 0.174 R against 0.233 R over the whole
archive, because 2024-2026 era ratios sit near 1 and the pre-2010 FX eras are absent. The **shape** is
what transfers, and the shape is what the decision needs.

---

## 4. The era anchor: unconfirmed, unidentifiable, and worth 0 verdicts — item 4 [B1230–B1244]

AH §6 sized a min-to-median inflation of **up to 1.50× on constant-spread FX eras**, called it
conservative in direction, and routed the repair to wave 9 as "re-derive the era table on a
min-consistent anchor". The brief's instruction assumes the bias is real at that magnitude. Nothing
measurable here confirms it, and — the part that decides the item — **it is worth zero verdicts even
at full magnitude.** Four findings, and the last one is the only one a decision needs.

### 4.1 The scope is narrower than AH states, by construction

`era_ratio_v1 = M_era / M_ref = (P_era / P_ref) × (k_era / k_ref)`, so the factor cancels whenever
`k_era = k_ref`. AH's case for it *not* cancelling is that a SCHEDULE era's recorded series is a
constant, so its min IS its median and `k_era = 1` exactly.

That argument requires the **reference** window to be a genuine within-bar minimum. Measured:
for **12 of 43** FTMO H4 symbols the reference window's own bar-`spread` column is a **single
constant** — a nominal quote, not a minimum. There both ends of the ratio were produced by the same
convention, and the factor cancels exactly as AG's own docstring claims. EURUSD, USDCAD, EURGBP,
JP225, USOIL_cash and six of the nine cryptos leave the defect's scope before any test is run.

**EURUSD is only readable at all through the model's own 90-day reference widening**: every one of
its 162 unwidened reference H4 bars records `spread` 0, and the first version of my scan therefore
dropped the estate's most-traded symbol without saying so. `reference_widened_days` is per symbol and
a scan that ignores it is reading a different reference than the ratio it corrects.

Control: the era **class reproduces from this scan on 2,653 of 2,653 quarters**, so the scan is
reading what `build_spread_model` read.

### 4.2 The estimator is chosen on held-out data, and the two accounts disagree

Two independent measurements of the same `k_ref` already existed. AH's is `tick p5 / tick p50`;
AG's `tick_over_bar_factor` is `tick p50 / bar level` — and AG's is the right one here, because
`era_ratio`'s numerator and denominator are literally bar levels, so `bar_level_ref / tick_p50_ref`
is the needed factor measured directly rather than through a p5 proxy.

| class | k_ref (AG, direct) | k_ref (AH, p5 proxy) |
|---|---:|---:|
| `fx` | 0.6671 | 0.6667 |
| `jpy_fx` | 0.6672 | 0.7500 |
| `metals` | 0.7138 | 0.7864 |
| `index` | 0.9917 | 0.9062 |
| `energy` | 0.9345 | 0.9828 |
| `crypto` | 0.9911 | 1.0000 |

They agree to 0.07 % on `fx` and differ by up to 11 % elsewhere. Leave-one-symbol-out picks the
predictor **per account**, on mean |log error| against each held-out symbol's own measured `k_ref`:

| account | class median | global median | no correction | winner |
|---|---:|---:|---:|---|
| FTMO | **0.1287** | 0.2088 | 0.2705 | class median |
| redacted_account | 0.3126 | **0.1563** | 0.1983 | global median |

On redacted_account only 7 symbols carry tick data, so a per-class median is 1–3 symbols deep and is
**worse than not correcting at all**. The choice is made by that number, not by preference.

### 4.3 The falsification test refutes the magnitude — and its naive form agreed for the wrong reason

If the bias is real, then at a boundary where a symbol's archive goes from a single-constant quarter
to a RECORDED one, `era_ratio_v1` must step by `log k_ref` (≈ −0.405 on `fx`/`jpy_fx`).

It does. **So does every boundary in the reverse direction, in the same sign**, where the bias
predicts +0.405: on FTMO `jpy_fx` the reverse boundaries move **−0.27** raw. The step is dominated by
the secular narrowing of spreads between two adjacent quarters, and the forward half of the test
matched the prediction because the confound points the same way.

Two things had to be fixed before the test meant anything, and both were mine:

- **the population.** My first degeneracy statistic was a relative IQR, which collapses on an integer
  points grid: **57 of the 62 boundaries it selected had a non-constant "degenerate" side, up to 44
  distinct values.** The interpolated `k_era = 1 + (k_ref − 1)·w` built on it is withdrawn; only a
  literal single-constant quarter on ≥ 30 nonzero bars is treated as backfilled now, and QUANTIZED /
  FLOORED eras are left alone rather than interpolated on a statistic that does not measure what it
  claims.
- **the estimator.** Re-estimated as a **difference-in-differences** against the contemporaneous move
  of same-class symbols whose *both* quarters are RECORDED, so the trend divides out and the forward
  and reverse boundaries estimate the same quantity once oriented.

| FTMO class | n (fwd/rev) | DiD | raw (oriented) | predicted `log k_ref` |
|---|---|---:|---:|---:|
| `jpy_fx` | 8 (4/4) | −0.0546 | +0.0179 | −0.4047 |
| `metals` | 2 (0/2) | +0.1627 | +0.4612 | −0.3372 |
| `index` | 2 (1/1) | +0.0260 | +0.0118 | −0.0083 |
| `fx` | 1 (1/0) | +0.0094 | −0.1867 | −0.4048 |

**And the test does not support an estimate — it does not even support the "13 % of AH's sizing" this
section said in its first version.** An adversarial pass over my own claim fired my own refutation
criterion, which is written into `am_era_anchor.do_boundary`'s docstring: *"forward and reverse
boundaries that disagree once oriented … would mean the step is a trend the control failed to
remove."* Once oriented they do disagree:

- forward median **−0.642** (159 % of the prediction), reverse median **+0.016** (−4 %) — opposite
  signs, 41× apart. The pooled −0.0546 is a mixture of two disagreeing clusters, not an estimate of
  one quantity; and the *median* of a balanced 50/50 mixture does not cancel residual trend the way
  the *mean* of a balanced design would, which is what the docstring's cancellation argument
  assumed.
- 4 of the 8 oriented values are negative — an exact two-sided sign test gives **p = 1.0000**.
- the 93 % distribution-free CI on the median is **[−0.817, +0.030]**, wider than the whole predicted
  effect and containing **both 0 and −0.4047**.

So the honest reading is: **the boundary test fails to confirm AH's magnitude, and it is not powerful
enough to put a number on the residual either.** "13 % of the sizing" is withdrawn. Two classes
additionally come out the wrong sign, and `fx` has n = 1. What the test does establish is that the
raw jump is a trend artifact (the reverse boundaries move the same way raw) and that no amount of
this archive will identify the term — which is §4.5's point.

**This does not weaken the section's conclusion, because the conclusion never rested on the DiD.**
§4.4 is the decisive measurement and it is a direct one.

### 4.4 What it costs to ignore it: 0 verdicts

The decisive measurement is not the DiD, it is the consequence. AH's own four-arm FX cohort was
re-judged with the level shift applied at **full** magnitude — same trades, same arms, same
intersected population, same composition, same bill, only the era table different:

- **0 of 42 member verdicts moved. 0 of 3 family verdicts moved. 0 members crossed zero.**
- mean charged cost 0.23273 → 0.21955 R on arm B (−5.7 %) and 0.07709 → 0.07112 R on arm C (−7.7 %);
- the largest pooled-OOS move is **+0.0156 R/day**, on the three `chfjpy` members, which sit at −0.43.

This is the claim the session most needed to be wrong about — if the alternate era table never reached
the gate, "0 moved" would be vacuous — so it was handed to an adversarial refuter with that
instruction. It came back verified three ways: the patch path traced end to end (`cost_r` imports
`spread_price` at call time and `load_spread_model` reads `DEFAULT_MODEL` as a module global at call
time; the only cache is the `lru_cache` this session clears on both entry and exit); proven
empirically on one USDJPY trade at 2003-01-14T22:00Z, where `era_ratio` goes **20.253 → 13.512** and
`total_r` **0.18188 → 0.15736** inside the context manager and restores exactly on exit; and shown not
to be a coverage artifact — **4,543 of the 16,337 trades fall in a corrected era**, 585 of 2,653 era
cells differ, all of class SCHEDULE, at a median factor 0.66716 = 1/1.4989, i.e. AH's *full* 1.50×.
The refuter re-ran all 16 gate runs independently and reproduced 0 moved, 0 crossings.

So AH's "every number this session publishes is conservative with respect to it" is correct, and the
size of that conservatism is now a number rather than a caveat.

### 4.5 Therefore the repair is a band, not a level

`k_era` is identified only by tick data contemporaneous with a SCHEDULE era, and those eras are
2000–2010. **No such data exists and none can be captured**, which makes this a permanent uncertainty
rather than a measurable defect — and `spread_model` already carries the right instrument for that,
with the explicit doctrine that *"a band too wide to decide anything is a capture requirement, not a
result"*. Two artifacts, and only one of them is a recommendation:

| artifact | what it does | status |
|---|---|---|
| `SPREAD_MODEL_V1_ERA_SCHEDULE_BAND_WIDENED.json` | level unchanged; **536 eras**' half-width raised to cover the hypothesis; mean increase 0.166 log; **0 become undecidable** | **the repair** |
| `SPREAD_MODEL_V1_ERA_LEVEL_SHIFT_SENSITIVITY.json` | 585 eras × `k_ref` (median factor 0.667) | sensitivity only — NOT validated |

Neither is a default. `SPREAD_MODEL_V1.json` is untouched, so no published number in the estate moves
unless a caller opts in, and adopting variant B is a merge-train decision because it re-prices every
banded verdict at `low`/`high` (the `mid` band, which every verdict in the estate uses, does not
move at all).

**AH's 19 composition tests stay green** (§9), which is what its own brief asked for: the repair
lands in an artifact and a per-era field, not in the composition algebra.

### 4.6 What the brief asked for that I did not do, and why

The brief said "validate on AG's held-out structure per AH's protocol". AG's held-out structure is
188 weekly **block pairs**, and AH §7 item 1 already established why that holdout cannot identify an
interaction term: both sides of every pair are all-hours medians. The same objection applies here
with more force — both sides of a block pair are RECORDED, so `k_era = k_ref` on both and the factor
is identically 1. The boundary DiD is the substitute, and its weakness is sample size (n = 8 on the
one cell that has any), not identification.

---

## 5. What I got wrong

**Eleven, and nine of them were found by an adversarial pass over my own claims** — nine refuters,
each told to default to `refuted=true` and to verify by running code rather than by reasoning. Four
returned `refuted`. Two more came from controls I built and then had to believe.

1. **§4.3's "13 % of AH's sizing" was not supportable and my own driver said so.** `do_boundary`'s
   docstring names "forward and reverse boundaries that disagree once oriented" as the refutation
   condition, and once oriented they disagree in **sign** (−0.642 vs +0.016). Sign test p = 1.0000 on
   n = 8; the 93 % CI on the median is [−0.817, +0.030], containing both 0 and the prediction. I wrote
   the refutation condition and then published a number that trips it. Withdrawn; §4's conclusion never
   depended on it.
2. **§2's gross mechanism was wrong, and refuted by my own control.** "The rollover distorts the mid,
   so entering there is a bad fill" — but moving the entry ONTO the rollover gains *more* gross
   (+0.0495 vs +0.0433). The real relationship is `sign(Δgross) = −sign(drift)` on 6 of 6 decision-hour
   cells, r = −0.915. §2 now says that instead.
3. **"Drift accounts for about half the gross gain" was structurally impossible.** The driver
   re-anchors stop and target at the shifted entry, so 98.0 % of rows exit at exactly −1.0 or exactly
   +2.0/+4.0 in both arms and the entry price cannot enter their R at all. 0.0206/0.04325 = 47.6 % was
   a coincidence with no channel. The delta is 757 flipped trades.
4. **"The best achievable saving" is the best on a 0–8 h grid.** On 0–24 h the best is 18 h and one hour
   is 93.79 % rather than 94.40 %. The 8 h cap is AH's `MAX_SHIFT_HOURS`, which is a defensible bound and
   not the same thing as "achievable".
5. **"An exact re-pricing" overstates it.** Swap is invariant *by construction* (every trade enters at
   broker 00, so the midnight count first moves at 24 h), commission is never re-priced, slippage is
   hour-blind. It is an exact **spread** frontier.
6. **"The fraction is composition-independent" is false.** The shifted-hour *levels* are; the fraction
   is 94.40 % under `v2_damped` and 97.98 % under `v1_multiplicative`, because the composition-sensitive
   shift-0 level sits in both numerator and denominator.
7. **"Only hour 00 is damped" over-generalised.** `fx` at broker Friday 23:00 is 1.6667 and is damped
   too; it is simply unreachable by this shift grid. And the `fx` table has 120 populated cells, not 168.
8. **"The repair cannot move the ARMED book because `need_hour=False`"** — premise verified, conclusion
   invalid. §1.4: `sub_mid_dn_revert`'s changed firing set moves the Kelly-lite conviction count, which
   sizes every unit that day including armed ones.
9. **My import form hid the repair from the live-lineage register** (§1.3), and my docstring fix to the
   vendored oracle would have forced a spurious register entry. Both corrected.
10. **The first A/B ran against `main` instead of my merge-base**, and `main` had moved mid-session, so
    two pre-existing failures read as mine. Chasing them found #9, so the wrong A/B was worth more than
    the right one — but the rule that resolves it is the agreement's, not mine.
11. **Three driver bugs, each caught by a control rather than by inspection:** the AF-parity path
    (`AH.parent` is `phase8`, not the audit root, so the parity check crashed after a 4-minute walk);
    the hour frontier priced 17,888 rows against AH's intersected 16,337 and read 6.5 % low; and
    `ah_entry_shift.load_archive` maps only D1/H4, so the M15 stage reported "0 M15 series" and would
    have published an empty frontier — it now raises instead.

**What the adversarial pass could NOT refute:** the AF arm-A parity (strengthened to row-for-row
identity on 16 fields over 68,360 rows), the control inversion and its 96.4 % attribution to the hour,
the hour-share correction (all four attack lines failed), and — the one that decides item 4 — the
zero-verdicts-moved measurement, which a refuter reproduced end to end including an empirical proof
that the alternate era table reaches the gate.

---

## 6. Routing

**Borhen — one decision, and it is AH's decision at a better price.** The FX D1 cohort's entry
convention. AH routed "move it from the D1 close to the first H4 close" and priced it at +0.063…+0.141
R/trade. The measurement now says **one hour, not four**: one hour buys 94 % of the achievable cost
saving on either composition and, on the window where the gross can be measured, the net frontier peaks
at **1–2 hours** and is *negative* at both 0 h and AH's 4 h. `atr_mean_reversion`'s own optimum is one
hour, where it halves its loss without turning positive. None of the affected sleeves is armed, so
nothing about the live book changes with it — but the convention is a contract, and contracts are yours.

**Borhen — nothing new on the multiplicity bill.** This session adds 270 looks and admits nothing;
the best raw p in its whole grid is 0.0324. It does not touch the `mx_btcusd` / `sub_xvol_pullback`
decision AI and AF routed.

**The merge train** — three things.
1. `b48441e4c` (already on `main`) and this branch both add to `DEPLOYED_HELPERS`, at adjacent lines:
   `structural_retest` there, `substrate` here. Expect a trivial conflict or a clean auto-merge.
2. Adopting `SPREAD_MODEL_V1_ERA_SCHEDULE_BAND_WIDENED.json` re-prices every banded verdict at `low`
   and `high` (the `mid` band, which every published verdict uses, does not move). That is a train
   decision, not a session decision, and the evidence for taking it is §4.5.
3. The `sub_mid_dn_revert` numbers in `SURVIVOR_BOOK_V1.json`, `AA_ESTATE_WALK.json` and
   `EXIT_FRONTIER_V1.json` are all on the wrong clock. §1 supersedes them for that sleeve; nothing else
   in those artifacts is affected.

**Wave 10, in value order.**
1. **The one-hour entry convention needs a live-path implementation sketch before it can be decided.**
   The book decides at a bar close and places immediately; a one-hour delay is a new state (a pending
   intent with an expiry) and its failure modes — restart during the delay, the intent's stop moving,
   the conviction count changing between decision and fill — are unpriced. That is engineering, not
   research, and it is what the decision actually waits on.
2. **The decision-hour reversion effect (§2, r = −0.915 over six cells) is a generation-side signal
   nobody has used.** If one bar of delay pays exactly where the intervening bar reverts, then the
   *sign of the intervening bar* is a filter, not a delay — and it is available at the fill instant.
3. **A behavioural clock-owner detector** for `generation_lineage`, replacing the source-string scan
   (§1.5): patch `_server_clock` and see whose hour function moves. The current detector's hole is one
   import style wide and I only found it by breaking it.
4. **`substrate_engine`'s docstring is still wrong on mainline and cannot be fixed** without diverging
   from the deployed lineage (§1.5). The clean resolution is a lineage register that classifies
   *behavioural* divergence, i.e. item 3.

---

## 7. Blocks, ledger and queue

**Blocks B1200–B1244**, appended to `IMPLEMENTATION_STATE.md`:
B1200–B1209 item 1 (the repair, the A/B, the solo gate, the carry restatement);
B1201 the lineage-register defects; B1210–B1219 item 2; B1220–B1229 item 3;
B1230–B1244 item 4.

**Trial ledger**: 506 rows written this session (`research/operations/trial_budget/TRIAL_LEDGER.jsonl`,
8,488 → 8,994). 2 for the reclock (one per clock arm), 504 for the H4 entry grid — 42 members × 3 arms ×
2 subsets × 2 scopes. No family MEMBER is added by any of it: the H4 arms are new **cells** of AF's
existing H4 members and the reclock is a re-look at an existing `CANDIDATE_BOOK_V1` member, so the
declared family stays 32 and the looks are counted.

**Repair queue**: 6 rows appended (96 → 102), session `AM`, each carrying
`prescription_in_diagnostics_enum`. `am_repair_rows.py` is idempotent on
`(session, sleeve, prescription, component)` — AK's §7.7 records its own script double-appending, and
re-running this one reports 6 skipped rather than adding them again (verified).

Three of the six are defects **this session introduced or inherited**, not findings about sleeves: the
lineage-register blind spot (§1.3), the Kelly-lite conviction coupling (§1.4), and the era term's park
note. The other three are the entry-convention decisions.

**Not left implicit — three level defects inherited from `ah_entry_gate.cost_decomposition`,** measured
by the adversarial pass and now named in the driver:
`side` is never passed to `cost_r`, so all 16,337 rows are priced LONG while 45.0 % are direction −1
(correctly sided, mean swap +52.6 % and the shift-0 level 0.2332 → 0.2415; the *fraction* is unchanged);
slippage is hour-blind by construction and is 12.4 % of the best saving — exactly the term a rollover
fill should pay extra of, so the rollover premium measured here is **spread-only**; and
`hold = max(0, hold − shift)` clamps 129 rows (0.79 %) at shifts ≥ 5 h, numerically inert
(0.94404 → 0.94393).

---

## 9. Verification — the §2 scoped receipt

`python3 scripts/pytest_failset.py scope --base fff431c6b --include-worktree` → 21 changed paths,
9 test files by import closure. Run with the six that name `sub_mid_dn_revert`, AH's composition
tests, the candidate-family seal tests and the raw-broker guards:

| | failed | passed |
|---|---:|---:|
| merge-base `fff431c6b` | 2 | 331 |
| HEAD | **2** | **343** |

**Same failure set, 0 regressed, +12 net new passing tests.** Both failures are
`tests/test_replay_policy_generation_lineage.py::test_register_covers_every_clock_owning_sleeve` and
`::test_deployed_lineage_claim_is_pinned_to_the_live_commit`, **pre-existing at the merge-base**
(verified in a worktree at `fff431c6b`: 2 failed / 13 passed in that file alone, identical set) and
**already fixed on `main` by `b48441e4c`**, which adds `NO_DEPLOYED_LINEAGE` for `session_leadlag` and
registers `structural_retest`. My branch does not carry that commit. After this session
`clock_dependent_sleeves() − DEPLOYED_HELPERS` is exactly `{session_leadlag, structural_retest}` —
`substrate` is classified.

**How that was nearly missed, and it is the more useful half.** My first A/B ran against `main` rather
than my merge-base, and `main` had moved during the session, so two pre-existing failures read as
mine. Chasing them found two real defects I *had* introduced (§1.5), which is why the wrong A/B was
worth more than the right one would have been. The agreement's rule — *verify any suspicious failure
at your merge-base* — is the one that resolves it; `main` is not the merge-base once a train is
running.

**AH's 19 composition tests are green** (`tests/test_spread_composition.py`), which its own §11
routing asked for: the era work lands in a separate artifact and a per-era field, not in the
composition algebra. The candidate-family seal tests are green, so no published `spec_sha256` moved.

**Two negative controls, because a test that cannot fail proves nothing:**

- the substrate clock tests were re-run with `substrate._session_hour` monkeypatched back to the
  pre-B1200 raw-UTC read. **6 of them fail**, including 2 of the 6 broker-grid parity rotations.
  Before I added the rotation *and* the assertion that the generator does not fire on non-firing
  bars, **zero** did — the parity test passed against the defect it was written for.
- `substrate_engine.py` is pinned to the deployed lineage by sha256, so the next cosmetic edit to the
  vendored oracle fails loudly instead of silently forcing a lineage-register entry.

---

## 10. Artifacts

| path | what |
|---|---|
| `phase9/receipts/SUBMID_RECLOCK_V1.json` | item 1 — the re-derivation, both-clock A/B, solo gate, carry tier |
| `phase9/receipts/AM_SUBMID_TRADES.json.gz` | both clock arms' trades |
| `phase9/receipts/ENTRY_FRONTIER_H4_V1.json` | items 2 + 3 — the H4 hour-00 subset and the shift frontier |
| `phase9/receipts/AM_ENTRY_H4_TRADES.json.gz` | the H4 FX arms' trades |
| `phase9/receipts/AM_ATRMR_FINE_TRADES.json.gz` | the M15-window fine-shift trades |
| `phase9/receipts/ERA_ANCHOR_V2_VALIDATION.json` | item 4 — reconciliation, DiD test, verdicts, artifacts |
| `phase9/receipts/SPREAD_MODEL_V1_ERA_SCHEDULE_BAND_WIDENED.json` | the era repair (opt-in) |
| `phase9/receipts/SPREAD_MODEL_V1_ERA_LEVEL_SHIFT_SENSITIVITY.json` | the era sensitivity (opt-in) |
| `phase9/receipts/am_submid_reclock.py` · `am_entry_frontier.py` · `am_era_anchor.py` · `am_repair_rows.py` | the drivers |
