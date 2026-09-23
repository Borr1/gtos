# d8x — WHAT HAVE WE NOT LOOKED AT

**Lane d8x, wave 19.** (Namespaced `d8x` because a concurrent `d8` process was live on this
machine and holding `d8_*.py` / `D8_*.json`; nothing of that lane's was overwritten, and its
`D8_EMIT_*.npz` emission arrays are used here as a read-only substrate with attribution.)

**Three things measured, one framing challenged, one register built. In one line each:**

1. **The broad family carries ZERO information about the live sleeve book.** 4,352 sleeve
   trades in the same 8 windows; every conditioning direction inside the noise band
   (agree−disagree −0.0432, p 0.706; activity hi−lo −0.1069, p 0.930). It is not a filter.
   *By-product:* those same 4,352 trades book **+0.15555 R/trade, CI [+0.0919, +0.2209]** on
   the exact calendar where the broad family books ≈0 — a 32× larger control than d3's n=134.
2. **The bar archive is BID, and every walker in this estate resolves exits against it with
   unshifted levels.** Settled on 76,734 M15 bars × 29 symbols: `close == last tick bid`
   exactly, `high == max tick bid`, `low == min tick bid`. The omitted spread shift is worth
   **−0.0696 R/trade** at the shipped contract — **5.2× f1's entire measured gross deficit
   (−0.01327) and 2.4× f2's entire measured signal (+0.02877).** This closes h3's own #1
   open question.
3. **The toll checked against 300.5 M broker ticks.** Confirms x6's M15-boundary premium with
   an independent whole-archive instrument (33 of 36 FTMO symbols wider in the first 60 s;
   EURUSD +26.07 %), corroborates l10-X12's redacted_account-BTCUSD blowout at **19.71×**
   independently, and finds the archive is **61 files / 300,538,915 accepted ticks against a
   manifest declaring 51 files / 263,894,769 rows** — 10 files in use by four lanes are
   outside both manifests and outside the sha256 verification.

**The framing challenge:** "signal vs usage" is the wrong dichotomy. The evidence implicates a
third thing neither term names — **accumulation** — and the wave's own instrument error is now
larger than the signal it is arbitrating. §5.

**Nothing here opened the sealed three (jun/aug/sep 2025).** They were not read, generated or
referenced.

---

## 1. MEASUREMENT A — is the broad family a FILTER on the live book?

**Nobody had put the two systems on the same rows in this direction.** d3 (concurrent) used the
live sleeves as a *control* — how big is a working signal. This asks the opposite and more
actionable question: the family's output is not only a set of trades, it is a per-instant,
24-instrument reading of *how many setups are firing and in which direction*. That is a
market-state observable whether or not its own trades pay, and the armed book is real money.

**Substrate.** 22,354 sleeve trades from `AQ_ESTATE_TRADES_V2.json.gz` (the estate walk of
record, 32 sleeves, 2017–2026); **4,352** fall inside the 8 broad windows, 518–584 per month,
no month starved. Broad emissions: **1,211,077** from `d8/D8_EMIT_<mm>.npz`. All features are
strictly backward-looking from the sleeve's own `entry_utc`.

