# Lane 6 Asset / Risk / Edge Triage

Date: 2026-05-03
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Question

Classify first Lane 6 asset/risk/volatility/edge items from local evidence.

## Evidence Summary

- Realized-vol rank tooling exists in H-PM01/H-PM03/NA8: `True` / `True` / `True`.
- H-PM01 portfolio-wide result failed: delta mean R `-0.004960547358764833`, DSR-p `0.9999646857030353`.
- Regime persistence feature names present: `10`; regime shadow rows `745`.
- FRED series available: `['DFII10', 'DGS10', 'DGS2', 'DTWEXBGS', 'GVZCLS', 'T10YIE', 'VIXCLS']`; real-gold deflator present `False`.
- Vol terms present: `{'VIXCLS': True, 'GVZCLS': True, 'VIX1D': False, 'VIX9D': False, 'VVIX': False, 'VRP': False}`.
- K54 Osler/K-7 proxy in train code `True`; K-7..K-10 marginal AUC lift `0.003457028435499998`.
- Tick substrate: max symbol days `5`, symbols with ticks `7`, XAU/FX LOB cache `False`.
- Production XAU+FX trade records with parameters `197` of `200`; TP round-hit proxy `0.03553299492385787`. These are GTOS levels, not counterparty stop observations.

## Task Classifications

| id | status | blocker / trigger | candidate strength |
| --- | --- | --- | --- |
| V-1 | DONE | none Trigger: No trigger; feature/tooling exists. Component 3C sizing integration remains separate V-9/P-1 work. | not_strategy_comparable_feature_done; portfolio-wide H-PM01 failed |
| V-2 | BLOCKED_WITH_REASON | No local VRP, VIX futures, implied-variance term-structure, or registered realized-vol estimator source exists; VIXCLS/GVZCLS alone do not define VRP. Trigger: Create a no-leak VRP construction spec with as-of implied-vol/variance source and realized-vol estimator, then build the point-in-time cache. | not_applicable_feature_feasibility |
| V-3 | DONE | none Trigger: No trigger; K54 regime feature family already contains run-length, flip-window, and score-dynamics persistence features. | not_strategy_comparable_feature_done |
| A-8 | BLOCKED_WITH_REASON | Local feeds have XAUUSD nominal bars plus FRED real-rate/inflation-expectation proxies, but no CPI/PCE deflator or pre-registered real-gold-price percentile construction. Trigger: Add a legal CPI/PCE deflator source with publication-time metadata and register the real-gold-price percentile lookback before feature construction. | not_applicable_feature_feasibility |
| C-2 | BLOCKED_WITH_REASON | GTOS does not observe counterparty stop placements, broker client positioning, or IG/OANDA-style client-sentiment locally; production trade records contain our proposed levels only. Trigger: Register a legal counterparty/retail-positioning proxy or order-book stop-density source before building disposition-effect features. | not_applicable_unobserved_counterparty_data |
| E-1 | REJECTED_FAILED | The K54 v3 Osler round-level stop-cluster proxy was implemented as K-7 and contributed only below-noise lift; production trade history records proposed GTOS levels, not counterparty stop clusters. Trigger: Reopen only with direct stop-cluster/counterparty data or a feature-specific preregistered cohort that clears the methodology gate. | rejected_below_noise_proxy |
| E-2 | DEFERRED_WITH_TRIGGER | Current all-symbol MT5 tick coverage is short and quote-only; the Toth-Bouchaud latent-liquidity shape needs mature tick/depth/order-flow evidence, not just recent bid/ask quote ticks. Trigger: Reopen after >=30 trading days all-symbol ticks or an approved depth/order-flow feed, with a preregistered V-shape estimator. | deferred_substrate_maturity |
| E-4 | BLOCKED_WITH_REASON | F11/OB-decay artifacts exist, but no retail-flow-share proxy, broker client-sentiment cache, Google Trends cache, or social-flow dataset is available locally. Trigger: Add a legal retail-flow-share proxy with time coverage aligned to F11 windows, then preregister the decay regression. | not_applicable_missing_retail_flow_proxy |

## Interpretation

- `V-1` and `V-3` are feature/tooling-complete, but this does not revive the portfolio-wide Component 3C overlay; that remains deferred under P-1/V-9.
- `V-2` and `A-8` are source/construction blocked, not coding tasks.
- `E-1` closes only the current Osler proxy path; it does not prove that counterparty stop clustering is false.
- `C-2`, `E-2`, and `E-4` need external counterparty/retail/depth evidence before validation claims are meaningful.

## Source Files

- `research/ml_program/MASTER_BACKLOG.md`
- `research/ml_program/phase_2/position_mgmt/h_pm01_vol_conditional_sizing.md`
- `research/ml_program/phase_2/position_mgmt/h_pm01_per_cohort_results.json`
- `research/ml_program/phase_2/position_mgmt/_compute_h_pm03.py`
- `research/ml_program/feature_catalogs/volatility.md`
- `research/ml_program/feature_catalogs/regime.md`
- `research/ml_program/audit/LANE5_K54_ARCHITECTURE_TRIAGE_2026-05-03.md`
- `research/operations/LANE4_OPTIONS_GAMMA_PROXY_TRIAGE_2026-05-03.md`
- `research/academic_pipeline/results/Q-crowding_retail.md`
- `data/external/normalized/`
- `knowledge_base/trade_records/`
- `.context/05_operations/WEEKEND_RESEARCH_GOAL_PROMPT_2026-05-03.md`

## NO_PROMOTION_VERDICT

This artifact classifies readiness only. It does not validate, promote, or modify live trading behavior.
