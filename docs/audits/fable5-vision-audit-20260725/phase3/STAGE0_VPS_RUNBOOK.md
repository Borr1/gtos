# Stage 0 — VPS runbook: carry the activation token, then the gate tripwire

**Executed by Borhen. Never by an agent.** The VPS is a live, funded, connected host —
supervisor task Running, both books healthy, both MT5 terminals connected, `trade_allowed`
true on both, ~108 k and ~96.1 k. Everything below was prepared and proved on the research
laptop; nothing in it was run against that host.

Written to be followed at 2 a.m. by someone who is tired. Read §0 and §1 before you touch
anything. If a **STOP** line fires, stop — the rollback in §6 puts you back where you
started in under a minute.

---

## 0. What you are doing, in three sentences

Right now the only thing between that host and live orders is config: two false booleans in
`agent_config.yaml` and one key that is absent (§7 corrects a claim in `CLAUDE.md` here).
Absence-of-halt is fail-open — a fresh clone, a reset config, a restored backup all trade.
You are installing the opposite: a **presence-of-authorization** check inside
`RealMT5.order_send`, so an exposure-increasing order requires a signed, unexpired,
account-bound token that lives outside the repo, and no token means no order.

**Risk-reducing requests — closes, partial closes, pending cancels, stop tightenings — pass
without any token.** That is the one property the whole mechanism is built around: a token
lapses by expiry, positions do not.

**This changes nothing while the gates are false.** In shadow the book returns before
`order_send` is ever called (proof in §5). You are installing a brake on a car that is
parked, which is the only sane time to do it.

---

## 1. The one thing that can break this: file ORDER

> **STOP — read this twice.**
>
> `run_book.py` imports `activation_token` at module scope, and `activation_token` imports
> `TRADE_ACTION_MODIFY` and `TRADE_ACTION_REMOVE` from `mt5_interface`. **The VPS's
> `mt5_interface.py` has neither** (measured: `git show redacted_host:src/mt5/mt5_interface.py`).
>
> If `activation_token.py` or `run_book.py` land **before** `mt5_interface.py`, then
> `run_book.py` raises `ImportError` at import on **both accounts**. The supervisor only ever
> *starts* a missing book — it never stops one — so you get an infinite 5-minute restart
> loop, and `manage_open_positions` (the code that manages exits on any open position) stops
> running entirely.
>
> **Copy `mt5_interface.py` first. Always. It is safe on its own — it adds two integer
> constants and a comment, and nothing on the VPS reads them yet.**

Copy order is: **1 → 2 → 3 → 4 → 5.** Do not reorder. Do not copy them "all at once" with a
folder sync unless you have stopped the books first (§2 tells you not to).

---

## 2. Preconditions — check these before copying anything

Run each on the VPS. All five must hold.

| # | Check | Command | Expected |
|---|---|---|---|
| 2.1 | Python version | `python --version` | `3.13.x` (measured 3.13.13). Anything ≥3.10 works; the carry uses PEP-604 unions the VPS already runs. |
| 2.2 | Both books alive | `Get-CimInstance Win32_Process -Filter "name like '%python%'" \| ? {$_.CommandLine -like '*run_book.py*'} \| select ProcessId, CommandLine` | Two rows, one per namespace |
| 2.3 | No open positions **preferred, not required** | `python .tools\monitor_books.py` | Note the count. If positions are open, §5.4 matters more. |
| 2.4 | Gates still false | `Select-String -Path config\agent_config.yaml -Pattern "ultimate_book_live_activation_allowed\|ultimate_book_apply_to_execution"` | `apply_to_execution: true`, `live_activation_allowed: false` |
| 2.5 | You have a rollback point | `git -C <repo> rev-parse HEAD` and write it down | a commit hash on paper |

> **STOP if 2.4 shows `live_activation_allowed: true`.** That is not a deployment
> precondition failure, it is an incident. Nothing should have set it. Investigate before
> anything else.

**Do NOT stop the books to do this.** They are in shadow; a running book will simply keep
using the old code until you restart it in §4. Stopping them removes exit management from
any open position for the duration, which is a strictly larger risk than a stale import.

