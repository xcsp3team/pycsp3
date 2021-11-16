"""
Example: python3 pycsp3/problems/cop/complex/Warehouse.py  -dataparser=pycsp3/problems/data/parsers/Warehouse_Random.py 20 50 100 10 1000 0
"""

import random

from pycsp3.compiler import Compilation
from pycsp3.problems.data.parsing import *

nWarehouses = ask_number("Number of warehouses")
nStores = ask_number("Number of stores")
fixedCost = ask_number("Fixed cost")
minSupplyCost = ask_number("Min supply cost")
maxSupplyCost = ask_number("Max supply cost")
seed = ask_number("Seed")

data["fixedCost"] = fixedCost

random.seed(seed)
data["warehouseCapacities"] = [random.randrange(1, nStores // 3) for _ in range(nWarehouses)]
data["storeSupplyCosts"] = [[random.randrange(minSupplyCost, maxSupplyCost) for _ in range(nWarehouses)] for _ in range(nStores)]

Compilation.string_data = "-" + "-".join(str(v) for v in (nWarehouses, nStores, "{:02d}".format(seed)))

# for the new series, fixedCost =100 and min/max supply cost was 10..1000
