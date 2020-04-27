from pycsp3.problems.data.parsing import *

t = numbers_in(line())
data["n"] = t[0]
data["m"] = t[1]
data["pieces"] = [numbers_in(next_line()) for _ in range(t[0] * t[1])]
