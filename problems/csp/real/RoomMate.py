"""
See https://en.wikipedia.org/wiki/Stable_roommates_problem
See "Stable Roommates and Constraint Programming" by Patrick Prosser. CPAIOR 2014: 15-28

Example of Execution:
  python3 RoomMate.py -data=RoomMate_sr0006.json
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

satisfy(
    (imply(x[i] > rank[i][k], x[k] < rank[k][i]), imply(x[i] == rank[i][k], x[k] == rank[k][i])) for i in range(n) for k in pref[i] if k != i
)


