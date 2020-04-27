from pycsp3.problems.data.parsing import *

n = number_in(line())
data["weights"] = [numbers_in(next_line()) for _ in range(n)]  # empty lines are discarced by the dataparser
data["distances"] = [numbers_in(next_line()) for _ in range(n)]
