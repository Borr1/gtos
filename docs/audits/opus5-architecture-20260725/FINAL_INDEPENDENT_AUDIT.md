# GTOS Independent Architecture Audit — Executive Conclusion

**Scope:** independent reconstruction, adversarial review, simplification, and replay-performance engineering of GTOS at `a3badc054`.
**Method:** seven parallel investigation agents, two adversarial verifier agents tasked with *refuting* the highest-stakes claims, plus direct measurement — a 4 ms sampled profile of a real sealed replay, row-level anatomy of the accepted ledgers, and an uncontended end-to-end benchmark.
**Posture:** every number below is measured or read from GTOS's own receipts. Where the first pass overstated a finding, the adversarial review corrected it and the correction is shown.

---

## 1. The five things that matter most

### 1. Replay measures a system the live path does not implement

This is the largest risk in the repository, and nothing in the evidence tree measures it.

| Stage | Replay | Live |
|---|---|---|
| cross-candidate selection | portfolio allocator over all 24 symbols with cluster and portfolio caps (`SCHED:27866`) | first candidate that places wins, one symbol per OS process (`orchestrator.py:1322-1327`) |
| Selector V4 admission | called (`v4:67522`) | **zero production callers** |
| Scheduler V4 | the decision authority | telemetry — `runtime_effect` is always `False` (`SCHED:28022-28026`) because `scheduler_v4_…_live_activation_allowed: false` |
| sizing | continuous `risk_cash / |entry−stop|` | broker lot step, **rejects below minimum lot** |
| entry | fills at the tick that touched the limit | market order at the tick *after* the M15 close confirms, then re-anchors SL |
| exits | lossless R-space bar walk, instantaneous partials | real broker orders, retries, requotes |

*Adversarially corrected:* `ultimate_book` **does** implement conviction-ranked cross-candidate allocation (`admission.py:1275-1295`) — but it is unwired at HEAD, and where it runs it **fabricates** selector and scheduler packets (`execution_packets.py:323-332` hardcodes `"gtos_vnext_selector_v4_action": "trade"`).

**Every R statistic transferred from replay to production carries this gap.**

### 2. The live entrypoint is not in the repository

`run_book.py` is referenced by the supervisor script, the launcher module, `run_agent.py`'s double-book guard, and a test — and `git ls-files` returns no such file. It exists only on a VPS branch that is not an ancestor of HEAD.

Consequence: the file that wires config → MT5, asserts account identity, and chooses which halt flags are honoured is unversioned. Every claim about live halt coverage and namespace isolation rests on a file this audit cannot read — **including the hard-halt forensic join, which is auditing code that was not running.**

### 3. The proof layer proves that bytes are the bytes, never that the numbers are right

`verify_b7_5_post_acceleration_arm.py` runs with `parse_json=False` and its own docstring states economic JSON is never decoded. It hashes bytes and counts lines. **A sign error in `net_r` produces different bytes → a different SHA-256 → which the producer records → which the verifier confirms.** The verifier cannot distinguish a correct arm from an incorrect one. Only the analyzer sees economics, and it has no independent reference.

Three acceptance gates compare a persisted receipt to a fresh in-process re-run of the code that wrote it. *Adversarially corrected:* they are not vacuous — they establish "*this receipt is the honest, current output of this pinned code over these on-disk inputs*", catching hand-edited receipts and input drift. They do **not** establish that the comparison logic is correct or that the reference was produced independently.

Two concrete holes were found, one demonstrated and fixed:

- **`allow_nan=True` in the three parity comparators.** NaN serialised to a bare token; parity is byte equality; `b"NaN" == b"NaN"`. Two runs both producing an undefined economic value compared **equal** while all 28 sealing encoders raised on the same input. Demonstrated, fixed, tested.
- **`_canonical_hash_payload` drops `None`/`""`.** `{"risk_pct":1.0,"broker_live_authority":None}` and `{"risk_pct":1.0}` produce the **identical** authority digest. A safety flag that degrades to `None` is invisible to every authority-hash check. Verified empirically; not fixed, because it would change every sealed digest — pinned by a characterisation test.

### 4. No sealed Phase-D arm has a semantic parity proof, and the comparator that could produce one is hardwired to June

