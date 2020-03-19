from pycsp3 import *

width, height = data.containerWidth, data.containerHeight
containers = data.containers
# separations = data.separations
nContainers = len(containers)

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

    # no overlapping between rectangles
    NoOverlap(origins=[(x[i], y[i]) for i in range(nContainers)], lengths=[(w[i], h[i]) for i in range(nContainers)])
)


# TODO model complet ? a voir avec la short table...

def table(i, j, separation):
    tuples = []
    # horizontal, i before j
    mini = min(containers[i].width, containers[i].height)
    maxi = max(containers[i].width, containers[i].height)
    for xi in range(width - mini):
        for k in range(mini, maxi):
            tuples.append(tuple(xi, mini, xi + k + separation, ANY, ANY, ANY, ANY, ANY))
        for xj in range(xi + maxi + separation, width):
            tuples.append(tuple(xi, ANY, xj, ANY, ANY, ANY, ANY, ANY))
    return tuples
