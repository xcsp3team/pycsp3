"""
See https://en.wikipedia.org/wiki/Survo_puzzle

In a Survo puzzle, the task is to fill an m × n table with integers 1, 2, ..., m·n
so that each of these numbers appears only once and their row and column sums
are equal to integers given on the bottom and the right side of the table.
Often some of the integers are given readily in the table in order to guarantee
uniqueness of the solution and/or for making the task easier.

Example of Execution:
  python3 Survo.py -data=Survo-01.json
"""

from pycsp3 import *

r_sums, c_sums, matrix = data
m, n = len(r_sums), len(c_sums)

# x[i][j] is the value in the cell at row i and column j
x = VarArray(size=[m, n], dom=range(1, m * n + 1))

satisfy(
    # taking hints into consideration
    [x[i][j] == matrix[i][j] for i in range(m) for j in range(n) if matrix[i][j] != 0],

    # all numbers must appear once
    AllDifferent(x),

    # respecting sums on rows
    [Sum(x[i]) == r_sums[i] for i in range(m)],

    # respecting sums on columns
    [Sum(x[:, j]) == c_sums[j] for j in range(n)]
)
