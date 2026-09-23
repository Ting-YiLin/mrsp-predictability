# Reproducibility

## A. Verify the released evidence without raw data

Run:

```bash
python reproduce/verify_release.py
```

This checks that the bundled machine-output snapshots reproduce the expected public metrics and that the public expected-results file has not drifted.

## B. Full reproduction with the same canonical CJ9 store

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run:

```bash
python reproduce/run_full_reproduction.py --cj9 /path/to/CJ9
```

Windows:

```bat
reproduce\run_all.bat C:\path\to\CJ9
```

The wrapper executes the exact frozen confirmatory package under `reproduce/frozen_confirmatory/` and then runs `verify_expected_results.py` against the newly generated `w/FULL/summary.json`.

## What the full run does

1. hashes the CJ9 source partitions;
2. reconstructs the week≤22 candidate pool;
3. verifies the candidate pool size expected by the frozen package;
4. reconstructs the first-batch stable keys and requires exact match;
5. excludes the first 100 product groups;
6. selects a second representative batch and a disjoint department-challenge batch using fixed hashes and week≤22 information only;
7. materializes their six-SKU event sets;
8. runs W1–W6 walk-forward B0/B1/P1 evaluation;
9. produces the confirmation grade and machine summaries;
10. compares core public metrics with `EXPECTED_RESULTS.json`.

## Expected numerical tolerance

The public verifier uses an absolute tolerance of 0.001 for core coverage/accuracy proportions (0.1 percentage point) and exact matching for counts/grade. The original frozen run is retained in `results/machine/`.

## Package integrity

Use:

```bash
python reproduce/verify_manifest.py
```

to verify the release manifest and SHA-256 values.
