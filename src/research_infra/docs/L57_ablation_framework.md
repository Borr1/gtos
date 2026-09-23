# L57 — Edge-Component Ablation Framework

Phase 1 research-program task L57. Provides one canonical mechanism
for "drop a single edge component and measure the delta", reusable by
Phase 2 B10 (prompt ablation matrix) and several Phase 1 follow-ups.

The framework is **additive only** — production trading code
(`src/components/`), production prompts (`prompts/`), and production
config (`config/agent_config.yaml`) are read-only inputs. Ablated
prompts are written exclusively under the run's `output_dir`.

---

## When to use ablation vs. A/B

| Situation | Use |
|---|---|
| Compare two specific prompts (e.g. V3 vs V4 candidate) | **A/B** — run `prompt_ab_harness.py` directly. |
| Measure the *individual* contribution of N components inside ONE prompt | **Ablation** — author a manifest with N entries, run `ablation_runner.py`. |
| Synthesize ablation findings across multiple prompts | Ablation per prompt + cross-comparison spreadsheet. |
| Test a single, post-hoc hypothesis after seeing results | **Neither** — that's CLAUDE.md prohibited behavior #5 (post-hoc hypothesis formation). |

Ablation is N parallel A/B comparisons against the same baseline; A/B
is one comparison. The ablation framework subprocesses to
`prompt_ab_harness.py` per manifest entry, so realized-R join,
Bonferroni correction, and walk-vs-realized splits are inherited from
L56 — no metric logic is re-implemented here.

---

## Pre-registration discipline

The manifest filename + content are hashed into the run report's
`run_hash`. Editing a committed manifest and re-running on the same
baseline produces a different run hash; review tooling can detect the
change.

To run fresh ablations without breaking the audit trail:

1. **Do NOT edit** an existing committed manifest after running it.
2. **Do** copy the manifest to a new filename (e.g.
   `ablation_default_v2.yaml`).
3. **Update** `manifest_set_id:` inside the new file to a unique value
   (e.g. `ablation_default_v2`).
4. Commit the new manifest BEFORE running. The run hash now reflects
   the new file's identity.

The pre-registration sentinel test in
`tests/scripts/test_ablation_runner.py` pins the SHA of
`ablation_default_v1.yaml`. If you change the file, the test fails —
prompting you to either commit a new `_v2.yaml` (the right move) or
update the sentinel deliberately.

---

## Walk-level vs. realized-R requirement

The framework emits **both** walk-level metrics (CR rate delta,
McNemar p, decision-flip sign test) **and** realized-R metrics
(paired t / Wilcoxon on `R_baseline - R_ablation`, plus per-prompt
WR Wilson intervals).

Per memory `feedback_walk_level_evidence_not_predictive.md`, walk-level
deltas are NOT predictive of realized R. Session 39 evidence:
Track A walk p=5e-16 on touch-count decay REVERSED under A1 realized-R
(touch=2 Exp +0.30R > touch=1 +0.04R). Reading walk-level results as
edge evidence is a known reproducible failure.

The framework therefore enforces a hard rule:

- If `--realized-r-join` is **NOT** provided, the runner emits walk-level
  metrics in `ablation_summary.json` but adds:
  ```
  "verdict_suppressed": "realized_r_join_not_provided",
  "verdict_note": "Walk-level deltas are NOT predictive of realized R..."
  ```
  Reviewers who want a verdict must re-run with the realized-R join.

- If `--realized-r-join` IS provided, both metric families are emitted
  side-by-side. The Markdown report also surfaces the
  Bonferroni-corrected significance flag from
  `realized_r_paired_t` so reviewers can read the headline number
  directly.

---

## Worked example: did dropping cross_instrument_context move expectancy?

```
# 1. Pin the manifest. ablation_default_v1.yaml has the
#    drop_cross_instrument_context entry with heading
#    "Cross-Instrument Context".

# 2. Stage the realized-R index. Trade records corpus is the right
#    source — A2 v2-active backtest already populated it.
python scripts/research/ablation_runner.py \
    --baseline-prompt prompts/short_validation_batch_prompt.md \
    --manifest scripts/research/manifests/ablation_default_v1.yaml \
    --fixtures historical_cands \
    --metrics scripts/research/metrics/prompt_ab_default.yaml \
    --realized-r-join knowledge_base/trade_records \
    --output research/ablation_v1_run1 \
    --seed 1

# 3. Open the report.
#    research/ablation_v1_run1/ablation_report.md
#
#    Look for the row:
#       drop_cross_instrument_context  drop_section  ...
#                                                 ^^^ realized-R Δ (mean) and p
#    plus the Bonferroni-corrected significance flag.

# 4. Read the per-entry detail.
#    research/ablation_v1_run1/ablation_summary.json["ablations"][1]
#       .realized_r_metrics.realized_r_paired_t
```

