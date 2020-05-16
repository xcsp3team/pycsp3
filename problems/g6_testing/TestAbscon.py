from pycsp3 import *
from pycsp3.solvers.abscon import AbsConProcess, AbsconPy4J
from pycsp3.solvers.chocosolver import ChocoProcess

x = VarArray(size=10, dom=range(20))
y = Var(range(20))

satisfy(
    x[0] == 5,
    y == Minimum(x),
    Sum(x) > 100
)

print("Compile:\n")
instance = compile()

print("\nStatic solving:\n")
solution = ChocoProcess().solve(instance)
print("solution:", solution)

print("\nPy4j solving:\n")
solver = AbsconPy4J()
solver.loadXCSP3(instance)

print("in progress")
