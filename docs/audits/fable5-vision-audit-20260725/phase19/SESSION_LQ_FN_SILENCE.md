# Session LQ — the redacted_account silence explained, and the labelling fix landed

Session LQ · phase19 · host `C:\Users\MSI\Documents\ai-trading-agent` · branch
`vps/ultimate-conditioned-expansion-minimal-2026-06-18` · host HEAD at start
`c989b1198` (Session LO).

**Result: the 2026-07-02 → 2026-07-31 silence is explained, and it is not what the question
assumed.** It was not a redacted_account defect and it was not redacted_account-specific. **Both** books were
deliberately switched to shadow/intelligence-only mode by a committed config change on
2026-07-02T05:39:52Z, and neither book placed a single order for the next four weeks. redacted_account ran
continuously, generated 446 intents, and had every one of them diverted to shadow *before* the
order-send path — so the activation gate was never even consulted in that window. F1 is a
**separate, later, third** cause that only became live on 2026-08-04.

The `timeout_no_fill` labelling fix is now **live on both books**, landed at a clean restart with
both accounts flat; every fenced value is byte-identical across the restart.

---

## 0. Findings first

1. **The silence has three sequential causes, not one.** Shadow-mode config (27 days) → armed but a
   narrowed sleeve set with genuinely no setups (5 days) → the F1 token wall (2 hours). §1–§4.

2. **It was estate-wide, not redacted_account-specific.** FTMO was silent in the same window for the same
   reason: 1833/1838 of its cycles report `shadow_apply_to_execution_off`, 0 placed. The premise
   "a month of a *funded account* doing nothing" is true of *both* funded accounts. §2.

3. **FTMO's July P&L was not the system.** FTMO shows +13,338 on 2026-07-03 and a −7.22 on
   2026-07-29. Both are **magic 0 with an empty comment** — manual/owner trades. The book's magic is
   `20260401` and its comment is `W7:{sleeve}`. Between 2026-07-02T03:15:26Z and 2026-08-04T16:00:28Z
   the FTMO *book* placed nothing at all. §2.3.

4. **"Not running" and "no signal" are both ruled out with evidence**, and they are the two answers
   a reader would most likely have guessed. redacted_account logged 1829 cycles across every weekday of
   the window and generated 446 intents. §3.

5. **The 231 refusals were 2 opportunities.** USOIL_cash and UKOIL_cash, sleeve `energy_agri`, both
   on the single H4 decision bar `2026-08-04T09:00:00Z`, retried every ~60 s for 118 minutes.
   Amplification **115.5×**. The storm was stopped by a staleness guard, not by the retry
   classifier. §5.

6. **Every activation refusal reason classifies as transient — including `activation_token_expired`.**
   So the 2026-08-14T17:23Z expiry will reproduce this exact storm shape on **both** books
   simultaneously. Measured, not inferred. §5.3, §6.

7. **The monitor has the same blind spot as `status`, one level up.** On 2026-08-04 it ran 287 clean
   cycles with `alert_count: 0`, `down: []`, `hung: []`, `monitoring_degraded: false` while every
   redacted_account entry was being refused. Its health model has terms for *alive*, *ticking* and
   *P&L* — none for *able to place*. §7.

8. **There is no mint script in the repo**, so no latent code bug caused the 07-31 mis-mint; it was
   the hand-invocation. That makes a written, verified ceremony the actual mitigation. §6.

---

## 1. The window, decomposed

All timestamps UTC. Broker rows are from `history_deals_get` on the live terminals; cycle rows are
from `shadow_logs/ultimate_book_launcher.jsonl` (6309 records, 2026-06-18 → 2026-08-06).

| # | window | duration | why redacted_account placed nothing | class |
|---|---|---|---|---|
| 1 | 2026-07-02T05:39:52Z → 2026-07-30T05:15:18Z | 27d 23h 36m | `ultimate_book_apply_to_execution=false` — every intent diverted to shadow **before** order-send | **gated, by decision** |
| 2 | 2026-07-30T05:15:18Z → 2026-08-04T13:00:32Z | 5d 8h | armed, authorized, but the sleeve set was narrowed to 3–5 tags; 4 intents in 5 days | **genuinely no setups** |
| 3 | 2026-08-04T13:00:42Z → 14:59:08Z | 1h 58m | F1 — the token bound the profile name; 231 refusals | **refused** |

