from pycsp3.problems.data.parsing import *

data["n"] = number_in(next_line())
data["m"] = number_in(next_line())
data["r"] = number_in(next_line())
next_line()
data["connections"] = [[v - 1 for v in numbers_in(line)] for line in remaining_lines()]
