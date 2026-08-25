import json
import os

REPORT_PATH = os.environ.get("TEST_REPORT_PATH", "/app/report.json")


def test_file_exists_and_not_symlink():
    """Verify the required report exists as a regular file."""
    assert os.path.exists(REPORT_PATH) and not os.path.islink(REPORT_PATH)


def test_report_schema_and_keys():
    """Verify the report schema, order count, and field types required by the instruction."""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert set(data.keys()) == {"orders"}
    orders = data.get("orders", [])
    assert len(orders) == 29, "Expected 29 order results in report"
    expected_keys = {"order_id", "allocated_qty", "shortfall_qty", "limiting_resource"}
    for x in orders:
        assert isinstance(x, dict) and set(x.keys()) == expected_keys
        assert isinstance(x["order_id"], str)
        assert isinstance(x["allocated_qty"], int) and not isinstance(x["allocated_qty"], bool)
        assert isinstance(x["shortfall_qty"], int) and not isinstance(x["shortfall_qty"], bool)
        assert x["limiting_resource"] is None or isinstance(x["limiting_resource"], str)


def test_output_sorting():
    """Verify orders are sorted by order_id as required by the output specification."""
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    expected_ids = ["O1", "O10C", "O11", "O12", "O15", "O15b", "O16", "O17", "O18", "O2", "O23", "O24", "O25", "O26", "O27", "O28", "O3", "O3_N1", "O3_N2", "O3b", "O4", "O5", "O6C", "O7", "O8", "O9", "OA", "OB", "OC"]
    assert [x["order_id"] for x in data["orders"]] == expected_ids


def _get_orders_map():
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {x["order_id"]: x for x in data["orders"]}


def test_order_O1_batch_rounding_and_parent_netting():
    """Verify rule 1 netting and rule 2 batch rounding for O1."""
    m = _get_orders_map(); assert m["O1"] == {"order_id":"O1","allocated_qty":12,"shortfall_qty":0,"limiting_resource":None}

def test_order_O2_aggregated_bom_explosion():
    """Verify rule 3 aggregates shared component demand for O2."""
    m = _get_orders_map(); assert m["O2"] == {"order_id":"O2","allocated_qty":10,"shortfall_qty":0,"limiting_resource":None}

def test_order_O3_deterministic_substitution():
    """Verify rule 4 ranked substitution and resulting shortage for O3."""
    m = _get_orders_map(); assert m["O3"] == {"order_id":"O3","allocated_qty":6,"shortfall_qty":4,"limiting_resource":"L3"}

def test_order_O3_N1_substitute_tie_break():
    """Verify rule 4 alphabetical tie-breaking for equal-rank substitutes in O3_N1."""
    m = _get_orders_map(); assert m["O3_N1"] == {"order_id":"O3_N1","allocated_qty":5,"shortfall_qty":0,"limiting_resource":None}

def test_order_O3_N2_substitute_tie_break():
    """Verify rule 4 alphabetical tie-breaking for the second equal-rank case in O3_N2."""
    m = _get_orders_map(); assert m["O3_N2"] == {"order_id":"O3_N2","allocated_qty":5,"shortfall_qty":0,"limiting_resource":None}

def test_order_O3b_substitute_tie_break():
    """Verify rule 4 substitute depletion and tie-breaking after earlier orders in O3b."""
    m = _get_orders_map(); assert m["O3b"] == {"order_id":"O3b","allocated_qty":0,"shortfall_qty":10,"limiting_resource":"SUB_L3_B"}

def test_order_O4_gross_limiting_resource_and_tie_break():
    """Verify rule 5 gross limiting-resource ratios and lexicographic tie-breaking."""
    m = _get_orders_map(); assert m["O4"] == {"order_id":"O4","allocated_qty":3,"shortfall_qty":3,"limiting_resource":"L_TIE"}

def test_order_O5_stateful_depletion():
    """Verify sequential order processing updates shared inventory and capacity state."""
    m = _get_orders_map(); assert m["O5"] == {"order_id":"O5","allocated_qty":9,"shortfall_qty":6,"limiting_resource":"WC1"}

def test_order_O6C_positive_partial_build_is_canceled_without_consumption():
    """Verify rule 6 cancels a positive partial build below 50 percent without consuming state."""
    m = _get_orders_map(); assert m["O6C"] == {"order_id":"O6C","allocated_qty":0,"shortfall_qty":5,"limiting_resource":"L_CANCEL"}

def test_order_O7_proves_canceled_order_consumes_no_inventory():
    """Verify the cancellation rollback leaves inventory available to the following order."""
    m = _get_orders_map(); assert m["O7"] == {"order_id":"O7","allocated_qty":2,"shortfall_qty":0,"limiting_resource":None}

def test_order_O8_deep_shared_bom_aggregation():
    """Verify deep BOM traversal and shared subassembly aggregation."""
    m = _get_orders_map(); assert m["O8"] == {"order_id":"O8","allocated_qty":4,"shortfall_qty":0,"limiting_resource":None}

def test_order_O9_carries_deep_subassembly_state_forward():
    """Verify deep subassembly inventory depletion carries into the next order."""
    m = _get_orders_map(); assert m["O9"] == {"order_id":"O9","allocated_qty":0,"shortfall_qty":6,"limiting_resource":"L5"}

