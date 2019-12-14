#  This is a Radar surveillance instance where " + nRadars + " radars are on a geographic area of size " + mapSize + "*" + mapSize + " and must cover all cells."
#  There are " + nInsignificantCells + " insignificant cells that must not be covered by any radar. All other cells must be covered by exactly " +
#  maxCoverage + " radars." + " This instance has been generated using a seed equal to " + seed . This instance follows the description given by the
#  Swedish Institute of Computer Science (SICS).

from pycsp3 import *
from enum import Enum

mapSize, maxCoverage = data.mapSize, data.maxCoverage
radars = data.radars
insignificantCells = data.insignificantCells


class Sector(Enum):
    NEAST = 0  # north east
    EAST = 1
    SEAST = 2  # south east
    SWEST = 3  # south west
    WEST = 4
    NWEST = 5  # north west

    def row_right_cell(self, i):
        return i + (-1 if self in {Sector.NEAST, Sector.NWEST} else 0 if self in {Sector.EAST, Sector.WEST} else 1)

    def row_left_cell(self, i):
        return i + (-1 if self in {Sector.NEAST, Sector.EAST} else 0 if self in {Sector.SEAST, Sector.NWEST} else 1)

    def col_right_cell(self, i, j):
        ro = 0 if i % 2 == 1 else 1
        return j + (1 if self == Sector.EAST else -1 if self == Sector.WEST else ro if self in {Sector.NEAST, Sector.SEAST} else ro - 1)

    def col_left_cell(self, i, j):
        ro = 0 if i % 2 == 1 else 1
        return j + (1 if self == Sector.SEAST else -1 if self == Sector.NWEST else ro if self in {Sector.EAST, Sector.SWEST} else ro - 1)

    def distance(self, i, j, k, l, curr_distance):
        if curr_distance > maxCoverage:
            return -1
        if (i, j) == (k, l):
            return curr_distance
        d = self.distance(i, j, self.row_right_cell(k), self.col_right_cell(k, l), curr_distance + 1)
        if d != -1:
            return d
        return self.distance(i, j, self.row_left_cell(k), self.col_left_cell(k, l), curr_distance + 1)


def cell_constraint(i, j):
    scope, dists = [], []
    for ir, radar in enumerate(radars):
        for sector in Sector:
            d = sector.distance(i, j, sector.row_right_cell(radar[0]), sector.col_right_cell(radar[0], radar[1]), 1)
            if d != -1:
                scope.append(x[ir][sector.value])
                dists.append(d)
    arity = len(scope)
    if arity == 0:
        return None
    significant_cell = [i, j] not in insignificantCells
    if arity == 1:
        return scope[0] > dists[0] - 1 if significant_cell else scope[0] < dists[0]
    return Sum(scope[i] >= dists[i] for i in range(arity)) == (min(arity, maxCoverage) if significant_cell else 0)


# x[i][j] is the power of the ith radar in the jth sector
x = VarArray(size=[len(radars), len(Sector)], dom=range(maxCoverage + 1))

satisfy(
    cell_constraint(i, j) for i in range(mapSize) for j in range(mapSize)
)
