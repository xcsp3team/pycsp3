"""
Well-known crypto-arithmetic puzzle of unknown origin (e.g., a model is present in Gecode)

Examples of Execution:
  python3 Alpha.py
  python3 Alpha.py -variant=var
"""

from pycsp3 import *

if not variant():
    def of(word):
        return [x[i] for i in alphabet_positions(word)]


    # x[i] is the value for the ith letter of the alphabet
    x = VarArray(size=26, dom=range(1, 27))

    satisfy(
        # all letters must be different
        AllDifferent(x),

        # respecting clues
        [Sum(of("ballet")) == 45,
         Sum(of("cello")) == 43,
         Sum(of("concert")) == 74,
         Sum(of("flute")) == 30,
         Sum(of("fugue")) == 50,
         Sum(of("glee")) == 66,
         Sum(of("jazz")) == 58,
         Sum(of("lyre")) == 47,
         Sum(of("oboe")) == 53,
         Sum(of("opera")) == 65,
         Sum(of("polka")) == 59,
         Sum(of("quartet")) == 50,
         Sum(of("saxophone")) == 134,
         Sum(of("scale")) == 51,
         Sum(of("solo")) == 37,
         Sum(of("song")) == 61,
         Sum(of("soprano")) == 82,
         Sum(of("theme")) == 72,
         Sum(of("violin")) == 100,
         Sum(of("waltz")) == 34]
    )

elif variant("var"):
    # letters[i] is the value for the ith letter of the alphabet
    a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z = letters = VarArray(size=26, dom=range(1, 27))

    satisfy(
        # all letters must be different
        AllDifferent(letters),

        # respecting clues
        [Sum(b, a, l, l, e, t) == 45,
         Sum(c, e, l, l, o) == 43,
         Sum(c, o, n, c, e, r, t) == 74,
         Sum(f, l, u, t, e) == 30,
         Sum(f, u, g, u, e) == 50,
         Sum(g, l, e, e) == 66,
         Sum(j, a, z, z) == 58,
         Sum(l, y, r, e) == 47,
         Sum(o, b, o, e) == 53,
         Sum(o, p, e, r, a) == 65,
         Sum(p, o, l, k, a) == 59,
         Sum(q, u, a, r, t, e, t) == 50,
         Sum(s, a, x, o, p, h, o, n, e) == 134,
         Sum(s, c, a, l, e) == 51,
         Sum(s, o, l, o) == 37,
         Sum(s, o, n, g) == 61,
         Sum(s, o, p, r, a, n, o) == 82,
         Sum(t, h, e, m, e) == 72,
         Sum(v, i, o, l, i, n) == 100,
         Sum(w, a, l, t, z) == 34]
    )

""" Comments
1) if ever you want to merge occurrences of the same variable, at compiling time, 
   you must add at the top of the file:
      from pycsp3.dashboard import options
      options.groupsumcoeffs=True
"""
