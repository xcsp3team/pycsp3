from pycsp3.problems.data.parsing import *

n = next_int()
nClues = next_int()

clues = [[0 for _ in range(n)] for _ in range(n)]
for _ in range(nClues):
    x, y, z = next_int() - 1, next_int() - 1, next_int()
    clues[x][y] = z

data["n"] = n
data["clues"] = clues
