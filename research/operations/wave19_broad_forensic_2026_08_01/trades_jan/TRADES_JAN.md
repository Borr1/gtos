# January executed-trade walk — CJ_RECLOCKED_S0R0_V7 (Session FA, wave-19 forensic)

Date: 2026-08-01. Walker for the owner's question: *"see what lost exactly and why it lost what it lost."*
All numbers computed directly from the raw ledgers (paths in §7); scripts in this directory are the receipts.

## 0. The one-paragraph answer

The 57 executed January trades realized **−5.50620829 R net** (physical basis; −$550.62 at the fixed
$100/0.1 % S0R0 risk unit), which reconciles exactly with the arm SUMMARY (`physical_net_r`,
`physical_cash_pnl`). Gross was only **−1.221 R**; **execution cost charged into net was −4.285 R**
(78 % of the realized loss). The loss is NOT one bad mechanism everywhere: 23 trades won (+24.14 R),
17 trades were simply wrong-way (−18.32 R), and **11 trades were RIGHT — up ≥ +0.5 R in-path — and the
exit machinery gave it all back (−9.94 R net, 18.56 R of peak-to-close giveback)**. The family that lost
the money in the executed book is **current_fvg_fill (21 trades, −12.26 R, 4 winners)**; CK's toxic pool
family `current_breaker_re_entry` was 9/57 = 15.8 % of the executed book and actually made **+4.36 R**.
The famous "21/21 negative days" is a *pool* metric (diagnostic net proxy summed over the 27,658 scoreable
missed candidates per day) — the executed book itself was positive on 8 of its 19 trade-days.

## 1. Contract of the executed trade (what a trade IS here)

- Fixed −1 R stop, +2.0 R policy target (`policy_target_r` = `raw_target_r` = 2.0 on every row),
  120-minute maximum horizon: max holding = 120.0 min exactly; median 72.1 min; closes at
  `path_end_mark_to_market` when neither side resolves. All 57 trades at `approved_risk_pct` 0.1,
  `risk_cash` $100 (S0R0 neutral sizing confirmed — zero deviations).
- Entry is an immediate-marketable limit at decision (`order_execution_path =
  'immediate_marketable_limit_at_decision'`), exits replayed on ordered tick truth where available
  (39 trades) or M1 proxy (15) — see §5.

## 2. Reconciliation (exact)

| quantity | walked from 57 TRADE rows | arm SUMMARY (`split_profile_stats[0]`) |
|---|---|---|
| net R (physical) | **−5.50620829** | `physical_net_r` −5.50620829 |
| gross R | −1.2209298 | `physical_gross_r` −1.2209298 |
| cost R, all 57 | 4.44958678 | `physical_expected_cost_r` 4.44958678 |
| cost R, 55 scoreable | 4.28527849 | `physical_scoreable_expected_cost_r` 4.28527849 |
| cash P&L | −550.62 | `physical_cash_pnl` −550.620829 |
| headline subset (39) | −9.52575822 | `headline_net_r` −9.52575822 |
| wins / losses | 23 / 32 | `physical_win_count` 23 / `physical_loss_count` 32 |

Identity: net = gross − scoreable cost (−1.2209 − 4.2853 = −5.5062). The two unscoreable trades
(gross/net = None) carry 0.16431 R of cost that appears in `physical_expected_cost_r` but never in net.
Lane trade table: 57/57 rows identity-match on net_r/final_r/cost_r/close_reason/risk (0 mismatches).

**122 orders : 57 trades.** `order_status` = 61 `pending_accepted` + 57 `filled` + 4 `expired_unfilled`.
The ledger writes one row at order acceptance and one at terminal resolution: 61 accepted orders → 57
filled (the trades) + 4 expired unfilled = 122 rows. No cancels, no partial fills
(`cancel_replace_event_count` 0). The ORDERED_PATH_ORACLE ledger has exactly 61 rows = the 61 accepted
orders; 56 match trades on (candidate_id, asof); 4 are the expired-unfilled candidates; 1 executed trade
(`broadorigin_4acedf6e…`, the guarded-market-fallback fill) is re-keyed in the oracle at its fallback
elapsed time (asof 10:00:00.206 vs decision 09:30:00).

