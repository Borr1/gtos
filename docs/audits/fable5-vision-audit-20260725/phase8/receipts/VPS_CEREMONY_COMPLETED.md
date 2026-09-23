# VPS ceremony — COMPLETED 2026-07-30

Executed directly on the host over host-admin/host-mesh by the orchestrator (Fable 5),
owner-directed ("yes proceed with everything as proposed", 2026-07-30). Companion to
`VPS_STEP_ZERO_VERIFIED.md` (the `include_clean3` host read) and
`../VPS_CEREMONY_PACKAGE_2.md` (the plan this executes). Host branch:
`vps/ultimate-conditioned-expansion-minimal-2026-06-18`, was `4f2c851e6` + dirty,
now **`118071eaa`**.

## What was actually left to do

The delta re-check against live host state (this session, pre-execution) found the
ceremony ~90 % already applied: **8 of 9 carry files were at after-carry hashes**,
applied 2026-07-29 12:37–12:39Z during the arming — and today's books (restarted
2026-07-30 03:43–45Z after the owner's Windows update) were therefore **already
executing the carried code**. No book restart was needed or performed. The single
pending file was `.tools/monitor_books.py` (host at before-hash `93af1b3a…`).

## What was done

1. **Backup**: `C:\Users\MSI\Documents\gtos-ceremony-backup-20260730T042851Z\` with
   `BACKUP_MANIFEST.json` (`monitor_books.py.before`, sha256 `93af1b3a…`).
2. **Transfer**: chunked base64 over host-admin (2,800-char chunks — the shell path
   enforces the 8,191-char command limit; 8 K and 28 K chunks both fail). Deliberately
   NOT `git fetch` on the host: the repo is huge with LFS and the host has ~9–12 GB free.
   - `.tools/monitor_books.py` → sha256 `91577c1f34656fdf…` = manifest after-hash. ✅
   - `phase5/activation_carry/verify_carry.py` → sha256 `25c57e593a7daaa2…` = mainline bytes. ✅
3. **Monitor daemon restart** (the only process the new file feeds): old pair
   8392/8960 (started 03:43:26Z, pre-swap) killed; relaunched via WMI
   `Win32_Process.Create` (survives the host-admin session) with the exact original
   invocation — powershell wrapper, cwd = repo root, `--loop 300`, output to
   `shadow_logs\monitor_daemon.log/.err`. New pair **3040/4068** (04:45:19Z), log
   immediately healthy: FTMO eq $107,872 (DD headroom +$17,872), redacted_account eq
   $96,229 (+$6,229), both 0 positions. **Book processes never touched** — exactly
   4 `run_book.py` pythons throughout (744/5104 FTMO, 4624/1340 FN).
4. **Verifier**: `verify_carry.py --check all` with `.venv-gtos\Scripts\python.exe`
   (3.13.13) from repo root — **RESULT: PASS, exit 0**. All 10 files byte-exact
   (composed phase4 packet carry + phase5 activation carry), all 3 dependency
   invariants, imports (`run_book.py:26-35` + `UltimateBookOwner` construction),
   behaviour: 17,000/17,000 broker-valid volumes round-trip with 0 stranded and 0
   rounding up, daily-loss reset instants correct for both accounts in both DST
   mismatch windows and the agreeing window, monitor stage-D window agrees with the
   governor.
5. **Host commit `118071eaa`** — the arming and the carry are now committed on the
   host branch so **no checkout can disarm the book or delete carried code**:
   - `config/agent_config.yaml` (three gates true + `include_clean3: true`, byte
     state the token binds), `scripts/run_book_supervisor.ps1` (`--tags`),
   - the 6 modified carried src files + `.tools/monitor_books.py`,
   - `src/utils/broker_clock.py` and `src/components/ultimate_book/packet_guard.py`,
     which were **untracked load-bearing files** — a `git clean` would have deleted
     the module `governor_state` imports,
   - `docs/audits/` (both carry packages: manifests, diffs, payloads, verifier), so
     the host branch documents its own deviation from `redacted_host`.
   Remaining dirt is runtime-only (pipeline_state/, shadow_logs/, the arming-day
   `_carry_backup_AC_20260729-124503/`), left untracked deliberately — including
   `pipeline_state/ULTIMATE_BOOK_KILL_fn.flag`, whose presence holds redacted_account.

## Post-verification (the armed state, from the host's own mouth)

- FTMO launcher log 2026-07-30 03:44:53Z: `authority_gates_ON=True halted=False killed=False`.
- Live FTMO command line: `--tags crypto,energy_agri,sub_xvol_pullback
  --kill-flag pipeline_state/ULTIMATE_BOOK_KILL_ftmo.flag --poll-seconds 60` (flag absent = released).
- **Token**: `host-local\.gtos\activation\310fcf06….token.json`, issued
  2026-07-29 12:54:48Z by borhen, expires **2026-08-05**, namespace
  `operator_profile`, binds `config_digest_sha256 ffe16657feaf…`. The book's own
  startup line (03:44:49Z) declares `config_digest=ffe16657feaf,
  token_dir=host-local\.gtos\activation` — **digest and directory both
  match by the book's own arithmetic**. FN declares `be50dae4ca92` and has no token:
  fail-closed, as designed.
- Two findings recorded so nobody re-derives them the hard way:
  - **`trader` IS the renamed builtin Administrator** (SID `…-500`, profile path
    `host-local`). All book processes run as `trader`, so `~/.gtos/activation`
    resolves to the Administrator profile — the token is exactly where the gate looks.
    A scan for `.gtos` under other profiles finds nothing; there is ONE token dir.
  - **The token's digest is `config_digest_for(config, profile)` (canonical), not a
    raw file hash.** `Get-FileHash config\agent_config.yaml` gives `a2d5c675…` ≠
    `ffe16657…` and that mismatch is EXPECTED — do not "fix" it. The book's logged
    startup declaration is the correct way to check.
  - The token's free-text `note` still says "4-sleeve survivor book (metals_core, …)"
    — the 12:55Z intent, written before the 14:25Z three-sleeve adjustment. The note
    is descriptive; the binding fields + `--tags` are what enforce. Armed set is THREE.
- **C5 (`--recover-pre-gap-bar`) remains OFF** — untouched, per the package (OD-AI-7 is open).

## Operational notes for the next host session

- host-admin one-shot commands: the effective ceiling is ~8,191 chars of encoded command;
  transfer files in ≤2,800-char base64 chunks via `Add-Content -NoNewline`.
- pywinrm sometimes returns a spurious nonzero status with a CLIXML progress record
  on stderr ("Preparing modules for first use") — tolerate unless `S="Error"` is
  present, and rely on explicit hash/state checks instead of exit codes.
- Count processes with `Get-CimInstance Win32_Process` (never `Get-Process |
  CommandLine` on PS 5.1); each book/daemon appears as a parent/child python pair.
- Detached launches that must survive the session: WMI `Win32_Process.Create` with
  `CurrentDirectory` set.
