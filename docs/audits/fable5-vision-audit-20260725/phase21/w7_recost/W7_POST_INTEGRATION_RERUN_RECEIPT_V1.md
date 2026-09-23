# Wave 21 — W7 recost POST-INTEGRATION rerun receipt (V1)

Produced 2026-08-11 on branch `wave21/post-integration-measurements` (worktree from
`origin/main = 2edefd48a`). This discharges the `WAVE21_INTEGRATION.md` §11 open item
`w7_separate_measurement` and the `ROUTE_STATUS.json` phase of the same name: the retained
`phase21/w7_recost/` receipts bound pre-integration code (manifest `git_head b9fdf37c2`,
`integration_state PRE_INTEGRATION_957_COST_QUOTE_TRUTH`), so the runner had to be re-executed
unchanged under integrated code before any result-bearing economics claim.

## 1. What was run

```
PYTHONDONTWRITEBYTECODE=1 python3 docs/audits/fable5-vision-audit-20260725/phase21/w7_recost/w7_current_recost.py \
    --integration-state POST_INTEGRATION_WAVE21_COST_QUOTE_TRUTH
```

- Runner **byte-unchanged**: `w7_current_recost.py` at HEAD is hash-identical to the copy the
  retained pre-integration receipts bound in their own input manifest. Only the
  `--integration-state` flag differs, exactly as the retained report's own rerun requirement
  states.
- Code under measurement: `main@2edefd48a` working tree, clean. Exactly **five** of the
  manifest's 33 committed inputs changed since the retained run — `src/costs/model.py`,
  `src/costs/spread_model.py`, `src/research_infra/walkforward/exits.py`,
  `src/research_infra/walkforward/quote_side.py`, `src/utils/broker_clock.py` — the wave-21
  cost/quote/clock integration surface. All 28 others (armed set, ultimate_book engine,
  sleeves, execution, generation, config, caches, prior artifacts) are hash-identical.
- External sources: same 35 series consumed, **byte-identical** (all sha256 equal); same
  `BARS_MANIFEST.json` (150 files / 4,358,938 rows).
- Determinism: **two invocations, byte-identical outputs across all six generated files**
  (`W7_CURRENT_DETERMINISM_V1.json` updated to the post-integration pair).
- Wall/RSS: 131.2 s / 403 MB max RSS per invocation.

## 2. Headline — unchanged, and correctly so

| | pre-integration (retained) | post-integration (this run) |
|---|---|---|
| `headline_status` | `W7_NOT_EVALUABLE_HIGHER_INFORMATION_STOP` | `W7_NOT_EVALUABLE_HIGHER_INFORMATION_STOP` |
| `integration_state` | `PRE_INTEGRATION_957_COST_QUOTE_TRUTH` | `POST_INTEGRATION_WAVE21_COST_QUOTE_TRUTH` |
| missing supported source cells | 10 | 10 (identical cells) |
| source-cell roster | 84 cells, statuses identical | 84 cells, statuses identical |

The ten blocking cells are unchanged: CORN_c / COTTON_c / EU50_cash / FRA40_cash /
US2000_cash on the `sub_*` sleeves (FTMO 7, redacted_account 3), exactly as tabulated in
`W7_CURRENT_REPORT_V1.md`. This is correct fail-closed behavior, not a defect of the rerun.

**Unblock condition (recorded for the next owner of this lane):** a VPS export of those
source cells is **in flight**; the headline unblocks when they land under
`data/mt5_research_exports/` with `.timebase.json` sidecars and manifest SHA-256s. Note the
runner as committed binds its bar estate at `BARS_ROOT = /Users/borr/GTOSActive/vps-bars-20260727`
via `BARS_MANIFEST.json` — when the export lands under `data/mt5_research_exports/`, the new
cells must be registered into the bound manifest (or the runner's source binding amended in a
named commit) before the rerun can load them; landing files alone does not change the
headline.

## 3. What DID change under integrated code — the loaded-cell diagnostics

Machine-readable: `W7_PRE_POST_INTEGRATION_DIFF_V1.json` (same directory). Summary:

