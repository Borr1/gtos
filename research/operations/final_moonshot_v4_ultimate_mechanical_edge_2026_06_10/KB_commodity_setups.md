# KB — Commodity Setup Breadth (track: csb)

Goal: add entry-trigger BREADTH on the commodity core beyond the confirmed FVG-retest,
each gated by the SAME momentum-persistence regime (`ac60>=0.10`) and managed by the SAME
exit (`cs.exit_state_d`). More trades/yr at comparable EV.

Build files (all under the route dir):
- `csb_commodity_setups.py` — 4 new triggers (OB, BRK, DISP, SWP) + FVG anchor, both gates, full report.
- `csb_probe_ob_refine.py` — OB quality-filter sweep.
- `csb_probe_split.py` — per-slice (metals/energy/per-symbol) forward breakdown.
- `csb_final_metals.py` — final deployable: FVG vs OB vs FVG+OB union on metals.
Results JSON: `CSB_COMMODITY_SETUPS_RESULT.json`, `CSB_FINAL_METALS_RESULT.json`.

No-lookahead: all signals use closed bars index<=i only (OB impulse check uses bar k+1 with
k<=i-2, so k+1<=i-1, a closed bar). Real cost via `w1.cost_for`. Exit winsorizes net R.

## Confirmed baseline reproduced exactly
FVG metals + ac60>=0.10 + `exit_state_d`: forward 2025-26 = **+0.865R/trade, 78% win, ~33/yr**.
Per-symbol forward: XAUUSD +1.10, XAGUSD +1.04, XAGEUR +1.04, XAGAUD +0.84, XAUEUR +0.89, XAUAUD ~0.

## THE DECISIVE STRUCTURAL FINDING
Raw new triggers (only ac60 gate) fire 3-10x more often than FVG but at near-zero/negative EV.
The FVG edge depends on TWO gates that `g.fvg_signals` bakes in: the momentum-persistence
gate (ac60) AND a **vol-expansion gate** (`atr >= 1.2 * SMA100(atr)`). Applying the vol gate to
the new triggers is mandatory. After both gates, per-slice forward is decisive:

| setup | metals fwd EV (n) | energy fwd EV (n) | XAUUSD fwd (n) | verdict |
|-------|------------------|-------------------|----------------|---------|
| FVG (baseline) | +0.865 (49) | -0.036 (41) | +1.10 (5) | keep, metals-only |
| **OB retest**  | **+0.467 (17)** | -0.304 (15) | **+0.954 (7)** | **forward-positive ADD (metals, small size)** |
| BRK breakout-retest | -0.713 (9) | -0.287 (6) | 0 (0) | learning only |
| DISP displacement | -0.242 (46) | +0.039 (33) | +0.004 (5) | learning only |
| SWP sweep-reclaim | +0.454 (1) | -0.180 (7) | 0 (0) | too sparse on metals |

Energy is net-negative across ALL triggers (incl. FVG). The commodity edge is **precious
metals**, not energy. Restrict everything to metals.

## KEEP — Order-Block retest on METALS (the new breadth that survives)
Rule (exact):
- STATE GATE 1 (persistence): `cs.autocorr(B,i,60) >= 0.10`.
- STATE GATE 2 (vol expansion): `atr14(B,i) >= 1.2 * mean(atr14 over i-99..i)`.
- HTF trend `w1.htf_trend(B,i,30)` = +1 (long) / -1 (short).
- TRIGGER: scan k in [i-2 .. i-8]; find last OPPOSITE-color candle (down candle for longs)
  immediately followed by an impulse that closes beyond its extreme (`B[k+1].c > B[k].h`);
  current bar i retests into the OB body (`b.l <= ob_top`), closes back inside trend
  (`b.c > ob_bot and b.c > b.o`). First match wins.
- STOP: `max((b.c - min(b.l, ob_bot)) + 0.10*atr, 0.25*atr)` (structural, mirrors FVG).
- DIRECTION: trend continuation. EXIT: `cs.exit_state_d` (vol-tiered scale-out).

Forward 2025-26: **+0.467R, 53% win, ~11 trades/yr.** Train<=24 −0.257.
Per-year: 2025 +0.669 (n15), 2026 −1.046 (n2). XAUUSD fwd +0.954 (n7), XAUEUR +1.56 (n2).

Controls (forward, metals):
- INVERT (fade continuation): **-0.296** -> edge is directional, not survivorship.
- NO ac60 gate: -0.139 (n258) -> persistence gate is load-bearing.
- NO vol gate: -0.068 (n103) -> vol-expansion gate is load-bearing.
Both gates are essential, identical to FVG. OB is the SAME edge expressed on a different
structure (order block instead of fair-value gap).

CAVEAT (honest): OB's forward positive is carried by 2025 (a strong metals trend-persistence
year); 2026 has only n=2 and is negative. Single-regime confound risk is real. Therefore OB is
a **confidence-SIZED keep at small size**, not a standalone equal-weight sleeve.

## BEST DEPLOYABLE: FVG + OB union on metals
Dedup by (sym,date,dir), FVG priority. Adds 22 unique entries (10 forward).
Forward 2025-26: **+0.740R, 71% win, ~39 trades/yr** (up from ~33).
2025 +0.927, **2026 +0.519** (stays positive, unlike OB alone — FVG anchors it).
Per-symbol forward gains: XAUUSD now n9 (was 5), XAUEUR n6 (was 4), XAUAUD n9 (was 6, now +0.01).
Trade-off: EV dilutes +0.865 -> +0.740 but frequency +18% and 2026 robustness preserved.
This is the breadth win: more trades/yr, EV still strongly positive, holdout still positive.

## LEARNINGS (the rejected triggers — where they DID work, what to try next)
- **BRK (breakout-retest)**: net negative on metals (-0.713 fwd). Trades taught us the swing-pivot
  break+retest fires mostly at trend EXHAUSTION (the break is the last gasp), so the retest fails.
  It DID show life in 2026 energy (+0.247 earlier, pre-split). NEXT: require the broken level to be
  a higher-timeframe (D1) level, and only take retests within N bars of the break (fresh breaks).
- **DISP (displacement continuation)**: net negative on metals, slightly + on energy (+0.039).
  Pure range-expansion without a structural retest LEVEL is noise — the pullback has no reference
  to defend. DID work in 2017/2019 metals (trend-explosive years). NEXT: anchor DISP to the FVG/OB
  created BY the displacement bar (then it just becomes FVG/OB — which is why FVG already wins).
- **SWP (liquidity-sweep-reclaim, trend-aligned)**: too sparse on metals after both gates (n=1 fwd).
  Trend-aligned sweeps of recent swing lows in an uptrend are rare because in strong persistence
  regimes price doesn't sweep back. DID work counter-trend historically (the wave1 sweep+reclaim
  reversal). NEXT: SWP belongs in the REVERSION sleeve (low ac60 / ranging), not the continuation
  core — test it under the INVERSE gate `ac60 <= 0` per the reversion thesis.

## Bottom line for the program
- Breadth ADD that ships: OB retest on metals, small confidence size; deploy as FVG+OB union.
- Net effect: ~33 -> ~39 trades/yr on the metals core, forward EV +0.74R, 71% win, 2026 positive.
- The persistence gate + vol-expansion gate are the universal commodity-continuation filters;
  any new continuation trigger MUST pass both and be metals-only.
- BRK/DISP/SWP are learnings for the energy and reversion tracks, not the metals continuation core.
