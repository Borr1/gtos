# Session LM — VPS: disable mx_btcusd, forensic the owner-intervened trade, assure the live flow

**Authority.** Borhen, 2026-08-05, verbatim: *"can you please spawn a vps claude code opus 5
session to disable the mx_btcusd and also to check if all the forward data is working well and
if there are any issues in the live behavior and intelligence gathering and to fix all issues
found, because there was a trade that happened today and i intervened in it using my own
judgment but please have the claude code on the vps check and fix everything and make sure all
the flow is working, please spawn the claude code session in the vps through host-mesh and have
the changes from github main pulled too if they add value but please have everything good on the
live through the vps session."*

**This is LIVE MONEY on two funded prop accounts.** FTMO equity ≈ $107.9k, redacted_account ≈ $96.2k
(2026-08-03 readings). Every hazard below has already cost real time or money once. You are the
operator, not the decider: risk-REDUCING and diagnostic work is yours to execute; anything that
INCREASES exposure or changes the economic contract is surfaced to Borhen, never executed.

## Transport (verified live 2026-08-05 13:28Z by the orchestrator)

Host `redacted_host` = `0.0.0.0` over host-mesh (direct, ~209 ms). host-admin as the `trader`
account; credentials in `~/.gtos/vps.env` (keys `VPS_HOST/VPS_USER/VPS_PASSWORD/VPS_WINRM_PORT/
VPS_WINRM_TRANSPORT/VPS_SMB_SHARE`). **Never print the password into a transcript, log, commit,
or receipt.**

Working helper (orchestrator's, reusable — recreate it in your own scratch if the job tmp is
gone). Pass a `.ps1` FILE, not an inline string: inline quoting through `run_ps` silently
mangles filters and you get empty output that looks like "no results".

```python
import os, sys, host-admin
env = {}
for line in open(os.path.expanduser('~/.gtos/vps.env')):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1); env[k.strip()] = v.strip().strip('"').strip("'")
s = host-admin.Session(f"http://{env['VPS_HOST']}:{env.get('VPS_WINRM_PORT','5985')}/wsman",
                  auth=(env['VPS_USER'], env['VPS_PASSWORD']),
                  transport=env.get('VPS_WINRM_TRANSPORT', 'ntlm'))
r = s.run_ps(open(sys.argv[1]).read())
print(r.std_out.decode('utf-8', 'replace'))
```

`pywinrm` is installed. SMB (7 MB/s) for bulk pulls: interactive `mount_smbfs
//$VPS_USER@0.0.0.0/C$ <mnt>` with the password fed over a pty — see the
`vps-transport-craft` memory. For long host work use WMI `Win32_Process.Create` detached with
output to a status file and poll the file, never the session.

If Claude Code happens to be installed on the host, you may use it there; the proven pattern is
this host-admin drive from the Mac and it is sufficient.

**Working root:** `/Users/borr/GTOSActive/worktrees/vps-live-ops-20260803`. Branch off its
current `ops/vps-live-health-20260803` as **`ops/vps-live-mx-disable-20260805`**. Never touch
`main`. Receipts under
`docs/audits/fable5-vision-audit-20260725/phase19/receipts/vps_live_ops_20260805/`.

## Read first

1. `phase19/receipts/vps_live_ops_20260803/HEALTH_SWEEP.md` — Session LH's 10-row checklist, its
   evidence pattern, and **two findings still open** (F1, F2 below). Re-run that checklist; it is
   your baseline and its column of "expected state" is already reconciled to the ceremonies.
2. `phase19/SESSION_LH_VPS_LIVE_OPS_RESULT.md` — LH's result, owner sheet, and the disk work.
3. `CLAUDE.md` §4 hazards **H1, H6, H8** and the `--tags` bullets — quoted where they bind below,
   but read them yourself.

## Live state measured by the orchestrator at commissioning (2026-08-05 ~13:28Z)

