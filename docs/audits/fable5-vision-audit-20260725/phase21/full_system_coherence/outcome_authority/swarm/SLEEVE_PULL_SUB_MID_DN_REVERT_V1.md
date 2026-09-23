# Sleeve pull: `sub_mid_dn_revert` is disarmed on both accounts

**Owner-authorized 2026-08-12** ("yes proceed as proposed and recommended"), on
`W7_INSTRUMENT_RESTATEMENT_V1.md` (commit `90824c858`). **Executed and verified live** at
**2026-08-11T11:47:56Z**; host commit `47d0960e6` on
`vps/ultimate-conditioned-expansion-minimal-2026-06-18`.

Receipts: `sleeve_pull_receipts/`. Every broker read used only `initialize / account_info /
positions_get / terminal_info / shutdown`. **No `order_send`, no `order_check`, no
`order_calc_*` was called at any point.** Account numbers are redacted as
`redacted:<sha256[:12]>`, the estate's convention.

---

## 0. What changed, in one table

| | before | after |
|---|---|---|
| `--tags`, **both** accounts | `crypto,energy_agri,sub_xvol_pullback,sub_mid_dn_revert` | **`crypto,energy_agri,sub_xvol_pullback`** |
| resolved generating sleeves, FTMO | 4 | **3** |
| resolved generating sleeves, redacted_account | 4 | **3** |
| host `scripts/run_book_supervisor.ps1` | sha256 `16901327…`, 19,494 B | sha256 `9B7F019C…`, 19,458 B (**−36 B**) |
| FTMO worker PIDs | 11056 / 10844 | 8028 / 2932 |
| redacted_account worker PIDs | 11256 / 11232 | 3980 / 2436 |
| supervisor PID | 7316 | 6536 |
| **config digest, FTMO** | `0b0dbe307379` | **`0b0dbe307379` — unchanged** |
| **config digest, redacted_account** | `8540f9a9f302` | **`8540f9a9f302` — unchanged** |
| activation tokens | valid | **untouched — no re-mint** |

**Not touched, by design:** `config/agent_config.yaml` (not one byte), the activation-token
layer *and* both tokens, `--spread-geometry-floor`, `--frontier-exits` (still absent on both),
`--poll-seconds`, the three authority gates, the kill flags, the risk dial, the cluster
envelope, every sleeve's geometry, and the `sub_mid_dn_revert` sleeve **definition** — it is
disarmed, not deleted, and the registry still resolves it.

---

## 1. Why — the evidence, and the fact that it is a risk reduction

From `W7_INSTRUMENT_RESTATEMENT_V1.md` §3.4, FTMO, 150 replicates, `net@max` being
`sleeve_table(...)['net_r']['n_max']` — the predicate the survivor book itself reads:

| sleeve | n | gross published → corrected | Δ | net@max published → **corrected** | 95 % interval |
|---|---:|---|---:|---|---|
| **`sub_mid_dn_revert`** | 398 | +0.3166 → **+0.0553** | **−82.5 %** | +0.0167 → **−0.2446** | **[−0.3507, −0.1240]** |

Three properties made this decision-bearing rather than merely negative:

1. **The interval excludes zero.** This is not "the edge shrank"; it is a measured negative
   expectancy at maximum carry with a 95 % interval entirely below zero.
2. **It fails the survivor predicate in 300/300 replicates on BOTH accounts** (§3.5). Under
   the correction the sleeve loses survivor status on FTMO *and* redacted_account — the only tier
   change in the table that lands on armed money.
3. **It is corroborated by an independent walker on an independent population**: lane m3
   measured **−59.6 %** of published gross on the *archive* population against **−82.5 %**
   here on the *cache* population. Two populations, two walkers, same direction. The sleeve
   also carries the estate's **highest migration rate (19.3 %)** and its second-highest
   spread-over-risk (0.0871), which is the mechanism — it is exactly the kind of sleeve a
   quote-side instrument defect would flatter.

Removing a sleeve from `--tags` is **risk-reducing**: it can only stop new exposure being
generated. It cannot close, open, or resize anything.

---

## 2. The five hazards this change had to clear, each verified rather than assumed

