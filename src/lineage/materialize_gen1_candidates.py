from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import os
from pathlib import Path

import pandas as pd

V11_ROOT = Path(os.environ.get("MRSP_V11_ROOT", r"C:\MR\V11_R1_EXEC"))
if str(V11_ROOT) not in sys.path:
    sys.path.insert(0, str(V11_ROOT))

from lib.v11_core import read_table, write_table  # noqa: E402


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def atomic_json(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    json.loads(tmp.read_text(encoding="utf-8"))
    tmp.replace(path)


def load_legacy(panel_path: Path) -> tuple[set[str], set[tuple[str, ...]]]:
    panel = json.loads(panel_path.read_text(encoding="utf-8-sig"))
    sets = panel["primary_sets"] + panel["control_sets"]
    names = {str(x["group_name"]).strip().casefold() for x in sets}
    tuples = {tuple(map(str, x["candidate_products"])) for x in sets}
    return names, tuples


def read_weeks(cj9: Path, weeks: range, columns: list[str]) -> pd.DataFrame:
    frames = []
    for week in weeks:
        frames.append(read_table(cj9 / "tx" / f"w{week:02d}", columns=columns))
    out = pd.concat(frames, ignore_index=True)
    for col in ["household_id", "basket_id", "product_id"]:
        out[col] = out[col].astype(str)
    return out


def candidate_pool(cj9: Path, legacy_panel: Path) -> tuple[list[dict], dict]:
    products = read_table(cj9 / "products")
    products["product_id"] = products["product_id"].astype(str)
    products["product_type"] = products["product_type"].fillna("").astype(str)
    products["department"] = products["department"].fillna("").astype(str)
    products = products.drop_duplicates("product_id")
    tx = read_weeks(cj9, range(1, 23), ["household_id", "basket_id", "product_id", "week"])
    support = tx.groupby("product_id").size().rename("pre_support")
    meta = products[products.product_type != ""].merge(
        support, left_on="product_id", right_index=True, how="left"
    ).fillna({"pre_support": 0})
    meta = meta.sort_values(
        ["product_type", "pre_support", "product_id"], ascending=[True, False, True]
    )
    top = meta.groupby("product_type", sort=True).head(6)
    valid = top.groupby("product_type").size()
    top = top[top.product_type.isin(valid[valid == 6].index)]
    joined = tx.merge(top[["product_id", "product_type"]], on="product_id", how="inner")
    basket_products = joined.groupby(["product_type", "basket_id"]).product_id.nunique()
    single_keys = basket_products[basket_products == 1].reset_index()[["product_type", "basket_id"]]
    single = joined.merge(single_keys, on=["product_type", "basket_id"], how="inner")
    single = single.drop_duplicates(["product_type", "basket_id"])
    counts = single.groupby("product_type").agg(
        events_pre22=("basket_id", "nunique"), households_pre22=("household_id", "nunique")
    )
    legacy_names, legacy_tuples = load_legacy(legacy_panel)
    raw = []
    for group_name, row in counts.iterrows():
        if int(row.events_pre22) < 120 or int(row.households_pre22) < 25:
            continue
        name = str(group_name)
        if "GAS" in name.upper() or "FUEL" in name.upper():
            continue
        group = top[top.product_type == name].sort_values(
            ["pre_support", "product_id"], ascending=[False, True]
        )
        pids = group.product_id.astype(str).tolist()
        if name.strip().casefold() in legacy_names or tuple(pids) in legacy_tuples:
            continue
        department_mode = group.department.mode()
        department = str(department_mode.iat[0]) if len(department_mode) else ""
        raw.append(
            {
                "group_name": name,
                "department": department,
                "candidate_products": pids,
                "events_pre22": int(row.events_pre22),
                "households_pre22": int(row.households_pre22),
                "raw_stable_key": sha256_text("|".join(["cj11", name, *pids])),
            }
        )
    raw.sort(key=lambda x: x["raw_stable_key"])
    keep = []
    duplicate_count = 0
    for item in raw:
        products_set = set(item["candidate_products"])
        name_key = item["group_name"].strip().casefold()
        duplicate = False
        for prior in keep:
            prior_set = set(prior["candidate_products"])
            jac = len(products_set & prior_set) / max(len(products_set | prior_set), 1)
            if name_key == prior["group_name"].strip().casefold() or jac >= 0.50:
                duplicate = True
                break
        if duplicate:
            duplicate_count += 1
        else:
            keep.append(item)
    for index, item in enumerate(keep, start=1):
        item["candidate_source_set"] = f"POOL{index:03d}"
        item["stable_key"] = sha256_text(
            "|".join(["cj11", item["candidate_source_set"], *item["candidate_products"]])
        )
    selected = sorted(keep, key=lambda x: x["stable_key"])[:100]
    for index, item in enumerate(selected, start=1):
        item["set_id"] = f"N{index:03d}"
    summary = {
        "pre22_transaction_rows": int(len(tx)),
        "candidate_groups_after_support_legacy_and_gasfuel": len(raw),
        "metadata_duplicates_removed": duplicate_count,
        "candidate_pool_after_dedup": len(keep),
        "selected_new_sets": len(selected),
        "selection_rule": "stable SHA-256 order; cap 100; no outcome fields used",
    }
    return selected, {"summary": summary, "all_pool_count": len(keep)}


def materialize(cj9: Path, raw_root: Path, legacy_cj11: Path, legacy_panel: Path, out: Path) -> dict:
    selected, pool_info = candidate_pool(cj9, legacy_panel)
    out.mkdir(parents=True, exist_ok=True)
    catroot = out / "cat"
    catroot.mkdir(parents=True, exist_ok=True)
    for set_id in ["L01", "L02", "L03", "M01", "M02", "M03", "H01", "H02", "H03"]:
        src = legacy_cj11 / "cat" / set_id
        dst = catroot / set_id
        if src.exists() and not dst.exists():
            shutil.copytree(src, dst)
    all_products = {p for item in selected for p in item["candidate_products"]}
    cols = [
        "household_id", "store_id", "basket_id", "product_id", "quantity", "sales_value",
        "retail_disc", "coupon_disc", "coupon_match_disc", "week", "transaction_timestamp",
        "net_price", "gross_proxy",
    ]
    alltx = read_weeks(cj9, range(1, 54), cols)
    alltx = alltx[alltx.product_id.isin(all_products)].copy()
    products = read_table(cj9 / "products")
    products["product_id"] = products["product_id"].astype(str)
    product_meta = products.set_index("product_id").to_dict(orient="index")
    for item in selected:
        set_id = item["set_id"]
        pids = item["candidate_products"]
        idx = {pid: i for i, pid in enumerate(pids)}
        obs = alltx[alltx.product_id.isin(pids)].copy()
        obs["choice_idx"] = obs.product_id.map(idx).astype("int16")
        basket_n = obs.groupby("basket_id").product_id.nunique()
        single = set(basket_n[basket_n == 1].index.astype(str))
        multi = set(basket_n[basket_n > 1].index.astype(str))
        events = obs[obs.basket_id.astype(str).isin(single)].sort_values(
            ["transaction_timestamp", "basket_id"], kind="mergesort"
        ).drop_duplicates("basket_id", keep="first")
        events = events.copy()
        events["event_id"] = set_id + "_" + events.basket_id.astype(str)
        events = events[["event_id", "household_id", "store_id", "basket_id", "week", "transaction_timestamp", "product_id", "choice_idx"]]
        base = catroot / set_id
        base.mkdir(parents=True, exist_ok=True)
        write_table(obs, base / "obs")
        write_table(events, base / "events")
        meta = {
            "set_id": set_id,
            "group_field": "product_type",
            "group_name": item["group_name"],
            "department": item["department"],
            "candidate_products": pids,
            "product_meta": [product_meta[p] for p in pids if p in product_meta],
            "n_alternatives": 6,
            "single_events": int(len(events)),
            "pre22_events": item["events_pre22"],
            "pre22_households": item["households_pre22"],
            "multi_candidate_baskets_excluded": int(len(multi)),
            "candidate_baskets": int(len(basket_n)),
            "choice_semantics": "same-product-type observed substitute proxy; not shelf availability",
            "selection_source": "CJ9 weeks<=22 metadata/support only; no W3-W6 outcomes",
        }
        atomic_json(base / "meta.json", meta)
    registry = {
        "status": "PASS",
        "source_cj9": str(cj9),
        "source_raw": str(raw_root),
        "legacy_source_cj11": str(legacy_cj11),
        "selected_new_sets": selected,
        "pool": pool_info,
        "formal_generalization_started": False,
        "scientific_rules_modified": False,
    }
    atomic_json(out / "gen1_materialization_registry.json", registry)
    atomic_json(out / "materialization_state.json", {"status": "COMPLETE_SAFE_TO_PAUSE", "selected_new_sets": len(selected), "next_action": "RUN_V1_CENSUS_ONLY_AFTER_USER_CONFIRMATION"})
    return registry


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cj9", default=r"C:\MR\data\CJ9")
    ap.add_argument("--raw", default=r"C:\MR\data\CJ_R")
    ap.add_argument("--legacy-cj11", default=r"C:\MR\data\CJ11")
    ap.add_argument("--legacy-panel", default=r"C:\MR\GEN1\MRSP_PREDICTABILITY_GENERALIZATION_V1_20260921\cfg\legacy_panel.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"REFUSE_NONEMPTY_OUTPUT:{out}")
    result = materialize(Path(a.cj9), Path(a.raw), Path(a.legacy_cj11), Path(a.legacy_panel), out)
    print(json.dumps({"status": result["status"], "selected_new_sets": len(result["selected_new_sets"]), "out": str(out)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
