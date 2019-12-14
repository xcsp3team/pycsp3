from pycsp3.problems.data.dataparser import *

nRows, nCols = next_int(), next_int()
data.rowPatterns = [[next_int() for _ in range(next_int())] for _ in range(nRows)]
data.colPatterns = [[next_int() for _ in range(next_int())] for _ in range(nRows)]
