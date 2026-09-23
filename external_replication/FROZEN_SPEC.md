# Frozen strict external-test specification

## Purpose

This kit tests transport to an independent retailer or consumer-panel environment while preserving the already-frozen MRSP V1 selective rule. A successful program run is **not by itself** a scientific confirmation; independence, pre-freezing, data provenance, and result interpretation still require human review.

## Frozen model construction

For each six-SKU group and event, the runner rebuilds the original pre-event state. B1 is the household-history distribution smoothed by the market prior excluding that household. The B1 smoothing parameter is selected separately for the maturity bins `0_2`, `3_9`, `10_plus` using only each walk-forward block's TUNE interval and the fixed lambda grid:

```text
[0.5, 1, 2, 3, 5, 8, 12, 20, 40]
```

The frozen W1-W6 clock is identical to the confirmatory release; external reporting uses W3-W6 evaluation events.

## Frozen P1

```text
maturity = clip(log(1 + prior_count) / log(21), 0, 1)
core = 0.30*top_share + 0.25*(1-normalized_entropy)
     + 0.25*(1-switch_rate) + 0.20*recent_concentration
P1 = clip(maturity * core, 0, 1)
```

Frozen P1 cutoffs:

- 0.6 target: `0.3608488067145302`
- 0.7 target: `0.5231119438280639`
- 0.8 target: `0.6660270791857679`

At each cutoff, `P1 >= cutoff` uses B1; otherwise the policy returns `ABSTAIN`. No B2, learned gate, exception rule, or P1 recalibration is permitted.

## Zero-shot boundary

The 53-week observation window, group definitions, inclusion rule, and input files must be frozen before evaluation outcomes are examined. Failed first runs are retained. If Retailer A is used to alter any rule, A becomes development/adaptation data and independent validation requires a newly frozen test on Retailer B/C.

## Privacy and output

The runner writes aggregate statistics only. It records SHA-256 hashes of the two input files and its own runner, but no household IDs or event-level rows.
