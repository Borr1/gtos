# GTOS research infrastructure (Phase 1)
"""50-eval Haiku-vs-Sonnet A/B quality check (mocked-by-default).

Purpose
-------
Before promoting any non-trading task type from Sonnet 4.6 to Haiku 4.5
in :mod:`src.research_infra.model_router`, we need empirical evidence
that Haiku reaches an acceptable agreement rate on a representative
fixture set. This harness implements that A/B for **one task type at a
time** (default: ``regime_classification``).

Modes
-----
* **Mocked mode (default)**: each "model" is replaced with a
  deterministic stochastic mock that emits labels under a documented
  probability distribution centered on the fixture's ``expected_label``.
  This verifies the harness scaffolding (loading, scoring, summary
  output, cost estimation arithmetic) without burning any API credit.
  This is the mode the harness is shipped to run in.

* **Live mode (``--live``)**: would dispatch real Haiku + Sonnet calls.
  **This script intentionally REFUSES to run --live in this commit.**
  Live runs require (a) explicit CEO authorization for the API spend,
  (b) production-faithful prompt templates not yet wired here, and
  (c) the cost-tracking wrapper from T0.2. The flag is parsed only so
  the help text documents future capability.

Output
------
A summary block printed to stdout + a JSON file alongside the fixtures::

    {
      "task_type": "regime_classification",
      "mode": "mocked",
      "n_evals": 52,
      "agreement_rate_haiku_vs_expected": 0.79,
      "agreement_rate_sonnet_vs_expected": 0.92,
      "agreement_rate_haiku_vs_sonnet": 0.81,
      "disagreement_breakdown": {
        "trending_bull->trending_bear": 1,
        ...
      },
      "estimated_cost_usd": {"sonnet": 0.18, "haiku": 0.012},
      "router_decision": "router_promotion_threshold (>=0.85) MET? false"
    }

Promotion gate (suggested, not enforced here): Haiku-vs-Sonnet agreement
rate >= 0.85 on >= 50 evaluations before flipping the routing entry in
``DEFAULT_ROUTING_TABLE``. Operator records the result in the README's
A/B validation log.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Optional

# Make ``src`` importable when this script is invoked directly via
# ``python scripts/research/haiku_quality_check.py``.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research_infra.model_router import (  # noqa: E402
    DEFAULT_ROUTING_TABLE,
    ModelRouter,
    TaskType,
    VALID_TASK_TYPES,
)

logger = logging.getLogger("haiku_quality_check")

# ---------------------------------------------------------------------------
# Mocked-mode probability model
# ---------------------------------------------------------------------------
#
# Each model is simulated by drawing labels from a categorical
# distribution. Sonnet has higher accuracy (closer to the
# ``expected_label``); Haiku has measurable degradation we can flag.
# These numbers are **not** a forecast — they exist to exercise the
# harness scoring + summary code on plausible-shaped inputs. Real-API
# values will replace them when the live mode is unlocked.
#
# Format: ``{model_key: {"correct": p_correct, "neighbour": p_neighbour, "wrong": p_wrong}}``
# where the leftover mass after ``correct + neighbour`` is split
# uniformly across all *other* labels.
_MOCK_AGREEMENT_PROBS = {
    "sonnet": {"correct": 0.92, "neighbour": 0.05},
    "haiku":  {"correct": 0.79, "neighbour": 0.12},
}

# Approximate per-call cost (USD) — order-of-magnitude only, used to
# populate ``estimated_cost_usd`` in the summary. Real values come from
# T0.2 cost tracking when live mode is unlocked.
_APPROX_COST_PER_CALL_USD = {
    "sonnet": 0.0035,
    "haiku":  0.00023,
}

# When mocked-Haiku draws a "neighbour" mistake, prefer these substitutes
# (the kinds of confusions a fast model is most likely to make).
_NEIGHBOUR_MAP = {
    "trending_bull": "reversal_in_progress",
    "trending_bear": "reversal_in_progress",
    "chop": "unclear",
    "reversal_in_progress": "trending_bull",
    "unclear": "chop",
}


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass
class FixtureRow:
    id: str
    instrument: str
    session: str
    features: dict
    expected_label: str
    rationale: str

    @classmethod
    def from_json(cls, obj: dict) -> "FixtureRow":
        return cls(
            id=obj["id"],
            instrument=obj["instrument"],
            session=obj["session"],
            features=obj["features"],
            expected_label=obj["expected_label"],
            rationale=obj.get("rationale", ""),
        )


@dataclass
class ABResult:
    task_type: str
    mode: str
    n_evals: int
    agreement_rate_haiku_vs_expected: float
    agreement_rate_sonnet_vs_expected: float
    agreement_rate_haiku_vs_sonnet: float
    disagreement_breakdown: dict
    estimated_cost_usd: dict
    router_target_model: str
    router_target_effort: str
    promotion_threshold: float
    promotion_threshold_met: bool


# ---------------------------------------------------------------------------
# Mocked label "models"
# ---------------------------------------------------------------------------


def _mock_predict(model_key: str, expected_label: str, rng: random.Random) -> str:
    """Deterministic-stochastic label predictor for mocked mode.

    ``model_key`` must be ``"sonnet"`` or ``"haiku"``.

    The rng is the *only* source of non-determinism — pass a seeded
    ``random.Random`` for reproducible runs.
    """
    probs = _MOCK_AGREEMENT_PROBS[model_key]
    p_correct = probs["correct"]
    p_neighbour = probs["neighbour"]
    p_wrong = max(0.0, 1.0 - p_correct - p_neighbour)

    roll = rng.random()
    if roll < p_correct:
        return expected_label
    if roll < p_correct + p_neighbour:
        return _NEIGHBOUR_MAP.get(expected_label, "unclear")
    # Wrong: pick uniformly from the *other* labels (not expected, not neighbour)
    pool = [
        label
        for label in (
            "trending_bull",
            "trending_bear",
            "chop",
            "reversal_in_progress",
            "unclear",
        )
        if label != expected_label
        and label != _NEIGHBOUR_MAP.get(expected_label, "unclear")
    ]
    if not pool:  # pragma: no cover — safety net
        return expected_label
    # Use a separate roll to keep the categorical clean
    idx = int(rng.random() * len(pool))
    return pool[idx]


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------


def load_fixtures(path: Path) -> list[FixtureRow]:
    """Load JSONL fixtures from disk.

    Each line must be a JSON object with keys ``id``, ``instrument``,
    ``session``, ``features``, ``expected_label``, ``rationale``.
    Comment lines / blank lines are ignored.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Fixture file not found: {path}. "
            "Did you run the harness from the repo root?"
        )

    rows: list[FixtureRow] = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError as e:
            raise ValueError(f"Malformed fixture at line {lineno}: {e}") from e
        rows.append(FixtureRow.from_json(obj))
    return rows


