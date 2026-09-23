# LIVE_HANDOFF — 2026-06-15 (live session → research session)

**Purpose.** This branch (`live-handoff-2026-06-15`) packages **everything** from the live trading
session so the research session can study it and **merge the live work on top of research**. It
captures: code & change context (the merge), live runtime state & config, the real broker rules,
all live fills/costs/decision logs, captured-data manifest, and forensics (hard-halt + every
go-live incident). The live system kept running untouched while this was assembled (git +
read-only MT5 export only). Secrets are redacted (`.env` is gitignored; no inline tokens). Account
**login numbers are kept** (operational, owner-shared): FTMO **531325516** / redacted_account **0**.

> **Do NOT force-push or rewrite history.** Preserve every live change; reconcile the divergences
> listed below deliberately. Push verified results to `deploy-live` only under owner gate.

---

## 1. The merge facts (read first)

| Fact | Value |
|---|---|
| Common ancestor (split) | `e0c2f8558` |
| This handoff branch HEAD | `d579885fa` (then + the LIVE_HANDOFF commit) |
| deploy-live tip (live runtime code) | `7d886e32f` |
| origin/deploy-live (your view) | `de040e475` — **ancestor of HEAD, fast-forwardable** (behind by the live-session commits) |
| Commits on deploy-live since split | **56** (code) + 5 handoff-data commits on this branch |
| **VPS is RUNNING** | **`056cfc7eb`** (last commit before the 10:51 restart) |
| Committed but **NOT loaded** in the running workers | `d7f1285a7` (precise pid-lock guard) + `7d886e32f` (PlacementLedger cross-process refresh) — they post-date the 10:51/10:57 worker starts. **The next clean restart loads them.** |

**Running ≠ pushed ≠ HEAD.** The live workers (FTMO pid 3636, FN pid 5028) execute `056cfc7eb`.
Two safety/hardening commits are staged on disk and verified by tests but unexercised in production
until the next restart. This is the single most important caveat for anyone reading the running
system's behavior.

---

## 1.5 Orchestrator's review, corrections & first-hand notes

*I (the live-session orchestrator) wrote/made every change here and lived the incidents; the section files
were drafted by subagents from the repo+logs, so I personally reviewed them. Corrections I applied, and
context only I have:*

**Corrections to the subagent drafts (applied 2026-06-15):**
- **Section 2 wrongly called the FN headroom identity mis-stamp "NOT fixed"** — it contradicted Sections 3
  and 5, which are correct. The fix **`78cbe370a` IS shipped and verified**: the post-restart FN record
  `245677491` (09:00Z) stamps `redacted_account_live_bee34003` + the FN-distinct hash. Only the pre-fix record
  `245629208` (06:13Z) carries the stale FTMO label, and it is intentionally **not backfilled** (the gate
  math always used the correct FN equity). Root cause was `execution_packets.py:27/:83` (hardcoded
  namespace), not `prop_firm_headroom_v4.py`. Corrected in §2.
- **Section 4 implied FN's larger JP225 size came from the running-count** — it did not. The FN 0.185813%
  vs FTMO 0.14025% gap was the **old per-evaluation-cycle** kelly_lite n_active (FN's cycle saw more
  sleeves → na 2-3; FTMO na 1), placed *before* running-count deployed. The running-count is the *fix* for
  that cross-account inconsistency, and it is inert today. Corrected in §4.

**The owner's exact authorizations behind the load-bearing changes (so research treats them as decisions, not my choices):**
- **Sizing — "go all the way in even with the current ftmo account."** This authorized flipping the
  running-count ON for **both** accounts (recover the per-cycle under-sizing UP to the validated 1.25%
  full-day convention). It did **NOT** authorize nominal > 1.25% — I explicitly held FTMO at 1.25% because
  the MC shows >1.25% spikes FTMO floor-breach to 2-5%.
- **Max-DD — "the max drawdown is the initial amount minus 10 percent so it's always 90k... and for the
  daily it follows the daily cycle for each."** This is the owner's literal rule and drove the static-90k
  governor fix (the validated MC had used a *trailing* peak, which I changed to match the real static
  rule). Daily = each broker's own server-midnight cycle (verified UTC+3 both).
- **FTMO thin cushion — "i accept it, im not resetting nor going conservative with the ftmo."** The owner
  saw the true reconstructed FTMO odds (~0.990 P(both), ~1% floor-breach, ~5-month median from the −2.87%
  start) and chose to run it at the validated dial. Not my call to revisit.

