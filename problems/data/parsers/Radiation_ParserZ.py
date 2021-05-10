from pycsp3.problems.data.parsing import *

skip_empty_lines(or_prefixed_by="%")
nRows = number_in(line())
next_line()
skip_empty_lines(or_prefixed_by="%")
nCols = number_in(line())
next_line()
skip_empty_lines(or_prefixed_by="%")
data["intensities"] = [numbers_in(next_line()) for _ in range(nRows)]


