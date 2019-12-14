from pycsp3 import *

height, width = data.height, data.width
bugs, types = data.bugs, data.bugTypes
nBugs = len(bugs)
maxB = max(len(bugType.cells) for bugType in types)

# one variable per square in the grid, whose domain is -1..nbBugs-1
x = VarArray(size=[height, width], dom=range(-1, nBugs))

# n1[i] corresponds to the number of squares in x with value i
n1 = VarArray(size=nBugs, dom=range(nBugs + 1))

# n2[i] corresponds to the number of squares in x with a bug on it and with value i
n2 = VarArray(size=nBugs, dom=range(height * width + 1))

# the number of times a bug is in a rectangle whose index is different from the one of the bug
s = Var(dom=range(nBugs + 1))


def neighbors(i, j, k, l):
    return i == k and j in {l - 1, l + 1} or j == l and i in {k - 1, k + 1}


satisfy(
    # each bug square can either take its bug index for value or take the one of another bug of the same type
    [(x[bug.row][bug.col]) in types[bug.type].cells for bug in bugs],

    # symmetry breaking: a bug's square's value is smaller or equal to the bug's index
    [x[bug.row][bug.col] <= i for i, bug in enumerate(bugs)],

    [n1[type.cells[j]] <= (len(type.cells) - j) * type.length for type in types for j in range(1, maxB) if j < len(type.cells)],

    Cardinality(x, occurrences={i: n1[i] for i in range(nBugs)}),

    Cardinality([x[bug.row][bug.col] for bug in bugs], occurrences={i: n2[i] for i in range(nBugs)}),

    [n2[i] * types[bugs[i].type].length == n1[i] for i in range(nBugs)],

    Count(n2, value=0) == s,

    # if two squares have the same value, then all the squares in the rectangle they delimit must take this value
    [
        (x[i][j] != x[k][l]) | (x[i][j] == x[m][n])
        for (i, j, k, l, m, n) in product(range(height), range(width), range(height), range(width), range(height), range(width))
        if
        i <= m <= k and not neighbors(i, j, k, l) and (i != k or j < l) and min(j, l) <= n <= max(j, l) and (m != i or n != j) and (m != k or n != l)
        ]
)

maximize(s)
