"""
See https://en.wikipedia.org/wiki/Verbal_arithmetic

Example of data: (no,no,yes) (two,two,four) (send,more,money) (cross,road,danger) (donald,gerarld,robert)

Examples of Execution:
  python3 CryptoPuzzle.py
  python3 CryptoPuzzle.py -data=[send,more,money]
  python3 CryptoPuzzle.py -data=[send,more,money] -variant=carry
"""

from pycsp3 import *

word1, word2, word3 = words = [w.lower() for w in data] if data else ("no", "no", "yes")
n = len(word1)
assert len(word2) == n and len(word3) in {n, n + 1}

# x[i] is the value assigned to the ith letter (if present) of the alphabet
x = VarArray(size=26, dom=lambda i: range(10) if i in alphabet_positions(words) else None)

# auxiliary lists of variables associated with the three words
x1, x2, x3 = [[x[i] for i in reversed(alphabet_positions(word))] for word in words]

satisfy(
    # all letters must be assigned different values
    AllDifferent(x),

    # the most significant letter of each word cannot be equal to 0
    [x1[-1] != 0, x2[-1] != 0, x3[-1] != 0]
)

if not variant():
    satisfy(
        # ensuring the crypto-arithmetic sum
        Sum((x1[i] + x2[i]) * 10 ** i for i in range(n)) == Sum(x3[i] * 10 ** i for i in range(len(x3)))
    )

elif variant("carry"):
    # c[i] is the ith carry
    c = VarArray(size=n + 1, dom={0, 1})

    satisfy(
        # managing the least significant carry
        c[0] == 0,

        # managing the most significant carry
        c[n] == (0 if len(x3) == n else x3[n]),  # NB: the parentheses are required

        # managing remainders
        [(c[i] + x1[i] + x2[i]) % 10 == x3[i] for i in range(n)],

        # managing quotients
        [(c[i] + x1[i] + x2[i]) // 10 == c[i + 1] for i in range(n)]
    )
