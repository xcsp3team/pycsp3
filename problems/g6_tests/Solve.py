from pycsp3 import *
from pycsp3.solvers.abscon import AbsConProcess, AbsconPy4J

x = VarArray(size=[10, 10], dom=range(150))
y = VarArray(size=[10, 10], dom=range(150))
z = VarArray(size=[10], dom=range(150))

satisfy(
    min(abs(x[0][0]), abs(y[0][0])),
    max(abs(x[0][0]), min(y[0], z[1]))
)

print("Compile:")
print("")
xcsp = compile()

print("")
print("Static solving:")
print("")
solution = AbsConProcess().solve(xcsp)
print("solution:", solution)

print("")
print("Py4j solving:")
print("")
solver = AbsconPy4J()
solver.loadXCSP3(xcsp)

print("in progress")
