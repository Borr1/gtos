from __future__ import annotations

import ast
import builtins
from collections.abc import Callable
import importlib
import importlib.util
import math
from pathlib import Path
import socket
import subprocess
import sys
from types import ModuleType
import urllib.request

import pytest


REPO = Path(__file__).resolve().parents[2]
ADAPTER_PATH = REPO / "src/research_infra/wave20_complete_path_shadow.py"
DECISION_US = 1_000_000_000
MINUTE_US = 60_000_000


@pytest.fixture(scope="module")
def adapter() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "session_hm_wave20_complete_path_shadow_under_test", ADAPTER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _permission_inputs() -> dict:
    return {
        "session_state": {
            "asof_utc": "2026-01-02T13:15:00Z",
            "session_open": True,
            "daily_loss_blocked": False,
        },
        "account_headroom": {
            "snapshot_status": "VALID",
            "daily_headroom_pct": 2.0,
            "overall_headroom_pct": 4.0,
        },
        "symbol_state": {
            "symbol": "XAUUSD",
            "trade_mode": "ENABLED",
            "position_conflict": False,
        },
        "mt5_interface_response": {
            "interface_status": "INERT_OK",
            "symbol_visible": True,
        },
    }


def _candidate(candidate_id: str = "candidate-src-1") -> dict:
    return {
        "candidate_id": candidate_id,
        "origin_family": "current_breaker_re_entry",
        "symbol": "XAUUSD",
        "side": "LONG",
        "direction": "LONG",
        "decision_time_utc": "2026-01-02T13:15:00Z",
        "entry_price": 100.0,
        "stop_loss": 98.0,
        "take_profit_1": 103.0,
        "risk_reward_ratio": 1.5,
        "predecision_features": {
            "stop_distance_atr": 2.0,
            "target_distance_atr": 3.0,
        },
        "source_fields": {"uses_outcome_fields": False},
        "trade_parameters": {
            "direction": "LONG",
            "entry_price": 100.0,
            "stop_loss": 98.0,
            "take_profit_1": 103.0,
            "risk_reward_ratio": 1.5,
        },
    }


def _account_snapshot(scope: str = "operator_profile") -> dict:
    return {
        "account_scope": scope,
        "profile_id": scope,
        "profile_snapshot_sha256": "a" * 64,
        "symbol_snapshot_sha256": "b" * 64,
        "broker_symbol": "XAUUSD",
        "deviation_points": 12,
        "magic": 20260725,
        "comment": "P1_SYNTHETIC",
        "filling_mode": "ORDER_FILLING_IOC",
    }


def _capture_evidence() -> dict:
    return {
        "spread_r": {
            "value": 0.10,
            "source": "historical_ftmo_predecision_tick",
            "source_status": "captured",
        },
        "expected_slippage_r": {
            "value": 0.02,
            "source": "config.selected_cell_default_expected_slippage_r",
            "source_status": "captured",
        },
        "swap_cost_r": {
            "value": 0.03,
            "source": "points_mode_time_stop_swap_cost_r_v1",
            "source_status": "captured",
        },
        "commission_r": {
            "value": 0.05,
            "source": "broker_true_BROKER_TRUE_COSTS_V1_round_turn_over_stop_distance",
            "source_status": "captured",
            "included_in_total_cost_r": True,
        },
    }


def _complete_cost_row() -> dict:
    return {
        "spread_r": 0.10,
        "expected_slippage_r": 0.02,
        "swap_cost_r": 0.03,
        "commission_r": 0.05,
        "cost_r": 0.20,
        "cost_component_capture_evidence": _capture_evidence(),
        "cost_quote_source": "historical_ftmo_predecision_tick",
        "expected_slippage_source": "config.selected_cell_default_expected_slippage_r",
        "commission_r_broker_true_measured": 0.05,
        "commission_r_repair_status": "applied",
        "commission_r_repair_total_redecode_status": "complete_component_sum",
        "commission_r_source": (
            "broker_true_BROKER_TRUE_COSTS_V1_round_turn_over_stop_distance"
        ),
    }


def _hdf_input() -> dict:
    return {
        "cell": {"id": "V00", "kind": "identity"},
        "decision_time_us": DECISION_US,
        "cost_r": 999.0,
        "source_mode": "SYNTHETIC_TICK",
        "points": [
            {
                "time_us": DECISION_US + MINUTE_US,
                "signed_r": 0.4,
                "deadline_eligible": True,
                "source_index": 1,
            },
            {
                "time_us": DECISION_US + 2 * MINUTE_US,
                "signed_r": 1.2,
                "deadline_eligible": True,
                "source_index": 2,
            },
        ],
    }


