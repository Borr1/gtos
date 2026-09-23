# G12 NOFILL USDJPY MQL5 Source Contract Audit - 2026-05-09

Promotion verdict: `NO_PROMOTION_VERDICT`. `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`.

## Contract Decision

`PASS_SOURCE_CONTRACT_LIMIT_CONFIRMED`.

The cached official MT5/MQL5 source captures support chronological ordering across returned `MqlTick` rows and expose quote-state fields such as bid, ask, `time_msc`, and flags. They do not expose a broker-native sequence/event ID or sub-row timestamp that can order two predicates inside one returned quote-state row.

## Raw Captures

| role | exists | sha256 | path |
| --- | --- | --- | --- |
| mql5_copyticksrange_mql | True | 17bbf5a0a246c5daae99719c4ec5deb3e98c5028885b7aa96913d7e5ed94d634 | C:\tmp\gtos_otb\G12USDJPYSEQ\research\science_program_2026_05\06_outcome_testing\nofill_remaining_residual_source_closure\raw\MQL5_COPY_TICKS_RANGE_MQL_2026-05-09.html |
| mql5_copyticksrange_python | True | e3d9d91d79e546485c36bdcff581ac2c19ef45cf6f7786ff235b22fbfad4cca2 | C:\tmp\gtos_otb\G12USDJPYSEQ\research\science_program_2026_05\06_outcome_testing\nofill_remaining_residual_source_closure\raw\MQL5_COPY_TICKS_RANGE_PY_2026-05-09.html |
| mql5_mqltick_structure | True | af91c7b54f50be49c8ea21a2267cf8eee8105453fd97e1ccbb0687ff813e7f5d | C:\tmp\gtos_otb\G12USDJPYSEQ\research\science_program_2026_05\06_outcome_testing\nofill_remaining_residual_source_closure\raw\MQL5_MQLTICK_STRUCTURE_2026-05-09.html |
| mql5_source_index | True | 85b90ee48ed127dba9068dac95ab2bad01f41c14bddb226e4e5d4bd17e45d650 | C:\tmp\gtos_otb\G12USDJPYSEQ\research\science_program_2026_05\06_outcome_testing\nofill_remaining_residual_source_closure\raw\MQL5_SOURCE_INDEX_2026-05-09.json |

## Local Line Evidence

| path | line | pattern |
| --- | --- | --- |
| C:\tmp\gtos_otb\G12USDJPYSEQ\research\science_program_2026_05\06_outcome_testing\nofill_remaining_residual_source_closure\raw\MQL5_COPY_TICKS_RANGE_MQL_2026-05-09.html | 9 | MqlTick |
| C:\tmp\gtos_otb\G12USDJPYSEQ\research\science_program_2026_05\06_outcome_testing\nofill_remaining_residual_source_closure\raw\MQL5_COPY_TICKS_RANGE_MQL_2026-05-09.html | 9 | Indexing goes from the past to the present |
| C:\tmp\gtos_otb\G12USDJPYSEQ\research\science_program_2026_05\06_outcome_testing\nofill_remaining_residual_source_closure\raw\MQL5_COPY_TICKS_RANGE_MQL_2026-05-09.html | 186 | flags |
| C:\tmp\gtos_otb\G12USDJPYSEQ\research\science_program_2026_05\06_outcome_testing\nofill_remaining_residual_source_closure\raw\MQL5_COPY_TICKS_RANGE_PY_2026-05-09.html | 282 | time_msc |
| C:\tmp\gtos_otb\G12USDJPYSEQ\research\science_program_2026_05\06_outcome_testing\nofill_remaining_residual_source_closure\raw\MQL5_COPY_TICKS_RANGE_PY_2026-05-09.html | 193 | flags |
| C:\tmp\gtos_otb\G12USDJPYSEQ\research\science_program_2026_05\06_outcome_testing\nofill_remaining_residual_source_closure\raw\MQL5_COPY_TICKS_RANGE_PY_2026-05-09.html | 209 | named time, bid, ask |
| C:\tmp\gtos_otb\G12USDJPYSEQ\research\science_program_2026_05\06_outcome_testing\nofill_remaining_residual_source_closure\raw\MQL5_MQLTICK_STRUCTURE_2026-05-09.html | 196 | time_msc |
| C:\tmp\gtos_otb\G12USDJPYSEQ\research\science_program_2026_05\06_outcome_testing\nofill_remaining_residual_source_closure\raw\MQL5_MQLTICK_STRUCTURE_2026-05-09.html | 197 | flags |
| C:\tmp\gtos_otb\G12USDJPYSEQ\research\science_program_2026_05\06_outcome_testing\nofill_remaining_residual_source_closure\raw\MQL5_MQLTICK_STRUCTURE_2026-05-09.html | 208 | TICK_FLAG_BID |
| C:\tmp\gtos_otb\G12USDJPYSEQ\research\science_program_2026_05\06_outcome_testing\nofill_remaining_residual_source_closure\raw\MQL5_MQLTICK_STRUCTURE_2026-05-09.html | 209 | TICK_FLAG_ASK |

## Interpretation Boundary

`time_msc` is millisecond precision. Tick flags identify which fields changed in the tick row; they are not an ordering stream for entry-touch versus protective-level predicates inside the same row. Therefore the official cached docs do not clear the four USDJPY same-tick rows without a separate broker-native quote-event stream/server-side quote log.