| # | hazard | how it was cleared |
|---|---|---|
| 1 | **`--tags ""` is FALSY and means ALL BUILT SLEEVES** (`run_book.py:383`, and the launcher's own `$tagArg = if ($b.tags) {…} else {""}` at host `:434` — the fail-open exists on *both* sides) | The new value is non-empty and was read back **out of the running process command line**, not out of the file. Both workers per account carry `--tags crypto,energy_agri,sub_xvol_pullback`. |
| 2 | **An all-typo `--tags` stands the book down silently** (`registry.py:144` — `[built[t] for t in tags if t in built]`, no fallback, no error) | Verified through **the engine's own resolver**, not by eye: `active_specs(tags, include-flags)` filtered by `effective_registry(...)`, i.e. the exact `book_engine._generate_intents` → `_active_sleeve_names` (DF-1) path. `dropped_unknown_tags` is **`[]`** on both accounts, and the resolved set is exactly the three intended names. |
| 3 | **The conviction ledger is monotone within a decision day** (`admission.py:1209-1210`, `na = max(na, override)`) | **Moot, and measured to be moot.** Both `firing_sleeves.json` files held only `{"days": {"2026-08-04": ["energy_agri"]}}`, unmodified since 2026-08-04T17:00Z — seven days stale. `n_active_override.get(day, 0)` returns 0 for an absent day, so a restart on 2026-08-11 could inherit nothing. Nothing was cleared, and nothing needed to be. The direction is also protective: this change can only *lower* the count. |
| 4 | **Open positions are not stranded** (`book_owner.py:489`, `:2680` call `active_specs(None, …)` un-intersected) | Nothing to strand: **0 open positions on both accounts**, before and after, and **0 positions naming the pulled sleeve**. |
| 5 | **Do not assume the current `--tags`** | Read first, two independent ways: the launcher's `$books` rows (host `:140`/`:141`) and all four running command lines. `sub_mid_dn_revert` **was** armed on both accounts. The record was correct. |
| 6 | **A token re-mint may be needed** | It was not, and this was verified rather than argued: `--tags` is argv, not a config byte. `config_digest_for` returned the same value before and after on both accounts, and the **running processes' own logs** print `config_digest=0b0dbe307379` / `8540f9a9f302` at the new start — identical to the pre-ceremony values. |

### 2.1 The trap that this ceremony actually hit, and that the precedent did not have

`LIVE_BOOK_INTEGRITY_V1.md` changed `config/agent_config.yaml` and restarted by stopping the
four workers and letting the supervisor relaunch them. **That procedure would have silently
failed here.**

`$books = @(…)` is a **top-level assignment executed once when the supervisor starts** (host
`:139`). The supervisor process holds the tag array in memory and does not re-read its own
source. Killing only the workers would have relaunched them with the **old four tags** — a
change that is applied on disk, committed, and *not applied in the process tree*, with every
heartbeat healthy.

So the restart was of the **`GTOS_W7_BookSupervisor` scheduled task itself**, and the proof is
the running argv, not the file. **This distinction is now recorded in `CLAUDE.md` §4** because
it applies to every future `--tags`, `--frontier-exits` or `--spread-geometry-floor` change and
to none of the config-file ceremonies.

### 2.2 Why `--spread-geometry-floor` was deliberately left naming the pulled sleeve

Both accounts still carry `--spread-geometry-floor sub_mid_dn_revert,sub_xvol_pullback`. That
is intentional, and it was checked rather than waved through, because a floor that refuses to
parse is a **launch refusal** (`run_book.py:557` → `return 4`), which would have killed both
books.

`parse_spread_geometry_floor` validates against `_known_sleeves`, and `run_book.py:548-552`
builds that from `BUILT | CANDIDATE_BUILT | MARKET_EXPANSION_BUILT` — **the full registry, not
`--tags`**. A disarmed sleeve is still a registered sleeve, so the name stays valid and inert.
Removing it would have been a second, unmandated change that silently drops a protection if
the sleeve is ever re-armed. `armed_set.reconcile()` has no floor-vs-armed check (only
`frontier_exit_for_unarmed_sleeve`), so the invariant is satisfied either way — the choice was
made on the merits, not to satisfy a test.

---

## 3. The ceremony, as executed

All times UTC, 2026-08-11. Host `C:\Users\MSI\Documents\ai-trading-agent`, HEAD `bba5a38ae`.
No `git checkout / pull / clean / stash` was run in the live tree at any point.

| # | step | result |
|---|---|---|
| 0 | pre-state (read-only) | 4 tags on both accounts; gates ×4 True on both; 0 open positions; kill flags absent; tokens valid; conviction ledger 7 days stale |
| 1 | backup | `host-local\smdr_20260811\run_book_supervisor.ps1.before`, sha256 verified equal to live |
| 2 | uniqueness assertion | the exact tags literal occurs **exactly 2×**; `sub_mid_dn_revert` occurs 4× in the file (2 tags + 2 spread-floor), so the replacement is unambiguous |
| 3 | edit, 11:47 | one hunk per account, **2 insertions / 2 deletions**, −36 B (= 2 × `,sub_mid_dn_revert`), PowerShell tokenizer reports **0 parse errors** *before* the bytes were written and again from disk |
| 4 | restart, 11:47:35 → 11:48:17 | supervisor task stopped, 4 workers stopped, task started; supervisor PID 6536; **all four workers relaunched within 21 s** |
| 5 | resolver verification | see §4 |
| 6 | placement drill | see §3.1 |
| 7 | host commit | `47d0960e6`, 1 file changed, 2 insertions(+), 2 deletions(−); nothing else staged |

### 3.1 The placement proof — through the engine's own gate, transmitting nothing

`sleeve_pull_receipts/sleeve_pull_verify.py` calls `activation_token.authorize_broker_mutation`,
the pure decision function behind `RealMT5.order_send`'s choke point. It classifies and answers
allow/deny; it does not transmit.

| probe | FTMO | redacted_account |
|---|---|---|
| **exposure-INCREASING** (`TRADE_ACTION_DEAL`, `ORDER_TYPE_BUY`, no `position`) | **allowed** · `activation_token_valid` · `increasing` | **allowed** · `activation_token_valid` · `increasing` |
| risk-REDUCING control | allowed · `activation_token_valid` | allowed · `activation_token_valid` |
| **stale-digest negative control** (digest `0×64`) | **REFUSED** · `activation_token_config_digest_mismatch` | **REFUSED** · same |

The negative control is the one that matters: it proves the digest binding is **live**, so the
"digests unchanged, no re-mint needed" claim in §2 is a measurement and not an assumption — a
token bound to a different digest would have been refused, and was.

---

## 4. Post-state, resolved through the engine's own resolver

Receipts: `sleeve_pull_receipts/SLEEVE_PULL_VERIFY_PRE.json` and `…_POST.json` (same script,
same code path, two phases).

| | FTMO | redacted_account |
|---|---|---|
| namespace | `operator_profile` | `redacted_account_live_bee34003` |
| `--tags` in the **running argv** | `crypto,energy_agri,sub_xvol_pullback` | `crypto,energy_agri,sub_xvol_pullback` |
| **resolved generating sleeves** | **`['crypto', 'energy_agri', 'sub_xvol_pullback']`** | **`['crypto', 'energy_agri', 'sub_xvol_pullback']`** |
| dropped unknown tags | `[]` | `[]` |
| `sub_mid_dn_revert` generates? | **False** (was True) | **False** (was True) |
| effective registry size | 20 | 20 |
| gates (`apply_to_execution` / `live_activation_allowed` / `live_broker_authority` / `include_clean3`) | True ×4 | True ×4 |
| broker `trade_allowed` / terminal connected | True / True | True / True |
| balance / equity | $108,342.47 | $96,229.28 |
| open positions | **0** | **0** |
| heartbeat | fresh (~60 s, matching `--poll-seconds 60`), `"healthy": true` | fresh, `"healthy": true` |
| `authority_gates_ON` | **True**, `halted=False killed=False` (11:48:01) | **True**, `halted=False killed=False` (11:48:03) |
| kill flag | absent | absent |
| conviction ledger | untouched, still `2026-08-04` only | untouched, still `2026-08-04` only |

**No stop condition fired.** The estate is not in a half-applied state: both accounts moved
together, in one supervisor restart, and both were verified independently afterwards.

### 4.1 Rollback

Restore `smdr_20260811\run_book_supervisor.ps1.before` over
`scripts/run_book_supervisor.ps1` (sha256 `16901327EAFD4B80…`, 19,494 B), then restart the
`GTOS_W7_BookSupervisor` task — **the task, not the workers**, per §2.1. **No token step is
required in either direction**, which is what makes this rollback a two-minute operation
rather than a ceremony: no config byte moved, so no digest moved.

---

## 5. The mainline record — four files, and one of them is a test that had to be repaired honestly

`--tags` is the arming mechanism, and `src/safety/armed_set.py` reconciles it against
`config/live_armed_set.json` (the owner-decision declaration). A host-only change would have
left the committed launcher re-arming a sleeve the owner disarmed — **exactly the 2026-08-05
`mx_btcusd` defect, which ran for two days.** So the same change lands on mainline:

1. `scripts/run_book_supervisor.ps1` — the committed launcher (2 insertions / 2 deletions).
2. `config/live_armed_set.json` — `armed_sleeves` on both accounts, plus a `decision_log` entry
   carrying the owner's words, the host commit, the receipt and the evidence.
3. `docs/…/phase20/receipts/r1/r1_estate_rewalk.py` — its `ARMED` is **derived** from
   `armed_sleeves()`; only the offline fallback tuple its own comment promises is "kept
   identical to the manifest" was updated, and `sub_mid_dn_revert` moved to `FORMERLY_ARMED`
   so the script **keeps measuring the sleeve** whose forward record now matters most.
4. `tests/safety/test_armed_set_single_source.py` — see below.
5. `scripts/rerate_book_from_live.py` — comment stamp only; its `ARMED` is derived, which was
   the point of the 08-07 repair, but two present-tense sentences ("…which is armed") had
   become false.

### 5.1 The test repair, and why it is stronger rather than weaker

Three tests failed on the change, and the honest fix was not the same for all three, because
the artifacts they pin are not the same kind of thing.

`R2_RESULT_V1.json` is a **dated measurement**. Editing it to match today's config would
destroy the evidence it exists to carry. The old assertion was
`set(r2.live_isolation.armed_sleeves) == armed_sleeves()`, which can only be kept true by
rewriting receipts every time the owner arms or disarms anything. It is replaced by a declared
reconciliation in the manifest — `dated_artifact_basis` with `as_of`, `armed_sleeves_then` and
`disarmed_since` — and two assertions:

```python
assert then - gone == expected          # the delta reduces to the single source
assert set(r2[...]["armed_sleeves"]) == then   # and the receipt is unedited
```

That is **strictly stronger** than the equality it replaces: it pins the receipt *and* forces
every armed-set change since to be written down in one place.

The two fixture tests (`test_the_pre_repair_launcher_is_rejected`,
`test_the_repair_changed_only_the_ftmo_row`) asserted things about the **2026-08-07 repair**
against *today's* armed set, which silently assumed no further owner decision would ever land.
They now compare against the dated basis, and the second additionally asserts that today's
redacted_account row is that basis **minus exactly the declared disarms, nothing else**.

`sub_mid_dn_revert` was added to `DISARMED_BY_OWNER`, which is the mechanism that blocks a
silent re-arm.

### 5.2 Both directions proven, not asserted

The repaired invariant was run against two deliberate re-arms:

| control | what it models | result |
|---|---|---|
| **A** — launcher re-arms, declaration does not | the 2026-08-05 defect shape | **4 tests FAIL** (`launcher_and_declaration_agree`, `assert_consistent…`, `no_owner_disarmed_sleeve…`, `the_repair_changed_only_the_ftmo_row`) |
| **B** — launcher **and** declaration both re-arm | *"a 'did the set change' test passes happily if a disarmed sleeve comes back with a matching declaration edit — exactly the mistake worth blocking"* (the test file's own words) | **3 tests FAIL** |

Control B is the important one: it is the failure mode a naive equality test cannot see, and
it is caught three times over. In the intended state the file is **14/14 green**, against a
parent-commit baseline whose only failure was a sparse-checkout path artifact.

---

## 6. What this leaves open

1. **The armed book is now three sleeves and every published economic figure prices four.**
   `LIVE_BOOK_INTEGRITY_V1.md` §1.3's four-sleeve grid (`AS_PUBLISHED` / `CURRENT_SURFACE` /
   `FN_TRADEABLE`) is stale on composition as of today, exactly as it recorded
   `redacted_account_RUNNABLE_3` being stale before it. `sub_mid_dn_revert` was the **largest** cache
   population of the four (398 trades against 104/162/90) and carried 20 of FTMO's 42 armed
   symbol slots, so this is not a marginal restatement. **Nothing in this document should be
   read as the new expected economics** — that is a measurement, and it has not been made.
2. **The `substrate` cluster is now a single sleeve.** `sub_xvol_pullback` and
   `sub_mid_dn_revert` shared it, and the restored one-unit-per-cluster-per-day envelope was
   priced on both being present (`LIVE_BOOK_INTEGRITY_V1.md` §2.3, 869 trades / 603
   cluster-days). Its measured value should be expected to change; the direction is not
   obvious and is not guessed here.
3. **`--spread-geometry-floor` now names a sleeve that cannot generate on both accounts.**
   Inert and deliberate (§2.2), but it is the kind of thing a future reader will trip over, so
   it is declared in `config/live_armed_set.json`'s decision log rather than left to be
   rediscovered.
4. **The committed launcher and the host launcher remain divergent** (19,458 B on the host
   against 9,072 B here; `$books` at `:139` there and `:102` here; the spread-floor key is
   `floor` there and `spreadFloor` here). The manifest's
   `known_divergence_committed_launcher_vs_host` block is itself stale on the byte counts.
   **Carry individual argument changes, never the file** — which is what was done.
