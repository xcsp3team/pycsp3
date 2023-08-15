from pycsp3 import *

limit, value = data or (364, 55440)


def decompositions():
    for i in range(1, limit + 1):
        if i * limit * (limit - 1) * (limit - 2) < value:
            continue
        if i * (i + 1) * (i + 2) * (i + 3) > value:
            break
        for j in range(i + 1, limit + 1):
            if i * j * limit * (limit - 1) < value:
                continue
            if i * j * (j + 1) * (j + 2) > value:
                break
            for k in range(j + 1, limit + 1):
                if i * j * k * limit < value:
                    continue
                if i * j * k * (k + 1) > value:
                    break
                for l in range(k + 1, limit + 1):
                    if i * j * k * l > value:
                        break
                    if i * j * k * l == value:
                        yield i, j, k, l


T = [(t[i], t[j], t[k], t[l]) for t in decompositions() for (i, j, k, l) in product(range(4), repeat=4) if different_values(i, j, k, l)]

x = VarArray(size=4 * 4 * 4, dom=range(1, limit + 1))

satisfy(
    AllDifferent(x),
    [(x[i * 4], x[i * 4 + 1], x[i * 4 + 2], x[i * 4 + 3]) in T for i in range(16)],
    [([x[i], x[i + 4], x[i + 8], x[i + 12]]) in T for i in range(4)],
    [([x[i], x[i + 4], x[i + 8], x[i + 12]]) in T for i in range(16, 20)],
    [([x[i], x[i + 4], x[i + 8], x[i + 12]]) in T for i in range(32, 36)],
    [([x[i], x[i + 4], x[i + 8], x[i + 12]]) in T for i in range(48, 52)],
    [([x[i], x[i + 16], x[i + 32], x[i + 48]]) in T for i in range(16)],
    (x[0], x[21], x[42], x[63]) in T,
    (x[15], x[26], x[37], x[48]) in T,
    ([x[3], x[22], x[41], x[60]]) in T,
    (x[12], x[25], x[38], x[51]) in T
)

"""
1° it is faster to use a list than a set for the table T
"""
