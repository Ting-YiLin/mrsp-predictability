# Scientific Logic Red Team

## Verdict after round 1
PASS AFTER REPAIR.

## Findings and repairs
1. **Prior-product reuse risk.** A second batch is invalid if any Gen1 N001-N100 candidate reappears. Repair: reconstruct the full 507-candidate universe, reproduce the frozen prior 100 stable keys exactly, then exclude them mechanically.
2. **Representative vs department-stress estimand conflict.** A department-balanced sample cannot also be treated as a prevalence estimate. Repair: two disjoint cohorts. REPRESENTATIVE is the primary replication cohort; DEPARTMENT_CHALLENGE is a transfer stress test only.
3. **Post-result cutoff tuning risk.** Repair: P1 cutoffs are stored in a frozen config and `run_confirmatory.py` has no cutoff-training function.
4. **Future-outcome selection leakage.** Repair: candidate pool builder reads weeks 1-22 only; W3-W6 outcome fields are absent from selection code.
5. **Current-block action leakage.** GLOBAL_SIMPLE_ACTION uses only accumulated prior blocks. Current block is evaluated after the action is frozen.
6. **Temporal attrition.** A pre-22-qualified product can disappear later. Repair: keep it selected, report selected vs evaluated counts, never replace it after seeing future availability.
7. **Large-product dominance.** Repair: primary event-weighted summaries are accompanied by product summaries and product-level bootstrap intervals.
8. **Department challenge cherry-picking.** Repair: fixed salted hashes, deterministic department order, fixed caps; no outcome-aware department inclusion.
9. **Source drift.** Repair: preflight reconstructs the expected 507-candidate universe and exact prior-100 identity; materialized outputs and all CJ9 source partitions are hashed for resume identity.
10. **Complexity creep.** B2, learned gates, local cutoff optimization, and new model families are forbidden.
