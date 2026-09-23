# Stage 0 item 0.1 — the token carry, as a reviewable diff

The five files that go to the VPS, diffed against the VPS-lineage commit `redacted_host`
(`origin/vps/ultimate-conditioned-expansion-minimal-2026-06-18`). Raw diffs are in
`token_carry/`. The ceremony is `STAGE0_VPS_RUNBOOK.md`; this document is the review
surface and the deployment-safety proof.

---

## 1. The carry

| # | file | VPS → this branch | shape |
|---|---|---:|---|
| 1 | `src/mt5/mt5_interface.py` | **+5, −0** | `TRADE_ACTION_MODIFY = 7`, `TRADE_ACTION_REMOVE = 8`, one comment |
| 2 | `src/safety/activation_token.py` | **NEW, 1,080** | the gate |
| 3 | `scripts/gtos_activation_token.py` | **NEW, 224** | mint / status / revoke |
| 4 | `src/mt5/mt5_real.py` | **+105, −0** | choke point + `set_activation_context` + `account_login_sha256` + `positions_for_activation` |
| 5 | `run_book.py` | **+36, −0** | one import, the activation-context declaration, the `.env` refusal |

Counts are total added lines, `diff` against `redacted_host`. Non-blank: 5 / 95 / 33.

**Nothing is deleted and nothing is rewritten.** Every hunk is an addition, which is what
makes the rollback in the runbook a one-liner.

Three files the carry *depends on* are already present and **byte-identical** between the
VPS commit and this branch, verified by `git show redacted_host:<path> | diff - <path>`:
`src/safety/runtime_halt.py`, `src/safety/__init__.py`, `src/utils/broker_profile.py`.
That is why "carry `src/safety/` as a package" costs one new file rather than a directory
sync.

### Corrections to the plan's description of this carry

- **`run_book.py` is a 15-line delta at the parent commit, not 17.** 15 added, 0 removed,
  14 non-blank. The session prompt asked for this to be re-derived and said a different
  number would be a finding. The *shape* is exactly as described. (It is +33 on this branch
  because B103 added the `.env` refusal.)
- **`scripts/gtos_activation_token.py` was not in the list and is absent from the VPS.**
  Without it there is no way to mint, inspect or revoke a token — the ceremony would have
  had no operator surface at all.
- **`src/components/execution.py` is not carryable.** It differs from the VPS by **2,178
  lines before this session touched it**. The 47 lines of B104 work in it are laptop-side
  hardening. Copying the file to pick them up would deploy a year of unrelated drift into a
  live engine. Flagged as an explicit *do-not-copy* in the runbook.

### The ordering constraint

`run_book.py` imports `activation_token` at module scope → `activation_token` imports
`TRADE_ACTION_MODIFY`/`TRADE_ACTION_REMOVE` from `mt5_interface` → **the VPS's
`mt5_interface.py` has neither**. Land file 1 first or `run_book.py` raises `ImportError` on
both accounts, the supervisor restart-loops (it starts a missing book, it never stops one),
and `manage_open_positions` stops running on any open position. This is the first **STOP** in
the runbook and the highest-consequence line in it.

---

## 2. Deployment safety — re-derived, not inherited

Borhen runs this on a live funded host, so each of the three claims was re-proved from
source rather than carried forward. Two survived. **One did not.**

### A — the carry imports nothing from the `book_owner`/packet coupling trap. **PROVEN.**

The trap is an atomicity constraint, not a general coupling: mainline's `book_owner.py`
passes a `convergence_advisory=` kwarg that the VPS's `runtime_learning_packet.py` has no
parameter for, so deploying either without the other is a `TypeError` on **every book
cycle** — a silent total outage of the live decision surface
(`.context/00_core/live_system_of_record.md:163`).

Full transitive import closure of `src/safety/activation_token.py`, computed by AST and
following the **lazy** import at line 653:

```
src.safety.activation_token
  ├── src.mt5.mt5_interface        (top-level, :65)
  ├── src.utils.broker_profile     (top-level, :72)
  └── src.safety.runtime_halt      (LAZY, :653)
4 repo modules. Trap check (book_owner / packet / convergence / ultimate_book): NONE.
```

The closure is closed — none of the three leaves reaches `src/components/`. The three
modified files add exactly this one edge between them; `mt5_interface.py` adds no import at
all. For contrast, `book_owner.py`'s own closure is **95 repo modules, 45 in the trap
family**.

