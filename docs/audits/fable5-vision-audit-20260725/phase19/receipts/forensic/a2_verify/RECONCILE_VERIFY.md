# A2 RECONCILE lane — claim-by-claim verification table

Lane: RECONCILE. Date: 2026-08-03. Full register resolution: `RECONCILE_A_Q.md` / `.json`.
**February reads are attribution-only under owner_mandate_20260801**; March and live-forward
(2026-07-29+) outcomes untouched. Everything recomputed from RAW inputs — compact pools
(streamed), raw TRADE/ORDER ledgers, the full 153,425-row Jan MISSED ledger (streamed), the CQ
sidecar (streamed), lane trade tables. Sol/FA receipts were treated as claims, never as evidence.

Verdicts: **28 VERIFIED, 4 REFUTED, 1 NOT_RECOMPUTABLE** (33 claims).

| # | claim (register/receipt) | recomputed (raw) | verdict |
|---|---|---|---|
| A-jan-janrule | Jan/Jan-rule: dir 17/−18.325, exit 11/−9.941, horizon 4/−1.382, winners 6+17 | 17/−18.3247, 11/−9.9410, 4/−1.3825, 6/+11.9111, 17/+12.2308, unscoreable 2 | VERIFIED (exact, 4dp) |
| A-jan-februle | Jan/Feb-rule: dir 11/−9.697, exit 21/−19.951 | 11/−9.6973, 21/−19.9509, target 6/+11.9111, other 17/+12.2308 | VERIFIED |
| A-feb-februle | Feb/Feb-rule: dir 10/−9.594, exit 23/−13.965, cost_dom 1/−0.017 | 10/−9.5935, 23/−13.9654, 1/−0.0173, target 2/+3.8567, other 22/+15.7581 | VERIFIED |
| A-sums | both tables sum to −5.506 / −3.961 | both rules, both months: −5.50620829 / −3.96139869 exactly | VERIFIED (8dp) |
| B-breaker | breaker n=9 vs n=8, same +4.356 | 9 rows / 8 scoreable / +4.35575072; 9th is the unscoreable USOIL_cash trade | VERIFIED (both counts true, different denominators) |
| C-authority-411 | authority_session n=411 +12.75 | 411 / +12.7494 (≡ route_session set, XOR 0) | VERIFIED |
| C-bucket-386 | session_bucket n=386 +21.99 | 386 / +21.9856 (strict subset of route-ny; the 25 excess rows carry −9.24 R) | VERIFIED |
| C-prose-mismatch | DECLINED_WINNERS prose ≠ its number | prose `(route OR bucket)` evaluates to exactly 411/+12.7494 — the number it reports | **REFUTED** |
| D-defA | n=4,509 −0.199 | 4,509 / −0.198588 | VERIFIED |
| D-defB | n=4,095 −0.213 | 4,095 scoreable (8,581 physical) / −0.212678 | VERIFIED |
| D-defC | 7,575/3,242 −0.205 | 7,575 physical / 3,242 scoreable / −0.204807 | VERIFIED |
| D-overlaps | A∩B 3,888; A\B 621; B\A 207 | same; plus C = 3,038 + 204; B = C + 853 effective-reject rows | VERIFIED |
| E-ranked | −0.213 ranked set | −0.212678 | VERIFIED |
| E-chosen-sets | −0.722 (register: "all-scoreable set") | −0.72247086 = executed trades' own same-timestamp set means; pool mean is −0.880657 (label wrong, value right); Feb −0.66506073 | VERIFIED (label corrected) |
| F-jan-78 | Jan pool 78 keys | 78, uniform on 27,658 rows | VERIFIED |
| F-feb-101 | Feb pool 101 keys | 101, uniform; superset of Jan +23 | VERIFIED |
| F-80 | "80 fields" (pool schema) | 80 = MISSED-ledger row width (uniform on all 153,425 rows); pools are 78/101 | **REFUTED** (origin identified) |
| F-47 | 47 enum subset | JAN_POOL_ENUMS scans exactly 47 of the 78 | VERIFIED |
| G-sidecar | 3,229,819 observations vs receipt 0 | 27,658 rows; Σ len(ordered_path_observations) = 3,229,819 | VERIFIED (0 = script bug, `verify_pool_crosschecks.py:129-132`, wrong key names) |
| H-totals | 7,706 / +6,447.2; no cross-walk | 7,706 / +6,447.2475; blocker partition cell-exact; cross-walk built | VERIFIED (+cross-walk delivered) |
| I-3536 | 3,536 rejects re-enter softened | 3,536 (3,526 → open-reduced-risk, 10 stay reject; 207 scoreable = 204+3); all router-refuse reason | VERIFIED |
| I-3281 | 3,281 non-scoreable delta | 128,293 − 125,012 = 3,281; all `source_or_signature_authority`, non-scoreable side; scoreable 20,448 == 20,448 | VERIFIED (carrier identified) |
| J-jan | 61→57, 4 unfilled/expired (unverified) | 61 accepted + 57 filled + 4 expired; accepted−filled == expired **exactly**, key-level | VERIFIED (now row-level) |
| J-feb | 66→58, 8 "unfilled/expired" | 66 accepted + 58 filled + **7 expired + 1 cancelled_replaced_by_scheduler_v4** (XAUUSD SHORT 02-18 15:15Z) | **REFUTED** (7/8 expiry; 1 cancel-replace) |
| K-flag | final_selection_claim False on ALL rows | false on 2,016 + 69,792 + 1,920 + 62,328 rows; zero true; absent from pools | VERIFIED |
| L-close-reasons | 2,811 / 11,499 | `opportunity_close_reason`: 2,811 target_reached / 11,499 stop_reached | VERIFIED |
| L-binary | binary_population 950/3,660 | fixed-2.0 @ 1e−9 on net+cost: 950/3,660 exact (own-target 953); native-gross binary population 2,880/12,192 | VERIFIED (definition pinned) |
| M-1e9 | 678/3,270 exact-1e−9 | fixed-2.0 @ 1e−9: 678/3,270; own-target: 682/3,270 | VERIFIED (fixed-2.0 basis identified) |
| M-1e6 | 3,072/15,057 1e−6-near | own-target @ 1e−6: 3,072/15,057 | VERIFIED |
| N-distinct | 1,231 / 988 distinct | 1,231 / 988 | VERIFIED |
| N-2.0-count | 2.0 on 26,427/27,658 | **26,428**/27,658 (26,427 is inconsistent with 1,231 distinct) | **REFUTED** (off by one) |
| O-file | cited ECONOMICS.json does not exist | it EXISTS (186 MB, born 2026-08-01 01:45) — git-untracked; named real receipts also exist | **REFUTED** (as filesystem claim) |
| P-joins | ~5,778 mis-joined rows; tuple key unique | 5,778 = 27,658 − 21,880 distinct ids (excess rows); 6,745 rows in multi-id groups; 0 tuple duplicates | VERIFIED (both quantifications pinned) |
| Q-meta | no Phase-1 output truncated | not recomputable from pools; ~40 tested quantities reconciled | NOT_RECOMPUTABLE |

Computation receipts: `POOLS_PASS_RESULT.json` (pools + sidecar + lane joins),
`TRADES_ORDERS_RESULT.json` (both rules × both months, movement cross-tabs, breaker, orders),
`MISSED_LEDGER_RESULT.json` (physical-side funnel counts, 80-key uniformity). Scripts:
`reconcile_pools_pass.py`, `reconcile_trades_orders.py`, `reconcile_missed_ledger_pass.py`,
`reconcile_followups.py`.
