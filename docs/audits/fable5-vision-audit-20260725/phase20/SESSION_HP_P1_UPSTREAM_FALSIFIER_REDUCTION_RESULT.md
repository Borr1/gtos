# Session HP canonical P1 upstream falsifier reduction result

## Findings

The source/control gate is green. The direct-parent canonical repair at `9059cfa0659f710dc56ba779181770468d5450f1` preserves every one of the 51 HN payloads, corrects the false sparse-M1 continuity proxy, and passes the one authorized full-generator proof, the one authorized M1 provenance proof, and 59/59 disposable adversarial tests. The offline P1 look remains unconsumed.

`execution_authority: false`
`activation_authority: false`
`result_bearing_science_executed: false`
`broker_orders: 0`
`result_use_status: SOURCE_CONTROL_ONLY_NO_OUTCOME_READ`
`exact_r: NOT_READ_SOURCE_CONTROL_ONLY`
`proxy_r: NOT_READ_SOURCE_CONTROL_ONLY`
`expectancy: NOT_READ_SOURCE_CONTROL_ONLY`

`terminal_state: P1_SOURCE_PACKET_CANONICAL_REFROZEN_READY_FOR_OFFLINE_RESULT_RUN`

## Accepted source ceremony

- Commit `9059cfa0659f710dc56ba779181770468d5450f1`; tree `38ece5bee3b927b459dcf07bc76fed5461517099`; sole parent `f59fbb829a5561b7e7b78bed324d67a8c01d6e74`.
- Exactly nine changed code/test paths: the inert adapter, expectations module, reconstruction, packet verifier, M1 verifier, and their four focused test files.
- Relative to accepted hardening sibling `8e7710da3ccd40983abd2d71346f36c506291e25`, only the M1 verifier and its test differ. Both accepted commits are siblings of HN, not ancestors of each other.
- The main packet verifier is 1,825 lines; M1 provenance is separated into a bounded 350-line module. Source pre-closeout gates were 17/17 M1-focused and 111/111 combined focused tests, nine Python compilations, and a clean diff check.

## Canonical packet and equivalence

The canonical packet is `/Users/borr/GTOSActive/p1-upstream-source-packet-canonical-hold-20260802/p1-source-packet-sha256-e1dc1330f47d5a8778456f30f42cb9a1a908d4f8f1d3b744d154c77d6e028f6f`.

- Manifest: 39,010 bytes, SHA-256 `70f4c5dde50774f34e248b9d56af604b827c165bea5f76eb8f4a9ad0bc52cbf2`, schema v2, tested source `9059cfa…`.
- Payload: root `e1dc1330f47d5a8778456f30f42cb9a1a908d4f8f1d3b744d154c77d6e028f6f`; 51 files / 28,849,175 bytes; 73,999 identities; 52,803 states; 612,190 M15 rows.
- Recursive packet: 52 files / 28,888,185 bytes.
- HN v1 manifest `cb1d71e38335dcc62eead82916d3576f80f873511a17886818673de3b28b4413`, repaired v2 manifest `1cc4bdf6e6ad1565cba8ba8d0ed495a3c260025195856a1417cfa2d09ef853ce`, and canonical v2 manifest `70f4c5dd…` differ, while all 51 payload paths, bytes, and SHA-256 values are identical.

## Production proofs

The full verifier ran once from `2026-08-02T02:06:06Z` to `2026-08-02T02:23:46Z` and exited zero. Raw stdout is 3,709 bytes / `e756db1e4b291d9b7a1bf9979a8ec013242c823d33aff0f0144e5d870786a96c`; raw stderr is 1,142 bytes / `7707fdb940e769613fe4dde982f6d6e501aa12d904b09fe0e58dc0f3d42b894f`. It passed 73,999/73,999 generator/domain matches, 52,803 state/ATR/breaker matches, 51 payloads, January 27,658 / April 25,056 / May 21,285, 2,357 reused candidate IDs covering 17,206 rows, and zero duplicates, unmatched, out-of-window, postdecision, H1, state, source, leakage, identity, slice, authority, or generator mismatches.

The M1 verifier ran once from `2026-08-02T02:24:15Z` to `2026-08-02T02:25:16Z` and exited zero. Raw stdout is 751 bytes / `4b110695ab0e4ca8946478045e743ffb89871262071099e94939b6816db5249b`; stderr is empty / `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`. It passed 2,188,895 M1 rows, 147,690 exact M15 buckets, 120 partial H1 buckets, 46 referenced, 37 M1-proven, and nine source-preserved December/session gaps.

