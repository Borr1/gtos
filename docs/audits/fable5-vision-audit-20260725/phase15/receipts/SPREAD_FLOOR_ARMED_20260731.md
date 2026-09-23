# The spread-geometry floor is ARMED on both books — ceremony receipt, 2026-07-31

**Executed by the orchestrator on CE's package** (`phase15/activation_carry_spread_floor/`),
authority OD-HISTORICAL-FIRST §3 and the standing ratifications. Host commit **`267cccc94`**
on `vps/ultimate-conditioned-expansion-minimal-2026-06-18`.

## What is armed

`--spread-geometry-floor sub_mid_dn_revert,sub_xvol_pullback` on **both** accounts. Proving
lines (the ceremony's own standard — the log line, never the process list) at **11:01:02Z
(FTMO)** and **11:01:05Z (redacted_account)**: `SPREAD-GEOMETRY FLOOR IS ON for <sleeve> at
spread_r <= 0.1000 (inherited from the send gate's own limit)` — one per sleeve per account.
`mx_btcusd`'s FRONTIER banner still renders (`target_5R`), FTMO tfs `[16388, 16408]`, FN
`[16388]`. **Both token digests unchanged** (`ffe16657feaf`, `e184a81d3b1b`) — the carry
wrote only `.py` files and the supervisor launcher; no config byte moved.

Planning numbers (recent-fold basis, CE §3): `sub_xvol_pullback` **+0.256 R/day**,
`sub_mid_dn_revert` **+0.041 R/day** — plus the conviction-count repair (a doomed intent no
longer inflates the day's Kelly multiplier; worst case measured +25.2 %/day). NEUTRAL sleeves
(`crypto`, `energy_agri`) deliberately not armed. Neither REPAIR sleeve admits; this is a
fidelity repair, not an admission.

## Steps executed

flat-check (0 pos both, monitor) → flags held → package transferred chunk-wise,
hash-verified 6/6 → **preflight PASS** (host at AC's `book_engine` bytes exactly as CE
predicted) → backup `gtos-spreadfloor-backup-20260731T104432Z` with sha manifest → carry in
`copy_order`, each verified (`1ea1b6bc / 42c1bd6c / b7a82dc3 / 39ddfd51`) → **verify_carry
--check all PASS** (deps, imports, behaviour incl. the conviction-count gate and every
fail-closed parse) → supervisor ps1 edited (pull-edit-push, sha `e46fe321` → `63079cec`;
`.before-spreadfloor` kept) → firing ledgers cleared (B365) → restart → proving lines →
flags released → host commit.

## Two operational truths this ceremony taught, both now standing knowledge

1. **The kill flag is a STAND-DOWN, not a process exit.** Both books launched 2026-07-31
   01:23 logged `killed=True` and ran all day, refusing. Flag-hold does NOT recycle a book
   process; a restart requires stopping the processes (task-tree stop does not reach them —
   they are WMI-detached). Every prior ceremony's "restart" worked by a path that no longer
   held tonight; the correct cycle is: flags held → **force-stop the book pythons** (safe
   when flat: stand-down already active, exits read trade records) → fresh supervisor →
   release. Filed for the ceremony template.
2. **`Stop-ScheduledTask` does not kill a supervisor that holds the single-instance lock
   from an earlier life** — and a CIM `CommandLine` filter can return an empty set for
   processes in another logon session, which reads as "drained" when nothing drained.
   **Verify by creation time and by the proving log line, never by a count.** The books that
   first relaunched after the edit were 01:23 survivors; caught because the ceremony verifies
   command lines.

## Week-one watch (CE §5, unchanged)

Stop conditions 1–4 as written; **condition 3 is the one to watch**: the floor's refused-leg
count should roughly match the send-layer `cost_screen_spread_r` skips the same sleeves
produced before — a systematic gap means one layer is not measuring what the page assumes.
Telemetry: `generation.spread_geometry_floor` `{evaluated, refused, sleeves}` per cycle.
