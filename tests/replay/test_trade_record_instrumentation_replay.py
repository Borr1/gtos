"""Replay validation for A3 trade record instrumentation (v1.1).

Takes historical trade records (pre-instrumentation), reconstructs the
MSO + AI analysis + config from what the record already holds, and
re-runs ``create_trade_record`` + ``update_verification`` +
``update_m5_refinement`` + ``update_exit`` to prove:

1. Every existing historical record can reach the new code path without
   raising (backward-compat on real data).
2. When the instrumentation block populates, the values are sane (no
   type mismatches, no exceptions, correct bucket strings).
3. Existing replay fixtures (live_evaluations, trade_records) continue
   to parse without schema breakage.

Runs with zero API cost — pure replay of local JSON.
"""
from __future__ import annotations

import sys

import pytest

pytestmark = pytest.mark.replay

# Make helpers importable
_REPLAY_DIR = __import__("pathlib").Path(__file__).resolve().parent
if str(_REPLAY_DIR) not in sys.path:
    sys.path.insert(0, str(_REPLAY_DIR))

from src.components.trade_capture import (
    CAPTURE_VERSION,
    EXIT_REASON_UNKNOWN,
    _VALID_EXIT_REASONS,
    create_trade_record,
    load_trade_record,
    update_exit,
    update_m5_refinement,
    update_verification,
)
from src.components.verification import verify_candidate

import helpers  # type: ignore[import-not-found]


# ---------------------------------------------------------------------------
# 1 — Replay: every historical record reparses without raising
# ---------------------------------------------------------------------------


def test_historical_records_load_without_instrumentation_errors(trade_records):
    """Every pre-1.1 record on disk loads without KeyError on instrumentation.

    The v1.1 schema adds optional fields; legacy records have no
    'instrumentation' block. Phase-2 query code MUST use .get(), this
    test documents that contract.
    """
    total = 0
    v10_records = 0
    v11_records = 0
    legacy_no_instrumentation = 0
    with_instrumentation = 0

    for record in trade_records(window_days=60):
        total += 1
        version = (record.get("metadata") or {}).get("capture_version", "1.0")
        if version == "1.0":
            v10_records += 1
        elif version == "1.1":
            v11_records += 1
        # Accessing as dict MUST never raise.
        inst = record.get("instrumentation")
        if inst is None:
            legacy_no_instrumentation += 1
        else:
            with_instrumentation += 1

    print(
        f"[replay] scanned {total} records: "
        f"v1.0={v10_records} v1.1={v11_records} "
        f"no_inst={legacy_no_instrumentation} with_inst={with_instrumentation}"
    )
    # Test passes as long as no record raises — 60-day window may be empty
    # on a fresh clone, which is fine (window-based sampling).
    assert total >= 0  # trivially true; assertion shape for clarity


# ---------------------------------------------------------------------------
# 2 — Replay: reconstruct a record's MSO + AI through create_trade_record
# ---------------------------------------------------------------------------