---

## 3. The carry — five files, in this order

All paths are relative to the repo root on the VPS. Every one of these was measured against
the VPS lineage commit `redacted_host`; the deltas are exact.

| # | File | VPS → new | What it is |
|---|---|---|---|
| 1 | `src/mt5/mt5_interface.py` | **+5 lines** | `TRADE_ACTION_MODIFY = 7`, `TRADE_ACTION_REMOVE = 8`, comment. Inert on its own. |
| 2 | `src/safety/activation_token.py` | **NEW, 1,080 lines** | The gate. Imports only `mt5_interface`, `broker_profile`, and (lazily) `runtime_halt` — all three already on the VPS and byte-identical. |
| 3 | `scripts/gtos_activation_token.py` | **NEW, 224 lines** | mint / status / revoke. You need this in §5. |
| 4 | `src/mt5/mt5_real.py` | **+105 lines, −0** | The `order_send` choke point, `set_activation_context`, `account_login_sha256`, `positions_for_activation`. |
| 5 | `run_book.py` | **+36 lines, −0** | One import, the activation-context declaration, and the `.env` refusal (§7.3). |

**`src/safety/` must go across as the package it is, not as one file** — `activation_token`
lazily imports `runtime_halt` at call time. `runtime_halt.py` and `src/safety/__init__.py`
are already there and are **byte-identical** to mainline (verified), so you copy nothing
else; just do not delete anything.

### What is deliberately NOT in this carry

`src/components/execution.py` also changed on the laptop. **Do not copy it.** It differs from
the VPS by **2,225 lines**, of which only 47 are this work; the rest is unrelated mainline
drift and carrying it would be a blind deployment of a year of changes into a live engine.
The same applies to `book_owner.py` (68 lines of drift) and `book_engine.py` (237). Those
changes are laptop-side hardening. They are not part of Stage 0.

### Copy

```powershell
# From wherever you staged the five files. One at a time, in order.
Copy-Item .\staged\mt5_interface.py        <repo>\src\mt5\mt5_interface.py
Copy-Item .\staged\activation_token.py     <repo>\src\safety\activation_token.py
Copy-Item .\staged\gtos_activation_token.py <repo>\scripts\gtos_activation_token.py
Copy-Item .\staged\mt5_real.py             <repo>\src\mt5\mt5_real.py
Copy-Item .\staged\run_book.py             <repo>\run_book.py
```

---

## 4. Import check BEFORE you restart anything

This is the step that catches a bad copy while both books are still running the old code.

```powershell
cd <repo>
python -c "import src.safety.activation_token as t; print('token module OK', t.TOKEN_VERSION)"
python -c "import src.mt5.mt5_real; print('adapter OK')"
python -c "import ast,sys; ast.parse(open('run_book.py',encoding='utf-8').read()); print('run_book parses OK')"
python scripts\gtos_activation_token.py status
```

Expected:

```
token module OK gtos_activation_token_v1
adapter OK
run_book parses OK
{ "token_dir": "C:\\Users\\<you>\\.gtos\\activation", "token_dir_exists": false,
  "signing_key_present": false, "tokens": [] }
```

> **STOP on any ImportError.** You are in the §1 failure mode. The books are still running
> the old code and are fine. Fix the copy (almost certainly `mt5_interface.py` did not land)
> and re-run this section. Do not restart a book until all four commands pass.

> **STOP if `token_dir` is anywhere inside the repo.** It must be under your Windows profile.
> If it points into the repo, something set `GTOS_ACTIVATION_TOKEN_DIR` — see §7.3, and do
> not proceed until it is gone.

---

## 5. Verification — zero-token status, then one healthy shadow cycle

### 5.1 Zero-token status

`python scripts\gtos_activation_token.py status` — you already ran it in §4. The state you
want is exactly the one above: **no directory, no key, no tokens**. That is the fail-closed
state and it is the correct state to deploy in. Do not mint a token now. Minting is a
separate, deliberate act for the day you actually activate.

### 5.2 One healthy shadow cycle

Restart **one** book — FTMO first — and watch a single cycle.

