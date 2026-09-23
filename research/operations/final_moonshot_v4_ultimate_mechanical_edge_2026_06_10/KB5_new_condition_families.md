# KB5 — New orthogonal condition families for the confluence engine (track: new condition families)

Builder pass 2026-06-15. THE_GRAND_VISION (§II/§III/§39) names four MM/behavioral condition
families the confluence engine (`confluence.py`, 7 families) lacks. Built all four leak-free,
plugged into the confluence registry, and measured **phi-independence vs the existing 7 +
marginal forward odds-lift + whether stacking them MULTIPLIES the confluence stack**.

Engine: `KB5_condition_families.py` (6 new `(ctx,i,d)->bool` families, `EXTRA_CONDITIONS`).
Harness: `KB5_run.py` (extends `confluence.CONDITIONS`, reuses its probes + `simulate` labeler).
Result map: `KB5_CONDITION_FAMILIES_RESULT.json`.

Doctrine enforced: every condition is a pure function of CLOSED bars `index<=i` (intermarket
leaders sampled at the laggard's *own* timestamp, never a future bar — **leak-free verified** by
re-evaluating after truncating all future leader data: signal unchanged); outcomes labeled ONLY
by `geometry_lib.simulate` (pessimistic same-bar, real `w1.cost_for`); **no averages as verdicts**
— TRAIN(<=2024) vs FORWARD(2025-26), per-YEAR, n-gate, label-permutation null.

## The four families built

| family | what it measures | type | leak-free mechanic |
|---|---|---|---|
| **round-number magnetism** | `round_magnet` (close within 0.15·ATR of a psych round level, favour-side) + `round_reject` (wick pierced a round level, close reclaimed) | behavioral | per-symbol price grid (mag/100), bar i only |
| **session / time-of-day** | `sess_active` (H4 bar in the London/NY active window 8/12/16) + `sess_mom` (active-window bar closed in d with body≥0.15·ATR) | institutional schedule | `T[i].hour`, bar i only |
| **DXY → FX bias** | `dxy_bias` (synthetic dollar-index direction over last 6 bars aligns with the pair's dollar-sign) | intermarket | **proxy** built from FX majors (see data note), closed bars ≤ i |
| **oil → CAD bias** | `oil_cad_bias` (crude direction over last 6 bars implies USDCAD direction: oil-up→CAD-up→USDCAD-down) | intermarket | USOIL closes ≤ i |

### Load-bearing DATA REALITY (measured, not assumed)
- **Real DXY_cash H4 begins 2025-01-06 — entirely inside the FORWARD window.** Real DXY therefore
  CANNOT be forward-holdout validated (no train data, no per-year). I built a **synthetic DXY proxy**
  from the FX majors (full history), weighted by official DXY weights (EUR .576 / JPY .136 / GBP .119
  / CHF .036; 4-major where available else EUR/JPY). The proxy tracks real DXY at **return-corr +0.993
  (4-major) / +0.987 (2-major)** over the 2025+ overlap, and is leak-free. This is the only way to give
  the DXY family a real TRAIN(≤2024) vs FWD test. Reported as a proxy, honestly.
- USOIL from 2020-12-31, USDCAD from 2019-05-20 → oil→CAD has train+forward, but the CAD universe is
  just **USDCAD** here (CADJPY/CADCHF not in the loaded set) → small sample, n≈130 fwd.
- H4 bars carry only **6 hour-buckets** (0/4/8/12/16/20 server) → session granularity is coarse
  (Asia / London / NY); honestly reported as such.

## INDEPENDENCE — the prerequisite for confluence to multiply (max |phi| vs the EXISTING 7)

| new family | max \|phi\| vs existing 7 | verdict |
|---|---|---|
| `oil_cad_bias` | **0.009** | fully orthogonal |
| `round_magnet` | **0.066** | orthogonal |
| `round_reject` | **0.084** | orthogonal |
| `dxy_bias` | **0.091** | orthogonal |
| `sess_mom` | 0.359 (vs `struct_prox` −0.36) | partly overlapping |
| `sess_active` | 0.404 (vs `vol_loc` +0.40) | partly overlapping (volume concentrates in active sessions) |

**Round-number, DXY, oil families are genuinely INDEPENDENT signals** (|phi|<0.10) — they carry
information the existing 7 do not. Sessions partially co-move with `vol_loc` (activity ↔ volume),
so session conditions are distinct but not fully orthogonal; they add timing, not new price structure.

## ADDITIVITY — relative FWD R-lift (cond-TRUE minus cond-FALSE on the same probe; the clean "does it improve the spot" metric)

```
              round_magnet round_reject  sess_active  sess_mom   dxy_bias  oil_cad_bias
fvg :metals     +0.073       +0.020       +0.142      +0.188       --         --
fvg :index      +0.069       +0.026       +0.137      +0.124       --         --
fvg :fx_jpy     -0.005       +0.063       +0.245      +0.134      +0.223      --
fvg :energy     -0.157       -0.187       -0.468      -0.241       --         --
fvg :crypto     -0.123       +0.009       -0.132      -0.040       --         --
sweep:metals    +0.091       +0.127       -0.040      -0.022       --         --
sweep:index     +0.037       -0.049       +0.131      +0.090       --         --
sweep:fx_jpy    +0.095       +0.003       +0.003      +0.017      +0.178     -0.081
sweep:energy    +0.007       +0.021       -0.048      -0.047       --         --
sweep:crypto    +0.116       -0.013       -0.039      -0.059       --         --
```

## VERDICT per family (additive / independent or not — with the learning)

### 1. DXY → FX bias — **ADDITIVE & INDEPENDENT (best new family), but a FILTER not a standalone edge**
- max|phi| vs existing 7 = **0.091** (orthogonal). On FX it lifts the SAME setups by **+0.18R (sweep)
  / +0.22R (fvg)** forward (dxy-agree FWD +0.005R vs dxy-disagree −0.173R; TRAIN −0.132 vs −0.195 —
  the relative lift holds in BOTH halves). **Perm-null: sweep p=0.0062, fvg p=0.077.**
- **Honest limit:** it only *neutralizes* the sweep probe's negative base (it does not make a losing
  base a winner alone), and per-year it is **only 4/11 positive** in absolute R — the dollar-bias edge
  is regime-lumpy. Read: a real, independent **directional FILTER** that improves any already-positive
  FX base; size it as a confluence multiplier on FX, never as a primary. Built on the **synthetic DXY
  proxy** (real DXY has no train data) — flagged as proxy-validated.

