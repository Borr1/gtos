# Token chaos drills — specifications

**Written, not run.** Stage 4 runs them. Each drill below states the exact setup, the exact
observation, the pass criterion, and — the part that makes it a drill rather than a test —
**what a failure would mean**, because two of these can only fail in ways that cost money.

Six were asked for. There are eight: D-7 and D-8 exist because the adversarial passes in
B102/B103 produced two questions that *cannot* be answered without a real MT5 terminal, and
leaving them as prose would be pretending they were settled.

---

## Where each drill may be run

| Environment | Drills | Why |
|---|---|---|
| **Laptop, no broker** | D-1, D-3, D-4, D-5 | Pure filesystem/clock/config. Already have unit coverage; the drill is the end-to-end version. |
| **Laptop or VPS, demo account** | D-2, D-6, D-7, D-8 | Need a real MT5 terminal. **Demo only.** |
| **Live funded account** | none | No drill in this file may be run against a funded account. |

> Anything that mints a token binds it to an account digest. **Mint against the demo
> account's login, never the funded one**, or the drill leaves a real authorization behind.

---

## D-1 — Gate flip without a token

**The question:** if someone flips the authority gates but no token exists, does the system
trade, and does anyone find out?

**Setup.** A laptop clone. Empty `GTOS_ACTIVATION_TOKEN_DIR`. Set all four gates true in a
scratch copy of `agent_config.yaml`:
`ultimate_book_enabled`, `ultimate_book_apply_to_execution`,
`ultimate_book_live_activation_allowed`, `ultimate_book_live_broker_authority`.
Drive `RealMT5.order_send` against a fake MT5 module with a normal entry request.

**Observe.** (a) whether the request reaches the fake module; (b) the `ActivationDecision`
reason; (c) whether `gate_tripwire()` returns an alert against the edited config; (d) whether
that alert reaches `send()`.

**Pass.** (a) no; (b) `activation_token_absent`; (c) at least one
`AUTHORITY GATE CHANGED ON DISK` naming `live_activation_allowed`; (d) yes.

**A failure means** the presence-of-authorization design does not hold: config alone is
sufficient to trade. That is the entire premise of Stage 0, so a failure here stops the
programme, not just the drill.

---

## D-2 — Expiry mid-position, plus a broker fetch error *(demo account)*

**The question:** the one the mechanism must never get wrong. Can a lapsed token, combined
with the broker read failing, prevent a position from being closed?

**Setup.** Demo account, one small position open (0.01 lot). Mint a token with a 1-minute
lifetime bound to that account. Wait for expiry. Then, with the token expired, force
`positions_get` to return `None` — the real MT5 failure signal — for the duration of one
close attempt. The supported way to induce it without patching: kill the MT5 terminal
process while the Python process stays up, so the IPC call fails; `positions_get` returns
`None`, not an exception.

**Observe.** The `ActivationDecision` for the close, and whether `order_send` reaches the
module once the terminal is back.

**Pass.** `allowed=True`, reason `risk_reducing_position_close_unverified`,
`positions_verified=False`. The close is attempted.

**A failure means** the never-strand invariant is broken *in exactly the state it exists
for*. This is the drill that maps onto the B101 bug: before that fix,
`RealMT5.get_positions` masked the `None` as `[]` and the close was refused. The unit tests
cover the mechanism; this drill covers whether killing a real terminal actually produces the
`None` the mechanism assumes. **If it produces something else — an exception, a hang, a stale
cached list — the fix is aimed at the wrong failure mode and must be re-derived.**

---

## D-3 — Activation directory unreadable

**The question:** can a broken token directory block a close?

**Setup.** Four sub-cases, each with an open position (or a synthetic close request):
(a) `GTOS_ACTIVATION_TOKEN_DIR` points at a regular file;
(b) at a broken symlink;
(c) at a directory with permissions removed;
(d) at a path under a nonexistent user's home (`~nosuchuser/act`).
Run one close and one new entry through `RealMT5.order_send` in each.

**Observe.** Close outcome, entry outcome, and whether the audit append raised.

**Pass.** In all four: the **close is allowed** (it returns before any token I/O — verify by
instrumenting `read_token`, which must not be called), and the **entry is refused**. Nothing
raises anything other than `ActivationTokenError`.

**A failure means** the risk-reducing return is not actually ahead of the filesystem work,
and a misconfigured directory can strand a position.

---

## D-4 — Clock skew

**The question:** does a wrong system clock create authorization or destroy it?

**Setup.** Three sub-cases on a laptop clone, using `now=` injection where the API allows and
a shifted system clock where it does not:
(a) clock **4 years fast** at mint time, then verified at the true time;
(b) clock **fast at verify** time, token minted normally;
(c) token whose `expires_utc` carries a broker-local offset (`+03:00`) rather than `Z`.

**Observe.** `verify_token` result in each.

**Pass.** (a) `activation_token_not_yet_valid` — `not_before_utc` is stamped from the same
skewed clock, so a fast mint cannot buy a valid future token; (b) `activation_token_expired`;
(c) parses as aware and compares correctly against UTC. All three fail **closed**.

**A failure in (a) means** a clock change is an authorization bypass, which is a far cheaper
attack than editing a signed token.

