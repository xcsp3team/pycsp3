from pycsp3.problems.data.dataparser import *

data.n = len(numbers_in(line()))
data.clues = [numbers_in(line) for line in remaining_lines()]
data.n = len(data.clues)