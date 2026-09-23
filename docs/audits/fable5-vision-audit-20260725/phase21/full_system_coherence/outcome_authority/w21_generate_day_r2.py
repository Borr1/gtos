#!/usr/bin/env python3
"""Wave-21 lane day generator, r2 — execution-layer repair of w21_generate_feb_day.py.

Why this exists (2026-08-10): the February validation generation ran with the BASE
config only. Base config/agent_config.yaml carries no ``broker_profile``, so
``account_for(server=None, namespace=None)`` raises CostTruthError inside the
pretrade cost machinery: the spread-model branch source-gaps on the 20 non-tick
symbols, and side-aware swap + broker-true commission fail on all 24. The packet
REFUSES, and the producer's legacy default then stamps the flat 0.12 ``cost_r``
(the convenience-default wave 20 flagged). January's development runs carried
complete four-component costs, so its (overwritten) generator must have supplied
the broker profile. This r2 makes the profile handling explicit and testable:

  MODE 'merge-ftmo'  : deep-merge config/profiles/ftmo.yaml over base config
  MODE 'broker-only' : copy only the profile's ``broker_profile`` block
  MODE 'none'        : byte-for-byte the original (defective) behavior — control

Validation gate: regenerating 2026-01-05 (january_2026, development split) must
reproduce the original January authority_root_sha256 exactly
(caac9f4a052315faf62f0e2d2c3cb575c353c04257f9965d8f465b7001277509). A root match
proves the reconstruction equals the configuration January actually ran.

Everything else is unchanged from w21_generate_feb_day.py (same campaign flags,
same truth-mode key, same lane resolution, same sink discipline).
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

REPO = Path("/Users/borr/GTOSActive/worktrees/wave21-full-system-coherence-20260809")
REGISTRY = Path(
    "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/"
    "evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/"
    "LANE_INPUT_REGISTRY.json"
)
sys.path.insert(0, str(REPO))

from src.research_infra import lane_rematerialization as lane
from src.research_infra import v4_timewarp_simulated_live_research_loop as timewarp
from src.research_infra.replay_compact_event_sink import ReplayCompactEventSink
from src.research_infra.train_engine import guard


def _deep_merge(base: dict, overlay: dict) -> dict:
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


_PROFILE_FILES = {
    "merge-ftmo": ("config/profiles/ftmo.yaml", "merge"),
    "broker-only": ("config/profiles/ftmo.yaml", "broker"),
    "merge-310": ("config/profiles/operator_profile.yaml", "merge"),
    "broker-310": ("config/profiles/operator_profile.yaml", "broker"),
}


def _config_for(mode: str) -> dict:
    config = copy.deepcopy(timewarp.load_config(REPO / "config/agent_config.yaml"))
    if mode != "none":
        import yaml

        if mode not in _PROFILE_FILES:
            raise SystemExit(f"unknown mode: {mode}")
        rel, how = _PROFILE_FILES[mode]
        profile = yaml.safe_load((REPO / rel).read_text(encoding="utf-8")) or {}
        if not isinstance(profile, dict):
            raise SystemExit("profile payload not a mapping")
        if how == "merge":
            config = _deep_merge(config, copy.deepcopy(profile))
        else:
            if not isinstance(profile.get("broker_profile"), dict):
                raise SystemExit("profile has no broker_profile block")
            config["broker_profile"] = copy.deepcopy(profile["broker_profile"])
    config.setdefault("gtos_vnext_runtime", {})[
        "wave21_full_flow_truth_mode_enabled"
    ] = True
    return config


def main() -> None:
    if len(sys.argv) != 5:
        raise SystemExit(
            "usage: w21_generate_day_r2.py WINDOW_ID YYYY-MM-DD OUTPUT_ROOT MODE"
        )
    window_id, day, output_root_text, mode = sys.argv[1:5]
    output_root = Path(output_root_text).resolve()
    day_root = output_root / day
    compact_root = day_root / "compact_events"
    if day_root.exists() or day_root.is_symlink():
        raise SystemExit(f"output day must be new: {day_root}")
    day_root.mkdir(parents=True, exist_ok=False)

    inputs = lane.LaneInputRegistry(
        REGISTRY,
        allow_registered_march_metadata=True,
    ).resolve(
        window_id=window_id,
        purpose=guard.PURPOSE_LANE_ITERATION,
    )
    if day not in inputs.window.days:
        raise SystemExit(f"day outside {window_id} authority: {day}")

    config = _config_for(mode)
    campaign = timewarp.CampaignConfig(
        name=f"wave21_market_top_choice_validation_{day.replace('-', '')}",
        phase="wave21_market_top_choice_validation",
        days=(day,),
        pending_expiry_minutes=120,
        use_repaired_pending_expiry=True,
        partial_be_runner=True,
        max_candidates_per_symbol_window=0,
        run_smoke_subset=False,
        materialize_packet_sidecars=False,
        materialize_semantic_diagnostics=False,
    )

    with inputs.runtime_bindings():
        resolver = lane._resolver_for(inputs)
        sources = resolver.build_sources_for_days(
            (day,),
            symbols=tuple(timewarp.GTOS_24_SYMBOL_SURFACE),
            source_authority_days=(day,),
        )
        sources = lane._with_loader_component_authority(inputs, sources)
        if set(sources) != set(timewarp.GTOS_24_SYMBOL_SURFACE):
            raise RuntimeError("symbol denominator incomplete")
        for symbol, frames in sources.items():
            missing = {"D1", "H4", "H1", "M15", "M1"} - set(frames)
            if missing:
                raise RuntimeError(f"source missing: {symbol}: {sorted(missing)}")

        sink = ReplayCompactEventSink(root=compact_root)
        try:
            with (
                lane._RAW_CAMPAIGN_WITNESS_LOCK,
                lane._installed_raw_campaign_successor_witness(sources) as used_streams,
            ):
                result = timewarp.run_campaign(
                    campaign=campaign,
                    config=config,
                    sources=sources,
                    compact_event_sink=sink,
                    prepared_day_pack=None,
                )
        except BaseException:
            sink.abort()
            raise

    expected_streams = len(timewarp.GTOS_24_SYMBOL_SURFACE) * len(
        lane.RAW_CAMPAIGN_DECISION_TIMEFRAMES
    )
    if len(used_streams) != expected_streams:
        raise RuntimeError(
            f"decision source stream coverage mismatch: {len(used_streams)} != {expected_streams}"
        )
    authority = result["compact_event_sink_authority"]
    summary = {
        "day": day,
        "window_id": window_id,
        "generator": "w21_generate_day_r2",
        "profile_mode": mode,
        "compact_root": str(compact_root),
        "authority_root_sha256": authority["authority_root_sha256"],
        "row_counts": authority["row_counts"],
        "source_manifest_root_sha256": inputs.source_manifest[
            "manifest_root_sha256"
        ],
        "used_decision_streams": len(used_streams),
    }
    (day_root / "run_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("W21_DAY_R2=" + json.dumps(summary, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
