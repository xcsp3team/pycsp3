"""
See OR-library
See "Scheduling aircraft landings - the static case" by J.E. Beasley, M. Krishnamoorthy, Y.M. Sharaiha and D. Abramson,
    Transportation Science, vol.34, 2000, pp180-197.
See "Displacement problem and dynamically scheduling aircraft landings" by J.E. Beasley, M. Krishnamoorthy, Y.M. Sharaiha and D. Abramson,
    Journal of the Operational Research Society, vol.55, 2004, pp54-64.
See http://people.brunel.ac.uk/~mastjjb/jeb/orlib/airlandinfo.html

See the model proposed in the Choco Tutorial, where the following short description is taken:
"Given a set of planes and runways, the objective is to minimize the total (weighted) deviation from the target landing time for each plane.
There are costs associated with landing either earlier or later than a target landing time for each plane.
Each plane has to land on one of the runways within its predetermined time windows such that separation criteria between all pairs of planes are satisfied."

Execution:
  python3 AircraftLanding.py -data=airland1.txt -dataparser=AircraftLanding_Parser.py
  python3 AircraftLanding.py -data=airland1.txt -dataparser=AircraftLanding_Parser.py -variant=table
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
        # computing earlinesses of planes
        [e[i] == max(0, target[i] - x[i]) for i in range(nPlanes)],

        # computing tardinesses of planes
        [t[i] == max(0, x[i] - target[i]) for i in range(nPlanes)],
    )

elif variant("table"):
    satisfy(
        # computing earlinesses and tardinesses of planes
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
   and posting new constraints (AllDifferent(s), ...) TODO
   
2) for the 2022 competition, we used as objective for the mini-track:
   Sum(e) + Sum(t)
"""
