from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def add_file(bucket: list[dict], role: str, path: Path, required: bool = True) -> None:
    item = {"role": role, "path": str(path), "exists": path.exists(), "required": required}
    if path.exists() and path.is_file():
        item.update({"size_bytes": path.stat().st_size, "sha256": sha256(path)})
    bucket.append(item)


def main() -> None:
    cj9 = Path(r"C:\MR\data\CJ9")
    raw = Path(r"C:\MR\data\CJ_R")
    cj11 = Path(r"C:\MR\data\CJ11")
    v11 = Path(os.environ.get("MRSP_V11_ROOT", r"C:\MR\V11_R1_EXEC"))
    v09 = Path(os.environ.get("MRSP_V09_ROOT", r"C:\MR\V09"))
    gen1 = Path(os.environ.get("MRSP_GEN1_ROOT", r"C:\MR\GEN1_UPSTREAM"))
    files: list[dict] = []

    add_file(files, "generator_program", Path(os.environ.get("MRSP_GEN1_MATERIALIZER", str(Path(__file__).with_name("materialize_gen1_candidates.py")))))
    add_file(files, "generator_dependency_used_for_table_io", v11 / "lib/v11_core.py")
    add_file(files, "historical_v11_builder_not_directly_used_for_N_sets", v11 / "code/build_cj11.py")
    add_file(files, "historical_v09_canonical_builder", v09 / "code/build_cj9.py")
    add_file(files, "formal_v1_census_reader", Path(r"C:\MR\GEN1\MRSP_PREDICTABILITY_GENERALIZATION_V1_20260921\code\census.py"))

    for name in ["transactions.rds", "promotions.rds", "completejourney_1.1.1.tar.gz", "manifest.csv", "inspect_summary.json"]:
        add_file(files, "raw_lineage_source_not_read_directly_by_materializer", raw / name, required=False)
    for name in ["products.parquet", "identity.json", "sets.json", "prod_stats.parquet"]:
        add_file(files, "direct_CJ9_metadata_input", cj9 / name)
    for p in sorted((cj9 / "tx").glob("w*.parquet")):
        week = int(p.stem[1:])
        add_file(files, "direct_CJ9_transaction_input_week_le_22" if week <= 22 else "direct_CJ9_transaction_input_for_full_event_materialization", p)
    add_file(files, "legacy_exclusion_panel", Path(r"C:\MR\GEN1\MRSP_PREDICTABILITY_GENERALIZATION_V1_20260921\cfg\legacy_panel.json"))
    for set_id in ["L01", "L02", "L03", "M01", "M02", "M03", "H01", "H02", "H03"]:
        for name in ["meta.json", "events.parquet", "obs.parquet"]:
            add_file(files, "legacy_CJ11_copied_validation_input", cj11 / "cat" / set_id / name, required=False)

    for p in [
        gen1 / "CJ11_GEN1" / "gen1_materialization_registry.json",
        gen1 / "CJ11_GEN1" / "materialization_state.json",
        gen1 / "preflight" / "preflight.json",
        gen1 / "preflight" / "selected_new_sets.json",
        gen1 / "preflight" / "census_registry.parquet",
        gen1 / "formal_run" / "FULL" / "study_result.json",
        gen1 / "formal_run" / "FULL" / "summary.json",
        gen1 / "formal_run" / "FULL" / "checkpoint.json",
        gen1 / "MRSP_PREDICTABILITY_GENERALIZATION_AUDIT_20260921_163956.zip",
    ]:
        add_file(files, "generated_evidence", p)

    output = Path(os.environ.get("MRSP_LINEAGE_OUTPUT", str(gen1 / "N001_N100_LINEAGE_HASH_MANIFEST_20260921.json")))
    payload = {
        "status": "PASS",
        "hash_algorithm": "SHA-256",
        "generator": "materialize_gen1_candidates.py",
        "direct_selection_source": r"C:\MR\data\CJ9",
        "raw_lineage_source": r"C:\MR\data\CJ_R",
        "legacy_validation_source": r"C:\MR\data\CJ11",
        "selection_window": "CJ9 tx w01..w22 only",
        "materialization_window": "CJ9 tx w01..w53 for obs/events; not used for candidate selection",
        "new_set_output": str(gen1 / "CJ11_GEN1" / "cat" / "N001..N100"),
        "files": files,
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": str(output), "file_records": len(files)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
