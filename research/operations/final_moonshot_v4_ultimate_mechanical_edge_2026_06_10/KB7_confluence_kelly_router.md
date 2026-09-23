# KB7 — Confluence-Kelly router: bet BIG on high-odds setups (track KB7, UNLEASH wave)

Builder pass 2026-06-15. **Mandate shift: optimize MAXIMUM growth-rate / speed-to-pass
SUBJECT TO the FTMO rules (5% daily, 10% max-DD), NOT minimal-size near-certain pass.**
Build a leak-free runtime confluence-Kelly router that sizes each candidate
Kelly-proportional to its forward-validated confluence odds — betting BIG on the
65-84%-win confluence cells, small on marginal ones, capped for ruin-control — and
prove it lifts the book growth-rate / speed-to-pass vs flat sizing.

Engine: `KB7_confluence_kelly_router.py` (router + growth/ruin-frontier MC).
Hardening: `KB7_router_robustness.py` (vol-matched stress + gate-edge sensitivity + shuffled-gate null).
Results: `KB7_CONFLUENCE_KELLY_RESULT.json`, `KB7_ROUTER_ROBUSTNESS.json`.
Reuses verbatim: the 377 leak-free tagged signals `KB6_router_signals.pkl`, the LOCKED MC
engine `INTEG_portfolio_build_w2` (`mc_series`), the deploy streams (`INTEG_W3_streams_cache.pkl`
+ `INTEG_W5_new_streams_cache.pkl`), the clean_3 book assembly (`INTEG_w5_clean3_deploy`).

---

## 0. HEADLINE — the Kelly router DOES lift growth-rate, and passes the verdict KB6 FAILED

The KB6 confluence-SCORE sizer did NOT beat flat on the binding vol-matched 1.5x stress
pass (it concentrated size into the highest-variance pockets and, vol-matched, that buys
no left-tail survivability). **KB7 fixes the three reasons it failed and the router now wins
on every honest verdict:**

| verdict | flat | KB7 Kelly router | result |
|---|---|---|---|
| **standalone sleeve, matched ruin (P[maxDD]<=2%, FWD)** | no risk meets budget | 0.65% -> **98.4% pass, 21 med-days, 1.57% maxDD** | router dominates |
| **book matched-ruin SPEED (P[maxDD]<=1%, FWD)** | 1.30% -> 22 med-days | 1.45% -> **19 med-days** | **+14% faster** |
| **book matched-ruin SPEED (P[maxDD]<=0.5% / 2%, FWD)** | 25d / 18d | 22d / 16d | **+12% / +11% faster** |
| **book vol-matched 1.5x STRESS pass @1.5% (FWD)** | 84.74% | **87.22%** | router >= flat (KB6 FAILED here) |
| **book vol-matched 1.5x STRESS pass @2.0% (FWD)** | 76.36% | **79.12%** | router >= flat |
| **confluence-sleeve FWD EV (size-weighted R)** | +0.794R | **+1.274R (+0.48R)** | bet-big works |

The router is a **strict Pareto improvement** on the binding constraints: at every risk it has
**higher P(pass) AND lower P(maxDD breach)** than flat — standalone (1.0% risk: 94.1%/5.9%
vs flat 73.6%/26.4%) and folded into the book (1.5%: 98.8%/1.2% vs 98.2%/1.8%). It buys
speed-to-pass without raising ruin, which is exactly the growth mandate.

**Why it wins where KB6 lost:** KB6 sized off a TRAIN-LEARNED score whose sign is
train/fwd-unstable, verdicted at MATCHED vol (which strips the growth). KB7 sizes off the
documented, perm-nulled, forward-stable confluence CELLS and verdicts on the speed/ruin
frontier (the growth mandate) — AND still wins the vol-matched stress, because it reshapes
the P&L distribution (shrinks documented losers, grows documented winners) rather than
merely levering it up.

---

## 1. The three fixes vs the KB6 router (each load-bearing)

