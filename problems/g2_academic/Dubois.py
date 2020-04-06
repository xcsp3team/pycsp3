"""
This problem has been conceived by Olivier Dubois, and submitted to the second DIMACS Implementation Challenge.
Dubois's generator produces contradictory 3-SAT instances that seem very difficult to be solved by any general method.
Given an integer n, called the degree, Dubois's process allows us to construct a 3-SAT contradictory instance with 3 * n variables and 2 * n clauses,
each of them having 3 literals.

Examples of Execution:
  python3 Dubois.py
  python3 Dubois.py -data=10
"""
from pycsp3 import *

n = data or 8

table1 = {(0, 0, 1), (0, 1, 0), (1, 0, 0), (1, 1, 1)}
table2 = {(0, 0, 0), (0, 1, 1), (1, 0, 1), (1, 1, 0)}

x = VarArray(size=3 * n, dom={0, 1})

satisfy(
    (x[2 * n - 2], x[2 * n - 1], x[0]) in table1,

    [(x[i], x[2 * n + i], x[i + 1]) in table1 for i in range(n - 2)],

    [(x[n - 2 + i], x[3 * n - 2], x[3 * n - 1]) in table1 for i in range(2)],

    [(x[i], x[4 * n - 3 - i], x[i - 1]) in table1 for i in range(n, 2 * n - 2)],

    (x[2 * n - 2], x[2 * n - 1], x[2 * n - 3]) in table2
)
