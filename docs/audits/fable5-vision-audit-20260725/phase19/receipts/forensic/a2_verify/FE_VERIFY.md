# Lane FE verification — Sol conditions scan (Phase A2)

Verifier: Fable verification agent, FA-continuation Phase A2. Evidence class
`FORENSIC_DIAGNOSTIC`. **February 2026 was read as fixed attribution only under
`owner_mandate_20260801`** — exactly the 26 frozen January cells and their frozen unions were
evaluated; nothing was selected, reordered, or retuned on February. March 2026 outcomes and
live-forward (2026-07-29+) outcomes were not read. The 3.2M-row ordered-path sidecar was not
needed — every FE claim lives on the two compact pools.

Audited worktree: `/Users/borr/GTOSActive/worktrees/wave19-sol-conditions-20260801`
(FE range `f8c05d0ac..2573afddb`, 7 commits, 20 changed paths — matches the completion receipt;
all **13/13** `SESSION_FE_COMPLETE.json` output hashes match disk).

**Method.** Sol receipts were treated as claims. I re-implemented `CONDITIONS_PROTOCOL.json`
from scratch and recomputed everything from the raw pools, streamed line-by-line
(peak RSS ~34 MB): 10-axis cell assignment, the 13/8-date TRAIN/HOLDOUT split,
`gross_r = opportunity_net_proxy_r + cost_r`, `net_r = opportunity_net_proxy_r`, the 200-row
TRAIN floor, alias collapse by hash of sorted TRAIN composite-identity membership
(`candidate_id, decision_time_utc, symbol, direction` — the FA Phase-1 join hazard key), the
frozen rankings, one-identity-once unions, the oil/GER40 cost sensitivity, and the
fixed-slippage width formulas. Both pool sha256s match the protocol pins
(`ee920fb0…fc8f`, `d89202…6b12`).

One wording note: the lane brief's "**15-field** condition scan" conflates two things. The
January scan is an **8-condition-field, 10-axis, 884-cell** scan; the **15 fields** are the FE3
telemetry allowlist. Sol's own artifacts are internally consistent.

## FE1 — January TRAIN scan

| claim | claimed | recomputed | verdict |
|---|---|---|---|
| pool rows / TRAIN / HOLDOUT | 27,658 / 16,248 / 11,410 | 27,658 / 16,248 / 11,410; identities all unique; dates match the protocol's 13+8 lists exactly | VERIFIED (exact) |
| declared / eligible / canonical cells | 884 / 119 / 87 | 119 eligible (TRAIN n≥200), 87 canonical after my own membership-hash alias collapse (32 aliases absorbed) | VERIFIED (exact) |
| TRAIN net-positive cells | **0** | **0** of 87 canonical (also 0 of 119 eligible) | VERIFIED (exact) |
| TRAIN gross-positive cells | 7 | 7 — and they are precisely the first 7 of the frozen gross ranking | VERIFIED (exact) |
| persistent net-positive | 0 | 0 | VERIFIED (exact) |
| strict survivors | 0 | 0 — arithmetically entailed: no TRAIN net-positive cell exists, and 0 of 26 frozen cells are Feb net-positive | VERIFIED |
| **persistent gross-positive** | **4** | **5 under the protocol's own `persistence_flags.gross` definition** (TRAIN>0 AND HOLDOUT>0, no floor); 4 only with a HOLDOUT n≥100 floor | **REFUTED as stated** |

**The 4-vs-5 discrepancy, loudly:** cell `family_hour|family=liquidity_sweep_reclaim|utc_hour=h08_09`
is gross-positive in both splits — TRAIN **+0.014759** (n=217), HOLDOUT **+0.317791** (n=96) —
yet `CELL_MAP_JAN.json` marks it `persistent_gross_positive: false`. The implementation folded
the 100-row HOLDOUT repair floor into the persistence flag; the protocol's
`cell_metrics.persistence_flags` declares no floor. CLAIMED **4** vs RECOMPUTED **5**
(protocol definition) / **4** (floored definition, = the frontier count). **Materiality LOW**:
the 5th cell is net-negative on every surface (TRAIN −0.4567, HOLDOUT −0.0683, Feb −0.6120), so
zero-net-positive / zero-survivor headlines are unmoved either way.

**3 best cells (spot-recompute, frozen gross rank order)** — all match my raw recompute to
≤ 8.3e-17 on means, exact on n:

| cell | TRAIN gross / net (n) |
|---|---|
| current_fvg_fill · SHORT · london | +0.243981 / −0.216142 (219) |
| displacement_continuation · h08_09 | +0.061684 / −0.207224 (248) |
| displacement_continuation · SHORT · london | +0.052606 / −0.144002 (299) |

Also verified from raw: the full frozen top-20 gross and top-20 net rankings reproduce
cell-for-cell in order (union = exactly 26 cells); Spearman TRAIN→HOLDOUT ρ **0.443847** gross /
**0.894602** net exactly as published (own average-rank implementation; the 999-draw max-adjusted
p-values were not re-run — they gate no headline when zero cells are net-positive); the 4-cell
frontier and its arithmetic (FVG cell: cost mean 0.3887412236, share ≤0.15R 0.4884393064,
p90 fixed-slippage width 8.595620841, mean gross − 0.15R = +0.0134855863, all quantiles ≤1e-9
from claims). Context: 59 subfloor TRAIN cells (largest n=18) are net-positive — the noise
population the 200-row floor exists to exclude.

## FE2 — Frozen February transfer (attribution-only, owner_mandate_20260801)

