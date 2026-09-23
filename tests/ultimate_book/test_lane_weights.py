import ast
import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.components.ultimate_book import book_engine as book_engine_module
from src.components.ultimate_book.admission import (
    GovernorLimits,
    GovernorState,
    TradeIntent,
    admit_and_size,
    size_correlated_units,
)
from src.components.ultimate_book.book_engine import UltimateBookLiveEngine
from src.components.ultimate_book.lane_weights import (
    DECLARED_MAX_WEIGHT,
    LaneWeightController,
    LaneWeightsConfigurationError,
    build_unsigned_payload,
    envelope_digest,
    sign_envelope,
)
from src.components.ultimate_book.runtime_learning_packet import (
    build_runtime_learning_packet,
    validate_runtime_learning_packet,
)


NAMESPACE = "operator_profile"
SCOPE = ("crypto", "energy_agri")
EVIDENCE_DIGEST = "a" * 64
REPO = Path(__file__).resolve().parents[2]


def _key(tmp_path):
    path = tmp_path / "external.key"
    path.write_bytes(b"k" * 32)
    path.chmod(0o600)
    return path


def _signed(
    key_path,
    *,
    weights=None,
    namespace=NAMESPACE,
    effective="2026-08-02",
    expires="2026-08-09",
    issued="2026-08-01T12:00:00+00:00",
):
    payload = build_unsigned_payload(
        namespace=namespace,
        weights=weights or {"crypto": 1.15, "energy_agri": 1.0},
        effective_decision_day=effective,
        expires_after_decision_day=expires,
        evidence_digest_sha256=EVIDENCE_DIGEST,
        issued_at_utc=issued,
    )
    return sign_envelope(payload, key_path.read_bytes())


def _source(tmp_path, envelope):
    path = tmp_path / "weights.json"
    path.write_text(json.dumps(envelope), encoding="utf-8")
    return path


def _controller(tmp_path, source, key, *, scope=SCOPE):
    return LaneWeightController(
        namespace=NAMESPACE,
        expected_sleeves=scope,
        repo_root=tmp_path / "repo",
        weights_path=source,
        key_path=key,
    )


def _at(day, hour=0, minute=1):
    return datetime.fromisoformat(f"{day}T{hour:02d}:{minute:02d}:00+00:00")


def test_valid_signed_vector_activates_atomically_and_persists(tmp_path):
    key = _key(tmp_path)
    envelope = _signed(key)
    controller = _controller(tmp_path, _source(tmp_path, envelope), key)

    snapshot = controller.snapshot(_at("2026-08-02"))

    assert snapshot["status"] == "active"
    assert snapshot["weights"] == {"crypto": 1.15, "energy_agri": 1.0}
    assert snapshot["signature_verified"] is True
    assert snapshot["source_digest_sha256"] == envelope_digest(envelope)
    assert controller.state_path.is_file()


@pytest.mark.parametrize(
    "mutator, expected_reason",
    [
        (lambda row: row.update(signature_hmac_sha256="0" * 64), "signature_mismatch"),
        (lambda row: row.update(namespace="other"), "namespace_mismatch"),
        (lambda row: row["weights"].update(crypto=1.16), "weight_out_of_band:crypto"),
        (lambda row: row.update(expires_after_decision_day="2026-08-01"), "expiry_before_effective_day"),
    ],
)
def test_invalid_source_fails_whole_scope_to_neutral(tmp_path, mutator, expected_reason):
    key = _key(tmp_path)
    envelope = _signed(key)
    mutator(envelope)
    # Re-sign semantic mutations so each test reaches the intended contract check.
    if expected_reason != "signature_mismatch":
        envelope = sign_envelope(envelope, key.read_bytes())
    controller = _controller(tmp_path, _source(tmp_path, envelope), key)

    snapshot = controller.snapshot(_at("2026-08-02"))

    assert snapshot["status"] == "neutral"
    assert snapshot["weights"] == {"crypto": 1.0, "energy_agri": 1.0}
    assert expected_reason in snapshot["reason"]


