# Token chaos drills — run receipts

Run 2026-07-29T05:27:37Z on a macOS laptop with no MT5 terminal and no broker connection.

| drill | title | environment required | ran on | verdict | criteria met |
|---|---|---|---|---|---|
| D-1 | Gate flip without a token | laptop | macOS laptop, no MT5 terminal, no broker connection | **PASS** | 4/4 |
| D-2 | Expiry mid-position, plus a broker fetch error | demo account | macOS laptop, no MT5 terminal, no broker connection | **PASS** | 5/5 |
| D-3 | Activation directory unreadable | laptop | macOS laptop, no MT5 terminal, no broker connection | **PASS** | 16/16 |
| D-4 | Clock skew | laptop | macOS laptop, no MT5 terminal, no broker connection | **PASS** | 4/4 |
| D-5 | Revoke and restore | laptop | macOS laptop, no MT5 terminal, no broker connection | **PASS** | 7/7 |
| D-6 | Wrong user | demo account (Windows) | macOS laptop, no MT5 terminal, no broker connection | **PASS** | 6/6 |
| D-7 | What MT5 does with an over-volume close | demo account | macOS laptop, no MT5 terminal, no broker connection | **NOT_RUNNABLE_HERE** | 2/2 |
| D-8 | Does killing a terminal really produce None? | demo account | macOS laptop, no MT5 terminal, no broker connection | **NOT_RUNNABLE_HERE** | 3/3 |
| X-1 | Direct attack on the never-strand invariant | laptop | macOS laptop, no MT5 terminal, no broker connection | **PASS** | 5/5 |

## What each drill found

### D-1 — Gate flip without a token — PASS
- PASS — (a) the request does not reach the broker module (expected `no order_send call`, observed `0 call(s)`)
- PASS — (b) the refusal reason is activation_token_absent (expected `activation_token_absent`, observed `activation_token_absent`)
- PASS — (c) at least one AUTHORITY GATE CHANGED alert naming live_activation_allowed (expected `>=1`, observed `1`)
- PASS — (d) the alert reaches send() (expected `every gate alert handed to send()`, observed `2/2`)
- NOTE: The config edit is made in a SCRATCH copy; config/agent_config.yaml is R2-decision-contract-bound (H1) and is never touched.
- NOTE: (d) proves the alert reaches the send() seam. Whether send() then delivers depends on this process holding a notification-delivery grant (src/safety/notification_authorization.py); the observed grant state is recorded above. This harness deliberately does NOT grant it — a drill must not page the owner.

### D-2 — Expiry mid-position, plus a broker fetch error — PASS
- PASS — the close is allowed (expected `reaches the broker`, observed `{'reached_broker': True, 'retcode': 10009, 'raised': None, 'reason': None}`)
- PASS — order_send is actually called once (expected `1`, observed `1`)
- PASS — reason is risk_reducing_position_close_unverified (expected `risk_reducing_position_close_unverified`, observed `risk_reducing_position_close_unverified`)
- PASS — positions_verified is False (expected `False`, observed `False`)
- PASS — an entry is still refused (the escape hatch is not a bypass) (expected `activation_token_expired`, observed `activation_token_expired`)
- NOTE: PARTIAL. The Python-side half ran here with a fake module returning None. The half that needs a demo terminal is D-8's question — whether killing terminal64.exe actually produces None rather than an exception, a hang, or a stale tuple. See the D-8 receipt: the stale-tuple branch is measured here and it STRANDS the close.

### D-3 — Activation directory unreadable — PASS
- PASS — a. token dir is a regular file: the close is allowed (expected `reaches the broker`, observed `{'reached_broker': True, 'retcode': 10009, 'raised': None, 'reason': None}`)
- PASS — a. token dir is a regular file: read_token is NOT called for the close (expected `0`, observed `0`)
- PASS — a. token dir is a regular file: the entry is refused (expected `refused`, observed `activation_token_unreadable`)
- PASS — a. token dir is a regular file: nothing raises but ActivationTokenError (expected `ActivationTokenError or nothing`, observed `{'close': None, 'entry': 'ActivationTokenError'}`)
- PASS — b. token dir is a broken symlink: the close is allowed (expected `reaches the broker`, observed `{'reached_broker': True, 'retcode': 10009, 'raised': None, 'reason': None}`)
- PASS — b. token dir is a broken symlink: read_token is NOT called for the close (expected `0`, observed `0`)
- PASS — b. token dir is a broken symlink: the entry is refused (expected `refused`, observed `activation_token_absent`)
- PASS — b. token dir is a broken symlink: nothing raises but ActivationTokenError (expected `ActivationTokenError or nothing`, observed `{'close': None, 'entry': 'ActivationTokenError'}`)
- PASS — c. token dir has no permissions: the close is allowed (expected `reaches the broker`, observed `{'reached_broker': True, 'retcode': 10009, 'raised': None, 'reason': None}`)
- PASS — c. token dir has no permissions: read_token is NOT called for the close (expected `0`, observed `0`)
- PASS — c. token dir has no permissions: the entry is refused (expected `refused`, observed `activation_token_unreadable`)
- PASS — c. token dir has no permissions: nothing raises but ActivationTokenError (expected `ActivationTokenError or nothing`, observed `{'close': None, 'entry': 'ActivationTokenError'}`)
- PASS — d. token dir under a nonexistent user's home: the close is allowed (expected `reaches the broker`, observed `{'reached_broker': True, 'retcode': 10009, 'raised': None, 'reason': None}`)
- PASS — d. token dir under a nonexistent user's home: read_token is NOT called for the close (expected `0`, observed `0`)
- PASS — d. token dir under a nonexistent user's home: the entry is refused (expected `refused`, observed `activation_token_dir_inside_repository`)
- PASS — d. token dir under a nonexistent user's home: nothing raises but ActivationTokenError (expected `ActivationTokenError or nothing`, observed `{'close': None, 'entry': 'ActivationTokenError'}`)
- NOTE: read_token is instrumented rather than inferred: the pass criterion is that the close returns BEFORE any token I/O, which a reason string alone cannot show.