If `realized_r_paired_t.significant_corrected` is `false`, the
ablation does NOT measurably move expectancy at family-wise α=0.05.
Walk-level CR/McNemar moves alone are NOT a verdict — they're a system
signal that the AI noticed the missing context, nothing about edge.

---

## Anti-pattern: post-hoc manifest editing

```
# WRONG.
git add scripts/research/manifests/ablation_default_v1.yaml   # edited
# After seeing that drop_kill_zone_schedule had p=0.04 raw but p=0.16
# Bonferroni-corrected, the author swaps in a "drop only NY kill zone"
# entry to chase the residual signal. This is post-hoc hypothesis
# formation — banned by CLAUDE.md #5.

# RIGHT.
cp scripts/research/manifests/ablation_default_v1.yaml \
   scripts/research/manifests/ablation_kz_focused_v1.yaml
# Edit the new file. Update manifest_set_id to ablation_kz_focused_v1.
# Commit. Re-run with --manifest pointing at the new file.
```

The framework cannot fully prevent this — it can only make it
detectable. The committed `manifest.sha256` and `run_hash` in
`ablation_summary.json` show the manifest at run time; reviewers
compare against `git log` for that path.

---

## Transformation reference

| transformation | params | scope | notes |
|---|---|---|---|
| `drop_section` | `heading: <str>` | prompt | Bounded by `## ` heading line through next `## ` or EOF. Heading match is on literal text. |
| `drop_framework` | `framework: <str>`, `target_file: <path>` | prompt + (Phase 2: agent_config.yaml) | Wave 1 strips lines mentioning the framework name from the PROMPT. Canonical `enabled_frameworks` edit lives in `agent_config.yaml`; full impl is Phase 2. |
| `drop_gate` | `gate: <str>` | prompt + (Phase 2: permissions.py) | Wave 1 strips sentences mentioning the gate name from the PROMPT. Canonical gate removal requires re-wiring `permissions.py`; Phase 2. |
| `replace_text` | `find: <str>`, `replace: <str>` | prompt | Literal find-replace. Empty `find` rejected. |
| `regex_remove` | `pattern: <regex>` | prompt | Sandboxed: rejects look-around and nested unbounded quantifiers. Compiled with `re.MULTILINE`. |

### Wave 1 limitations

`drop_framework` and `drop_gate` are accepted by the manifest schema
but operate on PROMPT TEXT only. The canonical removals require:

- `drop_framework`: edit `agent_config.yaml`'s
  `model_a.enabled_frameworks` list and re-run the orchestrator. The
  pre-AI POI helper, L2 verifier, and shadow loggers all have to be
  staged in lock-step. Phase 2 work — see CEO note in CLAUDE.md.
- `drop_gate`: edit `src/components/permissions.py` to remove the
  gate's branch and recompile. Likewise Phase 2.

Wave 1 prompt-only ablation tests "does the AI notice the missing
mention?", which is *related to* but not the same question as "does
removing the gate change realized R?". Documenting this gap up-front
prevents reviewers reading Wave 1 results as if they were Phase 2
results.

---

## Output layout

```
<output_dir>/
  ablation_summary.json       # aggregated, all entries
  ablation_report.md          # human-readable table
  ablated_prompts/
    drop_ob_zone_section.md   # one per manifest entry
    drop_cross_instrument_context.md
    ...
  harness_runs/
    drop_ob_zone_section/
      results.jsonl           # from prompt_ab_harness
      metrics_report.json
      decision_diff.md
      run_metadata.json
    ...
```

`ablation_summary.json` is the single artifact downstream consumers
should depend on. It contains the manifest run-hash, baseline prompt
hash, fixtures spec, realized-R join state, and one entry per
ablation with both walk-level and realized-R metrics.

---

## Cost note

Wave 1 default is **mocked** — the harness `evaluate_pair` runs the
deterministic mock decision engine. No Anthropic API calls are made.
A 10-entry manifest × 75-fixture canary = 1500 mock evaluations,
runtime ≈ a few seconds.

Real-API runs are gated behind `--live` (forwarded to the harness).
Per-fixture cost on Sonnet 4.6 effort=max is ~$0.03; a 10-entry × 75
fixture run is ~$22. CEO authorization required (CLAUDE.md prohibited
#3 and the $50/mo cap).
