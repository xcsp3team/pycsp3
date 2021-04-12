"""
See https://en.wikipedia.org/wiki/Minesweeper_(video_game)

Examples of Execution:
  python3 MineSweeper.py
  python3 MineSweeper.py -data=MineSweeper-example.json
"""

from pycsp3 import *

puzzle = data or [
    [2, 3, -1, 2, 2, -1, 2, 1],
    [-1, -1, 4, -1, -1, 4, -1, 2],
    [-1, -1, -1, -1, -1, -1, 4, -1],
    [-1, 5, -1, 6, -1, -1, -1, 2],
    [2, -1, -1, -1, 5, 5, -1, 2],
    [1, 3, 4, -1, -1, -1, 4, -1],
    [0, 1, -1, 4, -1, -1, -1, 3],
    [0, 1, 2, -1, 2, 3, -1, 2]
]  # 4 solutions
n, m = len(puzzle), len(puzzle[0])

# x[i][j] is 1 iff there is a mine in the square at row i and column j
x = VarArray(size=[n, m], dom=lambda i, j: {0} if puzzle[i][j] >= 0 else {0, 1})

satisfy(
    # respecting clues of the puzzle
    Sum(x.around(i, j)) == puzzle[i][j] for i in range(n) for j in range(m) if puzzle[i][j] >= 0
)

""" Comments
1) around() is a predefined method on matrices of variables (of type ListVar).
   Hence, x.around(i, j) is equivalent to :
   [x[i + k][j + l] for k in [-1, 0, 1] for l in [-1, 0, 1] if 0 <= i + k < n and 0 <= j + l < m and (k, l) != (0, 0)]
"""
