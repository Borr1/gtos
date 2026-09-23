# Target Architecture

**Designed from the invariants, not from the current decomposition.** Every choice below is justified by a measured fact in `REPLAY_TRUTH_AND_PERFORMANCE_AUDIT.md` or an evidenced finding in `MISMATCH_AND_RISK_REGISTER.md`.

---

## 1. What GTOS actually has to guarantee

Strip the vocabulary away and there are seven real requirements:

| # | Invariant | Currently protected by | Is that protection real? |
|---|---|---|---|
| I1 | A decision at time *t* uses only information available at *t* | `PRIMARY_DECISION_TIMEFRAMES` excludes M1/TICK (`v4:315-317`), `closed_bar_rows_until`, `PathTruthIndex(until=asof)` | **Yes for time-slicing.** No for provenance: the boundary is a string denylist (`SCHED:6864-6926`) and `no_leak_status` is a hardcoded `"pass"` everywhere |
| I2 | The same inputs produce the same outputs | 40 canonicalisers, 386 receipt schemas, three recompute gates | **Mostly.** Two holes found and fixed/flagged: `allow_nan=True` in the parity encoders; sets → `PYTHONHASHSEED`-dependent authority digests |
| I3 | Replay predicts live | naming, and nothing else | **No.** Replay has a portfolio allocator, a selector, continuous sizing and lossless exits; live has none of those |
| I4 | Money cannot move when halted | `enforce_runtime_not_halted` on most paths | **No.** `_modify_tp` was unguarded (fixed); the guard is `default=False` and CWD-relative; the follower has zero halt references |
| I5 | Configuration in force is knowable | `.context/LIVE_STATE.md`, execution seals | **No.** Live risk comes from a Python constant (`admission.py:775`); three economics-changing env vars appear in no seal |
| I6 | Evidence is complete and unaltered | inventory closure + self-hash + cold demotion | **Partially.** Byte binding is real; the *input set* is chosen by the producer, and 454 MB were relocated out of a namespace so closure would pass |
| I7 | A result can be reproduced | absolute-path seals, month-granular windows | **No.** Not on another machine, not from another checkout, not for a sub-window, and Task 9's bound namespace is gone |

**The target architecture exists to make I3, I4, I5 and I7 true, and to make I1, I2 and I6 provable by something other than the code that produced them.**

---

## 2. The minimal trusted core

```
┌──────────────────────────────────────────────────────────────────┐
│                     gtos.core  (~6–8k lines)                     │
│  Pure. No I/O. No clock. No broker. No filesystem. No hashing.   │
│                                                                  │
│   MarketState  ──►  generate_candidates  ──►  [Candidate]        │
│   [Candidate] + AccountState  ──►  select  ──►  [Selected]       │
│   [Selected]  + AccountState  ──►  size    ──►  [SizedOrder]     │
│   SizedOrder  + Fill          ──►  lifecycle ──► [Event]         │
│   [Event]     + AccountState  ──►  reduce  ──►  AccountState'    │
└──────────────────────────────────────────────────────────────────┘
            ▲                    ▲                     ▲
            │ Clock              │ Broker              │ Sink
   ┌────────┴────────┐  ┌────────┴────────┐  ┌─────────┴─────────┐
   │ ReplayClock     │  │ SimulatedBroker │  │ EventSink         │
   │ WallClock       │  │ MT5Broker       │  │ (typed, append)   │
   └─────────────────┘  └─────────────────┘  └───────────────────┘
```

Three ports, three pairs of adapters. **Replay and live differ only in which adapter is bound.** That is the entire fix for I3.

Everything currently in `finalize_scheduler_risk_admitted_selection` (8,750 lines), `build_runtime_risk_authority` (5,065), `materialize_scheduler_window` (3,958) and `simulate_order` (4,286) splits into two parts: the decision (small, in `core`) and the explanation of the decision (large, in `evidence`). The measured split says the second is ~4× the first.

### Why this is credible, not aspirational

The seam already exists. `run_campaign:90494-90499` injects `candidate_evaluator=evaluate_candidate_v4` and `scheduler_allocator=materialize_scheduler_window` as function references into `V4DecisionCycleCore`. A replacement core plugs in there without touching the monolith. That is the vertical-slice attachment point.

---

## 3. Evidence as a projection, not a payload

**The measured problem.** An order row is 494,196 bytes with 1,274 top-level keys and 8,091 scalar leaves that collapse to **765 distinct values**; **63.8 % of the row is key names**. `risk_config` (37,848 bytes, 198 keys) is byte-identical in all 148 rows. One arm emits 15.75 GB to produce 72 trades. Proof/canonicalise/encode/attribute is **60.6 % of measured CPU**; `evaluate_candidate_v4` is **8.3 %**.