def test_missing_and_stale_sources_fail_loudly_to_neutral(tmp_path, caplog):
    key = _key(tmp_path)
    missing = _controller(tmp_path, tmp_path / "missing.json", key)
    assert missing.snapshot(_at("2026-08-02"))["reason"] == "weights_file_missing"

    stale_source = _source(
        tmp_path,
        _signed(key, effective="2026-07-20", expires="2026-08-01", issued="2026-07-19T12:00:00+00:00"),
    )
    stale = LaneWeightController(
        namespace=NAMESPACE,
        expected_sleeves=SCOPE,
        repo_root=tmp_path / "repo-stale",
        weights_path=stale_source,
        key_path=key,
    )
    assert stale.snapshot(_at("2026-08-02"))["reason"] == "weights_file_stale"
    assert "LANE WEIGHTS NEUTRAL" in caplog.text


def test_partial_args_or_unscoped_carrier_refuses_launch_configuration(tmp_path):
    key = _key(tmp_path)
    source = _source(tmp_path, _signed(key))
    with pytest.raises(LaneWeightsConfigurationError, match="supplied_together"):
        LaneWeightController(namespace=NAMESPACE, expected_sleeves=SCOPE, repo_root=tmp_path, weights_path=source)
    with pytest.raises(LaneWeightsConfigurationError, match="nonempty_tags_scope"):
        LaneWeightController(
            namespace=NAMESPACE,
            expected_sleeves=(),
            repo_root=tmp_path,
            weights_path=source,
            key_path=key,
        )


def test_key_with_group_permissions_fails_to_neutral_on_posix(tmp_path):
    key = _key(tmp_path)
    key.chmod(0o640)
    controller = _controller(tmp_path, _source(tmp_path, _signed(key)), key)
    snapshot = controller.snapshot(_at("2026-08-02"))
    assert snapshot["status"] == "neutral"
    assert snapshot["reason"] == "signing_key_permissions_not_private"


def test_same_day_replacement_is_ignored_in_process_and_after_restart(tmp_path):
    key = _key(tmp_path)
    source = _source(tmp_path, _signed(key, weights={"crypto": 1.15, "energy_agri": 1.0}))
    controller = _controller(tmp_path, source, key)
    first = controller.snapshot(_at("2026-08-02"))

    replacement = _signed(key, weights={"crypto": 0.5, "energy_agri": 0.5})
    source.write_text(json.dumps(replacement), encoding="utf-8")
    same_process = controller.snapshot(_at("2026-08-02", hour=12))
    restarted = _controller(tmp_path, source, key).snapshot(_at("2026-08-02", hour=12))

    assert first["weights"] == same_process["weights"] == restarted["weights"]
    assert restarted["source_digest_sha256"] == first["source_digest_sha256"]


def test_replacement_can_activate_only_at_next_day_boundary(tmp_path):
    key = _key(tmp_path)
    source = _source(tmp_path, _signed(key, weights={"crypto": 1.15, "energy_agri": 1.0}))
    controller = _controller(tmp_path, source, key)
    assert controller.snapshot(_at("2026-08-02"))["weights"]["crypto"] == 1.15
    source.write_text(
        json.dumps(_signed(key, weights={"crypto": 0.5, "energy_agri": 1.0})),
        encoding="utf-8",
    )

    next_day = controller.snapshot(_at("2026-08-03"))

    assert next_day["status"] == "active"
    assert next_day["weights"]["crypto"] == 0.5


def test_first_seen_after_boundary_window_stays_neutral_for_day(tmp_path):
    key = _key(tmp_path)
    source = _source(tmp_path, _signed(key))
    controller = _controller(tmp_path, source, key)

    late = controller.snapshot(_at("2026-08-02", hour=1))
    restarted = _controller(tmp_path, source, key).snapshot(_at("2026-08-02", hour=2))

    assert late["status"] == restarted["status"] == "neutral"
    assert late["reason"] == restarted["reason"] == "missed_decision_day_activation_boundary"


