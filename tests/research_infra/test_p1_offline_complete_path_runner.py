from __future__ import annotations

import json
import gzip
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from src.research_infra import p1_offline_complete_path_runner as runner


UTC = timezone.utc


def _identity(
    *,
    candidate_id: str = "source-candidate",
    symbol: str = "EURUSD",
    side: str = "SHORT",
    decision: str = "2026-04-01T00:00:00+00:00",
) -> runner.CompositeIdentity:
    return runner.CompositeIdentity(candidate_id, symbol, side, decision)


def _intent(
    *,
    side: str = "LONG",
    entry: float = 100.0,
    stop: float | None = None,
    target: float | None = None,
    decision: str = "2026-04-01T00:00:00+00:00",
) -> dict:
    stop = (99.0 if side == "LONG" else 101.0) if stop is None else stop
    target = (120.0 if side == "LONG" else 80.0) if target is None else target
    return runner.limit_intent(
        _identity(decision=decision),
        repaired_side=side,
        entry=entry,
        stop=stop,
        target=target,
    )


def _tick(time: datetime, bid: float, ask: float) -> runner.TickQuote:
    return runner.TickQuote(time.isoformat(), bid, ask)


def _m1(
    decision: datetime,
    *,
    side: str,
    entry: float = 100.0,
    omit: set[int] | None = None,
) -> list[runner.M1Bar]:
    omit = omit or set()
    rows = []
    for minute in range(1, 121):
        if minute in omit:
            continue
        stamp = decision + timedelta(minutes=minute)
        if side == "LONG":
            values = (101.0, 102.0, 100.5, 101.5)
        else:
            values = (99.0, 99.5, 98.0, 98.5)
        rows.append(runner.M1Bar(stamp.isoformat(), *values))
    return rows


def _classify_ticks(intent: dict, ticks: list[runner.TickQuote]):
    decision = datetime.fromisoformat(intent["decision_time_utc"])
    expiry = datetime.fromisoformat(intent["expiry_time_utc"])
    return runner.classify_fill(
        intent,
        authority="FULL_TICK",
        ticks=ticks,
        authority_start_utc=(decision - timedelta(minutes=1)).isoformat(),
        authority_end_utc=expiry.isoformat(),
    )


def _completion_contract(window: str) -> dict:
    """Mirror the hash-bound sparse-M1 completion contract the runner emits.

    `_m1_authority_complete` accepts sparse authenticated M1 only under a
    literal completion contract bound to the window's real path/lane manifest
    hashes (runner.py:596-616); a binding without one is a source gap.
    """
    return {
        "schema": "gtos.p1-hash-bound-sparse-m1-completion.v1",
        "window": window,
        "path_manifest_sha256": runner.PATH_MANIFEST_BINDINGS[window][1],
        "lane_manifest_sha256": runner.LANE_MANIFEST_BINDINGS[window][1],
        "sparse_no_print_minutes_valid": True,
        "civil_minute_continuity_required": False,
    }


def _m1_binding(
    intent: dict, *, digest: str = "a" * 64, window: str = "april"
) -> dict:
    return {
        "sha256": digest,
        "expected_sha256": digest,
        "authenticated": True,
        "completion_contract": _completion_contract(window),
        "start_utc": intent["decision_time_utc"],
        "end_utc": intent["expiry_time_utc"],
    }


