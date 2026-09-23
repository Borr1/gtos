"""Unit tests for L55 incremental engine + CLI driver.

Coverage map
------------
Section 1 — ``hash_candle_inputs``
    determinism, sensitivity to relevant changes, insensitivity to irrelevant
    metadata, key-absence sentinel behavior.

Section 2 — ``hash_prompt``
    file-content sensitivity, newline normalization, error on missing file.

Section 3 — ``hash_config_subset``
    whitelist coverage: model + framework keys flip the hash, an explicitly
    non-whitelisted key (``telegram.enabled``) does NOT.

Section 4 — ``IncrementalRunPlan.compute_diff``
    100%-reuse on identical state, single-input-difference targeting, prompt
    bust, config bust, missing prior metadata = full-rerun fallback.

Section 5 — ``merge_results``
    pure (no input mutation), correct prior/fresh source per record,
    deterministic ordering, partial fresh path, NEW candle (key not in prior)
    appended.

Section 6 — CLI ``simulate_t7_incremental.py``
    --dry-run prints plan + zero subprocess spawns + writes plan.json.

Section 7 — Edge cases
    corrupt prior JSON, prior-results missing 'results' key, partial fresh
    merge, slicing with gaps.

Mockability
-----------
No real Anthropic API calls; no real T7 subprocess invocations. The CLI's
``runner`` parameter is monkeypatched to a fake that records the command list
and returns a stub `CompletedProcess`.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure project root importable.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.research_infra.incremental_engine import (  # noqa: E402
    CandleRef,
    IncrementalRunPlan,
    candle_key,
    hash_candle_inputs,
    hash_config_subset,
    hash_prompt,
    merge_results,
)
import scripts.research.simulate_t7_incremental as cli  # noqa: E402


# ════════════════════════════════════════════════════════════════════════════
# Test fixtures
# ════════════════════════════════════════════════════════════════════════════


def _baseline_record(
    candle_time: str = "2026-01-02T07:00:00Z",
    symbol: str = "XAUUSD",
    kill_zone: str = "london",
    decision: str = "CANDIDATE",
) -> dict:
    """Return a minimal but realistic candle record matching the T7 schema."""
    return {
        "candle_time": candle_time,
        "symbol": symbol,
        "kill_zone": kill_zone,
        "market_state": {
            "swings": [{"price": 2880.0, "kind": "HH"}],
            "h1_obs": [{"low": 2870.0, "high": 2872.0}],
            "fvgs": [],
        },
        "prescreen": "pass",
        "bias": "bullish",
        "bias_source": "D1+H4",
        "ob_proximity": "ok",
        "candle_close": 2879.5,
        "decision": decision,
        "cost": 0.025,
        "input_hash": None,  # set below
    }


def _baseline_record_with_hash(**overrides) -> dict:
    rec = _baseline_record(**overrides)
    rec["input_hash"] = hash_candle_inputs(rec)
    return rec


def _baseline_config() -> dict:
    """Minimal config dict that exercises every CONFIG_RELEVANT_KEYS entry
    we care about flipping. Anything not set here is treated as absent."""
    return {
        "ai": {
            "primary_model": "claude-sonnet-4-6",
            "primary_effort": "max",
            "api_timeout_seconds": 60,
        },
        "model_a": {
            "enabled_frameworks": ["ob_retest", "fvg_fill", "breaker_re_entry"],
            "bias_timeframes": ["D1", "H4"],
            "setup_timeframe": "H1",
            "entry_timeframe": "M15",
        },
        "market": {"symbol": "XAUUSD", "kill_zones": {}},
        "risk": {
            "sl_buffer_atr_multiplier": 0.25,
            "sl_buffer_breaker_atr_multiplier": 0.5,
            "sl_buffer_min_ticks": 5,
            "min_rr": 1.5,
        },
        "verification": {
            "enabled": True,
            "sl_beyond_ob_tick_floor": 1,
        },
        "gate1": {"touch_count_reject_threshold": 2},
        "session_memory_enabled": False,
        "confidence_filter_mode": "shadow",
        # Off-whitelist key — must NOT bust the hash.
        "telegram": {"enabled": True},
        "monitoring": {"dashboard_port": 8080},
    }


def _write_baseline_prior(
    tmp_path: Path,
    *,
    records: list[dict] | None = None,
    embed_meta: bool = True,
    prompt_hash: str = "PROMPT_HASH_A",
    config_hash: str = "CONFIG_HASH_A",
) -> Path:
    """Write an all_results.json fixture and return its path."""
    records = records if records is not None else [
        _baseline_record_with_hash(),
        _baseline_record_with_hash(candle_time="2026-01-02T13:30:00Z", kill_zone="ny"),
        _baseline_record_with_hash(candle_time="2026-01-03T07:15:00Z"),
    ]
    payload: dict = {
        "start": "2026-01-02",
        "end": "2026-01-03",
        "total_cost": 0.075,
        "results": records,
    }
    if embed_meta:
        payload["incremental_meta"] = {
            "prompt_hash": prompt_hash,
            "config_hash": config_hash,
        }
    p = tmp_path / "prior_all_results.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return p


def _write_prompt(tmp_path: Path, content: str = "PROMPT BODY V3\n") -> Path:
    p = tmp_path / "primary_analyzer_prompt.py"
    p.write_text(content, encoding="utf-8")
    return p


def _write_config(tmp_path: Path, config: dict | None = None) -> Path:
    import yaml
    p = tmp_path / "agent_config.yaml"
    p.write_text(yaml.safe_dump(config or _baseline_config()), encoding="utf-8")
    return p


# ════════════════════════════════════════════════════════════════════════════
# Section 1 — hash_candle_inputs
# ════════════════════════════════════════════════════════════════════════════


def test_hash_candle_inputs_is_deterministic():
    """Hashing the same record twice yields the same digest."""
    r = _baseline_record()
    h1 = hash_candle_inputs(r)
    h2 = hash_candle_inputs(r)
    assert h1 == h2
    assert len(h1) == 64
    assert all(ch in "009abcdef" for ch in h1)


def test_hash_candle_inputs_deterministic_across_dict_orders():
    """Insertion order of keys must not change the hash."""
    r1 = {"candle_time": "T1", "symbol": "XAUUSD", "kill_zone": "london",
          "market_state": {"a": 1, "b": 2}}
    r2 = {"market_state": {"b": 2, "a": 1}, "kill_zone": "london",
          "symbol": "XAUUSD", "candle_time": "T1"}
    assert hash_candle_inputs(r1) == hash_candle_inputs(r2)


def test_hash_candle_inputs_sensitive_to_market_state_change():
    """A swing-list change must produce a different hash."""
    r1 = _baseline_record()
    r2 = _baseline_record()
    r2["market_state"]["swings"] = [{"price": 2999.0, "kind": "HH"}]  # different
    assert hash_candle_inputs(r1) != hash_candle_inputs(r2)


def test_hash_candle_inputs_sensitive_to_kill_zone():
    r1 = _baseline_record(kill_zone="london")
    r2 = _baseline_record(kill_zone="ny")
    assert hash_candle_inputs(r1) != hash_candle_inputs(r2)


def test_hash_candle_inputs_sensitive_to_bias():
    r1 = _baseline_record()
    r1["bias"] = "bullish"
    r2 = _baseline_record()
    r2["bias"] = "bearish"
    assert hash_candle_inputs(r1) != hash_candle_inputs(r2)


def test_hash_candle_inputs_insensitive_to_decision_metadata():
    """Decision/cost/p2a fields are RESULTS, not inputs — must not bust hash."""
    r1 = _baseline_record(decision="CANDIDATE")
    r2 = _baseline_record(decision="REJECTED_L2")
    r2["cost"] = 999.0
    r2["p2a_decision"] = "DIFFERENT"
    r2["l2_passed"] = False
    r2["outcome"] = {"r_realized": -1.0}
    # Irrelevant timestamp / debug metadata that the engine should ignore.
    r2["generated_at"] = "2026-04-26T12:34:56Z"
    r2["debug_chunk"] = ["...", "..."]
    assert hash_candle_inputs(r1) == hash_candle_inputs(r2)


def test_hash_candle_inputs_absent_key_uses_sentinel():
    """A missing key produces a different hash from the same key set to None."""
    r1 = _baseline_record()
    del r1["bias"]                 # absent
    r2 = _baseline_record()
    r2["bias"] = None              # present but None
    assert hash_candle_inputs(r1) != hash_candle_inputs(r2)


def test_hash_candle_inputs_rejects_non_dict():
    with pytest.raises(TypeError):
        hash_candle_inputs("not a dict")  # type: ignore[arg-type]


# ════════════════════════════════════════════════════════════════════════════
# Section 2 — hash_prompt
# ════════════════════════════════════════════════════════════════════════════


def test_hash_prompt_changes_with_content(tmp_path):
    p = _write_prompt(tmp_path, "version 1")
    h1 = hash_prompt(p)
    p.write_text("version 2", encoding="utf-8")
    h2 = hash_prompt(p)
    assert h1 != h2
    assert len(h1) == len(h2) == 64


def test_hash_prompt_normalizes_newlines(tmp_path):
    """CRLF on Windows checkout vs LF on Unix must produce the same hash."""
    a = tmp_path / "lf.txt"
    b = tmp_path / "crlf.txt"
    a.write_bytes(b"line1\nline2\nline3\n")
    b.write_bytes(b"line1\r\nline2\r\nline3\r\n")
    assert hash_prompt(a) == hash_prompt(b)


def test_hash_prompt_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        hash_prompt(tmp_path / "does_not_exist.py")


def test_hash_prompt_directory_raises(tmp_path):
    with pytest.raises(IsADirectoryError):
        hash_prompt(tmp_path)


def test_hash_prompt_deterministic_across_invocations(tmp_path):
    """Same input bytes -> same hash, even invoked twice."""
    p = _write_prompt(tmp_path, "stable content\n")
    h1 = hash_prompt(p)
    h2 = hash_prompt(p)
    assert h1 == h2


# ════════════════════════════════════════════════════════════════════════════
# Section 3 — hash_config_subset
# ════════════════════════════════════════════════════════════════════════════


def test_hash_config_subset_deterministic():
    cfg = _baseline_config()
    assert hash_config_subset(cfg) == hash_config_subset(cfg)


def test_hash_config_subset_changes_when_evaluation_key_changes():
    """confidence_filter_mode is on the whitelist — must bust the hash."""
    cfg1 = _baseline_config()
    cfg2 = _baseline_config()
    cfg2["confidence_filter_mode"] = "active"
    assert hash_config_subset(cfg1) != hash_config_subset(cfg2)


def test_hash_config_subset_changes_when_framework_set_changes():
    cfg1 = _baseline_config()
    cfg2 = _baseline_config()
    cfg2["model_a"]["enabled_frameworks"] = ["ob_retest"]
    assert hash_config_subset(cfg1) != hash_config_subset(cfg2)


def test_hash_config_subset_changes_when_model_changes():
    cfg1 = _baseline_config()
    cfg2 = _baseline_config()
    cfg2["ai"]["primary_model"] = "claude-opus-4-7"
    assert hash_config_subset(cfg1) != hash_config_subset(cfg2)


def test_hash_config_subset_changes_when_min_rr_changes():
    cfg1 = _baseline_config()
    cfg2 = _baseline_config()
    cfg2["risk"]["min_rr"] = 2.0
    assert hash_config_subset(cfg1) != hash_config_subset(cfg2)


def test_hash_config_subset_invariant_to_telegram_change():
    """telegram.enabled is NOT on the whitelist — must NOT bust the hash."""
    cfg1 = _baseline_config()
    cfg2 = _baseline_config()
    cfg2["telegram"]["enabled"] = False
    cfg2["telegram"]["bot_token"] = "xyz"
    assert hash_config_subset(cfg1) == hash_config_subset(cfg2)


def test_hash_config_subset_invariant_to_monitoring_port_change():
    """monitoring.dashboard_port is NOT on the whitelist."""
    cfg1 = _baseline_config()
    cfg2 = _baseline_config()
    cfg2["monitoring"]["dashboard_port"] = 9999
    assert hash_config_subset(cfg1) == hash_config_subset(cfg2)


def test_hash_config_subset_invariant_to_unrelated_top_level_key():
    """Adding a brand-new top-level key not on the whitelist is a no-op."""
    cfg1 = _baseline_config()
    cfg2 = _baseline_config()
    cfg2["this_key_is_made_up"] = {"foo": "bar"}
    assert hash_config_subset(cfg1) == hash_config_subset(cfg2)


def test_hash_config_subset_rejects_non_dict():
    with pytest.raises(TypeError):
        hash_config_subset(["list", "not", "dict"])  # type: ignore[arg-type]


# ════════════════════════════════════════════════════════════════════════════
# Section 4 — IncrementalRunPlan.compute_diff
# ════════════════════════════════════════════════════════════════════════════


def _build_plan(tmp_path: Path, *,
                prior_records: list[dict] | None = None,
                cur_prompt: str = "PROMPT V3\n",
                cur_config: dict | None = None,
                prior_prompt_hash: str | None = None,
                prior_config_hash: str | None = None,
                embed_meta: bool = True):
    """Helper: stage tmp paths, instantiate IncrementalRunPlan, return diff."""
    prompt_path = _write_prompt(tmp_path, cur_prompt)
    config_path = _write_config(tmp_path, cur_config)
    if prior_prompt_hash is None:
        prior_prompt_hash = hash_prompt(prompt_path)
    if prior_config_hash is None:
        import yaml
        prior_cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        prior_config_hash = hash_config_subset(prior_cfg)
    prior_path = _write_baseline_prior(
        tmp_path,
        records=prior_records,
        embed_meta=embed_meta,
        prompt_hash=prior_prompt_hash,
        config_hash=prior_config_hash,
    )
    irp = IncrementalRunPlan(
        prior_results_path=prior_path,
        current_prompt_path=prompt_path,
        current_config_path=config_path,
    )
    return irp.compute_diff(), prompt_path, config_path, prior_path


def test_compute_diff_identical_state_full_reuse(tmp_path):
    """Same prompt + config + inputs => 100% reuse, zero changed candles."""
    plan, *_ = _build_plan(tmp_path)
    assert plan.n_total_candles == 3
    assert plan.n_unchanged == 3
    assert plan.n_changed == 0
    assert plan.changed_candles == []
    assert plan.reuse_ratio == 1.0
    assert plan.prompt_changed is False
    assert plan.config_changed is False


def test_compute_diff_prompt_change_busts_all(tmp_path):
    """Editing the prompt must mark every prior candle as changed."""
    # Construct a prior file whose prompt_hash does NOT match the current.
    prompt_path = _write_prompt(tmp_path, "ORIGINAL PROMPT\n")
    config_path = _write_config(tmp_path)
    import yaml
    cur_cfg_hash = hash_config_subset(yaml.safe_load(config_path.read_text(encoding="utf-8")))
    # Prior hash deliberately wrong.
    prior_path = _write_baseline_prior(
        tmp_path, prompt_hash="OUTDATED_PROMPT_HASH", config_hash=cur_cfg_hash,
    )
    plan = IncrementalRunPlan(prior_path, prompt_path, config_path).compute_diff()
    assert plan.prompt_changed is True
    assert plan.n_changed == plan.n_total_candles
    assert all(c.reason == "prompt_changed" for c in plan.changed_candles)


def test_compute_diff_config_change_busts_all(tmp_path):
    """Editing a whitelisted config key must mark every candle changed."""
    prompt_path = _write_prompt(tmp_path, "STABLE PROMPT\n")
    config_path = _write_config(tmp_path)  # baseline
    import yaml
    cur_cfg_hash = hash_config_subset(yaml.safe_load(config_path.read_text(encoding="utf-8")))
    cur_prompt_hash = hash_prompt(prompt_path)
    prior_path = _write_baseline_prior(
        tmp_path,
        prompt_hash=cur_prompt_hash,
        config_hash="OUTDATED_CONFIG_HASH",
    )
    plan = IncrementalRunPlan(prior_path, prompt_path, config_path).compute_diff()
    assert plan.config_changed is True
    assert plan.prompt_changed is False
    assert plan.n_changed == plan.n_total_candles
    assert all(c.reason == "config_changed" for c in plan.changed_candles)


def test_compute_diff_single_input_difference(tmp_path):
    """One candle's stored input_hash differs => only that one is changed."""
    rec_unchanged = _baseline_record_with_hash()
    rec_changed_input = _baseline_record(candle_time="2026-01-02T13:30:00Z", kill_zone="ny")
    # Compute the hash AFTER an alteration so the stored hash mismatches.
    rec_changed_input["input_hash"] = hash_candle_inputs(rec_changed_input)
    # Now mutate the inputs so re-hashing produces a different value.
    rec_changed_input["bias"] = "bearish"
    rec_unchanged_2 = _baseline_record_with_hash(candle_time="2026-01-03T07:15:00Z")

    plan, *_ = _build_plan(
        tmp_path,
        prior_records=[rec_unchanged, rec_changed_input, rec_unchanged_2],
    )
    assert plan.n_total_candles == 3
    assert plan.n_changed == 1
    assert plan.n_unchanged == 2
    assert plan.prompt_changed is False
    assert plan.config_changed is False
    only = plan.changed_candles[0]
    assert only.candle_time == "2026-01-02T13:30:00Z"
    assert only.kill_zone == "ny"
    assert only.reason == "input_changed"


