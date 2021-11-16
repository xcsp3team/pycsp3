"""
This is a Radar surveillance instance where some radars must be put on a geographic area of a specified size and must cover all cells.
There are some insignificant cells that must not be covered by any radar. All other cells must be covered by exactly a specified number of radars.
Instances of this problem follow the description given by the Swedish Institute of Computer Science (SICS).

Example of Execution:
  python3 RadarSurveillance.py -data=RadarSurveillance_8-24-3-2-00.json
"""

from enum import Enum

from pycsp3 import *

mapSize, maxCoverage, radars, insignificantCells = data
nRadars = len(radars)


class Sector(Enum):
    NORTH_EAST, EAST, SOUTH_EAST, SOUTH_WEST, WEST, NORTH_WEST = range(6)

    def row_right_cell(self, i):
        return i + (-1 if self in {Sector.NORTH_EAST, Sector.NORTH_WEST} else 0 if self in {Sector.EAST, Sector.WEST} else 1)

    def row_left_cell(self, i):
        return i + (-1 if self in {Sector.NORTH_EAST, Sector.EAST} else 0 if self in {Sector.SOUTH_EAST, Sector.NORTH_WEST} else 1)

    def col_right_cell(self, i, j):
        ro = 0 if i % 2 == 1 else 1
        return j + (1 if self == Sector.EAST else -1 if self == Sector.WEST else ro if self in {Sector.NORTH_EAST, Sector.SOUTH_EAST} else ro - 1)

    def col_left_cell(self, i, j):
        ro = 0 if i % 2 == 1 else 1
        return j + (1 if self == Sector.SOUTH_EAST else -1 if self == Sector.NORTH_WEST else ro if self in {Sector.EAST, Sector.SOUTH_WEST} else ro - 1)

    def distance(self, i, j, k, l, curr_distance):
        if curr_distance > maxCoverage:
            return -1
        if (i, j) == (k, l):
            return curr_distance
        d = self.distance(i, j, self.row_right_cell(k), self.col_right_cell(k, l), curr_distance + 1)
        return d if d != -1 else self.distance(i, j, self.row_left_cell(k), self.col_left_cell(k, l), curr_distance + 1)


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
x = VarArray(size=[nRadars, len(Sector)], dom=range(maxCoverage + 1))

satisfy(
    cell_constraint(i, j) for i in range(mapSize) for j in range(mapSize)
)
