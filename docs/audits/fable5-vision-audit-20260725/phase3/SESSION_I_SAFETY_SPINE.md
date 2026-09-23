# Session I — The safety spine

**Stage 0 items 0.1 + 0.2.** Worktree `worktrees/wave3-safety-spine-20260727`, branch
`phase3/safety-spine`, from `main` @ `1e95fe7fa`. **Your block range is B100–B109.**

**Read `../WAVE_3_WORKING_AGREEMENT.md` first.**

---

## Why this is item 0 of the whole plan

The review put it plainly: *"Before any of that: port the activation token to the VPS."*

The VPS is running **right now**. Supervisor task Running, both books healthy, both MT5 terminals
connected, `trade_allowed` **true** on both, two funded accounts (~108 k and ~96.1 k). The entire brake
between that host and live orders is **three false YAML booleans** — `apply_to_execution`,
`live_activation_allowed`, `live_broker_authority`, at exported working-tree `agent_config.yaml:1161-1163`.
No flag. No terminal block. No scheduler stop. **And nothing watching the gate** — a flip would not be
detected by anything.

The mechanism that fixes this exists and is well built: `src/safety/activation_token.py`, HMAC-signed,
account/namespace/config-bound, ≤720 h expiry, 36 dedicated tests, with risk-reducing requests exempt so
an expired token can never strand a position. **It is on mainline only.** The VPS copy's
`RealMT5.order_send` calls the raw module with no guard — verify for yourself:
`git show redacted_host:src/mt5/mt5_real.py`.

Absence-of-halt is fail-open. Presence-of-authorization is not. That is the whole argument.

## What you own

**The whole safety spine.** Not just the carry: the carry, its deployment-safety proof, the four
holes, the runbook, the chaos-drill specs, and — if you find one — the case that the token design
itself is wrong somewhere. That last one is live and worth your attention: the token is the mechanism
the entire activation plan rests on, it has been reviewed twice but **never attacked by a session whose
job was to break it**, and hole 1 below is proof that its own never-strand invariant has a hole in
exactly the state it exists for. If it has a fifth hole, or a design flaw rather than an
implementation one, **that is the most valuable thing this session can produce.** Attack it properly —
adversarial subagents, and the working agreement's orchestration grant is explicitly for work like
this.

**One hard boundary, and it is about the host, not about your scope.** The VPS is live, funded and
connected. You prepare and prove; Borhen executes. Never run a broker-capable script — working
agreement §4. That boundary constrains *where your hands go*, not how far your work reaches.

### 0.1 — the token carry

The review costed this at ~0.5–1 session and proved several of its preconditions already. Verify each
rather than trusting them:

- `src/safety/` must go across **as a package, not one file** — `authorize_raw_broker_request` lazily
  imports `runtime_halt`.
- `mt5_real.py` gets the guard.
- `run_book.py` gets the context call — the review measured this as a **17-line delta** against the VPS
  copy. Re-derive it; if it is not 17 lines, that is a finding.
- P4 `create_mt5` validation.
- Note `run_book.py:201` constructs `RealMT5` **directly**, so P4 protects the *other* entrypoints. The
  healthy-shadow-cycle check in the runbook exists to catch exactly a mode-string surprise.

**Deployment-safety is the claim that has to hold**, because Borhen will run this on a live host. The
review's mechanical argument: the carry imports nothing from the `book_owner`/packet coupling trap,
zero-token shadow is a no-op at every call site, and the risk-reducing exemption lives in the token
layer. **Re-prove all three yourself, and write the proof into your blocks.** If any of them fails, that
is the most valuable thing you will produce this session.

### 0.2 — the four holes, none previously filed

Each was found by the third review's live-surface reader and re-verified end-to-end by its adversarial
pass. Confirm each before fixing it.

**Hole 1 — the never-strand invariant has a hole in exactly the state it exists for.** This is the
serious one. `RealMT5.get_positions` masks broker fetch errors as `[]` (`mt5_real.py:321-333` — verified:
`if positions is None: return []`) and filters by magic number. So under token-absent **plus** a
transient fetch error, a **close** is refused as exposure-increasing, and a stop-tighten is refused as
`exposure_increasing_sltp_unknown_position` by the same path. The designed fail-safe branch
`risk_reducing_position_close_unverified` (`activation_token.py:394-437`) is **unreachable through the
real adapter**, because it triggers only when the provider *raises* — and this path never raises.

Fix the invariant, not just the symptom. A risk-reducing request must not be blocked by an unverifiable
position read.

**Hole 2 — `GTOS_UB_DERISK_MODE` sits outside the token's config digest.** It overrides the YAML derisk
mode at `book_engine.py:580-581`, while `config_digest_for` hashes exactly two files' bytes. Precise
exposure, per the adversarial pass: at the ≥2.0 % dial `admit_and_size` fails closed on any non-smooth
mode (`admission.py:1367-1370`), so this is a **silent fail-closed trading stop** plus un-audited
derisk-shape drift at sub-2.0 % dials — *not* un-certified trading. Fix it at the right severity.

**Hole 3 — `scripts/mt5_preflight.py`.** Default observation-only; armed via `--test-order` /
`GTOS_MT5_PREFLIGHT_TEST_ORDER=1`; on that path a raw `mt5.order_send` with **no halt check and no
token**. Last ungated mutating script. **Gate it or retire it** — your call, argued.

**Hole 4 — a gate tripwire.** Nothing watches the three booleans. Put the check in
`monitor_books.py`/digest so a flip is detected. This is the one that converts "no monitoring" into
monitoring.

## One thing to surface, not solve

The charter's culmination item 6 says *"credentials are absent."* They are **present** today —
authenticated terminals, `trade_allowed` true, in shadow. That is a divergence from the charter the
plan never stated. Write it for Borhen to accept or remediate; do not decide it.

## Deliverables — the floor

1. The carry, as a reviewable diff against the VPS copy, with the deployment-safety proof re-derived.
2. **The owner-executed VPS runbook** — exact steps, exact verification (zero-token status + one healthy
   shadow cycle), and the rollback. Written to be followed by a human on a live funded host at 2 a.m.
3. The four holes fixed, each with a behavioural test that fails against the current code.
4. Token chaos-drill specs written (not run): gate-flip-without-token, expiry-mid-position + fetch error,
   dir unreadable, clock skew, revoke-restore, wrong Windows user. Stage 4 will run them.
5. The charter item-6 divergence, written for the owner.
6. `IMPLEMENTATION_STATE.md` blocks **B100–B109**, and a full-suite A/B by failure set, committed.

Commit scoped work as you go, push your branch, do not merge to `main`.
