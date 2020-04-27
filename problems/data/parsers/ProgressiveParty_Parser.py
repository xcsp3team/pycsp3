from pycsp3.problems.data.parsing import *

nBoats = next_int()
data["nPeriods"] = next_int()
data["boats"] = [OrderedDict([("capacity", v2), ("crewSize", v3)]) for _ in range(nBoats) for (v1, v2, v3) in [(next_int(), next_int(), next_int())]]
