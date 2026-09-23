# Session LO — F1 repaired: redacted_account can place again

Session LO · phase19 · host `C:\Users\MSI\Documents\ai-trading-agent` · branch
`vps/ultimate-conditioned-expansion-minimal-2026-06-18` · host HEAD at start
`f43e5cd2b364d650bbe728bca49d2594fa4b064d` (Session LN).

**Result: F1 is repaired and empirically proven. redacted_account now authorizes exposure-increasing
requests.** LN's diagnosis was confirmed independently before anything was minted. The redacted_account
token was re-minted bound to the namespace the worker actually declares; FTMO's token is
byte-identical; no config byte moved; **no book restart was required**, and none was performed.

The `timeout_no_fill` masking that hid this for days is repaired with five regression tests, proven
sensitive by running them against the unfixed code. LN's unexplained kill-flag behaviour is now
explained with direct evidence — and it is not a defect.

Window: pre-state 2026-08-06T01:23Z · mint 2026-08-06T01:28:37Z · proofs to 01:41Z. Both accounts
flat throughout; both books ran continuously and were never stopped.

---

## 0. Findings first

1. **LN's diagnosis is correct, and I confirmed it from the running system, not from LN's document.**
   The redacted_account worker's live command line declares `--namespace redacted_account_live_bee34003
   --profile redacted_account`; the token bound `namespace: "redacted_account"`. `verify` against the *real*
   runtime namespace returned `activation_token_namespace_mismatch`. §1.

2. **`gtos_activation_token.py status` cannot detect this class of defect, and reported the broken
   token as `valid: true` throughout.** `describe_activation_state` verifies each token against
   `token.get("namespace")` — *its own* declared namespace (`activation_token.py:1008-1015`). It
   never learns what the worker declares, so a token bound to the wrong namespace self-certifies.
   This is why the defect survived a mint ceremony *and* every subsequent status check. Repaired
   with a new verifier, §6.

3. **The repair needed no restart, and I did not perform one.** `authorize_broker_mutation` re-reads
   the token from disk on every decision (`activation_token.py:850` → `read_token` →
   `path.read_text()`); there is no cache. The process-side context was already correct — the
   redacted_account book logged `namespace=redacted_account_live_bee34003, config_digest=e184a81d3b1b` at its
   01:10:47 start. Correct process context plus a now-valid token on disk is authorization, with no
   new process needed. Book PIDs are unchanged across the whole session (§3).

4. **The books run as `trader`, which is the renamed built-in Administrator (RID -500).** Its profile
   is `host-local`, so `~/.gtos/activation` resolves to the same directory my shell
   writes to. I checked this before minting rather than assuming it — minting into the wrong
   directory would have produced a confident report and zero repair. Both books' own log lines
   confirm `token_dir=host-local\.gtos\activation`. §1.

5. **The kill flags were never going to stop the books, and they worked exactly as designed.**
   `BookLauncher.run_forever` (`launcher.py:298-307`) has *no* kill check — the flag only sets
   `place = False` inside `tick()`. It is a **placement brake**, not a process stop. Both books
   acknowledged LN's flags within 19–24 seconds, not 150. Both of LN's hypotheses were wrong. §7.

6. **One pre-existing test failure at HEAD, unrelated to this work**, in Session LN's carried
   runtime-learning packet guard. Verified pre-existing by re-running it against reverted bytes. §8.

---

## 1. The diagnosis, confirmed independently

Three facts, each read from the running system.

**(a) What the worker declares** — live command line, `Get-CimInstance Win32_Process`, pid 2084/10964:

```text
run_book.py --terminal-path C:\MT5\redacted_account\terminal64.exe
  --namespace redacted_account_live_bee34003        <-- the NAMESPACE
  --profile   redacted_account                      <-- the PROFILE
  --kill-flag pipeline_state/ULTIMATE_BOOK_KILL_fn.flag ...
