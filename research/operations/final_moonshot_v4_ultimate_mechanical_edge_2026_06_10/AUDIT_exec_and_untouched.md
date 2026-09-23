# ADVERSARIAL AUDIT — 2x execution stress + truly-untouched slice

Auditor posture: skeptical-but-fair calibration of trust on real money. Separate **STRUCTURAL
pass-rate** (no-time-limit challenge math) from **EDGE MAGNITUDE** (return/speed). Quantified,
not hand-waved. Engine: LOCKED `INTEG_portfolio_build_w2.mc_series` (8%/5%/10%, BLOCK=5, N=20000).
Book reproduced **byte-identical** to `INTEG_W7_FINAL_RESULT.json` before any stress (parity proven).

Scripts: `AUDIT_exec_stress.py`, `AUDIT_recent_slice.py`.
Results: `AUDIT_exec_stress_RESULT.json`, `AUDIT_recent_slice_RESULT.json`.

---

## BOTTOM LINE

- **STRUCTURAL pass-rate is real and robust.** Even under doubled execution erosion + a crypto
  exec haircut + flat slippage, challenge P(pass) at 1.25%/1.50% stays **96.6%/94.1%** (heavy)
  vs the shipped **99.4%/98.6%**. The "you will pass the challenge eventually" claim is **not
  materially inflated** (it loses ~3-5 pp, not 30 pp).
- **EDGE MAGNITUDE (monthly% and speed) is the inflated part, and the inflation compounds from
  three sources**: (1) execution optimism, (2) profit hyper-concentration in a few days,
  (3) the absence of any clean out-of-sample slice. Net realistic monthly is roughly **70-80% of
  headline** under plausible execution, and the **forward monthly% (5-14%) is the least trustworthy
  number in the book**.

---

## (a) 2x EXECUTION STRESS

### What the shipped book actually applies for execution
The "tick" / "final" variants apply a per-symbol erosion measured from a tick ledger. Coverage
(verified from `KB7_TICK_*_LEDGER.jsonl`):

| symbol | covered/total trades | mean erosion applied |
|---|---|---|
| HEATOIL_c | 21/21 | -1.506R -> **dropped** |
| NATGAS_cash | 12/12 | -0.265R -> **dropped** |
| UKOIL_cash | 24/36 | -0.037R |
| USOIL_cash | 22/36 | **+0.037R (favorable)** |
| XAGUSD | 14/31 | -0.005R |
| XAUUSD | 14/66 | **+0.019R (favorable)** |
| USDJPY | 298/298 | **+0.018R (favorable)** |

**Two structural optimisms in the shipped execution model:**
1. **Crypto (~40% of book EV) gets ZERO execution erosion** — `KB7_TICK_CRYPTO_LEDGER.jsonl` does
   not exist; the script silently skips it. The single largest sleeve has no real-fill haircut.
2. The metals/JPY erosions that *are* applied are **net favorable** (XAU/XAG/JPY measured fills
   came in slightly *better* than modeled, on thin 14-of-66 coverage). So the "tick-true" variant
   adds essentially no execution cost to the dominant sleeves; it only removes two illiquid energy
   legs. "Tick-true fills" overstates how much real execution friction was charged.

### Stress design (no-lookahead, per-trade R haircuts before mean-pool)
- **2x measured erosion** on metals/JPY/energy (double the per-symbol haircut).
- **Crypto haircut** (the missing cost): moderate 0.08R, heavy 0.15R per crypto trade.
- **Flat slippage buffer** on all sleeves: moderate 0.03R, heavy 0.05R.
- Re-vol-matched to the same `sd_book` (apples-to-apples vs the vol-matched headline). Direct
  (non-rematched) framing also reported; results nearly identical.

### Degraded vs shipped (vol-matched, all-history)

| metric | SHIPPED | 2x exec moderate | 2x exec heavy |
|---|---|---|---|
| daily mean drop | — | **-12.7%** (fwd -10.9%) | **-22.4%** (fwd -19.3%) |
| **1.25% P(pass)** | 99.36% | 98.16% | 96.59% |
| 1.25% monthly% | 2.16% | 1.91% | 1.72% |
| 1.25% med days | 79 | 84 | 91 |
| 1.25% stress15 P(pass) | 79.1% | 69.1% | 59.8% |
| **1.50% P(pass)** | 98.59% | 96.44% | 94.06% |
| 1.50% monthly% | 2.59% | 2.30% | 2.07% |
| 1.50% med days | 66 | 70 | 72 |
| 1.50% stress15 P(pass) | 73.5% | 63.8% | 57.0% |
| 1.50% FWD P(pass) | 96.25% | 90.30% | 87.73% |
| 1.50% FWD monthly% | 10.57% | 9.42% | 8.53% |

**Daily-breach safety holds** under exec stress alone (0% at the dial; worst day -3.2% to -4.0%
vs the -5% limit). It only crosses -5% when 2x-exec is *stacked on top of* the 1.5x-loss stress
(worst day -5.7% to -6.0%, breach 0.06%). The "0% daily breach" headline is **fair, not inflated.**

### Verdict (a)
- **Structural pass-rate inflation: small.** ~1-5 pp lost at the dial under heavy stress. The
  challenge will still pass with high probability. This number is trustworthy.
