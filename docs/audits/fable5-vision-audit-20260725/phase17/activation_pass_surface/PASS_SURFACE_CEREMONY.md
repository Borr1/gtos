# Session CL pass-surface ceremony — verify and stop

Session CL, B2680–B2689. The measured approval set is empty. This is consequently a
**zero-mutation ceremony**: it verifies that the two live books still run the last promoted
set, captures the full host truth that is absent from the repository, and stops. It does not
turn a proposal into an approval.

Authority is `../receipts/CL_PASS_SURFACE_PRICING_V1.json` plus
`../receipts/CL_INCUBATION_PROPOSALS_V1.json`. `APPROVED_SET.json` is their fail-closed
projection. Package hashes are in `MANIFEST.json`.

## 1. Exact ordered ceremony

1. On the research laptop, run `python3 build_package.py`, then
   `python3 verify_pass_surface.py --check package`. A non-empty approved set, a changed input
   hash or a package hash mismatch is **STOP**.
2. The orchestrator—not Session CL—runs `capture_host_preflight.ps1` read-only on the host and
   returns `HOST_PREFLIGHT.json`. The script hashes the actual supervisor and both protected
   configs, records the literal `$books` hashtable block and its keys, captures every live
   `run_book.py` command line and creation time, hashes the firing ledgers, and extracts only
   the startup proving lines from the book logs. It does not run GTOS or MetaTrader code.
3. Back on the research laptop, run
   `python3 verify_pass_surface.py --check preflight --host-preflight HOST_PREFLIGHT.json`.
   Expect `RESULT: PASS — HOST MATCHES APPROVED NO-OP BASELINE`. Any mismatch is **STOP AND
   REBUILD/COMPOSE**; this package contains no overwrite instruction.
4. **STOP. Do not back up or edit the supervisor. Do not hold flags. Do not clear either
   `firing_sleeves.json`. Do not stop/restart a task or process. Do not copy runtime files.
   Do not read, inspect or re-mint a token.** There is no activation to perform.
5. For the ceremony receipt, capture `HOST_POSTFLIGHT.json` with the same read-only script and
   run `python3 verify_pass_surface.py --check postflight --host-preflight
   HOST_PREFLIGHT.json --host-postflight HOST_POSTFLIGHT.json`. Exact pre/post equality is the
   proof: full supervisor bytes and `$books` block, both protected-config hashes, command
   lines, process creation times and firing-ledger presence/hashes must not move.

## 2. The baseline that must prove

FTMO must have exactly these five tags:

`crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert,mx_btcusd_d1_donchian_20_breakout`

It must also have `--frontier-exits mx_btcusd_d1_donchian_20_breakout`,
`--spread-geometry-floor sub_mid_dn_revert,sub_xvol_pullback`, and the independent startup
proof `BookLauncher starting: tfs=[16388, 16408]`.

redacted_account must have exactly the first four tags, no `--frontier-exits`, the same spread-floor
selection, and `BookLauncher starting: tfs=[16388]`.

Both logs must show one `SPREAD-GEOMETRY FLOOR IS ON` line for each named repair sleeve. FTMO
must also show `FRONTIER EXIT CONTRACT IS ON ... target_5R`. Those lines distinguish the
intended set from a healthy but stale process. Exact live command lines distinguish it from
the two dangerous parser shapes: `--tags ""` selects all 32 built sleeves, while a non-empty
all-typo string produces a silent book.

The last committed live receipt identifies host branch
`vps/ultimate-conditioned-expansion-minimal-2026-06-18`, head prefix `267cccc94` and
supervisor SHA-256 prefix `63079cec`. Only prefixes were committed. The capture supplies the
full current values; a prefix mismatch means a later ceremony has moved the host and CL must
be rebuilt against that composition.

## 3. Protected bytes and prospective sizing

No byte of `config/agent_config.yaml` or `config/profiles/redacted_account.yaml` may move. The live
tokens bind config-digest prefixes `ffe16657feaf` and `e184a81d3b1b` respectively. This
package neither reads tokens nor attempts to reproduce their digest algorithm; it proves the
protected files are byte-identical pre/post.

No `--tags` change occurs, so B365 is not invoked: firing ledgers stay untouched and no
decision-day boundary is needed. The two incubation rows are `PROPOSED`, not `ARMED`; neither
proposal appears in a worker command line. If a later evidence pass approves any sleeve, it
needs a newly built non-empty ceremony, executed at a decision-day boundary or after backing
up and clearing the affected namespace's firing ledger.

## 4. Stop conditions

- Either authority receipt becomes non-empty or its hash changes.
- The host branch/head or supervisor hash no longer matches the latest committed receipt.
- There is not exactly one live book process per namespace.
- Any exact tag, frontier, spread-floor or derived-timeframe proof differs.
- An incubant appears in a live command line.
- Either protected config differs between preflight and postflight.
- Supervisor bytes, its `$books` block/keys, a command line, a process creation time, or a
  firing-ledger hash changes during this ceremony.
- Any operator step would require a flag, restart, ledger clear, payload copy or token action.

## 5. Rollback

There is nothing to roll back because the authorized mutation set is empty. If anything did
change, the operator departed from this package: hold the incident, preserve both captures,
and restore only from an independently verified host backup under the normal funded-machine
procedure. This package deliberately ships no runtime payload and grants no restart authority.