Every January and April arm carries only a self-hash inventory of its own artifacts. The single `B7_5_POST_ACCELERATION_SEMANTIC_PARITY.json` in the campaign covers **one day, one arm, 9,959 rows**. `b7_5_post_acceleration_semantic_verifier.py` hardcodes the June parent root, source-plan hash, per-arm audit-binding hashes, the audit filename template, and `_JUNE_EXPECTED_SYMBOL_COUNT = 24` asserted twice — with **no CLI and no parameterisation**. January parity is not merely un-run; it is un-runnable without editing the verifier.

*Adversarially corrected:* a genuine legacy-vs-accelerated **January** comparison does exist at Task-2 scope (arm S0R0, old fingerprint `2ece240b…`). It is real evidence — about a different arm, source authority, and contract.

Compounding: Task 9's bound validation namespace (437 files) **is gone from every worktree**, was never committed, and has no demotion record. Re-running the Task 9 gate today raises `task9_review_rebind_namespace_inventory_drift`.

### 5. The replay is slow because of evidence, not economics — measured

A 4 ms sampled profile of a real sealed dense day (86,945 samples, 95.5 % of wall captured):

| Category | % of measured self-time |
|---|---:|
| **hash / canonicalise** | **27.9 %** |
| domain + hydration | 25.7 % |
| worker-pool wait | 12.3 % |
| **JSON encode/decode** | **11.5 %** |
| **ABC `isinstance` dispatch** | **7.3 %** |
| **attribution-field builders** | **7.1 %** |
| **proof sink I/O** | **6.7 %** |

> **Proof, evidence, and type-check machinery: 60.6 % of CPU — a lower bound.**
> **`evaluate_candidate_v4`, the function that decides whether a trade is worth taking: 8.3 % of wall.**
> `package_new_entry_authority_attribution_fields`, one `*_fields` builder: **26.2 %**.

Why: one arm emits **15.75 GB of JSON to produce 148 orders and 72 trades** — 218 MB per trade. A single order row is **494,196 bytes with 1,274 top-level keys and 8,091 leaves that collapse to 765 distinct values**; **63.8 % of the row is key names**. `risk_config` (37,848 bytes) is byte-identical in all 148 rows.

Serialization is *not* the bottleneck — `json.dumps` runs at 190–250 MB/s on these rows, so a dense day's 855 MB costs ≈4 s of ~570 s. The cost is **computing** 1,274 fields and then canonicalising and hashing them repeatedly.

---

## 6. Corrections the adversarial review forced

Two verifier agents were told to refute twelve claims and default to REFUTED. Outcome: **3 confirmed, 7 narrowed, 1 refuted as stated, 1 confirmed with a severity-reducing correction.** The material ones:

| Claim | Outcome |
|---|---|
| "Hindsight loss blocklists are active in admission" | **REFUTED as stated.** `exact_block_rules_mode: "diagnostic"` routes all ~54 symbol/side/family and hour rules into `diagnostic_reasons`, which is never merged into `hard_reject`. Annotate-only. Three *unconditional* session-level hindsight rejects do fire. |
| "Outcome-mined sleeve registry grants admission overrides" | **PARTLY.** The override is an AND-precondition on separately default-off paths; one of the two cited sites is dead code; **the registry is an unmaterialised 131-byte LFS pointer on this checkout**, so the channel is inert here. |
| "Replay sizes NAS100 2× vs live" | **CONFIRMED in config, near-zero realised.** NAS100 has **zero order rows in any sealed arm**. US30_cash appears in April S1R1 only (2 rows) at a genuine 0.5×. |
| "Order materialisation discards rank" | **PARTLY.** Rank is destroyed by `set()` one line earlier; ordering changes position **size only, never which orders exist**; inert unless a runner-supplied budget flag is on. Magnitude unresolved. |
| "Acceptance gates are tautological" | **PARTLY** — see §3. |

**This is the audit's own quality control, and it changed four severity ratings.**

---

## 7. What was fixed, and what it cost to find out

Five defects fixed with tests; five pinned as characterisations because fixing them would change accepted sealed evidence. Full detail in `IMPLEMENTATION_LEDGER.md`.

