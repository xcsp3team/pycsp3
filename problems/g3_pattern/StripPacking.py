from pycsp3 import *

container = data.container
rectangles = data.rectangles
nRectangles = len(rectangles)

# x[i] is the x-coordinate of the ith rectangle
x = VarArray(size=nRectangles, dom=range(container.width))

# y[i] is the y-coordinate of the ith rectangle
y = VarArray(size=nRectangles, dom=range(container.height))

# w[i] is the width of the ith rectangle
w = VarArray(size=nRectangles, dom=lambda i: {rectangles[i].width, rectangles[i].height})

# h[i] is the height of the ith rectangle
h = VarArray(size=nRectangles, dom=lambda i: {rectangles[i].width, rectangles[i].height})

# r[i] is 1 iff the ith rectangle is rotated by 90 degrees
r = VarArray(size=nRectangles, dom={0, 1})

satisfy(
    # horizontal control
    [x[i] + w[i] <= container.width for i in range(nRectangles)],

    # vertical control
    [y[i] + h[i] <= container.height for i in range(nRectangles)],

    # managing rotation
    [(r[i], w[i], h[i]) in [(0, rect.width, rect.height), (1, rect.height, rect.width)] for i, rect in enumerate(rectangles)],

    # no overlapping between rectangles
    NoOverlap(origins=[(x[i], y[i]) for i in range(nRectangles)], lengths=[(w[i], h[i]) for i in range(nRectangles)])

)
