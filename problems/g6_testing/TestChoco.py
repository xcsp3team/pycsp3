from pycsp3 import *
from pycsp3.solvers.chocosolver import ChocoProcess, ChocoPy4J

n = 8

# x[i] is the ith note of the series
x = VarArray(size=n, dom=range(n))

satisfy(
    # notes must occur once, and so form a permutation
    AllDifferent(x),

    # intervals between neighbouring notes must form a permutation
    AllDifferent(abs(x[i + 1] - x[i]) for i in range(n - 1)),

    # tag(symmetry-breaking)
    x[0] < x[n - 1]
)


print("Compile:\n")
instance = compile()

print("\nStatic solving:\n")
solution = ChocoProcess().solve(instance)
print("solution:", solution)

print("\nPy4j solving:\n")
solver = ChocoPy4J()
solver.loadXCSP3(instance)

print("in progress")
