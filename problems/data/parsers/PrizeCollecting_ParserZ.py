from pycsp3.problems.data.dataparser import *

data["n"] = number_in(line())
data["prizes"] = [numbers_in(line)[1:] if i > 0 else numbers_in(line[line.index("["):])[1:] for i, line in enumerate(remaining_lines(skip_curr=True))]
