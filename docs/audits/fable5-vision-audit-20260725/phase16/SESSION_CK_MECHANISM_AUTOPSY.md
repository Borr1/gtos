# Session CK — the mechanism autopsy: why is the family wrong about direction (wave 16, B2600–B2649)

**Codex session. The conventions in `phase15/SESSION_CG_LANE_FOOTPRINT.md` §"Conventions that
bind you" apply verbatim.** Read first: `phase14/SESSION_CD_BROAD_REGENERATION_RESULT.md`
H-CD-8 (your charter), §3.3–§3.6 and §5 (what is already measured), the committed pools
(`phase14/receipts/pools/CD_REPAIRED_POOL_*_V1.jsonl.gz`, 4 arms × 28.5k rows × 78 columns),
`phase12/SESSION_AW_SEPARABILITY_MINE_RESULT.md` (the methods you inherit: declared cuts,
controls, holdout discipline), the wave-11 agreement §1/§6. Owner authority:
OD-HISTORICAL-FIRST and the training-lane ratification.

**The objective in one sentence:** the broad family loses 0.22 R/row before any cost and hits
16.8 % against a 33.3 % break-even — decompose WHY (entry rule, target geometry, stop
geometry, or exit model), on the committed pools, with zero replay.

## Work orders

**CK-1 — The geometry sweep, entries held fixed.** On the repaired pools' own rows: re-price
every row under a declared grid of target/stop geometries (the rows carry the path data the
first-touch model used). Declare the grid and the cut rules BEFORE reading outcomes; log
every look (VAL, unbilled, session CK). Deliverable: the geometry surface — is there ANY
(target, stop) cell where the entry set is net-positive, and if not, how far is the best
cell from zero? That answers "is the deficit in the exits" in one table.

**CK-2 — The direction test.** The brutal control: invert every entry (short↔long) and
re-price at the same geometries. If inverted entries are ALSO negative, the deficit is in
COSTS-vs-geometry, not direction; if inverted turns positive, the entry rule is
anti-predictive and that is a different repair path (and a curious one — an anti-predictive
signal is information). State which world the data says we are in.

**CK-3 — The exit-model check.** CD flagged the first-touch exit model as one suspect.
Measure its bias on these rows: where both target and stop are inside one bar, first-touch
resolves by an ordering assumption — quantify how often that case decides the outcome and
bound its worst-case contribution to the −0.22.

**CK-4 — The entry taxonomy.** The pool carries generator/blocker/candidate columns: which
entry sub-families carry the loss? AW's separability said no cell is net-positive — your
question is different: RANK the sub-families by gross-per-row and say whether the loss is
uniform (mechanism globally wrong) or concentrated (a fixable subset). Controls: AW's
random-split null on anything that looks concentrated.

**CK-5 — H-CD-7, the `--days N` hang.** A bounded debugging job the lane needs for mid-size
gradients: `--days 2` clean, `--days 12` stalls (0 % CPU, main thread in
`lock_PyThread_acquire_lock`; suspect: `sealed_inputs.build_january_args` narrowing
`expected_prepared_day_pack_roots` × the prewarm pool). Reproduce (90 s), fix, prove
`--days 12` and `--days 20` run, and re-state CB's CB-3.3 gate as proven at the sizes it now
is. If the fix threatens outcome identity, gate it behind the acceptance comparator before
shipping.

## Done means

Result doc `phase16/SESSION_CK_MECHANISM_AUTOPSY_RESULT.md` findings-first + receipts under
`phase16/receipts/`, blocks B2600–B2649, every look logged unbilled, scoped A/B vs the ZERO
baseline with the tool-emitted fence, honest what-I-got-wrong, handoff list. Never touch the
VPS; never run broker-capable scripts; never edit `config/agent_config.yaml`,
`config/profiles/redacted_account.yaml`, or any R2-bound path; March 2026 outcome-unread. Nothing
here bills the family; a genuinely positive cell gets FILED with its surface map, never
graduated by you.
