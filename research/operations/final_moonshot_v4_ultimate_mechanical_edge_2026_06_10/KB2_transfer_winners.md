# KB2 — Transfer the two Wave-1 execution wins to crypto + energy (track: TW)

Goal: apply the two Wave-1 EXECUTION winners to the OTHER persistence/continuation sleeves.
(a) **EXEC_COMBO / EXEC_LOCK exit** (deeper 2.0R scale + vol-banded profit-lock 0.25/0.5/0.75R
instead of flat BE; spec in `KB_execution.md`) -> transfer to crypto (BTC/DASH breakout) and
energy (vol-regime FVG). (b) **H1->M15 cascade better-fill** (spec in `KB_multitf.md` +
`multitf_lib.py`) -> transfer to crypto and energy. Forward-validate each vs the sleeve's CURRENT
exit/entry; keep if better, learning if not.

Engine reuse (no reinvention): `EXEC_exit_variants.sim_exit` (parity-proven to STATE_D, leak-free,
pessimistic adverse-before-favorable, winsorized [-1.3,+5]) for all exits; `multitf_lib` primitives
(`first_ltf_index_after`, leak-free binary search) for the cascade. Cost = `w1.cost_for(sym)`;
energy scaled by stop tightness exactly as `EXEC_exit_variants.build_entries`. Entries held
**identical** to each sleeve's locked rule. TRAIN=entries year<=2024; FORWARD=2025+2026 separate.

## HEADLINE VERDICT (per sleeve, per transfer)

| transfer | crypto | energy |
|---|---|---|
| **(b) H1->M15 cascade fill** | **PROMOTE** (FWD +0.751->+1.048, t2.10, maxDD 1.88%->1.39%) | **PROMOTE** (FWD +0.675->+0.877, t2.84, maxDD 0.51%->0.33%) |
| **(a) EXEC_COMBO exit** | **LEARNING** (does NOT beat native target4: +0.518 vs +0.751) | forward-win not train-validated (FWD +0.675->+0.924 t2.79, but TRAIN -0.121 t-0.70) |
| **(a) EXEC_LOCK exit** | LEARNING (does NOT beat target4) | **train-validated variance-neutral add** (TRAIN +0.100 t3.90; FWD-neutral) |

(Data note: `w1.load('UKOIL_cash')` returns full 2020-2026 H4 — `KB_energy_agri.md`'s "UKOIL
2020-2021 only" is STALE; UKOIL contributes 36 entries incl. 22 forward. The locked energy universe
under the A/B gate is **n=105 (35 train, 70 fwd)**, matching `energy_agri_sleeve.final_sleeve`.)

The **cascade is the universal winner** — it transfers cleanly to both sleeves with EV up and
maxDD flat-or-down. The COMBO/LOCK *exit* transfer is sleeve-specific: it does not beat crypto's
full-position 4R target, and on energy it splits (COMBO=forward-win/train-loss, LOCK=train-win).

---

## (b) H1->M15 CASCADE BETTER-FILL — the clean transfer (PROMOTE both)

Rule transferred verbatim from `KB_multitf.md`: after the H4 signal bar CLOSES (actionable t+4h),
wait W_H1=12 H1 bars for a pullback improving the fill by >=1.0*ATR_h1 vs signal close; enter there
with the SAME H4-width structural stop (same risk unit). If H1 finds nothing, scan W_M15=48 M15 bars
for a >=1.0*ATR_m15 pullback. Only THEN fall back to H4. Never skip a signal. Exit runs on the LTF
stream, wall-clock matched (H1 maxbars=320, M15=1280). **Leak audit: 0 entries before the H4 signal
close on either LTF leg, both sleeves.**

### CRYPTO (entries fixed: BTC+DASH lb20 breakout + ac60>=0.15 + sd=2*ATR; native target4 exit)
n=68 (8 train, 60 fwd). Fill source mix: 34 H4 / 30 H1 / 4 M15 (50% of signals got a better LTF fill).

| metric | base H4 | **cascade** |
|---|---|---|
| TRAIN<=2024 (n8) | +1.138 | +1.138 (no LTF pre-2025) |
| 2025 (n44) | +0.747 | **+0.988** (w 50->54%) |
| 2026 (n16) | +0.762 | **+1.211** (w 44->56%) |
| **FWD (n60)** | +0.751 | **+1.048** |
| FWD win% | 48 | **55** |
| FWD maxDD @0.25% | 1.88% | **1.39%** |
| trades/yr (fwd) | ~42 | ~42 (unchanged) |

