"""HALLUC-1 smoking-gun regression test (GBPJPY 2026-04-28 01:30 UTC).

Loads the actual production trade record at
``knowledge_base/trade_records/GBPJPY/2026-04-28_tokyo_0130.json`` (the
exact AI emission that triggered the deep-dive at
``research/halluc1_gbpjpy_deep_dive_2026-04-28/REPORT.md``), runs the
emission through the patched ``_check_h1_poi_exists`` + ``verify_candidate``
pipeline, and asserts that the routing now correctly switches to
``fvg_fill`` even though ``analysis.framework == "ob_retest"`` and
``frameworks_evaluated.fvg_fill.qualified == True``.

This is the bug-fix proof: pre-fix, the L2 routed against the empty H1
OB list and FAILED; post-fix, it routes to the M15 FVG that the AI
actually qualified.

The trade record is checked into the main repo at the standard
``knowledge_base/trade_records/GBPJPY/`` path. Tests that run inside an
isolated worktree may not see the file (worktrees don't inherit
gitignored content); when the file is missing the test SKIPs with a
clear message rather than failing — the regression check still runs
once the branch lands on main.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.components.verification import (
    _check_h1_poi_exists,
    _compute_effective_framework,
    verify_candidate,
)
from src.models.analysis_models import PrimaryAnalysisOutput
from src.models.market_state_models import MarketStateObject


_RECORD_RELATIVE = Path(
    "knowledge_base/trade_records/GBPJPY/2026-04-28_tokyo_0130.json"
)


def _resolve_trade_record_path() -> Path | None:
    """Walk up from this file looking for the repo root containing the
    GBPJPY 2026-04-28 trade record. Returns the path or ``None`` if the
    record is not present in the running checkout (worktree case).
    """
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        candidate = parent / _RECORD_RELATIVE
        if candidate.is_file():
            return candidate
    # Last resort: try the absolute project path. The standard live
    # checkout is at C:/Users/MSI/Documents/ai-trading-agent.
    fallback = Path("C:/Users/MSI/Documents/ai-trading-agent") / _RECORD_RELATIVE
    if fallback.is_file():
        return fallback
    return None


@pytest.fixture(scope="module")
def smoking_gun():
    """Load + parse the production trade record into Pydantic models.

    Returns a tuple ``(analysis, mso, raw)`` where ``raw`` is the parsed
    JSON for any test that needs to read other fields directly. SKIPs
    cleanly when the trade record is not present (worktree without
    gitignored content)."""
    path = _resolve_trade_record_path()
    if path is None:
        pytest.skip(
            "GBPJPY 2026-04-28 trade record not present in this checkout "
            "(probably an isolated worktree without gitignored "
            "knowledge_base/ content). Test runs once branch lands on main."
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    mso = MarketStateObject(**raw["mso"])
    analysis = PrimaryAnalysisOutput(**raw["ai_response"])
    return analysis, mso, raw


CONFIG = {
    "model_a": {"displacement_min_ratio": 1.5},
    "verification": {
        "enabled": True,
        "ob_price_tolerance_pct": 0.002,
        "strict_zone_check": False,
        "log_warnings": False,
    },
    "prompt": {"price_format": ".3f"},  # GBPJPY = 3 decimals
    "market": {"tick_size": 0.001},
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSmokingGunPreconditions:
    """Sanity checks — confirm the smoking-gun shape is what we expect.

    These guard against silent record drift; if the trade record is
    edited in any way that changes the bug-class signature, these
    preconditions FAIL loudly so the test author knows to refresh.
    """

    def test_wrapper_framework_is_ob_retest(self, smoking_gun):
        analysis, _, _ = smoking_gun
        assert analysis.framework == "ob_retest"

    def test_h1_setup_poi_type_is_FVG(self, smoking_gun):
        analysis, _, _ = smoking_gun
        assert analysis.reasoning.h1_setup.poi_type == "FVG"

    def test_fvg_fill_qualified_is_true(self, smoking_gun):
        analysis, _, _ = smoking_gun
        fe = analysis.frameworks_evaluated or {}
        fvg = fe.get("fvg_fill")
        assert fvg is not None
        assert fvg.qualified is True

    def test_overall_reasoning_names_fvg_fill(self, smoking_gun):
        analysis, _, _ = smoking_gun
        assert "fvg_fill" in analysis.reasoning.overall_reasoning


class TestSmokingGunRouting:
    """The actual regression: the patched routing must NOT route to
    ob_retest for this emission."""

    def test_gbpjpy_2026_04_28_tokyo_0130_routes_to_fvg_fill(self, smoking_gun):
        """End-to-end: this is the assertion line the brief asks for —
        the GBPJPY 2026-04-28 01:30 UTC emission must route to
        ``fvg_fill`` (not ``ob_retest``) and the FVG verification must
        actually run.
        """
        analysis, mso, _ = smoking_gun

        # Compute the effective framework directly to make the routing
        # decision visible in the assertion.
        effective_framework, was_overridden, routing_decision = (
            _compute_effective_framework(analysis)
        )
        assert effective_framework == "fvg_fill", (
            f"smoking-gun emission must route to fvg_fill; got "
            f"{effective_framework} (routing_decision={routing_decision})"
        )
        # Note: the smoking-gun has BOTH ob_retest.qualified=True AND
        # fvg_fill.qualified=True — the AI's reasoning explicitly says
        # ob_retest does NOT qualify (no unmitigated bullish H1 OBs)
        # but the qualified flag was emitted as True (internal
        # contradiction). Wrapper=ob_retest IS in the qualified set,
        # so the override doesn't trigger via the disagreement branch.
        # poi_type=FVG breaks the multi-qualified tie via the
        # poi_type-match path. Either way, the effective framework
        # must be fvg_fill.

    def test_full_verify_candidate_runs_fvg_fill_validation(self, smoking_gun):
        """End-to-end: the full L2 pipeline must run the
        ``entry_in_fvg`` check (NOT SKIP it), proving the routing fix
        flows through to the framework-specific validators."""
        analysis, mso, _ = smoking_gun
        result = verify_candidate(analysis, mso, CONFIG)

        c_fvg = next(c for c in result.checks if c.name == "entry_in_fvg")
        assert c_fvg.status != "SKIP", (
            "entry_in_fvg must actually execute on the smoking-gun "
            f"emission (NOT SKIP); got {c_fvg.status} - {c_fvg.detail}"
        )

        # The OB-specific checks should be SKIPPED (we routed to
        # fvg_fill). Validates that the OB-side defenses don't trigger
        # spurious FAILures on this emission.
        for skip_name in ("h1_poi_exists", "ob_zone", "entry_in_ob", "sl_beyond_ob"):
            c = next(c for c in result.checks if c.name == skip_name)
            assert c.status == "SKIP", (
                f"{skip_name} should be SKIP on fvg_fill effective branch; "
                f"got {c.status} - {c.detail}"
            )
