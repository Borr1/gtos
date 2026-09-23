# LAND gate — landing summary for Borhen (OD-FA2-2)

Session FA continuation, 2026-08-04. This is the owner-facing summary the commission requires
before the integration branch merges to `main` on your explicit word. Merge executes ONLY on
that word.

## What merges: branch `phase19/fa2-integration`

Built from `main` (f8c05d0ac) exactly per the landing recipe, plus the adjudications the
recipe's own intent required:

1. **The wave-20 program tip `502d90616`** (fast-forward adoption) — the entire Sol/wave-20
   chain: FG's integration of CR/CS/FB–FF (all 66 commits, content-verified), the
   falsifier-paired HA→HP chain, +572,576 lines, zero config/token/contract/component touches.
2. **Five doc-only session-close leaves cherry-picked**: HK, HL, HM, HN (per recipe) + **HIA**
   (found absent from the tip's tree and register — same class, so landed; deviation disclosed).
3. **HV adopted** (`4ae182bb6`): the 3,092-line P1 offline complete-path runner + its test +
   the frozen fill-authority prereg. Runner byte-identical to HV's copy; all 10 standing test
   failures were stale fixtures (repaired; 33/33). P1 execution stays PARKED.
4. **HM falsifier reconciled** (`0a838e49a`): 23 failures were stale expectations against HP's
   receipted adapter contract; 71/71 now; adapter bytes untouched.
5. **Relocation of docs/-resident production code** → `src/research_infra/` (five files; the
   P1 adapter keeps an immutable docs copy pinned byte-exact because the frozen canonical
   packet verifies that path from the working tree).
6. **`phase20/p1-m1-sparse-repair` DISCARDED** (HP repudiation; recorded).
7. The predicted B0 node-id/scanner collision adjudicated exactly as prescribed (KNOWN_GHOSTS
   entry, `82a1482de`).

## The two fences

- **(a) Full suite vs the sealed wave-20 baseline (12,809/2/0): PASSED — 13,304 passed /
  2 failed / 0 errored; ZERO regressions by failure set** (+495 net new passing; one baseline
  failure fixed; the single flagged ID is a registered load-flake, re-verified 1/1 isolated +
  29/29 module at this head). Receipt with embedded captures:
  `phase19/receipts/SESSION_FA_AB_RECEIPT.md`.
- **(b) 2-day January lane arm vs the sealed CJ baseline's first two days: PASSED —
  ZERO economic mismatches, zero unclassified differences, zero unjoinable rows across
  all eight ledgers** (identity joins, never sort order: TRADE 4/4, ORDER 8/8, ORACLE
  4/4, DECISION 4,608/4,608, SCORECARD 96/96, MISSED 8,448/8,448 with all 14 must-equal
  economic fields equal on every row, BUCKET 409/409 with every aggregate equal,
  SOURCE_UNIVERSE 174/174 with content anchors equal). Every difference proven
  non-outcome in six classes — namespace identity, hashes of namespaced/window-scoped
  payloads (nine per-field proofs: payload reconstruction with a natural control,
  432/432 sidecar-id rebuilds, 6/6 `source_sha256` slice hashes reproduced byte-exactly
  from the lane CSVs with the 2-day slice an exact prefix of the 31-day slice), CN's
  authorized v2→v3 stamp (every charged component byte-equal, e.g. commission
  0.005362274003855769), the retired-proxy diagnostic (Δnew−Δold = commission_r exactly,
  3,119/3,119), missed-pool projection v1→v3 field-set changes, and 31-day-vs-2-day
  window-scope fields. Receipt: `phase19/receipts/forensic/FENCE_LANE_ADJUDICATION.md`
  (commit `afbb6b5dc`).

**Both fences PASSED. The gate is green. The merge waits only on your word.**

## What the A-phases established (receipts committed on `phase19/broad-forensic`)

- **A1 (blind clean-room): the breaker gate's permutation rule is defective** — not
  rotation-invariant (verdict flips at 14/31 rotations; support capped at 2¹¹=2048). At the
  corrected null the inverted breaker **ADMITS at the ratified rule** (p 0.00130, q@59 0.0769,
  α 0.10) — three independent corrected constructions agree; fragility disclosed (flips if
  fold persistence ρ≥0.6; measured 0.372±0.175). DEVELOPMENT-FITTED windows; March remains the
  only confirmatory read, on your word only.
- **A1b (re-issued family table): ⚠ ONE BINDING FLIP REACHES ARMED MONEY** —
  `mx_btcusd @ target_5R` (live on FTMO since 07-31) **flips ADMIT→REJECT at flat/low/mid
  bands under the corrected null** (q 0.129–0.135 vs α 0.10). Precision: it still admits at
  MEASURED dependence (p 0.00135); the REJECT comes from the +1SE dependence variant — the
  admission carries **less than 1 SE of model margin** (the breaker's ADMIT survives its own
  +1SE). Dis-arm / keep / re-read is YOUR decision — flagged, not taken. (Registry weight
  0.025 — economically small by design; the forward record is the point.)
- **A2**: every Codex headline spot-recomputed from raw pools — FB reproduces bit-identically
  (198 cells, max deviation 0.0); two circulating claims refuted (details in the RESULT doc);
  the contradiction register resolved 15/16; the loss-class rule ratified (exit_geometry is
  the dominant executed loss class both months: −19.95 R of January's 55 scoreable,
  −13.97 R of February's 58).
- **A3/A4**: 28-branch disposition table; WAVE20 supersession register; four iteration-ledger
  rows (all `billed:false`); WA §4 wave-19/20 records + the B3100–B3199 block take.

## The trigger phrase

Say **"land it"** (or equivalent explicit words) and I merge `phase19/fa2-integration` into
`main` with the A/B receipt embedded in the merge commit. Both fences have returned PASS, so
the gate is fully green. Development (Phase B/C/D) continues on the integration branch
meanwhile; `main` is touched at this moment and the closing ceremony only.
