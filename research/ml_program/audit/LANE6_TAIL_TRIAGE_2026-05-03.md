# Lane 6 Tail Triage

Generated: 2026-05-03T01:11:48.223255+00:00
Scope: research/tooling only
Promotion verdict: `NO_PROMOTION_VERDICT`

## Question Registered Before Output

The remaining Lane 6 tail batch should mostly resolve from existing H-PM/NA8/WGC/K54 evidence: broad vol-managed sizing should fail, side-aware and baseline-reconciliation items should close, bar-sampling/Hawkes tasks should be data-substrate blocked or deferred, and AI behavior changes should be approval-filed.

## Evidence Inventory

- H-PM01 portfolio delta mean R: `-0.004960547358764833`, DSR-p: `0.9999646857030353`.
- H-PM01 NAS100-only delta R: `0.09066365782920549`, DSR-p: `0.015223281554341606`.
- WGC demand rows: `9475`; central-bank-like rows: `162`.
- Tick parquet inventory: `{'files': 30, 'symbols': {'GBPJPY': 4, 'GBPUSD': 4, 'NAS100': 5, 'US30_cash': 5, 'USDJPY': 4, 'XAGUSD': 4, 'XAUUSD': 4}}`.
- Rough-Hurst symbols found: `['GBPJPY', 'GBPUSD', 'NAS100', 'US30', 'USDJPY', 'XAGUSD', 'XAUUSD']`; median H: `0.5050851741228051`.
- Tail-correlation diagnostic status: `ok`, pairs: `21`.
- AI tooling scaffold: `{'ai_tools_dir_exists': True, 'ai_tool_files': ['__init__.py', 'base.py', 'lookup_session_vol.py', 'query_recent_outcomes.py', 'registry.py'], 'tool_use_design_exists': True, 'primary_imports_ai_tools': False, 'orchestrator_imports_debate': False, 'debate_code_exists': True, 'debate_tests_exist': True}`.

## Rough-Vol Hurst Proxy

| symbol | n_close | n_log_rv | H | status |
| --- | --- | --- | --- | --- |
| XAUUSD | 13288 | 13272 | 0.49803817880030904 | ok |
| US30 | 13279 | 13263 | 0.6033981383377698 | ok |
| USDJPY | 14013 | 13997 | 0.49154746386531645 | ok |
| GBPJPY | 14009 | 13993 | 0.48422314477656087 | ok |
| GBPUSD | 14013 | 13997 | 0.5473090274426017 | ok |
| XAGUSD | 13282 | 13266 | 0.5050851741228051 | ok |
| NAS100 | 13284 | 13268 | 0.5634779669227271 | ok |

## Tail / Correlation Diagnostic

| pair | pearson | lower_tail_proxy | upper_tail_proxy | FR_adjusted_high_corr |
| --- | --- | --- | --- | --- |
| XAUUSD-XAGUSD | 0.7717260715323941 | 0.573394495412844 | 0.463302752293578 | 0.2965275503315908 |
| US30-NAS100 | 0.7522136404139618 | 0.5565749235474006 | 0.5703363914373089 | 0.32351335742755744 |
| USDJPY-GBPUSD | -0.5359876165571533 | 0.019877675840978593 | 0.009174311926605505 | -0.06762566854669513 |
| USDJPY-GBPJPY | 0.5347368097099123 | 0.4235474006116208 | 0.3547400611620795 | 0.30326066558321146 |
| GBPJPY-GBPUSD | 0.42671326398493037 | 0.3058103975535168 | 0.327217125382263 | 0.22540361388290042 |

## Classification Matrix

