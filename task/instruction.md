You are given a SQLite database at `/app/manufacturing.db` containing a multi-level manufacturing bill-of-materials (BOM) system with routing, workcenter capacity, scrap, and substitute part rules across the following tables:

- `parts(part_id, name, on_hand_qty, batch_size)`: Inventory stock for leaf raw materials, sub-assemblies, and finished products. `batch_size` is the minimum manufacturing lot size (units must be produced in integer multiples of this value).
- `bom(parent_part_id, child_part_id, qty_per, scrap_rate_pct, setup_scrap_qty)`: Bill-of-materials component graph. Each row defines how many units of `child_part_id` are needed per unit of `parent_part_id` (`qty_per`), plus a percentage-based running scrap rate (`scrap_rate_pct`) and a fixed per-batch setup scrap quantity (`setup_scrap_qty`) that is incurred once regardless of build quantity.
- `workcenters(workcenter_id, name, available_hours)`: Finite shared capacity pools of labor/machine hours.
- `routing(parent_part_id, workcenter_id, setup_hours, run_hours_per_unit)`: Workcenter time requirements for manufacturing a parent part. Each manufacturing run of $U > 0$ units of `parent_part_id` consumes `setup_hours` plus `U * run_hours_per_unit` from the workcenter's shared `available_hours` pool.
- `substitutes(primary_part_id, substitute_part_id, qty_ratio, preference_rank)`: Substitute parts that can replace a primary part when its on-hand stock is insufficient. Each unit of `primary_part_id` demand requires `qty_ratio` units of `substitute_part_id`. Lower `preference_rank` substitutes are used first. Primary stock is always consumed before substitutes.
- `orders(order_id, product_part_id, requested_qty, priority)`: Production orders for finished products.

Process production orders sequentially in ascending `priority` order (break ties by `order_id` DESCENDING). For each order, perform a multi-level BOM explosion with routing and substitute stock allocation:

1. **BOM Explosion with Stock Netting**: Explode the product's BOM top-down through all assembly levels. At each node, consume available on-hand stock of that part first. Only the net shortfall (demand minus available stock) needs to be manufactured. When manufacturing is required, round the build quantity up to the nearest integer multiple of the part's `batch_size`. Any excess units produced beyond what is needed are credited back into inventory for later orders. Compute gross child component requirements based on the rounded-up build quantity, accounting for both the fixed setup scrap and the running scrap rate on each BOM edge. The running scrap adjustment multiplies the base requirement by `(1 + scrap_rate_pct / 100)` and the result is rounded up to the next integer, then the fixed `setup_scrap_qty` is added on top.

2. **Substitute Consumption**: If on-hand stock of a required part is insufficient, check available substitute parts in ascending `preference_rank` order. Each unit of primary demand can be satisfied by consuming `qty_ratio` units of the substitute. Only whole-unit conversions are permitted (floor division determines how many primary units a substitute can cover). Deduct consumed substitute stock from the shared pool.

3. **Workcenter Capacity**: Manufacturing any part that has routing entries consumes workcenter hours from the shared capacity pool. Both setup hours and per-unit run hours apply. This includes finished products — product-level routing setup hours are incurred when building the final product.

4. **Order Allocation**: For each order, determine the maximum `allocated_qty` (as an integer multiple of the product's `batch_size`) that can be fulfilled given available leaf materials, substitute stocks, and workcenter capacity. Set `shortfall_qty = requested_qty - allocated_qty`.

5. **Limiting Resource Identification**: When `shortfall_qty > 0`, identify the single most constraining resource that prevents building one additional batch of the product. Evaluate what resources would be needed to build `allocated_qty + batch_size` total units from the order's initial resource state (before any allocation from this order). Compare the fulfillment ratio (available / required) for every leaf component and every workcenter involved. Important: The "required" amount for any leaf component or workcenter must be the gross requirement calculated **after** fully netting out any available stock of parent sub-assemblies (i.e., only the demand that propagates down the BOM after sub-assemblies are consumed). For leaf components, include available substitute stock (converted at the appropriate `qty_ratio`) in the available supply. The resource with the lowest ratio below 1.0 is the `limiting_resource`. If multiple resources share the same minimum ratio, select the one with the ASCII-smallest resource ID. When `shortfall_qty == 0`, set `limiting_resource` to `null`.

6. **Shared Pool Update**: After processing each order, deduct all consumed inventory (primary parts and substitutes) and workcenter hours from the shared pools. Credit any excess sub-assemblies produced during lot rounding.

Write the result to `/app/report.json`:
```json
{"orders": [{"order_id": str, "allocated_qty": int, "shortfall_qty": int, "limiting_resource": str|null}, ...]}
```
Sort the `orders` array by `order_id` ascending.
