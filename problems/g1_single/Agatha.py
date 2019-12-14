from pycsp3 import *

"""
  The Dreadsbury Mansion Mystery
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
  - Agatha is not the butler.
"""

persons = range(3)
agatha, butler, charles = 0, 1, 2

# killer is the person who kills Agatha
killer = Var(dom=persons)

# hates[i][j] is 1 iff person i hates person j
hates = VarArray(size=[3, 3], dom={0, 1})

# richer[i][j] is 1 iff person i is richer than person j
richer = VarArray(size=[3, 3], dom={0, 1})
satisfy(
    # a killer always hates his victim
    hates[killer][agatha] == 1,

    # a killer is never richer than his victim
    richer[killer][agatha] == 0,

    # Charles hates no one that Agatha hates
    [imply(hates[agatha][p], ~hates[charles][p]) for p in persons],

    # Agatha hates everybody except the butler
    [hates[agatha][p] == 1 for p in range(3) if p != butler],

    # the butler hates everyone not richer than Aunt Agatha
    [imply(~richer[p, agatha], hates[butler, p]) for p in persons],

    # the butler hates everyone Agatha hates
    [imply(hates[agatha, p], hates[butler, p]) for p in persons],

    # no one hates everyone
    [Count(hates[p], value=0) > 0 for p in persons]
)
