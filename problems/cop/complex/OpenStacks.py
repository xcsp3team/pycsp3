""""
See https://ipg.host.cs.st-andrews.ac.uk/challenge/

Examples of Execution:
  python3 OpenStacks.py -data=OpenStacks_example.json -variant=m1
  python3 OpenStacks.py -data=OpenStacks_example.json -variant=m2
"""

from pycsp3 import *

orders = data
n, m = len(orders), len(orders[0])  # n orders (customers), m possible products

if variant("m1"):
    def table1(i):
        v = sum(orders[i])
        return [(0, 0, 0)] + [(i, ANY, 1) for i in range(1, v)] + [(v, 0, 0), (v, 1, 1)]


    # p[j] is the period (time) of the jth product
    p = VarArray(size=m, dom=range(m))

    # np[i][j] is the number of products made at time j and required by customer i
    np = VarArray(size=[n, m], dom=lambda i, j: range(sum(orders[i]) + 1))

    # r[i][t] is 1 iff the product made at time t concerns customer i
    r = VarArray(size=[n, m], dom={0, 1})

    # o[i][t] is 1 iff the stack is open for customer i at time t
    o = VarArray(size=[n, m], dom={0, 1})

    satisfy(
        # all products are scheduled at different times
        AllDifferent(p),

        [orders[i][p[j]] == r[i][j] for i in range(n) for j in range(m)],

        [np[i][j] == (r[i][j] if j == 0 else np[i][j - 1] + r[i][j]) for i in range(n) for j in range(m)],

        [(np[i][j], r[i][j], o[i][j]) in table1(i) for i in range(n) for j in range(m)],
    )

    minimize(
        # minimizing the number of stacks that are simultaneously open
        Maximum(Sum(o[:, t]) for t in range(m))
    )

elif variant("m2"):
    def table2(t):
        return {(ANY, te, 0) for te in range(t)} | {(ts, ANY, 0) for ts in range(t + 1, m)} | {(ts, te, 1) for ts in range(t + 1) for te in range(t, m)}


    # p[j] is the period (time) of the jth product
    p = VarArray(size=m, dom=range(m))

    # s[i] is the starting time of the ith stack
    s = VarArray(size=n, dom=range(m))

    # e[i] is the ending time of the ith stack
    e = VarArray(size=n, dom=range(m))

    # o[i][t] is 1 iff the ith stack is open at time t
    o = VarArray(size=[n, m], dom={0, 1})

    satisfy(
        # all products are scheduled at different times
        AllDifferent(p),

        # computing starting times of stacks
        [Minimum(p[j] for j in range(m) if orders[i][j]) == s[i] for i in range(n)],

        # computing ending times of stacks
        [Maximum(p[j] for j in range(m) if orders[i][j]) == e[i] for i in range(n)],

        # inferring when stacks are open
        [(s[i], e[i], o[i][t]) in table2(t) for i in range(n) for t in range(m)],
    )

    minimize(
        # minimizing the number of stacks that are simultaneously open
        Maximum(Sum(o[:, t]) for t in range(m))
    )

""" Comments
1) to have ordinary tables, we have to use: to_ordinary_table(tab, [v + 1, 2, 2]) and to_ordinary_table(tab, [m, m, 2])

2) If we want explicitly the number of open stacks at time t, we write instead:
 # ns[t] is the number of open stacks at time t
 ns = VarArray(size=m, dom=range(m + 1))

 # computing the number of open stacks at any time
 [Sum(o[:, j]) == ns[j] for j in range(m)]

 minimize (Maximum(ns))
"""
