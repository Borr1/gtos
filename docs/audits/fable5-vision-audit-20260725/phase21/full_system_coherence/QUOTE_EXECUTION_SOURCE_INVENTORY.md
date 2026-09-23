# Wave 21 quote execution source inventory

Status: `SOURCE_BOUND_PARTIAL_COVERAGE`. This inventory does not establish broker
fill, queue, order, deal, position, or economic truth.

## Claim boundary

Ordered BID/ASK rows can support three deliberately separate statements:

1. A passive LIMIT was *correct-side touch eligible*. This is an optimistic
   first-touch condition, not a fill.
2. A quote-only lifecycle can be *modelled* after an explicit post-Scheduler order
   intent and submission/ack boundary. MARKET uses the first strictly causal far-side
   quote; LIMIT retains its price bound. Exits use ordered executable-side quotes.
3. Broker fill remains `NOT_EVALUABLE` without broker order acknowledgement, queue or
   depth, deal, and position-event evidence.

M1/M15 bars do not substitute for ordered quote causality or broker execution. The
historical stored-candidate comparator is not an authority input to this inventory.

## Frozen October/November estate

Current hold:
`/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1`

The October manifest root is
`9f05faa3de9a96546ae67f5420d9f2ada190b4e2613a67b04cddfe1a1e98236f`; the
November root is
`e2212e97fce1f8aafe3ea7b3e3479387f89dccd7eaa55b6d81f4415eda139d7c`.
Both declare `LANE_ITERATION_EVIDENCE - unbilled exploration, never
admission-grade`, true UTC produced with registered rule `new_york_plus_7` and
`broker_epoch_to_utc`, and the same FTMO account/server hashes.

The eight raw files were rehashed and streamed in their captured order. Across
18,212,026 rows: JSON parse failures = 0, naive timestamps = 0, invalid or crossed
quotes = 0, and timestamp inversions = 0. Equal-time rows were retained in source
order; no sorting or deduplication was performed.

| Window | Symbol | Rows | SHA-256 | First UTC | Last UTC | Equal-time successors |
| --- | --- | ---: | --- | --- | --- | ---: |
| Oct | EURUSD | 1,200,205 | `51c676df3a1a4a2b13bd3b457df13cf9d1e90824e9886e19437d36d3fcc3806b` | 2025-10-01 00:00:00.192 | 2025-10-31 20:54:59.871 | 179 |
| Oct | USDJPY | 1,696,169 | `a121ff89295475881891ab9cc693c373d9693ce3936bcb9e949d8071e4877bc6` | 2025-10-01 00:00:00.192 | 2025-10-31 20:54:59.204 | 364 |
| Oct | XAGUSD | 2,733,115 | `965d8764daa6a0c0253b965162e15c02040eaa638a6bd2a2791ccd2a6cd6e5ec` | 2025-10-02 09:00:00.295 | 2025-10-31 20:49:39.190 | 1,361 |
| Oct | XAUUSD | 4,057,658 | `9e7cf234bd3db7e8343c6d3cc41ff38371ee5dcf4d9903aef3aae72255fd3a42` | 2025-10-01 00:00:00.520 | 2025-10-31 20:49:59.165 | 3,226 |
| Nov | EURUSD | 985,064 | `f43d043a91c9981da74a80c0e4987e392da5d166f045ab64238908cfa5c7f940` | 2025-11-02 22:05:00.359 | 2025-11-28 21:54:54.508 | 52 |
| Nov | USDJPY | 1,597,221 | `55a87b5cfba11b6d2d7ff4e0fa5edf85448e76f68669dd70865fca550b3d344c` | 2025-11-02 22:05:01.698 | 2025-11-28 21:54:54.506 | 54 |
| Nov | XAGUSD | 2,618,841 | `d783132cd040759c698646e2fd7e4168316b6ae1e71d7bb255d81e78360d8928` | 2025-11-02 23:05:00.096 | 2025-11-28 19:44:58.759 | 142 |
| Nov | XAUUSD | 3,323,753 | `c363eafd10c2768d0349205535f7b7d74da89ae25d638eb514d5952353ec4e9a` | 2025-11-02 23:05:00.086 | 2025-11-28 19:44:59.759 | 1,027 |