```

`run_book.py:307-308` passes the **namespace** into the activation context and the **profile** into
the config digest:

```python
_cfg_digest = config_digest_for(args.config, args.profile)
mt5.set_activation_context(namespace=args.namespace, config_digest_sha256=_cfg_digest)
```

**(b) What the token bound** — `bee34003….token.json`, minted 2026-07-31T17:23:50Z:
`"namespace": "redacted_account"`. The profile name, where the namespace was required.

**(c) What the gate does with that** — `verify` against the *real* runtime namespace:

```text
--- FTMO       ns operator_profile   -> valid=true   activation_token_valid
--- redacted_account ns redacted_account_live_bee34003 -> valid=false  activation_token_namespace_mismatch
                                              detail: redacted_account_live_bee34003 != redacted_account
```

The config digest matched on both accounts (`e184a81d3b1b` on FN, logged by the book itself and
recomputed by the tool). **The namespace field was the only defect.**

**Which token directory the books actually read.** The books run as `redacted_host\trader`; my shell
runs as Administrator. That is only safe to ignore once proven:

```text
SID of 'trader'      : S-1-5-21-…-500      <-- RID 500 = renamed built-in Administrator
Win32_UserProfile    : S-1-5-21-…-500 -> host-local
GTOS_ACTIVATION_TOKEN_DIR (Machine/User/process) : unset
.gtos\activation directories on this box          : exactly one
```

and both books state it themselves:

```text
run_book_fn_console.log   01:10:47  activation context declared (namespace=redacted_account_live_bee34003,
                                    config_digest=e184a81d3b1b, token_dir=host-local\.gtos\activation)
run_book_console.log      01:10:46  activation context declared (namespace=operator_profile,
                                    config_digest=ffe16657feaf, token_dir=host-local\.gtos\activation)
```

**Live impact, re-counted from the raw bytes** (NUL-stripped first — the file is mixed
ASCII/UTF-16LE, LN's lesson 1): **231** refusals in `run_book_fn_console.log.err`, first
`2026-08-04 13:00:42`, last `2026-08-04 14:59:08`, and the file has not been appended to since —
redacted_account has attempted no entry since. The masking, verbatim from the tail:

```text
2026-08-04 14:59:08,179 ERROR Order send exception: broker mutation refused:
  activation_token_namespace_mismatch [exposure_increasing_new_deal] (redacted_account_live_bee34003 != redacted_account)
2026-08-04 14:59:08,181 ERROR Order failed: timeout_no_fill
```

FTMO's `.err`: **zero** such refusals.

---

## 2. Pre-state

| item | value at 2026-08-06T01:23–01:28Z |
|---|---|
| FTMO token sha256 | `1972F42BACDA53B0590A6BD0D2DD050AC7E9A4E7467CEC9F5A8C2D0EF6E84452` (690 B) |
| redacted_account token sha256 | `D032810C391639199118593A9CD0E5049624E51AC491CB8800579D843C252451` (679 B) |
| `signing.key` sha256 | `9005A92D28022194BC5023E7ED80F3FE114954E32D0C423B9EFE8FDF58F37C9D` |
| `config/agent_config.yaml` | `a2d5c67575d7087fc4f2da443750aecb99e35437cee86edbe1d7c9bbcbf66c2c` |
| `config/profiles/redacted_account.yaml` | `cf82c49a08a1f88c9ea4181076e9ac2f0d580f1c6e4b7ce1b8aeeba18d99d632` |
| `config/profiles/operator_profile.yaml` | `ae9312e6c5c8e6b05f8e5eb5f9490166c44a1a3279b4eff5df10c3da2921e2b8` |
| FTMO runtime config digest | `ffe16657feaf` |
| redacted_account runtime config digest | `e184a81d3b1b` |
| FTMO equity / positions | $108,365.48 / **0** |
| redacted_account equity / positions | $96,229.28 / **0** |
| both terminals | `connected=True trade_allowed=True` |
| book PIDs | FTMO 3152→9848, FN 10964→2084 (created 01:10:40 / 01:10:44) |
| `monitor_books` heartbeat | cycle 3, `down=[] hung=[] blind=[]`, `monitoring_degraded=false` |
| kill flags | both **absent** (clear) |
| supervisor task | Running |

The three config digests match LN's §1 fence values exactly.

---

## 3. The mint — the exact command

Run at **2026-08-06T01:28:37Z**:

```bash
python scripts/gtos_activation_token.py mint \
    --profile redacted_account \
    --namespace redacted_account_live_bee34003 \
    --expires-in-hours 207.920517424972 \
    --issued-by borhen \
    --note "Session LO F1 repair: bind to the namespace run_book.py declares (redacted_account_live_bee34003); prior token bound the profile name and refused every entry" \
    --force