def _source(
    source_id: str = "src-1",
    *,
    window: str = "january_2026",
    decision_time_utc: str = "2026-01-02T13:15:00Z",
    scope: str = "operator_profile",
) -> dict:
    candidate_id = f"candidate-{source_id}"
    candidate = _candidate(candidate_id)
    candidate["decision_time_utc"] = decision_time_utc
    return {
        "source_window_id": window,
        "source_opportunity_id": source_id,
        "candidate_id": candidate_id,
        "symbol": "XAUUSD",
        "side": "LONG",
        "decision_time_utc": decision_time_utc,
        "account_scope": scope,
        "synthetic_candidate": candidate,
        "permission_inputs": _permission_inputs(),
        "order_kind": "market",
        "account_snapshot": _account_snapshot(scope),
        "synthetic_fill": {
            "status": "FILLED",
            "reason": "synthetic_known_answer_fill",
        },
        "hde_cost_input": _complete_cost_row(),
        "hdf_exit_input": _hdf_input(),
    }


def _dependencies(
    adapter: ModuleType,
    *,
    generate: Callable | None = None,
    route: Callable | None = None,
    schedule: Callable | None = None,
    fill: Callable | None = None,
):
    # Contract evolution at commit 9059cfa06 (receipted by
    # P1_UPSTREAM_PACKET_INDEPENDENT_FALSIFICATION.json, u11_status
    # U11_REPAIRED_ADAPTER_AND_REFERENCES_BOUND): the runner refuses any stage
    # callable that is not the exact in-module bound function
    # (*_dependency_not_bound). Defaults are therefore the four bound
    # callables; overrides remain so tests can pin that refusal itself.
    return adapter.ShadowDependencies(
        generate_candidate=generate or adapter.source_bound_candidate_generator,
        dynamic_router=route or adapter.inert_admit_unchanged_router,
        scheduler_capture=schedule or adapter.inert_scheduler_capture,
        fill_or_no_fill=fill or adapter.source_bound_fill_projection,
    )


class _Exploding:
    def __iter__(self):
        raise AssertionError("iterator touched")

    def __getattribute__(self, name: str):
        if name.startswith("__"):
            return object.__getattribute__(self, name)
        raise AssertionError(f"dependency touched:{name}")


def test_default_off_ignores_exploding_iterable_and_dependencies(adapter: ModuleType) -> None:
    result = adapter.run_complete_path_shadow(_Exploding(), dependencies=_Exploding())

    assert result["status"] == "DEFAULT_OFF"
    assert result["source_opportunity_count"] == result["stage_row_count"] == 0
    assert result["execution_authority"] is False
    assert result["activation_authority"] is False
    assert result["result_bearing_science_executed"] is False


@pytest.mark.parametrize("enabled", [1, "true", {"enabled": True}, object()])
def test_only_literal_true_can_leave_default_off(
    adapter: ModuleType, enabled: object
) -> None:
    result = adapter.run_complete_path_shadow(
        _Exploding(), enabled=enabled, dependencies=_Exploding()
    )

    assert result["status"] == "DEFAULT_OFF"
    assert result["enabled"] is False