Paired FWD casc-base: **+0.297R, t=2.10**. On the 34 forward rows that actually got a better LTF
fill: base +0.566 -> casc **+1.090 (+0.524R lift)** — same-magnitude as the metals +0.416..+0.537R
better-filled lift. Both forward years improve; the deeper 2026 BTC decline/chop year improves most
(+0.762->+1.211), i.e. the better entry rescues the adverse regime.

### ENERGY (entries fixed: ENERGY FVG + A/B gate vr>=2.0 OR |slope|<0.05; native STATE_D exit)
n=105 (35 train, 70 fwd). Fill mix: 77 H4 / 18 H1 / 10 M15 (27% got a better LTF fill; lower than
metals because UKOIL's 22 forward signals have no mapped LTF -> H4 fallback, correctly neutral).

| metric | base H4 | **cascade** |
|---|---|---|
| TRAIN<=2024 (n35) | +0.457 | +0.457 (no LTF pre-2025) |
| 2025 (n30) | +0.306 | **+0.421** (w 60->63%) |
| 2026 (n40) | +0.952 | **+1.219** (w 75->80%) |
| **FWD (n70)** | +0.675 | **+0.877** |
| FWD win% | 69 | **73** |
| FWD maxDD @0.25% | 0.51% | **0.33%** |
| trades/yr (fwd) | ~35 | ~35 (unchanged) |

Paired FWD casc-base: **+0.202R, t=2.84**. Better-filled rows only (n28): base +0.874 ->
casc **+1.378 (+0.504R lift)**. **Pareto improvement: EV up, win up, maxDD DOWN (0.51%->0.33%),
worst-day identical.**

### CONFOUND HONESTY (the one caveat — read before deploying)
Crypto and energy LTF (H1/M15) is **forward-only (2025-06+)**. Unlike XAUUSD metals (deep H1 from
2015), there is **no pre-2025 OOS** for the better-fill mechanic on these symbols, so the cascade
lift here is measured FORWARD ONLY. Mitigation (why this is mechanism, not a single-regime artifact):
1. `KB_multitf.md` already proved the mechanic CAUSAL on genuine pre-2025 OOS metals
   (TRAIN deep-H1 better-filled rows n33: base +0.126 -> +0.542 = **+0.416R lift**).
2. The transfer reproduces that lift at the SAME magnitude on a DIFFERENT asset class with a
   DIFFERENT entry: crypto better-filled rows +0.524R, energy +0.504R, metals +0.416R. Three
   asset classes, same R-space geometry, same-size lift => the edge is the geometry (better entry,
   same H4-width stop, same move), not a regime coincidence.
3. The lift appears in BOTH forward years for both sleeves (not a single 2026 spike).
Deploy with this label: forward-validated + cross-class causal corroboration; collect pre-2025
crypto/energy H1 to convert to a direct train proof (data is the only blocker).

---

## (a) EXEC_COMBO / EXEC_LOCK EXIT TRANSFER — sleeve-specific (one learning, one conditional)

EXEC_COMBO (per `KB_execution.md`): scale 50% @ +2.0R; runner stop -> vol-banded LOCK
(LOW vr<1.35: +0.25R, target 4.0R | MID 1.35-1.6: +0.5R, target 3.0R | HI vr>=1.6: +0.75R,
target 2.5R); structural 1R initial stop; no trail. EXEC_LOCK: keep STATE_D scale levels
(1.5/1.5/1.0) but swap flat-BE runner stop for the vol-banded lock (BE / +0.5 / +0.75).

### CRYPTO exit transfer — LEARNING: scale-out does NOT beat the full-position 4R runner
Same 68 entries; H4 exits compared.

| exit | FWD EV (n60) | FWD win% | runner-capture | FWD maxDD |
|---|---|---|---|---|
| **target4 (native baseline)** | **+0.751** | 48 | 207%* | 1.88% |
| STATE_D scale-out | +0.448 | 60 | 47% | 1.31% |
| EXEC_COMBO | +0.518 | 52 | 58% | 1.42% |
| EXEC_LOCK | +0.455 | 60 | 42% | 1.25% |

(*target4 "runner-capture" >100% because every win is a full-target win; the metric is rc vs a
scale-out denominator — read it as "all wins run to 4R".)

Paired vs target4: COMBO -0.271R (t-2.59), LOCK -0.361R (t-2.51) — both significantly WORSE.
**Decisive learning: crypto momentum breakouts pay by letting the WHOLE position run to a deep 4R
target. Any 50% scale-out (STATE_D, COMBO, or LOCK) caps the fat right tail that IS the crypto
edge — BTC/DASH continuation moves are large and one-directional, so booking half at +2.0R throws
away the part that makes the sleeve work.** This mirrors the metals finding inverted: metals
continuations are SLOW and give back (so scaling+lock helps); crypto continuations are FAST and
extended (so full-position-to-target wins). **Where the scale-out DID help on crypto:** among
scale-out exits, COMBO beats STATE_D (+0.518 vs +0.448, paired +0.102 t1.46) and trims maxDD vs
target4 (1.42% vs 1.88%). So for the **risk-tight crypto allocation** (KB_crypto already offers
`exit_state_d` as the lower-variance option at +0.45R), **swap that STATE_D for EXEC_COMBO** —
it lifts the conservative crypto allocation +0.448 -> +0.518 at similar variance. Keep target4 as
the full-size crypto exit.

### ENERGY exit transfer — COMBO is a forward win but NOT train-validated; LOCK is train-validated
Same 105 entries; H4 exits compared.

| exit | TRAIN ev (n35) | 2025 (n30) | 2026 (n40) | FWD ev (n70) | FWD win | FWD maxDD |
|---|---|---|---|---|---|---|
| **STATE_D (native baseline)** | +0.457 | +0.306 | +0.952 | +0.675 | 69 | 0.51% |
| **EXEC_COMBO** | +0.335 | +0.319 | **+1.377** | **+0.924** | 60 | 0.74% |
| **EXEC_LOCK** | **+0.557** | +0.294 | +0.934 | +0.659 | 69 | 0.51% |

Paired vs STATE_D:
- **COMBO**: FWD **+0.248R t2.79** (forward-significant) BUT **TRAIN -0.121R t-0.70** (mildly
  hurts the pre-2025 set — insignificant now with the fuller universe, but the SIGN is the warning).
  Forward-positive/train-soft split. Driven by the **supply-shock tier** (vr>=2.0):
  STATE_D +0.631 -> COMBO +0.990 forward. Per-year supply-shock: 2025 +0.161->+0.244, 2026
  +0.998->+1.574; but 2021 (n4) +0.490->+0.177 and 2022 (n3) +0.901->+0.067 are the train/pre-2025
  drag (small-n, the moves there peaked 1.5-2.0R then stopped).
- **LOCK**: **TRAIN +0.100R t3.90** (train-VALIDATED — the doctrine's gold standard) but FWD
  -0.016 (neutral). Same EXEC_LOCK "variance-neutral free add" profile from `KB_execution.md`:
  same win (69%), lower std (1.28 vs 1.33), same maxDD (0.51%), but lifts the give-back round-trips.

**Mechanism (matches KB_execution exactly):** COMBO's deeper 2.0R scale captures the long
supply-shock runs of 2026 (energy vr>=2.0 moves extend far -> deeper scale + deeper hold pays),
but it sacrifices the trades that peak between 1.5-2.0R then stop — and the thin 2021/2022 energy
pre-2025 set is dominated by exactly those, so train EV drops. LOCK keeps the 1.5R scale (banks
those) and only changes the give-back, so it is train-safe but leaves the 2026 supply-shock upside
on the table.

**Per-symbol forward (STATE_D -> COMBO):** USOIL +0.509->+0.641, HEATOIL +1.205->+1.651,
NATGAS +0.838->+0.824 (flat), UKOIL +0.240->+0.501. HEATOIL is forward-only (2026 single-regime)
so part of COMBO's forward win carries that confound; USOIL (forward-validatable, 2021 train +
2025-26 fwd) and UKOIL still improve forward — not a HEATOIL-only artifact.

### Per-regime (energy, FWD) — where each exit earns its keep
| vol tier | n | STATE_D | EXEC_COMBO |
|---|---|---|---|
| LOW <1.35 | 22 | +1.118 | +1.118 |
| MID 1.35-1.6 | 6 | -0.611 | -0.320 |
| HI >=1.6 | 42 | +0.627 | **+0.999** |
COMBO's entire energy edge is the **HIGH-vol tier** (the supply-shock state) — exactly the tier
`KB_energy_agri.md` flagged as leaving R on the table under STATE_D. Confirmed (LOW unchanged
because the 2.0R scale rarely fills there; HI lifts +0.627->+0.999).

---

## DEPLOYABLE RECOMMENDATIONS (sized by confidence, delete nothing)

1. **CRYPTO: deploy the H1->M15 cascade fill on top of the native target4 exit.** Drop-in: same
   BTC+DASH breakout signals, same sd=2*ATR risk unit, same 4R target; only the fill price + exit
   stream change. FWD **+0.751 -> +1.048R/trade**, win 48->55%, maxDD 1.88%->1.39%, ~42 trades/yr.
   Keep target4 as the exit (do NOT swap to scale-out at full size). For the risk-tight crypto
   allocation, use EXEC_COMBO instead of STATE_D (+0.448->+0.518) — also cascade-lifted (+0.696).
2. **ENERGY: deploy the H1->M15 cascade fill on top of the native STATE_D exit.** Pareto win: FWD
   **+0.675 -> +0.877R/trade**, win 69->73%, maxDD 0.51%->0.33%, worst-day unchanged, ~35 trades/yr.
3. **ENERGY exit, two confidence tiers:**
   - *Train-validated (full confidence):* swap STATE_D's flat-BE runner for **EXEC_LOCK**'s
     vol-banded lock (TRAIN +0.100 t3.90, variance-neutral, maxDD unchanged) — free give-back fix.
   - *Forward-aggressive (haircut confidence, supply-shock tier only):* **EXEC_COMBO** on the
     vr>=2.0 supply-shock sub-sleeve (FWD +0.631->+0.990) — gate it to HIGH vol so the train drag
     (which lives in small-n 2021/2022) is avoided; size at reduced confidence until deeper pre-2022
     energy H4 converts the supply-shock tier to train-validated.
   - **Best forward energy stack = cascade fill + COMBO exit:** baseline STATE_D-H4 +0.675 ->
     **+0.993R FWD** (2025 +0.306->+0.342, 2026 +0.952->+1.481), maxDD 0.74%. Highest EV; carries
     COMBO's train-soft confound, so deploy at haircut size vs the cascade+STATE_D Pareto stack.

## NEGATIVE / LEARNINGS (keep, do not delete)
- **EXEC_COMBO/LOCK scale-out exits LOSE to crypto's full-position 4R target** (COMBO -0.271R
  t-2.59 vs target4). Crypto = fast extended continuation -> ride the whole position; do NOT
  scale out at full size. (Among scale-outs, COMBO > STATE_D > LOCK on crypto.)
