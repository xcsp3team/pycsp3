from pycsp3.problems.data.dataparser import *

data.n = number_in(line())
data.prizes = [numbers_in(line) if i > 0 else numbers_in(line[line.index("["):]) for i, line in enumerate(remaining_lines(skip_curr=True))]
