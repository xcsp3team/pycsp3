"""
See https://en.wikipedia.org/wiki/Kakuro
See "Kakuro as a Constraint Problem" by Helmut Simonis

Example of Execution:
  python3 Kakuro.py -data=Kakuro_easy-000.json
"""

from pycsp3 import *

nRows, nCols, clues = data

# x[i][j] is the value put at row i and column j
x = VarArray(size=[nRows, nCols], dom=lambda i, j: range(1, 10) if clues[i][j].x == clues[i][j].y == 0 else None)


def structures():
    def h_scope(i, j):
        assert clues[i][j].x > 0
        t = []
        for k in range(j + 1, nCols):
            if clues[i][k].x != 0:
                break
            t.append(x[i][k])
        return t

    def v_scope(i, j):
        assert clues[i][j].y > 0
        t = []
        for k in range(i + 1, nRows):
            if clues[k][j].y != 0:
                break
            t.append(x[k][j])
        return t

    h = [(h_scope(i, j), clues[i][j].x) for i in range(nRows) for j in range(nCols) if clues[i][j].x > 0]
    v = [(v_scope(i, j), clues[i][j].y) for i in range(nRows) for j in range(nCols) if clues[i][j].y > 0]
    return h, v


horizontal, vertical = structures()

if not variant():
    satisfy(
        [Sum(scp) == clue for (scp, clue) in horizontal],

        [AllDifferent(scp) for (scp, _) in horizontal],

        [Sum(scp) == clue for (scp, clue) in vertical],

        [AllDifferent(scp) for (scp, _) in vertical]
    )

elif variant("table"):
    cache = dict()


    def table(limit, arity):  # tuples with different values summing to the specified limit
        n_values, offset = 9, 1  # hard coding for this context
        key = str(limit) + "_" + str(n_values) + "_" + str(arity) + "_" + str(offset)
        if key in cache:
            return cache[key]
        tuples = set()
        for comb in combinations(range(n_values), arity):
            if offset != 0:
                comb = [v + offset for v in comb]
            if sum(comb) == limit:
                for perm in permutations(range(arity)):
                    tuples.add(tuple(comb[perm[i]] for i in range(arity)))
        cache[key] = tuples
        return tuples


    satisfy(
        [scp in table(clue, len(scp)) for (scp, clue) in horizontal],

        [scp in table(clue, len(scp)) for (scp, clue) in vertical]
    )
