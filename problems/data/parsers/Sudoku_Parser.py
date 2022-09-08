from pycsp3.problems.data.parsing import *

data["n"] = n = len(numbers_in(line()))
data["clues"] = [numbers_in(line) for line in remaining_lines()]
