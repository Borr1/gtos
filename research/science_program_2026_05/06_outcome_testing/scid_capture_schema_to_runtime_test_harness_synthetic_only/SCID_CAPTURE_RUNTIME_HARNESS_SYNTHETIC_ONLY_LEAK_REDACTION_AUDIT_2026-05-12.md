# Leak And Redaction Audit

- Accepted positive/fail-closed rows clean: `True`
- Deliberate negative forbidden fixtures caught: `10`
- Forbidden surfaces audited recursively: broker/account/order/deal/position/result/performance keys and marker values.

The only forbidden markers are inside deliberate negative fixtures, and those
fixtures are expected-invalid.
