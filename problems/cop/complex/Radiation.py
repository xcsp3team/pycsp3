"""
See "CP and IP approaches to cancer radiotherapy delivery optimization" by D. Baatar, N. Boland, S. Brand, and P. Stuckey.
    Constraints Jounral, 16(2): 173-194 (2011)
See Model in MiniZinc -- https://github.com/MiniZinc/minizinc-benchmarks/blob/master/radiation/radiation.mzn
    used for competitions 2012, 2013, 2015 and 2020
Examples of Execution:
  python3 Radiation.py -data=Radiation-01.json
  python3 Radiation.py -data=Radiation-01.dzn -dataparser=Radiation_ParserZ.py
"""

from pycsp3 import *

intensity = data  # intensity matrix
nRows, nCols = len(intensity), len(intensity[0])
nIntensities = max(v for t in intensity for v in t) + 1  # +1 because we also have 0
nCells = nRows * nCols + 1  # +1 to avoid systematically adding 1 in the model

# k is the number of shape matrices
k = Var(range(nCells))

# x[b] is the number of shape matrices with associated beam-on time b
x = VarArray(size=nIntensities, dom=lambda b: range(nCells) if b > 0 else {0})

# q[i,j,b] is the number of shape matrices that have associated beam-on time b and that expose cell (i,j)
q = VarArray(size=[nRows, nCols, nIntensities], dom=lambda i, j, b: range(nCells) if b > 0 else {0})

satisfy(
    # computing k
    k == Sum(x),

    # respecting the specified intensity in each cell
    [Sum(b * q[i][j][b] for b in range(1, nIntensities)) == intensity[i][j] for i in range(nRows) for j in range(nCols)],

    # settings upper bounds on increments
    [x[b] >= q[i][0][b] + Sum(max(q[i][j][b] - q[i][j - 1][b], 0) for j in range(1, nCols)) for i in range(nRows) for b in range(1, nIntensities)]
)

minimize(
    # minimizing (beam-time,k)
    nCells * Sum(b * x[b] for b in range(1, nIntensities)) + k
)

""" Comments
1) using nCells as coefficient for the beam-time (i.e., the sum in the objective) allows us to simulate
   a lexicographic order
2) ACE is fairly competitive: on a fast laptop, e.g., the bound 4356 is found in 174 seconds for the instance i9-23  
"""