def run_ab(
    fixtures: Iterable[FixtureRow],
    task_type: TaskType,
    *,
    mode: str = "mocked",
    seed: int = 1729,
    promotion_threshold: float = 0.85,
) -> ABResult:
    """Run the A/B agreement check over the provided fixtures.

    Parameters
    ----------
    fixtures:
        Iterable of :class:`FixtureRow`.
    task_type:
        TaskType key — used to look up the routing-table target so the
        summary records *which* Haiku target is being validated.
    mode:
        ``"mocked"`` (default) or ``"live"``. Live mode is intentionally
        unsupported here; passing it raises ``NotImplementedError``.
    seed:
        RNG seed for the mocked predictors. Same seed -> same labels.
    promotion_threshold:
        Threshold for ``promotion_threshold_met`` in the result. Default
        0.85 matches the suggested A/B gate documented in the module
        docstring.

    Returns
    -------
    ABResult
    """
    if mode == "live":  # pragma: no cover - guarded entry point
        raise NotImplementedError(
            "Live A/B mode is intentionally disabled in this commit. "
            "Re-running this harness against the real API requires "
            "(a) explicit CEO authorization for the spend, "
            "(b) production-faithful prompt templates wired here, and "
            "(c) the T0.2 cost-tracking wrapper. None are present yet."
        )
    if mode != "mocked":
        raise ValueError(
            f"Unknown mode {mode!r}. Valid values: 'mocked' (only)."
        )

    rows = list(fixtures)
    if not rows:
        raise ValueError("No fixtures provided — refusing to run on empty input.")

    rng_sonnet = random.Random(seed)
    rng_haiku = random.Random(seed + 1)

    matches_sonnet = 0
    matches_haiku = 0
    matches_haiku_vs_sonnet = 0
    disagreement_counter: Counter[str] = Counter()

    for row in rows:
        sonnet_pred = _mock_predict("sonnet", row.expected_label, rng_sonnet)
        haiku_pred = _mock_predict("haiku", row.expected_label, rng_haiku)

        if sonnet_pred == row.expected_label:
            matches_sonnet += 1
        if haiku_pred == row.expected_label:
            matches_haiku += 1
        if haiku_pred == sonnet_pred:
            matches_haiku_vs_sonnet += 1
        else:
            disagreement_counter[f"{sonnet_pred}->{haiku_pred}"] += 1

    n = len(rows)
    haiku_vs_expected = matches_haiku / n
    sonnet_vs_expected = matches_sonnet / n
    haiku_vs_sonnet = matches_haiku_vs_sonnet / n

    # Costs are *summary-only* — mocked runs never spend.
    est_cost_sonnet = round(_APPROX_COST_PER_CALL_USD["sonnet"] * n, 4)
    est_cost_haiku = round(_APPROX_COST_PER_CALL_USD["haiku"] * n, 4)

    target = DEFAULT_ROUTING_TABLE[task_type]

    return ABResult(
        task_type=task_type,
        mode=mode,
        n_evals=n,
        agreement_rate_haiku_vs_expected=round(haiku_vs_expected, 4),
        agreement_rate_sonnet_vs_expected=round(sonnet_vs_expected, 4),
        agreement_rate_haiku_vs_sonnet=round(haiku_vs_sonnet, 4),
        disagreement_breakdown=dict(disagreement_counter),
        estimated_cost_usd={
            "sonnet": est_cost_sonnet,
            "haiku": est_cost_haiku,
        },
        router_target_model=target.model_id,
        router_target_effort=target.effort,
        promotion_threshold=promotion_threshold,
        promotion_threshold_met=haiku_vs_sonnet >= promotion_threshold,
    )


