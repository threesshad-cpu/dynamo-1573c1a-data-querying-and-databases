import sqlite3
from pathlib import Path

parts_data = [
    ("L1", "Bolt-M4", 250, 1),
    ("L2", "Bolt-M6", 300, 1),
    ("L3", "Steel-Plate", 88, 1),
    ("L4", "Rubber-Gasket", 150, 1),
    ("L5", "Circuit-Board", 25, 1),
    ("L6", "Wire-Harness", 60, 1),
    ("L7", "LED-Display", 30, 1),
    ("L8", "Power-Unit", 40, 1),
    ("SA1", "Bracket-Assembly", 8, 1),
    ("SA2", "Sensor-Module", 4, 1),
    ("SA3", "Base-Frame", 0, 1),
    ("SA4", "Control-Panel", 5, 1),
    ("P1", "Widget-X", 0, 5),
    ("P2", "Widget-Y", 0, 4),
    ("P3", "Widget-Z", 0, 2),
]

bom_data = [
    ("SA1", "L1", 4, 0.0),
    ("SA1", "L3", 1, 5.5),
    ("SA2", "L5", 1, 0.0),
    ("SA2", "L6", 2, 5.0),
    ("SA2", "L1", 2, 0.0),
    ("SA3", "L3", 2, 0.0),
    ("SA3", "L2", 6, 0.0),
    ("SA3", "L4", 4, 2.5),
    ("SA4", "SA2", 1, 0.0),
    ("SA4", "L7", 1, 0.0),
    ("P1", "SA1", 2, 0.0),
    ("P1", "SA2", 1, 0.0),
    ("P1", "L2", 4, 0.0),
    ("P2", "SA1", 1, 0.0),
    ("P2", "SA3", 1, 0.0),
    ("P2", "L4", 2, 0.0),
    ("P3", "SA4", 1, 0.0),
    ("P3", "L8", 1, 0.0),
]

orders_data = [
    ("O0", "P2", 12, 0),
    ("O1", "P1", 30, 1),
    ("O2", "P3", 15, 2),
    ("O3", "P2", 20, 3),
    ("O4", "P1", 25, 4),
    ("O5", "P3", 25, 5),
    ("O6", "P2", 20, 6),
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
            on_hand_qty INTEGER NOT NULL,
            batch_size INTEGER NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE bom (
            parent_part_id TEXT NOT NULL,
            child_part_id TEXT NOT NULL,
            qty_per INTEGER NOT NULL,
            scrap_rate_pct REAL NOT NULL,
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

    cursor.executemany("INSERT INTO parts VALUES (?, ?, ?, ?)", parts_data)
    cursor.executemany("INSERT INTO bom VALUES (?, ?, ?, ?)", bom_data)
    cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?)", orders_data)

    conn.commit()
    conn.close()
    print(f"Generated SQLite DB at {db_path}")


if __name__ == "__main__":
    db_path = Path("/app/manufacturing.db")
    try:
        create_database(db_path)
    except Exception:
        pkg_data = Path(__file__).resolve().parent.parent / "data"
        fallback = pkg_data / "manufacturing.db"
        print(f"Fallback to {fallback}")
        create_database(fallback)
