"""
Consider two groups of men and women who must marry.
Consider that each person has indicated a ranking for her/his possible spouses.
The problem is to find a matching between the two groups such that the marriages are stable.
A marriage between a man m and a woman w is stable iff:
- whenever m prefers an other woman o to w, o prefers her husband to m
- whenever w prefers an other man o to m, o prefers his wife to w

In 1962, David Gale and Lloyd Shapley proved that, for any equal number n of men and women,
it is always possible to make all marriages stable, with an algorithm running in O(n^2).

Nevertheless, this problem remains interesting
as it shows how a nice and compact model can be written.

Execution:
  python3 StableMarriage.py -data=StableMarriage-example.json
"""

from pycsp3 import *

w_rankings, m_rankings = data  # ranking by women and men
n = len(w_rankings)
Men, Women = range(n), range(n)

# wf[m] is the wife of the man m
wf = VarArray(size=n, dom=Women)

# hb[w] is the husband of the woman w
hb = VarArray(size=n, dom=Men)

satisfy(
    # spouses must match
    Channel(wf, hb),

    # whenever m prefers another woman o to his wife, o prefers her husband to m
    [
        If(
            m_rankings[m][o] < m_rankings[m][wf[m]],
            Then=w_rankings[o][hb[o]] < w_rankings[o][m]
        ) for m in Men for o in Women
    ],

    # whenever w prefers another man o to her husband, o prefers his wife to w
    [
        If(
            w_rankings[w][o] < w_rankings[w, hb[w]],
            Then=m_rankings[o][wf[o]] < m_rankings[o][w]
        ) for w in Women for o in Men
    ]
)

""" Comments
1) one could add two redundant constraints AllDifferent on wf and hb

2) one could replace Channel(wf, hb) with:
 # each man is the husband of his wife
 [hb[wf[m]] == m for m in Men],

 # each woman is the wife of her husband
 [wf[hb[w]] == w for w in Women],

3) global constraints involved in general expressions are externalized by introducing
   auxiliary variables. By using the compiler option, -useMeta, this is no more the case
   but the generated instance is no more in the perimeter of XCSP3-core
"""