Cause 3 is the only one that is a defect. Causes 1 and 2 are the system doing what it was
configured to do.

The precise seam: redacted_account's **last book-placed entry** was `2026-07-02T03:15:04Z` (JP225,
`W7:asia_pdl_fade`), and its **last deal of any kind** was `2026-07-02T19:03:00Z` (SPX500 closed at
TP, from a 07-01 entry). The account has been flat from that moment to now — so the shadow switch
stranded no position.

---

## 2. Cause 1 — shadow/intelligence-only mode (the 27 days)

### 2.1 The change

Commit `441708da8` — *"fix: switch vps runtime to shadow intelligence mode"*, Codex GPT-5,
**2026-07-02T05:39:52Z**. It set, in `config/agent_config.yaml`:

```yaml
ultimate_book_enabled: true                       # GATE 1: master on/off — LIVE 2026-06-15 owner GO
ultimate_book_apply_to_execution: false           # SHADOW 2026-07-02: generate intent, do not execute
ultimate_book_live_activation_allowed: false      # SHADOW 2026-07-02: no live order authority
ultimate_book_live_broker_authority: false        # SHADOW 2026-07-02: no broker order/position/SLTP mutation
```

and the same three gates in `config/profiles/redacted_account.yaml`. Its own commit body describes the
intent: *"broker mutation/order placement/close/flatten/SLTP mutation from the ultimate-book path is
disabled."* This was a decision, recorded, with a route
(`research/operations/vps_runtime_shadow_intelligence_only_handoff_2026_07_02/`).

The last book entry on either account preceded it by 2h 24m. Nothing was placed after it.

### 2.2 What the runtime did with that gate

`src/components/ultimate_book/bridge.py:443-446`:

```python
if not apply_to_execution:
    return _decide(status="shadow_apply_to_execution_off",
                   reason="ultimate_book_apply_to_execution_false", effect_now=False,
                   shadow=shadow, realized=[])
```

It returns with `realized=[]` **before** anything reaches `RealMT5.order_send`. This is why the
activation gate is not a candidate explanation for this window: it was never consulted. "Signal
refused" is ruled out by construction, not by absence of evidence.

Per-cycle, from the launcher ledger:

| segment | book | cycles | intents | shadowed | placed | dominant reason |
|---|---|---|---|---|---|---|
| A pre-shadow 06-18→07-02 | ftmo | 1084 | 342 | 22 | **80** | `no_candidates_this_bar` |
| A pre-shadow 06-18→07-02 | fn | 1057 | 345 | 18 | **67** | `no_candidates_this_bar` |
| B shadow 07-03→07-29 | ftmo | 1838 | 452 | 308 | **0** | `shadow_apply_to_execution_off` (1833/1838) |
| B shadow 07-03→07-29 | fn | 1829 | 446 | 307 | **0** | `shadow_apply_to_execution_off` (**1829/1829**) |
| C armed+narrow 07-30→08-03 | ftmo | 47 | 0 | 0 | 0 | `no_candidates_this_bar` |
| C armed+narrow 07-30→08-03 | fn | 53 | 4 | 2 | 0 | `no_candidates_this_bar` |
| D token wall 08-04 | ftmo | 6 | 2 | 0 | **1** | `no_candidates_this_bar` |
| D token wall 08-04 | fn | 122 | **233** | 0 | **0** | `admitted_book_authority` (117/122) |

**1829 of 1829** redacted_account cycles in segment B carry `shadow_apply_to_execution_off`. Not a
majority — all of them.

### 2.3 FTMO was equally silent, and its July P&L was manual

Every FTMO deal between 2026-07-02 and 2026-08-03, read from the broker:

