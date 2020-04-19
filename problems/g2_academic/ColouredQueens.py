"""
The queens graph is a graph with n*n nodes corresponding to the squares of a chess-board.
There is an edge between nodes iff they are on the same row, column, or diagonal, i.e. if two queens on those squares would attack each other.
The coloring problem is to color the queens graph with n colors.
See Tom Kelsey, Steve Linton, Colva M. Roney-Dougal: New Developments in Symmetry Breaking in Search Using Computational Group Theory. AISC 2004: 199-210.

Examples of Execution:
  python3 ColouredQueens.py
  python3 ColouredQueens.py -data=10
"""

from pycsp3 import *

n = data or 8

# x[i][j] is the color at row i and column j
x = VarArray(size=[n, n], dom=range(n))

satisfy(
    # different colors on rows and columns
    AllDifferent(x, matrix=True),

    # different colors on downward diagonals
    [AllDifferent(dgn) for dgn in diagonals_down(x)],

    # different colors on upward diagonals
    [AllDifferent(dgn) for dgn in diagonals_up(x)]
)