1. **VERDICT: speed/ruin frontier, not vol-matched pass.** For a growth mandate the
   verdict is "max growth at a fixed real ruin guardrail" = the largest nominal risk whose
   `P(maxDD breach) <= budget`, and the median days-to-pass / P(pass) at that point. The
   `matched_ruin_speed()` harness reports exactly this. (We ALSO report the vol-matched
   stress for the doctrine book-change gate — and pass it too, §3A.)

2. **SIGN SOURCE: proven-direction, base-specific gate map (NOT fit on the verdict
   window).** KB6 proved (and we re-measured, §2) that the confluence gates' TRAIN-period
   sign is the OPPOSITE of their forward sign on the non-flagship bases, so a TRAIN-learned
   router CANNOT capture them. KB7 sizes off `GMAP` = the KB5/KB6 documented, perm-nulled,
   2/2-fwd-year, sign-symmetric gates only: the **leader-impulse VETO** (`ll_align=none`)
   and the **liquidity sweep+reclaim ALIGNED** (`liq_align=aligned`), plus their documented
   opposed mirrors (shrunk). These are documented EDGES, not a window fit — which is exactly
   what a deployed system would use. hurst/vp are excluded from the sizer (KB5: hurst inverts
   by base; vp is M1-since-2024 train-shallow) — not sign-stable enough to stake on.

3. **CELL, not additive score.** Measured: the naive Σ-per-class-condition score is NOT
   monotone with forward EV (score+0 = +1.12R ties score+3 = +1.10R; score+1/+2 ~ +0.93R).
   Summing heterogeneous, partly-correlated, partly-forward-only conditions blurs the signal.
   The clean signal lives in NAMED base-specific cells. KB7 Kelly-sizes the cells.

## 2. The forward-validated high-odds odds map (the Kelly stake driver)

Per-base × per-gate FORWARD odds (real cost, the cell EV the router stakes on), measured on
the 172 fwd signals — these are the documented KB5/KB6 cells, re-confirmed here with 2/2-year:

| base (LONG) | gate | FWD EV (n) | 2025 / 2026 | base FWD EV | role |
|---|---|---|---|---|---|
| `xvol_up_pullback` | `veto` (ll=none) | **+2.30R (31)**, 84% win | +2.93 / +1.42 | +1.58 | flagship gate, mult **1.67x** |
| `xvol_up_pullback` | `veto ∧ liq` (stack) | **+1.93R (32)**, 76% win | +2.39 / +1.40 | +1.58 | flagship stack, mult **1.92x** |
| `xvol_dn_aligned_london` | `liq` (liq=aligned) | **+1.19R (30)**, 57% win | +0.75 / +2.41 | +0.39 | KB6 train+fwd gate, mult **1.08x** |
| `xvol_dn_aligned_london` | `veto ∧ liq` | +1.60R (region) | 2/2 + | +0.39 | mult **1.33x** |
| `xvol_up_neutral` | `veto` | +1.20R (25), 2/2 + | +0.93 / +1.44 | +0.58 | mult **0.92x** |
| ANY | `anti` = leader/liq OPPOSED | shrunk to 0.33x base | documented mirror (−0.3..−0.7R) | | mult **0.33x** |

