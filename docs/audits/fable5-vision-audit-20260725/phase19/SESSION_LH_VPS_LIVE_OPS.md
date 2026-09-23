# Session LH — VPS live health, forward-data assurance, and disk relief

**Ops session (no research block range). Branch `ops/vps-live-health-20260803`, worktree
`/Users/borr/GTOSActive/worktrees/vps-live-ops-20260803`.** You are Claude Fable 5 at
maximum effort; subagents (when useful) are Fable — no Codex, no Opus, no downgrades.
Receipts: `docs/audits/fable5-vision-audit-20260725/phase19/receipts/vps_live_ops_20260803/`.
Result doc: `phase19/SESSION_LH_VPS_LIVE_OPS_RESULT.md`. Commit receipts as you go on
this branch; hand the branch name to Session FA's closing ceremony when done.

**You operate the LIVE HOST. Both prop accounts are ARMED and trading real money on it.**
Read CLAUDE.md §3 (H1–H8) and §4 before your first host-admin call. The owner is at the
terminal — when his word is required, ask in plain text and wait.

## §1 The owner's directive, verbatim (2026-08-03)

> "ok now have a fable session as well in the vps to make sure that the live is going
> well and there are no issues and if there are it needs to fix all of them so the whole
> forward data and the active sleeves are good on live and everything is fully
> functional and if it needs to save some space because i received a notification that
> space may be low, if it's like that it has my explicit approval to delete the things
> not needed there or stale or too old to save disk space, please you launch the session
> in the vps through the tailsclae connection"

That is your charter: (1) live is going well — verify everything, (2) fix every issue
found, (3) the forward data and the active sleeves are good, (4) disk space relieved,
with his explicit approval standing for deleting the not-needed / stale / too-old.

## §2 Connection (secrets never printed, never committed)

- Credentials: `source ~/.gtos/vps.env` (VPS_HOST=0.0.0.0, VPS_NAME=redacted_host,
  VPS_USER, VPS_PASSWORD, host-admin 5985, transport ntlm). The file lives outside the repo
  on purpose; nothing from it is ever echoed into a transcript, commit, or receipt.
- Tooling: **pywinrm** (installed):
  `host-admin.Session(f"redacted-winrm/wsman", auth=(user, pw), transport='ntlm')` —
  `run_ps(...)` for PowerShell. SSH is closed by design. **SMB 445 / C$ is open** — for
  bulk pulls mount from the Mac (`mount_smbfs //VPS_USER@0.0.0.0/C\$ <mnt>`,
  password from the env file) instead of chunked base64.