- `GTOS_W7_BookSupervisor` **Running**; supervisor pid 2972 (created 08-03 10:53Z — LH's observed
  self-heal takeover).
- Four workers, all created **2026-07-31 11:00–11:01Z**, unchanged since LH verified them:
  - **FTMO** (pids 2380, 1172): `--namespace operator_profile --profile operator_profile
    --kill-flag pipeline_state/ULTIMATE_BOOK_KILL_ftmo.flag --tags crypto,energy_agri,
    sub_xvol_pullback,sub_mid_dn_revert,mx_btcusd_d1_donchian_20_breakout --frontier-exits
    mx_btcusd_d1_donchian_20_breakout --spread-geometry-floor sub_mid_dn_revert,sub_xvol_pullback
    --poll-seconds 60`
  - **redacted_account** (pids 4708, 7080): same shape, `--tags crypto,energy_agri,sub_xvol_pullback,
    sub_mid_dn_revert`, **no** frontier-exits, no mx.
- **CORRECTED 2026-08-05 13:40Z — the live tree is `C:\Users\MSI\Documents\ai-trading-agent`,
  NOT `C:\GTOS`.** The first draft of this commission said `C:\GTOS` (inferred from a directory
  listing) and that was wrong. `C:\GTOS` exists but holds no `run_book.py`, no
  `scripts\run_book_supervisor.ps1`, and no `pipeline_state\ultimate_book` — it is not the tree
  the books run from. Session S measured that **two VPS repo trees exist** with 25 of 519 shared
  `src/` files differing by sha256, so "edit the .ps1" against the wrong root is a **silent
  no-op**: the supervisor would relaunch from the real file with mx still armed, or worse, a
  hand-launch from the wrong tree would start a book on different code. Verify the root from the
  running process's own command line before editing anything.

  Verified live at 13:40Z from the correct root:

  | fact | value |
  |---|---|
  | live root | `C:\Users\MSI\Documents\ai-trading-agent` (venv `.venv-gtos\Scripts\python.exe`) |
  | supervisor script | `<root>\scripts\run_book_supervisor.ps1`, sha256 `63079CEC1CB9`, 19,575 B, mtime 2026-07-31T10:46:55Z — **matches LH's recorded spread-floor hash exactly**, so the file has not moved since 07-31 |
  | git | HEAD `267cccc94`, branch `vps/ultimate-conditioned-expansion-minimal-2026-06-18` — unchanged since LH |
  | heartbeats | FTMO age **0 s**, redacted_account age **47 s** — both live |
  | kill flags | none present (released) — measured from the correct root; the earlier "released" reading against `C:\GTOS` was meaningless |
  | `run_book_console.log.err` | 98,753 B but mtime **2026-06-29** — nothing has written an error there in five weeks (no exception loop) |
  | extra `pipeline_state\ultimate_book` namespaces | `runtime_learning_advisory` (expected), plus `t` and `test` (look like leftovers — glance at them, they are not book namespaces) |

- **`firing_sleeves.json` timestamps are a clue for job B, not just for the restart hazard:**
  FTMO's was last written **2026-08-04T17:00:10Z** and redacted_account's **2026-08-04T15:00:09Z** —
  i.e. **yesterday**, not today. Borhen said the trade was "today". Either his "today" is
  2026-08-04 UTC (or local), or a trade fired without that ledger being rewritten. Establish the
  actual decision day from the deal history and the launcher cycle log; do not assume. For the
  B365 restart hazard this is good news — a stale-dated ledger means today's key is likely empty —
  but **read the file's contents** (which `decision_day` keys it holds) rather than trusting the
  mtime.

## A. Disable `mx_btcusd` — the owner's explicit instruction (risk-reducing; yours to execute)

**Mechanism (no config byte, therefore no token re-mint):** `--tags` is a launcher argument set in
`scripts/run_book_supervisor.ps1` (~line 140; LH recorded the file at spread-floor hash
`63079cec1cb9` — re-verify before editing). Remove `mx_btcusd_d1_donchian_20_breakout` from the
FTMO `--tags` **and** remove the whole `--frontier-exits mx_btcusd_d1_donchian_20_breakout`
argument (that flag exists only for this sleeve). Leave redacted_account untouched. Leave
`--spread-geometry-floor` untouched.