### 2. Session / time-of-day — **ADDITIVE on metals & indices, ANTI-additive on energy/crypto (class-contingent)**
- On **metals & index FVG**: `sess_active` +0.14R, `sess_mom` +0.12–0.19R forward. **Decisive
  multiplication:** the KB4 headline metals edge `persistence ∧ vol_expand` (FWD +0.638R, n65) becomes
  `… ∧ sess_active` → **FWD 66.7% win / +0.992R (n39)**, TRAIN +0.481R (n55), **perm_p=0.0003**, and it
  **holds BOTH forward years** (2025 +1.40R n20, 2026 +0.56R n19). That is a genuine +0.35R confluence
  lift on the program's best validated cell.
- **Anti-additive where markets are 24h:** on **energy −0.47R** and **crypto −0.13R** the active-session
  flag is *negative* (crude/crypto don't respect the London/NY equity clock; their action is elsewhere).
- partly overlaps `vol_loc` (phi 0.40) → it adds **timing**, partly re-expressing the volume condition.
- **Learning:** sessions are additive ONLY for instruments driven by the equity-session clock
  (metals/indices); applying a time-of-day gate universally would DESTROY edge on energy/crypto. The
  engine must measure session additivity **per class**, never globally.

### 3. Round-number magnetism — **MILDLY additive on metals/index/crypto, independent, but small & noisy**
- Fully **independent** (max|phi| 0.066–0.084). On the wide sweep net it adds +0.09–0.13R on
  metals/crypto and +0.04R on index; on FVG +0.07R on metals/index. **But:** marginal FWD R-lifts are
  small (≤+0.07R as a standalone marginal), per-year is **unstable** (metals round_magnet is dominated
  by a 2017 n17 pocket; flat-to-negative most years; perm_p 0.05–0.012 borderline), and it is **negative
  on energy**. Read: a real-but-weak independent breadth nudge; useful as a tie-breaker inside a stack,
  not an edge alone. `round_reject` (the fade-off-the-magnet event) is the slightly stronger of the two
  on metals sweep (+0.127R, perm_p 0.0135) but still per-year-thin.

### 4. Oil → CAD bias — **NOT additive (honest rejection)**
- Fully orthogonal (max|phi| 0.009) but **forward-negative**: FWD −0.234R (n130), relative lift −0.08R,
  per-year unstable, perm_p 0.87. The H4 6-bar oil-lead signal is too slow to time USDCAD, and the CAD
  universe here is a single pair (n too small to confluence). **Do not add as a condition.** The
  intermarket *idea* is sound (oil↔CAD corr is real) but at H4 resolution on one pair it carries no
  tradeable, robust forward odds-lift. (Would need M15/M1 oil-lead + the full CAD-cross set to retest.)

## Net deliverable for the confluence stack
- **ADD `dxy_bias`** to the registry as an **FX-only directional filter** (independent, perm-significant,
  +0.18R relative lift) — multiplies any positive FX base; never standalone.
- **ADD `sess_active`/`sess_mom`** as **metals/index-only** confluence conditions — they multiply the
  program's best validated cell (metals persist∧vol_expand → +0.992R, perm_p 0.0003, both fwd years).
  Gate them OFF for energy/crypto (anti-additive).
- **KEEP `round_magnet`/`round_reject`** as independent tie-breakers (small, per-year-thin; size tiny).
- **REJECT `oil_cad_bias`** at H4 (orthogonal but forward-negative; revisit at LTF with full CAD set).
- **Layer lesson (reinforces KB4):** a new family's value is not its marginal win% — it is (a) phi-
  independence vs the existing stack AND (b) its **relative R-lift on the same spots, per class, per
  year**. Universal application is wrong: sessions help equity-clock instruments and hurt 24h ones;
  DXY/round-number help as filters not primaries; oil→CAD fails at this resolution. Measure SIGN ×
  CLASS × YEAR, never a global average.

## Files
- `KB5_condition_families.py` — the 6 new families (`EXTRA_CONDITIONS`), synthetic DXY proxy, leak-free.
- `KB5_run.py` — extends `confluence.CONDITIONS`; phi-independence, marginal lift, multiplication test,
  per-year, permutation null.
- `KB5_CONDITION_FAMILIES_RESULT.json` — full per-probe×per-class map.
