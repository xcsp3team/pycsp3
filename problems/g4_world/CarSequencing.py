from pycsp3 import *

classes, limits = data.classes, data.limits
demands = [c.demand for c in classes]
nCars, nOptions, nClasses = sum(demands), len(limits), len(classes)
allClasses = range(nClasses)


def redu(k, i):
    # i stands for the number of blocks set to the maximal capacity
    nOptionOccurrences = sum([cl.options[k] * cl.demand for cl in classes])
    nOptionsRemainingToSet = nOptionOccurrences - i * limits[k].num
    nOptionsPossibleToSet = nCars - i * limits[k].den
    if nOptionsRemainingToSet > 0 and nOptionsPossibleToSet > 0:
        return Sum([o[j][k] for j in range(nOptionsPossibleToSet)]) >= nOptionsRemainingToSet


#  c[i] is the class of the ith assembled car
c = VarArray(size=[nCars], dom=range(nClasses))

#  o[i][k] is 1 if the ith assembled car has option k
o = VarArray(size=[nCars, nOptions], dom={0, 1})

satisfy(
    # building the right numbers of cars per class
    Cardinality(c, occurrences={i: demands[i] for i in range(nClasses)})
)

useTable = True
if useTable:
    satisfy(
        # constraints about options
        [(c[i], *o[i]) in {(i, *cl.options) for i, cl in enumerate(classes)} for i in range(nCars)]
    )
else:
    satisfy(
        # linking cars and options
        [imply(c[i] == j, o[i][k] == cl.options[k]) for i in range(nCars) for j, cl in enumerate(classes) for k in range(nOptions)]
    )

satisfy(
    # constraints about option frequencies
    [Sum(o[j][k] for j in range(i, i + limit.den)) <= limit.num for k, limit in enumerate(limits) for i in range(nCars) if i <= nCars - limit.den],

    # tag(redundant-constraints)
    [redu(k, i) for k in range(nOptions) for i in range(nCars)]
)
