# April + May 2026 read — REJECT (frozen prereg V1.6, executed 2026-08-11)

**Decision: REJECT** — gate 2 (pooled worst-case strictly positive) failed: pooled actual
**−2.612 R** (worst-case −3.685) on 67 selected / 66 resolved across 43 days. Gates 1 and 3
passed (66 ≥ 40 resolved; 17 positive vs 11 negative active days).

| window | trades | actual net R |
|---|---:|---:|
| April 2026 | 50 | **−7.742** |
| May 2026 | 17 | **+5.130** |

Comparators (same universe, reported not used): naive mixed **−9.212** on 317; rerank −2.971
on 80 — the abstain discipline outperformed the naive expression by +6.6 R even in the losing
window, consistent with February (+14.17 vs −4.74). Outcome mix: 4 TARGET / 23 STOP /
39 TIME_STOP / 1 CENSORED — April was a near-zero-completion regime for this rule.
Dispositions: 2,712 windows top-below-0.1R, 718 LIMIT-top abstentions, 67 trades.
Family robustness: `FAMILY_SPECIFIC_EDGE:liquidity_sweep_reclaim` (+1.007, the only positive
family) — February's concentration flag pointed exactly here.

**Standing after this read:** one PASS (February +14.168, n=106) + one REJECT (April+May
−2.612, n=67); three-month pooled +11.556 R over 63 trading days. The rule as frozen is NOT
deployable; no arming proposal exists. April and May 2026 are now opened development data for
this pipeline. The read chain V1→V1.6 amendments were all execution-layer (calendar handling,
scorer guard staging), receipted in each prereg version; the verdict computation ran once, on
the V1.6-frozen bytes.

Result: `APRIL_MAY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json` (payload `d45c824f…`).