| ID | Status | Blocked By | Evidence / Note |
| --- | --- | --- | --- |
| V-4 | DONE | - | Sigma multiplier mapping exists in H-PM01: bsc_sigma_mult = clip(median_vol / realized_vol_30d, 0.5, 2.0). |
| V-5 | REJECTED_FAILED | - | Barroso-Santa-Clara vol-managed backtest failed portfolio-wide. H-PM01 portfolio delta mean R=-0.004960547358764833, delta Sharpe=-2.5761764707408985%, DSR-p=0.9999646857030353. |
| V-6 | REJECTED_FAILED | - | Vol-managed sizing vs uniform 2% A/B is H-PM01 and failed portfolio-wide. H-PM01 portfolio delta mean R=-0.004960547358764833, delta Sharpe=-2.5761764707408985%, DSR-p=0.9999646857030353. |
| V-7 | DONE | - | Daniel-Moskowitz-style LONG/side-aware sizing is closed by H-PM03/combined MC: H2 P(pass)=0.7806666666666666, full P(bust HARD)=0.022. |
| V-8 | REJECTED_FAILED | - | Moreira-Muir/Barroso broad vol-scaling integration fails as an all-symbol policy. H-PM01 portfolio delta mean R=-0.004960547358764833, delta Sharpe=-2.5761764707408985%, DSR-p=0.9999646857030353; NAS100-only remains shadow/deferred: delta R=0.09066365782920549, DSR-p=0.015223281554341606. |
| V-9 | DEFERRED_WITH_TRIGGER | Component 3C bundle depends on V-2 source completion and broad V-5/V-6 success; portfolio-wide vol sizing failed and live insertion requires approval. | Keep only NAS100-only shadow/approval route open. NAS100-only remains shadow/deferred: delta R=0.09066365782920549, DSR-p=0.015223281554341606. |
| X-1 | BLOCKED_WITH_REASON | Volume-bar E24/E26 retest needs real trade volume or approved tick/depth feed; MT5 retail tick volume is not a volume-bar substrate. | Current tick cache has 30 parquet files and remains quote/retail-substrate limited. |
| X-2 | BLOCKED_WITH_REASON | Dollar-bar E24/E26 retest needs price x real traded volume; current MT5 feed lacks true centralized trade volume. | Use only after approved futures/venue trade-volume feed exists. |
| X-3 | BLOCKED_WITH_REASON | Imbalance-bar E24/E26 retest needs signed trades or aggressor-side proxy; current local data is OHLCV/quote-tick only. | Do not substitute candle direction for signed trade imbalance. |
| X-5 | DONE | - | Rough-vol proxy H estimated on 7 symbols; median H=0.5050851741228051, range=[0.48422314477656087, 0.6033981383377698]. Diagnostic only. |
| X-6 | DONE | - | K54 v1 0.571 was reconciled by the canonical v1 rerun and K1 follow-ups: promotion anchor is CPCV-honest 0.5286, not the DSR-failing published 0.571. |
| A-10 | DONE | - | WGC data plumbing exists: latest demand rows=9475, central-bank-like rows=162. Alpha validation remains separate. |
| A-15 | BLOCKED_WITH_REASON | No He-Kelly-Manela/intermediary-capital source, status file, normalized cache, or source spec exists locally. | Same blocker as D-7; FRED/WGC/CFTC feeds do not supply H-K-M intermediary-capital SDF. |
| A-17 | DONE | - | Copula/tail-dependence diagnostic ran on 13064 aligned M15 returns and 21 pairs; feature feasibility only, no live risk rule. |
| A-18 | DONE | - | Forbes-Rigobon adjusted high-vol correlations are included in the tail-correlation diagnostic; feature feasibility only. |
| B-5 | FILED_FOR_APPROVAL | AI-grounding bundle depends on L-1/L-2/L-4/L-8 and would alter Component 3A/3B behavior if wired live. | Tool scaffolding and debate code exist, but live AI behavior changes need explicit CEO approval and a shadow-only design refresh. |
| R-3 | DEFERRED_WITH_TRIGGER | Strub EVT-CDaR sizing needs preregistered simulation over DSR-surviving baselines and CEO approval before risk behavior changes. | Keep as future risk-policy replacement branch, not an unblocked live implementation. |
| R-4 | DEFERRED_WITH_TRIGGER | Smooth Grossman-Zhou drawdown control needs simulation and owner approval; current H29 drawdown reducer remains the live safety path. | Do not alter live drawdown behavior from current evidence. |
| X-4 | DEFERRED_WITH_TRIGGER | Tick-level Hawkes fitting needs mature tick/depth/order-flow history; current tick capture is short and quote-only. | Current tick cache inventory: {'GBPJPY': 4, 'GBPUSD': 4, 'NAS100': 5, 'US30_cash': 5, 'USDJPY': 4, 'XAGUSD': 4, 'XAUUSD': 4}. Trigger: >=30 trading days all-symbol ticks or approved signed order-flow/depth feed. |
| X-7 | FILED_FOR_APPROVAL | Cascade-prompt rebuild would touch prompts/trading evaluation behavior; V4/cascade remains shelved/lost and requires explicit CEO approval before rebuild. | Recovered template exists, but no prompt rebuild is an unblocked research-loop change. |
| L-1 | FILED_FOR_APPROVAL | QuantMCP-style grounding would alter Component 3A behavior if wired live; approval and shadow-only design refresh are required. | ai_tools scaffolding exists=True, design exists=True, primary imports ai_tools=False. |
| L-2 | FILED_FOR_APPROVAL | FinAgent-style market-state tool inventory would alter Component 3A behavior if wired live; approval and shadow-only design refresh are required. | Current ai_tools files: ['__init__.py', 'base.py', 'lookup_session_vol.py', 'query_recent_outcomes.py', 'registry.py']. |
| L-4 | FILED_FOR_APPROVAL | Component 3B debate activation would alter AI evaluation flow and token spend; CEO DELETE/WIRE/LEAVE decision remains required. | Debate code exists=True, tests exist=True, orchestrator imports debate=False. |
| L-8 | DEFERRED_WITH_TRIGGER | LLM transfer test depends on L-1/L-2 shadow grounding implementation and approval path. | No Sonnet-class transfer test can be run before the grounding intervention exists in a shadow harness. |
| RR-1 | DEFERRED_WITH_TRIGGER | Quarterly last-6-months literature refresh across 22 domains requires a dedicated current-web literature sweep and source-citation pass outside this local evidence triage. | Existing local literature corpus remains usable, but RR-1 specifically asks for current last-6-month paper discovery. |

## NO_PROMOTION_VERDICT

This triage does not validate or promote a trading rule, live filter, risk setting, prompt, or execution change. It only classifies the next unblocked queue batch from local evidence and approval/source blockers.
