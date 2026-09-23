# KB4 — Liquidity map + engineered stop-hunt layer (track: liquidity_stophunt)

Builder/market-scientist pass 2026-06-15. LAYER, not a single strategy: a reusable
liquidity-map engine that models resting-liquidity / stop clusters, then mines the
forward odds of the canonical stop-hunt mechanic **SWEEP + RECLAIM** (price pierces a
cluster intrabar, then CLOSES back through it) conditioned on cluster type, relative
activity, reclaim strength, side, asset class, and HTF alignment — on H4 and M15.

Doctrine held throughout: **no lookahead** (all clusters from closed bars index<=i;
swing pivots need a right shoulder and are confirmed at c+k; the sweep bar is i and we
**ENTER at i+1 open**); fills via tested `geometry_lib.simulate` only; R-unit = structural
stop beyond the swept extreme; real per-asset cost `w1.cost_for`; **forward holdout**
TRAIN<=2024 vs FORWARD 2025-26, **per-YEAR, per-INSTRUMENT, per-CLUSTER-TYPE**, with n;
**no averages as verdicts**; high odds must come from **confluence**, sample size always shown.

## ENGINE (reusable, importable) — `liquidity_map.py`

`LiquidityMap(times, bars, sym).build()` exposes per-bar, leak-free cluster levels:

| ctype | meaning |
|-------|---------|
| `pd`  | prior-day high / low |
| `ps`  | prior-session high / low (Asia 00-08 / London 08-16 / NY 16-24 UTC bar-open) |
| `asia`| Asian-range edges (prior completed Asia session H/L) — tracked separately |
| `eq`  | equal highs/lows (>=2 confirmed swing extremes within `eq_tol*ATR` = a cluster) |
| `rn`  | round numbers (instrument-appropriate increment via `round_increment`) |
| `sw`  | swing pivots (fractal high/low, `swing_k` shoulders, confirmed at c+k) |

Surface: `cluster_levels_at(i)`, `relvol(i)` / `range_activity(i)` (precomputed, leak-free
rolling — relvol where broker volume exists, range-activity fallback), `sweep_signals(...)`
(generator of leak-free sweep+reclaim entries with full state), `run_cells(...)` /
`get_map(...)` (cached universe mining). Hot paths optimized (binary-search swing windows,
precomputed activity, per-(sym,tf) build cache) — full 46-sym H4 sweep ~6s, 5 configs ~12s.

Mining/grading harnesses (also reusable): `LM_mine.py` (per-ctype/class cells, multi-config),
`LM_probe_confluence.py` (HTF overlay + confluence stacks), `LM_strict_gate.py` (honest trust
gate), `LM_independence.py` (overlap vs the existing continuation sleeves + reversal isolation).

## HEADLINE VERDICT (honest, result-first)

**The sweep+reclaim stop-hunt mechanic is NOT a deployable standalone edge on this
universe.** It is robustly NEGATIVE in aggregate, and the apparently-positive forward
cells are single-regime artifacts and/or a noisier relabel of edges the book already owns.
This is the same trap data_depth caught for fx_jpy/idxrev — caught again, with hard evidence.

### 1) Pooled mechanic is a loser across EVERY cluster type, both regimes
`LM_LIQUIDITY_STOPHUNT_RESULT.json` — fixed-2R, full 46-sym H4 (n=520,945):

| ctype | TRAIN R (n) | FWD R (n) | FWD win% |
|-------|-------------|-----------|----------|
| pd    | -0.125 (23,962) | -0.087 (13,519) | 34% |
| ps    | -0.130 (42,197) | -0.082 (23,666) | 34% |
| asia  | -0.112 (38,685) | -0.092 (20,323) | 33% |
| eq    | -0.120 (26,085) | -0.103 (15,223) | 33% |
| rn    | -0.136 (55,322) | -0.102 (39,589) | 33% |
| sw    | -0.111 (141,733)| -0.101 (80,641) | 33% |

