"""
See Operations research: applications and algorithms by W. Winston

The Dakota Furniture Company manufactures desks, tables, and chairs. The manufacture
of each type of furniture requires lumber and two types of skilled labor: finishing and
carpentry. The amount of each resource needed to make each type of furniture is given in
the following table

  Resource        Desk  Table Chair
  Lumber           8     6     1
  Finishing hours  4     1     1.5
  Carpentry hours  2     1.5   0.5

Currently, 48 board feet of lumber, 20 finishing hours, and 8 carpentry hours are available.
A desk sells for $60, a table for $30, and a chair for $20. Dakota believes that demand for
desks and chairs is unlimited, but at most five tables can be sold. Because the available
resources have already been purchased, Dakota wants to maximize total revenue.

Execution:
  python3 DakotaFurniture.py
"""

from pycsp3 import *

# d is the number of manufactured desks
d = Var(range(100))

# t is the number of manufactured  tables
t = Var(range(100))

# c is the number of manufactured chairs
c = Var(range(100))

satisfy(
    8 * d + 6 * t + c <= 48,
    8 * d + 4 * t + 3 * c <= 40,
    4 * d + 3 * t + c <= 16,
    t <= 5
)

maximize(
    60 * d + 30 * t + 20 * c
)

""" Comments
1) PyCSP3 does not currently handle floats (as CP solvers, in general), 
   so some coefficients have been multiplied.
"""
