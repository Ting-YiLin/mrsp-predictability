# Spec-to-Code Review

Every hard scientific rule is mapped in `SPEC_TRACE.csv` to an implementation file and an auditable output. `tools/spec_trace_check.py` verifies both file existence and required implementation anchors before release.

Key traces:
- Frozen P1/B0/B1 byte hashes -> `cfg/frozen_core_hashes.json` -> `test/test_frozen_rules.py`.
- Frozen cutoffs -> `cfg/frozen_p1_cutoffs.json` -> direct read in `code/run_confirmatory.py` -> output policy tables.
- Prior 100 exclusion -> `cfg/frozen_gen1_selected.json` -> `select_confirmatory()` -> preflight `no_prior_overlap`.
- Week<=22 selection -> `build_candidate_pool()` -> preflight `future_outcome_free_selection`.
- Disjoint cohorts -> `select_confirmatory()` -> preflight `selected_unique/no_prior_overlap` and result assertion.
- No B2/learned gate -> no imports/calls and final spec assertions.
