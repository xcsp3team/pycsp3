from pycsp3 import *
from pycsp3.solvers.abscon import AbsConProcess, AbsconPy4J

x = VarArray(size=[10, 10], dom=range(150))
y = VarArray(size=[10, 10], dom=range(150))
z = VarArray(size=10, dom=range(150))

satisfy(
    min(abs(x[0][0]), abs(y[0][0])),
    max(abs(x[0][0]), min(y[0], z[1]))
)

print("Compile:\n")
instance = compile()

print("\nStatic solving:\n")
solution = AbsConProcess().solve(instance)
print("solution:", solution)

print("\nPy4j solving:\n")
solver = AbsconPy4J()
solver.loadXCSP3(instance)

print("in progress")
