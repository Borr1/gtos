# VPS Migration Contract

Generated: 2026-05-31T18:17:52.443331Z

## Scope

This route prepares compliant infrastructure and data preservation only. It does not start the live runtime, connect to MT5, change credentials, or perform broker/order/deal/position actions.

## Identity And Residency Basis

- Owner-provided fact: the owner is Tunisian with Tunisia residency/permanent address.
- Owner-provided fact: Malaysia is temporary travel only.
- Do not classify the owner as Malaysia resident or citizen unless official KYC evidence says so.
- Do not invent United States residency, citizenship, or broker eligibility.

## redacted_account/VPS Compatibility Contract

- VPS must be private/dedicated and use a stable dedicated IP.
- VPS country/IP must not be on redacted_account's restricted-country list.
- VPS country/IP must not be the United States when using MetaQuotes/MT5 access.
- Shared VPS use is incompatible with this route.
- Broker-sponsored MetaTrader VPS use is incompatible with this route.
- Manual trading through the VPS is incompatible with this route.
- VPS use must be tied to the trade-taking EA/system requirement where redacted_account policy requires it.
- redacted_account VPS/EA add-on or fee state must be documented before any MT5 server access.
- Any inaccurate residency, inaccurate nationality, inaccurate identity, restricted-country IP, shared VPS, or identity/location misstatement is a hard stop.

## Machine Roles

- Local machine while traveling: development, research, source inventory, and control artifacts only unless network-origin compliance is proven before broker access.
- VPS machine: read-only export first, then dry-run verifier, then a separate owner-approved live-ops action for any runtime start.

## Support Confirmation Slot

Save any written redacted_account support confirmation under this route with secrets redacted, then add it to `OFFICIAL_redacted_account_SOURCE_INDEX.json` or a follow-up support-confirmation ledger.
