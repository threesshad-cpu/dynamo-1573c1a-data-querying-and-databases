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
    assert len(orders) == 43, "Expected 43 order results in report"
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
    expected_ids = ["O1", "O10C", "O11", "O12", "O15", "O15b", "O16", "O17", "O18", "O2", "O23", "O24", "O25", "O26", "O27", "O28", "O29", "O3", "O30", "O31", "O32", "O33", "O34", "O35", "O36", "O37", "O38", "O39", "O3_N1", "O3_N2", "O3b", "O4", "O40", "O41", "O42", "O5", "O6C", "O7", "O8", "O9", "OA", "OB", "OC"]
    assert [x["order_id"] for x in data["orders"]] == expected_ids


def _get_orders_map():
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {x["order_id"]: x for x in data["orders"]}


def test_order_O1_batch_rounding_and_parent_netting():
    """Verify Rule 1 batch rounding and parent netting for O1."""
    m = _get_orders_map(); assert m["O1"] == {"order_id":"O1","allocated_qty":12,"shortfall_qty":0,"limiting_resource":None}

def test_order_O2_aggregated_bom_explosion():
    """Verify aggregated BOM explosion and netting for O2."""
    m = _get_orders_map(); assert m["O2"] == {"order_id":"O2","allocated_qty":10,"shortfall_qty":0,"limiting_resource":None}

def test_order_O3_deterministic_substitution():
    """Verify ranked deterministic substitution and resulting shortfall for O3."""
    m = _get_orders_map(); assert m["O3"] == {"order_id":"O3","allocated_qty":6,"shortfall_qty":4,"limiting_resource":"L3"}

def test_order_O3_N1_substitute_tie_break():
    """Verify the substitute preference tie-break for O3_N1."""
    m = _get_orders_map(); assert m["O3_N1"] == {"order_id":"O3_N1","allocated_qty":5,"shortfall_qty":0,"limiting_resource":None}

def test_order_O3_N2_substitute_tie_break():
    """Verify the alternate substitute tie-break outcome for O3_N2."""
    m = _get_orders_map(); assert m["O3_N2"] == {"order_id":"O3_N2","allocated_qty":5,"shortfall_qty":0,"limiting_resource":None}

def test_order_O3b_substitute_tie_break():
    """Verify a failed substitute tie-break leaves the correct limiting pool for O3b."""
    m = _get_orders_map(); assert m["O3b"] == {"order_id":"O3b","allocated_qty":0,"shortfall_qty":10,"limiting_resource":"SUB_L3_B"}

def test_order_O4_gross_limiting_resource_and_tie_break():
    """Verify gross limiting-resource calculation and lexicographic tie-break for O4."""
    m = _get_orders_map(); assert m["O4"] == {"order_id":"O4","allocated_qty":3,"shortfall_qty":3,"limiting_resource":"L_TIE"}

def test_order_O5_stateful_depletion():
    """Verify stateful inventory and workcenter depletion across O5."""
    m = _get_orders_map(); assert m["O5"] == {"order_id":"O5","allocated_qty":9,"shortfall_qty":6,"limiting_resource":"WC1"}

def test_order_O6C_positive_partial_build_is_canceled_without_consumption():
    """Verify Rule 7 cancels a positive partial build without consuming state for O6C."""
    m = _get_orders_map(); assert m["O6C"] == {"order_id":"O6C","allocated_qty":0,"shortfall_qty":5,"limiting_resource":"L_CANCEL"}

def test_order_O7_proves_canceled_order_consumes_no_inventory():
    """Verify the canceled O6C order leaves inventory available for O7."""
    m = _get_orders_map(); assert m["O7"] == {"order_id":"O7","allocated_qty":2,"shortfall_qty":0,"limiting_resource":None}

def test_order_O8_deep_shared_bom_aggregation():
    """Verify deep shared-BOM aggregation across nested components for O8."""
    m = _get_orders_map(); assert m["O8"] == {"order_id":"O8","allocated_qty":4,"shortfall_qty":0,"limiting_resource":None}

def test_order_O9_carries_deep_subassembly_state_forward():
    """Verify deep subassembly state carries forward into O9."""
    m = _get_orders_map(); assert m["O9"] == {"order_id":"O9","allocated_qty":0,"shortfall_qty":6,"limiting_resource":"L5"}

def test_order_OA_equal_rank_substitutes_and_batch_rounding():
    """Verify equal-rank substitutes combined with batch rounding for OA."""
    m = _get_orders_map(); assert m["OA"] == {"order_id":"OA","allocated_qty":4,"shortfall_qty":4,"limiting_resource":"L5"}

