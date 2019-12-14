from pycsp3 import *

spots = data.spots
nRows, nCols = len(spots), len(spots[0])

words = dict()
for line in open(data.dictFileName):
    code = to_alphabet_positions(line.strip().lower())
    if len(code) in words:
        words[len(code)].append(code)
    else:
        words[len(code)] = [code]


class Hole:
    def __init__(self, row, col, size, horizontal):
        self.row = row if horizontal else col
        self.col = col if horizontal else row
        self.size = size
        self.horizontal = horizontal

    def scope(self):
        return [x[self.row][self.col + i] for i in range(self.size)] if self.horizontal else [x[self.row + i][self.col] for i in range(self.size)]

    def offset(self, other):
        if self.horizontal == other.horizontal:
            return None
        offset = []
        if self.horizontal:
            offset.append(other.col - self.col)
            if offset[0] < 0 or offset[0] > self.size - 1:
                return None
            offset.append(self.row - other.row)
            if offset[1] < 0 or offset[1] > other.size - 1:
                return None
        else:
            offset.append(self.col - other.col)
            if offset[0] < 0 or offset[0] > other.size - 1:
                return None
            offset.append(other.row - self.row)
            if offset[1] < 0 or offset[1] > self.size - 1:
                return None
        return offset

    def __repr__(self, *args, **kwargs):
        return str(self.row) + " " + str(self.col) + " " + str(self.size) + " " + str(self.horizontal)


def find_holes(m, transposed):
    n, p = len(m), len(m[0])
    t = []
    for i in range(n):
        start = -1
        for j in range(p):
            if m[i][j] == 1:
                if start != -1 and j - start >= 2:
                    t.append(Hole(i, start, j - start, not transposed))
                start = -1
            else:
                if start == -1:
                    start = j
                elif j == p - 1 and p - start >= 2:
                    t.append(Hole(i, start, p - start, not transposed))
    return t


def compatible_words(hole1, hole2):
    offset = hole1.offset(hole2)
    words1, words2 = words[hole1.size], words[hole2.size]
    return {(i1, i2) for i1 in range(len(words1)) for i2 in range(len(words2)) if words1[i1][offset[0]] == words2[i2][offset[1]]}


holes = find_holes(spots, False) + find_holes(transpose(spots), True)
arities = sorted(set(hole.size for hole in holes))
nHoles = len(holes)

if not variant():
    #  x[i][j] is the letter, number from 0 to 25, at row i and column j (when no spot)
    x = VarArray(size=[nRows, nCols], dom=lambda i, j: range(26), when=lambda i, j: spots[i][j] == 0)

    satisfy(
        #  fill the grid with words
        [hole.scope() in words.get(hole.size) for hole in holes],

        # tag(distinct-words)
        [AllDifferentList(hole.scope() for hole in holes if hole.size == arity) for arity in arities]
    )
elif variant("alt"):
    # w[i] is the ith word to be put in the grid
    w = VarArray(size=nHoles, dom=lambda i: range(len(words[holes[i].size])))

    satisfy(
        # words must intersect correctly
        [(w[i], w[j]) in compatible_words(holes[i], holes[j]) for i in range(nHoles) for j in range(i + 1, nHoles) if holes[i].offset(holes[j]) is not None],

        # tag(distinct-words)
        [w[i] != w[j] for i in range(nHoles) for j in range(i + 1, nHoles) if holes[i].size == holes[j].size]
    )
