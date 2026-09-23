# Fresh Executor Simulation

Status: PASS.

A fresh executor simulation used an isolated synthetic CJ9 source and a copied package with test-only source-count parameters. It exercised the same production code paths for:

- candidate-universe construction;
- exact prior-batch reconstruction and exclusion;
- disjoint representative and department-challenge cohort selection;
- full event materialization;
- W1-W6 B0/B1/P1 evaluation;
- product checkpoint and normal resume;
- source/config identity locks;
- Audit ZIP staging and ZIP integrity.

Observed:
- normal first run: PASS;
- normal resume: PASS, all completed products skipped;
- core cfg change with old state: rejected with `RESUME_IDENTITY_MISMATCH`;
- Audit ZIP integrity: PASS.

The simulation does not establish scientific truth; it establishes executable semantics and package integrity.
