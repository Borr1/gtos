# Lane 6 Priority-620 Triage

Generated: 2026-05-03T00:54:57.914262+00:00
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Question Registered Before Output

Most priority-620 Lane 6 tasks will classify as feed/source blocked, risk-approval deferred, or already closed by H-PM/S79/J46 evidence; only feed-feasibility items with local normalized data should move to DONE.

## Local Evidence Inventory

- FRED normalized series: `DFII10, DGS10, DGS2, DTWEXBGS, GVZCLS, T10YIE, VIXCLS`.
- FlashAlpha GEX proxy rows: `15` across `15` files.
- CFTC COT latest rows: `195`; symbols: `{'XAUUSD': 195}`.
- LBMA calendar latest rows: `444`; symbols: `{'XAGUSD': 148, 'XAUUSD': 296}`.
- Inverted-TP log rows: `66`.
- H-PM01 portfolio delta mean R: `-0.004960547358764833`, DSR-p: `0.9999646857030353`.
- H-PM03 side-aware H2 P(pass): `0.7806666666666666`; full P(bust HARD): `0.022`.
- K54 v3 feature-stability mean Jaccard: `0.1685447455309013`.

## Classification Matrix

| ID | Status | Blocked By | Evidence / Note |
| --- | --- | --- | --- |
| A-1 | DEFERRED_WITH_TRIGGER | Local FlashAlpha GEX proxy exists but only forward/current snapshots are cached; no legal historical gamma-sign series is available for NAS/US30 cross-period sign-flip validation. | FlashAlpha GEX inventory has 15 local rows; treat gamma sign as forward proxy only until >=30 trading days of snapshots or legal historical CBOE/GEX data exists. |
| A-4 | BLOCKED_WITH_REASON | A-1 is forward-only and A-2/A-3 are blocked; same-cohort K54/K55 retraining is closed until cohort/source-quality triggers. | NAS_US30 specialist retrain cannot verify gamma/VRP sign-flip cure without A-1/A-2/A-3 features and an approved retraining trigger. |
| A-5 | BLOCKED_WITH_REASON | No local Japan/UK rate-differential, carry-unwind, or BIS/Aquilina source is cached for JPY-pair factor decomposition. | Local FRED/DXY/VIX partial macro cache is insufficient for Lustig-Roussanov-Verdelhan JPY carry factor decomposition. |
| A-6 | BLOCKED_WITH_REASON | No local BoE policy, GBP political-risk, or registered legal proxy feed exists. | GBP-pair specialist feature construction is source-blocked, not an ML architecture task. |
| A-7 | BLOCKED_WITH_REASON | FRED has partial USD macro series but no Treasury-basis/intermediary-capital source or Fed-funds feature contract is registered. | Available FRED series are ['DFII10', 'DGS10', 'DGS2', 'DTWEXBGS', 'GVZCLS', 'T10YIE', 'VIXCLS']; this is insufficient for the full dollar-specialist feature set. |
| A-9 | DONE | - | Gold COT feed feasibility is satisfied for XAUUSD: latest CFTC normalized cache has 195 rows and fields for managed-money/commercial-style positioning. Alpha validation remains separate. |
| A-11 | DONE | - | LBMA fix-calendar feature feasibility is satisfied for metals: latest normalized calendar has 444 rows. This is not an alpha validation. |
| A-12 | BLOCKED_WITH_REASON | No Krohn-Mueller-Whelan FX-fix source/cache exists locally; D-5 remains blocked for FX-fix scope. | LBMA calendar readiness does not supply the KMW top-9-currency FX-fix W-shape dataset. |
| A-13 | BLOCKED_WITH_REASON | VIXCLS and Treasury yields exist, but TED/funding-liquidity/intermediary-capital source contract is incomplete. | FRED cache includes VIXCLS=True and DGS10/DGS2=True, but not a complete funding-liquidity factor. |
| A-14 | BLOCKED_WITH_REASON | No BIS JPY carry-unwind table/cache/source spec exists locally. | Aquilina-style JPY carry-unwind classifier is source-blocked until BIS data is registered and cached. |
| A-16 | FILED_FOR_APPROVAL | Replacing the live cross-instrument correlation gate would alter risk behavior and needs CEO approval; research-only prototype can be scoped separately. | Static triage files DCC/cDCC/Block-DECO as an approval-gated risk-model replacement, not an unblocked live-code change. |
| B-2 | DEFERRED_WITH_TRIGGER | Portfolio-wide vol conditioning failed; NAS100-only subcandidate needs shadow/approval trigger before Component 3C work. | H-PM01 portfolio delta mean R=-0.004960547358764833 with DSR-p=0.9999646857030353; NAS100-only remains a future shadow candidate. |
| B-3 | DEFERRED_WITH_TRIGGER | Risk-policy replacement must be simulated over DSR-surviving J46-J49/S79 baselines and needs live-risk approval; current full-stack MC supports shipped stack, not replacement. | Combined MC full stack has realistic-density P(pass)=0.8126 and P(bust HARD)=0.0006; no replacement policy is validated. |
| B-4 | BLOCKED_WITH_REASON | Asset-specialist bundle depends on blocked/deferred A-1/A-2/A-3/A-4/A-5/A-6/A-7/A-8; A-9/A-11 are feed-feasibility only. | The bundle cannot be treated as complete because most constituent specialist features lack source-complete as-of data. |
| B-7 | BLOCKED_WITH_REASON | Edge-mechanism bundle has E-1 failed, E-2 deferred, E-4 blocked, and E-3 blocked below. | No bundle-level edge-mechanism validation can proceed from current local data. |
| C-3 | BLOCKED_WITH_REASON | Inverted-TP log has correction records but no symbol/outcome linkage, so Walasek lambda-context dependence cannot be measured from current data. | knowledge_base/inverted_tp_log.jsonl has 66 rows; keys lack realized-R/outcome and symbol is missing in current rows. |
| C-4 | DONE | - | Daniel-Moskowitz-style LONG modifier simulation is closed by H-PM03/combined MC: side_aware_everywhere H2 P(pass)=0.7806666666666666 and full P(bust HARD)=0.022. |
| C-5 | DEFERRED_WITH_TRIGGER | K54/K55 same-cohort training is closed after v3/v4 failures; reopen only with n>=5000 or source-quality/cohort-expansion trigger. | Sharpe-objective training is a future K-family loss-function study, not an unblocked current-cohort task. |
| C-6 | DEFERRED_WITH_TRIGGER | Continuous-sized entries require actual broker-R/fill truth, lifecycle telemetry, and live-risk approval before system-flow use. | Existing MC covers fixed policy overlays; continuous sizing remains future research after label-truth blockers clear. |
| C-8 | BLOCKED_WITH_REASON | Feature-stability artifacts exist, but there is no K54 production deployment performance series because K54 is not deployed. | K54 v3 mean Jaccard=0.1685447455309013 with stable features=2; deployment-performance regression awaits K55 shadow/live rows. |
| E-3 | BLOCKED_WITH_REASON | Lillo-Mike-Farmer-Sato meta-order long-memory needs signed order-flow/meta-order aggregates; local OHLCV/H1 bars and MT5 tick volume are not a parent-order flow substrate. | Do not substitute candle direction or retail tick volume for signed meta-order flow. |
| E-5 | DONE | - | Uncorrelated-edge discovery inventory is current via NA-11 plus queue state: empirical alpha correlation is low, but live candidates remain discovery/forward-shadow only. |
| R-1 | DEFERRED_WITH_TRIGGER | Risk-constrained Kelly replacement needs a preregistered simulation over DSR-surviving J46-J49/S79 baselines and CEO approval before risk behavior changes. | Current evidence supports shipped S79/full-stack risk, not replacing it with RCK. |
| R-2 | DEFERRED_WITH_TRIGGER | Lambda auto-calibration depends on R-1 and owner-approved risk replacement path. | No lambda knob is approved or validated for FN constraint auto-calibration. |
| R-5 | DEFERRED_WITH_TRIGGER | Per-instrument weights require the R-1 simulation path and source-flagged all-symbol cohort; do not override S79 uniform profile from current evidence. | Existing S79/full-stack evidence remains the active baseline; per-instrument optimized weights are future research. |
| R-6 | DONE | - | Side-aware sizing is closed by H-PM03/combined MC and existing config flip: side_aware_everywhere full P(bust HARD)=0.022. |
| R-7 | REJECTED_FAILED | - | All-7 vol-scaled sizing failed portfolio-wide in H-PM01: delta mean R=-0.004960547358764833, DSR-p=0.9999646857030353; NAS100-only remains separate deferred/shadow candidate. |
| R-8 | DONE | - | Lambda-context audit is resolved at control level: live risk assumptions are fixed-profile S79/side-aware scalars, while any lambda-knob replacement is deferred under R-1/R-2. |
| R-9 | DEFERRED_WITH_TRIGGER | Bundle depends on deferred R-1/R-2/R-5 and rejected R-7; only R-6 is done. | Risk-policy bundle cannot replace S79/full-stack from current evidence. |

## NO_PROMOTION_VERDICT

This triage does not validate or promote a trading rule, live filter, risk setting, or execution change. It only classifies which priority-620 Lane 6 tasks are locally executable, blocked, deferred, rejected, or already closed by committed research artifacts.
