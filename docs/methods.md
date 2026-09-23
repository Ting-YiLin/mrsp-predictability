# Methods

## Unit of prediction

Each row is a purchase event from a fixed six-SKU choice set. The response `y∈{0,…,5}` is the chosen SKU index. Features are generated sequentially: the feature row is created first, and only then is the current observed choice allowed to update state.

## B0 — market prior

For household `h`, event `t`, alternative `j`:

```text
other_count_j = max(global_count_j_before_t - household_count_hj_before_t, 0) + 1
B0_j = other_count_j / Σ_l other_count_l
```

B0 excludes the current household’s own counts from the market counts.

## B1 — household history

```text
x_j  = lambda_bin * B0_j + household_count_hj_before_t
B1_j = x_j / Σ_l x_l
```

The shrinkage `lambda_bin` is tuned using only prior FIT/TUNE windows in three bins: `0–2`, `3–9`, `10+` prior household purchases in the choice set.

## B2 — behavior fusion, retained only as a development comparator

B2 begins with B1 probabilities and adds an alternative-specific log-probability offset using recent-behavior features: last choice, repeat streak, recent choice share and exponential elapsed-time recency. It showed a small average gain but did not become the public default.

## P1 — household stability

```text
maturity(k) = clip(log(1+k)/log(21), 0, 1)
core = 0.30*top_share + 0.25*(1-normalized_entropy) + 0.25*(1-switch_rate) + 0.20*recent_concentration
P1 = clip(maturity * core, 0, 1)
```

Definitions:

- `top_share`: largest historical alternative share for the household in the choice set;
- `normalized_entropy`: `-Σ p_j log(p_j)/log(6)`;
- `switch_rate`: fraction of adjacent historical purchases in which the chosen alternative changed;
- `recent_concentration`: largest share among the most recent up-to-five choices;
- `k`: number of prior purchases in the current choice set.

## Frozen P1 operating points

| Label | Cutoff | Historical calibration coverage | Historical calibration accuracy |
|---|---:|---:|---:|
| 0.60 | 0.3608488067 | 64.07% | 69.06% |
| 0.70 | 0.5231119438 | 40.00% | 76.96% |
| 0.80 | 0.6660270792 | 20.01% | 86.93% |

The labels are not future guarantees. They identify frozen operating points.

## Walk-forward blocks

| Block | FIT through | TUNE | EVAL |
|---|---:|---|---|
| W1 | 17 | 18–22 | 23–27 |
| W2 | 22 | 23–27 | 28–32 |
| W3 | 27 | 28–32 | 33–37 |
| W4 | 32 | 33–37 | 38–42 |
| W5 | 37 | 38–42 | 43–47 |
| W6 | 42 | 43–47 | 48–53 |

New-product confirmatory evidence uses W3–W6.

## New-product universe and outcome blindness

The canonical CJ9 store contains product metadata and week-partitioned transactions. Candidate product groups are built from weeks 1–22 only:

1. group by `product_type`;
2. keep six highest-supported products per group;
3. keep single-product basket events;
4. require at least 120 pre-22 events and 25 households;
5. remove legacy development groups, GAS/FUEL terms, duplicate names and high-overlap groups;
6. assign stable hashes.

This generated 507 eligible candidates. The first 100 were frozen before their future evaluation. The confirmatory package reconstructs those stable keys, excludes them, then selects a separate representative batch and a separate department-challenge batch without using W3–W6 outcomes.

## Primary selective policy

For cutoff `c`:

```text
if P1 >= c: predict with B1
else:       ABSTAIN
```

`Coverage = accepted events / all evaluable events`.

`Accuracy = correct accepted predictions / accepted events`.

## Evidence grade

The confirmatory package returns `CONFIRMED_WITHIN_PANEL_CROSS_PRODUCT` only when the predeclared representative, department-breadth and secondary simple-action checks pass.