def test_compute_diff_missing_meta_treats_as_full_rerun(tmp_path):
    """Prior payload lacking `incremental_meta` => prompt/config considered changed."""
    prompt_path = _write_prompt(tmp_path)
    config_path = _write_config(tmp_path)
    prior_path = _write_baseline_prior(tmp_path, embed_meta=False)
    plan = IncrementalRunPlan(prior_path, prompt_path, config_path).compute_diff()
    assert plan.prompt_changed is True
    assert plan.config_changed is True
    assert plan.n_changed == plan.n_total_candles


def test_compute_diff_missing_prior_results_raises(tmp_path):
    prompt_path = _write_prompt(tmp_path)
    config_path = _write_config(tmp_path)
    irp = IncrementalRunPlan(
        prior_results_path=tmp_path / "no_such.json",
        current_prompt_path=prompt_path,
        current_config_path=config_path,
    )
    with pytest.raises(FileNotFoundError):
        irp.compute_diff()


def test_compute_diff_corrupt_prior_results_raises(tmp_path):
    prompt_path = _write_prompt(tmp_path)
    config_path = _write_config(tmp_path)
    p = tmp_path / "corrupt_prior.json"
    p.write_text("{this is not valid json", encoding="utf-8")
    irp = IncrementalRunPlan(
        prior_results_path=p,
        current_prompt_path=prompt_path,
        current_config_path=config_path,
    )
    with pytest.raises(ValueError, match="not valid JSON"):
        irp.compute_diff()


