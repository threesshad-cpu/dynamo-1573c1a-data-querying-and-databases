You are given a SQLite database at `/app/manufacturing.db` containing a multi-level manufacturing bill-of-materials (BOM) system.

Tables:
- `parts(part_id, name, on_hand_qty)` — `on_hand_qty` is current warehouse stock (only meaningful for raw/leaf components; sub-assemblies are built on demand and always have `on_hand_qty = 0`).
- `bom(parent_part_id, child_part_id, qty_per)` — `qty_per` units of `child_part_id` are consumed to build 1 unit of `parent_part_id`. The BOM is a DAG: a component can appear as a child under multiple parents and at multiple levels — its total requirement per finished unit must be aggregated across every path it appears on.
- `orders(order_id, product_part_id, requested_qty, priority)` — production orders for top-level products, all drawing from the same shared warehouse inventory in `parts.on_hand_qty`.

Process orders in ascending `priority` order (ties broken by `order_id` ascending), one at a time, against a single shared, mutable inventory pool that starts at each part's `on_hand_qty`:

1. Explode the ordered product's full BOM (all levels) into total raw-component requirements per finished unit, correctly summing contributions from components that recur via more than one path.
2. Given remaining inventory at the time this order is processed, compute the maximum number of complete units buildable: the largest integer N such that, for every raw component required, `N * qty_per <= remaining_on_hand` for that component.
3. `allocated_qty` = min(requested_qty, that maximum).
4. `shortfall_qty` = requested_qty - allocated_qty.
5. `limiting_component` = the `part_id` of the raw component with the smallest `remaining_on_hand / qty_per` ratio if `shortfall_qty > 0`, else `null`.
6. Deduct `allocated_qty * qty_per` of every raw component actually consumed from the shared pool before processing the next order.

Write `/app/report.json`:
```json
{
  "orders": [
    {
      "order_id": "O0",
      "allocated_qty": 5,
      "shortfall_qty": 0,
      "limiting_component": null
    }
  ]
}
```

`orders` must be sorted by `order_id` ascending (independent of processing order). All values are integers, no rounding needed.

You have 300 seconds to complete this task.
