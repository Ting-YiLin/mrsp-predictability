# MRSP Upstream Source Recon — 2026-09-21

Status: COMPLETE_SAFE_TO_PAUSE

This is a read-only upstream-source reconnaissance record. No new MRSP generalization batch was started, no existing failure bundle was modified, and no scientific rule was changed.

## Findings

- Raw source: `C:\MR\data\CJ_R`
  - `transactions.rds`: 1,469,307 rows, weeks 1–53, 2,469 households, 68,509 products.
  - `promotions.rds`: 20,940,529 rows.
  - `completejourney_1.1.1.tar.gz`: product metadata source.
- Canonical source store: `C:\MR\data\CJ9`.
- Replan source store: `C:\MR\data\CJ9_REPLAN`.
- V0.11 product store: `C:\MR\data\CJ11`.

## Authoritative builders

- V0.9 predecessor: `<LOCAL_MRSP_V09_ROOT>`
  - `code\build_cj9.py` creates canonical transactions, product metadata, six-product category proxies, events, observations, and promotions.
  - `w\code\build_replan_sets.py` excludes prior selected groups and created `R01` and `R02` in the work copy.
- Latest complete builder execution artifact: `<LOCAL_MRSP_V11_R1_ROOT>`
  - `code\build_cj11.py` reuses CJ9 transaction partitions and writes `cat\<SET_ID>` outputs.
  - Builder SHA-256: `6d54ebde8d3853cbb3c79e76c1f06af2293492917e26963a869beb76879a0b90`.
  - Its recorded `qualified_sets` is 107, while its selected/materialized development panel is 9 sets.

## Actual data flow

`CJ_R raw RDS/tar` → V0.9 `build_cj9.py` → `CJ9 products.parquet + tx/w01..w53` → V0.9 replan builder / V0.11 `build_cj11.py` → `cat\<SET_ID>\meta.json + events + obs + promo`.

The current V1 Census only scans existing `cat` directories. It does not discover raw product-type groups directly from CJ9. Therefore `n_eligible_before_cap=0` means no eligible new groups were materialized under the three configured cat roots; it does not mean the upstream product universe is empty.

## Read-only pre-22 availability check

Using CJ9 weeks 1–22, six top-supported products per metadata group, single-product basket events, at least 120 events, at least 25 households, legacy name/tuple exclusion, GAS/FUEL exclusion, and metadata name/Jaccard de-duplication:

- pre-22 transaction rows inspected: 594,831
- candidate groups after those checks: 507
- Jaccard/name duplicates removed: 0

This is a source-availability recon count, not a formal V1 Census result, and no candidate groups were written to `cat`.

## Search record

Checked current project task records for Action Map, Frontier, Confidence, and Event Ledger work, plus relevant handoff conversations. Checked MRSP packages including PHCM, PPF W1/W2A/W2B, V10, V11/V11R1, Predictability Frontier, Action Map, and Generalization. Checked `C:\MR\CONF1`, `PRED1`, `ROLL2`, `GEN1`, and the four CJ data roots.

`MRSP_MASTER_HANDOFF_20260917.zip` was not found at the searched Downloads or `C:\MR` locations. The V09/V11 builder artifacts and their manifests/handoffs provide the operative upstream evidence.

## Pause boundary

Safe to pause. The continuation work unit completed upstream materialization and the existing V1 Census/preflight only; it did not start W3-W6 evaluation, policy computation, `run_study.py`, or `go.bat`.

## Continuation result: isolated Gen1 materialization and preflight

- Materializer used: `materialize_gen1_candidates.py`.
- Isolated output: `MRSP_GEN1_UPSTREAM_20260921/CJ11_GEN1/cat`.
- Output contains 100 new sets `N001`–`N100` and 9 copied legacy validation sets.
- Existing V1 preflight against the isolated `cj11` root: `PASS`.
- `n_selected_new_sets = 100`; `n_eligible_before_cap = 100`.
- Structural checks all passed: legacy validity, legacy primary/control composition, unique selected keys, no legacy overlap, cap respect, and future-outcome-free selection.
- Selection used only the pre-22 upstream support/materialization logic and fixed stable ordering; no W3-W6 outcome was used.
- The original V1 package and its failure bundle were not modified. Scientific rules were not modified.

Saved verification artifacts:

- `MRSP_GEN1_UPSTREAM_20260921/CJ11_GEN1/gen1_materialization_registry.json`
- `MRSP_GEN1_UPSTREAM_20260921/CJ11_GEN1/materialization_state.json`
- `MRSP_GEN1_UPSTREAM_20260921/preflight/preflight.json`
- `MRSP_GEN1_UPSTREAM_20260921/preflight/selected_new_sets.json`
- `MRSP_GEN1_UPSTREAM_20260921/preflight/census_registry.parquet`

Pause boundary: HOLD before formal generalization. Do not start a new formal batch automatically; the next authorized step is to run the existing V1 study using the isolated root overrides.

## Formal V1 continuation result

- Existing V1 tests, spec trace, and preflight passed. The original `test_census.py` needed only an isolated pandas 3 test-harness compatibility copy because pandas 3 rejects its integer-to-string synthetic mutation; the V1 package source and rules remained unchanged.
- Existing `code/run_study.py` processed all 100 new sets product-by-product and returned `RUN_PASS EXPLORATORY_SUPPORT`.
- The formal result contains 52,854 new evaluation events; summary breadth is `CONFIRMATORY_BREADTH`, with generalization grade `EXPLORATORY_SUPPORT`.
- Release result: `execution_status = RUN_PASS`, `semantic_status = SEMANTIC_PASS`.
- Spec assertions passed: no legacy sets in primary evidence, no future-outcome selection, and no B2.
- The audit pack was created with the existing package-audit contents in the writable workspace and ZIP integrity verification passed.
- Audit ZIP: `MRSP_PREDICTABILITY_GENERALIZATION_AUDIT_20260921_163956.zip`.

## Why the policy summary has 99 products

The Census selected and the checkpoint processed 100 logical new products. The policy summary counts products with W3-W6 evaluation rows, not merely Census eligibility. Logical `N014` maps to materialized source set `N010` after the V1 Census re-enumerates the materialized sets by its own stable registry order. `N010` is `SEASONAL CANDY BAGS-CHOCOLATE`; its six products had 226 pre-22 events and 181 households, but all 226 materialized events are in weeks 8–18 and it has zero week>=23 events. Therefore it is correctly absent from `new_event_panel.parquet` and every policy summary has `n_products=99`. It was not dropped by the Census, checkpoint, or an execution failure.

The machine-readable evidence is `N014_POLICY_SUMMARY_RECON_20260921.json`.

Lineage and SHA-256 records are in `N001_N100_LINEAGE_HASH_MANIFEST_20260921.json`. It records 104 source/program/output file records, including all CJ9 transaction partitions, raw CJ_R lineage files, the generator, V11/V09 builder lineage, the legacy exclusion panel, and formal outputs.

Final pause boundary: HOLD after audit package. No further batch is pending automatically.
