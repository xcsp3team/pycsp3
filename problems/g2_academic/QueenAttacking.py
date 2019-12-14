from pycsp3 import *


# Problem 029 at CSPLib

def primes(limit):
    """ Returns a list of primes < limit """
    sieve = [True] * limit
    for i in range(3, int(limit ** 0.5) + 1, 2):
        if sieve[i]:
            sieve[i * i::2 * i] = [False] * ((limit - i * i - 1) // (2 * i) + 1)
    return [2] + [i for i in range(3, limit, 2) if sieve[i]]


n = data.n
primes = primes(n * n)
m = len(primes)

# q is the cell for the queen
q = Var(dom=range(n * n))

# x[i] is the cell for the i+1th value
x = VarArray(size=[n * n], dom=range(n * n))

# b[i] is 0 if the ith prime value is not attacked
b = VarArray(size=m, dom={0, 1})

satisfy(
    AllDifferent(x),

    Slide(knight_attack(x[i], x[i + 1], n) for i in range(n * n - 1)),

    [b[i] == ~queen_attack(q, x[primes[i] - 1], n) for i in range(m)]
)

minimize(
    Sum(b)
)
