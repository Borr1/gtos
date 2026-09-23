# Gate G1b receipt — W7 live-vs-validation divergence forensics

**Session E, Phase 1 item 2.** Branch `phase1/w7-forensics`. 2026-07-26.
Blocks **B60–B69** in `IMPLEMENTATION_STATE.md`.

**Artifacts, all reproducible:**

| what | path |
|---|---|
| generator, broker-truth lane | `scripts/w7_live_forensics.py` |
| generator, packet-telemetry lane | `scripts/w7_packet_forensics.py` |
| the row set (300 positions) | `phase1/w7_forensics/LIVE_TRADE_ROWS.jsonl` |
| provenance, reconciliation, attribution | `phase1/w7_forensics/LIVE_TRADE_ROWS_MANIFEST.json` |
| book telemetry, cost gate, composition | `phase1/w7_forensics/W7_PACKET_FORENSICS.json` |
| row schema, for Session F | `LIVE_DIVERGENCE_ROW_SCHEMA.md` |

**This receipt was revised after an adversarial pass that refuted one of its headline claims and found
ten bugs in the generator.** §14 records what was withdrawn and why. Read it before quoting anything.

**A second pass, 2026-07-27, narrowed two more claims** — the JPY Bonferroni result (§7) and the
framing of §10 decision 2. **§15** records both, in §14's form. Neither claim is deleted above; both
are marked in place.

---

## 1. Verdict

**Gate G1b: PASS on its own bar.** Every W7 live trade is attributed to sleeve, dial and cost, and the
attribution closes with **residual 0.000000 over all 175 positions** — an exact partition, published in
the manifest as `_partition_check` and independently reproduced. The remaining gaps are named in §8
rather than absorbed.

**The substantive finding is not the one the plan anticipated. It reframes the question rather than
answering it either way.**

