You are given a SQLite database at `/app/manufacturing.db` containing a multi-level manufacturing bill-of-materials (BOM) system with routing, workcenter capacity, scrap, and substitute part rules across the following tables:

- `parts(part_id, name, on_hand_qty, batch_size)`: Inventory stock for leaf raw materials, sub-assemblies, and finished products. `batch_size` is the minimum manufacturing lot size (units must be produced in integer multiples of this value).
- `bom(parent_part_id, child_part_id, qty_per, scrap_rate_pct, setup_scrap_qty)`: Bill-of-materials component graph. Each row defines how many units of `child_part_id` are needed per unit of `parent_part_id` (`qty_per`), plus a percentage-based running scrap rate (`scrap_rate_pct`) and a fixed per-batch setup scrap quantity (`setup_scrap_qty`) that is incurred once regardless of build quantity.
- `workcenters(workcenter_id, name, available_hours)`: Finite shared capacity pools of labor/machine hours.
- `routing(parent_part_id, workcenter_id, setup_hours, run_hours_per_unit)`: Workcenter time requirements for manufacturing a parent part. Each manufacturing run of $U > 0$ units of `parent_part_id` consumes `setup_hours` plus `U * run_hours_per_unit` from the workcenter's shared `available_hours` pool.
- `substitutes(primary_part_id, substitute_part_id, qty_ratio, preference_rank)`: Substitute parts that can replace a primary part when its on-hand stock is insufficient. Each unit of `primary_part_id` demand requires `qty_ratio` units of `substitute_part_id`. Lower `preference_rank` substitutes are used first. Primary stock is always consumed before substitutes.
- `orders(order_id, product_part_id, requested_qty, priority)`: Production orders for finished products.

Process production orders sequentially in ascending `priority` order. For each order, evaluate fulfillment against 5 core mechanics:

1. **Parent/SA Netting**: Before propagating demand down the BOM to leaf components, you must net out (consume) any available on-hand stock of sub-assemblies. Only the remaining net shortfall propagates downwards.
2. **Batch Rounding**: When manufacturing is required, the build quantity must be rounded up to the nearest integer multiple of the part's `batch_size`. Compute gross child component requirements based on this rounded-up build quantity. The running scrap adjustment multiplies the base requirement by `(1 + scrap_rate_pct / 100)` and the result is rounded up to the next integer, then the fixed `setup_scrap_qty` is added on top. Any excess units produced beyond what is needed are credited back into inventory for later orders.
3. **Aggregated BOM Explosion**: If a component appears under multiple parents (multiple BOM paths), its net requirement must be aggregated (summed) across all paths and it is manufactured exactly once per order at its lowest BOM level. Because shared components are aggregated into a single run, routing `setup_hours` and BOM `setup_scrap_qty` are incurred exactly ONCE per order's aggregated production run.
4. **Deterministic Substitution**: If the required quantity of a leaf part cannot be fully met by its own on-hand stock, use substitute parts in ascending order of their `preference_rank`. Floor division determines how many primary units a substitute can cover based on its `qty_ratio`.
5. **Limiting Resource Logic**: Determine the maximum `allocated_qty` (as an integer multiple of the product's `batch_size`) that can be fulfilled given available resources. Set `shortfall_qty = requested_qty - allocated_qty`. If `shortfall_qty > 0`, identify the `limiting_resource` that prevents building one additional batch. 
   - To do this, calculate the **gross requirement** of leaf components and workcenters needed to build `allocated_qty + batch_size` units from the order's initial resource state (before any allocation from this order). 
   - Compute the ratio: `available / gross_propagated_requirement`. The resource with the lowest ratio strictly below 1.0 is the `limiting_resource`. 
   - If multiple resources (leaves or workcenters) tie for the lowest ratio, break the tie by selecting the resource with the ASCII-smallest resource ID (e.g. `L15` < `WC10`). 
   - When `shortfall_qty == 0`, set `limiting_resource` to `null`.

Update the shared inventory and workcenter pools after each order is processed.

Write the result to `/app/report.json`:
```json
{"orders": [{"order_id": str, "allocated_qty": int, "shortfall_qty": int, "limiting_resource": str|null}, ...]}
```
Sort the `orders` array by `order_id` ascending.
