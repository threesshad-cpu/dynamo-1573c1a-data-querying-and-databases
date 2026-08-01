import os
import json

REPORT_PATH = "/app/report.json"

def _load_report():
    assert os.path.exists(REPORT_PATH), f"{REPORT_PATH} does not exist"
    with open(REPORT_PATH, "r") as f:
        return json.load(f)

def test_file_exists_and_not_symlink():
    """Verifies that /app/report.json exists and is a real file (not a symlink exploit)."""
    assert os.path.exists(REPORT_PATH), "report.json does not exist"
    assert not os.path.islink(REPORT_PATH), "report.json must not be a symlink"

def test_report_schema_keys():
    """Verifies top-level JSON schema keys and evaluation_date value."""
    data = _load_report()
    assert "evaluation_date" in data, "Missing evaluation_date key"
    assert "high_risk_subsidiaries" in data, "Missing high_risk_subsidiaries key"
    assert "summary" in data, "Missing summary key"
    assert data["evaluation_date"] == "2026-07-29", f"Expected evaluation_date '2026-07-29', got {data['evaluation_date']}"

def test_summary_counts():
    """Verifies summary block metrics for total entities analyzed and flagged count."""
    data = _load_report()
    summary = data["summary"]
    assert "total_entities_analyzed" in summary, "Missing total_entities_analyzed in summary"
    assert "flagged_subsidiaries_count" in summary, "Missing flagged_subsidiaries_count in summary"
    assert summary["total_entities_analyzed"] == 8, f"Expected 8 total entities, got {summary['total_entities_analyzed']}"
    assert summary["flagged_subsidiaries_count"] == 3, f"Expected 3 flagged count, got {summary['flagged_subsidiaries_count']}"

def test_exemption_handling():
    """Verifies that entities marked exemptFromInheritance (e.g. E104) are excluded from high_risk_subsidiaries."""
    data = _load_report()
    flagged_ids = [item["entity_id"] for item in data["high_risk_subsidiaries"]]
    assert "http://example.org/entity/E104" not in flagged_ids, "E104 should be exempt from sanctions"

def test_high_risk_subsidiaries_count():
    """Verifies exact count of flagged high-risk subsidiaries."""
    data = _load_report()
    high_risk = data["high_risk_subsidiaries"]
    assert len(high_risk) == 3, f"Expected 3 high-risk subsidiaries, got {len(high_risk)}"

def test_entity_names():
    """Verifies that entity_name is present for all flagged subsidiaries and matches expected labels."""
    data = _load_report()
    high_risk = data["high_risk_subsidiaries"]
    id_to_name = {item["entity_id"]: item.get("entity_name") for item in high_risk}
    
    assert "http://example.org/entity/E101" in id_to_name
    assert id_to_name["http://example.org/entity/E101"] == "Alpha Subsidiary", f"Expected 'Alpha Subsidiary', got {id_to_name['http://example.org/entity/E101']}"
    
    assert "http://example.org/entity/E102" in id_to_name
    assert id_to_name["http://example.org/entity/E102"] == "Beta Logistics", f"Expected 'Beta Logistics', got {id_to_name['http://example.org/entity/E102']}"
    
    assert "http://example.org/entity/E103" in id_to_name
    assert id_to_name["http://example.org/entity/E103"] == "Gamma Shipping", f"Expected 'Gamma Shipping', got {id_to_name['http://example.org/entity/E103']}"

def test_effective_ownership_values():
    """Verifies integrated effective ownership values for flagged entities within 0.0001 (1e-4) tolerance."""
    data = _load_report()
    high_risk = data["high_risk_subsidiaries"]
    id_to_ownership = {item["entity_id"]: item["effective_ownership"] for item in high_risk}

    # E101: Integrated Ownership = (0.60 + 0.20*0.10) / (1 - 0.50*0.10) = 0.62 / 0.95 = 0.65263158 -> 0.6526
    assert abs(id_to_ownership["http://example.org/entity/E101"] - 0.6526) <= 0.0001

    # E102: Integrated Ownership = (0.60*0.50 + 0.20) / 0.95 = 0.50 / 0.95 = 0.52631579 -> 0.5263
    assert abs(id_to_ownership["http://example.org/entity/E102"] - 0.5263) <= 0.0001

    # E103: Integrated Ownership = 0.65263158*0.40 + 0.52631579*0.30 = 0.41894737 -> 0.4189
    assert abs(id_to_ownership["http://example.org/entity/E103"] - 0.4189) <= 0.0001

def test_inherited_sanctions_values():
    """Verifies inherited sanction categories for flagged entities."""
    data = _load_report()
    high_risk = data["high_risk_subsidiaries"]
    id_to_sanctions = {item["entity_id"]: item["inherited_sanctions"] for item in high_risk}

    expected_sanctions = ["Financial", "Trade"]
    assert id_to_sanctions["http://example.org/entity/E101"] == expected_sanctions
    assert id_to_sanctions["http://example.org/entity/E102"] == expected_sanctions
    assert id_to_sanctions["http://example.org/entity/E103"] == expected_sanctions

def test_output_sorting():
    """Verifies high_risk_subsidiaries is sorted by effective_ownership descending, then entity_id ascending."""
    data = _load_report()
    high_risk = data["high_risk_subsidiaries"]
    
    ids = [item["entity_id"] for item in high_risk]
    expected_order = [
        "http://example.org/entity/E101",
        "http://example.org/entity/E102",
        "http://example.org/entity/E103"
    ]
    assert ids == expected_order, f"Expected order {expected_order}, got {ids}"

def test_inherited_sanctions_sorting():
    """Verifies inherited_sanctions arrays are sorted alphabetically ASCII with no duplicate entries."""
    data = _load_report()
    for item in data["high_risk_subsidiaries"]:
        sanctions = item["inherited_sanctions"]
        assert sanctions == sorted(list(set(sanctions))), f"Sanctions list {sanctions} is not sorted or has duplicates"
