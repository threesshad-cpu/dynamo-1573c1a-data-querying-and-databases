import os
import json

REPORT_PATH = "/app/report.json"

def test_file_exists_and_not_symlink():
    """Verifies that /app/report.json exists and is a real file (not a symlink exploit)."""
    assert os.path.exists(REPORT_PATH), "report.json does not exist"
    assert not os.path.islink(REPORT_PATH), "report.json must not be a symlink"

def test_schema_and_contents():
    """Verifies output structure, integrated matrix ownership calculations, exemptions, and sorting."""
    with open(REPORT_PATH, "r") as f:
        data = json.load(f)

    assert data["evaluation_date"] == "2026-07-29"
    assert "summary" in data
    assert data["summary"]["total_entities_analyzed"] == 8

    high_risk = data["high_risk_subsidiaries"]
    flagged_ids = [item["entity_id"] for item in high_risk]
    assert "http://example.org/entity/E104" not in flagged_ids, "E104 should be exempt from sanctions"

    assert len(high_risk) == 3, f"Expected 3 high-risk subsidiaries, got {len(high_risk)}"

    # E101: Integrated Ownership = (0.60 + 0.20*0.10) / (1 - 0.50*0.10) = 0.62 / 0.95 = 0.65263158 -> 0.6526
    assert high_risk[0]["entity_id"] == "http://example.org/entity/E101"
    assert abs(high_risk[0]["effective_ownership"] - 0.6526) < 0.0001
    assert high_risk[0]["inherited_sanctions"] == ["Financial", "Trade"]

    # E102: Integrated Ownership = (0.60*0.50 + 0.20) / 0.95 = 0.50 / 0.95 = 0.52631579 -> 0.5263
    assert high_risk[1]["entity_id"] == "http://example.org/entity/E102"
    assert abs(high_risk[1]["effective_ownership"] - 0.5263) < 0.0001
    assert high_risk[1]["inherited_sanctions"] == ["Financial", "Trade"]

    # E103: Integrated Ownership = 0.65263158*0.40 + 0.52631579*0.30 = 0.41894737 -> 0.4189
    assert high_risk[2]["entity_id"] == "http://example.org/entity/E103"
    assert abs(high_risk[2]["effective_ownership"] - 0.4189) < 0.0001
    assert high_risk[2]["inherited_sanctions"] == ["Financial", "Trade"]

    assert data["summary"]["flagged_subsidiaries_count"] == 3
