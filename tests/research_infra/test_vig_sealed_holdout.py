"""Known-answer tests for the sealed go-forward holdout registry."""
import os
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.research_infra.validation_integrity.sealed_holdout import (
    register_sealed_cutoff, is_sealed, assert_selection_clean, sealed_slice_summary,
)


def test_is_sealed():
    assert is_sealed("2026-07-01", "2026-06-15") is True
    assert is_sealed("2026-06-15", "2026-06-15") is False  # on the cutoff = selectable
    assert is_sealed("2025-01-01", "2026-06-15") is False


def test_assert_selection_clean_passes_and_raises():
    # clean: all selection dates <= cutoff
    assert_selection_clean(["2024-01-01", "2026-06-15"], "2026-06-15")  # no raise
    # violation: a selection date after the cutoff
    raised = False
    try:
        assert_selection_clean(["2024-01-01", "2026-07-01"], "2026-06-15")
    except ValueError:
        raised = True
    assert raised


def test_register_and_summary():
    with tempfile.TemporaryDirectory() as d:
        rp = os.path.join(d, "reg", "sealed.json")
        e = register_sealed_cutoff("2026-06-15", "post-session go-forward", rp, created_at_iso="2026-06-15")
        assert e["stamp"] and os.path.exists(rp)
        # append-only
        register_sealed_cutoff("2026-09-01", "next", rp, created_at_iso="2026-09-01")
        import json
        assert len(json.load(open(rp))) == 2
    s = sealed_slice_summary(["2025-12-31", "2026-06-15", "2026-06-20", "2026-07-10"], "2026-06-15")
    assert s["n_sealed_virgin"] == 2 and s["n_selectable"] == 2
    assert s["sealed_span"] == ("2026-06-20", "2026-07-10")


if __name__ == "__main__":
    test_is_sealed(); test_assert_selection_clean_passes_and_raises(); test_register_and_summary()
    print("sealed_holdout: 3/3 known-answer tests passed")
