from pycsp3 import *

n = 5
x = VarArray(size=[n, n], dom=range(1, n + 1))

table = list(permutations(range(1, n + 1)))

try:
    satisfy(x in table)
except AssertionError as e:
    print("Wrong test 1: Scope and tuples not compatible:", e)
    curser.queue_in.clear()

satisfy(
    # supports
    x[0] in table,

    # conflicts
    x[0] not in table
)

try:
    satisfy([1] * len(x[0]) in table)
except AssertionError as e:
    print("Wrong test 2: Parameter 1:", e)
    curser.queue_in.clear()

try:
    satisfy(x[0] in None)
except TypeError as e:
    print("Wrong test 3: Parameter 2:", e)
    curser.queue_in.clear()

table[1] = (1, 2)
try:
    satisfy(x[0] in table)
except AssertionError as e:
    print("Wrong test 4: Scope and tuples not compatible:", e)
    curser.queue_in.clear()

table = list(permutations(range(1, n + 1)))
table[1] = ("a", "b", "c", "d", "e")

try:
    satisfy(x[0] in table)
except TypeError as e:
    print("Wrong test 5: Table with different types:", e)
    curser.queue_in.clear()

table = [(1, 2, 3, 4, 5), (0.1, 0.2, 0.3, 0.4, 0.5)]

try:
    satisfy(
        # supports
        x[0] in table,

        # conflicts
        x[0] not in table
    )
except AssertionError as e:
    print("Wrong test 6: Table with different types:", e)
    curser.queue_in.clear()

try:
    satisfy(x[0][0] in table)
except AssertionError as e:
    print("Wrong test 7: Scope and tuples not compatible:", e)
    curser.queue_in.clear()

try:
    satisfy(x[0] in table[0])
except AssertionError as e:
    print("Wrong test 8: Bad type for operand of in:", e)
    curser.queue_in.clear()

# TODO
satisfy(
    # TODO is wrong or not ?
    x[0][0] in [0, 1]
)