**3.1 Population identity.** 3,396 diagnostic rows pre and post, with **identical row
identity sets** (namespace, band, sleeve, symbol, entry_utc, direction). Generation, quote
walk, exit reasons, floor decisions: unchanged. Gross roster values: unchanged. Spread and
floor columns: byte-stable. The whole delta is in the cost-authority column and the net
values it feeds.

**3.2 The integrated fail-closed cost authority refuses 1,662 of 3,396 rows**
(`COMPLETE -> NOT_EVALUABLE`; 554 per band × 3 bands; zero rows moved the other way). Every
refusal reason is the artifact-bound slippage authority:
`cost_unavailable:CostTruthError:no reconciled price-domain slippage sample for <symbol> on
<broker>`. This is the same mechanism `WAVE21_INTEGRATION.md` §10 measured on the CS/CQ
breaker candidate, now measured on the W7 stack. Refusing symbols (mid band, rows):

| namespace | sleeve | refusing symbols (rows) |
|---|---|---|
| operator_profile | crypto | DASHUSD (31) |
| operator_profile | energy_agri | UKOIL_cash (35), USOIL_cash (33) — **the entire sleeve: 68/68 rows, no cost-evaluable row remains** |
| operator_profile | sub_mid_dn_revert | XAGUSD (36), CHFJPY (39), EURJPY (27), AUDJPY (22), USOIL_cash (20), UKOIL_cash (16), XAGEUR (14), XAGAUD (10), XAUAUD (9), XAUEUR (4) |
| operator_profile | sub_xvol_pullback | XAGUSD (26), XAGEUR (10), XAGAUD (8), UKOIL_cash (8), XAUAUD (5), USOIL_cash (4), XAUEUR (4) |
| redacted_account_live_bee34003 | energy_agri | UKOIL_cash (35), USOIL_cash (33) — **entire sleeve, 68/68** |
| redacted_account_live_bee34003 | sub_mid_dn_revert | AUDJPY (29), EURJPY (27), CHFJPY (21), USOIL_cash (20), UKOIL_cash (16) |
| redacted_account_live_bee34003 | sub_xvol_pullback | UKOIL_cash (8), USOIL_cash (4) |

Per-cell cost-evaluable counts (each band):

| cell | pre cost-evaluable | post cost-evaluable |
|---|---:|---:|
| FTMO crypto | 180 | 149 |
| FTMO energy_agri | 68 | **0** |
| FTMO sub_mid_dn_revert | 323 | 126 |
| FTMO sub_xvol_pullback | 79 | 14 |
| redacted_account crypto | 94 | 94 |
| redacted_account energy_agri | 68 | **0** |
| redacted_account sub_mid_dn_revert | 268 | 155 |
| redacted_account sub_xvol_pullback | 52 | 40 |

**3.3 On rows still priced, the integrated models move slippage (all rows) and commission
(some rows); swap and spread are byte-stable.** Mid band, 578 rows COMPLETE on both sides
with components:

| component | rows changed | mean delta (R) | max abs delta (R) |
|---|---:|---:|---:|
| slippage_r | 578 / 578 | −0.011146 | 0.039000 |
| commission_r | 96 / 578 | −0.001919 (−0.011555 on changed) | 0.030687 |
| swap_r | 0 / 578 | 0 | 0 |
| spread_r | 0 / 578 | 0 | 0 |
| net `r_net_current_clip` | 493 / 493 valued rows | **+0.012413** | — |

Directionally: the reconciled artifact-bound models price the covered symbols slightly
*cheaper* than the pre-integration layer, so surviving diagnostics improve a little while
coverage narrows a lot. Both effects are visible together in the per-cell table of
`W7_CURRENT_REPORT_V1.md`; the diagnostic means must never be read across the two runs
without this decomposition (survivor-mean changes mix re-pricing with population
restriction).