| conditioner (at the sleeve's entry instant) | n | R/trade | 95 % CI | p(≤0) |
|---|---:|---:|---|---:|
| **all sleeve trades in the 8 windows** | **4,352** | **+0.15555** | [+0.0919, +0.2209] | **0.000** |
| same-symbol broad emissions AGREE with sleeve side (60 min) | 1,331 | +0.1408 | [+0.030, +0.257] | 0.006 |
| same-symbol broad emissions DISAGREE | 1,318 | +0.1839 | [+0.068, +0.302] | 0.000 |
| **agree − disagree** | — | **−0.0432** | [−0.206, +0.112] | 0.706 |
| any same-symbol emission in 60 min | 2,878 | +0.1556 | [+0.083, +0.234] | 0.000 |
| none | 389 | +0.2416 | [+0.015, +0.473] | 0.017 |
| **with − without** | — | **−0.0860** | [−0.328, +0.133] | 0.760 |
| market-wide emission count 60 min, low tertile (0–264) | 1,422 | +0.1905 | [+0.085, +0.302] | 0.000 |
| … mid (265–323) | 1,464 | +0.1938 | [+0.069, +0.322] | 0.002 |
| … high (324–536) | 1,466 | +0.0835 | [−0.013, +0.178] | 0.044 |
| **high − low** | — | **−0.1069** | [−0.257, +0.036] | 0.930 |
| market-wide breadth (distinct symbols firing), high − low | — | −0.0221 | [−0.150, +0.107] | 0.636 |
| market-wide direction aligned with sleeve side, high − low | — | −0.0174 | [−0.165, +0.130] | 0.580 |

Spearman(feature, sleeve R) over all 4,352: activity-60 **−0.0226**, activity-15 **−0.0151**,
breadth **+0.0079**. Per sleeve (5 sleeves with n ≥ 60 and a spread of the feature): the
activity hi−lo delta is negative on 4 and positive on 1, none significant, best p 0.131.

**d8x-A1 — VERDICT: the broad family is not a filter, in either polarity.** Not by agreement,
not by presence, not by breadth, not by directional consensus. The one consistent *direction* —
high broad-family activity is mildly bad for the live book (−0.107 R/trade, same sign on
activity-60, activity-15 and breadth) — never clears its own confidence band and would be a
6-look pick if it did.

**d8x-A2 — the by-product is the larger number.** On the identical eight months the estate's
*other* generator books **+0.15555 R/trade with the CI clear of zero on 239 day-blocks**, while
the broad family's clean roster books −0.01327 gross / −0.29445 net (f1). This is not a
sleeve-versus-broad economic claim (different symbols, different contracts, sleeves in-sample),
but it **kills one specific alibi**: the eight windows are not an untradeable market. Something
made money on them. The armed subset (n = 138, five sleeves) books +1.2408 R/trade.

**Coverage limit, stated:** 3,267 of 4,352 sleeve trades (75.1 %) are on a symbol the broad
universe carries. The other 1,085 sit on 18 instruments the broad family does not trade
(`UK100_cash`, `JP225_cash`, `US500_cash`, `GER40_cash`, `DASHUSD`, `LTCUSD`, `XPDUSD`,
`XPTUSD`, `XAUEUR`, …). **The two systems do not measure the same market surface** — which is
itself a finding about how little of the estate's instrument space the broad family covers, and
it is why the market-wide features (which need no symbol match) carry the headline.

Receipt `D8X_CROSS_V1.json`, script `d8x_cross.py`.

---

## 2. MEASUREMENT B — the quote side of the bar archive, and what it costs every walk

h3 §11 names this as its **#1 open question**: *"The quote side of the M1 archive. Settling bid
vs mid changes the passive-entry arithmetic by …"*. e5 §12 item 1 names the same class of
question as *"the single highest-value next measurement in the lane"*. It has never been
settled, because the two artifacts were never put side by side.

**They overlap by 37 days and both are in RAW broker stamps, so the measurement takes no clock
risk at all:**

* `vps-bars-20260727` — M15 OHLC + the MT5 `spread` column, to 2026-07-24
* `vps-ticks-20260726` — raw bid/ask ticks, same broker, same wall clock, from 2026-06-18

**Result, over 76,734 M15 bars on 29 symbols — unanimous and exact:**

| tested | median, in units of the prevailing spread |
|---|---:|
| (bar close − last tick **bid**) | **0.000000** (range across 29 symbols: [0.0000, 0.0000]) |
| (bar close − last tick **mid**) | **−0.500000** (range [−0.5000, −0.5000]) |
| bar close **exactly equal** to the last tick bid | **100.00 %** (min per-symbol share 0.9997) |
| (bar high − max tick **bid**) | **0.0000** |
| (bar high − max tick **ask**) | −1.0000 |
| (bar low − min tick **bid**) | **0.0000** |
| (bar low − min tick **ask**) | −1.0000 |

**d8x-B1 — the archive is BID on open/high/low/close. Settled, not inferred.**

### 2.1 The consequence, which nobody has priced

A long buys the **ask** and sells the **bid**; a short sells the **bid** and buys the **ask**.
Either way the exit legs sit one spread away from the series the walks resolve on, so against a
bid series the true trigger conditions are

```
stop   touched when adverse    excursion >= d - s     (EASIER than walked, by s)
target touched when favourable excursion >= T*d + s   (HARDER than walked, by s)
```

— **the same shift on both sides**, so this is not a long/short asymmetry, it is a uniform
optimism. The estate's walker of record does neither shift:

```python
# phase19/receipts/pbg/pbg_econ.py:117, :130-136
tgt = entry + target_r * d if long else entry - target_r * d
...
if long:  hit_t = hi >= tgt;  hit_s = lo <= stop
else:     hit_t = lo <= tgt;  hit_s = hi >= stop
```

`hi`/`lo` are the bid series just settled. **Charging a spread COST does not repair this**: cost
is a level adjustment applied after the fact, the shift is a *resolution* adjustment — a trade
booked as reaching target may in truth have stopped first, and no cost term can undo a wrong
exit reason.

**Measured over all 1,129,304 emissions (93.2 % of 1,211,077; the rest lack a finite risk
distance or excursion), spreads from this lane's own whole-archive tick table:**

| | value |
|---|---:|
| median spread / risk distance (`s/d`) | **0.0988** |
| mean `s/d` | 0.1405 |
| p90 / p99 | 0.2960 / 0.7359 |
| share of emissions with `s/d` > 10 % / 25 % / 50 % / 100 % | **49.4 % / 13.8 % / 3.3 % / 0.26 %** |
| median risk distance | 8.084 bps |
| median spread | 0.775 bps |

| contract | stop-touch Δ | target-touch Δ | **first-order R bound** |
|---|---:|---:|---:|
| T=2.0, horizon 15 min | +5.27 pp | −1.35 pp | **−0.07983** |
| T=2.0, horizon 60 min | +4.54 pp | −2.17 pp | **−0.08879** |
| **T=2.0, horizon 240 min (the shipped contract)** | **+2.86 pp** | **−2.05 pp** | **−0.06956** |
| T=2.0, horizon 24 h | +1.19 pp | −1.10 pp | −0.03400 |
| T=1.5 (`risk.min_rr`), horizon 240 min | +2.86 pp | −2.38 pp | −0.06437 |

By risk-distance decile at the shipped contract the bound runs **−0.1132 (tightest, d 0.26–3.41
bps) → −0.0361 (widest, d ≥ 34.6 bps)** — monotone, and largest exactly where f1 measured the
toll to be largest. The bound charges a newly-touched stop at −1 R and a lost target at −T·R and
ignores ordering, so it is a **bound, not a book**.

**d8x-B2 — the estate's walkers are optimistic by more than the entire quantity they are
arbitrating.** −0.0696 R/trade against f1's clean-roster gross deficit of −0.01327 (**5.2×**)
and against f2's measured signal of +0.02877 (**2.4×**).

**This does not overturn the wave's verdict — it deepens it, and that is why it is safe to
report and unsafe to ignore.** The correction makes the broad family *more* negative, so every
"the family is short of its toll" conclusion survives a fortiori. What it does overturn is the
error bar on every *usage* lever priced on the same walkers: exit frontiers, trail contracts,
target ladders and delay levers are all measured through an instrument whose bias is 0.07 R and
whose sign is always the same way. Any lever worth less than that is not distinguishable from
the instrument.

Receipts `D8X_QUOTESIDE_V1.json`, `D8X_GEOM_V1.json`; scripts `d8x_quoteside.py`, `d8x_geom.py`.

---

## 3. MEASUREMENT C — the toll against 300.5 M ticks

The toll is 21× the signal deficit (f1), so it is the most load-bearing number in the wave.
Whole-archive, no sampling: **61 files, 300,538,915 accepted ticks** (FTMO 36 files /
128,150,823; redacted_account 25 files / 172,388,092), spread histogrammed at 0.02 bps resolution by
UTC hour and by position inside the M15 bar.

**C1 — the M15-boundary premium reproduces on an independent instrument.** x6 measured it with
per-minute medians; this measures it with a whole-archive tick-weighted histogram, and agrees:
**33 of 36 FTMO symbols quote wider in the first 60 s after an M15 boundary than at 5–15 min
in.** Median premium +3.89 %, mean +6.65 %.

| symbol | s∈[0,60) | s∈[300,900) | premium |
|---|---:|---:|---:|
| EURUSD | 0.1422 | 0.1128 | **+26.07 %** |
| USDJPY | 0.3605 | 0.3064 | +17.67 % |
| USDCHF | 0.9033 | 0.7770 | +16.26 % |
| EURGBP | 0.9065 | 0.7816 | +15.99 % |
| GBPUSD | 0.4494 | 0.3917 | +14.73 % |
| XAGUSD | 9.9585 | 9.3825 | +6.14 % |
| XAUUSD | 1.1626 | 1.1316 | +2.75 % |
| BTCUSD | 0.1834 | 0.1819 | +0.81 % |

The effect is concentrated in **FX majors and crosses**; index CFDs, crypto and oil are flat
(≤ +1 %). So the delay lever's microstructure credit is an FX phenomenon and is worth ~0.03 bps
there — real, mechanistic, and **too small to matter against a 3.06 bps toll**. That is a useful
negative: the delay lever's value is not a spread artifact.

**C2 — redacted_account costs more than FTMO, and BTCUSD is the outlier, independently.** On 17
shared symbols the redacted_account/FTMO tick-weighted spread ratio has median **1.132**; the extremes
are **BTCUSD 19.71×**, USDCHF 1.99×, USDJPY 1.72×, EURGBP 1.67×, and four crosses where
redacted_account is *cheaper* (CHFJPY 0.69×). l10-X12 reported BTCUSD at 21.9× from a different
instrument — this corroborates it to within 10 % and confirms h1's own caveat that its FTMO
surface does not transfer across brokers. **`crypto` is armed on both accounts.**

**C3 — a provenance defect in the archive four lanes are using.** `TICKS_MANIFEST.jsonl` +
`TICKS_MANIFEST_V2.jsonl` declare **51 files / 263,894,769 rows**, all sha256-verified
(CLAUDE.md §4 quotes exactly that). On disk there are **61 `*.csv.gz`**, six of them written
**2026-07-30**, four days after the manifest. This lane accepted 300,538,915 ticks from them.
**Ten files, ≈36.6 M rows, are outside both manifests and outside the hash verification**, and
they are already inside the estate's cost model (`pbg_econ.CostModel` loads
`L10X_TICK_SPREAD_V1.json`, built from this directory). Cheap to close: re-run
`scripts/declare_tick_export_timebase.py` / the manifest builder over all 61.

