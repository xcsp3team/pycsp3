from pycsp3 import *

# Problem 005 at CSPLib

n = data.n

# x[i] is the ith value of the sequence to be built.
x = VarArray(size=n, dom={-1, 1})

# y[k][i] is the ith product value required to compute the kth auto-correlation
y = VarArray(size=[n - 1, n - 1], dom={-1, 1}, when=lambda k, i: i < n - k - 1)

# c[k] is the value of the kth auto-correlation
c = VarArray(size=n - 1, dom=lambda k: range(-n + k + 1, n - k))

# s[k] is the square of the kth auto-correlation
s = VarArray(size=n - 1, dom=lambda k: {v ** 2 for v in range(n - k)})

satisfy(
    [y[k][i] == x[i] * x[i + k + 1] for k in range(n - 1) for i in range(n - k - 1)],

    [Sum(y[k]) == c[k] for k in range(n - 1)],

    [s[k] == c[k] * c[k] for k in range(n - 1)]
)


minimize(
    # minimizing the sum of the squares of the auto-correlation
    Sum(s)
)
