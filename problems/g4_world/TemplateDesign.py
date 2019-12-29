from pycsp3 import *
from math import ceil, floor

nSlots = data.nSlots
nTemplates = nVariations = len(data.demands)


def variation_interval(v):
    return range(ceil(data.demands[v] * 0.95), floor(data.demands[v] * 1.1) + 1)


# d[i][j] is the number of occurrences of the jth variation on the ith template
d = VarArray(size=[nTemplates, nVariations], dom=range(nSlots + 1))

# p[i] is the number of printings of the ith template
p = VarArray(size=nTemplates, dom=range(max(data.demands) + 1))

# u[i] is 1 iff the ith template is used
u = VarArray(size=nTemplates, dom={0, 1})

satisfy(
    # all slots of all templates are used
    [Sum(d[i]) == nSlots for i in range(nTemplates)],

    # if a template is used, it is printed at least once
    [iff(u[i] == 1, p[i] > 0) for i in range(nTemplates)]
)

if not variant():
    satisfy(
        # respecting printing bounds for each variation
        p * d[:, j] in variation_interval(j) for j in range(nVariations)
    )

elif variant("aux"):
    # pv[i][j] is the number of printings of the jth variation by using the ith template
    pv = VarArray(size=[nTemplates, nVariations], dom=lambda i, j: range(variation_interval(j).stop))

    satisfy(
        # linking variables of arrays p and pv
        [p[i] * d[i][j] == pv[i][j] for i in range(nTemplates) for j in range(nVariations)],

        # respecting printing bounds for each variation v
        [Sum(pv[:, j]) in variation_interval(j) for j in range(nVariations)]
    )

satisfy(
    # tag(symmetry-breaking)
    [
        [iff(u[i] == 0, d[i][0] == nSlots) for i in range(nTemplates)],

        Decreasing(p),
    ]
)

minimize(
    # minimizing the number of used templates
    Sum(u)
)