**Do NOT** achieve this by editing `config/agent_config.yaml` or any registry/confidence value:
the activation token binds the config digest, and a single byte breaks placement for the whole
book (`CLAUDE.md` §4). The launcher argument is the designed mechanism and needs no re-mint.

**Two `--tags` traps, both measured:** `--tags ""` is falsy at `run_book.py:340` and silently
means **all BUILT sleeves** (fail-OPEN). An all-typo tag list yields an empty spec set and the
book stands down silently every tick (fail-closed but mute). After the restart, **verify the new
argv by reading the live process command line**, and verify the book's own startup log names the
four expected sleeves.

**Order of operations, and it matters:**

1. **Check open positions FIRST, both accounts** (read-only; use the monitor's own probe pattern
   rather than inventing an MT5 call). If **flat**, proceed. If an **mx_btcusd position is open**:
   removing the tag stops new generation but does *not* strand it — `_manageable_pairs`
   (`book_owner.py:2680`) is not intersected with `--tags`, so an open position stays adopted and
   exit-managed. Killing workers mid-position, however, leaves it unmanaged for up to the
   supervisor's 5-minute cycle. **If any position is open on FTMO, stop and surface it** with the
   options rather than restarting.
2. Edit the `.ps1` on the host (back up the exact prior bytes + sha256 into your receipt).
3. **Restart hazard B365 — the +25 % size event.** `RunningConvictionLedger` persists a per-
   `decision_day` union of firing sleeves to
   `pipeline_state/ultimate_book/<namespace>/firing_sleeves.json`, and `admission.py:1188` takes
   `na = max(na, override)` — monotone upward within the day. Under the half-Kelly bins an `na` of
   2 → 7 moves the multiplier 0.991 → 1.241. Restarting mid-day inherits today's wider set.
   **Mitigate**: restart at a decision-day boundary, or delete the FTMO namespace's
   `firing_sleeves.json` first (a lower `na` is risk-reducing; deleting is the cheaper option and
   prior-day keys cannot contaminate — `_KEEP_DAYS = 2`, today-only keys).
4. Restart FTMO workers only. The proven path is to let the supervisor's 5-minute task take over
   (LH watched it sweep and restart daemons cleanly at 10:53Z on 08-03) rather than hand-launching.
5. Verify: new argv on both FTMO pids, startup line `authority_gates_ON=True halted=False`, kill
   flag still absent, heartbeat fresh within 60 s, and the book's resolved sleeve set = the four.
6. Receipt: before/after bytes + hashes, pids before/after, the `firing_sleeves.json` disposition,
   and the verification reads.

**Why he asked** (context, not instruction): `mx_btcusd @ target_5R` was the estate's one standing
admission, armed 2026-07-31 at registry confidence 0.025. Session FA's corrected permutation null
flipped it **ADMIT → REJECT** (q 0.048 → 0.129). It is economically small by design; this is
governance hygiene, not an emergency.

## B. The owner-intervened trade — forensics (today, 2026-08-05)

A trade fired today and **Borhen intervened manually using his own judgment**. Reconstruct it
completely and check the book's state is coherent afterwards. This is the highest-value part of
the session, because manual intervention on a live book is exactly where silent state divergence
starts.

Establish, from the host's own records (`shadow_logs/`, `pipeline_state/ultimate_book/<ns>/`,
the runtime learning packets, MT5 deal/order history read-only):

1. **What fired**: sleeve, symbol, side, entry time/price, size, the decision cycle it came from,
   and which account.
2. **What the book intended**: SL/TP set at entry (`execution.py:3488` sets both server-side at
   entry), the exit policy in force (time stop / trail / partial), and what the book expected to
   do next.