Coverage is candidate-specific, not calendar-wide. In particular, October XAGUSD
starts on October 2. Any no-touch, no-terminal, or scheduled horizon outcome requires
verified continuous coverage from the explicit submission/ack boundary through the
required horizon and an explicit executable quote strictly before that horizon. An
observed stop/target event can be modelled on a verified shorter prefix, but missing
capture after entry cannot be turned into a time-stop.

## Exact frozen-window gaps

Both manifests retain one terminal gap row with
`status=no_captured_tick_source_for_symbol` and
`ordered_tick_truth_satisfied=false` for each of these twenty symbols:

`AUDJPY`, `AUDUSD`, `BTCUSD`, `CHFJPY`, `ETHUSD`, `EURGBP`, `EURJPY`,
`GBPJPY`, `GBPUSD`, `GER40`, `JP225`, `NAS100`, `NZDUSD`, `SPX500`, `UK100`,
`UKOIL_cash`, `US30_cash`, `USDCAD`, `USDCHF`, and `USOIL_cash`.

The approved local holds, worktrees, source manifests, and direct same-window
tick/quote path names under `/Users/borr/GTOSActive` and
`/Users/borr/Documents/gtos` were searched. No second October/November ordered-quote
estate for these symbols was found. This is a current-disk acquisition gap, not proof
that an unnamed external archive cannot exist.

## Exact acquisition contract

Result-bearing acquisition for a missing symbol requires all of the following:

- the same frozen October/November window and declared broker/server/account/source
  role, or a separately named comparator arm;
- raw ordered BID/ASK rows with captured sequence or ordinal preserved, including
  equal timestamps; no stable sorting, silent parse drops, quote repair, or inferred
  sides;
- timezone-aware true UTC, or raw broker time plus an exact schema/server/timebase
  sidecar and registered clock conversion;
- a manifest binding every component hash, row count, first/last instant, row locator
  or row root, parser/code identity, invalid-row count, and inversion count;
- coverage from the explicit post-Scheduler submission or acknowledged boundary
  through pending expiry, an observed terminal, or the required scheduled horizon,
  with an explicit strictly-before-horizon executable quote for a modelled close;
- final MARKET/LIMIT intent and approved entry, stop, target, units/risk basis; and
- broker order/ack/deal/position plus queue/depth evidence for any statement stronger
  than touch eligibility or a modelled lifecycle.

Absent those inputs, fill/lifecycle is `NOT_EVALUABLE`; candidates remain in the
denominator with their source-gap disposition.

## Later estates: separate follow-up windows only

Two local FTMO exports cover all 24 symbols and may support a later bounded engineering
window, but they cannot be substituted into the frozen October/November graph:

| Estate | Window | Files | Rows | Declared scope |
| --- | --- | ---: | ---: | --- |
| `bridge_ftmo_ticks_v122i_20260513_20260517_full_plus_expiry` | 2026-05-13 00:00 to 2026-05-18 02:00 UTC | 24 | 9,941,602 | ordered price path only; no broker lifecycle truth |
| `bridge_ftmo_ticks_v127_b7_3_20260601_20260605_full_plus_expiry` | 2026-06-01 00:00 to 2026-06-06 02:00 UTC | 24 | 15,847,737 | ordered price path only; no broker lifecycle truth |

Both declare the same FTMO account/server hashes and
`source_role=owner_authorized_path_override`. The separate June/July VPS and
redacted_account captures are likewise later-window sources, not frozen-window repairs.

## Code baseline

At plan commit `01446b383`, the cleared generic quote-side commits `cd3ccd3cb` and
`b9df90f44` are already ancestors. They provide ordered tick validation, correct-side
LIMIT touch, time-varying short ASK exits, first-tradable gap prices, and broker-target
priority over an unproved same-quote client partial. The Wave 21 callable seam is kept
outside the currently misordered timewarp graph: integration must invoke it only after
Scheduler/risk has produced explicit order intent and an actual submission/ack
boundary.
