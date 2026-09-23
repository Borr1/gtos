from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.research_infra import p1_upstream_packet_verifier as verifier
from src.research_infra import p1_upstream_reconstruction as subject


UTC = timezone.utc


def _bar(minute: int, *, symbol: str = "XAUUSD", price: float = 100.0) -> subject.Bar:
    timestamp = datetime(2026, 1, 2, 0, minute, tzinfo=UTC)
    return subject.Bar(
        time=timestamp,
        time_utc=timestamp.isoformat(),
        symbol=symbol,
        open=price,
        high=price + 2.0,
        low=price - 1.0,
        close=price + 1.0,
        volume=10.0,
    )


def _identity(
    candidate_id: str,
    *,
    symbol: str = "XAUUSD",
    side: str = "LONG",
    minute: int = 15,
) -> subject.IdentityRow:
    decision = datetime(2026, 1, 2, 0, minute, tzinfo=UTC)
    return subject.IdentityRow(
        window="january",
        candidate_id=candidate_id,
        symbol=symbol,
        side=side,
        decision_time_utc=decision.isoformat(),
        decision_time=decision,
        kill_zone="off_configured_session",
        origin_family="current_breaker_re_entry",
        framework="breaker_re_entry",
        route_family="current_breaker_re_entry",
    )


def test_true_utc_parser_refuses_naive_and_nonzero_offsets() -> None:
    assert subject.parse_true_utc("2026-03-09T00:00:00Z", field="t") == datetime(
        2026, 3, 9, tzinfo=UTC
    )
    with pytest.raises(subject.ReconstructionError, match="naive_timestamp_refused"):
        subject.parse_true_utc("2026-03-09T00:00:00", field="t")
    with pytest.raises(subject.ReconstructionError, match="non_utc_offset_refused"):
        subject.parse_true_utc("2026-03-09T03:00:00+03:00", field="t")


def test_clock_contract_refuses_eu_or_fixed_offset_dst_story() -> None:
    valid = {
        "time_column_basis": "true_utc",
        "broker_clock_rule": "new_york_plus_7",
        "conversion_function": "src.utils.broker_clock.broker_epoch_to_utc",
        "broker_clock_anchor_offset_hours": 7.0,
        "broker_clock_anchor_zone": "America/New_York",
    }
    subject.validate_clock_contract(valid, label="valid")
    for mutation in (
        {"broker_clock_rule": "eet_eest"},
        {"broker_clock_anchor_zone": "Europe/Helsinki"},
        {"time_column_basis": "broker_wall"},
        {"broker_clock_anchor_offset_hours": 3.0},
    ):
        invalid = {**valid, **mutation}
        with pytest.raises(subject.ReconstructionError, match="timebase_invalid"):
            subject.validate_clock_contract(invalid, label="bad_dst")


def test_required_hash_refuses_missing_changed_and_external_tampering(tmp_path: Path) -> None:
    path = tmp_path / "payload.bin"
    with pytest.raises(subject.ReconstructionError, match="required_file_missing"):
        subject.require_file_binding(path, "0" * 64)
    path.write_bytes(b"generator-v1")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    subject.require_file_binding(path, digest, len(b"generator-v1"))
    path.write_bytes(b"generator-v2")
    with pytest.raises(subject.ReconstructionError, match="sha256_mismatch"):
        subject.require_file_binding(path, digest)
    with pytest.raises(verifier.VerificationError, match="sha256_mismatch"):
        verifier.require_file(path, digest)


def test_m15_loader_binds_schema_hash_timebase_and_coverage(tmp_path: Path) -> None:
    relative = "sources/bars/test/XAUUSD_M15.csv"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_text(
        "time,open,high,low,close,volume\n"
        "2026-01-02T00:00:00+00:00,100,102,99,101,10\n"
        "2026-01-02T00:15:00+00:00,101,103,100,102,11\n",
        encoding="utf-8",
    )
    entry = {
        "symbol": "XAUUSD",
        "lane_relpath": relative,
        "sha256": subject.sha256_file(path),
        "row_count": 2,
        "first_utc": "2026-01-02T00:00:00+00:00",
        "last_utc": "2026-01-02T00:15:00+00:00",
        "time_column_basis": "true_utc",
    }
    loaded = subject.load_m15_series(tmp_path, {"XAUUSD": entry})
    assert [bar.time_utc for bar in loaded["XAUUSD"]] == [
        "2026-01-02T00:00:00+00:00",
        "2026-01-02T00:15:00+00:00",
    ]
    with pytest.raises(subject.ReconstructionError, match="mixed_or_unverified_timebase"):
        subject.load_m15_series(
            tmp_path, {"XAUUSD": {**entry, "time_column_basis": "broker_wall"}}
        )