**The target.** The chronological loop emits **typed events only** — a fixed-width struct per decision, order, fill, exit. Everything else is derived afterwards, out of the hot path, from those events plus the window-scoped constants.

```
hot path            :  Event{kind, ts, symbol, candidate_id, refs…}   ~200 bytes
window constants    :  emitted ONCE per window, referenced by id
evidence projection :  a separate pass that expands events → ledgers
```

Concretely:

| Today | Target |
|---|---|
| `risk_config` inlined in all 148 order rows (5.6 MB) | emitted once per campaign, referenced by `risk_config_id` |
| `predecision_stop_hazard_guard` written into two dicts (`SCHED:14693-14694`) and serialised twice | one object, one reference |
| `_append_canonical_row` expands to canonical JSON inside the loop (73.6 s self time) | append a typed record; expand offline |
| 1.94 MB scorecard rows | scorecard is a *view* over events |

**This is not a new idea in this codebase — it is the idea Task 5 already implemented and then did not finish.** `replay_compact_event_sink` exists and is accepted as "an enabling proof-transport primitive". The measurement shows why it did not pay off: the sink is being fed **already-canonicalised full rows** (`_append_canonical_row` at 73.6 s), so the expansion still happens inline. Feeding it compact typed events is the missing half.

---

## 4. One configuration resolution, sealed with the run

Today: `agent_config.yaml` → profile → instrument overrides (which merge over the config *root*, inverting the kill switch), plus a Python constant that actually governs live sizing, plus three env vars that override YAML and appear in no seal, plus a replay-only profile pin.

Target:

```
resolve_config(profile, symbol, env) -> FrozenConfig      # one function, one order
FrozenConfig.digest                                        # includes env
```

Rules:
1. **One resolver.** Every entrypoint calls it; nothing reads YAML directly.
2. **Instrument overrides merge into `instruments.<sym>`, never into the root** — this alone fixes R11.
3. **The environment is part of the digest.** `GTOS_PROFILE`, `GTOS_UB_DERISK_MODE`, `GTOS_DUAL_BROKER_INTENT_ENABLED` change economics; a seal that omits them is not a seal.
4. **No behavioural constant outside config.** `ALLOCATION_PROFILES[...].risk_per_unit = 0.020` moves into the resolved config or the config becomes documentation.
5. **Replay and live resolve identically.** The `timewarp_replay_risk_profile_path` pin disappears; replay takes the profile it is asked to model.

---

## 5. Proof that is smaller and stronger

The current layer establishes exactly three properties, at ~54,000 lines, 386 schema names, and 1,411 distinct hash-field names.

| Property | Minimal mechanism | Replaces |
|---|---|---|
| P1 — these bytes are what the run produced, with nothing added or removed | one `MANIFEST.json` per namespace: `{run_id, config_digest, source_digest, engine_commit, files[], excluded[], manifest_sha256}` + one CLI that rehashes the directory | arm receipt, artifact inventory, arm independent verification, cold manifest, and the producerless demotion receipts. **`excluded[]` is the honest form of what is today a post-hoc prune** |
| P2 — the configuration was frozen before the run | one `SEAL.json`: `{config_digest, source_digest, engine_commit, window, options}` + git for code identity | six digests over the same frozen dict; the 42-file input binding |
| P3 — the archive decompresses to the original | keep `b7_5_cold_evidence.py` verbatim — it is the one genuinely load-bearing piece | delete the four "reverification" fields that are dict re-projections, not re-reads |

**And add the one thing that does not exist:** a **shadow reducer** — a few hundred lines, zero shared imports with the engine — that recomputes the five headline economics (`scoreable_net_cash`, `total_accepted_risk_cash`, `physical_net_r`, `trade_count`, `scoreable_risk_coverage`) directly from the trade and order ledgers, and must agree with the analyzer.

That single check catches every failure mode the current 54,000 lines cannot: an engine that computes the wrong economics, a `None`-elided authority flag, a non-deterministic digest, a NaN accepted by one canonicaliser and refused by another. **The current stack verifies that bytes are the bytes. Nothing verifies that the numbers are right.**

### Break the circular binding

Bind only what executes. Verifiers, gates and acceptance modules are **versioned, not sealed into the execution contract**. A verifier bug then costs a verifier release, not a campaign re-run.

---

## 6. Reproducibility

| Defect | Fix |
|---|---|
| absolute paths in seals (`fresh_source_authority_path_binding_mismatch`) | seals record **content digests and repo-relative paths**; the root is a runtime argument |
| `ATTEMPT5_RUNTIME_EVIDENCE_ROOT = /Users/borr/GTOSActive/repo` (`attempt5:186`) and the `~/Documents/…` tick manifest (`:187-190`) | resolved from config; the four off-checkout decision inputs are vendored or submoduled at a pinned commit — today they sit in a sibling checkout at a **different commit** than the code consuming them |
| no sub-window replay (three independent assertions) | the window is an input; the *source-plan digest is computed over the requested window*, and the seal records a per-day root set that a sub-window must be a **subset** of, not equal to |
| Task 9's bound namespace is gone, and re-running the gate now raises `task9_review_rebind_namespace_inventory_drift` | acceptance binds a manifest digest, and the manifest is retained; artifacts may be cold-demoted but the demotion is recorded and reversible |

