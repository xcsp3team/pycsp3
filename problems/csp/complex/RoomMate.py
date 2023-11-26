"""
In mathematics, economics and computer science, the stable-roommate problem is the problem of finding a stable matching for an even-sized set.
A matching is a separation of the set into disjoint pairs (‘roommates’).
The matching is stable if there are no two elements which are not roommates and which both prefer each other to their roommate under the matching.
This is distinct from the stable-marriage problem in that the stable-roommates problem allows matches between any two elements, not just between classes of
”men” and ”women”.
See wikipedia.org

## Data Example
  RoomMate_sr0006.json

## Model
  constraints: Element, Table

## Execution
  - python RoomMate.py -data=<datafile.json>
  - python RoomMate.py -variant=table -data=<datafile.json>

## Links
  - https://en.wikipedia.org/wiki/Stable_roommates_problem
  - https://link.springer.com/chapter/10.1007/978-3-319-07046-9_2
  - https://www.cril.univ-artois.fr/XCSP22/competitions/csp/csp

## Tags
  recreational, xcsp22
"""

from pycsp3 import *

preferences = data
n = len(preferences)


def pref_rank():
    pref = [[0] * n for _ in range(n)]  # pref[i][k] = j <-> ith guy has jth guy as kth choice
    rank = [[0] * n for _ in range(n)]  # rank[i][j] = k <-> ith guy ranks jth guy as kth choice
    for i in range(n):
        for k in range(len(preferences[i])):
            j = preferences[i][k] - 1  # because we start at 0
            rank[i][j] = k
            pref[i][k] = j
        rank[i][i] = len(preferences[i])
        pref[i][len(preferences[i])] = i
    return pref, rank


pref, rank = pref_rank()

# x[i] is the value of k, meaning that j = pref[i][k] is the paired agent
x = VarArray(size=n, dom=lambda i: range(len(preferences[i])))

if not variant():
    satisfy(
        (
            If(x[i] > rank[i][k], Then=x[k] < rank[k][i]),
            If(x[i] == rank[i][k], Then=x[k] == rank[k][i])
        ) for i in range(n) for k in pref[i] if k != i
    )

elif variant('table'):

    def T(i, k):
        return [(a, ANY) for a in x[i].dom if a < rank[i][k]] + [(rank[i][k], rank[k][i])] + \
            [(a, b) for a in x[i].dom if a > rank[i][k] for b in x[k].dom if b < rank[k][i]]


    satisfy(
        (x[i], x[k]) in T(i, k) for i in range(n) for k in pref[i] if k != i
    )

elif variant('hybrid'):

    satisfy(
        [(x[i], x[k]) in {(le(rank[i][k]), ANY), (ANY, lt(rank[k][i]))} for i in range(n) for k in pref[i] if k != i],
        [(x[i], x[k]) in {(ne(rank[i][k]), ANY), (ANY, rank[k][i])} for i in range(n) for k in pref[i] if k != i]
    )

""" Comments
1) It is very expensive to build starred tables for large instances.
"""
