# OTB0 G5 Sonnet-Only Prompt-Neutral Pilot Design - 2026-05-07

**Promotion verdict:** `NO_PROMOTION_VERDICT`
**Validation safe:** `false`
**Outcome review opened:** `false`
**OTB0 API calls:** `0`

## Pilot Gates

| Gate | Requirement |
| --- | --- |
| Gate 0 | Run only after OTB3 clears source refs and OTB1/OTB2 supply frozen no-outcome packet samples. |
| Gate 1 | Estimate token cost from frozen prompts and sample before any API call; stop if estimate cannot fit within $20. |
| Model | Sonnet only; no Opus; use one fixed model version string in the ledger. |
| Sample | Small high-information stratified sample, default maximum 24 paired setups across packet class, symbol/session/side/regime/source-blocker family; reduce if cost estimate requires. |
| Prompt freeze | Write baseline and prompt-neutral prompt text plus SHA256 hashes before calls; prompts must contain no result/R fields. |
| Scoring | Fixed rubric before calls: comparator decision class, rationale tags, refusal/malformed flags, source-use compliance, confidence calibration; no outcome values in prompt or scoring context. |
| Ledger | Record request_time_utc, model, prompt_hash, setup_id, token estimate, actual tokens/cost if run, cache key, response hash, and error state. |
| Stop conditions | Stop on $20 cap, any Opus route, uncached duplicate call, prompt hash drift, outcome/R field exposure, or sample expansion pressure. |

## Pilot Status

The pilot is justified only as a future OTB5 lane if OTB3 clears `SRC-G5-PROMPT-NEUTRAL-001` from design-only into a packet-safe paired-run protocol and if OTB1/OTB2 provide frozen setup packets with no outcome/R fields. OTB0 performs no API calls.
