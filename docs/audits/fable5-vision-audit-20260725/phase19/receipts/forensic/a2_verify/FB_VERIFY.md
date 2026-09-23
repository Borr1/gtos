# Lane FB Verification — Session FB (Sol full-family grid)

**Verifier:** Fable verification agent, FA-continuation Phase A2 · 2026-08-03
**Verdict summary: 5/5 claims VERIFIED, all exact (0.0 deviation). No refutations.**

Sol receipts were treated as CLAIMS; the January pool, ordered path sidecar, and raw lane-registry
tick files were the EVIDENCE. Everything below was recomputed by
[`a2_fb_walker.py`](a2_fb_walker.py) (log: `a2_fb_walker.log`, full output:
`A2_FB_RECOMPUTE_RESULT.json`) in 31.5 s at **peak RSS 0.54 GB** (bound: 1.5 GB), sidecar streamed
line-by-line, never materialized.

## Mandate compliance

- **March 2026 outcomes: never read.** Walker enforces a January-only guard on every walked
  timestamp (pool rows and all 3,229,819 sidecar observations).
- **Live-forward (2026-07-29+): never read.**
- **February: attribution-only under owner_mandate_20260801 — and this lane read NO February raw
  data at all.** `FEB_CORROBORATION.json` was sha256-verified (file hash vs
  `SESSION_FB_COMPLETE.json`, rooted self-hash) but not recomputed; no FB claim in this lane
  touches February.
- No lane arms, no replays, no test suite, no source edits. Writes confined to this directory.

## Input authentication (all pass)

| artifact | check | result |
|---|---|---|
| 7 grid outputs | sha256 vs `SESSION_FB_COMPLETE.json` | all match |
| 6 rooted JSONs | canonical `self_sha256` | all valid |
| January pool | `ee920fb0…` (= GRID_PROTOCOL bound input) | match |
| Ordered path sidecar | `ffa2a215…` (= GRID_PROTOCOL bound input) | match |
| 4 tick sources (wave16 lane registry) | sha256 vs `GRID_FULL_RESULTS.path_resolution` | all match |
| max-T blocks | `FAMILY_CLASSIFICATION` vs `BREAKER_REDERIVATION` | deep-equal |

Composite-join hazard reconfirmed from the raw pool: 967 candidate_ids with multiplicity, 6,745
rows non-unique, 5,778 excess rows — a bare `candidate_id` join is invalid; the 4-tuple
`(candidate_id, decision_time_utc, symbol, side)` is unique on all 27,658 rows and the sidecar
aligns key-for-key in pool order (validated at every row).

## Method

Independent walker mirrors `GRID_PROTOCOL.json` semantics: `D_i = |entry − stop_loss|`; 120-min
horizon, strict-after windows; conservative same-M1-bar stop; tick override on EURUSD/USDJPY/
XAGUSD/XAUUSD (LONG exits bid, SHORT exits ask); `gross = target_d/stop_d | −1 |
terminal_signed_d/stop_d`; `net = gross − cost_r/stop_d`; TRAIN = first 13 UTC dates, HOLDOUT =
last 8. Costs are the pool's `cost_r`: Sol's broker-true commission reprice is an **exact
identity** (27,658/27,658 rows, max |Δ| = 0.0), so no cost model import was needed.
Independence scope, stated honestly: the walker was written from the protocol; where the protocol
leaves implementation detail open it mirrors Sol's committed code, so a defect shared by protocol
and implementation would not surface as an inequality here. Independently enforced regardless:
January-only guard, horizon arithmetic, observation window/order validity, outcome partition
validity, count identities, eligibility thresholds, leader tie-breaks, classification precedence.

## Claims

### FB1 — inverted breaker, target 5D / stop 0.25D: +11.901 R/trade over 4,263 rows — **VERIFIED (exact)**

`inverted|target_5D|stop_0.25D` × `family:current_breaker_re_entry`, FULL stratum:

| split | n | mean_net_r (mine = receipt, Δ=0.0) | mean_gross_r | TARGET/STOP/HORIZON |
|---|---|---|---|---|
| TRAIN | 2,257 | **11.877104777925545** | 15.169398 | 1,635 / 430 / 192 |
| HOLDOUT | 2,006 | **11.928115221505827** | 13.686005 | 1,287 / 485 / 234 |
| FULL | **4,263** | **11.901108284803811** | 14.471371 | 2,922 / 915 / 426 |

Verdict PERSISTENT_NET_POSITIVE reproduces. Zero ambiguous rows — the conservative same-bar rule
is inert in this cell, so +11.901 does not rest on ambiguity resolution. The 0.25D denominator
amplifies cost 4× (family mean cost 0.6426 R → 2.5703 in cell units) and the cell still clears it;
the gross−net gap reproduces the family census `cost_mean_r` exactly.

### FB2 — OB-retest as-declared, 1.5D / 0.25D: +1.647 R over 1,340 rows — **VERIFIED (exact)**

`as_declared|target_1.5D|stop_0.25D` × `family:current_ob_retest`: FULL mean net
**1.6467194254150541**, n **1,340** (TRAIN 1.6308229668744396 / n 799; HOLDOUT 1.6701968198216184
/ n 541; outcomes 707/549/84; zero ambiguous). Δ = 0.0 everywhere. Verdict
PERSISTENT_NET_POSITIVE reproduces.

