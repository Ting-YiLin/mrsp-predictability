# Change log

## 1.0.0 strict repair

- Replaced partner-precomputed `b1_pred_sku` and P1 feature inputs with canonical raw event input.
- Added exact six-SKU group manifest.
- Reconstructed all pre-event histories internally.
- Added frozen B1 lambda grid and W1-W6 tuning/evaluation clock.
- Added chronology, duplicate, group-membership and exact-schema fail-closed checks.
- Added input/code SHA-256 provenance and aggregate-only output.
- Added current-label leakage regression test.
- Clarified that program PASS is execution integrity, not scientific replication.