def _resolve_local_module(module: str) -> Path | None:
    stem = REPO.joinpath(*module.split("."))
    for candidate in (stem.with_suffix(".py"), stem / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None


def test_ast_transitive_closure_has_no_effect_capabilities() -> None:
    queue = [ADAPTER_PATH]
    seen: set[Path] = set()
    forbidden_imports = {
        "MetaTrader5",
        "src.mt5.mt5_real",
        "src.components.execution",
        "src.components.orchestrator",
    }
    risky_import_roots = {
        "aiohttp",
        "ftplib",
        "http",
        "importlib",
        "os",
        "pathlib",
        "requests",
        "smtplib",
        "socket",
        "subprocess",
        "urllib",
    }
    effect_calls = {
        "__import__",
        "connect",
        "dump",
        "eval",
        "exec",
        "mkdir",
        "open",
        "open_trade",
        "order_send",
        "Popen",
        "rename",
        "rmdir",
        "send",
        "sendall",
        "system",
        "touch",
        "unlink",
        "urlopen",
        "write_bytes",
        "write_text",
    }
    import_hits: list[tuple[str, str]] = []
    effect_hits: list[tuple[str, int, str]] = []
    top_level_effects: list[tuple[str, int, str]] = []

    while queue:
        path = queue.pop(0).resolve()
        if path in seen:
            continue
        seen.add(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                names = [node.module]
            for name in names:
                root = name.split(".", 1)[0]
                if name in forbidden_imports or root in risky_import_roots:
                    import_hits.append((str(path.relative_to(REPO)), name))
                local = _resolve_local_module(name)
                if local is not None and local.resolve() not in seen:
                    queue.append(local)
            if isinstance(node, ast.Call):
                called = (
                    node.func.id
                    if isinstance(node.func, ast.Name)
                    else node.func.attr
                    if isinstance(node.func, ast.Attribute)
                    else ""
                )
                if called in effect_calls:
                    effect_hits.append((str(path.relative_to(REPO)), node.lineno, called))
        for node in tree.body:
            if isinstance(
                node,
                (
                    ast.Import,
                    ast.ImportFrom,
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Assign,
                    ast.AnnAssign,
                ),
            ):
                continue
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                continue
            if (
                isinstance(node, ast.If)
                and len(node.body) == 1
                and isinstance(node.body[0], ast.Raise)
                and not node.orelse
            ):
                # Receipted fail-closed import-time integrity guard (adapter
                # lines 198-199, commit 9059cfa06: FIXED_BREAKER_MEMBER_RECORD
                # must canonical-hash to FIXED_BREAKER_MEMBER_CANONICAL_SHA256
                # or import raises). A lone-raise conditional can only fail
                # closed; it has no effect capability. Any effectful call or
                # risky import inside it is still swept by the ast.walk
                # import/effect checks above.
                continue
            top_level_effects.append(
                (str(path.relative_to(REPO)), node.lineno, type(node).__name__)
            )

    assert {path.relative_to(REPO).as_posix() for path in seen} == {
        "src/research_infra/wave20_complete_path_shadow.py",
        "src/components/candidate_geometry.py",
        "src/components/current_breaker_re_entry_repair.py",
        "src/research_infra/exit_overlay.py",
        "src/research_infra/train_engine/decision_semantics.py",
    }
    assert import_hits == []
    assert effect_hits == []
    assert top_level_effects == []


def test_fresh_import_has_no_write_network_subprocess_or_dynamic_import_effect(
    adapter: ModuleType, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    del adapter
    touched: list[str] = []

    def bomb(label: str):
        def fail(*args, **kwargs):
            touched.append(label)
            raise AssertionError(label)

        return fail

    real_open = builtins.open

    def guarded_open(file, mode="r", *args, **kwargs):
        if any(flag in str(mode) for flag in "wax+"):
            return bomb(f"open:{mode}")(file)
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    monkeypatch.setattr(builtins, "open", guarded_open)
    for name in ("write_text", "write_bytes", "touch", "mkdir", "unlink", "rename", "replace"):
        monkeypatch.setattr(Path, name, bomb(f"Path.{name}"))
    monkeypatch.setattr(socket, "create_connection", bomb("socket.create_connection"))
    monkeypatch.setattr(urllib.request, "urlopen", bomb("urllib.request.urlopen"))
    for name in ("Popen", "run", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, bomb(f"subprocess.{name}"))
    monkeypatch.setattr(importlib, "import_module", bomb("importlib.import_module"))

    spec = importlib.util.spec_from_file_location("session_hm_fresh_import", ADAPTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    assert touched == []


def test_duplicate_composite_identity_refuses_before_dependency_invocation(
    adapter: ModuleType,
) -> None:
    calls: list[str] = []
    deps = _dependencies(
        adapter,
        generate=lambda source: calls.append("generate") or [source["synthetic_candidate"]],
    )
    source = _source()

    with pytest.raises(adapter.ShadowRefusal, match="duplicate_source_composite_identity"):
        adapter.run_complete_path_shadow([source, source], enabled=True, dependencies=deps)
    assert calls == []


@pytest.mark.parametrize(
    "generated",
    [
        [],
        [_candidate(), _candidate("second")],
        _candidate(),
    ],
    ids=["zero_rows", "two_rows", "mapping_not_iterable_of_rows"],
)
def test_bad_generator_cardinality_preserves_eleven_stage_denominator(
    adapter: ModuleType, generated: object
) -> None:
    # Since 9059cfa06 an injected generator is refused as not-bound BEFORE it
    # can misreport cardinality. Had the lambda been invoked, the recorded
    # reason would have been a cardinality/shape refusal instead, so the exact
    # reason assertion below doubles as proof of non-invocation. The
    # cardinality taxonomy itself stays pinned by
    # test_bound_generator_zero_candidates_is_exact_cardinality_miss.
    result = adapter.run_complete_path_shadow(
        [_source()],
        enabled=True,
        dependencies=_dependencies(adapter, generate=lambda source: generated),
    )

    assert result["stage_row_count"] == len(adapter.STAGES) == 11
    assert [row["stage"] for row in result["stage_ledger"]] == list(adapter.STAGES)
    assert result["missed_opportunity_ledger"][0]["first_missing_stage"] == (
        "candidate_generation"
    )
    assert result["missed_opportunity_ledger"][0]["reason"] == (
        "candidate_generator_dependency_not_bound"
    )


def test_bound_generator_zero_candidates_is_exact_cardinality_miss(
    adapter: ModuleType,
) -> None:
    # The bound generator projects only the source-embedded candidate; a
    # source that carries none must become the exact cardinality-zero miss at
    # candidate_generation with the eleven-stage denominator preserved.
    source = _source()
    del source["synthetic_candidate"]

    result = adapter.run_complete_path_shadow(
        [source], enabled=True, dependencies=_dependencies(adapter)
    )

    assert result["stage_row_count"] == len(adapter.STAGES) == 11
    assert [row["stage"] for row in result["stage_ledger"]] == list(adapter.STAGES)
    assert result["missed_opportunity_ledger"][0]["first_missing_stage"] == (
        "candidate_generation"
    )
    assert result["missed_opportunity_ledger"][0]["reason"] == (
        "candidate_generation_candidate_count_not_one:0"
    )


@pytest.mark.parametrize("malformed", [None, [], "permission", 7, True])
def test_malformed_permission_container_fails_closed(
    adapter: ModuleType, malformed: object
) -> None:
    result = adapter.evaluate_inert_permission(malformed)

    assert result["status"] == "REFUSED"
    assert result["reason"] == "permission_inputs_not_mapping"


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (
            lambda value: value["account_headroom"].__setitem__("daily_headroom_pct", True),
            "permission_invalid_numeric:account_headroom.daily_headroom_pct",
        ),
        (
            lambda value: value["account_headroom"].__setitem__(
                "overall_headroom_pct", math.inf
            ),
            "permission_invalid_numeric:account_headroom.overall_headroom_pct",
        ),
        (
            lambda value: value["account_headroom"].__setitem__("daily_headroom_pct", -0.01),
            "permission_daily_headroom_negative",
        ),
        (
            lambda value: value["account_headroom"].__setitem__("dailyHeadroomPct", value["account_headroom"].pop("daily_headroom_pct")),
            "permission_missing_required_field:account_headroom.daily_headroom_pct",
        ),
        (
            lambda value: value.__setitem__("symbol_state", ["XAUUSD"]),
            "permission_missing_required_field:symbol_state",
        ),
    ],
)
def test_permission_boolean_nonfinite_negative_alias_and_nested_malformed_refuse(
    adapter: ModuleType, mutation: Callable[[dict], None], reason: str
) -> None:
    inputs = _permission_inputs()
    mutation(inputs)

    result = adapter.evaluate_inert_permission(inputs)

    assert result["status"] == "REFUSED"
    assert result["reason"] == reason


@pytest.mark.parametrize(
    "bad_hash",
    ["", "a" * 63, "g" * 64, "A" * 64, True, 7],
)
def test_invalid_injected_hash_refuses_before_fill_dependency(
    adapter: ModuleType, bad_hash: object
) -> None:
    source = _source()
    source["account_snapshot"]["profile_snapshot_sha256"] = bad_hash
    calls: list[str] = []
    result = adapter.run_complete_path_shadow(
        [source],
        enabled=True,
        dependencies=_dependencies(
            adapter,
            fill=lambda preimage, row: calls.append("fill") or row["synthetic_fill"],
        ),
    )

    assert calls == []
    assert result["missed_opportunity_ledger"][0]["first_missing_stage"] == (
        "order_preimage"
    )
    assert "profile_snapshot_sha256" in result["missed_opportunity_ledger"][0]["reason"]


@pytest.mark.parametrize(
    ("path", "reason"),
    [
        ("january/../march/pool.jsonl.gz", "march_2026_read_forbidden"),
        ("april\\..\\live-forward\\rows.jsonl", "live_forward_read_forbidden"),
        ("may/../february/result.json", "february_window_alias_forbidden"),
        ("january/%2e%2e/january/pool.jsonl", "source_path_alias_forbidden"),
    ],
)
def test_path_aliased_forbidden_window_refuses_before_reader(
    adapter: ModuleType, path: str, reason: str
) -> None:
    calls: list[str] = []

    with pytest.raises(adapter.ShadowRefusal, match=reason):
        adapter.guarded_source_read(
            path,
            window_id="january_2026",
            purpose="metadata",
            reader=lambda value: calls.append(value),
        )
    assert calls == []


@pytest.mark.parametrize(
    ("window", "decision_time", "reason"),
    [
        ("january_2026", "2026-01-31T00:00:00Z", "source_decision_outside_commissioned_window"),
        ("april_2026", "2026-05-01T00:00:00Z", "source_decision_outside_commissioned_window"),
        ("may_2026", "2026-05-31T00:00:00Z", "source_decision_outside_commissioned_window"),
        ("january_2026", "2026-01-02T13:15:00", "source_decision_time_not_true_utc"),
        ("january_2026", "not-a-time", "source_decision_time_invalid"),
    ],
)
def test_noncommissioned_or_non_utc_identity_refuses_before_dependency(
    adapter: ModuleType, window: str, decision_time: str, reason: str
) -> None:
    calls: list[str] = []

    with pytest.raises(adapter.ShadowRefusal, match=reason):
        adapter.run_complete_path_shadow(
            [_source(window=window, decision_time_utc=decision_time)],
            enabled=True,
            dependencies=_dependencies(
                adapter,
                generate=lambda source: calls.append("generate")
                or [source["synthetic_candidate"]],
            ),
        )
    assert calls == []


def test_scheduler_input_mutation_is_isolated_refused_and_cannot_change_preimage(
    adapter: ModuleType,
) -> None:
    source = _source()
    original_hash = source["account_snapshot"]["profile_snapshot_sha256"]
    invoked: list[str] = []

    def mutate(candidate: dict, row: dict) -> dict:
        invoked.append("scheduler")
        candidate["entry_price"] = 1.0
        row["account_snapshot"]["profile_snapshot_sha256"] = "c" * 64
        return {"capture": "benign"}

    result = adapter.run_complete_path_shadow(
        [source],
        enabled=True,
        dependencies=_dependencies(adapter, schedule=mutate),
    )

    # Since 9059cfa06 a non-bound scheduler is refused BEFORE invocation
    # (scheduler_capture_dependency_not_bound), which is strictly stronger
    # than the detect-after-invocation contract this test originally pinned
    # (scheduler_capture_input_mutation_forbidden): the hostile mutation can
    # no longer run at all, so the caller's source and the preimage stay
    # untouched by construction — both still asserted below.
    assert invoked == []
    assert source["account_snapshot"]["profile_snapshot_sha256"] == original_hash
    miss = result["missed_opportunity_ledger"][0]
    assert miss["first_missing_stage"] == "scheduler_capture_only"
    assert miss["reason"] == "scheduler_capture_dependency_not_bound"
    rows = {row["stage"]: row for row in result["stage_ledger"]}
    assert rows["order_preimage"]["disposition"] == "NOT_REACHED_PRIOR_STAGE_MISS"


@pytest.mark.parametrize(
    "alias",
    ["candidateProbability", "candidate-probability", "modelProbability", "predicted-value", "learnedValue"],
)
def test_nested_aliased_learned_probability_or_value_stops_k1(
    adapter: ModuleType, alias: str
) -> None:
    packet = {"nested": [{alias: 0.9}]}

    with pytest.raises(adapter.K1StaleRefusal, match="k1_learned_authority_forbidden"):
        adapter.scheduler_capture_only(packet, incoming_disposition="ADMIT")


def test_cyclic_scheduler_packet_fails_closed_without_recursion_escape(
    adapter: ModuleType,
) -> None:
    cycle: list[object] = []
    cycle.append(cycle)

    with pytest.raises(adapter.ShadowRefusal, match="canonical_payload_cycle"):
        adapter.scheduler_capture_only({"telemetry": cycle}, incoming_disposition="ADMIT")


def test_scheduler_rank_suppression_sizing_and_disposition_are_telemetry_only(
    adapter: ModuleType,
) -> None:
    result = adapter.scheduler_capture_only(
        {
            "rank": 1,
            "suppression": "DROP",
            "size": 99,
            "requested_disposition": "REJECT",
        },
        incoming_disposition="ADMIT",
    )

    assert result["input_disposition"] == result["output_disposition"] == "ADMIT"
    assert result["effect"] == "NONE"
    assert result["selection_authority"] is False
    assert result["ranking_authority"] is False
    assert result["suppression_authority"] is False
    assert result["sizing_authority"] is False


def test_scheduler_writer_object_is_never_invoked_and_becomes_exact_miss(
    adapter: ModuleType,
) -> None:
    called: list[str] = []

    class Writer:
        def __call__(self):
            called.append("writer")
            raise AssertionError("writer invoked")

    result = adapter.run_complete_path_shadow(
        [_source()],
        enabled=True,
        dependencies=_dependencies(
            adapter,
            schedule=lambda candidate, source: {"writer": Writer()},
        ),
    )

    # Since 9059cfa06 the non-bound scheduler is refused before it can even
    # construct the writer payload.
    assert called == []
    assert result["missed_opportunity_ledger"][0]["first_missing_stage"] == (
        "scheduler_capture_only"
    )
    assert result["missed_opportunity_ledger"][0]["reason"] == (
        "scheduler_capture_dependency_not_bound"
    )

    # The canonical-payload taxonomy this test originally surfaced through the
    # run path stays pinned at its source: a writer object can never enter a
    # canonical hash, and it is refused without ever being invoked.
    with pytest.raises(
        adapter.ShadowRefusal, match="canonical_payload_unsupported:Writer"
    ):
        adapter.canonical_sha256({"writer": Writer()})
    assert called == []


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("candidate_id", "another-candidate"),
        ("symbol", "EURUSD"),
        ("side", "SHORT"),
        ("direction", "SHORT"),
        ("decision_time_utc", "2026-01-02T13:16:00Z"),
    ],
)
def test_generated_candidate_identity_alias_refuses_before_transform(
    adapter: ModuleType, field: str, value: str
) -> None:
    # Since 9059cfa06 candidates can only enter through the bound
    # source-embedded generator, so the identity drift is planted inside the
    # source's own synthetic_candidate. The composite identity is still bound
    # from the source's top-level fields, so the drifted candidate must refuse
    # at candidate_generation before the fixed breaker transform runs.
    source = _source()
    source["synthetic_candidate"][field] = value
    result = adapter.run_complete_path_shadow(
        [source],
        enabled=True,
        dependencies=_dependencies(adapter),
    )

    assert result["missed_opportunity_ledger"][0]["first_missing_stage"] == (
        "candidate_generation"
    )
    assert result["missed_opportunity_ledger"][0]["reason"].startswith(
        "candidate_generation_identity_mismatch:"
    )
    rows = {row["stage"]: row for row in result["stage_ledger"]}
    assert rows["fixed_breaker_transform"]["disposition"] == (
        "NOT_REACHED_PRIOR_STAGE_MISS"
    )


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (lambda row: row.__setitem__("entry_price", True), "order_preimage_invalid_numeric:entry_price"),
        (lambda row: row.__setitem__("entry_price", math.nan), "order_preimage_invalid_numeric:entry_price"),
        (lambda row: row.__setitem__("entry_price", 0.0), "order_preimage_nonpositive:entry_price"),
        (lambda row: row.__setitem__("stop_loss", -1.0), "order_preimage_nonpositive:stop_loss"),
        (lambda row: row.__setitem__("direction", "SHORT"), "order_preimage_side_direction_conflict"),
        (lambda row: row.__setitem__("stop_loss", 101.0), "order_preimage_geometry_invalid"),
    ],
)
def test_order_preimage_malformed_nonfinite_negative_alias_and_geometry_refuse(
    adapter: ModuleType, mutation: Callable[[dict], None], reason: str
) -> None:
    candidate = _candidate()
    mutation(candidate)

    with pytest.raises(adapter.ShadowRefusal, match=reason):
        adapter.project_order_preimage(
            candidate,
            order_kind="market",
            account_snapshot=_account_snapshot(),
            account_scope="operator_profile",
        )


