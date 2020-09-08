"""
Someone in the university ate Alice’s sandwich at the cafeteria. We want to find out who the culprit is.
The witnesses are unanimous about the following facts:
 - Three persons were in the cafeteria at the time of the crime: Alice, Bob, and Sascha.
 - The culprit likes Alice.
 - The culprit is taller than Alice.
 - Nobody is taller than himself.
 - If A is taller than B, then B is not taller than A.
 - Bob likes no one that Alice likes.
 - Alice likes everybody except Bob.
 - Sascha likes everyone that Alice likes.
 - Nobody likes everyone.

Execution:
  python3 Sandwich.py
"""

from pycsp3 import *

alice, bob, sascha = persons = 0, 1, 2

# culprit is among alice (0), bob (1) and sascha (2)
culprit = Var(persons)

# liking[i][j] is 1 iff the ith guy likes the jth guy
liking = VarArray(size=[3, 3], dom={0, 1})

# taller[i][j] is 1 iff the ith guy is taller than the jth guy
taller = VarArray(size=[3, 3], dom={0, 1})

satisfy(
    # the culprit likes Alice
    liking[culprit][alice] == 1,

    # the culprit is taller than Alice
    taller[culprit][alice] == 1,

    # nobody is taller than himself
    [taller[p][p] == 0 for p in persons],

    # the ith guy is taller than the jth guy iff the reverse is not true
    [taller[p1][p2] != taller[p2][p1] for p1 in persons for p2 in persons if p1 != p2],

    # Bob likes no one that Alice likes
    [imply(liking[alice][p], ~liking[bob][p]) for p in persons],

    # Alice likes everybody except Bob
    [liking[alice][p] == 1 for p in persons if p != bob],

    # Sascha likes everyone that Alice likes
    [imply(liking[alice][p], liking[sascha][p]) for p in persons],

    # nobody likes everyone
    [Count(liking[p], value=0) >= 1 for p in persons]
)
