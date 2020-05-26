from pycsp3 import *

x = VarArray(size=10, dom=range(10))

satisfy(
    (x[0:3] in {(inside(range(1, 7)), ANY, gt(7)), (lt(3), ANY, ge(6)), (ne(2), 9, ANY), (inside(2, 4), ANY, inside([6, 8])),
                (outside(range(2, 8)), outside(1, 3, 5, 7, 9), ANY)})
)
