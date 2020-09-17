"""
See QAPLib and https://en.wikipedia.org/wiki/Quadratic_assignment_problem

Example of Execution:
  python3 QuadraticAssignment.py -data=QuadraticAssignment_qap.json
  python3 QuadraticAssignment.py -data=QuadraticAssignment_example.txt -dataparser=QuadraticAssignment_Parser.py
"""

from pycsp3 import *

weights, distances = data  # facility weights and location distances
all_distances = {d for row in distances for d in row}
n = len(weights)

table = {(i, j, distances[i][j]) for i in range(n) for j in range(n) if i != j}

# x[i] is the location assigned to the ith facility
x = VarArray(size=n, dom=range(n))

# d[i][j] is the distance between the locations assigned to the ith and jth facilities
d = VarArray(size=[n, n], dom=lambda i, j: all_distances if i < j and weights[i][j] != 0 else None)

satisfy(
    # all locations must be different
    AllDifferent(x),

    # computing the distances
    [(x[i], x[j], d[i][j]) in table for i, j in combinations(range(n), 2) if weights[i][j] != 0]
)

minimize(
    #  minimizing summed up distances multiplied by flows
    d * weights
)


#  Note that:
#  a) d * weights is possible because d is of type 'ListVar' and because None values (and associated coeffs) will be discarded
#  b) weights * d is also possible because weights is of type 'ListInt' and because None values (and associated coeffs) will be discarded
#  c) one can also write of course:
#     Sum(d[i][j] * weights[i][j] for i, j in combinations(range(n), 2) if weights[i][j] != 0)
# d) the model is only valid for symmetric instances (and then, the bound must be multiplied by two)   TODO
