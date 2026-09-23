"""Prequential daily refit for the forward-shadow lane (owner directive
2026-08-12: the flat single fit "must be fixed and activated immediately").

Semantics — exactly the sealed reads': at the first cycle of each new trading
day (UTC), the rule's ridge is refitted on the FROZEN corpus (Oct/Nov dev +
Jan + Feb + Apr/May — the same 284,652 rows, shipped as the committed
``FROZEN_TRAINING_CORPUS_V1.npz``) plus every shadow-observed
resolved-eligible outcome row logged to date (the lane's own would-be orders
with FINAL modelled resolutions, filtered exactly as ``r.resolved_eligible``:
geometry-valid, finite complete cost <= 0.2R, resolved — censored rows are
excluded, RESOLVED_NO_FILL trains as 0R).  Model parameters are the frozen
rule's; the fit code path is the same sklearn pipeline that built
SHADOW_RIDGE_MODEL_V1, exported through the same portable-JSON layer.  The
pure-python predictor is untouched — it loads the day's artifact.

With zero forward rows the refit reproduces the committed V1 artifact — the
transition's golden test (asserted at export time and in the suite); the
runner therefore uses V1 directly on day zero and refits from the first day
with observed outcomes.

sklearn (pinned 1.8.0) is imported lazily inside the fit path only; the
decision/predict path stays sklearn-free.
"""

from __future__ import annotations

import dataclasses
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from src.research_infra.wave21_forward_shadow.feature_contract import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    RULE_PAYLOAD_SHA256,
)
from src.research_infra.wave21_forward_shadow.ridge_artifact import (
    export_fitted_pipeline,
)

# Lifecycle statuses that count as RESOLVED for training (the funnel's
# ``fit._state`` returns a state for exactly these; censored rows are None).
RESOLVED_STATUS_PREFIX = "RESOLVED_"
DAILY_ARTIFACT_TEMPLATE = "SHADOW_RIDGE_DAILY_{day}.json"


class DailyRefitError(RuntimeError):
    pass


@dataclasses.dataclass
class FrozenCorpus:
    """The exported frozen design columns, reloaded exactly."""

    columns: dict[str, np.ndarray]  # CAT: object arrays of str; NUM: float64
    y: np.ndarray
    window_ids: np.ndarray
    row_count: int
    path: Path


def load_frozen_corpus(path: str | Path) -> FrozenCorpus:
    path = Path(path)
    if not path.is_file():
        raise DailyRefitError(f"frozen training corpus missing: {path}")
    with np.load(path, allow_pickle=False) as bundle:
        columns: dict[str, np.ndarray] = {}
        for name in CATEGORICAL_FEATURES:
            vocab = bundle[f"cat__{name}__vocab"]
            codes = bundle[f"cat__{name}__codes"]
            # object array of python str — the exact dtype r.frame() produced
            columns[name] = np.asarray(
                [str(token) for token in vocab], dtype=object
            )[codes]
        for name in NUMERIC_FEATURES:
            columns[name] = np.asarray(bundle[f"num__{name}"], dtype=np.float64)
        y = np.asarray(bundle["terminal_net_r"], dtype=np.float64)
        window_vocab = bundle["decision_window_vocab"]
        window_codes = bundle["decision_window_codes"]
        window_ids = np.asarray(
            [str(token) for token in window_vocab], dtype=object
        )[window_codes]
    row_count = int(y.shape[0])
    for name, column in columns.items():
        if column.shape[0] != row_count:
            raise DailyRefitError(f"corpus column misaligned: {name}")
    if window_ids.shape[0] != row_count:
        raise DailyRefitError("corpus window ids misaligned")
    return FrozenCorpus(
        columns=columns, y=y, window_ids=window_ids, row_count=row_count, path=path
    )


def make_rule_pipeline():
    """The frozen rule's exact sklearn pipeline (mirror of ``r.make_model``)."""

    from sklearn.compose import ColumnTransformer
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    numeric = Pipeline(
        [
            ("impute", SimpleImputer(strategy="constant", fill_value=0.0, add_indicator=True)),
            ("scale", StandardScaler()),
        ]
    )
    pre = ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore"), list(CATEGORICAL_FEATURES)),
            ("num", numeric, list(NUMERIC_FEATURES)),
        ],
        sparse_threshold=0.3,
    )
    return Pipeline([("pre", pre), ("ridge", Ridge(alpha=10.0, solver="lsqr"))])


