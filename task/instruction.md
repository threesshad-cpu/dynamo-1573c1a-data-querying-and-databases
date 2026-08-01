You are given a SQLite database at `/app/manufacturing.db` containing a multi-level manufacturing bill-of-materials (BOM) system.

Database Tables:
- `parts(part_id, name, on_hand_qty)`: Current warehouse stock. Sub-assemblies and products have `on_hand_qty = 0`.
- `bom(parent_part_id, child_part_id, qty_per)`: Directed graph of component requirements per parent unit.
- `orders(order_id, product_part_id, requested_qty, priority)`: Production orders for top-level products.

Process orders sequentially in ascending `priority` order (ties broken by `order_id` ascending) against the shared inventory pool:

1. Aggregate total raw component requirements per product unit across all BOM paths (handling DAG reconvergence).
2. Compute `allocated_qty` = min(requested_qty, maximum complete units buildable given current remaining inventory).
3. Compute `shortfall_qty` = requested_qty - allocated_qty.
4. Set `limiting_component` to the raw `part_id` with the smallest `remaining_on_hand / qty_per` ratio if `shortfall_qty > 0`, else `null` (ties broken by `part_id` ASCII ascending).
5. Deduct consumed raw components (`allocated_qty * qty_per`) from the shared inventory pool before processing the next order.

Write the final output object to `/app/report.json`:
`{"orders": [{"order_id": str, "allocated_qty": int, "shortfall_qty": int, "limiting_component": str|null}, ...]}`

Sort the `orders` list by `order_id` ascending.

You have 300 seconds to complete this task.
