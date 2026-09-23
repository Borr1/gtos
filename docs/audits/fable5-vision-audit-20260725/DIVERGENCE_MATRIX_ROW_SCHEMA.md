# Live-divergence row schema — v1

**Owner: Session F (`phase1/divergence-matrix`), 2026-07-26.** Published under the Wave-2 tiebreak rule
(`phase1/SESSION_F_DIVERGENCE_MATRIX.md` §"Coordination with E"): *whoever pushes a schema first owns it;
the other adapts.* Session E had not pushed one at the time of writing — verified against
`origin/phase1/w7-forensics` (ref absent) and the local `phase1/w7-forensics` tip
(`dddc2627a`, no new commits). **Session E: adopt this, or tell Borhen why it cannot carry your rows and
I will amend it.** Amendment is cheap; a second schema is not.

The machine-readable form of this document is `src/research_infra/divergence_matrix.py`. Where the two
disagree, the code is authority and this file is stale — say so rather than editing around it.

---

## 1. What a row asserts

Exactly one thing, and it is a *comparison*, not a description:

> On dimension **X**, the sealed replay path does **A**; the live path does **B**; substituting a replay
> number for a live number on this dimension is wrong by **C**.

If a row cannot name both sides, it is not a divergence row — it is a note, and it belongs somewhere else.
If it can name both sides but not `C`, it is still a row: it is emitted with
`quantification.status = "UNQUANTIFIED"` and it is **louder**, not quieter, for being unquantified.

## 2. The one rule that makes this survive

**Every row is either `DERIVED` or `DECLARED`, and the two never look alike.**

- `DERIVED` — the value was read at generation time from a file, config key, or sealed artifact, and the
  row carries that source's path *and* its `sha256`. A `DERIVED` row is reproducible: re-run the
  generator against the same bytes and you get the same row.
- `DECLARED` — a human asserted it. It carries `owner`, `declared_utc`, `justification`, and
  `review_by`. It is rendered with a `[DECLARED]` marker in every output format.

A hand-typed value that looks derived is the failure this schema exists to prevent. There is no third
mode; a row with neither is a generator bug and raises.

## 3. Row fields

```jsonc
{
  "row_id": "E1.PORTFOLIO_ALLOCATOR",   // stable. <FINDING>.<DIMENSION>, SCREAMING_SNAKE after the dot.
  "family": "execution_model",          // see §4
  "finding": "E1",                      // audit finding ID this descends from, or null if newly found
  "dimension": "Portfolio allocator",   // short human name, <= 60 chars

  "replay_behavior": { "value": "...", "locator": "file:line or config key" },
  "live_behavior":   { "value": "...", "locator": "file:line or config key" },

  "direction": "REPLAY_ONLY",           // see §5 — UNKNOWN is legal and is the fail-closed value
  "transfer_risk": "BLOCKS_TRANSFER",   // see §6

  "quantification": {
    "status": "UNQUANTIFIED",           // QUANTIFIED | UNQUANTIFIED | NOT_APPLICABLE
    "metric": null,                     // e.g. "delta_R_per_arm"
    "value": null,
    "unit": null,
    "source": null                      // path to the artifact carrying the number
  },

  "derivation": {
    "mode": "DERIVED",                  // DERIVED | DECLARED
    "rule": "config_surface_diff",      // name of the generator function that produced it
    "sources": [                        // DERIVED only, non-empty, each with a hash
      { "path": "config/agent_config.yaml", "sha256": "…", "locator": "gtos_vnext_runtime.selector_v4_apply_to_execution" }
    ],
    "owner": null,                      // DECLARED only
    "declared_utc": null,               // DECLARED only
    "justification": null,              // DECLARED only
    "review_by": null                   // DECLARED only
  }
}
```

`replay_behavior` / `live_behavior` are **symmetric**. A row that only exists on one side still fills
both: the absent side takes `value: "<not implemented>"` with a locator proving the absence was looked
for, not assumed. *An empty result from a probe that cannot see the thing is indistinguishable from a
genuine absence* — the locator is where you show the probe worked.

## 4. `family` — the partition

| family | Owner | What it covers |
|---|---|---|
| `execution_model` | F | Replay runs machinery the live path does not, or vice versa (E1) |
| `strategy_family` | F | Replay measures one book; live declares another (F1) |
| `clock` | F | Timebase, DST calendar, session labelling, day boundary (F7) |
| `data` | F | Input archive differences: symbol specs, contract sizes, tick source |
| `live_only` | **E** | Behaviour observable only on the live host — the W7 forensics row set (G1b) |

`live_only` is reserved for Session E and the generator does not populate it. E's rows arrive as a
JSON file the generator merges; see §8.

## 5. `direction`

| value | Meaning |
|---|---|
| `REPLAY_ONLY` | Replay does it, live does not |
| `LIVE_ONLY` | Live does it, replay does not |
| `BOTH_DIFFERENT` | Both do it, differently |
| `EQUIVALENT` | Both do it, provably the same — requires a `DERIVED` row on both sides |
| `UNKNOWN` | Could not be classified. **This is the fail-closed value.** |

Borrowed deliberately from Session D's differential harness, and it inherits D's rule: **`EQUIVALENT`
requires that nothing was unknown.** A row cannot be `EQUIVALENT` with a null locator on either side.

## 6. `transfer_risk`

What this divergence does to the sentence *"replay R therefore live R"*.

| value | Meaning |
|---|---|
| `BLOCKS_TRANSFER` | The replay number is not a live number on this dimension, full stop |
| `BOUNDS_TRANSFER` | Transfer is possible with a stated correction or bound |
| `INFORMATIONAL` | Known, measured, and does not move the economics |

## 7. Matrix-level verdict

The matrix carries a single `transfer_verdict`, and it is computed, not written:

- `REPLAY_R_IS_NOT_A_LIVE_CLAIM` — any row is `BLOCKS_TRANSFER`, `UNKNOWN`, or `UNQUANTIFIED`.
- `TRANSFER_BOUNDED` — no blocker, no unknown, no unquantified; at least one `BOUNDS_TRANSFER`.
- `TRANSFER_UNOBSTRUCTED` — every row `EQUIVALENT` and `QUANTIFIED` or `NOT_APPLICABLE`.

Today the answer is `REPLAY_R_IS_NOT_A_LIVE_CLAIM` and it will stay that way for a long time. That is
the correct answer, not a defect in the matrix.

## 8. How Session E's rows arrive

E writes one JSON file, `family: "live_only"` on every row, conforming to §3:

```
docs/audits/fable5-vision-audit-20260725/receipts/live_divergence_rows_w7.json
{ "schema": "gtos.divergence_matrix.live_rows.v1", "rows": [ … ] }
```

The generator merges it if present. **If it is absent the generator does not fail — it emits a single
`UNKNOWN` row saying the live row set was not supplied**, which propagates to
`REPLAY_R_IS_NOT_A_LIVE_CLAIM` through §7. Missing evidence is a loud unknown, never a silent pass.
E is therefore never a blocker for F, and F is never a reason for E to rush.

## 9. Completeness — the part that stops it going stale

A matrix that lists the divergences someone remembered is a document. The mechanism is the **residual
row**: the generator diffs the entire replay-vs-live config surface, maps every differing key onto a
row, and emits any key it could not map into `UNCLASSIFIED_CONFIG_DIVERGENCE` with `direction: UNKNOWN`.

So a divergence introduced next month by someone who never read this file still appears — as an unknown,
which blocks transfer, which is exactly the behaviour wanted. The alternative (drop unmapped keys) makes
the matrix *look* complete while decaying, which is the failure mode this whole artifact exists to stop.
