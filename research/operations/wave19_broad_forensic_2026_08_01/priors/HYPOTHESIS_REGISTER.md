# Session FA — hypothesis register (PRIORS-DIGEST)

Companion to `HYPOTHESIS_REGISTER.json` (the machine-readable authority; this file is the
readable index). Every prior claim below is a **hypothesis** for Session FA, per the owner's
2026-08-01 commission: *"anchor on the RAW artifacts, re-derive what you rely on."*

**Cross-check status: all KNOWN CROSS-CHECKS reconcile against the raw compact pools**, verified
by `verify_pool_crosschecks.py` → `POOL_CROSSCHECK_V1.json` in this directory (single streamed
pass per pool, no whole-file loads):

| measure | January (CJ re-clocked S0R0) | February (CP true-UTC S0R0) |
|---|---:|---:|
| scoreable rows | 27,658 | 24,239 |
| pool net sum | −24,357.19891 R | −15,513.47283 R |
| net mean /row | −0.88065655 | −0.64002116 |
| gross mean /row | −0.21749595 | −0.15055128 |
| cost mean /row | 0.66316060 | 0.48946988 |
| positive rows | 7,706 (0.278617) | 7,498 (0.309336) |
| negative days | 21/21 | 20/20 |
| binary endpoints (target/stop, exact 2R/−1R at 1e−9) | 678 / 3,270 (hit 0.171733) | 950 / 3,660 (hit 0.206074) |
| executed trades / realized net | 57 / −5.50620829 R | 58 / −3.96139869 R |
| broker_pretrade_cost_executable true/false | 7,210 / 20,448 | (in receipt) |
| breakeven precision | 0.648551 | 0.606359 |

CQ sidecar verified: 27,658 rows, **3,229,819** observations (3–120 per path), 4,985 tick-pointer
rows. **Join hazard:** `candidate_id` alone is NOT unique (21,880 distinct); the unique join key is
`(candidate_id, decision_time_utc, symbol, side)` — 27,658 unique, 0 dups.

## Register (one line per row; full text in the JSON)

| id | claim (short) | axis | status |
|---|---|---|---|
| H01 | Selection `inconclusive` −0.049138 licenses only "these two switches failed" (two bits) | wrong_selection | ALREADY_RAW |
| H02 | ±38,317 R separable bound → true-UTC replacement +6,447.25/−30,804.45; breakeven 0.648551 | ex_ante_separator | SUPERSEDED |
| H03 | AW 0/212 cells separate; Spearman 0.919; model ceiling AUC 0.712 | ex_ante_separator, wrong_selection | **RE_DERIVE** (clock + membership −3.10 %) |
| H04 | AW B_TIME 81(83) cells all negative | inaccurate_conditions | SUPERSEDED by `CP_TRUE_UTC_B_TIME_MAP_V1.json` (83 cells, all negative, best london −0.42799) |
| H05 | Not a cost problem: gross −0.2199, binary 16.9 % vs 33.3 % | wrong_mechanism | ALREADY_RAW (true-UTC: −0.21750; 678/3,270 → 0.1717) |
| H06 | confidence 0.55 on EVERY row, default applied on EVERY row; F38 commission=0 | wrong_selection | **RE_DERIVE** (trivial field scan; F38 half superseded) |
| H07 | Cost tail >1R = generator stop-geometry defect, ~50 % of loss | wrong_mechanism, inaccurate_conditions | ALREADY_RAW (true-UTC: 4,908 rows / 54.17 % / max 18.7758) |
| H08 | CD: repairs make family WORSE (−0.858→−0.882); only commission+swap reach replay | wrong_mechanism | ALREADY_RAW (CJ arm runs repairs-on) |
| H09 | Switches move trade set (63/55/61/54) not pool (0.0003 R/row) | wrong_selection | RE_DERIVE (only S0R0 exists at true UTC) |
| H10 | CJ: invariance FALSE — trades 63→57, realized +3.43505 R, mean +0.00158 | inaccurate_conditions | ALREADY_RAW (re-verified) |
| H11 | CK: breaker pocket −0.82755 gross over 15.19 %, 21.55 % of neg gross, p 0.000999 | wrong_mechanism, inaccurate_sleeve | **RE_DERIVE** (persistence/p not re-run at true UTC; CQ FULL −0.82544 corroborates) |
| H12 | CK: liq_sweep_reclaim×LONG gross-positive both splits | declined_winners | SUPERSEDED (CQ: TRAIN gross −0.00539, sign flips; cost-vetoed everywhere) |
| H13 | CK: first-touch ambiguity 0–11.91 % could explain the hole | wrong_mechanism | SUPERSEDED (CQ measured 0/27,658) |
| H14 | CK: 99-cell surface unidentifiable from committed pools | wrong_mechanism | SUPERSEDED (CQ path-complete 198-cell grid) |
| H15 | CQ: inverted breaker 5D/0.25D +11.88/+11.93 net R/trade; gate NOT_EVALUABLE (1 fold of 3) | wrong_mechanism, ex_ante_separator | ALREADY_RAW (CS owns folds 2–3) |
| H16 | CP: virgin February rejects broad V4 (0/20 days, precision 0.309 vs 0.606) | wrong_mechanism | ALREADY_RAW (re-verified raw) |
| H17 | CP factory: 1,092 looks → 1 TRAIN survivor (NY-metals-LONG); gate NOT_EVALUABLE | ex_ante_separator, declined_winners | ALREADY_RAW (CR owns capture) |
| H18 | THIRD_REVIEW §1.2 asymmetry: broad = negative, W7 = invalid; "unrepairable" = policy layers only | wrong_selection, wrong_mechanism | ALREADY_RAW |
| H19 | Sealed clock = broker wall +2 h mislabelled UTC | inaccurate_conditions | SUPERSEDED (CJ closed it: 54/54, 96/96, 778,162 rows) |
| H20 | AW alias groups (origin/route/framework = one partition; 8 more) | wrong_selection, ex_ante_separator | **RE_DERIVE** (partition-hash on the new pool) |
| H21 | CQ transform wired default-off, absent-false key; fidelity ceiling 95.808 % transferred | wrong_mechanism | ALREADY_RAW |
| H22 | AW estate spread-filter is per-sleeve, not estate-wide | inaccurate_conditions | ALREADY_RAW (out of FA scope; do not re-import as broad evidence) |
| H23 | CD repair queue: GENERATOR_STOP_GEOMETRY still OPEN; GROSS_DEFICIT → answered by CQ; clock → closed by CJ; live commission → CN seal break | wrong_mechanism, inaccurate_conditions | ALREADY_RAW |
| H24 | Family tip V27 = 59 declared / 57 looks, B_balanced α 0.10, all_declared | declined_winners, ex_ante_separator | ALREADY_RAW (verified by member count) |