def test_market_and_limit_preimages_keep_owner_volume_unset_across_accounts(
    adapter: ModuleType,
) -> None:
    candidate = _candidate()
    candidate.update({"volume": 88.0, "risk_per_trade_pct": 4.0})
    ftmo_snapshot = _account_snapshot()
    funded_snapshot = _account_snapshot("redacted_account")
    ftmo_snapshot.update({"volume": 77.0, "risk_per_trade_pct": 3.0})
    funded_snapshot.update({"volume": 66.0, "risk_per_trade_pct": 2.0})

    market = adapter.project_order_preimage(
        candidate,
        order_kind="market",
        account_snapshot=ftmo_snapshot,
        account_scope="operator_profile",
    )
    limit = adapter.project_order_preimage(
        candidate,
        order_kind="limit",
        account_snapshot=funded_snapshot,
        account_scope="redacted_account",
    )

    assert market["volume"] is limit["volume"] is None
    assert market["volume_status"] == limit["volume_status"] == (
        "NOT_EVALUABLE_OWNER_INPUT_REQUIRED"
    )
    assert adapter.account_claim_scope("redacted_account")["economic_gate_allowed"] is False
    assert adapter.account_claim_scope("redacted_account")["promotion_or_veto_allowed"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("spread_r", True),
        ("expected_slippage_r", math.inf),
        ("swap_cost_r", -0.01),
        ("commission_r", "0.05"),
    ],
)
def test_hde_invalid_component_arithmetic_never_becomes_authoritative(
    adapter: ModuleType, field: str, value: object
) -> None:
    row = _complete_cost_row()
    row[field] = value
    row["cost_component_capture_evidence"][field]["value"] = value

    result = adapter.project_hde_cost(row)

    assert result["state"] in {"incomplete", "refused"}
    assert result["authoritative_cost_r"] is None


