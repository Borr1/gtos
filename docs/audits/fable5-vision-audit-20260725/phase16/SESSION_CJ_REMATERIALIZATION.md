# Session CJ — the re-materialization: correct clocks, fresh windows, the seal broken on purpose (wave 16, B2550–B2599)

**Codex session. The conventions in `phase15/SESSION_CG_LANE_FOOTPRINT.md` §"Conventions that
bind you" apply verbatim.** Read first: `phase14/SESSION_CD_BROAD_REGENERATION_RESULT.md`
§0.3 + H-CD-1 (the defect you repair: the sealed January source is broker wall clock
mislabelled UTC, +2.0 h; April +3.0 h; not rebind-repairable), `phase14/receipts/` CD's
prediction/delta receipts, `src/utils/broker_clock.py` (the sanctioned conversion),
CLAUDE.md §3 H1/H4 (what the seal binds and where absolute paths bite), the wave-11
agreement §6 (surfaces; January is VAL), `WAVE_11_WORKING_AGREEMENT.md` §4.

**Owner authority, quoted because it is the whole charter: Borhen, 2026-07-31 — "yes you can
break the seal and proceed as proposed."** Consequences you state rather than hide: the
parked B7.5 campaign's resume option (sealed-window comparability, ~36 MH) is DEAD from the
moment a re-materialized January exists — the orchestrator records that in the decision
queue; the frozen engine's sealed artifacts remain untouched history; everything you build is
a LANE input (provenance-stamped, unsealed), never a sealed-campaign input.

**The objective in one sentence:** re-materialize replay source bundles and prepared day
packs under the REPAIRED exporter (true UTC via `broker_clock`) for the lane's 2026 windows —
January (re-clocked), February (never materialized), April, May — so the lane can regenerate
at scale on honest clocks and the hour axis stops lying.

## Work orders

**CJ-1 — The repaired export path, proven on January.** Re-run the source materialization
for January 2026 through the 2026-07-26-repaired exporter (broker epoch → true UTC via
`broker_clock.broker_epoch_to_utc`). Validation gates: the 54/54 weekly-open check must now
land at the true-UTC session open (state what it is per the US-DST rule, and show it
DST-invariantly); a bar-by-bar overlap diff against the sealed bundle must show EXACTLY the
uniform +2.0 h shift and nothing else (any non-uniform residual = stop and report).

**CJ-2 — Day packs for the lane.** Build prepared day packs from the re-clocked sources for
January, February, April, May 2026 under a LANE namespace (never the sealed roots; H4 warns
absolute paths bind — keep the lane roots relocatable and say where they live). The pack
fields computed at build time (`kill_zone` / `session` / `utc_hour_bucket`) are the whole
point — they are now honest. Register the roots with the guard/partition wiring so
`--purpose LANE_ITERATION` resolves them (surface axis: all four months are VAL).

**CJ-3 — The invariance measurement.** One regenerated January arm on the re-clocked packs
vs CD's regenerated arm on the sealed packs: the ECONOMICS should be invariant (a uniform
shift moves no R) while every hour-of-day feature shifts by exactly 2 h. Measure both, don't
assume either. If economics move materially, that is a finding about session-conditioned
logic in the pipeline — report it, don't smooth it.

**CJ-4 — The hour axis, re-stated once.** AW's 81-cell `B_TIME` axis and any hour-of-day
claim in the estate's receipts are shifted +2 h on sealed-January data. Publish the
correction table (old label → true UTC label) as ONE receipt other documents can cite, and
list which standing conclusions (if any) change when the labels move — CD §0.3 expects none
economically, but entry-hour work (AH's lever, CE/CH's JPY gate) touches hour labels and
must be checked against the shift.

**CJ-5 — February.** The first window nobody has ever read at ANY clock. State its data
completeness honestly (bars/ticks available per symbol), build its packs, and leave it as
the lane's freshest VAL window — do NOT run economics on it in this session beyond a
smoke-day proving the packs load; scoping its first read is the trainer loop's call, not a
materialization session's.

## Done means

Result doc `phase16/SESSION_CJ_REMATERIALIZATION_RESULT.md` findings-first + receipts under
`phase16/receipts/`, blocks B2550–B2599, iteration-ledger rows for every VAL look, scoped
A/B vs the ZERO baseline with the tool-emitted fence, honest what-I-got-wrong, handoff list.
Never touch the VPS; never run broker-capable scripts; never edit `config/agent_config.yaml`,
`config/profiles/redacted_account.yaml`; the FROZEN sealed artifacts and R2 contract files are
history — read them, never rewrite them; March 2026 stays outcome-unread on every path
(re-materializing March's SOURCE is allowed by the owner's decision ONLY if you never read
outcomes — safer: skip March entirely this session and say so). Keep heavy runs ≤2 concurrent
while sibling sessions finish.
