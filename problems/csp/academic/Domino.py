"""
See problem as defined in "Making AC3 an optimal algorithm" by Zhang and Yap, IJCAI 2001

Informally the DOMINO problem is an undi-rected constraint graph with a cycle and a trigger constraint.

Examples of Execution:
  python3 Domino.py
  python3 Domino.py -data=[300,300]
  python3 Domino.py -data=[300,300] -variant=table
"""

from pycsp3 import *

n, d = data  # number of dominoes and number of values

# x[i] is the value of the ith domino
x = VarArray(size=n, dom=range(d))

if not variant():
    satisfy(
        AllEqual(x),

        (x[0] + 1 == x[-1]) | ((x[0] == x[-1]) & (x[0] == d - 1))
    )

elif variant("table"):
    satisfy(
        [(x[i], x[i + 1]) in {(v, v) for v in range(d)} for i in range(n - 1)],

        (x[0], x[-1]) in {(v + 1, v) for v in range(d - 1)} | {(d - 1, d - 1)}
    )

""" Comments
1) Note that it is not possible to write: x[0] == x[-1] == v - 1
"""
