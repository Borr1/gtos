# Stage 3 — VPS runbook: carry the packet-emitter hardening

**You execute this, not an agent.** The VPS is a live, funded, connected host with
`trade_allowed: true` on both terminals and two healthy books running.

Read `PACKET_EMITTER_CARRY.md` §4 and §5 first. This file is the hands-on sequence.

---

## 0. What you are doing, in four sentences

You are copying five Python files to the VPS so that future packets record **holding time with a
stated provenance, swap nights on the broker clock, the spread the cost screen already computes,
and the governor's raw equity and open risk** — none of which any of the 99,112 existing packets
contain. You are also replacing a validator that could discard a whole cycle's packets on one bad
row with one that quarantines the bad row and leaves a visible marker in the main log. **Nothing in
this carry reads or writes a placement gate, opens an order path, or imports anything that can reach
a broker** — that is proven by test, see the carry doc §5. The books keep running throughout; the
only restart is the ordinary supervisor respawn in step 5.

**This changes what is recorded. It does not change what is decided.**

---

## 1. The one thing that can break this: file ORDER

`book_owner.py` imports the two new modules. If it lands first, the live book fails to import on its
next respawn and **stops**.

**Copy in the numbered order below and do not restart anything until all five are in place.**

The good news is that files 1–4 are inert on their own: nothing calls them until `book_owner.py`
lands. A copy that stops halfway changes nothing.

`broker_clock.py` (file 1) is the one genuinely optional file — **it does not exist on the VPS
today**. Without it the night count degrades to a labelled refusal and everything else works, so if
it gives you any trouble, skip it and carry it separately. It cannot break the book by its absence.

---

## 2. Preconditions

```powershell
# On the VPS, in the repo root.

# 2.1 The books are healthy right now (so you know what "unchanged" looks like afterwards).
Get-ScheduledTask -TaskName *GTOS* | Select TaskName, State

# 2.2 The gates are false. They MUST still read false after this carry.
Select-String -Path config\agent_config.yaml -Pattern "apply_to_execution|live_activation_allowed|live_broker_authority"

# 2.3 Record where the packet log is and how big it is, so step 6 can compare.
Get-Item shadow_logs\ultimate_book_runtime_learning_packets.jsonl | Select Name, Length, LastWriteTime

# 2.4 Back up the two files you are about to overwrite.
$stamp = Get-Date -Format "yyyyMMddTHHmmssZ"
New-Item -ItemType Directory -Force -Path "..\gtos-packet-carry-backup-$stamp"
Copy-Item src\components\ultimate_book\runtime_learning_packet.py "..\gtos-packet-carry-backup-$stamp\"
Copy-Item src\components\ultimate_book\book_owner.py "..\gtos-packet-carry-backup-$stamp\"
Write-Host "backup at ..\gtos-packet-carry-backup-$stamp"
```

**If 2.2 shows anything other than false, stop and do not proceed.** That is a different problem
and it outranks this one.

---

## 3. The carry — five files, in this order

From the branch `phase3/packet-emitter` @ commit recorded in `PACKET_EMITTER_CARRY.md`:

| # | source | destination |
|---|---|---|
| 1 | `src/utils/broker_clock.py` | `src\utils\broker_clock.py` *(new; optional — see §1)* |
| 2 | `src/components/ultimate_book/runtime_learning_packet.py` | same path |
| 3 | `src/components/ultimate_book/packet_economics.py` | same path *(new)* |
| 4 | `src/components/ultimate_book/packet_guard.py` | same path *(new)* |
| 5 | `src/components/ultimate_book/book_owner.py` | same path |

Optional, any time, no coupling: `scripts/ultimate_book_packet_silence_alarm.py`.

### What is deliberately NOT in this carry

- No config change. No new config key. Nothing to enable.
- No change to any placement gate, order path, or activation token.
- No emit-on-change, no join-key repair, no `modelled_cost_r` wiring — those are OD-P1/P2/P3 and
  they are your call, not this carry's.

---

## 4. Import check BEFORE you restart anything

This is the step that catches a bad copy while both books are still running on the old code.

```powershell
# Must print OK. If it raises, you have a partial copy -- restore from the 2.4 backup and stop.
python -c "import src.components.ultimate_book.book_owner; import src.components.ultimate_book.packet_guard; import src.components.ultimate_book.packet_economics; print('OK')"

# Confirms the optional dependency resolved (or didn't, which is fine).
python -c "from src.components.ultimate_book.packet_economics import BROKER_CLOCK_AVAILABLE as a; print('broker_clock available:', a)"
```

`broker_clock available: False` is **not** an error. It means night counts will come back as
`rollover_nights: null` with `error: broker_clock_module_unavailable` until file 1 lands. Everything
else works.

---

## 5. Let the supervisor restart the books

Do not launch `run_book.py` yourself. Stop the worker and let the supervisor respawn it — it loops
every 30 s and sleeps 3 s after launching, so 45 s is enough.

```powershell
# FTMO first, one book at a time.
Get-Process python | Where-Object { $_.CommandLine -like "*ftmo_server3*" } | Stop-Process
Start-Sleep -Seconds 45
Get-Process python | Where-Object { $_.CommandLine -like "*ftmo_server3*" } | Select Id, StartTime
```

