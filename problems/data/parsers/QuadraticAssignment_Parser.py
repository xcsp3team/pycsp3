from pycsp3.problems.data.parsing import *

n = next_int()
data["weights"] = [[next_int() for _ in range(n)] for _ in range(n)]
data["distances"] = [[next_int() for _ in range(n)] for _ in range(n)]