**3.4 The broker-clock repair relabels only pre-2007 series metadata.** 8 of 35 consumed
series move their `first_true_utc` by +1 h (all first bars in 2000–2006; the deliberate
pre-2007 DST calendar repair carried by `src/utils/broker_clock.py`). Zero emitted rows move
(`entry_utc` sets identical); `last_true_utc` unchanged on all 35. No economic effect on this
window.

**3.5 Sleeve scorecard.** Recommendations unchanged (4 `NE`, 4 `RESEARCH_ONLY`; `KEEP` 0,
`REPAIR` 0; no partial modelled row promoted). FTMO `energy_agri` keeps `RESEARCH_ONLY` as its
fail-closed disposition class while its cost column is now fully `NOT_EVALUABLE` — with the
narrower claim visible in its all-NE net columns.

## 4. Delta classification (per the wave-21 commit classes)

| delta | class | mechanism |
|---|---|---|
| 1,662-row cost refusal | **cost truth** | `src/costs/model.py` + `slippage_model` artifact-bound fail-closed slippage authority (per-broker reconciled sample set) |
| slippage_r / commission_r re-pricing on covered rows | **cost truth** | same layer, reconciled magnitudes |
| pre-2007 `first_true_utc` +1 h on 8 series | **chronology** | `src/utils/broker_clock.py` DST calendar repair |
| generation / quote walk / floor / identity | **no delta** | `walkforward/exits.py` + `quote_side.py` changed on disk but produced byte-stable walk results on this population |

No unexplained deltas: every changed field in the receipts traces to one of the five changed
inputs, and the two runs are internally deterministic.

## 5. Independent verification and tests

- `verify_w7_current_recost.py` (independent behavioral verifier, not contract-bound,
  runner untouched): the retained copy **crashed** on the post-integration outputs — it
  called `cost_r` bare with no refusal boundary, a code path written before the fail-closed
  cost authority existed (`CostTruthError: no reconciled price-domain slippage sample for
  XAGUSD on FTMO`, first FTMO silver row). It could never have verified a fail-closed cost
  refusal. Repaired this session to mirror the producer's single refusal boundary
  (`w7_current_recost.py:813-834`) and to *verify* refusals: on recomputed refusal it now
  asserts the row is cost-`NOT_EVALUABLE` with the same `cost_unavailable:` reason, correct
  floor interplay, and no cost/net fields; on recomputed success it now also pins
  `cost_authority_status == COMPLETE`. No assertion weakened.
- Post-repair verification: **PASS, zero failures** (`W7_CURRENT_VERIFICATION_V1.json`) —
  3,396 walker rows and 3,396 cost rows independently recomputed, all 726,822 external rows
  re-parsed, 692,492 generator bar evaluations re-executed, refusals verified row-by-row
  against the recomputed refusal reasons. One mechanical note: because the producer's input
  manifest binds the verifier's own file hash, the verifier repair required one further
  producer invocation; the final determinism pair (runs 3-4) is byte-identical across all
  six outputs and only `W7_CURRENT_INPUT_MANIFEST_V1.json` (the verifier-hash binding) and
  `W7_CURRENT_RECOST_V1.json` (which embeds the manifest hash) differ from the runs-1-2
  pair. Rows, source cells, report, and prior reconciliation are byte-identical across all
  four post-integration invocations.
- Lane-focused tests: **22 passed, 0 failed** post-integration
  (`W7_CURRENT_TEST_RECEIPT_V1.json` updated). One test re-pinned to the post-integration
  cell truth — `test_redacted_account_high_band_floor_exclusion_and_disclosed_cost_refusals` —
  keeping every floor pin and adding the disclosed cost refusal counts, so the
  zero-survivor claim stays floor-explained and the narrowing stays visible.

## 6. Claim boundary

Unchanged from the retained report: headline `NOT_EVALUABLE`; loaded-cell numbers are
`OBSERVED_SOURCE_ROWS_PARTIAL_DIAGNOSTIC_ONLY`; quote/lifecycle stays `MODELLED`; no
survivor-book result, no promotion input, no arming/risk/broker/live mutation. The
post-integration diagnostics additionally narrow the cost-evaluable population as §3.2
tabulates — a narrower claim, not a worse measurement.
