Calculate multi-level manufacturing BOM bill-of-materials explosion and sequential shared inventory allocation in SQLite database at `/app/manufacturing.db`.

1. Explode BOM DAG requirements per product unit across all assembly paths.
2. Process orders by priority ascending. Compute `allocated_qty` = min(requested_qty, max complete units buildable).
3. Compute `shortfall_qty` = requested_qty - allocated_qty.
4. Set `limiting_component` to the raw part_id with smallest `remaining_on_hand / qty_per` ratio if shortfall > 0, else `null`.
5. Deduct `allocated_qty * qty_per` from shared inventory.

Write `/app/report.json`:
`{"orders": [{"order_id": str, "allocated_qty": int, "shortfall_qty": int, "limiting_component": str|null}]}`

You have 300 seconds to complete this task.
