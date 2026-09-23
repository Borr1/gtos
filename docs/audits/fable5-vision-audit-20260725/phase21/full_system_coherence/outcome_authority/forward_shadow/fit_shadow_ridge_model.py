#!/usr/bin/env python3
"""Fit the frozen funnel ridge ONCE on the full opened estate; export to JSON.

Produces the forward-shadow lane's frozen model artifact
(`SHADOW_RIDGE_MODEL_V1.json`) and a golden parity fixture
(`GOLDEN_PARITY_FIXTURE_V1.json.gz`, >= 1000 real rows + sklearn predictions)
for the pure-python predictor's equivalence test.

Faithfulness contract:
  * The pipeline is the rule's exact declaration — loaded from the FROZEN
    research chain, byte-identical to what scored February and April/May: the
    committed r2 scorer (which pins the frozen wave21 worktree in sys.path)
    and the frozen `/private/tmp/w21_predecision_ridge.py` module.  This
    script purges its own repo's ``src`` bindings before loading that chain so
    every research import resolves against the frozen tree, exactly as the
    r3b April/May scorer ran.
  * Training rows are ALL opened resolved-eligible occurrences: Oct/Nov
    development + January + February + April/May — the same loaders, the same
    lifecycle labeler, the same eligibility.
  * Fit is ONE flat fit (candidate weight 1/window as the rule declares); no
    prequential continuation, because the forward lane cannot retrain daily by
    construction (the artifact is frozen).

Run on the research Mac (the opened estate lives in /private/tmp and the
lane-inputs hold):

    python3 docs/audits/.../forward_shadow/fit_shadow_ridge_model.py
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import importlib.util
import json
import math
import sys
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
ARTIFACT_PATH = HERE.parent / "SHADOW_RIDGE_MODEL_V1.json"
FIXTURE_PATH = HERE.parent / "GOLDEN_PARITY_FIXTURE_V1.json.gz"
FIXTURE_ROWS = 1200

# ---------------------------------------------------------------------------
# Step 1: import THIS repo's artifact layer, then purge `src` bindings so the
# frozen research chain (loaded next) owns every subsequent src.* import.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(MY_REPO))
from src.research_infra.wave21_forward_shadow.feature_contract import (  # noqa: E402
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    RULE_PAYLOAD_SHA256,
)
from src.research_infra.wave21_forward_shadow.ridge_artifact import (  # noqa: E402
    export_fitted_pipeline,
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
s2 = load_module("w21_score_feb_r2_frozen_for_shadow_fit", R2_SCORER)
r = s2.r  # frozen ridge module (loads the frozen worktree's src.* chain)

if list(r.CAT) != list(CATEGORICAL_FEATURES) or list(r.NUM) != list(NUMERIC_FEATURES):
    raise SystemExit("frozen feature lists diverge from the shadow feature contract")

rule = json.loads(RULE_PATH.read_text(encoding="utf-8"))
rule_core = dict(rule)
claimed_rule_sha = rule_core.pop("payload_sha256")
if canonical_hash(rule_core) != claimed_rule_sha or claimed_rule_sha != RULE_PAYLOAD_SHA256:
    raise SystemExit("frozen rule payload mismatch")

prereg = json.loads(PREREG_PATH.read_text(encoding="utf-8"))
prereg_core = dict(prereg)
claimed_prereg_sha = prereg_core.pop("payload_sha256")
if canonical_hash(prereg_core) != claimed_prereg_sha:
    raise SystemExit("frozen prereg payload mismatch")


def load_m1_sources(manifest_path: Path, expected_root: str):
    """Parameterized copy of the r3b loader (r2 hardcodes February's manifest)."""

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

    corpus_binding: dict = {"windows": [], "loaders": {}}

    initial, january = r.load_all()
    training = r.resolved_eligible(initial)
    initial_binding = {
        "window_id": "october_november_2025_development",
        "days": [day for day, _root, _sha in r.j.INITIAL_RUNS],
        "rows": len(initial),
        "resolved_eligible_rows": len(training),
        "authorities": {day: sha for day, _root, sha in r.j.INITIAL_RUNS},
    }
    corpus_binding["windows"].append(initial_binding)

    jan_start = len(training)
    for day, _authority in r.j.JAN_RUNS:
        training.extend(r.resolved_eligible(january[day]))
    corpus_binding["windows"].append(
        {
            "window_id": "january_2026",
            "days": [day for day, _authority in r.j.JAN_RUNS],
            "rows": sum(len(rows) for rows in january.values()),
            "resolved_eligible_rows": len(training) - jan_start,
            "authorities": {day: sha for day, sha in r.j.JAN_RUNS},
        }
    )

    feb_days = list(rule["validation"]["days_in_order"])
    feb_root_sha = rule["bindings"]["february_manifest_root_sha256"]
    feb_manifest_root, feb_sources = load_m1_sources(
        MANIFEST_DIR / "february_2026.json", feb_root_sha
    )
    old_root = s2.ROOT
    feb_rows = 0
    feb_start = len(training)
    feb_authorities = {}
    s2.ROOT = FEB_ROOT
    try:
        for day in feb_days:
            _raw, rows, summary = s2.load_day(day, feb_manifest_root, feb_sources)
            feb_rows += len(rows)
            feb_authorities[day] = summary["authority_root_sha256"]
            training.extend(r.resolved_eligible(rows))
    finally:
        s2.ROOT = old_root
    corpus_binding["windows"].append(
        {
            "window_id": "february_2026",
            "days": feb_days,
            "rows": feb_rows,
            "resolved_eligible_rows": len(training) - feb_start,
            "manifest_root_sha256": feb_manifest_root,
            "authorities": feb_authorities,
        }
    )

    for window in prereg["validation"]["windows"]:
        window_id = window["window_id"]
        manifest_root, sources = load_m1_sources(
            MANIFEST_DIR / f"{window_id}.json", window["manifest_root_sha256"]
        )
        window_rows = 0
        window_start = len(training)
        window_authorities = {}
        s2.ROOT = APRMAY_ROOT
        try:
            for day in window["days"]:
                _raw, rows, summary = s2.load_day(day, manifest_root, sources)
                window_rows += len(rows)
                window_authorities[day] = summary["authority_root_sha256"]
                training.extend(r.resolved_eligible(rows))
        finally:
            s2.ROOT = old_root
        corpus_binding["windows"].append(
            {
                "window_id": window_id,
                "days": list(window["days"]),
                "rows": window_rows,
                "resolved_eligible_rows": len(training) - window_start,
                "manifest_root_sha256": manifest_root,
                "authorities": window_authorities,
            }
        )
        print(
            json.dumps({"loaded_window": window_id, "training_rows": len(training)}),
            flush=True,
        )

    print(json.dumps({"total_training_rows": len(training)}), flush=True)

    model = r.make_model()
    train_y = np.asarray(
        [float(row.get("terminal_net_r") or 0.0) for row in training], dtype=float
    )
    weights = r.weights(training)
    frame = r.frame(training)
    model.fit(frame, train_y, ridge__sample_weight=weights)

    import sklearn

    corpus_binding["loaders"] = {
        "r2_scorer_path": str(R2_SCORER),
        "r2_scorer_sha256": sha256_file(R2_SCORER),
        "ridge_module_path": str(s2.RIDGE_SOURCE),
        "ridge_module_sha256": sha256_file(s2.RIDGE_SOURCE),
        "frozen_repo": str(s2.REPO),
        "candidate_generator_sha256_frozen": sha256_file(
            s2.REPO / "src/components/broader_origin_generators.py"
        ),
        "sklearn_version": sklearn.__version__,
    }
    training_binding = {
        "fitted_utc": datetime.now(timezone.utc).isoformat(),
        "training_rows": len(training),
        "target": "complete modelled terminal net R; no-fill 0R; censored excluded",
        "candidate_weight": "1 / resolved training candidates in same decision_window_id",
        "fit_mode": "single_flat_fit_all_opened_windows",
        "prereg_payload_sha256": claimed_prereg_sha,
        **corpus_binding,
    }

    payload = export_fitted_pipeline(
        pipeline=model,
        categorical_features=list(r.CAT),
        numeric_features=list(r.NUM),
        training_binding=training_binding,
        rule_payload_sha256=RULE_PAYLOAD_SHA256,
    )
    ARTIFACT_PATH.write_text(
        json.dumps(payload, indent=1, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    # Golden fixture: deterministic stride sample across the whole corpus.
    stride = max(1, len(training) // FIXTURE_ROWS)
    sample_indexes = list(range(0, len(training), stride))[:FIXTURE_ROWS]
    sample_rows = [training[i] for i in sample_indexes]
    sample_predictions = model.predict(r.frame(sample_rows))

    def fixture_row(row: dict) -> dict:
        out = {}
        for key in list(r.CAT) + list(r.NUM):
            value = row[key]
            if isinstance(value, float) and not math.isfinite(value):
                out[key] = None
            elif isinstance(value, np.floating):
                out[key] = float(value)
            else:
                out[key] = value
        return out

    fixture = {
        "schema": "gtos.wave21.forward_shadow.golden_parity_fixture.v1",
        "artifact_sha256": payload["artifact_sha256"],
        "sklearn_version": sklearn.__version__,
        "row_count": len(sample_rows),
        "stride": stride,
        "rows": [fixture_row(row) for row in sample_rows],
        "sklearn_predictions": [float(v) for v in sample_predictions],
    }
    with gzip.open(FIXTURE_PATH, "wt", encoding="utf-8") as handle:
        json.dump(fixture, handle, sort_keys=True, allow_nan=False)

    print(
        "SHADOW_MODEL_FIT="
        + json.dumps(
            {
                "artifact": str(ARTIFACT_PATH),
                "artifact_sha256": payload["artifact_sha256"],
                "training_rows": len(training),
                "fixture": str(FIXTURE_PATH),
                "fixture_rows": len(sample_rows),
                "windows": [
                    {
                        "window_id": w["window_id"],
                        "resolved_eligible_rows": w["resolved_eligible_rows"],
                    }
                    for w in corpus_binding["windows"]
                ],
            },
            sort_keys=True,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
