# Session 29 Close Handoff — 2026-04-19

**Session focus:** Ship T1.3.1 (canary PASS-threshold regression discovered during T1.3 cold review) end-to-end. Chose Option C (tiered thresholds) over CEO-offered A/B, dispatched impl + cold-review agents, absorbed cold-review nits directly, finished with a clean doc sweep.

---

## First actions for the fresh session

1. Read `CLAUDE.md`.
2. Run `python scripts/generate_live_state.py` → read `.context/LIVE_STATE.md` (authoritative current state).
3. Read this file for session-29 delta.
4. Wait for CEO direction before touching files.

**Trust rule (unchanged):** if any handoff/backlog/ADR disagrees with `LIVE_STATE.md` or `git log`, the code/git is correct and the doc is stale — update the doc in the same commit.

---

## What session 29 shipped (2 commits, local only — repo now 2 commits ahead of `origin/main`)

| SHA | Scope |
|-----|-------|
| `2d500f1` | fix(canary): tiered PASS_THRESHOLDs restore drift sensitivity (T1.3.1) |
| `ac9bad7` | fix(canary): rename BORDERLINE_PREFIX, drop stale pass_threshold, add CLI smoke test |

Do not push without CEO approval.

### Commit detail

**`2d500f1` — T1.3.1 core (Option C)**
- `scripts/canary_test.py` refactored. Hardcoded `PASS_THRESHOLD = 10` replaced with derived per-tier thresholds.
- Public helpers exposed: `classify_fixture_label(label)` (prefix-based), `categorize_labels(labels)`, `derive_thresholds(baseline_count, borderline_count)`, `evaluate_tiered_pass(details, keyword_drifts, baseline_labels=None, borderline_labels=None)`.
- Policy constants: `BASELINE_ALLOWED_FLIPS = 1`, `BORDERLINE_MATCH_FRACTION = 0.75`, `KEYWORD_DRIFT_LIMIT = 2` (unchanged from pre-T1.3.1).
- For current 12 baseline + 4 borderline: thresholds (11, 3) — 92% / 75% floors. Overall PASS requires both tiers AND the keyword-drift budget.
- New `last_run.json` fields (tiered): `baseline_matches`, `baseline_total`, `baseline_threshold`, `baseline_pass`, `borderline_matches`, `borderline_total`, `borderline_threshold`, `borderline_pass`, `keyword_pass`. Legacy `decision_matches` (sum of tier matches) retained for backward compat.
- 31 new tests in `tests/test_canary_tiered_thresholds.py` covering classification, derivation, tiered pass evaluation, alarm truth table, keyword-drift budget, edge cases, and a regression-guard test that the runner never reads `manifest["pass_threshold"]`.
- Cold-review verdict: GO-WITH-NITS.

**`ac9bad7` — cold-review follow-ups (done directly, not delegated)**
- Nit 1: Renamed constant `BASELINE_PREFIX` → `BORDERLINE_PREFIX`. The constant marks the borderline category, not baseline; the old name was reviewer-flagged as confusing. Updated two sites in `scripts/canary_test.py` + 1 assertion in `tests/test_canary.py`.
- Nit 2: Dropped stale `"pass_threshold": 10` from `scripts/canary_fixtures/manifest.json` and removed the matching field-write from `scripts/generate_canary_fixtures.py` so regeneration will not re-introduce it. Added a comment pointing to the T1.3.1 derivation path. `scripts/canary_fixtures/README_borderline.md`: the bottom "Known discrepancy" paragraph replaced with a new "Threshold policy" section describing the tiered scheme.
- Nit 3: Added 3 CLI smoke tests in `tests/test_canary_tiered_thresholds.py::TestDoTestCliSmoke`, exercising `do_test()` end-to-end with a mocked `run_all`: (a) all-match → tier stdout printed, rc=0, overall PASS; (b) 1 baseline flip within tolerance → baseline tier still PASS; (c) 1 borderline flip → borderline tier FAIL, rc=1, "CANARY FAIL" printed. Tests capture stdout via `capsys`, use `tmp_path` + module-ref monkeypatch (session 21 canon), and lock the exact `Baseline tier: N/M match (threshold: >= T) -> PASS|FAIL` format so dashboard parsers / on-call eyes don't break silently.

### Test suite delta
- Canary-focused tests: 45 pass (`tests/test_canary.py` 11 + `tests/test_canary_tiered_thresholds.py` 34).
- No existing tests modified other than the `BASELINE_PREFIX → BORDERLINE_PREFIX` constant name.

---

## T1.3.1 decision record (preserved for future reference)

CEO offered A (hardcode 13, restore pre-T1.3 floor) or B (derive from manifest, e.g. `ceil(0.83 * total)`).

**Recommended + shipped: Option C — tiered thresholds by fixture category.**

