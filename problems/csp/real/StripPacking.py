"""
See https://en.wikipedia.org/wiki/Strip_packing_problem

Example of Execution:
  python3 StripPacking.py -data=StripPacking_C1P1.json
"""

from pycsp3 import *

width, height = data.container
rectangles = data.rectangles
nRectangles = len(rectangles)

# x[i] is the x-coordinate of the ith rectangle
x = VarArray(size=nRectangles, dom=range(width))

# y[i] is the y-coordinate of the ith rectangle
y = VarArray(size=nRectangles, dom=range(height))

# w[i] is the width of the ith rectangle
w = VarArray(size=nRectangles, dom=lambda i: {rectangles[i].width, rectangles[i].height})

# h[i] is the height of the ith rectangle
h = VarArray(size=nRectangles, dom=lambda i: {rectangles[i].width, rectangles[i].height})

# r[i] is 1 iff the ith rectangle is rotated by 90 degrees
r = VarArray(size=nRectangles, dom={0, 1})

satisfy(
    # horizontal control
    [x[i] + w[i] <= width for i in range(nRectangles)],

    # vertical control
    [y[i] + h[i] <= height for i in range(nRectangles)],

    # managing rotation
    [(r[i], w[i], h[i]) in {(0, wgt, hgt), (1, hgt, wgt)} for i, (wgt, hgt) in enumerate(rectangles)],

    # no overlapping between rectangles
    NoOverlap(origins=[(x[i], y[i]) for i in range(nRectangles)], lengths=[(w[i], h[i]) for i in range(nRectangles)])
)