| time UTC | symbol | vol | entry | profit | magic | comment |
|---|---|---|---|---|---|---|
| 2026-07-02 03:15:26 | JP225.cash | 3.81 | IN | — | `20260401` | `W7:asia_pdl_fade` |
| 2026-07-02 10:12:57 | US500.cash | 1.95 | OUT | +75.08 | `20260401` | `[tp 7466.28]` |
| 2026-07-02 18:15:01 | XAUUSD | **1.00** | IN | — | **`0`** | **`''`** |
| 2026-07-02 19:28:24 | XAUUSD | **1.00** | IN | — | **`0`** | **`''`** |
| 2026-07-03 04:24:17 | XAUUSD | 1.00 | OUT | **+6,171.00** | **`0`** | `[tp 4188.45]` |
| 2026-07-03 04:24:32 | XAUUSD | 1.00 | OUT | **+7,167.00** | **`0`** | `[tp 4189.83]` |
| 2026-07-29 03:47:23 | XAUUSD | **0.01** | IN | — | **`0`** | **`''`** |
| 2026-07-29 04:02:54 | XAUUSD | 0.01 | OUT | −7.22 | **`0`** | `[sl 4015.40]` |
| 2026-08-04 16:00:28 | UKOIL.cash | 1.91 | IN | — | `20260401` | `W7:energy_agri` |

The book stamps `magic=20260401` and `comment=W7:{sleeve}` on every entry it places. The four
`magic 0` / empty-comment rows are not book trades. So the FTMO book's silence runs
**2026-07-02T03:15:26Z → 2026-08-04T16:00:28Z** — 33 days — and the +13,338 that lands inside it is
owner activity, not system performance.

---

## 3. Ruling out the alternatives, each with its own evidence

| hypothesis | verdict | evidence |
|---|---|---|
| **not running** | **ruled out** | 1829 FN cycles in segment B, ~84–96/weekday, tracking FTMO's count within ~3%. The only July days with no FN cycles are **2026-07-11, 07-18, 07-25 — all Saturdays**. |
| **not generating** | **ruled out** | 446 FN intents and 307 shadow rows in segment B. The book was finding setups the whole time. |
| **not authorized** | **ruled out for this window** | `bridge.py:443` returns `realized=[]` before order-send, so the activation gate is unreachable. It becomes the cause only on 2026-08-04 (§4). |
| **gated** | **CONFIRMED for 07-02→07-30** | `shadow_apply_to_execution_off` on 1829/1829 cycles, from commit `441708da8`. |
| **genuinely no setups** | **CONFIRMED for 07-30→08-04** | 53 cycles, 4 intents, `no_candidates_this_bar` dominant, after the sleeve set narrowed to 3–5 tags. |

---

## 4. Cause 2 and Cause 3 — arming, and where F1 actually came from

**Armed 2026-07-30T05:15:18Z.** Commit `eb7c28516` flipped redacted_account's three profile gates to
`true`. The ledger shows the exact tick: `runtime_effect_now` goes `False → True` and the tag count
drops from 19/10/32 to **3** — the `--tags crypto,energy_agri,sub_xvol_pullback` narrowing landed in
the same ceremony. FTMO had done the same at 2026-07-29T12:55:33Z.

That narrowing is the whole of cause 2: a book restricted to 3–5 sleeves produced 4 intents in five
days, against 446 in the preceding 27 on the broad set. Nothing was broken; there was nothing to
take.

**Where the bad token came from.** The 07-30 arming commit records a *correct* mint
(`namespace redacted_account_live_bee34003`, expiring 2026-08-06). The defect was introduced the next day.
FTMO's token — untouched by Session LO — still carries the issuance metadata:

```json
"issued_utc": "2026-07-31T17:23:49.842976+00:00",
"issued_by":  "borhen",
"note":       "all-in re-mint 2026-08-01, owner directive, executed by Fable orchestrator; flat-verified 0/0"
```

The pre-repair redacted_account token was issued `2026-07-31T17:23:50.704453Z` — **0.86 s later, in the
same ceremony**, for the same 14-day window. FTMO's got `--namespace operator_profile`;
redacted_account's got `--namespace redacted_account`.

The trap is structural: **redacted_account is the only account where profile ≠ namespace.** For FTMO the
two strings are identical, so a ceremony that reads one value and uses it for both arguments is
correct on FTMO and silently wrong on redacted_account. `mint` does not default `--namespace` to the
profile (it warns loudly when the namespace is *omitted*, `gtos_activation_token.py:151-162`) — so
the wrong value was passed explicitly, not defaulted.