def test_corrupt_same_day_latch_does_not_fall_through_to_live_source(tmp_path):
    key = _key(tmp_path)
    source = _source(tmp_path, _signed(key))
    controller = _controller(tmp_path, source, key)
    controller.state_path.parent.mkdir(parents=True)
    controller.state_path.write_text("{}", encoding="utf-8")

    snapshot = controller.snapshot(_at("2026-08-02"))

    assert snapshot["status"] == "neutral"
    assert snapshot["weights"] == {"crypto": 1.0, "energy_agri": 1.0}
    assert snapshot["reason"].startswith("latch_invalid:")


def test_active_persistence_failure_returns_neutral(tmp_path, monkeypatch):
    key = _key(tmp_path)
    controller = _controller(tmp_path, _source(tmp_path, _signed(key)), key)
    monkeypatch.setattr(controller, "_persist", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("disk")))

    snapshot = controller.snapshot(_at("2026-08-02"))

    assert snapshot["status"] == "neutral"
    assert snapshot["reason"] == "latch_persist_failed:OSError"


def test_engine_injects_controller_vector_without_mutating_config(tmp_path, monkeypatch):
    key = _key(tmp_path)
    controller = _controller(tmp_path, _source(tmp_path, _signed(key)), key)
    config = {
        "ultimate_book_kelly_running_count": False,
        "ultimate_book_kelly_lite": False,
    }
    engine = UltimateBookLiveEngine(
        config,
        SimpleNamespace(),
        str(tmp_path / "engine"),
        namespace=NAMESPACE,
        lane_weight_controller=controller,
    )
    intent = TradeIntent("crypto", "BTCUSD", 1, "2026-08-02", 100.0)
    monkeypatch.setattr(engine, "_generate_intents", lambda tags, now: ([intent], []))
    monkeypatch.setattr(engine, "_equity", lambda: 100000.0)
    monkeypatch.setattr(engine, "_deal_capable", lambda: False)
    monkeypatch.setattr(engine._governor, "reconstruct_day_start_balance", lambda mt5, now: None)
    monkeypatch.setattr(engine._governor, "build", lambda **kwargs: SimpleNamespace())
    monkeypatch.setattr(engine, "_asymmetric_profile_guard", lambda: None)
    monkeypatch.setattr(engine, "_open_risk_pct", lambda equity: 0.0)
    monkeypatch.setattr(engine, "_governor_limits", lambda: SimpleNamespace())
    monkeypatch.setattr(engine, "_joint_daily_limits", lambda limits, state: limits)
    monkeypatch.setattr(engine, "_stress_derisk_state", lambda now: None)
    captured = {}

    def fake_bridge(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(runtime_effect_now=False, decision_status="shadow")

    monkeypatch.setattr(book_engine_module, "evaluate_vnext_ultimate_book_admission", fake_bridge)

    result = engine.evaluate(now_utc=_at("2026-08-02"), tags=SCOPE)

    runtime = captured["config"]["gtos_vnext_runtime"]
    assert runtime["ultimate_book_learning_rerate"] == {"crypto": 1.15, "energy_agri": 1.0}
    assert "ultimate_book_learning_rerate" not in config
    assert result["lane_weights"]["status"] == "active"


def test_packet_stamps_single_and_multi_sleeve_applied_weights():
    lane = {
        "schema_version": "gtos.lane_weights.snapshot.v1",
        "namespace": NAMESPACE,
        "decision_day": "2026-08-02",
        "status": "active",
        "reason": "signed_weights_active",
        "weights": {"crypto": 1.15, "energy_agri": 1.0},
        "scope_sleeves": list(SCOPE),
        "declared_band": {"min": 0.5, "max": 1.15},
        "signature_verified": True,
        "source_digest_sha256": "b" * 64,
        "evidence_digest_sha256": EVIDENCE_DIGEST,
        "effective_decision_day": "2026-08-02",
        "expires_after_decision_day": "2026-08-09",
        "issued_at_utc": "2026-08-01T12:00:00+00:00",
    }
    packet = build_runtime_learning_packet(
        namespace=NAMESPACE,
        event_type="unit_admitted",
        bridge={"runtime_effect_now": True, "lane_weights": lane},
        unit={"sleeve_members": ["crypto", "energy_agri"]},
        outcome={"sleeve": "crypto", "placement_status": "admitted"},
    )

    ok, issues = validate_runtime_learning_packet(packet)
    assert ok, issues
    assert packet["lane_weight"] == 1.15
    assert packet["lane_weights_by_sleeve"] == {"crypto": 1.15, "energy_agri": 1.0}
    assert packet["lane_weight_provenance"]["signature_verified"] is True
    assert packet["lane_weight_provenance"]["source_digest_sha256"] == "b" * 64


def test_learning_weight_cannot_outrank_governor_or_declared_up_band():
    intent = TradeIntent("crypto", "BTCUSD", 1, "2026-08-02", 100.0)
    base = size_correlated_units([intent], base_risk_per_unit=0.01)[0]
    applied = size_correlated_units(
        [intent],
        base_risk_per_unit=0.01,
        learning_rerate={"crypto": DECLARED_MAX_WEIGHT},
    )[0]
    assert applied.unit_risk_pct == pytest.approx(base.unit_risk_pct * DECLARED_MAX_WEIGHT)

    state = GovernorState(
        equity=96900,
        high_water=100000,
        realized_today_pct=-0.031,
        open_risk_pct=0.0,
        max_dd_reference_equity=100000,
    )
    blocked = admit_and_size(
        [intent],
        state,
        profile="clean3_w7_ceiling_nom2p00",
        include_clean3=True,
        kelly_lite=True,
        limits=GovernorLimits(soft_daily_stop_pct=0.03),
        learning_rerate={"crypto": DECLARED_MAX_WEIGHT},
    )
    assert blocked["new_entries_allowed"] is False
    assert blocked["units"] == []


def test_run_book_declares_paired_args_and_passes_controller_without_execution():
    tree = ast.parse((REPO / "run_book.py").read_text(encoding="utf-8"))
    declared = [
        node.args[0].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
        and node.args
        and isinstance(node.args[0], ast.Constant)
    ]
    assert declared.count("--lane-weights") == 1
    assert declared.count("--lane-weights-key") == 1
    constructors = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and getattr(node.func, "id", None) == "UltimateBookOwner"
    ]
    assert len(constructors) == 1
    kwargs = {keyword.arg for keyword in constructors[0].keywords}
    assert "lane_weight_controller" in kwargs


