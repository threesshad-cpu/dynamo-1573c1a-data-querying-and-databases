You are given a SQLite database at `/app/manufacturing.db` containing a multi-level manufacturing bill-of-materials (BOM) system with routing, workcenter capacity, scrap, and substitute part rules across the following tables:

- `parts(part_id, name, on_hand_qty, batch_size)`: Inventory stock for leaf raw materials, sub-assemblies, and finished products. `batch_size` is the minimum manufacturing lot size (units must be produced in integer multiples of this value).
- `bom(parent_part_id, child_part_id, qty_per, scrap_rate_pct, setup_scrap_qty)`: Bill-of-materials component graph. Each row defines how many units of `child_part_id` are needed per unit of `parent_part_id` (`qty_per`), plus a percentage-based running scrap rate (`scrap_rate_pct`) and a fixed per-batch setup scrap quantity (`setup_scrap_qty`) that is incurred once regardless of build quantity.
- `workcenters(workcenter_id, name, available_hours)`: Finite shared capacity pools of labor/machine hours.
- `routing(parent_part_id, workcenter_id, setup_hours, run_hours_per_unit)`: Workcenter time requirements for manufacturing a parent part. Each manufacturing run of $U > 0$ units of `parent_part_id` consumes `setup_hours` plus `U * run_hours_per_unit` from the workcenter's shared `available_hours` pool.
- `substitutes(primary_part_id, substitute_part_id, qty_ratio, preference_rank)`: Substitute parts that can replace a primary part when its on-hand stock is insufficient. Each unit of `primary_part_id` demand requires `qty_ratio` units of `substitute_part_id`. Lower `preference_rank` substitutes are used first. Primary stock is always consumed before substitutes.
- `orders(order_id, product_part_id, requested_qty, priority)`: Production orders for finished products.

Process production orders one by one, starting with the lowest `priority` number. For each order, follow these 6 rules:

1. **Use Sub-Assemblies First**: Before you calculate how many raw materials (leaf components) you need, always use up any sub-assemblies you already have in stock. You only need to manufacture the difference.
2. **Batch Rounding & Scrap**: Whenever you manufacture a part, you must build it in multiples of its `batch_size` (e.g., if you need 7 but batch size is 5, you build 10). Any extra units go into inventory for future orders. When calculating the materials needed, multiply the base requirement by `(1 + scrap_rate_pct / 100)` and round up to the next whole number. Then, add the fixed `setup_scrap_qty`.
3. **Single Production Runs**: If a component is required in multiple places within the same order, add up the total amount needed and build it all in one single run. This means you only pay the fixed `setup_hours` and `setup_scrap_qty` exactly once per order. (Don't calculate requirements batch-by-batch).
4. **Using Substitutes**: If you run out of a leaf part, you can use its substitutes. Always use substitutes with a lower `preference_rank` first. If two substitutes share the same rank, break the tie by picking the one whose ID comes first alphabetically (e.g., `SUB_10` over `SUB_2`). Use floor division to determine how many primary units a substitute can replace based on its `qty_ratio`.
5. **Finding the Limiting Resource**: Find the maximum `allocated_qty` you can successfully build (which must be a multiple of the product's batch size). If you can't fulfill the entire requested quantity, you must identify the single `limiting_resource` that stopped you from building just one more batch:
   - Figure out the **gross requirement** of leaf components and workcenter hours needed to build `allocated_qty + batch_size` units. (Calculate this from the inventory state *before* you started the order). *Important*: You still net out sub-assemblies, but do NOT subtract leaf inventory from this gross requirement.
   - For each resource, compute its fulfillment ratio: `total available / gross requirement`. For leaves, "total available" includes its own stock plus any equivalent stock you can get from substitutes.
   - The resource with the lowest ratio strictly below 1.0 is the `limiting_resource`. 
   - If multiple resources tie for the lowest ratio, break the tie by picking the resource whose ID comes first alphabetically as a string (e.g., if `L2` and `WC3` tie, choose `L2` because L comes before W).
   - If you fulfill the entire order (`shortfall_qty == 0`), just set `limiting_resource` to `null`.
6. **Minimum Fill Rate**: If the maximum `allocated_qty` you can build is less than 50% of the `requested_qty` (i.e., `allocated_qty / requested_qty < 0.5`), the order is unviable and canceled. You must set `allocated_qty` to 0 and `shortfall_qty` to the full `requested_qty`, and consume NO inventory or workcenter hours. You must still compute and report the `limiting_resource` that originally constrained the order.

Update the shared inventory and workcenter pools after each order is processed.

Write the result to `/app/report.json`:
```json
{"orders": [{"order_id": str, "allocated_qty": int, "shortfall_qty": int, "limiting_resource": str|null}, ...]}
```
Sort the `orders` array by `order_id` ascending.
