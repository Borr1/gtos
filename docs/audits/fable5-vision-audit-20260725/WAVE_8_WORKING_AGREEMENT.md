# Wave 8 — working agreement

**Orchestrated by Fable 5, cut 2026-07-30 from the wave-7 evidence.** The standing correction is
unchanged and still not a mood: **the default is that a sleeve can be made to work and your job is
to find how.** A sleeve leaves the queue only after its enumerated repair paths are shown to fail,
and "leaves" means parked with its repair list, never killed. If a check would end in "therefore
reject", turn it into "therefore repair X". Verify that your repairs do what you claim — that is
where the rigour points, not at manufacturing grounds for rejection.

Wave 7 executed the estate's prescriptions and changed the map: every sleeve's exit surface
improves but none admits on its own (`significance` everywhere), breadth is refuted (2 of 30
families cohere), and the binding constraints are **exit geometry, member conditioning, and the
multiplicity bill** — each of which wave 8 now owns a lane of. Read
`phase7/SESSION_AD_EXIT_REPAIR_RESULT.md` §0, `phase7/SESSION_AF_FAMILY_EXPANSION_RESULT.md` §0
and `phase7/SESSION_AE_LEARNING_DIRECTION_RESULT.md` §0 before your own prompt.

**Three standing instructions from Borhen, 2026-07-30, verbatim in spirit and binding:**

1. **Use your own judgment throughout.** Your prompt is a commission, not a script — if the
   evidence says the work list is wrong, follow the evidence and say so in your report.
2. **The posture is build, improve, fix — never refute-and-stop.** When a measurement comes back
   negative, the deliverable is the repair it prescribes, the conditioning that would rescue it,
   or the exact data that would close it. "Therefore reject" is not an ending this programme
   accepts; "therefore repair X" is. Rigour points at verifying your repairs do what they claim.
3. **You have explicit owner opt-in to use the Workflow tool (multi-agent orchestration)**
   whenever fan-out genuinely helps: parallel sweep cells, independent adversarial verification
   of your own findings before you publish them, breadth of member coverage, judge panels over
   competing repair designs. Borhen asked for this in his own words — treat the opt-in as
   standing for every substantive task in your lane, and spend it where verification quality or
   coverage buys the most.

---

## 1. Authority and the live account

1. **Your session prompt.** 2. This agreement. 3. `FOURTH_REVIEW.md` (the plan of record; its §3.3
sequencing is amended by the wave-7 results named above). 4. `CLAUDE.md` (wave-7 plan position is
current). 5. Everything else — historical unless a current artifact says otherwise. If your prompt
and a repo document conflict, follow the prompt and say so in your report.

**FTMO IS LIVE AND TRADING REAL MONEY** — armed 2026-07-29, adjusted 14:25 UTC to three sleeves:
`crypto`, `energy_agri`, `sub_xvol_pullback` via `run_book.py --tags`. Therefore, verbatim from
waves 6–7:

- **Do not edit `config/agent_config.yaml`** — the live activation token binds its digest
  (`ffe16657feaf`); one byte stops the armed book placing.
- **Never run a broker-capable script**: `run_book.py`, `run_agent.py`, `fn_smoke_trade.py`,
  `mt5_preflight.py`, `dual_broker_execution_follower.py`, `start_all.bat`,
  `.tools/monitor_books.py`, `flatten_all_positions.py`,
  `emergency_close_and_stop_redacted_account.py`. `create_mt5("live")` *succeeds* on macOS — the
  ImportError only surfaces on `.connect()` — so construction is **not** a safety boundary.
- **Nothing you do touches the VPS.** VPS-side changes ship only as owner-executed carry packages.
- **H1**: check decision-contract membership before editing anything under `src/` (`CLAUDE.md` §3,
  R2 contract). The walkforward / validation_integrity / learning / ultimate_book sleeve surfaces
  have been verified unbound repeatedly — but check anything new you touch. **Read H1's LFS caveat
  as amended 2026-07-30**: for the sleeve-registry ledger the pointer oid is NOT the contract hash;
  never "clean up" `/Users/borr/GTOSActive/repo`'s dirty working copy of it.

## 2. Verification — the committed baseline is live. Read this even if you ran wave 7.

Session AT landed: the standing failure set is **67** (36 KEEP-REAL on purpose, 25 precondition
skips, 6 hydration-pending), and `scripts/pytest_failset.py` now has `scope` — a diff maps to the
tests that can observe it, fail-safe (anything unmappable escalates to `tests/`).

1. **Commit your implementation first**, in scoped commits, before any capture or long run.
2. **Name your blast radius** with `python3 scripts/pytest_failset.py scope` over your diff (plus
   your own new tests), run that scope at your HEAD, and embed the receipt in your result doc. A
   suspicious failure is verified by running the same scope at your merge-base — never the full
   suite.
