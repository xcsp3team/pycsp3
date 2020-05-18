from pycsp3.problems.data.parsing import *

data["n"] = number_in(line())
data["m"] = number_in(next_line())

nPairs = number_in(next_line())
p1 = list(zip(numbers_in(next_line()), numbers_in(next_line())))
p2 = list(zip(numbers_in(next_line()), numbers_in(next_line())))
assert nPairs == len(p1) == len(p2)
data["points"] = [[p1[i], p2[i]] for i in range(len(p1))]

