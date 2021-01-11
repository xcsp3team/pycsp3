from pycsp3.problems.data.parsing import *

data["nTeams"] = number_in(line())
next_line()
t = [numbers_in(line) for line in remaining_lines(skip_curr=True)]
for row in t:
    for j, v in enumerate(row):
        if v == 2:
            row[j] = 0
data["venues"] = t
