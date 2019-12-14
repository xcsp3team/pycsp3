from pycsp3.problems.data.dataparser import *

data.n, data.m = numbers_in(line())
data.pieces = [numbers_in(next_line()) for _ in range(data.n * data.m)]