```

Output:

```json
{
  "account_login_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
  "binds_config_digest": true,
  "config_digest_sha256": "e184a81d3b1be81aceabe8e11784a4864c5e1fc299e7cd4e9c029e0a868c4f3b",
  "expires_utc": "2026-08-14T17:23:51.500112+00:00",
  "namespace": "redacted_account_live_bee34003",
  "written": "C:\\Users\\Administrator\\.gtos\\activation\\0000000000000000000000000000000000000000000000000000000000000000.token.json"
}
```

**On each argument:**

- `--expires-in-hours` is required by the tool, so the target expiry was expressed as a delta. It was
  computed to land on the **existing redacted_account token's own expiry**, `2026-08-14T17:23:50.704453Z`,
  so that the re-mint changes exactly one field. The mint landed 0.80 s later
  (`…17:23:51.500112Z`) — the elapsed time between computing the delta and `build_token` sampling its
  own `now`. That is drift, not a decision; both are within a second of FTMO's `…17:23:49.842976Z`.
- `--force` is required because a token already exists for this account. `write_token` is
  write-then-rename (`os.replace`), so there is no window in which the account has no token — which
  `revoke` then `mint` would have created.
- The config digest was **not** passed; it is computed by the tool from `config/agent_config.yaml` +
  `config/profiles/redacted_account.yaml`. Its output `e184a81d3b1b…` equals the digest the running book
  logged at 01:10:47, so the tool and the runtime agree by measurement, not by assumption.
- `--issued-by borhen`: the owner authorized this repair; the note records that Session LO executed it.

**No config byte moved.** All three config digests in §2 are unchanged post-mint.

---

## 4. Empirical proof of authorization

Not inspection. This drives a **real `RealMT5`** connected to the live redacted_account terminal, declares
the activation context exactly as `run_book.py:307-308`, and calls the choke point's own check
(`mt5_real.py:490-496`) with its exact argument tuple — stopping immediately before
`self._mt5.order_send`. `MetaTrader5.order_send` is replaced with a function that raises, so the
process is structurally incapable of placing. `order_check` is broker-side validation and places
nothing.

```text
book               : fn
token_dir          : host-local\.gtos\activation
declared namespace : redacted_account_live_bee34003
declared cfg digest: e184a81d3b1b
account digest     : 0000000000000000000000000000000000000000000000000000000000000000

=== the engine's own authorization path ===
  [live runtime namespace] ALLOWED  reason=activation_token_valid classification=exposure_increasing_new_deal

  -- negative controls: the gate must still discriminate --
  [wrong namespace]        REFUSED  activation_token_namespace_mismatch (redacted_account_not_the_namespace != redacted_account_live_bee34003)
  [namespace not declared] REFUSED  activation_token_namespace_unsatisfied (redacted_account_live_bee34003)

=== broker-side validation (order_check — places NOTHING) ===
  retcode=0 comment='Done'

