"""Configuration for the forward-shadow runner.

Two layers, deliberately separate:

  * **Shadow config** — a small standalone YAML of the lane's own
    (`config/wave21_forward_shadow.yaml` by default).  Cadence, namespace,
    staleness bounds, symbol surface.  NOT agent_config; the live book never
    reads it and it never reads the live book's runtime state.
  * **Decision config** — the frozen rule's merge-310 runtime config, built
    in memory exactly as the committed r2b generator builds it: deep-merge
    ``config/profiles/operator_profile.yaml`` over
    ``config/agent_config.yaml`` (profile wins), then set
    ``gtos_vnext_runtime.wave21_full_flow_truth_mode_enabled = true`` in the
    in-memory copy.  Nothing is written back.  The input shas are fingerprinted
    into every heartbeat so drift from the rule's bindings
    (``runtime_config_sha256`` / ``overlay_sha256``) is visible, not silent.
"""

from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml

# The frozen rule's generation-config bindings
# (MARKET_TOP_CHOICE_VALIDATION_RULE_V1_1.json: bindings + amendment).
RULE_RUNTIME_CONFIG_SHA256 = (
    "dfbdb7e2f7ecd76ae76616164d3fcd838b91864a6222bb6878cc4709246d5d20"
)
RULE_OVERLAY_SHA256 = (
    "ae9312e6c5c8e6b05f8e5eb5f9490166c44a1a3279b4eff5df10c3da2921e2b8"
)

DEFAULT_SHADOW_CONFIG_RELPATH = "config/wave21_forward_shadow.yaml"


class ShadowConfigError(ValueError):
    pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _deep_merge(base: dict, overlay: dict) -> dict:
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


@dataclass
class ShadowRunnerConfig:
    repo_root: Path
    namespace_dir: Path
    model_artifact_path: Path
    settle_delay_seconds: float = 30.0
    cycle_grid_minutes: int = 15
    max_tick_staleness_seconds: float = 900.0
    m1_fetch_bars: int = 420
    heartbeat_echo: bool = True
    symbols: tuple[str, ...] = ()
    base_config_relpath: str = "config/agent_config.yaml"
    profile_relpath: str = "config/profiles/operator_profile.yaml"
    mt5_terminal_path: str | None = None
    # Prequential daily refit (owner directive 2026-08-12): ON by default.
    daily_refit_enabled: bool = True
    frozen_corpus_path: Path | None = None
    models_dir: Path | None = None
    extra: dict[str, Any] = field(default_factory=dict)


def load_shadow_config(path: str | Path, *, repo_root: str | Path | None = None) -> ShadowRunnerConfig:
    path = Path(path).resolve()
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, Mapping):
        raise ShadowConfigError(f"shadow config is not a mapping: {path}")
    root = Path(repo_root).resolve() if repo_root else Path(__file__).resolve().parents[3]
    shadow = payload.get("forward_shadow")
    if not isinstance(shadow, Mapping):
        raise ShadowConfigError("shadow config missing 'forward_shadow' block")
    namespace_dir = Path(str(shadow.get("namespace_dir") or "shadow_logs/funnel_shadow"))
    if not namespace_dir.is_absolute():
        namespace_dir = root / namespace_dir
    model_path = Path(str(shadow.get("model_artifact") or ""))
    if not str(model_path):
        raise ShadowConfigError("shadow config missing forward_shadow.model_artifact")
    if not model_path.is_absolute():
        model_path = root / model_path
    symbols = tuple(str(s) for s in (shadow.get("symbols") or ()))
    frozen_corpus = shadow.get("frozen_corpus")
    frozen_corpus_path = None
    if frozen_corpus:
        frozen_corpus_path = Path(str(frozen_corpus))
        if not frozen_corpus_path.is_absolute():
            frozen_corpus_path = root / frozen_corpus_path
    models_dir = shadow.get("models_dir")
    models_dir_path = None
    if models_dir:
        models_dir_path = Path(str(models_dir))
        if not models_dir_path.is_absolute():
            models_dir_path = root / models_dir_path
    return ShadowRunnerConfig(
        repo_root=root,
        namespace_dir=namespace_dir,
        model_artifact_path=model_path,
        settle_delay_seconds=float(shadow.get("settle_delay_seconds", 30.0)),
        cycle_grid_minutes=int(shadow.get("cycle_grid_minutes", 15)),
        max_tick_staleness_seconds=float(shadow.get("max_tick_staleness_seconds", 900.0)),
        m1_fetch_bars=int(shadow.get("m1_fetch_bars", 420)),
        heartbeat_echo=bool(shadow.get("heartbeat_echo", True)),
        symbols=symbols,
        base_config_relpath=str(
            shadow.get("base_config_relpath") or "config/agent_config.yaml"
        ),
        profile_relpath=str(
            shadow.get("profile_relpath")
            or "config/profiles/operator_profile.yaml"
        ),
        mt5_terminal_path=(
            str(shadow["mt5_terminal_path"]) if shadow.get("mt5_terminal_path") else None
        ),
        daily_refit_enabled=bool(shadow.get("daily_refit_enabled", True)),
        frozen_corpus_path=frozen_corpus_path,
        models_dir=models_dir_path,
        extra=dict(shadow.get("extra") or {}),
    )


def build_decision_config(
    runner_config: ShadowRunnerConfig,
    *,
    load_config: Any,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Merge-310 in memory, exactly as `w21_generate_day_r2b._config_for`.

    ``load_config`` is the timewarp's loader (injected to keep this module
    import-light for unit tests).  Returns ``(config, fingerprints)``.
    """

    base_path = runner_config.repo_root / runner_config.base_config_relpath
    profile_path = runner_config.repo_root / runner_config.profile_relpath
    config = copy.deepcopy(load_config(base_path))
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    if not isinstance(profile, dict):
        raise ShadowConfigError("profile payload not a mapping")
    config = _deep_merge(config, copy.deepcopy(profile))
    config.setdefault("gtos_vnext_runtime", {})[
        "wave21_full_flow_truth_mode_enabled"
    ] = True
    fingerprints = {
        "base_config_sha256": _sha256_file(base_path),
        "profile_sha256": _sha256_file(profile_path),
        "rule_runtime_config_sha256": RULE_RUNTIME_CONFIG_SHA256,
        "rule_overlay_sha256": RULE_OVERLAY_SHA256,
    }
    fingerprints["base_matches_rule_binding"] = str(
        fingerprints["base_config_sha256"] == RULE_RUNTIME_CONFIG_SHA256
    )
    fingerprints["profile_matches_rule_binding"] = str(
        fingerprints["profile_sha256"] == RULE_OVERLAY_SHA256
    )
    broker_profile = config.get("broker_profile")
    if not isinstance(broker_profile, Mapping) or not broker_profile.get("server"):
        raise ShadowConfigError(
            "merged decision config carries no broker_profile.server — the "
            "February run-1 NOT_EVALUABLE failure mode; refusing to start"
        )
    return config, fingerprints
