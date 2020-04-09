""""
Problem 001 on CSPLib

Examples of Execution:
  python3 CarSequencing.py -data=CarSequencing_dingbas.json
  python3 CarSequencing.py -data=CarSequencing_dingbas.json -variant=table
"""

from pycsp3 import *

classes, limits = data
nCars, nClasses, nOptions = sum(cl.demand for cl in classes), len(classes), len(limits)


def redu(k, i):
    # i stands for the number of blocks set to the maximal capacity
    remaining = sum(options[k] * demand for (demand, options) in classes) - i * limits[k].num
    possible = nCars - i * limits[k].den
    if remaining > 0 and possible > 0:
        return Sum(o[j][k] for j in range(possible)) >= remaining


# c[i] is the class of the ith assembled car
c = VarArray(size=nCars, dom=range(nClasses))

# o[i][k] is 1 if the ith assembled car has option k
o = VarArray(size=[nCars, nOptions], dom={0, 1})

satisfy(
    # building the right numbers of cars per class
    Cardinality(c, occurrences={i: classes[i].demand for i in range(nClasses)})
)

if not variant():
    satisfy(
        # constraints about options
        imply(c[i] == j, o[i][k] == options[k]) for i in range(nCars) for j, (_, options) in enumerate(classes) for k in range(nOptions)
    )
elif variant("table"):
    satisfy(
        # constraints about options
        (c[i], *o[i]) in {(j, *options) for j, (_, options) in enumerate(classes)} for i in range(nCars)
    )

satisfy(
    # constraints about option frequencies
    [Sum(o[i:i + den, k]) <= num for k, (num, den) in enumerate(limits) for i in range(nCars) if i <= nCars - den],

    # tag(redundant-constraints)
    [redu(k, i) for k in range(nOptions) for i in range(nCars)]
)
