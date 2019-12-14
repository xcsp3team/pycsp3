from pycsp3 import *

vr_sizes = data.visitorGroups  # vr_sizes[i] gives the size of the ith visitor group
ve_sizes = data.visiteeGroups  # ve_sizes[i] gives the size of the ith visitee group

nVisitors, nVisitees = sum(vr_sizes), sum(ve_sizes)
assert nVisitors >= nVisitees, "The number of visitors must be greater than the number of visitees"
if nVisitors - nVisitees > 0:
    ve_sizes.append(nVisitors - nVisitees)  # an artificial group with dummy visitees is added
nWeeks = len(vr_sizes)
n = nVisitors

vr_table = [(i, sum(vr_sizes[:i]) + j) for i, size in enumerate(vr_sizes) for j in range(size)]
ve_table = [(i, sum(ve_sizes[:i]) + j) for i, size in enumerate(ve_sizes) for j in range(size)]

# vr[i][w] is the visitor for the ith visitee at week w
vr = VarArray(size=[n, nWeeks], dom=range(n))

# ve[i][w] is the visitee for the ith visitor at week w
ve = VarArray(size=[n, nWeeks], dom=range(n))

# gr[i][w] is the visitor group for the ith visitee at week w
gr = VarArray(size=[n, nWeeks], dom=range(len(vr_sizes)))

# ge[i][w] is the visitee group for the ith visitor at week w
ge = VarArray(size=[n, nWeeks], dom=range(len(ve_sizes)))

satisfy(
    # each week, all visitors must be different
    [AllDifferent(col) for col in columns(vr)],

    # each week, all visitees must be different
    [AllDifferent(col) for col in columns(ve)],

    # the visitor groups must be different for each visitee
    [AllDifferent(row) for row in gr],

    # the visitee groups must be different for each visitor
    [AllDifferent(row) for row in ge],

    # channeling arrays vr and ve, each week
    [Channel(vr[:, w], ve[:, w]) for w in range(nWeeks)],

    #  tag(symmetry-breaking)
    [
        LexIncreasing(vr, matrix=True),

        [Increasing([vr[i][w] for i in range(nVisitees, n)], strict=True) for w in range(nWeeks)]
    ],

    # linking a visitor with its group
    [(gr[i][w], vr[i][w]) in vr_table for i in range(n) for w in range(nWeeks)],

    # linking a visitee with its group
    [(ge[i][w], ve[i][w]) in ve_table for i in range(n) for w in range(nWeeks)]
)