### FB3 — grid totals — **VERIFIED (exact)**

Recomputed directly from pool fields (net = Σ `opportunity_net_proxy_r`, cost = Σ `cost_r`,
gross = Σ(net+cost)) while streaming and counting rows:

| quantity | claimed | recomputed | Δ |
|---|---|---|---|
| january_rows | 27,658 | 27,658 | 0 |
| net R | −24,357.1989144 | −24,357.1989144 | 0.0 |
| gross R | −6,015.50302925635 | −6,015.50302925635 | 0.0 |
| cost R | 18,341.69588514365 | 18,341.69588514365 | 0.0 |

21 UTC trading days; 13 TRAIN / 8 HOLDOUT dates reproduce the receipt's split exactly.

### FB4 — max-T p = 0.001 for the survivors — **VERIFIED (exact, scope-bounded)**

Re-ran FB's declared procedure end-to-end on **my own** recomputed per-row net vectors
(numpy 2.4.4, `default_rng(20260801)`, 999 draws, joint family|direction labels permuted within
each sorted UTC TRAIN day, one-sided fixed-leader lift vs same-cell full-pool TRAIN baseline):

- **Candidate set**: re-derived from my own leader table under the declared rule → exactly the
  same 11 leader_ids and cells. None missing, none extra.
- **Observed lifts**: all 11 match at Δ = 0.0 (survivors: 12.6184 / 12.7418 / 12.4994 breaker-
  inverted; 3.7167 / 3.9181 / 3.4879 OB-retest).
- **Null distribution**: bit-identical — max 1.9496112754930073, mean 1.0915398318898366,
  sd 0.24139016472957842, q95 1.4954002165011033, min 0.34357047067932844.
- **p-values**: all 11 identical (0.001 × 6 survivors; 1.0 / 1.0 / 1.0 / 0.995 / 0.998 for the
  non-survivors). p = 0.001 is the resolution floor 1/(999+1) with zero null exceedances; the
  smallest survivor lift (3.4879) is 1.79× the largest null max-T ever drawn.
- **Receipt-internal arithmetic**: for all 11, baseline == cell-table full-pool TRAIN mean,
  population mean == cell-table population TRAIN mean, lift == their difference (1e-12).

Scope: this confirms FB's **arithmetic and procedure execution**, not the null **design**'s
validity — the clean-room lane owns that. Exact p equality relies on same-machine numpy 2.4.4;
a different numpy could give a statistically equivalent, non-bit-identical null (survivor
verdicts are robust to that).

### FB5 — "7 further families gross-positive but cost-killed" — **VERIFIED**

- Recount from `FAMILY_CLASSIFICATION.json`: family-level GROSS_POSITIVE_COST_KILLED = **7**
  (cross_asset_lead_lag, current_fvg_fill, displacement_continuation, liquidity_sweep_reclaim,
  session_open_range_break, structural_distance_extreme, volatility_compression_expansion).
- Independently **re-derived all 30 population classifications** from my raw-recomputed leader
  splits under the declared precedence: zero mismatches (so the 20-strata figure incl.
  family_direction also reproduces).
- Spot-verified from the pool+sidecar (leader gross > 0 on BOTH TRAIN and HOLDOUT while net ≤ 0
  on both — the classification's exact meaning):

| family | leader cell | gross T/H | net T/H |
|---|---|---|---|
| cross_asset_lead_lag | `inverted\|target_4D\|stop_4D` | +0.0911 / +0.0436 | −0.1337 / −0.1240 |
| current_fvg_fill | `as_declared\|target_2.5D\|stop_4D` | +0.1948 / +0.1218 | −0.0852 / −0.0760 |
| liquidity_sweep_reclaim | `as_declared\|target_2.5D\|stop_4D` | +0.0710 / +0.0644 | −0.0871 / −0.0493 |

## Verification depth beyond the five claims

- **Full 198-cell sweep** vs `GRID_FULL_RESULTS.json`: 32,076 float values compared across
  198 cells × (26 eligible populations + full_pool) × 3 splits — **max |deviation| = 0.0**;
  zero n / outcome-count / ambiguous-count mismatches; zero verdict mismatches across all 5,148
  population-cell evaluations.
- **All 52 TRAIN-selected orientation leaders** re-derived with the declared tie-breaks: zero
  mismatches.
- **Tick priority** reproduces per symbol: EURUSD 808/0, USDJPY 893/0, XAGUSD 921/7 fallback,
  XAUUSD 2,356/0 → 4,978 ORDERED_TICK + 22,680 M1_CONSERVATIVE.
- **Null-clean repairs (6)**: TRAIN/HOLDOUT/FULL net > 0 and recomputed p ≤ 0.05 all hold.

## Findings

1. **No refutations.** Session FB's grid receipts reproduce bit-identically from raw evidence.
2. FB4's p=0.001 is the floor value with zero exceedances (arithmetic confirmed; null design out
   of scope here).
3. Corroborating: both repair-candidate cells carry zero ambiguous rows and clear a 4×-amplified
   cost term.
4. Determinism caveat on exact-p reproduction (numpy version), stated above.
