# Downstream Compatibility Audit

The 40-card/8-domain hypothesis factory is supported as downstream compatibility only. The implementation preserves context fields for baseline controls, setup family, side/direction, entry/stop/target references, POI bounds, LTF availability, orderflow/depth availability, and lifecycle status. It does not rank cards, select edges, validate outcomes, or promote anything.

LTF and orderflow/proxy unavailable paths fail closed. Code evidence is in `src/research_infra/forward_capture.py:2250-2296` and `src/research_infra/forward_capture.py:2480-2512`; tests cover this at `tests/test_scid_forward_capture_runtime_adapter.py:160-179`.

The `3,014` value remains prospective denominator context only, not a validation sample size or performance claim.
