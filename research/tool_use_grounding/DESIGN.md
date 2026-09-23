# Tool-Use Grounding for Primary Analyzer — Design Doc

**Status:** Sprint-3 design (Wave-1-demoted from #1 to #5; AI-decay-justified revival).
**Author:** Opus 4.7 design + scaffolding agent (session 40 KICKOFF, 2026-04-25).
**Branch base:** `main` HEAD `1b2d4e8` (no live changes proposed in this doc — design only).
**Out of scope:** shipping live this week. Post-Monday infrastructure work, sprint-3.
**Vision-program reference:** Option 5 in the (not-yet-written) `research/vision_program_2026-04-25/05_ARCHITECTURE_OPTIONS.md`. This doc is the implementable expansion of that option; if the vision-program docs land later they should cross-reference this file rather than re-invent the design.

---

## 0. TL;DR (for the impatient)

1. The primary analyzer is currently STATIC — it gets MSO + frozen KB context and a frozen prompt. There is no mechanism for the AI to ASK questions. When live regime shifts (decay, vol spike, correlation cluster), the AI has no way to self-calibrate.
2. Anthropic's tool-use API gives the AI N callable functions. Multi-turn flow: model reads MSO → optionally calls tool(s) → reads tool results → emits decision JSON.
3. Three tier-1 tools (`query_recent_trade_outcomes`, `lookup_session_volatility`, `check_correlation_exposure`) cover the AI-decay use case at ~$10-15/mo additional API spend and ~1-2 weeks engineering time per tool including canary validation.
4. Two tier-2 tools (`query_historical_WR`, `find_similar_setups`) ride on the existing LanceDB infra (already in `src/components/knowledge_base.py`) — high value but require feature-vector matching design + SHORT-data-availability concerns.
5. Validation strategy: F3-replay A/B (12 slices, ~$80) gated on ≥3pp WR uplift OR ≥0.05R Exp uplift OR rationale-faithfulness >90% (vs current <80%).
6. Multi-week build, NOT a quick win. Estimated **6-9 calendar weeks** (3 weeks tier-1 + 2 weeks A/B + 2-4 weeks tier-2 if green) until any tool-use code is live in production.
7. Biggest unknown: whether AI will ACTUALLY call tools when uncertain, vs hallucinating / ignoring them. Anthropic's claim is "yes when prompted properly", but not validated in the GTOS prompt-and-decision shape. F3 A/B is the only honest answer.

---

## 1. Why tool-use matters specifically for AI-decay

### 1.1 Current AI invocation is static

`src/components/primary_analyzer.py:243-335` (`PrimaryAnalyzer.analyze`) follows a strict single-turn flow:

1. Build prompt = system blocks (cached, invalidated on D1/H4 direction change) + user message (MSO + KB context + cross-instrument context + session memory + additional context).
2. `_call_claude` (line 341-415) issues a **single** `messages.create` call with `messages=[{"role": "user", "content": user_message}]`. No `tools=` parameter.
3. Parse response → run output guards (degenerate, wrong-side-SL, inconsistent-POIs) → emit decision.

The AI has no opportunity to **ask** anything. Its only inputs are:
- The MSO snapshot Component 2 produced for this M15 candle.
- KB three-layer context (`assemble_full_context` for XAUUSD; empty dict for non-gold per `primary_analyzer.py:181-185`).
- Static cross-instrument context (when enabled).
- Session memory (currently `session_memory_enabled: false` per CLAUDE.md, after the T2b -55% CR finding).
- The prompt template itself (V3, frozen at ship-time).

This is fundamentally **a frozen-context system**. Whatever the prompt-author decided to surface is what the AI sees, period.

### 1.2 Decay = the system prompt drifting from reality

CEO's #1 concern (memory `feedback_decay_is_ceo_number_one_concern.md`): edge decay is the principal risk. CLAUDE.md item #9 documents the XAUUSD H1→H2 2026 decay (chi-square p=0.006, Apr WR 10% n=10). Item #1 documents the quarterly trend (73.2% → 71.4% → 63.6% → 59.4%).

Static prompt + slow decay = the prompt CONTINUES to encode WR / Exp R / regime assumptions that no longer hold. Examples of how this hurts:

- **WR-anchored confidence calibration.** Prompt's setup-grading rubric (A+/A/B+/B/C) is implicitly anchored to historical WR. If XAUUSD live WR drops to 35%, the AI continues grading at A/A+ frequencies because nothing in its inputs reflects the regime shift.
- **Session-vol assumptions.** Prompt assumes "London KZ has wide impulses, NY has wide impulses post-13:30". If a quiet-NY week lands (FOMC the next Wednesday compresses the prior week), nothing in MSO tells the AI that today's W1 candle is 0.7σ instead of 1.5σ.
- **Correlation exposure.** Prompt has no concept of fleet-wide concurrent positions. If XAUUSD + USDJPY + GBPJPY are all sitting in correlated LONG limits, AI has no way to know the next CAND would breach the 2% combined-correlation cap (CLAUDE.md emergency stop #6).

### 1.3 Tool-use as self-calibration mechanism

With tool-use, the AI gains an action: ASK. When the prompt's general reasoning produces uncertainty ("this looks like a B+ but recent XAUUSD setups have been failing"), the AI can:

```
tool_call: query_recent_trade_outcomes(symbol="XAUUSD", days_back=30)
tool_result: {"n": 12, "WR": 0.25, "exp_R": -0.18, "last_5_outcomes": ["L","L","L","W","L"]}
```

…and downgrade its confidence accordingly. The AI's subsequent decision is then **grounded in current reality**, not the prompt's frozen assumptions.

Equivalently for vol:

```
tool_call: lookup_session_volatility(symbol="XAUUSD", session="ny")
tool_result: {"atr_now": 4.2, "atr_30d_median": 7.8, "percentile": 0.18}
```

→ AI knows we're in a low-vol pocket, may downgrade entry expectations or skip impulse-required setups.

And for correlation:

```
tool_call: check_correlation_exposure(direction="LONG", symbol="USDJPY")
tool_result: {"open_correlated_positions": 2, "max_combined_risk_pct": 1.8, "would_breach_cap": false}
```

→ AI understands the fleet context and may demote the CAND to NO_TRADE or accept it cautiously.

### 1.4 What tool-use is NOT

- **Not a fix for prompt bugs.** If V3 has a broken instruction, tools don't fix it.
- **Not a replacement for safety gates.** L1/L2/Gate-1 deterministic checks remain the source of truth. Tool-use is INPUT enrichment.
- **Not a fix for MSO bugs.** If `market_state.py` produces a bad swing detection, tools don't help.
- **Not free.** Each tool call = additional API tokens (input + output) + latency (tool-execution time) + complexity surface area.

This is squarely an AI-decay mitigation. For per-trade quality, prompt iteration is cheaper. Wave-1 demotion was correct on those grounds.

---

## 2. Tool catalog — five candidates ranked by value/cost

Each tool has: input schema, output schema, implementation cost, expected value, dependencies, sample usage, failure modes.

### 2.1 Tier-1 (Phase-1 build, weeks 1-3)

#### Tool A — `query_recent_trade_outcomes` (RANK #1, highest value)

**Purpose.** Self-calibration on rolling realized-R. Direct hit on the CEO's #1 concern (decay).

**Input schema.**
```json
{
  "symbol": "XAUUSD",          // required, one of the live 5 instruments
  "days_back": 30,             // optional, int 7-90, default 30
  "framework": "ob_retest",    // optional, filter by framework
  "direction": "LONG"          // optional, "LONG" | "SHORT"
}
```

**Output schema.**
```json
{
  "symbol": "XAUUSD",
  "window_days": 30,
  "n_trades": 14,
  "win_rate": 0.357,
  "exp_R": -0.082,
  "last_5_outcomes": [
    {"date": "2026-04-22", "R": -1.0, "framework": "ob_retest", "direction": "LONG"},
    {"date": "2026-04-21", "R": +1.5, "framework": "ob_retest", "direction": "LONG"},
    {"date": "2026-04-19", "R": -1.0, "framework": "ob_retest", "direction": "SHORT"},
    {"date": "2026-04-18", "R": -1.0, "framework": "ob_retest", "direction": "LONG"},
    {"date": "2026-04-15", "R": +1.5, "framework": "ob_retest", "direction": "LONG"}
  ],
  "baseline_3mo_WR": 0.535,    // comparison
  "wilson_95ci": [0.140, 0.642]
}
```

**Implementation sketch (Python, ~80 LOC).**

```python
# src/components/ai_tools/query_recent_outcomes.py
from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
from typing import Optional

TRADE_RECORDS_ROOT = Path("knowledge_base/trade_records")

def query_recent_trade_outcomes(
    symbol: str,
    days_back: int = 30,
    framework: Optional[str] = None,
    direction: Optional[str] = None,
) -> dict:
    """Read knowledge_base/trade_records/{SYMBOL}/*.json, filter, aggregate."""
    if symbol not in {"XAUUSD", "US30_cash", "USDJPY", "GBPJPY", "GBPUSD"}:
        return {"error": "unknown_symbol", "symbol": symbol}
    if not 7 <= days_back <= 90:
        return {"error": "days_back_out_of_range", "days_back": days_back}

    sym_dir = TRADE_RECORDS_ROOT / symbol
    if not sym_dir.exists():
        return {"error": "no_records", "symbol": symbol, "n_trades": 0}

    cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)
    rows: list[dict] = []
    for fp in sorted(sym_dir.glob("*.json")):
        try:
            d = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        meta = d.get("metadata", {})
        ex = d.get("exit") or {}
        # Only count filled-and-exited trades.
        realized_R = ex.get("realized_R")
        if realized_R is None:
            continue
        candle_iso = meta.get("candle_time", "")
        try:
            candle_dt = datetime.fromisoformat(candle_iso.replace("Z", "+00:00"))
        except Exception:
            continue
        if candle_dt < cutoff:
            continue
        # Direction / framework filtering.
        tp = d.get("trade_parameters") or {}
        if direction and tp.get("direction") != direction:
            continue
        ai_resp = d.get("ai_response") or {}
        if framework and ai_resp.get("framework") != framework:
            continue
        rows.append({
            "date": candle_dt.date().isoformat(),
            "R": float(realized_R),
            "framework": ai_resp.get("framework", "?"),
            "direction": tp.get("direction", "?"),
        })

    n = len(rows)
    if n == 0:
        return {"symbol": symbol, "window_days": days_back, "n_trades": 0,
                "win_rate": None, "exp_R": None, "last_5_outcomes": []}

    wins = sum(1 for r in rows if r["R"] > 0)
    wr = wins / n
    # Clip per memory project_distributional_findings.md
    clipped = [max(-5.0, min(5.0, r["R"])) for r in rows]
    exp = sum(clipped) / n
    last_5 = rows[-5:]

    # Wilson 95% CI (uses scipy.stats.beta or statsmodels)
    from statsmodels.stats.proportion import proportion_confint
    lo, hi = proportion_confint(wins, n, alpha=0.05, method="wilson")

    # 3-month baseline (already-cached snapshot or live recompute — TBD).
    baseline = _load_3mo_baseline(symbol, framework, direction)

    return {
        "symbol": symbol,
        "window_days": days_back,
        "n_trades": n,
        "win_rate": round(wr, 3),
        "exp_R": round(exp, 3),
        "last_5_outcomes": last_5,
        "baseline_3mo_WR": baseline,
        "wilson_95ci": [round(lo, 3), round(hi, 3)],
    }


def _load_3mo_baseline(
    symbol: str, framework: Optional[str], direction: Optional[str]
) -> Optional[float]:
    """Return cached 3-month baseline WR. Recompute weekly via cron."""
    cache = Path("knowledge_base/ai_tools_cache/3mo_baseline.json")
    if not cache.exists():
        return None
    data = json.loads(cache.read_text(encoding="utf-8"))
    key = f"{symbol}|{framework or 'any'}|{direction or 'any'}"
    return data.get(key)
```

**Implementation cost.** ~1 engineering day (helper) + ~1 day (cron baseline-snapshot script + tests) + ~0.5 day for canary fixtures. **Total: 2.5 engineering days.**

**Expected value.** HIGH for AI-decay specifically. AI can self-throttle when WR is degrading. Direct mitigation for items #1, #9, #11 in CLAUDE.md.

**Dependencies.**
- A3 v1.1 trade-record instrumentation (already shipped — handoff §"What's shipped and live").
- `statsmodels` (already in `requirements.txt`? — verify; alternatively use `scipy.stats.beta` for Wilson which is in scipy).
- Cron job for 3-month baseline cache update (separate ~30 LOC script, runs weekly).

**Failure modes.**
- Sparse data for non-XAUUSD instruments early on (USDJPY n=33 batch, GBPUSD observer-only). Tool returns `n_trades=0` cleanly; AI must handle.
- Time-zone drift in `candle_time` parsing — already burned us in `data_ingestion.py` empty-symbol fix (2026-04-24 Wave 2.5). Use UTC-explicit parsing.
- Test isolation — must use `tmp_path` per memory `project_pytest_contamination_forensics.md`.

---

#### Tool B — `lookup_session_volatility` (RANK #2)

**Purpose.** Give AI access to current-session ATR vs the rolling 30-day median. Primary use: detect "vol pocket" days where impulse-required setups should be downgraded.

**Input schema.**
```json
{
  "symbol": "XAUUSD",
  "session": "ny",          // "london" | "ny" | "tokyo" | "asia"
  "lookback_days": 30       // optional, 7-90, default 30
}
```

**Output schema.**
```json
{
  "symbol": "XAUUSD",
  "session": "ny",
  "atr_now": 4.21,            // ATR-14 over current session-window M15 candles so far
  "atr_30d_median": 7.84,     // median session-ATR over lookback_days
  "atr_30d_p25": 5.12,
  "atr_30d_p75": 9.61,
  "percentile_today": 0.18,   // where today's atr_now falls in the 30d distribution
  "regime": "low_vol",        // discrete label: "low_vol" | "normal" | "high_vol" | "extreme"
  "n_session_samples": 28
}
```

**Implementation sketch.** Reuses `market_state.py:1057-1191` (`session_vol_ratio` already computed for XAUUSD M15). Generalize to all 5 instruments + cache 30-day session-ATR distribution per (symbol, session) pair.

```python
# src/components/ai_tools/lookup_session_vol.py
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json, statistics
from src.components.data_ingestion import DataIngestion  # existing

# Pre-computed snapshot — refreshed weekly via cron.
VOL_CACHE = Path("knowledge_base/ai_tools_cache/session_vol_30d.json")

def lookup_session_volatility(symbol: str, session: str,
                              lookback_days: int = 30) -> dict:
    if session not in ("london", "ny", "tokyo", "asia"):
        return {"error": "unknown_session", "session": session}
    cache = json.loads(VOL_CACHE.read_text()) if VOL_CACHE.exists() else {}
    key = f"{symbol}|{session}"
    snapshot = cache.get(key, {})

    # Compute current session ATR-14 from live MT5 / latest pipeline state.
    # Implementation detail: mirror market_state.py:1057-1191 for the
    # *running* session window, not just XAUUSD M15.
    atr_now = _compute_current_session_atr(symbol, session)

    median_30d = snapshot.get("median")
    p25 = snapshot.get("p25")
    p75 = snapshot.get("p75")
    samples = snapshot.get("daily_atrs", [])

    if not samples or atr_now is None:
        return {
            "symbol": symbol, "session": session,
            "atr_now": atr_now, "atr_30d_median": median_30d,
            "regime": "unknown", "n_session_samples": len(samples),
        }

    # Empirical percentile.
    rank = sum(1 for x in samples if x <= atr_now)
    pct = rank / len(samples)
    if pct < 0.20: regime = "low_vol"
    elif pct < 0.80: regime = "normal"
    elif pct < 0.95: regime = "high_vol"
    else: regime = "extreme"

    return {
        "symbol": symbol, "session": session,
        "atr_now": round(atr_now, 4),
        "atr_30d_median": round(median_30d, 4),
        "atr_30d_p25": round(p25, 4),
        "atr_30d_p75": round(p75, 4),
        "percentile_today": round(pct, 2),
        "regime": regime,
        "n_session_samples": len(samples),
    }
```

**Implementation cost.** ~3 engineering days (1 day generalize session-ATR for all 5 symbols, 1 day cron snapshot, 1 day tests + canary).

**Expected value.** MEDIUM-HIGH. Lower-hanging than tool A (vol regime is more transient than WR decay), but still adds calibration. Most value when prompt has impulse-required language.

**Dependencies.** `market_state.py` session-ATR generalization (currently only XAUUSD-M15 has `atr_session`). Cron weekly snapshot. Live MT5 or pipeline-state read for current session.

**Failure modes.**
- Stale cache during weekend/dead-zone. Tool returns `n_session_samples` so AI can detect.
- DST transitions (London → BST 2026-03-29, NY → EDT 2026-03-08 — already historical). Already handled in `market_state.py`.

---

#### Tool C — `check_correlation_exposure` (RANK #3)

**Purpose.** Give AI fleet awareness — tell it which other instruments have open or pending correlated positions and whether one more would breach the 2% combined cap.

**Input schema.**
```json
{
  "symbol": "USDJPY",
  "direction": "LONG",
  "would_be_risk_pct": 1.0     // optional: simulated risk if this CAND fills
}
```

**Output schema.**
```json
{
  "symbol": "USDJPY",
  "direction": "LONG",
  "open_correlated_positions": [
    {"symbol": "GBPJPY", "direction": "LONG", "risk_pct": 1.0, "state": "open"},
    {"symbol": "XAUUSD", "direction": "SHORT", "risk_pct": 1.0, "state": "limit_pending"}
  ],
  "n_open_correlated_same_direction": 1,
  "max_combined_risk_pct_if_filled": 2.0,
  "would_breach_2pct_cap": true,    // CLAUDE.md emergency stop #6
  "correlation_group": "JPY_CROSSES"
}
```

**Implementation sketch.** Hook into existing `concurrent_tracker.py` and `portfolio_risk.py` (already exist per `ls src/components/`). Read live state from these singletons.

```python
# src/components/ai_tools/check_correlation.py
from src.components.concurrent_tracker import ConcurrentTracker
from src.components.portfolio_risk import PortfolioRisk

# Same correlation groups as portfolio_risk.py — DO NOT re-define here.
# Memory: feedback_decision_preservation.md and CLAUDE.md §VERIFICATION rule 3
# warn against unilateral correlation-group edits.
def check_correlation_exposure(symbol: str, direction: str,
                               would_be_risk_pct: float = 1.0) -> dict:
    tracker = ConcurrentTracker.get_instance()  # singleton
    risk = PortfolioRisk.get_instance()
    group = risk.correlation_group(symbol)  # e.g. "JPY_CROSSES"

    open_positions = tracker.get_filled_positions()
    pending = tracker.get_pending_limits()
    correlated = [
        p for p in (open_positions + pending)
        if risk.correlation_group(p.symbol) == group and p.symbol != symbol
    ]

    same_dir_n = sum(1 for p in correlated if p.direction == direction)
    current_risk = sum(p.risk_pct for p in correlated if p.direction == direction)
    combined = current_risk + would_be_risk_pct
    breach = combined > 2.0

    return {
        "symbol": symbol,
        "direction": direction,
        "open_correlated_positions": [
            {"symbol": p.symbol, "direction": p.direction,
             "risk_pct": p.risk_pct, "state": p.state}
            for p in correlated
        ],
        "n_open_correlated_same_direction": same_dir_n,
        "max_combined_risk_pct_if_filled": round(combined, 2),
        "would_breach_2pct_cap": breach,
        "correlation_group": group,
    }
```

**Implementation cost.** ~1.5 engineering days. Most logic exists; tool is a thin wrapper.

**Expected value.** MEDIUM. Existing `portfolio_risk.py` already gates the breach at execution time, so this is BELT-AND-SUSPENDERS — the AI can demote a CAND BEFORE the gate fires, surfacing the reason in its rationale. Faithfulness gain: AI can EXPLAIN to the trader why it skipped a setup.

**Dependencies.** `ConcurrentTracker` + `PortfolioRisk` cross-process singletons. The 5 orchestrator processes each have their own tracker — cross-process IPC needed (file-based: read `pipeline_state/concurrent_state.json` produced by `concurrent_tracker.py`). Verify existing IPC pattern before implementing.

**Failure modes.**
- Read-during-write race on `concurrent_state.json`. Use atomic-rename write pattern (already in `file_io.py`).
- Stale pending intent (limit cancelled but state file not yet updated). Mitigated by `pending intent persistence` already shipped.

---

### 2.2 Tier-2 (Phase-3 build, post-A/B-validation)

#### Tool D — `query_historical_WR(features)` (RANK #4)

**Purpose.** Feature-vector matching: "given a setup with these features, what's the historical WR over the matching subset?"

**Input schema.**
```json
{
  "symbol": "XAUUSD",
  "features": {
    "framework": "ob_retest",
    "h1_ob_touch_count": 1,
    "kill_zone": "ny",
    "h4_aligned": true,
    "setup_grade": "B+"
  },
  "min_n_for_match": 10        // refuse to return WR if fewer matches
}
```

**Output schema.**
```json
{
  "n_matches": 27,
  "win_rate": 0.518,
  "exp_R": +0.142,
  "wilson_95ci": [0.337, 0.692],
  "matching_records_window_days": 90,
  "feature_match_strictness": "exact"   // "exact" | "fuzzy_topk"
}
```

**Implementation sketch.** TWO routes — pick one based on data scale:

**Route 1 (deterministic).** Indexed scan over `trade_records/`. Build a feature-tuple → list-of-R index at startup, refresh on file-change. Match on exact tuple equality.

```python
# src/components/ai_tools/query_historical_wr.py
def query_historical_WR(symbol: str, features: dict,
                        min_n_for_match: int = 10) -> dict:
    index = _load_or_build_feature_index(symbol)  # tuple → [R, R, R, ...]
    key = _features_to_tuple(features)
    matches = index.get(key, [])
    if len(matches) < min_n_for_match:
        return {"n_matches": len(matches), "insufficient_data": True}
    wr = sum(1 for r in matches if r > 0) / len(matches)
    exp = sum(max(-5, min(5, r)) for r in matches) / len(matches)
    return {
        "n_matches": len(matches),
        "win_rate": round(wr, 3),
        "exp_R": round(exp, 3),
        "matching_records_window_days": 90,
        "feature_match_strictness": "exact",
    }
```

**Route 2 (LanceDB).** Use existing LanceDB infra in `knowledge_base.py` (`initialize_vectordb` — confirmed wired). Embed feature dict via existing `all-MiniLM-L6-v2` model + retrieve top-k similar setups; aggregate their R outcomes.

Route 1 is simpler, deterministic, and adequate for 5-instrument scale (≤500 trade records over 6 months). Route 2 is necessary for the 50-instrument vision (handoff "Tier-2 candidates").

**Recommendation: Phase 3a Route 1 (n=5 instruments). Phase 3b Route 2 (50-instrument scaling).**

**Implementation cost.**
- Route 1: ~3 engineering days (index builder, file-change watcher, tests, canary).
- Route 2: ~5-7 engineering days (embedding decisions, similarity threshold tuning, OOS-vs-IS data hygiene tests).

**Expected value.** HIGH if data is dense; MEDIUM at current 5-instrument scale. ~250 trade records across 5 instruments over 6 months → average ~50 records per instrument, sparse for fine-grained feature tuples. **Risk: returns insufficient_data ≥80% of the time at present scale.**

**Dependencies.** Same as Tool A + LanceDB if Route 2.

**Failure modes.**
- Sparse-data noise — tool may return CIs wider than the prompt's prior. Acceptable; AI must read CI.
- Survivorship — only filled trades in `trade_records/`. NO_TRADE / REJECTED_L2 records exist but lack realized R. **Decision:** filter to filled-only (matches Tool A).
- IS contamination if `trade_records/` includes the very candle being evaluated. **Mitigation:** filter `candle_dt < now - 1h` to be safe.

---

#### Tool E — `find_similar_setups(features, k=5)` (RANK #5)

**Purpose.** Concrete examples retrieval — give AI the 5 most-similar past setups so it can read their outcomes.

**Input schema.**
```json
{
  "symbol": "XAUUSD",
  "features": {
    "framework": "ob_retest",
    "h1_ob_touch_count": 1,
    "kill_zone": "ny",
    "h4_aligned": true,
    "atr_session_pct_of_30d": 0.42
  },
  "k": 5
}
```

**Output schema.**
```json
{
  "k_returned": 5,
  "similarity_threshold": 0.78,
  "matches": [
    {
      "date": "2026-04-15",
      "session": "ny",
      "framework": "ob_retest",
      "outcome": "loss",
      "realized_R": -1.0,
      "exit_reason": "stop_loss_hit",
      "similarity_score": 0.92,
      "summary": "XAUUSD LONG on H1 OB touch=1 in NY KZ; SL hit on first reaction, no MFE."
    },
    ...
  ]
}
```

**Implementation sketch.** Pure LanceDB.

```python
# src/components/ai_tools/find_similar_setups.py
from src.components.knowledge_base import KnowledgeBase

def find_similar_setups(symbol: str, features: dict, k: int = 5) -> dict:
    kb = KnowledgeBase.get_instance()
    # Embed features to vector (consistent with Layer-3 retrieval)
    vec = kb.embed_features(features)
    table = kb._lancedb.open_table("trades")
    results = table.search(vec).limit(k).to_pandas()
    matches = []
    for _, row in results.iterrows():
        matches.append({
            "date": row["candle_date"],
            "session": row["kill_zone"],
            "framework": row["framework"],
            "outcome": "win" if row["realized_R"] > 0 else "loss",
            "realized_R": float(row["realized_R"]),
            "similarity_score": round(float(row["_distance"]), 3),
            "summary": row.get("summary", ""),
        })
    return {"k_returned": len(matches), "matches": matches}
```

**Implementation cost.** ~5-7 engineering days. Embedding-schema decisions are non-trivial: which features matter, how to encode categorical (framework, KZ) vs continuous (touch_count, ATR percentile).

**Expected value.** HIGH for AI **explanation** (anchors AI's reasoning to concrete past setups), MEDIUM for actual decision quality (vs Tool D aggregate WR). Adversarial-faithfulness wins are real here — AI can cite "this is similar to 2026-04-15 which lost; I'll skip" instead of generic risk-aversion language.

**Dependencies.** LanceDB schema design + embedding-model commitment.

**Failure modes.**
- Embedding drift — `all-MiniLM-L6-v2` was chosen for KB; we should NOT introduce a second embedder. Pin and version.
- Cherry-picked similarities (top-k may all be losses or all be wins by chance). AI's prompt must instruct it to read aggregate, not anecdotes.

---

### 2.3 Tools NOT recommended (decided OUT)

- **`get_regime_label(symbol, timeframe)`** — depends on a regime classifier we don't have. ADR-004 addressed market-structure direction (the v2_shadow path); a generic "regime" label is undefined work. Skip until classifier ships.
- **`check_news_calendar(symbol, window_min)`** — code stub exists in `news_calendar.py`, currently disabled. Per handoff §P7, news calendar is on the month-3+ roadmap. Tool-use can wait on that.
- **`query_session_avg_outcome(symbol, session)`** — subsumed by Tool A with a `session=` filter parameter. Don't proliferate tools.
- **`compute_implied_volatility(symbol)`** — interesting but requires an IV data source we don't have. Out of scope.

---

## 3. Anthropic tool-use API integration

### 3.1 API surface (Claude Sonnet 4.6, tool-use native support)

Anthropic SDK (already imported at `src/components/primary_analyzer.py:34-39`) accepts a `tools=` parameter:

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=2000,
    temperature=0,
    system=system_blocks,
    tools=[
        {
            "name": "query_recent_trade_outcomes",
            "description": "Query realized R outcomes over a recent rolling window for a symbol. Use when uncertain about current edge state.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "enum": ["XAUUSD", "USDJPY", "GBPJPY", "GBPUSD", "US30_cash"]},
                    "days_back": {"type": "integer", "minimum": 7, "maximum": 90},
                    "framework": {"type": "string"},
                    "direction": {"type": "string", "enum": ["LONG", "SHORT"]},
                },
                "required": ["symbol"],
            },
        },
        # ... tool B, C definitions ...
    ],
    messages=[{"role": "user", "content": user_message}],
    timeout=self.timeout,
)
```

### 3.2 Multi-turn flow

When Claude decides to call a tool, the response has `stop_reason="tool_use"` and `content` is a list of blocks with `type="tool_use"` mixed with `type="text"`:

```python
# Pseudocode
def analyze_with_tools(market_state, ...):
    messages = [{"role": "user", "content": user_message}]
    max_tool_iterations = 3   # safety cap

    for _ in range(max_tool_iterations):
        response = client.messages.create(
            model=self.model,
            tools=TOOL_DEFS,
            messages=messages,
            ...
        )
        if response.stop_reason != "tool_use":
            break  # final answer

        # Extract tool_use blocks, execute, append results
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

    # Final response is decision JSON
    final_text = next((b.text for b in response.content if b.type == "text"), "")
    return parse_and_validate(final_text)