**The restart incident, first-hand (operational lesson for whoever next restarts the books):** I caused the
FN double-book. After a kill, the old pid-lock guard false-positived on an OS-recycled PID and blocked the
supervisor's respawn; I **cleared the lock AND manual-started FN while the supervisor was also starting it**
— two starters raced the now-absent lock → two workers for ~8 s. It placed no double order (proven), I
killed the duplicate, and I fixed the guard (`d7f1285a7`, precise psutil check) + hardened the
PlacementLedger (`7d886e32f`). **Rule: let the supervisor be the SOLE starter; never clear the lock and
manual-start in parallel.** Those two fixes are staged but **not yet loaded** in the running workers — the
next clean restart is their live test.

**My honest read for the research session:** the trading logic and every fix are sound and verified live;
the genuine residual is **verification/resilience debt, not edge** — (1) the running-count's *safety* is a
rigorous by-construction bound (running ≤ validated full-day → cannot breach more), but the confirmatory
KB7 MC **could not run (data caches absent)** so the *absolute* FTMO odds are a calibrated reconstruction and
the 2nd-order recovery-slowdown is unmeasured — **rebuild the W3/W5 stream caches and run the real harness
before a 2nd carrier reactivates and running-count first sizes up**; (2) the two staged commits need a clean
restart; (3) the FTMO +8% runtime target vs the official 2-Step +10%/+5% needs owner reconciliation. In ~30h
live the book did **not** repeat the hard-halt failure pattern.

---

## 2. Section index (`live_handoff_2026_06_15/sections/`)

