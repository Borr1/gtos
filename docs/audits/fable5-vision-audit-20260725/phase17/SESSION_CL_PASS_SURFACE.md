# Session CL — widen the pass surface: every armed-set extension, priced at firm-true rules

Session: CL · Wave 17 · Blocks **B2650–B2699** · Branch `phase17/pass-surface` ·
Worktree `/Users/borr/GTOSActive/worktrees/wave17-pass-surface-20260801`

**Authority: OD-ALL-IN (`phase17/OD_ALL_IN_20260801.md`) — read it first, whole.** The owner
has directed: no new accounts; more sleeves and more live testing ON the two existing
challenge accounts; anything the factory approves goes live on both accounts directly. Your
job is to turn that from a sentence into a priced, per-account, ceremony-ready package. The
orchestrator executes the ceremony; you build everything up to it.

Standing owner directives (embedded in every session since wave 8): use your own judgment —
this commission is a brief, not a script; build/improve/fix, never refute-and-stop; the
Workflow tool is opt-in-approved if you want multi-agent fan-out.

## The question

The registry resolves 32 sleeves. FTMO arms 5 (`crypto, energy_agri, sub_xvol_pullback,
sub_mid_dn_revert, mx_btcusd_d1_donchian_20_breakout`), redacted_account arms 4 (same minus mx).
Which currently-unarmed sleeves should be armed, on which account, at what confidence — and
what does each do to the pass probability and the payout clock?

## Work orders

**CL-1 — enumerate the candidate set from evidence already on disk.** At minimum:
`fx_jpy` (MEASURED_LIVE_CARRY — the broker charged swap on 0 of 41 live JPY positions),
`fx_jpy_ny` (CARRY_CONDITIONAL_LIVE_SUPPORTED), `vp_euidx_pocgrav` (UNCONDITIONAL on
redacted_account per `SURVIVOR_BOOK_V1.json` — note the account-tier swap with `metals_core`, B358),
`mx_btcusd` on redacted_account (incubation extension: FN's decision timeframes are `[16388]` today;
mx needs its generating timeframe — measure what that requires and what else a tf change
admits), `metals_core` on either account (AE's cost-true verdict is DOWN_WEIGHT ×0.50 — if the
evidence says no, the answer is no), and anything else the survivor book or wave 7–9 receipts
support that we have simply never armed. Read the tiers from the artifact, never from prose,
and read them PER ACCOUNT.

**CL-2 — price every candidate at firm-true rules.** Use the existing
`INTEG_portfolio_build.py` / `MC_FIRM_TRUE_V1` machinery (firm-true: FTMO static $90k floor,
redacted_account rules as measured; phase 2 at 5% both firms; worst-carry and forward variants).
Deliver, per candidate set: `p_pass` phase-1, `p_pass` 2-step, expected %/month, expected
calendar days to payout, and the marginal delta vs the current armed set. The current armed
sets are the baseline; a widened set that LOWERS 2-step `p_pass` materially needs to say so in
bold. In-window vs out-of-window economics stated separately, per the standing honesty rule
(the 5.46 headline vs +0.100 OOS lesson).

**CL-3 — the incubation proposals.** Up to 4 free slots at ≤ 0.05 confidence
(`phase14` incubation registry, CC's rules). Propose the strongest near-admission candidates
with their measured basis (e.g. AL's closers output, `sub_xvol` vr≥1.4 variant state, AK's
`asia_pdl_fade` exit cell). Each proposal: the dossier the registry demands, the bounded
confidence, the live veto conditions, and what live data would graduate or kill it. Do not
bill any new look for this — these are existing measurements being armed at bounded size,
disclosed in the iteration ledger as unbilled carries.

**CL-4 — the ceremony package.** CE's `activation_carry_spread_floor/` is your template:
MANIFEST with hashes, exact supervisor-args diffs (`run_book_supervisor.ps1` hashtable keys +
`--tags`/timeframe args), preflight checks against the HOST's actual bytes (assume drift;
verify), verify script, stop conditions, and rollback. **Constraints that are absolute:** no
byte of `config/agent_config.yaml` or `config/profiles/redacted_account.yaml` moves (both tokens
bind config digests `ffe16657feaf…` / `e184a81d3b1b…`, re-minted 2026-08-01 to Aug 14 — a
single byte kills the book's ability to place); `--tags` changes bound conviction counts
PROSPECTIVELY only — the ceremony must clear `firing_sleeves.json` or arm at a decision-day
boundary (B365); `--tags ""` is fail-open (all 32) and all-typo `--tags` is fail-closed-mute
(B327-class) — the package must include the proving log lines that distinguish the intended
set. FN weekend policy: weekend-flat with crypto exempt arms AT THE FN PASS (owner word),
not in this package.

## Boundaries

Never-execute: `run_book.py`, `run_agent.py`, `fn_smoke_trade.py`, `mt5_preflight.py`,
`dual_broker_execution_follower.py`, flatten/emergency scripts, `.tools/monitor_books.py`.
Never edit: the two token-bound configs; R2-bound paths (H1 — check membership before ANY
`src/` edit); never clean `ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl` in the
main repo (B905). The VPS is the orchestrator's only. March 2026 outcomes: NEVER read. TEST
surfaces (March + blackouts + live forward from 2026-07-29) are inviolable.

Conventions that bind you: `WAVE_11_WORKING_AGREEMENT.md` §5–§6 (blocks with citations,
scoped `pytest_failset.py` A/B with the tool-emitted `gtos-ab-receipt-v1` fence — embedded,
not referenced; the committed ZERO baseline is `receipts/FAILSET_BASELINE_MAIN.json`), plus
`phase15/SESSION_CG_LANE_FOOTPRINT.md` §"Conventions that bind you" for the mechanics.
Commit as you go. Result doc `phase17/SESSION_CL_PASS_SURFACE_RESULT.md` with findings-first,
a "What I got wrong" section, and a handoff that names the exact ceremony steps in order.