```

### 3.3 Tool-result schema constraints

- Each `tool_result` MUST have `tool_use_id` matching the call.
- `content` is stringified JSON (not a Python dict) — Anthropic expects string.
- Tool-results live in a `user`-role message; Claude reads them as if they were user-supplied.

### 3.4 Token cost implications

Per Anthropic docs (verified via `claude-api` skill / cached docs as of 2026-04-25):

| Cost component | Tokens | Notes |
|---|---|---|
| Tool definition (in `tools=`) | ~150-300 per tool (system-cached after first call) | Caches with `cache_control: {"type": "ephemeral"}` analogous to system blocks |
| Tool-call output block | ~50-100 | Claude emits the JSON input |
| Tool-result block (input back to Claude) | ~100-500 depending on payload | Tool A returns ~150 tokens; Tool E with k=5 may return ~500 |
| Additional turn round-trip | ~+1 input + 1 output cycle | Each tool-call is its own turn |

Realistic: **+800-1500 tokens per analyze() call IF a tool is called**, vs ~5000-tok baseline. ~+15-30% per-call cost. AI calls a tool ~20-40% of the time (estimate; validate in A/B).

**Average cost increase:** ~+5-10% per analyze(). Monthly: ~$60 baseline → ~$66-70.

### 3.5 Caching considerations

Tool definitions can be cached just like system blocks. Recommended: include tools= in the same cached content block as the system prompt, since tools rarely change. Verify cache_control behavior on `tools=` parameter (Anthropic's Sonnet 4.6 docs are explicit: yes, supported as of 2025).

### 3.6 Error handling

| Failure | Handling |
|---|---|
| Tool execution times out | Return `{"error": "tool_timeout", "tool": "query_recent_trade_outcomes"}` to Claude as tool_result. Claude proceeds without that data. |
| Tool execution raises | Wrap in try/except, return `{"error": str(exc)}`. NEVER propagate to caller. |
| Claude infinite-loops on tool calls | `max_tool_iterations=3` hard cap. After 3, force final answer (re-prompt without tools). |
| Tool output schema violation | Validate against Pydantic model on the tool side; on violation log + return `{"error": "tool_internal", "fields_missing": [...]}`. |
| API timeout during multi-turn | Existing retry logic in `_call_claude` (lines 358-413) needs extension. Each tool-call cycle is a separate API call, so timeout is per-cycle. |
| Tool returns insufficient data | Cleanly return `{"insufficient_data": true, "n": 0}`. Claude is instructed by tool description to handle. |

---

## 4. Validation strategy

### 4.1 Backtest-replay A/B (PRIMARY validation)

**Methodology.** F3-style 12 parallel slices (XAUUSD ×8 + USDJPY ×4), pre-registered:

| Arm | Configuration | Variable cost |
|---|---|---|
| Control (V3) | Current V3 prompt, no tools | $40 |
| Tool-Use Tier-1 | V3 + tools A/B/C wired | $50 |

Total: ~$90 (Tier-1 tools add tokens, hence the bump).

**Pre-registered metrics.**

| Metric | Control expectation | Tool-Use ship gate |
|---|---|---|
| Fleet WR | F3 baseline 56.2% | ≥+3pp = ≥59.2% |
| Fleet Exp R | F3 +0.407R | ≥+0.05R uplift = ≥+0.457R |
| Rationale-faithfulness | Estimated 75-80% (per V3 cold-review) | ≥90% post-tool |
| Tool-call rate | N/A | 20-50% of evaluations (sanity check) |
| L2 reject rate | F3 baseline | NO regression (≤+2pp) |
| Cost per fill | ~$0.30 | ≤$0.40 |

**Ship gate (OR-conjunction).** Ship Phase-1 tools to live IF:
- WR ≥+3pp **OR**
- Exp R ≥+0.05R **OR**
- Rationale-faithfulness >90% AND no metric regresses

**Pre-registered failure cases.**
- WR drops ≥-3pp → IMMEDIATE shelve.
- Tool-call rate <5% → AI is ignoring tools; redesign prompts before re-run.
- Tool-call rate >70% → AI is over-relying; re-tune tool descriptions toward "use only when uncertain."
- Tool execution latency >2s P99 → infrastructure bottleneck; refactor.

### 4.2 Rationale-faithfulness audit (SECONDARY)

Hand-audit 30 CAND rationales pre/post tool-use. Score each on:

1. Does the AI cite specific evidence? (vs generic "looks good")
2. Is the evidence verifiable against MSO / tool outputs? (vs hallucination)
3. Does the rationale account for live recent context? (vs frozen prompt assumptions)

V3 baseline cold-review (research/v4_prompt_engineering V8 review, partial) suggests current faithfulness is in the 75-80% range. Tool-use should drive this >90% because claims become verifiable against tool outputs.

This is the strongest pro-tool-use argument — tool outputs are AUDIT TRAIL. Even if WR and Exp R don't move materially, the AI's reasoning becomes inspectable in a way it wasn't before.

### 4.3 Live shadow phase (TERTIARY, post-A/B)

Once A/B is green: ship tools=[A,B,C] to PRODUCTION but log-only — i.e., wire the tool definitions, capture which calls AI makes, but do NOT change behavior gates. Shadow-log AI's tool-call patterns for 14 days. Validate that AI calls tools at expected rate AND that the tool-call distribution matches A/B simulator predictions.

Decision: only after shadow-phase numbers match simulator predictions, flip a config flag (`primary_analyzer.tool_use_active: true`) to make tool outputs INFLUENCE the decision (rather than only being logged).

This is intentionally analogous to v2_shadow → v2 detector promotion: separate the wire/observe step from the use step.

### 4.4 What we are NOT validating

- **Live A/B.** Too slow given decay risk (memory `feedback_decay_is_ceo_number_one_concern.md`); compress validation timelines via backtest-replay instead.
- **Per-tool ablation.** Phase 1 ships A+B+C together. Per-tool ablation is a Phase 4 follow-up (3 control × 8 ablation arms ≈ $200, deferred).
- **Cross-instrument generalization.** F3-replay slices cover XAUUSD + USDJPY only; generalization to GBP/US30 deferred to instrument-expansion sprint (handoff §P2).

---

## 5. Cost analysis

### 5.1 Per-call cost increase

Baseline Claude Sonnet 4.6 pricing (2026-04, may change):

| Component | Tokens | Cost ($) |
|---|---|---|
| Input (system + user, with cache hit) | ~5000 input | $0.0024 (cached @ $0.0006/1k cached + ~5K not-cached one-shot) |
| Output (decision JSON) | ~600 output | $0.009 ($0.015/1k output) |
| Per-call total (no tools) | — | ~$0.011 |

With tool-use (1 tool called, 1 round-trip):

| Component | Tokens | Cost ($) |
|---|---|---|
| Tool defs (cached) | +200 input cached | +$0.00012 |
| Round 1 output (tool_use block) | +80 output | +$0.0012 |
| Round 2 input (tool_result block) | +200 input | +$0.0012 |
| Round 2 output (decision) | +600 output | +$0.009 |
| **Net additional** | — | **+$0.012** |

Approximately **2× per-call cost when AI calls a tool**, vs no-tool path.

### 5.2 Monthly impact projections

Current state: ~600 evaluations/mo (5 instruments × ~30 KZ candles × 4 trading weeks × ~50% K-zone candle eligibility), ~$60/mo Anthropic API spend (CLAUDE.md).

| Scenario | Tool-call frequency | Monthly impact |
|---|---|---|
| Pessimistic (5% tool-use) | 30 calls × +$0.012 | +$0.36 |
| Realistic (25% tool-use) | 150 × +$0.012 | +$1.80 |
| Heavy (50% tool-use) | 300 × +$0.012 | +$3.60 |
| **All-on (100%)** | 600 × +$0.012 | **+$7.20** |

Reality: **+$2-7/mo** in API costs. Well within the $50/mo cap, which CEO has on hard cap (memory `project_anthropic_billing_auto_reload_disabled.md`).

This is dramatically lower than my initial estimate in the briefing (+$10-20/mo). Cause of the discrepancy: tool calls add tokens but DON'T duplicate the system prompt (cache hit). The marginal cost per tool round-trip is small.

### 5.3 Engineering cost (NOT API cost)

| Phase | Calendar weeks | Engineer-days | Notes |
|---|---|---|---|
| Phase 1 build (tools A, B, C) | 1.5 weeks | ~6 days | + API integration ~3 days |
| Phase 1 canary + tests | 0.5 week | ~3 days | 60 fixtures × 2 modes |
| Phase 2 F3-replay A/B | 1.5 weeks | ~3 days dev + 1 week wall | ~$90 API |
| Shadow rollout + observation | 2 weeks | ~1 day setup | Wall-clock observation only |
| Phase 3 promote to live | 0.5 week | ~1 day flag flip + monitor | If green |
| Phase 4 tools D, E (LanceDB) | 2-3 weeks | ~10 days | Optional, post-vision |
| **Total to live (Phases 1-3)** | **~6 weeks calendar** | **~15 engineer-days** | — |
| **Total with Phase 4** | **~9 weeks calendar** | **~25 engineer-days** | — |

This is multi-week. Honest. Not a quick win.

---

## 6. Deployment phases

### 6.1 Phase 1 — Tier-1 build (weeks 1-3)

**Engineer activities.**
1. Create `src/components/ai_tools/` module skeleton (Phase 2 below).
2. Build Tool A (`query_recent_trade_outcomes`) + tests.
3. Build Tool B (`lookup_session_volatility`) + cron baseline-snapshot script + tests.
4. Build Tool C (`check_correlation_exposure`) + tests.
5. Wire `tools=` into `PrimaryAnalyzer._call_claude` behind a feature flag (`config.ai.tool_use_enabled: false` default).
6. Update prompt with TOOL-USE block (under "## ANALYSIS WORKFLOW") instructing the AI when to use which tool.
7. Run `pytest tests/` — all must pass with feature flag OFF (i.e., zero behavior change in default).

**CEO approval needed for.** Prompt edits (WF-1). Step 6.

**Exit criteria.** All tools have ≥80% test coverage. Canary 60/60 PASS with flag OFF. Canary delta with flag ON for sanity (expect ≤2 borderline flips).

### 6.2 Phase 2 — F3-replay A/B (weeks 3-4)

**Engineer activities.**
1. Adapt `scripts/simulate_t7_live_period.py` to support tool-use mode (pass `--tool-use-enabled` flag through to `PrimaryAnalyzer`).
2. Implement DETERMINISTIC tool-execution backend for replay: tools must return what they WOULD have returned at the candle's wall-clock time, NOT current state. (E.g., `query_recent_trade_outcomes` reads only trade_records with `candle_time < replay_now`.)
3. Run 12 parallel slices, control vs tool-use arm.
4. Synthesis: pre-registered metrics, ship-gate evaluation.

**Pre-reg.** Lock in writing BEFORE running, per memory `feedback_walk_level_evidence_not_predictive.md` — pre-reg gates only.

**Exit criteria.** Pass ship gate (§4.1).

### 6.3 Phase 3 — Live shadow rollout (weeks 5-6)

**Engineer activities.**
1. Flip `config.ai.tool_use_enabled: true` BUT add `config.ai.tool_use_influence_decisions: false` — i.e., tools are CALLED and LOGGED but their outputs are OVERWRITTEN with `null` before AI sees them. (This pattern lets us measure call-rate without behavior change.)
2. Rolling restart fleet under shadow-mode flags.
3. Observe 14 days. Collect tool-call distribution, latency, error rate.
4. Compare to simulator A/B predictions. If ≥80% match: proceed.

**Exit criteria.** Tool-call rate within 50% of simulator prediction. Tool latency P99 < 2s. Error rate < 1%.

### 6.4 Phase 4 — Live tool influence + tier-2 expansion (weeks 7+)

**Engineer activities.**
1. Flip `config.ai.tool_use_influence_decisions: true`. AI now USES tool outputs.
2. Concurrent: build Tool D + E on LanceDB.
3. Evaluate against Phase 1 fleet metrics over 14-30 days. SPRT halt rule: WR drops ≥3pp → revert flag.
4. If green AND Tools D/E ready: F3-replay A/B for Tools D/E (separate sprint).

---

## 7. Risk register

| # | Risk | Severity | Likelihood | Mitigation |
|---|---|---|---|---|
| R1 | AI ignores tools (call rate <5%) | HIGH | MEDIUM | Tool description engineering; F3 A/B catches at simulator stage |
| R2 | AI over-relies on tools (call rate >70%) | MEDIUM | MEDIUM | Same; explicit "use only when uncertain" instruction |
| R3 | Tool latency degrades user-perceived perf | MEDIUM | LOW | 1-2s acceptable; ≤500ms target per tool; monitor P99 |
| R4 | Tool implementation bugs propagate to AI decisions | HIGH | MEDIUM | Comprehensive tests + Phase-3 shadow-mode (call but null-out) |
| R5 | Multi-turn complexity breaks existing retry logic | MEDIUM | MEDIUM | Wrap multi-turn loop separately; preserve current `_call_claude` for non-tool path |
| R6 | Cache invalidation bugs (system+tools cache) | MEDIUM | LOW | Pin tool-defs hash; invalidate on change |
| R7 | Sparse data → tools return n=0 frequently → AI loses confidence in tools → ignores them | MEDIUM | HIGH (current scale) | Phase 1 tools (A,B,C) don't depend on dense per-feature data; Phase 4 tools (D,E) postponed to 50-instrument scale |
| R8 | Tool output schema drift between dev/prod | MEDIUM | LOW | Pydantic-validated tool outputs; canary fixtures cover schema |
| R9 | API timeout during multi-turn cycle | MEDIUM | MEDIUM | Per-cycle timeout = 15s (vs current 60s for single call); abort + use no-tool fallback |
| R10 | Tool exposes information that shouldn't influence decisions (e.g., recent SHORT WR pre-v2-promotion) | LOW | LOW | Tool A respects detector_version filter; document in tool descriptions |
| R11 | Cost unexpectedly higher than +$2-7/mo estimate | LOW | LOW | Watchdog cap on api_calls_made; per-call budget assertion |
| R12 | Determinism in replay broken (tool returns differ in replay vs live) | HIGH | MEDIUM | Phase-2 step 2: time-travel-aware tool execution; pin clocks in tests |

### Top-3 risks to engineer around

1. **R7 (sparse data)** is the most likely deal-breaker for Phase 4 tools. Defer until 50-instrument scale, or use Tool A's lookback flexibility to compensate.
2. **R12 (replay determinism)** is the most likely root cause of false-positive A/B results. The methodology lesson from session 39 (`feedback_walk_level_evidence_not_predictive.md`) applies — pre-reg + reproducible replay matters.
3. **R1 (AI ignores tools)** is the silent killer. If F3 A/B shows 2% tool-call rate, tool-use is NOT solving anything regardless of WR numbers. Prompt engineering for tool-use language is its own sprint.

---

## 8. Open questions / known unknowns

1. **Will Sonnet 4.6 effort=max actually call tools?** Per memory `project_opus_vs_sonnet_p2c.md`, Sonnet beats Opus on the MSO gate. Anthropic's tool-use docs are model-agnostic; effort=max should not interfere. Validate empirically in Phase 1 — first canary run with flag ON.
2. **Does cache_control extend to tools= block?** Per Anthropic docs (2025): yes, tools cache. Verify by checking response.usage.cache_read_input_tokens after first call.
3. **Should tools be exposed for ALL primary analyzer calls or only CAND-borderline candles?** Cost-mitigation argument for "only when ambiguous", but adds prompt-routing complexity. Default: expose tools always; rely on AI's "use only when uncertain" discipline.
4. **Race conditions on cross-process state reads (Tool C).** 5 orchestrator processes write to their own state files; Tool C reads UNION. Currently `concurrent_tracker` writes via atomic-rename, so reads should be consistent — but verify under load.
5. **Tool D vs Phase 4 timing.** If Tool D returns n=0 80% of the time at current scale, it's dead weight. Defer until trade_records density hits some threshold (probably ~500 records per (instrument, framework) bucket).

---

## 9. Phase-2 scaffolding artifacts (delivered alongside this doc)

If time permits in this sprint, scaffolding artifacts under `src/components/ai_tools/`:

```
src/components/ai_tools/
  __init__.py                     — module marker
  README.md                       — module purpose + how to add a tool
  base.py                         — Tool ABC (input schema, output schema, execute)
  query_recent_outcomes.py        — Tool A skeleton (data-fetching logic only, no API integration)
  lookup_session_vol.py           — Tool B skeleton (placeholder for cache + computation)
  registry.py                     — TOOL_REGISTRY mapping name -> ToolDef for Anthropic API