3. **Any suspected regression is re-run in isolation at HEAD and at base before you believe it.**
   `KNOWN_LOAD_FLAKES` grows only with the evidence its docstring demands.
4. **The full suite is the orchestrator's, once per merge train**, diffed by failure set against
   the committed baseline capture at
   `docs/audits/fable5-vision-audit-20260725/receipts/FAILSET_BASELINE_MAIN.json`. Do not re-capture
   the before side; it is committed.
5. **Sets, not counts.** And do not "fix" a skip whose reason names an absent input — the skip IS
   the correct state until the input exists.

## 3. The trial-budget ledger is mandatory and now carries 4,785 look events

Every variant you evaluate goes to `research/operations/trial_budget/TRIAL_LEDGER.jsonl`
(append-only JSONL, `session:` tag, safe for concurrent sessions — but note the path is
**sparse-checkout-excluded** in fresh worktrees: `git sparse-checkout add
research/operations/trial_budget` first, then confirm the file has AA/AD/AF/AE rows before
appending). Admission statistics deflate against the measured count. No variant is forbidden and
nothing waits; the ledger is what lets aggression and honesty coexist.

## 4. Machine discipline

- **Memory is the binding constraint.** Three wave-8 sessions share this machine. Chunk
  archive-scale runs; scope every wait to your own worktree by path, never machine-wide.
- **Reuse the walked substrate before regenerating.** `phase6/receipts/AA_ESTATE_TRADES.json.gz`
  (22,324 trades with intents), `phase7/receipts/AF_FAMILY_TRADES.json.gz` (134,027 trades,
  path-stats, regime-labellable, reachability-flagged), `phase7/receipts/EXIT_FRONTIER_V1.json`
  (1,631 gated cells). Exit re-simulation from stored intents costs minutes; only regenerate when
  the repair changes *generation* (stop width, new symbols, entry timing).
- **Bars and ticks are broker wall clock, not UTC.** Convert with `src/utils/broker_clock.py`.
  Bars archive `/Users/borr/GTOSActive/vps-bars-20260727/` (41 instruments — the "43" in older
  docs double-counts two dotted-name re-exports, AF §1.3), ticks
  `/Users/borr/GTOSActive/vps-ticks-20260726/`.
- **Sparse-checkout lies twice.** A committed file can be absent with `git status` clean
  (`git sparse-checkout add` hydrates), and `research/operations/spread_model_2026_07_29/` being
  outside the cone makes every `spread_band=` verdict silently unavailable — hydrate it before
  pricing anything.
- **The spread model has a known composition defect (AF §6):** era_ratio × hour multiplier is
  unvalidated as a product and reaches 198× on pre-2010 FX. Until Session AH repairs it, restrict
  banded pricing to `era_class == RECORDED` (outcome-independent) exactly as AF did, and say so in
  any row it touches.
- **Engine-reachability matters at D1**: every Friday is a pre-gap bar (AB's defect, 4.26 % of D1
  trades, unreachable live). Use AF's `engine_reachable` flag; default every economic number to the
  live convention, publish fix-enabled as a sensitivity band.

## 5. Block allocation

Wave 7: AD `B750–B757` · AF `B800–B818` · AE `B850–B883` · AT `B900–B912` — all landed.
**Wave 8: AK `B950–B999` · AH `B1000–B1049` · AI `B1050–B1099`.**
Need more? Take the next free 50 above `B1100` and record it in your result doc. Whoever raises
the block ceiling past a sibling's allocation owns `IN_FLIGHT_WAVE_RANGES` in
`tests/test_implementation_state_block_citations.py` — the mechanism is documented at the constant.

## 6. What "done" means

1. Implementation **committed on your branch** — do not merge to `main`.
2. The §2 scoped verification, receipt embedded in your result doc.
3. Every trial logged to the ledger (§3).
4. Blocks appended to `IMPLEMENTATION_STATE.md`, tagged `[MEASURED]` / `[VERIFIED]` /
   `[UNVERIFIED]` — append only; never renumber another session's blocks.
5. **Repair-queue updates append, never overwrite** — rows tagged with your session id beside the
   134 standing rows (+ AD's 49 in `phase6/receipts/REPAIR_QUEUE_APPEND.jsonl`).

## 7. Reporting

State what you measured, what you repaired, and what you got wrong and withdrew. Cite `file:line`
for production-state claims. **Never report a rejection as a headline: if a variant fails, the
headline is the next prescription.** Numbers over adjectives, and give Borhen the number that lets
him decide something. Wave 7's own results are the standard — including their "what I got wrong"
sections, which caught four errors before they cost a sibling session anything.
