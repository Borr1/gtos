# V7 A8 — Gate 0.5 Independent Review

**Reviewer:** Claude Opus 4.7 (independent, max effort)
**Date:** 2026-04-24
**Scope:** commits `32fbe58` (feat) + `4369214` (docs) on branch `worktree-agent-ad0a9ebd`
**Verdict:** **APPROVE** — the feature is correct, safe, well-tested, and the smoke test is independently reproducible. One genuine latent bug flagged (dead `skip_first_ny_candle` code at `orchestrator.py:1999` — pre-existing, NOT introduced by this change) plus two low-priority observations.

---

## 1. Gate ordering correctness — PASS

`check_permissions` at `src/components/permissions.py:46-72` now executes in this order:

| # | Gate | Function | File:line |
|---|------|----------|-----------|
| 0 | deployment.phase | `_reject_if_deployment_phase_blocked` | `permissions.py:113` |
| 0.5 | trading_enabled (NEW) | `_reject_if_trading_disabled` | `permissions.py:75` |
| 3 | circuit breakers (dormant → daily PnL → concurrent cap → MT5 → spread) | `_gate3_circuit_breakers` | `permissions.py:186` |
| 1 | safety checks (grade → bias → touch count → inverted TP → liquidity cluster → RR → SL/TP geometry) | `_gate1_safety_checks` | `permissions.py:624` |

Insertion point is correct: Gate 0 (phase, fail-closed on misconfig) still fires first; Gate 0.5 fires second, before any external state is consulted (no MT5 call, no session_state read, no MSO traversal). That means an observer-mode instrument under a misconfigured `deployment.phase` still reports the phase diagnostic rather than masking it — verified by the `test_gate_0_fires_before_gate_0_5` test and by reading the early-return `if denial: return denial` at `permissions.py:56-62`.

Ordering reasoning is sound:
- **Gate 0 first** — config-only fail-closed check for prod/paper misconfig, as designed.
- **Gate 0.5 second** — pure config read, no external state, cheap. Correct placement before Gate 3 because Gate 3's concurrent-cap gate involves an MT5 `positions_get` call (via `concurrent_tracker.get_filled_position_count`); wasting that call on a known-observer instrument would be silly. Also before Gate 1, so a `trading_enabled=false` instrument never burns CPU on grade/RR/SL checks.
- **No gate re-ordering issue** — LIVE_STATE.md's pre-patch references (line 70 for deployment gate, 199 for concurrent cap) corresponded to the pre-commit file layout; after the 43-line insertion, the post-patch offsets are 113 and 242 respectively. The brief's "line numbers" were from before this commit, matching the previous HEAD, not a hallucination.

**No ordering concerns.**

---

## 2. Config-loading correctness — PASS with caveats

`src/utils/config.py` behavior:
- `apply_profile_overrides` (line 81-103) — reads `config/profiles/<profile>.yaml`, deep-merges the overlay on top of the base.
- `apply_instrument_overrides` (line 32-65) — looks up `config["instruments"][symbol]`, deep-merges it into the base, then pops the entire `instruments` key from the returned dict.

Orchestrator order (`src/components/orchestrator.py:2963-2965`):
```
config = apply_profile_overrides(raw, resolved_profile)
config = apply_instrument_overrides(config, symbol)
```

