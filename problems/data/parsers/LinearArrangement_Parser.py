from pycsp3.problems.data.parsing import *

n = number_in(line())
edges = [(i, j) for i in range(n) for j in numbers_in(next_line())[1:] if i < j]

data["n"] = n
data["edges"] = edges
