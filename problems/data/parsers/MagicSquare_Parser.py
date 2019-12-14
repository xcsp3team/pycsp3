from pycsp3.problems.data.dataparser import *

data.n = next_int()
nClues = next_int()

data.clues = [[0 for _ in range(data.n)] for _ in range(data.n)]
for _ in range(nClues):
    x, y, z = next_int() - 1, next_int() - 1, next_int()
    data.clues[x][y] = z
