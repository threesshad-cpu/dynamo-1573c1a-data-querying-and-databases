You are given a SQLite database at `/app/manufacturing.db` containing a multi-level manufacturing BOM system with routing, workcenter capacity, scrap, substitutes, and production orders.

Tables:
- `parts(part_id, name, on_hand_qty, batch_size)`: stock and minimum manufacturing lot size.
- `bom(parent_part_id, child_part_id, qty_per, scrap_rate_pct, setup_scrap_qty)`: component requirements, running scrap, and fixed per-batch setup scrap.
- `workcenters(workcenter_id, name, available_hours)`: shared labor/machine capacity.
- `routing(parent_part_id, workcenter_id, setup_hours, run_hours_per_unit)`: setup plus run time for manufacturing a parent.
- `substitutes(primary_part_id, substitute_part_id, qty_ratio, preference_rank)`: replacement stock; lower rank is preferred.
- `orders(order_id, product_part_id, requested_qty, priority)`: finished-product orders.

Definitions: a **leaf part** has no row in `bom` with it as `parent_part_id`; a routing row alone does not make it non-leaf. A **production run** is one manufacturing batch within the current candidate order allocation. A **shared substitute pool** is the remaining inventory of one substitute listed for multiple primary leaves; those units may be consumed only once per candidate run. A **primary-part allocation** is the tuple of fulfilled primary units for the demanded leaves, listed in ascending leaf-ID order.

Process orders by increasing `priority` and apply these rules:
1. **Sub-assemblies first:** use stocked sub-assemblies before manufacturing their difference or calculating leaf demand.
2. **Batch & scrap:** manufacture only integer multiples of `batch_size`. Extra units remain in inventory. For each BOM component, required material is `ceil(base_qty*(1+scrap_rate_pct/100)) + setup_scrap_qty`.
3. **Single runs:** aggregate repeated demand for a component within an order and manufacture it in one run, applying fixed setup once. If the current order uses the same workcenter as the immediately preceding production order, waive that workcenter's `setup_hours`; canceled orders do not count as preceding production orders.
4. **Substitutes:** consume primary stock first. Then use lower `preference_rank`; for equal rank choose highest remaining inventory, then alphabetically. Use floor division for replacement capacity from `qty_ratio`.
5. **Limiting resource:** maximize `allocated_qty` in product `batch_size` multiples. If short, evaluate the gross requirements for `allocated_qty + batch_size` before raw-stock netting (sub-assembly inventory is still netted). For each resource use `total available / gross requirement`; a leaf's availability is its stock plus all equivalent substitute stock, counted independently for this ratio. Shared-pool no-double-counting applies only to actual feasibility. Choose the lowest ratio strictly below 1.0, breaking ties by lexicographically smallest resource ID. Use `null` when the order is fully fulfilled or no ratio is below 1.0.
6. **Cancellation:** if `allocated_qty / requested_qty < 0.5`, cancel: report `allocated_qty=0`, full shortfall, and consume no inventory or workcenter hours. Still report the resource that originally constrained the order.
7. **Shared substitute contention:** within one candidate run, each substitute is one shared pool across all primary leaves. Never consume it twice. Choose the allocation maximizing total primary units fulfilled; on ties minimize total preference rank, then choose the lexicographically smallest primary-part allocation tuple defined above.

After each order, update shared inventory and workcenter capacity.

Write `/app/report.json` as:
```json
{"orders": [{"order_id": str, "allocated_qty": int, "shortfall_qty": int, "limiting_resource": str|null}, ...]}
```
Sort `orders` by `order_id` ascending.