---

## 7. Migration — four stages, each independently valuable

Each stage keeps the current green semantic baseline. No stage requires the next.

### Stage 0 — free wins, no semantic change (days)
- Exact-parity performance fixes: concrete-type fast path in the hot canonicalisers (**measured 2.19×** on `_canonical_hash_payload`, exact digests over 296 real payloads), `query_cache` on the three execution-path `path_source_and_oracle` calls.
- **Run the four arms in parallel.** Task 7 already proved four isolated reducers over one prepared pack. January measured 59,221.8 s serial; four-way on this 10-core machine is ~16,000 s wall. **3.7× campaign speedup, zero semantic change** — the single cheapest large win available, already built and not used.
- Safety: the halt/mode/config fixes already landed in this audit branch.
- Delete the LOW tier (219,469 lines) — nothing reachable.

### Stage 1 — one config resolver (1–2 weeks)
Introduce `resolve_config`, route every entrypoint through it, put the environment in the digest, fix the instrument-override inversion, retire `timewarp_replay_risk_profile_path`. **Verification:** replay every accepted arm and require identical ledgers except where the profile pin genuinely changed sizing — which is the point.

### Stage 2 — vertical slice of the new core (3–4 weeks)
Implement `gtos.core` for **one symbol, one day**, plugged into the existing `V4DecisionCycleCore` seam at `run_campaign:90494-90499`. Run it beside the monolith on the sealed January pack. **Falsification criterion:** if the slice cannot reproduce that day's orders and trades exactly, the decomposition is wrong and the migration stops. That is a two-week answer to a question currently worth months.

### Stage 3 — evidence as projection (4–6 weeks)
Emit typed events from the loop; build ledgers offline from events + window constants. **Verification:** the offline projection must reproduce the existing ledgers byte-for-byte (Task 5's reconstruction test already does exactly this for the compact sink). Then the 180 s dense-day target becomes arithmetic rather than aspiration.

### Stage 4 — collapse the proof layer (2–3 weeks)
`MANIFEST` + `SEAL` + cold archive + shadow reducer. Delete the recompute gates and the producerless receipts. Unbind verifiers from the execution contract.

---

## 8. "Optimise the current system" vs "replace the dominant path"

| | Optimise in place | Replace the dominant path |
|---|---|---|
| dense day | ~570 s → ~480 s (Stage 0 only) | ~570 s → ~150–250 s (Stages 0+3) |
| campaign wall | 16.4 h → 4.4 h (parallel arms) | 4.4 h → ~1.5 h |
| lines removed | ~219k (dead only) | ~550k |
| replay/live gap | unchanged — **still the largest risk** | closed by construction |
| proof strength | unchanged | numbers verified, not just bytes |
| risk | very low | staged, with an explicit falsification gate at Stage 2 |

**Recommendation: do Stage 0 now, unconditionally.** It is measured, exact-parity, and includes a 3.7× campaign speedup that requires no semantic change at all. Then run Stage 2 as a two-week bet whose failure is cheap and informative.

Do **not** start Stage 3 or 4 before Stage 2 answers whether the decomposition holds.

---

## 9. What is deleted, merged, kept

| Action | Target |
|---|---|
| **Delete** | 219,469 lines LOW tier now; 179 `moonshot_*` modules; the 16 TEST_ONLY `replay_acceleration_*` rungs; the four dict-re-projection "reverification" fields; the three recompute gates; the 14 producerless receipt schemas; 527.5 MB of unreferenced artifacts |
| **Merge** | 40 canonicalisers → 1 (**done**); 203 JSONL readers → 2; 119 file-hashers → 1; 80 time parsers → 1; 57 R-multiple → 1; 84 symbol normalisers → 1 |
| **Replace** | arm receipt + inventory + independent verification + cold manifest → `MANIFEST`; six seal digests → `SEAL`; per-row inlined authority → window-scoped constants + references |
| **Isolate** | verifiers out of the execution contract; proof generation out of the chronological loop |
| **Keep verbatim** | `b7_5_cold_evidence.py` archive verification; the four-arm isolated reducer (Task 7); the prepared-day-pack format (the strongest layer in the stack — manifest root + `SEALED` + shard sha + raw sha + per-record sha); `replay_compact_event_sink` |
| **Build new** | `resolve_config`; the shadow reducer; `gtos.core` |
