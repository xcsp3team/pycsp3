from pycsp3.problems.data.parsing import *

n = number_in(line())
budget = number_in(next_line())
t1 = numbers_in(next_line())
t2 = numbers_in(next_line())

data["budget"] = budget
data["distances"] = [[t1[i * n + j] for j in range(n)] for i in range(n)]
data["costs"] = [[t2[i * n + j] for j in range(n)] for i in range(n)]
