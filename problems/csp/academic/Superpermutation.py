"""
See https://en.wikipedia.org/wiki/Superpermutation

In combinatorial mathematics, a superpermutation on n symbols is a string that contains each permutation of n symbols
as a substring. While trivial superpermutations can simply be made up of every permutation listed together,
superpermutations can also be shorter (except for the trivial case of n = 1) because overlap is allowed.
For instance, in the case of n = 2, the superpermutation 1221 contains all possible permutations (12 and 21),
but the shorter string 121 also contains both permutations.

It has been shown that for 1 ≤ n ≤ 5, the smallest superpermutation on n symbols has length 1! + 2! + ... + n!.
The first four smallest superpermutations have respective lengths 1, 3, 9, and 33, forming the strings 1, 121,
123121321, and 123412314231243121342132413214321.
However, for n = 5, there are several smallest superpermutations having the length 153.

Examples of Execution:
  python3 Superpermutation -data=4
  python3 Superpermutation -data=4 -variant=table
"""

from math import factorial

from pycsp3 import *

n = data
m = sum(factorial(i) for i in range(1, n + 1))  # the length of the sequence; this is valid for 2 <= n <= 5 (see above)
assert 2 <= n <= 5, "for the moment, the model is valid for n between 2 and 5"

permutations = list(permutations(list(range(1, n + 1))))
nPermutations = len(permutations)

# x[i] is the ith value of the sequence
x = VarArray(size=m, dom=range(1, n + 1))

if not variant():

    # p[j] is the index in the sequence of the first value of the jth permutation
    p = VarArray(size=nPermutations, dom=range(m))

    satisfy(
        # all permutations start at different indexes  tag(redundant-constraints)
        AllDifferent(p),

        # ensuring that each permutation occurs in the sequence
        [x[p[j] + k] == permutations[j][k] for k in range(n) for j in range(nPermutations)]
    )

elif variant("table"):

    nPatterns = m - n + 1  # a pattern is a possible subsequence of length n
    gap = nPatterns - nPermutations  # the gap corresponds to the flexibility we have

    table = [(i, *t) for i, t in enumerate(permutations)]
    table += [(-1, *(v if k in (i, j) else ANY for k in range(n))) for v in range(n) for i, j in combinations(range(n), 2)]

    # y[i] is the index of the permutation x[i:i+n] or -1 if this is not a permutation
    y = VarArray(size=nPatterns, dom=range(-1, nPermutations))

    satisfy(
        # identifying each pattern (subsequence of n values)
        [(y[i], x[i:i + n]) in table for i in range(nPatterns)],

        # ensuring that each permutation occurs in the sequence
        Cardinality(y, occurrences={-1: range(gap + 1)} + {i: range(1, gap + 1) for i in range(nPermutations)})
    )

satisfy(
    # setting the first permutation  tag(symmetry-breaking)
    [x[i] == i + 1 for i in range(n)],

    # constraining a palindrome  tag(palindrome)
    [x[i] == x[-1 - i] for i in range(m // 2)]
)
