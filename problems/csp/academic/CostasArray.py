"""
A costas array is a pattern of n marks on an n∗n grid, one mark per row and one per column,
in which the n∗(n−1)/2 vectors between the marks are all-different.

See problem 076 at CSPLib.

## Data
  a unique integer, the order of the grid

## Model
  constraints: AllDifferent

## Execution
  - python CostasArray.py -data=[number]

## Links
  - https://en.wikipedia.org/wiki/Costas_array
  - https://www.csplib.org/Problems/prob076/
  - https://www.cril.univ-artois.fr/XCSP22/competitions/csp/csp

## Tags
  academic, csplib, xcsp22
"""

from pycsp3 import *

n = data or 8

# x[i] is the row where is put the ith mark (on the ith column)
x = VarArray(size=n, dom=range(n))

satisfy(
    # all marks are on different rows (and columns)
    AllDifferent(x),

    # all displacement vectors between the marks must be different
    [AllDifferent(x[i] - x[i + d] for i in range(n - d)) for d in range(1, n - 1)]
)

""" Comments
1) how to break all symmetries?  x[0] <= math.ceil(n / 2), x[0] < x[-1], ... ? TODO
"""
