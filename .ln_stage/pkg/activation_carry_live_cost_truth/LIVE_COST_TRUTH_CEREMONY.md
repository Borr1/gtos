# Session CN live-cost-truth carry ceremony

This is an orchestrator handoff. Session CN did not touch the VPS and did not run any
broker-capable entrypoint. The carry changes the cost screen for already-armed money, so the
ceremony is complete only after exact-byte preflight, an orderly two-worker restart, and a natural
post-restart packet proving captured v3 commission on each namespace.

## 1. Compose before touching the host

Resolve the CL and CM packages first. CN shares no supervisor or `run_book.py` destination, but it
does carry `book_owner.py`. If either sibling package also carries that path, do not use last-copy
wins: rebuild CN's two anchored owner additions on the resolved post-CL/CM owner bytes, regenerate
the CN manifest, and rerun `build_carry.py --check` plus `verify_carry.py --check payload` on the
laptop. An unrecognised preflight hash is a STOP, not permission to overwrite.

On the laptop, the package gates are:

```powershell
python3 docs/audits/fable5-vision-audit-20260725/phase17/activation_carry_live_cost_truth/build_carry.py --check
python3 docs/audits/fable5-vision-audit-20260725/phase17/activation_carry_live_cost_truth/verify_carry.py --check payload
```

## 2. Host preflight and backup

Use the book interpreter and repository paths recorded in `MANIFEST.json`. Run these checks before
stopping or copying anything:

```powershell
$Root = 'C:\Users\MSI\Documents\ai-trading-agent'
$Pkg = Join-Path $Root 'docs\audits\fable5-vision-audit-20260725\phase17\activation_carry_live_cost_truth'
$Py = Join-Path $Root '.venv-gtos\Scripts\python.exe'
& $Py (Join-Path $Pkg 'verify_carry.py') --check preflight --repo-root $Root
```

Capture SHA-256 for the three read-only config files named in the manifest and preserve that output
in the ceremony receipt. The post-copy values must be byte-identical. Also record whether each of
the four new destinations is absent or already at the manifest after-hash; rollback depends on that
distinction.

Stop both book workers through the established supervisor/service ceremony. Confirm they are down,
then copy the three existing destination files to a timestamped backup directory outside the repo.
Do not delete or overwrite an unrecognised destination.

## 3. Copy in the manifest order

Copy exactly the seven payloads in `MANIFEST.json.files[].copy_order`:

1. `src/costs/coverage.py`
2. `research/operations/broker_truth_layer_2026_07_27/BROKER_TRUE_COSTS_V1.json`
3. `src/costs/model.py`
4. `src/costs/__init__.py` from payload `costs___init__.py`
5. `src/components/ultimate_book/packet_economics.py`
6. `src/components/ultimate_book/book_owner.py`
7. `src/components/broker_net_cost_engine.py`

The last copy is the economic activation boundary. Files 1–4 are inert dependencies, file 5 keeps
historical v2 packets readable, and file 6 adds observation-only provenance. Do not copy file 7
until every prior after-hash verifies.

## 4. Offline postflight before restart

With both workers still stopped:

```powershell
& $Py (Join-Path $Pkg 'verify_carry.py') --check all --repo-root $Root
```

Re-hash the three token-bound/read-only configs and compare them with the preflight capture. Any
change is a STOP and rollback; this package has no config ceremony and does not authorize a token
re-mint.

## 5. Restart and prove the behavior

Restart the namespaces through the orchestrator's existing supervisor procedure, one namespace at
a time. Require a fresh worker PID/start record and normal management of any pre-existing position
before proceeding to the second namespace. Do not use a smoke order or any broker-capable test
script.

For the first naturally occurring post-restart `unit_placed` learning packet on each namespace,
require all of:

```text
modelled_cost_model_version = vnext_selected_cell_pretrade_cost_model_v3
modelled_commission_mode = broker_true_commission_default_v1
modelled_commission_cost_source_status = captured
modelled_commission_cost_artifact = BROKER_TRUE_COSTS_V1.json
modelled_cost_components.commission_r = <numeric, zero allowed only when broker truth says zero>
modelled_cost_r = <numeric>
modelled_cost_excludes = []
```

A v2 producer, comparator mode, `source_gap`, missing numeric commission, or non-empty exclusion
list is not proof. Until each namespace emits its line, record that namespace as
`CARRIED_RESTARTED_PROVING_PACKET_PENDING`, not activated/proven.

## 6. Stop and rollback

Stop immediately on any manifest stop condition, dependency/import/behavior failure, worker restart
failure, changed config digest, or missing/incorrect proving field. With both workers stopped:

- restore the three existing paths from the exact preflight backups;
- remove a new path only when preflight recorded it as absent; otherwise restore/retain its
  pre-existing after-byte;
- run `verify_carry.py --check rollback --repo-root $Root` and compare the state-specific new-path
  result with the preflight record;
- re-check the three config hashes;
- restart and prove both namespaces on the prior code.

Rollback changes no supervisor argument and no config byte. Preserve the failed postflight and
proving output alongside the rollback receipt; do not turn a failed carry into an unexplained retry.
