from pycsp3 import *

word1, word2, word3 = data.word1.lower(), data.word2.lower(), data.word3.lower()
n = len(word1)
assert len(word2) == n and len(word3) in {n, n + 1}
letters = set(to_alphabet_positions(word1 + word2 + word3))

# l[i] is the value assigned to the ith letter (if present) of the alphabet
l = VarArray(size=26, dom=range(10), when=lambda i: i in letters)

# c[i] is the ith carry
c = VarArray(size=n + 1, dom={0, 1})

# auxiliary lists of variables associated with the three words
x1, x2, x3 = [l[w] for w in to_alphabet_positions(word1)], [l[w] for w in to_alphabet_positions(word2)], [l[w] for w in to_alphabet_positions(word3)]

satisfy(
    # all letters must be assigned different values
    AllDifferent(l),

    # managing first carry
    c[0] == 0,

    # managing last carry
    c[n] == (0 if len(word3) == n else x3[0]),

    # managing remainders
    [(c[i] + x1[-1 - i] + x2[-1 - i]) % 10 == x3[-1 - i] for i in range(n)],

    # managing quotients
    [(c[i] + x1[-1 - i] + x2[-1 - i]) // 10 == c[i + 1] for i in range(n)]
)
