"""
See https://algorist.com/problems/Set_Packing.html

The data are represented by a set of subsets S1,...,Sm of the universal set U={1,...,n}.
The problem is to find the largest number of mutually disjoint subsets from S?

Examples of Execution:
  python3 SetPacking.py -data=Subsets_example.json
"""

from pycsp3 import *

subsets = data
vals = sorted({v for subset in subsets for v in subset})
m = len(subsets)

# x[i] is 1 iff the ith subset is selected
x = VarArray(size=m, dom={0, 1})

satisfy(
    # avoiding intersection of subsets
    Count(scp, value=1) <= 1 for scp in [[x[i] for i, subset in enumerate(subsets) if v in subset] for v in vals]
)

maximize(
    # maximizing the number of selected subsets
    Sum(x)
)

"""
1) we avoid using values instead of vals as name for the list of bid values 
   as it may enter in conflict with the function values() in a notebook 
"""