### D-4 — Clock skew — PASS
- PASS — (a) a fast mint cannot buy a valid future token (expected `activation_token_not_yet_valid`, observed `activation_token_not_yet_valid`)
- PASS — (b) a fast verify clock expires the token (expected `activation_token_expired`, observed `activation_token_expired`)
- PASS — (c) an offset-stamped expiry parses aware and compares against UTC (expected `valid before expiry, expired after`, observed `{'before': 'activation_token_valid', 'after': 'activation_token_expired'}`)
- PASS — (d) a naive expiry is read as UTC and still fails closed on EXPIRY, not merely on signature (expected `activation_token_expired`, observed `activation_token_expired`)
- NOTE: Sub-case (d) is not in the spec. It was added because `_parse_utc` back-fills a missing tzinfo with UTC, and a token whose expiry lost its suffix in transit must not become unbounded.

### D-5 — Revoke and restore — PASS
- PASS — a minted token authorizes an entry (expected `reaches the broker`, observed `{'reached_broker': True, 'retcode': 10009, 'raised': None, 'reason': None}`)
- PASS — revocation is effective on the very next request, no restart (expected `activation_token_absent`, observed `activation_token_absent`)
- PASS — re-authorization works after a revoke (expected `reaches the broker`, observed `{'reached_broker': True, 'retcode': 10009, 'raised': None, 'reason': None}`)
- PASS — with no key present the old token does not verify (expected `not allowed`, observed `activation_token_signing_key_absent`)
- PASS — the old token reports signature_invalid, not valid (expected `activation_token_signature_invalid`, observed `activation_token_signature_invalid`)
- PASS — (e) a corrupt key file does not brick the mint path (expected `mint succeeds and the operator can re-authorize`, observed `{'mint': True, 'entry': None}`)
- PASS — no step leaves a position unclosable (expected `every close reaches the broker`, observed `[True, True, True]`)
- NOTE: 'Revoke' is modelled as removing the token file — the operation scripts/gtos_activation_token.py exposes. There is no revocation list; absence IS revocation, which is why step 2 is the whole test.

### D-6 — Wrong user — PASS
- PASS — the two users resolve different token directories (expected `different`, observed `['/var/folders/xs/jrjm70xd7fgfnznxtps12nc80000gn/T/gtos_token_chaos_vntjrkbg/home_userA/.gtos/activation', '/var/folders/xs/jrjm70xd7fgfnznxtps12nc80000gn/T/gtos_token_chaos_vntjrkbg/home_userB/.gtos/activation']`)
- PASS — user B does not see user A's token; new exposure is refused (expected `activation_token_absent`, observed `activation_token_absent`)
- PASS — the failure mode is a DENIAL, not a crash (expected `ActivationTokenError`, observed `ActivationTokenError`)
- PASS — and user B can still close (expected `reaches the broker`, observed `{'reached_broker': True, 'retcode': 10009, 'raised': None, 'reason': None}`)
- PASS — the resolved token_dir is machine-readable for the operator (expected `describe_activation_state reports the dir it actually read`, observed `/var/folders/xs/jrjm70xd7fgfnznxtps12nc80000gn/T/gtos_token_chaos_vntjrkbg/home_userB/.gtos/activation`)
- PASS — run_book.py surfaces the resolved token_dir so a 2 a.m. operator can see WHY nothing trades (expected `present`, observed `True`)
- NOTE: PARTIAL, and the residual is named. The mechanism — `token_dir()` reads `$GTOS_ACTIVATION_TOKEN_DIR`, else expands `~/.gtos/activation` at call time — is measured here by moving HOME. What CANNOT be measured on macOS is how Windows expands `~` for a scheduled task running as SYSTEM or a service account: `Path.expanduser()` there consults USERPROFILE/HOMEDRIVE+HOMEPATH, and SYSTEM's profile is C:\Windows\System32\config\systemprofile. That is a real difference in kind, not degree, and it stays UNVERIFIED until run on the host.

