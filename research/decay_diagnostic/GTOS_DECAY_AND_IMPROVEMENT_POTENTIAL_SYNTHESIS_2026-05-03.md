# GTOS Decay And Improvement Potential Synthesis - 2026-05-03

Status: research synthesis only
Promotion posture: `NO_PROMOTION_VERDICT`
Account lens for dollar conversions: `$100,000` challenge account

## Number Discipline

This document separates four number classes:

| Label | Meaning | Use |
|---|---|---|
| `ACCOUNT_HISTORY_REALIZED` | MT5 account-history screenshot / account balance | the only true account-level live PnL number |
| `LIVE_R_ARTIFACT` | local realized-R/path labels in trade records or shadow logs | useful for strategy forensics, not always equal to account dollars |
| `RESEARCH_MEASURED` | backtest, replay, or Monte Carlo artifact output | real artifact number, not live proof |
| `CONVERSION` | arithmetic conversion from R to percent/dollars | useful for sizing, not new evidence |
| `HYPOTHETICAL_IF_LIVE_HOLDS` | what the measured discovery delta would be worth if it survives live | scenario only |

The real account-history sample is positive. The local R artifacts are still useful, but they must not be used as account PnL when lot size, manual/minimum-day trades, commissions, false-close races, or incomplete lifecycle fields differ.

## Executive Readout

The `+10.8R/month` figure is **not live realized** and **not the final system return**. It is a `HYPOTHETICAL_IF_LIVE_HOLDS` conversion from the 2026 V2 path-event best-structural oracle delta versus the J46-J49 path baseline:

`+0.636190R/trade * 17 trades/month = +10.815R/month`

Mechanical conversion on a `$100,000` account:

| R value | Percent impact | Dollar impact |
|---:|---:|---:|
| 1R = 1% risk | `+10.82%` | `+$10,815` |
| 1R = 2% risk | `+21.63%` | `+$21,630` |

That number is **not live validated** and **not implementable as-is**. It is an upper-bound size-of-prize from choosing the best structural path policy per row after seeing outcomes. The actionable interpretation is only: there is meaningful path-management signal in 2026, but it still needs as-of routing, forward rows, lifecycle telemetry, and a separate promotion dossier.

Decay is a real concern, but the evidence does **not** say the system edge is dead. The current picture is:

- Core OB mechanism: decayed but still real; the relative headline overfit failed DSR, but the mechanical OB-retest mechanism survives separately at cross-period `z=10.5`.
- XAUUSD 2026 decay: serious enough to monitor aggressively; not fully explained by AI hallucination, and one scary cell was largely a fixed SL-buffer/prompt-geometry bug.
- AI/algo crowding: plausible medium-term risk, but not currently proven as the main decay cause.
- Operational truth gap: still one of the largest blockers. Several promising ideas are measured on synthetic/path labels, and even current local live logs can disagree with MT5 account history.

## Real Account History From Screenshot

Correction source: CEO-provided MT5 account-history screenshot on 2026-05-03.

The small `0.01` volume trades on 2026-04-27 and 2026-04-30 were minimum-trading-day filler / safety trades. They should not be treated as normal system expectancy evidence.

Account-level state visible in the screenshot:

| Account item | Value |
|---|---:|
| Initial deposit | `$100,000.00` |
| Balance shown | `$101,223.36` |
| Net balance gain | `+$1,223.36` |
| Net balance percent | `+1.223%` |
| Gross displayed trade-profit sum by visible rows | `+$1,262.56` |
| Difference between gross visible profit and balance gain | `-$39.20` apparent costs/commission/swap or hidden account-history charges |

Visible closed-trade rows:

