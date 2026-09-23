# Ceremony — arm the bounded learning-lane vector

Session CO, wave 17, B2800–B2849. The orchestrator executes this page; Session CO did not
touch the VPS. The package is `phase17/lane_weights_ceremony/`.

## 0. Decision being implemented

The current cost-true read emits this complete vector:

| account | sleeve | multiplier |
|---|---|---:|
| FTMO | `crypto` | **1.15** |
| FTMO | `mx_btcusd_d1_donchian_20_breakout` at `target_5R` | **1.15** |
| FTMO | `energy_agri`, `sub_xvol_pullback`, `sub_mid_dn_revert` | 1.00 |
| redacted_account | all four armed sleeves | 1.00 |

The declared band is **[0.50, 1.15]**. The carrier is all-or-neutral: a missing, stale,
malformed, wrongly scoped, out-of-band, or badly signed source becomes **1.00 for every
scoped sleeve** and logs an ERROR. The governor, gross-risk cap, soft/hard stops, and
breach-flatten path remain downstream and senior.

Evidence and A/B: `phase17/receipts/CO_CURRENT_VECTOR_V1.json`. FTMO `p_pass` moves
0.99980 → 0.99982 (delta +0.00002 against pooled 2-SE 0.0001743); worst day moves
-0.94282% → -1.08424% and worst week is unchanged. redacted_account is byte-for-byte the neutral
vector in economic effect: `p_pass` 0.10128 → 0.10128 and both tails unchanged.

## 1. Package and host preflight

The last host-proven state is commit `267cccc94`, receipt
`phase15/receipts/SPREAD_FLOOR_ARMED_20260731.md`. The host is a composed carry lineage.
**Do not copy mainline `book_engine.py`, `book_owner.py`, or `run_book.py`.** This package
applies only CO's edits to the exact after-bytes proven live by the spread-floor ceremony;
`build_carry.py` reproduces every payload and `MANIFEST.json` gives full before/after hashes.

Transfer the package directory to the same relative path on the host, without copying any
payload into a live destination. Then:

```powershell
cd C:\Users\MSI\Documents\ai-trading-agent
& .\.venv-gtos\Scripts\python.exe `
  docs\audits\fable5-vision-audit-20260725\phase17\lane_weights_ceremony\verify_carry.py `
  --check preflight --root .
```

Expect `RESULT: PASS`: four modified files at the exact previous carry hashes; two new code
paths absent; supervisor hash beginning `63079cec` and containing the current five-/four-
sleeve tags, FTMO frontier contract, and both spread-floor selectors. Any mismatch is a
**STOP**: capture the actual hashes and rebuild against those bytes. Do not overwrite drift.

## 2. Backup and carry order

Confirm both accounts flat. Hold both per-account kill flags. Back up the six destination
paths plus `scripts\run_book_supervisor.ps1` to a timestamped directory with a SHA-256
manifest. Then copy and verify in this order:

| order | payload | live destination | after SHA-256 |
|---:|---|---|---|
| 1 | `files\lane_weights.py` | `src\components\ultimate_book\lane_weights.py` | `8d1446563b1b…` |
| 2 | `files\runtime_learning_packet.py` | same path under `src\components\ultimate_book` | `c804aaaace49…` |
| 3 | `files\book_engine.py` | same path | `5c8af2a9ab12…` |
| 4 | `files\book_owner.py` | same path | `cf6aa69d402b…` |
| 5 | `files\run_book.py` | `run_book.py` | `ea73af4d1500…` |
| 6 | `files\gtos_lane_weights.py` | `scripts\gtos_lane_weights.py` | `10806a82801e…` |

The order is load-bearing. `book_engine.py` imports the new module; `book_owner.py` passes a
new engine kwarg; `run_book.py` passes a new owner kwarg. The first four default to disabled
until the launcher receives both external paths, so an interrupted carry does not arm a
weight. Never put the supervisor arguments in place before file 5.

Verify carried bytes before editing the supervisor:

```powershell
& .\.venv-gtos\Scripts\python.exe docs\audits\fable5-vision-audit-20260725\phase17\lane_weights_ceremony\verify_carry.py --check postflight --root .
```

## 3. Stage the external declarations and private key

The local handoff key is at
`/Users/borr/GTOSActive/ceremony-secrets/session-co-20260801/lane_weights.key`. It is 32 bytes,
mode 0600, outside the repository; neither it nor a digest of it is committed or printed.
Transfer it through the same private channel used for activation material. On Windows:

```powershell
New-Item -ItemType Directory -Force C:\ProgramData\GTOS\lane-weights | Out-Null
# transfer the key and the two signed JSON files, then restrict the key ACL:
icacls C:\ProgramData\GTOS\lane-weights\lane_weights.key /inheritance:r
icacls C:\ProgramData\GTOS\lane-weights\lane_weights.key /grant:r `
  "${env:USERNAME}:(R)" "SYSTEM:(F)" "Administrators:(F)"
```

Copy:

- `files\operator_profile.json` →
  `C:\ProgramData\GTOS\lane-weights\operator_profile.json`
- `files\redacted_account_live_bee34003.json` →
  `C:\ProgramData\GTOS\lane-weights\redacted_account_live_bee34003.json`

Both are effective **2026-08-02 through 2026-08-08 UTC, inclusive**. Verify before arming:

```powershell
$k = 'C:\ProgramData\GTOS\lane-weights\lane_weights.key'
$w = 'C:\ProgramData\GTOS\lane-weights'
& .\.venv-gtos\Scripts\python.exe scripts\gtos_lane_weights.py verify `
  --input "$w\operator_profile.json" --key $k `
  --namespace operator_profile `
  --tags crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert,mx_btcusd_d1_donchian_20_breakout
& .\.venv-gtos\Scripts\python.exe scripts\gtos_lane_weights.py verify `
  --input "$w\redacted_account_live_bee34003.json" --key $k `
  --namespace redacted_account_live_bee34003 `
  --tags crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert
