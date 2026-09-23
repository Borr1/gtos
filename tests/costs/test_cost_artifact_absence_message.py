"""Session BD (B2095) -- AS handoff 6: the exception that cost three sessions a false measurement.

`load_broker_true_costs` raised *"broker truth artifact not found at <path>. Build it with
`python3 scripts/build_broker_true_costs.py -o <path>`"* whenever the artifact was absent. The
artifact is COMMITTED. On a fresh worktree it is absent because sparse-checkout did not materialise
it, and the message told the reader to re-run a broker-truth capture.

That message has now been read by three sessions in a row -- AR (B1473), AS (handoff 6), and this
one -- each after a ~25 s substrate build, which is what AS meant by *"a failed run that reads like
an expensive measurement."* AS filed the fix as *"one line in the profile"*; that line DID land, in
`scripts/gtos_hydrate_test_data.py`. What never landed is the message, which is what a session
actually reads at the moment it is stuck, and which was actively pointing the wrong way.

The repair distinguishes the two cases with `git ls-files` and says the true thing in each.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

# Wave-21 moved the absence-path messages from the retired `_load_cached` helper
# into `load_broker_true_costs` itself; the two-way message this file pins is
# unchanged.
from src.costs.model import CostTruthError, _is_tracked_by_git, load_broker_true_costs

REPO = Path(__file__).resolve().parents[2]


def _a_tracked_but_unhydrated_path() -> str | None:
    """A path git tracks that this worktree's sparse-checkout has not materialised."""
    out = subprocess.run(
        ["git", "ls-files", "research/operations/"],
        cwd=REPO, capture_output=True, text=True, timeout=60,
    ).stdout.split("\n")
    for rel in out:
        rel = rel.strip()
        if rel and not (REPO / rel).exists():
            return rel
    return None


def test_an_untracked_missing_artifact_still_says_build_it():
    with pytest.raises(CostTruthError) as exc:
        load_broker_true_costs(REPO / "research/operations/no_such_route_2026/NOPE.json")
    msg = str(exc.value)
    assert "build_broker_true_costs.py" in msg
    assert "git does not track it" in msg
    assert "sparse" not in msg.split("If you expected")[0]


def test_a_committed_but_unhydrated_artifact_says_hydrate_not_rebuild():
    """The whole point. This message is what AR, AS and BD each needed and did not get."""
    rel = _a_tracked_but_unhydrated_path()
    if rel is None:
        pytest.skip("this worktree has every research/operations path hydrated")
    with pytest.raises(CostTruthError) as exc:
        load_broker_true_costs(REPO / rel)
    msg = str(exc.value)
    assert "COMMITTED but not checked out" in msg
    assert "gtos_hydrate_test_data.py" in msg
    assert "git sparse-checkout add" in msg
    # ...and it must NOT send the reader back to the capture.
    assert "Do NOT re-run the broker-truth capture" in msg
    assert "build_broker_true_costs.py" not in msg


def test_the_tracked_check_resolves_a_repo_relative_path():
    """The first version ran git from `path.parent` -- the directory sparse checkout had left out --
    so it silently answered "cannot tell" for the exact artifact it was written to recognise."""
    assert _is_tracked_by_git(Path("src/costs/model.py")) is True
    assert _is_tracked_by_git(REPO / "src/costs/model.py") is True
    assert _is_tracked_by_git(Path("research/operations/no_such_route_2026/NOPE.json")) is False


def test_the_check_never_raises():
    """It is on an error path. A git that is missing, slow or unhappy must not mask the real fault."""
    assert _is_tracked_by_git(Path("/nonexistent/\x00weird")) in (True, False)
    assert _is_tracked_by_git(Path("")) in (True, False)


def test_the_hydrator_carries_the_broker_truth_path():
    """AS's 'one line in the profile', asserted where it lives rather than assumed."""
    text = (REPO / "scripts/gtos_hydrate_test_data.py").read_text(encoding="utf-8")
    assert "research/operations/broker_truth_layer_2026_07_29" in text