| Date/time open | Symbol | Volume | Direction | Profit |
|---|---|---:|---|---:|
| 2026-04-27 03:44:35 | xauusd | `0.01` | buy | `+$0.40` |
| 2026-04-27 03:44:40 | us30 | `0.01` | buy | `-$0.34` |
| 2026-04-27 03:44:45 | usdjpy | `0.01` | buy | `-$0.21` |
| 2026-04-27 03:44:51 | gbpjpy | `0.01` | buy | `-$0.21` |
| 2026-04-27 03:44:56 | gbpusd | `0.01` | buy | `+$0.08` |
| 2026-04-27 03:45:01 | xagusd | `0.01` | buy | `-$4.25` |
| 2026-04-27 03:45:07 | ndx100 | `0.01` | buy | `-$0.17` |
| 2026-04-28 12:30:06 | gbpjpy | `7.76` | buy | `+$1,380.81` |
| 2026-04-29 18:15:05 | ndx100 | `0.08` | buy | `-$103.56` |
| 2026-04-30 20:02:47 | eurusd | `0.01` | buy | `-$0.14` |
| 2026-05-01 17:00:05 | xauusd | `0.01` | sell | `-$9.85` |

Grouped account PnL:

| Group | Rows | Gross PnL |
|---|---:|---:|
| 2026-04-27 minimum-day basket | 7 | `-$4.70` |
| 2026-04-28 GBPJPY large live trade | 1 | `+$1,380.81` |
| 2026-04-29 NDX100/NAS100 live trade | 1 | `-$103.56` |
| 2026-04-30 EURUSD minimum-day trade | 1 | `-$0.14` |
| 2026-05-01 XAUUSD `0.01` trade | 1 | `-$9.85` |
| Visible trade-profit total | 11 | `+$1,262.56` |

The correct account-level statement is therefore: **the account is up about `+1.22%` to `+1.26%`, depending whether we use the screenshot balance gain (`+$1,223.36`) or visible gross trade-profit sum (`+$1,262.56`). The live account is not down.**

## Local R Artifacts After J46-J49

These are local strategy/path labels found in `knowledge_base/trade_records` and `shadow_logs/j46_j49_shadow_outcomes.jsonl`. They are **not** the same as account PnL.

| Trade | Instrument | Direction | Local realized R | Screenshot/account USD | Exit reason | Broker reconciled | Delta vs old path |
|---|---|---|---:|---:|---|---|---:|
| `GBPJPY_2026-04-28_london_0900` | GBPJPY | LONG | `+0.7380R` | `+$1,380.81` | `ny_close_force` | true | `+0.9906R` |
| `NAS100_2026-04-29_ny_1500` | NAS100/NDX100 | LONG | `-1.0167R` | `-$103.56` | `sl_hit` | true | `-1.0845R` |
| `XAUUSD_2026-05-01_london_0815` | XAUUSD | SHORT | `-0.7395R` | `-$9.85` | `MANUAL` / broker close artifact | false | `-6.8851R` |

Local-R summary from those rows:

| Metric | Value |
|---|---:|
| n | `3` |
| Winners / losers | `1 / 2` |
| WR | `33.33%` |
| Total local realized R | `-1.0182R` |
| Mean local realized R | `-0.3394R/trade` |
| Total J46 delta vs old path | `-6.9790R` |
| Mean J46 delta vs old path | `-2.3263R/trade` |
| Same three rows, account USD | `+$1,267.40` gross |

Important artifact conflicts:

- `shadow_logs/daily_pnl_history.jsonl` has the NAS100 false-close race as `-$4.19`; the corrected trade record and screenshot show `-$103.56`.
- `shadow_logs/daily_pnl_history.jsonl` has the 2026-05-01 XAUUSD row as `-$739.49`; the screenshot account history shows `-$9.85` because the actual volume was `0.01`.
- Therefore, for dollars and account status, use MT5 account history / screenshot. Use local R labels only for strategy forensics until the lifecycle/PnL logger is reconciled.

The honest live account answer is: **the account is up approximately `+1.22%` net by balance, and the local R artifacts are not currently reliable as account-dollar truth.**

## Current Stack Monte Carlo In Dollars

The current redacted_account live stack already includes J46-J49 plus S79-style risk policy plus side-aware sizing. The best existing forward-looking dollar lens is the combined 30-day Monte Carlo in `research/ml_program/phase_2/position_mgmt/combined_mc_j46_s79_side_aware.md`.

