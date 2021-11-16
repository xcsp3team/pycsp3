"""
See Problem in MiniZinc -- https://github.com/MiniZinc/minizinc-benchmarks/blob/master/road-cons/road_naive.mzn

Example of Execution:
  python3 RoadConstruction.py -data=road_11.json
"""

from pycsp3 import *

budget, distances, costs = data
n = len(distances)

M = 10000

sp = VarArray(size=[n, n, n], dom=lambda i, j, k: range(M + 1) if i < j else None)

construct = VarArray(size=[n, n], dom=lambda i, j: {0, 1} if i < j else None)

satisfy(
    [(sp[i][j][0], construct[i][j]) in {(M, 0), (distances[i][j], 1)} for i, j in combinations(range(n), 2)],

    [sp[i][j][s + 1] == Minimum([sp[i][j][s]] + [sp[i][k][s] + sp[min(j, k)][max(j, k)][s] for k in range(i + 1, n) if j != k])
     for i, j in combinations(range(n), 2) for s in range(n - 1)],

    Sum(costs[i][j] * construct[i][j] for i, j in combinations(range(n), 2)) <= budget
)

minimize(
    Sum(sp[i][j][-1] for i, j in combinations(range(n), 2))
)
