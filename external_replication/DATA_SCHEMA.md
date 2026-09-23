# Canonical partner input schema

The strict runner accepts **raw canonical purchase events**, not precomputed B1/P1 features. This closes the main reproducibility gap in the earlier draft kit.

## `groups.csv`

Exact header:

```text
product_group_id,department,sku_0,sku_1,sku_2,sku_3,sku_4,sku_5
```

Each group must contain exactly six distinct SKUs in a **pre-frozen order**. The group definition must be fixed before evaluation outcomes are inspected. `department` may be blank but the column must exist.

## `events.csv`

Exact header:

```text
event_id,household_id,event_time,week_index,product_group_id,target_sku
```

Rules:

- `event_id` is unique.
- `household_id` is a partner-local key and is never written to aggregate output.
- `event_time` is ISO-8601.
- `week_index` is the partner's pre-frozen 53-week study clock, integer 1..53. Week labels must not run backward in chronological time.
- `product_group_id` must exist in `groups.csv`.
- `target_sku` must be one of that group's six frozen SKUs.
- Ambiguous duplicate household/group/timestamp events fail closed.
- No precomputed prediction, P1 score, history count, or outcome-derived selection field is accepted.

The runner constructs all pre-event household and market histories internally and mutates state only after each current event has been scored.