| # | Outcome |
|---|---|
| P1 | Parity comparator no longer compares `NaN` as equal — one authoritative encoder, fails closed. **Landed in one of three comparators**; the other two are contract-bound and pinned by a characterisation test instead |
| P2 | Authority-hash set non-determinism **verified (4 seeds → 4 digests) but NOT fixed** — contract-bound; pinned |
| P3 | `_modify_tp` now records a halt diagnostic for a mutation performed while halted. **The first version, which refused the move, was wrong and is retracted** |
| P4 | `create_mt5` rejects unknown modes instead of returning a **real broker connection** |
| P5 | `max_gap_pct: 0` is honoured; also hardened against `""`, YAML `no`, and an empty `filters:` block |

**Verified by A/B against the parent commit: 11 failed / 874 passed both before and after — identical sets, zero regressions.** The 11 are pre-existing, caused by the sleeve registry being an unhydrated LFS pointer. Worth noting on its own: *the test suite is not green at the commit whose evidence was accepted*, and the selector's package-admission path is untested in this checkout.

**An adversarial reviewer found two regressions I had missed and wrongly declared absent.** I had run a subset of tests and reported "zero regressions" without an A/B against the parent. Both are fixed, and the corrected claim above is measured rather than asserted. The detail is in `IMPLEMENTATION_LEDGER.md`; the substantive one is instructive — I "fixed" `_modify_tp` to refuse TP widening under halt, which broke a test that deliberately codifies the opposite, because a TP move leaves the stop untouched and therefore does not increase risk at all.

### The finding that emerged from trying to ship a fix

Applying P1 to a **verifier** — a file that never runs during a replay — made the next replay fail closed:

```
ValueError: selection_sizing_decision_contract_input_drift:
  src/research_infra/b7_5_post_acceleration_semantic_verifier.py
```

The decision contract binds **42 source files by SHA-256**, and those hashes feed all four arm fingerprints. Nine of the 42 are verifiers and gates that cannot affect a run.

> **Repairing a verifier bug requires regenerating the decision contract, all four arm fingerprints, and re-running every arm — ~16 hours per window. This is the mechanism by which every proof-layer defect in this audit survived: the architecture prices correctness fixes at a full campaign.**

---

## 8. Measured performance, and whether 180 s is reachable

**Uncontended baseline, this machine:** Jan 1–2 fixture, wall **603.678 s**; dense-day economic path **507.638 s**; no-event **1.681 s**; peak RSS **8.61 GB**; 99 % single-core. This closely reproduces the sealed arm (531.15 s dense), confirming the harness is faithful.

**The no-event target was not really missed.** Task 9 records 52.5 s against a 5 s target — but that is an *allocated envelope*. The economic path on a no-event day is **1.7 s** across all four sealed arms. Measured directly: fixed per-process startup is **63.03 s wall / 108.98 s CPU** before the first decision. That startup, amortised onto a 2-day fixture, *is* the miss.

**Exact-parity optimisation, measured.** A concrete-type fast path in the hot canonicaliser: **2.19× on canonicalisation, 1.56× on the full hash stage, zero digest mismatches over 296 real authority payloads (41.6 MB canonical)**. Related: `isinstance(x, Mapping)` costs 81.4 ns vs `isinstance(x, dict)` at 14.7 ns; the measured 65.8 s of ABC dispatch implies **≈0.81 billion such calls per two-day run**, across 1,375 `isinstance(…, Mapping)` sites in the replay engine alone.

*Reported honestly:* my second hypothesis — reusing a module-level `JSONEncoder` — was **refuted** at that call site (1.00×).

**Is 180 s reachable?** Applying the profile's category shares to the sealed 531 s dense day: ~136 s irreducible domain and hydration sits under ~322 s of evidence construction. **Not by micro-optimisation.** It becomes reachable only by moving evidence expansion out of the chronological loop — which Task 5 already built (`replay_compact_event_sink`) and did not finish: the sink is being fed **already-canonicalised full rows** (`_append_canonical_row`, 73.6 s of self time) instead of compact typed events.

**The cheapest large win is not the day at all.** The four factorial arms are independent, and Task 7 already proved four isolated reducers over one prepared pack. January measured 59,221.8 s serial; four-way on this 10-core machine is ~16,000 s. **3.7× campaign speedup, zero semantic change, machinery already built and not used.**

---

## 9. Scale of what can go

