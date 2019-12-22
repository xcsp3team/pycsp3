from pycsp3 import *

# Problem 018 at CSPLib

c1, c2, c3 = data.c1, data.c2, data.c3
t1, t2, t3 = data.t1, data.t2, data.t3
h = data.h

assert c1 >= c2 >= c3 > 0, "Bucket capacities must be in decreasing order"

#  x[i][j] is the volume of water in bucket j at time (round) i
x = VarArray(size=[h, 3], dom=[[range(c1 + 1), range(c2 + 1), range(c3 + 1)]] * h)

# k is the number of transfers of water in order to reach the goal
k = Var(dom=range(h))


def tables():
    def related(tuple1, tuple2):
        a1, a2, a3 = tuple1
        b1, b2, b3 = tuple2
        if (a1, a2, a3) == (t1, t2, t3):
            return b1 == b2 == b3 == 0
        if a1 == a2 == a3 == 0:
            return b1 == b2 == b3 == 0
        if b1 == b2 == b3 == 0:
            return False
        if all(tuple1[i] != tuple2[i] for i in range(3)):
            return False
        if a1 != b1 and a2 != b2:
            return b1 in {0, c1} or b2 in {0, c2}
        if a1 != b1 and a3 != b3:
            return b1 in {0, c1} or b3 in {0, c3}
        if a2 != b2 and a3 != b3:
            return b2 in {0, c2} or b3 in {0, c3}
        return False

    table_capacities = {(0, 0, 0)} | {(i, j, k) for i in range(c1 + 1) for j in range(c2 + 1) for k in range(c3 + 1) if i + j + k == c1}
    table_dual = {(*cap1, *cap2) for cap1 in table_capacities for cap2 in table_capacities if related(cap1, cap2)}
    table_goal = set()
    for i in range(h):
        t = [0] * (h * 3 + 1)
        t[0] = i
        for j in range(1, (i * 3) + 1):
            t[j] = ANY
        t[i * 3 + 1], t[i * 3 + 2], t[i * 3 + 3] = t1, t2, t3
        table_goal.add(tuple(t))
    return table_capacities, table_dual, table_goal


table1, table2, table3 = tables()

satisfy(
    # Initially, only water in bucket 1
    x[0] == [c1, 0, 0],

    [x[i] in table1 for i in range(h)],

    [(x[i] + x[i + 1]) in table2 for i in range(h - 1)],  # or (*x[i], *x[i + 1])

    (k, *flatten(x)) in table3
)

minimize(k)