```powershell
# Let the supervisor do it: stop the FTMO worker and wait for the respawn.
# The supervisor loops every 30 s (run_book_supervisor.ps1:121) and sleeps 3 s
# after launching, so 45 s is enough.
Get-CimInstance Win32_Process -Filter "name like '%python%'" |
  ? {$_.CommandLine -like '*run_book.py*--namespace operator_profile*'} |
  % { Stop-Process -Id $_.ProcessId -Force }
Start-Sleep -Seconds 45
Get-Content .\shadow_logs\run_book_console.log -Tail 40
Get-Content .\shadow_logs\run_book_console.log.err -Tail 20   # ImportError lands here
```

> The log paths come from `scripts/run_book_supervisor.ps1:86-87`:
> FTMO → `shadow_logs\run_book_console.log`,
> redacted_account → `shadow_logs\run_book_fn_console.log`, each with a `.err` sibling.
> The supervisor launches with `-WorkingDirectory $repo` (`:110`), which is why the config
> digest in §5.2 resolves at all — `run_book.py` passes `--config` as a **relative** path.

Four lines must appear, in this order:

1. `account identity verified (namespace=operator_profile): fields=[...]`
2. `activation context declared (namespace=operator_profile, config_digest=<12 hex>, token_dir=C:\Users\...\.gtos\activation)`
3. `book launcher: profile=... authority_gates_ON=False halted=... killed=...`
4. a normal cycle line

> **The one that matters is line 2, and specifically `config_digest=` followed by twelve hex
> characters.** If it says `config_digest=unavailable`, the process cannot read its own
> config files from its working directory. It is not dangerous today — an unbound token
> would still work — but it means a config-bound token would be refused later, so fix it
> before you ever mint one.

> **STOP if `authority_gates_ON=True`.** Shut the book down. That is not this deployment.

**The mode-string check.** `run_book.py:201` constructs `RealMT5` directly rather than going
through `create_mt5`, so nothing validates a mode string on this path. Line 2 appearing at
all is the proof that the object really is the guarded adapter: `set_activation_context`
exists only on `RealMT5`, and the launcher would have logged an exception instead.

### 5.3 Then the second book

Repeat 5.2 for the redacted_account worker — namespace **`redacted_account_live_bee34003`**, profile
`redacted_account`, log `shadow_logs\run_book_fn_console.log`. Do them **one at a time**: if the
first one misbehaves you still have a working book on the other account, and you will know
which change caused it.

### 5.4 If a position was open during the restart

Confirm it is still managed: `python .tools\monitor_books.py` and check the position is
still listed and the book that owns it is up. The carry does not touch adoption or exit
management, and a zero-token shadow book manages exits exactly as before — but check,
because this is the only irreversible thing in the room.

---

## 6. Rollback — under a minute, from any point

The carry adds files and adds lines. Nothing is deleted, nothing is rewritten.

```powershell
cd <repo>
git checkout -- run_book.py src\mt5\mt5_real.py src\mt5\mt5_interface.py
Remove-Item src\safety\activation_token.py, scripts\gtos_activation_token.py -ErrorAction SilentlyContinue
# then restart both workers exactly as in 5.2
```

If the repo on the VPS is not a clean checkout, restore the five files from the commit you
wrote down in §2.5 instead.

**Rollback is safe at every point in this runbook**, including with both books restarted,
because a zero-token shadow book and a pre-carry shadow book do the same thing: log
`would_units` and send nothing.

---

## 7. Three things that are not what the docs said

### 7.1 The brake is two booleans and one absence, not three booleans

`CLAUDE.md` says "three false YAML booleans ... at `agent_config.yaml:1161-1163`". In this
repository there are **two** — `ultimate_book_apply_to_execution: true` and
`ultimate_book_live_activation_allowed: false` at `config/agent_config.yaml:1249-1250` — and
`ultimate_book_live_broker_authority`, which **appears in no committed config at all** and
resolves `False` from a code default (`bridge.py:67-70`). The 1161-1163 line numbers came
from the exported VPS working tree, which is a different file.

