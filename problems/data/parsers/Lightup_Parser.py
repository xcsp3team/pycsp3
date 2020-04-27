from pycsp3.problems.data.parsing import *

nRows, nCols = numbers_in(line())
next_line()

data["grid"] = [[5 if token == "a" else -1 if token == "-" else int(token) for token in [next_str() for col in range(nCols)]] for row in range(nRows)]