def test_compute_diff_prior_missing_results_key_raises(tmp_path):
    prompt_path = _write_prompt(tmp_path)
    config_path = _write_config(tmp_path)
    p = tmp_path / "no_results_key.json"
    p.write_text(json.dumps({"start": "x", "end": "y"}), encoding="utf-8")
    irp = IncrementalRunPlan(
        prior_results_path=p,
        current_prompt_path=prompt_path,
        current_config_path=config_path,
    )
    with pytest.raises(ValueError, match="missing list-valued 'results'"):
        irp.compute_diff()


def test_compute_diff_changed_candles_sorted(tmp_path):
    """Output ordering must be deterministic (chronological)."""
    # Insert prior records out of chronological order on purpose.
    r_late = _baseline_record_with_hash(candle_time="2026-01-04T07:00:00Z")
    r_early = _baseline_record_with_hash(candle_time="2026-01-02T07:00:00Z")
    # Force prompt change so all are reported.
    prompt_path = _write_prompt(tmp_path)
    config_path = _write_config(tmp_path)
    import yaml
    cur_cfg_hash = hash_config_subset(yaml.safe_load(config_path.read_text(encoding="utf-8")))
    prior_path = _write_baseline_prior(
        tmp_path,
        records=[r_late, r_early],
        prompt_hash="OUTDATED",
        config_hash=cur_cfg_hash,
    )
    plan = IncrementalRunPlan(prior_path, prompt_path, config_path).compute_diff()
    assert [c.candle_time for c in plan.changed_candles] == [
        "2026-01-02T07:00:00Z",
        "2026-01-04T07:00:00Z",
    ]