These are `RESEARCH_MEASURED` MC numbers, not live realized PnL.

| Stack | Density | P(pass) | P(bust hard) | Mean PnL | Dollar mean on $100K | p99 DD | Median pass |
|---|---|---:|---:|---:|---:|---:|---:|
| Baseline + S79, J46 off | realistic | `64.56%` | `1.28%` | `+6.89%` | `+$6,888` | `8.68%` | 16d |
| J46 + S79, side-aware off | realistic | `91.98%` | `0.60%` | `+9.94%` | `+$9,941` | `6.82%` | 9d |
| Current full stack: J46 + S79 + side-aware | realistic | `81.26%` | `0.06%` | `+8.47%` | `+$8,473` | `4.77%` | 14d |
| Current full stack: J46 + S79 + side-aware | S79-density | `99.96%` | `0.04%` | `+9.58%` | `+$9,584` | `4.92%` | 3d |

Interpretation:

- J46-J49 is a performance/velocity lift versus baseline.
- Side-aware sizing is a safety/risk-quality improvement, not a pure return maximizer. In the realistic-density MC it gives up about `$1,468` of mean 30-day PnL versus J46+S79 alone, but cuts hard-bust risk from `0.60%` to `0.06%` and p99 drawdown from `6.82%` to `4.77%`.
- Current stack versus baseline+S79 realistic improves mean 30-day PnL by about `$1,586`, improves P(pass) by `+16.70pp`, and cuts hard-bust risk by `-1.22pp`.

## Measured Research Deltas Converted To Dollars

These are not live performance numbers. They are exact `RESEARCH_MEASURED` deltas converted into dollars under explicit assumptions. They answer: if the discovery-set delta held live, and if implementation captured it without extra slippage or frequency distortion, what is the dollar size?

Assumption for this table: old canonical `17 trades/month` frequency. This is **not** a proven current frequency. The live effective risk per R is not always 2% because redacted_account profile overrides, side-aware LONG `0.5x`, correlation halving, NAS100 observer risk, and drawdown reduction all change actual risk. Therefore both `1R = 1%` and `1R = 2%` are shown.

| Research idea | Evidence slice | Delta vs J46 | Monthly R at 17/mo | At 1R=1% | At 1R=2% | Readiness |
|---|---|---:|---:|---:|---:|---|
| V2 OB-boundary | full resolved slice | `+0.024061R/trade` | `+0.409R/mo` | `+$409` | `+$818` | cleanest V2b candidate, not validated |
| V2 FVG mid/edge | full resolved slice | `+0.033292R/trade` | `+0.566R/mo` | `+$566` | `+$1,132` | larger headline, less clean across groups |
| V2 OB-boundary | 2026 slice | `+0.233839R/trade` | `+3.975R/mo` | `+$3,975` | `+$7,951` | promising anti-decay candidate, discovery only |
| V2 FVG mid/edge | 2026 slice | `+0.365975R/trade` | `+6.222R/mo` | `+$6,222` | `+$12,443` | promising but concentration/robustness issues |
| V2 best structural oracle | 2026 slice | `+0.636190R/trade` | `+10.815R/mo` | `+$10,815` | `+$21,630` | upper bound, not implementable as-is |
| V2 best of J46+structural oracle | 2026 slice | `+0.811874R/trade` | `+13.802R/mo` | `+$13,802` | `+$27,604` | upper bound, not implementable as-is |
| V3 FVG-only rescue | full eligible subset | `+0.270259R/trade` on affected rows | `+0.641R/mo` if 14% of 17/mo | `+$641` | `+$1,283` | discovery-only subset candidate |

Do **not** add these directly to the Monte Carlo table as a "new expected month." A proper forecast requires rerunning the MC with the changed R distribution, actual symbol risk overrides, side distribution, correlation gates, fill/no-fill lifecycle, slippage, and frequency changes.

## Frequency And Trade Capture

The short answer: the weekend discoveries mostly improve **quality/path management**, not proven raw trade frequency.

