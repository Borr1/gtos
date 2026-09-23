# KB3 — M1/tick execution-realism gate (the live go/no-go)

Track: EXEC_REALISM (builder). Date 2026-06-15. Goal: prove the PORTFOLIO_BUILD_W2 book survives
REAL fills before live. Re-simulate every deployed sleeve at **M1 intrabar resolution** and quantify
the R erosion vs the H4/H1/M15-bar fill model. This is the realism gate; it does not pick a strategy,
it certifies that the picked book's modeled EV is achievable when fills are priced honestly.

## Verdict (headline)

**The book PASSES the realism gate.** Net of realistic M1 fills the combined conf-weighted book
erodes only **~5.6%** (103.0 -> 97.2 conf-wtd unit-R/yr). The three train-validated EV-carriers
(95% of book EV) lose **<=0.03R/trade**; every deployed sleeve stays net-positive (except the
already-negative `metals_ob_micro` tail). **The H1->M15 cascade better-fill is M1-achievable**
(only 1 of 58 cascade limits unreachable). No sleeve must be cut for fill reasons.

| sleeve | conf | modeled FWD EV | **M1-net EV** | erosion/trade | source |
|---|---|---|---|---|---|
| metals_core (EXEC_COMBO) | 1.00 | +1.164 | **+1.158** | **-0.006** | measured n=47 clean |
| crypto (target4+cascade) | 0.85 | +0.950 | **+0.920** | **-0.030** | measured n=58 clean |
| energy_agri (STATE_D+cascade) | 0.80 | +0.691 | **+0.695** | **+0.004** | measured n=61 clean |
| metals_softband | 0.50 | +0.140 | +0.130 | -0.010 (proxy) | metals-class proxy |
| metals_ob_micro | 0.30 | -0.171 | -0.181 | -0.010 (proxy) | metals-class proxy |
| fx_jpy_ny | 0.15 | +0.154 | +0.104 | -0.050 | measured n=530 (raw) |
| fx_jpy_london | 0.15 | +0.168 | +0.120 | -0.048 | measured n=530 |
| idxrev | 0.15 | +0.025 | +0.012 | -0.013 | measured n=2672 |

**Book conf-wtd unit-R/yr: modeled 103.0 -> M1-net 97.2 (-5.6%).** No EV-carrier flips; no breadth
sleeve flips negative once measured (idxrev's wide-stop geometry is low fill-sensitivity, not
JPY-like). The conservative half-spread-on-stops assumption already loads the breadth sleeves; even
so they survive.

## Method (what was modeled, and the doctrine held)

- **Entry realism.** The whole book's signal convention is *enter at the signal-bar CLOSE*
  (`geometry_lib.simulate` / `sim_exit` use `bars[i].c`). A bar close is **not fillable live**. The
  M1 model replaces it with: market entries fill at the **next M1 OPEN** at/after the signal-close
  instant; cascade LIMIT entries fill **at the limit price** (`sc -/+ 1*ATR`) the moment M1 touches
  it (live limit-order semantics). No extra spread is added on entry — see double-count note below.
- **Exit realism.** Scale legs / vol-banded profit-lock / runner fixed targets are **limit fills at
  the level** (no positive slippage). Structural and lock STOPS take **gap-fill** (the M1 open if
  price gapped through the stop) **plus an exit-side half-spread buffer** (`0.5 * cost_R(sym) * sd`).
- **Same-bar ambiguity.** Resolved by the ACTUAL M1 sequence, with per-M1-bar pessimism preserved
  (adverse checked before favorable within each bar) — the same convention as `geometry_lib`.
- **No spread double-count (the decisive correction).** The book's R is ALREADY net of round-trip
  cost via `w1.cost_for` (e.g. jpy_fx 0.1148R ~ 0.0113 price on a GBPJPY 1R stop). An early version
  re-added a full M1-range spread on BOTH entry and stop, which **double-counted ~2.6x the real
  spread** and falsely collapsed fx_jpy_london to -0.18R. The honest incremental realism charged on
  top of the already-cost-netted R is only: (1) entry open-vs-close, (2) M1 same-bar resolution,
  (3) exit-side half-spread on stops. JPY-London then erodes only -0.048R (stays +0.12R).
- **Wall-clock horizon alignment.** The M1 exit horizon ends at the SAME wall-clock instant as the
  modeled H4 horizon (`Th4[i+80]+4h`), removing the bar-count-vs-calendar mismatch from the
  measurement.
- **M1 data-gap quarantine.** Metals/index M1 starts ~01:05 each day (broker daily-rollover); the
  H4 00:00 fill bar then spans an M1 gap. 8/55 metals entries hit this; their M1 path is unreliable
  (one XAUAUD case spuriously flipped a -1R stop to +3R because M1 missed the adverse excursion).
  These are flagged `gapped` and EXCLUDED from the erosion verdict (reported separately).
- Doctrine held: per-YEAR + per-SYMBOL (no averages-as-verdict); winsorize net R [-1.3,+5]; real
  `w1.cost_for`; no lookahead added (this is a fill audit of already-decided entries — M1 is never
  used before the signal-bar close to change WHETHER we trade).

## The H1->M15 cascade better-fill IS M1-achievable (central go/no-go)

The cascade enters after an H4 signal closes by placing a LIMIT 1*ATR_LTF better than the signal
close and waiting W_H1=12 H1 bars (=12h) then W_M15=48 M15 bars (=12h) before falling back to H4.
The realism question: does that limit actually trade at M1, within that window?

- **Crypto:** 34 modeled cascade-limit fills (30 H1 + 4 M15) among 58 clean trades; **1** unreachable
  on M1 within the 12h window (fell back to H4). 33/34 = **97% of cascade limits filled at M1**.