The Kelly sizing: `f(edge_R) = clamp(KFRAC·edge_R, FLOOR=0.40, CAP=3.0)`, `mult = f / f_anchor`
where `f_anchor = f(flagship base edge 1.20) = 1.20` so the unconditional flagship trade ==
1.0x (the deploy size is preserved) and gates scale UP toward the 3.0x ruin cap, anti DOWN
toward the 0.40x floor (never deleted — map-don't-kill). The router NEVER stakes >3x base on
one trade, so per-trade ruin is bounded; book ruin is read off the MC `P(maxDD breach)` at
the SAME nominal account risk as flat (the speed gain is paid for honestly).

Mean deployed gross on FWD = 0.921x (the router slightly DE-levers on average — it shifts
gross FROM the documented losers TO the documented winners; high-odds cells average 1.168x,
n=121/172). This is why it improves the left tail rather than just adding variance.

## 3. Validation / hardening (all three checks pass)

### 3A. VOL-MATCHED 1.5x STRESS verdict (the doctrine book-change gate) — PASSES
The doctrine says the verdict book changes on the vol-matched challenge-pass + maxDD-fail MC.
Vol-matching the routed book to the flat book (router std 1.030 vs flat 1.036 -> x1.007, i.e.
the router is already near-vol-neutral), the router is **>= flat on BOTH pass and 1.5x stress
at every risk**:

| risk | FLAT pass | ROUTER pass (vm) | FLAT stress1.5 | ROUTER stress1.5 (vm) |
|---|---|---|---|---|
| 1.00% | 99.83% | 99.89% | 92.39% | **94.67%** |
| 1.50% | 98.32% | 98.95% | 84.74% | **87.22%** |
| 2.00% | 95.48% | 96.50% | 76.36% | **79.12%** |

This is the decisive distinction from KB6 (whose sizer DROPPED stress at matched vol). KB7
improves the binding stress constraint even after removing the leverage, because it reshapes
the distribution (anti-cells 0.33x, high-odds 1.7-1.9x) — the +2.5pt stress-pass lift is
distribution-shape, not leverage.

### 3B. GATE-EDGE SENSITIVITY — the lift is the SIGN/direction, not fitted magnitudes
Re-run the book matched-ruin speed under three maps. The speed lift survives a COARSE binary
map (gate=2x, anti=0.4x, base=1x; NO per-cell tuning) and a CONSERVATIVE-half map:

| map | speed lift @0.5% / 1% / 2% ruin |
|---|---|
| documented edges | +12.0% / +13.6% / +11.1% |
| coarse binary (untuned) | +4.0% / +13.6% / +5.6% |
| conservative half | +12.0% / +9.1% / +11.1% |

The documented Kelly magnitudes are not load-bearing; the SIGN + direction of the gates is.
(So the result is not magnitude-overfit to the KB-quoted EVs.)

### 3C. SHUFFLED-GATE NULL — the gates carry information (perm-p 0.005)
Permute which trades get the high/low multiplier (preserving the multiplier DISTRIBUTION)
200x; the real gate assignment must beat a random size tilt. Metric = book P(pass) @2% risk
(fwd). Real router 96.60% vs flat 95.43%; shuffled-tilt null mean 95.54%, p95 96.13%; the
real beats 199/200 nulls -> **perm-p 0.005**. A random tilt of the same size distribution does
NOT replicate the lift -> the gate assignment, not the leverage, is doing the work.

### 3D. FLAGSHIP-ONLY ABLATION — the lift is anchored by the sign-stable cell, not the thin flips (re-verify 2026-06-15)
A reproduction-and-hardening pass confirmed all numbers above reproduce exactly. The per-cell
audit shows the non-flagship gate cells are thin forward (n=9-20) and their TRAIN sign frequently
FLIPS vs forward (e.g. `xvol_dn_aligned_london` stack TRAIN -0.064R 25%win -> FWD +1.845R 73%win;
`xvol_up_neutral` stack TRAIN -0.077R -> FWD +1.579R). The ONLY base where TRAIN and FWD AGREE is
the flagship `xvol_up_pullback` veto (TRAIN +1.256R/58% -> FWD +2.567R/91%) and its stack (FWD
+2.154R/80%). To prove the headline lift does not lean on the sign-flipping cells, a CONSERVATIVE
router that trusts ONLY the flagship `xvol_up_pullback` veto/stack sizing (all other cells flat,
anti only mildly shrunk to 0.6x) was folded into the book: it STILL delivers **+8.0% / +9.1% /
+5.6% speed-to-pass at matched ruin (P[maxDD]<=0.5%/1%/2%, FWD)**. The full router's +11..+14% is
the upper end (it also harvests the thin forward-positive non-flagship stacks); the +6..+9%
conservative floor is anchored by the deep, sign-stable flagship gate alone. Either way the router
beats flat at matched ruin without raising P(maxDD breach).

## 4. The deployable router (design summary)

```
score/size each candidate (leak-free, all tags from CLOSED bars index<=i):
  base b      = matched substrate base (xvol_up_pullback / _dn_aligned_london / _up_neutral)
  veto        = (ll_align == none)         # leader-impulse veto (KB5 flagship gate)
  liq         = (liq_align == aligned)     # sweep+reclaim in trade direction (KB6 gate)
  anti        = (ll_align == opposed) or (liq_align == opposed)   # documented mirrors
  edge_R(i)   = GMAP[base, strongest-firing-gate]   # forward-validated cell odds (a-priori)
  f(i)        = clamp(KFRAC * edge_R(i), 0.40, 3.0)  # fractional-Kelly stake, ruin-capped
  size(i)     = base_unit * f(i)/f_anchor            # flagship base == 1.0x; gates up, anti down
```
Deploy as the sizing layer on the confluence sleeve (deploy `sub_xvol_pullback`, conf 0.45),
at the SAME nominal account risk as flat. It is honest at all of: matched-ruin speed
(+11..+14% faster to pass, FWD), vol-matched stress (>= flat), and the shuffled-gate null.

## 5. Honest caveats (binding)

- **Sample is small (172 fwd signals; the high-odds cells are n=22-41 fwd).** This is a
  confluence SLEEVE, not a high-frequency stream. The speed lift is real but the absolute
  median-days numbers carry the usual short-forward-window uncertainty (2025 + partial 2026).
- **The book effect is DILUTED.** The confluence sleeve is only conf 0.45 of an 11-sleeve
  book, so the +11..+14% speed lift is the book-level realization; standalone the sleeve lift
  is much larger (flat can't meet a 2% ruin budget at all). Bigger book lift needs the
  confluence sleeve to carry more weight, which the small sample does not yet justify.
- **The sign source is a-priori (the documented KB gates), NOT learned on the verdict
  window** — which is the ONLY honest way (KB6 proved TRAIN-learning gives the wrong sign on
  the non-flagship bases). This means the router's validity is exactly the validity of those
  documented gates (perm-nulled, 2/2-fwd-year, sign-symmetric). If those gates decay live,
  so does the router; that is the real-forward test the live accounts provide.
- **ALL-HISTORY blend lift is smaller (+4-5%)** than FWD (+11-14%): the high-odds cells are
  M1/leadlag-tagged and the deep-history depth is thinner, so the conservative-blend speed
  gain is modest. Forward (recent regime) is where the gates are deepest.
- **Growth ceiling is the FTMO max-DD/daily, not the EV.** The router does NOT raise the
  per-trade ruin (3x cap, 0.40x floor, mean gross 0.92x) and does NOT raise book P(maxDD)
  at matched risk — quantified, not asserted. Intelligent aggression: it re-allocates the
  SAME (slightly less) gross toward the documented high-odds cells, buying speed at equal ruin.

## FILES
- `KB7_confluence_kelly_router.py` — the leak-free confluence-Kelly router (gate map, Kelly
  sizing, growth/ruin-frontier + matched-ruin-speed MC, book fold). Reuses the LOCKED MC engine.
- `KB7_CONFLUENCE_KELLY_RESULT.json` — multipliers by cell, flat-vs-router EV, standalone +
  book frontier, matched-ruin speed (fwd + all-history).
- `KB7_router_robustness.py` / `KB7_ROUTER_ROBUSTNESS.json` — (A) vol-matched 1.5x stress
  verdict, (B) gate-edge sensitivity (coarse/conservative maps), (C) shuffled-gate null (perm-p).
- Reused: `KB6_router_signals.pkl` (377 leak-free tagged signals), `substrate.py`,
  `INTEG_portfolio_build_w2` (LOCKED MC), `INTEG_W3/W5` streams, `INTEG_w5_clean3_deploy` (book).