tests/components/ai_tools/
  test_query_recent_outcomes.py   — Tool A tests (with synthetic trade_records)
  test_registry.py                — Schema validation
```

These are skeletons only — NO live wiring to `PrimaryAnalyzer._call_claude`. A future implementation agent can wire them in Phase-1 step 5 (above).

The branch `feat/tool-use-design-scaffold` will host these. NOT merged to main; reviewable artifact only.

---

## 10. Summary table for the implementation agent

| Tool | Rank | Phase | Engineering days | Expected value (AI-decay) | Hard dependency |
|---|---|---|---|---|---|
| A. query_recent_trade_outcomes | 1 | 1 | 2.5 | HIGH | A3 v1.1 records (shipped) |
| B. lookup_session_volatility | 2 | 1 | 3 | MEDIUM-HIGH | session-ATR generalization |
| C. check_correlation_exposure | 3 | 1 | 1.5 | MEDIUM | concurrent_state.json IPC |
| D. query_historical_WR | 4 | 4 | 3 (Route 1) / 7 (Route 2) | MEDIUM | data density (n≥500/bucket) |
| E. find_similar_setups | 5 | 4 | 5-7 | HIGH (faithfulness) | LanceDB schema design |

---

## 11. Decision-time summary

**Three-month outlook.** This is the right design for AI-decay specifically. Tools A+B+C address 80% of the AI-decay value at 30% of the engineering effort vs. the full 5-tool suite.

**Risk-adjusted recommendation.** Phase 1 + Phase 2 (F3-replay A/B). Total: 4-6 weeks calendar, ~$90 API. Decision-gate at end of Phase 2: ship-or-shelve with quantitative criteria. Phase 3-4 conditional on Phase 2 PASS.

**Honest caveat.** This work exists to mitigate AI-decay over months-years. If the system trades for 12 weeks under stable performance, the tool-use ROI is small. If decay materializes (per CEO's #1 concern), tool-use ROI is large. Bet on the decay scenario per memory `feedback_decay_is_ceo_number_one_concern.md`.

**Single biggest residual unknown.** Whether AI will actually CALL the tools when uncertain, vs hallucinating. F3 A/B is the only cheap way to find out. If A/B shows tool-call rate <5%, this whole design is shelved or restarted with a heavier-handed prompt that mandates tool calls (which has its own problems).

---

*End of design doc. Implementation agent: start with Phase 1 (§6.1) once CEO approves the scope. Phase 0 (this doc) complete.*
