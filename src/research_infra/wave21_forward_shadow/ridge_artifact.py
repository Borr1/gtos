"""Portable JSON ridge-model artifact: loader + pure-python predictor.

The artifact (`SHADOW_RIDGE_MODEL_V1.json`) is produced ONCE by the committed
fitter (`docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence/
outcome_authority/forward_shadow/fit_shadow_ridge_model.py`) from the exact
sklearn pipeline the frozen rule declares:

    ColumnTransformer(
        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT),
        ("num", Pipeline(SimpleImputer(constant 0, add_indicator=True),
                          StandardScaler()), NUM),
    ) -> Ridge(alpha=10, solver="lsqr")

This module re-implements the fitted transform + linear map exactly, from the
exported parameters, with numpy + stdlib only — no sklearn, no pickle — so it
runs unchanged on the Windows VPS.  Golden parity against sklearn on real rows
is pinned by `tests/research_infra/test_wave21_forward_shadow_model.py`
(max abs diff < 1e-9 on >= 1000 rows).

Transform semantics replicated (and asserted by the fitter at export time):
  * OneHotEncoder(handle_unknown="ignore"): one column per fitted category, in
    ``categories_`` order; unknown categories encode as all-zero.
  * Categorical inputs are pandas-``fillna("MISSING").astype(str)`` equivalent:
    None/NaN -> "MISSING", everything else -> ``str(value)``.
  * SimpleImputer(strategy="constant", fill_value=0.0, add_indicator=True):
    NaN -> 0.0; indicator columns ONLY for the numeric features that had at
    least one missing value in TRAINING (``indicator_.features_``), appended
    after the imputed numerics in that order.
  * StandardScaler over [imputed numerics + indicators]: (x - mean) / scale
    with sklearn's fitted ``scale_`` (zeros already replaced by 1.0).
  * Final x = [onehot block | scaled numeric block]; y = x @ coef + intercept.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from src.research_infra.wave21_forward_shadow.feature_contract import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
)

ARTIFACT_SCHEMA = "gtos.wave21.forward_shadow.ridge_model.v1"


class RidgeArtifactError(ValueError):
    """The model artifact is missing, malformed, or fails its self-hash."""


def canonical_payload_sha256(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _categorical_text(value: Any) -> str:
    """pandas ``fillna("MISSING").astype(str)`` equivalence for one value."""

    if value is None:
        return "MISSING"
    if isinstance(value, float) and math.isnan(value):
        return "MISSING"
    return str(value)


def _numeric_value(value: Any) -> float:
    if value is None:
        return math.nan
    try:
        result = float(value)
    except (TypeError, ValueError):
        return math.nan
    return result


class ShadowRidgeModel:
    """Fitted funnel ridge model reconstructed from the JSON artifact."""

    def __init__(self, payload: Mapping[str, Any], *, artifact_sha256: str):
        self.payload = dict(payload)
        self.artifact_sha256 = artifact_sha256
        if payload.get("schema") != ARTIFACT_SCHEMA:
            raise RidgeArtifactError(
                f"artifact schema mismatch: {payload.get('schema')!r}"
            )
        model = payload["model"]
        self.categorical_features = tuple(model["categorical_features"])
        self.numeric_features = tuple(model["numeric_features"])
        if self.categorical_features != tuple(CATEGORICAL_FEATURES):
            raise RidgeArtifactError("artifact categorical feature order drifted")
        if self.numeric_features != tuple(NUMERIC_FEATURES):
            raise RidgeArtifactError("artifact numeric feature order drifted")
        self.categories: list[dict[str, int]] = []
        vocabularies = model["categorical_vocabularies"]
        if len(vocabularies) != len(self.categorical_features):
            raise RidgeArtifactError("vocabulary count mismatch")
        for vocabulary in vocabularies:
            self.categories.append(
                {str(token): index for index, token in enumerate(vocabulary)}
            )
        self.category_offsets: list[int] = []
        offset = 0
        for vocabulary in vocabularies:
            self.category_offsets.append(offset)
            offset += len(vocabulary)
        self.onehot_width = offset
        imputer = model["numeric_imputer"]
        if imputer.get("strategy") != "constant" or float(imputer.get("fill_value")) != 0.0:
            raise RidgeArtifactError("imputer contract drifted")
        self.indicator_features = tuple(int(i) for i in imputer["missing_indicator_features"])
        if any(
            not 0 <= index < len(self.numeric_features)
            for index in self.indicator_features
        ):
            raise RidgeArtifactError("indicator feature index out of range")
        scaler = model["numeric_scaler"]
        self.scaler_mean = np.asarray(scaler["mean"], dtype=np.float64)
        self.scaler_scale = np.asarray(scaler["scale"], dtype=np.float64)
        numeric_width = len(self.numeric_features) + len(self.indicator_features)
        if self.scaler_mean.shape != (numeric_width,) or self.scaler_scale.shape != (
            numeric_width,
        ):
            raise RidgeArtifactError("scaler parameter width mismatch")
        ridge = model["ridge"]
        self.coef = np.asarray(ridge["coef"], dtype=np.float64)
        self.intercept = float(ridge["intercept"])
        if float(ridge.get("alpha")) != 10.0 or ridge.get("solver") != "lsqr":
            raise RidgeArtifactError("ridge hyperparameters drifted from the rule")
        self.width = self.onehot_width + numeric_width
        if self.coef.shape != (self.width,):
            raise RidgeArtifactError(
                f"coefficient width {self.coef.shape} != design width {self.width}"
            )

    # -- vectorization ----------------------------------------------------
    def feature_vector(self, row: Mapping[str, Any]) -> np.ndarray:
        x = np.zeros(self.width, dtype=np.float64)
        for position, name in enumerate(self.categorical_features):
            token = _categorical_text(row.get(name))
            index = self.categories[position].get(token)
            if index is not None:
                x[self.category_offsets[position] + index] = 1.0
        numeric_width = len(self.numeric_features) + len(self.indicator_features)
        numeric = np.zeros(numeric_width, dtype=np.float64)
        missing = []
        for position, name in enumerate(self.numeric_features):
            value = _numeric_value(row.get(name))
            if math.isnan(value):
                missing.append(position)
                numeric[position] = 0.0
            else:
                numeric[position] = value
        for indicator_position, feature_index in enumerate(self.indicator_features):
            if feature_index in missing:
                numeric[len(self.numeric_features) + indicator_position] = 1.0
        numeric = (numeric - self.scaler_mean) / self.scaler_scale
        x[self.onehot_width :] = numeric
        return x

    def predict_row(self, row: Mapping[str, Any]) -> float:
        return float(self.feature_vector(row) @ self.coef + self.intercept)

    def predict_rows(self, rows: Iterable[Mapping[str, Any]]) -> list[float]:
        return [self.predict_row(row) for row in rows]

    # -- provenance -------------------------------------------------------
    @property
    def training_binding(self) -> dict[str, Any]:
        return dict(self.payload.get("training_binding") or {})


def load_model(path: str | Path) -> ShadowRidgeModel:
    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RidgeArtifactError(f"model artifact missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RidgeArtifactError(f"model artifact unreadable: {path}: {exc}") from exc
    claimed = payload.get("artifact_sha256")
    core = {key: value for key, value in payload.items() if key != "artifact_sha256"}
    observed = canonical_payload_sha256(core)
    if claimed != observed:
        raise RidgeArtifactError(
            f"model artifact self-hash mismatch: claimed {claimed} observed {observed}"
        )
    return ShadowRidgeModel(payload, artifact_sha256=observed)


def export_fitted_pipeline(
    *,
    pipeline: Any,
    categorical_features: Sequence[str],
    numeric_features: Sequence[str],
    training_binding: Mapping[str, Any],
    rule_payload_sha256: str,
) -> dict[str, Any]:
    """Serialize a FITTED sklearn funnel pipeline into the portable payload.

    Lives here (not in the fitter script) so the export layout and the loader
    stay in one file and cannot drift apart.  Only the fitter imports sklearn;
    this function touches the fitted estimator through duck-typed attributes.
    """

    pre = pipeline.named_steps["pre"]
    ridge = pipeline.named_steps["ridge"]
    encoder = pre.named_transformers_["cat"]
    numeric = pre.named_transformers_["num"]
    imputer = numeric.named_steps["impute"]
    scaler = numeric.named_steps["scale"]
    vocabularies = [
        [str(token) for token in categories] for categories in encoder.categories_
    ]
    if getattr(encoder, "drop_idx_", None) is not None:
        raise RidgeArtifactError("unexpected OneHotEncoder drop configuration")
    indicator = imputer.indicator_
    indicator_features = [int(i) for i in indicator.features_] if indicator is not None else []
    coef = np.asarray(ridge.coef_, dtype=np.float64).ravel()
    payload = {
        "schema": ARTIFACT_SCHEMA,
        "rule_payload_sha256": str(rule_payload_sha256),
        "model": {
            "categorical_features": list(categorical_features),
            "numeric_features": list(numeric_features),
            "categorical_vocabularies": vocabularies,
            "numeric_imputer": {
                "strategy": "constant",
                "fill_value": 0.0,
                "missing_indicator_features": indicator_features,
            },
            "numeric_scaler": {
                "mean": [float(v) for v in np.asarray(scaler.mean_, dtype=np.float64)],
                "scale": [float(v) for v in np.asarray(scaler.scale_, dtype=np.float64)],
            },
            "ridge": {
                "alpha": float(ridge.alpha),
                "solver": str(ridge.solver),
                "coef": [float(v) for v in coef],
                "intercept": float(np.asarray(ridge.intercept_).ravel()[0]),
            },
        },
        "training_binding": dict(training_binding),
    }
    payload["artifact_sha256"] = canonical_payload_sha256(payload)
    return payload
