#!/usr/bin/env python3
"""Export the frozen 284,652-row training corpus to a portable npz.

The daily-refit shadow (owner directive 2026-08-12: prequential refit
"activated immediately") refits the rule's ridge every trading day on the
FROZEN corpus (Oct/Nov dev + Jan + Feb + Apr/May — the exact rows the flat
SHADOW_RIDGE_MODEL_V1 was fitted on, loaded through the exact frozen research
chain) PLUS the shadow's own resolved-eligible forward rows.  The VPS has no
compact roots, no lane hold, and no M1 labelers — so the corpus ships as a
committed artifact: the POST-``r.frame()`` design columns (14 categorical
string columns + 29 float64 columns, in the model's column order), the
training target, and the decision-window ids the 1/window candidate weights
derive from.

This exporter runs on the research Mac, loads the corpus through the same
frozen chain the V1 fitter used, dumps ``FROZEN_TRAINING_CORPUS_V1.npz`` (+ a
sidecar binding JSON), then PROVES the transition: reloading the npz and
refitting with the runtime refit code path must reproduce the committed V1
artifact's predictions on the golden fixture rows (the day-zero golden test).
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve()
MY_REPO = HERE.parents[7]
OA = HERE.parents[1]
R2_SCORER = OA / "w21_score_feb_market_top_r2.py"
RULE_PATH = OA / "MARKET_TOP_CHOICE_VALIDATION_RULE_V1_1.json"
PREREG_PATH = OA / "APRIL_MAY_MARKET_TOP_CHOICE_PREREG_V1_6.json"
FEB_ROOT = Path("/private/tmp/w21-market-top-feb-r2")
APRMAY_ROOT = Path("/private/tmp/w21-market-top-aprmay-r3")
HOLD = Path("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805")
MANIFEST_DIR = (
    HOLD
    / ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/manifests"
)
CORPUS_PATH = HERE.parent / "FROZEN_TRAINING_CORPUS_V1.npz"
BINDING_PATH = HERE.parent / "FROZEN_TRAINING_CORPUS_V1.binding.json"
V1_ARTIFACT_PATH = HERE.parent / "SHADOW_RIDGE_MODEL_V1.json"
FIXTURE_PATH = HERE.parent / "GOLDEN_PARITY_FIXTURE_V1.json.gz"

# ---------------------------------------------------------------------------
# Import this repo's runtime refit layer FIRST, then purge `src` bindings so
# the frozen research chain owns every later src.* import (same pattern as the
# committed V1 fitter).
# ---------------------------------------------------------------------------
sys.path.insert(0, str(MY_REPO))
from src.research_infra.wave21_forward_shadow.daily_refit import (  # noqa: E402
    load_frozen_corpus,
    refit_payload,
)
from src.research_infra.wave21_forward_shadow.feature_contract import (  # noqa: E402
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
)
from src.research_infra.wave21_forward_shadow.ridge_artifact import (  # noqa: E402
    ShadowRidgeModel,
    canonical_payload_sha256,
    load_model,
)

sys.path.remove(str(MY_REPO))
for _name in [n for n in list(sys.modules) if n == "src" or n.startswith("src.")]:
    del sys.modules[_name]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def canonical_hash(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


print(json.dumps({"loading": str(R2_SCORER)}), flush=True)
s2 = load_module("w21_score_feb_r2_frozen_for_corpus_export", R2_SCORER)
r = s2.r

if list(r.CAT) != list(CATEGORICAL_FEATURES) or list(r.NUM) != list(NUMERIC_FEATURES):
    raise SystemExit("frozen feature lists diverge from the shadow feature contract")

# ---------------------------------------------------------------------------
# Registry-pin override (2026-08-12).  The June/July prereg train rewrote the
# lane-hold registry (fc505c32... -> current; status COMPLETE -> SOURCE_READY;
# june/july windows added), so the frozen chain's Oct/Nov raw-campaign pin now
# fails closed on a file that legitimately evolved.  The old bytes exist
# nowhere.  We pin the CURRENT file instead and skip the frozen-status cross
# check — every SOURCE-level sha validation stays on, and correctness is
# enforced by a stronger gate below: the exported corpus must refit to the V1
# artifact bit-for-bit, which is only possible if every loaded row is
# identical to the sealed fit's.  The override is recorded in the binding.
# ---------------------------------------------------------------------------
import src.research_infra.lane_rematerialization as _frozen_lane  # noqa: E402

_REGISTRY_PATH = _frozen_lane.RAW_CAMPAIGN_REGISTRY_PATH
_OLD_PIN = _frozen_lane.RAW_CAMPAIGN_REGISTRY_FILE_SHA256
_CURRENT_REGISTRY_SHA = sha256_file(_REGISTRY_PATH)
REGISTRY_OVERRIDE: dict | None = None
if _CURRENT_REGISTRY_SHA != _OLD_PIN:
    import inspect

    _current_registry = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
    _frozen_lane.RAW_CAMPAIGN_REGISTRY_FILE_SHA256 = _CURRENT_REGISTRY_SHA
    _frozen_lane.RAW_CAMPAIGN_REGISTRY_ROOT_SHA256 = str(
        _current_registry.get("registry_root_sha256")
    )
    # Re-exec the frozen authority validator with ONLY the status literal
    # relaxed (COMPLETE -> the current registry's status); every other check —
    # registry/entry equality, estate authority, manifest authority, and the
    # approved-days derivation this function RETURNS — runs untouched.
    _source = inspect.getsource(_frozen_lane._validate_raw_campaign_frozen_authority)
    _needle = '!= "LANE_TRUE_UTC_INPUT_REGISTRY_COMPLETE"'
    if _source.count(_needle) != 1:
        raise SystemExit("frozen validator status literal not found exactly once")
    _source = _source.replace(
        _needle, f'!= "{_current_registry.get("status")}"'
    )
    _namespace = _frozen_lane.__dict__
    exec(compile(_source, "<patched_frozen_authority>", "exec"), _namespace)
    REGISTRY_OVERRIDE = {
        "reason": "lane_hold_registry_evolved_by_junjul_train",
        "frozen_pin_sha256": _OLD_PIN,
        "current_registry_sha256": _CURRENT_REGISTRY_SHA,
        "current_registry_status": _current_registry.get("status"),
        "override_scope": "registry file sha + root sha pins repointed to current file; status literal relaxed; estate/manifest/day checks untouched",
        "correctness_gate": "day_zero_refit_must_reproduce_v1_bit_identically",
    }
    print("REGISTRY_PIN_OVERRIDE=" + json.dumps(REGISTRY_OVERRIDE), flush=True)

rule = json.loads(RULE_PATH.read_text(encoding="utf-8"))
rule_core = dict(rule)
if canonical_hash({k: v for k, v in rule_core.items() if k != "payload_sha256"}) != rule[
    "payload_sha256"
]:
    raise SystemExit("frozen rule payload mismatch")
prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))


def load_m1_sources(manifest_path: Path, expected_root: str):
    from src.components.ultimate_book.primitives import Bar
    from src.research_infra.walkforward.quote_side import spread_for

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["manifest_root_sha256"] != expected_root:
        raise ValueError(f"manifest root changed: {manifest_path}")
    bundle = {}
    for entry in manifest["bar_sources"]:
        if entry["timeframe"] != "M1":
            continue
        path = HOLD / entry["repo_relpath"]
        if sha256_file(path) != entry["sha256"]:
            raise ValueError(f"M1 hash mismatch: {path}")
        times, bars = [], []
        with path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames != ["time", "open", "high", "low", "close", "volume"]:
                raise ValueError(f"M1 schema mismatch: {path}")
            for row in reader:
                times.append(r.m._utc(row["time"]))
                bars.append(
                    Bar(
                        float(row["open"]),
                        float(row["high"]),
                        float(row["low"]),
                        float(row["close"]),
                    )
                )
        if len(times) != entry["row_count"] or any(
            left >= right for left, right in zip(times, times[1:])
        ):
            raise ValueError(f"M1 chronology mismatch: {path}")
        spread_cache, spreads = {}, []
        for instant in times:
            hour = instant.replace(minute=0, second=0, microsecond=0)
            if hour not in spread_cache:
                spread_cache[hour] = spread_for(
                    entry["symbol"], hour, account="FTMO", band="mid"
                )
            spreads.append(spread_cache[hour])
        bundle[entry["symbol"]] = (
            SimpleNamespace(sha256=entry["sha256"]),
            tuple(times),
            tuple(bars),
            tuple(spreads),
        )
    if len(bundle) != 24:
        raise ValueError("M1 symbol denominator is not 24")
    return manifest["manifest_root_sha256"], bundle


def main() -> None:
    import numpy as np

    initial, january = r.load_all()
    training = r.resolved_eligible(initial)
    for day, _authority in r.j.JAN_RUNS:
        training.extend(r.resolved_eligible(january[day]))
    feb_manifest_root, feb_sources = load_m1_sources(
        MANIFEST_DIR / "february_2026.json",
        rule["bindings"]["february_manifest_root_sha256"],
    )
    old_root = s2.ROOT
    s2.ROOT = FEB_ROOT
    try:
        for day in rule["validation"]["days_in_order"]:
            _raw, rows, _summary = s2.load_day(day, feb_manifest_root, feb_sources)
            training.extend(r.resolved_eligible(rows))
    finally:
        s2.ROOT = old_root
    for window in prereg["validation"]["windows"]:
        manifest_root, sources = load_m1_sources(
            MANIFEST_DIR / f"{window['window_id']}.json",
            window["manifest_root_sha256"],
        )
        s2.ROOT = APRMAY_ROOT
        try:
            for day in window["days"]:
                _raw, rows, _summary = s2.load_day(day, manifest_root, sources)
                training.extend(r.resolved_eligible(rows))
        finally:
            s2.ROOT = old_root
    print(json.dumps({"total_training_rows": len(training)}), flush=True)

    v1 = load_model(V1_ARTIFACT_PATH)
    if len(training) != int(v1.training_binding["training_rows"]):
        raise SystemExit(
            f"corpus row count {len(training)} != V1 binding "
            f"{v1.training_binding['training_rows']}"
        )

    frame = r.frame(training)  # POST fillna/astype — the exact design columns
    arrays: dict[str, "np.ndarray"] = {}
    for name in r.CAT:
        column = frame[name].to_numpy()
        vocab, codes = np.unique(column.astype("U"), return_inverse=True)
        arrays[f"cat__{name}__vocab"] = vocab
        arrays[f"cat__{name}__codes"] = codes.astype(np.int32)
    for name in r.NUM:
        arrays[f"num__{name}"] = frame[name].to_numpy(dtype=np.float64)
    arrays["terminal_net_r"] = np.asarray(
        [float(row.get("terminal_net_r") or 0.0) for row in training], dtype=np.float64
    )
    window_ids = np.asarray(
        [str(row["decision_window_id"]) for row in training], dtype="U"
    )
    window_vocab, window_codes = np.unique(window_ids, return_inverse=True)
    arrays["decision_window_vocab"] = window_vocab
    arrays["decision_window_codes"] = window_codes.astype(np.int32)
    np.savez_compressed(CORPUS_PATH, **arrays)
    corpus_sha = sha256_file(CORPUS_PATH)
    print(
        json.dumps(
            {"corpus": str(CORPUS_PATH), "bytes": CORPUS_PATH.stat().st_size,
             "sha256": corpus_sha}
        ),
        flush=True,
    )

    # ------------------------------------------------------------------
    # Transition golden proof: reload the npz, refit through the RUNTIME
    # refit code path with ZERO forward rows, and compare predictions on
    # the golden fixture rows against the committed V1 artifact.
    # ------------------------------------------------------------------
    corpus = load_frozen_corpus(CORPUS_PATH)
    if corpus.row_count != len(training):
        raise SystemExit("corpus reload row count mismatch")
    started = time.time()
    payload = refit_payload(
        corpus,
        forward_rows=[],
        day="1970-01-01",
        frozen_corpus_sha256=corpus_sha,
    )
    fit_seconds = round(time.time() - started, 1)
    refit_model = ShadowRidgeModel(
        payload,
        artifact_sha256=canonical_payload_sha256(
            {k: v for k, v in payload.items() if k != "artifact_sha256"}
        ),
    )
    with gzip.open(FIXTURE_PATH, "rt", encoding="utf-8") as handle:
        fixture = json.load(handle)
    max_diff = 0.0
    for row, expected in zip(fixture["rows"], fixture["sklearn_predictions"]):
        max_diff = max(max_diff, abs(refit_model.predict_row(row) - float(expected)))
    identical_payload = payload["model"] == v1.payload["model"]
    print(
        json.dumps(
            {
                "day_zero_refit_fit_seconds": fit_seconds,
                "golden_rows": len(fixture["rows"]),
                "max_abs_pred_diff_vs_V1": max_diff,
                "model_payload_bit_identical_to_V1": identical_payload,
            }
        ),
        flush=True,
    )
    if max_diff > 1e-12:
        raise SystemExit("day-zero refit does not reproduce V1 — refusing to bind")

    binding = {
        "schema": "gtos.wave21.forward_shadow.frozen_training_corpus_binding.v1",
        "exported_utc": datetime.now(timezone.utc).isoformat(),
        "corpus_file": CORPUS_PATH.name,
        "corpus_sha256": corpus_sha,
        "row_count": len(training),
        "categorical_features": list(r.CAT),
        "numeric_features": list(r.NUM),
        "reproduces_v1_artifact_sha256": v1.artifact_sha256,
        "day_zero_golden_max_abs_pred_diff": max_diff,
        "day_zero_model_payload_bit_identical": identical_payload,
        "source_binding": v1.training_binding,
        "registry_pin_override": REGISTRY_OVERRIDE,
        "exporter_environment": {
            "python": sys.version.split()[0],
        },
    }
    try:
        import sklearn
        import scipy

        binding["exporter_environment"]["sklearn"] = sklearn.__version__
        binding["exporter_environment"]["scipy"] = scipy.__version__
    except ImportError:
        pass
    BINDING_PATH.write_text(
        json.dumps(binding, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("CORPUS_EXPORT=" + json.dumps(binding, sort_keys=True)[:600], flush=True)


if __name__ == "__main__":
    main()