def test_order_OB_deep_branch_cancellation():
    """Verify cancellation propagates through the deep BOM branch for OB."""
    m = _get_orders_map(); assert m["OB"] == {"order_id":"OB","allocated_qty":0,"shortfall_qty":5,"limiting_resource":"L7"}

def test_order_OC_proves_second_cancellation_is_side_effect_free():
    """Verify a second cancellation remains side-effect free for OC."""
    m = _get_orders_map(); assert m["OC"] == {"order_id":"OC","allocated_qty":2,"shortfall_qty":0,"limiting_resource":None}

def test_order_O10C_multi_parent_bom_capacity_cancellation():
    """Verify multi-parent BOM capacity causes the expected O10C cancellation boundary."""
    m = _get_orders_map(); assert m["O10C"] == {"order_id":"O10C","allocated_qty":5,"shortfall_qty":5,"limiting_resource":"WC5"}

def test_order_O11_proves_O10C_consumed_state():
    """Verify O11 observes the inventory state consumed by O10C."""
    m = _get_orders_map(); assert m["O11"] == {"order_id":"O11","allocated_qty":90,"shortfall_qty":10,"limiting_resource":"L9"}

def test_order_O12_scrap_formula():
    """Verify the batch scrap formula determines O12 allocation and shortage."""
    m = _get_orders_map(); assert m["O12"] == {"order_id":"O12","allocated_qty":6,"shortfall_qty":4,"limiting_resource":"L_SCRAP"}

def test_order_O15_boundary_cancellation_50():
    """Verify exactly 50 percent allocation is retained at the O15 cancellation boundary."""
    m = _get_orders_map(); assert m["O15"] == {"order_id":"O15","allocated_qty":5,"shortfall_qty":5,"limiting_resource":"L15"}

def test_order_O15b_boundary_cancellation_below_50():
    """Verify allocation below 50 percent triggers cancellation for O15b."""
    m = _get_orders_map(); assert m["O15b"] == {"order_id":"O15b","allocated_qty":0,"shortfall_qty":100,"limiting_resource":"L15b"}

def test_order_O16_lexicographical_tiebreaker():
    """Verify lexicographic tie-breaking selects the limiting resource for O16."""
    m = _get_orders_map(); assert m["O16"] == {"order_id":"O16","allocated_qty":5,"shortfall_qty":5,"limiting_resource":"WC10"}

def test_order_O17_substitute_floor_semantics():
    """Verify floor semantics for fractional substitute coverage in O17."""
    m = _get_orders_map(); assert m["O17"] == {"order_id":"O17","allocated_qty":9,"shortfall_qty":1,"limiting_resource":"L17"}

def test_order_O18_near_equal_bottlenecks():
    """Verify near-equal bottleneck ratios and tie handling for O18."""
    m = _get_orders_map(); assert m["O18"] == {"order_id":"O18","allocated_qty":7,"shortfall_qty":3,"limiting_resource":"L18A"}

def test_order_O23_global_shared_substitute_contention():
    """Verify global matching when multiple leaves contend for one shared substitute pool in O23."""
    m = _get_orders_map(); assert m["O23"] == {"order_id":"O23","allocated_qty":1,"shortfall_qty":0,"limiting_resource":None}

def test_order_O24_fractional_shared_ratio_contention():
    """Verify fractional substitute ratios under shared-pool contention for O24."""
    m = _get_orders_map(); assert m["O24"] == {"order_id":"O24","allocated_qty":2,"shortfall_qty":1,"limiting_resource":None}

def test_order_O25_ranked_shared_pool_with_private_fallback():
    """Verify ranked shared-pool allocation preserves a private fallback for O25."""
    m = _get_orders_map(); assert m["O25"] == {"order_id":"O25","allocated_qty":1,"shortfall_qty":1,"limiting_resource":None}

def test_order_O26_three_way_shared_matching():
    """Verify three-way shared substitute matching and deterministic allocation for O26."""
    m = _get_orders_map(); assert m["O26"] == {"order_id":"O26","allocated_qty":1,"shortfall_qty":1,"limiting_resource":None}

def test_order_O27_batch_contention_cancels_below_fifty_percent():
    """Verify shared-pool contention drives O27 below the 50 percent cancellation threshold."""
    m = _get_orders_map(); assert m["O27"] == {"order_id":"O27","allocated_qty":0,"shortfall_qty":5,"limiting_resource":"L27B"}