RESULT: PASS   (exit 0)
```

Three things this establishes that a `status` check cannot:

- the classification is `exposure_increasing_new_deal` — **the exact classification of all 231
  refusals**, not some easier-to-authorize request;
- the gate still refuses a wrong or undeclared namespace, so the repair rebound the token rather
  than opening the gate. Note the refusal string is now the mirror image of the live incident's
  (`… != redacted_account_live_bee34003` instead of `redacted_account_live_bee34003 != …`);
- the broker itself would accept the order (`retcode=0 'Done'`), so nothing downstream of the gate
  blocks a redacted_account entry either.

**On the running process.** The proof ran in a separate process. What it establishes for pid 2084 is
that the token on disk is valid for `redacted_account_live_bee34003` and that `read_token` is a fresh disk
read per decision (§0.3); the running book's half — that it declares that exact namespace and config
digest — is established by its own 01:10:47 log line. Those two facts compose to authorization. The
remaining unproven step is a live `unit_placed` from redacted_account, which requires a signal to fire and
is not something I can or should manufacture. **Named as pending, not claimed.**

---

## 5. FTMO untouched

| check | pre | post | result |
|---|---|---|---|
| FTMO token sha256 | `1972F42BACDA53B0…` | `1972F42BACDA53B0…` | **byte-identical** |
| `signing.key` sha256 | `9005A92D28022194…` | `9005A92D28022194…` | **byte-identical** |
| FTMO token namespace / expiry | `operator_profile` / 2026-08-14T17:23:49Z | unchanged | unchanged |
| FTMO `verify` vs runtime ns | `activation_token_valid` | `activation_token_valid` | unchanged |
| FTMO config digest | `ffe16657feaf` | `ffe16657feaf` | unchanged |

The signing key matters as much as the token file: `write_token` calls `ensure_signing_key`, which
returns the **existing** key when present and only generates one when absent. A rotated key would
have silently invalidated FTMO's signature. It did not rotate.

The full verifier was also run against FTMO end-to-end: `RESULT: PASS`, exit 0, same negative
controls refusing. FTMO's *behaviour* is unchanged, not merely its bytes.

---

## 6. The `timeout_no_fill` repair

**The defect.** Three lines, in two functions:

1. `RealMT5.order_send` raises `ActivationTokenError` when the gate refuses (`mt5_real.py:490`).
2. `safe_place_order`'s blanket `except Exception` swallows it and returns `None`
   (`execution.py:6646-6654`, pre-change numbering).
3. `open_trade` labelled **every** `None` `timeout_no_fill` (`execution.py:3785`).

So "the broker did not answer in time" and "the order was never sent, because it was refused" became
the same string. 231 refusals read as broker latency.

**The change**, in `src/components/execution.py`:

```python
# 1. record WHY safe_place_order returned None, when the cause was authorization
except ActivationTokenError as e:
    self._last_order_send_refusal = (
        getattr(getattr(e, "decision", None), "reason", None) or "activation_refused"
    )
    logger.error(f"Order send exception: {e}")          # identical to the generic handler
    self._clear_checkpoint()                            # identical
    _record_order_send_diagnostic(result=None, status="order_send_exception", error=str(e))
    return None                                         # identical

# 2. cleared per call, at the top of safe_place_order, so a refusal cannot
#    mislabel a LATER genuine timeout
self._last_order_send_refusal = None