def test_m15_loader_refuses_naive_time_and_missing_bar_hash(tmp_path: Path) -> None:
    relative = "sources/bars/test/XAUUSD_M15.csv"
    path = tmp_path / relative
    path.parent.mkdir(parents=True)
    path.write_text(
        "time,open,high,low,close,volume\n"
        "2026-01-02T00:00:00,100,102,99,101,10\n",
        encoding="utf-8",
    )
    entry = {
        "symbol": "XAUUSD",
        "lane_relpath": relative,
        "sha256": subject.sha256_file(path),
        "row_count": 1,
        "first_utc": "2026-01-02T00:00:00+00:00",
        "last_utc": "2026-01-02T00:00:00+00:00",
        "time_column_basis": "true_utc",
    }
    with pytest.raises(subject.ReconstructionError, match="naive_timestamp_refused"):
        subject.load_m15_series(tmp_path, {"XAUUSD": entry})
    with pytest.raises(subject.ReconstructionError, match="required_file_sha256_mismatch"):
        subject.load_m15_series(tmp_path, {"XAUUSD": {**entry, "sha256": "0" * 64}})


def test_h1_aggregation_is_exact_and_utc_bucketed() -> None:
    rows = [_bar(0, price=100), _bar(15, price=103), _bar(45, price=102)]
    aggregated = subject.aggregate_h1_from_m15(rows, symbol="XAUUSD")
    assert len(aggregated) == 1
    assert aggregated[0].time_utc == "2026-01-02T00:00:00+00:00"
    assert aggregated[0].open == 100
    assert aggregated[0].high == 105
    assert aggregated[0].low == 99
    assert aggregated[0].close == 103
    assert aggregated[0].volume == 30


def test_closed_slice_excludes_forming_and_postdecision_bars() -> None:
    rows = [_bar(0), _bar(15), _bar(30)]
    decision = datetime(2026, 1, 2, 0, 15, tzinfo=UTC)
    assert subject.closed_slice_indices(rows, decision=decision, minutes=15, lookback=672) == (0, 1)
    with pytest.raises(subject.ReconstructionError, match="missing_closed_bar_slice"):
        subject.closed_slice_indices(
            rows,
            decision=datetime(2026, 1, 2, 0, 14, 57, tzinfo=UTC),
            minutes=15,
            lookback=672,
        )
    with pytest.raises(subject.ReconstructionError, match="naive_decision"):
        subject.closed_slice_indices(
            rows,
            decision=datetime(2026, 1, 2, 0, 15),
            minutes=15,
            lookback=672,
        )


def test_two_second_tolerance_never_admits_a_postdecision_close() -> None:
    decision = datetime(2026, 1, 2, 0, 15, tzinfo=UTC)
    for delta in (timedelta(seconds=1), timedelta(seconds=2)):
        with pytest.raises(subject.ReconstructionError, match="missing_closed_bar_slice"):
            subject.closed_slice_indices_from_closes(
                [decision + delta], decision=decision, lookback=672
            )


def test_warmup_requires_51_m15_and_168_h1() -> None:
    subject.require_warmup(m15_count=51, h1_count=168, label="known_answer")
    with pytest.raises(subject.ReconstructionError, match="insufficient_warmup"):
        subject.require_warmup(m15_count=50, h1_count=168, label="missing_m15")
    with pytest.raises(subject.ReconstructionError, match="insufficient_warmup"):
        subject.require_warmup(m15_count=672, h1_count=167, label="missing_h1")


def test_symbol_alias_is_refused_instead_of_silently_normalized() -> None:
    subject.require_exact_symbol_domain([_identity("a", symbol="US30_cash")], {"US30_cash"})
    with pytest.raises(subject.ReconstructionError, match="symbol_alias_or_unbound"):
        subject.require_exact_symbol_domain([_identity("a", symbol="US30.cash")], {"US30_cash"})


