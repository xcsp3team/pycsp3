from pycsp3 import *

n = 5
x = VarArray(size=[n, n], dom=range(1, n + 1))

table = list(permutations(range(1, n + 1)))

try:
    Extension(scope=x, table=table, positive=True)
except AssertionError as e:
    print("Scope and tuples not compatible:")
    print(str(e))
    print()

satisfy(
    # supports
    Extension(scope=x[0], table=table, positive=True),

    # conflicts
    Extension(scope=x[0], table=table, positive=False)
)
try:
    satisfy(Extension(scope=[1] * len(x[0]), table=table, positive=True))
except TypeError as e:
    print("Parameter 1:")
    print(str(e))
    print()

try:
    satisfy(Extension(scope=x[0], table=None, positive=True))
except TypeError as e:
    print("Parameter 1:")
    print(str(e))
    print()

table[1] = (1, 2)
satisfy(
    # Wrong but too costly to check all lengths
    Extension(scope=x[0], table=table, positive=True)
)

table = list(permutations(range(1, n + 1)))
table[1] = ("a", "b", "c", "d", "e")

try:
    satisfy(Extension(scope=x[0], table=table, positive=True))
except TypeError as e:
    print("Table with different types:")
    print(str(e))
    print()

table = [(1, 2, 3, 4, 5), (0.1, 0.2, 0.3, 0.4, 0.5)]
satisfy(
    #  float and int in table
    Extension(scope=x[0], table=table, positive=True)
)

satisfy(
    # supports
    x[0] in table,

    # conflicts
    x[0] not in table
)

try:
    satisfy(x[0][0] in table)
except AssertionError as e:
    print("Scope and tuples not compatible:")
    print(str(e))
    print()

try:
    satisfy(x[0] in table[0])
except AssertionError as e:
    print("Bad type for operand of in:")
    print(str(e))
    print()

# TODO
satisfy(
    # TODO is wrong or not ?
    x[0][0] in [0, 1]
)
