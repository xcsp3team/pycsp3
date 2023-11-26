"""
Given a grid with imposed black cells (spots) and a dictionary, the problem is to fulfill the grid with the words contained in the dictionary.

## Data Example
  vg0607-ogd.json

## Model
  Two variants are defined from different angles:
  - a main variant where variables correspond to letters
  - a variant 'alt' where variables correspond to words

  constraints: AllDifferentList, Table

## Execution
  - python Crossword.py -data=<datafile.json>
  - python Crossword.py -variant=alt -data=<datafile.json>
  - python Crossword.py -data=[vg0405,dict=ogd2008] -parser=Crossword_Parser.py

## Links
  - https://www.researchgate.net/publication/221442491_Constraint_Programming_Lessons_Learned_from_Crossword_Puzzles
  - https://www.cril.univ-artois.fr/XCSP22/competitions/csp/csp

## Tags
  recreational, xcsp22
"""

from pycsp3 import *

spots, dict_name = data
words = dict()
for line in open(dict_name):
    code = alphabet_positions(line.strip().lower())
    words.setdefault(len(code), []).append(code)


def find_holes(matrix, transposed):
    def build_hole(row, col, size, horizontal):
        sl = slice(col, col + size)
        return Hole(row, sl, size) if horizontal else Hole(sl, row, size)

    Hole = namedtuple("Hole", "i j r")  # i and j are indexes (one of them being a slice) and r is the size
    p, q = len(matrix), len(matrix[0])
    t = []
    for i in range(p):
        start = -1
        for j in range(q):
            if matrix[i][j] == 1:
                if start != -1 and j - start >= 2:
                    t.append(build_hole(i, start, j - start, not transposed))
                start = -1
            elif start == -1:
                start = j
            elif j == q - 1 and q - start >= 2:
                t.append(build_hole(i, start, q - start, not transposed))
    return t


holes = find_holes(spots, False) + find_holes(columns(spots), True)
arities = sorted({size for (_, _, size) in holes})
n, m, nHoles = len(spots), len(spots[0]), len(holes)

if not variant():
    #  x[i][j] is the letter, number from 0 to 25, at row i and column j (when no spot)
    x = VarArray(size=[n, m], dom=lambda i, j: range(26) if spots[i][j] == 0 else None)

    satisfy(
        # fill the grid with words
        [x[i, j] in words[r] for (i, j, r) in holes],

        # tag(distinct-words)
        [AllDifferentList(x[i, j] for (i, j, r) in holes if r == arity) for arity in arities]
    )

elif variant("alt"):
    def offset(hole1, hole2):
        if type(hole1.i) == type(hole2.i):  # it means that they are both horizontal or vertical (type is int or slice)
            return None
        if isinstance(hole1.i, int):  # if hole1 is horizontal (and so hole2 is vertical)
            ofs1, ofs2 = hole2.j - hole1.j.start, hole1.i - hole2.i.start
            return (ofs1, ofs2) if 0 <= ofs1 < hole1.r and 0 <= ofs2 < hole2.r else None
        else:  # if hole1 is vertical (and so hole2 is horizontal)
            ofs1, ofs2 = hole1.j - hole2.j.start, hole2.i - hole1.i.start
            return (ofs1, ofs2) if 0 <= ofs1 < hole2.r and 0 <= ofs2 < hole1.r else None


    def table_compatible_words(hole1, hole2):
        ofs1, ofs2 = offset(hole1, hole2)
        return [(i1, i2) for i1, word1 in enumerate(words[hole1.r]) for i2, word2 in enumerate(words[hole2.r]) if word1[ofs1] == word2[ofs2]]


    # w[i] is the ith word to be put in the grid
    w = VarArray(size=nHoles, dom=lambda i: range(len(words[holes[i].r])))

    satisfy(
        # words must intersect correctly
        [(w[i], w[j]) in table_compatible_words(holes[i], holes[j]) for i, j in combinations(nHoles, 2) if offset(holes[i], holes[j])],

        # tag(distinct-words)
        [w[i] != w[j] for i, j in combinations(nHoles, 2) if holes[i].r == holes[j].r]
    )

""" Comments
1) we use lists instead of sets for tables ([(i1, i2)  ... instead of  {(i1, i2) ..) because it is quite faster to process

2) it is not possible to write x[i][j] when i is a slice; this must be x[i, j]
"""
