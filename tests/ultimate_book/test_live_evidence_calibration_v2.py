"""The V2 live-evidence calibration: a family-wise budget that is family-wise, and reproducible.

Two defects in V1, both measured before anything was rebuilt on them.

**The budget was per sleeve per account.** R published this as a stated limitation (its section 4 item
14): 0.20 per cell across 22 calibrated cells is a book-level down-weight false-alarm rate bounded
by 22 x 0.20, and ~0.75 across the armed sleeves alone. The number the owner reads and the error
the system delivers were different numbers.

**And V1 could not be regenerated from its own generator.** The per-cell seed was
`abs(hash((SEED, account, sleeve)))`, and CPython randomises `str.__hash__` per process. Seeding per
(account, sleeve) also gave the same sleeve's two accounts independent Monte-Carlo noise, so R's
section 4 item 11 ("the two accounts now agree exactly") is false in the file it shipped: 1 of 11
sleeves has both `c` values identical.

These tests are the properties, not the numbers: they pass at any `--family-scope` and survive a
rebuild at a different budget. Where a number IS pinned it is a seed, because a seed changing
silently is the whole defect.
"""
import json
from pathlib import Path

import pytest

from src.components.ultimate_book.learning_actuator import LIVE_MIN_N, LIVE_MIN_N_SUPPORT
from src.components.ultimate_book.live_evidence import CALIBRATION_V2, boundaries_at

pytestmark = pytest.mark.skipif(not CALIBRATION_V2.is_file(),
                                reason="LIVE_EVIDENCE_CALIBRATION_V2.json not built in this tree")


@pytest.fixture(scope="module")
def cal():
    return json.loads(CALIBRATION_V2.read_text())


def _cells(cal):
    for account, sleeves in cal["accounts"].items():
        for sleeve, row in sleeves.items():
            if row.get("calibrated"):
                yield account, sleeve, row


def test_schema_and_scope(cal):
    assert cal["schema"] == "gtos.learning_lane.live_evidence_calibration.v2"
    assert cal["familywise_scope"] in ("book", "armed", "account", "cell")
    assert cal["familywise_correction"]["method"] == "bonferroni"


def test_the_seed_is_deterministic_across_processes():
    """The regression guard for the defect V1 shipped with.

    `hash()` on a str is salted per process; three runs of V1's seed expression gave 336168621,
    1028826546 and 3564764250 for one cell. Pinning the value is the point — if someone reaches for
    `hash()` again this fails, and a calibration nobody can regenerate is a calibration nobody can
    audit.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "_blec", Path(__file__).resolve().parents[2] / "scripts/build_live_evidence_calibration.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.sleeve_seed("crypto") == 3553087526
    assert mod.sleeve_seed("crypto") == mod.sleeve_seed("crypto")
    assert mod.sleeve_seed("crypto") != mod.sleeve_seed("idxrev")


def test_the_two_accounts_agree_exactly_on_the_boundary_width(cal):
    """`c` is invariant to the location shift, so it MUST be identical across accounts.

    V1 seeded per (account, sleeve) and got 1 of 11 identical; the rest was Monte-Carlo noise
    published as per-account structure. Seeding per sleeve makes the agreement structural.
    """
    by_sleeve: dict = {}
    for account, sleeve, row in _cells(cal):
        by_sleeve.setdefault(sleeve, []).append((account, row["c_down"], row["c_kill"]))
    checked = 0
    for sleeve, rows in by_sleeve.items():
        if len(rows) < 2:
            continue
        checked += 1
        downs = {r[1] for r in rows}
        kills = {r[2] for r in rows}
        assert len(downs) == 1, f"{sleeve}: c_down differs across accounts {rows}"
        assert len(kills) == 1, f"{sleeve}: c_kill differs across accounts {rows}"
    assert checked >= 10


def test_the_stated_budget_is_delivered_over_the_family_it_names(cal):
    """Bonferroni union bound over the scoped family <= the stated budget, whatever the dependence."""
    scope = cal["familywise_scope"]
    ub = cal["attained_familywise_upper_bound"]
    key = {"armed": "over_armed_cells_only", "book": "over_all_calibrated_cells"}.get(scope)
    if key is None:
        pytest.skip(f"no published bound for scope {scope!r}")
    assert ub[key]["down"] <= cal["familywise_down"] + 1e-9
    assert ub[key]["kill"] <= cal["familywise_kill"] + 1e-9


def test_a_wider_family_never_makes_the_brake_more_sensitive(cal):
    """Monotonicity: more tests in the family -> a smaller per-cell budget -> a wider boundary.

    If this ever inverts, the correction is being applied backwards and the brake would get
    TWITCHIER as the book grows.
    """
    order = ["cell", "account", "armed", "book"]
    sizes = {"cell": 1, "account": None, "armed": cal["familywise_correction"]["family_size_armed"],
             "book": cal["familywise_correction"]["family_size_book"]}
    for account, sleeve, row in _cells(cal):
        sizes["account"] = cal["familywise_correction"]["family_size_by_account"][account]
        sens = row["familywise_sensitivity"]
        ranked = sorted(order, key=lambda s: sizes[s])
        for a, b in zip(ranked, ranked[1:]):
            if sizes[a] == sizes[b]:
                continue
            assert sens[a]["c_down"] <= sens[b]["c_down"] + 1e-9, (account, sleeve, a, b)
            assert sens[a]["c_kill"] <= sens[b]["c_kill"] + 1e-9, (account, sleeve, a, b)


def test_no_calibrated_sleeve_can_be_gated_by_one_or_two_trades(cal):
    """The hard floor V1's first two drafts violated. Unchanged by the correction, and checked."""
    for account, sleeve, row in _cells(cal):
        for field in ("stop_outs_to_down_weight", "stop_outs_to_gate"):
            got = row[field]
            assert got is None or got >= LIVE_MIN_N, f"{account}/{sleeve}.{field} == {got}"


