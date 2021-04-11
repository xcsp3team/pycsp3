"""
See https://www.logisch-gedacht.de/logikraetsel/10stellige-zahl

We are looking for the 10-digit number which satisfies the following conditions:
- all digits from 0-9 occur exactly once
- the first 2 digits are divisible by 2
- the first 3 digits are divisible by 3
- ...
- the first 10 digits are divisible by 10

Using divisibility rules (https://en.wikipedia.org/wiki/Divisibility_rule) allows us
to use less expensive operations (constraints), but a less compact model

Examples of Execution:
  python3 SuperNumber.py
  python3 SuperNumber.py -variant=rules
"""

from pycsp3 import *

# x is the ith digit of the number
x = VarArray(size=10, dom=lambda i: {0} if i == 9 else range(10))

satisfy(
    # all digits must be different
    AllDifferent(x)
)

if not variant():
    satisfy(
        # the first i numbers must be divisible by i
        [x[:i] * [10 ** (i - j - 1) for j in range(i)] % i == 0 for i in range(2, 10)],
    )

elif variant("rules"):
    satisfy(
        # divisibility by 2
        x[1] in {0, 2, 4, 6, 8},

        # divisibility by 3
        Sum(x[0:3]) % 3 == 0,

        # divisibility by 4
        (x[2] * 10 + x[3]) % 4 == 0,

        # divisibility by 5
        x[4] in {0, 5},

        # divisibility by 6
        [x[5] in {0, 2, 4, 6, 8}, Sum(x[0:6]) % 3 == 0],

        # divisibility by 7
        (x[0] - x[1:4] * [100, 10, 1] + x[4:7] * [100, 10, 1]) % 7 == 0,

        # divisibility by 8
        x[5:8] * [100, 10, 1] % 8 == 0,

        # divisibility by 9
        Sum(x[:9]) % 9 == 0
    )

""" Comments
1) we directly set 0 for the last digit (because it must be divisible by 10)
   as a valid alternative, we could have written [x[:i] * [10 ** (i - j - 1) for j in range(i)] % i == 0 for i in range(2, 11)]
   but this generates still bigger integers (for example, not managed by Choco 4.10.5 and Ace)
"""