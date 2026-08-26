import json
import os
import sqlite3
from pathlib import Path

from reference_model import compute_reference

REPORT_PATH = os.environ.get("TEST_REPORT_PATH", "/app/report.json")
DB_PATH = Path("/app/manufacturing.db")
if not DB_PATH.exists():
    DB_PATH = Path(__file__).resolve().parent.parent / "environment" / "manufacturing.db"


def _load_report():
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_file_exists_and_not_symlink():
    """The requested artifact exists as a regular file."""
    assert os.path.exists(REPORT_PATH) and not os.path.islink(REPORT_PATH)


def test_report_schema_and_keys():
    """The report schema and order cardinality are derived from the input DB."""
    data = _load_report()
    assert set(data) == {"orders"}
    with sqlite3.connect(str(DB_PATH)) as con:
        expected_count = con.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    orders = data["orders"]
    assert len(orders) == expected_count
    keys = {"order_id", "allocated_qty", "shortfall_qty", "limiting_resource"}
    for row in orders:
        assert isinstance(row, dict) and set(row) == keys
        assert isinstance(row["order_id"], str)
        assert isinstance(row["allocated_qty"], int) and not isinstance(row["allocated_qty"], bool)
        assert isinstance(row["shortfall_qty"], int) and not isinstance(row["shortfall_qty"], bool)
        assert row["limiting_resource"] is None or isinstance(row["limiting_resource"], str)


def test_output_sorting():
    """Order results are sorted by order_id as required by the output contract."""
    ids = [row["order_id"] for row in _load_report()["orders"]]
    assert ids == sorted(ids)


def test_order_quantities_follow_db_contract():
    """Allocated plus shortfall equals the requested quantity for every DB order."""
    rows = {r[0]: r for r in sqlite3.connect(str(DB_PATH)).execute("SELECT order_id,requested_qty,product_part_id FROM orders")}
    with sqlite3.connect(str(DB_PATH)) as con:
        batches = dict(con.execute("SELECT part_id,batch_size FROM parts"))
    for row in _load_report()["orders"]:
        requested = rows[row["order_id"]][1]
        batch = batches[rows[row["order_id"]][2]]
        assert row["allocated_qty"] + row["shortfall_qty"] == requested
        assert row["allocated_qty"] % batch == 0
        if row["shortfall_qty"] == 0:
            assert row["limiting_resource"] is None


def test_against_db_derived_reference_model():
    """Compute the expected result from the SQLite input instead of a static answer key."""
    actual = _load_report()["orders"]
    expected = compute_reference(DB_PATH)
    assert actual == expected