def test_order_O28_deep_shared_substitute_contention():
    """Verify shared substitute contention propagates through a deep BOM for O28."""
    m = _get_orders_map(); assert m["O28"] == {"order_id":"O28","allocated_qty":1,"shortfall_qty":1,"limiting_resource":"L28B"}

def test_order_O29_repeated_shared_pool_is_depleted():
    """Verify the repeated shared substitute pool is depleted by O29."""
    m = _get_orders_map(); assert m["O29"] == {"order_id":"O29","allocated_qty":0,"shortfall_qty":2,"limiting_resource":"L23A"}

def test_order_O30_repeated_fractional_pool_is_depleted():
    """Verify the repeated fractional shared pool is depleted by O30."""
    m = _get_orders_map(); assert m["O30"] == {"order_id":"O30","allocated_qty":0,"shortfall_qty":4,"limiting_resource":"L24A"}

def test_order_O31_repeated_ranked_pool_is_depleted():
    """Verify the repeated ranked shared pool is depleted by O31."""
    m = _get_orders_map(); assert m["O31"] == {"order_id":"O31","allocated_qty":0,"shortfall_qty":3,"limiting_resource":"L25A"}

def test_order_O32_repeated_three_way_pool_is_depleted():
    """After O26 consumes the shared pools, Rule 5's zero-ratio tie must select L26A."""
    m = _get_orders_map(); assert m["O32"] == {"order_id":"O32","allocated_qty":0,"shortfall_qty":3,"limiting_resource":"L26A"}

def test_order_O33_repeated_cancellation_state_is_preserved():
    """Verify repeated cancellation state remains preserved for O33."""
    m = _get_orders_map(); assert m["O33"] == {"order_id":"O33","allocated_qty":0,"shortfall_qty":5,"limiting_resource":"L27B"}

def test_order_O34_repeated_deep_pool_is_depleted():
    """Verify repeated deep shared-pool depletion produces the O34 bottleneck."""
    m = _get_orders_map(); assert m["O34"] == {"order_id":"O34","allocated_qty":0,"shortfall_qty":3,"limiting_resource":"L28A"}

def test_order_O35_late_global_matching_with_private_fallback():
    """Two primary leaves compete for one shared pool; private stock must be reserved for the leaf that cannot use another pool."""
    m = _get_orders_map(); assert m["O35"] == {"order_id":"O35","allocated_qty":3,"shortfall_qty":0,"limiting_resource":None}

def test_order_O36_late_matching_pool_depletion():
    """Verify the late shared matching pool is depleted and limits O36."""
    m = _get_orders_map(); assert m["O36"] == {"order_id":"O36","allocated_qty":0,"shortfall_qty":2,"limiting_resource":"L35A"}

def test_order_O37_late_deep_three_way_consumption():
    """A batch-sized multi-parent order must split a shared substitute pool across two deep branches."""
    m = _get_orders_map(); assert m["O37"] == {"order_id":"O37","allocated_qty":2,"shortfall_qty":0,"limiting_resource":None}

def test_order_O38_late_deep_pool_depletion():
    """Verify the deep shared pool consumed by O37 is depleted before O38."""
    m = _get_orders_map(); assert m["O38"] == {"order_id":"O38","allocated_qty":0,"shortfall_qty":2,"limiting_resource":"L36A"}

def test_order_O39_late_workcenter_state():
    """Verify late workcenter capacity is consumed statefully by O39."""
    m = _get_orders_map(); assert m["O39"] == {"order_id":"O39","allocated_qty":4,"shortfall_qty":0,"limiting_resource":None}

def test_order_O40_late_workcenter_cancellation():
    """The second order sees only 0.5 hours left, so even its first batch is impossible and WC37 is limiting."""
    m = _get_orders_map(); assert m["O40"] == {"order_id":"O40","allocated_qty":0,"shortfall_qty":4,"limiting_resource":"WC37"}

def test_order_O41_late_batch_generated_subassembly_boundary():
    """Using one stocked assembly plus a batch-produced assembly lands exactly at the 50-percent boundary."""
    m = _get_orders_map(); assert m["O41"] == {"order_id":"O41","allocated_qty":1,"shortfall_qty":1,"limiting_resource":"L38"}

def test_order_O42_late_generated_subassembly_carryover():
    """Verify generated subassembly inventory carries over from O41 into O42."""
    m = _get_orders_map(); assert m["O42"] == {"order_id":"O42","allocated_qty":1,"shortfall_qty":0,"limiting_resource":None}
