# Science Program Worktree Map - 2026-05-06

**External root:** `C:\tmp\gtosg`
**Promotion verdict:** `NO_PROMOTION_VERDICT`

This file records the intended isolated worktrees. The builder does not create external directories; run the generated PowerShell script only when ready to launch lanes.

| Lane | Branch | Worktree | Prompt |
| --- | --- | --- | --- |
| G0 | science-goals/g0-program-governor | C:\tmp\gtosg\G0 | research\science_program_2026_05\04_goal_prompts\G0_G0_PROGRAM_GOVERNOR_GOAL_PROMPT_2026-05-06.md |
| G1 | science-goals/g1-validation-statistics | C:\tmp\gtosg\G1 | research\science_program_2026_05\04_goal_prompts\G1_G1_VALIDATION_STATISTICS_GOAL_PROMPT_2026-05-06.md |
| G2 | science-goals/g2-stochastic-tails | C:\tmp\gtosg\G2 | research\science_program_2026_05\04_goal_prompts\G2_G2_STOCHASTIC_TAILS_GOAL_PROMPT_2026-05-06.md |
| G3 | science-goals/g3-geometry-signal | C:\tmp\gtosg\G3 | research\science_program_2026_05\04_goal_prompts\G3_G3_GEOMETRY_SIGNAL_GOAL_PROMPT_2026-05-06.md |
| G4 | science-goals/g4-microstructure-auction | C:\tmp\gtosg\G4 | research\science_program_2026_05\04_goal_prompts\G4_G4_MICROSTRUCTURE_AUCTION_GOAL_PROMPT_2026-05-06.md |
| G5 | science-goals/g5-behavioral-game | C:\tmp\gtosg\G5 | research\science_program_2026_05\04_goal_prompts\G5_G5_BEHAVIORAL_GAME_GOAL_PROMPT_2026-05-06.md |
| G6 | science-goals/g6-momentum-reversion | C:\tmp\gtosg\G6 | research\science_program_2026_05\04_goal_prompts\G6_G6_MOMENTUM_REVERSION_GOAL_PROMPT_2026-05-06.md |
| G7 | science-goals/g7-macro-cross-asset | C:\tmp\gtosg\G7 | research\science_program_2026_05\04_goal_prompts\G7_G7_MACRO_CROSS_ASSET_GOAL_PROMPT_2026-05-06.md |
| G8 | science-goals/g8-options-vol | C:\tmp\gtosg\G8 | research\science_program_2026_05\04_goal_prompts\G8_G8_OPTIONS_VOL_GOAL_PROMPT_2026-05-06.md |
| G9 | science-goals/g9-ai-ml-systems | C:\tmp\gtosg\G9 | research\science_program_2026_05\04_goal_prompts\G9_G9_AI_ML_SYSTEMS_GOAL_PROMPT_2026-05-06.md |
| G10 | science-goals/g10-execution-risk | C:\tmp\gtosg\G10 | research\science_program_2026_05\04_goal_prompts\G10_G10_EXECUTION_RISK_GOAL_PROMPT_2026-05-06.md |
| G11 | science-goals/g11-data-sources-expansion | C:\tmp\gtosg\G11 | research\science_program_2026_05\04_goal_prompts\G11_G11_DATA_SOURCES_EXPANSION_GOAL_PROMPT_2026-05-06.md |
| G12 | science-goals/g12-red-team | C:\tmp\gtosg\G12 | research\science_program_2026_05\04_goal_prompts\G12_G12_RED_TEAM_GOAL_PROMPT_2026-05-06.md |

## Creation Commands

```powershell
New-Item -ItemType Directory -Path "C:\tmp\gtosg" -Force | Out-Null
git -C C:\Users\MSI\Documents\ai-trading-agent worktree add -b science-goals/g0-program-governor "C:\tmp\gtosg\G0" main
git -C C:\Users\MSI\Documents\ai-trading-agent worktree add -b science-goals/g1-validation-statistics "C:\tmp\gtosg\G1" main
git -C C:\Users\MSI\Documents\ai-trading-agent worktree add -b science-goals/g2-stochastic-tails "C:\tmp\gtosg\G2" main
git -C C:\Users\MSI\Documents\ai-trading-agent worktree add -b science-goals/g3-geometry-signal "C:\tmp\gtosg\G3" main
git -C C:\Users\MSI\Documents\ai-trading-agent worktree add -b science-goals/g4-microstructure-auction "C:\tmp\gtosg\G4" main
git -C C:\Users\MSI\Documents\ai-trading-agent worktree add -b science-goals/g5-behavioral-game "C:\tmp\gtosg\G5" main
git -C C:\Users\MSI\Documents\ai-trading-agent worktree add -b science-goals/g6-momentum-reversion "C:\tmp\gtosg\G6" main
git -C C:\Users\MSI\Documents\ai-trading-agent worktree add -b science-goals/g7-macro-cross-asset "C:\tmp\gtosg\G7" main
git -C C:\Users\MSI\Documents\ai-trading-agent worktree add -b science-goals/g8-options-vol "C:\tmp\gtosg\G8" main
git -C C:\Users\MSI\Documents\ai-trading-agent worktree add -b science-goals/g9-ai-ml-systems "C:\tmp\gtosg\G9" main
git -C C:\Users\MSI\Documents\ai-trading-agent worktree add -b science-goals/g10-execution-risk "C:\tmp\gtosg\G10" main
git -C C:\Users\MSI\Documents\ai-trading-agent worktree add -b science-goals/g11-data-sources-expansion "C:\tmp\gtosg\G11" main
git -C C:\Users\MSI\Documents\ai-trading-agent worktree add -b science-goals/g12-red-team "C:\tmp\gtosg\G12" main
```

Do not stage runtime dirt from `main`; each lane commits only its scoped research files.
