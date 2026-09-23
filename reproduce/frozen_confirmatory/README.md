# MRSP Predictability Confirmatory V1

Purpose: confirm, on a second untouched cross-product batch, whether the frozen simple predictability architecture transfers beyond the first 100 new products.

This package intentionally does **not** optimize P1, B0/B1, cutoffs, or action thresholds.

Execution flow:
1. dependency/self tests;
2. real-data availability + upstream-universe reconstruction;
3. reproduce the prior 100 exactly and exclude them;
4. create a 100-product representative cohort plus a 60-100 product department challenge cohort;
5. materialize events;
6. W1-W6 walk-forward evaluation, product-first with checkpoint/resume;
7. product-level bootstrap and cross-department summaries;
8. one Audit ZIP.

Expected local source: `C:\MR\data\CJ9`.

Default output: `MRSP_PREDICTABILITY_CONFIRMATORY_AUDIT_<run_id>.zip`.
