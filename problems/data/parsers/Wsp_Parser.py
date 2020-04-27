from pycsp3.problems.data.parsing import *

data["nSteps"] = number_in(line())
data["nUsers"] = number_in(next_line())
nConstraints = number_in(next_line())


def auth(line):
    s = line[line.index(":") + 1:].strip()
    return [i for i in range(len(s)) if s[i] == '1']


next_line()
data["auths"] = [auth(next_line()) for _ in range(data["nUsers"])]
next_line()
am, al = [], []
for _ in range(nConstraints):
    line = next_line().lower().strip()
    t = numbers_in(line)
    if "least" in line:
        al.append((t[0], t[1:]))
    elif "most" in line:
        am.append((t[0], t[1:]))
    else:
        raise AssertionError
data["atMost"] = am
data["atLeast"] = al



#
# if next_line().startswith("capacity"):
#     data.warehouseCapacities = numbers_in(line())
#     next_line()
# else:
#     data.warehouseCapacities = [data.nStores] * data.nWarehouses
#
# data.storeSupplyCosts = [numbers for numbers in [numbers_in(line) for line in remaining_lines()] if numbers]
