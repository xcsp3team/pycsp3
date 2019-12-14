from pycsp3 import *

v, b, r = data.v, data.b, data.r


def lb():
    rv = r * v
    floor_rv, ceil_rv = rv // b, rv // b + (1 if rv % b != 0 else 0)
    num, den = (ceil_rv * ceil_rv * (rv % b) + floor_rv * floor_rv * (b - rv % b) - rv), v * (v - 1)
    return num // den + (1 if num % den != 0 else 0)


# objective variable
z = Var(dom=range(lb(), b + 1))

# x[i][j] is the value at row i and column j
x = VarArray(size=[v, b], dom={0, 1})

satisfy(
    Sum(x[i]) == r for i in range(v)
)

if not variant():
    satisfy(
        Sum(x[i] * x[j]) <= z for i in range(v) for j in range(i + 1, v)
    )

elif variant("aux"):
    #  scalar variables
    s = VarArray(size=[v, v, b], dom={0, 1}, when=lambda i, j, k: i < j)

    satisfy(
        [s[i][j][k] == x[i][k] * x[j][k] for i in range(v) for j in range(i + 1, v) for k in range(b)],

        # at most lambda
        [Sum(s[i][j]) <= z for i in range(v) for j in range(i + 1, v)]
    )

satisfy(
    # tag(symmetry-breaking)
    LexIncreasing(x, matrix=True)
)

minimize(z)