---

## D-5 — Revoke and restore

**The question:** is revocation immediate, and is re-authorization possible afterwards?

**Setup.** Mint a token. Confirm an entry is authorized. `revoke`. Confirm the entry is
refused. Mint again. Confirm authorized. Then the harder half: **delete `signing.key`**
between the revoke and the re-mint.

**Observe.** Behaviour at each step, and specifically whether the old token verifies after a
new key is generated.

**Pass.** Revoke is effective on the next request with no restart. Re-mint works. After key
deletion: any surviving old token reports `activation_token_signature_invalid` (not
"valid"), and a fresh mint generates a new key and works. **No step leaves the operator
unable to re-authorize.**

**Note what this drill is really testing.** B103 found that a corrupt (non-UTF-8) key file
used to raise out of `ensure_signing_key`, bricking the mint path so the operator could not
re-authorize without deleting the file by hand. Add that as sub-case (e): write
`b"\xff\xfe\x00"` into `signing.key` and confirm `mint` still succeeds.

---

## D-6 — Wrong Windows user *(demo account)*

**The question:** the token directory defaults to `~/.gtos/activation`. Does that mean what
we think it means when the process runs as a different user?

**Setup.** On a Windows box, mint a token as user A. Then run the book as user B — the
realistic version is the scheduled task running as `SYSTEM` or as a service account while
the operator minted from an interactive session.

**Observe.** `token_dir()` as resolved by each process, and whether the book finds the token.

**Pass.** The book run by user B does **not** see user A's token and refuses new exposure
(`activation_token_absent`). The failure mode must be a *denial*, and the log line at
`run_book.py` must print the `token_dir` it actually resolved, so the operator can see why.

**A failure means** either the token is shared more widely than intended, or — worse — the
operator mints into a directory the live process never reads, believes the system is
authorized, and cannot understand why nothing trades. **This drill is the one most likely to
produce a confusing 2 a.m. incident, and it is cheap to run.**

---

## D-7 — What MT5 actually does with an over-volume close *(demo account)* — **NEW**

**The question this session could not answer.** The classifier refuses a DEAL whose volume
exceeds the live position's volume, because it cannot prove such a request only closes. B103
showed the cost: if the broker reduces a position out-of-band (a partial fill, a manual
partial in the terminal) between the engine's resync points, the engine's in-memory volume is
stale, the close it builds is over-volume, and with no token it is refused. Whether that is
the *right* trade-off depends entirely on what MT5 does with such a request, which cannot be
determined from the Python side.

**Setup.** Demo account. Open a 0.03-lot position. Close 0.02 of it manually in the terminal
(leaving 0.01). Without letting the engine resync, send a raw `TRADE_ACTION_DEAL` with
`position=<ticket>`, opposing type, `volume=0.03`.

**Observe.** The retcode, and — the whole point — **whether any new position exists
afterwards**. Then repeat with the correct 0.01.

**Pass criterion is knowledge, not a green.** Record which of these MT5 does:
1. rejects with 10014 (invalid volume) and opens nothing;
2. closes 0.01 and ignores the excess;
3. closes 0.01 and **opens 0.02 of new opposing exposure**.

**If (1) or (2):** the classifier can safely treat an over-volume DEAL against an existing
opposing position as risk-reducing, and the B103 strand disappears. Change
`deal_reduces_existing_position` and delete the volume bound, with this drill as the receipt.
**If (3):** the current conservative refusal is correct and must stay; instead fix it at the
engine, by re-reading the position volume immediately before building a close.

Until this drill runs, the refusal stays and `flatten_all_positions.py` (deliberately
ungated) is the manual escape hatch.

---

## D-8 — Does killing a terminal really produce `None`? *(demo account)* — **NEW**

**The question:** every never-strand repair in B101 rests on one premise —
`MetaTrader5.positions_get` signals failure by returning `None`, not by raising. The repo
asserts this itself (`mt5_real.py:562`) but nothing has measured it.

**Setup.** Demo account, terminal connected, one position open. In a Python session, loop
`positions_get()` once a second and log `type(result)`. Then, in sequence:
(a) kill `terminal64.exe`;
(b) restart it but log out of the account;
(c) disconnect the network;
(d) restart the terminal and let it reconnect.

**Observe.** For each phase, exactly what `positions_get()` returns: `None`, `()`, a stale
tuple, an exception, or a hang — and how long any hang lasts.

**Pass criterion is, again, knowledge.** The dangerous answer is **a stale non-empty tuple**:
that would be a reader that is confidently wrong rather than unavailable, and neither the
`raise`-on-`None` fix nor the strict-provider marker would catch it. If that happens, the
provider needs a freshness check, and `positions_for_activation` needs a timestamp.

**Run D-8 before D-2.** D-2 assumes D-8's answer.

---

## Reporting

One receipt per drill under
`docs/audits/fable5-vision-audit-20260725/phase3/drill_receipts/`, each carrying: the
environment, the exact commands, the raw observation (paste it, do not summarise), the
verdict, and — for D-7 and D-8 — the decision the answer forces. A drill that was run and
not written down did not happen, the same way an A/B that was not committed did not happen.
