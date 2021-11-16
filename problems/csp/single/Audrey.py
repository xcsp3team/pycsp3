"""
Little Problem given by Audrey at n-Side (see problem in OscaR).

Based on a little game I used to play in high school when I was getting bored in the classroom...
Draw a ten cells by ten cells board.
The purpose is to fill in all cells with numbers from 0 to 99.
You start by writing 0 in whatever cell.
From there on, you need to write the 1 by moving around in one of the following ways:
  - Move by 3 cells horizontally or vertically
  - Or move by 2 cells diagonally
Then, starting from the 1, you need to write the 2 using the same permitted moves, and so on.

The problem can be generalized for any order n.

Examples of Execution:
  python3 Audrey.py
  python3 Audrey.py -data=10
  python3 Audrey.py -data=10 -variant=display1
  python3 Audrey.py -data=10 -variant=display2
"""

from pycsp3 import *

n = data or 10
n2 = n * n


def reachable(i, j):
    possible_cells = [(i - 3, j), (i + 3, j), (i, j - 3), (i, j + 3), (i - 2, j - 2), (i - 2, j + 2), (i + 2, j - 2), (i + 2, j + 2)]
    return {k * n + l for k, l in possible_cells if 0 <= k < n and 0 <= l < n}


# x[i] is the index of the cell of the board following the ith cell in the circuit
x = VarArray(size=n2, dom=lambda i: reachable(i // n, i % n))

satisfy(
    # ensuring that we build a circuit
    Circuit(x)
)

if variant("display1"):
    # y[i] is the value put in the ith cell of the board
    y = VarArray(size=n2, dom=range(n2))

    satisfy(
        # linking values of the board
        [y[x[i]] == (y[i] + 1) % n2 for i in range(n2)],

        # putting 0 in the first cell  tag(symmetry-breaking)
        y[0] == 0
    )

elif variant("display2"):
    # b[i][j] is the value put in the cell at row i and column j of the board
    b = VarArray(size=[n, n], dom=range(n2))

    satisfy(
        # linking values of the board
        [b[x[i] // n, x[i] % n] == (b[i // n][i % n] + 1) % n2 for i in range(n2)],

        # putting 0 in the first cell  tag(symmetry-breaking)
        b[0][0] == 0
    )

""" Comments
1) the main model variant is sufficient to compute solutions.
   It is the fastest model. Hence, in a complex-world application, 
   adding constraints for pure presentational issue should be carefully thought. 
2) the variant 'display1' allows us to display the values (and not only the chaining).
   From this variant, to really get a matrix being printed, on can add:
     b = VarArray(size=[n, n], dom=range(n2))
     satisfy(
       b[i // n][i % n] == y[i] for i in range(n2)
     )
3) the variant 'display2' allows us to directly print the values in a matrix.
   This involves a constraint 'ElementMatrix' whose computed value must be equal to a variable.    
4) note that b[x[i] // n][x[i] % n] is not correct: we need to use indexing extension based on slices (as in numpy)
5) we obtain 96 solutions for n=5 with the three variants.
"""