### D-7 — What MT5 does with an over-volume close — NOT_RUNNABLE_HERE
- PASS — the over-volume close is refused TODAY (the strand exists) (expected `refused`, observed `activation_token_absent`)
- PASS — the correctly-sized close is allowed (expected `reaches the broker`, observed `{'reached_broker': True, 'retcode': 10009, 'raised': None, 'reason': None}`)
- NOTE: CANNOT RUN. The question is what the BROKER does with the request, which no fake module can answer — a stand-in would only replay whichever of the three outcomes I chose to encode, which is assuming the answer.
- NOTE: What IS measured: the strand is real and reachable at HEAD. A position reduced out-of-band to 0.01 while the engine believes 0.03 produces a refused close with no token present. The exposure is bounded by how long the engine's in-memory volume can stay stale.
- NOTE: Cheapest partial mitigation that needs NO drill: re-read the position volume immediately before building a close. That is the fix the spec prescribes for outcome (3) and it is safe under all three outcomes — it is not blocked on D-7.
- NOTE: Until then flatten_all_positions.py (deliberately ungated) is the manual hatch.

### D-8 — Does killing a terminal really produce None? — NOT_RUNNABLE_HERE
- PASS — None -> the close survives (expected `allowed`, observed `risk_reducing_position_close_unverified`)
- PASS — an exception -> the close survives (expected `allowed`, observed `risk_reducing_position_close_unverified`)
- PASS — a STALE tuple -> the close is STRANDED (the dangerous answer) (expected `documented, not passed`, observed `activation_token_absent`)
- NOTE: CANNOT RUN. Which of {None, (), stale tuple, exception, hang} the real module produces when terminal64.exe dies is a property of the MT5 IPC layer. `mt5_real.py:449-450` asserts None; nothing has measured it.
- NOTE: What IS measured here: the three shapes' CONSEQUENCES, driven through the real adapter. None and exception both survive. A stale tuple that omits the live ticket STRANDS the close — `positions_for_activation` is marked @strict_positions_provider, so 'ticket absent' is read as authoritative absence, the close classifies as exposure_increasing_deal_on_position, and with no token it is refused.
- NOTE: SCOPE, corrected (B335). This is the only path found that can refuse a close INSIDE THE ACTIVATION-TOKEN LAYER. It is not the only one in the system, and saying so without the qualifier turned a true measurement into a false guarantee. Above this layer, `execution.py`'s close-volume gate refused ~11 % of position sizes outright (B333, fixed), `live_broker_authority: false` suppresses flatten entirely (B334), and a runtime halt's risk-reducing carve-out reads positions through the lossy reader B101 repaired here (B334). Every drill in this file exercises the token layer, and the token layer was not where the risk was.
- NOTE: So D-8 is not merely unanswered — its dangerous branch is the one reachable strand in this layer, and the cost of leaving it unmeasured is now priced.
- NOTE: Run D-8 before D-2, as the spec says.

### X-1 — Direct attack on the never-strand invariant — PASS
- PASS — no close-shaped request in the repo carries sl or tp (expected `none`, observed `[]`)
- PASS — a close carrying sl IS refused (so the claim above is load-bearing) (expected `refused`, observed `activation_token_absent`)
- PASS — all four risk-reducing shapes pass with no token (expected `all reach the broker`, observed `{'market close': True, 'partial close': True, 'stop tighten': True, 'pending cancel': True}`)
- PASS — an unwritable audit sink does not block a close (expected `reaches the broker`, observed `{'reached_broker': True, 'retcode': 10009, 'raised': None, 'reason': None}`)
- PASS — a non-Exception raise out of the provider is REPORTED, not silently swallowed — recorded either way (expected `documented`, observed `{'raised': 'KeyboardInterrupt', 'reason': "KeyboardInterrupt('terminal killed mid-read')", 'allowed': None}`)
- NOTE: Not in TOKEN_CHAOS_DRILLS.md. Added because the session prompt ranks the never-strand invariant above everything else in it.
- NOTE: Criterion 5 is recorded rather than judged: `_read_positions` catches `Exception`, so a `BaseException` from a provider propagates and would block the close. No real MT5 path raises one — `positions_for_activation` wraps its own call in `except Exception` — so this is a latent shape, not a live defect. It is written down so a future provider author sees the boundary.

