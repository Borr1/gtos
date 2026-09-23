# SCID FC Additive Impl LTF Orderflow Proxy Compatibility - 2026-05-12

- LTF and orderflow rows are valid when source data is unavailable; they fail closed for future use rather than fetching.
- Orderflow capture is local/cache-only and does not open paid/vendor/API access.
- Raw market blobs are not committed by this route.
