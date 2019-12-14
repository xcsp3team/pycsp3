import math

from pycsp3 import *

"""
    Rectangle packing problem. See Simonis and O'Sullivan. Search strategies for rectangle packing. 
    In Proceedings of CP 2008. Also used in short supports papers."
"""

width, height = data.container.width, data.container.height
boxes = data.boxes
nBoxes = len(boxes)

# x[i] is the x-coordinate where is put the ith rectangle
x = VarArray(size=nBoxes, dom=range(width))

# y[i] is the y-coordinate where is put the ith rectangle
y = VarArray(size=nBoxes, dom=range(height))

satisfy(
    #  unary constraints on x
    [x[i] + boxes[i].width <= width for i in range(nBoxes)],

    # unary constraints on y
    [y[i] + boxes[i].height <= height for i in range(nBoxes)],

    # no overlap on boxes
    NoOverlap(origins=[(x[i], y[i]) for i in range(nBoxes)], lengths=[(box.width, box.height) for box in boxes]),

    # tag(symmetry-breaking)
    [x[- 1] <= math.floor((width - boxes[- 1].width) // 2.0), y[- 1] <= x[- 1]] if width == height else None
)
