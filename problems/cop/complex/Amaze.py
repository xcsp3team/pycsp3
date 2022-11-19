"""
See Problem in MiniZinc -- https://github.com/MiniZinc/minizinc-benchmarks/tree/master/amaze

Given a grid containing pairs of numbers (ranging from 1 to a greater value), connect the pairs (e.g. 1 to 1; 2 to 2; etc)
by drawing a line horizontally and vertically, but not diagonally.
The lines must never cross.

Example of Execution:
  python3 Amaze.py -data=Amaze_simple.json
"""

from pycsp3 import *

n, m, points = data  # points[v] gives the pair of points for value v+1
nValues = len(points) + 1  # number of pairs of points + 1 (for 0)
free_cells = [(i, j) for i in range(1, n + 1) for j in range(1, m + 1) if (i, j) not in [tuple(p) for pair in points for p in pair]]

# x[i][j] is the value at row i and column j (a boundary is put around the board).
x = VarArray(size=[n + 2, m + 2], dom=lambda i, j: {0} if i in {0, n + 1} or j in {0, m + 1} else range(nValues))

table = ({(0, ANY, ANY, ANY, ANY)}
         | {tuple(ne(v) if k in (i, j) else v for k in range(5)) for v in range(1, nValues) for i, j in combinations(range(1, 5), 2)})

satisfy(
    # putting two occurrences of each value on the board
    [x[i, j] == v for v in range(1, nValues) for i, j in points[v - 1]],

    # each cell with a fixed value has exactly one neighbour with the same value
    [Count([x[i - 1][j], x[i + 1][j], x[i][j - 1], x[i][j + 1]], value=v) == 1 for v in range(1, nValues) for i, j in points[v - 1]],

    # each empty cell either contains 0 or has exactly two neighbours with the same value
    [(x[i][j], x[i - 1][j], x[i + 1][j], x[i][j - 1], x[i][j + 1]) in table for i, j in free_cells]
)

minimize(
    Sum(x)
)

""" Comments
1) the table contains (hybrid) conditions, which makes code more compact than:
  table = ({(0, ANY, ANY, ANY, ANY)}
      | {(v, v, v, v1, v2) for v in range(1, nValues) for v1 in range(nValues) for v2 in range(nValues) if v1 != v and v2 != v}
      | {(v, v, v1, v, v2) for v in range(1, nValues) for v1 in range(nValues) for v2 in range(nValues) if v1 != v and v2 != v}
          ...
  the hybrid conditions are automatically converted to form starred tuples except if the option -keephybrid is set

2) even if  data come from a text file via a parser that builds tuples (and not lists)
   so, we have to write tuple(p) because tuples (in data) are automatically converted to lists

3) old code:
 for v in range(1,nValues):
     for i, j in combinations(range(1, 5), 2):
         for vv in range(nValues):
             if v !=vv:
                  table |=  {tuple(vv if k in (i, j) else v for k in range(5))}
"""