Then confirm it is emitting before touching the second book:

```powershell
Get-Content shadow_logs\ultimate_book_runtime_learning_packets.jsonl -Tail 3
```

You should see fresh rows with a `created_at_utc` from the last couple of minutes. **Only then**
repeat for `redacted_account`.

---

## 6. Verification

### 6.1 The books are still deciding exactly as before

```powershell
# Gates unchanged.
Select-String -Path config\agent_config.yaml -Pattern "apply_to_execution|live_activation_allowed|live_broker_authority"

# Both terminals still connected and permitted.
python .tools\..\scripts\mt5_status_readonly.py  # if present; otherwise check the terminals directly
```

**Do not run any broker-capable script to verify this** — not `mt5_preflight.py`, not
`fn_smoke_trade.py`, not `dual_broker_execution_follower.py`. Reading the config and the terminal
UI is sufficient.

### 6.2 The new blocks are actually appearing

The economics block only attaches to packets that carry a position — `unit_placed`,
`position_managed`, `position_closed`, `position_adopted`. On a quiet book with no open positions
you will see none, and that is correct, not a failure.

```powershell
python - <<'PY'
import json, collections
p = "shadow_logs/ultimate_book_runtime_learning_packets.jsonl"
seen = collections.Counter(); econ = collections.Counter(); rej = 0
for line in open(p, encoding="utf-8"):
    line = line.strip()
    if not line: continue
    r = json.loads(line)
    et = r.get("event_type"); seen[et] += 1
    if r.get("event_type") == "packet_rejected": rej += 1
    if "economics" in r: econ[et] += 1
print("events:", dict(seen))
print("with economics block:", dict(econ))
print("packet_rejected markers:", rej)
PY
```

`packet_rejected markers: 0` is what you want. **Any non-zero value means the emitter refused a
packet** — the body is in
`shadow_logs\ultimate_book_runtime_learning_packets.jsonl.quarantine.jsonl` with its issue list.
That file existing at all is a signal; it is not created unless something was refused.

### 6.3 Nothing broke the existing corpus

```powershell
# Every packet in the log -- old and new -- must still validate.
python - <<'PY'
import json
from src.components.ultimate_book.runtime_learning_packet import validate_runtime_learning_packet
ok = bad = 0
for line in open("shadow_logs/ultimate_book_runtime_learning_packets.jsonl", encoding="utf-8"):
    line = line.strip()
    if not line: continue
    good, issues = validate_runtime_learning_packet(json.loads(line))
    if good: ok += 1
    else:
        bad += 1
        if bad <= 3: print("FAIL:", issues[:4])
print(f"validated ok={ok} bad={bad}")
PY
```

`bad=0` is the requirement. On this machine the same check passes 99,112 / 99,112 against the
2026-07-25 export.

### 6.4 Silence alarm (optional, and useful from now on)

```powershell
python scripts\ultimate_book_packet_silence_alarm.py `
  --packets shadow_logs\ultimate_book_runtime_learning_packets.jsonl `
  --expect-namespace operator_profile `
  --expect-namespace redacted_account_live_bee34003 `
  -o shadow_logs\packet_silence_report.json
```

Exit 1 with `DEAD: <namespace>` is the one that matters — it means a book emitted **nothing at
all**. Exit 1 with `SILENT:` and multi-hour weekend gaps is normal; the live baseline shows 43
such gaps for FTMO and 5 for redacted_account across 37 days.

---

## 7. Rollback — under two minutes, from any point

```powershell
$backup = "..\gtos-packet-carry-backup-<stamp>"   # from step 2.4
Copy-Item "$backup\runtime_learning_packet.py" src\components\ultimate_book\ -Force
Copy-Item "$backup\book_owner.py"              src\components\ultimate_book\ -Force
Remove-Item src\components\ultimate_book\packet_economics.py -ErrorAction SilentlyContinue
Remove-Item src\components\ultimate_book\packet_guard.py     -ErrorAction SilentlyContinue
# then restart both workers exactly as in step 5
```

`broker_clock.py` can be left in place — nothing on the old build imports it.

**Packets written while the carry was live are not affected by rollback and stay readable.** The
`economics` key is additive and the old validator ignores unknown keys, so a rolled-back build
reads the newer packets without complaint. That is the point of not bumping `SCHEMA_VERSION`.

---

## 8. Two things worth knowing before you start

### 8.1 This carry only helps from the moment it lands

Nothing here retrofits the 99,112 existing packets. They will never contain a spread, a governor
state, or a carry-night count. Every day it is not deployed is a day of shadow data that cannot
bear weight on OD-3 — which is why Stage 3 was brought forward ahead of its place in the plan.

### 8.2 The disk goes the wrong way, for now

The corpus is 826 MB uncompressed per 37 days, and the economics block makes position-carrying
packets slightly larger. It attaches to about 21 % of packets, so expect a modest increase.

**OD-P1 is what pays for it and then some**: emit-on-change on `position_managed` would drop 76.9 %
of the entire stream with no measured information loss. It is not in this carry because it changes
what the book records and that is your decision. If disk is a concern, take OD-P1 next.