# ════════════════════════════════════════════════════════════════════════════
# Section 5 — merge_results
# ════════════════════════════════════════════════════════════════════════════


def test_merge_results_pure_no_input_mutation():
    prior = {
        "start": "2026-01-02",
        "end": "2026-01-03",
        "total_cost": 1.0,
        "results": [
            {"candle_time": "2026-01-02T07:00:00Z", "symbol": "XAUUSD",
             "kill_zone": "london", "decision": "CAND", "cost": 0.0},
        ],
    }
    fresh = {
        "2026-01-02T07:00:00Z|XAUUSD|london": {
            "candle_time": "2026-01-02T07:00:00Z", "symbol": "XAUUSD",
            "kill_zone": "london", "decision": "REJECTED", "cost": 0.025,
        },
    }
    snapshot = json.dumps(prior, sort_keys=True)
    snapshot_fresh = json.dumps(fresh, sort_keys=True)
    merge_results(prior, fresh)
    assert json.dumps(prior, sort_keys=True) == snapshot
    assert json.dumps(fresh, sort_keys=True) == snapshot_fresh


def test_merge_results_fresh_overrides_prior():
    prior = {
        "start": "x", "end": "y", "total_cost": 0.0,
        "results": [
            {"candle_time": "T1", "symbol": "XAUUSD", "kill_zone": "london",
             "decision": "OLD"},
        ],
    }
    fresh = {
        "T1|XAUUSD|london": {
            "candle_time": "T1", "symbol": "XAUUSD", "kill_zone": "london",
            "decision": "NEW", "cost": 0.05,
        }
    }
    out = merge_results(prior, fresh)
    assert len(out["results"]) == 1
    rec = out["results"][0]
    assert rec["decision"] == "NEW"
    assert rec["incremental_source"] == "fresh"
    assert out["total_cost"] == pytest.approx(0.05)
    assert out["incremental_meta"]["n_fresh"] == 1
    assert out["incremental_meta"]["n_prior"] == 1


