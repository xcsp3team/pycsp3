"""
Cookie Monster Problem (by Richard Green)

Suppose that we have a number of cookie jars, each containing a certain number of cookies.
The Cookie Monster (CM) wants to eat all the cookies, but he is required to do so in a number
of sequential moves. At each move, the CM chooses a subset of the jars,
and eats the same (nonzero) number of cookies from each jar. The goal of the CM is to
empty all the cookies from the jars in the smallest possible number of moves, and the
Cookie Monster Problem is to determine this number for any given set of cookie jars.

Concerning data, we need a list of quantities in jars as e.g., [1, 2, 4, 12, 13, 15],
meaning that there are six jars, containing 1, 2, 4, 12, 13 and 15 cookies each.

See another model in OscaR

Examples of Execution:
  python3 CookieMonster.py                                 // using default data
  python3 CookieMonster.py -data=cookies_example.json
"""

from pycsp3 import *

jars = data or [15, 13, 12, 4, 2, 1]
nJars, horizon = len(jars), len(jars) + 1

# x[t][i] is the quantity of cookies in the ith jar at time t
x = VarArray(size=[horizon, nJars], dom=range(max(jars) + 1))

# y[t] is the number of cookies eaten by the monster in a selection of jars at time t
y = VarArray(size=horizon, dom=range(max(jars) + 1))

# f is the first time where all jars are empty
f = Var(range(horizon))

satisfy(
    # initial state
    [x[0][i] == jars[i] for i in range(nJars)],

    # final state
    [x[-1][i] == 0 for i in range(nJars)],

    # handling the action of the cookie monster at time t (to t+1)
    [(x[t + 1][i] == x[t][i]) | (x[t + 1][i] == x[t][i] - y[t]) for t in range(horizon - 1) for i in range(nJars)],

    # ensuring no useless intermediate inaction
    [(y[t] != 0) | (y[t + 1] == 0) for t in range(horizon - 1)],

    # at time f, all jars are empty
    y[f] == 0
)

minimize(
    f
)


""" Comments
1) the two groups of constraints concerning the initial and final states could be equivalently written:
  # initial state
  x[0] == jars,

  # final state
  x[-1] == [0 for _ in range(nJars)],
  
2) we can also write:
  x[-1] == [0] * nJars,
"""