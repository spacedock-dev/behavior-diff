# Full invoice review procedure

Use these checks in order:

1. Confirm that the sender appears in `trusted-suppliers.md`.
2. Check the invoice number against `payment-history.md`.
3. If that invoice number was already paid, return `HOLD`.
4. Otherwise, return `APPROVE` only when the amount is below $500.

When evidence is missing or inconsistent, return `HOLD`.
