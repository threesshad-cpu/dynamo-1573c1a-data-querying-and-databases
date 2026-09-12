import json
import os

REPORT_PATH = "/app/report.json"


def _load_report():
    assert os.path.exists(REPORT_PATH), f"{REPORT_PATH} does not exist"
    with open(REPORT_PATH, "r") as f:
        return json.load(f)


def test_file_exists_and_not_symlink():
    assert os.path.exists(REPORT_PATH), "report.json does not exist"
    assert not os.path.islink(REPORT_PATH), "report.json must not be a symlink"


def test_report_schema_keys():
    data = _load_report()
    assert set(("evaluation_date", "high_risk_subsidiaries", "summary")) <= set(data)
    assert data["evaluation_date"] == "2026-07-29"


def test_summary_counts():
    data = _load_report()
    summary = data["summary"]
    assert summary["total_entities_analyzed"] == 20
    assert summary["flagged_subsidiaries_count"] == 4


def test_exemption_handling():
    data = _load_report()
    flagged_ids = {item["entity_id"] for item in data["high_risk_subsidiaries"]}
    assert "http://example.org/entity/E104" not in flagged_ids


def test_high_risk_subsidiaries_count():
    assert len(_load_report()["high_risk_subsidiaries"]) == 4


def test_entity_names():
    data = _load_report()
    id_to_name = {item["entity_id"]: item.get("entity_name") for item in data["high_risk_subsidiaries"]}
    assert id_to_name == {
        "http://example.org/entity/E101": "Alpha Subsidiary",
        "http://example.org/entity/E103": "Gamma Shipping",
        "http://example.org/entity/E105": "Epsilon Maritime",
        "http://example.org/entity/E107": "Eta Infrastructure",
    }


def test_effective_ownership_values():
    data = _load_report()
    id_to_ownership = {item["entity_id"]: item["effective_ownership"] for item in data["high_risk_subsidiaries"]}
    expected = {
        "http://example.org/entity/E101": 0.4799,
        "http://example.org/entity/E103": 0.3990,
        "http://example.org/entity/E105": 0.3348,
        "http://example.org/entity/E107": 0.3252,
    }
    assert set(id_to_ownership) == set(expected)
    for entity_id, value in expected.items():
        assert abs(id_to_ownership[entity_id] - value) <= 0.0001


def test_inherited_sanctions_values():
    data = _load_report()
    id_to_sanctions = {item["entity_id"]: item["inherited_sanctions"] for item in data["high_risk_subsidiaries"]}
    assert id_to_sanctions == {
        "http://example.org/entity/E101": ["Financial", "Trade"],
        "http://example.org/entity/E103": ["Defense"],
        "http://example.org/entity/E105": ["Environmental"],
        "http://example.org/entity/E107": ["Defense"],
    }


def test_output_sorting():
    ids = [item["entity_id"] for item in _load_report()["high_risk_subsidiaries"]]
    assert ids == [
        "http://example.org/entity/E101",
        "http://example.org/entity/E103",
        "http://example.org/entity/E105",
        "http://example.org/entity/E107",
    ]


def test_inherited_sanctions_sorting():
    for item in _load_report()["high_risk_subsidiaries"]:
        sanctions = item["inherited_sanctions"]
        assert sanctions == sorted(set(sanctions))
