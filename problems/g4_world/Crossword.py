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

        def __repr__(self, *args, **kwargs):
            return str(self.row) + " " + str(self.col) + " " + str(self.size) + " " + str(self.horizontal)

    n, m = len(matrix), len(matrix[0])
    t = []
    for i in range(n):
        start = -1
        for j in range(m):
            if matrix[i][j] == 1:
                if start != -1 and j - start >= 2:
                    t.append(Hole(i, start, j - start, not transposed))
                start = -1
            else:
                if start == -1:
                    start = j
                elif j == m - 1 and m - start >= 2:
                    t.append(Hole(i, start, m - start, not transposed))
    return t


nRows, nCols = len(data.spots), len(data.spots[0])
holes = find_holes(data.spots, False) + find_holes(transpose(data.spots), True)
nHoles = len(holes)

words = dict()
for line in open(data.dictFileName):
    code = alphabet_positions(line.strip().lower())
    words.setdefault(len(code), []).append(code)

if not variant():
    #  x[i][j] is the letter, number from 0 to 25, at row i and column j (when no spot)
    x = VarArray(size=[nRows, nCols], dom=lambda i, j: range(26) if data.spots[i][j] == 0 else None)

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
        [(w[i], w[j]) in table_compatible_words(holes[i], holes[j]) for i in range(nHoles) for j in range(i + 1, nHoles) if holes[i].offset(holes[j])],

        # tag(distinct-words)
        [w[i] != w[j] for i in range(nHoles) for j in range(i + 1, nHoles) if holes[i].size == holes[j].size]
    )
