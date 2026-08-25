import sqlite3
from pathlib import Path


def extend(db_path: Path):
    if not db_path.exists():
        return
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # O22 must leave both rank-1 substitutes exhausted so O23 starts
    # with a genuinely scarce shared pool.
    cur.execute("UPDATE parts SET on_hand_qty = 3 WHERE part_id IN ('SUB22_A', 'SUB22_B')")

    # Replace the simple O23 leaf with a contention case:
    # L23A can use either shared stock or its private substitute;
    # SUB22_A can use only the shared stock. A greedy solver can strand
    # SUB22_A, while a globally feasible allocation gets one full unit.
    cur.execute("DELETE FROM bom WHERE parent_part_id = 'P23'")
    cur.executemany(
        "INSERT INTO parts VALUES (?, ?, ?, ?)",
        [
            ("L23A", "Shared Allocation Leaf", 0, 1),
            ("SUB23_SHARED", "Shared Substitute 23", 1, 1),
            ("SUB23_A", "A-Only Substitute 23", 1, 1),
        ],
    )
    cur.executemany(
        "INSERT INTO bom VALUES (?, ?, ?, ?, ?)",
        [
            ("P23", "L23A", 1, 0.0, 0),
            ("P23", "SUB22_A", 1, 0.0, 0),
        ],
    )
    cur.executemany(
        "INSERT INTO substitutes VALUES (?, ?, ?, ?)",
        [
            ("L23A", "SUB23_SHARED", 1.0, 1),
            ("L23A", "SUB23_A", 1.0, 2),
            ("SUB22_A", "SUB23_SHARED", 1.0, 1),
        ],
    )
    conn.commit()
    conn.close()


for target in [
    Path("/app/manufacturing.db"),
    Path(__file__).resolve().parent.parent / "data" / "manufacturing.db",
]:
    try:
        extend(target)
    except sqlite3.IntegrityError:
        pass
