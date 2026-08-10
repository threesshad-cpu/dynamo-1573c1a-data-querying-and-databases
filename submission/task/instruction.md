You are given a SQLite database at `/app/manufacturing.db` containing a multi-level manufacturing bill-of-materials (BOM) system with routing, workcenter capacity, setup scrap, and substitute part rules across the following tables:

- `parts(part_id, name, on_hand_qty, batch_size)`: Inventory stock for raw leaf components, sub-assemblies, and finished products (`on_hand_qty >= 0`), and minimum build lot size constraint (`batch_size`).
- `bom(parent_part_id, child_part_id, qty_per, scrap_rate_pct, setup_scrap_qty)`: Component graph per parent unit. When building $U$ units of parent part, the gross child requirement is:
  $\text{gross\_qty} = \text{setup\_scrap\_qty} + \lceil U \times \text{qty\_per} \times (1 + \text{scrap\_rate\_pct}/100) \rceil$.
- `workcenters(workcenter_id, name, available_hours)`: Finite capacity pool of available labor/machine hours (`available_hours >= 0`).
- `routing(parent_part_id, workcenter_id, setup_hours, run_hours_per_unit)`: Workcenter hours required to build parent parts. Building $U > 0$ units of `parent_part_id` incurs $\text{setup\_hours} + (U \times \text{run\_hours\_per\_unit})$ hours on `workcenter_id`.
- `substitutes(primary_part_id, substitute_part_id, qty_ratio, preference_rank)`: Substitute parts that can replace `primary_part_id` if primary stock on hand is insufficient. 1 unit of `primary_part_id` requires `qty_ratio` units of `substitute_part_id`. Lower `preference_rank` is used first. Primary stock on hand is always consumed before any substitutes.
- `orders(order_id, product_part_id, requested_qty, priority)`: Production orders for finished products.

Perform a multi-level BOM explosion with routing and substitute stock allocation sequentially across production orders in ascending `priority` order (ties broken by `order_id` ascending):

1. **Stock & Substitute Consumption**:
   - Explode sub-assemblies in top-down topological order (level-by-level from products down to leaf components).
   - For sub-assemblies and raw components, consume available primary stock on hand first before exploding net requirements into child components or using substitute part stock.
   - If pre-built primary stock of component $X$ is insufficient for required quantity $Q$, check substitute parts $S$ in ascending `preference_rank`. Up to $\lfloor \text{avail}[S] / \text{qty\_ratio} \rfloor$ units of primary demand $X$ can be satisfied using substitute stock $S$ (deducting $\text{units\_satisfied} \times \text{qty\_ratio}$ from $S$'s stock).

2. **Manufacturing Lot Sizing & Routing**:
   - Sub-assemblies and products must be built in integer multiples of their respective `batch_size`. When exploding a net sub-assembly requirement $N > 0$, the build quantity is rounded up: $\text{build\_qty} = \lceil N / \text{batch\_size} \rceil \times \text{batch\_size}$. Gross child requirements use $\text{build\_qty}$, and any excess sub-assemblies $(\text{build\_qty} - N)$ enter on-hand inventory for subsequent orders.
   - Manufacturing $\text{build\_qty}$ of parent $X$ consumes $\text{setup\_hours} + (\text{build\_qty} \times \text{run\_hours\_per\_unit})$ from the shared `available_hours` pool of each mapped workcenter in `routing`. Routing setup hours are also incurred when manufacturing finished products.

3. **Order Allocation & Limiting Resource**:
   - Allocate `allocated_qty` as the maximum units buildable up to `requested_qty` subject to product `batch_size` lot constraints (`allocated_qty` must be a multiple of `batch_size` and cannot exceed available raw materials, substitute stocks, or workcenter capacity).
   - Compute `shortfall_qty` = `requested_qty - allocated_qty`.
   - If `shortfall_qty == 0`, set `limiting_resource` to `null`.
   - If `shortfall_qty > 0`, set `limiting_resource` to the candidate resource ID (`part_id` or `workcenter_id`) restricting allocation for the next batch increment target $T = \text{allocated\_qty} + \text{batch\_size}$ product units (measured from the order's initial state before allocation):
     - Calculate gross leaf component demands and routing workcenter hours required to build target $T$ units starting from the order's initial pool state.
     - For each required candidate leaf component $L$, evaluate fulfillment ratio $\text{ratio}[L] = \frac{\text{avail}[L] + \sum_S \lfloor \text{avail}[S] / \text{qty\_ratio} \rfloor}{\text{required}[L]}$, where $\text{avail}$ values reflect inventory available at the start of the order.
     - For each required candidate workcenter $W$, evaluate fulfillment ratio $\text{ratio}[W] = \frac{\text{available\_hours}[W]}{\text{required\_hours}[W]}$, where $\text{available\_hours}$ reflects hours available at the start of the order.
     - Select the candidate resource $R$ with ratio $< 1.0$ having the smallest ratio. Break ties by ASCII-smallest resource ID (e.g. `"L1"` < `"WC1"`).

4. **Pool Update**: Deduct consumed inventory (primary and substitute) and workcenter hours (and credit excess sub-assemblies created) after fulfilling each order.

Write the final result to `/app/report.json` with the schema:
`{"orders": [{"order_id": str, "allocated_qty": int, "shortfall_qty": int, "limiting_resource": str|null}, ...]}`

Sort the `orders` array in `/app/report.json` by `order_id` ascending.