## 3. Where the −5.506 R sits (per-trade loss attribution)

Class rule (precedence): unscoreable → winner → cost_dominated (gross ≥ 0 but net < 0, or |gross| ≤ cost)
→ exit_geometry (loss with in-path MFE ≥ +0.5 R) → direction_wrong (stop-class close or MAE ≤ −0.9 with
MFE < 0.5) → horizon_marked → other.

| class | n | net R sum | reading |
|---|---:|---:|---|
| winner_target | 6 | +11.911 | full-target (or target-before-stop) wins |
| winner_other | 17 | +12.231 | giveback-close / mark-to-market / time-stop wins |
| direction_wrong | 17 | **−18.325** | wrong-way from entry; 16 straight stops + 1 deep-MAE mark |
| exit_geometry | 11 | **−9.941** | MFE ≥ +0.5 R first, then gave it ALL back (8 rode to the full −1 R stop) |
| horizon_marked | 4 | −1.382 | drifted small-negative into the 120-min mark |
| cost_dominated | 0 | 0 | **no single trade was sign-flipped by cost** |
| unscoreable | 2 | 0.000 | terminal R never scoreable (ordered-tick sequence required, absent) |
| **total** | 57 | **−5.506** | |

**Cost is a book-level, not trade-level, killer**: no individual trade flipped sign on cost, but the book
paid 4.45 R of cost against |gross| of 1.22 R. Components: spread 2.111, flat modeled slippage 1.140
(exactly 0.02 × 57 — a constant, not a measurement), commission 0.563, swap 0.161, **fill-geometry cost
rebase +0.425** (`marketable_limit_cost_r_rebased_to_effective_fill_geometry`: the cost packet is scaled
by up to 2.0× when the marketable fill tightens effective stop geometry; largest multiplier seen 1.842),
guarded-fallback surcharge 0.050.

**The exit-geometry story is the actionable one.** 35 of 57 trades reached MFE ≥ +0.5 R and 19 reached
≥ +1.0 R inside the 120-min horizon (median MFE +0.77 R against median MAE −0.94 R). The 11
exit_geometry losers alone gave back 18.56 R peak-to-close. Oracle upper bound: exiting every trade at
its MFE (net of cost) is +48.13 R — not a strategy, but it bounds how much path opportunity the 2.0 R
fixed-target + giveback policy leaves on the table. First-touch inside horizon: stop 26, target 8,
neither 23 — at this geometry the stop is touched 3.3× as often as the target, so the 2 R target is
rarely collected (6 target-class wins) while the giveback/mark exits harvest the rest.

## 4. What the executed book actually bought

By origin_family (n, net R, winners):

| family | n | net R | winners |
|---|---:|---:|---:|
| current_fvg_fill | 21 | **−12.264** | 4 |
| session_open_range_break | 20 | −1.097 | 10 |
| structural_distance_extreme | 7 | +3.499 | 4 |
| current_breaker_re_entry | 9 | **+4.356** | 5 |

**CK's pool-toxic `current_breaker_re_entry` is 15.8 % of the executed book (9/57) and was POSITIVE
(+4.36 R) in execution.** The executed book's toxin is `current_fvg_fill`: it alone lost 2.2× the whole
book's net loss. Other cuts: symbols — XAUUSD 24 trades −8.01, XAGUSD 8 trades −6.10 (metals = 32/57
trades and −14.11 R) vs UKOIL_cash +8.74 (8) and USDJPY +2.45 (7); direction — SHORT 28 trades −10.39
vs LONG 29 +4.89; session — ny 23 trades −6.05, london 28 +2.53, tokyo 3 +1.31.

## 5. Headline vs physical (two nets, both real)