Known frequency anchors:

| Frequency lens | Value | Meaning |
|---|---:|---|
| Screenshot account-history rows | `11` closed rows from 2026-04-27 to 2026-05-01 | includes minimum-day filler trades; account is up `+$1,223.36` net by balance |
| Local post-J46 R-artifact rows | `3` rows from 2026-04-28 to 2026-05-01 | strategy/path R labels; not account-dollar truth |
| Canonical pre-April rough rate | `~17 trades/month` | old all-instrument rough planning number |
| Realistic-density MC | `0.55 fills/day` | about `12` fills/month over 22 trading days |
| S79-density MC | `2.97 fills/day` | about `65` fills/month; upper-density methodology bracket |
| Combined MC interpretation | live truth between realistic and S79-density | 7-instrument live fleet should not be assumed equal to the old 17/mo forever |

Impact by research category:

- J46-J49: does not mainly create more setups; it changes path/exit distribution and improves R per accepted trade.
- S79 risk policy: changes sizing and pass probability; no setup-frequency increase.
- Side-aware sizing: reduces LONG risk; it can slow pass velocity under thin density.
- V2 OB/FVG/Swing structural path policies: manage existing trade path exits/locks; not new entry generators.
- V3 FVG-only rescue: could increase **broker order count** if implemented as close-and-reenter, but it should still be counted as the same setup risk budget. Eligible share in the V3 replay was `625 / 4477 = 13.96%`; using 17 setups/month, that is about `2.37` affected setups/month. Actual added fill count is unknown until lifecycle telemetry exists.
- Multi-framework `fvg_fill` and `breaker_re_entry`: already live in the current system and can expand the opportunity universe, but the weekend improvement numbers above did not prove an additional validated frequency lift.
- Orderflow/Sierra/Databento: currently awareness/quality research, not a quantified frequency unlock. Actual broker-R coverage remains too sparse for promotion.

So yes, there may be future frequency upside, especially from reducing false rejects, better reentry lifecycle handling, and expanding symbol/session categories. But the numbers currently strong enough to write down are mostly **expectancy-per-trade and risk-policy numbers**, not proven `more trades/month` numbers.

## Decay Map

Decay in GTOS should be split into six different problems. Mixing them creates false fear or false confidence.

| Decay type | Is it present? | Current seriousness | Evidence |
|---|---|---:|---|
| Selection/statistical overfit | yes | high methodological risk | DSR killed many old headline claims; promotion p-values currently allowed count is `0` in the latest methodology gate |
| Market-regime decay | yes | medium/high | XAU H1-2026 `64.5%` WR to H2-2026 `24.0%`, p=`0.006`; quarterly WR declined over time |
| Implementation bug masquerading as decay | yes, historically | medium but improving | A4 showed the scary XAU trending-bull cell was largely pre-FA-2 `sl_buffer_applied: 0.0` geometry bug |
| AI hallucination/drift | not dominant in current evidence | low/medium | F8 found H1-to-H2 hallucination delta `-5.10pp`; grounding improved while realized R worsened |
| Crowding/public AI/algo adoption | plausible, not proven | medium long-term | edge mechanism can be crowded, but no direct current proof that crowding is the dominant decay driver |
| Execution/data/live-label decay | yes | high operational blocker | stale trade index, incomplete lifecycle fields, sparse actual broker-R labels for orderflow/V3 validation |

## Decay Evidence

### 1. The Core OB Mechanism Is Real, But The Headline Was Too Strong

The system edge is OB-zone precision: price often continues in the impulse direction after revisiting the last opposing-candle zone before a structural break. The durable explanation is stop-cascade mean-reversion to a prior balanced zone, not mystical institutional footprint reading.

Important split:

- The old relative claim, "OB advantage +17pp versus generic pullback," failed DSR with DSR-p `0.524`.
- The mechanical OB-retest mechanism itself survives separately on cross-period evidence at `z=10.5`.
- F11 decay velocity estimates show the OB edge shrinking: `+16.8pp` pre-2026, `+12.1pp` H1-2026, `+4.6pp` H2-2026.

