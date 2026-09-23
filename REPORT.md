# Predictability Before Prediction: A Selective-Prediction Framework for Household Product Choice

## Abstract

Most product-choice work asks how to maximize predictive accuracy over every event. This project reached a different conclusion: a large part of practical performance comes from deciding **which household × product events are predictable enough to answer at all**. We study a conditional six-alternative choice task in the Complete Journey data ecosystem. A market-prior model (B0) and a household-history model (B1) were developed first; household history increased pooled forward-test accuracy from 37.28% to 64.53% across 17,408 development events. A more complex behavior-fusion model (B2) improved accuracy only modestly and did not clear a predeclared practical-complexity threshold. The project therefore shifted to pre-outcome predictability ranking.

We define P1, a fixed household-stability score using history maturity, concentration, entropy, switching, and recent concentration. After development, both the P1 formula and three cutoffs were frozen. In a first 100-product generalization batch, P1 achieved 76.18% accuracy at 39.16% coverage, 83.55% at 21.49%, and 88.14% at 11.50%. In a second untouched representative batch (99 evaluable products; 40,474 events), the same frozen rule reproduced 77.17% accuracy at 41.08% coverage, 84.78% at 22.00%, and 90.06% at 11.01%. A separate department-challenge cohort produced 79.33% accuracy at 40.22% coverage versus 61.18% for B1 on all events. The evidence supports a simple selective-prediction architecture: use pre-event household stability to decide whether to make a conditional SKU-choice prediction, and abstain when the historical signal is weak.

## 1. Research question

The final research question is not “What is the most complex model that predicts product choice best?” It is:

> **Can we identify, before the outcome, which household × product purchase events contain enough stable historical structure to justify a prediction?**

The task is conditional choice. Each event belongs to a fixed six-SKU choice set. The target is the SKU chosen on the current purchase. Purchase incidence and full next-basket prediction are separate future tasks.

## 2. Development path

### 2.1 Fixing the problem definition before optimizing models

Several early experiments produced apparently strong signals but later failed semantic review. Examples included row-order state without reliable timestamps, heterogeneous choice sets, prior discontinuities, an off-by-one cohort definition, and pooled context effects dominated by one product set. These failures led to a governance rule: a model result is not retained unless its labels, temporal order, choice set and comparison baseline survive adversarial review.

### 2.2 Household history becomes the main predictor

On the 9-product development panel, two forward test windows contained 17,408 events. Pooled results were:

| Model | Accuracy |
|---|---:|
| B0 — market prior | 37.28% |
| B1 — household history | 64.53% |
| B2 — behavior fusion | 65.52% |

The B1–B0 difference was about +27.25 percentage points. This established household-specific history as the dominant increment over the market baseline.

### 2.3 Complexity does not earn its cost

B2 starts from B1 and adds recent behavior: last choice, repeat streak, recent choice shares and elapsed time since prior choices. In a later practical-value study across 26,659 nonzero-history events, B2 exceeded B1 by about +1.26 points. Household- and week-cluster bootstrap intervals remained positive, suggesting that the increment was real. However, the project had predeclared that a more complex model needed at least a 3-point practical improvement to become the default. B1 therefore remained the public predictor.

### 2.4 The research question shifts from “which model?” to “which events?”

Learned routing, switch specialists, cold-start rescue and several other complex strategies did not produce a stable practical upgrade. At the same time, forward tests repeatedly showed that some events were much easier than others. This motivated selective prediction.

## 3. Models and score

### 3.1 B0 — market prior

For household `h`, event `t` and alternative `j`:

```text
other_count_j = max(global_count_j_before_t - household_count_hj_before_t, 0) + 1
B0_j = other_count_j / sum_l(other_count_l)
```

The household’s own counts are excluded from B0. The +1 term is smoothing.

### 3.2 B1 — household history

```text
x_j  = lambda_bin * B0_j + household_count_hj_before_t
B1_j = x_j / sum_l(x_l)
```

`lambda_bin` is selected only from past FIT/TUNE data for three history-maturity bins: `0–2`, `3–9`, and `10+` prior purchases.

### 3.3 P1 — household stability

```text
maturity = clip(log(1+k) / log(21), 0, 1)

core = 0.30*top_share
     + 0.25*(1-normalized_entropy)
     + 0.25*(1-switch_rate)
     + 0.20*recent_concentration

P1 = clip(maturity * core, 0, 1)
```

Every component is pre-event. P1 has no fitted coefficients.

Frozen cutoffs were calibrated before the new-product batches and then kept fixed:

| Label | P1 cutoff |
|---|---:|
| 0.60 | 0.3608488067 |
| 0.70 | 0.5231119438 |
| 0.80 | 0.6660270792 |