- 39 headline-eligible trades: **−9.526 R** (`headline_result_eligible`, ordered-tick truth).
- 18 diagnostic-only scoreable trades (15 M1-proxy + 1 guarded-fallback + 2 of the same set): **+4.020 R**
  (`diagnostic_only_net_r` 4.01954993 in SUMMARY — matches).
- 2 unscoreable (USOIL_cash `broadorigin_93c40b…`, US30_cash `broadorigin_b3f78f…`): no terminal R.

The tick-truth subset is materially WORSE than the physical book (−9.53 vs −5.51): the M1-proxy trades
skew positive. Any claim built on the physical −5.506 should disclose that the headline-grade subset
is −9.526 on 39 trades.

## 6. "21/21 negative days" — what a negative day means

Verified from the compact pool (27,658 rows streamed): 21 scoreable days, **21/21 negative** on the pool
metric = sum of `opportunity_net_proxy_r` over that day's diagnostic-scoreable missed candidates
(pool total −24,357.199 R; matches receipt). This metric contains **zero executed trades** — it is the
counterfactual cost-loaded net of the ~1,300 missed candidates/day (mean −0.881/row), so a day is
"negative" almost by construction under the S0R0 cost model. The executed book traded on **19 days**
(2026-01-12 and -14 had pool candidates but no fills) and its realized day series is positive on 8 of 19
(best +2.92 on 01-19; worst −3.74 on 01-22, the 9-trade cluster day). Day-level clustering exists:
01-22 had 9 trades (4 XAUUSD + 3 US30_cash), and 11 day×symbol pairs carry ≥2 trades.

## 7. Anomaly register

1. **Two unscoreable executed trades** (gross/net None; close_reason is the *scoreability status string*
   `entry_fill_executable_terminal_r_ordered_tick_sequence_required` leaked into `close_reason`); their
   0.164 R cost is in physical cost but outside net.
2. **Duplicate candidate_ids** (2): `broadorigin_bf030f05…` (XAGUSD, 09:00 then 13:15 on 01-02) and
   `broadorigin_7cf2b78b…` (US30_cash, 08:30 then 10:30 on 01-22). Same candidate re-fired at a later
   instance; identity is (candidate_id, decision_time_utc), not candidate_id alone.
3. **Zero-minute holding** (1): `broadorigin_eb0b3a35…` UKOIL_cash LONG 01-26 13:31 → 13:31,
   `stop_reached_before_target` on M1 proxy — entry and stop inside one M1 bar.
4. **Cost residual above the four components: +0.475 R over 18 trades** — explained, not a fault:
   fill-geometry cost rebase (multiplier ≤ 2.0, `limit_immediate_marketable_cost_r_rebase_multiplier`)
   plus the single 0.05 guarded-fallback surcharge.
5. **Flat modeled slippage** 0.02 R on all 57 trades (1.14 R total) — a constant, never symbol- or
   size-conditioned.
6. No cost_r > 1 trade, no entry price outside its own stop/target band (57/57 sane), no missing MFE/MAE,
   no duplicate (candidate_id, decision_time) pairs, no lane-table mismatches.
7. Oracle key re-stamp for the guarded-fallback trade (§2) — join on candidate_id alone if using the
   oracle ledger.

## 8. Sources

- TRADE/ORDER/ORACLE ledgers + SUMMARY: `/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse/CJ_RECLOCKED_S0R0_V7/` (read-only, in place)
- Lane trade table: `docs/audits/fable5-vision-audit-20260725/phase16/receipts/CJ_RECLOCKED_S0R0_V7_LANE/LANE_TRADE_TABLE.jsonl`
- Compact pool: `docs/audits/fable5-vision-audit-20260725/phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz` (streamed)
- Receipts here: `TRADES_JAN_TABLE.json` (per-trade table + order/oracle accounting),
  `TRADES_JAN_ATTRIBUTION.json` (classes, aggregations, day series, anomalies, extras),
  scripts `extract_trades_jan.py`, `attribute_trades_jan.py`, `finalize_jan_extras.py`.