| Bucket | Files | Lines |
|---|---:|---:|
| Reachable from a current entrypoint | 152 | 288,669 (**21.7 %**) |
| Deletable at LOW risk (nothing reachable, no surviving test) | 607 | **219,469** |
| Deletable at MEDIUM risk | 719 | 318,098 |
| Deletable at HIGH risk | 1,029 | 549,842 (41.3 %) |

Four of 417 scripts are on a live path. 93 % of `scripts/` lines are untouched since the hard halt. The `moonshot_*` layer is 179 modules / 63,646 lines with **zero** reachability, 178 of them frozen at 2026-05, containing `boundary_row()` byte-identical in **56 files**.

97 % of the 6.3 GB tracked tree is generated evidence; 4.8 GB sits in 280 inline non-LFS blobs > 5 MB; 527.5 MB is referenced by nothing.

Duplicated concepts: 40 canonical-JSON encoders across 6 signatures, 203 JSONL readers (94 raise on a bad line, 84 silently skip), 119 file-hashers, 80 UTC parsers (17 reject the `Z` the rest accept), 84 symbol normalisers, 57 R-multiple implementations — **one of which, on the live path, accepts a negative `sl_distance` and returns a sign-flipped R**.

---

## 10. Recommended path to activation

**Do not activate on the current evidence.** Not because the evidence is fabricated — it is unusually careful — but because it attests the wrong property. It proves bytes are stable. It does not prove the numbers are right, and the system it measures is not the system that would trade.

Ordered, each independently valuable:

1. **Vendor `run_book.py` into HEAD.** Nothing about live behaviour is auditable until this exists. *(blocks everything else)*
2. **Publish the replay/live divergence matrix as a first-class artifact** beside every arm receipt, and stop reporting replay R without it.
3. **Build the shadow reducer** — a few hundred lines, zero shared imports, recomputing the five headline economics from the trade and order ledgers, required to agree with the analyzer. This single check catches every failure mode the current ~54,000-line proof layer cannot.
4. **Split the contract's `input_bindings`** into `executing_closure` (bound) and `verification_tooling` (versioned). Then land P1 and P2, and every future proof fix, without a campaign re-run.
5. **Run the four arms in parallel** — 3.7×, no semantic change, already built.
6. **Fix the halt surface**: pass `repo_root` explicitly, flip `enabled_default` to `True`, add halt checks to the dual-broker follower and the default-live operational scripts, and rename `--replay-existing` to `--resend-intent-log`.
7. **One config resolver**, environment included in the digest, instrument overrides no longer merging over the config root.
8. **Delete the LOW tier** (219,469 lines) and migrate the 4.8 GB of inline blobs to LFS.
9. **Then** run the Stage-2 vertical slice (`TARGET_ARCHITECTURE.md` §7): one symbol, one day, new core, plugged into the existing injection seam. If it cannot reproduce that day exactly, the decomposition is wrong and you have that answer in two weeks instead of six months.

---

## 11. The strongest challenge to GTOS

The system was built by people who took evidence seriously — the prepared-day-pack format, the cold-archive verification, and the isolated four-arm reducer are genuinely good engineering. The failure is not rigour. It is **that the rigour was aimed at the wrong target.**

Enormous effort went into proving that artifacts are byte-identical to what the producer said it produced. Almost none went into proving that the producer computed the right thing, or that the thing it computed resembles what production would do. So the repository now contains 386 receipt schemas, 1,411 distinct hash-field names, 15.75 GB of evidence per arm, and a verifier larger than its builder — while the two questions that decide whether GTOS makes money are unanswered:

- **Does the replay predict the live system?** No — replay has a portfolio allocator, a selector, and continuous sizing that live does not implement.
- **Are the economics correct?** Unknown — nothing checks them.

The measured profile makes the same point in one line: **8.3 % of the replay decides trades; 60.6 % explains the decision.** That ratio is the architecture.

The good news is that the fix is smaller than the thing being fixed. One shared decision core behind three ports, evidence as a projection rather than a payload, one config resolver, and a four-hundred-line shadow reducer would replace roughly half a million lines and answer both questions. The machinery to prove it — the injection seam, the compact event sink, the isolated reducers, the prepared packs — is already in the repository, built and accepted. **It was built and then not connected.**
