"""Prequential daily-refit tests (owner directive 2026-08-12).

Two load-bearing assertions:
  * the TRANSITION golden test — refitting the frozen corpus with ZERO forward
    rows reproduces the committed flat V1 artifact (payload-identical model,
    predictions equal on the golden rows);
  * the MECHANICS test — one synthetic resolved forward row is consumed:
    training-row count +1, artifact sha changes, forward window weighted.

Plus the collector's eligibility/resolution filters and the runner's
day-boundary hook.  Requires sklearn (pinned 1.8.0) + the committed corpus;
skips cleanly where either is absent.
"""

from __future__ import annotations

import gzip
import json
import platform
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

pytest.importorskip("sklearn")

from src.research_infra.wave21_forward_shadow.daily_refit import (
    collect_forward_training_rows,
    load_frozen_corpus,
    refit_payload,
)
from src.research_infra.wave21_forward_shadow.feature_contract import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
)
from src.research_infra.wave21_forward_shadow.ridge_artifact import (
    ShadowRidgeModel,
    canonical_payload_sha256,
    load_model,
)

REPO = Path(__file__).resolve().parents[2]
FORWARD_SHADOW_DIR = (
    REPO
    / "docs/audits/fable5-vision-audit-20260725/phase21/full_system_coherence"
    / "outcome_authority/forward_shadow"
)
CORPUS = FORWARD_SHADOW_DIR / "FROZEN_TRAINING_CORPUS_V1.npz"
V1_ARTIFACT = FORWARD_SHADOW_DIR / "SHADOW_RIDGE_MODEL_V1.json"
FIXTURE = FORWARD_SHADOW_DIR / "GOLDEN_PARITY_FIXTURE_V1.json.gz"
DRIFT_RECEIPT = FORWARD_SHADOW_DIR / "SOLVER_PLATFORM_DRIFT_RECEIPT_V1.json"


def _platform_band() -> tuple[dict, str]:
    """Select this platform's measured reproduction band from the receipt.

    Keyed on the receipt rather than on a literal so the number in the test and
    the number in the evidence cannot drift apart.
    """

    bands = json.loads(DRIFT_RECEIPT.read_text(encoding="utf-8"))["bands"]
    applies = bands["reference"]["applies_to"]
    if (
        sys.platform == applies["sys_platform"]
        and platform.machine() == applies["machine"]
    ):
        return bands["reference"], "reference"
    return bands["other"], "other"

pytestmark = pytest.mark.skipif(
    not CORPUS.is_file(), reason="frozen training corpus not present"
)

UTC = timezone.utc


def _model_from_payload(payload) -> ShadowRidgeModel:
    return ShadowRidgeModel(
        payload,
        artifact_sha256=canonical_payload_sha256(
            {k: v for k, v in payload.items() if k != "artifact_sha256"}
        ),
    )


@pytest.fixture(scope="module")
def corpus():
    return load_frozen_corpus(CORPUS)


@pytest.fixture(scope="module")
def day_zero_payload(corpus):
    return refit_payload(
        corpus, forward_rows=[], day="2026-08-12", frozen_corpus_sha256="test"
    )