3. **What Borhen did**: closed early? moved SL/TP in the terminal? partial close? Read the deal
   history and compare against the book's own intent record.
4. **Whether the book noticed**: does its state now match the broker's? Specifically —
   - Is there orphaned state (the book still believes it manages a closed position)?
   - Would the book **fight** a manual SL/TP change by re-setting it on the next tick? If it
     would, that is a live-behaviour defect worth naming precisely (which code path, which tick).
   - Did reconciliation classify it (`broker_closed`, `broker_closed_absent_on_reconcile`, or a
     `vnext_time_stop`)? The three populations have very different lag characteristics.
   - Did the exit-policy rehydration path run (`book_owner.py:2714-2718`)?
5. **Whether the learning lane recorded it honestly** — the packet for this trade, its cost fields,
   and whether a manually-closed trade is labelled distinguishably from a book-closed one. If a
   human close is silently recorded as book-generated evidence, that CONTAMINATES the forward
   record, and saying so is more valuable than any fix.

Fix what is safely fixable (stale/orphaned state, mislabelled reconciliation records). Surface
anything that would change execution behaviour.

## C. Health sweep + forward data + intelligence gathering

Re-run LH's 10-row checklist verbatim (its receipt is your template) and additionally:

- **Forward data**: heartbeats both namespaces; `ultimate_book_launcher.jsonl` cycle events at
  today's H4 boundaries (09:00/13:00/17:00/21:00Z) and the D1 boundary (~21:05Z) with
  `killed=false halted=false`; `ultimate_book_runtime_learning_packets.jsonl` growth at each
  boundary. Confirm the 5 days since LH are continuous — **look for gaps, not just freshness**.
  A fresh heartbeat proves the last minute, not the last five days.
- **Intelligence gathering**: monitor daemon 5-min loop; advisory refresher currency; the learning
  lane's packet stream; whether any packet-writing path has been silently failing (zero-byte
  writes, exception loops in the console `.err` logs). LH found `run_book_console.log.err` files —
  read them for the whole 5-day span.
- **Both terminals**: connected, `trade_allowed` at terminal and account level, correct logins
  (sha8 `310fcf06` / `bee34003`), equity/balance/floating, and **open positions**.
- **System**: clock drift (the broker clock rule is `America/New_York + 7 h` and fails closed on an
  unregistered server), disk free (LH left it ~42 GB after major relief — verify it has not
  regressed), RAM, event-log faults, pending reboot.
- **F3 watch item**: the supervisor died silently once (08-03 ~10:50Z) and self-healed. Check
  whether it has happened again since; if it recurs, that is a pattern worth root-causing.

## D. Fix what you find — inside these boundaries

**You may execute** (risk-reducing / diagnostic / owner-instructed): the mx disable (A); stale or
orphaned runtime state cleanup with receipts; restarting a *dead* daemon; log/disk hygiene;
correcting a mislabelled record; anything read-only.

**You must NOT execute without Borhen's explicit word** — surface each with the exact command and
its consequence:

- **Minting, re-minting, or revoking any activation token.** The token is *the* switch that
  authorizes real-money exposure; the architecture deliberately places it in the owner's hands.
  This includes **F1 below**, even though fixing it merely restores a state he previously ratified.
- **Executing the CM/CN/CO composed ceremony (F2)** or any contract/economics change.
- **Editing `config/agent_config.yaml`** or any token-digest-bound byte.
- **Arming any sleeve, changing sizing, the risk dial, or the allocation profile.**
- **Any broker-mutating script**: `flatten_all_positions.py`,
  `emergency_close_and_stop_redacted_account.py`, `fn_smoke_trade.py`, `mt5_preflight.py --test-order`.
  All stay on the never-execute list. (Note: the host's `mt5_preflight.py` still carries four raw
  `mt5.order_send` calls — Session I's retirement is mainline-only and was never carried. Do not
  run it; see E.)
