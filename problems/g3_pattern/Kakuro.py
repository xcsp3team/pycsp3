import itertools

from pycsp3 import *

nRows, nCols, clues = data.nRows, data.nCols, data.clues


def hscope(i, j):
    assert clues[i][j].x > 0
    t = []
    for k in range(j + 1, nCols):
        if clues[i][k].x != 0:
            break
        t.append(x[i][k])
    return t


def vscope(i, j):
    assert clues[i][j].y > 0
    t = []
    for k in range(i + 1, nRows):
        if clues[k][j].y != 0:
            break
        t.append(x[k][j])
    return t


cache = dict()

# x[i][j] is the value put at row i and column j
x = VarArray(size=[nRows, nCols], dom=lambda i, j: range(1, 10) if clues[i][j].x == clues[i][j].y == 0 else None)

if not variant():
    satisfy(
        [Sum(hscope(i, j)) == clues[i][j].x for i in range(nRows) for j in range(nCols) if clues[i][j].x > 0],

        [AllDifferent(hscope(i, j)) for i in range(nRows) for j in range(nCols) if clues[i][j].x > 0],

        [Sum(vscope(i, j)) == clues[i][j].y for i in range(nRows) for j in range(nCols) if clues[i][j].y > 0],

        [AllDifferent(vscope(i, j)) for i in range(nRows) for j in range(nCols) if clues[i][j].y > 0]
    )

elif variant("table"):
    def table(limit, nValues, arity, offset):  # tuples with different values summing to the specified limit
        key = str(limit) + "_" + str(nValues) + "_" + str(arity) + "_" + str(offset)
        if key in cache:
            return cache[key]
        tuples = set()
        combs = list(combinations(range(nValues), arity))
        perms = list(permutations(range(arity)))
        for comb in combs:
            if offset != 0:
                comb = [v + offset for v in comb]
            if sum(comb) == limit:
                for perm in perms:
                    tuples.add(tuple(comb[perm[i]] for i in range(arity)))
        cache[key] = tuples
        return tuples


    satisfy(
        [hscope(i, j) in table(clues[i][j].x, 9, len(hscope(i, j)), 1) for i in range(nRows) for j in range(nCols) if clues[i][j].x > 0],

        [vscope(i, j) in table(clues[i][j].y, 9, len(vscope(i, j)), 1) for i in range(nRows) for j in range(nCols) if clues[i][j].y > 0]
    )
