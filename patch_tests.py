import sys

with open("task/tests/test_outputs.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'assert len(orders) == 11, "Expected 11 order results in report"' in line:
        line = line.replace('11', '13')
    
    if 'expected_ids = ["O00_A", "O00_B", "O00_C", "O00_D", "O00_E", "O01", "O02", "O03", "O04", "O05", "O06"]' in line:
        line = '    expected_ids = ["O00_A", "O00_B", "O00_C", "O00_D", "O00_E", "O00_F", "O00_G", "O01", "O02", "O03", "O04", "O05", "O06"]\n'
    
    new_lines.append(line)

new_tests = """
def test_order_O00_F_allocation():
    \"\"\"Verifies that O00_F fails allocation due to scrap rate requirement on L13.\"\"\"
    m = _get_orders_map()
    assert m["O00_F"]["allocated_qty"] == 0
    assert m["O00_F"]["shortfall_qty"] == 1
    assert m["O00_F"]["limiting_resource"] == "L13"


def test_order_O00_G_allocation():
    \"\"\"Verifies that O00_G fails allocation due to setup and run hours on WC5.\"\"\"
    m = _get_orders_map()
    assert m["O00_G"]["allocated_qty"] == 0
    assert m["O00_G"]["shortfall_qty"] == 1
    assert m["O00_G"]["limiting_resource"] == "WC5"
"""
new_lines.append(new_tests)

with open("task/tests/test_outputs.py", "w") as f:
    f.writelines(new_lines)