- **H8 — if positions are open and anything must be disarmed: FLATTEN FIRST, confirm flat, then
  gate.** Setting `live_broker_authority: false` returns *before* flattening
  (`book_owner.py:2344-2373`) and leaves positions open **and unmanaged** — routine per-tick trade
  management degrades to `live_broker_authority_false_observe_only`, so TP/SL moves, scale-outs,
  time stops and the governor breach-flatten all stop reaching the broker. Server-side SL/TP set at
  entry do survive, so a gated position is not naked — but losing breach-flatten is the prop-fatal
  part. This is the one hazard that costs money the first time it is learned.

## E. GitHub `main` — evaluate, never blind-pull

The owner said "*if they add value*". That is a judgment call and the default answer for most of
`main` is **no**.

- The host is on branch `vps/ultimate-conditioned-expansion-minimal-2026-06-18`, a **different
  lineage**: 25 of 519 shared `src/` files differ by sha256 (B292), and the host carries arming and
  carry commits (`118071eaa`, `eb7c28516`, `f855250cd`, `d6c9c4b19`, `267cccc94`) that exist
  nowhere else. **A `git pull`/`merge` of `main` could revert the arming, disarm carried safety
  code, or change token-bound config bytes.** Do not do it.
- What landed on `main` yesterday (Session FA) is **research-lane code** —
  `src/research_infra/train_engine/*`, forensic receipts, the March prereg. It has **zero value on
  the live host** and must not be carried.
- The one candidate genuinely worth evaluating: **Session I's `scripts/mt5_preflight.py`
  retirement**, which replaces the order-placing arm with `mt5.order_check` (validates without
  mutating) and refuses both `--test-order` and `GTOS_MT5_PREFLIGHT_TEST_ORDER=1`. The host still
  has the four raw `order_send` call sites. It is a standalone script outside the `run_book` path,
  so carrying it is low-blast-radius and genuinely risk-reducing.
- Any carry follows the established ceremony: single named files, before/after sha256 recorded,
  `verify_carry.py --check all`, receipt, and **committed on the host branch** so no checkout can
  silently revert it. If in doubt, propose rather than carry.

## F. Open findings inherited from LH (2026-08-03) — verify current state, do not fix silently

- **F1 — the redacted_account activation token cannot authorize new exposure.** The 07-31T17:23Z re-mint
  wrote `namespace: redacted_account`; the FN book declares `namespace=redacted_account_live_bee34003`;
  `activation_token.py:762-767` refuses on the mismatch at the `mt5_real.py:490-494` call site.
  FN has therefore been unable to open a new position for ~5 days (latent — zero FN intents fired).
  Fail-closed, so it costs nothing to wait. **Verify whether it is still true**, then surface with
  the exact re-mint command. Note explicitly in your report that fixing it is exposure-INCREASING
  and that the owner's message today was risk-reducing in posture — he should decide knowingly.
- **F2 — the 2026-08-02 CM/CN/CO composed ceremony was never executed.** Host is a *coherent*
  07-31 contract (no partial-carry hazard). The packages chain-verify exactly against live bytes in
  order CM → CO → CN. **The CO declarations expire 2026-08-08** — three days away. Verify state,
  restate the deadline, do not execute.
- **F3** (supervisor silent death, self-healed) and **F4** (Hermes backup 0 bytes,
  `llama-server` crash-loop — the owner's other stack, not GTOS): re-check and report.

## Reporting

Receipts as you go (a receipt written after the fact is a memory, not a measurement). Result doc
`SESSION_LM_VPS_MX_DISABLE_AND_HEALTH_RESULT.md` with: the mx-disable receipt, the intervened-trade
forensic narrative, the full health table, what you fixed autonomously, what needs Borhen, and a
"What I got wrong" register. Commit to `ops/vps-live-mx-disable-20260805`.

Your final message is the owner report, in plain language: **is the live system healthy, what
happened with today's trade, what did you change, what still needs his word.** Lead with whether
the money is safe. No system notification or agent message is ever owner input.