def test_reused_candidate_id_is_allowed_only_across_unique_composite_keys() -> None:
    rows = [
        _identity("same", symbol="XAUUSD", side="LONG", minute=15),
        _identity("same", symbol="XAUUSD", side="LONG", minute=30),
    ]
    summary = subject.validate_composite_identities(rows)
    assert summary == {
        "rows": 2,
        "unique_composite_identities": 2,
        "candidate_ids_reused": 1,
        "rows_under_reused_candidate_ids": 2,
    }
    with pytest.raises(subject.ReconstructionError, match="duplicate_composite_identity"):
        subject.validate_composite_identities([rows[0], rows[0]])


def test_generator_identity_multiplicity_must_be_exactly_one() -> None:
    marker = object()
    assert subject.require_single_generator_match([marker], label="one") is marker
    with pytest.raises(subject.ReconstructionError, match="matches=0"):
        subject.require_single_generator_match([], label="none")
    with pytest.raises(subject.ReconstructionError, match="matches=2"):
        subject.require_single_generator_match([marker, marker], label="duplicate")


def test_static_import_boundary_refuses_live_import_and_order_send(tmp_path: Path) -> None:
    safe = tmp_path / "safe.py"
    safe.write_text("import json\nvalue = json.dumps({})\n", encoding="utf-8")
    assert subject.verify_static_import_boundary([safe])["forbidden_findings"] == 0
    forbidden_import = tmp_path / "forbidden_import.py"
    forbidden_import.write_text("import MetaTrader5\n", encoding="utf-8")
    with pytest.raises(subject.ReconstructionError, match="forbidden_import"):
        subject.verify_static_import_boundary([forbidden_import])
    forbidden_call = tmp_path / "forbidden_call.py"
    forbidden_call.write_text("def f(client):\n    return client.order_send({})\n", encoding="utf-8")
    with pytest.raises(subject.ReconstructionError, match="forbidden_order_send"):
        subject.verify_static_import_boundary([forbidden_call])

    attacks = {
        "dynamic_import.py": "__import__('Meta' + 'Trader5')\n",
        "exec_import.py": "exec(\"__import__('MetaTrader5')\")\n",
        "eval_import.py": "eval(\"__import__('socket')\")\n",
        "compile_import.py": "code=compile('import socket','<x>','exec')\nexec(code)\n",
        "importlib.py": "import importlib\nimportlib.import_module('MetaTrader5')\n",
        "importlib_getattr.py": "import importlib\ngetattr(importlib, 'import_' + 'module')('socket')\n",
        "builtins_getattr.py": "import builtins\ngetattr(builtins, '__im' + 'port__')('socket')\n",
        "getattr_send.py": "def f(client):\n    return getattr(client, 'order_' + 'send')({})\n",
        "network.py": "import socket\nsocket.create_connection(('localhost', 1))\n",
        "subprocess.py": "import subprocess\nsubprocess.run(['uname'])\n",
        "subprocess_alias.py": "import subprocess as sp\nsp.run(['git', 'show'])\n",
        "subprocess_from.py": "from subprocess import run\nrun(['git', 'show'])\n",
        "os_system.py": "import os\nos.system('id')\n",
        "os_popen.py": "import os\nos.popen('id')\n",
        "os_exec.py": "import os\nos.execv('/bin/sh', ['sh'])\n",
        "os_spawn.py": "import os\nos.spawnv(0, '/bin/sh', ['sh'])\n",
        "os_dynamic.py": "import os\ngetattr(os, 'sys' + 'tem')('id')\n",
        "pty_spawn.py": "import pty\npty.spawn(['/bin/sh'])\n",
        "from_live.py": "from src.components import execution\n",
        "relative_import.py": "from . import execution\n",
        "outcome.py": "def f(row):\n    return row['pro' + 'fit']\n",
        "outcome_get.py": "def f(row):\n    return row.get('p' + 'nl')\n",
    }
    for name, source in attacks.items():
        path = tmp_path / name
        path.write_text(source, encoding="utf-8")
        with pytest.raises(subject.ReconstructionError):
            subject.verify_static_import_boundary([path])


