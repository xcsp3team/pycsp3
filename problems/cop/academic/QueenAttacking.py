"""
Problem 029 on CSPLib

Examples of Execution:
  python3 QueenAttacking.py
  python3 QueenAttacking.py -data=6
  python3 QueenAttacking.py -data=6 -variant=aux
  python3 QueenAttacking.py -data=6 -variant=hybrid
  python3 QueenAttacking.py -data=6 -variant=table
"""

from pycsp3 import *

n = data or 8
primes = all_primes(n * n)
m = len(primes)


def row(var):
    return var // n


def col(var):
    return var % n


# q is the cell for the queen
q = Var(dom=range(n * n))

# x[i] is the cell for the i+1th value
x = VarArray(size=n * n, dom=range(n * n))

if not variant():
    satisfy(
        # all values are put in different cells
        AllDifferent(x),

        # ensuring a knight move between two successive values
        [(d1 == 1) & (d2 == 2) | (d1 == 2) & (d2 == 1)
         for d1, d2 in [(abs(row(x[i]) - row(x[i + 1])), abs(col(x[i]) - col(x[i + 1]))) for i in range(n * n - 1)]]
    )

    minimize(
        # minimizing the number of free primes
        Sum((q == x[j]) | (row(q) != row(x[j])) & (col(q) != col(x[j])) & (abs(row(q) - row(x[j])) != abs(col(q) - col(x[j]))) for j in [p - 1 for p in primes])
    )

elif variant("aux"):
    # p[j] is 1 iff the j+1th prime number is not attacked by a queen
    p = VarArray(size=m, dom={0, 1})

    satisfy(
        # all values are put in different cells
        AllDifferent(x),

        # ensuring a knight move between two successive values
        [(d1 == 1) & (d2 == 2) | (d1 == 2) & (d2 == 1)
         for d1, d2 in [(abs(row(x[i]) - row(x[i + 1])), abs(col(x[i]) - col(x[i + 1]))) for i in range(n * n - 1)]],

        # determining if prime numbers are attacked by the queen
        [iff(p[j], (q == x[k]) | (row(q) != row(x[k])) & (col(q) != col(x[k])) & (abs(row(q) - row(x[k])) != abs(col(q) - col(x[k]))))
         for j, k in enumerate(p - 1 for p in primes)]
    )

    minimize(
        # minimizing the number of free primes
        Sum(p)
    )

elif variant("hybrid"):  # hybrid as compilation will build and combine both intension and extension constraints for the list of constraints about knight moves
    satisfy(
        # all values are put in different cells
        AllDifferent(x),

        # ensuring a knight move between two successive values
        [(abs(row(x[i]) - row(x[i + 1])), abs(col(x[i]) - col(x[i + 1]))) in {(1, 2), (2, 1)} for i in range(n * n - 1)]
    )

    minimize(
        # minimizing the number of free primes
        Sum((q == x[j]) | (row(q) != row(x[j])) & (col(q) != col(x[j])) & (abs(row(q) - row(x[j])) != abs(col(q) - col(x[j]))) for j in [p - 1 for p in primes])
    )

elif variant("table"):
    def neighbours(r1, c1):
        return [(r1 + r2) * n + c1 + c2 for (r2, c2) in [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)] if
                0 <= r1 + r2 < n and 0 <= c1 + c2 < n]


    table1 = {(i, j) for i in range(n * n) for j in neighbours(i // n, i % n)}
    table2 = {(i, j, 1 if (i == j) | (i // n != j // n) & (i % n != j % n) & (abs(i // n - j // n) != abs(i % n - j % n)) else 0) for i in range(n * n) for j in
              range(n * n)}

    # p[j] is 1 iff the j+1th prime number is not attacked by a queen
    p = VarArray(size=m, dom={0, 1})

    satisfy(
        # all values are put in different cells
        AllDifferent(x),

        # ensuring a knight move between two successive values
        [(x[i], x[i + 1]) in table1 for i in range(n * n - 1)],

        # determining if prime numbers are attacked by the queen
        [(q, x[k], p[j]) in table2 for j, k in enumerate(p - 1 for p in primes)]
    )

    minimize(
        # minimizing the number of free primes
        Sum(p)
        # (q == x[j]) | (row(q) != row(x[j])) & (col(q) != col(x[j])) & (abs(row(q) - row(x[j])) != abs(col(q) - col(x[j]))) for j in [p - 1 for p in primes])
    )

""" Comments
1) the variant hybrid involves the automatic introduction of auxiliary variables
"""
