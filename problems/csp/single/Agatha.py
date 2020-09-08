"""
The Dreadsbury Mansion Mystery (4 solutions)
F. J. Pelletier, "Seventy-five problems for testing automatic theorem provers",
Journal of Automated Reasoning, 2: 191 216, 1986.

Someone who lives in Dreadsbury Mansion killed Aunt Agatha.
Agatha, the butler, and Charles live in Dreadsbury Mansion, and are the only people who live therein.
 - A killer always hates his victim, and is never richer than his victim.
 - Charles hates no one that Aunt Agatha hates.
 - Agatha hates everyone except the butler.
 - The butler hates everyone not richer than Aunt Agatha.
 - The butler hates everyone Agatha hates.
 - No one hates everyone.

Execution:
  python3 Agatha.py
"""

from pycsp3 import *

persons = agatha, butler, charles = 0, 1, 2

# killer is the person who kills Agatha
killer = Var(dom=persons)

# hating[i][j] is 1 iff person i hates person j
hating = VarArray(size=[3, 3], dom={0, 1})

# richer[i][j] is 1 iff person i is richer than person j
richer = VarArray(size=[3, 3], dom={0, 1})

satisfy(
    # a killer always hates his victim
    hating[killer][agatha] == 1,

    # a killer is never richer than his victim
    richer[killer][agatha] == 0,

    # Charles hates no one that Agatha hates
    [imply(hating[agatha][p], ~hating[charles][p]) for p in persons],

    # Agatha hates everybody except the butler
    [hating[agatha][p] == 1 for p in persons if p != butler],

    # the butler hates everyone not richer than Aunt Agatha
    [imply(~richer[p, agatha], hating[butler, p]) for p in persons],

    # the butler hates everyone Agatha hates
    [imply(hating[agatha, p], hating[butler, p]) for p in persons],

    # no one hates everyone
    [Count(hating[p], value=0) > 0 for p in persons]
)