def test_git_static_allowlist_requires_exact_commit_colon_path_fstring() -> None:
    def command(source: str) -> ast.AST:
        return ast.parse(source, mode="eval").body

    assert subject._static_git_command_allowed(
        command("['git', 'show', f'{commit}:{relative_path}']")
    )
    assert not subject._static_git_command_allowed(
        command("['git', 'show', f'--output=/tmp/escape:{commit}']")
    )
    assert not subject._static_git_command_allowed(
        command("['git', 'show', f'--ext-diff:{commit}']")
    )
    assert not subject._static_git_command_allowed(
        command("['git', 'show', '-s', '--format=%P', '--output=/tmp/escape']")
    )
    assert not subject._static_git_command_allowed(
        command("['git', 'show', '-s', '--format=%P', str('--output=/tmp/escape')]")
    )


def test_builder_write_targets_are_separately_containment_audited(tmp_path: Path) -> None:
    packet_root = tmp_path / "packet-parent"
    packet_root.mkdir()
    subject.require_builder_write_target(packet_root / "stage" / "payload", root=packet_root)

    with pytest.raises(subject.ReconstructionError, match="builder_write_outside_root"):
        subject.require_builder_write_target(tmp_path / "escape", root=packet_root)
    with pytest.raises(subject.ReconstructionError, match="builder_write_root_itself_refused"):
        subject.require_builder_write_target(packet_root, root=packet_root)

    outside = tmp_path / "outside"
    outside.mkdir()
    (packet_root / "linked").symlink_to(outside, target_is_directory=True)
    with pytest.raises(subject.ReconstructionError, match="builder_write_symlink_ancestor_refused"):
        subject.require_builder_write_target(packet_root / "linked" / "payload", root=packet_root)


def test_builder_refuses_to_create_an_unbound_packet_parent(tmp_path: Path) -> None:
    missing = tmp_path / "not-created"

    with pytest.raises(
        subject.ReconstructionError,
        match="packet_parent_must_be_existing_regular_directory",
    ):
        subject.build_packet(
            source_root=tmp_path / "unused-source",
            packet_parent=missing,
            source_commit="0" * 40,
        )
    assert not missing.exists()


def test_source_control_json_projection_never_decodes_noncontrol_values() -> None:
    text = json.dumps(
        {
            "candidate_id": "c",
            "symbol": "XAUUSD",
            "side": "LONG",
            "direction": "LONG",
            "decision_time_utc": "2026-01-02T00:15:00+00:00",
            "kill_zone": "ny",
            "origin_family": "current_breaker_re_entry",
            "framework": "breaker_re_entry",
            "route_family": "current_breaker_re_entry",
            "uncommissioned_result_field": {"trap": [1, 2, 3]},
        }
    )
    row = subject.project_source_control_json(text)
    assert set(row) == set(subject.SOURCE_CONTROL_FIELDS)
    assert "uncommissioned_result_field" not in row

    duplicate = text[:-1] + ',"candidate_id":"duplicate"}'
    with pytest.raises(subject.ReconstructionError, match="duplicate_json_key"):
        subject.project_source_control_json(duplicate)


def test_deterministic_gzip_is_byte_identical(tmp_path: Path) -> None:
    first = tmp_path / "first.jsonl.gz"
    second = tmp_path / "second.jsonl.gz"
    for path in (first, second):
        with subject.DeterministicJsonlGzipWriter(path) as writer:
            writer.write({"b": 2, "a": 1})
    assert first.read_bytes() == second.read_bytes()


def test_path_scope_refuses_forbidden_windows_but_allows_raw_warmup() -> None:
    with pytest.raises(subject.ReconstructionError, match="forbidden_window_or_live_path"):
        subject.assert_path_scope(Path("receipts/march_2026/result.json"))
    source_root = Path("/bound/source")
    allowed = source_root / "sources/bars/march_2026/XAUUSD_M15.csv"
    subject.assert_path_scope(
        allowed,
        raw_warmup_source=True,
        source_root=source_root,
        allowed_raw_paths={allowed},
    )
    for attack in (
        source_root / "sources/bars/march_2026/result.json",
        source_root / "sources/bars/MARCH-2026/result.json",
        source_root / "sources/bars/march2026/result.json",
        source_root / "sources/bars/march_2026/../result.json",
    ):
        with pytest.raises(subject.ReconstructionError):
            subject.assert_path_scope(
                attack,
                raw_warmup_source=True,
                source_root=source_root,
                allowed_raw_paths={allowed},
            )
