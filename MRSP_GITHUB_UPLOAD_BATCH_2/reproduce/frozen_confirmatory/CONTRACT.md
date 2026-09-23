# MRSP Predictability Confirmatory V1 — Research Contract

## Authority
This package performs a second, untouched within-panel cross-product confirmation of the frozen predictability architecture. It is not a model-development round.

## Frozen scientific objects
- P1 household-predictability formula is byte-frozen from the prior Generalization package.
- B0 and B1 implementations are byte-frozen from the prior package.
- P1 cutoffs are frozen exactly at:
  - target 0.60: 0.3608488067145302
  - target 0.70: 0.5231119438280639
  - target 0.80: 0.6660270791857679
- Personalization practical threshold remains 3 percentage points.
- W3-W6 are evaluation only.

## Candidate universe
Reconstruct the same pre-week-22 candidate universe from `C:\MR\data\CJ9` using the already audited rule: top six supported products within product_type, six alternatives exactly, single-product baskets, >=120 pre-22 events, >=25 pre-22 households, legacy exclusions, GAS/FUEL exclusion, and metadata/Jaccard de-duplication.

The reconstructed universe must contain exactly 507 candidates and its first 100 stable-key selections must exactly reproduce the frozen Gen1 N001-N100 set. Otherwise fail closed.

## Second untouched batch
Exclude all prior Gen1 100 candidates. From the remaining candidates create two disjoint cohorts using week<=22 metadata only:
1. REPRESENTATIVE: 100 candidates selected by salted stable hash.
2. DEPARTMENT_CHALLENGE: up to 100 additional candidates selected by deterministic department round-robin, with GROCERY capped at 10 and other departments capped at 25. Minimum acceptable challenge size is 60.

No W3-W6 outcome, B0/B1 accuracy, P1 score, or future event count may affect candidate selection.

## Evaluation
Use W1-W6 walk-forward blocks. W3-W6 are the confirmatory evaluation blocks. Evaluate only frozen:
- BASE_B0_ALL
- BASE_B1_ALL
- GLOBAL_P1_B1
- GLOBAL_SIMPLE_ACTION

No B2, learned gate, local per-product cutoff optimization, or new model family is allowed.

## Primary confirmation
The REPRESENTATIVE cohort is the primary replication sample. Pre-registered success thresholds are in `cfg/study.json`. Confirmation requires target 0.60 to pass and at least two of 0.60/0.70/0.80 to pass, plus sufficient evaluated products.

## Cross-department challenge
The DEPARTMENT_CHALLENGE cohort is not used to estimate population prevalence. It stress-tests transport across departments. At target 0.60, a supported department must have >=5 evaluated products. A positive department must have >=20% selective coverage and >=10pp accuracy gain versus BASE_B1_ALL. At least four departments and >=2/3 positive fraction are required for department confirmation.

## Evidence ceiling
A successful result may be called `CONFIRMED_WITHIN_PANEL_CROSS_PRODUCT`. It must not be called external validation.

## Fail closed
Stop on candidate-universe mismatch, prior-100 reconstruction mismatch, source identity change, core code/config identity change during resume, overlap between cohorts, use of future outcomes in selection, or any frozen-rule mismatch.
