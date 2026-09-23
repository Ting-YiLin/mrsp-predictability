# Data layout and release status

## Canonical source expected by full reproduction

The frozen confirmatory code expects a canonical `CJ9` directory with:

```text
CJ9/
├── products.parquet  (or products.csv.gz / products.csv)
└── tx/
    ├── w01.parquet
    ├── ...
    └── w53.parquet
```

Required product metadata fields include `product_id`, `product_type`, and `department`.

Required transaction fields used by the confirmatory materializer include:

`household_id, store_id, basket_id, product_id, quantity, sales_value, retail_disc, coupon_disc, coupon_match_disc, week, transaction_timestamp, net_price, gross_proxy`.

## Observed upstream lineage

The project recon recorded an upstream raw store containing approximately 1.47M transaction rows across weeks 1–53, 2,469 households and 68,509 products, which was transformed into the canonical CJ9 store by earlier builders.

## Redistribution

Raw event-level consumer data are intentionally **not included** in this release. The final public release should keep the code/results-only distribution unless a dedicated license audit closes the exact provenance and redistribution rights for the local source files.
