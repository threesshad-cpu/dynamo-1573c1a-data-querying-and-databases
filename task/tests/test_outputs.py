import json
import os
REPORT_PATH = os.environ.get("TEST_REPORT_PATH", "/app/report.json")

def _get_orders_map():
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        return {x["order_id"]: x for x in json.load(f)["orders"]}

def test_file_exists_and_not_symlink():
    """Verify the required report exists as a regular file."""
    assert os.path.exists(REPORT_PATH) and not os.path.islink(REPORT_PATH)

def test_report_schema_and_keys():
    """Verify the report schema, 43-order count, and field types."""
    with open(REPORT_PATH, "r", encoding="utf-8") as f: data=json.load(f)
    assert set(data)=={"orders"} and len(data["orders"])==43
    keys={"order_id","allocated_qty","shortfall_qty","limiting_resource"}
    for x in data["orders"]:
        assert isinstance(x,dict) and set(x)==keys
        assert isinstance(x["order_id"],str)
        assert isinstance(x["allocated_qty"],int) and not isinstance(x["allocated_qty"],bool)
        assert isinstance(x["shortfall_qty"],int) and not isinstance(x["shortfall_qty"],bool)
        assert x["limiting_resource"] is None or isinstance(x["limiting_resource"],str)

def test_output_sorting():
    """Verify orders are sorted by the required order_id."""
    ids=["O1","O10C","O11","O12","O15","O15b","O16","O17","O18","O2","O23","O24","O25","O26","O27","O28","O29","O3","O30","O31","O32","O33","O34","O35","O36","O37","O38","O39","O3_N1","O3_N2","O3b","O4","O40","O41","O42","O5","O6C","O7","O8","O9","OA","OB","OC"]
    with open(REPORT_PATH,"r",encoding="utf-8") as f: data=json.load(f)
    assert [x["order_id"] for x in data["orders"]]==ids

def _check(i,a,s,l): assert _get_orders_map()[i]=={"order_id":i,"allocated_qty":a,"shortfall_qty":s,"limiting_resource":l}

def test_order_O1(): """Verify batch rounding and parent netting."""; _check("O1",12,0,None)
def test_order_O2(): """Verify aggregated BOM explosion."""; _check("O2",10,0,None)
def test_order_O3(): """Verify deterministic substitution."""; _check("O3",6,4,"L3")
def test_order_O3_N1(): """Verify substitute tie-break N1."""; _check("O3_N1",5,0,None)
def test_order_O3_N2(): """Verify substitute tie-break N2."""; _check("O3_N2",5,0,None)
def test_order_O3b(): """Verify failed substitute tie-break."""; _check("O3b",0,10,"SUB_L3_B")
def test_order_O4(): """Verify gross limiting-resource tie-break."""; _check("O4",3,3,"L_TIE")
def test_order_O5(): """Verify stateful depletion."""; _check("O5",9,6,"WC1")
def test_order_O6C(): """Verify cancellation without consumption."""; _check("O6C",0,5,"L_CANCEL")
def test_order_O7(): """Verify canceled order consumes no inventory."""; _check("O7",2,0,None)
def test_order_O8(): """Verify deep shared BOM aggregation."""; _check("O8",4,0,None)
def test_order_O9(): """Verify deep subassembly state carryover."""; _check("O9",0,6,"L5")
def test_order_OA(): """Verify equal-rank substitutes and batch rounding."""; _check("OA",4,4,"L5")
def test_order_OB(): """Verify deep branch cancellation."""; _check("OB",0,5,"L7")
def test_order_OC(): """Verify second cancellation is side-effect free."""; _check("OC",2,0,None)
def test_order_O10C(): """Verify multi-parent capacity cancellation."""; _check("O10C",5,5,"WC5")
def test_order_O11(): """Verify O10C consumed state."""; _check("O11",90,10,"L9")
def test_order_O12(): """Verify scrap formula."""; _check("O12",6,4,"L_SCRAP")
def test_order_O15(): """Verify exact 50-percent cancellation boundary."""; _check("O15",5,5,"L15")
def test_order_O15b(): """Verify below-50-percent cancellation."""; _check("O15b",0,100,"L15b")
def test_order_O16(): """Verify lexicographical tie-break."""; _check("O16",5,5,"WC10")
def test_order_O17(): """Verify substitute floor semantics."""; _check("O17",9,1,"L17")
def test_order_O18(): """Verify near-equal bottlenecks."""; _check("O18",7,3,"L18A")
def test_order_O23(): """Verify global shared-substitute contention."""; _check("O23",1,0,None)
def test_order_O24(): """Verify fractional shared-ratio contention."""; _check("O24",2,1,None)
def test_order_O25(): """Verify ranked shared pool with private fallback."""; _check("O25",1,1,None)
def test_order_O26(): """Verify three-way shared matching."""; _check("O26",1,1,None)
def test_order_O27(): """Verify batch contention cancellation."""; _check("O27",0,5,"L27B")
def test_order_O28(): """Verify deep shared-substitute contention."""; _check("O28",1,1,"L28B")
def test_order_O29(): """Verify repeated shared-pool depletion."""; _check("O29",0,2,"L23A")
def test_order_O30(): """Verify repeated fractional-pool depletion."""; _check("O30",0,4,"L24A")
def test_order_O31(): """Verify repeated ranked-pool depletion."""; _check("O31",0,3,"L25A")
def test_order_O32(): """Verify three-way zero-ratio ASCII tie-break."""; _check("O32",0,3,"L26A")
def test_order_O33(): """Verify cancellation state is preserved."""; _check("O33",0,5,"L27B")
def test_order_O34(): """Verify repeated deep-pool depletion."""; _check("O34",0,3,"L28A")
def test_order_O35(): """Verify late global matching with private fallback."""; _check("O35",3,0,None)
def test_order_O36(): """Verify late matching-pool depletion."""; _check("O36",0,2,"L35A")
def test_order_O37(): """Verify late deep three-way consumption."""; _check("O37",2,0,None)
def test_order_O38(): """Verify late deep-pool depletion."""; _check("O38",0,2,"L36A")
def test_order_O39(): """Verify late workcenter state."""; _check("O39",4,0,None)
def test_order_O40(): """Verify late workcenter cancellation."""; _check("O40",0,4,"WC37")
def test_order_O41(): """Verify late generated-subassembly boundary."""; _check("O41",1,1,"L38")
def test_order_O42(): """Verify generated-subassembly carryover still respects depleted leaf stock."""; _check("O42",0,1,"L38")