It then sat latent for four days, because segment 2 produced no intents to refuse. The first bar
that fired was 2026-08-04T09:00:00Z.

---

## 5. Decide-support A — the retry classification, measured

### 5.1 What 231 actually is

Every launcher record in the burst carries the same two skipped rows:

```json
{"symbol": "USOIL_cash", "sleeve": "energy_agri", "decision_bar_iso": "2026-08-04T09:00:00+00:00", "reason": "order_rejected:timeout_no_fill"}
{"symbol": "UKOIL_cash", "sleeve": "energy_agri", "decision_bar_iso": "2026-08-04T09:00:00+00:00", "reason": "order_rejected:timeout_no_fill"}
```

and `advanced_tf: [16388]` (H4) on **all 122** of the day's cycles — the same bar, re-presented on
every 60-second tick, because it is never consumed.

| measure | value |
|---|---|
| genuine refused opportunities | **2** (USOIL_cash, UKOIL_cash) |
| distinct decision bars | **1** (`2026-08-04T09:00:00Z`) |
| total refusals logged | **231** |
| duplicate retries | **229** |
| amplification per genuine opportunity | **115.5×** |
| ticks in the burst | 117, over 118 m 26 s (13:00:42 → 14:59:08) |
| owner notifications sent | **2**, not 231 — deduped on `(sleeve, symbol, bar, reason)` at `book_owner.py:2000-2005` |
| broker order_send calls | **0** — the gate refuses before `self._mt5.order_send` |
| what stopped it | `stale_late_entry_after_restart` at 15:00:08 — **a staleness guard, not the retry classifier** |

### 5.2 The mechanism

`book_owner.py:1995-1997`:

```python
if _is_transient_place_failure(result.get("reason")):
    attempted_transient_broker_symbol_keys.update(target_broker_keys)
    summary["bar_consumable"] = False
```

`order_rejected:` is a transient prefix (`book_owner.py:52`) and no
`_TERMINAL_BROKER_REJECT_MARKERS` substring appears in an activation reason, so the bar stays
unconsumed and the next tick re-runs it. The design intent is explicit at `book_owner.py:43-49`: a
once-per-bar signal must not be lost to a momentary broker hiccup.

### 5.3 Every activation reason is transient — including expiry

Run against the live classifier:

```text
order_rejected:activation_token_signature_invalid              True
order_rejected:activation_token_expired                        True
order_rejected:activation_token_not_yet_valid                  True
order_rejected:activation_token_namespace_unsatisfied          True
order_rejected:activation_token_namespace_mismatch             True
order_rejected:activation_token_config_digest_unsatisfied      True
order_rejected:activation_token_config_digest_mismatch         True
order_rejected:timeout_no_fill                                 True
-- controls --
order_rejected:no money / invalid stops / market closed        False
```

LO's relabelling does not change this, by design and by test
(`test_retry_classification_is_unchanged`). It renames the log line; it does not move the bar.

### 5.4 Both sides, so Borhen can decide