1. **[`01_code_change_context.md`](live_handoff_2026_06_15/sections/01_code_change_context.md)** — THE MERGE. Exact git topology, the VPS-running-SHA caveat, and a 10-theme **changelog-with-rationale** tying each major change to the live failure it fixed (go-live triple-gate + 1.25% half-Kelly; FIX-1 native per-sleeve exits + overlay neutralization; FIX-2/3 management/rehydration/trade-records; FIX-4 `W7:<sleeve>` comment + FN identity; canonical→broker symbol resolver; FN follower; supervisor + monitor + scheduled-task; and today's static-90k governor, 4% gross-cap, running-count Kelly, GoldAgent→W7:UNTAGGED, + the 2 staged restart-incident fixes). Each classified **LOAD-BEARING / experimental / hard-halt-fix**.
2. **[`02_runtime_state_and_config.md`](live_handoff_2026_06_15/sections/02_runtime_state_and_config.md)** — effective per-account config (both run the identical surface: triple-gate all true, dial `clean3_w7_measured_nom1p25` 1.25% half-Kelly, `kelly_running_count=true` inert today, governor −3/−5/−10% + 4% gross, **static 90k floor**, halt flags absent = placement LIVE), per-account state, and the **dual-broker = two independent processes** (not a mirror) with the inert `dual_broker.role` vestiges.
3. **[`03_broker_rules.md`](live_handoff_2026_06_15/sections/03_broker_rules.md)** — the real FTMO + FN rules, sourced from code + owner clarifications; **unconfirmable items flagged, not invented**.
4. **[`04_live_fills_costs_decisions.md`](live_handoff_2026_06_15/sections/04_live_fills_costs_decisions.md)** — per-trade table of all 10 go-live W7 trades, realized per-symbol round-trip costs, the decision/shadow-log summary, and the captured-data manifest.
5. **[`05_forensics_and_incidents.md`](live_handoff_2026_06_15/sections/05_forensics_and_incidents.md)** — the hard-halt redacted_account forensics (−$859.69/77 trades, the ETHUSD swap blow-up, the flatten-not-halt control failure, the 8 failure mechanisms → W7 fixes) and **every post-go-live incident** tagged REAL/FALSE-POSITIVE + FIXED/OPEN, including the restart incident + the proven-harmless double-book.

**Data** (`live_handoff_2026_06_15/data/`): `git_state_summary.txt`, `changelog_commits_since_split.txt`, `changelog_full_with_stats.txt`, `diff_stat_*`, `mt5_ftmo_account_and_fills.json`, `mt5_redacted_account_account_and_fills.json` (account_info + open_positions + 30d deals/orders per account, captured read-only).

---

## 3. ⚠️ KEY RECONCILIATION ITEMS (elevated — what the research merge must resolve)

These were surfaced honestly by the section authors; several need **owner input**, not a code merge:

1. **FTMO profit target: runtime `+8%` vs official 2-step `+10%/+5%`.** `admission.py FTMO_TARGET=0.08`, but the profile's `ftmo_rules` (from OFFICIAL_FTMO_SOURCE_INDEX) records FTMO 2-Step = **+10% Phase 1 / +5% Phase 2**; agent_config base overrides 10→8. **Needs owner reconciliation** — which product/phase is this FTMO account actually on?
2. **redacted_account has NO FN-specific rules in the repo** — it inherits FTMO's constants (100k/5%/10%/8%) by hardcoded default. FN's actual product, target, daily-reset basis, consistency rule are **UNCONFIRMED**. (Owner did confirm: max-DD static 90k, daily on FN's own server-midnight cycle.)
3. **Owner-confirmed broker rules (already applied live):** max drawdown = **static 90k** (initial −10%, NOT trailing) on **both**; daily −5% on each broker's own **server-midnight (UTC+3 → 21:00 UTC)** cycle. The −5%/−10% assumption is **correct**; the governor was fixed to match (commit `64b9e6a69`, wall verified = 90000 live).
4. **Go-live halt-flag deletion is a deliberate divergence.** `AUTOSTART_DISABLED.flag`, `GTOS_HARD_PRODUCTION_HALT.flag`, `RESEARCH_RUNTIME_HALT.flag` are removed on deploy-live (system runs un-halted). **Do NOT auto-un-halt research on merge.**
5. **Two staged-but-unloaded commits** (`d7f1285a7`, `7d886e32f`) — load on the next restart; verify a single clean spawn (no flapping) then.
6. **Running-count is LIVE on both but INERT today** (na=1; only idxrev fired). Its size-up safety is **by-construction** (running ≤ validated full-day → can't breach more), but the confirmatory KB7 MC **could not run** (data caches absent) so the absolute FTMO odds (~0.990 P(both), ~1% floor-breach) are a **calibrated reconstruction**, and the 2nd-order recovery-slowdown is unmeasured. **Rebuild the W3/W5 stream caches + run the real harness before a 2nd carrier reactivates and it first sizes up.**
7. **No recent OHLC/tick capture.** The tick/M1 capture daemons stopped at the 2026-06-03 hard halt; there is **no 06-15 tick/M1 capture**. The W7 book reads live MT5 bars directly (doesn't depend on the capture daemons), but the research session won't find fresh captured tick. Manifest in Section 4.
8. **Known-open minor items:** the GER40 legacy-comment orphan (158716676, bounded on broker SL/TP); FN trade-records before 09:00Z carry the FTMO namespace (fixed `78cbe370a`, not backfilled — gate math always used correct FN equity); the notifier startup banner shows a legacy "2%/$2,000" (display-only, real sizing is the 1.25% half-Kelly dial).

---

## 4. Current live state (snapshot ~12:05 UTC)

- **FTMO** 531325516 / FTMO-Server3 — Challenge, balance $97,205.20, equity ~$97,264 (started −2.87% → **~7.3% real DD runway** to the static 90k floor, not 10%), 5 open positions (GER40 vp orphan + idxrev index-short cluster), daily +0.23%, gross 0.55%.
- **redacted_account** 0 / redacted_account-Server 2 — equity ~$99,981, ~10% runway, 4 open idxrev index-shorts, daily +0.02%, gross 0.31%.
- The whole open book is **one factor: short global equity indices** (the validated/accepted GAP2 limitation, conviction-split, bounded ~0.55%/0.31% worst-case-to-stop). One realized win: USDJPY fx_jpy **+$152.82** net at its native 2.5R.
- Process topology: supervisor PID 264 owns both books (one worker each) + monitor + the `GTOS_W7_BookSupervisor` scheduled task.

---

## 5. How to merge

- **Preserve all live changes.** deploy-live `de040e475..7d886e32f` is fast-forwardable onto your view; the 5 handoff-data commits on this branch add the runtime state + logs + intelligence + this doc.
- **Reconcile** the divergences in §3 (esp. the halt flags, the FTMO target, the running-count MC) — these are judgment calls, not mechanical merges.
- **The live runtime state** (`pipeline_state/ultimate_book/`) is a point-in-time snapshot; the running books keep writing it. Use it for context, not as a moving source of truth.
- **LFS:** `shadow_logs/**/*.jsonl` is LFS-tracked (the decision/shadow logs + most data already on origin). `git lfs pull` after checkout.

*Generated by the live session orchestrator, 2026-06-15. The live system remained running and monitored throughout.*