## Sparse-M1 repair

The HR failure demanded every wall-clock minute. Independent read-only inventory proved 6,405 legitimate sparse intervals, 15,119 absent civil-minute timestamps, and 5,277 gap-affected M15 buckets, while all 147,690 independently derived M15 canonical rows matched the packet exactly. The repair removed only that false continuity proxy. It retains strict schema, true UTC, grid, geometry, order, path, hash, row-count, coverage, denominator, exact-domain, and exact-OHLCV enforcement. No bar was synthesized and no experimental look was spent.

## Adversarial and preservation result

The disposable matrix ran once from `2026-08-02T02:25:30Z` to `2026-08-02T02:25:32Z`: 59 passed. Raw stdout is 9,522 bytes / `460d56bdb5d149264bc3c6b1745ed062e089cc3c0ec500b26d0f7987d4d0ae84`; stderr is empty. It covered manifest/root/path/symlink/inventory/schema/OHLC/outcome/multiplicity/slice/transitive/U4/U5/U11/B0/runtime failures plus sparse positive controls and M1 deletion, mutation, type, bucket-domain, order, traversal, and hash attacks.

The canonical inventory listing is exactly `ff272cee01ed474f031dbd7ac400f6d7a9b910f9ebc1de340cb6554a218b89db` before and after. Trusted recursive inventory hashes are HN `915fc33ad2a3ee2fc7d8b0eae33b01ef20130e4aaa0a60ca7fa532f37139f4b7`, repaired `7eb5b127769f07111e18f7ef584876916c66357e600fb47c736f7f4c2e2dc731`, and canonical `ff272cee…`; all share payload-only listing SHA `b374f9a5279ba96c6fa1821b3deb8c85975381b6fd7381f7ad569449b6556c25`.

## Incident ledger

1. Original HP/HO interrupted work was preserved without a terminal claim.
2. An HO internal reviewer made an over-broad search that printed unrelated legacy JSONL profit/swap rows. The output was quarantined, excluded, and never treated as P1 evidence.
3. During canonical proof monitoring, a separate read-only helper made an over-broad archived-document search that surfaced unrelated legacy economics. That output was also quarantined and excluded; no active P1 result or bound outcome file was opened.
4. Wrong-source result PID `89784` was killed before output decoding; no P1 result was consumed.
5. The root continuation exited its scope gate without duplicating source work.
6. Accidental `generate_live_state` dirt was restored; the accepted source remained clean.
7. Accidental commit prefix `6a599591…` included the context anchor and is permanently superseded and non-authoritative.
8. HQ's default-parent refreeze reached reconstruction but failed closed on the existing content-addressed leaf; HN stayed unchanged.
9. The repaired hold from `8e7710da…` passed its full generator proof, then HR exposed the false civil-minute continuity invariant. No outcome ran.
10. The visible HS Sol launch was quota-refused and produced no authoritative work.
11. `880eda679f8160c79e074826a9e1e18f66803778` is a weaker two-file diagnostic child of `8e7710da…`, not authority.
12. `840d12ae10f304c7d47a341e6a059703838919a9` broadened lineage but remained incompatible with the unchanged verifier's direct-parent contract; it is not authority.
13. Repaired2 PID `7868` and repaired3 PID `16862` were deliberately interrupted by another orchestrator after the safer direct-parent successor `9059cfa…` existed. This was conflict resolution, not a data failure. Repaired2 remains 50 files / 17,042,178 bytes / no manifest; repaired3 remains 50 files / 16,303,457 bytes / no manifest. Neither may be resumed, deleted, renamed, or treated as a packet.
14. An early `git status` from the wrong working directory failed harmlessly before the guarded launcher.

## Instruction coverage and decision

All source lineage, payload equivalence, exactly-once proof, sparse-M1, disposable attack, trusted-packet preservation, false-authority, broker-inert, no-economics, no-March-outcome, and evidence-only requirements are mapped to the context anchor and machine receipts. The implementation decision is `ACCEPT_CANONICAL_SOURCE_CONTROL_REPAIR`; the branch decision is `READY_FOR_SEPARATELY_COMMISSIONED_OFFLINE_P1_RESULT`. This is not merge, paper, live, or activation authority.