def test_order_OA_equal_rank_substitutes_and_batch_rounding():
    """Verify equal-rank substitution ordering combined with batch rounding."""
    m = _get_orders_map(); assert m["OA"] == {"order_id":"OA","allocated_qty":4,"shortfall_qty":4,"limiting_resource":"L5"}

def test_order_OB_deep_branch_cancellation():
    """Verify deep-branch allocation triggers the documented sub-50-percent cancellation."""
    m = _get_orders_map(); assert m["OB"] == {"order_id":"OB","allocated_qty":0,"shortfall_qty":5,"limiting_resource":"L7"}

def test_order_OC_proves_second_cancellation_is_side_effect_free():
    """Verify a canceled order does not alter resources used by the subsequent order."""
    m = _get_orders_map(); assert m["OC"] == {"order_id":"OC","allocated_qty":2,"shortfall_qty":0,"limiting_resource":None}

def test_order_O10C_multi_parent_bom_capacity_cancellation():
    """Verify multi-parent aggregation and workcenter capacity constrain O10C."""
    m = _get_orders_map(); assert m["O10C"] == {"order_id":"O10C","allocated_qty":5,"shortfall_qty":5,"limiting_resource":"WC5"}

def test_order_O11_proves_O10C_consumed_state():
    """Verify O10C's committed state affects the downstream O11 allocation."""
    m = _get_orders_map(); assert m["O11"] == {"order_id":"O11","allocated_qty":90,"shortfall_qty":10,"limiting_resource":"L9"}

def test_order_O12_scrap_formula():
    """Verify rule 2 applies percentage scrap and fixed setup scrap correctly."""
    m = _get_orders_map(); assert m["O12"] == {"order_id":"O12","allocated_qty":6,"shortfall_qty":4,"limiting_resource":"L_SCRAP"}

def test_order_O15_boundary_cancellation_50():
    """Verify rule 6 keeps an allocation at exactly 50 percent."""
    m = _get_orders_map(); assert m["O15"] == {"order_id":"O15","allocated_qty":5,"shortfall_qty":5,"limiting_resource":"L15"}

def test_order_O15b_boundary_cancellation_below_50():
    """Verify rule 6 cancels an allocation strictly below 50 percent."""
    m = _get_orders_map(); assert m["O15b"] == {"order_id":"O15b","allocated_qty":0,"shortfall_qty":100,"limiting_resource":"L15b"}

def test_order_O16_lexicographical_tiebreaker():
    """Verify rule 5 lexicographically breaks a limiting-resource tie."""
    m = _get_orders_map(); assert m["O16"] == {"order_id":"O16","allocated_qty":5,"shortfall_qty":5,"limiting_resource":"WC10"}

def test_order_O17_substitute_floor_semantics():
    """Verify rule 4 uses floor division for substitute capacity."""
    m = _get_orders_map(); assert m["O17"] == {"order_id":"O17","allocated_qty":9,"shortfall_qty":1,"limiting_resource":"L17"}

def test_order_O18_near_equal_bottlenecks():
    """Verify rule 5 selects the true minimum among near-equal bottleneck ratios."""
    m = _get_orders_map(); assert m["O18"] == {"order_id":"O18","allocated_qty":7,"shortfall_qty":3,"limiting_resource":"L18A"}

def test_order_O23_global_shared_substitute_contention():
    """Verify rule 7 globally allocates one shared substitute pool across two leaves."""
    m = _get_orders_map(); assert m["O23"] == {"order_id":"O23","allocated_qty":1,"shortfall_qty":0,"limiting_resource":None}

def test_order_O24_fractional_shared_ratio_contention():
    """Verify rule 7 handles fractional substitute conversion ratios without double-counting stock."""
    m = _get_orders_map(); assert m["O24"] == {"order_id":"O24","allocated_qty":2,"shortfall_qty":1,"limiting_resource":None}

def test_order_O25_ranked_shared_pool_with_private_fallback():
    """Verify rule 7 balances ranked shared stock against a private fallback leaf."""
    m = _get_orders_map(); assert m["O25"] == {"order_id":"O25","allocated_qty":2,"shortfall_qty":0,"limiting_resource":None}

def test_order_O26_three_way_shared_matching():
    """Verify rule 7 finds a globally feasible allocation across three competing leaves."""
    m = _get_orders_map(); assert m["O26"] == {"order_id":"O26","allocated_qty":1,"shortfall_qty":1,"limiting_resource":None}

def test_order_O27_batch_contention_cancels_below_fifty_percent():
    """Verify batch rounding plus shared contention still triggers rule 6 rollback below 50 percent."""
    m = _get_orders_map(); assert m["O27"] == {"order_id":"O27","allocated_qty":0,"shortfall_qty":5,"limiting_resource":"L27B"}

def test_order_O28_deep_shared_substitute_contention():
    """Verify shared-substitute contention is preserved through two top-level subassemblies."""
    m = _get_orders_map(); assert m["O28"] == {"order_id":"O28","allocated_qty":1,"shortfall_qty":1,"limiting_resource":"L28B"}