**If it stays TRANSIENT (today's behaviour)**

- Cost, measured: 229 wasted intent-build/sizing cycles and 229 log lines per stuck bar. No broker
  load, no notification spam, no double-place risk (the placed-leg ledger guards it), and the
  staleness guard bounds each storm at ~2 h.
- Benefit, and it is real: if a token lapses and is re-minted **within the staleness window**, the
  bar is still unconsumed and the trade goes on automatically. Nothing is lost.

**If it becomes TERMINAL-for-the-bar**

- On 2026-08-04 it would have changed **nothing** about the trading outcome: 0 fills either way, the
  token was broken. It would have turned 231 log lines into 2.
- It permanently loses any bar that was refused, even if a human fixes the token 90 seconds later.

**The concrete case that decides it is 2026-08-14.** §5.3 shows `activation_token_expired` is
transient, so at expiry both books will enter this storm simultaneously and stay there until each
bar goes stale. Under TRANSIENT, a re-mint inside ~2 h recovers the pending bars by itself. Under
TERMINAL, those bars are gone. **On the measured evidence the transient classification costs log
volume and buys automatic recovery — I would leave it alone and fix the visibility instead (§7).
That is a recommendation, not a change: it alters bar consumption, so it is Borhen's call and I have
not touched it.**

---

## 6. Decide-support B — the re-mint procedure (prepared, NOT executed)

**Deadline: `2026-08-14T17:23:49.842976Z` (FTMO) and `2026-08-14T17:23:51.500112Z` (redacted_account) — a
dual-account deadline, 8 days 8 h from this session.** At lapse both books stop placing (closes and
risk-reducing requests never need a token, so nothing can be stranded) and both enter the §5 retry
storm.

### What it needs before anything is minted

1. **Both accounts flat.** Not strictly required by the gate, but the ceremony should not run
   alongside open exposure — verify `positions=0 / pending_orders=0` on both.
2. **The running books' config digest must equal the freshly computed one.** `mint` computes the
   digest from `config/agent_config.yaml` + the profile *on disk now*; the running worker declared
   its digest at **startup**. If a config byte moved since the book started, the new token binds a
   digest the running process does not declare and every entry is refused with
   `activation_token_config_digest_mismatch` — F1's shape with a different field. Confirm against
   the book's own startup line, not against the file:
   ```text
   run_book_console.log     activation context declared (namespace=operator_profile,    config_digest=ffe16657feaf, ...)
   run_book_fn_console.log  activation context declared (namespace=redacted_account_live_bee34003, config_digest=e184a81d3b1b, ...)
   ```
3. **`--namespace` must be the `run_book.py --namespace` value, never the profile.** This is the one
   that cost a month. Read it off the live command line:
   ```powershell
   Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
     Where-Object { $_.CommandLine -like '*run_book.py*' } |
     ForEach-Object { $_.CommandLine }
   ```
   | book | `--profile` | `--namespace` |
   |---|---|---|
   | FTMO | `operator_profile` | `operator_profile` (identical — this is what hides the bug) |
   | redacted_account | `redacted_account` | **`redacted_account_live_bee34003`** (**differs** — this is the whole trap) |
4. **`--force`.** A token already exists per account. `write_token` is write-then-rename
   (`os.replace`), so there is no window without a token — do **not** `revoke` then `mint`.
5. **The signing key must not rotate.** `ensure_signing_key` returns the existing key when present;
   a rotation would silently invalidate the *other* account's signature. Fence
   `~/.gtos/activation/signing.key` sha256 = `9005a92d28022194…` before and after.

### The commands

```bash
# FTMO
python scripts/gtos_activation_token.py mint \
    --profile operator_profile --namespace operator_profile \
    --expires-in-hours <N> --issued-by borhen --force \
    --note "<why, one line>"

# redacted_account — NOTE the namespace differs from the profile
python scripts/gtos_activation_token.py mint \
    --profile redacted_account --namespace redacted_account_live_bee34003 \
    --expires-in-hours <N> --issued-by borhen --force \
    --note "<why, one line>"
```

Do not pass `--no-bind-config`. Do not omit `--namespace` (a namespace-less token authorizes *any*
process on that account).

### Verification — and it must not be `status`

```bash
python scripts/verify_activation_authorization.py --book ftmo   # must print PASS, exit 0
python scripts/verify_activation_authorization.py --book fn     # must print PASS, exit 0
```

`gtos_activation_token.py status` verifies each token against **its own** declared namespace
(`activation_token.py:1008-1015`), so it reported the broken token as `valid: true` for four days.
It is structurally incapable of catching a mis-bound namespace. **A ceremony that ends with `status`
is not verified.** Both verifiers pass on the current tokens as of this session (§8).

No restart is needed after a re-mint: `authorize_broker_mutation` re-reads the token from disk on
every decision (`activation_token.py:850` → `read_token` → `path.read_text()`).

---

## 7. The blind-spot pattern, one level up from `status`

LO found that `status` validates a token against **its own declaration** rather than against what
the consumer declares. The same shape exists in the monitor, and it is why nobody noticed on 08-04.

`.tools/monitor_books.py::alerts()` raises on exactly five conditions: daily P&L ≤ −4.5% / ≤ −2.5%,
gross open risk ≥ 3.5%, max-DD headroom ≤ 1% of initial balance, **BOOK DOWN** (no process), and
**BOOK HUNG** (process alive, heartbeat stale). There is no term for *placement failing*.

The consequence, from the record: on 2026-08-04 the monitor ran **287 cycles** and its heartbeat
read `alert_count: 0, down: [], hung: [], blind: [], monitoring_degraded: false` throughout the
two hours in which every redacted_account entry was refused. The book was alive, ticking, healthy, gates
ON — and unable to place. Every question the monitor asks returned "fine", because it never asks the
one that mattered.

To the monitor's credit its *process* checks are consumer-side and well built: `live_namespaces()`
parses the real `--namespace` off the live command line rather than trusting a heartbeat, and
`book_hung` requires the heartbeat's own pid to still be alive. The gap is in the health *model*,
not the plumbing.

**The generalisable rule, now paid for twice:** a check must validate against what the *consumer*
declares or does, never against what the artifact declares about itself. `status` asked the token
about the token. The monitor asks the book whether it is running, not whether it can trade.

Cheap closures, both out of scope here and recorded rather than done:
- run `verify_activation_authorization.py --book {ftmo,fn}` from the watchdog or the supervisor's
  start path — it already exits non-zero correctly, nothing runs it;
- alert on consecutive `order_rejected:` skips for the same decision bar — that single signal would
  have fired within minutes on 08-04, and would fire on 08-14.

---

## 8. The labelling fix: landed and verified

Both accounts flat throughout. The books were running code loaded at 01:10:40/01:10:44, which
predates LO's `execution.py` edit (mtime 01:32:23) — so the fix was on disk but not live.

### Sequence

| time UTC | action |
|---|---|
| 08:37:01 | pre-state fence captured; both accounts **0 positions / 0 pending orders**; all four gates `True`; both verifiers PASS |
| 08:37:56 | kill flags placed on both books |
| 08:37:58 / 08:38:44 | `PLACEMENT PAUSED` acknowledged — FN **+2.0 s**, FTMO **+48.6 s** (both inside one 60 s poll) |
| 08:38:55 | force-kill of all four book processes (9848, 2084, 3152, 10964) — the kill flag is a placement brake, never a stop, so this is the only mechanism |
| 08:39:18 / 08:39:22 | supervisor restarted both books — FTMO 5412→10196, FN 1172→3956 (**~25 s**) |
| 08:39:22 / 08:39:24 | both declared the correct activation context; `authority_gates_ON=True halted=False killed=True` |
| 08:40:20 | kill flags released after startup verification |
| 08:40:29 / 08:40:30 | `placement RESUMED` on both, +9.5 s / +10.2 s |

Books were actually down for **27 seconds**; placement was braked for 2 m 34 s.

### Proof the restarted processes run the fixed bytes

Process creation (08:39:18 / 08:39:22) postdates the source mtime (01:32:23), and the bytecode cache
validates against the fixed source exactly:

```text
source mtime : 2026-08-06T01:32:23+00:00, size 473833
execution.cpython-313.pyc  embedded source mtime 2026-08-06T01:32:23+00:00  size 473833  -> MATCH
'_last_order_send_refusal' occurrences in execution.py: 4
```

Python's import check is `(mtime, size)`; both match, so the loaded module is the fixed module.

### The fence — every value identical across the restart

| item | pre 08:37:01 | post 08:40:41 |
|---|---|---|
| `src/components/execution.py` sha | `38629ce934917a4f` | `38629ce934917a4f` |
| `book_owner.py` sha | `69efc33e27e23eee` | `69efc33e27e23eee` |
| `agent_config.yaml` sha | `a2d5c67575d7087f` | `a2d5c67575d7087f` |
| `redacted_account.yaml` / `ftmo…yaml` sha | `cf82c49a08a1f88c` / `ae9312e6c5c8e6b0` | unchanged |
| FTMO token sha / ns | `1972f42bacda53b0` / `operator_profile` | unchanged |
| FN token sha / ns | `346a316868219017` / `redacted_account_live_bee34003` | unchanged |
| `signing.key` sha | `9005a92d28022194` | `9005a92d28022194` |
| config digests | `ffe16657feaf` / `e184a81d3b1b` | unchanged |
| four authority gates, both books | all `True` | all `True` |
| kill / halt flags | all absent | all absent |
| FTMO equity / positions / orders | 108,365.48 / 0 / 0 | 108,365.48 / 0 / 0 |
| FN equity / positions / orders | 96,229.28 / 0 / 0 | 96,229.28 / 0 / 0 |
| command lines | — | **byte-identical** (namespace, profile, tags, kill-flag, spread-geometry-floor, poll-seconds) |

### Post-restart health

```text
verify_activation_authorization --book fn    RESULT: PASS  exit 0
verify_activation_authorization --book ftmo  RESULT: PASS  exit 0
book heartbeat ftmo  pid 10196 healthy=true   08:43:30Z
book heartbeat fn    pid  3956 healthy=true   08:43:31Z
monitor_books        cycle 90  down=[] hung=[] blind=[] monitoring_degraded=false  alert_count=0
supervisor heartbeat pid 2704  08:40:29Z
run_book*.log.err    zero error lines after 08:30
```

Tests at HEAD before the restart: `TestActivationRefusalIsNotReportedAsATimeout` — **5 passed**.

### End-to-end: the first real bar after the restart

The restart landed between H4 bars, so the checks above are startup-state. The 09:00Z bar is the
first full decision cycle the restarted processes ran, and both completed it live and unbraked:

```text
2026-08-06T09:00:36  redacted_account_live_bee34003  reason=no_candidates_this_bar
                     place=True killed=False halted=False effect_now=True tags=4 n_intents=0 placed=0
2026-08-06T09:00:37  operator_profile     reason=no_candidates_this_bar
                     place=True killed=False halted=False effect_now=True tags=4 n_intents=0 placed=0
```

`place=True` with `effect_now=True` is the state that was impossible for redacted_account for the whole of
July. The one thing still not proven is a live `unit_placed` from redacted_account — that needs a signal
to fire and cannot be manufactured. **Named as pending, not claimed**, exactly as LO left it.

---

## 9. What I got wrong

1. **I nearly reported the git-log gap as the answer.** There are no commits between
   2026-07-02T07:35Z and 2026-07-29T02:36Z — an exact match for the silence window, and a very
   inviting "nobody was working on it". It is a *coincidence of the same cause*: the estate was in
   shadow mode, so nobody was shipping. Commits are not runtime state, and commit `118071eaa` says
   so explicitly — *"everything in this commit was already LIVE on this host before it was
   committed"* — the host had diverged from its own branch for a month. Had I stopped at the git
   log I would have reported an absence of *work* as an absence of *running*, and they are not the
   same claim.

2. **I briefly doubted the launcher ledger instead of the broker row.** FTMO shows a XAUUSD entry on
   2026-07-29 while the ledger says `placed: 0` that day, and my first instinct was that the ledger
   was lossy. The ledger was right: `magic 0`, empty comment — not a book trade. The correct
   discipline is to reconcile a broker row to the book by `magic` + `W7:{sleeve}` comment *before*
   treating it as system activity. The same error at the next row up would have booked the
   +13,338 manual XAUUSD win as system performance, which is a much more expensive mistake than the
   one I nearly made.

3. **I assumed 231 refusals meant 231 opportunities.** That is the natural reading of the brief and
   it is wrong by a factor of 115. Anchoring on the raw count would have overstated both the missed
   opportunity and the case for changing the retry classifier — I would have argued for a trading
   behaviour change on a number that was 99.1% duplicates.

4. **My first state-fence script died on `from src.utils.config import load_config`** — a function
   that does not exist in this repo. I wrote the checker from an assumed API instead of reading the
   module first. Trivial to fix, but it is the same class as LO's §9.5: the failure mode of a
   checker built on assumption is that it returns *nothing* and nothing looks like clean.

5. **What I could not establish.** I cannot prove *how* the wrong namespace reached the 07-31 mint —
   there is no mint script in the repo (grep: only the verifier, the supervisor and
   `activation_token.py` reference it), and the ceremony ran over host-admin with no captured command
   line. I can prove the ceremony existed, when, that it minted both tokens 0.86 s apart, and that
   `mint` does not default the namespace — so the value was passed explicitly. Whether it was
   hand-typed or substituted from a variable is not recoverable from this host. That is why §6 is
   written as a procedure with a mandatory verifier rather than a code fix: there is no code to fix.

6. **Not quantified.** Segment 2's 4 intents in 5 days is consistent with narrowing 10–32 tags to
   3–5, but I did not test whether the narrow sleeve set is firing at its designed rate. If it is
   under-firing, redacted_account has a *fourth* reason for quietness that this session did not
   measure — and it would look exactly like "no setups". Flagged, not claimed.

---

## 10. What Borhen must decide

1. **The retry classification (§5).** Measured both ways. My read: transient costs log volume and
   buys automatic recovery after a re-mint, and the 08-14 expiry is precisely the case where
   recovery is worth having. Recommend leaving it and closing the *visibility* gap instead. Your
   call — it changes bar consumption.
2. **Both tokens expire 2026-08-14T17:23Z (§6).** Dual-account. Procedure is written and its
   prerequisites are stated; nothing was minted. Needs a date, a lifetime (`--expires-in-hours`),
   and someone to run it — ending with the **verifier**, not `status`.
3. **Nothing runs the verifier (§7).** `verify_activation_authorization.py` exists and exits
   non-zero correctly; no scheduled path invokes it. One line in the watchdog or the supervisor
   start path turns a four-day outage into a four-minute one.
4. **The monitor cannot see an unplaceable book (§7).** An alert on repeated `order_rejected:` for
   the same decision bar would have fired on 08-04 within minutes, and will fire on 08-14.
5. **Was July's shadow mode meant to last four weeks?** Commit `441708da8` switched both books to
   intelligence-only on 2026-07-02 and nothing switched them back until the 07-29/07-30 arming
   ceremonies. If that was the plan, the estate behaved correctly. If it was meant to be a short
   diagnostic pause, then 27 days of two funded accounts not trading is the finding, and it is a
   process gap, not a code one. **Only you can answer this one.**
6. **The pre-existing `test_book_owner` failure** carried by LO's §8 (CN runtime-learning packet
   guard) is still open. Untouched here.