# 3. say which of the two actually happened
reason = result.comment if result else (self._last_order_send_refusal or "timeout_no_fill")
```

`order_rejected:timeout_no_fill` → `order_rejected:activation_token_namespace_mismatch`.

**Why this changes no trading behaviour — checked, not asserted:**

- `timeout_no_fill` appears in `src/` exactly **once** (the line changed). Nothing keys on the string.
- Retry/bar-consumption is decided by `book_owner._is_transient_place_failure`, which prefix-matches
  `_TRANSIENT_PLACE_REASON_PREFIXES`. Both the old and new labels carry `order_rejected:`, and none
  of the `_TERMINAL_BROKER_REJECT_MARKERS` substrings occur in the new suffix — so the classification
  is identical. Pinned by a test.
- The diagnostic `status` is deliberately left as `order_send_exception`. `order_router.py:103-104`
  falls back to that status as the reason when `_last_open_trade_block_reason` is empty, and
  `order_send_exception` is itself a transient prefix; changing it could have altered bar
  consumption. It is the one thing I was tempted to make more descriptive and deliberately did not.
- Only the entry path (`execution.py:3762`) labels this way. The other eight `safe_place_order` call
  sites are close paths, which are risk-reducing and never require a token.

**Tests** — `tests/test_execution.py::TestActivationRefusalIsNotReportedAsATimeout`, 5 tests:

| test | pins |
|---|---|
| `test_safe_place_order_records_the_gates_reason` | the gate's mechanical reason is captured |
| `test_open_trade_names_the_refusal_not_a_timeout` | label is the refusal, and `"timeout_no_fill" not in reason` |
| `test_a_real_timeout_is_still_called_timeout_no_fill` | the other direction — the repair narrows the label, it does not rename every failure |
| `test_a_refusal_does_not_leak_into_the_next_attempt` | the per-call clear; a refusal cannot mislabel a later timeout |
| `test_retry_classification_is_unchanged` | behaviour neutrality, asserted against `_is_transient_place_failure` |

The refusal fixture is the live decision, reproduced field for field
(`activation_token_namespace_mismatch` / `exposure_increasing_new_deal` /
`redacted_account_live_bee34003 != redacted_account`).

**The tests are sensitive** — a regression test that passes on broken code is worthless, so this was
measured by running them against the *unfixed* `execution.py` (restored from HEAD, then restored back):

```text
vs UNFIXED execution.py : 4 failed, 1 passed
vs FIXED   execution.py : 5 passed
```

The one that passes in both is `test_retry_classification_is_unchanged` — correctly, since it asserts
the behaviour that did **not** change.

Wider suite: `tests/test_execution.py`, `tests/ultimate_book/test_book_owner.py`,
`tests/ultimate_book/test_order_route.py` → **170 passed, 1 failed**, the failure pre-existing (§8).

**A reusable verifier**, `scripts/verify_activation_authorization.py`, promotes §4's proof from a
one-off into an operator check, because §0.2 means `status` cannot be trusted for this class of
defect. Read-only; `order_send` disabled; exits non-zero unless the live namespace authorizes **and**
a wrong namespace is still refused.

```bash
python scripts/verify_activation_authorization.py --book fn     # PASS, exit 0
python scripts/verify_activation_authorization.py --book ftmo   # PASS, exit 0
```

---

## 7. Why the kill flags did not stop the books (LN §9.4)

Answered, from code and from live evidence. **It is not a defect, and neither of LN's two hypotheses
— a blocking MT5 call, or a flag-path mismatch — was right.**

The kill flag is a **placement brake, not a process stop.** `BookLauncher.run_forever` contains no
kill check at all:

```python
def run_forever(self, max_ticks=None):
    n = 0
    while max_ticks is None or n < max_ticks:
        self.tick()
        n += 1
        if max_ticks is not None and n >= max_ticks:
            break
        time.sleep(self.poll_seconds)
