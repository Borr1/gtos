"""Regression and characterisation tests from the Opus-5 architecture audit.

Two kinds of test live here.

**Hardening tests** pin a defect that this audit *fixed*. They fail if the fix
is reverted.

**Characterisation tests** pin a defect this audit deliberately did **not**
fix, because fixing it would change accepted sealed evidence. They document the
current behaviour precisely so it cannot change by accident, and they name the
finding id in `docs/audits/opus5-architecture-20260725/MISMATCH_AND_RISK_REGISTER.md`.

Run: `python3 -m pytest tests/test_opus5_architecture_audit_hardening.py -q`
"""

from __future__ import annotations

import ast
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


# ---------------------------------------------------------------------------
# R-P1 (hardening): the semantic-parity comparators must fail closed on
# non-finite economic values instead of comparing NaN==NaN byte-equal.
# ---------------------------------------------------------------------------

# Only replay_semantic_parity could be repaired: the other two comparators are
# SHA-256-bound in the sealed decision contract (finding R37), so editing them
# fails the next replay closed. See test_characterise_contract_bound_comparators.
PARITY_MODULES = ("src.research_infra.replay_semantic_parity",)


@pytest.mark.parametrize("module_name", PARITY_MODULES)
def test_parity_canonical_bytes_rejects_non_finite(module_name: str) -> None:
    """NaN/Infinity must raise, not serialise to a byte-equal token.

    Before the fix all three used ``allow_nan=True``. Because parity is byte
    equality, two runs that both produced ``NaN`` in an economic field compared
    EQUAL and the comparator reported zero differences — while every one of the
    28 sealing encoders raised on the same input.
    """
    module = __import__(module_name, fromlist=["canonical_bytes"])
    from src.research_infra.replay_canonical_bytes import NonFiniteCanonicalValueError

    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(NonFiniteCanonicalValueError) as excinfo:
            module.canonical_bytes({"symbol": "NAS100", "final_r": bad})
        assert "final_r" in str(excinfo.value)


def test_parity_canonical_bytes_matches_sealing_signature() -> None:
    """The comparison encoder and the sealing encoder must agree byte-for-byte."""
    from src.research_infra import replay_acceleration_fresh_source_authority as sealing
    from src.research_infra import replay_semantic_parity as parity

    payload = {
        "b": [1, 2.5, {"z": None, "a": True}],
        "a": "ünïcode",
        "n": 1.0000000000001,
    }
    assert parity.canonical_bytes(payload) == sealing.canonical_json_bytes(payload)


def test_parity_difference_paths_no_longer_silently_equates_nan() -> None:
    """The regression itself: two NaN rows must not report zero differences."""
    from src.research_infra import replay_semantic_parity as parity
    from src.research_infra.replay_canonical_bytes import NonFiniteCanonicalValueError

    row = {"final_r": float("nan"), "symbol": "NAS100"}
    with pytest.raises(NonFiniteCanonicalValueError):
        parity._difference_paths(dict(row), dict(row))


def test_non_finite_paths_reports_every_offending_leaf() -> None:
    from src.research_infra.replay_canonical_bytes import non_finite_paths

    payload = {
        "ok": 1.0,
        "nested": {"bad": float("inf")},
        "rows": [{"r": float("nan")}, {"r": 2.0}],
    }
    paths = non_finite_paths(payload)
    assert any(p.startswith("$.nested.bad=") for p in paths)
    assert any(p.startswith("$.rows[0].r=") for p in paths)
    assert len(paths) == 2


# ---------------------------------------------------------------------------
# R7 (hardening): create_mt5 must not default an unknown mode to a real broker.
# ---------------------------------------------------------------------------


def test_create_mt5_rejects_unknown_mode() -> None:
    """`else: return RealMT5(...)` meant `create_mt5("mok")` opened a real
    terminal. Unknown modes must fail closed."""
    from src.mt5 import create_mt5

    for bad in ("mok", "simulate", "", "LIVE", "paper"):
        with pytest.raises(ValueError, match="unknown mt5 mode"):
            create_mt5(bad)


def test_create_mt5_mock_still_works() -> None:
    from src.mt5 import create_mt5
    from src.mt5.mt5_mock import MockMT5

    assert isinstance(create_mt5("mock", balance=25_000.0), MockMT5)


