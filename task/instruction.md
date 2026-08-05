You are given a SQLite database at `/app/manufacturing.db` containing a multi-level manufacturing bill-of-materials (BOM) system with the following tables:
- `parts(part_id, name, on_hand_qty, batch_size)`: Inventory stock for raw components and pre-built sub-assemblies (`on_hand_qty >= 0`), and minimum build lot size constraint (`batch_size`).
- `bom(parent_part_id, child_part_id, qty_per, scrap_rate_pct)`: Component graph per parent unit with scrap/yield loss percentage (`scrap_rate_pct`). Gross child requirement for $U$ parent units is $\lceil U \times \text{qty\_per} \times (1 + \text{scrap\_rate\_pct}/100) \rceil$.
- `orders(order_id, product_part_id, requested_qty, priority)`: Production orders for products.

Perform a multi-level BOM explosion and simulate sequential shared-inventory allocation across production orders in ascending `priority` order (ties broken by `order_id` ascending):

- Consume pre-built sub-assembly stock on hand first before exploding net sub-assembly requirements into child components.
- Allocate `allocated_qty` as the maximum units buildable up to `requested_qty` subject to `batch_size` lot constraints (`allocated_qty` must be a multiple of `batch_size`).
- Compute `shortfall_qty` = `requested_qty - allocated_qty`.
- If `shortfall_qty > 0`, set `limiting_component` to the raw component restricting allocation for the next batch increment of `batch_size` units (evaluated for producing `allocated_qty + batch_size` total product units from the current order's initial state). Select the raw component $L$ with the smallest remaining inventory ratio $\frac{\text{inventory}[L]}{\text{gross\_required}[L]}$, breaking ties by ASCII-smallest `part_id`. If `shortfall_qty == 0`, set `limiting_component` to `null`.
- Deduct consumed sub-assemblies and raw components from the shared inventory pool after fulfilling each order.

Write the final result to `/app/report.json` with the schema:
`{"orders": [{"order_id": str, "allocated_qty": int, "shortfall_qty": int, "limiting_component": str|null}, ...]}`

Sort the `orders` array in `/app/report.json` by `order_id` ascending.