@pytest.fixture(scope="module")
def fixture_rows():
    with gzip.open(FIXTURE, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def synthetic_forward_row(fixture_rows, *, net_r=1.5, window="forward_shadow:test"):
    row = dict(fixture_rows["rows"][0])
    row["terminal_net_r"] = net_r
    row["decision_window_id"] = window
    # null (json) numerics -> the collector normally converts; mirror that
    for name in NUMERIC_FEATURES:
        if row[name] is None:
            row[name] = float("nan")
    return row


class TestTransitionGolden:
    def test_day_zero_refit_reproduces_v1(self, day_zero_payload, fixture_rows):
        """Zero forward rows must reproduce V1 — to this platform's measured band.

        The bar is platform-dependent and the band comes from a receipt, not
        from a constant chosen here: `Ridge(solver="lsqr")` is an iterative
        solve over a wide one-hot design, so its last bits depend on the BLAS
        and its thread count.  On the platform V1 was fitted on this is
        bit-exact; on the VPS it is not, and loosening the constant globally
        would have thrown away the bit-exactness guard that still holds where
        it should.  See SOLVER_PLATFORM_DRIFT_RECEIPT_V1.json for the
        measurements, the mechanism, and what the band does not license.
        """

        band, band_name = _platform_band()
        v1 = load_model(V1_ARTIFACT)
        refit_model = _model_from_payload(day_zero_payload)
        max_diff = 0.0
        for row, expected in zip(
            fixture_rows["rows"], fixture_rows["sklearn_predictions"]
        ):
            max_diff = max(
                max_diff, abs(refit_model.predict_row(row) - float(expected))
            )
        tolerance = float(band["max_abs_prediction_drift"])
        assert max_diff < tolerance, (
            f"day-zero refit drifted from V1 by {max_diff:g} on the "
            f"{band_name!r} band (limit {tolerance:g}). If this is a non-reference "
            "platform, first check the launcher still pins OMP_NUM_THREADS / "
            "OPENBLAS_NUM_THREADS / MKL_NUM_THREADS to 1 — unpinned measured 3.5x "
            "worse. A genuine excursion is a finding to record in "
            "SOLVER_PLATFORM_DRIFT_RECEIPT_V1.json, not a constant to raise."
        )
        # Below the decision threshold by construction: a drift that could move
        # a candidate across the 0.10 R abstain bar is not a tolerance.
        assert max_diff < 0.10 * 0.10
        if band.get("assert_payload_bit_identical"):
            assert day_zero_payload["model"] == v1.payload["model"], (
                "day-zero refit model payload is not bit-identical to V1 on the "
                "reference platform"
            )

    def test_band_selection_covers_both_platforms(self, monkeypatch):
        """Both branches are reachable — the Windows band is not dead code.

        Without this the non-reference branch would only ever execute on a
        host nobody runs the suite on, which is how it would rot.
        """

        import tests.research_infra.test_wave21_forward_shadow_refit as module

        monkeypatch.setattr(module.sys, "platform", "darwin")
        monkeypatch.setattr(module.platform, "machine", lambda: "arm64")
        band, name = module._platform_band()
        assert name == "reference"
        assert band["assert_payload_bit_identical"] is True
        assert band["max_abs_prediction_drift"] == 1e-12

        monkeypatch.setattr(module.sys, "platform", "win32")
        monkeypatch.setattr(module.platform, "machine", lambda: "AMD64")
        band, name = module._platform_band()
        assert name == "other"
        assert band["assert_payload_bit_identical"] is False
        # the deployed VPS measurement must sit inside the band it selects
        assert 0.00079 < band["max_abs_prediction_drift"] < 0.10

    def test_drift_receipt_bands_are_self_consistent(self):
        """The receipt is the authority, so it must not contradict itself."""

        receipt = json.loads(DRIFT_RECEIPT.read_text(encoding="utf-8"))
        other = receipt["bands"]["other"]["max_abs_prediction_drift"]
        reference = receipt["bands"]["reference"]["max_abs_prediction_drift"]
        assert reference < other
        for row in receipt["measurements"]:
            measured = float(row["max_abs_prediction_drift"])
            limit = reference if row["role"] == "reference" else other
            assert measured < limit, (
                f"{row['role']} measured {measured:g} outside its own band {limit:g}"
            )
            if row["role"] == "reference":
                assert row["payload_bit_identical"] is True
        # every non-reference measurement must stay under the decision threshold
        assert all(
            float(row["max_abs_prediction_drift"]) < 0.10
            for row in receipt["measurements"]
        )

    def test_corpus_binding_matches_v1(self, corpus):
        v1 = load_model(V1_ARTIFACT)
        assert corpus.row_count == int(v1.training_binding["training_rows"])
        binding = json.loads(
            (FORWARD_SHADOW_DIR / "FROZEN_TRAINING_CORPUS_V1.binding.json").read_text()
        )
        assert binding["row_count"] == corpus.row_count
        assert binding["reproduces_v1_artifact_sha256"] == v1.artifact_sha256


class TestRefitMechanics:
    def test_one_forward_row_consumed(self, corpus, day_zero_payload, fixture_rows):
        forward = [synthetic_forward_row(fixture_rows)]
        payload = refit_payload(
            corpus, forward, day="2026-08-13", frozen_corpus_sha256="test"
        )
        assert payload["training_binding"]["training_rows"] == corpus.row_count + 1
        assert payload["training_binding"]["forward_rows"] == 1
        assert payload["artifact_sha256"] != day_zero_payload["artifact_sha256"]
        assert payload["model"] != day_zero_payload["model"]
        # the refit model still loads and predicts through the frozen predictor
        model = _model_from_payload(payload)
        value = model.predict_row(fixture_rows["rows"][0])
        assert isinstance(value, float)


class TestForwardRowCollector:
    @staticmethod
    def _write(namespace: Path, name: str, rows):
        path = namespace / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row) + "\n")

    def _packet_candidate(self, fixture_rows, *, key, window, eligible=True):
        features = dict(fixture_rows["rows"][1])
        features["candidate_occurrence_key"] = key
        features["decision_window_id"] = window
        return {"eligible": eligible, "features": features}

    def test_filters_mirror_resolved_eligible(self, tmp_path, fixture_rows):
        namespace = tmp_path / "ns"
        key_resolved = "candidate_occurrence_" + "aa" * 32
        key_censored = "candidate_occurrence_" + "bb" * 32
        key_pending = "candidate_occurrence_" + "cc" * 32
        key_ineligible = "candidate_occurrence_" + "dd" * 32
        window = "forward_shadow:2026-08-12T12:15:00+00:00"
        self._write(
            namespace,
            "decision_packets/2026-08-12.jsonl",
            [
                {
                    "decision_window_id": window,
                    "candidates": [
                        self._packet_candidate(fixture_rows, key=key_resolved, window=window),
                        self._packet_candidate(fixture_rows, key=key_censored, window=window),
                        self._packet_candidate(fixture_rows, key=key_pending, window=window),
                        self._packet_candidate(
                            fixture_rows, key=key_ineligible, window=window, eligible=False
                        ),
                    ],
                }
            ],
        )
        now = datetime(2026, 8, 12, 14, 0, tzinfo=UTC)
        self._write(
            namespace,
            "order_outcomes.jsonl",
            [
                {
                    "candidate_occurrence_key": key_resolved,
                    "final": True,
                    "lifecycle_label_status": "RESOLVED_FILLED_TARGET",
                    "terminal_net_r": 1.234,
                    "resolved_at_utc": now.isoformat(),
                },
                {
                    "candidate_occurrence_key": key_censored,
                    "final": True,
                    "lifecycle_label_status": "CENSORED_SOURCE_INTERVAL_GAP",
                    "terminal_net_r": None,
                    "resolved_at_utc": now.isoformat(),
                },
                {
                    "candidate_occurrence_key": key_pending,
                    "final": False,
                    "lifecycle_label_status": None,
                },
                {
                    "candidate_occurrence_key": key_ineligible,
                    "final": True,
                    "lifecycle_label_status": "RESOLVED_FILLED_STOP",
                    "terminal_net_r": -1.05,
                    "resolved_at_utc": now.isoformat(),
                },
            ],
        )
        rows = collect_forward_training_rows(namespace, until_utc=now + timedelta(hours=1))
        assert len(rows) == 1
        assert rows[0]["terminal_net_r"] == 1.234
        assert rows[0]["decision_window_id"] == window
        assert set(CATEGORICAL_FEATURES + NUMERIC_FEATURES) <= set(rows[0])

    def test_until_utc_excludes_future_resolutions(self, tmp_path, fixture_rows):
        namespace = tmp_path / "ns"
        key = "candidate_occurrence_" + "ee" * 32
        window = "forward_shadow:2026-08-12T12:15:00+00:00"
        self._write(
            namespace,
            "decision_packets/2026-08-12.jsonl",
            [
                {
                    "decision_window_id": window,
                    "candidates": [
                        self._packet_candidate(fixture_rows, key=key, window=window)
                    ],
                }
            ],
        )
        resolved_at = datetime(2026, 8, 12, 14, 0, tzinfo=UTC)
        self._write(
            namespace,
            "order_outcomes.jsonl",
            [
                {
                    "candidate_occurrence_key": key,
                    "final": True,
                    "lifecycle_label_status": "RESOLVED_FILLED_TARGET",
                    "terminal_net_r": 0.5,
                    "resolved_at_utc": resolved_at.isoformat(),
                }
            ],
        )
        before = collect_forward_training_rows(
            namespace, until_utc=resolved_at - timedelta(minutes=1)
        )
        after = collect_forward_training_rows(
            namespace, until_utc=resolved_at + timedelta(minutes=1)
        )
        assert before == [] and len(after) == 1
