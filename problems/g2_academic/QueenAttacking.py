"""
Problem 029 on CSPLib

Illustration:
 - python3 QueenAttacking
 - python3 QueenAttacking -data=6

"""
from pycsp3 import *


def primes(limit):
    """ Returns a list of primes < limit """
    sieve = [True] * limit
    for i in range(3, int(limit ** 0.5) + 1, 2):
        if sieve[i]:
            sieve[i * i::2 * i] = [False] * ((limit - i * i - 1) // (2 * i) + 1)
    return [2] + [i for i in range(3, limit, 2) if sieve[i]]


n = data or 8
primes = primes(n * n)
m = len(primes)

# q is the cell for the queen
q = Var(dom=range(n * n))

# x[i] is the cell for the i+1th value
x = VarArray(size=n * n, dom=range(n * n))

satisfy(
    # all values are put in different cells
    AllDifferent(x),

    # ensuring a knight move between two successive values
    Slide(knight_attack(x[i], x[i + 1], n) for i in range(n * n - 1))
)

minimize(
    # minimizing the number of free primes
    Sum(~queen_attack(q, x[primes[i] - 1], n) for i in range(m))
)