@pytest.mark.parametrize(
    ("delta", "state"),
    [(0.5e-8, "complete"), (1.5e-8, "refused")],
)
def test_hde_component_sum_tolerance_edge(
    adapter: ModuleType, delta: float, state: str
) -> None:
    row = _complete_cost_row()
    row["cost_r"] = 0.20 + delta

    result = adapter.project_hde_cost(row)

    assert result["state"] == state
    assert (result["authoritative_cost_r"] is not None) is (state == "complete")


def test_hdf_deadline_partial_terminal_and_source_gap_edges(adapter: ModuleType) -> None:
    deadline = adapter.project_hdf_exit(
        {
            "cell": {"id": "TB", "kind": "time_box", "minutes": 30},
            "decision_time_us": DECISION_US,
            "cost_r": 0.0,
            "source_mode": "SYNTHETIC",
            "points": [
                {
                    "time_us": DECISION_US + 30 * MINUTE_US,
                    "signed_r": 2.2,
                    "deadline_eligible": True,
                    "source_index": 30,
                }
            ],
        }
    )
    partial = adapter.project_hdf_exit(
        {
            "cell": {"id": "PH", "kind": "partial_harvest", "trigger_r": 0.5, "fraction": 0.5},
            "decision_time_us": DECISION_US,
            "cost_r": 0.2,
            "source_mode": "SYNTHETIC",
            "points": [
                {"time_us": DECISION_US + MINUTE_US, "signed_r": 0.5, "deadline_eligible": True, "source_index": 1},
                {"time_us": DECISION_US + 2 * MINUTE_US, "signed_r": 2.0, "deadline_eligible": True, "source_index": 2},
            ],
        }
    )
    terminal = adapter.project_hdf_exit(_hdf_input())
    gap = adapter.project_hdf_exit(
        {
            "cell": {"id": "V00", "kind": "identity"},
            "decision_time_us": DECISION_US,
            "cost_r": 0.0,
            "source_mode": "SYNTHETIC",
            "points": [],
        }
    )

    assert deadline["exit_reason"] == "time_box"
    assert deadline["gross_r"] == pytest.approx(2.0)
    assert partial["partial_realized_r"] == pytest.approx(0.25)
    assert partial["net_r"] == pytest.approx(1.05)
    assert terminal["exit_reason"] == "horizon_terminal_mark"
    assert gap["status"] == "SOURCE_GAP"