def test_merge_results_partial_fresh_keeps_uncovered_prior():
    """Fresh covers only one of two prior candles → other comes from prior."""
    prior = {
        "start": "x", "end": "y", "total_cost": 0.05,
        "results": [
            {"candle_time": "T1", "symbol": "XAUUSD", "kill_zone": "london",
             "decision": "OLD-A", "cost": 0.025},
            {"candle_time": "T2", "symbol": "XAUUSD", "kill_zone": "ny",
             "decision": "OLD-B", "cost": 0.025},
        ],
    }
    fresh = {
        "T2|XAUUSD|ny": {
            "candle_time": "T2", "symbol": "XAUUSD", "kill_zone": "ny",
            "decision": "FRESH-B", "cost": 0.030,
        }
    }
    out = merge_results(prior, fresh)
    # Sorted by (candle_time, symbol, kill_zone): T1 first.
    decisions = [r["decision"] for r in out["results"]]
    sources = [r["incremental_source"] for r in out["results"]]
    assert decisions == ["OLD-A", "FRESH-B"]
    assert sources == ["prior", "fresh"]


def test_merge_results_appends_new_candle():
    """A fresh key that does not exist in prior is appended as NEW."""
    prior = {
        "start": "x", "end": "y", "total_cost": 0.0,
        "results": [
            {"candle_time": "T1", "symbol": "XAUUSD", "kill_zone": "london",
             "decision": "OLD"},
        ],
    }
    fresh = {
        "T9|XAUUSD|ny": {
            "candle_time": "T9", "symbol": "XAUUSD", "kill_zone": "ny",
            "decision": "NEW", "cost": 0.04,
        }
    }
    out = merge_results(prior, fresh)
    assert len(out["results"]) == 2
    new_rec = next(r for r in out["results"] if r["candle_time"] == "T9")
    assert new_rec["incremental_source"] == "fresh"


