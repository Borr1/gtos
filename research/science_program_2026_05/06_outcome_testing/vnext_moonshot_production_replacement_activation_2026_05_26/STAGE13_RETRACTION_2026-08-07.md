# STAGE13 — the founding numbers for all ten broad families are SUPERSEDED

**Annotated 2026-08-07, wave-20 lane p4. Nothing in this directory has been deleted or altered.**
Every original value is byte-preserved; five artifacts gained one additive top-level
`_RETRACTED_2026_08_07` key each (95 inserted lines, 0 deleted, verified by parsing both sides and
comparing the documents with the annotation removed — identical on all five).

## Why this file exists

Commit `69d000fb3` (*"vnext: activate moonshot production replacement"*, 2026-05-27) turned on seven
broad origin families and three POI frameworks. Its evidence is this directory. Those numbers have
**never been retracted**, and until today they were the only evidence a reader of that commit would
find.

## What was claimed, and what supersedes it

| claimed here | value | superseded by |
|---|---:|---|
| pooled, `broader_origin_selected_metrics` | **+0.41278** R/trade, PF 2.252, 217,485 rows | **−0.29226** R/trade, same machinery, out of sample — `phase19/SLEEVES_OR_USAGE_VERDICT.md` row R1. **A 0.70504 gap and a sign flip.** |
| `structural_distance_extreme` | **+1.196255** R/trade, **83.73 %** win rate, 53,415 rows | **GEOMETRY_WRONG** — resolves at the median in 5 minutes; its 21-cell price grid is negative in 20 of 21 (`phase20/SLEEVE_FORENSIC_REPORT.md` row 14). The 15-window persistence is the one-sided tape, not the setups (`phase20/SESSION_M2_...md`). |
| `liquidity_sweep_reclaim` | **+0.201752** R/trade, 100,326 rows | the measured object is a **transcription, not the idea**: a 1–5 minute premise detected at 15-minute resolution, realised resolution 25 min, and no time stop at all (`SLEEVE_FORENSIC_REPORT.md` §5.2). |
| old-three POI component | **+0.55764** R/trade, PF 3.250, 72,115 rows | same selection defect, same route, same day; `current_fvg_fill` is IDEA_WRONG as a standalone family (`SLEEVE_FORENSIC_REPORT.md` row 12). |

## Three things measured for the first time on 2026-08-07

All three come from the artifacts in this directory, read directly.

**1. Four of the seven activated families were NEGATIVE in their own activating evidence.**
From `VNEXT_REPLACEMENT_STAGE13_BROADER_ORIGIN_REPLAY_SUMMARY_2026-05-26.json`,
`family_summary.<family>.activation_ready_dynamic_metrics`:

| family | expectancy_r | rows | activated? |
|---|---:|---:|---|
| `structural_distance_extreme` | **+1.196255** | 53,415 | yes |
| `cross_asset_lead_lag` | +0.324116 | 22,947 | yes |
| `liquidity_sweep_reclaim` | +0.201752 | 100,326 | yes |
| `displacement_continuation` | **−0.001394** | 93,918 | **yes** |
| `regime_transition_break` | **−0.025308** | 5,537 | **yes** |
| `session_open_range_break` | **−0.036532** | 17,666 | **yes** |
| `volatility_compression_expansion` | **−0.037773** | 14,357 | **yes** |

**130,354 of 307,042 rows — 42.5 % — sat in families the activating artifact itself scored
negative.** All seven were switched on.

**2. The headline is a selection, and the selection is the headline.**
`+0.41278` is measured over **217,485 of 316,489** family rows (68.7 %), retained by an in-sample
positive-EV cell filter: `min_group_rows: 20`, one exit policy (`be_after_trigger`) for all 1,302
kept cells, no out-of-sample split, no multiplicity adjustment, and **zero** of the 1,302 kept cells
has `expectancy_r <= 0` — positive by construction. Row-weighted over exactly the seven families the
commit activated, the same artifact gives **+0.293508**. **The selection premium is +0.119273
R/trade and it is entirely in-sample.**

**3. One family carries 70.9 % of the evidence.**
`structural_distance_extreme` contributes **63,898** of the activated set's **90,119** total R. The
family the forensic judges GEOMETRY_WRONG is more than two-thirds of the case for turning on the
other six.

## The activation lag

| cohort | born | activated | lag |
|---|---|---|---:|
| 7 `PRODUCTION_ORIGIN` families | `d6f09c5a2` 2026-05-26 | `69d000fb3` 2026-05-27 | **1 day** |
| 3 `current_*` POI frameworks | `34213a339` 2026-05-26 | `69d000fb3` 2026-05-27 | **1 day** |

This route's own docstring specifies TRAIN-only days, day-clustered t-statistics, Benjamini-Hochberg
at Q=0.05 across all cells, an effect floor net of a spread proxy, and survivors pre-registered for a
single out-of-time confirmation — materially the standard the estate ratified six and a half weeks
later. **The three families mined under that standard were never enabled. The seven from the
uncorrected sweep were.**

## Scope — what this does and does not change

`live_activation_allowed` is **false** for Selector V4 and Scheduler V4, so their permission gates
never fire (`permissions.py:930` returns `None` for every candidate). **No armed money is sized by
this allowlist today.** The armed book is the `ultimate_book` W7 book on four sleeves
(`config/live_armed_set.json`), none of which is a broad origin family. The allowlist in
`config/agent_config.yaml:1174-1181` is left exactly as it stands and carries the same annotation:
changing it is a strategy decision and belongs to Borhen.

Register: `docs/audits/fable5-vision-audit-20260725/phase20/forward/SUPERSEDED_CLAIMS_V1.json`
Receipt: `docs/audits/fable5-vision-audit-20260725/phase20/forward/P4_RECORD_CORRECTION.md`
