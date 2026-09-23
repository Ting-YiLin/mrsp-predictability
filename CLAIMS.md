# Public Claim Sheet

The public release is limited to the approved claims below.

## Approved claims

### C1 — Task definition
This project studies **conditional six-alternative product choice**: given that a household makes a purchase within a fixed six-SKU choice set, predict which SKU is chosen.

### C2 — Household history is the dominant predictive increment in development
Across 17,408 forward-test events in the original 9-product development panel, B0 market prior achieved 37.28% accuracy, B1 household history 64.53%, and B2 behavior fusion 65.52%. B1 improved over B0 by about 27.25 percentage points.

### C3 — Small complexity gains do not automatically justify a more complex model
Across 26,659 nonzero-history events, B2 improved over B1 by about 1.26 percentage points and the direction was stable under household- and week-cluster bootstrap. Because this was below the predeclared 3-point practical-complexity threshold, the public system keeps B1 as the simple predictor.

### C4 — A simple pre-outcome score can identify more predictable events
P1 uses only pre-event history maturity, household choice concentration, historical entropy, switching rate, and recent choice concentration. It has no learned parameters and no product-specific fitted weights.

### C5 — First new-product generalization batch
In a first batch of 100 new product groups (99 evaluable), the frozen P1 gate achieved approximately:
- 39.16% coverage → 76.18% accuracy
- 21.49% coverage → 83.55% accuracy
- 11.50% coverage → 88.14% accuracy

### C6 — Untouched confirmatory replication
In a second, non-overlapping 100-product representative batch (99 evaluable; 40,474 events), with P1 formula, cutoffs, B0/B1 and time windows frozen:
- 41.08% coverage → 77.17% accuracy
- 22.00% coverage → 84.78% accuracy
- 11.01% coverage → 90.06% accuracy

The release grade is **CONFIRMED_WITHIN_PANEL_CROSS_PRODUCT**.

### C7 — Cross-department stress test
In a separate 100-product department-challenge cohort (99 evaluable; 36,027 events), the frozen 60-target P1 cutoff achieved 40.22% coverage and 79.33% accuracy, versus 61.18% for B1 on all events. Among seven departments with at least five evaluated products, six met the predeclared ≥10-point selective-gain criterion; Produce improved by 8.62 points and therefore remained directionally positive but below the strict threshold.

### C8 — Abstention is part of the system
The model is not required to answer every event. Low-P1 events can be marked **ABSTAIN**, and the coverage–accuracy frontier is a primary system output.

## Required wording boundaries

### R1
Do not describe these results as predicting whether a customer will buy bread, milk, or another category next. Purchase incidence has not yet been tested in this release.

### R2
Do not describe the task as next-basket prediction. The current task is conditional six-choice SKU selection.

### R3
Do not write “40% of customers reach 77% accuracy.” Coverage is the fraction of **evaluable household × product purchase events**, not the fraction of unique customers.

### R6 — What B2 means
Do not say “B2 has no information value.” **B2 is a behavior-fusion model: it starts from B1 household-history probabilities and adds recent-behavior features such as the last choice, streak, recent choice shares, and time since prior choices.** Its average gain over B1 appears real but did not clear the predeclared practical-complexity threshold.