## The re-derivation shortlist (what FA should actually recompute)

1. **H03 — the separability map at true UTC.** AW's 212-cell verdicts have never been recomputed
   on the −3.10 %-different population. Non-time axes are probably stable; that is a hypothesis,
   not a fact. Substrate: `CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz`; declared cut rules in
   `AW_MINE_PROTOCOL_V1.json`; register looks as FORENSIC_DIAGNOSTIC (see LEDGER_CONVENTION).
2. **H11 — breaker-pocket persistence at true UTC** (TRAIN/HOLDOUT + within-day max-T), because
   CQ's repair hypothesis rests on the pocket being real, and only its FULL mean is confirmed
   on the new clock.
3. **H06/H20 — degeneracy and alias census** on the new pool: cheap, structural, and it bounds
   how many honest looks any FA mining pass can even declare.
4. **H09 — factorial trade-set sensitivity** only if a specific FA hypothesis needs it (no
   true-UTC S1R0/S0R1/S1R1 arms exist; do not build them without a priced reason).

## Anomalies found while cross-checking (also in the structured output)

1. The commission's stated path `phase16/receipts/CJ_RECLOCKED_ARM_S0R0_V7_ECONOMICS.json` does
   not exist; the committed receipts are `CJ_RECLOCKED_ARM_S0R0_V7.json` (arm) and
   `CJ_CD_BASELINE_S0R0_ECONOMICS_V1.json` (CD baseline). Realized −5.50620829 R was verified
   from `CJ_RECLOCKED_S0R0_V7_LANE/LANE_TRADE_TABLE.jsonl` instead.
2. Sidecar `candidate_id` is non-unique (21,880/27,658) — composite key required (H14 note).
3. `CANDIDATE_FAMILY_V27.json.superseded_because` carries one parent's "57→58 / 55→56" prose
   while the members list is 59/57 — fork inheritance, counts verified by enumeration.
4. AW prose "81 cells" vs committed 83 (already flagged by CJ finding 5); AW's cost-tail 16.5 %
   was masked on `cost_r` while the note said `spread_r` (CD's correction) — both are reasons
   to quote the receipts, not the prose.