Win rate ~33% at 2R = exactly what a no-edge 2R bet pays. Tightening sweep/reclaim
thresholds, raising the activity gate (relvol>=1.2), switching to 3R or opposing-cluster
targets — none of it moves the verdict (all stay -0.09..-0.10R). M15 is identical: 3.35M
signals pooled at ~-0.10R.

### 2) HTF alignment does NOT rescue it
`LM_CONFLUENCE_RESULT.json` — H4 overlay:
- ALIGNED (continuation): TRAIN -0.123 / FWD -0.115
- COUNTER (reversal):     TRAIN -0.124 / FWD -0.080
- NEUTRAL:                TRAIN -0.109 / FWD -0.100

All three are train-negative. There is no HTF-conditioned slice of the bare mechanic
that is a real edge.

### 3) The "forward-validated" cells are TRAIN-NEGATIVE single-regime artifacts
Loose forward-validation (`fv`: fwd n>=40, fwd_R>0, majority fwd years +) flags ~dozens of
cells, but **nearly all have NEGATIVE train EV** and their forward EV is concentrated in
**2026 only** (e.g. `eq/energy/ALN` TRAIN -0.011 -> FWD +0.180 but 2025:+0.00 / 2026:+0.83;
`sw/energy/ALN` 2025:-0.03 / 2026:+0.39). That is the precise definition of a single-regime
artifact, not an edge. Applying the **STRICT honest gate** (`LM_STRICT_GATE_RESULT.json`:
fwd n>=40 AND fwd_R>+0.05 AND train_R>-0.02 AND **BOTH** fwd years >0 AND train n>=30):

- pooled `ctype x class x htf`: **2 / 143** cells pass (eq/energy/ALN, rn/energy/NEU) — both
  with most EV in 2026.
- `ctype x class x side x htf`: **12 / 283** pass — all HTF-aligned continuation **longs** on
  metals/energy/index/agri.
- `ctype x sym x htf`: 51 / 822 "pass", **but most have train n=0** (HEATOIL_c, XCUUSD, JP225,
  AUS200_cash, XAUAUD… have no pre-2025 broker history) — they pass the gate *vacuously*
  (no train to contradict). These are forward-only, NOT validated. M15 is worse: every M15
  passer has train n=0 (non-FX M15 starts 2025-06), so **all M15 cells are forward-only**.

The handful with REAL train evidence and both fwd years positive:
`('pd','metals','long','ALN')` TRAIN +0.015 / FWD +0.228 (2025 +0.24, 2026 +0.20, n_fwd 374);
`('ps','energy','long','ALN')` TRAIN +0.018 / FWD +0.147; `('eq','index','long','ALN')`
TRAIN -0.012 / FWD +0.192. All are **HTF-aligned continuation longs** — see (4).

### 4) The aligned survivors are a NOISIER RELABEL of the existing continuation sleeves
`LM_INDEPENDENCE_RESULT.json` — liquidity ALIGNED-continuation daily-R vs the canonical
FVG-retest continuation mechanic (`gold_sleeve.fvg_signals`) on the SAME symbols:

| group | daily-R corr | FVG-day overlap | liquidity total R / days | FVG total R / days |
|-------|--------------|-----------------|--------------------------|--------------------|
| metals| +0.198 | **91.4% of FVG days** are also liquidity days | **-277.5R / 2,500 days** | +124.4R / 267 days |
| energy| +0.166 | **94.4% of FVG days** | **-437.6R / 1,283 days** | +22.7R / 178 days |

The liquidity aligned-continuation slice **bleeds heavily in aggregate** (-277R metals,
-437R energy) while the FVG sleeve makes money on ~10x fewer, higher-quality days that the
liquidity layer almost entirely *contains* (91-94% overlap). The positive liquidity *cells*
are tiny pockets inside a losing river, and they fire on the same days the book already
harvests better. Cost sensitivity confirms the fragility: pooled metals-aligned is **+0.032R
zero-cost, -0.014R at real spread** — the mechanic barely clears zero gross and is killed by
cost. Net: the aligned slice adds **no new alpha**, only correlated noise.