This means: profile overlay is applied FIRST (profile's `instruments.GBPUSD.trading_enabled`, if present, deep-merges into base `instruments.GBPUSD`). Only AFTER that merge is the per-symbol section flattened to top level and the `instruments` section popped. That order is correct for this feature — any profile-level override of an instrument's `trading_enabled` would survive the flatten step.

Agent's stated contract — "flag at `instruments.XXX.trading_enabled` surfaces as top-level `config["trading_enabled"]`" — **verified correct** by reproduction.

### 2a. Red-team scenarios (reproduced on real config + FN profile)

| # | Scenario | Expected | Actual | Verdict |
|---|----------|----------|--------|---------|
| A | Base `instruments.GBPUSD.trading_enabled=false`, profile silent | `False` | `False` | OK |
| B | Base `false`, profile explicitly `true` | `True` (profile wins) | `True` | OK |
| C | Base silent, profile `false` | `False` | `False` | OK |
| D | Neither base nor profile set the key | default `True` (via `cfg.get("trading_enabled", True)` in gate) | key absent → gate reads `True` default → pass | OK |
| E | `instruments.GBPUSD: null` (explicit null dict) | loader raises (`instruments.get("GBPUSD")` returns None → `ValueError`) | `ValueError: No instrument config for 'GBPUSD'. Available: ['GBPUSD']` | OK — explicit fail, not a silent fallthrough |

Bonus scenarios I also ran:
- **Base `true`, profile `null`** — deep-merge replaces `True` with `None`; gate's `if trading_enabled:` evaluates `None` as falsy → **rejects as observer**. Fail-closed by accident, but the `details` dict reports `"trading_enabled": False` even though the actual value was `None`. Not a correctness issue but a minor footgun if a CEO ever writes `trading_enabled: null` expecting "inherit default".
- **String `"false"` (quoted in YAML)** — the value is a truthy string; gate reads it as `True` → allows trading. Real YAML should coerce unquoted `false` correctly, but a quoted string would silently disable the gate. Worth a `isinstance(trading_enabled, bool)` check with a loud warning, but low priority (no current user would type a quoted bool).

Both edge cases are YAML-typing hazards, not regressions introduced by this commit.

### 2b. Real-config smoke (reproduced independently)

Running the live `config/agent_config.yaml` + `config/profiles/redacted_account.yaml` through the real loader:

```
GBPUSD  trading_enabled: False
XAUUSD  trading_enabled: True
USDJPY  trading_enabled: True
GBPJPY  trading_enabled: True
US30    trading_enabled: True
instruments key in GBP: False   (popped)
instruments key in XAU: False   (popped)
XAUUSD risk: 0.5                 (FN XAUUSD override survives)
GBPUSD risk: 1.0                 (FN fleet default survives)
```

All five instruments ship with the correct flag. Per-instrument `risk_per_trade_pct` overrides from the redacted_account profile (`XAUUSD: 0.5%`, fleet `1.0%`) coexist cleanly with the flag.

---

## 3. Gate invocation correctness — PASS

`_reject_if_trading_disabled(config, symbol)` at `permissions.py:75-110`:
- Reads `cfg.get("trading_enabled", True)` from the TOP LEVEL of the passed config — matches the contract documented in the docstring and the agent's claim. No nested `config.get("instruments", {}).get(symbol, {})` pattern, so the "instruments popped" issue is structurally avoided.
- Default `True` preserves behavior for instruments without explicit config. Verified via `test_trading_enabled_defaults_true_when_missing`.
- `symbol` is passed through `check_permissions`'s `symbol` parameter, which is populated by the orchestrator from the command-line `--symbol` arg (same source that drives `apply_instrument_overrides`). So the gate always sees the same symbol that was used to flatten the config — no mismatch risk.
- `details={"symbol": symbol, "trading_enabled": False}` — hard-codes `False` in the details rather than echoing the actual (possibly `None`) value. Minor (see 2a edge case) but fine for production alerting.

Log line emitted at INFO: `"<SYMBOL> trade blocked by observer-mode flag (trading_enabled=false)"` — matches brief exactly.

---

## 4. Test quality — PASS, one gap noted

All six tests in `TestGate05TradingEnabled` (`tests/test_permissions.py:1005-1169`) exercise the right invariants:

| Test | Intent | Verdict |
|------|--------|---------|
| `test_trading_enabled_flag_allows_live_instrument` | XAUUSD `true` → pass | covers happy path |
| `test_trading_enabled_flag_blocks_observer_instrument` | GBPUSD `false` → reject with full details | covers rejection shape |
| `test_trading_enabled_defaults_true_when_missing` | Missing key → default `True` → pass | **critical safety test** — confirms fail-OPEN on missing key (so accidentally omitting the flag doesn't disable an instrument). Correctly wired. |
| `test_trading_enabled_gate_runs_before_gate1` | Observer block fires even with Gate 1/Gate 3 triggers pending | locks ordering vs downstream |
| `test_gate_0_fires_before_gate_0_5` | `phase=1` + `trading_enabled=false` → phase diagnostic wins | locks ordering vs Gate 0 |
| `test_config_loader_flattens_flag_from_nested_instruments_block` | End-to-end loader → gate contract | locks the `instruments → top-level` contract |

**Minor gap 1 (low priority):** No test for "profile-overrides-base `trading_enabled`" (scenario B above). `tests/test_profile_overrides.py` covers profile overrides generally, but no test explicitly pins the invariant "profile's `instruments.GBPUSD.trading_enabled: true` can promote a base `false`". If a future profile relies on this, it would silently break. Suggested add:

```python
def test_profile_overrides_trading_enabled_from_base(tmp_path, monkeypatch):
    base = {"instruments": {"GBPUSD": {"trading_enabled": False}}}
    profile_yaml = "instruments:\n  GBPUSD:\n    trading_enabled: true\n"
    # ... write profile, apply_profile_overrides, then apply_instrument_overrides, assert True
```

**Minor gap 2:** No test for the `trading_enabled: "false"` (quoted string) footgun. Low priority; YAML convention should rule this out in practice.

Neither gap is a blocker.

---

## 5. Regression risk — PASS

`pytest tests/test_permissions.py -v` → **60/60 pass** (0.38s).

Full suite `pytest tests/ --tb=no -q` → **1838 passed, 1 failed, 2 skipped, 22 warnings** in 280s.

The 1 failure is `tests/test_orchestrator.py::TestPendingIntentPersistence::test_pending_intent_stale_before_first_kz_discarded`. **Verified pre-existing** — I reproduced the same failure against an unrelated stashed state; the root cause is a time-of-day flake (the test's `now - 20h` computation falls before today's 07:00 UTC boundary only when the test runs after 03:00 UTC; my run was at 02:02 UTC, inside the skip window the test tries to guard against but doesn't cover precisely). Unrelated to Gate 0.5, unrelated to permissions at all.

All four live instruments (XAUUSD / USDJPY / GBPJPY / US30_cash) ship with `trading_enabled: true` explicitly set in the agent_config.yaml diff; behavior is fully preserved. GBPUSD is the only behavioral change — and only under a pre-AI-passing CANDIDATE (which is currently gated by the `h1_poi_availability` cost governor anyway).

---

## 6. Bonus finding verification — CONFIRMED (pre-existing, NOT introduced by this commit)

Agent flagged `orchestrator.py:1999` — `_should_skip_first_ny_candle`:

```python
inst_cfg = self.config.get("instruments", {}).get(self._symbol, {})
skip = inst_cfg.get("skip_first_ny_candle", False)
```

Reproduced:
```
instruments key present?  False                 # popped by apply_instrument_overrides
top-level skip_first_ny_candle: True            # actual flag for XAUUSD
nested (dead lookup):     None                  # what the function reads
```

**This is dead code.** The function always returns `False` early because `skip` resolves to `False` from the empty dict default. The actual XAUUSD `skip_first_ny_candle: true` setting at `config/agent_config.yaml:301` **is currently being ignored in production.**

This contradicts CLAUDE.md's "XAUUSD is configured to skip the 13:00 UTC candle" claim in `.context/05_operations/operator_decision_playbook.md:260`. It also contradicts the pre-lock checklist at `.context/00_core/pre_lock_final_review.md:181` which confirms the feature.

Scope: isolated — `grep` shows only one occurrence of `config.get("instruments"...)` in `src/` (this one), so no other dead-lookup regressions exist.

**NOT introduced by Gate 0.5** — this pre-dates this commit. But the agent correctly identified a real latent bug while doing their config-loading audit. Two safe fix paths:
1. Add `skip_first_ny_candle: true` at the top level after the pop (either manually or by flattening all per-instrument scalars in `apply_instrument_overrides`, which would also be cleaner).
2. Change `orchestrator.py:1999` to `self.config.get("skip_first_ny_candle", False)` (matches how Gate 0.5 reads its flag).

**Recommend option 2** — one-line change, mirrors the Gate 0.5 pattern, and the existing `apply_instrument_overrides` contract (flatten + pop) is documented and depended on.

---

## 7. Hallucinations — NONE

Every cited file/line and every behavioral claim in the agent's brief reproduces:

| Claim | Status |
|-------|--------|
| New `_reject_if_trading_disabled` in `permissions.py` | Confirmed at line 75-110 |
| Wired between Gate 0 and Gate 3 in `check_permissions` | Confirmed at lines 56-62 |
| Rejection shape `gate="gate0_5_trading_enabled"`, `reason="trading_disabled_for_instrument:<SYMBOL>"` | Confirmed at line 106-109 |
| INFO log wording | Confirmed at line 102-105 |
| Config schema: XAUUSD=true, GBPUSD=false, others=true | Confirmed at `agent_config.yaml:298-527` |
| 6 tests in `TestGate05TradingEnabled` | Confirmed at `tests/test_permissions.py:1005-1169` |
| 60/60 permissions tests pass | Verified |
| ~1838 full suite | Verified (1838 pass, 1 pre-existing flake, 2 skipped) |
| Smoke test: GBPUSD → `gate0_5_trading_enabled` denial; XAUUSD passes | Reproduced end-to-end |
| `apply_instrument_overrides` pops `instruments` post-merge | Confirmed at `config.py:47`, 55, 64 |
| Flag surfaces at top level after load | Reproduced on real config |
| Order: `apply_profile_overrides` → `apply_instrument_overrides` | Confirmed at `orchestrator.py:2964-2965` |
| Bonus finding about `orchestrator.py:1999` dead lookup | Confirmed; pre-existing |

No fabrications. The agent's diagnostic work was accurate.

---

## 8. Recommendations

### Ship — approve the merge

The feature is minimal, correct, well-tested, reversible (one-line config flip), and independently smoke-verified against live config. Documentation (`research/gbpusd_observer_mode_decision_2026-04-24.md`) is thorough and correctly records the rationale, trade-offs rejected, and promotion blockers.

### Follow-ups (not blocking)

1. **Fix the `skip_first_ny_candle` dead code at `orchestrator.py:1999`** — change `inst_cfg = self.config.get("instruments", {}).get(self._symbol, {})` + `inst_cfg.get("skip_first_ny_candle", False)` to `self.config.get("skip_first_ny_candle", False)`. This is a real latent bug (agent correctly flagged it); XAUUSD's 0% WR 13:00 UTC candle skip has been silently disabled for an unknown period. Worth its own commit + a regression test that round-trips the flag through the loader. Needs CEO approval since it restores a logic path.
2. **Add a profile-override test for `trading_enabled`** (Scenario B) to `tests/test_profile_overrides.py` or `tests/test_permissions.py::TestGate05TradingEnabled` — low effort, pins the invariant that profile overlays can promote an observer instrument to live.
3. **Consider `isinstance(trading_enabled, bool)` in the gate** with a `logger.warning` if violated — protects against the quoted-string YAML footgun. Low priority; no current user would do that.
4. **Update the `details` dict** in `_reject_if_trading_disabled` to echo the actual value (`"trading_enabled": trading_enabled`) rather than hard-coding `False`. Minor — helps debugging if someone writes `null` by mistake.
5. **Audit for similar `config.get("instruments", ...)` dead lookups in non-src paths** — `grep` confirmed only one in `src/`, but scripts/ and tests/ weren't audited. Low priority; contained risk.

### Evidence produced

- End-to-end config + gate smoke with both XAUUSD and GBPUSD passing/rejecting as claimed.
- All five red-team config scenarios + two bonus edge cases traced through the real loader.
- 60/60 `test_permissions.py` + 1838/1841 full-suite reproduction.
- Dead-code verification on bonus finding.