def test_merge_results_deterministic_order():
    """Sort by (candle_time, symbol, kill_zone) regardless of input order."""
    prior = {
        "start": "x", "end": "y", "total_cost": 0.0,
        "results": [
            {"candle_time": "T3", "symbol": "GBPJPY", "kill_zone": "ny",
             "decision": "C"},
            {"candle_time": "T1", "symbol": "XAUUSD", "kill_zone": "london",
             "decision": "A"},
            {"candle_time": "T2", "symbol": "USDJPY", "kill_zone": "tokyo",
             "decision": "B"},
        ],
    }
    out = merge_results(prior, {})
    assert [r["candle_time"] for r in out["results"]] == ["T1", "T2", "T3"]


def test_merge_results_rejects_invalid_inputs():
    with pytest.raises(TypeError):
        merge_results("not a dict", {})  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        merge_results({"results": []}, "not a dict")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        merge_results({"results": "not a list"}, {})


def test_merge_results_meta_block_propagates():
    prior = {"start": "x", "end": "y", "total_cost": 0.0,
             "results": [{"candle_time": "T1", "symbol": "X", "kill_zone": "k"}]}
    fresh = {
        "T1|X|k": {"candle_time": "T1", "symbol": "X", "kill_zone": "k",
                   "decision": "DONE"},
        "__meta__": {"prompt_hash": "abc123", "config_hash": "def456"},
    }
    out = merge_results(prior, fresh)
    # __meta__ must NOT leak into results.
    assert all("decision" in r for r in out["results"])
    assert out["incremental_meta"]["prompt_hash"] == "abc123"
    assert out["incremental_meta"]["config_hash"] == "def456"


def test_merge_results_preserves_existing_source_tag():
    """If a record already has ``incremental_source``, don't overwrite it."""
    prior = {
        "start": "x", "end": "y", "total_cost": 0.0,
        "results": [
            {"candle_time": "T1", "symbol": "X", "kill_zone": "k",
             "incremental_source": "manual_override"},
        ],
    }
    out = merge_results(prior, {})
    assert out["results"][0]["incremental_source"] == "manual_override"


def test_candle_key_format():
    rec = {"candle_time": "T1", "symbol": "XAUUSD", "kill_zone": "london"}
    assert candle_key(rec) == "T1|XAUUSD|london"


# ════════════════════════════════════════════════════════════════════════════
# Section 6 — slicing
# ════════════════════════════════════════════════════════════════════════════


def test_slice_changed_candles_groups_contiguous_dates():
    cs = [
        CandleRef(candle_time="2026-01-02T07:00:00Z", symbol="X",
                  kill_zone="london", reason="prompt_changed"),
        CandleRef(candle_time="2026-01-03T07:00:00Z", symbol="X",
                  kill_zone="london", reason="prompt_changed"),
        CandleRef(candle_time="2026-01-07T07:00:00Z", symbol="X",
                  kill_zone="london", reason="prompt_changed"),
    ]
    slices = cli.slice_changed_candles(cs, max_gap_days=0)
    assert len(slices) == 2
    assert slices[0].start == date(2026, 1, 2)
    assert slices[0].end == date(2026, 1, 3)
    assert slices[1].start == date(2026, 1, 7)
    assert slices[1].end == date(2026, 1, 7)


def test_slice_changed_candles_gap_coalesce():
    """max_gap_days=2 should fuse Jan-2 and Jan-4 into one slice."""
    cs = [
        CandleRef(candle_time="2026-01-02T07:00:00Z", symbol="X",
                  kill_zone="london", reason="prompt_changed"),
        CandleRef(candle_time="2026-01-04T07:00:00Z", symbol="X",
                  kill_zone="london", reason="prompt_changed"),
    ]
    slices = cli.slice_changed_candles(cs, max_gap_days=2)
    assert len(slices) == 1
    assert slices[0].start == date(2026, 1, 2)
    assert slices[0].end == date(2026, 1, 4)


def test_slice_changed_candles_empty_input():
    assert cli.slice_changed_candles([]) == []


# ════════════════════════════════════════════════════════════════════════════
# Section 7 — CLI dry-run end to end
# ════════════════════════════════════════════════════════════════════════════


