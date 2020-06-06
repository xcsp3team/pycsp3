from pycsp3 import *

x = VarArray(size=10, dom=range(10))

table = {(range(1, 7), ANY, gt(7)), (lt(3), ANY, ge(6)), (ne(2), 9, ANY), ((2, 4), ANY, (6, 8)),
         (complement(range(2, 8)), complement(1, 3, 5, 7, 9), ANY)}

satisfy(
    x[0:3] in table
)


# Note that:
# if table is defined as a set, it is not possible to embed sets (or lists), this is why we have to write ((2, 4), ANY, (6, 8))
# if instaed table is defined as a list, one can write ({2, 4}, ANY, {6, 8})