### B — zero-token shadow is a no-op at every call site. **PROVEN.**

The sharp version of the question is: *does shadow reach `order_send` and rely on a
downstream no-op, or is the authority gate checked first?* It is checked first, at four
independent places:

| site | what it does |
|---|---|
| `book_owner.py:1492-1498` | `run_cycle` returns `would_units` **before any placement** when `runtime_effect_now` is false |
| `book_owner.py:2419` | `_manage_engine` returns `live_broker_authority_false_observe_only` before the exit paths |
| `book_owner.py:2257 / :2316 / :2351` | the flatten and breach-flatten paths are gated |
| `book_owner.py:2607-2611` | rehydrate passes `modify_broker_tp=False`, which gates the only mutation inside it |

So the guard is **unreachable in shadow**. Call-site enumeration confirms the surface is
three symbols wide: `enforce_broker_mutation_authorized` has one invocation
(`mt5_real.py:443`), `set_activation_context` one caller (`run_book.py:240`),
`account_login_sha256` one self-call.

And if it *were* reached, a raise is survivable rather than an outage: `launcher.py:290`
catches broadly, notifies, and returns the record; `tick` is documented and implemented as
never-raising; `run_forever` calls it bare. `run_book.py`'s activation block is itself
wrapped in `try/except`, and `config_digest_for` returns `None` on `OSError` rather than
raising.

**The start-up risk is nil on Python version and real on partial carry.** The VPS runs
**3.13.13** (measured, `vps-export-20260725/.../python_version.txt`), and its own
`mt5_real.py` already carries an unquoted PEP-604 union in an evaluated signature
(`git show redacted_host:src/mt5/mt5_real.py`, `-> list[dict] | None`), so that lineage already
requires ≥3.10 and the carry adds no floor. The real risk is §1's ordering constraint.

### C — the risk-reducing exemption lives in the token layer. **REFUTED as stated.**

Two findings, and this is where re-proving paid for itself.

**There were two definitions of the stop-modify test.** `activation_token.sltp_reduces_or_preserves_risk`
and `execution.py:526-540 _sl_modify_reduces_or_preserves_risk`. Differential over a 60-case
matrix: **2 disagreements**, both on dict-shaped positions, and the execution copy errs
**permissive** — it read `getattr(position, "sl", 0.0)` where the token layer reads dicts
too, so `current = 0.0` → "no stop yet" → `True`, calling a **widened** stop risk-reducing.
Latent (both adapters return `PositionInfo` today), one refactor from live. Now delegates.

**One call site bypasses the token layer entirely.** `heartbeat_monitor.py:727` drives the
raw module. It is halt-checked but never token-checked, and its exemption was **asserted by
an allowlist in a test**, not computed by the classifier. The exemption is correct — its only
mutation is a flatten, and it runs unattended, so a token that lapsed overnight must not
block it — but "no call site can bypass" was false.

*The DEAL half of the claim did hold:* `execution.py:510-524` delegates to
`deal_reduces_existing_position`, single definition. But the test guarding that
(`assert "deal_reduces_existing_position" in source`) is a source-substring grep — the exact
anti-pattern `CLAUDE.md` §6 names — and it never covered the SLTP half at all.

---

## 3. What the carry now contains that the review's version did not

The carry grew by 275 lines in `activation_token.py` and 49 in `mt5_real.py`, all of it
repairs found by attacking the mechanism (blocks B101–B103). The load-bearing ones:

- **The gate's position reader can no longer mask a failed broker read as an empty account**,
  which is what made a close classify as new exposure and be refused with no token — the
  never-strand invariant failing in exactly the state it exists for.
- **A DEAL on one symbol quoting another symbol's ticket is no longer a close.** Dropping the
  symbol filter to fix the strand opened a token-free path to new exposure; the classifier
  now checks the symbol itself.
- **The activation directory cannot be relocated from inside the repository.** One line in an
  untracked `.env` was a self-issued authorization for a funded account, because
  `load_dotenv(override=True)` runs before the safety import and `ensure_signing_key` mints a
  key wherever it is pointed.
- **`authorize_broker_mutation` actually never raises now** (it did, three ways), and a
  corrupt signing key no longer bricks the mint path.
- **`write_token` is atomic.** Both books share one directory; ~1.2 % of concurrent reads saw
  a torn file and refused a legitimate entry.