- Transport craft (learned, don't relearn): `phase8/receipts/VPS_CEREMONY_COMPLETED.md`
  — ~8,191-char encoded-command ceiling; chunked base64 at 2,800 chars for file pushes;
  `Win32_Process.Create` for anything that must survive the host-admin session; pywinrm
  sometimes returns spurious nonzero with a CLIXML progress record on stderr — read the
  actual streams, not just the status code.
- Python-string hazard: pass PowerShell as **raw strings** (`r"""..."""`) — `C:\Users`
  contains `\U`.

## §3 State at commissioning — measured 2026-08-03 ≈13:45 UTC (do not re-derive)

**Disk C: was 0.84 GB free of 199.9 GB at first contact — active threat to the books'
own writes.** The commissioning session executed the unambiguous emergency lane under
the owner's approval: recycle bin, temp files older than 1 day (Windows + user), Windows
Update download cache, crash dumps, hibernation off. **Free went 0.84 → 1.42 GB.** Still
critical; the real mass is mapped below.

| consumer | GB | note |
|---|---:|---|
| `C:\Users\MSI\Documents\ai-trading-agent` | **106.9** | **THE live tree** — `.git` 59.59, `research/` 41.29, `shadow_logs/` 3.61, `knowledge_base*` 1.68 |
| `C:\Users\MSI\Documents\ai-trading-agent-runtime-learning-packet` | 6.2 | the packet repo (second tree) |
| `host-local` | 19.56 | unmeasured below level 0 — break it down |
| `C:\MT5` | 19.53 | terminals live HERE (not AppData/ProgramData) |
| `C:\pagefile.sys` | 15.19 | see §5.g |
| `C:\ProgramData\HermesAgent` | 6.07 | agent versions/logs |
| GTOS staging (`GTOS_EXPORT_BARS_20260727`, `gtos_ticks_*`, `gtos_exports`, `GTOS_CARRY_20260729`, `tmp`, `Trading`, ceremony backups) | ≈0.4 total | already small |
| `C:\GTOS` | 0.64 | small live aux tree |

Processes/tasks at contact: `GTOS_W7_BookSupervisor` **Running**; `GTOS_Watchdog`
**Disabled** (establish whether that is intended — it belongs to the supervision-
hardening lineage); `Hermes-GTOS-BridgeSync` Ready; 12 python processes (one at ~1.5 GB
working set — identify it); `terminal64` ×2 at oddly small working sets (19/24 MB) —
verify both terminals are actually connected and `trade_allowed`, not just present.
No VSS shadow storage. No `trader` profile under `C:\Users` (host-admin account ≠ the
run-as account — verify which account the supervisor task runs as).

## §4 Phase 1 — Health sweep first (read-only, before any further deletion)

Derive the EXPECTED state from the receipts (in this worktree), then diff reality:
`phase17/OD_ALL_IN_20260801.md` + the CM/CN/CO ceremony receipts (phase17),
`phase13/receipts/MX_ACTIVATION_20260731.md`, `phase8/receipts/`
(`VPS_CEREMONY_COMPLETED.md`, `VPS_STEP_ZERO_VERIFIED.md`, `FIVE_SLEEVE_EXPANSION_20260730.md`,
`FXJPY_PULL_20260730.md`, `FN_ARMING_20260730.md`), `phase4/PACKET_UNBLOCK_VPS_RUNBOOK.md`.

Checklist — every row gets a PASS/FAIL/FIXED line in the result doc:
1. Supervisor task running; worker command lines carry the post-ceremony args (FTMO:
   5 tags + `--frontier-exits` mx,crypto + lane weights; redacted_account: 4 tags + neutral
   lane — read the exact strings from the ceremony receipts, don't trust this summary).
2. Both books' heartbeats fresh; `authority_gates_ON` in both books' own logs; kill
   flags absent/released.
3. **Activation tokens valid** (minted to 2026-08-14; FTMO binds config digest
   `ffe16657feaf`, redacted_account `e184a81d3b1b`) AND the host config's CURRENT digest still
   matches the token binding — a mismatch means the book cannot place and is a live
   incident (fix = owner word; only Borhen re-mints).
4. Both MT5 terminals connected, `trade_allowed` true, correct accounts.
5. **Forward data flowing**: runtime-learning packets jsonl growing (both books, check
   mtime + size deltas over ~15 min), shadow logs current, monitor daemon alive on
   carried code, telemetry fresh.
6. The 2026-08-02 00:00 UTC boundary ceremonies (CM frontier `crypto@stop_1p5x_target_scale`,
   CN broker-true commission as fail-closed fourth cost term both books, CO lane's first
   live vector FTMO ×1.15/×1.15 + FN neutral) actually took effect, and the ~2 days of
   operation since show no errors attributable to them. **CO declarations expire
   2026-08-08 — owner-sheet item, not yours to renew.**
7. Host repo tree: clean `git status`, at/past the expected host commits (`118071eaa`,
   `eb7c28516`, `f855250cd`, `d6c9c4b19`, + the 2026-08-02 ceremony commits).
8. System: clock drift vs UTC; pending-reboot flags; System/Application event-log
   errors last 72 h; CPU/RAM headroom; the 1.5 GB python identified.
9. Open positions inventory (READ-ONLY — management belongs to the books).
10. `GTOS_Watchdog` Disabled: intended or drift? (Receipts lineage decides; if it should
    run, that is a supervision fix — §6 allows it.)

## §5 Phase 2 — Disk relief (owner's deletion approval is standing; his words in §1)

Floor first: get free space ≥ 25 GB before any heavy operation; final target ≥ 60 GB.
Every batch gets a receipt row: path, size, category —
`SAFE-DELETE` | `ARCHIVED-THEN-DELETED (archive path + sha256)` | `RECOMMENDED-ONLY`.

a. **Pull before delete** (SMB mount to the Mac; hold `~/gtos-vps-archive-20260803/`):
   current full `shadow_logs/` (3.6 GB — the W7 live-ledger copy-off priority from
   2026-07-25 still stands), the runtime-learning-packet repo (6.2 GB, it is a git repo
   — clone/pull it), and any UNTRACKED or host-modified files under the live tree's
   `research/` (tracked-and-unmodified content is already recoverable from the Mac's
   repo objects — verify per file via git before treating it as such).
b. **`research/` 41.3 GB out of the live working tree** — the git-clean way: sparse-
   checkout exclude `/research/` on the live tree. FIRST verify nothing live reads
   `research/` paths (grep the supervisor script, `run_book.py`, and the active config
   for `research/` references). Then apply, confirm `git status` clean, confirm both
   books' next heartbeats healthy.
c. **`.git` 59.6 GB**: `git count-objects -v` + `git lfs env` first. **LFS caution: the
   storage doctrine deliberately does NOT push LFS to GitHub — the host's LFS store may
   hold the only copy of host-side objects.** `git lfs prune --dry-run`; any OID absent
   from the Mac's store (`/Users/borr/GTOSActive/repo/.git/lfs`) is pulled to the
   archive hold before pruning. Then prune + a plain `git gc` (not `--aggressive` on a
   starved disk); heavy I/O in one pass, watching book heartbeats during.
d. **`C:\MT5` 19.5 GB**: delete terminal `logs/` older than 14 days, `Tester/` caches,
   mail/news caches. **Keep `bases/` (price history) — the books read charts from these
   terminals.**
e. **`host-local` 19.6 GB**: break down level-1; old downloads, installers,
   superseded exports → archive-or-delete per rule.
f. **HermesAgent 6.1 GB**: keep the running version + current logs; stale versions and
   rotated logs → delete.
g. **`pagefile.sys` 15.2 GB → RECOMMENDED-ONLY**: propose a fixed 6–8 GB pagefile to the
   owner; it takes a reboot (books restart) — his schedule, never unilateral.
h. The small staging dirs (§3 table, ≈0.4 GB): already-exported content verified against
   the Mac copies (`/Users/borr/GTOSActive/vps-ticks-20260726/` is sha256-verified;
   `vps-export-20260725/` exists locally) → delete after spot-hash.

## §6 Fix authority and hard boundaries

FIX AUTONOMOUSLY (with receipts + host-branch commits, precedent `118071eaa`): anything
broken that is NOT the armed decision surface — monitor/telemetry daemons, data
pipelines (packet export, log rotation), supervision tasks (incl. `GTOS_Watchdog` if
lineage says it should run), scheduled-task drift outside the supervisor's book args,
disk/system hygiene per §5.

OWNER'S WORD FIRST (he is at the terminal — ask, wait, then execute exactly): any drift
on the armed surface (supervisor `--tags`/args, gates, lane weights, config bytes —
**editing token-bound config breaks the token digest and the book refuses to place;
config fixes follow the ceremony pattern and only Borhen re-mints**), any book restart
that is not pure restoration of a dead book, the pagefile change, any reboot.

NEVER (no owner word changes these in THIS session): place/modify/close an order or run
any broker-mutating script (the H6 never-execute list stands); stop a healthy book or
flip a gate — and know H8 cold: gating off does NOT flatten, it strands positions
unmanaged; if the owner ever orders disarm, flatten-first is the sequence you put in
front of him. No sleeve/weight/dial changes. No arming. Restart hazard: a mid-day book
restart inherits the day's wider `firing_sleeves` union (B365) — restoration restarts
note this in the receipt. Live-forward OUTCOMES never feed a research claim (ops reads
are fine; economics claims are not yours to make). Protected from deletion always:
current `pipeline_state/`, current shadow logs and packets, tokens/secrets, MT5
`bases/`, both repo trees' tracked-and-unmodified content only per §5's git rules,
anything a running process holds open.

## §7 Deliverables

1. `SESSION_LH_VPS_LIVE_OPS_RESULT.md` — health checklist verdicts (PASS/FAIL/FIXED per
   row), every fix with its receipt and host commit, disk before/after table (target
   ≥ 60 GB free), the owner sheet (CO declarations expiring 2026-08-08; pagefile/reboot
   recommendation; anything awaiting his word).
2. Receipts under `phase19/receipts/vps_live_ops_20260803/` — including the deletion
   ledger (path/size/category/archive-hash) and the archive-hold manifest.
3. Host-side changes committed on the host branch; Mac-side receipts committed on
   `ops/vps-live-health-20260803`; branch name handed to Session FA's closing ceremony.
4. "What I got wrong" — house style.