def _baseline_cli_args(tmp_path: Path) -> list[str]:
    """Stage prior+prompt+config and return argv for the CLI."""
    prompt_path = _write_prompt(tmp_path, "PROMPT V3 BODY\n")
    config_path = _write_config(tmp_path)
    import yaml
    cur_cfg_hash = hash_config_subset(yaml.safe_load(config_path.read_text(encoding="utf-8")))
    cur_prompt_hash = hash_prompt(prompt_path)
    # Identical state -> 100% reuse, no slices.
    prior_path = _write_baseline_prior(
        tmp_path, prompt_hash=cur_prompt_hash, config_hash=cur_cfg_hash,
    )
    out_dir = tmp_path / "out"
    return [
        "--prior-results", str(prior_path),
        "--prompt", str(prompt_path),
        "--config", str(config_path),
        "--start", "2026-01-02",
        "--end", "2026-01-03",
        "--symbol", "XAUUSD",
        "--output-dir", str(out_dir),
    ]


def test_cli_dry_run_exits_zero_no_subprocess(tmp_path, capsys, monkeypatch):
    """--dry-run must print plan, exit 0, and never call subprocess.run."""
    spawn_log: list = []

    def boom(*a, **kw):
        spawn_log.append((a, kw))
        raise AssertionError("subprocess must NOT be called during --dry-run")

    monkeypatch.setattr(cli.subprocess, "run", boom)

    argv = _baseline_cli_args(tmp_path) + ["--dry-run"]
    rc = cli.main(argv)
    assert rc == 0
    assert spawn_log == []
    captured = capsys.readouterr().out
    assert "INCREMENTAL T7 PLAN" in captured
    assert "DRY RUN" in captured
    # Plan file must be written.
    out_dir = next(p for i, p in enumerate(argv) if argv[i - 1] == "--output-dir")
    plan_path = Path(out_dir) / "incremental_plan.json"
    assert plan_path.exists()
    with open(plan_path) as f:
        body = json.load(f)
    assert body["plan"]["n_total_candles"] == 3
    assert body["plan"]["n_unchanged"] == 3
    assert body["plan"]["n_changed"] == 0


def test_cli_dry_run_with_changed_prompt(tmp_path, capsys, monkeypatch):
    """When prompt hash differs, dry-run plan reports n_changed > 0 + slices."""
    prompt_path = _write_prompt(tmp_path, "NEW PROMPT V4 BODY\n")
    config_path = _write_config(tmp_path)
    import yaml
    cur_cfg_hash = hash_config_subset(yaml.safe_load(config_path.read_text(encoding="utf-8")))
    prior_path = _write_baseline_prior(
        tmp_path, prompt_hash="OUTDATED_PROMPT", config_hash=cur_cfg_hash,
    )
    out_dir = tmp_path / "out_changed"

    def boom(*a, **kw):
        raise AssertionError("no subprocess")
    monkeypatch.setattr(cli.subprocess, "run", boom)

    rc = cli.main([
        "--prior-results", str(prior_path),
        "--prompt", str(prompt_path),
        "--config", str(config_path),
        "--start", "2026-01-02",
        "--end", "2026-01-03",
        "--symbol", "XAUUSD",
        "--output-dir", str(out_dir),
        "--dry-run",
    ])
    assert rc == 0
    plan_path = out_dir / "incremental_plan.json"
    body = json.loads(plan_path.read_text())
    assert body["plan"]["prompt_changed"] is True
    assert body["plan"]["n_changed"] == body["plan"]["n_total_candles"]
    assert len(body["slices"]) >= 1


def test_cli_bad_dates_exits_2(tmp_path, monkeypatch):
    argv = _baseline_cli_args(tmp_path)
    # Replace --end with a string that is before --start.
    end_idx = argv.index("--end")
    argv[end_idx + 1] = "2026-01-01"
    start_idx = argv.index("--start")
    argv[start_idx + 1] = "2026-04-13"
    rc = cli.main(argv + ["--dry-run"])
    assert rc == 2


def test_cli_missing_prior_exits_2(tmp_path, monkeypatch):
    prompt_path = _write_prompt(tmp_path)
    config_path = _write_config(tmp_path)
    out_dir = tmp_path / "out"
    rc = cli.main([
        "--prior-results", str(tmp_path / "does_not_exist.json"),
        "--prompt", str(prompt_path),
        "--config", str(config_path),
        "--start", "2026-01-02",
        "--end", "2026-01-03",
        "--symbol", "XAUUSD",
        "--output-dir", str(out_dir),
        "--dry-run",
    ])
    assert rc == 2


# ════════════════════════════════════════════════════════════════════════════
# Section 8 — CLI live path (mocked subprocess)
# ════════════════════════════════════════════════════════════════════════════


class _FakeCompletedProcess:
    def __init__(self, returncode=0):
        self.returncode = returncode


