from pycsp3 import *

n = 5
x = VarArray(size=[n, n], dom=range(1, n + 1))

table = list(permutations(range(1, n + 1)))

try:
    x in table
except AssertionError as e:
    print("Scope and tuples not compatible:", e)

satisfy(
    # supports
    x[0] in table,

    # conflicts
    x[0] not in table
)
try:
    satisfy([1] * len(x[0]) in table)
except TypeError as e:
    print("Parameter 1:", e)

try:
    satisfy(x[0] in None)
except TypeError as e:
    print("Parameter 1:", e)

table[1] = (1, 2)
satisfy(
    # Wrong but too costly to check all lengths
    x[0] in table
)

table = list(permutations(range(1, n + 1)))
table[1] = ("a", "b", "c", "d", "e")

try:
    satisfy(x[0] in table)
except TypeError as e:
    print("Table with different types:", e)

table = [(1, 2, 3, 4, 5), (0.1, 0.2, 0.3, 0.4, 0.5)]
satisfy(
    #  float and int in table
    x[0] in table
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
    print("Scope and tuples not compatible:", e)

try:
    satisfy(x[0] in table[0])
except AssertionError as e:
    print("Bad type for operand of in:", e)

# TODO
satisfy(
    # TODO is wrong or not ?
    x[0][0] in [0, 1]
)