def render_summary(result: ABResult) -> str:
    """Render the A/B result as a human-readable summary block."""
    lines = [
        "=" * 64,
        "Haiku quality A/B summary",
        "=" * 64,
        f"  task_type            : {result.task_type}",
        f"  mode                 : {result.mode}",
        f"  n_evals              : {result.n_evals}",
        f"  router target model  : {result.router_target_model}",
        f"  router target effort : {result.router_target_effort}",
        "",
        f"  Sonnet vs expected   : {result.agreement_rate_sonnet_vs_expected:.3f}",
        f"  Haiku  vs expected   : {result.agreement_rate_haiku_vs_expected:.3f}",
        f"  Haiku  vs Sonnet     : {result.agreement_rate_haiku_vs_sonnet:.3f}",
        "",
        f"  Promotion threshold  : {result.promotion_threshold:.3f} "
        f"({'MET' if result.promotion_threshold_met else 'NOT MET'})",
        "",
        f"  Estimated cost USD   : Sonnet=${result.estimated_cost_usd['sonnet']:.4f} "
        f"Haiku=${result.estimated_cost_usd['haiku']:.4f}",
        "",
        "  Disagreement breakdown (Sonnet -> Haiku):",
    ]
    if not result.disagreement_breakdown:
        lines.append("    (none)")
    else:
        for k, v in sorted(
            result.disagreement_breakdown.items(), key=lambda kv: -kv[1]
        ):
            lines.append(f"    {k:<40s} {v}")
    lines.append("=" * 64)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="haiku_quality_check",
        description="50-eval Haiku-vs-Sonnet A/B quality check (mocked).",
    )
    p.add_argument(
        "--task-type",
        default="regime_classification",
        choices=list(VALID_TASK_TYPES),
        help="Which routing-table entry to validate (default: regime_classification).",
    )
    p.add_argument(
        "--fixtures",
        type=Path,
        default=None,
        help="Path to a JSONL fixture file. Default: scripts/research/fixtures/{task_type}_50.jsonl",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=1729,
        help="RNG seed for the mocked predictors (default: 1729).",
    )
    p.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Promotion threshold for Haiku-vs-Sonnet agreement (default: 0.85).",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Where to write the summary JSON. Default: alongside the fixture file.",
    )
    p.add_argument(
        "--live",
        action="store_true",
        help="Use the live API. INTENTIONALLY DISABLED in this commit — "
             "raises NotImplementedError. See module docstring.",
    )
    return p.parse_args(argv)


def _default_fixture_path(task_type: str) -> Path:
    return _REPO_ROOT / "scripts" / "research" / "fixtures" / f"{task_type}_50.jsonl"


def main(argv: Optional[list[str]] = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    args = _parse_args(argv)

    # Defense in depth: even if the user passes --live we refuse here
    # before any fixture work, with a clear message + non-zero exit.
    if args.live:
        # Belt-and-braces: also require an env var that we never set.
        # The agent running this harness MUST NOT call --live mode.
        if not os.environ.get("GTOS_HAIKU_QUALITY_CHECK_ALLOW_LIVE"):
            logger.error(
                "--live mode is intentionally disabled. To re-enable in "
                "the future, set GTOS_HAIKU_QUALITY_CHECK_ALLOW_LIVE=1 "
                "and wire production-faithful prompts + cost tracking "
                "(T0.2). For now, run without --live (mocked mode)."
            )
            return 2
        raise NotImplementedError(
            "Live A/B mode is intentionally disabled in this commit."
        )

    fixtures_path = args.fixtures or _default_fixture_path(args.task_type)
    fixtures = load_fixtures(fixtures_path)
    logger.info(
        "Loaded %d fixtures from %s for task_type=%s",
        len(fixtures),
        fixtures_path,
        args.task_type,
    )

    # Sanity-check the routing table before running — surfaces any
    # accidental tampering of the immutable trading_decision entry
    # before we burn (mocked) compute.
    ModelRouter()  # constructor raises if DEFAULT_ROUTING_TABLE is broken

    result = run_ab(
        fixtures,
        args.task_type,
        mode="mocked",
        seed=args.seed,
        promotion_threshold=args.threshold,
    )

    summary = render_summary(result)
    print(summary)

    out_path = args.out or fixtures_path.with_suffix(".ab_summary.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(asdict(result), indent=2), encoding="utf-8")
    logger.info("A/B summary written to %s", out_path)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
