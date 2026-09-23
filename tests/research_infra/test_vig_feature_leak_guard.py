"""test_vig_feature_leak_guard.py — the feature-level causal lookahead guard discriminates clean vs leaky.

Proves: causal_probe CLEANs a backward-only feature + FLAGS a future-reading feature; the token contract
passes clean classes + flags dirty/empty; certify_feature_causal fails-closed on a leak.
"""
import sys
# NOTE 2026-07-26: a hardcoded sys.path.insert(0, "/Users/borr/Documents/gtos/repo/
# ai-trading-agent") was removed here. It prepended a DIFFERENT, stale checkout, so this
# file silently tested that repo instead of the working tree whenever it ran in isolation
# (in a full-suite run sys.modules was already populated, so the same tests exercised the
# real code and could disagree). Tests must import the tree they are checked out in.
from src.components.ultimate_book.primitives import Bar
from src.research_infra.validation_integrity.feature_leak_guard import (
    causal_probe, assert_filter_source_clean, certify_feature_causal)

# deterministic synthetic series
BARS = [Bar(100 + k * 0.1, 100 + k * 0.1 + 0.5, 100 + k * 0.1 - 0.5, 100 + k * 0.1 + 0.05, 100) for k in range(200)]
SAMPLES = [(BARS, i) for i in range(50, 170, 10)]   # interior indices with future bars to poison


def feat_trailing_mean(bars, i, n=10):      # CAUSAL: only bars <= i
    lo = max(0, i - n + 1)
    return sum(bars[k].c for k in range(lo, i + 1)) / (i - lo + 1)


def feat_future_return(bars, i, h=5):       # LEAKY: reads bar i+h
    j = min(i + h, len(bars) - 1)
    return bars[j].c - bars[i].c


def feat_centered_ma(bars, i, n=10):        # LEAKY: uses n bars each side
    lo = max(0, i - n); hi = min(len(bars) - 1, i + n)
    return sum(bars[k].c for k in range(lo, hi + 1)) / (hi - lo + 1)


def test_causal_probe_passes_backward_only_feature():
    for bars, i in SAMPLES:
        verdict, _ = causal_probe(feat_trailing_mean, bars, i)
        assert verdict == "CLEAN", f"backward-only feature must be CLEAN at i={i}"


def test_causal_probe_flags_future_reading_features():
    for fn in (feat_future_return, feat_centered_ma):
        verdict, det = causal_probe(fn, BARS, 100)
        assert verdict == "LOOKAHEAD", f"{fn.__name__} reads the future -> must be flagged; got {det}"


def test_token_contract_passes_clean_flags_dirty_and_empty():
    for clean in ("selector", "market_state", "cost", "lifecycle", "source_completeness"):
        assert assert_filter_source_clean(clean) is None, f"{clean} should pass"
    for dirty in ("x_outcome_y", "realized_pnl", "post_decision_result", "hindsight_signal", "result_row_feat"):
        assert assert_filter_source_clean(dirty) is not None, f"{dirty} should be flagged"
    assert assert_filter_source_clean("") is not None and assert_filter_source_clean(None) is not None


def test_certify_fails_closed_on_leak_passes_clean():
    ok = certify_feature_causal(feat_trailing_mean, SAMPLES, evidence_class="market_state")
    assert ok["passed"] is True and ok["lookahead"] == 0 and ok["clean"] > 0
    bad = certify_feature_causal(feat_future_return, SAMPLES, evidence_class="market_state")
    assert bad["passed"] is False and bad["lookahead"] > 0 and bad["first_flag"] is not None
    dirty = certify_feature_causal(feat_trailing_mean, SAMPLES, evidence_class="realized_outcome")
    assert dirty["passed"] is False and dirty["token_violation"] is not None   # clean feature, dirty class -> fail


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    p = 0
    for fn in fns:
        try:
            fn(); p += 1; print(f"PASS {fn.__name__}")
        except Exception:
            print(f"FAIL {fn.__name__}"); traceback.print_exc()
    print(f"\n{p}/{len(fns)} feature-leak-guard tests passed")
    assert p == len(fns)
