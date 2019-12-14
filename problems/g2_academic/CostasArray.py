from pycsp3 import *

# Problem 076 at CSPLib
# NumberJack example

n = data.n

# x[i] is the row where is put the ith mark (on the ith column)
x = VarArray(size=n, dom=range(1, n + 1))


satisfy(
    AllDifferent(x),

    # all vectors between the marks must be different
    [AllDifferent(x[j] - x[j + i + 1] for j in range(n - i - 1)) for i in range(n - 2)]
)

# TODO how to break all symmetries?
# x[0] <= math.ceil(n / 2), x[0] < x[-1], ... ?