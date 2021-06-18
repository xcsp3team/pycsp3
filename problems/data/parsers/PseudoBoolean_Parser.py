from pycsp3.problems.data.parsing import *


def linear_objective():
    tokens = line().split()
    assert len(tokens) % 2 == 0 and tokens[0] == "min:" and tokens[-1] == ";"
    coeffs, nums = [int(tokens[i]) for i in range(1, len(tokens) - 1, 2)], [int(tokens[i][1:]) - 1 for i in range(2, len(tokens) - 1, 2)]
    return OrderedDict([("coeffs", coeffs), ("nums", nums)])


def linear_constraint():
    tokens = line().split()
    assert len(tokens) % 2 == 1 and tokens[-1] == ";"
    coeffs, nums = [int(tokens[i]) for i in range(0, len(tokens) - 3, 2)], [int(tokens[i][1:]) - 1 for i in range(1, len(tokens) - 3, 2)]
    return OrderedDict([("coeffs", coeffs), ("nums", nums), ("op", tokens[- 3]), ("limit", int(tokens[- 2]))])


t = numbers_in(line())
data["n"] = t[0]
data["e"] = t[1]

while next_line()[0] == "*":  # comments
    pass

data["constraints"] = []
if line()[0] == "m":
    data["objective"] = linear_objective()
else:
    data["objective"] = None
    data["constraints"].append(linear_constraint())

while next_line() is not None:
    if line()[0] != "*":
        data["constraints"].append(linear_constraint())

assert len(data["constraints"]) == data["e"]