Interpretation: the mechanism should remain in the system, but it should not be treated as an eternal, broad, undifferentiated edge. It needs regime, side, path, and execution awareness.

### 2. XAUUSD 2026 Decay Was Real Enough To Respect

The caveat file records:

- H1-2026 XAUUSD WR: `64.5%`, n=`31`
- H2-2026 XAUUSD WR: `24.0%`, n=`25`
- Chi-square p=`0.006`

Quarterly WR series:

| Period | WR | Note |
|---|---:|---|
| Q3 2025 | `73.2%` | first batched quarter |
| Q4 2025 | `71.4%` | still strong |
| Q1 2026 | `63.6%` | decayed but tradable-looking |
| H1-2026 / early 2026 reference | `59.4%` / `64.5%` depending slice | still not dead |
| Q2-2026 partial | `24.0%` | n=`25`, Mar-Apr partial, alarm not final baseline |

Interpretation: decay is not paranoia. It is empirically visible. But Q2 partial is small and contaminated by live-system changes, bugs, and detector/prompt evolution, so it is an alarm requiring monitoring rather than proof the strategy is dead.

### 3. One Scary Decay Cell Was Actually A Geometry Bug

A4 re-tested the XAUUSD H2 trending-bull cohort using current AI emissions after FA-2. The result:

- n=`11`
- mean R `+0.818`
- WR `72.7%`
- friction haircut estimate: about `+0.65R`

The issue was not that the AI suddenly forgot the market in that cell. The old prompt emitted `sl_buffer_applied: 0.0`, putting stops exactly at the OB boundary and causing deterministic L2 rejection. FA-2 corrected the prompt-side geometry. This matters because some apparent decay was system implementation, not market death.

### 4. Hallucination Is Not The Main H2 Decay Explanation

F8 found:

- Overall H1-to-H2 hallucination delta: `-5.10pp`
- Structural fields such as OB high/low and protected swing had `0.00pp` degradation
- Conclusion: hallucination improved in late-April while realized R got worse

Interpretation: the next decay suspects are path-vs-realized-R, regime, execution/lifecycle, touch-count and structure quality, not generic "AI hallucinated more."

### 5. Current Rolling OB Continuation Monitor Is Not Screaming

The long-form edge mechanism sets:

- OB continuation baseline: `70%`
- rolling-50 alarm: `<60%`
- small-sample gate: flag windows with fewer than 50 OBs

Latest current-state snapshot says OB continuation latest date is `2026-05-01` with `0` current alarms.

Interpretation: the system has a decay alarm framework, and as of the latest snapshot it is not showing an active OB-continuation breach. That does not eliminate XAU-specific or path-specific decay, but it argues against "entire OB mechanism is already dead."

## AI And Algorithm Crowding Risk

Your concern about more people using AI and algorithms is reasonable. The risk path is:

1. More traders identify similar OB/FVG/liquidity concepts.
2. Entries cluster around the same zones.
3. Price may still react at the zone, but post-fill continuation becomes weaker.
4. TP-hit rate drops, BE stops increase, or the market reverses faster after touching obvious zones.

GTOS can detect that kind of decay through:

- OB continuation rate dropping below rolling baseline.
- TP/SL and MFE/MAE distribution worsening even if entry touch still works.
- More same-bar ambiguity and faster reversal after fill.
- Lower average R while entry WR remains superficially okay.
- Candidate rate staying stable while realized R decays.

Current evidence does not prove public AI/algo crowding as the dominant cause. The stronger near-term causes are regime shift, implementation bugs, selection overfit, and incomplete lifecycle measurement. Crowding should be monitored, but it is not currently the reason to abandon the system.

## How Strong The System Looks Now

