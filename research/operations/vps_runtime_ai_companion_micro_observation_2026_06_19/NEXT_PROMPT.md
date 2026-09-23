# Next Prompt

Use this only if the owner wants to promote the read-only companion digest into a durable runtime companion lane.

Objective: convert `AI_COMPANION_CYCLE_DIGEST.json` into a continuously refreshed read-only operator/AI companion artifact that explains each scheduled cycle by terminal cause, skipped rows, governor state, placement state, management state, and evidence paths. Keep it observation-only: no order placement, no broker/account/order/deal/position mutation, no reload, no gate override.

Required starting evidence:

- `MICRO_OBSERVATION_SYNTHESIS.json`
- `AI_COMPANION_CYCLE_DIGEST.json`
- `VERIFICATION_RESULT.json`
- final supervision snapshot `research/operations/vps_runtime_active_monitoring_repair_2026_06_19/VPS_ACTIVE_SUPERVISION_REPAIR_BROKER_SNAPSHOT_20260619T090827Z.json`

Minimum closure: builder/verifier/focused tests, route artifact audit clean, exact runtime boundary, and explicit queues for cost-screen review, duplicate protection, broker-profile hygiene, risk-governor awareness, legacy attribution boundaries, and active/nonclosed lifecycle normalization.