@pytest.mark.parametrize(
    ("stage", "reason", "overrides"),
    [
        (
            "candidate_generation",
            "candidate_generator_dependency_not_bound",
            {"generate": lambda source: (_ for _ in ()).throw(RuntimeError("boom"))},
        ),
        (
            "dynamic_router",
            "dynamic_router_dependency_not_bound",
            {"route": lambda candidate, source: (_ for _ in ()).throw(RuntimeError("boom"))},
        ),
        (
            "scheduler_capture_only",
            "scheduler_capture_dependency_not_bound",
            {"schedule": lambda candidate, source: (_ for _ in ()).throw(RuntimeError("boom"))},
        ),
        (
            "fill_or_no_fill",
            "fill_projection_dependency_not_bound",
            {"fill": lambda preimage, source: (_ for _ in ()).throw(RuntimeError("boom"))},
        ),
    ],
)
def test_dependency_exception_becomes_first_miss_without_denominator_loss(
    adapter: ModuleType, stage: str, reason: str, overrides: dict
) -> None:
    # Since 9059cfa06 a throwing injected dependency is refused as not-bound
    # BEFORE it can throw. Had the lambda been invoked, the recorded reason
    # would be dependency_exception:RuntimeError, so the exact-reason
    # assertion below also proves non-invocation. The dependency_exception
    # taxonomy and its denominator conservation stay pinned by
    # test_hdf_exception_becomes_first_miss_without_denominator_loss.
    result = adapter.run_complete_path_shadow(
        [_source()], enabled=True, dependencies=_dependencies(adapter, **overrides)
    )

    assert result["stage_row_count"] == len(adapter.STAGES) == 11
    assert len({row["stage"] for row in result["stage_ledger"]}) == 11
    assert result["missed_opportunity_ledger"] == [
        {
            **result["missed_opportunity_ledger"][0],
            "first_missing_stage": stage,
            "reason": reason,
        }
    ]


