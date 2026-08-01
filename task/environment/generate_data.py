import sqlite3
from pathlib import Path

parts_data = [
    ("L1", "Bolt-M4", 500),
    ("L2", "Bolt-M6", 300),
    ("L3", "Steel-Plate", 40),
    ("L4", "Rubber-Gasket", 150),
    ("L5", "Circuit-Board", 25),
    ("L6", "Wire-Harness", 60),
    ("SA1", "Bracket-Assembly", 0),
    ("SA2", "Sensor-Module", 0),
    ("SA3", "Base-Frame", 0),
    ("P1", "Widget-X", 0),
    ("P2", "Widget-Y", 0),
]

bom_data = [
    ("SA1", "L1", 4),
    ("SA1", "L3", 1),
    ("SA2", "L5", 1),
    ("SA2", "L6", 2),
    ("SA2", "L1", 2),
    ("SA3", "L3", 2),
    ("SA3", "L2", 6),
    ("SA3", "L4", 4),
    ("P1", "SA1", 2),
    ("P1", "SA2", 1),
    ("P1", "L2", 4),
    ("P2", "SA1", 1),
    ("P2", "SA3", 1),
    ("P2", "L4", 2),
]

orders_data = [
    ("O0", "P2", 5, 0),
    ("O1", "P1", 30, 1),
    ("O2", "P2", 20, 2),
    ("O3", "P1", 15, 3),
]


def create_database(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE parts (
            part_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            on_hand_qty INTEGER NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE bom (
            parent_part_id TEXT NOT NULL,
            child_part_id TEXT NOT NULL,
            qty_per INTEGER NOT NULL,
            PRIMARY KEY (parent_part_id, child_part_id)
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE orders (
            order_id TEXT PRIMARY KEY,
            product_part_id TEXT NOT NULL,
            requested_qty INTEGER NOT NULL,
            priority INTEGER NOT NULL
        )
    """
    )

    cursor.executemany("INSERT INTO parts VALUES (?, ?, ?)", parts_data)
    cursor.executemany("INSERT INTO bom VALUES (?, ?, ?)", bom_data)
    cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", orders_data)

    conn.commit()
    conn.close()
    print(f"Generated SQLite DB at {db_path}")


paths = [
    Path("/app/manufacturing.db"),
    Path("/tmp/manufacturing.db"),
    Path("/data/manufacturing.db"),
    Path(__file__).resolve().parent.parent / "data" / "manufacturing.db",
]

for p in paths:
    try:
        create_database(p)
    except Exception as e:
        print(f"Note: Could not write to {p}: {e}")
