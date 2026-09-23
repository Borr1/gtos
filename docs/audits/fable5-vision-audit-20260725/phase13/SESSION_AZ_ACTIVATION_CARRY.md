# Session AZ — the mx_btcusd activation carry, built to the transfer step (wave 13, B1850–B1899)

Read first: `phase5/activation_carry/` (Session T's carry package — MANIFEST with per-file
before/after sha256, build_carry.py, verify_carry.py, ORDERING_AND_PARTIAL_STATES.md — **this
session produces exactly that shape for the new carry**), AU's result §1–§2 (the wiring and
every file it touched), AS's result §0.1/§0.8 (the no-op proof and the adopt-path KeyError
fix), AQ's §1 (the time-stop repair), CLAUDE.md §3–§4. Owner authority: Borhen's standing
approvals — the candidate book activates on the live accounts; and his direct challenge today
that the surface must move.

**The objective in one sentence:** a verified, orderable carry package that takes the host
(host-local) to the state where the orchestrator can run
`--tags ...,mx_btcusd` + `--frontier-exits mx_btcusd` and the book trades the ADMITTED
contract — carrying AS's live KeyError fix in the same package.

## Work orders

**AZ-1 — Enumerate the exact carry set by DIFF, not by assumption.**
The host's files of interest are the phase4/phase5 after-carry bytes (manifests carry their
sha256s) plus nothing since. Mainline has moved. For every file the activation touches —
`run_book.py`, `book_owner.py`, `book_engine.py`, `execution.py`, `execution_packets.py`,
`admission.py`/bridge (AR's DEFAULT_CONFIG key rule!), the market-expansion generator, and
anything AU's §2 lists — produce: host-expected sha256 (from the existing manifests where
applicable), mainline sha256, and the semantic diff between them. Every mainline change riding
along in a carried file must be NAMED and classified (needed for activation / harmless / must
NOT go — e.g. anything whose dependency closure the host lacks). If a file's closure is not
satisfiable on the host lineage, build a minimal port of the needed hunks instead and say so.
The package must also carry **AS's `execution.py` adopt-path fix** — it is a live-crash fix
independent of the activation and rides the same file.

**AZ-2 — The package, in Session T's shape.**
`phase13/activation_carry_mx/`: MANIFEST.json (copy order, per-file before/after sha256,
composes-with declarations for the phase4/phase5 manifests), payload files, diffs, and a
`verify_carry.py` (six-gate shape: postflight bytes, dependency invariants, imports from
`run_book.py`'s own import list, behaviour — including the wired exit resolving `target_5R`
for `mx_btcusd` through `build_book_trade_params` exactly as AU's identity proof did, and the
adopt path rehydrating a `time_stop` position without KeyError). The verifier must run on the
host interpreter (`.venv-gtos`, resolve_repo_root from file location — copy T's discipline).

**AZ-3 — The ceremony page for the orchestrator.**
One page: preconditions already met (probe 7,800 ≥ 7,680 both terminals; seal-membership
answers pinned by AS), the transfer mechanics note (host-admin ≤2,800-char base64 chunks), the
exact tag string (five: the armed four + `mx_btcusd`), the `--frontier-exits mx_btcusd`
supervisor-line edit, sizing statement (registry confidence 0.025 — economically small by
design, per ratified OD-AI-5; sized on recent folds +0.198 R/day per the ratified population
rule), flat-check requirement, flags-held restart order, post-verification lines to expect
(the book must LOG the frontier-exit resolution — say what line proves it), and rollback.

## Done means

Result doc + the package committed, blocks B1850–B1899, scoped A/B green vs the zero
baseline, handoff = the ceremony page. Never touch the VPS (the orchestrator executes);
never run broker-capable scripts; never edit `config/agent_config.yaml`,
`config/profiles/redacted_account.yaml`, or any R2-bound path. The package arms nothing by itself.
