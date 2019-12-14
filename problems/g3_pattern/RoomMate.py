from pycsp3 import *

preferences = data.preferences
n = len(preferences)

pref = [[0] * n for _ in range(n)]  # pref[i][k] = j <-> ith guy has jth guy as kth choice
rank = [[0] * n for _ in range(n)]  # rank[i][j] = k <-> ith guy ranks jth guy as kth choice

for i in range(n):
    for k in range(len(preferences[i])):
        j = preferences[i][k] - 1  # because we start at 0
        rank[i][j] = k
        pref[i][k] = j
    rank[i][i] = len(preferences[i])
    pref[i][len(preferences[i])] = i

# x[i] is the value of k, meaning that j = pref[i][k] is the paired agent
x = VarArray(size=n, dom=lambda i: range(len(preferences[i])))

satisfy(
    [imply(x[i] > rank[i][pref[i][k]], x[pref[i][k]] < rank[pref[i][k]][i]) for i in range(n) for k in range(len(preferences[i]))],

    [imply(x[i] == rank[i][pref[i][k]], x[pref[i][k]] == rank[pref[i][k]][i]) for i in range(n) for k in range(len(preferences[i]))]
)
