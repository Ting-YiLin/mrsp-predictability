# Aggregate output schema

The JSON output contains:

- protocol/version and execution status;
- explicit `scientific_interpretation = UNASSESSED_REQUIRES_HUMAN_REVIEW`;
- SHA-256 hashes for `events.csv`, `groups.csv`, and the runner;
- frozen protocol values (six choices, 53 weeks, W3-W6, lambda grid, P1 cutoffs);
- overall B0/B1 accuracy;
- selective B1 coverage/accuracy for the 0.6/0.7/0.8 frozen P1 cutoffs;
- optional department-level aggregate summaries;
- failure diagnostics;
- privacy assertions.

It never contains `household_id`, `event_id`, or event-level prediction rows.