- **EXEC_COMBO softens the energy pre-2025 set** (TRAIN -0.121R t-0.70; the sign, not the
  magnitude, is the warning) even though it wins forward (+0.248 t2.79) — its deeper 2.0R scale only
  pays where moves extend (supply-shock 2026), and the thin 2021/2022 set is the wrong regime for
  it. Gate COMBO to vr>=2.0, or use LOCK (TRAIN +0.100 t3.90) for train-safety.
- **LTF forward-only confound** for crypto/energy: cascade lift is forward-measured; relies on the
  metals pre-2025 causal proof + cross-class magnitude match for OOS credibility. Source pre-2025
  crypto/energy H1 to close this directly.

## NEXT STEPS
1. Source pre-2025 H1/M15 for BTC/DASH and USOIL/NATGAS -> convert the cascade lift to a direct
   train-validated proof (current blocker is data, not signal; the mechanic is causal on metals).
2. M1-intrabar realism on the cascade limit fills (the >=1*ATR pullback is a limit order) and on
   COMBO's deeper 2.0R scale leg + lock stop for energy — price the slippage on the supply-shock
   tier specifically.
3. Wire cascade(crypto/target4) and cascade(energy/STATE_D) into `INTEG_portfolio_build.py`;
   re-run the portfolio maxDD/FTMO gate with the lifted per-sleeve EV at identical (or lower) tail.
4. Test the cascade on the FX sleeve where M15 exists (per the brief) — `KB_fx_jpy.md` probe11/12
   already touched M15; check whether the same better-fill geometry adds there.

## Artifacts
- `TW_exit_transfer.py` (exit policies + reporting), `TW_run_exit_transfer.py` (driver),
  `TW_EXIT_TRANSFER_RESULT.json`.
- `TW_mtf_cascade_transfer.py` (cascade engine, leak-audited), `TW_run_mtf_cascade.py` (driver),
  `TW_MTF_CASCADE_RESULT.json`.
- `TW_CRYPTO_CASCADE_LEDGER.jsonl` (68 rows: src + base_R + casc_R per signal),
  `TW_ENERGY_CASCADE_LEDGER.jsonl` (62 rows: src + base_state_d_h4 + casc_state_d/combo/lock).
