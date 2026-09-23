# Session HP canonical source-control context anchor

Findings: the canonical v2 packet is byte-identical to the original HN payload, the one-shot full-generator and M1 proofs passed, the disposable adversarial matrix passed 59/59, and the trusted canonical inventory was unchanged. This anchor authorizes evidence closeout only; it does not authorize or consume the offline P1 result.

`execution_authority: false`
`activation_authority: false`
`result_bearing_science_executed: false`
`broker_orders: 0`
`result_use_status: SOURCE_CONTROL_ONLY_NO_OUTCOME_READ`
`exact_r: NOT_READ_SOURCE_CONTROL_ONLY`
`proxy_r: NOT_READ_SOURCE_CONTROL_ONLY`
`expectancy: NOT_READ_SOURCE_CONTROL_ONLY`

- `held_baseline_sha256: 35644abdf04a9c279ee8561a3fd538a34bc24ecf23d0ad9711241f0a34e0eb03`
- `accepted_source_commit: 9059cfa0659f710dc56ba779181770468d5450f1`
- `accepted_source_tree: 38ece5bee3b927b459dcf07bc76fed5461517099`
- `accepted_source_sole_parent: f59fbb829a5561b7e7b78bed324d67a8c01d6e74`
- `canonical_manifest_sha256: 70f4c5dde50774f34e248b9d56af604b827c165bea5f76eb8f4a9ad0bc52cbf2`
- `canonical_manifest_bytes: 39010`
- `payload_root_sha256: e1dc1330f47d5a8778456f30f42cb9a1a908d4f8f1d3b744d154c77d6e028f6f`
- `terminal_state: P1_SOURCE_PACKET_CANONICAL_REFROZEN_READY_FOR_OFFLINE_RESULT_RUN`

| Rule | Enforcement | Evidence / terminal condition |
|---|---|---|
| Exact source lineage | Accept only the one-parent `9059cfa… -> f59fbb…` ceremony and exactly nine code/test paths. | Tree `38ece5…`; 17/17 M1-focused and 111/111 combined focused tests passed; all nine Python paths compiled. |
| Packet identity | Bind the full tuple of tested source, manifest SHA, and payload root; the leaf name alone is insufficient. | Canonical hold contains schema v2, 39,010-byte manifest `70f4c5…`, 51 payloads / 28,849,175 bytes, and 52 recursive files / 28,888,185 bytes. |
| Three-way payload equivalence | Compare paths, bytes, and SHA-256 for all payloads; permit only manifest/control changes. | HN v1 `cb1d71…`, repaired v2 `1cc4bd…`, and canonical v2 `70f4c5…` share all 51 payloads and root `e1dc13…`. |
| Sparse M1 semantics | Never require a bar for every civil minute; require strict UTC order, binding hashes/counts, exact M15 domain, and canonical OHLCV bytes. Never synthesize bars. | Independent inventory: 2,188,895 M1 rows, 6,405 legitimate sparse intervals, 15,119 absent civil-minute timestamps, 147,690 M15 buckets, 5,277 gap-affected buckets, zero canonical mismatches. |
| HR diagnosis | Classify the earlier civil-minute continuity rejection as a false proxy, not missing capture. | AUDJPY sparse rows aggregated exactly to immutable packet M15; repaired verifier keeps fail-closed domain/OHLCV checks. |
| Exactly-once proofs | One full-generator command followed by one M1 command; never rerun either. | Full PASS 73,999/73,999 and M1 PASS 2,188,895/147,690; raw captures are hash-bound in the science receipts. |
| Adversarial attacks | Mutate disposable fixtures/copies only and require deterministic refusal for each commissioned defect family. | 59/59 focused attacks/positive controls passed; canonical inventory listing SHA `ff272cee…` before and after. |
| Packet preservation | Never alter HN, repaired, or canonical trusted packets. | Recursive inventory SHA values: HN `915fc33a…`, repaired `7eb5b127…`, canonical `ff272cee…`; common payload-only listing SHA `b374f9a5…`. |
| Diagnostic quarantine | HS/HT commits and partial staging holds are not packets or authority. | `880eda679…` and `840d12ae…` rejected; repaired2 has 50 files / 17,042,178 bytes / no manifest; repaired3 has 50 files / 16,303,457 bytes / no manifest. |
| Outcome boundary | No economics, P1, replay, paper, canary, calibration, broker, VPS, MetaTrader, runtime, network, production, or live-forward access. | All authority/result flags remain false; orders are zero; exact-R, proxy-R, and expectancy remain `NOT_READ_SOURCE_CONTROL_ONLY`. |
| Evidence ceremony | Create only the seven commissioned closeout paths, then one evidence-only commit with sole parent `9059cfa…`. | This file is one of the five non-A/B, non-completion artifacts; receipt and completion are created separately. |
| Next-lane authority | A green closeout means readiness for a separately commissioned offline result, never activation. | The offline look remains unconsumed; even a later positive offline result can authorize at most a separately approved paper-shadow readiness review. |

Raw March bars remain permitted only as the preregistered predecision warmup for April. February remains attribution-only. March outcomes and live-forward outcomes remain unopened.
