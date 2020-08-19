from pycsp3.problems.data.parsing import *

n = data["n"] = number_in(line())
p = data["prizes"] = [numbers_in(line)[1:] if i > 0 else numbers_in(line[line.index("["):])[1:] for i, line in enumerate(remaining_lines(skip_curr=True))]
for i in range(n):
    p[i][i] = 0
