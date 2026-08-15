import sys

with open("task/tests/test_outputs.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'assert len(orders) == 16, "Expected 16 order results in report"' in line:
        line = line.replace('16', '19')
    
    if 'expected_ids = ["O00_A", "O00_B", "O00_C", "O00_D", "O00_E", "O00_F", "O00_G", "O00_H", "O00_I", "O00_J", "O01", "O02", "O03", "O04", "O05", "O06"]' in line:
        line = '    expected_ids = ["O00_A", "O00_B", "O00_C", "O00_D", "O00_E", "O00_F", "O00_G", "O00_H", "O00_I", "O00_J", "O00_K", "O00_L", "O00_M", "O01", "O02", "O03", "O04", "O05", "O06"]\n'
    
    new_lines.append(line)

new_tests = """
def test_order_O00_K_allocation():
    \"\"\"Verifies O00_K correctly ignores Sub-Assemblies when finding limiting resources.\"\"\"
    m = _get_orders_map()
    assert m["O00_K"]["allocated_qty"] == 2
    assert m["O00_K"]["shortfall_qty"] == 1
    assert m["O00_K"]["limiting_resource"] == "WC10"


def test_order_O00_L_allocation():
    \"\"\"Verifies O00_L applies batch size rounding to child sub-assembly run hours.\"\"\"
    m = _get_orders_map()
    assert m["O00_L"]["allocated_qty"] == 0
    assert m["O00_L"]["shortfall_qty"] == 1
    assert m["O00_L"]["limiting_resource"] == "WC11"


def test_order_O00_M_allocation():
    \"\"\"Verifies O00_M applies math.ceil() on the scrap percentage calculation.\"\"\"
    m = _get_orders_map()
    assert m["O00_M"]["allocated_qty"] == 0
    assert m["O00_M"]["shortfall_qty"] == 1
    assert m["O00_M"]["limiting_resource"] == "L21"
"""
new_lines.append(new_tests)

with open("task/tests/test_outputs.py", "w") as f:
    f.writelines(new_lines)
