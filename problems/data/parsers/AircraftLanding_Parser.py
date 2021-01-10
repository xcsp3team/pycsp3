from pycsp3.problems.data.parsing import *

n = next_int()  # nPlanes
next_int()  # freezing time
times, costs, separations = [], [], []
for i in range(n):
    next_int()  # appearance time is useless for our current model
    times.append(OrderedDict([("earliest", next_int()), ("target", next_int()), ("latest", next_int())]))
    costs.append(OrderedDict(
        [("early_penalty", int(float(next_str()) * 100)), ("late_penalty", int(float(next_str()) * 100))]))  # [int(float(next_str()) * 100) for _ in range(2)])
    separations.append([next_int() for _ in range(n)])
data["n"] = n
data["times"] = times
data["costs"] = costs
data["separations"] = separations
