import sys

with open("task/tests/test_outputs.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'assert len(orders) == 13, "Expected 13 order results in report"' in line:
        line = line.replace('13', '16')
    
    if 'expected_ids = ["O00_A", "O00_B", "O00_C", "O00_D", "O00_E", "O00_F", "O00_G", "O01", "O02", "O03", "O04", "O05", "O06"]' in line:
        line = '    expected_ids = ["O00_A", "O00_B", "O00_C", "O00_D", "O00_E", "O00_F", "O00_G", "O00_H", "O00_I", "O00_J", "O01", "O02", "O03", "O04", "O05", "O06"]\n'
    
    new_lines.append(line)

new_tests = """
def test_order_O00_H_allocation():
    \"\"\"Verifies that O00_H fails with correct limiting resource, distinguishing INITIAL vs LEFTOVER calculation.\"\"\"
    m = _get_orders_map()
    assert m["O00_H"]["allocated_qty"] == 1
    assert m["O00_H"]["shortfall_qty"] == 1
    assert m["O00_H"]["limiting_resource"] == "L15"


def test_order_O00_I_allocation():
    \"\"\"Verifies O00_I allocates correctly with substitute integer conversion constraints.\"\"\"
    m = _get_orders_map()
    assert m["O00_I"]["allocated_qty"] == 2
    assert m["O00_I"]["shortfall_qty"] == 1
    assert m["O00_I"]["limiting_resource"] == "L16"


def test_order_O00_J_allocation():
    \"\"\"Verifies O00_J consumes leftover substitute correctly if O00_I did not over-consume.\"\"\"
    m = _get_orders_map()
    assert m["O00_J"]["allocated_qty"] == 1
    assert m["O00_J"]["shortfall_qty"] == 0
    assert m["O00_J"]["limiting_resource"] is None
"""
new_lines.append(new_tests)

with open("task/tests/test_outputs.py", "w") as f:
    f.writelines(new_lines)