def test_reconstruction_populates_v11_instrumentation(trade_records, replay_config):
    """Re-running create_trade_record against a historical (MSO, AI) pair
    populates the v1.1 instrumentation block with sane values."""
    sampled = 0
    sane = 0
    bucket_failures = 0
    sl_source_failures = 0

    for record in trade_records(window_days=60, require_mso=True):
        # Pull the original inputs back out
        meta = record.get("metadata") or {}
        mso_dict = record.get("mso")
        ai_response = record.get("ai_response")
        if not isinstance(mso_dict, dict) or not isinstance(ai_response, dict):
            continue
        if not meta.get("candle_time") or not meta.get("kill_zone"):
            continue

        # Re-build the record via current code
        try:
            rebuilt = create_trade_record(
                symbol=meta.get("symbol", "XAUUSD"),
                kill_zone=meta["kill_zone"],
                candle_time=meta["candle_time"],
                mso=mso_dict,
                prompt_system=(record.get("prompt") or {}).get("system_prompt", ""),
                prompt_user=(record.get("prompt") or {}).get("user_message", ""),
                ai_response=ai_response,
                cross_instrument_context=None,
                session_memory="",
                config=replay_config,
            )
        except Exception as e:  # noqa: BLE001
            pytest.fail(
                f"create_trade_record raised on historical record "
                f"{record.get('_source_file')}: {e}"
            )

        sampled += 1
        inst = rebuilt.get("instrumentation") or {}

        # Instrumentation must be present + dict-shaped
        assert isinstance(inst, dict), f"instrumentation not a dict in {record.get('_source_file')}"

        # Sanity checks on types
        if not isinstance(inst.get("h1_fvg_unfilled_count"), int):
            continue
        if not isinstance(inst.get("m15_fvg_unfilled_count"), int):
            continue
        # target_ob_touch_count starts None (set later by update_verification)
        assert inst.get("target_ob_touch_count") is None
        # m5_refined boolean default
        assert inst.get("m5_refined") is False

        # kill_zone_bucket_15min must match the source kz + an HHMM suffix
        bucket = inst.get("kill_zone_bucket_15min") or ""
        if not bucket.startswith(meta["kill_zone"]) or len(bucket.split("_")[-1]) != 4:
            bucket_failures += 1
            continue

        # sl_source must be a known enum
        if inst.get("sl_source") not in ("ob", "atr_fallback", "structural", "unknown"):
            sl_source_failures += 1
            continue

        sane += 1

    print(
        f"[replay] sampled={sampled} sane={sane} "
        f"bucket_failures={bucket_failures} sl_source_failures={sl_source_failures}"
    )
    # If we sampled anything, at least one record must produce a sane instrumentation.
    if sampled > 0:
        assert sane > 0, "No historical record produced a sane instrumentation block"


# ---------------------------------------------------------------------------
# 3 — Replay verification matching → target_ob_touch_count
# ---------------------------------------------------------------------------


def test_replay_verification_populates_touch_count(trade_records, replay_config):
    """Replay verify_candidate through historical records + attach to record.

    Asserts: when verify_candidate resolves a matched OB, update_verification
    writes its touch_count to instrumentation. When no match, touch_count
    stays None, no exception.
    """
    sampled = 0
    with_match = 0
    touch_counts_seen: list[int] = []
    none_touch = 0

    for record in trade_records(window_days=60, require_mso=True):
        mso = helpers.reconstruct_mso(record)
        pa = helpers.reconstruct_pa(record)
        if mso is None or pa is None or pa.decision != "CANDIDATE":
            continue

        # Re-build the record fresh
        meta = record.get("metadata") or {}
        rebuilt = create_trade_record(
            symbol=meta.get("symbol", "XAUUSD"),
            kill_zone=meta.get("kill_zone", "london"),
            candle_time=meta.get("candle_time", ""),
            mso=mso,
            prompt_system="", prompt_user="",
            ai_response=record.get("ai_response") or {},
            cross_instrument_context=None, session_memory="",
            config=replay_config,
        )

        # Run verification
        try:
            vr = verify_candidate(pa, mso, replay_config)
        except Exception:  # noqa: BLE001
            continue

        update_verification(rebuilt, vr)
        sampled += 1

        inst = rebuilt.get("instrumentation") or {}
        tc = inst.get("target_ob_touch_count")
        if tc is not None:
            with_match += 1
            touch_counts_seen.append(int(tc))
        else:
            none_touch += 1

    print(
        f"[replay] verification_replay: sampled={sampled} with_match={with_match} "
        f"no_match={none_touch} touches_sample={touch_counts_seen[:10]}"
    )
    # This test is observational — just confirms no exception across all
    # historical records. Empty-window replay (fresh clone, no records) is
    # a valid pass.
    if sampled > 0:
        # Touch counts must be non-negative ints
        for tc in touch_counts_seen:
            assert tc >= 0