def test_hdf_exception_becomes_first_miss_without_denominator_loss(
    adapter: ModuleType,
) -> None:
    source = _source()
    source["hdf_exit_input"]["points"] = [{"time_us": DECISION_US + MINUTE_US}]

    result = adapter.run_complete_path_shadow(
        [source], enabled=True, dependencies=_dependencies(adapter)
    )

    assert result["stage_row_count"] == len(adapter.STAGES) == 11
    assert result["missed_opportunity_ledger"][0]["first_missing_stage"] == (
        "hdf_exit_or_terminal"
    )
    assert result["missed_opportunity_ledger"][0]["reason"] == (
        "dependency_exception:TypeError"
    )


def test_one_dependency_refusal_cannot_drop_or_duplicate_another_identity(
    adapter: ModuleType,
) -> None:
    # Since 9059cfa06 the only admitted generator is the bound source-embedded
    # one, so a per-identity selective failure can no longer be injected as a
    # raising callable. The same pinned property — one identity's stage
    # refusal cannot drop or duplicate another identity's rows — is exercised
    # by planting the refusal in the "bad" source itself: it carries no
    # synthetic_candidate and must miss at candidate_generation while "good"
    # completes untouched.
    good = _source("good")
    bad = _source("bad")
    del bad["synthetic_candidate"]

    result = adapter.run_complete_path_shadow(
        [good, bad],
        enabled=True,
        dependencies=_dependencies(adapter),
    )

    assert result["source_opportunity_count"] == 2
    assert result["stage_row_count"] == 2 * len(adapter.STAGES) == 22
    keys = [
        (
            tuple(row["composite_identity"][field] for field in adapter.IDENTITY_FIELDS),
            row["stage"],
        )
        for row in result["stage_ledger"]
    ]
    assert len(keys) == len(set(keys)) == 22
    assert len(result["missed_opportunity_ledger"]) == 1
    miss = result["missed_opportunity_ledger"][0]
    assert miss["composite_identity"]["source_opportunity_id"] == "bad"
    assert miss["reason"] == "candidate_generation_candidate_count_not_one:0"
    good_rows = [
        row
        for row in result["stage_ledger"]
        if row["composite_identity"]["source_opportunity_id"] == "good"
    ]
    assert len(good_rows) == 11
    assert all(
        row["disposition"] not in {"REFUSED", "NOT_REACHED_PRIOR_STAGE_MISS"}
        for row in good_rows
    )
