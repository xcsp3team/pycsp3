"""
This is Problem 064 on CSPLib, called Synchronous Optical Networking Problem (SONET).

In the SONET problem we are given a set of nodes, and for
each pair of nodes we are given the demand (which is the number of channels required to carry
network traffic between the two nodes). The demand may be zero, in which case the two nodes
do not need to be connected. A SONET ring connects a set of nodes. A node is installed on
a ring using a piece of equipment called an add-drop multiplexer (ADM). Each node may be
installed on more than one ring. Network traffic can be transmitted from one node to another
only if they are both installed on the same ring. Each ring has an upper limit on the number
of nodes, and a limit on the number of channels. The demand of a pair of nodes may be split
between multiple rings. The objective is to minimize the total number of ADMs used while
satisfying all demands.

## Data (example)
  s3ring03json

## Model
  constraints: Lex, Sum, Table

## Execution
  - python Sonet.py -data=<datafile.json>
  - python Sonet.py -data=<datafile.txt> -parser=Sonet_Parser.py

## Links
  - https://www.csplib.org/Problems/prob056/
  - https://www.cril.univ-artois.fr/XCSP23/competitions/cop/cop

## Tags
  real, csplib, xcsp23
"""

from pycsp3 import *

n, m, r, connections = data

# x[i][j] is 1 if the ith ring contains the jth node
x = VarArray(size=[m, n], dom={0, 1})

T = {tuple(1 if j // 2 == i else ANY for j in range(2 * m)) for i in range(m)}

satisfy(
    [(x[i][conn] for i in range(m)) in T for conn in connections],

    # respecting the capacity of rings
    [Sum(x[i]) <= r for i in range(m)],

    # tag(symmetry-breaking)
    LexIncreasing(x)
)

minimize(
    # minimizing the number of nodes installed on rings
    Sum(x)
)

"""
1) Note that
   [(x[i][conn] for i in range(m)) in T for conn in connections]
 is a shortcut for:
   [(x[i][j1 if k == 0 else j2] for i in range(m) for k in range(2)) in T
      for (j1, j2) in connections]
"""
