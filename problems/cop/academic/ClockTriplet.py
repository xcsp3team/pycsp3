"""
Clock Triplet Problem -- http://www.f1compiler.com/samples/Dean%20Clark%27s%20Problem.f1.html

The problem was originally posed by Dean Clark and then presented to a larger audience by Martin Gardner.
The problem was discussed in Dr. Dobbs's Journal, May 2004 in an article  by Timothy Rolfe.
According to the article, in his August 1986 column for Isaac Asimov's Science Fiction Magazine,
Martin Gardner presented this problem:
  Now for a curious little combinatorial puzzle involving the twelve numbers on the face of a clock.
  Can you rearrange the numbers (keeping them in a circle) so no triplet of adjacent numbers has a sum higher
  than 21? This is the smallest value that the highest sum of a triplet can have.

Timothy Rolfe solves the problem using a rather complex algorithm and also presents a generic algorithm
for numbers other than 12 (clock numbers) and 21 (highest sums of triplets).
The main emphasis of the algorithm was put on the computational speed.
The article stressed the fact that a simple backtracking algorithm would be simply too slow
due to the number of permutations.

The model here is given in a general form.

Example of Execution:
  python3 ClockTriplet.py -data=[3,12]
"""

from pycsp3 import *

r, n = data or (3, 12)

# x[i] is the ith number in the circle
x = VarArray(size=n, dom=range(1, n + 1))

# z is the minimal value such that any (circular) subsequence of x  of size r is less than or equal to z
z = Var(range(sum(n - v for v in range(r)) + 1))

satisfy(
    # a permutation is required
    AllDifferent(x),

    # any subsequence of size r must be less than or equal to z
    [Slide(Sum(x[j] for j in [(i + k) % n for k in range(r)]) <= z for i in range(n))],

    # tag(symmetry-breaking)
    [x[0] == 1, x[1] < x[-1]]
)

minimize(
    z
)

""" Comments
1) the call to Slide can be avoided, but the interest is two-fold:
  - getting a more compact XCSP3 file
  - letting solvers the possibility of exploiting the meta-constraint Slide (stronger filtering)
"""
