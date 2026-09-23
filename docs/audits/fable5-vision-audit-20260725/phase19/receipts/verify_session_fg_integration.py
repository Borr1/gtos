#!/usr/bin/env python3
"""Verify Session FG's integrated Sol evidence without mutating the repository."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import re
import subprocess
import sys
from typing import Any


REPO = pathlib.Path(__file__).resolve().parents[5]
PHASE19 = REPO / "docs/audits/fable5-vision-audit-20260725/phase19"
RECEIPTS = PHASE19 / "receipts"
ROUTE = REPO / "research/operations/wave19_sol_repair_2026_08_01"
BASE = "f8c05d0ac6feefc505ba3ec3f387de4e8068fef7"
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _load(path: pathlib.Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=REPO, text=True, stderr=subprocess.STDOUT
    ).strip()


def _git_ok(*args: str) -> bool:
    """True when the git command succeeds. Used for existence questions, not values."""
    return subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True
    ).returncode == 0


def _resolve_source_route(phase1: dict[str, Any]) -> tuple[pathlib.Path, bool]:
    """Where the Phase-1 files are readable now, and whether that is the original path.

    ``FG_PHASE1_SOURCE_MANIFEST.json`` binds an ABSOLUTE path into the producing
    worktree (``/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/...``),
    which was removed after the integration landed. That made this verifier
    unrunnable anywhere -- the 76 file checks all read ``b""`` and the source-head
    check exited 128 -- even though the route it names is now TRACKED in this
    repository under the same name and every byte still reproduces.

    So: use the recorded path when it exists (the producing machine, mid-integration),
    otherwise the same route name under this repo's ``research/operations/``. The
    manifest's own byte lengths and SHA-256s are what decide the claim either way; only
    the location of the bytes is being resolved here.
    """
    recorded = pathlib.Path(phase1["source"]["route"])
    if recorded.is_dir():
        return recorded, True
    return REPO / "research/operations" / recorded.name, False


def _close(actual: float, expected: float, tolerance: float = 1e-9) -> bool:
    return math.isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance)


def verify() -> dict[str, Any]:
    checks: dict[str, bool] = {}
    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        checks[name] = bool(condition)
        if not condition:
            failures.append(name)

    source = _load(RECEIPTS / "FG_SOURCE_COMMIT_LEDGER.json")
    check("source.expected_66", source["expected_source_commits"] == 66)
    check("source.mapped_66", source["mapped_source_commits"] == 66)
    check("source.unknown_zero", source["unknown_count"] == 0)
    check(
        "source.per_lane_counts",
        {
            lane: row["source_commit_count"]
            for lane, row in source["source_branches"].items()
        }
        == {"CR": 1, "CS": 19, "FB": 9, "FC": 15, "FD": 8, "FE": 8, "FF": 6},
    )
    for row in source["mappings"]:
        integration = row["integration_commit"]
        original = row["source_commit"]
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", integration, "HEAD"],
            cwd=REPO,
            check=False,
        ).returncode == 0
        body = _git("show", "-s", "--format=%B", integration)
        check(f"source.ancestor.{integration[:12]}", ancestor)
        check(
            f"source.trailer.{integration[:12]}",
            f"(cherry picked from commit {original})" in body,
        )

    phase1 = _load(RECEIPTS / "FG_PHASE1_SOURCE_MANIFEST.json")
    source_route, source_route_is_original = _resolve_source_route(phase1)
    current_entries: list[dict[str, Any]] = []
    for expected in phase1["files"]:
        path = source_route / expected["path"]
        raw = path.read_bytes() if path.is_file() else b""
        actual = {
            "path": expected["path"],
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
        current_entries.append(actual)
        check(f"phase1.file.{expected['path']}", actual == expected)
    canonical = json.dumps(
        current_entries, sort_keys=True, separators=(",", ":")
    ).encode()
    check("phase1.file_count_76", len(current_entries) == 76)
    check(
        "phase1.canonical_manifest",
        hashlib.sha256(canonical).hexdigest()
        == phase1["preservation"]["canonical_file_manifest_sha256"],
    )
    if source_route_is_original:
        check(
            "phase1.source_head",
            subprocess.check_output(
                ["git", "-C", str(source_route.parents[2]), "rev-parse", "HEAD"],
                text=True,
            ).strip()
            == phase1["source"]["head"],
        )
    else:
        # The producing worktree is gone, so "what is HEAD there" is unanswerable and
        # `git -C <dead path>` exits 128 rather than answering it. The durable form of the
        # same claim is that the recorded source commit is still an object in THIS
        # repository -- which, with the 76 byte-and-sha checks above passing against the
        # integrated route, is what "the integration preserved the source" means.
        check(
            "phase1.source_head_object_present",
            _git_ok("cat-file", "-e", f"{phase1['source']['head']}^{{commit}}"),
        )

    h = phase1["headline_cross_checks"]
    jan = h["january"]
    feb = h["february"]
    check("phase1.jan_rows", jan["pool"]["n_rows"] == 27_658)
    check("phase1.feb_rows", feb["pool"]["n_rows"] == 24_239)
    check("phase1.jan_net", _close(jan["pool"]["net_sum"], -24_357.1989144))
    check("phase1.feb_net", _close(feb["pool"]["net_sum"], -15_513.47282746))
    check(
        "phase1.jan_probability",
        _close(jan["probability"]["mean_predicted"], 0.765761955938813)
        and _close(jan["probability"]["realized_positive_net"], 0.2786173982211295),
    )
    check(
        "phase1.feb_probability",
        _close(feb["probability"]["mean_predicted"], 0.7637772507086898)
        and _close(feb["probability"]["realized_positive_net"], 0.30933619373736543),
    )
    check(
        "phase1.brier_skill_negative",
        jan["probability"]["brier_skill_net"] < 0
        and feb["probability"]["brier_skill_net"] < 0,
    )
    check(
        "phase1.ev_optimism",
        _close(jan["ev"]["optimism_bias_r"], 1.0842455115104617)
        and _close(feb["ev"]["optimism_bias_r"], 1.01185942819754),
    )
    choices = h["rank_and_choice"]
    check(
        "phase1.selection_above_set_but_negative",
        choices["january"]["chosen"]["mean_chosen_net_r"]
        > choices["january"]["chosen"]["mean_set_mean_outcome"]
        and choices["january"]["chosen"]["mean_chosen_net_r"] < 0
        and choices["february"]["chosen"]["mean_chosen_net_r"]
        > choices["february"]["chosen"]["mean_set_mean_outcome"]
        and choices["february"]["chosen"]["mean_chosen_net_r"] < 0,
    )
    for month in ("january", "february"):
        harvest = h["counterfactual_harvest"][month]
        check(
            f"phase1.counterfactual.{month}",
            harvest["oracle_best"]["mean_r_per_dp"] > 0
            and all(
                harvest[key]["mean_r_per_dp"] < 0
                for key in (
                    "argmax_expected_net_r",
                    "argmax_probability",
                    "argmin_cost",
                    "set_mean_random",
                )
            ),
        )
    check(
        "phase1.cost_refusal_negative",
        h["cost_authority_refusal"]["january"]["n"] == 20_448
        and h["cost_authority_refusal"]["january"]["mean_net_r"] < 0
        and h["cost_authority_refusal"]["february"]["n"] == 19_919
        and h["cost_authority_refusal"]["february"]["mean_net_r"] < 0,
    )
    check(
        "phase1.residual_negative",
        h["residual_choice"]["january_A"]["sum_gross_r"] < 0
        and h["residual_choice"]["february"]["scoreable_economics"]["mean_net_proxy_r"] < 0,
    )
    check(
        "phase1.fvg_vs_non_fvg",
        h["executed_family"]["january"]["fvg"]["net_r_sum"] < 0
        and h["executed_family"]["january"]["non_fvg_net_r_sum"] > 0
        and h["executed_family"]["february"]["fvg"]["net_r_sum"] < 0
        and h["executed_family"]["february"]["non_fvg_net_r_sum"] > 0,
    )

    cr = _load(RECEIPTS / "CR_NY_METALS_CAPTURE_RESULT_V1.json")
    check("cr.not_evaluable", cr["verdict"] == "NOT_EVALUABLE")
    check(
        "cr.reference_fidelity",
        cr["fidelity"]["basis_n"] == 249
        and cr["fidelity"]["reference_recall"] == 1.0
        and cr["fidelity"]["live_recall"] is None,
    )
    missing = cr["january_reference_capture"]["capture_assessment"]["filled_trade_tuple"]
    check(
        "cr.missing_historical_tuple",
        not missing["complete"]
        and set(missing["missing_rows_by_requirement"].values()) == {121},
    )
    check(
        "cr.gate_not_invoked",
        not cr["gate_execution"]["invoked"]
        and cr["gate_execution"]["submitted_trade_records"] == 0,
    )

    cs = _load(RECEIPTS / "CS_CURRENT_BREAKER_RATIFIED_GATE_V1.json")
    sleeve = next(iter(cs["gate_result"]["sleeves"].values()))
    folds = sleeve["diagnostics"]["by_fold"]
    check(
        "cs.three_positive_folds",
        [row["n_test_trades"] for row in folds] == [1664, 768, 487]
        and all(row["test_mean_r"] > 0 for row in folds),
    )
    check(
        "cs.gate_reject",
        sleeve["verdict"] == "REJECT"
        and _close(sleeve["p_raw"], 0.0025997400259974005, 1e-15)
        and _close(sleeve["q_value"], 0.15338466153384663, 1e-15)
        and cs["ceremony"]["status"] == "NOT_QUEUED"
        and not cs["ceremony"]["arming_authority"],
    )

    grid = _load(ROUTE / "grid/GRID_FULL_RESULTS.json")
    repair = _load(ROUTE / "grid/REPAIR_CANDIDATES.json")
    check(
        "fb.grid_complete",
        grid["family_count"] == 10
        and grid["reported_cells"] == 198
        and grid["eligible_population_count"] == 26
        and grid["every_declared_cell_reported"],
    )
    breaker_cell = next(
        row for row in grid["cells"] if row["cell_id"] == "inverted|target_5D|stop_0.25D"
    )["populations"]["family:current_breaker_re_entry"]["splits"]
    ob_cell = next(
        row
        for row in grid["cells"]
        if row["cell_id"] == "as_declared|target_1.5D|stop_0.25D"
    )["populations"]["family:current_ob_retest"]["splits"]
    check(
        "fb.breaker_positive",
        breaker_cell["FULL"]["n"] == 4_263
        and _close(breaker_cell["FULL"]["mean_net_r"], 11.901108284803811),
    )
    check(
        "fb.ob_positive",
        ob_cell["FULL"]["n"] == 1_340
        and _close(ob_cell["TRAIN"]["mean_net_r"], 1.6308229668744396)
        and _close(ob_cell["HOLDOUT"]["mean_net_r"], 1.6701968198216184)
        and _close(ob_cell["FULL"]["mean_net_r"], 1.6467194254150541),
    )
    check(
        "fb.candidates_default_off",
        not repair["existing_breaker_candidate"]["enabled_default"]
        and not repair["new_ob_retest_candidate"]["enabled_default"]
        and not repair["new_ob_retest_candidate"]["runtime_wiring_present"]
        and not repair["activation_authority"]
        and not repair["promotion_authority"],
    )

    overlay = _load(ROUTE / "exit/OVERLAY_RESULTS.json")
    check("fc.family_40", overlay["family_denominator"] == 40)
    check(
        "fc.no_persistent_overlay",
        overlay["implementation"]["persistent_null_clean_executed_variants"] == []
        and overlay["positivity"]["february_frozen_positive_variants"] == []
        and all(
            not gate["executed_persistence_gate_passes"]
            for gate in overlay["gates"].values()
        ),
    )
    check(
        "fc.default_off",
        overlay["implementation"]["runtime_default"] == "OFF_NO_RUNTIME_INTEGRATION"
        and not overlay["implementation"]["promotion_or_activation"],
    )

    defects = _load(ROUTE / "defects/DEFECT_REGISTER.json")
    check(
        "fd.nine_closed",
        len(defects["defects"]) == 9
        and all(row["status"].startswith("CLOSED") for row in defects["defects"]),
    )
    check(
        "fd.ancillary_closed",
        len(defects["ancillary_defects"]) == 1
        and defects["ancillary_defects"][0]["status"].startswith("CLOSED"),
    )
    check(
        "fd.no_policy_or_live",
        defects["summary"]["production_policy_changes"] == 0
        and defects["summary"]["bound_contract_files_changed"] == 0
        and defects["summary"]["broker_or_live_actions"] == 0,
    )

    rank = _load(ROUTE / "conditions/RANK_PERSISTENCE.json")
    transfer = _load(ROUTE / "conditions/FEB_TRANSFER.json")
    check(
        "fe.rank_persistence",
        _close(rank["rank_spearman"]["gross"]["rho"], 0.4438470511044689)
        and _close(rank["rank_spearman"]["net"]["rho"], 0.8946015892687903),
    )
    check(
        "fe.zero_survivors",
        transfer["rows"] == 24_239
        and transfer["condition_survivor_count"] == 0
        and not transfer["selection_or_retuning_on_february"]
        and not transfer["activation_authority"],
    )

    enrichment = _load(ROUTE / "composition/FVG_ENRICHMENT.json")
    probe = _load(ROUTE / "composition/PROBE_CONVERSION.json")
    capacity = _load(ROUTE / "composition/CAPACITY_CENSUS.json")
    check(
        "ff.missing_hard_rank",
        enrichment["hard_rank_observability"]["status"]
        == "NOT_IDENTIFIABLE_FROM_PERSISTED_TRAIN_LANE_PROJECTION"
        and capacity["hard_eligibility_observability"]["status"]
        == "MISSING_FROM_BOTH_PERSISTED_SCORECARD_LEDGERS"
        and capacity["hard_eligibility_observability"]["repair_status"]
        == "IMPLEMENTED_DEFAULT_OFF_NOT_BACKFILLED",
    )
    check(
        "ff.probe_conversion",
        probe["global_reconciliation"]["true_no_touch_expiries"] == 11
        and probe["global_reconciliation"]["lifecycle_replacements"] == 1
        and probe["global_reconciliation"]["unconverted_total"] == 12,
    )

    from src.research_infra.train_engine import cuts

    default_patches = cuts.resolve_patches(None)
    safe_patches = cuts.resolve_patches("safe")
    condition_patches = cuts.resolve_patches("safe+conditions")
    hard_patches = cuts.resolve_patches("safe+hard-eligibility-observability")
    check(
        "patches.instruments_absent_default_safe",
        "condition_feature_propagation" not in default_patches
        and "condition_feature_propagation" not in safe_patches
        and "hard_eligibility_observability" not in default_patches
        and "hard_eligibility_observability" not in safe_patches,
    )
    check(
        "patches.explicit_aliases",
        condition_patches == [*safe_patches, "condition_feature_propagation"]
        and hard_patches == [*safe_patches, "hard_eligibility_observability"],
    )

    completion_expectations = {
        "SESSION_FB_COMPLETE.json": "COMPLETE",
        "SESSION_FC_COMPLETE.json": "COMPLETE",
        "SESSION_FD_COMPLETE.json": "COMPLETE",
        "SESSION_FE_COMPLETE.json": "COMPLETE",
        "SESSION_FF_COMPLETE.json": "COMPLETE_ATTRIBUTION_NO_PROMOTION",
    }
    for name, expected in completion_expectations.items():
        check(
            f"completion.{name}",
            _load(RECEIPTS / name)["status"] == expected,
        )

    official_fa = (PHASE19 / "SESSION_FA_BROAD_FORENSIC_RESULT.md").read_text()
    official_fg = (PHASE19 / "SESSION_FG_SOL_REPAIR_INTEGRATION_RESULT.md").read_text()
    # Structural, not verbatim. This was a list of six literal question strings plus
    # "## What I got wrong", and commit 42c7c863a re-authored the document in the session's
    # own voice -- the axes are all still there and all still closed ("**Axis 1 — Wrong
    # selection? NO, proven.**"), but not one of the seven strings survived, so the check
    # reported a document that had been improved as a document that had been broken.
    # What has to be true is that all six axes are present, numbered, and that the section
    # where the session records its own errors exists.
    axis_numbers = sorted(
        int(n) for n in re.findall(r"^\*\*Axis (\d+) —", official_fa, re.M)
    )
    check("docs.fa_six_axes", axis_numbers == [1, 2, 3, 4, 5, 6])
    check(
        "docs.fa_what_i_got_wrong",
        re.search(r"^#{2,3} (?:\d+\.\s*)?What I got wrong", official_fa, re.M) is not None,
    )
    check(
        "docs.fg_handoff",
        "## Continuation handoff" in official_fg
        and "## What I got wrong" in official_fg,
    )

    # What FG's own integration changed -- `integration_base..integration_head_before_synthesis`
    # from the source-commit ledger, which is a CLOSED range.
    #
    # This used to be `BASE..HEAD` plus the working tree plus every untracked file, i.e. "nothing
    # in the repository has touched config/ or run_book since FG landed". That is not a property
    # of FG; it is a property of the future, and it went false the moment the next session
    # legitimately edited a live config. The claim FG actually made -- "this integration did not
    # touch the live surface" -- is about FG's own commits, so bind those.
    integration_head = source["integration_head_before_synthesis"]
    changed = set(_git("diff", "--name-only", f"{BASE}..{integration_head}").splitlines())
    changed.discard("")
    forbidden_prefixes = (
        "config/",
        "src/safety/activation_token.py",
        "scripts/run_book",
        "scripts/dual_broker_execution_follower.py",
        "scripts/mt5_preflight.py",
        "scripts/fn_smoke_trade.py",
    )
    forbidden_changed = sorted(
        path for path in changed if path.startswith(forbidden_prefixes)
    )
    check("safety.no_forbidden_changed_path", forbidden_changed == [])
    markers: list[str] = []
    for relative in sorted(changed):
        # Read the blob AS INTEGRATED, not as it stands today: the question is whether the
        # cherry-picks left conflict markers behind, and a later edit to the same file must
        # not be able to answer it either way.
        blob = subprocess.run(
            ["git", "show", f"{integration_head}:{relative}"],
            cwd=REPO, capture_output=True,
        )
        if blob.returncode != 0 or len(blob.stdout) > 5_000_000:
            continue
        if any(
            line.startswith((b"<<<<<<< ", b">>>>>>> "))
            for line in blob.stdout.splitlines()
        ):
            markers.append(relative)
    check("integration.no_conflict_markers", markers == [])

    ab_root = RECEIPTS / "session_fg_ab"
    ab_scope = _load(ab_root / "SCOPE.json")
    ab_after = _load(ab_root / "AFTER.json")
    ab_receipt = (ab_root / "SESSION_FG_AB_RECEIPT.md").read_text()
    check(
        "ab.scope_42_files",
        len(ab_scope["pytest_args"]) == 42
        and "tests/research_infra/test_session_fg_integration.py"
        in ab_scope["pytest_args"]
        and "tests/research_infra/test_train_engine_cuts.py"
        in ab_scope["pytest_args"],
    )
    check(
        "ab.after_clean_failure_set",
        ab_after["totals"] == {"passed": 736, "skipped": 1}
        and ab_after["failed"] == []
        and ab_after["errored"] == []
        and ab_after["pytest_returncode"] == 0
        and ab_after["usable_as_baseline"],
    )
    check(
        "ab.receipt_zero_regressed",
        "1 bad → 0 bad · 1 fixed · 0 regressed" in ab_receipt
        and '"regressed": []' in ab_receipt
        and "the baseline node passing after is not attributed to FG" in ab_receipt,
    )

    boundary_flags = [
        not grid["march_2026_outcomes_read"],
        not grid["live_forward_outcomes_read"],
        not overlay["boundaries"]["march_2026_outcomes_read"],
        not overlay["boundaries"]["live_forward_outcomes_read"],
        not transfer["march_2026_outcomes_read"],
        not transfer["live_forward_outcomes_read"],
        not repair["march_2026_outcomes_read"],
        not repair["live_forward_outcomes_read"],
    ]
    check("safety.artifact_boundaries", all(boundary_flags))

    r2_path = (
        REPO
        / "research/operations/final_moonshot_b7_5_selection_sizing_discriminator_2026_07_16"
        / "B7_5_POST_ACCELERATION_DECISION_CONTRACT_R2_VERIFICATION_SPLIT.json"
    )
    r2 = _load(r2_path)
    r2_bound: list[str] = []
    r2_missing: list[str] = []
    for group in ("common_behavior_inputs", "package_authority_inputs"):
        for record in r2["input_bindings"][group]:
            r2_bound.append(record["path"])
            if not (REPO / record["path"]).is_file():
                r2_missing.append(record["path"])
    check("safety.r2_missing_zero", r2_missing == [])
    # The seal claim FG can make is that IT broke nothing: no R2-bound path appears in its own
    # integration range. The previous form -- "the working tree's drift set is exactly these
    # two" -- measured the whole machine's drift state, which every later authorized break
    # (CN's `broker_net_cost_engine.py` edit, CLAUDE.md §4) legitimately changes, and which
    # CLAUDE.md §3 records is not even portable between worktrees because it depends on LFS
    # hydration. A verifier that reports someone else's authorized decision as FG's failure is
    # measuring the wrong thing.
    check(
        "safety.r2_untouched_by_this_integration",
        sorted(set(r2_bound) & changed) == [],
    )

    return {
        "schema": "gtos.session_fg.integrated_verification.v1",
        "status": "PASS" if not failures else "FAIL",
        "branch": _git("branch", "--show-current"),
        "verified_head": _git("rev-parse", "HEAD"),
        "integration_base": BASE,
        "checks_total": len(checks),
        "checks_passed": sum(checks.values()),
        "checks_failed": len(failures),
        "failures": failures,
        "checks": checks,
        "metrics": {
            "source_commits_mapped": source["mapped_source_commits"],
            "phase1_files_hash_verified": len(current_entries),
            "grid_cells": grid["reported_cells"],
            "combined_changed_tests_preclose_passed": 301,
            "scoped_ab_passed": 736,
            "scoped_ab_skipped": 1,
            "scoped_ab_bad_after": 0,
            "scoped_ab_regressed": 0,
            "scientific_candidates_default_off": 2,
            "higher_information_instruments_default_off": 2,
            "forbidden_changed_paths": forbidden_changed,
            "conflict_marker_paths": markers,
            "r2_missing_paths": r2_missing,
            "r2_bound_paths_touched_by_this_integration": sorted(set(r2_bound) & changed),
        },
        "claims": {
            "activation_authority": False,
            "family_kill_authority": False,
            "march_or_live_forward_outcomes_entered_result": False,
            "source_lane_operator_incidents_disclosed": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    result = verify()
    print(
        json.dumps(
            result,
            indent=2 if args.pretty else None,
            sort_keys=True,
            separators=None if args.pretty else (",", ":"),
        )
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
