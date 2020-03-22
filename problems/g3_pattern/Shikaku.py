from pycsp3 import *

"""
 See https://en.wikipedia.org/wiki/Shikaku
"""

nRows, nCols = data.nRows, data.nCols
rooms = data.rooms
nRooms = len(rooms)


def no_overlapping(i, j):
    leftmost = i if rooms[i].col <= rooms[j].col else j
    rightmost = j if leftmost == i else i
    p = r[leftmost] <= l[rightmost]
    if rooms[leftmost].row == rooms[rightmost].row:
        return p
    if rooms[leftmost].row > rooms[rightmost].row:
        return p | (t[leftmost] >= b[rightmost])
    return p | (b[leftmost] <= t[rightmost])


# l[i] is the position of the left border of the ith room
l = VarArray(size=nRooms, dom=range(nCols + 1))

# r[i] is the position of the right border of the ith room
r = VarArray(size=nRooms, dom=range(nCols + 1))

# t[i] is the position of the top border of the ith room
t = VarArray(size=nRooms, dom=range(nRows + 1))

# b[i] is the position of the bottom border of the ith room
b = VarArray(size=nRooms, dom=range(nRows + 1))

satisfy(
    # each room must be surrounded by its borders
    [(l[i] <= col, r[i] > col, t[i] <= row, b[i] > row) for i, (row, col, _) in enumerate(rooms)],

    # respecting the surface of each room
    [(r[i] - l[i]) * (b[i] - t[i]) == rooms[i].value for i in range(nRooms)],

    # rooms must not overlap
    [no_overlapping(i, j) for i, j in combinations(range(nRooms), 2)]
)



# [l[i] <= rooms[i].col for i in range(nRooms)],
#
# [r[i] > rooms[i].col for i in range(nRooms)],
#
# [t[i] <= rooms[i].row for i in range(nRooms)],
#
# [b[i] > rooms[i].row for i in range(nRooms)],