def _iter_jsonl(path: Path):
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def collect_forward_training_rows(
    namespace_dir: str | Path,
    *,
    until_utc: datetime | None = None,
) -> list[dict[str, Any]]:
    """Shadow-observed resolved-eligible rows, mirroring ``r.resolved_eligible``.

    A row enters training iff: it was an ELIGIBLE candidate (geometry-valid,
    finite complete cost <= 0.2R — the packet's own eligibility verdict), it
    was selected as a would-be order, and its modelled lifecycle reached a
    FINAL RESOLVED_* status by ``until_utc`` (censored rows are excluded, like
    ``fit._state`` None).  Target: ``terminal_net_r`` (RESOLVED_NO_FILL -> 0R,
    the rule's declared training target).
    """

    namespace = Path(namespace_dir)
    outcomes: dict[str, dict[str, Any]] = {}
    for row in _iter_jsonl(namespace / "order_outcomes.jsonl"):
        if row.get("final") is not True:
            continue
        status = str(row.get("lifecycle_label_status") or "")
        if not status.startswith(RESOLVED_STATUS_PREFIX):
            continue
        if until_utc is not None:
            resolved_at = row.get("resolved_at_utc")
            try:
                resolved_dt = datetime.fromisoformat(str(resolved_at))
            except (TypeError, ValueError):
                resolved_dt = None
            if resolved_dt is not None and resolved_dt > until_utc:
                continue
        outcomes[str(row.get("candidate_occurrence_key"))] = row

    if not outcomes:
        return []

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    packet_dir = namespace / "decision_packets"
    for path in sorted(packet_dir.glob("*.jsonl")):
        for packet in _iter_jsonl(path):
            for candidate in packet.get("candidates") or ():
                if not candidate.get("eligible"):
                    continue
                features = candidate.get("features")
                if not isinstance(features, Mapping):
                    continue
                key = str(features.get("candidate_occurrence_key") or "")
                if not key or key in seen or key not in outcomes:
                    continue
                seen.add(key)
                outcome = outcomes[key]
                cleaned: dict[str, Any] = {}
                for name in CATEGORICAL_FEATURES:
                    value = features.get(name)
                    cleaned[name] = "MISSING" if value is None else str(value)
                for name in NUMERIC_FEATURES:
                    value = features.get(name)
                    try:
                        number = float(value)
                    except (TypeError, ValueError):
                        number = math.nan
                    cleaned[name] = number if math.isfinite(number) else math.nan
                cleaned["terminal_net_r"] = float(outcome.get("terminal_net_r") or 0.0)
                cleaned["decision_window_id"] = str(features.get("decision_window_id"))
                rows.append(cleaned)
    return rows


def refit_payload(
    corpus: FrozenCorpus,
    forward_rows: Iterable[Mapping[str, Any]],
    *,
    day: str,
    frozen_corpus_sha256: str,
) -> dict[str, Any]:
    """One prequential fit: frozen corpus + forward rows -> portable payload."""

    import pandas as pd
    import sklearn

    forward_rows = list(forward_rows)
    frozen_frame = pd.DataFrame(
        {
            name: corpus.columns[name]
            for name in (*CATEGORICAL_FEATURES, *NUMERIC_FEATURES)
        }
    )
    if forward_rows:
        forward_frame = pd.DataFrame(
            [
                {name: row[name] for name in (*CATEGORICAL_FEATURES, *NUMERIC_FEATURES)}
                for row in forward_rows
            ]
        )
        for name in CATEGORICAL_FEATURES:
            forward_frame[name] = forward_frame[name].fillna("MISSING").astype(str)
        frame = pd.concat([frozen_frame, forward_frame], ignore_index=True)
        y = np.concatenate(
            [
                corpus.y,
                np.asarray(
                    [float(row.get("terminal_net_r") or 0.0) for row in forward_rows],
                    dtype=np.float64,
                ),
            ]
        )
        window_ids = list(corpus.window_ids) + [
            str(row["decision_window_id"]) for row in forward_rows
        ]
    else:
        frame = frozen_frame
        y = corpus.y
        window_ids = list(corpus.window_ids)

    counts = Counter(window_ids)
    weights = np.asarray(
        [1.0 / counts[window_id] for window_id in window_ids], dtype=np.float64
    )
    pipeline = make_rule_pipeline()
    pipeline.fit(frame, y, ridge__sample_weight=weights)
    payload = export_fitted_pipeline(
        pipeline=pipeline,
        categorical_features=list(CATEGORICAL_FEATURES),
        numeric_features=list(NUMERIC_FEATURES),
        training_binding={
            "mode": "prequential_daily_refit",
            "day": str(day),
            "refit_utc": datetime.now(timezone.utc).isoformat(),
            "frozen_corpus_file": corpus.path.name,
            "frozen_corpus_sha256": frozen_corpus_sha256,
            "frozen_rows": corpus.row_count,
            "forward_rows": len(forward_rows),
            "training_rows": corpus.row_count + len(forward_rows),
            "target": "complete modelled terminal net R; no-fill 0R; censored excluded",
            "candidate_weight": (
                "1 / resolved training candidates in same decision_window_id"
            ),
            "sklearn_version": sklearn.__version__,
        },
        rule_payload_sha256=RULE_PAYLOAD_SHA256,
    )
    return payload


def write_daily_artifact(
    payload: Mapping[str, Any], *, models_dir: str | Path, day: str
) -> Path:
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    path = models_dir / DAILY_ARTIFACT_TEMPLATE.format(day=day)
    path.write_text(
        json.dumps(payload, indent=1, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return path
