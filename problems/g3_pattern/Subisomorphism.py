from pycsp3 import *

nPatternNodes, nTargetNodes = data.nPatternNodes, data.nTargetNodes
patternEdges, targetEdges = data.patternEdges, data.targetEdges

pLoops = [n1 for (n1, n2) in patternEdges if n1 == n2]
tLoops = [n1 for (n1, n2) in targetEdges if n1 == n2]

pDegrees = [len([edge for edge in patternEdges if i in edge]) for i in range(nPatternNodes)]
tDegrees = [len([edge for edge in targetEdges if i in edge]) for i in range(nTargetNodes)]

bothWayTable = [(n1, n2) for (n1, n2) in targetEdges] + [(n2, n1) for (n1, n2) in targetEdges]
degree_conflicts = [[j for j in range(nTargetNodes) if tDegrees[j] < pDegrees[i]] for i in range(nPatternNodes)]

# x[i] is the node from the target graph to which the ith node of the pattern graph is mapped.
x = VarArray(size=nPatternNodes, dom=range(nTargetNodes))

satisfy(
    # ensuring injectivity
    AllDifferent(x),

    # being careful of self-loops
    [x[n] in tLoops for n in pLoops],

    # preserving edges
    [(x[n1], x[n2]) in bothWayTable for (n1, n2) in patternEdges],

    # tag(redundant-constraints)
    [x[i] not in conflicts for i, conflicts in enumerate(degree_conflicts) if len(conflicts) > 0]
)