### 5) The one STRUCTURALLY-DISTINCT mechanic (reversal reclaim) has no edge
COUNTER-trend reclaim is the only liquidity mechanic the continuation sleeves do NOT trade,
so it is where genuinely new alpha could live. It does not:
- metals CTR: TRAIN -0.074 / FWD -0.055 ; energy CTR: TRAIN -0.018 / FWD -0.077 ;
  index CTR: TRAIN -0.062 / FWD -0.126 ; jpy_fx CTR: TRAIN -0.128 / FWD +0.020 (the lone
  forward-positive, but train -0.128 = single-regime artifact, same JPY bias data_depth falsified).

### 6) Negative control — the ONE narrow pocket that carries real directional info
Inverting `pd/metals/long/ALN`: NORMAL FWD +0.218 vs INVERTED FWD -0.395 (and TRAIN +0.015 vs
-0.194). The strong asymmetry means this *specific* cell's direction is informative (not pure
survivorship) — but it is exactly the metals-continuation regime the book already monetizes via
FVG far more efficiently, so it is not a reason to add a new sleeve.

## WHAT TO DO WITH THIS (build-and-improve, never kill)

- **DO NOT deploy a standalone liquidity/stop-hunt sleeve.** Evidence: pooled-negative across
  all cluster types/timeframes/configs; "validated" cells are train-negative 2026 artifacts or
  train-n=0 forward-only; the only real-train survivors are a noisier, cost-fragile relabel of
  the existing FVG continuation (91-94% day overlap, daily-R corr ~0.18); the distinct reversal
  mechanic is negative; M15 has no train at all for non-FX.
- **KEEP the engine** (`liquidity_map.py`) as a reusable **feature/context layer**, not a signal
  generator. Its leak-free cluster levels (pd/ps/asia/eq/rn/sw), relvol/activity, and
  sweep-detection are useful as **conditioning inputs / exit context** for the validated sleeves
  (e.g. "is price sweeping a prior-session low into a metals continuation long?" as a confluence
  filter), and as a stop-placement reference (structural stops just beyond swept extremes). This
  is how a liquidity map should enter the book — as substrate, not as its own trades.
- **Highest-potential follow-up** (if revisited): test the cluster levels purely as an EXIT /
  target map for the metals_core + energy continuation sleeves (take-profit at the next opposing
  liquidity cluster) rather than as entries — the entry mechanic is dead but the *level map* may
  still improve exits. This is left as a pointer, not run here.

## CORRELATION / INTEGRATION CHECK vs the existing book

The existing W2 book is ~zero cross-sleeve correlation, dominated by metals/crypto/energy
continuation + a few breadth sleeves. The liquidity aligned-continuation slice is **+0.166..+0.198
daily-R correlated with the FVG continuation it overlaps 91-94%** — i.e. it is NOT orthogonal to
the book's core; it is the same regime, captured worse. Adding it would raise correlation and drag
EV. Honest conclusion: this layer's value to the book is as conditioning substrate, with **zero
new tradable sleeves admitted** from the stop-hunt mechanic on this evidence.

## FILES (all under the route dir)
- `liquidity_map.py` — the reusable liquidity-map / stop-hunt ENGINE (importable).
- `LM_mine.py` -> `LM_LIQUIDITY_STOPHUNT_RESULT.json` — per-ctype/class cells, multi-config.
- `LM_probe_confluence.py` -> `LM_CONFLUENCE_RESULT.json` — HTF overlay + confluence stacks.
- `LM_strict_gate.py` -> `LM_STRICT_GATE_RESULT.json` — honest trust gate; survivors.
- `LM_independence.py` -> `LM_INDEPENDENCE_RESULT.json` — overlap vs FVG continuation + reversal.
- Data: H4 via `w1.load` (46 syms, 2015-2026, deep-backfilled); M15 via `liquidity_map.load_m15`
  (deep FX backfill 2014-2025 unioned with recent 2025-06..2026-06; non-FX M15 is 2025-06+ only,
  hence train-n=0 — stated honestly).
```
TRUST GATE used: fwd n>=40 AND fwd_R>+0.05 AND train_R>-0.02 AND BOTH fwd years >0 AND train n>=30.
Cells with train n=0 are reported but treated as FORWARD-ONLY (not validated).
```