def test_gating_stays_cheaper_than_sizing_up_on_the_LIVE_account(cal):
    """The design property, on the cells where it costs money to be wrong.

    The multiplicity correction is paid for out of brake sensitivity, so it CAN invert
    "gating is cheap, sizing is dear". The artifact publishes every cell where it does
    (`asymmetry_check`). What must not invert is the armed set on the live account: FTMO is trading
    real money, and a sleeve that needs more stop-outs to brake than fills to size up has the
    learning loop pointing the wrong way.
    """
    armed = {c for c in cal["familywise_correction"]["armed_cells"] if c.startswith("FTMO/")}
    assert armed, "no armed FTMO cells in the artifact"
    for cell in sorted(armed):
        account, sleeve = cell.split("/", 1)
        row = cal["accounts"][account][sleeve]
        down = row["stop_outs_to_down_weight_measured"]
        gate = row["stop_outs_to_gate_measured"]
        assert down is not None and gate is not None, cell
        assert LIVE_MIN_N <= down < LIVE_MIN_N_SUPPORT, (
            f"{cell}: {down} stop-outs to down-weight against a {LIVE_MIN_N_SUPPORT}-fill size-up "
            "bar is not an asymmetry")
        assert gate > down, cell


def test_the_asymmetry_failures_are_published_not_hidden(cal):
    """Where the property does fail, the artifact must say so by name."""
    check = cal["asymmetry_check"]
    assert "cells_where_it_fails" in check and "armed_cells_where_it_fails" in check
    for row in check["cells_where_it_fails"]:
        account, sleeve = row["cell"].split("/", 1)
        got = cal["accounts"][account][sleeve]["stop_outs_to_down_weight_measured"]
        assert got is None or got >= LIVE_MIN_N_SUPPORT, row


def test_the_runtime_reads_the_same_boundary_the_artifact_publishes(cal):
    """`boundaries_at` must reproduce the table inside it and the closed form beyond it.

    The closed form is what stopped the 61st losing fill from REMOVING a gate the 60th applied
    (B276); it has to keep agreeing with the table it extends.
    """
    n_max = cal["n_max"]
    for account, sleeve, row in _cells(cal):
        for n in (1, 7, 30, n_max):
            down, kill = boundaries_at(row, n)
            assert down == row["thresholds_down_r"][str(n)], (account, sleeve, n)
            assert kill == row["thresholds_kill_r"][str(n)], (account, sleeve, n)
        # Past the table's end the closed form takes over. It must be CONTINUOUS with the table --
        # a jump at n_max+1 would reintroduce B276 in a subtler form (a boundary that moves when
        # the table runs out rather than one that vanishes).
        closed_only = {k: v for k, v in row.items()
                       if k not in ("thresholds_down_r", "thresholds_kill_r")}
        cd, ck = boundaries_at(closed_only, n_max)
        # 1e-4 R, not 0: the closed form re-multiplies `claim_mean_r`, `sd_r` and `c_*` after each
        # has been rounded to 6 dp for publication, so ~1e-5 accumulates by n=60. A stop-out is
        # ~1.0 R, so the residual is four orders below anything it could decide.
        assert abs(cd - row["thresholds_down_r"][str(n_max)]) < 1e-4, (account, sleeve)
        assert abs(ck - row["thresholds_kill_r"][str(n_max)]) < 1e-4, (account, sleeve)
        beyond_d, beyond_k = boundaries_at(row, n_max + 40)
        assert beyond_d is not None and beyond_k is not None, (account, sleeve)
        assert beyond_k < beyond_d, "the gate boundary must sit below the down-weight boundary"
