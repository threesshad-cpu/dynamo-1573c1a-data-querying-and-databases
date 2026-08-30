import sqlite3
from pathlib import Path

DB_PATH = Path('/app/manufacturing.db')

# Additional adversarial cases for held-out coverage. They exercise shared-pool
# optimization, deep BOM traversal, fractional substitutes, setup waiver, and
# cross-order depletion/cancellation without changing the verifier.
parts = [
    ('L47A', 'Held-Out Shared Leaf A', 0, 1),
    ('L47B', 'Held-Out Shared Leaf B', 0, 1),
    ('SUB47_SHARED', 'Held-Out Shared Pool', 4, 1),
    ('SUB47_PRIVATE', 'Held-Out Private Fallback', 2, 1),
    ('P47', 'Held-Out Shared Matching Product', 0, 1),
    ('P48', 'Held-Out Depletion Product', 0, 1),
    ('L49A', 'Deep Challenge Leaf A', 0, 1),
    ('L49B', 'Deep Challenge Leaf B', 0, 1),
    ('L49C', 'Deep Challenge Leaf C', 0, 1),
    ('SUB49', 'Deep Shared Substitute', 19, 1),
    ('SUB49_ALT', 'Deep Fractional Substitute', 11, 1),
    ('SA49A', 'Deep Challenge Assembly A', 0, 2),
    ('SA49B', 'Deep Challenge Assembly B', 0, 3),
    ('SA49C', 'Deep Challenge Assembly C', 0, 2),
    ('P49', 'Deep Challenge Product', 0, 2),
]

bom = [
    ('P47', 'L47A', 1, 0.0, 0),
    ('P47', 'L47B', 1, 0.0, 0),
    ('P48', 'L47A', 1, 0.0, 0),
    ('P49', 'SA49A', 1, 5.0, 1),
    ('P49', 'SA49B', 1, 0.0, 0),
    ('P49', 'SA49C', 1, 10.0, 1),
    ('SA49A', 'L49A', 2, 5.0, 1),
    ('SA49A', 'L49B', 1, 0.0, 0),
    ('SA49B', 'L49B', 2, 10.0, 1),
    ('SA49B', 'L49C', 1, 0.0, 0),
    ('SA49C', 'L49A', 1, 0.0, 0),
    ('SA49C', 'L49C', 2, 5.0, 1),
]

substitutes = [
    ('L47A', 'SUB47_SHARED', 1.0, 1),
    ('L47B', 'SUB47_SHARED', 1.0, 1),
    ('L47B', 'SUB47_PRIVATE', 1.0, 1),
    ('L49A', 'SUB49', 1.0, 1),
    ('L49B', 'SUB49', 1.0, 1),
    ('L49C', 'SUB49', 1.0, 2),
    ('L49C', 'SUB49_ALT', 0.5, 1),
]

routing = [
    ('SA49A', 'WC49A', 0.75, 0.55),
    ('SA49B', 'WC49A', 1.10, 0.65),
    ('SA49B', 'WC49B', 0.60, 0.35),
    ('SA49C', 'WC49B', 0.90, 0.50),
    ('P49', 'WC49C', 1.25, 0.40),
]

workcenters = [
    ('WC49A', 'Deep Challenge Assembly', 25.0),
    ('WC49B', 'Deep Challenge Secondary', 18.0),
    ('WC49C', 'Deep Challenge Final', 14.0),
]

orders = [
    ('O47', 'P47', 3, 1000),
    ('O48', 'P48', 1, 1001),
    ('O49', 'P49', 3, 2000),
    ('O50', 'P49', 2, 2001),
    ('O51', 'P49', 4, 2002),
    ('O52', 'P49', 3, 2003),
    ('O53', 'P49', 5, 2004),
    ('O54', 'P49', 2, 2005),
    ('O55', 'P49', 4, 2006),
    ('O56', 'P49', 3, 2007),
    ('O57', 'P49', 5, 2008),
    ('O58', 'P49', 2, 2009),
]

with sqlite3.connect(DB_PATH) as con:
    cur = con.cursor()
    cur.executemany(
        'INSERT OR IGNORE INTO parts(part_id, name, on_hand_qty, batch_size) VALUES (?, ?, ?, ?)',
        parts,
    )
    cur.executemany(
        'INSERT OR IGNORE INTO bom(parent_part_id, child_part_id, qty_per, scrap_rate_pct, setup_scrap_qty) VALUES (?, ?, ?, ?, ?)',
        bom,
    )
    cur.executemany(
        'INSERT OR IGNORE INTO substitutes(primary_part_id, substitute_part_id, qty_ratio, preference_rank) VALUES (?, ?, ?, ?)',
        substitutes,
    )
    cur.executemany(
        'INSERT OR IGNORE INTO routing(parent_part_id, workcenter_id, setup_hours, run_hours_per_unit) VALUES (?, ?, ?, ?)',
        routing,
    )
    cur.executemany(
        'INSERT OR IGNORE INTO workcenters(workcenter_id, name, available_hours) VALUES (?, ?, ?)',
        workcenters,
    )
    cur.executemany(
        'INSERT OR IGNORE INTO orders(order_id, product_part_id, requested_qty, priority) VALUES (?, ?, ?, ?)',
        orders,
    )
    con.commit()

print('Applied held-out coverage O47-O58')
