"""
Illustrative problem used in the PyCSP3 guide (See Chapter 1)

Example of Execution:
  python3 Riddle.py -variant="v1"
  python3 Riddle.py -variant="v2"
  python3 Riddle.py -variant="v3a"
  python3 Riddle.py -variant="v3b"
  python3 Riddle.py -variant="v4a"
  python3 Riddle.py -variant="v4b"
  python3 Riddle.py -variant="v5"
"""

from pycsp3 import *

if variant("v1"):
    x1 = Var(range(15))
    x2 = Var(range(15))
    x3 = Var(range(15))
    x4 = Var(range(15))

    satisfy(
        x1 + 1 == x2,
        x2 + 1 == x3,
        x3 + 1 == x4,
        x1 + x2 + x3 + x4 == 14
    )
elif variant("v2"):
    x = VarArray(size=4, dom=range(15))

    satisfy(
        x[0] + 1 == x[1],
        x[1] + 1 == x[2],
        x[2] + 1 == x[3],
        x[0] + x[1] + x[2] + x[3] == 14
    )
elif variant("v3a"):
    def domain_x(i):
        return range(6) if i < 2 else range(9)


    x = VarArray(size=4, dom=domain_x)

    satisfy(
        x[0] + 1 == x[1],
        x[1] + 1 == x[2],
        x[2] + 1 == x[3],
        x[0] + x[1] + x[2] + x[3] == 14
    )
elif variant("v3b"):
    x = VarArray(size=4, dom=lambda i: range(6) if i < 2 else range(9))

    satisfy(
        x[0] + 1 == x[1],
        x[1] + 1 == x[2],
        x[2] + 1 == x[3],
        x[0] + x[1] + x[2] + x[3] == 14
    )
elif variant("v4a"):
    x = VarArray(size=4, dom=range(15))

    satisfy(
        [x[i] + 1 == x[i + 1] for i in range(3)],

        x[0] + x[1] + x[2] + x[3] == 14
    )
elif variant("v4b"):
    x = VarArray(size=4, dom=range(15))

    for i in range(3):
        satisfy(
            x[i] + 1 == x[i + 1]
        )

    satisfy(
        x[0] + x[1] + x[2] + x[3] == 14
    )
elif variant("v5"):
    # x[i] is the ith value of the sequence
    x = VarArray(size=4, dom=range(15))

    satisfy(
        # four successive values are needed
        [x[i] + 1 == x[i + 1] for i in range(3)],

        # values must sum up to 14
        Sum(x) == 14
    )
