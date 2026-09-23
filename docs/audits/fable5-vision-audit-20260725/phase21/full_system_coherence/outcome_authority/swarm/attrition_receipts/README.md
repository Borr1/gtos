# attrition_receipts — ATTRITION_RECOVERY_V1

Every script reads sealed inputs and writes only to `/private/tmp`. Nothing touches a live path,
a config, or the VPS. Run order is irrelevant; the scripts are independent.

| script | writes | establishes |
|---|---|---|
| `fb_rewalk.py` | `FB_REWALK_V2.json` | Target 1. Re-walks FB's `current_ob_retest` 1.5D/0.25D cell from `CJ_RECLOCKED_S0R0_POOL_V1` + `CQ_TRUE_UTC_S0R0_ORDERED_PATH_SIDECAR_V1` with the tick override. **CONTROL reproduces the published cell exactly** (gross 2.862376572451229, net 1.6467194254150541, 707/549/84). Then MIRROR, FILL_GATED, SPREAD_CORRECTED and the two compositions, plus the displacement diagnostics. |
| — | `FB_REWALK_LIMITONLY.json` | the same six arms restricted to the 1,243 rows the pool labels `effective_order_type: limit`. |
| `ah_repro.py` | `AH_REPRO.json` | Target 2. Rebuilds AB's regime spine with AF's own `label_regimes`/`bucket` and re-derives `VOL_REGIME==hi` (n 203, mean 0.22660, identical quintile means). Establishes the instrument: `r_gross ∈ {−1.0, +2.0}` on 610/610 rows. |
| `ah_restate.py` | `AH_RESTATE.json` | Target 2. Broker-true `spread_r`, the quote-frame level correction, the migration bound, and the max-T permutation over the 9-cell enumeration (20,000 label permutations). |
| `ah_addendum.py` | `AH_ADDENDUM.json` | Target 2. The conditioning effect (hi vs rest), the cell-vs-zero t, and a 100-day day-block bootstrap. |
| `merge_arith.py` | `MERGE_ARITH_V2.json` | Target 3. Executes the three `SLEEVE_FORENSIC_REPORT.md` §5.4 merges against `CANDIDATE_FAMILY_V27` and recomputes BH at α 0.10 over the 28 real p-values of `AI_GATE_AT_DECLARED_FAMILY_V1`. Needs those three JSONs staged under `/private/tmp/attrition-inputs/`. |
| `funnel_basis.py` | `FUNNEL_BASIS.json` | Target 4. Puts the three published abstain-vs-mixed margins on one basis and tests each paired by day, on both bases. Reads the three committed validation results. |
| `funnel_limit.py` | `FUNNEL_LIMIT.json` | Target 4. `E[net + cost_r]` by family on Lane G's `pool_table.npz`, plus the count-matched random-abstention control (20,000 draws). |

External inputs, none of them in the repo: `/Users/borr/GTOSActive/vps-bars-20260727` (bars),
`/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/.../sources/ticks/202601`
(ticks), `/private/tmp/laneG-walk/pool_table.npz` (Lane G, rebuildable by `lane_g_receipts/extract.py`).