- **Energy:** 24 cascade-limit fills (17 H1 + 7 M15) among 61 clean; **0** unreachable.
- Limit fills are slightly WORSE than the modeled LTF-bar-close for crypto (limit fill -0.023R vs
  the LTF close that had already recovered) and slightly BETTER for energy (+0.074R) — both small.
  The cascade is NOT a phantom edge; the better-fill prices are genuinely reachable.

## Per-year erosion (clean M1, EV-carriers) — non-stationary, no averages-as-verdict

| sleeve | 2024 | 2025 | 2026 |
|---|---|---|---|
| metals_core | -0.002 (n6) | +0.001 (n19) | -0.008 (n22) |
| crypto | -0.002 (n2) | +0.025 (n40) | -0.041 (n16) |
| energy_agri | -0.007 (n3) | -0.004 (n23) | +0.045 (n35) |

Erosion is within +/-0.05R every year for every carrier. The only mildly negative cell is crypto
2026 (-0.041R) on 16 trades; metals/energy are flat-to-positive forward.

## Fill-sensitive sleeves (the brief's explicit flag)

- **JPY (low-win, tight 1*ATR stop) is the most fill-sensitive class, as expected**, eroding
  ~-0.05R/trade — but it stays net-positive at conf-0.15 breadth (London +0.120R, NY +0.104R).
  The single-trade worst erosion (-3.56R, winsor floor) confirms tight-stop low-win sleeves carry a
  fill tail; sized as breadth this is contained.
  - CAVEAT: the NY-JPY probe replicates the RAW NY mirror (hour>=14 ungated) which the book itself
    falsified (-0.12R); the book's deployed NY-JPY is GATED (hour>=15 + imp>=1*ATR + trend20, +0.154R).
    Gating changes WHICH trades enter, not the per-fill slip mechanics, so the **-0.05R erosion
    transfers** to the gated variant; net gated NY-JPY ~ +0.104R holds.
- **idxrev is NOT fill-sensitive** despite being high-frequency low-win: its LOCKED rule is WIDE stop
  (1.5*ATR) + TIGHT target (0.75R, a limit), so the stop buffer is a small fraction of R and the
  target takes no slippage. Measured -0.013R across 2,672 trades / 6 indices. The earlier JPY-class
  proxy (-0.05R) was wrong and was REPLACED by this direct measurement (it had falsely flipped
  idxrev negative; measured, idxrev stays +0.012R).
- **Metals/crypto/energy are fill-robust**: metals EXEC_COMBO's 2.0R scale leg + vol-band lock + deep
  runner target are all limit fills; only the structural stop slips, and the metals stop is wide.

## Honest caveats / open items

1. **M1 coverage window.** M1 is 2024-01+ for base symbols (XAUUSD, XAGUSD, USOIL, BTC, ETH, JPY,
   indices) and 2025-06+ for ext symbols (XAU/XAG-EUR/AUD, DASH, NATGAS, HEATOIL, CORN). So
   pre-2024 train trades have NO M1 (uncovered: metals 76/131, crypto 9/68, energy 33/105). The
   erosion is measured on the M1-covered (mostly forward) subset and assumed to transfer to the
   uncovered train trades (same symbols, same geometry). This is the same forward-only-LTF confound
   the cascade KBs already carry.
2. **Slip model is a conservative proxy, not tick truth.** No real bid/ask tick stream was used;
   the stop buffer = half the per-symbol round-trip cost. Real spread widens around news/rollover;
   a tick-level pass on the highest-frequency sleeves (idxrev 1013/yr) would tighten the tail
   estimate. The MT5 bridge (siliconmetatrader5 @ localhost:8001) can export ticks on demand if a
   tick-exact pass is wanted next.
3. **metals_softband / metals_ob_micro** use a metals-class proxy (-0.010R), not a direct measure
   (their entries were not rebuilt here). They are metals FVG geometry like the core, so the proxy
   is well-founded, but a direct pass would close the last proxy.

## NEXT
1. Adopt the M1-net EVs into the live book sizing (negligible change; metals/crypto/energy intact).
2. Optional tick-exact pass on idxrev + JPY via the MT5 bridge to harden the breadth-sleeve tail.
3. Direct M1 measure of metals_softband/ob_micro to remove the last two proxies.
4. Re-run the FTMO challenge-pass MC on the M1-NET sleeve EVs (5.6% haircut) to confirm P(both pass)
   stays ~99%+ at 0.75%/0.75% — expected trivially since the haircut is small and daily-breach
   (mathematically 0% at the worst-day -2.98% vs -5%) is fill-insensitive (driven by win-day caps).

## FILES
- `EXEC_REALISM_m1_lib.py` — M1 loader (base+ext month dirs, dedup/sort) + leak-free intrabar exit
  (limit-fill TPs, gap+buffer stops, same-bar pessimism, wall-clock horizon).
- `EXEC_REALISM_reconcile.py` — driver: metals_core (EXEC_COMBO), crypto (target4+cascade),
  energy (STATE_D+cascade). Writes `EXEC_REALISM_RESULT.json` + `EXEC_REALISM_TRADE_LEDGER.jsonl`.
- `EXEC_REALISM_jpy_probe.py` — JPY London/NY fill-sensitivity probe -> `EXEC_REALISM_JPY_RESULT.json`.
- `EXEC_REALISM_idxrev_probe.py` — idxrev direct M1 check -> `EXEC_REALISM_IDXREV_RESULT.json`.
- `EXEC_REALISM_combined.py` — book net-of-fills restatement -> `EXEC_REALISM_COMBINED_RESULT.json`.