```

The flag is read inside `tick()` and only suppresses placement (`launcher.py:208-209`):

```python
killed, halted = self.killed(), self.halted()
place = not (killed or halted)
```

Nothing exits on it. The supervisor is explicit about the same design
(`run_book_supervisor.ps1:6-7`): *"the supervisor only ever STARTS a missing book; it never stops one,
so it can never orphan an open position. Operator brakes remain the per-account kill flags + the halt
flags."*

**And the flags were seen — quickly.** Both books emitted the brake transition, still in their
notification queues:

```text
operator_profile   2026-08-06T01:06:40.447951Z  W7 BOOK: PLACEMENT PAUSED (kill=True halt=False) — observe-only
redacted_account_live_bee34003 2026-08-06T01:06:35.168758Z  W7 BOOK: PLACEMENT PAUSED (kill=True halt=False) — observe-only
```

LN placed the flags at 01:06:16Z. redacted_account acknowledged in **19 s**, FTMO in **24 s** — well inside
one 60 s poll. The flag path was correct and the poll was not blocked. The books stayed alive for the
only reason available: **nothing in the system terminates a book on a kill flag.** LN's force-kill was
therefore not a workaround — it was the only mechanism that stops the process, and with both accounts
flat it was the correct action.

The operational correction is to the *procedure*, not the code: a kill flag guarantees observe-only,
not exit. It engages fast, so "flag, confirm PLACEMENT PAUSED, confirm flat, then stop the process"
is a sound stop sequence — the confirmation signal exists and LN's 150 s wait was waiting for
something that was never coming.

*(The launcher JSONL cannot show this: a `no_new_bar` tick returns before the record write, so only
cycle ticks are logged. The notification queue is the right evidence source.)*

---

## 8. The pre-existing test failure

`tests/ultimate_book/test_book_owner.py::test_runtime_learning_batch_preserves_valid_packets_when_one_packet_is_invalid`
fails with `missing_targetless_time_stop_clock_field:policy_clock_status` (also
`policy_clock_checked_at_utc`, `policy_clock_time_stop_bars`).

Confirmed pre-existing rather than assumed: `src/components/execution.py` was restored to HEAD, the
single test re-run — **still failed** — and my bytes restored. It is in the runtime-learning packet
guard carried by Session LN (CN), untouched by this session. **Not repaired here** — it is outside
this session's scope and belongs with the CN carry. Flagged in §10.

---

## 9. What I got wrong

1. **My first "genuine timeout" test was unfaithful, and the code told me so.** I mocked a timeout as
   `order_send` returning `None`, and got `AttributeError: 'NoneType' object has no attribute
   'success'` from `execution.py:6698` — a line *after* the try/except. I had assumed `None` was the
   no-fill path; it is not. `RealMT5.order_send` converts a raw `None` into an `OrderResult`
   (`mt5_real.py:498-500`), so `None` never reaches there in production, and the real
   `timeout_no_fill` path is the `concurrent.futures.TimeoutError` branch. I rewrote the test to
   drive the actual branch. Had the mock happened to pass, I would have shipped a test that pinned
   a path the system never takes.

2. **A latent gap I found this way and did *not* fix.** If anything ever hands `safe_place_order` an
   adapter whose `order_send` returns `None`, that `AttributeError` escapes a function documented as
   the most important safety function. It is unreachable through `RealMT5` today. I left it alone
   because touching that path is riskier than the defect, but it is real and it is recorded here
   rather than quietly discarded. §10.

3. **I nearly proved the repair against the wrong directory.** `token_dir()` resolves `~`, my shell
   is Administrator, and the books run as `trader` — which looks like a different profile and would
   have meant minting somewhere the books never read, with every check I ran still passing. I caught
   it only because the owner mismatch was visible in the process list. The SID check (RID 500) and
   the books' own logged `token_dir` are what settle it. **Generalisable:** a token/credential repair
   must prove the *path the consumer reads*, and "my shell resolved it" is not that proof.

4. **I initially framed the restart question as "restart cleanly if needed" and had to invert it.**
   The instinct was to restart to make everything live. Reading the gate showed the token needs no
   restart at all, which makes a restart pure added risk against the primary objective. The code fix
   does need one — but it is additive observability, so deploying it is a scheduling decision, not a
   correctness one. Splitting those two was the right call and I did not make it immediately.

5. **My first two attempts to read the console logs failed on tooling, not on evidence.** `grep`,
   `head` and `tail` do not exist in this Bash, and PowerShell has no heredoc, so a Python one-liner
   died on a parser error. Trivial, but it is exactly the shape of failure that produced LN's
   false negative on the same files — a tooling error that returns *nothing* looks like evidence of
   absence. I wrote the reader to a file and NUL-stripped before decoding.

---

## 10. What Borhen must decide

1. **The `timeout_no_fill` repair is on disk and committed, but not yet live.** The books are still
   running the code they loaded at 01:10:40. It takes effect at the next restart, natural or
   deliberate. It changes no trading behaviour (§6), and the import chain was verified so a
   supervisor restart at any moment is safe. **My recommendation: let it land at the next natural
   restart.** The token repair — the part that actually matters — is already live and needs nothing.
   The next predictable authorization wall is token expiry on **2026-08-14T17:23Z**; the labelling
   fix should be live before then, so if no natural restart occurs first, restart while flat closer
   to that date.

2. **Both tokens expire 2026-08-14T17:23Z**, in 8 days. That is now a *dual-account* deadline: when
   they lapse, both books stop placing. Worth a calendar entry rather than a rediscovery.

3. **An authorization refusal is currently classified as a *transient* placement failure**, so a
   refused entry retries every tick — which is why 231 refusals accumulated in under two hours rather
   than a handful. Arguably it should be terminal for the bar, since it cannot clear without a human
   re-mint. I deliberately did **not** change this: it alters bar consumption, which is trading
   behaviour, and the brief was explicitly observability-only. **Flagged as a candidate repair, your
   call.**

4. **The pre-existing `test_book_owner` failure (§8)** sits in the CN runtime-learning packet guard
   carried by Session LN. Unrelated to F1, not fixed here, and it should not be left to rot.

5. **`gtos_activation_token.py status` self-certifies a mis-bound token (§0.2).** The new verifier
   covers it, but nothing *runs* the verifier automatically. Worth wiring into the watchdog or the
   supervisor's start path so the next mis-mint is caught in minutes, not days.

6. **redacted_account's silence from 2026-07-02 to 2026-07-31 is still unexplained.** F1 accounts only for
   the post-mint window (2026-07-31T17:23:50Z onward), exactly as LN said. Repairing F1 does not
   close that earlier gap, and I did not investigate it.

---

## 11. Changed bytes

| path | change |
|---|---|
| `src/components/execution.py` | `ActivationTokenError` import; `_last_order_send_refusal` init + per-call clear; refusal-aware `except` branch; the label at the entry path |
| `tests/test_execution.py` | `TestActivationRefusalIsNotReportedAsATimeout` (5 tests) + `concurrent.futures` / activation imports |
| `scripts/verify_activation_authorization.py` | **new** — read-only authorization verifier |
| `docs/…/phase19/SESSION_LO_FN_TOKEN_REPAIR.md` | this document |
| `host-local\.gtos\activation\bee34003….token.json` | **re-minted** (outside the repo, by design) |

No config byte, no launcher byte, no book restart, no FTMO token change.

## 12. Session log

```text
2026-08-06T01:21Z  preflight: generate_live_state.py, LIVE_STATE, CLAUDE.md, LN ceremony result
2026-08-06T01:23Z  diagnosis confirmed independently: cmdline, run_book.py:307-308, verify vs runtime ns
2026-08-06T01:25Z  token-directory resolution proven (trader = RID 500 = host-local)
2026-08-06T01:26Z  pre-state: token/config/signing digests, PIDs, monitor heartbeat
2026-08-06T01:27Z  broker pre-state read-only: FTMO 0 positions $108,365.48 / FN 0 positions $96,229.28
2026-08-06T01:28:37Z  MINT — redacted_account only, --force, ns=redacted_account_live_bee34003
2026-08-06T01:29Z  FTMO token + signing key byte-identical; all three config digests unchanged
2026-08-06T01:31Z  empirical authorization proof, FN: PASS (negative controls refuse)
2026-08-06T01:33Z  empirical authorization proof, FTMO: PASS (behaviour unchanged)
2026-08-06T01:36Z  timeout_no_fill repair + 5 tests; sensitivity proven vs unfixed bytes (4 fail / 5 pass)
2026-08-06T01:38Z  book_owner failure proven pre-existing at HEAD; import chain + compile verified
2026-08-06T01:40Z  kill-flag question answered from launcher.py + brake-transition notifications
2026-08-06T01:41Z  post-state: both books still pid 3152/9848 + 10964/2084, never restarted
```