Why C over A/B:
- **A reintroduces the same bug T1.3.1 is fixing** — another hardcoded constant that drifts out of sync with the fixture set.
- **B treats all fixtures identically.** But baseline fixtures (deep-zone, clear CANDIDATE/NO_TRADE) and borderline fixtures (near the C-gate boundary, expected to wobble under noise) have fundamentally different drift semantics. Blending them either under-alarms on serious deep-zone drift or over-alarms on routine borderline wobble.
- **C keeps the safety guarantee while matching detector sensitivity to signal quality.** Any deep-zone flip is treated as serious (at most 1 allowed); borderline wobble is treated as expected up to 25%. Both auto-scale with fixture counts via the `borderline_*` prefix convention.

The rationale is preserved inline in `scripts/canary_test.py:75-165` (module docstring + constants block) so future refactors see the "why" without excavating handoffs.

---

## Current repo state (verify via LIVE_STATE.md before acting)

- HEAD: `ac9bad7`
- Unpushed commits ahead of `origin/main`: **2** (`2d500f1`, `ac9bad7`).
- Working tree (post-handoff commit): clean.
- Canary tests pass: 45/45.
- Config unchanged this session.

---

## Known open items (last swept 2026-04-19 session 29 — re-verify before acting)

Carried forward from session 28 unchanged:

1. **GBPUSD XAUUSD macro override** — partial fix `bf57d90` (strip XAUUSD D1 context). Verify gap closed in fresh session via a simulation or live replay.
2. **Batch simulations for remaining 4 instruments** — ~$120.58 total, script ready, CEO decision pending.
3. **MT5 timezone bug** — `fromtimestamp()` without UTC in `mt5_real.py`, latent on UTC machines.
4. **Heartbeat kill switch live enablement** — T1.1 shipped DISABLED (`05fd5ef`). `config.heartbeat.flatten_enabled: false`. CEO enables after live observation window.
5. **Multi-symbol borderline canary fixtures** — T1.3 delivered XAUUSD-only (4 fixtures). Non-XAUUSD archives too thin today. Revisit once live produces enough non-XAUUSD CANDIDATE rows.
6. **Quantlabs P0 folds still valid** (complement to T1.x infra):
   - Per-symbol no-data alert (S, $0/mo) — T1.7
   - Correlation-shock Telegram alert (S, $0/mo) — T1.6
   - Time-in-trade shadow logger (S, $0/mo)
   - Weekly AI-reasoned skipped-trades summary (S, ~$2/mo)
7. **T1.4 Model-id pinning + drift alert** — research-tier, ~20 LOC + alert wiring. Catches silent Anthropic model updates.
8. **T1.5 CUSUM on CANDIDATE rate** — early-warning monitor independent of WR. Standalone ~100-150 LOC.

No new "open" items created by session 29.

---

## redacted_account kickoff (unchanged from session 28)

Tuesday 2026-04-21 — Stellar 2-Step $100K @ 1% risk. Profile `config/profiles/redacted_account.yaml` + watchdog `--profile redacted_account` hook both present and validated by `fa94b96`. No code changes required pre-kickoff.

---

## Suggested first work for fresh session

The council-worthy backlog after T1.3.1 closes leans toward three candidates, any of which the CEO might pick:

- **T1.4 model-id pinning + drift alert** (HIGH impact, ~20 LOC) — catches silent Anthropic model updates before live P/L reveals them. Pairs well with canary (content-drift detection) and canary cache (`0c26d25`). LOW risk.
- **T1.5 CUSUM on CANDIDATE rate** (HIGH impact, standalone script) — early-warning monitor that fires BEFORE WR decay appears. Independent of existing SPRT/CUSUM on WR.
- **T1.7 per-symbol no-data alert** (MEDIUM impact, ~50 LOC) — catches broker-data-feed outages that neither canary nor between-KZ fix detect.

All three are LOW risk, additive, and independent — could run concurrently. If the CEO picks more than one, dispatch them as parallel Opus 4.7 impl agents (single impl + single cold-review each, no council — scope well-defined in each case).

If the CEO picks none of the above: default to GBPUSD macro-override verification (open item #1), which requires a surgical T7 sim replay + inspection.

---

## How to start the fresh session

1. Close this Claude Code session (or type `/clear` if available in your CLI).
2. Open a fresh Claude Code session in `C:\Users\MSI\Documents\ai-trading-agent`.
3. The fresh session will auto-read `CLAUDE.md` and execute its MANDATORY FIRST ACTION protocol (regenerate `LIVE_STATE.md`, read this handoff).
4. First message to the fresh session (template — adapt to CEO intent):
   > "Session 29 closed T1.3.1. Confirm state via LIVE_STATE.md + handoff 29. Then [either: dispatch T1.4/T1.5/T1.7 as parallel Opus 4.7 max-effort agents (specs in backlog §T1) / verify GBPUSD macro-override gap / wait for CEO direction]."

Signed: session 29 close.
