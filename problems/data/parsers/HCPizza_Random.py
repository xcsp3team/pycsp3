"""
Example: python3 pycsp3/problems/cop/complex/HCPizza.py  -dataparser=pycsp3/problems/data/parsers/HCPizza_Random.py 10 10 2 6 0
"""

import random

from pycsp3.compiler import Compilation
from pycsp3.problems.data.parsing import *

nRows = ask_number("Number of rows")
nCols = ask_number("Number of columns")
minIngredients = ask_number("Min ingredients")
maxSize = ask_number("Max size")
seed = ask_number("Seed")

random.seed(seed)

data["minIngredients"] = minIngredients
data["maxSize"] = maxSize
data["pizza"] = [[random.randrange(0, 2) for _ in range(nCols)] for _ in range(nRows)]

Compilation.string_data = "-" + "-".join(str(v) for v in (nRows, nCols, minIngredients, maxSize, "{:02d}".format(seed)))
