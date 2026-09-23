# Repaired Proxy Scope Scorer Application

Generated UTC: `2026-05-17T11:58:37Z`

Branch-local repaired-proxy scope scorer application. This artifact consumes broker/source repair implementation decisions into a callable repaired-proxy scope registry and applies it to every numeric shadow event, producing default-off score rows, avoid/redesign comparator rows, repair-required rows, and full summaries. It is research-only and has no live behavior.

## Counts

- `input_implementation_decision_rows`: `290`
- `input_repair_result_rows`: `17753`
- `input_event_score_rows`: `17916`
- `registry_rows`: `290`
- `event_application_rows`: `17916`
- `default_off_score_rows`: `12303`
- `avoid_redesign_rows`: `5443`
- `repair_required_rows`: `170`
- `application_summary_rows`: `309`
- `bucket_rows`: `37`
- `question_rows`: `4`
- `source_manifest_rows`: `11`

## Event Status

- `REPAIRED_PROXY_EVENT_AVOID_OR_REDESIGN_EMITTED`: `5443`
- `REPAIRED_PROXY_EVENT_DEFAULT_OFF_SCORE_EMITTED`: `12303`
- `REPAIRED_PROXY_EVENT_SOURCE_REPAIR_REQUIRED`: `170`
