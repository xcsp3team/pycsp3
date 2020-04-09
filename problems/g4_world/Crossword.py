"""
See, e.g., "Constraint programming lessons learned from crossword puzzles" by A. Beacham, X. Chen, J. Sillito, and P. van Beek. 2001

Examples of Execution:
  python3 Crossword.py -data=Crossword_vg6-7-ogd.json
  python3 Crossword.py -data=Crossword_vg6-7-ogd.json -variant=alt
"""

from pycsp3 import *


def find_holes(matrix, transposed):
    class Hole:
        def __init__(self, row, col, size, horizontal):
            self.row = row if horizontal else col
            self.col = col if horizontal else row
            self.size = size
            self.horizontal = horizontal

        def scope(self):
            return [x[self.row][self.col + k] if self.horizontal else x[self.row + k][self.col] for k in range(self.size)]

        def offset(self, other):
            if self.horizontal == other.horizontal:
                return None
            if self.horizontal:
                ofs1, ofs2 = other.col - self.col, self.row - other.row
                return (ofs1, ofs2) if 0 <= ofs1 < self.size and 0 <= ofs2 < other.size else None
            else:
                ofs1, ofs2 = self.col - other.col, other.row - self.row
                return (ofs1, ofs2) if 0 <= ofs1 < other.size and 0 <= ofs2 < self.size else None

        def __str__(self):
            return str(self.row) + " " + str(self.col) + " " + str(self.size) + " " + str(self.horizontal)

    p, q = len(matrix), len(matrix[0])
    t = []
    for i in range(p):
        start = -1
        for j in range(q):
            if matrix[i][j] == 1:
                if start != -1 and j - start >= 2:
                    t.append(Hole(i, start, j - start, not transposed))
                start = -1
            elif start == -1:
                start = j
            elif j == q - 1 and q - start >= 2:
                t.append(Hole(i, start, q - start, not transposed))
    return t


spots, dict_name = data
holes = find_holes(spots, False) + find_holes(transpose(spots), True)
n, m, nHoles = len(spots), len(spots[0]), len(holes)

words = dict()
for line in open(dict_name):
    code = alphabet_positions(line.strip().lower())
    words.setdefault(len(code), []).append(code)

if not variant():
    #  x[i][j] is the letter, number from 0 to 25, at row i and column j (when no spot)
    x = VarArray(size=[n, m], dom=lambda i, j: range(26) if spots[i][j] == 0 else None)

    satisfy(
        # fill the grid with words
        [hole.scope() in words[hole.size] for hole in holes],

        # tag(distinct-words)
        [AllDifferentList(hole.scope() for hole in holes if hole.size == arity) for arity in sorted(set(hole.size for hole in holes))]
    )
elif variant("alt"):
    def table_compatible_words(hole1, hole2):
        ofs1, ofs2 = hole1.offset(hole2)
        return {(i1, i2) for i1, word1 in enumerate(words[hole1.size]) for i2, word2 in enumerate(words[hole2.size]) if word1[ofs1] == word2[ofs2]}


    # w[i] is the ith word to be put in the grid
    w = VarArray(size=nHoles, dom=lambda i: range(len(words[holes[i].size])))

    satisfy(
        # words must intersect correctly
        [(w[i], w[j]) in table_compatible_words(holes[i], holes[j]) for i, j in combinations(range(nHoles), 2) if holes[i].offset(holes[j])],

        # tag(distinct-words)
        [w[i] != w[j] for i, j in combinations(range(nHoles), 2) if holes[i].size == holes[j].size]
    )
