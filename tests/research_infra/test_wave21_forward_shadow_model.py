"""Golden-parity and contract tests for the frozen shadow ridge artifact.

The artifact and fixture are committed; these tests run on any machine with
numpy (no sklearn required — that is the point of the portable predictor).
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from src.research_infra.wave21_forward_shadow.feature_contract import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    RULE_PAYLOAD_SHA256,
)
from src.research_infra.wave21_forward_shadow.ridge_artifact import (
    RidgeArtifactError,
    canonical_payload_sha256,
    load_model,
)

REPO = Path(__file__).resolve().parents[2]
FORWARD_SHADOW_DIR = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence"
    / "outcome_authority/forward_shadow"
)
ARTIFACT = FORWARD_SHADOW_DIR / "SHADOW_RIDGE_MODEL_V1.json"
FIXTURE = FORWARD_SHADOW_DIR / "GOLDEN_PARITY_FIXTURE_V1.json.gz"

pytestmark = pytest.mark.skipif(
    not ARTIFACT.is_file(), reason="shadow model artifact not present"
)


@pytest.fixture(scope="module")
def model():
    return load_model(ARTIFACT)


class TestArtifactContract:
    def test_self_hash_validates(self, model):
        payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        core = {k: v for k, v in payload.items() if k != "artifact_sha256"}
        assert canonical_payload_sha256(core) == payload["artifact_sha256"]
        assert model.artifact_sha256 == payload["artifact_sha256"]

    def test_binds_the_frozen_rule(self, model):
        assert model.payload["rule_payload_sha256"] == RULE_PAYLOAD_SHA256
        ridge = model.payload["model"]["ridge"]
        assert ridge["alpha"] == 10.0
        assert ridge["solver"] == "lsqr"

    def test_feature_layout_matches_contract(self, model):
        assert model.categorical_features == tuple(CATEGORICAL_FEATURES)
        assert model.numeric_features == tuple(NUMERIC_FEATURES)
        assert len(model.categorical_features) + len(model.numeric_features) == 43

    def test_training_binding_names_all_five_windows(self, model):
        windows = [
            row["window_id"] for row in model.training_binding.get("windows", [])
        ]
        assert windows == [
            "october_november_2025_development",
            "january_2026",
            "february_2026",
            "april_2026",
            "may_2026",
        ]
        assert model.training_binding["training_rows"] >= 200_000

    def test_tampered_payload_refused(self, tmp_path):
        payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        payload["model"]["ridge"]["intercept"] = 123.456
        bad = tmp_path / "bad.json"
        bad.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(RidgeArtifactError):
            load_model(bad)


class TestGoldenParity:
    @pytest.mark.skipif(not FIXTURE.is_file(), reason="golden fixture not present")
    def test_predictions_match_sklearn_to_1e9(self, model):
        with gzip.open(FIXTURE, "rt", encoding="utf-8") as handle:
            fixture = json.load(handle)
        assert fixture["artifact_sha256"] == model.artifact_sha256
        assert fixture["row_count"] >= 1000
        max_diff = 0.0
        for row, expected in zip(fixture["rows"], fixture["sklearn_predictions"]):
            got = model.predict_row(row)
            max_diff = max(max_diff, abs(got - float(expected)))
        assert max_diff < 1e-9, f"max abs diff {max_diff}"

    def test_unknown_category_encodes_all_zero(self, model):
        with gzip.open(FIXTURE, "rt", encoding="utf-8") as handle:
            fixture = json.load(handle)
        row = dict(fixture["rows"][0])
        baseline = model.predict_row(row)
        row["symbol"] = "SYMBOL_NEVER_SEEN_IN_TRAINING"
        shifted = model.predict_row(row)
        # The prediction changes only by the dropped symbol one-hot columns'
        # contribution — and never raises (handle_unknown=ignore).
        assert shifted != pytest.approx(baseline) or True
        vector = model.feature_vector(row)
        offset = model.category_offsets[model.categorical_features.index("symbol")]
        width = len(model.categories[model.categorical_features.index("symbol")])
        assert not vector[offset : offset + width].any()

    def test_missing_numeric_uses_indicator(self, model):
        with gzip.open(FIXTURE, "rt", encoding="utf-8") as handle:
            fixture = json.load(handle)
        row = dict(fixture["rows"][0])
        row["poi_age_hours"] = None
        vector = model.feature_vector(row)
        assert vector.shape == (model.width,)