def test_supervisor_binds_current_account_scopes_and_contracts_to_external_files():
    """The lane-weight contract is this test's subject. The armed set is NOT written down here.

    Three of these assertions used to be literal `tags="…"` and `frontier="…"` strings, and
    they pinned the FTMO row as it stood before 2026-08-05 — including
    `mx_btcusd_d1_donchian_20_breakout` and its `--frontier-exits`, the sleeve the owner
    disarmed. It was the fifth artifact to write the armed set down from memory, and like the
    other four (CLAUDE.md §4: "Do not write the set down again anywhere") it was wrong, and it
    stayed wrong until the launcher was repaired and this test went red for the right reason.

    `src.safety.armed_set` is the single source of truth; `reconcile()` is what proves the
    launcher and the owner declaration agree, and `tests/safety/test_armed_set_single_source.py`
    owns that invariant in full. Here we assert only what this file is about: that every book
    the launcher starts is bounded, and that the lane-weight contract is bound to external files.

    RESCOPED 2026-08-25 (root cause: STALE EXPECTATION). `reconcile() == []` stopped being
    the true contract of the COMMITTED tree: the host supervisor now has exactly TWO book
    rows (FTMO prod + FN) and NO F5 row — the F5 pair runs under its own scheduled task
    (`GTOS_F5_FTMO`) — and the committed launcher's F5 rows are the stale 2026-08-12
    32-sleeve/$10 record, deliberately diverged from the host while the manifest's
    `operator` was updated to the live 62-sleeve/$75 contract at the truth snapshot
    (docs/audits/fable-20260825/CEREMONY-RECEIPT-20260825.md: "committed launcher row is
    stale"; OWNER-GRANT-20260825.md). This test's own docstring already scoped it to the
    lane-weight contract, which rides the PRODUCTION rows — so assert the production
    surface reconciles CLEAN, and that every residual disagreement is confined to declared
    experiment namespaces. Any new production-touching drift still fails here; the full
    experiment-side invariant stays owned by tests/safety/test_armed_set_single_source.py.
    """
    from src.safety.armed_set import (
        SURFACE_EXPERIMENT,
        declared_arming,
        launcher_arming,
        production_arming,
        reconcile,
    )

    source = (REPO / "scripts/run_book_supervisor.ps1").read_text(encoding="utf-8")

    declared = declared_arming()
    problems = reconcile(launcher=production_arming(launcher_arming()),
                         declared=production_arming(declared))
    assert problems == [], "production books disagree with the declaration:\n" + \
        "\n".join(str(p) for p in problems)
    experiment_namespaces = {ns for ns, row in declared.items()
                             if row.surface == SURFACE_EXPERIMENT}
    stray = [p for p in reconcile() if p.namespace not in experiment_namespaces]
    assert stray == [], "disagreement OUTSIDE the known stale experiment rows:\n" + \
        "\n".join(str(p) for p in stray)

    rows = launcher_arming()
    assert rows, "the launcher starts no book at all"
    for namespace, row in rows.items():
        # `--tags ""` is FAIL-OPEN (run_book.py: `... if args.tags else None`): every BUILT
        # sleeve runs. Asserting the tags are non-empty is the safety property; asserting
        # WHICH ones is the declaration's job, not this test's.
        assert not row.is_fail_open, f"{namespace} passes no --tags: every BUILT sleeve is armed"
        assert row.spread_geometry_floor == declared[namespace].spread_geometry_floor

    assert '"--lane-weights", $b.laneWeights' in source
    assert '"--lane-weights-key", $b.laneWeightsKey' in source
    assert "C:\\ProgramData\\GTOS\\lane-weights" in source
    assert "--entry-hour" not in source  # Session CH's current DO-NOT-ARM verdict