- **Edge-magnitude inflation: real.** Monthly% and speed are overstated by roughly **10-20%**
  purely from execution optimism, with most of the gap coming from the un-costed crypto sleeve.
  The **combined exec+loss-tail (stress15)** is where it bites hardest: 1.50% drops from a
  shipped 73.5% to **57-64%** — i.e. in a bad-fill + fat-loss regime, roughly **1-in-3 challenge
  attempts fail the maxDD wall**, vs the ~1-in-4 the headline stress implies.

---

## (b) TRULY-UNTOUCHED SLICE — there is none

**Finding: NO clean out-of-sample slice exists.** The entire **2025-26 forward window (through
2026-06-12) was the FORWARD HOLDOUT that served as the verdict gate** for sleeve selection, conf
weights, the HEATOIL/NATGAS drop, and the aggression dial. Evidence:
- Every selection script splits `d.year >= 2025` as "forward" and reports forward EV as the
  decision criterion (`INTEG_portfolio_build_w2.py`, `KB7_growth_kelly_sizing.py`, W7 book).
- Wave MDs explicitly score the most recent data: `KB6_deepen_forward.md` cites "2026 +0.483",
  "FWD25 / FWD26" per-year tables, and converts/falsifies sleeves *on* those forward years.
- Data caches extend to **2026-06-12**; the final book was committed **2026-06-15** — the last
  days of available data were inside the selection set.

So the forward numbers (P(pass) ~96-98%, monthly 5-14%) are **in-sample to the selection process**.
They are a forward *holdout vs training*, but they are **not OOS vs model selection** — the sleeves
and dial were chosen to look good on exactly this window.

### Best-available "freshest regime" read (explicitly partly in-sample)
Deploy book on the most recent slices (FINAL book, vol-matched eff):

| slice | dates | active days | mean R/day | win-day% | worst day | monthly@1.50% |
|---|---|---|---|---|---|---|
| last 4w | 05-15..06-12 | 21 | +0.50 | 52% | -0.52R | +11.8% |
| last 8w | 04-17..06-12 | 41 | +0.30 | 46% | -1.72R | +7.1% |
| last 12w | 03-20..06-12 | 63 | +0.29 | 52% | -1.72R | +6.9% |

Recent calendar months expose the volatility the headline hides:

| month | mean R/day | win-day% | monthly@1.50% |
|---|---|---|---|
| 2026-02 | +0.40 | 65% | +9.5% |
| 2026-03 | +0.75 | 83% | +17.8% |
| **2026-04** | **-0.15** | **44%** | **-3.6% (losing month)** |
| 2026-05 | +0.20 | 38% | +4.7% |
| 2026-06 (10d) | +1.01 | 70% | +24.0% |

Caveat: thin-slice block-bootstrap MC returns ~100% pass (it resamples the same hot days); that
is **not** a probability claim and is flagged as such in the script.

### Verdict (b)
- No clean OOS exists; the freshest reads cannot be treated as independent confirmation.
- The freshest months are **highly volatile and include a losing month (April 2026)**. Win-day%
  in the last 4-12 weeks is only **44-52%** — the book is positive via a few large days, not via
  consistency.

---

## CROSS-CUTTING: profit hyper-concentration (the deepest magnitude risk)

The single biggest reason to discount the **magnitude** headline:

- **Forward (382 days):** top 10 days = **46%** of all forward profit; top 20 days = **75%**;
  **43% of active days are negative.**
- **All-history (1679 days):** top 20 days = **56%** of total; **top 50 days = 96%** of total
  profit. ~50 outlier days out of 1679 made essentially the entire book.

The MC block-bootstrap resamples these hot days into every path, so the projected monthly% and
speed inherit their full magnitude. If even a handful of those outlier days underperform live
(slippage on the large moves, gaps, non-repeating setups — exactly what real execution erodes),
the realized monthly magnitude can be a **fraction** of projected, while the binary pass/fail is
far less sensitive (you still clear +8% eventually from the surviving winners).

---

## HOW MUCH IS THE HEADLINE INFLATED (honest quantification)

| claim | headline | realistic | inflation |
|---|---|---|---|
| **STRUCTURAL** P(pass) @1.25-1.50% (all-hist VM) | 98.6-99.4% | 94-98% under 2x exec | **~1-5 pp — low** |
| Daily-breach safety @dial | 0% | 0% (exec-only) | **none — fair** |
| **MAGNITUDE** monthly% (all-hist VM) | 2.16-2.59% | ~1.7-2.3% (2x exec) | **~10-20%** |
| **MAGNITUDE** FORWARD monthly% | 5.3-14.1% | partly in-sample + concentration-driven | **most-inflated number; discount heavily** |
| Stress15 P(pass) @1.50% | 73.5% | **57-64%** under 2x exec | **~10-16 pp — the real tail risk** |
| Speed (med days @1.50%) | 66 | 70-91 | **~6-40% slower** |

**One-line trust calibration:** believe the "we will pass" structural claim (robust to 2x
execution); **halve your confidence in the forward monthly% / speed**; and plan for the realistic
maxDD-stress failure rate of **~1-in-3, not 1-in-4**, with the dominant unmodeled risk being the
un-costed crypto sleeve and the fact that ~50 days carry the entire edge.
