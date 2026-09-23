# MRSP V1 Strict External Replication Kit

This is the repaired external kit. Unlike the earlier evaluation harness, the partner **does not precompute B1 or P1 features**. The supplied runner starts from canonical raw events and a pre-frozen six-SKU group manifest, reconstructs the pre-event state, tunes only B1's frozen smoothing grid inside the frozen TUNE windows, computes P1, applies the already-frozen P1 cutoffs, and returns aggregate statistics.

## Scientific target

The task is conditional choice: given that a household purchased within a fixed six-SKU choice set, which SKU was selected? This is not purchase-incidence or next-basket prediction. Coverage is accepted purchase-event coverage, not the fraction of households.

## Local QA

```bash
python qa/make_fixture.py
python qa/test_no_current_label_leak.py
python run_external_test.py --events qa/fixture_events.csv --groups qa/fixture_groups.csv --output qa/fixture_output.json
python validate_external_output.py --input qa/fixture_output.json
```

## Real frozen run

```bash
python run_external_test.py --events partner_events.csv --groups groups.csv --output aggregate_output.json
python validate_external_output.py --input aggregate_output.json
```

Read `PRECHECK.md`, `DATA_SCHEMA.md`, and `FROZEN_SPEC.md` before a real run. The input must stay inside the partner environment; only the aggregate JSON should leave it.

## Interpretation boundary

`execution_status=PASS` only means the code ran under the frozen protocol. It does **not** mean the study replicated scientifically. Independence of the data, pre-freezing of the 53-week period and groups, adequacy of sample size, and the observed performance must be reviewed separately.
