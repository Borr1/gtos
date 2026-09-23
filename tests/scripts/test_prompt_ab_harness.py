"""Tests for L56 prompt A/B harness.

Coverage:
  - Identical prompts → zero decision-diff (sanity check)
  - Different prompts → expected divergence count
  - McNemar arithmetic on a known 2x2 table
  - Bonferroni correction across multiple metrics
  - Realized-R join correctness
  - Missing realized R → fixture excluded from R-based metrics + warning
  - --dry-run prints plan, skips API
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from scripts.research import prompt_ab_harness as harness

# Path to the bundled JSONL fixture set used as input for these tests.
FIXTURES_PATH = Path(__file__).parent / "fixtures" / "prompt_ab_test_fixtures.jsonl"
DEFAULT_METRICS_PATH = (
    Path(__file__).parents[2] / "scripts" / "research" / "metrics"
    / "prompt_ab_default.yaml"
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_prompt_file(tmp_path: Path, name: str, body: str) -> Path:
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return p


@pytest.fixture
def sample_fixtures() -> list[harness.Fixture]:
    return harness.load_fixtures(str(FIXTURES_PATH))


@pytest.fixture
def metrics_specs() -> list[dict]:
    import yaml
    with DEFAULT_METRICS_PATH.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return list(data["metrics"])


# ---------------------------------------------------------------------------
# Sanity 1 — identical prompts produce zero decision diff
# ---------------------------------------------------------------------------


def test_identical_prompts_produce_zero_diff(tmp_path, sample_fixtures):
    """Two prompts with bit-identical system text MUST produce identical
    decisions on every fixture under mocked engine (sanity #1)."""
    body = "system prompt v1: emit your standard JSON."
    p_a = _make_prompt_file(tmp_path, "prompt_a.md", body)
    p_b = _make_prompt_file(tmp_path, "prompt_b.md", body)

    bundle_a = harness.load_prompt(p_a)
    bundle_b = harness.load_prompt(p_b)

    # SHA must match → engine must produce identical outputs
    assert bundle_a.sha256 == bundle_b.sha256

    paired = harness.evaluate_pair(
        bundle_a, bundle_b, sample_fixtures, seed=42, live=False,
    )
    assert len(paired) == len(sample_fixtures)
    for r in paired:
        assert r.decision_a.decision == r.decision_b.decision
        assert r.decision_a.side == r.decision_b.side


# ---------------------------------------------------------------------------
# Sanity 2 — different prompts produce non-zero divergence
# ---------------------------------------------------------------------------


def test_different_prompts_produce_divergence(tmp_path, sample_fixtures):
    """Two prompts with different SHA must produce SOME divergent
    decisions (mocked engine derives outcome from sha + fixture). On a
    5-fixture set with the default 60% CR rate, expected divergence is
    non-zero with very high probability."""
    p_a = _make_prompt_file(tmp_path, "prompt_a.md",
                            "system prompt VARIANT-A: alpha")
    p_b = _make_prompt_file(tmp_path, "prompt_b.md",
                            "system prompt VARIANT-B: beta gamma delta")
    bundle_a = harness.load_prompt(p_a)
    bundle_b = harness.load_prompt(p_b)
    assert bundle_a.sha256 != bundle_b.sha256

    paired = harness.evaluate_pair(
        bundle_a, bundle_b, sample_fixtures, seed=1, live=False,
    )
    diffs = sum(
        1 for r in paired
        if r.decision_a.decision != r.decision_b.decision
        or r.decision_a.side != r.decision_b.side
    )
    assert diffs >= 1, (
        "Two distinct prompts should disagree on at least one of 5 fixtures "
        "under mocked engine"
    )


# ---------------------------------------------------------------------------
# McNemar arithmetic — hand-verified 2x2 table
# ---------------------------------------------------------------------------


def test_mcnemar_hand_verified_large_sample():
    """Large-sample McNemar check.
    For b=20, c=5 → chi_sq = (|20-5|-1)^2 / (20+5) = 14^2 / 25 = 196/25 = 7.84
    p_value (chi^2 1df) ≈ 0.00512 — significant at alpha=0.05.
    """
    p = harness._mcnemar(b=20, c=5)
    assert 0.004 < p < 0.007, f"unexpected McNemar p={p}"


def test_mcnemar_small_sample_uses_exact_binomial():
    """For small discordant counts (b+c < 25), McNemar should fall back to
    the exact two-sided binomial. b=2, c=0, n=2: P(K<=0|n=2,p=0.5) = 0.25,
    two-sided = 0.5 (capped at 1.0)."""
    p = harness._mcnemar(b=2, c=0)
    assert abs(p - 0.5) < 1e-9, f"unexpected small-sample McNemar p={p}"


def test_mcnemar_zero_discordant_returns_one():
    p = harness._mcnemar(b=0, c=0)
    assert p == 1.0


def test_sign_test_extremes():
    # 10 vs 0 should be highly significant: 2 * binomial(0|10,0.5)
    # = 2 * (1/1024) = 0.00195
    p = harness._sign_test(plus=10, minus=0)
    assert abs(p - 2 * (1 / 1024)) < 1e-9
    # Equal counts
    p = harness._sign_test(plus=5, minus=5)
    assert p == pytest.approx(1.0, abs=0.01)


# ---------------------------------------------------------------------------
# Bonferroni correction
# ---------------------------------------------------------------------------


def test_bonferroni_correct_counts_only_flagged_metrics(metrics_specs):
    """The default metrics YAML has 4 metrics with bonferroni_corrected:true
    (decision_label_diff, cr_rate_compare, realized_r_paired_t,
    directional_agreement). Verify the harness counts those correctly."""
    n = harness._bonferroni_correct(metrics_specs)
    assert n == 4, (
        f"Expected 4 inferential metrics, got {n}. "
        "If you edited the metrics yaml after authoring this test, that's "
        "exactly the prohibited post-hoc change CLAUDE.md flags."
    )


def test_bonferroni_correction_applied_to_alpha(tmp_path, sample_fixtures,
                                                metrics_specs):
    """When bonferroni_corrected metrics exist, alpha_bonferroni must equal
    alpha_raw / n_inferential, and significant_corrected respects it."""
    # Build the simplest case: identical prompts → all p-values 1.0,
    # nothing significant — but the alpha fields must still be populated
    p_a = _make_prompt_file(tmp_path, "a.md", "alpha system")
    p_b = _make_prompt_file(tmp_path, "b.md", "alpha system")
    bundle_a = harness.load_prompt(p_a)
    bundle_b = harness.load_prompt(p_b)
    paired = harness.evaluate_pair(bundle_a, bundle_b, sample_fixtures,
                                   seed=1, live=False)
    report = harness.compute_metrics(paired, metrics_specs,
                                     has_realized_r=False)
    assert report["bonferroni_denominator"] == 4
    for m in report["metrics"]:
        if m.get("bonferroni_corrected"):
            assert m["alpha_bonferroni"] is not None
            assert abs(m["alpha_bonferroni"] - 0.05 / 4) < 1e-12, (
                f"metric {m['name']}: bonferroni alpha was "
                f"{m['alpha_bonferroni']}, expected {0.05/4}"
            )
        else:
            assert m["alpha_bonferroni"] is None


# ---------------------------------------------------------------------------
# Realized-R join
# ---------------------------------------------------------------------------


def test_realized_r_join_matches_by_symbol_and_candle_and_side(tmp_path):
    """Synthesize a tiny all_results.json file, build the index, and
    verify lookups."""
    sim = {
        "results": [
            {
                "candle_time": "2026-01-15T13:15:00Z",
                "symbol": "XAUUSD",
                "decision": "CANDIDATE",
                "direction": "LONG",
                "r_multiple": 1.5,
            },
            {
                "candle_time": "2026-02-01T07:30:00Z",
                "symbol": "USDJPY",
                "decision": "CANDIDATE",
                "direction": "SHORT",
                "r_multiple": -1.0,
            },
        ]
    }
    sim_path = tmp_path / "all_results.json"
    sim_path.write_text(json.dumps(sim), encoding="utf-8")

    index = harness.load_realized_r_index(sim_path)

    r = harness.lookup_realized_r(index, "XAUUSD",
                                  "2026-01-15T13:15:00Z", "LONG")
    assert r == pytest.approx(1.5)

    r = harness.lookup_realized_r(index, "USDJPY",
                                  "2026-02-01T07:30:00Z", "SHORT")
    assert r == pytest.approx(-1.0)

    # Side-less fallback should also work
    r = harness.lookup_realized_r(index, "XAUUSD",
                                  "2026-01-15T13:15:00Z", None)
    assert r == pytest.approx(1.5)

    # Different timestamp → no match
    r = harness.lookup_realized_r(index, "XAUUSD",
                                  "2026-01-15T14:00:00Z", "LONG")
    assert r is None


def test_realized_r_join_microsecond_normalization(tmp_path):
    """Trade records use microsecond precision (``2026-04-15T13:15:52.698253+00:00``).
    The harness must normalize down to whole-minute UTC for joining."""
    rec = {
        "metadata": {
            "trade_id": "XAUUSD_2026-04-15_ny_1315",
            "symbol": "XAUUSD",
            "candle_time": "2026-04-15T13:15:52.698253+00:00",
        },
        "decision_pipeline": {
            "ai_decision": "CANDIDATE",
            "ai_direction": "LONG",
            "outcome": {"r_multiple": 0.75},
        },
    }
    rec_dir = tmp_path / "trade_records" / "XAUUSD"
    rec_dir.mkdir(parents=True)
    (rec_dir / "rec.json").write_text(json.dumps(rec), encoding="utf-8")

    index = harness.load_realized_r_index(tmp_path / "trade_records")
    # Lookup with second-precision timestamp must still succeed
    r = harness.lookup_realized_r(index, "XAUUSD",
                                  "2026-04-15T13:15:00Z", "LONG")
    assert r == pytest.approx(0.75)


def test_paired_results_with_realized_r_index(tmp_path, sample_fixtures):
    """End-to-end: build index, run paired eval with realized-R join."""
    sim = {
        "results": [
            {
                "candle_time": "2026-01-15T13:15:00Z",
                "symbol": "XAUUSD",
                "decision": "CANDIDATE",
                "direction": "LONG",
                "r_multiple": 2.0,
            },
        ]
    }
    sim_path = tmp_path / "sim.json"
    sim_path.write_text(json.dumps(sim), encoding="utf-8")
    index = harness.load_realized_r_index(sim_path)

    p_a = _make_prompt_file(tmp_path, "a.md", "system A")
    p_b = _make_prompt_file(tmp_path, "b.md", "system A")  # identical
    bundle_a = harness.load_prompt(p_a)
    bundle_b = harness.load_prompt(p_b)

    paired = harness.evaluate_pair(
        bundle_a, bundle_b, sample_fixtures,
        seed=1, live=False, realized_r_index=index,
    )
    # The XAU long fixture should resolve to r=2.0 IF the mock engine
    # picks LONG (deterministic via SHA). Identical prompts → A and B
    # have the same side — so either both match (and r_a=r_b=2.0) or
    # neither matches (both None).
    xau_paired = next(r for r in paired
                      if r.fixture_label == "synthetic_xau_long_jan15")
    if xau_paired.decision_a.side == "LONG":
        assert xau_paired.realized_r_a == pytest.approx(2.0)
        assert xau_paired.realized_r_b == pytest.approx(2.0)
    # The other fixtures lack a sim record → realized R must be None
    other = next(r for r in paired
                 if r.fixture_label == "synthetic_us30_no_trade_c1_fail")
    assert other.realized_r_a is None
    assert other.realized_r_b is None


# ---------------------------------------------------------------------------
# Missing realized R → fixture excluded from R metrics with warning
# ---------------------------------------------------------------------------


def test_missing_realized_r_excluded_with_warning(tmp_path, sample_fixtures,
                                                  metrics_specs, caplog):
    """When realized-R join is provided but no fixture matches, R-based
    metrics report n=0 / underpowered=true; harness logs warnings."""
    sim_path = tmp_path / "empty_sim.json"
    sim_path.write_text(json.dumps({"results": []}), encoding="utf-8")
    index = harness.load_realized_r_index(sim_path)
    assert index == {}

    p_a = _make_prompt_file(tmp_path, "a.md", "system A")
    p_b = _make_prompt_file(tmp_path, "b.md", "system B different")
    bundle_a = harness.load_prompt(p_a)
    bundle_b = harness.load_prompt(p_b)

    with caplog.at_level(logging.WARNING, logger="prompt_ab_harness"):
        paired = harness.evaluate_pair(
            bundle_a, bundle_b, sample_fixtures,
            seed=1, live=False, realized_r_index=index,
        )

    # Realized R should be None on every fixture
    for r in paired:
        assert r.realized_r_a is None
        assert r.realized_r_b is None

    report = harness.compute_metrics(paired, metrics_specs,
                                     has_realized_r=True)
    # realized_r_paired_t must be flagged underpowered (n=0 < min_sample 20)
    rt = next(m for m in report["metrics"]
              if m["name"] == "realized_r_paired_t")
    assert rt["n"] == 0
    assert rt["underpowered"] is True
    assert rt["significant_raw"] is False
    assert rt["significant_corrected"] is False


def test_realized_r_skipped_when_no_join_provided(sample_fixtures, metrics_specs):
    """When --realized-r-join is NOT provided, realized-R metrics must be
    skipped (not silently treated as zero)."""
    paired = []
    for f in sample_fixtures:
        paired.append(harness.PairedResult(
            fixture_label=f.label, symbol=f.symbol,
            candle_time=f.candle_time,
            decision_a=harness.Decision("CANDIDATE", "LONG", "{}"),
            decision_b=harness.Decision("CANDIDATE", "LONG", "{}"),
        ))
    report = harness.compute_metrics(paired, metrics_specs,
                                     has_realized_r=False)
    rt = next(m for m in report["metrics"]
              if m["name"] == "realized_r_paired_t")
    assert rt.get("skipped") is True
    assert rt.get("skip_reason") == "realized_r_join_not_provided"


# ---------------------------------------------------------------------------
# --dry-run skips API and writes nothing
# ---------------------------------------------------------------------------


def test_dry_run_skips_api_and_writes_nothing(tmp_path, capsys):
    p_a = _make_prompt_file(tmp_path, "a.md", "alpha")
    p_b = _make_prompt_file(tmp_path, "b.md", "beta")
    out_dir = tmp_path / "out_dry"
    rc = harness.main([
        "--prompt-a", str(p_a),
        "--prompt-b", str(p_b),
        "--fixtures", str(FIXTURES_PATH),
        "--metrics", str(DEFAULT_METRICS_PATH),
        "--output", str(out_dir),
        "--dry-run",
        "--seed", "7",
    ])
    assert rc == 0
    assert not out_dir.exists(), "dry-run must not create output directory"
    captured = capsys.readouterr()
    assert "DRY-RUN PLAN" in captured.out
    assert "decision_label_diff" in captured.out  # metrics listed


# ---------------------------------------------------------------------------
# End-to-end main() smoke
# ---------------------------------------------------------------------------


def test_main_writes_all_outputs(tmp_path):
    p_a = _make_prompt_file(tmp_path, "a.md", "alpha-system")
    p_b = _make_prompt_file(tmp_path, "b.md", "beta-system")
    out_dir = tmp_path / "out_run"
    rc = harness.main([
        "--prompt-a", str(p_a),
        "--prompt-b", str(p_b),
        "--fixtures", str(FIXTURES_PATH),
        "--metrics", str(DEFAULT_METRICS_PATH),
        "--output", str(out_dir),
        "--seed", "1",
    ])
    assert rc == 0
    assert (out_dir / "results.jsonl").exists()
    assert (out_dir / "metrics_report.json").exists()
    assert (out_dir / "decision_diff.md").exists()
    assert (out_dir / "run_metadata.json").exists()

    # results.jsonl must have one row per fixture
    with (out_dir / "results.jsonl").open() as fh:
        rows = [json.loads(l) for l in fh if l.strip()]
    assert len(rows) == 5

    # metrics_report.json must have all 9 metrics in the default pack
    report = json.loads((out_dir / "metrics_report.json").read_text())
    assert len(report["metrics"]) == 9
    assert report["bonferroni_denominator"] == 4
    assert report["n_fixtures"] == 5

    # decision_diff.md must reference the prompt SHAs
    diff_text = (out_dir / "decision_diff.md").read_text()
    assert "Prompt A" in diff_text
    assert "Prompt B" in diff_text


def test_yaml_prompt_with_user_template(tmp_path):
    """Prompt YAML files can include a user_template that wraps the
    fixture's user_message via {{fixture_user}} substitution."""
    yaml_body = (
        "system: |\n"
        "  System prompt header\n"
        "  Multi-line ok\n"
        "user_template: |\n"
        "  WRAPPER START\n"
        "  {{fixture_user}}\n"
        "  WRAPPER END\n"
    )
    p = tmp_path / "prompt.yaml"
    p.write_text(yaml_body, encoding="utf-8")
    bundle = harness.load_prompt(p)
    assert "System prompt header" in bundle.system
    assert bundle.user_template is not None
    rendered = bundle.render_user("FIXTURE BODY")
    assert "WRAPPER START" in rendered
    assert "FIXTURE BODY" in rendered
    assert "WRAPPER END" in rendered


def test_unknown_fixture_set_raises():
    with pytest.raises(ValueError):
        harness.load_fixtures("not_a_real_set_name")


def test_wilson_interval_basic():
    """Wilson 95% CI sanity. For p=0.5, n=100 the symmetric interval
    should be roughly (0.404, 0.596)."""
    p, lo, hi = harness._wilson_interval(50, 100)
    assert p == 0.5
    assert 0.39 < lo < 0.41
    assert 0.59 < hi < 0.61
    # Edge case: n=0
    p, lo, hi = harness._wilson_interval(0, 0)
    assert (p, lo, hi) == (0.0, 0.0, 0.0)


def test_paired_t_zero_variance():
    # All deltas identical → infinite t statistic (or 0 for zero mean)
    t, p = harness._paired_t([1.0, 1.0, 1.0])
    assert t == float("inf")
    assert p == 0.0
    t, p = harness._paired_t([0.0, 0.0])
    assert t == 0.0
    assert p == 1.0


# ---------------------------------------------------------------------------
# Pre-registration sentinel — guard against silent metric-pack edits
# ---------------------------------------------------------------------------


def test_pre_registration_sentinel(metrics_specs):
    """Pin the default metrics-pack identity. If the YAML's metrics list
    or metrics_set_id changes, this test fails — forcing the author to
    bump the metrics_set_id (i.e., commit a NEW yaml file rather than
    silently editing the existing one). This is the test-layer enforcement
    of CLAUDE.md prohibited #5 (post-hoc hypothesis formation)."""
    expected_names = [
        "decision_label_diff",
        "cr_rate_compare",
        "cr_rate_a",
        "cr_rate_b",
        "realized_r_paired_t",
        "realized_r_wilcoxon",
        "realized_r_winrate_a",
        "realized_r_winrate_b",
        "directional_agreement",
    ]
    actual_names = [m["name"] for m in metrics_specs]
    assert actual_names == expected_names, (
        f"Default metrics pack changed.\n"
        f"  expected: {expected_names}\n"
        f"  actual:   {actual_names}\n"
        "If this is intentional, bump metrics_set_id AND commit a new yaml "
        "file rather than editing the v1 file in place."
    )
