You are given a SQLite database at `/app/manufacturing.db` containing a multi-level manufacturing bill-of-materials (BOM) system with the following tables:
- `parts(part_id, name, on_hand_qty)`: Current stock. Sub-assemblies and top-level products have `on_hand_qty = 0`.
- `bom(parent_part_id, child_part_id, qty_per)`: Component requirement graph per parent unit.
- `orders(order_id, product_part_id, requested_qty, priority)`: Production orders for products.

Perform a multi-level BOM explosion and simulate sequential shared-inventory allocation across all production orders in ascending `priority` order (ties broken by `order_id` ascending):

- For each order, allocate as many complete units as buildable from the remaining raw inventory pool (`allocated_qty`).
- If an order experiences a stock shortfall (`shortfall_qty > 0`), identify the bottleneck raw component (`limiting_component`) that restricts build capacity due to having the lowest remaining stock ratio (`remaining_on_hand / qty_per` per product unit). If there is a tie, pick the raw component with the ASCII-smallest `part_id`. If `shortfall_qty == 0`, set `limiting_component` to `null`.
- Deduct consumed raw components from the shared inventory pool after fulfilling each order before processing subsequent orders.

Write the final result to `/app/report.json` with the schema:
`{"orders": [{"order_id": str, "allocated_qty": int, "shortfall_qty": int, "limiting_component": str|null}, ...]}`

Sort the `orders` array in `/app/report.json` by `order_id` ascending.