| Area | Current confidence | Reason |
|---|---:|---|
| Core OB mechanism | medium/high | mechanism survives separately, but decayed and relative headline failed DSR |
| Current J46/S79 risk stack | high for risk-direction, medium for exact PnL | MC is strong, but density assumptions bracket reality |
| Side-aware sizing | high for reducing tail risk, medium for return impact | safety improves; velocity cost depends on future LONG/SHORT mix |
| V2 path management | medium as discovery, low as promotion | full/2026 deltas are promising; V2b has zero resolved prospective pairs |
| V3 FVG-only rescue | low/medium as discovery, low as promotion | positive subset, but same-dataset and lifecycle-blocked |
| Market awareness/orderflow | low/medium | real data path exists, but actual broker-R coverage is sparse |
| Execution/lifecycle truth | low/medium | this is still a blocker for exact live expectancy and frequency claims |
| Decay monitoring | medium | OB monitor exists and no current alarm; monthly decay watchdog hook/operator cadence still needs live accumulation |

## What Remains Unanswered

Unanswered or deferred questions:

- Whether V2 OB-boundary keeps positive delta on resolved post-cutoff prospective pairs. Current status: `0` resolved post-cutoff OB-boundary/J46 pairs.
- Whether FVG's larger 2026 lift survives concentration, cost, and leave-group stress in forward data.
- Whether V3 FVG-only rescue remains positive when broker fill/no-fill and actual lifecycle accounting are complete.
- Whether current live frequency is closer to 12/month, 17/month, or much higher under the seven-instrument fleet after the framework expansion.
- Whether recent XAU decay is mostly regime, side, volatility, execution, or residual detector behavior once n >= 30 post-fix live trades exist.
- Whether orderflow/depth features improve decision quality with actual broker-R labels, not just synthetic/path outcomes.
- Whether public crowding can be observed directly through lower continuation, faster reversal, or worsening MFE/MAE at obvious OB/FVG zones.

## Practical Conclusion

Decay is serious enough to make GTOS cautious and evidence-driven. It is not serious enough, based on current evidence, to conclude the system is structurally dead.

The correct posture is:

- Keep strict risk policy and current safety gates.
- Treat V2/V3 and orderflow findings as research opportunities, not live promotions.
- Push forward validation and lifecycle telemetry hard so promising path improvements become measurable in broker-realized terms.
- Monitor OB continuation, XAU LONG WR, monthly decay, candidate-rate drift, MFE/MAE, and pass/fail MC sensitivity.
- Prefer incremental improvements that either reduce tail risk or add robust R without depending on a single symbol/session/year pocket.

The system is stronger than before because it now has J46-J49, S79, side-aware sizing, DSR methodology discipline, path-management discoveries, orderflow infrastructure, and explicit decay monitors. The remaining weakness is not lack of ideas; it is proving which ideas survive forward, live, broker-realized data.

## Source Map

- CEO-provided MT5 account-history screenshot, 2026-05-03
- `.context/01_knowledge_base/edge_mechanism.md`
- `.context/01_knowledge_base/validated_numbers_caveats.md`
- `.context/00_core/research_current_state.md`
- `CLAUDE.md`
- `research/a4_trending_bull_replay_2026-04-28/A4_FINAL_SYNTHESIS.md`
- `research/ai_behavior/B7_hallucination_h1_h2_delta/F8_VERDICT.md`
- `research/ml_program/phase_2/position_mgmt/combined_mc_j46_s79_side_aware.md`
- `research/ml_program/phase_2/position_mgmt/combined_mc_results.json`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_SELECTOR_FORENSICS_2026-05-02.json`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V2_CONFLUENCE_DEEPDIVE_2026-05-03.json`
- `research/phase_3_external_feed_validation/RAW_OHLC_PATH_SCALING_V3_FULL_EXPLORATORY_REPLAY_2026-05-03.json`
- `shadow_logs/j46_j49_shadow_outcomes.jsonl`
- `shadow_logs/daily_pnl_history.jsonl`
- `knowledge_base/trade_records/GBPJPY/2026-04-28_london_0900.json`
- `knowledge_base/trade_records/NAS100/2026-04-29_ny_1500.json`
- `knowledge_base/trade_records/XAUUSD/2026-05-01_london_0815.json`
