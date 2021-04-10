"""
See https://en.wikipedia.org/wiki/Knight%27s_tour

Examples of Execution:
  python3 KnightTour.py
  python3 KnightTour.py -data=16
  python3 KnightTour.py -data=16 -variant=table-2
  python3 KnightTour.py -data=16 -variant=table-3
"""

from pycsp3 import *

n = data or 8
n2 = n * n

# x[i] is the cell number where the ith knight is put
x = VarArray(size=n2, dom=range(n2))

satisfy(
    AllDifferent(x)
)

if not variant():
    satisfy(
        (d1 == 1) & (d2 == 2) | (d1 == 2) & (d2 == 1) for d1, d2 in
        [(abs(x[i] // n - x[(i + 1) % n2] // n), abs(x[i] % n - x[(i + 1) % n2] % n)) for i in range(n2)]
    )

elif variant("table"):
    r = int(subvariant())
    assert r > 1 and n % (r - 1) == 0


    def jump(i, j):
        t = []
        if i - 2 >= 0:
            if j - 1 >= 0:
                t.append((i - 2) * n + j - 1)
            if j + 1 < n:
                t.append((i - 2) * n + j + 1)
        if i + 2 < n:
            if j - 1 >= 0:
                t.append((i + 2) * n + j - 1)
            if j + 1 < n:
                t.append((i + 2) * n + j + 1)
        if j - 2 >= 0:
            if i - 1 >= 0:
                t.append((i - 1) * n + j - 2)
            if i + 1 < n:
                t.append((i + 1) * n + j - 2)
        if j + 2 < n:
            if i - 1 >= 0:
                t.append((i - 1) * n + j + 2)
            if i + 1 < n:
                t.append((i + 1) * n + j + 2)
        return sorted(t)


    jumps = [jump(i, j) for i in range(n) for j in range(n)]


    def table_recursive(i, tmp):
        if i == len(tmp):
            table.add(tuple(tmp[:]))
        else:
            for v in jumps[tmp[i - 1]]:
                if len([j for j in range(0, i - 1) if tmp[j] == v]) == 0:
                    tmp[i] = v
                    table_recursive(i + 1, tmp)


    table = set()
    for i in range(n * n):
        table_recursive(1, [i] + [0] * (r - 1))

    satisfy(
        [x[(i + j) % n2] for j in range(r)] in table for i in range(0, n2, r - 1)
    )

satisfy(
    # breaking symmetries by putting the first knight in the first cell, and the second knight in the first possible cell  tag(symmetry-breaking)
    [x[0] == 0, x[1] == n + 2]
)

""" Comments
1) it is possible to use extension constraints instead of intension constraints (see, e.g., the problem QueensKnights)
"""