24,239 rows, all identities unique, all dated 2026-02-02..2026-02-27. Evaluating exactly the 26
frozen cells: **9 gross-positive, 0 net-positive, 0 strict survivors — VERIFIED.** Across all
26 cells × {n, gross_mean, net_mean, sens_n, sens_net_mean} the worst absolute difference vs
Sol's artifact is **6.4e-15**. All six frozen-union rows (gross/net × top-5/10/20) match to 6 dp
including sensitivity nets. The gross-identity reconciliation reproduces **exactly**: 16,560
rows > 1e-9, **0** rows > 5e-9, max **4.99998265e-9**.

The nine gross-positive cells, recomputed from raw (gross / net, n):

| frozen cell | n | Feb gross | Feb net |
|---|---:|---:|---:|
| current_fvg_fill · SHORT · london | 461 | +0.040268 | −0.204442 |
| displacement_continuation · LONG · london | 441 | +0.057614 | −0.144093 |
| displacement_continuation · LONG · ny | 465 | +0.036543 | −0.158607 |
| liquidity_sweep_reclaim · LONG · london | 329 | +0.109883 | −0.228178 |
| displacement_continuation · h00_01 | 260 | +0.190691 | −0.047256 |
| displacement_continuation · h07_08 | 321 | +0.010069 | −0.281792 |
| displacement_continuation · h14_15 | 451 | +0.185818 | −0.024173 |
| displacement_continuation · h15_16 | 341 | +0.048156 | −0.142829 |
| session_open_range_break (family) | 943 | +0.100452 | −0.093987 |

Every one is net-negative. The energy `symbol_class` cell's sensitivity population is empty on
both sides (energy = the two excluded oil symbols) — consistent, not a defect.

## FE3 — 15-field telemetry repair is default-off

**VERIFIED in code.** The entry is **`make_condition_feature_propagation_patch()` at
`src/research_infra/train_engine/cuts.py:1192-1261`** (Sol worktree), patch_id
`condition_feature_propagation`, constructed `default_on=False` (`:1259`),
`sealed_compatible=False` (`:1260`).

- `CONDITION_FEATURE_KEYS` (`cuts.py:879-895`) is **exactly 15 fields**, byte-identical to the
  pre-existing `PREDECISION_FEATURE_KEYS` (`src/components/broader_origin_generators.py:178-194`,
  untouched in FE's range) and to the protocol allowlist.
- Absent from `TRAIN_SAFE_SET_PATCHES` (`:1284-1291`) and `TRAIN_DEFAULT_PATCHES` (`:1292`,
  aliased to the safe set); reachable via `resolve_patches("safe+conditions")` →
  `TRAIN_CONDITION_FEATURE_PATCHES` (`:1298-1301`, `:1352-1353`). Nuance: the comma-list
  fallback (`:1354`) also accepts the bare patch id — still explicit-by-name, never a default.
- The installer's default selection independently honors `default_on=False`
  (`src/research_infra/fast_engine/accel.py:155`).
- The wrapped target `v4_timewarp_simulated_live_research_loop.py` **is R2-bound and was not
  edited** (empty `git diff f8c05d0ac..2573afddb` over it and over `broader_origin_generators.py`);
  the patch wraps `ledger_namespace_alias_fields` at runtime with exact-function revert. FE's
  edited paths (`cuts.py`, `sol_conditions.py`, tests) are **not** among R2's 43 bound paths.
- Projection is observation-only and fail-open: missing/malformed telemetry yields status fields
  (`condition_feature_ledger_fields`, `cuts.py:910+`), never suppresses candidate generation.

## Screening family for the A4 retro-declaration

FE's scan implies a screening family of **884 declared cells × 2 outcome bases = 1,768 screened
cell statistics** (8 declared condition fields — family, direction, session, utc_hour,
symbol_class, kill_zone, route_session, day_of_week — composed into 10 axes: the 8 marginals
plus family×direction×session = 540 and family×hour = 240). After the 200-row TRAIN floor
(119 cells) and alias collapse (87 canonical), the **inferential family is 87 × 2 = 174 looks**,
max-T FWER-adjusted jointly, plus 10 × 2 = 20 axis-η² looks and 2 rank-persistence looks.
February adds 26 frozen cells × 2 bases + 6 frozen unions, attribution-only, zero selection.
FE's own `LOOK_MANIFEST.json` self-reports `declared_cells=884`,
`january_cell_split_observations=1768` (cells × 2 **splits** — same number as my cells × 2
**bases**, different accounting), `eligible=119`, `canonical_inferential_looks=87`,
`billed_looks=0`, `permutation_draws=999`.

## Verdict summary

- **FE1: VERIFIED** — zero TRAIN net-positive, zero persistent net-positive, zero strict
  survivors, 3 best cells reproduced at float precision — **except** the sub-claim
  `persistent_gross_positive = 4`, **REFUTED as stated** (5 under the protocol's own
  definition; 4 only with the undeclared HOLDOUT n≥100 floor; low materiality).
- **FE2: VERIFIED** — 9 gross-positive / 0 net-positive on February, all 26 cells at ≤6.4e-15,
  unions and gross-identity reconciliation exact.
- **FE3: VERIFIED** — `condition_feature_propagation`, default-off at two independent layers,
  named entry `make_condition_feature_propagation_patch()` (`cuts.py:1192`), R2-bound bytes
  untouched.

Helper scripts and full recompute dumps in this directory:
`FE_recompute_jan.py`, `FE_recompute_feb.py`, `FE_JAN_RECOMPUTE_RAW.json`,
`FE_FEB_RECOMPUTE_RAW.json`.