def test_cli_live_path_invokes_subprocess_per_slice(tmp_path, monkeypatch):
    """When NOT --dry-run + plan has slices, one subprocess.run per slice."""
    # Build a plan with prompt change so all 3 prior candles are flagged.
    prompt_path = _write_prompt(tmp_path, "PROMPT V4 NEW\n")
    config_path = _write_config(tmp_path)
    import yaml
    cur_cfg_hash = hash_config_subset(yaml.safe_load(config_path.read_text(encoding="utf-8")))
    # Three candles spread over 3 dates so slicing should make 3 contiguous-but-
    # separate ranges (gaps of 0 days between Jan-2 and Jan-3 = same slice;
    # Jan-3 to Jan-4 = same slice). Force gaps with non-contiguous dates.
    rec_a = _baseline_record_with_hash(candle_time="2026-01-02T07:00:00Z")
    rec_b = _baseline_record_with_hash(candle_time="2026-01-05T07:00:00Z")
    rec_c = _baseline_record_with_hash(candle_time="2026-01-09T07:00:00Z")
    prior_path = _write_baseline_prior(
        tmp_path, records=[rec_a, rec_b, rec_c],
        prompt_hash="OUTDATED", config_hash=cur_cfg_hash,
    )
    out_dir = tmp_path / "out_live"

    spawn_log: list[list[str]] = []
    fake_outputs: dict[str, dict] = {}

    def fake_run(cmd, stdout=None, stderr=None, cwd=None):
        spawn_log.append(list(cmd))
        # Write the synthetic per-slice all_results.json that the inner sim
        # would have produced.
        out_idx = cmd.index("--output-dir") + 1
        per_slice_dir = Path(cmd[out_idx])
        per_slice_dir.mkdir(parents=True, exist_ok=True)
        start_idx = cmd.index("--start") + 1
        end_idx = cmd.index("--end") + 1
        slice_start = cmd[start_idx]
        slice_end = cmd[end_idx]
        # Synthetic: emit one record matching the slice's date.
        record = {
            "candle_time": f"{slice_start}T07:00:00Z",
            "symbol": "XAUUSD",
            "kill_zone": "london",
            "decision": "FRESH",
            "cost": 0.025,
        }
        payload = {
            "start": slice_start, "end": slice_end, "total_cost": 0.025,
            "results": [record],
        }
        with open(per_slice_dir / "all_results.json", "w") as f:
            json.dump(payload, f)
        fake_outputs[per_slice_dir.name] = payload
        return _FakeCompletedProcess(returncode=0)

    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    rc = cli.main([
        "--prior-results", str(prior_path),
        "--prompt", str(prompt_path),
        "--config", str(config_path),
        "--start", "2026-01-02",
        "--end", "2026-01-09",
        "--symbol", "XAUUSD",
        "--output-dir", str(out_dir),
    ])
    assert rc == 0
    # 3 contiguous-date slices (each candle on a separate date with gaps).
    assert len(spawn_log) == 3
    # Consolidated file should exist.
    consolidated = list(out_dir.glob("incremental_XAUUSD_*.json"))
    assert len(consolidated) == 1
    body = json.loads(consolidated[0].read_text())
    assert body["incremental_meta"]["n_fresh"] == 3
    # Source tags must reflect provenance.
    sources = [r["incremental_source"] for r in body["results"]]
    assert sources == ["fresh", "fresh", "fresh"]


def test_cli_live_path_handles_failed_slice(tmp_path, monkeypatch):
    """A failing inner subprocess must exit 1 but still produce a merged file."""
    prompt_path = _write_prompt(tmp_path, "PROMPT V4 NEW\n")
    config_path = _write_config(tmp_path)
    import yaml
    cur_cfg_hash = hash_config_subset(yaml.safe_load(config_path.read_text(encoding="utf-8")))
    rec_a = _baseline_record_with_hash(candle_time="2026-01-02T07:00:00Z")
    prior_path = _write_baseline_prior(
        tmp_path, records=[rec_a],
        prompt_hash="OUTDATED", config_hash=cur_cfg_hash,
    )
    out_dir = tmp_path / "out_fail"

    def fake_run(cmd, stdout=None, stderr=None, cwd=None):
        # Don't write the output JSON; simulate a crash.
        return _FakeCompletedProcess(returncode=137)
    monkeypatch.setattr(cli.subprocess, "run", fake_run)

    rc = cli.main([
        "--prior-results", str(prior_path),
        "--prompt", str(prompt_path),
        "--config", str(config_path),
        "--start", "2026-01-02",
        "--end", "2026-01-02",
        "--symbol", "XAUUSD",
        "--output-dir", str(out_dir),
    ])
    assert rc == 1
    consolidated = list(out_dir.glob("incremental_XAUUSD_*.json"))
    assert len(consolidated) == 1
    body = json.loads(consolidated[0].read_text())
    assert "failed_slices" in body["incremental_meta"]
    assert body["incremental_meta"]["failed_slices"][0]["returncode"] == 137
    # Prior record stays in the merged output.
    assert any(r["incremental_source"] == "prior" for r in body["results"])