> **The W7 live window does not measure the W7 book.** Of core-8's 3.90 total confidence weight,
> **0.45 — 11.5 % — placed a single trade.** `metals_core` (confidence 1.00, `train_validated`, the
> registry's own "deepest anchor", +1.16 R forward) placed **nothing** in 14 trading days, nor did
> `crypto` (0.85), `energy_agri` (0.80), `metals_softband` (0.50) or `metals_ob_micro` (0.30). The core
> sleeves that traded are **exactly the three weakest** — `idxrev`, `fx_jpy`, `fx_jpy_ny`, all at
> confidence 0.15, two labelled `breadth_falsified` and one `forward_only` **in the registry, before
> deployment**.
>
> **And the 2.00 % dial was structurally unreachable.** A unit's worst-case stop is
> `base_risk_per_unit × sleeve_confidence` (`admission.py:1038-1040`), so 2.00 % is only expressible by
> a confidence-1.00 sleeve. **The highest confidence that traded all window was 0.40.** The dial's
> ceiling could not have been touched by the book that ran.

So the standing risk in `FULL_VISION_PLAN.md` — *"Stack-B evidence does not survive audit (G1b fails)
→ OD-1 reopens"* — **does not trigger on the ground that the book lost money live.** 88.5 % of the book
never traded. What ran was its three weakest sleeves plus a 9-sleeve candidate book and a 12-sleeve
market-expansion book switched on 2026-06-18 that carry, in `live_system_of_record.md`'s words, "none
cited" for validation.

**OD-1's evidence base is nonetheless weaker than the decision assumed, in a different direction:**
there is no live evidence *for* the W7 book either. The activation candidate has never been measured in
the market. §9 states what would close that.

**One directional signal is strong enough to report at this sample size, and it is not the dial.** The
JPY-cross pair `fx_jpy` + `fx_jpy_ny` lost **−2,349.58 across both accounts on 41 trades with 7
winners** — mean realized **−0.591 R**, `p = 0.00016` against a generous 45 % null. `fx_jpy_ny` lost
**9 of 9**. Those two sleeves alone ran a **cost gate relaxed 3×** by owner approval on **2026-06-16**,
explicitly to "MEASURE the live edge net of spread". §5 shows the measurement returned a clear negative.
Ending that trial is an owner decision, queued in §10.

**And there is a second finding of comparable weight, on cost rather than composition.** **The validation
and the live pre-trade engine charge no commission at all** — zero at five independent sites, behind a
gate that accepts a status string emitted by the code it gates, with `selected_cell_risk_decision_basis`
**null on all 149 live intents** (§5.2a, **F38**). Realized commission is **0.0591 R per trade and
37.8 % of absolute gross P&L**, and it is **concentrated on exactly the sleeves that lost**: USDJPY
0.1948 R, GBPJPY 0.0927 R, BTCUSD 0.1102 R — while **all six index CFDs pay zero**, and `idxrev`, the
only profitable sleeve, is the only one trading a commission-free instrument set. Worse, the MC that
authorized the book applied its tick-erosion term with the **wrong sign**, granting USDJPY a **+0.018 R
credit** where reality charges **−0.195 R** (§5.2b, **F39**). That is a ~0.2 R-per-trade optimistic error
on the sleeve family that lost 9 of 9.

---

## 2. The denominator, corrected — the headline number is misattributed by roughly half

`SECOND_AUDIT.md:155-167` derives **FTMO ≈ −5.3 %** from two broker equity snapshots and gives
redacted_account as **≈ −3.0 to −3.9 %** because its start is unpinned. Both are arithmetically right about
the **account**. Neither is the **W7 book's** result, because both accounts traded a different stack
first.

**FTMO** [MEASURED — `LIVE_TRADE_ROWS_MANIFEST.json:accounts.ftmo.eras`]:

| era | positions | realized net | % of 100 k | window |
|---|---:|---:|---:|---|
| pre-W7 fleet (`GoldAgent_*`) | 32 | **−2,735.56** | −2.7356 % | 06-02 → 06-15 |
| **W7 book (`W7:*`)** | **97** | **−2,551.57** | **−2.5516 %** | **06-15 → 07-02** |
| hand-placed, phone (`manual_mobile`) | 2 | +13,166.69 | +13.1667 % | 07-02 → 07-03 |
| **partition check** | **131 / 131** | **+7,879.56** | | **residual 0.00** |

−2.7356 % + −2.5516 % = **−5.2872 %**, the audit's "−5.3 %" to within a rounding step. **The audit
measured the account correctly and attributed all of it to W7. Slightly over half belongs to the
pre-W7 fleet.** W7's own contribution is **−2.55 % of the initial balance**, or **−2.63 % of the
97,052.38 equity it was handed.**

**redacted_account** — the range collapses to a point, and the premise behind the range is wrong:

| era | positions | realized net | % of 100 k |
|---|---:|---:|---:|
| smoke tests | 7 | −4.98 | −0.0050 % |
| manual | 1 | −0.19 | −0.0002 % |
| pre-W7 fleet (`GoldAgent_*`) | 82 | **+988.47** | +0.9885 % |
| hand-placed, phone (single 05-14 XAGUSD) | 1 | −1,018.10 | −1.0181 % |
| **W7 book** | **78** | **−3,735.92** | **−3.7359 %** |
| **partition check** | **169 / 169** | **−3,770.72** | **residual 0.00** |

**redacted_account's W7 result is −3.7359 %** — inside the audit's range, near its pessimistic end, now
exact. The range existed on the assumption that "pre-halt fleet losses sit on the same account". **The
`GoldAgent` fleet on redacted_account was net positive, +988.47.** The whole pre-W7 *period* was
approximately flat (**−34.80**, i.e. −0.035 %), because the fleet's gain is offset by one hand-placed
XAGUSD trade at −1,018.10. **So 99.1 % of redacted_account's entire account loss is W7's** — the cleanest
framing, and it needed the deal history nobody had until this export.

**Both accounts, W7 book: 175 positions, −6,287.49, −3.1437 % of the 200 k two-account base.**

### 2.1 Three corrections to the record

**(a) `VPS_EXPORT_FINDINGS.md` V5's "Net since inception: FTMO +7,879.56" must never be read as a W7
result.** +13,166.69 of it is **two hand-placed phone trades**, and five independent discriminators
establish that — not one:

| position | entry (UTC) | exit (UTC) | vol | entry → exit | net |
|---|---|---|---:|---|---:|
| 164264833 | 07-02 15:15:01 | 07-03 01:24:17 | 1.00 | 4126.88 → 4188.59 | +6,085.34 |
| 164288287 | 07-02 16:28:24 | 07-03 01:24:32 | 1.00 | 4118.35 → 4190.02 | +7,081.35 |

1. `magic == 0`. All 175 W7 positions carry `20260401` (`src/mt5/mt5_interface.py:58`).
2. Opening **deal and order** `reason == 1` = `DEAL_REASON_MOBILE`. All 175 W7 opens are `reason 3`
   (`EXPERT`).
3. Empty comment, which `execution.py:3430-3444` cannot emit — its fallback is the literal
   `W7:UNTAGGED`, of which there are **zero** rows.
4. Opening order `sl == 0.0` **and** `tp == 0.0` — no stop at entry. Every W7 position has a broker SL.
5. Round 1.00 lot, ≈ $412 k notional each, ≈ $825 k combined on a 100 k account.

**Empty comment ⟺ mobile open is a perfect 1:1 correspondence** across both accounts (3 positions
total), so the classification rests on a measured equivalence, not an inference from one field. Earlier
drafts of this receipt called these "the post-switch broad system's first trades". **That was wrong:
they were placed by hand from the phone.** Without them FTMO closes at **94,712.87 (−5.29 %)** — the
+7.88 % headline is two hand trades, not the system.

**(b) The true drawdowns are deeper than any era sum, and they are what prop rules bite on.** Measured
deal-by-deal across all eras [MEASURED — `accounts.*.drawdown.account_true_drawdown`]:

| | trough | at | from initial balance | from running peak |
|---|---:|---|---:|---:|
| FTMO | 94,619.74 | 2026-06-30T20:10:30Z | **−5.3803 %** | −5.3803 % |
| redacted_account | 95,905.39 | 2026-07-01T15:28:34Z | −4.0946 % | **−5.8302 %** (−$5,937.60 from a 101,842.99 peak) |

No prop rule was breached: the limits are −5 % *per day* and −10 % max drawdown, and the worst *day*
was −1.05 % (FTMO) / −1.41 % (redacted_account) — §4. Note the FTMO figure of −5.5923 % that appears in the
manifest's `drawdown.series` is a **W7-only synthetic curve** and is correctly labelled as such: it
excludes a pre-W7 fleet position that closed inside the window for +212.06. The account number is
−5.3803 %.

**(c) The window starts 2026-06-15, not 06-18.** 06-18 is when the candidate and market-expansion books
were switched on. 21 of the 175 positions precede it. The window bounds are now derived from the data at
runtime rather than hardcoded.

---

## 3. Axis (a) — sleeve family. The partition, and what was silent

**The join key is broker truth itself.** The book stamps `f"W7:{sleeve}"[:16]` on every order
(`src/components/execution.py:3430-3444`) and MT5 preserves it on the deal, so sleeve identity survives
in the broker's own record and does not depend on the three GTOS execution ledgers that died on
2026-07-02 (finding V3). Resolution: 137 exact, 38 recovered from the 16-char truncation as a unique
prefix, **0 ambiguous, 0 unresolved** across all 175 W7 positions.

**Say this out loud, because a reader will assume otherwise: `magic` does NOT separate the two stacks.**
Both the pre-W7 fleet and the W7 book carry `20260401`. `GoldAgent_OBRete` is the 16-char truncation of
`GoldAgent_OBRetest` — the same code path at an older commit. **The comment string is the only
discriminator, and it has no corroborating field.** What makes it safe is directionality:
`execution.py:3430-3444` can emit only `W7:<sleeve>` or `W7:UNTAGGED`, never `GoldAgent*`, and there are
zero `W7:UNTAGGED` rows — so misattribution is impossible in either direction. Corroborating the
boundary independently: **11 consecutive calendar days (06-04 → 06-14) carry zero deals of any kind on
either account**, and the fleet was hand-flattened, not stopped by software (7 FTMO positions closed at
one instant on 2026-06-03 with `reason == 1`, MOBILE).

**The partition — 175 of 175 positions, residual 0.000000:**

| component | n | realized net | share of net loss | share of gross losses |
|---|---:|---:|---:|---:|
| **candidate book** (9 sleeves, ON 2026-06-18) | 70 | **−4,801.44** | **76.4 %** | **67.4 %** |
| **core-8 JPY cluster** (`fx_jpy` + `fx_jpy_ny`) | 41 | **−2,349.58** | **37.4 %** | 31.1 % |
| core-8 `idxrev` | 59 | **+875.51** | −13.9 % | 15.1 % (of losing trades) |
| market-expansion book (12 sleeves, ON 2026-06-18) | 5 | −11.98 | 0.2 % | 0.1 % |
| core-8, the other five sleeves | **0** | **0.00** | 0.0 % | 0.0 % |
| **total** | **175** | **−6,287.49** | **100 %** | |

**Two bases are given because they differ and the net one is fragile.** A component's share of a *net*
total is inflated by other components' winners. On redacted_account the candidate book is **90.4 % of the net
loss but 73.4 % of gross losses**, and core-8 is **9.6 % net but 26.6 % gross** — because `idxrev` made
+559.43 there. FTMO is stable (55.9 % net / 57.7 % gross). **Quote the basis with the number.**

**By correlated cluster** — the key the one-unit-per-cluster-per-day envelope is defined on, and now
resolved for all 175 rows (it was `unknown` for 43 % of the book before the adversarial pass):

| cluster | n | net | | cluster | n | net |
|---|---:|---:|---|---|---:|---:|
| `fx_reversion` (`asian_fade`) | 17 | −2,526.85 | | `crypto_alt_or_major` | 1 | −10.96 |
| **`jpy`** (`fx_jpy`, `fx_jpy_ny`) | **41** | **−2,349.58** | | `jpy_fx` (`mx_*`) | 3 | −3.13 |
| `liquidity_sweep` (`asia_pdl_fade`) | 20 | −1,370.42 | | `indices_context` | 1 | +2.11 |
| `metal_reversion` | 11 | −1,087.94 | | `crypto` | 22 | +183.77 |
| | | | | **`index`** (`idxrev`) | **59** | **+875.51** |

**Per sleeve, both accounts pooled.** `p` is `P(wins ≤ k)` under Binomial(n, 0.45). **`mean R` is net of
cost; `gross R` is price-only** — reported side by side so "worse than −1 R" is not misread as slippage:

| family | sleeve | conf | status | n | net | mean R | gross R | wins | p |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| candidate | `asian_fade` | 0.40 | promotion_candidate | 17 | −2,526.85 | −0.244 | | 7 | 0.474 |
| candidate | `asia_pdl_fade` | 0.25 | | 20 | −1,370.42 | −0.432 | | 5 | 0.055 |
| **core8** | **`fx_jpy_ny`** | **0.15** | **forward_only** | **9** | **−1,213.60** | **−1.142** | **−1.036** | **0** | **0.0046** |
| **core8** | **`fx_jpy`** | **0.15** | **breadth_falsified** | **32** | **−1,135.98** | **−0.436** | **−0.290** | **7** | **0.0059** |
| candidate | `metal_session_reversion` | 0.40 | | 11 | −1,087.94 | −0.157 | | 7 | 0.939 |
| candidate | `ny_crypto_momentum` | 0.35 | | 18 | −282.41 | +0.023 | | 4 | 0.041 |
| market_exp | `mx_*` (3 distinct) | 0.03 | | 5 | −11.98 | −0.13 | | 2 | — |
| candidate | `orb_crypto_london` | 0.35 | | 2 | +207.39 | +0.416 | | 1 | — |
| candidate | `kz_london_crypto_low` | 0.10 | | 2 | +258.79 | +1.290 | | 1 | — |
| **core8** | **`idxrev`** | **0.15** | **breadth_falsified** | **59** | **+875.51** | **+0.174** | | **40** | **1.000** |

**`kz_london_crypto_low`'s +258.79 is a human decision, not the sleeve's.** One of its two positions
(160425965, BTCUSD) was **closed by hand from the phone** for +304.37. Excluding it the sleeve is
**−45.58**. It is the only hand-closed W7 position on either account, it is flagged
`hand_closed: true` on the row and enumerated in `attribution.hand_intervention`, and the wrong
`ENUM_DEAL_REASON` map that hid it is bug B1 in §14.

### 3.1 The five silent sleeves

Across 99,112 runtime-learning packets, `metals_core`, `crypto`, `energy_agri`, `metals_softband` and
`metals_ob_micro` emitted **no `unit_placed`, no `unit_admitted`, and no `unit_shadow`**
[MEASURED — `W7_PACKET_FORENSICS.json:core8_composition`]. They did not generate candidates that were
rejected. They generated nothing on any symbol either broker carries. Their only skips are
`future_decision_bar_time` (7/3/4/7/7) and, on redacted_account only,
`profile_missing_instrument_config` for the four cross-metals and DASHUSD that **redacted_account genuinely
does not list** — the book correctly declining instruments the broker lacks, not a defect.

**I nearly published the opposite, and the correction is instructive.** My first probe grepped each
packet line for `profile_missing_instrument_config` and concluded the metals complex had been silenced
by a config defect. Every packet carries a `bridge.broker_profile_generation.broker_unsupported_skips`
**summary list** that repeats the same reasons on unrelated events, including `unit_admitted` rows. The
grep inflated the count ~10× and mislabelled admissions as skips. The corrected measurement counts only
`event_type == "unit_skipped"` and reads that row's own `skip_reason`; the guard is written into
`scripts/w7_packet_forensics.py`'s docstring and its `method_warning` field.

**Stated at the strength the evidence supports:** whether 14 days is simply too short for an H4-cascade
sleeve gated on vol-persistence to fire, or whether generation is defective, is **not decidable from
this window** — gap **G4**. What *is* decidable needs no frequency model: the validated book's economics
are a confidence-weighted blend of eight sleeves and the live window realized 11.5 % of that weight.
**The live and validated portfolios are different portfolios; their returns are not comparable
quantities.**

**A nuance against my own narrative.** It is tempting to say "the falsified sleeves lost". They did not
uniformly: `idxrev` is also `breadth_falsified` (train −0.065 R) and was **the best performer live**,
+875.51 at +0.174 R over 59 trades. The registry's `status` field did not predict live sign. What
separated the losers was the **cluster** — JPY — and §5 gives the mechanism.

---

## 4. Axis (b) — the dial. **A claim withdrawn, and the corrected finding**

### 4.1 What was withdrawn

An earlier revision of this receipt reported that measured per-trade risk (~0.11–0.14 % of balance) was
"10–15× below the configured 2.00 % dial", and treated that as an under-sizing finding. **That claim was
wrong and is withdrawn.** It compared a per-**trade** statistic to a per-**unit** base. The sizer is
explicit (`src/components/ultimate_book/admission.py:1170-1171`):

```python
unit_risk = base_risk_per_unit * conf * derisk_mult
per_trade = unit_risk / n if n else 0.0
```

and its docstring states the invariant (`:1038-1040`): *"Per-trade risk% = base_risk_per_unit \*
sleeve_confidence \* intra_size, split across the unit's members so the correlated unit's worst-case
simultaneous stop = base_risk_per_unit \* conf."*

**So 2.00 % is not the risk any unit expresses — it is the base a confidence-1.00 sleeve would express.**
The generator now emits `designed_unit_risk_pct = 0.020 × conf` next to the observed value, and the
misleading adjacency that produced the bad claim (`configured_nominal_pct` printed beside
`mean_risk_pct`) is removed.

### 4.2 The corrected finding

**The 2.00 % ceiling was structurally unreachable in this window.** The highest sleeve confidence that
traded at all was **0.40** (`asian_fade`, `metal_session_reversion`), capping any unit's designed
worst-case stop at **0.80 %**. Reaching 2.00 % requires `metals_core` at confidence 1.00, which placed
nothing (§3.1).

**Observed against designed, per correlated unit** [MEASURED — `unit_risk.observed_over_designed_unit_risk`]:

| | FTMO | redacted_account |
|---|---:|---:|
| units measured | 61 | 47 |
| observed / designed, median | **0.376** | **0.577** |
| observed / designed, mean | 0.460 | 0.668 |
| observed / designed, max | 1.332 | 1.687 |
| **units that exceeded their design** | **5 of 61** | **8 of 47** |

So the book ran at roughly **0.38–0.58× of designed size at the median** — fully explained by the two
size-*reducing* multipliers deliberately enabled (`ultimate_book_stress_derisk: true` with
`derisk_mode: smooth`, §6) — and **exceeded its design on 13 units**, consistent with
`ultimate_book_kelly_lite: true` sizing up on high-breadth days. The largest excursion is
`asian_fade` on redacted_account, 2026-06-26: designed unit 0.80 %, observed **1.35 %** (1.69×), realized
**−922.55** — the single worst unit-day in the window.

**Absolute risk, for the record:** per trade FTMO median 0.109 % / max 0.450 %, redacted_account median
0.143 % / max 0.710 %. Per day, total deployed stop-risk peaked at **1.685 %** (FTMO) and **2.127 %**
(redacted_account) against a **4 %** `ultimate_book_gross_open_risk_cap_pct` — **the gross cap never bound.**

**Independently confirmed by the book's own telemetry, from disjoint inputs.**
`bridge.realized_units[].risk_pct_per_trade` medians are **0.1097 % (FTMO) / 0.1429 % (redacted_account)**
against my broker-derived **0.1087 % / 0.1432 %** — two measurements from disjoint inputs (broker stop
distances and fill prices on one side, the sizer's own computed fractions on the other) **agreeing to
within 1 %.** That is the cross-validation for every R figure in this receipt.

**The dossier-dial counterfactual**, since the dial is a linear scalar on fixed-fractional sizing:

| account | at the live 2.00 % base | at the dossier's 1.25 % | attributable to the dial choice |
|---|---:|---:|---:|
| FTMO | −2,551.57 (−2.5516 %) | −1,594.73 (−1.5947 %) | **−956.84 (−0.9568 %)** |
| redacted_account | −3,735.92 (−3.7359 %) | −2,334.95 (−2.3350 %) | **−1,400.97 (−1.4010 %)** |

**Axis (b)'s answer, in two parts.** The dial choice accounts for **37.5 % of the loss's magnitude** —
a real, quantified confounder worth −0.96 % / −1.40 %. It accounts for **none of the loss's sign**: at
1.25 % the book still loses, because per-trade expectancy was negative. Running the 2.00 % base instead
of 1.25 % made a losing fortnight 1.6× worse; it did not make it losing. **And the ceiling itself was
never in play** — not because sizing was defective, but because no high-confidence sleeve fired.

### 4.3 A live defect found on the way through

`agent_config.yaml:1348` sets `governor_daily_reset_offset_hours: 3.0` with the comment *"FTMO/FN
server = UTC+3 so the daily window resets at 21:00 UTC"*. Wrong twice for FTMO, whose daily-loss window
resets at **00:00 CE(S)T = UTC+2 in summer** (`config/profiles/operator_profile.yaml:104`, and
B56/B58), and wrong for both accounts in the ~4 weeks a year the US and EU DST calendars disagree,
because it is a hardcoded constant where `broker_clock` is measured and fails closed. It did not bite
here — the worst day was −1.05 % against a −5 % wall, so no boundary placement could have changed an
outcome. Filed as **F32**.

---

## 5. Axis (c) — execution friction. Partial by construction, and the cost is the whole excess

### 5.1 Coverage, stated first

| source | covers the 14 W7 days? | usable for cost? |
|---|---|---|
| runtime-learning packets (99,112 rows) | **yes, all 14** | partly — see 5.3 |
| `broker_order_lifecycle_capture_v4` (594 rows) | 06-18 → 07-02 (11 of 14) | **no** — request-side only, `order_result` absent on all rows (V2) |
| `execution_manager_v4_decisions` (236 rows) | to 07-02 | no — no broker ticket on any row |
| `slippage_runtime` (165 rows) | to 07-02, `candidate_id` on 33 | marginal — 18–21 % of positions |
| tick export | **06-18 → 07-24 only** | **88.0 % of W7 positions** (154/175); 06-15/16/17 uncovered = 21 positions |
| packet `spread_r` field | all 14 days | **no — NULL on all 99,112 rows** |

The three ledgers dying on 2026-07-02 (V3) hurts less than feared *for this window*, because the window
**ends** on 07-02. The binding gaps are different: the lifecycle capture never recorded a fill, and the
packet's own `spread_r` is declared and never populated. **State 88.0 % for anything tick-derived and
0 % for anything needing a captured fill price.**

### 5.2 What is measurable — and stops are clean, cost is the excess

*Explicit charges, from broker truth — exact, 100 % coverage, no modelling:*

| | commission | swap | total | as % of that account's W7 loss |
|---|---:|---:|---:|---:|
| FTMO | −842.52 | −116.01 | **−958.53** | **37.6 %** |
| redacted_account | −786.01 | −239.81 | **−1,025.82** | **27.5 %** |
| both | −1,628.53 | −355.82 | **−1,984.35** | **31.6 %** |

**Nearly a third of the W7 loss is commission and swap.** In R: **−0.0725 R per trade** mean, **−12.69 R**
total against a total realized **−25.32 R** — **roughly half the R the book lost, it paid.**

*Stop-outs against the modelled −1.00 R.* 102 of 175 positions closed at stop:

| | median |
|---|---:|
| **gross R** (price only) | **−1.0036** |
| cost R (commission + swap) | −0.0720 |
| **net R** | **−1.0691** |

**There is no stop slippage.** The price behaviour at the stop is −1.0036 R — a clean fill. The entire
6.9 % excess over a modelled −1.00 R is commission and swap. This corrects an earlier reading of these
numbers as slippage, and it matters for Phase 6: the fix is a cost model, not a fill model.

The same holds where it hurt most. `fx_jpy_ny`: net **−1.142 R**, gross **−1.036 R**, cost **−0.107 R**.
`fx_jpy`: net **−0.436 R**, gross **−0.290 R**, cost **−0.146 R** — **a third of `fx_jpy`'s loss is
cost.**

### 5.2a The validation charged **zero commission**, at every layer, by construction

This is the largest single finding on this axis and it is not a calibration gap — it is a missing term.

**Five independent sites, all `0.0` or absent** [MEASURED]:

| layer | citation | what it does |
|---|---|---|
| KB7 metals/energy | `KB7_tick_truth.py:64` | `COMMISSION_R = {s: 0.0 for s in (TICK_SYMS_METALS \| TICK_SYMS_ENERGY)}` |
| KB7 crypto | `KB7_tick_crypto.py:46` | `COMMISSION_R = {s: 0.0 for s in TICK_SYMS}` |
| KB7 JPY | `KB7_tick_jpy.py:108-109` | term dropped — *"honest: spread already in fills, jpy spread-only"* |
| sealed replay | `v4_timewarp…py:58965-58966` | `"commission_r": 0.0, "commission_r_source": "commission_included_in_selected_cell_risk_status"` |
| **live pre-trade engine** | `broker_net_cost_engine.py:577-583` | `total_cost_r = spread_r + expected_slippage_r + swap_cost_r` — **three components, no commission**, and `total_cost_components` (`:644-648`) lists only those three |

I verified the last one directly; it is the engine that gates live admission and it is the same engine the
sealed replay calls (`v4_timewarp…py:55`, invoked `:58906`).

**And the commission gate is circular.** `broker_net_cost_engine.py:729-736` refuses a packet unless
`commission_model_status` is in an allowlist (`agent_config.yaml:741-743`). The permitted string
`COMMISSION_INCLUDED_IN_SELECTED_CELL_RISK` is **emitted by the very code the gate protects**
(`ultimate_book/execution_packets.py:340`, `v4_timewarp…py:58899`). On all 149 live intents that status
was set while `selected_cell_risk_decision_basis` was **null** — the "included" claim has no basis, and
the replay then charges `0.0` citing its own declaration as the source.

**So the comparison is not "realized cost is ~2× the model". It is realized 0.0725 R against a modelled
0.0000 R.**

**Commission by symbol, from broker truth** — and the distribution is the point [MEASURED]:

| symbol | n | commission R | swap R | | symbol | n | commission R |
|---|---:|---:|---:|---|---|---:|---:|
| **USDJPY** | 18 | **0.1948** | 0.0000 | | XAUUSD | 13 | 0.0054 |
| AUDUSD | 3 | 0.1509 | 0.0000 | | XAGUSD | 1 | 0.0013 |
| BTCUSD | 14 | 0.1102 | 0.0373 | | **US30_cash** | 12 | **0.0000** |
| GBPUSD | 7 | 0.1065 | 0.0000 | | **SPX500** | 15 | **0.0000** |
| EURUSD | 12 | 0.1063 | 0.0000 | | **JP225** | 18 | **0.0000** |
| **GBPJPY** | 23 | **0.0927** | 0.0000 | | **UK100 / GER40 / NAS100** | 25 | **0.0000** |
| ETHUSD | 9 | 0.0589 | 0.0919 | | **pooled** | **175** | **0.0591** |

**The six index CFDs — 70 of 175 trades — pay exactly zero commission.** So the cost burden falls
entirely on the FX, JPY and crypto legs, and `idxrev`, the only profitable sleeve, is the only sleeve
that trades a commission-free instrument set. Commission alone is **37.8 % of absolute gross P&L**
(−1,628.53 against a gross of −4,303.14).

**Which splits `fx_jpy` into two different failures** [MEASURED]:

| sleeve · symbol | n | gross R | commission R | net R |
|---|---:|---:|---:|---:|
| `fx_jpy` · **GBPJPY** | 17 | **+0.0124** | 0.1039 | **−0.0915** |
| `fx_jpy` · **USDJPY** | 15 | **−0.6320** | 0.1942 | **−0.8261** |
| `fx_jpy_ny` · GBPJPY | 6 | −1.0218 | 0.0609 | −1.0827 |
| `fx_jpy_ny` · USDJPY | 3 | −1.0627 | 0.1981 | −1.2608 |

**`fx_jpy` on GBPJPY had a marginally positive price edge and commission alone made it a loser.** On
USDJPY the price edge was genuinely bad *and* it carries the highest commission of any instrument
traded. Those are two different defects with two different fixes, and "fx_jpy lost −0.436 R" hides both.

### 5.2b The MC that authorized the book applied tick erosion with the wrong sign

`INTEG_W7_FINAL_RESULT.json` — the artifact behind the deploy book — carries `tick_erosion_applied`
[MEASURED, byte-identical in the repo and the VPS export]:

```json
{"HEATOIL_c": -1.506, "NATGAS_cash": -0.2647, "UKOIL_cash": -0.0372,
 "USDJPY":  0.0179,  "USOIL_cash":  0.037,   "XAGUSD":  -0.005,  "XAUUSD": 0.019}
```

Computed as `tick_real − modeled` (`KB7_tick_book_restate.py:41`, `KB7_tick_mc.py:38`) and applied as
`R + h` (`:62`). The illiquid energy legs correctly took large negative haircuts and were dropped.
**But USDJPY, XAUUSD and USOIL_cash received positive *credits*** — because the per-class map
(`ULTIMATE_REAL_COST_MAP.json`: `jpy_fx 0.1148`, `metals 0.0459`, `energy 0.0372`) charged more than the
measured *spread*, and the difference was handed back as an EV gain.

**The measured part, which is not in doubt.** For USDJPY: modelled 0.1148 → credited +0.0179 →
effectively ~0.084 R, the spread alone. Reality is 0.0841 spread **plus 0.1948 commission = 0.2789 R**.
So the MC granted **+0.018 R where reality charged −0.195 R** — a **~0.2 R-per-trade optimistic error, on
exactly the sleeve family that then lost 9 of 9.** That arithmetic rests only on the artifact's own values
and on broker truth.

**The mechanism, stated as the inference it is — this is weaker than an earlier draft of this receipt
claimed.** I wrote that the class map's headroom over measured spread "was accidentally covering
commission". **That cannot be established from the surviving record, and one contemporaneous script
contradicts it.** `wave7_pairs_statarb.py:206-210`, in the *same route directory*, charges the class map
**in addition to** an explicit bid/ask crossing and annotates it as a *"slippage/commission proxy"*:

```python
cross = (spread_price(symA) + abs(beta_entry) * spread_price(symB)) / sd_entry
klass_cost = cost_r_for(symA) + cost_r_for(symB)   # (slippage/commission proxy)
R = gross_R - cross - klass_cost
```

So the map's author may have intended it as commission-inclusive all along, in which case W7's removal of
the "over-charge" was not an accident but a reclassification that dropped a commission proxy. **Both
readings produce the same measured outcome and the same repair; they differ only in whose mistake it
was, and the record does not settle it.** The map is **not re-derivable**: `ULTIMATE_REAL_COST_MAP.json`
enters git history at `450a275f8` as a **JSON-only diff with no generator** (searched across both repo
copies), and `KB7_stale_audit.md:36-39` states the surviving simulated ledgers carry `expected_cost_r`
clamped at 0.18 and are *"NOT the source of the deployed map."* What W7 itself did is documented:
`KB7_execution_truth.md:31-47` tabulates the class map directly against a column headed *"TICK-observed
round-trip **spread** R"* and calls the metals difference a *"~4x OVER-charge (too harsh)"* — i.e. the W7
pass treated the two as the same quantity, with commission in neither.

### 5.2c `TICK_SPREAD_FLOOR_R` is inert, and covers a quarter of what traded

`admission.py:73-86` holds 9 symbols. It is **never enforced** — `v4_timewarp…py:58695` hardcodes
`"measured_tick_spread_floor_enforced": False`, and the floor serves only as a quote substitute when a
tick is missing. `is_tick_tradeable()` has no production caller. The same-class transfer table its own
comment promises (`:93-94`, *"GBPJPY ← USDJPY"*) **does not exist**, so `tick_spread_floor_for` returns
`None` and `is_tick_tradeable` returns `True`.

| | |
|---|---:|
| live symbols with a floor | **4 of 18 (22.2 %)** |
| live entries covered by a floor | **26.8 %** |
| floor symbols never traded | 5 of 9 (55.6 %) |
| **GBPJPY** — 23 live trades, worst measured spread (0.183 R) | **no floor** |
| XAUUSD floor 0.0118 vs measured round-trip 0.0409 | **3.47× understated** |
| BTCUSD floor 0.0001 vs measured | **77.8× understated** |

**An integrity gap worth its own line:** `admission.py` sets the **sealed replay's** spread floor
(imported `v4_timewarp…py:106-107`, applied `:58745`, `:58791`, `:58939`) and is **not in R2's bound
paths nor in `code_authority_paths`** — so the cost floor the sealed economics rests on can be edited
without triggering `selection_sizing_decision_contract_input_drift`. Filed **F40**.

### 5.3 The live cost model's own numbers, and the gate that was widened

Recovered from `skip_reason` rejection strings, because the ledger that should hold this died:

| sleeve | rejections | measured `total_cost_r` | its limit |
|---|---:|---|---:|
| **`fx_jpy`** | 32 | 0.4569 → **1.3744** | **0.45** |
| **`fx_jpy_ny`** | 5 | 0.4571 → 0.6153 | **0.45** |
| `orb_crypto_london` | 9 | 0.1624 → 0.6252 | 0.15 |
| `asian_fade` | 7 | 0.1500 → 0.2553 | 0.15 |
| `kz_london_crypto_low` | 5 | 0.1843 → 0.3373 | 0.15 |
| `asia_pdl_fade` | 3 | 0.1795 → 0.3126 | 0.15 |
| `metal_session_reversion` | 1 | 0.1533 | 0.15 |

**The JPY sleeves ran a cost gate 3× looser than every other sleeve, and the config documents it in the
owner's own framing** — `agent_config.yaml:715-729`, verbatim:

> `selected_cell_pretrade_max_spread_r: 0.10` / `selected_cell_pretrade_max_total_cost_r: 0.15`
>
> *"# OWNER-APPROVED JPY-CROSS LIVE TRIAL (2026-06-16): fx_jpy/fx_jpy_ny are M15 session-momentum
> scalps with a ~8-pip stop (1.0\*ATR(M15)); a normal JPY-CROSS spread (GBPJPY ~2 pips) is ~22% of that
> stop, **which the global 0.10 spread / 0.15 total-cost gate correctly refuses** (USDJPY at ~0.3 pips
> passes). To **MEASURE the live edge net of spread** (not reject from logs), these two sleeves run a
> looser ceiling ONLY. … Set the by_sleeve maps to {} to end the trial and revert to the strict global
> gate."*
>
> `fx_jpy: 0.35` / `fx_jpy_ny: 0.35` (spread) · `fx_jpy: 0.45` / `fx_jpy_ny: 0.45` (total cost)

The trial was dated (**2026-06-16**, one day after the book went live), its purpose was explicit, and it
recorded its own reversal procedure. **It has returned its result: −2,349.58 over 41 trades, 7 winners,
mean −0.591 R net / −0.453 R gross, `p = 0.00016`.** The strict gate's judgement that these trades
should be refused was correct — and note the gross figure: even before cost, the JPY sleeves lost.

The spread screen shows how thin the margin was where it fired: rejections at stop/spread ratios of
**2.52×, 2.38×, 1.09× and 0.77×** — in the last case **the stop was inside the spread**.

**Verdict on axis (c): PARTIAL on spread — 88.0 % of positions / 78.6 % of days for tick-derived spread,
0 % for per-trade spread on admitted trades — but COMPLETE and unambiguous on the term that matters.**

Commission and swap are broker-truth-exact at **100 % coverage on all 175 trades and all 14 days**, they
are **31.6 % of the net loss and 37.8 % of absolute gross P&L**, and **the validation charged zero for
them at five independent sites behind a circular gate** (§5.2a). Slippage, which I previously reported as
unmeasurable, is measurable and is **small** (+0.012 R, §8 G1). Stops fill clean (−1.0036 R gross).

**So the friction that broke this window is not slippage and not spread — it is a first-order cost term
the model does not contain, concentrated on precisely the sleeves that lost and absent from the one that
won.** The 0.45 R JPY cost gate was widened to measure an edge net of spread while commission — up to
0.195 R per trade on USDJPY — was outside the arithmetic entirely.

---

## 6. Axis (d) — the asymmetry. The stated mechanism is refuted; the real one is measured

64 signals fired on **both** accounts as the same `(sleeve, symbol, side, UTC day)`; 33 were FTMO-only,
14 redacted_account-only. Paired: FTMO **−2,152.72**, redacted_account **−2,358.20**. Unpaired: FTMO −398.85,
redacted_account −1,377.72. **redacted_account was sized larger on the same signal — median risk ratio 1.398, mean
1.502.**

**`VPS_EXPORT_FINDINGS.md` V4's causal claim is refuted.** V4 says the 18-of-19 `trade_contract_size`
divergence *"gives the FTMO-vs-redacted_account asymmetry on identical signals … a concrete mechanism rather
than a hypothesis."* Tested directly [MEASURED]:

| paired signals | n | median risk ratio FN/FTMO | IQR |
|---|---:|---:|---|
| **equal** contract size | 39 | **1.411** | 1.05 – 1.69 |
| **unequal** contract size | 25 | **1.355** | 1.03 – 1.58 |

**Indistinguishable.** The oversizing is uniform across symbols whose contract sizes agree and those
differing by up to 10×. V4's spec divergence is **not** the mechanism — and the corollary is good news
the audit did not have: **the sizer handles the per-broker contract-size divergence correctly.** V4
remains a true and important measurement about the brokers; it is not the cause of the asymmetry.

**The real mechanism, from the live governor's own telemetry** [MEASURED —
`W7_PACKET_FORENSICS.json:governor_asymmetry`]:

| | FTMO | redacted_account | ratio |
|---|---:|---:|---:|
| `governor.size_cap_multiplier`, median | **0.5405** | **0.8537** | **1.579** |
| `unit_risk_pct`, median | 0.1277 % | 0.2022 % | 1.583 |
| `governor.reason` | `derisking_into_maxdd_wall` on **79/79** | on **66/66** | |
| overlays | `ladder_step2` ×51, `coloss_breaker` ×44 | `coloss_breaker` ×55, `ladder_step2` ×39 | |

**FTMO entered the W7 window already −2.74 % down from the fleet era** (equity 97,052 vs redacted_account's
99,965), **so its reactive de-risk ladder was further along.** Same book, same signals, two independent
worker processes, different governor states → redacted_account took ~1.6× the size. The entire window ran with
the drawdown defence engaged on both accounts.

**So the asymmetry is the safety machinery working.** `ultimate_book_stress_derisk` shrank FTMO's
exposure precisely because FTMO was the account already in drawdown, and FTMO consequently lost less
(−2.55 % vs −3.74 %) on a book whose expectancy was negative. That is the overlay doing exactly what it
was built to do, measured live for the first time.

---

## 7. Sample size — the arithmetic, and what it does and does not license

**At account level the result is not distinguishable from the validated model.** Using CYCLE62's own
per-unit daily R distribution for the deployed book (`series.core8`: n=1679, mean **+0.08151 R**,
std 0.65754, at `eff_pct` 1.729), read from `origin/live-handoff-2026-06-15@98da29d2a` since the
artifact `agent_config.yaml:1299` cites exists nowhere on disk:

| | FTMO | redacted_account |
|---|---:|---:|
| trading days | 14 | 14 |
| realized | −2.5516 % | −3.7359 % |
| model at **certified** risk: expected ± sd | +1.973 % ± 4.254 % | +1.973 % ± 4.254 % |
| → z, one-sided p | **−1.06, p 0.144** | **−1.34, p 0.090** |
| model **rescaled to deployed risk**: expected ± sd | +1.017 % ± 2.193 % | +1.191 % ± 2.569 % |
| → z, one-sided p | **−1.63, p 0.052** | **−1.92, p 0.028** |

The rescaled row is the fairer test. Even so: **−1.6σ and −1.9σ.** The two accounts are **not
independent** — same book, 64 shared signals — so they cannot be pooled into a stronger claim. And
CYCLE62's own median days-to-target is **64 (redacted_account) / 110 (FTMO)**; 14 days is **13–22 % of that
horizon**. Fourteen days is a thin basis for overturning a 2014–2026 validation, and the arithmetic says
so.

**At sleeve level one result is ~~decisive~~ *[AMENDED 2026-07-27 — real, but not decisive; the
denominator below double-counts cross-account duplicates. See §15]*, and small-sample caution would be
a way of not reporting it.**
`P(wins ≤ k)` under a generous Binomial(n, 0.45):

| | n | wins | mean R (net) | mean R (gross) | p |
|---|---:|---:|---:|---:|---:|
| **JPY cluster pooled** | **41** | **7** | **−0.591** | **−0.453** | **0.00016** |
| `fx_jpy` | 32 | 7 | −0.436 | −0.290 | 0.0059 |
| `fx_jpy_ny` | 9 | **0** | −1.142 | −1.036 | 0.0046 |

~~That survives Bonferroni over the 12 sleeves that traded (0.00016 × 12 = 0.0019)~~ *[STRUCK
2026-07-27 — the pooled n=41 counts each cross-account duplicate twice. At the honest signal-level
denominator: **29 distinct signals, 6 winners, p = 0.00588, ×12 = 0.0706** — which does **not** survive
at 0.05. §15]*, and it survives on
the **gross** figure too, so it is not an artifact of the cost gate. **It is a real signal at n=41 and
should be reported as one** *[amended: real, yes — direction and magnitude stand at 29 independent
signals; "decisive" does not. §15]*.

**Both statements hold and neither is a hedge:** the *window* cannot falsify the book's validation, and
the *JPY-cross trial* has returned a clear negative on its own terms — which is what it was switched on
to do.

---

## 8. Gaps, named rather than absorbed

- **G1 — CORRECTED. Entry slippage IS measurable, and it is small.** An earlier revision of this
  receipt stated 0 % coverage on the strength of finding V2. That was wrong twice over. `order_result`
  is not a literal key anywhere — the result object is `order_send_observation.result`, and while
  `…result.price` is `0.0` on all 149 rows, **`order_send_observation.request.price` is populated
  149/149 and `deal_cost_reconciliation.broker_entry_price` 140/149**, which is a requested/filled pair.
  Measured entry slippage: **mean +0.0132 R (n=140)**, median +0.0003, p95 +0.069, 78 adverse / 25
  favourable / 37 exactly zero. Independently corroborated by `slippage_runtime.jsonl` on a different
  denominator: **mean +0.0108 R (n=147)** entry-only, sign convention `>0 = adverse`, side-normalised.
  Worst are the tight-stop FX legs (AUDUSD +0.041, GBPUSD +0.040, USDJPY +0.039); XAUUSD is +0.003.
  **Coverage is 11 of 14 W7 days (78.6 %)** — both files start 2026-06-18T17:15:48Z, so 06-15/16/17 are
  unmeasured for slippage by any source. Combined with the clean −1.0036 R gross stop (§5.2),
  **slippage is not a material contributor to this drawdown; commission is.**
- **G2 — packet `spread_r` is NULL on all 99,112 rows.** What replaced it is the cost-gate **rejection**
  strings, which by construction describe only *refused* trades — a censored sample biased toward high
  cost. Admitted trades' spreads are not recorded.
- **G3 — tick coverage is 88.0 %.** The export begins 2026-06-18; the window begins 2026-06-15. **21 of
  175 positions (12.0 %) have no tick data.** Closing it needs a three-day tick pull on both brokers.
- **G4 — why the five high-confidence core sleeves generated nothing is undetermined.** They emitted no
  admissions and no shadows, so the question is generation, not admission. Distinguishing "natural low
  frequency at 14 days" from "generation defect" needs either the validation's per-sleeve firing
  frequency (not vendored at HEAD) or a shadow re-run over the window. **Highest-value single gap here**
  — §9.
- **G5 — cost attribution is exact for commission and swap, bounded for spread.** The −1,984.35 is
  broker truth. The spread component sits inside `gross_profit` and is separable only where ticks exist
  (G3) and a requested price exists (G1).
- **G6 — the pre-W7/W7 split rests on the comment string alone.** Both eras share `magic 20260401`. §3
  gives the three independent corroborations (directionality of the emitter, zero `W7:UNTAGGED`, the
  11-day blank gap) and CYCLE62's own account label `FTMO_97p2k_tgt110` independently confirms FTMO
  stood at ~97.2 k when the dial was certified. I found no second per-trade source.
- **G7 — sleeve-name uniqueness after MT5's 16-char truncation is unenforced.** Two `mx_ger40_cash_*`
  and two `mx_aus200_cash_*` names collide at 13 chars; only one of each is live, so no collision
  occurred. **F34**.
- **G8 — redacted_account's `trade_tick_value` is quantised to 2 dp and is wrong by up to +5.5 %** on GER30,
  UK100 and JP225. My R uses a factor solved from each position's own realized P&L, which is unaffected
  and is provably the more accurate of the two (§14). Anything that sizes from redacted_account's spec inherits
  the error. **F37**.

---

## 9. What would actually settle OD-1

1. **Replay the 14 live days through the book in shadow with the live config, and count generation per
   sleeve.** Closes G4 for one bounded run and answers directly: were `metals_core`, `crypto` and
   `energy_agri` silent because 14 days is short, or because generation is broken? If the former, OD-1
   stands and needs a longer forward window. If the latter, the activation candidate has a generation
   defect and OD-1's premise is materially wrong.
2. **Do not spend Phase 2 on a broad-stack pivot on the strength of this window.** The standing risk row
   treats a G1b failure as evidence for the broad lane. This window is not that evidence — it measured
   neither stack. The broad V4 selector's own −0.25 R/fill over 454 fills
   (`ULTIMATE_GO_LIVE_DOSSIER.md:276-280`) remains the better-evidenced number about that lane, and it
   is negative.
3. **The 29-sleeve composition that ran has no joint validation.** `live_system_of_record.md:107-112`
   measured that CYCLE62 contains zero occurrences of "candidate", "expansion" or "weighted12". If those
   two books stay on they need their own MC at the live dial; if not, the config change is one line each,
   and this window's 76.4 %-of-net / 67.4 %-of-gross loss share argues for it.

---

## 10. For the owner — three decisions, none of which I have taken

1. **The JPY-cross trial has returned its result. End it?** `agent_config.yaml:717-729` says how: set
   `selected_cell_pretrade_max_spread_r_by_sleeve` and `selected_cell_pretrade_max_total_cost_r_by_sleeve`
   to `{}`, reverting `fx_jpy`/`fx_jpy_ny` to the strict global 0.10 / 0.15 gate. Basis: −2,349.58 over
   41 trades, 7 winners, −0.591 R net and **−0.453 R gross**, p = 0.00016; the live cost model itself
   measured up to 1.37 R round-trip cost on the sleeve.
2. **The JPY cluster is the only cluster exempt from the one-unit-per-cluster-per-day cap**
   (`ultimate_book_cluster_cap_exempt_clusters: ["jpy"]`, ~~`agent_config.yaml:1370`~~
   **`agent_config.yaml:1374`** *[citation corrected 2026-07-27 — §15]*), which let `fx_jpy`
   (London) and `fx_jpy_ny` (NY) both take correlated units on GBPJPY and USDJPY the same day. The
   exemption's stated purpose was the trial in (1). ~~If the trial ends, does the exemption?~~
   *[REFRAMED 2026-07-27 — the cap itself is globally `false` at HEAD
   (`agent_config.yaml:1373`), so the exemption is inert and ending it changes nothing. The real
   decision is whether to re-impose the certified one-unit-per-cluster-per-day envelope **at all**, for
   every cluster. See §15.]*
3. **The candidate book carries 76.4 % of the net loss (67.4 % of gross losses) and has no cited
   validation.** Keeping it on at the 2.00 % base is a risk-composition decision, not an engineering one.

I have changed no config. Everything in this receipt is measurement.

---

## 11. Defects filed

| id | sev | what | status |
|---|---|---|---|
| **F32** | med | `governor_daily_reset_offset_hours: 3.0` hardcodes UTC+3 as FTMO's daily-loss reset; FTMO resets **00:00 CE(S)T** (UTC+2 in summer), and a constant is wrong for both accounts in the ~4 weeks/year the US and EU calendars disagree. `agent_config.yaml:1348`. Did not bite this window. | filed, not fixed — live governor boundary, owner-visible behaviour change |
| **F33** | med | The packet's declared redaction policy `hash_ticket_and_account_identifiers_v1` is an **unsalted SHA-256 of a 9-digit ticket** (`src/components/ultimate_book/runtime_learning_packet.py:99-101`). A rainbow table over the 629 real ids reverses it; the redaction provides no privacy. It is also what made this receipt's cross-validation possible, so it cuts both ways. | filed |
| **F34** | low | Nothing enforces sleeve-name uniqueness after MT5's 16-char comment truncation (G7). | filed |
| **F35** | low | `broker_actual_r_audit.jsonl` can never join sleeve to ticket: builder A hardcodes `"ticket": None` (`src/research_infra/broker_actual_r_audit.py:289`), builder B hardcodes `"candidate_id": None` (`:398`). Measured: **0 of 285** rows carry both; **277 of 285** have `broker_actual_r == null`. Despite the name it holds no W7 realized R. | filed |
| **F36** | low | Packet `spread_r` declared and NULL on all 99,112 rows (G2). | filed |
| **F37** | med | **redacted_account quantises `trade_tick_value` to 2 decimals**, so tv/ts is wrong by **+5.5 % (GER30), +5.1 % (UK100), −1.7 % (JP225)**. Provable inside redacted_account's own file: GER30 spec gives 12.0000 where 10 × its own EURUSD bid gives 11.3701. FTMO does not quantise. Anything sizing from the redacted_account spec inherits the error; this receipt's solved factor does not. | filed |
| **F38** | **HIGH** | **The validation and the live pre-trade engine charge zero commission, at five independent sites, and the gate that should catch it is circular.** `broker_net_cost_engine.py:577-583` computes `total_cost_r = spread_r + expected_slippage_r + swap_cost_r`. The `commission_model_required` gate (`:729-736`) accepts a status string emitted by the code it gates (`execution_packets.py:340`), and on all 149 live intents `selected_cell_risk_decision_basis` was **null**. Realized commission is **0.0591 R/trade** and **37.8 % of absolute gross P&L**, concentrated on FX/JPY/crypto (USDJPY 0.1948 R) with the six index CFDs at exactly zero. §5.2a. | filed — the highest-value cost repair for Phase 6 |
| **F39** | **HIGH** | **`INTEG_W7_FINAL_RESULT.json`'s `tick_erosion_applied` grants positive credits where reality charges a cost.** USDJPY **+0.0179**, XAUUSD +0.019, USOIL_cash +0.037, applied as `R + h` (`KB7_tick_mc.py:62`). USDJPY's true charge is ≈ **−0.195 R**, so the MC is optimistic by **~0.2 R/trade on the sleeve family that lost 9 of 9** — measured from the artifact's own values plus broker truth. **Why the headroom existed is NOT established:** `wave7_pairs_statarb.py:206-210`, same route, charges the map on top of a real spread crossing and calls it a *"slippage/commission proxy"*, so the map may have been commission-inclusive by intent. Both readings give the same repair. The map has **no generator** (`450a275f8` is a JSON-only diff, searched in both repo copies). §5.2b. | filed |
| **F40** | med | **`admission.py` sets the sealed replay's spread floor and is not contract-bound.** Imported `v4_timewarp…py:106-107`, applied `:58745/:58791/:58939`, absent from R2's 43 paths and from `code_authority_paths` — so the cost floor the sealed economics rests on can be edited without triggering `selection_sizing_decision_contract_input_drift`. Also: `TICK_SPREAD_FLOOR_R` is never enforced (`measured_tick_spread_floor_enforced: False`), covers 26.8 % of live entries, and the same-class transfer table its own comment promises does not exist. §5.2c. | filed |
| **F41** | low | **`pretrade_cost_model.profile.dual_broker_role` reads `follower_projector_only` for FTMO (80 intents) and `primary_full_runtime` for redacted_account (69)** — contradicting `live_system_of_record.md`'s "two fully independent per-account workers, **not** primary/follower". Either the doc or the runtime packet is wrong about the live topology. Not the axis-(d) mechanism (§6 measures that directly) but it is an unexplained structural asymmetry between the accounts. | filed |

**Also corrected in the record, not defects:**

- `VPS_EXPORT_FINDINGS.md` **V4's causal claim** that contract-size divergence drives the FTMO/redacted_account
  asymmetry — **refuted** (§6). The measurement stands; the attribution does not, and the sizer in fact
  handles the divergence correctly.
- `SECOND_AUDIT.md:159-160`'s **FTMO −5.3 %** — correct about the account, misattributed to W7. W7's own
  contribution is **−2.55 %** (§2). The true account trough is **−5.3803 %**.
- The same passage's **"FN's 06-18 start is not pinned (pre-halt fleet losses on the same account)"** —
  the start is pinned exactly; the redacted_account `GoldAgent` fleet era was **net positive +988.47**, and the
  whole pre-W7 period was approximately flat, so **99.1 % of redacted_account's account loss is W7's**.
- The window starts **2026-06-15**, not 06-18.

---

## 12. Measured cost inputs for Phase 6, with coverage

| input | value | modelled | coverage | source |
|---|---|---|---|---|
| **commission, in R, mean** | **0.0591 R/trade** (ratio-of-means 0.0601) | **0.0000** | **100 %** | broker deals ÷ measured risk |
| commission + swap, in R, mean | **0.0725 R/trade** (FTMO 0.0808, FN 0.0622) | 0.0000 | 100 % | as above |
| commission + swap, total | **−1,984.35** = 31.6 % of net loss; commission alone = **37.8 % of abs. gross** | — | 100 % | broker deals |
| commission, per trade, USD | FTMO $8.69, FN $10.08 | — | 100 % | broker deals |
| **commission by class** | **USDJPY 0.1948 · AUDUSD 0.1509 · BTCUSD 0.1102 · GBPUSD 0.1065 · EURUSD 0.1063 · GBPJPY 0.0927 · ETHUSD 0.0589 · XAUUSD 0.0054 · all 6 index CFDs 0.0000** | 0.0000 | 100 % | broker deals |
| swap, per trade, mean | FTMO −$1.20, FN −$3.07 (0.0134 R) | ~0 | 100 % | broker deals |
| **stop-out, median GROSS R** | **−1.0036** — a clean fill | −1.0000 | 102 SL closes | broker deals + order SL |
| stop-out, median cost R / net R | −0.0720 / −1.0691 | 0 / −1.0000 | as above | as above |
| **entry slippage, mean** | **+0.0132 R** (n=140); corroborated **+0.0108 R** (n=147) | `default_expected_slippage_r: 0.02` | **78.6 % of days** | lifecycle capture; `slippage_runtime` |
| entry slippage, worst legs | AUDUSD +0.041, GBPUSD +0.040, USDJPY +0.039; XAUUSD +0.003 | as above | as above | as above |
| **measured round-trip spread** | XAUUSD 0.0409 R (floor says 0.0118); BTCUSD 77.8× its floor; **GBPJPY 0.183 R, no floor** | `TICK_SPREAD_FLOOR_R` | 4 of 18 symbols | ticks + packets |
| XAUUSD spread, 2026-06-22, median | **FTMO $0.44 / FN $0.50**; FN p95 **$1.31** vs FTMO $0.49 | — | 1 day, 875 k ticks | tick export |
| live cost model, JPY total cost | 0.457 – **1.374 R** | limit 0.45 | censored to rejects | packet `skip_reason` |
| live cost model, non-JPY | 0.150 – 0.625 R | limit 0.15 | censored to rejects | packet `skip_reason` |
| per-trade spread, admitted trades | **unavailable** | — | **0 %** | G2 |
| tick-derived spread | reconstructible | — | **88.0 % of positions / 78.6 % of days** | G3 |
| median holding time | **2.46 h** (mean 8.90 h, max 90 h) | — | 100 % | broker deals |
| realized risk per trade | FTMO 0.109 %, FN 0.143 % (median) | — | 100 % | broker deals + order SL |
| observed / designed unit risk | FTMO 0.376, FN 0.577 (median) | 1.000 | 108 units | broker deals + registry conf |
| governor size-cap applied | FTMO 0.5405, FN 0.8537 (median) | — | 145 placements | packet telemetry |

**What Phase 6 should take from this, in order:**

1. **Add a commission term.** It does not exist (F38) and it is **37.8 % of absolute gross P&L**. Every
   other cost refinement is second-order next to a missing first-order term.
2. **Charge it per instrument class, not per portfolio.** A single 0.06 R portfolio mean is wrong in both
   directions: it over-charges the index CFDs, which pay **zero**, and under-charges USDJPY, which pays
   **0.1948 R**. The distribution is the finding, not the mean.
3. **Fix the erosion sign before re-running any MC** (F39). Applying `tick_real − modeled` as a credit
   gave the JPY sleeves +0.018 R where reality charged −0.195 R.
4. **Do not spend the effort on a fill model.** Stops fill clean (−1.0036 R gross) and entry slippage is
   **+0.012 R** — real, small, and roughly half the `0.02` already assumed. Slippage is not the gap.
5. **Spread floors need per-symbol coverage, enforcement, and the transfer table that was promised**
   (F40). Today they cover 26.8 % of entries, are never enforced, and omit the most-traded symbol.

---

## 13. Reproduce

```bash
python3 scripts/w7_live_forensics.py     # broker-truth lane; prints the residual on both accounts
python3 scripts/w7_packet_forensics.py   # packet-telemetry lane
```

Both are deterministic and read only the read-only export trees. Neither imports `MetaTrader5`, opens a
socket, or touches a broker. The reconciliation printed by the first — residual **0.00** against
107,879.56 and 96,229.28 — is the row set's own correctness proof and is the thing to re-check before
trusting any number above.

---

## 14. The adversarial pass, and what it took off this receipt

An independent verifier was asked to **refute** eight headline claims, writing its own scripts from the
raw JSONL rather than reusing the generator. Recorded because the corrections are the result, not an
appendix to it.

**Confirmed independently:** the exact reconciliation on both accounts (two separate routes, residual
+0.000000); the era split and its disjointness; the FTMO −2.55 % / fleet −2.74 % decomposition; the
redacted_account −3.7359 % point value and the positive `GoldAgent` fleet; the two untagged FTMO positions and
their +13,166.69; `fx_jpy_ny` at 0 wins in 9; the family shares.

**Refuted, and withdrawn from this receipt:**

- **The "10–15× below the 2.00 % dial" under-sizing claim** (§4.1). It compared a per-trade statistic to
  a per-unit base. The corrected measurement is observed/designed **0.38–0.58× at the median with 13
  units over design** — the de-risk overlays doing their job, not a sizing defect. The generator now
  emits the designed value alongside the observed one and no longer prints the base next to a per-trade
  figure.
- **`VPS_EXPORT_FINDINGS.md` V4's causal claim** about the cross-broker asymmetry (§6) — refuted by
  measurement, not by the verifier, but it belongs on the same list.

**Materially corrected:**

- The two untagged FTMO positions are **hand-placed phone trades** (five discriminators, §2.1a), not
  "the post-switch broad system". The generator now classifies them `manual_mobile`.
- **A hand exit inside the W7 window was hidden by a bug.** `kz_london_crypto_low`'s entire positive
  contribution is one phone close worth +304.37; the sleeve is **−45.58** without it (§3).
- The true drawdowns are **−5.3803 % (FTMO)** and **−5.8302 % from peak (redacted_account)**, deeper than any
  era sum, and they are what prop rules measure (§2.1b).
- redacted_account's pre-W7 *era* is **flat (−34.80)**, not +988.47 — so **99.1 %** of its account loss is
  W7's (§2).
- `fx_jpy_ny`'s "worse than −1 R" is **−1.036 R gross plus commission**, not stop slippage. Every group
  now reports gross, cost and net R side by side (§5.2).
- Family shares are given on **two bases**; redacted_account's candidate share is 90.4 % of net but 73.4 % of
  gross losses (§3).

**Ten bugs found in `scripts/w7_live_forensics.py`; all ten are fixed at HEAD.** The two most
consequential: a wrong `ENUM_DEAL_REASON` map that labelled all EA-driven closes as browser closes and
hid the hand exit above (`EXPERT` is 3, not 1); and `_attach_sleeve_meta` resolving `sleeve_cluster` for
core-8 only, leaving **43 % of the book in a cluster called `unknown`** — on the one axis that actually
feeds sizing. Also fixed: the balance/trade split now keys on deal **type** rather than symbol
truthiness (a commission or dividend row carrying a symbol would have corrupted the reconciliation that
*is* this artifact's correctness proof); the W7 window bounds are derived at runtime rather than
hardcoded under a comment claiming they were; falsy-zero guards on risk and R replaced with
`is not None`; and `daily_curve` resolves the DST offset at the exit instant rather than the entry's.

---

## 15. The second pass — what the third review's reader narrowed on this receipt

**Recorded 2026-07-27, in §14's form, because the corrections are the result and not an appendix to
it.** After this receipt was accepted, the third independent review ran its own reader over it
(`THIRD_REVIEW.md` §5 "Session E — KEEP, act on it, and amend the receipt"; confirmed in its
adversarial pass, §A2). Two claims narrow. Neither is deleted above; both are marked in place and
restated here.

**Narrowed — real, but no longer decisive:**

- **The JPY "survives Bonferroni" claim (§7) double-counts cross-account duplicates.** The 41 JPY
  trades are not 41 independent trials. FTMO and redacted_account run the same sleeves on the same symbols
  from their own feeds, so one signal fires twice — a fact this receipt already states at **account**
  level ("the two accounts are **not** independent — same book, 64 shared signals — so they cannot be
  pooled into a stronger claim", §7) and then contradicts at **sleeve** level by pooling trades across
  both. §14's verifier confirmed the computations; it did not test the independence assumption
  underneath them.

  At the honest signal-level denominator — `(sleeve, symbol, side, UTC day)` — the 41 trades collapse
  to **29 distinct signals**. **12 of those fired on both accounts, and they were 12/0
  outcome-concordant**: paired trades are effectively perfectly dependent, so the second copy carries
  no information. Six of the 29 signals won. Under the same generous Binomial(n, 0.45),
  **P(X ≤ 6 | n = 29) = 0.00588**, and Bonferroni over the **12 sleeves that traded** gives
  **×12 = 0.0706 — which does not survive at 0.05.** `fx_jpy_ny` is **0 of 6 independent signals,
  p = 0.0277**, not 0 of 9 (p 0.0046).

  **What stands, unchanged:** the sign; 41 trades and 7 winners; **−0.591 R net and −0.453 R gross**,
  so the result is not an artifact of the cost gate; the live cost model's measured round-trip cost up
  to 1.37 R on the sleeve; and 0-of-6 independent NY signals. **The trial's negative verdict stands.
  "Decisive, survives Bonferroni" does not** — restate it at the signal level before §10 decision 1 is
  taken on it.

  **A reading trap worth naming:** the corrected pooled signal-level p (**0.00588**) is numerically
  almost identical to the §7 table's trade-level `fx_jpy` p (**0.0059**). They are different
  quantities. Do not let the coincidence make the correction look like a no-op.

  [MEASURED — re-derived independently for this amendment directly from
  `phase1/w7_forensics/LIVE_TRADE_ROWS.jsonl`: 41 in-denominator rows with `sleeve_cluster == "jpy"`
  (32 `fx_jpy` + 9 `fx_jpy_ny`), 7 trade-level winners, **29** distinct signal keys, **12**
  multi-account signals, **12/0** outcome-concordant, **6** signal-level winners, **12** distinct
  sleeve tags in the W7 denominator. Binomial tails recomputed at p = 0.45: the receipt's own three
  values reproduce exactly — P(X≤7|41) = 0.000163 (§7's 0.00016), P(X≤7|32) = 0.005855 (0.0059),
  0.55⁹ = 0.004605 (0.0046); the corrected pair is P(X≤6|29) = 0.005879 and 0.55⁶ = 0.027681. **It is
  the denominator that was wrong, not the arithmetic.**]

**Reframed — the decision was posed on a mechanism that is already off:**

- **§10 decision 2 asks whether the JPY cluster's cap exemption should end with the trial. At HEAD
  there is no cap to be exempt from.** `ultimate_book_one_unit_per_cluster_per_day` is globally
  **`false`** (`config/agent_config.yaml:1373`), under a comment that states the trade-off in the
  config's own words: *"a cluster can take >1 correlated unit on a multi-fire day, slightly above the
  certified one-unit-per-cluster-per-day envelope — accepted for trade frequency + the validated
  diversification. Set back to true to re-impose the strict envelope."* The exemption list
  `ultimate_book_cluster_cap_exempt_clusters: ["jpy"]` sits at **`:1374`** and is **inert** while the
  cap is off — the JPY cluster is not privileged relative to any other cluster, because no cluster is
  capped.

  **So the real owner decision is not "does the JPY exemption end with the trial."** Ending it alone
  would change nothing. It is **whether to re-impose the certified one-unit-per-cluster-per-day
  envelope at all**, for every cluster — trading measured trade frequency against the diversification
  the validation certified. That is a strictly larger decision than the one §10 put in front of
  Borhen, and it should be delivered as such.

  **Citation correction:** §10 decision 2 cited `agent_config.yaml:1370` for the exemption list. The
  true line at HEAD is **`:1374`** (line 1370 is a comment). `config/agent_config.yaml` is unchanged
  since `95105914f` and both keys sit at the same lines there, so the citation was **off by four when
  written** — it did not move.

  [MEASURED — read directly from `config/agent_config.yaml` at HEAD and from
  `git show 95105914f:config/agent_config.yaml`.]

**Unchanged by this pass:** §1's verdict and the exact 0.000000 partition; §2's denominator
correction; §3.1's five silent sleeves; §5.2a's zero-commission finding and §5.2b's wrong-sign tick
erosion (which the third review carries as F38/F39, the largest economic findings in the programme);
§6's measured asymmetry; and every §14 disposition.

**One standing caution the reader added — not an amendment, but it belongs beside them:** the
packet-telemetry lane (`scripts/w7_packet_forensics.py`) rests on a **single generator whose
adversarial pass covered only the broker-truth lane**. Treat single-generator packet claims as
one-witness evidence until the generation port cross-checks them (`THIRD_REVIEW.md` §5, Stage 1.3).