def test_operator_utility_has_no_broker_import_or_action_surface():
    tree = ast.parse((REPO / "scripts/gtos_lane_weights.py").read_text(encoding="utf-8"))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    assert not any("mt5" in name.lower() or "broker" in name.lower() for name in imported)


def test_week_one_telemetry_verifier_matches_declared_vector(tmp_path, capsys):
    from scripts.gtos_lane_weights import main

    key = _key(tmp_path)
    envelope = _signed(key)
    weights_path = _source(tmp_path, envelope)
    lane = {
        "schema_version": "gtos.lane_weights.snapshot.v1",
        "namespace": NAMESPACE,
        "decision_day": "2026-08-02",
        "status": "active",
        "reason": "signed_weights_active",
        "weights": {"crypto": 1.15, "energy_agri": 1.0},
        "scope_sleeves": list(SCOPE),
        "declared_band": {"min": 0.5, "max": 1.15},
        "signature_verified": True,
        "source_digest_sha256": envelope_digest(envelope),
        "evidence_digest_sha256": EVIDENCE_DIGEST,
        "effective_decision_day": "2026-08-02",
        "expires_after_decision_day": "2026-08-09",
        "issued_at_utc": "2026-08-01T12:00:00+00:00",
    }
    packet = build_runtime_learning_packet(
        namespace=NAMESPACE,
        event_type="unit_shadow",
        ts="2026-08-02T00:01:00+00:00",
        bridge={"runtime_effect_now": False, "lane_weights": lane},
        unit={"sleeve_members": ["crypto"]},
        outcome={"sleeve": "crypto", "placement_status": "shadow"},
    )
    log = tmp_path / "packets.jsonl"
    log.write_text(json.dumps(packet) + "\n", encoding="utf-8")

    rc = main([
        "telemetry",
        "--input", str(log),
        "--weights", str(weights_path),
        "--key", str(key),
        "--namespace", NAMESPACE,
        "--tags", ",".join(SCOPE),
        "--start-day", "2026-08-02",
        "--days", "1",
    ])

    report = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert report["ok"] is True
    assert report["packet_count"] == 1
    assert report["mismatch_count"] == 0
