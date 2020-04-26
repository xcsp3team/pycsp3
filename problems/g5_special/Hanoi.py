from pycsp3 import *
from pycsp3.tools.utilities import value_in_base

nDisks = data
nTowers = 3
nStates, nSteps = nTowers ** nDisks, 2 ** nDisks - 1

x = VarArray(size=nSteps - 1, dom=range(nStates))


def table():
    def are_compatible(state1, state2):
        t1, t2 = value_in_base(state1, nDisks, nTowers), value_in_base(state2, nDisks, nTowers)
        frozen_towers = [False] * nTowers
        for i in range(len(t1) - 1, -1, -1):
            if t1[i] != t2[i]:
                break
            frozen_towers[t1[i]] = True
        return i >= 0 and not frozen_towers[t1[i]] and not frozen_towers[t2[i]] and all(t1[j] == t2[j] for j in range(i))

    return {(i, j) for i in range(nStates) for j in range(nStates) if are_compatible(i, j)}


table = table()

satisfy(
    x[0] in {1, 2},

    [(x[i], x[i + 1]) in table for i in range(nSteps - 2)]
)