```

Both must return `"ok": true`, `"signature_verified": true`, and the vectors in §0.

## 4. Supervisor edit and decision-day boundary

Apply `SUPERVISOR_ARGS.diff` semantically to the live host file. Add exactly two arguments per
book:

```text
FTMO:
  --lane-weights C:\ProgramData\GTOS\lane-weights\operator_profile.json
  --lane-weights-key C:\ProgramData\GTOS\lane-weights\lane_weights.key

redacted_account:
  --lane-weights C:\ProgramData\GTOS\lane-weights\redacted_account_live_bee34003.json
  --lane-weights-key C:\ProgramData\GTOS\lane-weights\lane_weights.key
```

Do not change tags, frontier exits, spread floors, `--entry-hour`, or `--weekend-flat`.

**Restart inside 00:00:00–00:05:00 UTC on 2026-08-02.** The controller admits a previously
unseen non-neutral vector only in that five-minute boundary window, persists it beneath
`pipeline_state\ultimate_book\<namespace>\lane_weights_latch.json`, and reuses those signed
bytes across every same-day restart. If the window is missed, it deliberately latches 1.00
for the day. Do not delete a latch and retry intraday; stage a new effective day instead.

The 2026-07-31 ceremony established that kill flags stand books down but do not terminate the
detached processes. With flags held and books flat: force-stop the two book process trees,
start a fresh supervisor, and verify creation times plus the proving lines. Do not infer a
restart from the scheduled-task state or process count alone.

## 5. Proving lines and release gate

The launcher emits one line before broker connection. FTMO must show exactly:

```text
LANE WEIGHTS ACTIVE: crypto=1.15 energy_agri=1.00 mx_btcusd_d1_donchian_20_breakout=1.15 sub_mid_dn_revert=1.00 sub_xvol_pullback=1.00
```

redacted_account must show exactly:

```text
LANE WEIGHTS ACTIVE: crypto=1.00 energy_agri=1.00 sub_mid_dn_revert=1.00 sub_xvol_pullback=1.00
```

Absent, `LANE WEIGHTS NOT ACTIVE`, or `LANE WEIGHTS NEUTRAL` means **do not release the kill
flags**. Also require the existing frontier/spread proving lines, fresh worker creation times,
unchanged activation-token config digests, healthy management cycles, and one runtime-learning
packet whose `lane_weight_provenance.source_digest_sha256` matches the signed declaration.

After the supervisor edit, run:

```powershell
& .\.venv-gtos\Scripts\python.exe docs\audits\fable5-vision-audit-20260725\phase17\lane_weights_ceremony\verify_carry.py `
  --check activated --root . --key C:\ProgramData\GTOS\lane-weights\lane_weights.key
```

Only then release both kill flags.

## 6. Week-one telemetry and veto

At the end of each UTC day, audit every packet emitted since activation. For day 1 use
`--days 1`; increment through 7:

```powershell
& .\.venv-gtos\Scripts\python.exe scripts\gtos_lane_weights.py telemetry `
  --input shadow_logs\ultimate_book_runtime_learning_packets.jsonl `
  --weights C:\ProgramData\GTOS\lane-weights\operator_profile.json `
  --key C:\ProgramData\GTOS\lane-weights\lane_weights.key `
  --namespace operator_profile `
  --tags crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert,mx_btcusd_d1_donchian_20_breakout `
  --start-day 2026-08-02 --days 1 `
  --output pipeline_state\ultimate_book\operator_profile\lane_weights_telemetry.json
```

Run the same command for redacted_account with its four tags and signed file. Any missing day,
provenance hole, source-digest mismatch, non-active status, or applied-weight mismatch is a
stop-and-investigate condition.

The live forward stream is **VETO ONLY, never fitting input**. Predeclared reversals from
`CO_CURRENT_VECTOR_V1.json`:

- either FTMO up-weight returns to 1.00 at the next boundary when it has at least 3 closed
  fills and live mean R ≤ 0;
- FTMO `crypto` moves to 0.50 at its calibrated down boundary (the receipt's 11-stop-out
  first-passage equivalent) or stops at cumulative net R -12.375;
- FTMO `mx_btcusd…` has no calibrated inferred down/kill boundary; its pre-registered risk
  floor is cumulative net R -9.089;
- every existing five-sleeve account stop condition remains senior and unchanged.

A live record weaker than MEASURED may brake but may never support or raise a weight. Every
new vector must be signed and staged before a future UTC boundary.

## 7. Rollback

Behavior rollback is two arguments per book: remove `--lane-weights` and
`--lane-weights-key`, keep both kill flags held, restart the detached books, verify the two
arguments and ACTIVE lines are absent, then release. The next process injects no rerate and
all sleeves are x1.00. The signed files and latches may be archived; they are inert without
the args.

If the carry itself is defective, restore `run_book.py` before `book_owner.py`, then owner
before engine, then runtime packet; remove the two new modules/scripts. Restore the supervisor
first so an old launcher never receives unknown arguments. Verify backup hashes and fresh
management cycles before release.

On 2026-08-09 the declarations become stale and the controller automatically latches neutral
for that day. Renewal requires a newly signed file staged before its effective boundary; never
extend the committed JSON by editing its dates, because that invalidates the signature.
