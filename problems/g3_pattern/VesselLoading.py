from pycsp3 import *

"""
  Problem 008 on CSPLib
"""

width, height = data.deckWidth, data.deckHeight
containers = data.containers
nContainers = len(containers)

groups = [[i for i, container in enumerate(containers) if container.type == k] for k in range(max(container.type for container in containers) + 1)]
t = [(i, j, separation.distance) for separation in data.separations for i in groups[separation.type1] for j in groups[separation.type2]]

# x[i] is the x-coordinate of the ith container
x = VarArray(size=nContainers, dom=range(width))

# y[i] is the y-coordinate of the ith container
y = VarArray(size=nContainers, dom=range(height))

# w[i] is the width of the ith container
w = VarArray(size=nContainers, dom=lambda i: {containers[i].width, containers[i].height})

# h[i] is the height of the ith container
h = VarArray(size=nContainers, dom=lambda i: {containers[i].width, containers[i].height})

# r[i] is 1 iff the ith container is rotated by 90 degrees
r = VarArray(size=nContainers, dom={0, 1})

satisfy(
    # horizontal control
    [x[i] + w[i] <= width for i in range(nContainers)],

    # vertical control
    [y[i] + h[i] <= height for i in range(nContainers)],

    # managing rotation
    [(r[i], w[i], h[i]) in {(0, container.width, container.height), (1, container.height, container.width)} for i, container in enumerate(containers)],

    # no overlapping between containers
    NoOverlap(origins=[(x[i], y[i]) for i in range(nContainers)], lengths=[(w[i], h[i]) for i in range(nContainers)]),

    # respecting separations between classes
    [(x[i] + w[i] + sep <= x[j]) | (x[j] + w[j] + sep <= x[i]) | (y[i] + h[i] + sep <= y[j]) | (y[j] + h[j] + sep <= y[i]) for (i, j, sep) in t]
)