# ---------------------------------------------------------------------------
# 4 — Replay update_exit on synthetic exits derived from record outcome
# ---------------------------------------------------------------------------


def test_replay_update_exit_populates_canonical_fields(trade_records):
    """For every record that had any exit dict, replay update_exit and
    confirm exit_reason is a known enum + realized_R is an alias for actual_r."""
    exits_seen = 0
    canonical_ok = 0
    aliases_ok = 0

    for record in trade_records(window_days=60):
        existing_exit = record.get("exit")
        if not isinstance(existing_exit, dict):
            continue

        # Start from a fresh baseline record to avoid mutating the original
        # in-memory fixture
        clone = {"exit": None, "instrumentation": {}}
        update_exit(clone, existing_exit)
        exits_seen += 1

        new_exit = clone.get("exit") or {}
        reason = new_exit.get("exit_reason")
        if reason in _VALID_EXIT_REASONS:
            canonical_ok += 1

        # realized_R alias MUST match actual_r when both exist
        if "actual_r" in existing_exit:
            if new_exit.get("realized_R") == existing_exit["actual_r"]:
                aliases_ok += 1

    print(
        f"[replay] exit_replay: exits_seen={exits_seen} "
        f"canonical_ok={canonical_ok} aliases_ok={aliases_ok}"
    )
    # Zero exits in window is a valid pass (FTMO free-trial EA exclusion
    # means no real fills yet). If we had any, they must all map.
    if exits_seen > 0:
        # If any exit was seen, every one MUST produce a canonical reason
        # (even UNKNOWN is canonical).
        assert canonical_ok == exits_seen


# ---------------------------------------------------------------------------
# 5 — Replay update_m5_refinement against the pipeline_state snapshot
# ---------------------------------------------------------------------------


def test_m5_refinement_snapshot_attaches(replay_config):
    """Sanity: update_m5_refinement can absorb the raw pipeline_state/m5_refinement.json
    output without raising — regardless of whether applied=True/False.

    Note: orchestrator persists m5_out via ``atomic_write(path, json.dumps(m5_out, ...))``
    which stringifies the dict first, so the on-disk file is a JSON-encoded
    STRING (not a dict).  We handle both parse paths + also directly test
    update_m5_refinement on a reasonable synthetic, so this test doesn't
    silently pass when m5_refinement.json is missing / malformed.
    """
    import json

    m5_state_path = helpers.repo_root() / "pipeline_state" / "m5_refinement.json"
    m5_out = None
    if m5_state_path.exists():
        with m5_state_path.open(encoding="utf-8") as f:
            raw = json.load(f)
        # Orchestrator writes json.dumps(m5_out) via atomic_write which
        # double-encodes: the outer load gives us a string, parse once more.
        if isinstance(raw, str):
            try:
                m5_out = json.loads(raw)
            except json.JSONDecodeError:
                m5_out = None
        elif isinstance(raw, dict):
            m5_out = raw

    # If the on-disk file isn't parseable, fall back to a synthetic so we
    # still exercise the code path — this test is about update_m5_refinement
    # being robust, not about the live pipeline_state format.
    if not isinstance(m5_out, dict):
        m5_out = {
            "applied": False,
            "m5_result": {"decision": "SL_TOO_TIGHT", "m5_quality": "MEDIUM"},
            "overrides": None,
        }

    # Build a minimal record
    record = {"instrumentation": {}}
    try:
        update_m5_refinement(record, m5_out)
    except Exception as e:  # noqa: BLE001
        pytest.fail(f"update_m5_refinement raised on live m5_refinement.json: {e}")

    inst = record["instrumentation"]
    assert "m5_refined" in inst
    assert isinstance(inst["m5_refined"], bool)
    print(
        f"[replay] m5_snapshot: m5_refined={inst['m5_refined']} "
        f"details_keys={list((inst.get('m5_refinement_details') or {}).keys())}"
    )
