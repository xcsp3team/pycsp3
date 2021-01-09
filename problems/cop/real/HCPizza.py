"""
See Practice Problem for Google Hash Code 2017
See https://www.academia.edu/31537057/Pizza_Practice_Problem_for_Hash_Code_2017

Examples of Execution:
  python3 HCPizza.py -data=HCPizza_tiny.json
  python3 HCPizza.py -data=HCPizza_tiny.txt -dataparser=HCPizza_Parser.py
"""

from pycsp3 import *

minIngredients, maxSize, pizza = data
nRows, nCols = len(pizza), len(pizza[0])
patterns = [(i, j) for i in range(1, min(maxSize, nRows) + 1) for j in range(1, min(maxSize, nCols) + 1) if 2 * minIngredients <= i * j <= maxSize]
nPatterns = len(patterns)


def possible_slices():
    _overlaps = [[[] for _ in range(nCols)] for _ in range(nRows)]
    _possibleSlices = [[[False for _ in range(nPatterns)] for _ in range(nCols)] for _ in range(nRows)]
    for i, j, k in product(range(nRows), range(nCols), range(nPatterns)):
        height, width = patterns[k][0], patterns[k][1]
        n_mushrooms, n_tomatoes = 0, 0
        for ib, jb in product(range(i, min(i + height, nRows)), range(j, min(j + width, nCols))):
            if pizza[ib][jb] == 0:
                n_mushrooms += 1
            else:
                n_tomatoes += 1
        if n_mushrooms >= data.minIngredients and n_tomatoes >= data.minIngredients:
            _possibleSlices[i][j][k] = True
            for ib, jb in product(range(i, min(i + height, nRows)), range(j, min(j + width, nCols))):
                _overlaps[ib][jb].append((i, j, k))
    return _overlaps, _possibleSlices


overlaps, slices = possible_slices()


def pattern_size(i, j, k):
    return (min(i + patterns[k][0], nRows) - i) * (min(j + patterns[k][1], nCols) - j)


# x[i][j][k] is 1 iff the slice with left top cell at (i,j) and pattern k is selected
x = VarArray(size=[nRows, nCols, nPatterns], dom=lambda i, j, k: {0, 1} if slices[i][j][k] else None)

# s[i][j][k] is the size of the slice with left top cell at (i,j) and pattern k (0 if the slice is not selected)
s = VarArray(size=[nRows, nCols, nPatterns], dom=lambda i, j, k: {0, pattern_size(i, j, k)} if slices[i][j][k] else None)

# z is the number of selected pizza cells
z = Var(range(nRows*nCols+1))

satisfy(
    # computing sizes of selected slices
    [(x[i][j][k], s[i][j][k]) in {(0, 0), (1, pattern_size(i, j, k))} for i, j, k in product(range(nRows), range(nCols), range(nPatterns)) if slices[i][j][k]],

    # ensuring that no two slices overlap
    [Sum([x[t[0]][t[1]][t[2]] for t in overlaps[i][j]]) <= 1 for i in range(nRows) for j in range(nCols) if len(overlaps[i][j]) > 1],

    Sum(s) == z
)

maximize(
    # maximizing the number of selected pizza cells
    z
)