The labels are names for operating points, not promises that future accuracy equals 60%, 70% or 80%.

## 4. Evaluation design

The final confirmatory evaluation uses six walk-forward blocks. New-product evidence is evaluated in W3–W6. The candidate universe is built from week≤22 information only. The first new-product batch is excluded from the second-batch selection using frozen stable keys. The second representative batch and the department-challenge batch are disjoint. W3–W6 outcomes are evaluation-only.

The second-batch package explicitly forbids P1 recalibration, B2, learned gates, future-outcome candidate selection and reuse of the first-batch product groups.

## 5. Results

### 5.1 First new-product batch

100 product groups were selected; 99 had W3–W6 evaluation events, totaling 52,854 events.

| Frozen operating point | Coverage | Accuracy |
|---|---:|---:|
| 0.60 | 39.16% | 76.18% |
| 0.70 | 21.49% | 83.55% |
| 0.80 | 11.50% | 88.14% |

### 5.2 Second untouched confirmatory batch

The second representative batch selected another 100 product groups; 99 were evaluable, with 40,474 events.

| Frozen operating point | Coverage | Accuracy |
|---|---:|---:|
| 0.60 | **41.08%** | **77.17%** |
| 0.70 | **22.00%** | **84.78%** |
| 0.80 | **11.01%** | **90.06%** |

The close replication of both coverage and accuracy is the main confirmatory result.

### 5.3 Breadth across products

For the confirmatory representative cohort:

- at the 0.60 operating point, 97 products were active and 93 (95.9%) met the target rule;
- at 0.70, 77 were active and 74 (96.1%) met the target rule;
- at 0.80, 34 were active and 32 (94.1%) met the target rule.

Thus the pooled result was not produced by only a few large product groups.

### 5.4 Department challenge

The deliberately non-Grocery-heavy cohort contained 99 evaluable products and 36,027 events. At the frozen 0.60 cutoff:

- B1 on all events: 61.18%
- P1-selective B1: 79.33%
- coverage: 40.22%
- selective gain: +18.15 points

Seven departments had at least five products. Six passed the predeclared ≥10-point gain criterion. Produce improved from 80.19% to 88.81% (+8.62 points), which was directionally positive but below the strict threshold.

### 5.5 Secondary simple action policy

A secondary policy can use B0 when market-level prediction is already sufficient and B1 when personalization has value. On the second representative cohort:

| Operating point | Coverage | Accuracy |
|---|---:|---:|
| 0.60 | 56.60% | 70.87% |
| 0.70 | 29.04% | 80.76% |
| 0.80 | 14.95% | 85.11% |

This is a productization result, not the primary scientific claim.

## 6. What failed and why it matters

The final simple architecture emerged after rejecting multiple attractive but unstable paths. The public failure history includes: invalid timestamp interpretations, choice-set definition errors, an off-by-one cohort bug, context effects driven by a single set, routers that failed to beat simpler baselines, hard-case rescue that hurt performance, unreliable short-window model selection, a control-isolation bug later repaired, and an initial false assumption that dozens of new materialized product groups already existed locally.

Preserving these failures matters because the final result is not a retrospective search for the prettiest score. Key complex alternatives were explicitly tested and discarded.

## 7. Interpretation

The evidence supports three practical statements:

1. household history contains much more product-choice information than a market prior;
2. predictability is heterogeneous across household × product events and can be ranked before the outcome;
3. abstention converts that heterogeneity into a stable coverage–accuracy frontier that reproduced on a second untouched product batch.

The result does **not** mean that a household itself is globally “predictable” or “random.” The unit of decision is a household × product purchase event, and the task remains conditional six-choice prediction.

## 8. Evidence scope and limitations

The strongest grade is `CONFIRMED_WITHIN_PANEL_CROSS_PRODUCT`: the frozen rule reproduced across new products and departments inside the same Complete Journey data ecosystem. No claim is made here about purchase incidence, next-basket prediction, or guaranteed transport to a different retailer or consumer panel. The choice sets are observed substitute proxies, not a formal model of real-time shelf availability.

Raw data are not redistributed in this release pending a final data-license audit.

## 9. Reproducibility

The repository includes:

- exact frozen confirmatory code and configuration;
- frozen first-batch selection keys;
- predeclared success rules;
- released machine summaries;
- source-artifact hashes and evidence ledger;
- a no-data verification script;
- a full reproduction wrapper for users with the same canonical CJ9 source store.

See `docs/reproducibility.md`.

## 10. Next research question

The current task conditions on a purchase occurring in a product category. The next meaningful extension is a two-stage system: first predict purchase incidence (next trip / next seven days), then conditionally predict which SKU will be selected. That extension is outside the evidence claims of this release.
