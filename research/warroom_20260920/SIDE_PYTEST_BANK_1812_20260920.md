# Side pytest bank — Continue 1812

**When:** 2026-09-20 18:24 ICT
**Tip:** `chair/p0-shadow-land-20260920` @ **0beb16d09**
**Result:** **10 failed, 463 passed** in 414.34s (APPLY unset)

## Failures (honest)
1. `test_scout_attach_map_resolves_chair_names` — missing `/workspace/gtos/_scout_packets/SLEEVE_ATTACH_MAP.md`
2–4. pack6 / edge_freeze — `UnicodeDecodeError` cp1252 on VPS
5. `test_challenge_tape_is_true_utc...` — Windows `\` path breaks `endswith(.../XAUUSD_M15.csv)`
6. `test_default_on_when_key_present_explicit_off` — host JEV key → calls_enabled True
7. `test_harness_scores_all_closes_without_place` — unexpected `timeframes.m15` in inventory
8–10. `test_news_inventory_live*` — host contamination (live shadow_logs / challenge_host_news_writer)

## Gate
Continue 1604 IN_FLIGHT **resolved = FAIL**. **Do not land** PR39 onto f5-live this fire.