This matters for what you watch for: the third gate cannot be "flipped", it can only
**appear**. Nothing at any layer would have caught it appearing as `true`. The tripwire in §8
does.

### 7.2 The alerting daemon does not run on the current repo build

`.tools/monitor_books.py` crashes on its first cycle at mainline HEAD — an unpacking bug
introduced by B58 that this session fixed (block B105). **The VPS still runs the older,
working version, so your alerts are fine today.** But do not deploy the repo's
`monitor_books.py` casually: deploy the fixed one from §8 or leave the VPS's alone.

### 7.3 A line in `.env` could relocate the entire authorization root

`run_book.py` calls `load_dotenv(override=True)` **before** it imports the safety module, and
the token layer reads `GTOS_ACTIVATION_TOKEN_DIR` at call time — then mints a fresh signing
key wherever it is pointed. So one line in the repo's own untracked `.env` was a self-issued
authorization for a funded account whose digest is published in-tree. Fixed in the carried
`run_book.py` (block B103): the machine's value is captured before `.env` is read and
restored after, and the gate refuses exposure-increasing requests when the activation
directory resolves inside the working tree.

**Action for you:** check the VPS `.env` for that variable.

```powershell
Select-String -Path .env -Pattern "GTOS_ACTIVATION_TOKEN_DIR"
```

Expected: no match. If there is one, delete the line — the carried `run_book.py` will refuse
it anyway and say so on stderr, but a line that exists is a line someone will "fix" later.

---

## 8. Ceremony B — the gate tripwire (separate, and it can wait)

Do this **after** §1–§6 have been green for at least one full trading day. It is not
load-bearing for the token; it is what converts "nothing watches the gates" into monitoring.

Two files:

| File | VPS → new | Note |
|---|---|---|
| `src/components/ultimate_book/launcher.py` | **+69, −0** | Publishes gate state, resolved derisk mode and the un-digested env in the per-tick heartbeat. **Byte-identical to mainline before this change**, so the carry is exactly these 69 lines. |
| `.tools/monitor_books.py` | **+241** | 182 lines are the tripwire and the cycle-0 crash fix; **59 are the B58 daily-reset clock correction**, which the VPS does not have. |

That second row is a decision, not a copy: the VPS's monitor currently computes its
daily-loss alerts on a hardcoded UTC+3 that B56/B58 measured as wrong (the brokers follow the
**US** DST calendar, and the two calendars disagree ~4 weeks a year). Carrying the file fixes
that too. **That is an improvement, but it changes when your daily-loss alerts fire**, so do
it deliberately and on a quiet day, not bundled with the token.

Verification after Ceremony B:

```powershell
python .tools\monitor_books.py           # one-shot; must print a cycle and exit 0
Get-Content .\pipeline_state\ultimate_book\operator_profile\heartbeat.json
```

The heartbeat must now contain `gates`, `runtime_effect_now`, `profile`,
`derisk_mode_effective` and `env`. If it does not, the launcher did not restart.

Then, deliberately, prove the tripwire fires: **on the laptop, not here.** Drill D-1 in
`TOKEN_CHAOS_DRILLS.md` is exactly that test and it is designed to be run somewhere that is
not a funded account.

---

## 9. What is still true after all of this

- **The token does not stop you flipping the gates.** It stops an *unauthorized process*
  trading. An operator who flips `live_activation_allowed` and mints a token has activated
  the system, which is the intended path. The tripwire is what tells you it happened.
- **The signing key sits beside the tokens.** This is tamper-evidence against accident, not
  defence against someone with write access to your Windows profile. Stated plainly because
  an overclaimed security property is worse than none.
- **`scripts/mt5_preflight.py` no longer places orders** (block B102): Test 5 now uses
  `order_check`, which validates against the broker's server and returns the same retcode
  without placing anything. If you have a runbook line with `--test-order` in it, the script
  now refuses and tells you why.
- **Six drills remain unrun.** `TOKEN_CHAOS_DRILLS.md` specifies them. Two of them
  (D-2, D-6) can only be answered on a real MT5 terminal, and one of those answers a question
  this session could not: what MT5 actually does with an over-volume close.
