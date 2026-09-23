"""Adversarial tests for Wave 21's offline verification tooling."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace


REPO = Path(__file__).resolve().parents[2]
VERIFY_DIR = (
    REPO / "docs/audits/fable5-vision-audit-20260725/phase21/full_flow_truth/verification"
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


WAVE = _load("wave21_verification", VERIFY_DIR / "wave21_verification.py")
HOST = _load("wave21_host_parity", VERIFY_DIR / "verify_host_parity.py")


def test_host_observation_schema_matches_offline_consumer_contract():
    schema = json.loads((VERIFY_DIR / "HOST_OBSERVATION_SCHEMA.json").read_text())
    assert schema["$id"] == HOST.SCHEMA
    assert set(schema["required"]) == {
        "schema", "observation_id", "captured_at_utc", "expires_at_utc",
        "preservation", "host_files", "workers", "payload_sha256",
    }
    assert set(schema["properties"]["workers"]["items"]["required"]) == {
        "argv", "argv_sha256", "config_digest_sha256", "token_config_digest_sha256",
    }


def test_canonical_hash_is_mapping_order_independent_and_list_order_sensitive():
    assert WAVE._canonical_hash({"a": 1, "b": 2}) == WAVE._canonical_hash({"b": 2, "a": 1})
    assert WAVE._canonical_hash(["a", "b"]) != WAVE._canonical_hash(["b", "a"])


def test_lfs_pointer_parser_rejects_truncated_and_accepts_exact_contract():
    oid = "a" * 64
    pointer = (
        "version https://git-lfs.github.com/spec/v1\n"
        f"oid sha256:{oid}\n"
        "size 205754\n"
    ).encode()
    assert WAVE._parse_lfs_pointer(pointer) == (oid, 205754)
    assert WAVE._parse_lfs_pointer(pointer.replace(b"size 205754", b"size nope")) is None
    assert WAVE._parse_lfs_pointer(b"ordinary bytes") is None


def test_secret_scan_never_returns_the_matched_secret(monkeypatch):
    # Assemble the synthetic match at runtime so the test itself never adds a
    # high-confidence secret-shaped literal to repository history.
    token = "sk-" + "proj-" + "abcdefghijklmnopqrstuvwxyz012345"

    def fake_git(*args, **kwargs):
        pattern = args[args.index("-e") + 1]
        if pattern == WAVE.SECRET_PATTERNS["openai_key"].pattern:
            return SimpleNamespace(returncode=0, stdout=f"HEAD:x.py:7:key = '{token}'\n", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="")

    monkeypatch.setattr(WAVE, "_git", fake_git)
    hits = WAVE._secret_hits("HEAD")
    rendered = json.dumps(hits)
    assert hits == [{
        "kind": "openai_key", "path": "x.py", "line": 7,
        "match_sha256": WAVE._sha256(token.encode()),
    }]
    assert token not in rendered


def _capture(path: Path, bad: list[str], args=None):
    path.write_text(json.dumps({
        "usable_as_baseline": True,
        "parse_complete": True,
        "totals": {"passed": 10, "failed": len(bad)},
        "pytest_args": args or ["tests/x.py"],
        "failed": bad,
        "errored": [],
    }), encoding="utf-8")
    return path


def _inspection(path: Path, contract: dict):
    path.write_text(json.dumps({
        "comparison_contract": contract,
        "comparison_contract_sha256": WAVE._canonical_hash(contract),
    }), encoding="utf-8")
    return path


def _selected_tests(*, args=None, available=True):
    pytest_args = args or ["tests/x.py"]
    rows = [{
        "path": pytest_args[0].split("::", 1)[0],
        "expected_kind": "file" if available else "missing",
        "available": available,
    }]
    payload = {
        "bound": True,
        "selection_roots": [rows[0]["path"]],
        "rows": rows,
    }
    return {
        **payload,
        "pytest_args_sha256": WAVE._canonical_hash(pytest_args),
        "all_available": available,
        "inventory_sha256": WAVE._canonical_hash(payload),
    }


def _contract(**overrides):
    contract = {
        "dependency": "A",
        "sparse": "S",
        "lfs": "L",
        "fixtures": "X",
        "selected_tests": _selected_tests(),
        "environment_controls": {"NO_COLOR": "1"},
    }
    contract.update(overrides)
    return contract


def test_ab_guard_refuses_environment_or_fixture_drift(tmp_path):
    before = _capture(tmp_path / "before.json", [])
    after = _capture(tmp_path / "after.json", [])
    bctx = _inspection(tmp_path / "bctx.json", _contract(dependency="A", fixtures="X"))
    actx = _inspection(tmp_path / "actx.json", _contract(dependency="B", fixtures="Y"))
    result, code = WAVE.build_ab_guard(before, after, bctx, actx)
    assert code == 1
    assert result["status"] == "REFUSED_CONTEXT_MISMATCH"
    assert result["context_mismatches"] == ["dependency", "fixtures", "scope_contract"]
    assert result["fixed"] == result["regressed"] == []
    assert result["before_scope_sha256"] != result["after_scope_sha256"]
    assert result["diagnostic_only_incomparable_removed"]["count"] == 0
    assert result["diagnostic_only_incomparable_added"]["count"] == 0


def test_ab_guard_compares_failure_identity_not_count(tmp_path):
    before = _capture(tmp_path / "before.json", ["tests/x.py::old"])
    after = _capture(tmp_path / "after.json", ["tests/x.py::new"])
    contract = _contract()
    bctx = _inspection(tmp_path / "bctx.json", contract)
    actx = _inspection(tmp_path / "actx.json", contract)
    result, code = WAVE.build_ab_guard(before, after, bctx, actx)
    assert code == 1
    assert result["bad_before"] == result["bad_after"] == 1
    assert result["fixed"] == ["tests/x.py::old"]
    assert result["regressed"] == ["tests/x.py::new"]


def test_ab_guard_refuses_incomplete_or_tampered_context_contract(tmp_path):
    before = _capture(tmp_path / "before.json", [])
    after = _capture(tmp_path / "after.json", [])
    bctx = _inspection(tmp_path / "bctx.json", _contract())
    actx = _inspection(tmp_path / "actx.json", {"dependency": "A"})
    doc = json.loads(actx.read_text())
    doc["comparison_contract_sha256"] = "0" * 64
    actx.write_text(json.dumps(doc))
    result, code = WAVE.build_ab_guard(before, after, bctx, actx)
    assert code == 1
    assert result["status"] == "REFUSED_CONTEXT_MISMATCH"
    assert "after_context_contract_incomplete" in result["context_mismatches"]
    assert "after_context_contract_hash_invalid" in result["context_mismatches"]


def test_ab_guard_refuses_rehashed_selected_test_root_row_mismatch(tmp_path):
    before = _capture(tmp_path / "before.json", [])
    after = _capture(tmp_path / "after.json", [])
    bctx = _inspection(tmp_path / "bctx.json", _contract())
    changed = _contract()
    selected = changed["selected_tests"]
    selected["selection_roots"] = ["tests/not-the-captured-root.py"]
    selected["inventory_sha256"] = WAVE._canonical_hash({
        "bound": selected["bound"],
        "selection_roots": selected["selection_roots"],
        "rows": selected["rows"],
    })
    actx = _inspection(tmp_path / "actx.json", changed)

    result, code = WAVE.build_ab_guard(before, after, bctx, actx)

    assert code == 1
    assert "after_selected_test_contract_invalid" in result["context_mismatches"]


def test_ab_guard_refuses_rehashed_unknown_contract_key(tmp_path):
    before = _capture(tmp_path / "before.json", [])
    after = _capture(tmp_path / "after.json", [])
    changed = _contract()
    changed["unexpected_schema_atom"] = "before-only"
    bctx = _inspection(tmp_path / "bctx.json", changed)
    actx = _inspection(tmp_path / "actx.json", _contract())

    result, code = WAVE.build_ab_guard(before, after, bctx, actx)

    assert code == 1
    assert result["status"] == "REFUSED_CONTEXT_MISMATCH"
    assert result["same_scope"] is False
    assert result["before_scope_sha256"] != result["after_scope_sha256"]
    assert result["context_mismatches"] == [
        "before_context_contract_keys_invalid",
        "scope_contract",
    ]


def test_sparse_context_ignores_added_audit_path_but_keeps_it_diagnostic(
    tmp_path, monkeypatch
):
    state = {
        "added_audit": False,
        "extra_pattern": False,
        "reverse_patterns": False,
    }

    def fake_git(*args, **kwargs):
        if args == ("config", "--bool", "core.sparseCheckout"):
            return SimpleNamespace(stdout="true\n")
        if args == ("config", "--bool", "core.sparseCheckoutCone"):
            return SimpleNamespace(stdout="false\n")
        if args == ("sparse-checkout", "list"):
            patterns = ["docs/", "tests/"]
            if state["extra_pattern"]:
                patterns.append("src/")
            if state["reverse_patterns"]:
                patterns.reverse()
            return SimpleNamespace(stdout="\n".join(patterns) + "\n")
        if args == ("ls-files", "-v", "-z"):
            rows = ["H tests/x.py", "S src/sparse_only.py"]
            if state["added_audit"]:
                rows.append("H docs/new_audit.md")
            return SimpleNamespace(stdout="\0".join(rows) + "\0")
        raise AssertionError(args)

    monkeypatch.setattr(WAVE, "_git", fake_git)
    before_sparse = WAVE._sparse_inventory()
    state["added_audit"] = True
    after_sparse = WAVE._sparse_inventory()

    assert before_sparse["comparison_sha256"] == after_sparse["comparison_sha256"]
    assert (
        before_sparse["diagnostic_inventory_sha256"]
        != after_sparse["diagnostic_inventory_sha256"]
    )
    assert before_sparse["materialized_count"] == 1
    assert after_sparse["materialized_count"] == 2

    before = _capture(tmp_path / "before.json", [])
    after = _capture(tmp_path / "after.json", [])
    bctx = _inspection(
        tmp_path / "bctx.json",
        _contract(sparse=before_sparse["comparison_sha256"]),
    )
    actx = _inspection(
        tmp_path / "actx.json",
        _contract(sparse=after_sparse["comparison_sha256"]),
    )
    result, code = WAVE.build_ab_guard(before, after, bctx, actx)
    assert code == 0
    assert result["status"] == "NO_REGRESSION"
    assert result["same_scope"] is True

    state["reverse_patterns"] = True
    reordered_sparse = WAVE._sparse_inventory()
    assert reordered_sparse["comparison_sha256"] != before_sparse["comparison_sha256"]
    state["reverse_patterns"] = False

    state["extra_pattern"] = True
    drifted_sparse = WAVE._sparse_inventory()
    assert drifted_sparse["comparison_sha256"] != before_sparse["comparison_sha256"]
    drift_ctx = _inspection(
        tmp_path / "drift_ctx.json",
        _contract(sparse=drifted_sparse["comparison_sha256"]),
    )
    result, code = WAVE.build_ab_guard(before, after, bctx, drift_ctx)
    assert code == 1
    assert result["status"] == "REFUSED_CONTEXT_MISMATCH"
    assert result["context_mismatches"] == ["scope_contract", "sparse"]


def test_ab_guard_refuses_committed_but_sparse_absent_selected_test(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(WAVE, "REPO", tmp_path)
    (tmp_path / "tests").mkdir()
    selected = WAVE._selected_test_availability(
        ["tests/missing.py"],
        {"tests/missing.py": {"oid": "synthetic"}},
    )
    assert selected["all_available"] is False
    assert selected["rows"][0]["expected_kind"] == "file"

    args = ["tests/missing.py"]
    before = _capture(tmp_path / "before.json", [], args=args)
    after = _capture(tmp_path / "after.json", [], args=args)
    contract = _contract(selected_tests=selected)
    bctx = _inspection(tmp_path / "bctx.json", contract)
    actx = _inspection(tmp_path / "actx.json", contract)

    result, code = WAVE.build_ab_guard(before, after, bctx, actx)

    assert code == 1
    assert result["status"] == "REFUSED_CONTEXT_MISMATCH"
    assert result["context_mismatches"] == [
        "after_selected_test_unavailable",
        "before_selected_test_unavailable",
    ]


def test_selected_test_directory_refuses_partial_sparse_materialization(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(WAVE, "REPO", tmp_path)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/present.py").write_text("", encoding="utf-8")

    selected = WAVE._selected_test_availability(
        ["tests"],
        {
            "tests/present.py": {"oid": "present"},
            "tests/sparse_absent.py": {"oid": "absent"},
        },
    )

    assert selected["selection_roots"] == ["tests"]
    assert selected["rows"] == [{
        "path": "tests",
        "expected_kind": "directory",
        "available": False,
    }]
    assert selected["all_available"] is False


def test_selected_test_parser_refuses_indirect_and_option_selectors(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(WAVE, "REPO", tmp_path)
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/x.py").write_text("", encoding="utf-8")
    tree = {
        "tests/x.py": {"oid": "test"},
        "pytest-args.txt": {"oid": "args"},
    }

    for index, args in enumerate((
        ["--pyargs", "definitely_not_tests"],
        ["@pytest-args.txt"],
        ["--rootdir=tests", "tests/x.py"],
    )):
        selected = WAVE._selected_test_availability(args, tree)
        assert selected["all_available"] is False
        assert "tests" not in selected["selection_roots"]
        assert any(
            row["expected_kind"] in {"missing", "unsupported_argument"}
            for row in selected["rows"]
        )
        before = _capture(tmp_path / f"before-{index}.json", [], args=args)
        after = _capture(tmp_path / f"after-{index}.json", [], args=args)
        contract = _contract(selected_tests=selected)
        bctx = _inspection(tmp_path / f"bctx-{index}.json", contract)
        actx = _inspection(tmp_path / f"actx-{index}.json", contract)
        result, code = WAVE.build_ab_guard(before, after, bctx, actx)
        assert code == 1
        assert result["status"] == "REFUSED_CONTEXT_MISMATCH"
        assert result["same_scope"] is False


def test_ab_guard_reparses_capture_and_refuses_forged_selected_roots(tmp_path):
    cases = (
        (["--pyargs", "definitely_not_tests"], "tests/x.py"),
        (["tests/x.py"], "tests/unrelated.py"),
    )
    for index, (args, claimed_root) in enumerate(cases):
        rows = [{
            "path": claimed_root,
            "expected_kind": "file",
            "available": True,
        }]
        payload = {
            "bound": True,
            "selection_roots": [claimed_root],
            "rows": rows,
        }
        forged = {
            **payload,
            "pytest_args_sha256": WAVE._canonical_hash(args),
            "all_available": True,
            "inventory_sha256": WAVE._canonical_hash(payload),
        }
        before = _capture(tmp_path / f"forged-before-{index}.json", [], args=args)
        after = _capture(tmp_path / f"forged-after-{index}.json", [], args=args)
        contract = _contract(selected_tests=forged)
        bctx = _inspection(tmp_path / f"forged-bctx-{index}.json", contract)
        actx = _inspection(tmp_path / f"forged-actx-{index}.json", contract)

        result, code = WAVE.build_ab_guard(before, after, bctx, actx)

        assert code == 1
        assert result["status"] == "REFUSED_CONTEXT_MISMATCH"
        assert result["same_scope"] is False
        assert "before_selected_test_selection_mismatch" in result["context_mismatches"]
        assert "after_selected_test_selection_mismatch" in result["context_mismatches"]


def test_determinism_check_accepts_only_equal_well_formed_hashes(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text(json.dumps({"deterministic_payload_sha256": "a" * 64}))
    second.write_text(json.dumps({"deterministic_payload_sha256": "a" * 64}))
    result, code = WAVE.build_determinism_check(first, second)
    assert code == 0
    assert result["status"] == "PASS"
    second.write_text(json.dumps({"deterministic_payload_sha256": "not-a-hash"}))
    result, code = WAVE.build_determinism_check(first, second)
    assert code == 1
    assert result["hashes_well_formed"] is False


def _git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True, capture_output=True, check=True
    ).stdout.strip()


def _worker(row, *, frontier=None):
    argv = [
        "python", "run_book.py",
        "--namespace", row.namespace,
        "--profile", row.profile,
        "--tags", ",".join(row.tags or ()),
        "--spread-geometry-floor", ",".join(row.spread_geometry_floor),
    ]
    exits = row.frontier_exits if frontier is None else tuple(frontier)
    if exits:
        argv.extend(["--frontier-exits", ",".join(exits)])
    digest = HOST._local_config_digest(row.profile)
    assert digest
    return {
        "argv": argv,
        "argv_sha256": HOST.argv_sha256(argv),
        "config_digest_sha256": digest,
        "token_config_digest_sha256": digest,
    }


NOW = datetime(2026, 8, 8, 7, 0, tzinfo=timezone.utc)


def _receipt(*, mechanism=True):
    launcher = HOST.parse_local_launcher()
    receipt = {
        "schema": HOST.SCHEMA,
        "observation_id": "offline-test-observation",
        "captured_at_utc": "2026-08-08T06:45:00Z",
        "expires_at_utc": "2026-08-08T07:45:00Z",
        "preservation": {"ref": "HEAD", "commit": _git_head()},
        "host_files": {
            "head": _git_head(),
            "launcher_sha256": HOST._sha256(HOST.LAUNCHER.read_bytes()),
            "armed_set_module_present": mechanism,
            "armed_set_manifest_present": mechanism,
        },
        "workers": [_worker(row) for row in launcher.values()],
    }
    receipt["payload_sha256"] = HOST.payload_sha256(receipt)
    return receipt


def test_matching_fresh_receipt_establishes_current_parity():
    result, code = HOST.verify_receipt(_receipt(), now=NOW, max_validity_seconds=3600)
    assert code == 0
    assert result["status"] == "CURRENT_MATCH"
    assert result["observation_current"] is True
    assert result["parity_established"] is True
    assert result["authority"]["host_contacted"] is False
    assert result["authority"]["mutation_performed"] is False


def test_current_ftmo_frontier_and_missing_host_mechanism_are_detected():
    receipt = _receipt(mechanism=False)
    ftmo = HOST.parse_local_launcher()["operator_profile"]
    receipt["workers"][0] = _worker(ftmo, frontier=("crypto",))
    receipt["payload_sha256"] = HOST.payload_sha256(receipt)
    result, code = HOST.verify_receipt(receipt, now=NOW, max_validity_seconds=3600)
    assert code == 1
    assert result["status"] == "CURRENT_MISMATCH"
    frontier = [issue for issue in result["issues"] if issue["field"] == "frontier_exits"]
    assert frontier
    assert all(issue["expected"] == [] and issue["observed"] == ["crypto"] for issue in frontier)
    absent = [issue for issue in result["issues"]
              if issue["kind"] == "host_armed_set_mechanism_absent"]
    assert {issue["field"] for issue in absent} == {
        "armed_set_module_present", "armed_set_manifest_present",
    }


def test_tampering_after_seal_makes_receipt_invalid():
    receipt = _receipt()
    receipt["workers"][0]["argv"].extend(["--frontier-exits", "crypto"])
    result, code = HOST.verify_receipt(receipt, now=NOW, max_validity_seconds=3600)
    assert code == 2
    assert result["status"] == "INVALID_RECEIPT"
    assert "payload_sha256_mismatch" in result["validation_errors"]
    assert any("argv_sha256_mismatch" in error for error in result["validation_errors"])


def test_receipt_without_observation_identity_is_invalid():
    receipt = _receipt()
    receipt.pop("observation_id")
    receipt["payload_sha256"] = HOST.payload_sha256(receipt)
    result, code = HOST.verify_receipt(receipt, now=NOW, max_validity_seconds=3600)
    assert code == 2
    assert "observation_id_missing_or_invalid" in result["validation_errors"]


def test_expired_receipt_never_claims_current_even_when_values_match():
    receipt = _receipt()
    receipt["captured_at_utc"] = "2026-08-08T04:00:00Z"
    receipt["expires_at_utc"] = "2026-08-08T05:00:00Z"
    receipt["payload_sha256"] = HOST.payload_sha256(receipt)
    result, code = HOST.verify_receipt(receipt, now=NOW, max_validity_seconds=3600)
    assert code == 2
    assert result["status"] == "STALE_NOT_CURRENT"
    assert result["observation_current"] is False
    assert result["claim_current_allowed"] is False
    assert result["parity_established"] is False


def test_receipt_cannot_extend_its_validity_window_to_look_fresh():
    receipt = _receipt()
    receipt["expires_at_utc"] = "2026-08-09T06:45:00Z"
    receipt["payload_sha256"] = HOST.payload_sha256(receipt)
    result, code = HOST.verify_receipt(receipt, now=NOW, max_validity_seconds=3600)
    assert code == 2
    assert "validity_window_exceeds_policy" in result["validation_errors"]


def test_local_launcher_and_declaration_currently_agree():
    launcher = HOST.parse_local_launcher()
    declared = HOST.parse_declaration()
    assert set(launcher) == set(declared)
    for namespace in launcher:
        assert launcher[namespace].profile == declared[namespace].profile
        assert set(launcher[namespace].tags or ()) == set(declared[namespace].tags or ())
        assert set(launcher[namespace].frontier_exits) == set(declared[namespace].frontier_exits)
        assert set(launcher[namespace].spread_geometry_floor) == set(
            declared[namespace].spread_geometry_floor
        )