---

## 11. Changed bytes

| path | change |
|---|---|
| `docs/…/phase19/SESSION_LQ_FN_SILENCE.md` | this document |

No source, config, launcher, profile or token byte was changed by this session. The only runtime
action was the restart in §8, which loaded already-committed bytes (HEAD `c989b1198`) and left every
fenced value identical.

## 12. Session log

```text
2026-08-06T08:27Z  preflight: generate_live_state.py, LIVE_STATE, CLAUDE.md, LO report
2026-08-06T08:30Z  launcher ledger parsed (6309 records); per-day/per-namespace activity map
2026-08-06T08:31Z  cause 1 identified: 441708da8 shadow mode; bridge.py:443 confirmed
2026-08-06T08:33Z  broker ground truth, both accounts, 2026-06-01..08-07 (read-only, order_send disabled)
2026-08-06T08:34Z  FTMO July P&L identified as magic-0 manual trades, not book trades
2026-08-06T08:35Z  231 refusals resolved to 2 opportunities on one H4 bar; staleness bound found
2026-08-06T08:36Z  all 7 activation reasons classified transient, incl. activation_token_expired
2026-08-06T08:37Z  pre-restart fence; both flat; verifier PASS
2026-08-06T08:37:56Z  kill flags placed; PLACEMENT PAUSED acknowledged both books
2026-08-06T08:38:55Z  force-kill; 08:39:22 supervisor restarted both; startup verified
2026-08-06T08:40:20Z  flags released; placement RESUMED both books
2026-08-06T08:40:41Z  post-restart fence: every value identical; both verifiers PASS
2026-08-06T08:42Z  07-31 mint ceremony reconstructed from FTMO token metadata
2026-08-06T08:43Z  monitor cycle 90 clean on the new PIDs; monitor blind spot confirmed
```