def test_every_create_mt5_caller_uses_a_known_mode() -> None:
    """Guard the fix: no caller may pass a mode outside the accepted set.

    Parses the call sites instead of shelling out to `rg`. The old form ran
    ``subprocess.run(["rg", ...])`` and `rg` is not an executable on every machine
    that runs this suite -- on this one it is a shell function, so the call raised
    ``FileNotFoundError`` and the test reported an environment fact as a defect.
    The AST is also strictly better at the job: the regex could only see a mode that
    was the FIRST thing inside the parentheses and written with double quotes, so
    ``create_mt5(balance=1, mode='live')`` was invisible to it.
    """
    import ast

    from src.mt5 import _REAL_MODES

    accepted = {"mock", *_REAL_MODES}
    here = Path(__file__).name
    tracked = subprocess.run(
        ["git", "ls-files", "--", "*.py"],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout.split()

    literals: dict[str, str] = {}
    for relative in tracked:
        # This file deliberately passes bad modes to assert they are refused.
        if Path(relative).name == here:
            continue
        path = REPO / relative
        if not path.is_file():  # sparse-checkout-hidden; tracked but not materialised
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        except (SyntaxError, UnicodeDecodeError, ValueError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            if name != "create_mt5":
                continue
            mode = next(
                (kw.value for kw in node.keywords if kw.arg == "mode"),
                node.args[0] if node.args else None,
            )
            if isinstance(mode, ast.Constant) and isinstance(mode.value, str):
                literals.setdefault(mode.value, f"{relative}:{node.lineno}")

    assert literals, "expected to find at least one literal create_mt5 mode"
    unknown = {m: where for m, where in literals.items() if m not in accepted}
    assert not unknown, f"unknown literal modes in callers: {unknown}"


# ---------------------------------------------------------------------------
# R33 (hardening): max_gap_pct=0 is the strictest setting, not "unset".
# ---------------------------------------------------------------------------


def test_max_gap_pct_zero_is_honoured_not_coerced_to_default() -> None:
    """`.get("max_gap_pct") or 1.5` turned the strictest value into the loosest.

    Behavioural: drives `_check_gap_ceiling` with a 1.0% gap under several
    configs. The old code returned PASS for `max_gap_pct: 0` because `0 or 1.5`
    is 1.5.
    """
    from types import SimpleNamespace

    from src.components.verification import _check_gap_ceiling

    analysis = SimpleNamespace(
        trade_parameters=SimpleNamespace(entry_price=100.0, direction="LONG")
    )
    mso = SimpleNamespace(
        timeframes={"M15": SimpleNamespace(candles=[SimpleNamespace(close=101.0)])}
    )

    def verdict(filters):
        return _check_gap_ceiling(analysis, mso, {"filters": filters}).status

    # 1.0% gap vs a 0 ceiling must FAIL; the old `or 1.5` made it PASS.
    assert verdict({"max_gap_pct": 0}) == "FAIL"
    # 1.0% gap vs the 1.5 default must PASS.
    assert verdict({"max_gap_pct": 1.5}) == "PASS"
    assert verdict({}) == "PASS"
    # YAML string, empty `filters:`, bool, and junk must not crash or invert.
    assert verdict({"max_gap_pct": "1.5"}) == "PASS"
    assert verdict(None) == "PASS"
    assert verdict({"max_gap_pct": False}) == "PASS"
    assert verdict({"max_gap_pct": ""}) == "PASS"


# ---------------------------------------------------------------------------
# CHARACTERISATION — defects deliberately NOT fixed (would change sealed
# evidence). These pin current behaviour so it cannot change silently.
# ---------------------------------------------------------------------------


def test_characterise_selected_orders_materialise_in_finaliser_order() -> None:
    """R8, REPAIRED by wave-21 (d39355635, occurrence identity closure): selected
    orders now materialise in the FINALISER'S ordered keys
    (`final_selected_candidate_instance_keys`), not by `sorted(instance_key_set)`
    lexical accident. The old pin's own caveat -- "changing the iteration order
    changes every sealed result" -- is discharged: the affected R2-bound file is
    on the wave-21 forward-seal-break register (WAVE21_INTEGRATION.md §7), and
    any future sealed replay regenerates its decision contract first.

    This pin now guards the REPAIRED order: a return to lexical-set iteration
    (or any third ordering) must trip it.
    """
    path = REPO / "src/research_infra/v4_timewarp_simulated_live_research_loop.py"
    text = path.read_text()
    needle = "for selected_instance_key in final_selected_candidate_instance_keys"
    assert needle in text, (
        "order-materialisation loop changed — re-verify R8 before accepting new arms"
    )
    assert "for selected_instance_key in sorted(selected_instance_key_set)" not in text, (
        "the retired lexical-order materialisation loop reappeared"
    )


def test_characterise_duplicate_top_level_definition_in_replay_engine() -> None:
    """R26. `package_or_replay_row_requires_explicit_action_intent` is defined
    twice at module scope; Python binds the second, so the first (54 lines) is
    unreachable by construction and its precedence logic never executes.

    This test also acts as a guard: no NEW duplicate definition may appear.
    """
    known = {
        # R26. Second definition (v4:72711, `(row, packets=None)`) shadows the
        # first (v4:71321, `(candidate, packets)`). Two call sites pass a single
        # argument, which only type-checks against the second — proving the
        # first never executes. Not deleted here: editing the monolith changes
        # its code-authority hash and breaks every sealed arm binding.
        (
            "src/research_infra/v4_timewarp_simulated_live_research_loop.py",
            "package_or_replay_row_requires_explicit_action_intent",
        ): 2,
        # R26b, found by this guard. `_is_sha256` is defined twice with
        # DIFFERENT semantics: :480 uses `int(value, 16)` (accepts uppercase
        # hex); :997 requires every character in "009abcdef" (lowercase
        # only). The stricter :997 wins, so the live behaviour is the safe one —
        # but a reader studying :480 sees validation that never runs.
        (
            "src/research_infra/replay_acceleration_progressive_benchmark.py",
            "_is_sha256",
        ): 2,
    }
    offenders: dict[tuple[str, str], int] = {}
    for path in sorted((REPO / "src").rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(errors="replace"))
        except SyntaxError:  # pragma: no cover - none today
            continue
        counts: dict[str, int] = {}
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                counts[node.name] = counts.get(node.name, 0) + 1
        rel = str(path.relative_to(REPO))
        for name, count in counts.items():
            if count > 1:
                offenders[(rel, name)] = count
    assert offenders == known, (
        "duplicate top-level definitions changed.\n"
        f"  expected: {known}\n  actual:   {offenders}\n"
        "A duplicate definition silently shadows the first; remove it or update "
        "the allowlist with a documented finding."
    )


def test_characterise_replay_and_live_use_different_risk_profiles() -> None:
    """R10. Replay sizes from ftmo.yaml; live sizes from redacted_account.yaml. Two of
    the 24 replayed symbols therefore size differently in replay than in
    production."""
    import yaml

    agent_cfg = yaml.safe_load((REPO / "config/agent_config.yaml").read_text())
    assert (
        agent_cfg["gtos_vnext_runtime"]["timewarp_replay_risk_profile_path"]
        == "config/profiles/ftmo.yaml"
    )

    def effective(profile: dict, symbol: str) -> float:
        inst = (profile.get("instruments") or {}).get(symbol) or {}
        risk = (inst.get("risk") or {}).get("risk_per_trade_pct")
        if risk is not None:
            return float(risk)
        root = (profile.get("risk") or {}).get("risk_per_trade_pct")
        if root is not None:
            return float(root)
        return float(agent_cfg["risk"]["risk_per_trade_pct"])

    live = yaml.safe_load((REPO / "config/profiles/redacted_account.yaml").read_text())
    replay = yaml.safe_load((REPO / "config/profiles/ftmo.yaml").read_text())

    from src.research_infra.v4_timewarp_simulated_live_research_loop import (
        GTOS_24_SYMBOL_SURFACE,
    )

    divergent = {
        symbol: (effective(live, symbol), effective(replay, symbol))
        for symbol in GTOS_24_SYMBOL_SURFACE
        if not math.isclose(effective(live, symbol), effective(replay, symbol))
    }
    assert divergent == {
        "NAS100": (0.25, 0.5),
        "US30_cash": (2.0, 1.0),
    }, f"replay/live sizing divergence changed: {divergent}"


def test_canonical_bytes_does_not_hang_on_circular_reference() -> None:
    """H1 from adversarial review. `json.dumps` raises `ValueError("Circular
    reference detected")`; the non-finite handler runs inside that `except`, so
    it must not recurse forever on the same payload."""
    from src.research_infra.replay_canonical_bytes import canonical_bytes

    payload: dict = {"a": 1}
    payload["self"] = payload
    with pytest.raises(ValueError, match="Circular reference"):
        canonical_bytes(payload)

    nested: dict = {"rows": []}
    nested["rows"].append(nested)
    with pytest.raises(ValueError, match="Circular reference"):
        canonical_bytes(nested)


def test_non_finite_paths_terminates_on_shared_and_cyclic_structure() -> None:
    from src.research_infra.replay_canonical_bytes import non_finite_paths

    shared = {"r": float("nan")}
    payload = {"a": shared, "b": shared}
    # Shared (non-cyclic) subtrees are visited once; the leaf is still reported.
    assert len(non_finite_paths(payload)) == 1

    cyclic: dict = {"bad": float("inf")}
    cyclic["loop"] = cyclic
    assert non_finite_paths(cyclic) == ["$.bad=inf"]


def test_r_p1_is_closed_in_both_previously_contract_bound_comparators() -> None:
    """R-P1 CLOSED 2026-07-26. Supersedes
    `test_characterise_contract_bound_comparators_still_use_the_old_encoder`.

    The characterisation this replaces asserted the hole was still open, and said
    it "fails when the contract is re-sealed and the fix lands, which is exactly
    when the register entry should be closed." That happened: OD-2's R2 split
    moved both comparators to `input_bindings.verification_tooling`, which the
    enforcement loop never reads, so the fix could finally land.

    The defect, restated because it is subtle: parity is decided on BYTES, and
    under `allow_nan=True` a non-finite float serialises to the bare token
    `NaN`. So `b"NaN" == b"NaN"` — two runs that both produced an undefined
    economic value compared EQUAL and the comparator reported zero differences.
    """
    import json

    from src.research_infra import b7_5_post_acceleration_semantic_verifier as verifier
    from src.research_infra import replay_acceleration_task2_semantic_acceptance as task2
    from src.research_infra.replay_canonical_bytes import NonFiniteCanonicalValueError

    for module in (verifier, task2):
        # Finite values are unchanged — the encoder is byte-identical on every
        # value the sealed ledgers actually contain.
        assert module.canonical_bytes({"net_r": 1.5, "symbol": "NAS100"}) == (
            b'{"net_r":1.5,"symbol":"NAS100"}'
        )
        for bad in (float("nan"), float("inf"), float("-inf")):
            with pytest.raises(NonFiniteCanonicalValueError, match="non_finite_canonical_value"):
                module.canonical_bytes({"final_r": bad})

    # R2, not R1, is the contract these two are governed by now.
    route = REPO / "research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16"
    r2 = json.loads(
        (route / "B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json").read_text()
    )
    unbound = {row["path"] for row in r2["input_bindings"]["verification_tooling"]}
    assert unbound == {
        "src/research_infra/b7_5_post_acceleration_semantic_verifier.py",
        "src/research_infra/replay_acceleration_task2_semantic_acceptance.py",
    }


def test_r1_is_superseded_and_the_cost_of_that_is_stated() -> None:
    """The honest ledger entry for landing P1.

    R1 now reports these two paths as drifted, so a January arm cannot be
    re-launched under R1 without `git checkout <sealed sha> --` on both files.
    That is the price OD-2 was approved to pay, and it is bounded: the two files
    never execute during an arm, so no January *result* changes and no receipt
    is invalidated. Recording it as a test so nobody rediscovers it as a
    surprise mid-campaign.
    """
    import hashlib
    import json

    route = REPO / "research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16"
    r1 = json.loads((route / "B7_5_POST_ACCELERATION_DECISION_CONTRACT.json").read_text())
    bound = {
        row["path"]: row["sha256"]
        for group in ("common_behavior_inputs", "package_authority_inputs")
        for row in r1["input_bindings"][group]
    }
    for rel in (
        "src/research_infra/b7_5_post_acceleration_semantic_verifier.py",
        "src/research_infra/replay_acceleration_task2_semantic_acceptance.py",
    ):
        assert rel in bound, "R1 must stay untouched — it is January's contract of record"
        assert hashlib.sha256((REPO / rel).read_bytes()).hexdigest() != bound[rel], (
            f"{rel} still matches R1's sealed hash, so P1 did not actually land"
        )


def test_characterise_authority_hash_defects_remain_unfixed() -> None:
    """R-A5-2 / R-A5-3. `_canonical_hash_payload` lives in a contract-bound file,
    so three verified defects were left in place: `None`/`""` elision collides
    with absence, floats round to 12dp, and a set produces a
    PYTHONHASHSEED-dependent digest via `json.dumps(default=str)`.
    """
    from src.research.moonshot_scheduler_v4_best_trade_allocator import (
        _stable_sha256,
        _stable_sha256_material,
    )

    absent = _stable_sha256({"risk_pct": 1.0})
    assert _stable_sha256({"risk_pct": 1.0, "broker_live_authority": None}) == absent
    assert _stable_sha256({"risk_pct": 1.0, "broker_live_authority": ""}) == absent
    assert _stable_sha256({"risk_pct": 1.0, "broker_live_authority": False}) != absent
    assert _stable_sha256({"net_r": 1.0000000000001}) == _stable_sha256(
        {"net_r": 1.0000000000002}
    )
    # A set still reaches `default=str` and emits the Python set repr.
    assert "{'" in _stable_sha256_material({"symbols": {"AUDJPY", "BTCUSD"}})
