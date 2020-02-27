from pycsp3 import *

nPeriods = data.nPeriods
minCourses, maxCourses = data.minCourses, data.maxCourses
minCredits, maxCredits = data.minCredits, data.maxCredits * maxCourses if subvariant("d") else data.maxCredits
credits, prerequisites = data.credits, data.prerequisites
nCourses, nPrerequisites = len(credits), len(prerequisites)


def table(c):
    return {tuple(credits[c] if j == p else p if j == nPeriods else 0 for j in range(nPeriods + 1)) for p in range(nPeriods)}


# s[c] is the period (schedule) for course c
s = VarArray(size=nCourses, dom=range(nPeriods))

# co[p] is the number of courses at period p
co = VarArray(size=nPeriods, dom=range(minCourses, maxCourses + 1))

# cr[p] is the number of credits at period p
cr = VarArray(size=nPeriods, dom=range(minCredits, maxCredits + 1))

if variant("m1"):
    # cp[c][p] is 0 if the course c is not planned at period p, the number of credits for c otherwise
    cp = VarArray(size=[nCourses, nPeriods], dom=lambda c, p: {0, credits[c]})

    satisfy(
        # channeling between arrays cp and s
        [(*cp[c], s[c]) in table(c) for c in range(nCourses)],

        # counting the number of courses in each period
        [Count(s, value=p) == co[p] for p in range(nPeriods)],

        # counting the number of credits in each period
        [Sum(cp[:, p]) == cr[p] for p in range(nPeriods)]
    )

elif variant("m2"):
    # pc[p][c] is 1 iff the course c is at period p
    pc = VarArray(size=[nPeriods, nCourses], dom={0, 1})

    satisfy(
        # tag(channeling)
        [iff(pc[p][c], s[c] == p) for p in range(nPeriods) for c in range(nCourses)],

        # ensuring that each course is assigned to a period
        [Sum(pc[:, c]) == 1 for c in range(nCourses)],

        # counting the number of courses in each period
        [Sum(pc[p]) == co[p] for p in range(nPeriods)],

        # counting the number of credits in each period
        [pc[p] * credits == cr[p] for p in range(nPeriods)]
    )

satisfy(
    # handling prerequisites
    s[c1] < s[c2] for (c1, c2) in prerequisites
)

if subvariant("d"):
    minimize(
        # minimizing the maximal distance in term of credits
        Maximum(cr) - Minimum(cr)
    )
else:
    minimize(
        # minimizing the maximum number of credits in periods
        Maximum(cr)
    )

annotate(decision=s)



# mincr is the minimum number of credits over the periods
# mincr = Var(dom=range(minCredits, maxCredits + 1))
#
# # maxcr is the maximum number of credits over the periods
# maxcr = Var(dom=range(minCredits, maxCredits + 1))
#
# satisfy(
#     Minimum(cr) == mincr,
#     Maximum(cr) == maxcr
#     #Count(s, value=1) > Count(s,value=2)
# )
#
# minimize(
#     # minimizing the maximal distance in term of credits
#     maxcr - mincr
# )


# distcr is the maximal distance in term of credits
# distcr = Var(dom=range(maxCredits + 1))
# distcr == maxcr - mincr