def test_run_is_default_off_before_any_anchor_or_marker(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def forbidden(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("anchor must not run")

    monkeypatch.setattr(runner, "_git", forbidden)
    with pytest.raises(runner.P1RunnerRefusal, match="default_off"):
        runner.run_once(tested_source_commit="0" * 40)
    assert called is False


def test_composite_identity_collision_fails_closed() -> None:
    row = {
        "candidate_id": "same",
        "symbol": "EURUSD",
        "side": "LONG",
        "decision_time_utc": "2026-01-02T00:00:00+00:00",
    }
    with pytest.raises(runner.P1RunnerRefusal, match="duplicate_composite"):
        runner.require_unique_identities([row, dict(row)])


def test_limit_intent_freezes_order_type_expiry_geometry_and_no_cancel() -> None:
    intent = _intent()
    assert intent["effective_order_type"] == runner.ORDER_TYPE
    assert intent["observation_interval"] == "(decision_time_utc,expiry_time_utc]"
    assert intent["cancellation_policy"] == "NONE_CAPTURE_ONLY"
    assert intent["cancel_time_utc"] is None
    assert intent["cancel_reason"] is None
    assert intent["market_fallback"] is False
    assert datetime.fromisoformat(intent["expiry_time_utc"]) - datetime.fromisoformat(
        intent["decision_time_utc"]
    ) == timedelta(minutes=120)
    assert intent["entry_price"] - intent["stop_loss"] == 1.0
    assert intent["take_profit"] - intent["entry_price"] == 20.0


def test_plus2_geometry_drift_is_rejected() -> None:
    with pytest.raises(runner.P1RunnerRefusal, match="minus1_plus20"):
        _intent(target=102.0)


def test_order_type_and_cancellation_drift_fail_closed() -> None:
    intent = _intent()
    drifted = dict(intent, effective_order_type="MARKET")
    with pytest.raises(runner.P1RunnerRefusal, match="order_type_drift"):
        runner.classify_fill(drifted, authority="PATH_START_GAP")
    drifted = dict(intent, cancel_reason="imagined")
    with pytest.raises(runner.P1RunnerRefusal, match="cancellation_policy_drift"):
        runner.classify_fill(drifted, authority="PATH_START_GAP")


def test_decision_quote_excluded_and_expiry_quote_included_long_ask() -> None:
    intent = _intent(side="LONG")
    decision = datetime.fromisoformat(intent["decision_time_utc"])
    expiry = datetime.fromisoformat(intent["expiry_time_utc"])
    result = _classify_ticks(
        intent,
        [
            _tick(decision, 99.0, 99.5),
            _tick(expiry, 99.0, 100.0),
        ],
    )
    assert result.status == "FILLED"
    assert result.fill_time_utc == expiry.isoformat()
    assert result.fill_price == 100.0


def test_long_uses_ask_and_opposite_bid_touch_does_not_fill() -> None:
    intent = _intent(side="LONG")
    expiry = datetime.fromisoformat(intent["expiry_time_utc"])
    result = _classify_ticks(intent, [_tick(expiry, 99.0, 100.1)])
    assert result.status == "NO_FILL"
    assert result.reason == "EXPIRED_UNFILLED"


def test_short_uses_bid_and_opposite_ask_touch_does_not_fill() -> None:
    intent = _intent(side="SHORT")
    expiry = datetime.fromisoformat(intent["expiry_time_utc"])
    no_fill = _classify_ticks(intent, [_tick(expiry, 99.9, 100.1)])
    assert no_fill.status == "NO_FILL"
    filled = _classify_ticks(intent, [_tick(expiry, 100.0, 100.1)])
    assert filled.status == "FILLED"
    assert filled.fill_price == 100.0


def test_full_tick_no_touch_is_expired_unfilled() -> None:
    intent = _intent(side="LONG")
    decision = datetime.fromisoformat(intent["decision_time_utc"])
    result = _classify_ticks(
        intent,
        [_tick(decision + timedelta(minutes=1), 100.1, 100.2), _tick(decision + timedelta(minutes=120), 100.2, 100.3)],
    )
    assert (result.status, result.reason) == ("NO_FILL", "EXPIRED_UNFILLED")


def test_five_april_out_of_bounds_tick_pointers_are_m1_only() -> None:
    archive_end = "2026-04-15T23:59:59+00:00"
    decisions = [f"2026-04-{day:02d}T00:00:00+00:00" for day in range(16, 21)]
    authorities = [
        runner.resolve_fill_authority(
            _identity(candidate_id=f"c-{index}", decision=decision),
            tick_pointer_present=True,
            archive_start_utc="2026-04-01T00:00:00+00:00",
            archive_end_utc=archive_end,
        )
        for index, decision in enumerate(decisions)
    ]
    assert authorities == ["M1_ONLY"] * 5


def test_m1_no_touch_can_prove_no_fill() -> None:
    intent = _intent(side="LONG")
    decision = datetime.fromisoformat(intent["decision_time_utc"])
    result = runner.classify_fill(
        intent,
        authority="M1_ONLY",
        m1_parts=[_m1(decision, side="LONG")],
        m1_authority_bindings=[_m1_binding(intent)],
    )
    assert (result.status, result.reason) == ("NO_FILL", "EXPIRED_UNFILLED")


def test_m1_touch_is_not_evaluable_not_fill() -> None:
    intent = _intent(side="LONG")
    decision = datetime.fromisoformat(intent["decision_time_utc"])
    bars = _m1(decision, side="LONG")
    bars[9] = replace(bars[9], low=100.0)
    result = runner.classify_fill(
        intent,
        authority="M1_ONLY",
        m1_parts=[bars],
        m1_authority_bindings=[_m1_binding(intent)],
    )
    assert result.status == "NOT_EVALUABLE"
    assert result.reason == "NOT_EVALUABLE_M1_TOUCH_WITHOUT_EXECUTABLE_TICK"
    assert result.fill_price is None


@pytest.mark.parametrize("decision", sorted(runner.UK100_GAPS))
def test_three_uk100_gaps_are_unconditional_not_evaluable(decision: str) -> None:
    identity = _identity(symbol="UK100", decision=decision)
    authority = runner.resolve_fill_authority(
        identity,
        tick_pointer_present=False,
        archive_start_utc=None,
        archive_end_utc=None,
    )
    assert authority == "PATH_START_GAP"
    intent = runner.limit_intent(identity, repaired_side="LONG", entry=100, stop=99, target=120)
    result = runner.classify_fill(intent, authority=authority)
    assert (result.status, result.reason) == ("NOT_EVALUABLE", "NOT_EVALUABLE_PATH_START_GAP")


def test_sparse_m1_is_valid_only_under_literal_bound_closure() -> None:
    intent = _intent(side="LONG")
    decision = datetime.fromisoformat(intent["decision_time_utc"])
    omitted = set(range(20, 31))
    bars = _m1(decision, side="LONG", omit=omitted)
    without = runner.classify_fill(intent, authority="M1_ONLY", m1_parts=[bars])
    assert without.reason == "NOT_EVALUABLE_M1_SOURCE_OR_SESSION_GAP"
    with_closure = runner.classify_fill(
        intent,
        authority="M1_ONLY",
        m1_parts=[bars],
        m1_authority_bindings=[_m1_binding(intent)],
    )
    assert with_closure.status == "NO_FILL"


def test_cross_month_stitching_is_sorted_and_deterministic() -> None:
    decision = datetime(2026, 4, 30, 23, 30, tzinfo=UTC)
    intent = _intent(side="SHORT", decision=decision.isoformat())
    rows = _m1(decision, side="SHORT")
    april = [row for row in rows if row.time_utc.startswith("2026-04")]
    may = [row for row in rows if row.time_utc.startswith("2026-05")]
    stitched = runner.stitch_m1([may, april])
    assert len(stitched) == 120
    assert stitched[0].time_utc.startswith("2026-04")
    assert stitched[-1].time_utc.startswith("2026-05")
    split = datetime(2026, 5, 1, 0, 0, tzinfo=UTC)
    first = _m1_binding(intent, digest="a" * 64, window="april")
    first["end_utc"] = split.isoformat()
    second = _m1_binding(intent, digest="b" * 64, window="may")
    second["start_utc"] = split.isoformat()
    result = runner.classify_fill(
        intent,
        authority="M1_ONLY",
        m1_parts=[may, april],
        m1_authority_bindings=[second, first],
    )
    assert result.status == "NO_FILL"


def test_duplicate_cross_month_bar_refuses() -> None:
    decision = datetime(2026, 4, 30, 23, 30, tzinfo=UTC)
    rows = _m1(decision, side="LONG")
    with pytest.raises(runner.P1RunnerRefusal, match="duplicate_or_order"):
        runner.stitch_m1([rows, [rows[-1]]])


def _filled(intent: dict) -> runner.FillClassification:
    decision = datetime.fromisoformat(intent["decision_time_utc"])
    return runner.FillClassification(
        "FILLED",
        "FIRST_EXECUTABLE_QUOTE_TOUCH",
        "FULL_TICK",
        (decision + timedelta(minutes=1)).isoformat(),
        intent["entry_price"],
        intent["expiry_time_utc"],
    )


def test_exit_consumes_only_points_strictly_after_fill() -> None:
    intent = _intent(side="LONG")
    fill = _filled(intent)
    fill_time = datetime.fromisoformat(fill.fill_time_utc)
    horizon = datetime.fromisoformat(intent["expiry_time_utc"])
    # A tick at exactly fill_time would read -1.0R (hard stop) if consumed; the
    # terminal quote sits at the horizon because a path ending earlier only
    # yields horizon_terminal_mark, which the runner refuses as truncated
    # evidence (runner.py:800-801).  A complete path exits as time_box at the
    # deadline point (exit_overlay.py:415-432).
    result = runner.evaluate_tick_exit(
        intent,
        fill,
        [
            _tick(fill_time, 99.0, 99.1),
            _tick(horizon, 101.0, 101.1),
        ],
    )
    assert result.reason == "time_box"
    assert result.gross_r == 1.0


def test_terminal_quote_side_is_bid_for_long_and_ask_for_short() -> None:
    # Terminal quotes sit at the horizon: the runner refuses a horizon terminal
    # mark evidenced by a path that ends before it (runner.py:800-801).
    long_intent = _intent(side="LONG")
    long_fill = _filled(long_intent)
    long_time = datetime.fromisoformat(long_intent["expiry_time_utc"])
    long_result = runner.evaluate_tick_exit(long_intent, long_fill, [_tick(long_time, 101.0, 120.0)])
    assert long_result.gross_r == 1.0
    short_intent = _intent(side="SHORT")
    short_fill = _filled(short_intent)
    short_time = datetime.fromisoformat(short_intent["expiry_time_utc"])
    short_result = runner.evaluate_tick_exit(short_intent, short_fill, [_tick(short_time, 80.0, 99.0)])
    assert short_result.gross_r == 1.0


def test_m1_same_bar_stop_target_collision_selects_lower_net() -> None:
    intent = _intent(side="LONG")
    fill = _filled(intent)
    stamp = datetime.fromisoformat(fill.fill_time_utc) + timedelta(minutes=1)
    result = runner.evaluate_m1_exit_bar(
        intent,
        fill,
        runner.M1Bar(stamp.isoformat(), 100.0, 120.0, 99.0, 110.0),
    )
    assert result.reason == "hard_stop"
    assert result.gross_r == -1.0
    assert result.ambiguity is True


def test_counts_reconcile_without_denominator_shrinkage() -> None:
    assert sum(runner.EXPECTED_AUTHORITY.values()) == runner.EXPECTED_FAMILY == 11_305
    assert runner.EXPECTED_NON_FAMILY == 62_694
    assert runner.EXPECTED_FAMILY + runner.EXPECTED_NON_FAMILY == runner.EXPECTED_TOTAL
    assert runner.EXPECTED_TOTAL * len(runner.STAGES) == runner.EXPECTED_STAGE_ROWS == 813_989
    rows = list(runner.expected_non_family_stage_rows(_identity(), "april"))
    assert len(rows) == 11
    assert {row["disposition"] for row in rows} == {"EXPECTED_NON_FAMILY_NO_P1_MUTATION"}


def test_prereg_hashes_roles_and_all_predecode_values_are_null() -> None:
    payload = json.loads(runner.PREREGISTRATION_PATH.read_text(encoding="utf-8"))
    assert payload["packet_binding"]["manifest_sha256"] == runner.PACKET_MANIFEST_SHA256
    assert payload["packet_binding"]["payload_root_sha256"] == runner.PACKET_PAYLOAD_ROOT_SHA256
    assert payload["authority_accounting"] == {**runner.EXPECTED_AUTHORITY, "TOTAL": 11_305}
    assert all(value is None for value in payload["predecode_null_fields"].values())
    assert payload["account_roles"]["operator_profile"]["sole_economic_role"] is True
    assert payload["account_roles"]["redacted_account"]["mechanical"] is True
    assert payload["account_roles"]["redacted_account"]["economic"] is False
    assert payload["account_roles"]["redacted_account"]["promotion_or_veto"] is False
    assert payload["exit_contract"]["hidden_plus2_cap"] is None


def test_classifier_spec_hash_is_self_consistent() -> None:
    payload = json.loads(runner.PREREGISTRATION_PATH.read_text(encoding="utf-8"))
    assert payload["classifier_spec_sha256"] == runner.canonical_sha256(
        payload["classifier_state_machine"]
    )


def test_git_subprocess_accepts_only_closed_read_only_shapes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    def forbidden(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("subprocess must not be reached")

    monkeypatch.setattr(runner.subprocess, "run", forbidden)
    with pytest.raises(runner.P1RunnerRefusal, match="git_command_shape_refused"):
        runner._git("status", "--short")
    with pytest.raises(runner.P1RunnerRefusal, match="git_command_shape_refused"):
        runner._git("show", "--format=%P", "HEAD")
    with pytest.raises(runner.P1RunnerRefusal, match="git_command_shape_refused"):
        runner._git("rev-parse", "--show-toplevel")
    assert called is False


def test_deterministic_gzip_bytes(tmp_path) -> None:
    rows = [{"z": 1, "a": "same"}, {"value": None}]
    outputs = []
    for name in ("one.gz", "two.gz"):
        path = tmp_path / name
        with runner.DeterministicJsonlGzipWriter(path) as writer:
            for row in rows:
                writer.write(row)
        outputs.append(path.read_bytes())
    assert outputs[0] == outputs[1]


def _write_synthetic_gzip(path: runner.Path, rows: list[dict]) -> tuple[str, int]:
    with runner.DeterministicJsonlGzipWriter(path) as writer:
        for row in rows:
            writer.write(row)
    return runner.file_sha256(path), path.stat().st_size


def _configure_synthetic_transaction(
    monkeypatch: pytest.MonkeyPatch, tmp_path, name: str, *, crash: bool = False
) -> tuple[runner.Path, str]:
    tested = "1" * 40
    output = tmp_path / name
    decision = datetime(2026, 1, 2, 1, 0, tzinfo=UTC)
    common = {
        "symbol": "EURUSD",
        "side": "SHORT",
        "direction": "SHORT",
        "decision_time_utc": decision.isoformat(),
    }
    pool_rows = [
        {
            **common,
            "candidate_id": "non-family",
            "origin_family": "another_family",
        },
        {
            **common,
            "candidate_id": "family",
            "origin_family": runner.ORIGIN_FAMILY,
            "entry_price": 100.0,
            "stop_loss": 101.0,
            "take_profit_1": 99.0,
        },
    ]
    observations = [
        {
            "time_utc": (decision + timedelta(minutes=minute)).isoformat(),
            "open": 101.0,
            "high": 102.0,
            "low": 100.5,
            "close": 101.5,
        }
        for minute in range(1, 121)
    ]
    sidecars = [
        {
            "schema": "gtos-session-ck-ordered-path-sidecar-v1",
            **common,
            "candidate_id": candidate_id,
            "horizon_end_utc": (decision + timedelta(minutes=120)).isoformat(),
            "source_path": "m1.csv",
            "source_sha256": "c" * 64,
            "ordered_tick_source": None,
            "ordered_path_observations": observations,
        }
        for candidate_id in ("non-family", "family")
    ]
    # Real bound files under tmp_path: the runner reads pool/sidecar bytes via
    # _read_bound_bytes (symlink guard + digest + size + TOCTOU checks), so the
    # synthetic containers must exist as regular files with true digests.  The
    # shim only redirects the two synthetic names to their tmp_path location
    # (with root=tmp_path); every verification stays live via the real reader.
    pool_path = tmp_path / f"{name}-synthetic-pool.jsonl.gz"
    side_path = tmp_path / f"{name}-synthetic-sidecar.jsonl.gz"
    pool_sha, pool_size = _write_synthetic_gzip(pool_path, pool_rows)
    side_sha, side_size = _write_synthetic_gzip(side_path, sidecars)
    monkeypatch.setattr(runner, "OUTPUT_PARENT", output)
    monkeypatch.setattr(runner, "EXPECTED_TOTAL", 2)
    monkeypatch.setattr(runner, "EXPECTED_FAMILY", 1)
    monkeypatch.setattr(runner, "EXPECTED_NON_FAMILY", 1)
    monkeypatch.setattr(runner, "EXPECTED_STAGE_ROWS", 22)
    monkeypatch.setattr(runner, "EXPECTED_WINDOWS", {"january": 2})
    monkeypatch.setattr(runner, "EXPECTED_FAMILY_WINDOWS", {"january": 1})
    monkeypatch.setattr(
        runner,
        "EXPECTED_AUTHORITY",
        {"FULL_TICK": 0, "M1_ONLY": 1, "PATH_START_GAP": 0},
    )
    monkeypatch.setattr(
        runner,
        "POOL_BINDINGS",
        (("january", pool_path.name, pool_sha, pool_size),),
    )
    monkeypatch.setattr(
        runner,
        "SIDECAR_BINDINGS",
        {"january": (side_path.name, side_sha, side_size)},
    )
    monkeypatch.setattr(runner, "_require_run_anchors", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(runner, "_require_file", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        runner.shutil,
        "disk_usage",
        lambda _path: SimpleNamespace(free=20 * 1024**3),
    )
    real_read_bound_bytes = runner._read_bound_bytes

    def synthetic_read_bound_bytes(path, *, root, digest, size=None):
        candidate = tmp_path / runner.Path(path).name
        if candidate in {pool_path, side_path}:
            return real_read_bound_bytes(candidate, root=tmp_path, digest=digest, size=size)
        return real_read_bound_bytes(path, root=root, digest=digest, size=size)

    monkeypatch.setattr(runner, "_read_bound_bytes", synthetic_read_bound_bytes)
    if crash:
        def crash_iter(_payload, *, label):
            raise runner.P1RunnerRefusal("synthetic_crash_after_marker")

        monkeypatch.setattr(runner, "_iter_full_jsonl", crash_iter)
    lane_m1_record = {
        "symbol": "EURUSD",
        "mapped_symbol": "EURUSD",
        "timeframe": "M1",
        "lane_relpath": "m1.csv",
        "sha256": "c" * 64,
        "row_count": 120,
        "first_utc": (decision + timedelta(minutes=1)).isoformat(),
        "last_utc": (decision + timedelta(minutes=120)).isoformat(),
        "time_column_basis": "true_utc",
    }
    monkeypatch.setattr(
        runner,
        "_window_authority",
        lambda _window: {
            "source_inventory": {
                "EURUSD": {
                    "m1": {"path": "m1.csv", "sha256": "c" * 64, "rows": 120},
                    "tick": None,
                }
            },
            "lane_m1_sources": {"EURUSD": lane_m1_record},
            "lane_tick_sources": {},
            "path_manifest_sha256": runner.PATH_MANIFEST_BINDINGS["january"][1],
            "lane_manifest_sha256": runner.LANE_MANIFEST_BINDINGS["january"][1],
        },
    )

    def synthetic_m1_binding(
        _record, _lane_record, *, window, path_manifest_sha256, lane_manifest_sha256, cache
    ):
        return {
            "sha256": "c" * 64,
            "expected_sha256": "c" * 64,
            "authenticated": True,
            "completion_contract": {
                "schema": "gtos.p1-hash-bound-sparse-m1-completion.v1",
                "window": window,
                "path_manifest_sha256": path_manifest_sha256,
                "lane_manifest_sha256": lane_manifest_sha256,
                "sparse_no_print_minutes_valid": True,
                "civil_minute_continuity_required": False,
            },
            "start_utc": decision.isoformat(),
            "end_utc": (decision + timedelta(minutes=120)).isoformat(),
        }

    monkeypatch.setattr(runner, "_m1_binding", synthetic_m1_binding)
    return output, tested


def _gzip_rows(path: runner.Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def test_run_once_streams_exact_five_outputs_and_atomic_install(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    output, tested = _configure_synthetic_transaction(monkeypatch, tmp_path, "result")
    result = runner.run_once(tested_source_commit=tested, enabled=True)
    assert result["output_parent"] == output.as_posix()
    assert {path.name for path in output.iterdir()} == {
        "stage_ledger.jsonl.gz",
        "identity_results.jsonl.gz",
        "missed_opportunities.jsonl.gz",
        "P1_FILL_CLASSIFICATION.jsonl.gz",
        "RUN_MANIFEST.json",
    }
    assert not output.with_name(f".{output.name}.staging-{tested[:12]}").exists()
    assert len(_gzip_rows(output / "stage_ledger.jsonl.gz")) == 22
    identity_rows = _gzip_rows(output / "identity_results.jsonl.gz")
    assert len(identity_rows) == 2
    assert len(_gzip_rows(output / "P1_FILL_CLASSIFICATION.jsonl.gz")) == 1
    assert _gzip_rows(output / "missed_opportunities.jsonl.gz") == []
    assert identity_rows[0]["ftmo_economics"] is None
    # The runner forbids any "economics" key under redacted_account outright
    # (redacted_account_economics_key_forbidden, runner.py:2549-2550, :2584-2585);
    # absence is the guaranteed contract, not a null value.
    assert all("economics" not in row["redacted_account"] for row in identity_rows)
    manifest = json.loads((output / "RUN_MANIFEST.json").read_text())
    assert manifest["complete_denominator"]["stage_rows"] == 22
    assert manifest["partial_economic_summary"] is None
    marker = json.loads(
        output.with_name(output.name + ".RUN_STARTED").read_text(encoding="utf-8")
    )
    assert marker["tested_source_commit"] == tested
    assert marker["canonical_evidence_commit"] == runner.CANONICAL_EVIDENCE_COMMIT
    assert marker["packet_manifest_sha256"] == runner.PACKET_MANIFEST_SHA256
    assert marker["packet_payload_root_sha256"] == runner.PACKET_PAYLOAD_ROOT_SHA256
    assert marker["preregistration_sha256"] == runner.file_sha256(
        runner.PREREGISTRATION_PATH
    )
    assert marker["output_parent"] == output.as_posix()


def test_synthetic_transaction_descriptors_are_deterministic(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    first, tested = _configure_synthetic_transaction(monkeypatch, tmp_path, "first")
    runner.run_once(tested_source_commit=tested, enabled=True)
    first_manifest = json.loads((first / "RUN_MANIFEST.json").read_text())
    second, tested = _configure_synthetic_transaction(monkeypatch, tmp_path, "second")
    runner.run_once(tested_source_commit=tested, enabled=True)
    second_manifest = json.loads((second / "RUN_MANIFEST.json").read_text())
    assert first_manifest["files"] == second_manifest["files"]
    assert first_manifest["output_payload_root_sha256"] == second_manifest[
        "output_payload_root_sha256"
    ]


def test_crash_after_marker_preserves_marker_and_staging(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    output, tested = _configure_synthetic_transaction(
        monkeypatch, tmp_path, "crash", crash=True
    )
    with pytest.raises(runner.P1RunnerRefusal, match="synthetic_crash"):
        runner.run_once(tested_source_commit=tested, enabled=True)
    assert output.with_name(output.name + ".RUN_STARTED").is_file()
    assert output.with_name(f".{output.name}.staging-{tested[:12]}").is_dir()
    assert not output.exists()


def test_preexisting_marker_refuses_before_staging(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    output, tested = _configure_synthetic_transaction(monkeypatch, tmp_path, "marked")
    marker = output.with_name(output.name + ".RUN_STARTED")
    marker.write_text("preserved\n", encoding="utf-8")
    with pytest.raises(runner.P1RunnerRefusal, match="marker_already_exists"):
        runner.run_once(tested_source_commit=tested, enabled=True)
    assert marker.read_text(encoding="utf-8") == "preserved\n"
    assert not output.with_name(f".{output.name}.staging-{tested[:12]}").exists()
    assert not output.exists()


def test_preexisting_staging_refuses_and_preserves_marker_and_staging(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    output, tested = _configure_synthetic_transaction(monkeypatch, tmp_path, "staged")
    staging = output.with_name(f".{output.name}.staging-{tested[:12]}")
    staging.mkdir()
    (staging / "prior").write_text("preserved\n", encoding="utf-8")
    with pytest.raises(runner.P1RunnerRefusal, match="staging_target_preexists"):
        runner.run_once(tested_source_commit=tested, enabled=True)
    assert output.with_name(output.name + ".RUN_STARTED").is_file()
    assert (staging / "prior").read_text(encoding="utf-8") == "preserved\n"
    assert not output.exists()


def test_preexisting_output_parent_refuses_in_preflight(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    output = tmp_path / "already-there"
    output.mkdir()
    monkeypatch.setattr(runner, "OUTPUT_PARENT", output)
    # `preflight` checks SOURCE_ROOT (`:1754`) BEFORE it reaches the output-parent refusal
    # this test is about, and SOURCE_ROOT is an absolute path into
    # `worktrees/wave16-rematerialization-20260731/.hermes/...` — a worktree that was removed,
    # and a `.hermes` tree that CLAUDE.md §4 records was moved off this machine's worktrees
    # entirely. So the refusal that fired was `path_component_missing`, from the setup rather
    # than from the behaviour under test. Point it at a directory that exists; the test's own
    # subject is unchanged.
    source_root = tmp_path / "source-root"
    source_root.mkdir()
    monkeypatch.setattr(runner, "SOURCE_ROOT", source_root)
    monkeypatch.setattr(
        runner,
        "_load_preregistration",
        lambda: {"repo_file_bindings": [], "account_roles": {}},
    )

    def fake_git(*args):
        if args[:3] == ("show", "-s", "--format=%P"):
            return runner.BASE_SOURCE_COMMIT
        return "\n".join(sorted(runner.CANONICAL_EVIDENCE_PATHS))

    monkeypatch.setattr(runner, "_git", fake_git)
    denominator = {
        "total": runner.EXPECTED_TOTAL,
        "window_counts": runner.EXPECTED_WINDOWS,
        "family_window_counts": runner.EXPECTED_FAMILY_WINDOWS,
        "family": runner.EXPECTED_FAMILY,
        "non_family": runner.EXPECTED_NON_FAMILY,
        "stage_rows": runner.EXPECTED_STAGE_ROWS,
        "authority_counts": runner.EXPECTED_AUTHORITY,
        "false_april_tick_references": [],
    }
    monkeypatch.setattr(runner, "_source_control_proof", lambda: (denominator, []))
    monkeypatch.setattr(runner, "_dry_run_digest", lambda _rows: ("d" * 64, 0))
    monkeypatch.setattr(
        runner, "_verify_static_boundary", lambda _paths: {"status": "PASS"}
    )
    with pytest.raises(runner.P1RunnerRefusal, match="output_parent_must_be_absent"):
        runner.preflight(verify_packet_structure=False)


def test_no_forbidden_import_order_send_or_protocol_cell_mapping() -> None:
    source = runner.Path(runner.__file__).read_text(encoding="utf-8")
    result = runner._verify_static_boundary((runner.Path(runner.__file__),))
    assert result["status"] == "PASS"
    assert "ExitOverlaySpec.from_protocol_cell" not in source
