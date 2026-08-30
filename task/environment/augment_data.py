import sqlite3
from pathlib import Path

DB_PATH = Path('/app/manufacturing.db')

# Additional adversarial cases for held-out coverage. They are deliberately
# self-contained and exercise Rule 7 shared-pool optimization plus a later
# cross-order depletion/cancellation check.
parts = [
    ('L47A', 'Held-Out Shared Leaf A', 0, 1),
    ('L47B', 'Held-Out Shared Leaf B', 0, 1),
    ('SUB47_SHARED', 'Held-Out Shared Pool', 4, 1),
    ('SUB47_PRIVATE', 'Held-Out Private Fallback', 2, 1),
    ('P47', 'Held-Out Shared Matching Product', 0, 1),
    ('P48', 'Held-Out Depletion Product', 0, 1),
]

bom = [
    ('P47', 'L47A', 1, 0.0, 0),
    ('P47', 'L47B', 1, 0.0, 0),
    ('P48', 'L47A', 1, 0.0, 0),
]

substitutes = [
    ('L47A', 'SUB47_SHARED', 1.0, 1),
    ('L47B', 'SUB47_SHARED', 1.0, 1),
    ('L47B', 'SUB47_PRIVATE', 1.0, 1),
]

orders = [
    ('O47', 'P47', 3, 1000),
    ('O48', 'P48', 1, 1001),
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
        'INSERT OR IGNORE INTO orders(order_id, product_part_id, requested_qty, priority) VALUES (?, ?, ?, ?)',
        orders,
    )
    con.commit()

print('Applied held-out coverage O47-O48')
