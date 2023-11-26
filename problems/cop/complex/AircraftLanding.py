"""
See OR-library, and the model proposed in the Choco Tutorial, where the following short description is taken:
Given a set of planes and runways, the objective is to minimize the total (weighted) deviation from the target landing time for each plane.
There are costs associated with landing either earlier or later than a target landing time for each plane.
Each plane has to land on one of the runways within its predetermined time windows such that separation criteria between all pairs of planes are satisfied.

## Data Example
  airland01.json

## Model
  constraints: AllDifferent, NoOverlap, Sum, Table

## Execution
  - python AircraftLanding.py -data=<datafile.json>
  - python AircraftLanding.py -data=<datafile.json> -variant=table
  - python AircraftLanding.py -data=<datafile.txt> -parser=AircraftLanding_Parser.py

## Links
  - http://people.brunel.ac.uk/~mastjjb/jeb/orlib/airlandinfo.html
  - https://www.jstor.org/stable/25768908
  - https://www.jstor.org/stable/4101827
  - https://www.cril.univ-artois.fr/XCSP22/competitions/cop/cop

## Tags
  real, xcsp22
"""

from pycsp3 import *

nPlanes, times, costs, separations = data
earliest, target, latest = zip(*times)
early_penalties, late_penalties = zip(*costs)

# x[i] is the landing time of the ith plane
x = VarArray(size=nPlanes, dom=lambda i: range(earliest[i], latest[i] + 1))

# e[i] is the earliness of the ith plane
e = VarArray(size=nPlanes, dom=lambda i: range(target[i] - earliest[i] + 1))

# t[i] is the tardiness of the ith plane
t = VarArray(size=nPlanes, dom=lambda i: range(latest[i] - target[i] + 1))

satisfy(
    # planes must land at different times
    AllDifferent(x),

    # the separation time required between any two planes must be satisfied:
    [NoOverlap(origins=[x[i], x[j]], lengths=[separations[i][j], separations[j][i]]) for i, j in combinations(nPlanes, 2)]
)

if not variant():
    satisfy(
        # computing earliness of planes
        [e[i] == max(0, target[i] - x[i]) for i in range(nPlanes)],

        # computing tardiness of planes
        [t[i] == max(0, x[i] - target[i]) for i in range(nPlanes)],
    )

elif variant("table"):
    satisfy(
        # computing earliness and tardiness of planes
        (x[i], e[i], t[i]) in {(v, max(0, target[i] - v), max(0, v - target[i])) for v in range(earliest[i], latest[i] + 1)} for i in range(nPlanes)
    )

minimize(
    # minimizing the deviation cost
    e * early_penalties + t * late_penalties
)

""" Comments
1) we could extend the model for handling several runways. 
   For example, by introducing a new array r where r[i] is the runway ; 
   a new array s where s[i] is x[i]*k+r[i] where k is the number of runways
   and posting new constraints (AllDifferent(s), ...). 
   This is something to do.
   
2) for the 2022 competition, we used as objective for the mini-track:
   Sum(e) + Sum(t)
"""
