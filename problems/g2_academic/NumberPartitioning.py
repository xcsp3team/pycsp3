from pycsp3 import *

# Problem 049 at CSPLib

n = data.n
assert n % 2 == 0, "The value of n must be even"

# x[i] is the ith value of the first set
x = VarArray(size=n // 2, dom=range(1, n + 1))

# y[i] is the ith value of the second set
y = VarArray(size=n // 2, dom=range(1, n + 1))

# cx[i] is the square of the ith value of the first set
cx = VarArray(size=n // 2, dom=range(1, n * n + 1))

# cy[i] is the square of the ith value of the second set
cy = VarArray(size=n // 2, dom=range(1, n * n + 1))

satisfy(
    AllDifferent(x + y),

    # tag(power1)
    [
        Sum(x) == n * (n + 1) // 4,
        Sum(y) == n * (n + 1) // 4
    ],

    # tag(power2)
    [
        [cx[i] == x[i] * x[i] for i in range(n // 2)],
        [cy[i] == y[i] * y[i] for i in range(n // 2)],
        Sum(cx) == n * (n + 1) * (2 * n + 1) // 12,
        Sum(cy) == n * (n + 1) * (2 * n + 1) // 12
    ],

    # tag(symmetry-breaking)
    [
        x[0] == 1,
        Increasing(x, strict=True),
        Increasing(y, strict=True)
    ]
)