Receipt `D8X_TICK_TOLL_V1.json`, script `d8x_ticks.py`.

---

## 4. THE REGISTER — questions raised and never answered

Built by reading every `*_RESULT.md` under `discovery/` (39 lane receipts + the swarm-1
synthesis) and extracting every "what would make this bankable", "what is still missing",
"limits", "what would have to be true" section. Ranked by **decision value per unit of effort**.
Status: **OPEN** · **CLOSED HERE** · **MIS-STATED** (the receipt's own premise is wrong).

| # | question | raised by | status / price |
|---|---|---|---|
| R1 | **Is the bar archive BID or MID?** Every exit resolution in the estate depends on it. | h3 §11.1; e5 §12.1 | **CLOSED HERE.** BID, exactly, 76,734 bars. Consequence −0.0696 R/trade (§2). |
| R2 | **Do the POI-limit families (46 % of the book) have any edge once non-fills are booked at 0?** | synthesis U1 (PRIORITY 1); e4 §10.3; e-stack §6 | **PARTLY CLOSED, elsewhere in this wave.** d4 §3.5 re-gated the limit book on R units: 69,233 fills, gross −0.01065, toll +0.23916, net −0.24981. e4 §8.3 gives the per-*placed*-order curve for March only. Still open for Jan/Feb: their raw ledgers lack `counterfactual_order_fill_status`. |
| R3 | **Does the family's signal accumulate with holding time?** The 120-M1-bar wall is a pending-order expiry, not a contract. | synthesis U8; e-coherence §6 M1; e2 B4; e6 | **CLOSED, concurrently, by d3 and by the live `d8` lane.** d3: broad grows **0.97×** over 2 h → 320 h while a live sleeve grows **37.58×**. This is the single most important closed question of the wave (§5). |
| R4 | **Is there a random-TIME null anywhere?** Every lane compared the pool to itself. | e-coherence §6 M2 | **CLOSED** by f2's PLACEBO-TIME (pooled R1 −0.00149) and by the `d8` lane's 96-window grid control. |
| R5 | **Does anything separate the ±0.04 gross band into a positive cell big enough to pay 0.22 R?** | f1 §7 — *"the one thing that has never been measured"* | **OPEN, and it is the last standing economic question about this family.** f2 bounds it hard: a conditioner must find ≥ +0.330 R inside a population whose total directional content is +0.003 ± 0.010. |
| R6 | **Index commission.** h2's GER40/NAS100 headline assumes **0.0 commission on every index CFD** (`e_lib._COMM:85`); margin is +0.87 / +0.68 bps, so > ~0.7 bps round trip erases it. | h2 §8.3 — *"the single cheapest thing that could falsify the headline"* | **OPEN. Needs one broker statement, not a replay.** Both accounts are live; h4 already inventoried the live records. |
| R7 | **Does the April/May travel test need a bar capture?** | h2 §8.1 | **MIS-STATED — CLOSED HERE.** h2 says *"there are no April or May 2026 M1 bars anywhere on this machine"*. There are: `bridge_ftmo_m1_202604` and `_202605`, 24 symbols each, in the same directory h2 cites. Eleven months of M1 exist (202506, 202508–202605). d3, f2 and the `d8` lane already used them. **h2's headline is testable out of sample today.** |
| R8 | **A month-matched spread series.** Every "real cost" number in l10/e1/e2/h1/h3 — and in §2 above — applies ONE tick-measured spread from 2026-06-18..07-26 to 2025-10..2026-05 rows. | e2 B1 — *"the single largest open error bar"* | **OPEN.** No bar-level bid/ask capture exists for the pool months. §3 sharpens the transfer (the archive is 14 % bigger than declared, and the FN/FTMO ratio is symbol-specific) but cannot close it. |
| R9 | **Are the 10 undeclared tick files trustworthy?** | **raised here** | **OPEN, cheap.** §3 C3. |
| R10 | **Is the broad family a filter on the armed book?** | **never posed by any lane** | **CLOSED HERE. No** (§1). |
| R11 | **Does `poi_execution_lifecycle`'s `limit_marketable` boolean at decision time equal what the live broker path sees?** e4's only ex-ante rule depends on it. | e4 §10.4 | **OPEN.** H7 applies. |
| R12 | **Can the live engine be given a limit-order path?** `TRADE_ACTION_PENDING` is defined once and referenced only by a risk classifier. | synthesis U6; h1 §8.2 | **OPEN, owner-gated.** h1 prices the *capability* at 0.07684 R/trade of toll (31.3 % of the bill) — and bounds it: **even at zero spread the pooled book is −0.0532 R/trade**. |
| R13 | **What does a 5-minute-delayed market order actually fill at, live?** | synthesis U5 | **OPEN, unrecoverable from history.** Needs arming. |
| R14 | **`session_open_range_break` measures a range that starts before the session opens for 98.2 % of NY and 64.5 % of London rows.** | d4 §5.4 | **OPEN as a repair.** It is a clock defect in a generator, not a research question — and `session_open_range_break` is f2's *best* family by signal (+0.02423). Nobody has re-measured it repaired. |
| R15 | **The `current_fvg_fill` proximity gate is denominated in percent-of-price where it should be in R.** | d4 §3.5 | **OPEN as a repair, one predicate**, `broader_origin_generators.py:1201/:1391/:1446`. Worth 91.8 % of one family's loss. |
| R16 | **The February `current_breaker_re_entry` anomaly** — 45.94 % past-stop vs 69–82 % everywhere else. | synthesis U7 | **OPEN, ~1 h.** Unexplained generator behaviour in the estate's used-once VAL month. |
| R17 | **Does the fill-inside-60 s cancel filter apply to the ARMED sleeves' own entries?** | e6 §8.1 — *"the single cheapest next test … needs no new data"* | **OPEN.** It is the only e-lane finding with a direct route to live money and it has never been run on the live book. |
| R18 | **Multiplicity.** h1 reports 651 winning cells from 28 definitions over 3,472 cells with no correction, deliberately. h2, h5, h6, e5 likewise. | h1 §10; h2 §8.5; e5 §12.5 | **OPEN and accumulating.** Nothing found by this swarm has been declared against `CANDIDATE_FAMILY_V27` or gated at `CANDIDATE_BOOK_V1`. |
| R19 | **Sizing / correlation / portfolio construction** — f2 explicitly does not test whether the family's value lies in a third channel. | f2 §9.4; e-coherence §6 M4 | **OPEN, and now bounded**: §1 shows the family's *cross-sectional state* carries no information about another book's outcomes, which is the natural first form of that claim. |
| R20 | **Does the family's edge exist on instruments it does not trade?** 18 of the estate's own live instruments are outside the broad 24. | **raised here** (§1) | **OPEN.** |

---

## 5. THE FRAMING — "signal vs usage" is the wrong dichotomy

Asked to be adversarial about the wave's own framing. I think it is wrong in two specific ways,
and both are now measured.

**(a) It has no term for the thing the evidence actually implicates: ACCUMULATION.** "Signal"
asks *is the setup right about direction* — measured, yes, barely (f2 +0.02877 R/trade paired;
d3 +0.1490 bps, p 0.0045). "Usage" asks *does everything downstream destroy it* — measured, no;
f1 §5 shows the stack *adds* +0.0667 R/trade against a matched control, and f2 shows perfect
usage on every axis simultaneously buys +0.028. **Both answers are "fine", and the book still
loses**, which is the signature of a question that is missing a term.

The missing term is that **the toll is charged per TRADE and the signal is measured per TRADE,
while the only thing that can outgrow a fixed toll is time.** d3 measured it: a live sleeve's
capture grows **37.58×** from 2 h to 320 h; the broad family's grows **0.97× — it is flat.** A
signal that does not accumulate cannot pay a fixed toll at any contract, at any size, under any
filter. That is a property of the **contract class** — a high-frequency harvester on an 8.08 bps
stop against a 0.78 bps spread — not of the setups and not of the usage.

**The better decomposition is three axes, not two:**

| axis | question | measured |
|---|---|---|
| **existence** | is the direction call better than a coin flip? | +0.0288 R/trade, CI [−0.00, +0.057] (f2); +0.149 bps, p 0.0045 (d3) — real, ~0 |
| **accumulation** | does capture grow with holding time? | **0.97× vs a working sleeve's 37.58× (d3)** |
| **fidelity** | can the instrument see a quantity this small? | **no: the walkers' own bias is −0.0696 R (§2), 2.4× the signal** |

On that frame the answer to Borhen's question is: **it is the SIGNAL — specifically, it is a
signal that does not grow — and the usage is innocent.** And it says what would have to be true,
which is what he asked for: **a generating family whose capture increases with the horizon.**
That is a buildable object, it is testable on data already on this machine (§6), and it is not
"the broad family is finished" — it is "this contract class is finished, and here is the
property the next one must have."

**(b) The dichotomy assumes the two halves are separately measurable, and right now they are
not.** Every "usage" number in this wave — exit frontiers, trail contracts, target ladders,
delay levers — is produced by walkers whose resolution bias I measured at −0.0696 R/trade with a
constant sign. Levers smaller than that are not distinguishable from the instrument. The wave
has been arbitrating a ±0.03 R question with a ±0.07 R ruler.

**One more, smaller:** the wave keeps asking *"does the broad family pay?"* while the owner's
actual decision surface is two funded accounts. The only route from this family to that decision
is as a filter or an overlay — and §1 measures that at zero. Whatever the family's verdict, it
does not currently touch the money.

---

## 6. DATA ON THIS MACHINE THAT HAS NEVER ANSWERED AN ECONOMIC QUESTION

Checked by grepping every `.py` and `.md` under `discovery/` for each artifact's path.

| asset | size | referenced by any wave-19 lane? |
|---|---|---|
| **`deep_universe_h4d1_2014_2026`** — H4 + D1 bars, **24 instruments (exactly the broad family's own 24)**, **2014-01-02 → 2026-06-15**, 439,895 bars, 27 MB, sitting in the *same directory* as the M1 packs every lane loads | 12.5 years | **ZERO references. Never opened.** |
| `AB_LABEL_STORE_V1.jsonl.gz` — the regime spine's label store (Session AB) | — | **ZERO** |
| `AB_REGIME_DIALS_V1.json` — the measured regime dials | — | **ZERO** |
| `AA_ESTATE_TRADES.json.gz` — the 22,324-trade estate walk | — | **ZERO** (its successor `AQ_ESTATE_TRADES_V2` is used by d3 and by §1 here) |
| `BROKER_SYMBOL_SPEC_COMPARISON.json` — 18 of 19 shared symbols differ in `trade_contract_size` between the two live brokers | — | **ZERO** |
| `SLEEVE_DOSSIER_V1.json` | — | 1 file (`d3_bps.py`) |
| VPS learning packets / `shadow_logs` | — | used (h4, l10) |
| tick archive | 300.5 M | used (x4, x6, l10, here) |

**The finding is the first row, and it is structural.** The wave rationed itself to eight months
of M1 while **12.5 years of H4/D1 bars for the identical 24 instruments** sat unread in the same
folder. It cannot regenerate the broad family's candidates (they are M15/M1 structural setups),
which is exactly why nobody opened it — but that is the point: **the estate's evidence
bottleneck is not data, it is that its only broad generator is bound to a substrate 1/19th the
length of what is on disk.** Under §5's frame — where the property to hunt for is *accumulation*
— the deep universe is the natural substrate, because accumulation is a horizon property and the
armed sleeves are themselves H4/D1 objects measured on exactly this archive.

**Cheapest first use, and it needs no replay:** re-run d3's transplant ladder (which currently
runs on 8 months of M15) over 12.5 years of H4/D1 for the 24 instruments, to establish the
*base-rate* accumulation curve of an instrument with no setup at all. That is the null d3's
37.58× is missing, and without it "a working sleeve accumulates" and "holding anything
accumulates" are not separated.

---

## 7. STRUCTURAL QUESTIONS NEVER POSED (beyond the three I measured)

1. **Does the family predict VOLATILITY rather than direction, and is that monetisable without
   an options book?** The concurrent `d8` lane is measuring the price-space magnitude side; the
   monetisation question (there is no vol instrument on either account) is unposed and probably
   dead on arrival — worth stating so nobody spends a lane on it.
2. **Is the estate's own instrument fidelity ever validated against ticks?** §2 says no, and the
   answer moved 0.07 R. Every future exit-research engine should be tick-validated on one symbol
   before its frontier is believed. (Synthesis §6 row 16 already flagged the *class*: *"every
   exit-research engine in this estate is exposed to this defect class."* It was right, and the
   defect is bigger than the one it caught.)
3. **What is the base rate of "a signal that accumulates"?** — §6.
4. **Do the 18 live-book instruments outside the broad 24 behave differently?** The broad family
   has never been generated on `US500_cash`, `UK100_cash`, `JP225_cash`, `GER40_cash` under
   their live-book names, yet those are where h1/h2/h5 find every affordable cell.
5. **Is the emission RATE itself a tradeable state variable for the armed book?** §1 measures the
   nearest form (activity tertiles) at −0.107 R/trade with p 0.930 — suggestive, not significant,
   and the honest next form is a *daily* rather than per-trade cut, with a pre-declared rule.

---

## 8. LIMITS

1. **§1's sleeve trades are a research walk, not live P&L**, and the five armed sleeves were
   selected from 32 — every one of them REJECTS at the ratified gate (d3 §7). The +0.15555 is a
   control, not a claim about the live book, and no live-forward P&L was read.
2. **§2's spreads are transferred** from 2026-06-18..07-26 onto 2025-10..2026-05 emissions —
   the same transfer x6 and h1 make, declared as such (R8). The *sign* of the bound is not at
   risk (spreads would have to have been zero), the magnitude is.
3. **§2's R bound ignores exit ordering** and so is a bound, not a book. The exact number needs a
   re-walk with shifted thresholds, which is ~1 h on the existing tape machinery and is the
   single cheapest thing anyone can do with this receipt.
4. **§2 settles the quote side of `vps-bars-20260727` M15.** The M1 packs the lanes walk
   (`bridge_ftmo_m1_*`) are a separate, re-stamped export with no `spread` column and no Jun–Jul
   coverage, so the finding transfers to them **by broker provenance, not by direct
   measurement.** Closing that gap needs one month of M1 with an overlapping tick window — or,
   cheaper, a single `copy_rates`/`copy_ticks` parity probe on the live terminal.
5. **§3's boundary premium is measured on a 37-day window** and is a microstructure property
   claim, not a period claim.
6. **The sealed three (jun/aug/sep 2025) were not opened, generated or referenced.**
7. A concurrent `d8` lane holds `d8_*.py` and `D8_*.json`; this lane wrote only `d8x_*` /
   `D8X_*` and read that lane's `D8_EMIT_*.npz` without modification.

---

## 9. FILES

| artifact | what |
|---|---|
| `d8x_cross.py` → `D8X_CROSS_V1.json` | broad family as a filter on 4,352 live-sleeve trades |
| `d8x_ticks.py` → `D8X_TICK_TOLL_V1.json` | 300,538,915 ticks: spread by symbol, UTC hour, M15 offset, both brokers |
| `d8x_quoteside.py` → `D8X_QUOTESIDE_V1.json` | bid-vs-mid settled on 76,734 M15 bars × 29 symbols |
| `d8x_geom.py` → `D8X_GEOM_V1.json` | what the BID archive costs every walk: `s/d`, touch-rate deltas, R bound |
| `d8x_RESULT.json` | machine index of every headline number here |
